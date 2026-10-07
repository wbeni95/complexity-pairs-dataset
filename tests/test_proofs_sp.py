"""Checks for pairs/shortest-path-enumeration-vs-dijkstra/PROOFS.md (correctness, the enumeration's exact
search-tree sizes, Dijkstra's reads, the lower-bound instance, space).

The implementations are not modified: calls of the inner function `dfs` are counted with sys.setprofile, and weight
reads with a matrix wrapper whose rows record the indices read.

Run:  python -m unittest tests.test_proofs_sp   (a few seconds)
"""
import importlib.util
import inspect
import math
import random
import sys
import tracemalloc
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "shortest-path-enumeration-vs-dijkstra"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


ENUM = _load(ENTRY / "implementations" / "enumeration.py", "tpsp_enum").shortest_path_enumerate
DIJ = _load(ENTRY / "implementations" / "dijkstra.py", "tpsp_dij").shortest_path_dijkstra


def complete(n, rng, lo=1, hi=100):
    return tuple(tuple(0 if i == j else rng.randint(lo, hi) for j in range(n)) for i in range(n))


def floyd_warshall(W):
    n = len(W)
    d = [[0 if i == j else W[i][j] for j in range(n)] for i in range(n)]
    for k in range(n):
        for i in range(n):
            for j in range(n):
                if d[i][k] + d[k][j] < d[i][j]:
                    d[i][j] = d[i][k] + d[k][j]
    return d[0][n - 1]


class RecordingRow:
    def __init__(self, u, row, log):
        self.u, self.row, self.log = u, row, log

    def __getitem__(self, v):
        self.log.append((self.u, v))
        return self.row[v]

    def __len__(self):
        return len(self.row)


class RecordingMatrix:
    def __init__(self, W):
        self.W = W
        self.log = []

    def __getitem__(self, u):
        return RecordingRow(u, self.W[u], self.log)

    def __len__(self):
        return len(self.W)


def profile_dfs(W):
    """(number of dfs calls, largest dfs recursion depth) for one run of the enumeration."""
    stats = {"calls": 0, "depth": 0, "max": 0}

    def prof(frame, event, arg):
        if frame.f_code.co_name != "dfs":
            return
        if event == "call":
            stats["calls"] += 1
            stats["depth"] += 1
            stats["max"] = max(stats["max"], stats["depth"])
        elif event == "return":
            stats["depth"] -= 1

    sys.setprofile(prof)
    try:
        ENUM(W)
    finally:
        sys.setprofile(None)
    return stats["calls"], stats["max"]


def P(n):
    m = n - 2
    return sum(math.factorial(m) // math.factorial(j) for j in range(m + 1))


class Correctness(unittest.TestCase):
    def test_against_floyd_warshall(self):
        count = 0
        for n in range(1, 9):
            for trial in range(9):
                rng = random.Random(f"tp-sp-{n}-{trial}")
                W = complete(n, rng, *rng.choice(((0, 100), (1, 3))))
                ref = floyd_warshall(W)
                self.assertEqual(ENUM(W), ref)
                self.assertEqual(DIJ(W), ref)
                count += 1
        self.assertEqual(count, 72)
        for n in range(9, 31):
            W = complete(n, random.Random(f"tp-sp-big-{n}"), 0, 100)
            self.assertEqual(DIJ(W), floyd_warshall(W))

    def test_absent_arcs_and_zero_weights(self):
        unreachable = 0
        for n in range(1, 9):
            for trial in range(6):
                rng = random.Random(f"tp-sp-inf-{n}-{trial}")
                p = rng.choice((0.3, 0.6))
                W = tuple(tuple(0 if i == j else (math.inf if rng.random() < p else rng.randint(0, 5))
                                for j in range(n)) for i in range(n))
                ref = floyd_warshall(W)
                unreachable += ref == math.inf
                self.assertEqual(ENUM(W), ref)
                self.assertEqual(DIJ(W), ref)
        self.assertGreater(unreachable, 0)


ENUM_SRC, ENUM_START = inspect.getsourcelines(sys.modules["tpsp_enum"].shortest_path_enumerate)
SCAN_LINE = ENUM_START + next(i for i, line in enumerate(ENUM_SRC) if line.strip() == "if not visited[v]:")


def scans_per_call(W):
    """[(u, number of executions of the scan line in that call)] for every dfs call."""
    out, counts = [], {}

    def local(frame, event, arg):
        if event == "line" and frame.f_lineno == SCAN_LINE:
            counts[id(frame)] += 1
        elif event == "return":
            out.append((frame.f_locals["u"], counts.pop(id(frame))))
        return local

    def tracer(frame, event, arg):
        if event == "call" and frame.f_code.co_name == "dfs":
            counts[id(frame)] = 0
            return local
        return None

    sys.settrace(tracer)
    try:
        ENUM(W)
    finally:
        sys.settrace(None)
    return out


class EnumerationSizes(unittest.TestCase):
    def test_scans_per_call(self):
        for n in range(2, 9):
            calls = scans_per_call(complete(n, random.Random(f"tp-sp-scan-{n}")))
            self.assertEqual(len(calls), 2 * P(n))
            for u, scans in calls:
                self.assertEqual(scans, 0 if u == n - 1 else n, (n, u))

    def test_calls_and_reads(self):
        for n in range(2, 10):
            W = complete(n, random.Random(f"tp-sp-size-{n}"))
            calls, _ = profile_dfs(W)
            self.assertEqual(calls, 2 * P(n))
            R = RecordingMatrix(W)
            ENUM(R)
            self.assertEqual(len(R.log), 2 * P(n) - 1)

    def test_floor_e_factorial(self):
        from decimal import Decimal, getcontext
        getcontext().prec = 80
        e = sum(Decimal(1) / Decimal(math.factorial(j)) for j in range(80))
        for n in range(3, 21):
            m = n - 2
            value = e * Decimal(math.factorial(m))
            self.assertEqual(P(n), int(value))          # floor (value > 0)
            self.assertTrue(0 < value - P(n) < 1)


class DijkstraReads(unittest.TestCase):
    def test_exactly_one_arc_per_pair(self):
        for trial in range(40):
            rng = random.Random(f"tp-sp-reads-{trial}")
            n = rng.randint(1, 40)
            W = complete(n, rng, 0, 100)
            R = RecordingMatrix(W)
            DIJ(R)
            read = set(R.log)
            self.assertEqual(len(read), n * (n - 1) // 2)
            # replay the settling order (same rule: minimum dist, smallest index first)
            dist = [math.inf] * n
            dist[0] = 0
            done = [False] * n
            rank = {}
            for r in range(n):
                u = min((d, v) for v, d in enumerate(dist) if not done[v])[1]
                done[u] = True
                rank[u] = r
                for v in range(n):
                    if not done[v] and dist[u] + W[u][v] < dist[v]:
                        dist[v] = dist[u] + W[u][v]
            for u in range(n):
                for v in range(u + 1, n):
                    first, second = (u, v) if rank[u] < rank[v] else (v, u)
                    self.assertIn((first, second), read)
                    self.assertNotIn((second, first), read)


def instance_I(n):
    s, t = 0, n - 1
    inner = list(range(1, n - 1))
    U = inner[: (n - 2) // 2]
    X = inner[(n - 2) // 2:]
    W = [[0 if i == j else 100 for j in range(n)] for i in range(n)]
    for u in U:
        W[s][u] = 1
        for x in X:
            W[u][x] = 2
    for x in X:
        W[x][t] = 1
    return W, U, X


class LowerBoundInstance(unittest.TestCase):
    def test_distance_four_and_three(self):
        for n in range(4, 13):
            W, U, X = instance_I(n)
            self.assertEqual(len(U) * len(X), (n - 2) ** 2 // 4)
            impls = (DIJ, floyd_warshall) + ((ENUM,) if n <= 8 else ())
            for fn in impls:
                self.assertEqual(fn(tuple(map(tuple, W))), 4)
            for u in U:
                for x in X:
                    W2 = [r[:] for r in W]
                    W2[u][x] = 1
                    for fn in impls:
                        self.assertEqual(fn(tuple(map(tuple, W2))), 3)


class Space(unittest.TestCase):
    def test_recursion_depth_is_n(self):
        for n in range(2, 10):
            _, depth = profile_dfs(complete(n, random.Random(f"tp-sp-depth-{n}")))
            self.assertEqual(depth, n)

    def test_dijkstra_linear_space(self):
        peaks = []
        for n in (50, 100, 200):
            W = complete(n, random.Random(f"tp-sp-space-{n}"))
            tracemalloc.start()
            DIJ(W)
            _, p = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            peaks.append(p)
        for a, b in zip(peaks, peaks[1:]):
            self.assertLess(b / a, 3.0, peaks)


if __name__ == "__main__":
    unittest.main()
