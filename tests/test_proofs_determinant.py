"""Deterministic checks for pairs/determinant-cofactor-vs-gaussian/PROOFS.md (about two seconds).

Ranges: P = 2^31 - 1 is prime (section 0); both algorithms against the Leibniz formula, exhaustively over 0/1
matrices with n <= 3 and on seeded matrices with n <= 6 (1.2, 2.2); cofactor call and operation counts n = 0..8
(1.4); Gaussian elimination operation counts on seeded non-singular matrices n = 0..40 and on singular ones
(2.3); the harness's known determinants n = 0..6 (section 4); the count of invertible matrices over GF(q) for
q = 2, 3, 5 and n <= 3 (section 4); tracemalloc peaks (1.5, 2.4).
"""
import importlib.util
import itertools
import math
import random
import sys
import tracemalloc
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "determinant-cofactor-vs-gaussian"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_det_harness")
COF = _load(ENTRY / "implementations" / "cofactor.py", "proofs_det_cofactor")
GAU = _load(ENTRY / "implementations" / "gaussian.py", "proofs_det_gaussian")
P = 2 ** 31 - 1

OPS = {"mul": 0, "add": 0, "mod": 0, "inv": 0, "neg": 0}


class C:
    """Residue that counts *, +, -, %, unary - and three-argument pow (inversions) with a counted operand."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, C) else x

    def _op(self, kind, value):
        OPS[kind] += 1
        return C(value)

    def __mul__(self, o):
        return self._op("mul", self.v * self._val(o))

    def __rmul__(self, o):
        return self._op("mul", self._val(o) * self.v)

    def __add__(self, o):
        return self._op("add", self.v + self._val(o))

    def __radd__(self, o):
        return self._op("add", self._val(o) + self.v)

    def __sub__(self, o):
        return self._op("add", self.v - self._val(o))

    def __rsub__(self, o):
        return self._op("add", self._val(o) - self.v)

    def __mod__(self, m):
        return self._op("mod", self.v % m)

    def __neg__(self):
        return self._op("neg", -self.v)

    def __pow__(self, e, m=None):
        return self._op("inv", pow(self.v, e, m))

    def __bool__(self):
        return self.v != 0

    def __eq__(self, o):
        return self.v == self._val(o)

    __hash__ = None


def reset():
    for k in OPS:
        OPS[k] = 0


def leibniz(A, mod=P):
    n = len(A)
    total = 0
    for s in itertools.permutations(range(n)):
        inv = sum(1 for i in range(n) for j in range(i + 1, n) if s[i] > s[j])
        prod = 1
        for i in range(n):
            prod = prod * A[i][s[i]]
        total += -prod if inv % 2 else prod
    return total % mod


def rand_matrix(n, rng, zero_prob=0.0):
    return tuple(tuple(0 if rng.random() < zero_prob else rng.randrange(P) for _ in range(n)) for _ in range(n))


class Prime(unittest.TestCase):
    def test_p_is_prime(self):
        r = math.isqrt(P)
        self.assertTrue(all(P % d for d in range(2, r + 1)))


class Correctness(unittest.TestCase):
    def test_exhaustive_01(self):
        for n in range(0, 4):
            for bits in range(1 << (n * n)):
                A = tuple(tuple((bits >> (i * n + j)) & 1 for j in range(n)) for i in range(n))
                d = leibniz(A)
                self.assertEqual(COF.det_cofactor(A), d)
                self.assertEqual(GAU.det_gaussian(A), d)

    def test_seeded(self):
        for n in range(0, 7):
            for t in range(6):
                A = rand_matrix(n, random.Random(f"proofs-det|{n}|{t}"), zero_prob=t / 8)
                d = leibniz(A)
                self.assertEqual(COF.det_cofactor(A), d)
                self.assertEqual(GAU.det_gaussian(A), d)


class CofactorCounts(unittest.TestCase):
    def test_calls_and_operations(self):
        original = COF._expand
        calls = [0]

        def counting_expand(A, r, cols):
            calls[0] += 1
            return original(A, r, cols)

        try:
            COF._expand = counting_expand
            for n in range(0, 9):
                A = tuple(tuple(C(x) for x in row) for row in rand_matrix(n, random.Random(f"proofs-det-c|{n}")))
                calls[0] = 0
                reset()
                COF.det_cofactor(A)
                f = math.factorial(n)
                nodes = sum(f // math.factorial(k) for k in range(n + 1))
                self.assertEqual(calls[0], nodes)
                if n >= 1:
                    self.assertEqual(nodes, math.floor(math.e * f) if n <= 15 else nodes)
                self.assertEqual(OPS["mul"], nodes - 1)
                self.assertEqual(OPS["add"], nodes - 1)
                self.assertEqual(OPS["mod"], (nodes - 1) + (nodes - f) if n else 0)
        finally:
            COF._expand = original


class GaussianCounts(unittest.TestCase):
    def test_non_singular(self):
        for n in range(0, 41):
            rng = random.Random(f"proofs-det-g|{n}")
            A = rand_matrix(n, rng, zero_prob=0.2 if n % 2 else 0.0)
            if n and GAU.det_gaussian(A) == 0:
                self.fail(f"seeded matrix is singular at n={n}")
            reset()
            GAU.det_gaussian(tuple(tuple(C(x) for x in row) for row in A))
            self.assertEqual(OPS["inv"], n)
            mult_sub = (n ** 3 - n) // 3
            self.assertEqual(OPS["mul"], n * (n + 1) * (2 * n + 1) // 6, n)
            self.assertEqual(OPS["add"], mult_sub, n)

    def test_singular_stops_early(self):
        for n in range(2, 16):
            rng = random.Random(f"proofs-det-s|{n}")
            A = [list(r) for r in rand_matrix(n, rng)]
            i, j = rng.sample(range(n), 2)
            A[i] = [(2 * x) % P for x in A[j]]                     # two proportional rows
            A = tuple(tuple(r) for r in A)
            self.assertEqual(GAU.det_gaussian(A), 0)
            self.assertEqual(leibniz(A) if n <= 6 else 0, 0)
            reset()
            GAU.det_gaussian(tuple(tuple(C(x) for x in row) for row in A))
            self.assertLessEqual(OPS["add"], (n ** 3 - n) // 3)
            self.assertLess(OPS["inv"], n)


class HarnessOracle(unittest.TestCase):
    def test_known_determinants(self):
        for n in range(0, 7):
            for t in range(8):
                A = H.generate(n, random.Random(f"proofs-det-h|{n}|{t}"))
                self.assertEqual(H._KNOWN[A], leibniz(A))

    def test_invertible_count_formula(self):
        # The number of invertible n x n matrices over GF(q) is prod_{i=0..n-1} (q^n - q^i).
        for q in (2, 3, 5):
            for n in range(1, 4 if q <= 3 else 3):
                count = 0
                for entries in itertools.product(range(q), repeat=n * n):
                    A = tuple(tuple(entries[i * n:(i + 1) * n]) for i in range(n))
                    count += leibniz(A, q) != 0
                self.assertEqual(count, math.prod(q ** n - q ** i for i in range(n)))


class WorkingMemory(unittest.TestCase):
    @staticmethod
    def _peak(fn, arg):
        tracemalloc.start()
        tracemalloc.reset_peak()
        base = tracemalloc.get_traced_memory()[0]
        fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
        tracemalloc.stop()
        return peak

    def test_quadratic_upper_bounds(self):
        # Upper bounds only (free lists hide some small allocations): 100 n^2 + 8192 bytes.
        for n in range(1, 61, 7):
            A = rand_matrix(n, random.Random(n))
            self.assertLessEqual(self._peak(GAU.det_gaussian, A), 100 * n * n + 8192, n)
        for n in range(1, 9):
            A = rand_matrix(n, random.Random(n))
            self.assertLessEqual(self._peak(COF.det_cofactor, A), 100 * n * n + 8192, n)


if __name__ == "__main__":
    unittest.main()
