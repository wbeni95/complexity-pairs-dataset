"""Checks of the proofs in pairs/integer-multiplication-schoolbook-vs-karatsuba/PROOFS.md (sections 4 to 8).

Every test runs the UNCHANGED implementations on fixed inputs and seeds, over the ranges stated in each test. The
written proofs cover the general statements; these tests re-run their computable facts.
"""
import importlib.util
import math
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "integer-multiplication-schoolbook-vs-karatsuba"
BITS = 15
BASE = 1 << BITS


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SCHOOL = load(ENTRY / "implementations" / "schoolbook.py", "proofs_imul_school").multiply_schoolbook
KA = load(ENTRY / "implementations" / "karatsuba.py", "proofs_imul_kara")
KARA = KA.multiply_karatsuba


def value(digits):
    v = 0
    for d in reversed(digits):
        v = (v << BITS) | int(d)
    return v


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


def inputs(n, rng):
    """Uniform digits, all maximal digits, runs of 0 and BASE - 1, and factors with equal halves at the top node."""
    out = [tuple(rng.randrange(BASE) for _ in range(n)) for _ in range(2)]
    out.append(tuple([BASE - 1] * n))
    out.append(tuple(rng.choice((0, BASE - 1)) for _ in range(n)))
    half = tuple(rng.randrange(BASE) for _ in range(n // 2))
    out.append(half + half + tuple(rng.randrange(BASE) for _ in range(n % 2)))
    return out


class MaxDigit:
    """An int-like digit that records the largest absolute value of every result of an arithmetic operation."""
    __slots__ = ("v",)
    top = 0

    def __init__(self, v):
        self.v = v
        if abs(v) > MaxDigit.top:
            MaxDigit.top = abs(v)

    @staticmethod
    def _v(x):
        return x.v if isinstance(x, MaxDigit) else x

    def __mul__(self, o):
        return MaxDigit(self.v * self._v(o))

    __rmul__ = __mul__

    def __add__(self, o):
        return MaxDigit(self.v + self._v(o))

    __radd__ = __add__

    def __sub__(self, o):
        return MaxDigit(self.v - self._v(o))

    def __rsub__(self, o):
        return MaxDigit(self._v(o) - self.v)

    def __neg__(self):
        return MaxDigit(-self.v)

    def __and__(self, o):
        return MaxDigit(self.v & self._v(o))

    __rand__ = __and__

    def __rshift__(self, o):
        return MaxDigit(self.v >> self._v(o))

    def __lt__(self, o):
        return self.v < self._v(o)

    def __ne__(self, o):
        return self.v != self._v(o)

    def __eq__(self, o):
        return self.v == self._v(o)

    def __bool__(self):
        return bool(self.v)

    def __int__(self):
        return self.v

    __index__ = __int__

    def __hash__(self):
        return hash(self.v)


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 4 and 5: both return the 2n-digit representation of the product, every digit in
    [0, BASE). n = 0..70, 96, 100, 127, 128, 129, 200, 257; five inputs per factor kind (see inputs())."""

    SIZES = list(range(71)) + [96, 100, 127, 128, 129, 200, 257]

    def test_products(self):
        for n in self.SIZES:
            rng = random.Random(f"imul-proofs|{n}")
            xs = inputs(n, rng)
            for a in xs:
                for b in xs[:3]:
                    want = value(a) * value(b)
                    for fn in (SCHOOL, KARA):
                        out = fn((a, b))
                        self.assertEqual(len(out), 2 * n, (n, fn.__name__))
                        self.assertTrue(all(0 <= d < BASE for d in out), (n, fn.__name__))
                        self.assertEqual(value(out), want, (n, fn.__name__))


class ValueBoundTests(unittest.TestCase):
    """PROOFS.md section 6: every value computed from digits by either implementation (indices are plain ints and are
    not recorded) has absolute value at most BASE^2 - 1 < 2^30, and the schoolbook bound BASE^2 - 1 is attained on all-maximal digits.
    n = 1, 2, 31, 32, 33, 64, 65, 100, 129 on the inputs of inputs()."""

    def test_bounds(self):
        for n in (1, 2, 31, 32, 33, 64, 65, 100, 129):
            rng = random.Random(f"imul-bound|{n}")
            xs = inputs(n, rng)
            for a in xs:
                for b in xs[:3]:
                    for fn in (SCHOOL, KARA):
                        MaxDigit.top = 0
                        out = fn((tuple(map(MaxDigit, a)), tuple(map(MaxDigit, b))))
                        self.assertLessEqual(MaxDigit.top, BASE * BASE - 1, (n, fn.__name__))
                        self.assertEqual(value(out), value(a) * value(b))
        MaxDigit.top = 0
        SCHOOL((tuple(map(MaxDigit, [BASE - 1] * 4)), tuple(map(MaxDigit, [BASE - 1] * 4))))
        self.assertEqual(MaxDigit.top, BASE * BASE - 1)


class RecursionShapeTests(unittest.TestCase):
    """PROOFS.md section 7: for every n > 32, all calls at depth j have ceil(n / 2^j) digits, the leaves are the 3^d
    calls at depth d (the least d with ceil(n / 2^d) <= 32) and have between 17 and 32 digits, and the multiplications
    performed (in _schoolbook) number exactly 3^d ceil(n / 2^d)^2, between 17^2 (n/32)^log2(3) and 32^2 (n/16)^log2(3);
    for n <= 32 they number n^2. Measured by wrapping the module's _schoolbook (the code is unchanged), n = 1..300 and
    n = 383, 384, 385, 511, 512, 513, 600."""

    def test_shape(self):
        original = KA._schoolbook
        calls = []

        def spy(x, y):
            calls.append((len(x), len(y)))
            return original(x, y)

        KA._schoolbook = spy
        try:
            for n in list(range(1, 301)) + [383, 384, 385, 511, 512, 513, 600]:
                rng = random.Random(f"imul-shape|{n}")
                a = tuple(rng.randrange(BASE) for _ in range(n))
                b = tuple(rng.randrange(BASE) for _ in range(n))
                calls.clear()
                KARA((a, b))
                performed = sum(p * q for p, q in calls)
                if n <= 32:
                    self.assertEqual(calls, [(n, n)])
                    continue
                d = 0
                while -(-n // (1 << d)) > 32:
                    d += 1
                leaf = -(-n // (1 << d))
                self.assertEqual(calls, [(leaf, leaf)] * 3 ** d, n)
                self.assertTrue(17 <= leaf <= 32, n)
                self.assertEqual(performed, 3 ** d * leaf * leaf, n)
                e = math.log2(3)
                self.assertTrue(17 ** 2 * (n / 32) ** e <= performed <= 32 ** 2 * (n / 16) ** e, n)
        finally:
            KA._schoolbook = original


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 8: Theta(n) space. For n = 128, 256, 512, 1024 the peak traced allocation during the call
    (instance built before tracing) divided by n is at least 16 (2n output slots of 8 bytes), at most 1000, and varies by
    a factor of at most 1.5 across the four sizes (n^log2(3) would vary by a factor of 3.3, n log n by 1.43 only, so the
    lower-order alternative is excluded by the written proof, not by this check)."""

    def test_peaks(self):
        for fn in (SCHOOL, KARA):
            per = []
            for n in (128, 256, 512, 1024):
                rng = random.Random(f"imul-space|{n}")
                inst = (tuple(rng.randrange(BASE) for _ in range(n)), tuple(rng.randrange(BASE) for _ in range(n)))
                per.append(peak_bytes(fn, inst) / n)
            self.assertGreaterEqual(min(per), 16, fn.__name__)
            self.assertLessEqual(max(per), 1000, fn.__name__)
            self.assertLessEqual(max(per) / min(per), 1.5, (fn.__name__, per))


if __name__ == "__main__":
    unittest.main()
