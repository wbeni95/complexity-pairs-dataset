"""Checks of the proofs in pairs/or-convolution-naive-vs-zeta-mobius/PROOFS.md (sections 3 to 8).

Every test runs the UNCHANGED implementations on fixed inputs and seeds, over the ranges stated in each test. The
written proofs cover the general statements; these tests re-run their computable facts.
"""
import importlib.util
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "or-convolution-naive-vs-zeta-mobius"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NAIVE = load(ENTRY / "implementations" / "naive.py", "proofs_orc_naive").or_convolution_naive
ZM_MOD = load(ENTRY / "implementations" / "zeta_mobius.py", "proofs_orc_zm")
FAST = ZM_MOD.or_convolution_zeta_mobius


def definition(f, g):
    size = len(f)
    h = [0] * size
    for a in range(size):
        for b in range(size):
            h[a | b] += f[a] * g[b]
    return h


def zeta_def(v):
    size = len(v)
    return [sum(v[t] for t in range(size) if t & ~s == 0) for s in range(size)]


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class MaxInt:
    """An integer that records the largest absolute value of every sum, difference and product it produces."""
    __slots__ = ("v",)
    top = 0

    def __init__(self, v):
        self.v = v
        if abs(v) > MaxInt.top:
            MaxInt.top = abs(v)

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, MaxInt) else x

    def __add__(self, o):
        return MaxInt(self.v + self._v(o))

    __radd__ = __add__

    def __sub__(self, o):
        return MaxInt(self.v - self._v(o))

    def __rsub__(self, o):
        return MaxInt(self._v(o) - self.v)

    def __mul__(self, o):
        return MaxInt(self.v * self._v(o))

    __rmul__ = __mul__


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 3 and 4. Both implementations are bilinear in (f, g) (every output entry is a sum of
    products of one f entry and one g entry, with integer coefficients), so agreeing with the definition on every
    pair of unit vectors is a complete check; done for n = 0..4. Seeded random inputs: n = 0..8, 3 per n."""

    def test_unit_pairs_complete(self):
        for n in range(5):
            size = 1 << n
            for a in range(size):
                for b in range(size):
                    f = tuple(int(i == a) for i in range(size))
                    g = tuple(int(i == b) for i in range(size))
                    want = [int(s == (a | b)) for s in range(size)]
                    self.assertEqual(list(NAIVE((f, g))), want, (n, a, b))
                    self.assertEqual(list(FAST((f, g))), want, (n, a, b))

    def test_random(self):
        for n in range(9):
            for seed in range(3):
                rng = random.Random(f"orc-proofs|{n}|{seed}")
                f = tuple(rng.randint(-9, 9) for _ in range(1 << n))
                g = tuple(rng.randint(-9, 9) for _ in range(1 << n))
                want = definition(f, g)
                self.assertEqual(list(NAIVE((f, g))), want, n)
                self.assertEqual(list(FAST((f, g))), want, n)

    def test_diagonalisation_identity(self):
        """zeta(h) = zeta(f) . zeta(g) pointwise, n = 0..9."""
        for n in range(10):
            rng = random.Random(f"orc-diag|{n}")
            f = tuple(rng.randint(-9, 9) for _ in range(1 << n))
            g = tuple(rng.randint(-9, 9) for _ in range(1 << n))
            h = FAST((f, g))
            self.assertEqual(ZM_MOD._zeta(h), [x * y for x, y in zip(zeta_def(f), zeta_def(g))], n)


class AndMirrorTests(unittest.TestCase):
    """PROOFS.md section 6: the AND convolution equals the OR convolution of the complemented-index functions, read
    at complemented indices (n = 0..7, both implementations, 2 seeds per n)."""

    def test_mirror(self):
        for n in range(8):
            size, full = 1 << n, (1 << n) - 1
            for seed in range(2):
                rng = random.Random(f"orc-and|{n}|{seed}")
                f = tuple(rng.randint(-9, 9) for _ in range(size))
                g = tuple(rng.randint(-9, 9) for _ in range(size))
                direct = [0] * size
                for a in range(size):
                    for b in range(size):
                        direct[a & b] += f[a] * g[b]
                fc = tuple(f[x ^ full] for x in range(size))
                gc = tuple(g[x ^ full] for x in range(size))
                for impl in (NAIVE, FAST):
                    h = impl((fc, gc))
                    self.assertEqual([h[s ^ full] for s in range(size)], direct, (n, seed))


class ValueSizeTests(unittest.TestCase):
    """PROOFS.md section 7: with entries of absolute value at most 9, every value the fast method computes has
    absolute value at most 81 * 8^n, and every output entry h[S] at most 81 * 3^|S| (n = 0..12; inputs f = g = 9
    and f = 9, g = -9, plus 2 seeded random inputs per n); f = g = 9 attains 81 * 3^n at the full set (n = 10)."""

    def test_bounds(self):
        for n in range(13):
            size = 1 << n
            rng = random.Random(f"orc-size|{n}")
            inputs = [([9] * size, [9] * size), ([9] * size, [-9] * size)]
            inputs += [([rng.randint(-9, 9) for _ in range(size)], [rng.randint(-9, 9) for _ in range(size)])
                       for _ in range(2)]
            for f, g in inputs:
                MaxInt.top = 0
                h = FAST((tuple(map(MaxInt, f)), tuple(map(MaxInt, g))))
                self.assertLessEqual(MaxInt.top, 81 * 8 ** n, n)
                self.assertTrue(all(abs(x.v) <= 81 * 3 ** bin(s).count('1') for s, x in enumerate(h)), n)
        h = FAST(((9,) * 1024, (9,) * 1024))
        self.assertEqual(h[1023], 81 * 3 ** 10)


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 8: Theta(2^n) space. Peak traced allocation during the call (instance built before
    tracing) between 8 * 2^n and 192 * 2^n + 4096 bytes: naive n = 4..9, zeta-Moebius n = 4..14."""

    def _check(self, fn, ns):
        for n in ns:
            rng = random.Random(f"orc-space|{n}")
            inst = (tuple(rng.randint(-9, 9) for _ in range(1 << n)), tuple(rng.randint(-9, 9) for _ in range(1 << n)))
            peak = peak_bytes(fn, inst)
            self.assertGreaterEqual(peak, 8 * (1 << n), n)
            self.assertLessEqual(peak, 192 * (1 << n) + 4096, n)

    def test_naive(self):
        self._check(NAIVE, range(4, 10))

    def test_fast(self):
        self._check(FAST, range(4, 15))


if __name__ == "__main__":
    unittest.main()
