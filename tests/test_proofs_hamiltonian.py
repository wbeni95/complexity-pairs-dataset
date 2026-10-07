"""Deterministic checks for pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion/PROOFS.md,
sections 4-10 (a few seconds; the exact counts of sections 1-3 are checked by the scripts named there).

Ranges: the three algorithms against an independent count over successor permutations, on every digraph with
n <= 4 (random diagonal bits) and on seeded digraphs n = 5..7 (sections 4-6); integer arc weights, n <= 6 (5.3);
undirected graphs, n = 3..7 (7); integer sizes on complete digraphs, n <= 8 (8); the oracle's closed forms, the
depth-first node bound and the necessary conditions, n <= 9 (10); tracemalloc peaks (8).
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
ENTRY = REPO / "pairs" / "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_ham_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "proofs_ham_en").count_hamiltonian_cycles_enumeration
IE_MOD = _load(ENTRY / "implementations" / "inclusion_exclusion.py", "proofs_ham_ie")
HK_MOD = _load(ENTRY / "implementations" / "held_karp_counting.py", "proofs_ham_hk")
IE = IE_MOD.count_hamiltonian_cycles_inclusion_exclusion
HK = HK_MOD.count_hamiltonian_cycles_held_karp


def tup(a):
    return tuple(tuple(r) for r in a)


def cycles_by_successors(adj, weighted=False):
    """Independent oracle: sum over the successor permutations that form one n-cycle (n >= 2) of the product of
    the arc entries (or of 1 if all entries are non-zero, when weighted is False)."""
    n = len(adj)
    if n <= 1:
        return 0
    total = 0
    for succ in itertools.permutations(range(n)):
        v, length = 0, 0
        while True:
            v = succ[v]
            length += 1
            if v == 0:
                break
        if length != n:
            continue
        w = 1
        for u in range(n):
            w *= adj[u][succ[u]] if weighted else (1 if adj[u][succ[u]] else 0)
        total += w
    return total


def random_digraph(n, rng, p, diag=True):
    a = [[1 if u != v and rng.random() < p else 0 for v in range(n)] for u in range(n)]
    if diag:
        for v in range(n):
            a[v][v] = rng.randint(0, 1)
    return a


class Correctness(unittest.TestCase):
    def test_every_digraph_up_to_four_vertices(self):
        rng = random.Random("proofs-ham-diag")
        for n in range(0, 5):
            pairs = [(u, v) for u in range(n) for v in range(n) if u != v]
            for bits in range(1 << len(pairs)):
                a = [[rng.randint(0, 1) if u == v else 0 for v in range(n)] for u in range(n)]
                for i, (u, v) in enumerate(pairs):
                    a[u][v] = bits >> i & 1
                g = tup(a)
                c = cycles_by_successors(g)
                self.assertEqual((EN(g), IE(g), HK(g)), (c, c, c), g)

    def test_seeded_digraphs(self):
        for n in range(5, 8):
            for t in range(10):
                g = tup(random_digraph(n, random.Random(f"proofs-ham|{n}|{t}"), (0.3, 0.5, 0.7, 0.9)[t % 4]))
                c = cycles_by_successors(g)
                self.assertEqual((EN(g), IE(g), HK(g)), (c, c, c))

    def test_integer_weights(self):
        # PROOFS.md section 5.3: with integer entries the two DPs return the arc-weighted sum over the Hamiltonian
        # cycles; the enumeration counts the cycles whose arcs are all non-zero.
        for n in range(2, 7):
            for t in range(6):
                rng = random.Random(f"proofs-ham-w|{n}|{t}")
                a = tup([[rng.randint(0, 3) for _ in range(n)] for _ in range(n)])
                w = cycles_by_successors(a, weighted=True)
                self.assertEqual(IE(a), w)
                self.assertEqual(HK(a), w)
                self.assertEqual(EN(a), cycles_by_successors(a))


class Undirected(unittest.TestCase):
    def test_twice_the_undirected_count(self):
        for n in range(3, 8):
            for t in range(6):
                rng = random.Random(f"proofs-ham-u|{n}|{t}")
                a = H._random_graph(n, 0.6, rng)
                undirected = set()
                for order in itertools.permutations(range(1, n)):
                    cyc = (0,) + order
                    if all(a[cyc[i]][cyc[(i + 1) % n]] for i in range(n)):
                        undirected.add(frozenset(frozenset((cyc[i], cyc[(i + 1) % n])) for i in range(n)))
                self.assertEqual(HK(tup(a)), 2 * len(undirected))
                self.assertEqual(IE(tup(a)), 2 * len(undirected))


class IntegerSizes(unittest.TestCase):
    def test_largest_intermediate_values(self):
        # PROOFS.md section 8, on the complete digraph (entrywise the largest 0/1 input).
        for n in range(2, 9):
            g = tup(H.complete_digraph(n))
            seen = {"acc": 0, "total": 0}

            def local(frame, event, arg):
                if event == "line":
                    for name in ("acc", "total"):
                        v = frame.f_locals.get(name)
                        if isinstance(v, int):
                            seen[name] = max(seen[name], abs(v))
                return local

            sys.settrace(lambda f, e, a: local if f.f_code is IE.__code__ else None)
            try:
                IE(g)
            finally:
                sys.settrace(None)
            self.assertLessEqual(seen["acc"], (n - 1) ** n)
            self.assertLessEqual(seen["total"], 2 ** (n - 1) * (n - 1) ** n)
            seen = {"acc": 0, "total": 0}
            sys.settrace(lambda f, e, a: local if f.f_code is HK.__code__ else None)
            try:
                HK(g)
            finally:
                sys.settrace(None)
            self.assertLessEqual(seen["acc"], math.factorial(max(n - 2, 0)))
            self.assertLessEqual(seen["total"], math.factorial(n - 1))

    def test_table_sizes_quoted_in_notes(self):
        self.assertEqual((10 - 1) * 2 ** (10 - 1), 4608)
        self.assertEqual((20 - 1) * 2 ** (20 - 1), 9961472)


class OracleFacts(unittest.TestCase):
    def test_closed_forms(self):
        for n in range(3, 10):
            k = H.complete_digraph(n)
            self.assertEqual(HK(tup(k)), math.factorial(n - 1))
            k[0][1] = 0
            self.assertEqual(HK(tup(k)), math.factorial(n - 1) - math.factorial(n - 2))
            rng = random.Random(f"proofs-ham-cf|{n}")
            perm = list(range(n))
            rng.shuffle(perm)
            single = [[0] * n for _ in range(n)]
            for i in range(n):
                single[perm[i]][perm[(i + 1) % n]] = 1
            self.assertEqual(HK(tup(single)), 1)
            self.assertEqual(H.closed_form(tup(single))[0], 1)
            und = [[0] * n for _ in range(n)]
            for i in range(n):
                und[perm[i]][perm[(i + 1) % n]] = und[perm[(i + 1) % n]][perm[i]] = 1
            self.assertEqual(HK(tup(und)), 2)
            self.assertEqual(H.closed_form(tup(und))[0], 2)
            for s in range(1, n):
                if 2 * s != n:
                    self.assertEqual(HK(tup(H.complete_bipartite(s, n - s))), 0)
        for m in range(2, 5):
            g = tup(H.complete_bipartite(m, m))
            self.assertEqual(HK(g), math.factorial(m) * math.factorial(m - 1))
            self.assertEqual(H.closed_form(g)[0], math.factorial(m) * math.factorial(m - 1))

    def test_dfs_node_bound(self):
        # PROOFS.md section 10: the depth-first count visits one node per simple path from vertex 0, at most
        # sum_{i=0..n-1} (n-1)!/i!, attained by the complete digraph (986 410 at n = 10).
        bound = lambda n: sum(math.factorial(n - 1) // math.factorial(i) for i in range(n))
        self.assertEqual(bound(10), 986410)
        for n in range(2, 9):
            k = tup(H.complete_digraph(n))
            self.assertIsNotNone(H.dfs_count(k, bound(n)))
            self.assertIsNone(H.dfs_count(k, bound(n) - 1))
            for t in range(4):
                g = tup(random_digraph(n, random.Random(f"proofs-ham-dfs|{n}|{t}"), 0.6))
                self.assertEqual(H.dfs_count(g, bound(n)), HK(g))

    def test_necessary_conditions(self):
        for n in range(3, 9):
            for t in range(6):
                rng = random.Random(f"proofs-ham-nc|{n}|{t}")
                g = tup(random_digraph(n, rng, 0.5))
                c = HK(g)
                succ, pred = H._arc_lists(g)
                self.assertLessEqual(c, math.prod(len(s) for s in succ))
                self.assertLessEqual(c, math.prod(len(p) for p in pred))
                self.assertEqual(HK(tup(H._random_graph(n, 0.6, rng))) % 2, 0)


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
        for n in range(8, 15):
            g = tup(H.complete_digraph(n))
            per = self._peak(HK, g) / ((n - 1) * 2 ** (n - 1))
            self.assertTrue(8 <= per <= 200, (n, per))                   # Theta(n 2^n) table entries
        for n in range(4, 11):
            g = tup(H.complete_digraph(n))
            self.assertLessEqual(self._peak(IE, g), 4096 + 256 * n, n)    # no growth with 2^n


if __name__ == "__main__":
    unittest.main()
