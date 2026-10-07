"""Checks for pairs/spanning-tree-count-enumeration-vs-kirchhoff/PROOFS.md, sections 3-7 (correctness, the
matrix-tree theorem and Lemma T, no row swap on reduced Laplacians, union-find heights, sizes of the numbers, space).
The exact counts (sections 1-2) are checked by the experiment scripts named in PROOFS.md.

The implementations are not modified: the zero-pivot search is observed by replacing the module-level name `next`
of the Kirchhoff module with a counting wrapper.

Run:  python -m unittest tests.test_proofs_stc   (a few seconds)
"""
import builtins
import importlib.util
import math
import random
import sys
import tracemalloc
import unittest
from fractions import Fraction
from itertools import combinations
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "spanning-tree-count-enumeration-vs-kirchhoff"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


EN_MOD = _load(ENTRY / "implementations" / "enumeration.py", "tpstc_enum")
KB_MOD = _load(ENTRY / "implementations" / "kirchhoff_bareiss.py", "tpstc_kirch")
ENUM = EN_MOD.count_spanning_trees_enumeration
KIRCH = KB_MOD.count_spanning_trees_kirchhoff


def random_graph(n, rng, p=None, connected=None):
    while True:
        q = p if p is not None else rng.choice((0.2, 0.5, 0.8))
        A = [[0] * n for _ in range(n)]
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < q:
                    A[u][v] = A[v][u] = 1
        if connected is None or is_connected(A) == connected:
            return tuple(tuple(r) for r in A)


def is_connected(A):
    n = len(A)
    if n == 0:
        return True
    seen, stack = {0}, [0]
    while stack:
        x = stack.pop()
        for y in range(n):
            if A[x][y] and y not in seen:
                seen.add(y)
                stack.append(y)
    return len(seen) == n


def edges_of(A):
    n = len(A)
    return [(u, v) for u in range(n) for v in range(u + 1, n) if A[u][v]]


def tau_by_subsets(A):
    n = len(A)
    E = edges_of(A)
    count = 0
    for S in combinations(E, n - 1):
        B = [[0] * n for _ in range(n)]
        for u, v in S:
            B[u][v] = B[v][u] = 1
        if is_connected(B):
            count += 1
    return count


def det_fraction(M):
    M = [[Fraction(x) for x in row] for row in M]
    n = len(M)
    det = Fraction(1)
    for k in range(n):
        piv = next((r for r in range(k, n) if M[r][k] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != k:
            M[k], M[piv] = M[piv], M[k]
            det = -det
        det *= M[k][k]
        for i in range(k + 1, n):
            f = M[i][k] / M[k][k]
            for j in range(k, n):
                M[i][j] -= f * M[k][j]
    return det


def cofactor(A, r, c=None):
    """(-1)^(r+c) det of the Laplacian without row r and column c (c = r by default)."""
    n = len(A)
    c = r if c is None else c
    rows = [i for i in range(n) if i != r]
    cols = [j for j in range(n) if j != c]
    sign = -1 if (r + c) % 2 else 1
    return sign * det_fraction([[sum(A[i]) if i == j else -A[i][j] for j in cols] for i in rows])


class MatrixTree(unittest.TestCase):
    def test_implementations_and_every_cofactor(self):
        count = 0
        for n in range(1, 8):
            for trial in range(13 if n > 1 else 6):
                A = random_graph(n, random.Random(f"tp-stc-{n}-{trial}"))
                ref = tau_by_subsets(A)
                self.assertEqual(ENUM(A), ref)
                self.assertEqual(KIRCH(A), ref)
                for r in range(n):
                    for c in range(n):
                        self.assertEqual(cofactor(A, r, c), ref)
                count += 1
        self.assertEqual(count, 84)

    def test_lemma_T(self):
        for trial in range(30):
            rng = random.Random(f"tp-stc-lemmaT-{trial}")
            n = rng.randint(2, 6)
            A = random_graph(n, rng)
            E = edges_of(A)
            r = rng.randrange(n)
            for S in combinations(E, n - 1):
                B = [[0] * (n - 1) for _ in range(n)]
                for col, (u, v) in enumerate(S):
                    B[u][col] = 1
                    B[v][col] = -1
                Br = [B[i] for i in range(n) if i != r]
                d = det_fraction(Br)
                G = [[0] * n for _ in range(n)]
                for u, v in S:
                    G[u][v] = G[v][u] = 1
                self.assertEqual(abs(d), 1 if is_connected(G) else 0)


class CountingNext:
    def __init__(self):
        self.calls = 0
        self.found = 0

    def __call__(self, it, *default):
        self.calls += 1
        r = builtins.next(it, *default)
        if r is not None:
            self.found += 1
        return r


class NoSwap(unittest.TestCase):
    def test_zero_pivot_search(self):
        counter = CountingNext()
        KB_MOD.next = counter
        try:
            for trial in range(200):
                rng = random.Random(f"tp-stc-noswap-c-{trial}")
                A = random_graph(rng.randint(2, 20), rng, connected=True)
                counter.calls = counter.found = 0
                self.assertGreater(KIRCH(A), 0)
                self.assertEqual(counter.calls, 0)
            entered = 0
            for trial in range(200):
                rng = random.Random(f"tp-stc-noswap-d-{trial}")
                A = random_graph(rng.randint(2, 20), rng, p=rng.choice((0.1, 0.2, 0.3)), connected=False)
                counter.calls = counter.found = 0
                self.assertEqual(KIRCH(A), 0)
                self.assertLessEqual(counter.calls, 1)
                self.assertEqual(counter.found, 0)
                entered += counter.calls
            self.assertEqual(entered, 162)          # graphs on which the zero-pivot branch is reached
        finally:
            del KB_MOD.next


class UnionFind(unittest.TestCase):
    def test_height_at_most_log2_n(self):
        for trial in range(200):
            rng = random.Random(f"tp-stc-uf-{trial}")
            n = rng.randint(2, 64)
            parent = list(range(n))
            size = [1] * n
            for _ in range(3 * n):
                u, v = rng.randrange(n), rng.randrange(n)
                ru, rv = EN_MOD._find(parent, u), EN_MOD._find(parent, v)
                if ru == rv:
                    continue
                if size[ru] < size[rv]:
                    ru, rv = rv, ru
                parent[rv] = ru
                size[ru] += size[rv]
                for x in range(n):
                    depth, y = 0, x
                    while parent[y] != y:
                        y = parent[y]
                        depth += 1
                    self.assertLessEqual(2 ** depth, n)


class Track:
    big_mid = 0
    big_val = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _x(o):
        return o.v if isinstance(o, Track) else o

    def _mid(self, r):
        Track.big_mid = max(Track.big_mid, abs(r))
        return Track(r)

    def __add__(self, o):
        return Track(self.v + self._x(o))

    __radd__ = __add__

    def __mul__(self, o):
        return self._mid(self.v * self._x(o))

    __rmul__ = __mul__

    def __sub__(self, o):
        return self._mid(self.v - self._x(o))

    def __rsub__(self, o):
        return self._mid(self._x(o) - self.v)

    def __floordiv__(self, o):
        r = self.v // self._x(o)
        Track.big_val = max(Track.big_val, abs(r))
        return Track(r)

    def __rfloordiv__(self, o):
        r = self._x(o) // self.v
        Track.big_val = max(Track.big_val, abs(r))
        return Track(r)

    def __neg__(self):
        return Track(-self.v)

    def __eq__(self, o):
        return self.v == self._x(o)

    def __ne__(self, o):
        return self.v != self._x(o)

    def __bool__(self):
        return self.v != 0

    __hash__ = None


class NumberSizes(unittest.TestCase):
    def _check(self, A):
        n = len(A)
        Track.big_mid = Track.big_val = 0
        out = KIRCH(tuple(tuple(Track(x) for x in r) for r in A))
        val = out.v if isinstance(out, Track) else out
        self.assertEqual(val, KIRCH(A))
        self.assertLessEqual(val, n ** (n - 2) if n >= 2 else 1)
        self.assertLess(Track.big_val, n ** (n - 1))
        self.assertLess(Track.big_mid, 2 * n ** (2 * (n - 1)))

    def test_complete_and_random(self):
        for n in range(2, 31):
            self._check(tuple(tuple(int(i != j) for j in range(n)) for i in range(n)))
        for trial in range(60):
            rng = random.Random(f"tp-stc-size-{trial}")
            self._check(random_graph(rng.randint(2, 25), rng))


class Space(unittest.TestCase):
    @staticmethod
    def peak(fn, A):
        tracemalloc.start()
        fn(A)
        _, p = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return p

    def test_kirchhoff_peak(self):
        peaks = [self.peak(KIRCH, tuple(tuple(int(i != j) for j in range(n)) for i in range(n))) for n in (16, 32, 64)]
        for a, b in zip(peaks, peaks[1:]):
            self.assertTrue(3.0 < b / a < 8.0, peaks)

    def test_enumeration_linear_peak(self):
        peaks = []
        for n in (10, 20, 40):
            A = [[0] * n for _ in range(n)]
            for u in range(n):
                A[u][(u + 1) % n] = A[(u + 1) % n][u] = 1
            A[0][n // 2] = A[n // 2][0] = 1
            A[1][n // 3 + 1] = A[n // 3 + 1][1] = 1
            peaks.append(self.peak(ENUM, tuple(tuple(r) for r in A)))
        for a, b in zip(peaks, peaks[1:]):
            self.assertLess(b / a, 3.0, peaks)


if __name__ == "__main__":
    unittest.main()
