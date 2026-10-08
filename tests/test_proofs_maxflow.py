"""Checks for pairs/max-flow-edmonds-karp-vs-dinic/PROOFS.md (correctness, the bounds of Theorem F and Lemma A,
the phase bound of Theorem DI, space, the bipartite-matching reduction, and the correspondence between
generate_scaling and the random model of sections 9-10), plus the exact reproduction of the measured counts that
entry.json quotes. The probabilistic statements of section 10 are checked by the verify.py scripts of the three
theorem notes theorems/max-flow-random-dense-*.

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


class RecordingRandom(random.Random):
    """random.Random that records the calls generate_scaling makes (random() and randint()). It also defines
    getrandbits (unchanged), so that randint keeps drawing from getrandbits as in random.Random: a subclass that
    overrides only random() would make randint draw from random() instead. The test checks that the instances are
    identical to those of a plain random.Random with the same seed."""

    def __init__(self, seed):
        self.calls = []
        super().__init__(seed)

    def getrandbits(self, k):
        return super().getrandbits(k)

    def random(self):
        x = super().random()
        self.calls.append(("random", x))
        return x

    def randint(self, a, b):
        x = super().randint(a, b)
        self.calls.append(("randint", a, b, x))
        return x


class RandomModel(unittest.TestCase):
    """PROOFS.md section 9: generate_scaling draws exactly as the model G_n describes (one random() per ordered pair
    u != v in loop order; randint(1, 100) right after it iff the value is < 1/2; these edges, s = 0, t = n - 1)."""

    def test_generator_call_sequence(self):
        instances = 0
        for n in (2, 3, 5, 10, 25, 60):
            for k in range(4):
                rng = RecordingRandom(f"tp-maxflow-model-{n}-{k}")
                nn, s, t, edges = H.generate_scaling(n, rng)
                self.assertEqual((nn, s, t, edges), H.generate_scaling(n, random.Random(f"tp-maxflow-model-{n}-{k}")))
                self.assertEqual((nn, s, t), (n, 0, n - 1))
                calls = iter(rng.calls)
                expected = []
                for u in range(n):
                    for v in range(n):
                        if u == v:
                            continue
                        kind, x = next(calls)
                        self.assertEqual(kind, "random")
                        self.assertEqual(x * 2 ** 53, int(x * 2 ** 53))     # 53-bit value (premise check only)
                        if x < 0.5:
                            kind, a, b, c = next(calls)
                            self.assertEqual((kind, a, b), ("randint", 1, 100))
                            expected.append((u, v, c))
                self.assertIsNone(next(calls, None))                     # no further calls
                self.assertEqual(edges, tuple(expected))
                self.assertEqual(len({(u, v) for u, v, _ in edges}), len(edges))   # no parallel edges
                self.assertTrue(all(u != v and 1 <= c <= 100 for u, v, c in edges))
                instances += 1
        self.assertEqual(instances, 24)


class MeasuredCounts(unittest.TestCase):
    """The measured counts quoted in entry.json (verification) on the probe's instances
    random.Random('max-flow-edmonds-karp-vs-dinic|v2|n'): E, Edmonds-Karp augmentations, Dinic phases with t
    reachable. Data, reproduced exactly; not part of a proof."""

    def test_probe_counts(self):
        expect = {20: (191, 21, 4), 40: (770, 40, 3), 80: (3182, 87, 2), 160: (12754, 176, 3)}
        for n, (E, aug, phases) in expect.items():
            net = H.generate_scaling(n, random.Random(f"max-flow-edmonds-karp-vs-dinic|v2|{n}"))
            F, ek_bfs = bfs_passes(EK.max_flow_edmonds_karp, net)
            F2, di_bfs = bfs_passes(DI.max_flow_dinic, net)
            self.assertEqual(F, F2)
            self.assertEqual((len(net[3]), ek_bfs - 1, di_bfs - 1), (E, aug, phases), n)


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
