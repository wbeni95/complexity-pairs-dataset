"""Checks for pairs/max-flow-edmonds-karp-vs-dinic/PROOFS.md (correctness, the bounds of Theorem F and Lemma A,
the phase bound of Theorem DI, space, and the bipartite-matching reduction).

The implementations are not modified. The number of breadth-first searches is counted by replacing the module-level
name `deque` of each implementation module with a counting subclass (each BFS creates exactly one deque).

Run:  python -m unittest tests.test_proofs_maxflow   (a few seconds)
"""
import collections
import importlib.util
import random
import sys
import tracemalloc
import unittest
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-flow-edmonds-karp-vs-dinic"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "tpmf_harness")
EK = _load(ENTRY / "implementations" / "edmonds_karp.py", "tpmf_ek")
DI = _load(ENTRY / "implementations" / "dinic.py", "tpmf_dinic")


class CountingDeque(collections.deque):
    made = 0

    def __init__(self, *args, **kwargs):
        CountingDeque.made += 1
        super().__init__(*args, **kwargs)


EK.deque = CountingDeque
DI.deque = CountingDeque


def bfs_passes(fn, network):
    CountingDeque.made = 0
    value = fn(network)
    return value, CountingDeque.made


def min_cut_enumeration(network):
    """Minimum s-t cut capacity over all vertex sets S with s in S, t not in S (written here, not the harness's)."""
    n, s, t, edges = network
    others = [v for v in range(n) if v != s and v != t]
    best = None
    for bits in product((0, 1), repeat=len(others)):
        S = {s} | {v for v, b in zip(others, bits) if b}
        cap = sum(c for u, v, c in edges if u in S and v not in S)
        best = cap if best is None else min(best, cap)
    return best


def v1_battery():
    """The validator's sizes with 6 instances each, from fixed seeds."""
    for n in (2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 14):
        for trial in range(6):
            yield H.generate(n, random.Random(f"tp-maxflow-{n}-{trial}"))


class Correctness(unittest.TestCase):
    def test_both_equal_min_cut(self):
        count = 0
        for n in range(2, 10):
            for trial in range(19):
                net = H.generate(n, random.Random(f"tp-maxflow-cut-{n}-{trial}"))
                ref = min_cut_enumeration(net)
                self.assertEqual(EK.max_flow_edmonds_karp(net), ref, net)
                self.assertEqual(DI.max_flow_dinic(net), ref, net)
                count += 1
        self.assertEqual(count, 152)


class FlowValueBounds(unittest.TestCase):
    def _check(self, net):
        n, s, t, edges = net
        E = len(edges)
        L = min(n - 1, E)
        F, ek_bfs = bfs_passes(EK.max_flow_edmonds_karp, net)
        F2, di_bfs = bfs_passes(DI.max_flow_dinic, net)
        self.assertEqual(F, F2)
        A = ek_bfs - 1                       # every EK iteration but the last augments once
        self.assertLessEqual(A, F)           # Theorem F(a)
        self.assertLessEqual(A, E * (L + 1))  # Lemma A
        phases = di_bfs                      # BFS passes, the final one included
        self.assertLessEqual(phases, F + 1)  # Theorem F(b)
        self.assertLessEqual(phases, L + 1)  # Theorem DI
        C = max((c for _, _, c in edges), default=0)
        outdeg = sum(1 for u, _, _ in edges if u == s)
        self.assertLessEqual(F, C * outdeg)  # Theorem F(c)
        return F

    def test_v1_battery(self):
        flows = [self._check(net) for net in v1_battery()]
        self.assertEqual(len(flows), 66)

    def test_generate_scaling(self):
        for n in (20, 40, 80):
            net = H.generate_scaling(n, random.Random(f"tp-maxflow-scaling-{n}"))
            F = self._check(net)
            s_out = sum(1 for u, _, _ in net[3] if u == net[1])
            self.assertLessEqual(s_out, n - 1)      # no parallel edges out of s
            self.assertLessEqual(F, 100 * (n - 1))


class Space(unittest.TestCase):
    def test_peak_per_vertex_plus_edge_is_bounded(self):
        for fn in (EK.max_flow_edmonds_karp, DI.max_flow_dinic):
            ratios = []
            for n in (40, 80, 160):
                net = H.generate_scaling(n, random.Random(f"tp-maxflow-space-{n}"))
                tracemalloc.start()
                fn(net)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                ratios.append(peak / (n + len(net[3])))
            # O(V + E): the peak per (V + E) stays bounded (about 100-115 bytes here); a peak of order V*(V + E)
            # would double it with every doubling of n
            self.assertLess(max(ratios), 200, ratios)
            self.assertLess(ratios[1] / ratios[0], 1.3, ratios)
            self.assertLess(ratios[2] / ratios[1], 1.3, ratios)


def max_matching_brute(X, Y, adj):
    best = 0

    def go(i, used, size):
        nonlocal best
        if size + (len(X) - i) <= best:
            return
        if i == len(X):
            best = max(best, size)
            return
        go(i + 1, used, size)
        for y in adj[X[i]]:
            if y not in used:
                go(i + 1, used | {y}, size + 1)

    go(0, frozenset(), 0)
    return best


class BipartiteMatching(unittest.TestCase):
    def test_unit_network_equals_maximum_matching(self):
        for trial in range(60):
            rng = random.Random(f"tp-maxflow-bip-{trial}")
            nx, ny = rng.randint(1, 5), rng.randint(1, 5)
            p = rng.choice((0.2, 0.4, 0.7))
            X = list(range(1, nx + 1))
            Y = list(range(nx + 1, nx + ny + 1))
            adj = {x: [y for y in Y if rng.random() < p] for x in X}
            s, t = 0, nx + ny + 1
            edges = [(s, x, 1) for x in X] + [(x, y, 1) for x in X for y in adj[x]] + [(y, t, 1) for y in Y]
            net = (nx + ny + 2, s, t, tuple(edges))
            ref = max_matching_brute(X, Y, adj)
            self.assertEqual(EK.max_flow_edmonds_karp(net), ref)
            self.assertEqual(DI.max_flow_dinic(net), ref)


if __name__ == "__main__":
    unittest.main()
