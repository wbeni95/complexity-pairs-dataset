"""Checks for pairs/minimum-spanning-tree-brute-vs-kruskal/PROOFS.md, sections 4-8 (correctness, the binomial
estimate, Kruskal's decision-tree lower bound, the adversary instance, space). The exact counts (sections 1-3) are
checked by the experiment scripts named in PROOFS.md.

Run:  python -m unittest tests.test_proofs_mst   (a few seconds)
"""
import importlib.util
import math
import random
import sys
import tracemalloc
import unittest
from itertools import permutations, product
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "minimum-spanning-tree-brute-vs-kruskal"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "tpmst_harness")
BRUTE = _load(ENTRY / "implementations" / "brute_force.py", "tpmst_brute").mst_brute
KRUSKAL = _load(ENTRY / "implementations" / "kruskal.py", "tpmst_kruskal").mst_kruskal
PRIM = _load(ENTRY / "implementations" / "prim.py", "tpmst_prim").mst_prim


def matrix(n, rng, hi):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = rng.randint(1, hi)
    return tuple(tuple(r) for r in W)


def prufer_trees(n):
    """All n^(n-2) labelled trees on n >= 2 vertices, decoded from Pruefer sequences."""
    if n == 2:
        yield [(0, 1)]
        return
    for seq in product(range(n), repeat=n - 2):
        degree = [1] * n
        for x in seq:
            degree[x] += 1
        edges = []
        for x in seq:
            leaf = min(v for v in range(n) if degree[v] == 1)
            edges.append((leaf, x))
            degree[leaf] -= 1
            degree[x] -= 1
        u, v = [w for w in range(n) if degree[w] == 1]
        edges.append((u, v))
        yield edges


def mst_by_all_trees(W):
    n = len(W)
    if n <= 1:
        return 0
    return min(sum(W[u][v] for u, v in t) for t in prufer_trees(n))


class Correctness(unittest.TestCase):
    def test_three_implementations_equal_minimum_over_all_trees(self):
        count = 0
        for n in range(1, 8):
            for trial in range(10):
                rng = random.Random(f"tp-mst-{n}-{trial}")
                W = matrix(n, rng, rng.choice((3, 100)))
                ref = mst_by_all_trees(W)
                if n <= 6:
                    self.assertEqual(BRUTE(W), ref)
                self.assertEqual(KRUSKAL(W), ref)
                self.assertEqual(PRIM(W), ref)
                count += 1
        self.assertEqual(count, 70)

    def test_pruefer_lists_cayley_many_trees(self):
        for n in range(2, 8):
            trees = list(prufer_trees(n))
            self.assertEqual(len(trees), n ** (n - 2))
            self.assertEqual(len({frozenset(frozenset(e) for e in t) for t in trees}), n ** (n - 2))


class Binomial(unittest.TestCase):
    def test_bounds(self):
        for n in range(2, 61):
            M, k = n * (n - 1) // 2, n - 1
            c = math.comb(M, k)
            upper = (math.e * n / 2) ** (n - 1)
            lower = 2 / (math.e * n ** 1.5) * upper
            self.assertLessEqual(c, upper * (1 + 1e-12))
            self.assertGreaterEqual(c, lower * (1 - 1e-12))
            self.assertGreaterEqual(c, (n / 2) ** (n - 1) * (1 - 1e-12))


class KruskalLowerBound(unittest.TestCase):
    def test_some_weight_order_needs_log2_m_factorial_sort_comparisons(self):
        for n in (3, 4):
            m = n * (n - 1) // 2
            edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
            worst = 0
            for perm in permutations(range(1, m + 1)):
                W = [[0] * n for _ in range(n)]
                for (u, v), w in zip(edges, perm):
                    W[u][v] = W[v][u] = H.CountingWeight(w)
                H._ops = 0
                total = KRUSKAL(tuple(tuple(r) for r in W))
                # scanned keys = position of the (n-1)-th taken edge; replay the scan on plain ints
                order = sorted(edges, key=lambda e: perm[edges.index(e)])
                parent = list(range(n))

                def find(x):
                    while parent[x] != x:
                        x = parent[x]
                    return x

                taken = scanned = 0
                for u, v in order:
                    if taken == n - 1:
                        break
                    scanned += 1
                    ru, rv = find(u), find(v)
                    if ru != rv:
                        parent[ru] = rv
                        taken += 1
                sort_cmps = H._ops - 3 * m - scanned
                self.assertGreaterEqual(sort_cmps, 0)
                worst = max(worst, sort_cmps)
                self.assertEqual(total.v if hasattr(total, "v") else total, mst_by_all_trees(
                    [[x.v if hasattr(x, "v") else x for x in r] for r in W]))
            self.assertGreaterEqual(worst, math.ceil(math.log2(math.factorial(m))), (n, worst))


class AdversaryInstance(unittest.TestCase):
    def test_all_two_and_one_lowered_edge(self):
        for n in range(2, 9):
            base = [[0 if u == v else 2 for v in range(n)] for u in range(n)]
            impls = (BRUTE, KRUSKAL, PRIM) if n <= 6 else (KRUSKAL, PRIM)
            for fn in impls:
                self.assertEqual(fn(tuple(tuple(r) for r in base)), 2 * (n - 1))
            for u in range(n):
                for v in range(u + 1, n):
                    W = [r[:] for r in base]
                    W[u][v] = W[v][u] = 1
                    for fn in impls:
                        self.assertEqual(fn(tuple(tuple(r) for r in W)), 2 * n - 3)


class Space(unittest.TestCase):
    @staticmethod
    def peak(fn, W):
        tracemalloc.start()
        fn(W)
        _, p = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return p

    def test_kruskal_quadratic_prim_linear(self):
        sizes = (25, 50, 100)
        Ws = [matrix(n, random.Random(f"tp-mst-space-{n}"), 10 ** 9) for n in sizes]
        k = [self.peak(KRUSKAL, W) for W in Ws]
        p = [self.peak(PRIM, W) for W in Ws]
        for a, b in zip(k, k[1:]):
            self.assertTrue(2.5 < b / a < 5.0, k)
        for a, b in zip(p, p[1:]):
            self.assertLess(b / a, 2.6, p)


if __name__ == "__main__":
    unittest.main()
