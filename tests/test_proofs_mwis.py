"""Checks for pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp/PROOFS.md, sections 4-9
(correctness, the compatibility test, states, the oracle's window, the bipartite min-cut reduction, README numbers).
The exact counts (sections 1-3) are checked by the experiment scripts named in PROOFS.md.

Run:  python -m unittest tests.test_proofs_mwis   (a few seconds)
"""
import importlib.util
import inspect
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"
FLOW = REPO / "pairs" / "max-flow-edmonds-karp-vs-dinic"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "tpmwis_harness")
BF = _load(ENTRY / "implementations" / "brute_force.py", "tpmwis_bf").mwis_brute_force
DP = _load(ENTRY / "implementations" / "column_dp.py", "tpmwis_dp").mwis_column_dp
DINIC = _load(FLOW / "implementations" / "dinic.py", "tpmwis_dinic").max_flow_dinic


def edges_from_definition(k, n, diagonals):
    E = set()
    for r in range(k):
        for c in range(n):
            if c + 1 < n:
                E.add(frozenset({(r, c), (r, c + 1)}))
            if r + 1 < k:
                E.add(frozenset({(r, c), (r + 1, c)}))
            if r + 1 < k and c + 1 < n:
                if diagonals[r][c] & 1:
                    E.add(frozenset({(r, c), (r + 1, c + 1)}))
                if diagonals[r][c] & 2:
                    E.add(frozenset({(r, c + 1), (r + 1, c)}))
    return E


def brute_optimum(k, n, weights, diagonals):
    V = [(r, c) for r in range(k) for c in range(n)]
    E = edges_from_definition(k, n, diagonals)
    best = 0
    for mask in range(1 << len(V)):
        S = [V[i] for i in range(len(V)) if mask >> i & 1]
        if any(frozenset({a, b}) in E for i, a in enumerate(S) for b in S[i + 1:]):
            continue
        best = max(best, sum(weights[r][c] for r, c in S))
    return best


def random_instance(rng, max_vertices=12):
    while True:
        k, n = rng.randint(1, 5), rng.randint(0, 6)
        if k * n <= max_vertices:
            break
    kind = rng.randrange(4)
    weights = tuple(tuple((0 if kind == 0 and rng.random() < 0.5 else rng.randint(0, 9)) for _ in range(n))
                    for _ in range(k))
    diagonals = tuple(tuple(rng.randrange(4) if kind != 3 else 0 for _ in range(n - 1)) for _ in range(k - 1))
    return k, n, weights, diagonals


INSTANCES = [random_instance(random.Random(f"tp-mwis-{i}")) for i in range(120)]


def all_pattern_instances():
    """Every diagonal pattern of the 2 x 2, 2 x 3, 3 x 2 and 3 x 3 grids, with seeded weights 0..9."""
    out = []
    for k, n in ((2, 2), (2, 3), (3, 2), (3, 3)):
        squares = (k - 1) * (n - 1)
        for code in range(4 ** squares):
            codes = [(code >> (2 * q)) & 3 for q in range(squares)]
            diagonals = tuple(tuple(codes[r * (n - 1) + c] for c in range(n - 1)) for r in range(k - 1))
            rng = random.Random(f"tp-mwis-pattern-{k}-{n}-{code}")
            weights = tuple(tuple(rng.randint(0, 9) for _ in range(n)) for _ in range(k))
            out.append((k, n, weights, diagonals))
    return out


PATTERN_INSTANCES = all_pattern_instances()


class Correctness(unittest.TestCase):
    def test_both_equal_brute_optimum_and_set_is_valid(self):
        self.assertEqual(len(PATTERN_INSTANCES), 4 + 16 + 16 + 256)
        for inst in INSTANCES + PATTERN_INSTANCES:
            k, n, weights, diagonals = inst
            ref = brute_optimum(*inst)
            E = edges_from_definition(k, n, diagonals)
            for fn in (BF, DP):
                value, chosen = fn(inst)
                self.assertEqual(value, ref, inst)
                self.assertEqual(sum(weights[r][c] for r, c in chosen), value)
                self.assertFalse(any(frozenset({a, b}) in E for i, a in enumerate(chosen) for b in chosen[i + 1:]))


class ZeroWeights(unittest.TestCase):
    def test_addition_count_with_zero_weights(self):
        for trial in range(600):
            rng = random.Random(f"tp-mwis-zero-{trial}")
            k, n = rng.randint(1, 6), rng.randint(1, 12)
            p0 = rng.choice((0.3, 0.6, 0.9, 1.0))
            raw = [[0 if rng.random() < p0 else rng.randint(1, 3) for _ in range(n)] for _ in range(k)]
            weights = tuple(tuple(H.CountingInt(x) for x in row) for row in raw)
            diagonals = tuple(tuple(rng.randrange(4) for _ in range(n - 1)) for _ in range(k - 1))
            H.reset_counters()
            DP((k, n, weights, diagonals))
            states = [s for s in range(1 << k) if s & (s >> 1) == 0]
            F, P = len(states), sum(bin(s).count("1") for s in states)
            z = 0
            for c in range(1, n):
                if all(raw[r][cc] == 0 for r in range(k) for cc in range(c)):
                    z += 1
            self.assertEqual(H._ops["add"], n * P + (n - 1) * F - z, (k, n, raw))


class Comparisons(unittest.TestCase):
    def test_comparison_bounds_positive_weights(self):
        for trial in range(300):
            rng = random.Random(f"tp-mwis-cmp-{trial}")
            k, n = rng.randint(1, 6), rng.randint(1, 15)
            weights = tuple(tuple(H.CountingInt(rng.randint(1, 9)) for _ in range(n)) for _ in range(k))
            diagonals = tuple(tuple(rng.randrange(4) for _ in range(n - 1)) for _ in range(k - 1))
            H.reset_counters()
            DP((k, n, weights, diagonals))
            F = sum(1 for s in range(1 << k) if s & (s >> 1) == 0)
            cmps = H._ops["compare"]
            self.assertGreaterEqual(cmps, n * (F - 1))
            self.assertLessEqual(cmps, (n - 1) * F * (F - 1) + F - 1)


class CompatibilityTest(unittest.TestCase):
    def test_bit_tests_reject_exactly_the_joined_pairs(self):
        for k in range(1, 6):
            states = [s for s in range(1 << k) if s & (s >> 1) == 0]
            for codes in range(4 ** (k - 1)):
                column_codes = [(codes >> (2 * r)) & 3 for r in range(k - 1)]
                down = sum(1 << r for r in range(k - 1) if column_codes[r] & 1)
                up = sum(1 << r for r in range(k - 1) if column_codes[r] & 2)
                diagonals = tuple((column_codes[r],) for r in range(k - 1))   # a k x 2 grid: one square column
                E = edges_from_definition(k, 2, diagonals)
                for t in states:
                    for s in states:
                        joined = any(frozenset({(a, 0), (b, 1)}) in E
                                     for a in range(k) if t >> a & 1 for b in range(k) if s >> b & 1)
                        passes = not (t & s) and not (((t & down) << 1) & s) and not (((s & up) << 1) & t)
                        self.assertEqual(passes, not joined, (k, column_codes, t, s))


class States(unittest.TestCase):
    def test_fibonacci_states_and_P(self):
        fib = [0, 1]
        while len(fib) < 12:
            fib.append(fib[-1] + fib[-2])
        P = {1: 1, 2: 2, 3: 5, 4: 10, 5: 20, 6: 38}
        for k in range(1, 7):
            states = [s for s in range(1 << k) if s & (s >> 1) == 0]
            self.assertEqual(len(states), fib[k + 2])
            self.assertEqual(sum(bin(s).count("1") for s in states), P[k])
            self.assertGreaterEqual(fib[k + 2], k + 1)
            self.assertLessEqual(2 ** k, fib[k + 2] ** 2)

    def test_readme_number(self):
        N = 3 * 20
        self.assertEqual(round(N * 2 ** (N - 1) / 1e19, 2), 3.46)


SRC_LINES, SRC_START = inspect.getsourcelines(H.profile_dp_value)
LINE_NXT = SRC_START + next(i for i, line in enumerate(SRC_LINES) if line.strip() == "nxt = {}")
LINE_FOR = SRC_START + next(i for i, line in enumerate(SRC_LINES)
                            if line.strip().startswith("for state, value in table.items():"))


def traced_oracle(inst):
    """Run the unchanged profile_dp_value and read its local `blocked` per vertex and the table sizes."""
    blocked, sizes = {}, []

    def local(frame, event, arg):
        if event == "line":
            if frame.f_lineno == LINE_NXT:
                blocked[(frame.f_locals["r"], frame.f_locals["c"])] = frame.f_locals["blocked"]
            elif frame.f_lineno == LINE_FOR:
                sizes.append(len(frame.f_locals["table"]))
        return local

    def tracer(frame, event, arg):
        if frame.f_code is H.profile_dp_value.__code__:
            return local
        return None

    sys.settrace(tracer)
    try:
        value = H.profile_dp_value(inst)
    finally:
        sys.settrace(None)
    return value, blocked, sizes


class OracleWindow(unittest.TestCase):
    def _check_instance(self, k, n, diagonals):
        weights = tuple(tuple(1 for _ in range(n)) for _ in range(k))
        _, blocked, sizes = traced_oracle((k, n, weights, diagonals))
        E = edges_from_definition(k, n, diagonals)
        pos = {(r, c): c * k + r for c in range(n) for r in range(k)}
        for e in E:
            a, b = sorted(pos[v] for v in e)
            self.assertLessEqual(b - a, k + 1)
        for v, i in pos.items():
            own = 0
            for e in E:
                if v in e:
                    (u,) = [x for x in e if x != v]
                    if pos[u] < i:
                        own |= 1 << (i - pos[u] - 1)
            self.assertEqual(blocked[v], own, (k, n, diagonals, v))
        self.assertTrue(all(size <= 2 ** (k + 1) for size in sizes))

    def test_blocked_read_from_the_running_oracle(self):
        cases = 0
        for k in range(1, 6):
            for n in range(1, 6):
                squares = (k - 1) * (n - 1)
                if squares > 4:
                    continue
                for code in range(4 ** squares):
                    codes = [(code >> (2 * q)) & 3 for q in range(squares)]
                    self._check_instance(k, n, tuple(tuple(codes[r * (n - 1) + c] for c in range(n - 1))
                                                     for r in range(k - 1)))
                    cases += 1
        for trial in range(200):
            rng = random.Random(f"tp-mwis-oracle-{trial}")
            k, n = rng.randint(1, 6), rng.randint(1, 6)
            self._check_instance(k, n, tuple(tuple(rng.randrange(4) for _ in range(n - 1)) for _ in range(k - 1)))
            cases += 1
        self.assertGreater(cases, 600)

    def test_profile_dp_equals_brute(self):
        for inst in INSTANCES + PATTERN_INSTANCES:
            self.assertEqual(H.profile_dp_value(inst), brute_optimum(*inst))


class Space(unittest.TestCase):
    @staticmethod
    def peak(fn, inst):
        import tracemalloc
        tracemalloc.start()
        fn(inst)
        _, p = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return p

    def test_dp_linear_in_n_and_brute_small(self):
        dp = [self.peak(DP, H.king_instance(3, n, random.Random(f"tp-mwis-space-{n}"), wrap=int))
              for n in (200, 400, 800)]
        for a, b in zip(dp, dp[1:]):
            self.assertTrue(1.5 < b / a < 2.6, dp)          # Theta(F_{k+2} n) for fixed k
        bf = [self.peak(BF, H.king_instance(k, 3, random.Random(f"tp-mwis-space-bf-{k}"), wrap=int))
              for k in (2, 4)]                             # N = 6 and 12: 64 and 4096 subsets
        self.assertLess(bf[1] / bf[0], 4.0, bf)             # Theta(N), not Theta(2^N)


class BipartiteFlow(unittest.TestCase):
    def test_min_cut_reduction_on_grids_without_diagonals(self):
        for trial in range(40):
            rng = random.Random(f"tp-mwis-flow-{trial}")
            k, n = rng.randint(1, 4), rng.randint(1, 6)
            weights = tuple(tuple(rng.randint(0, 9) for _ in range(n)) for _ in range(k))
            diagonals = tuple(tuple(0 for _ in range(n - 1)) for _ in range(k - 1))
            inst = (k, n, weights, diagonals)
            idx = {(r, c): 1 + c * k + r for c in range(n) for r in range(k)}
            sigma, tau = 0, k * n + 1
            total = sum(map(sum, weights))
            big = total + 1
            arcs = []
            for (r, c), i in idx.items():
                if (r + c) % 2 == 0:
                    arcs.append((sigma, i, weights[r][c]))
                else:
                    arcs.append((i, tau, weights[r][c]))
            for e in edges_from_definition(k, n, diagonals):
                a, b = sorted(e, key=lambda v: (v[0] + v[1]) % 2)   # a in the even class X
                arcs.append((idx[a], idx[b], big))
            cut = DINIC((k * n + 2, sigma, tau, tuple(arcs)))
            self.assertEqual(total - cut, DP(inst)[0])


if __name__ == "__main__":
    unittest.main()
