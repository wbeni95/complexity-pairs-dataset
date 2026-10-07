"""Checks for pairs/global-min-cut-brute-vs-stoer-wagner/PROOFS.md, sections 3-7 (problem facts, correctness,
the cut-of-the-phase lemma, space, sizes of the numbers). The exact counts (sections 1-2) are checked by the
experiment scripts named in PROOFS.md.

Run:  python -m unittest tests.test_proofs_mincut   (a few seconds)
"""
import importlib.util
import random
import sys
import tracemalloc
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "global-min-cut-brute-vs-stoer-wagner"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "tpmc_harness")
BF = _load(ENTRY / "implementations" / "brute_force.py", "tpmc_bf").min_cut_brute_force
SW = _load(ENTRY / "implementations" / "stoer_wagner.py", "tpmc_sw").min_cut_stoer_wagner


def cut_weight(W, S):
    n = len(W)
    return sum(W[u][v] for u in S for v in range(n) if v not in S)


def min_cut_enumeration(W):
    """Minimum over all non-empty proper subsets S containing vertex 0 (a direct sum, written here)."""
    n = len(W)
    if n < 2:
        return None
    best = None
    for mask in range(1 << (n - 1)):
        S = {0} | {v for v in range(1, n) if mask >> (v - 1) & 1}
        if len(S) == n:
            continue
        w = cut_weight(W, S)
        best = w if best is None else min(best, w)
    return best


def min_st_cut(W, s, t):
    n = len(W)
    others = [v for v in range(n) if v not in (s, t)]
    best = None
    for mask in range(1 << len(others)):
        S = {s} | {v for i, v in enumerate(others) if mask >> i & 1}
        w = cut_weight(W, S)
        best = w if best is None else min(best, w)
    return best


def random_matrix(n, rng, p_zero=0.3, hi=9):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = 0 if rng.random() < p_zero else rng.randint(1, hi)
    return W


class Correctness(unittest.TestCase):
    def test_both_equal_enumeration(self):
        count = 0
        for n in range(0, 11):
            for trial in range(12):
                W = H.generate(n, random.Random(f"tp-mincut-{n}-{trial}"))
                ref = min_cut_enumeration(W)
                self.assertEqual(BF(W), ref)
                self.assertEqual(SW(W), ref)
                count += 1
        self.assertEqual(count, 132)


class CutOfThePhase(unittest.TestCase):
    """Lemma P on a separate implementation of one phase with random tie-breaking among maximum keys."""

    @staticmethod
    def phase(W, rng):
        n = len(W)
        a = rng.randrange(n)
        A = [a]
        rest = [v for v in range(n) if v != a]
        key = {v: W[a][v] for v in rest}
        while rest:
            top = max(key[v] for v in rest)
            sel = rng.choice([v for v in rest if key[v] == top])
            rest.remove(sel)
            A.append(sel)
            for v in rest:
                key[v] += W[sel][v]
        s, t = A[-2], A[-1]
        return s, t, sum(W[t][v] for v in range(n) if v != t)

    def test_cut_of_the_phase_is_a_minimum_st_cut(self):
        count = 0
        for n in range(2, 9):
            for trial in range(30):
                rng = random.Random(f"tp-mincut-phase-{n}-{trial}")
                W = random_matrix(n, rng, p_zero=rng.choice((0.0, 0.3, 0.6)), hi=rng.choice((1, 3, 9)))
                s, t, c = self.phase(W, rng)
                self.assertEqual(c, min_st_cut(W, s, t))
                count += 1
        self.assertEqual(count, 210)


class ProblemFacts(unittest.TestCase):
    def test_disconnected_graphs_have_answer_zero(self):
        for trial in range(60):
            rng = random.Random(f"tp-mincut-disc-{trial}")
            n = rng.randint(2, 12)
            k = rng.randint(1, n - 1)
            side = list(range(n))
            rng.shuffle(side)
            part = set(side[:k])
            W = random_matrix(n, rng, p_zero=0.2)
            for u in range(n):
                for v in range(n):
                    if (u in part) != (v in part):
                        W[u][v] = 0
            self.assertEqual(BF(W), 0)
            self.assertEqual(SW(W), 0)

    def test_diagonal_is_ignored(self):
        for trial in range(60):
            rng = random.Random(f"tp-mincut-diag-{trial}")
            n = rng.randint(2, 10)
            W = random_matrix(n, rng)
            D = [row[:] for row in W]
            for v in range(n):
                D[v][v] = rng.randint(1, 50)
            self.assertEqual(BF(D), BF(W))
            self.assertEqual(SW(D), SW(W))


class Tracking:
    """Integer weight that records the largest value produced by an addition."""
    largest = 0
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, Tracking) else x

    def __add__(self, other):
        r = self.v + self._val(other)
        Tracking.largest = max(Tracking.largest, r)
        return Tracking(r)

    __radd__ = __add__

    def __lt__(self, other):
        return self.v < self._val(other)

    def __gt__(self, other):
        return self.v > self._val(other)


class NumberSizes(unittest.TestCase):
    def test_every_value_is_at_most_n2_B_over_4(self):
        count = 0
        for n in list(range(2, 13)) + [16, 20, 24]:
            for trial in range(6) if n <= 12 else range(12):
                W = H.generate(n, random.Random(f"tp-mincut-size-{n}-{trial}"))
                B = max(max(row) for row in W)
                T = tuple(tuple(Tracking(x) for x in row) for row in W)
                fns = (BF, SW) if n <= 12 else (SW,)
                for fn in fns:
                    Tracking.largest = 0
                    fn(T)
                    self.assertLessEqual(4 * Tracking.largest, n * n * B)
                count += 1
        self.assertEqual(count, 102)


class Space(unittest.TestCase):
    @staticmethod
    def peak(fn, W):
        tracemalloc.start()
        fn(W)
        _, p = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return p

    def test_brute_force_linear_space(self):
        p8 = self.peak(BF, random_matrix(8, random.Random("tp-mincut-space-8")))
        p12 = self.peak(BF, random_matrix(12, random.Random("tp-mincut-space-12")))
        self.assertLess(p12 / p8, 2.0, (p8, p12))

    def test_stoer_wagner_quadratic_space(self):
        sizes = (32, 64, 128)
        peaks = [self.peak(SW, random_matrix(n, random.Random(f"tp-mincut-space-{n}"))) for n in sizes]
        # measured 13568, 43432, 152912 bytes: ratios 3.2 and 3.5, approaching 4 (the n^2 working copy)
        for a, b in zip(peaks, peaks[1:]):
            self.assertTrue(2.5 < b / a < 5.0, peaks)
        for n, p in zip(sizes, peaks):
            self.assertLess(p / (n * n), 16, peaks)


if __name__ == "__main__":
    unittest.main()
