"""Checks of the proofs in pairs/subset-sum-zeta-transform-naive-vs-yates/PROOFS.md (sections 3 to 8).

Every test runs the UNCHANGED implementations (or the entry's harness) on fixed inputs and seeds, over the ranges
stated in each test. The written proofs cover the general statements; these tests re-run their computable facts.
"""
import importlib.util
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "subset-sum-zeta-transform-naive-vs-yates"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NAIVE = load(ENTRY / "implementations" / "naive.py", "proofs_zeta_naive").zeta_naive
YATES = load(ENTRY / "implementations" / "yates.py", "proofs_zeta_yates").zeta_yates
MOEBIUS = load(ROOT / "pairs" / "or-convolution-naive-vs-zeta-mobius" / "implementations" / "zeta_mobius.py",
               "proofs_zeta_orc")._moebius


def definition(f):
    """zeta[S] = sum of f[T] over T subset of S, by scanning all masks T (no submask stepping, no passes)."""
    size = len(f)
    return [sum(f[t] for t in range(size) if t & ~s == 0) for s in range(size)]


def peak_bytes(fn, arg):
    """Peak traced allocation (bytes) during fn(arg), above the level at the call; arg is built before tracing."""
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class SubmaskStepTests(unittest.TestCase):
    """PROOFS.md section 3: from t = s, the step t -> (t - 1) & s visits every submask of s exactly once, in
    decreasing order, and reaches 0 last. Exhaustive for every s < 2^11."""

    def test_order_and_completeness(self):
        for s in range(1 << 11):
            seen, t = [], s
            while True:
                seen.append(t)
                if t == 0:
                    break
                t = (t - 1) & s
            expect = sorted((u for u in range(s + 1) if u & ~s == 0), reverse=True)
            self.assertEqual(seen, expect, s)


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 3 and 4: both implementations compute zeta. Both are linear maps with integer
    coefficients (they only add entries), so agreeing with the definition on every unit vector is a complete check
    of the map; it is done for n = 0..8. Random vectors (3 seeds per n, n = 0..10) are checked too."""

    def test_unit_vectors_complete(self):
        for n in range(9):
            size = 1 << n
            for t in range(size):
                e = [0] * size
                e[t] = 1
                col = [1 if t & ~s == 0 else 0 for s in range(size)]
                self.assertEqual(NAIVE(tuple(e)), col, (n, t))
                self.assertEqual(YATES(tuple(e)), col, (n, t))

    def test_random_vectors(self):
        for n in range(11):
            for seed in range(3):
                rng = random.Random(f"zeta-proofs|{n}|{seed}")
                f = tuple(rng.randint(-9, 9) for _ in range(1 << n))
                want = definition(f)
                self.assertEqual(NAIVE(f), want, n)
                self.assertEqual(YATES(f), want, n)


class KroneckerAndMoebiusTests(unittest.TestCase):
    """PROOFS.md section 5: the zeta matrix is the n-fold Kronecker power of Z1 = [[1,0],[1,1]] (n = 1..5); the
    Moebius passes (the OR-convolution entry's _moebius, Kronecker power of [[1,0],[-1,1]] = Z1^-1) invert Yates'
    passes on both sides (n = 0..10, seeded vectors)."""

    @staticmethod
    def kron(a, b):
        return [[x * y for x in ra for y in rb] for ra in a for rb in b]

    def test_kronecker_power(self):
        z1 = [[1, 0], [1, 1]]
        for n in range(1, 6):
            m = [[1]]
            for _ in range(n):
                m = self.kron(z1, m)          # the first factor applied acts on the highest bit
            size = 1 << n
            zeta = [[1 if t & ~s == 0 else 0 for t in range(size)] for s in range(size)]
            self.assertEqual(m, zeta, n)

    def test_moebius_inverts_zeta_with_n_2n1_subtractions(self):
        for n in range(11):
            rng = random.Random(f"zeta-moebius|{n}")
            f = [rng.randint(-9, 9) for _ in range(1 << n)]
            self.assertEqual(MOEBIUS(YATES(tuple(f))), f, n)
            self.assertEqual(YATES(tuple(MOEBIUS(f))), f, n)
        z1, m1 = [[1, 0], [1, 1]], [[1, 0], [-1, 1]]
        prod = [[sum(z1[i][k] * m1[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        self.assertEqual(prod, [[1, 0], [0, 1]])


class ValueSizeTests(unittest.TestCase):
    """PROOFS.md section 8: with entries of absolute value at most 9, every value the implementations compute
    has absolute value at most 9 * 2^n; the constant input 9 attains 9 * 2^|S| at S. n = 0..12."""

    def test_extremal_input(self):
        for n in range(13):
            f = tuple([9] * (1 << n))
            want = [9 * (1 << bin(s).count("1")) for s in range(1 << n)]
            self.assertEqual(YATES(f), want, n)
            if n <= 11:
                self.assertEqual(NAIVE(f), want, n)
            self.assertLessEqual(max(map(abs, want)), 9 * (1 << n))


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 7: Theta(2^n) space. The peak traced allocation during the call (instance built before
    tracing) lies between 8 * 2^n bytes (one list slot per output entry) and 64 * 2^n + 4096 bytes (a slot plus at
    most one int object per entry, and O(1) more), for naive n = 6..12 and Yates n = 6..15."""

    def _check(self, fn, ns):
        for n in ns:
            rng = random.Random(f"zeta-space|{n}")
            f = tuple(rng.randint(-9, 9) for _ in range(1 << n))
            peak = peak_bytes(fn, f)
            self.assertGreaterEqual(peak, 8 * (1 << n), n)
            self.assertLessEqual(peak, 64 * (1 << n) + 4096, n)

    def test_naive(self):
        self._check(NAIVE, range(6, 13))

    def test_yates(self):
        self._check(YATES, range(6, 16))


if __name__ == "__main__":
    unittest.main()
