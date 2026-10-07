"""Deterministic checks for pairs/permanent-naive-vs-ryser/PROOFS.md (about two seconds).

Ranges: correctness exhaustive over 0/1 matrices with n <= 3 and on seeded matrices up to n = 7 (section 1 and 2);
Gray-code lemma n <= 16 (2.2); exact operation counts naive n = 0..8, Ryser n = 1..12 (1.2, 2.4); integer sizes
(section 4); harness facts n = 0..8 (5.1-5.3); closed forms J_n and J_n - I (5.4); tracemalloc peaks (1.3, 2.5).
"""
import importlib.util
import itertools
import math
import random
import sys
import tracemalloc
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "permanent-naive-vs-ryser"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_perm_harness")
NAIVE = _load(ENTRY / "implementations" / "naive.py", "proofs_perm_naive").permanent_naive
RYSER = _load(ENTRY / "implementations" / "ryser.py", "proofs_perm_ryser").permanent_ryser

OPS = {"add": 0, "mul": 0, "neg": 0}
MAXABS = [0]


class Counted:
    """Integer that counts +, -, * and unary - with at least one Counted operand, and records the largest |value|."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v
        if abs(v) > MAXABS[0]:
            MAXABS[0] = abs(v)

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, Counted) else x

    def _op(self, kind, value):
        OPS[kind] += 1
        return Counted(value)

    def __add__(self, o):
        return self._op("add", self.v + self._val(o))

    def __radd__(self, o):
        return self._op("add", self._val(o) + self.v)

    def __sub__(self, o):
        return self._op("add", self.v - self._val(o))

    def __rsub__(self, o):
        return self._op("add", self._val(o) - self.v)

    def __mul__(self, o):
        return self._op("mul", self.v * self._val(o))

    def __rmul__(self, o):
        return self._op("mul", self._val(o) * self.v)

    def __neg__(self):
        return self._op("neg", -self.v)

    def __eq__(self, o):
        return self.v == self._val(o)

    __hash__ = None


def reset():
    for k in OPS:
        OPS[k] = 0
    MAXABS[0] = 0


def counted(A):
    return tuple(tuple(Counted(x) for x in row) for row in A)


def rand_matrix(n, rng, lo, hi):
    return tuple(tuple(rng.randint(lo, hi) for _ in range(n)) for _ in range(n))


def perm_by_rows(A, r=0, used=0):
    """Independent oracle: expansion along rows (no inclusion-exclusion, no permutation generator)."""
    n = len(A)
    if r == n:
        return 1
    return sum(A[r][c] * perm_by_rows(A, r + 1, used | (1 << c)) for c in range(n) if not used >> c & 1)


def ryser_direct(A):
    """Ryser's formula 2.1 over all subsets, without Gray code."""
    n = len(A)
    if n == 0:
        return 1
    total = 0
    for S in range(1 << n):
        prod = 1
        for i in range(n):
            prod *= sum(A[i][j] for j in range(n) if S >> j & 1)
        total += (-1) ** bin(S).count("1") * prod
    return (-1) ** n * total


def det_exact(A):
    n = len(A)
    M = [[Fraction(x) for x in row] for row in A]
    det = Fraction(1)
    for c in range(n):
        piv = next((r for r in range(c, n) if M[r][c] != 0), None)
        if piv is None:
            return 0
        if piv != c:
            M[c], M[piv] = M[piv], M[c]
            det = -det
        det *= M[c][c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    return int(det)


class Correctness(unittest.TestCase):
    def test_exhaustive_01_small(self):
        for n in range(0, 4):
            for bits in range(1 << (n * n)):
                A = tuple(tuple((bits >> (i * n + j)) & 1 for j in range(n)) for i in range(n))
                expected = perm_by_rows(A)
                self.assertEqual(NAIVE(A), expected)
                self.assertEqual(RYSER(A), expected)

    def test_seeded_signed(self):
        for n in range(0, 8):
            for t in range(5):
                A = rand_matrix(n, random.Random(f"proofs-perm|{n}|{t}"), -2, 3)
                expected = perm_by_rows(A)
                self.assertEqual(ryser_direct(A), expected)
                self.assertEqual(NAIVE(A), expected)
                self.assertEqual(RYSER(A), expected)


class GrayCode(unittest.TestCase):
    def test_lowest_bit_rule_gives_reflected_code(self):
        for n in range(0, 17):
            g, seen = 0, {0}
            for k in range(1, 1 << n):
                v = (k & -k).bit_length() - 1
                g ^= 1 << v
                self.assertEqual(g, k ^ (k >> 1))
                seen.add(g)
            self.assertEqual(len(seen), 1 << n)


class Counts(unittest.TestCase):
    def test_naive_counts(self):
        for n in range(0, 9):
            A = counted(rand_matrix(n, random.Random(f"proofs-perm-c|{n}"), 1, 4))
            reset()
            NAIVE(A)
            f = math.factorial(n)
            expected = {"add": f, "mul": n * f, "neg": 0} if n else {"add": 0, "mul": 0, "neg": 0}
            self.assertEqual(OPS, expected, n)

    def test_ryser_counts(self):
        for n in range(1, 13):
            A = counted(rand_matrix(n, random.Random(f"proofs-perm-c|{n}"), -2, 3))
            reset()
            RYSER(A)
            steps = 2 ** n - 1
            self.assertEqual(OPS, {"add": (n + 1) * steps, "mul": n * steps, "neg": 2 ** (n - 1) + (n % 2)}, n)

    def test_value_sizes(self):
        M = 4
        for n in range(1, 8):
            A = rand_matrix(n, random.Random(f"proofs-perm-s|{n}"), -M, M)
            reset()
            NAIVE(counted(A))
            self.assertLessEqual(MAXABS[0], math.factorial(n) * M ** n)
        for n in range(1, 11):
            A = rand_matrix(n, random.Random(f"proofs-perm-s|{n}"), -M, M)
            reset()
            RYSER(counted(A))
            self.assertLessEqual(MAXABS[0], (2 ** n - 1) * (n * M) ** n)
            self.assertLessEqual(MAXABS[0].bit_length(), n * math.log2(2 * n * M) + 1)


class Harness(unittest.TestCase):
    def test_parity_and_gf2_elimination(self):
        for n in range(0, 9):
            for t in range(6):
                A = rand_matrix(n, random.Random(f"proofs-perm-h|{n}|{t}"), -2, 3)
                d = det_exact(A)
                self.assertEqual(H._det_mod2(A), d % 2)
                self.assertEqual(perm_by_rows(A) % 2, d % 2)

    def test_subset_dp_oracle_and_cost(self):
        for n in range(0, 8):
            A = rand_matrix(n, random.Random(f"proofs-perm-dp|{n}"), -2, 3)
            self.assertEqual(H._subset_dp(A), NAIVE(A))
            reset()
            H._subset_dp(counted(A))
            self.assertEqual(OPS["mul"], n * 2 ** (n - 1) if n else 0)
            self.assertEqual(OPS["add"], n * 2 ** (n - 1) if n else 0)


class ClosedForms(unittest.TestCase):
    def test_all_ones_and_derangements(self):
        D = [1, 0]
        for n in range(2, 13):
            D.append((n - 1) * (D[-1] + D[-2]))
        for n in range(0, 13):
            J = tuple(tuple(1 for _ in range(n)) for _ in range(n))
            JI = tuple(tuple(0 if i == j else 1 for j in range(n)) for i in range(n))
            self.assertEqual(RYSER(J), math.factorial(n))
            self.assertEqual(RYSER(JI), D[n])
            if n <= 8:
                self.assertEqual(NAIVE(J), math.factorial(n))
                self.assertEqual(NAIVE(JI), D[n])

    def test_no_row_operation_invariance(self):
        self.assertEqual(NAIVE(((1, 1), (1, 1))), 2)
        self.assertEqual(NAIVE(((1, 1), (0, 0))), 0)


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

    def test_peaks(self):
        # Upper bounds only: CPython's free lists reuse small tuples without a traced allocation.
        for n in range(1, 15):
            A = rand_matrix(n, random.Random(n * 100), 1, 4)
            p = self._peak(RYSER, A)
            self.assertLessEqual(p, 16 * n * n + 4096, n)
            if n <= 8:
                self.assertLessEqual(self._peak(NAIVE, A), 64 * n + 4096, n)


if __name__ == "__main__":
    unittest.main()
