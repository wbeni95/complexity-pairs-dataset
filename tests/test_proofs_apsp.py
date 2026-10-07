"""Checks for pairs/all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall/PROOFS.md, sections 3-8.

Correctness on the problem's inputs and with negative weights (no negative cycle), the negative-cycle test of the
standard Bellman-Ford variant, the pass bounds of the early-exit variant, and the space bounds. The implementations
are run unchanged; the early-exit variant and the negative-cycle test are written here (they are not part of the
entry). All inputs come from fixed seeds. Runs in a few seconds.
"""
import heapq
import importlib.util
import itertools
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_apsp_h")
BF_FILE = E / "implementations" / "bellman_ford.py"
FW_FILE = E / "implementations" / "floyd_warshall.py"
BF = _load(BF_FILE, "tp_apsp_bf").apsp_bellman_ford
FW = _load(FW_FILE, "tp_apsp_fw").apsp_floyd_warshall
INF = float("inf")


def edges_of(W):
    n = len(W)
    return [(u, v, W[u][v]) for u in range(n) for v in range(n) if u != v and W[u][v] is not None]


def dijkstra_all(W):
    """Heap-based Dijkstra from every source (non-negative weights only)."""
    n = len(W)
    adj = [[(v, W[u][v]) for v in range(n) if v != u and W[u][v] is not None] for u in range(n)]
    out = []
    for s in range(n):
        dist = [None] * n
        heap = [(0, s)]
        while heap:
            d, u = heapq.heappop(heap)
            if dist[u] is not None:
                continue
            dist[u] = d
            for v, w in adj[u]:
                if dist[v] is None:
                    heapq.heappush(heap, (d + w, v))
        out.append(dist)
    return out


def early_exit_passes(W, s):
    """The early-exit variant of experiments/2026-10-07_apsp_bellman_ford_early_exit.py: (passes, relaxations)."""
    n = len(W)
    edges = edges_of(W)
    dist = [INF] * n
    dist[s] = 0
    passes = 0
    for _ in range(n - 1):
        passes += 1
        changed = False
        for u, v, w in edges:
            d = dist[u] + w
            if d < dist[v]:
                dist[v] = d
                changed = True
        if not changed:
            break
    return passes, passes * len(edges)


def extra_pass_reports_cycle(W, s):
    """Standard Bellman-Ford negative-cycle test from s: n - 1 passes, then one more; True if it lowers a value."""
    n = len(W)
    edges = edges_of(W)
    dist = [INF] * n
    dist[s] = 0
    for _ in range(n - 1):
        for u, v, w in edges:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
    return any(dist[u] + w < dist[v] for u, v, w in edges)


def negative_cycle_reachable(W, s):
    """Exhaustive: is some cycle of negative weight reachable from s? (small n only)"""
    n = len(W)
    seen, stack = {s}, [s]
    while stack:
        u = stack.pop()
        for v in range(n):
            if v != u and W[u][v] is not None and v not in seen:
                seen.add(v)
                stack.append(v)
    for k in range(2, n + 1):
        for cyc in itertools.permutations(range(n), k):
            if cyc[0] != min(cyc) or cyc[0] not in seen:
                continue
            total = 0
            for a, b in zip(cyc, cyc[1:] + cyc[:1]):
                if W[a][b] is None:
                    break
                total += W[a][b]
            else:
                if total < 0:
                    return True
    return False


class APSPProofChecks(unittest.TestCase):
    def test_correct_on_problem_inputs(self):
        for n in range(0, 21):
            for t in range(4):
                W = H.generate(n, random.Random(f"tp-apsp|gen|{n}|{t}"))
                expected = tuple(tuple(r) for r in dijkstra_all(W))
                self.assertEqual(BF(W), expected, (n, t))
                self.assertEqual(FW(W), expected, (n, t))

    def test_correct_with_negative_weights(self):
        negative_seen = 0
        for n in range(0, 13):
            for t in range(6):
                rng = random.Random(f"tp-apsp|neg|{n}|{t}")
                density = rng.choice((0.2, 0.5, 1.0))
                p = [rng.randint(-30, 30) for _ in range(n)]
                W0 = tuple(tuple(0 if i == j else (rng.randint(0, 20) if rng.random() < density else None)
                                 for j in range(n)) for i in range(n))
                W = tuple(tuple(0 if i == j else (None if W0[i][j] is None else W0[i][j] + p[i] - p[j])
                                for j in range(n)) for i in range(n))
                negative_seen += sum(1 for u, v, w in edges_of(W) if w < 0)
                d0 = dijkstra_all(W0)
                expected = tuple(tuple(None if d0[s][v] is None else d0[s][v] + p[s] - p[v] for v in range(n))
                                 for s in range(n))
                self.assertEqual(BF(W), expected, (n, t))
                self.assertEqual(FW(W), expected, (n, t))
        self.assertGreater(negative_seen, 500)

    def test_negative_cycle_test(self):
        yes = no = 0
        for n in range(1, 7):
            for t in range(60):
                rng = random.Random(f"tp-apsp|cyc|{n}|{t}")
                density = rng.choice((0.3, 0.6, 1.0))
                W = tuple(tuple(0 if i == j else (rng.randint(-6, 9) if rng.random() < density else None)
                                for j in range(n)) for i in range(n))
                for s in range(n):
                    truth = negative_cycle_reachable(W, s)
                    self.assertEqual(extra_pass_reports_cycle(W, s), truth, (n, t, s))
                    yes += truth
                    no += not truth
        self.assertGreater(yes, 100)
        self.assertGreater(no, 100)

    def test_early_exit_lower_bound_family(self):
        for n in range(2, 17):
            rng = random.Random(f"tp-apsp|ee|{n}")
            full = n * (n - 1)
            ms = sorted({n - 1, full} | {rng.randint(n - 1, full) for _ in range(4)})
            others = [(u, v) for u in range(n) for v in range(n) if u != v and v != u - 1]
            for m in ms:
                extra = set(rng.sample(others, m - (n - 1)))
                W = tuple(tuple(0 if u == v else (1 if v == u - 1 else
                                                  (rng.randint(n, 3 * n) if (u, v) in extra else None))
                                for v in range(n)) for u in range(n))
                self.assertEqual(len(edges_of(W)), m)
                total = 0
                for s in range(n):
                    passes, relax = early_exit_passes(W, s)
                    self.assertGreaterEqual(passes, min(s + 1, n - 1), (n, m, s))
                    total += relax
                self.assertGreaterEqual(total, m * (n * (n - 1) // 2 + n - 1), (n, m))

    def test_early_exit_upper_bound(self):
        for n in range(1, 17):
            for density in (0.0, 0.05, 0.2, 0.6, 1.0):
                for t in range(4):
                    rng = random.Random(f"tp-apsp|eu|{n}|{density}|{t}")
                    W = tuple(tuple(0 if i == j else (rng.randint(0, 50) if rng.random() < density else None)
                                    for j in range(n)) for i in range(n))
                    m = len(edges_of(W))
                    for s in range(n):
                        passes, _ = early_exit_passes(W, s)
                        self.assertLessEqual(passes, min(m + 1, n - 1), (n, density, t, s))

    def test_space(self):
        for n in range(0, 11):
            for t in range(3):
                W = H.generate(n, random.Random(f"tp-apsp|space|{n}|{t}"))
                m = len(edges_of(W))
                out, peak_bf = peak_words(BF, (W,), BF_FILE)
                self.assertEqual(out, FW(W))
                _, peak_fw = peak_words(FW, (W,), FW_FILE)
                self.assertTrue(n * n + n <= peak_bf <= 4 * m + n * n + 3 * n, (n, t, m, peak_bf))
                self.assertTrue(n * n + n <= peak_fw <= 2 * n * n + 2 * n, (n, t, peak_fw))


if __name__ == "__main__":
    unittest.main()
