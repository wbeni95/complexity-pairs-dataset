"""Deterministic checks for pairs/first-match-rule-ordering-enumeration-vs-subset-dp/PROOFS.md, sections 3-10
(a few seconds; the exact V2 counts of sections 1-2 are checked by the scripts named there).

Ranges: correctness against brute force over all orders, k <= 6 (sections 3, 4); the set-dependent-cost
generalisation, k <= 6 (4.4); the enumeration's truth tests on arbitrary instances, k <= 6, and the
expected-position identity, k <= 12 (5.1); the DP's per-subset work by line-execution counts, k <= 8 (5.2);
the feedback-arc-set reduction with loops and thresholds, digraphs with at most 6 vertices and 10 arcs (7); both
directions of the linear-ordering equivalence, k <= 6 (8); the oracle facts, k <= 7 (9); tracemalloc peaks (6).
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
ENTRY = REPO / "pairs" / "first-match-rule-ordering-enumeration-vs-subset-dp"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "proofs_fm_harness")
EN_MOD = _load(ENTRY / "implementations" / "enumeration.py", "proofs_fm_enum")
DP_MOD = _load(ENTRY / "implementations" / "subset_dp.py", "proofs_fm_dp")
EN = EN_MOD.first_match_order_enumeration
DP = DP_MOD.first_match_order_subset_dp


def brute_opt(inst):
    k = inst[0]
    return min(H.order_cost(inst, order) for order in itertools.permutations(range(k)))


def instances(k_values, per_k, tag):
    for k in k_values:
        for t in range(per_k):
            yield H.generate(k, random.Random(f"{tag}|{k}|{t}"))


def counted(inst):
    k, match, cost, default = inst
    C = H.CountingInt
    return (k, tuple(tuple(C(x) for x in row) for row in match), tuple(tuple(C(x) for x in row) for row in cost),
            tuple(C(x) for x in default))


def line_numbers(module, *texts):
    lines = Path(module.__file__).read_text(encoding="utf-8").splitlines()
    out = []
    for text in texts:
        hits = [i + 1 for i, line in enumerate(lines) if line.strip() == text]
        assert len(hits) == 1, (text, hits)
        out.append(hits[0])
    return out


def count_lines(func, lines, arg):
    code = func.__code__
    counts = {line: 0 for line in lines}

    def local(frame, event, a):
        if event == "line" and frame.f_lineno in counts:
            counts[frame.f_lineno] += 1
        return local

    def glob(frame, event, a):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        func(arg)
    finally:
        sys.settrace(None)
    return counts


class Correctness(unittest.TestCase):
    def test_against_all_orders(self):
        for inst in instances(range(0, 7), 8, "proofs-fm-corr"):
            opt = brute_opt(inst)
            for fn in (EN, DP):
                value, order = fn(inst)
                self.assertEqual(value, opt)
                self.assertEqual(H.order_cost(inst, order), opt)          # the returned order attains it

    def test_set_dependent_costs(self):
        # PROOFS.md section 4.4: the recurrence stays exact when the price of item i captured by rule r depends on
        # the set R of rules placed before r.
        for k in range(0, 7):
            for t in range(6):
                rng = random.Random(f"proofs-fm-setcost|{k}|{t}")
                m = rng.randint(0, 2 * k + 1)
                M = [frozenset(r for r in range(k) if rng.random() < 0.5) for _ in range(m)]
                table = {}

                def c(i, r, R):
                    key = (i, r, R)
                    if key not in table:
                        table[key] = random.Random(f"{k}|{t}|{i}|{r}|{sorted(R)}").randint(0, 20)
                    return table[key]

                default = [rng.randint(0, 9) for _ in range(m)]

                def price(order):
                    total, placed = 0, set()
                    for i in range(m):
                        placed = []
                        for r in order:
                            if r in M[i]:
                                total += c(i, r, frozenset(placed))
                                break
                            placed.append(r)
                        else:
                            total += default[i]
                    return total

                brute = min(price(o) for o in itertools.permutations(range(k)))
                best = {0: 0}
                for s in range(1 << k):
                    if s not in best:
                        continue
                    S = frozenset(r for r in range(k) if s >> r & 1)
                    for r in range(k):
                        if s >> r & 1:
                            continue
                        gain = sum(c(i, r, S) for i in range(m) if r in M[i] and not (M[i] & S))
                        t2 = s | (1 << r)
                        best[t2] = min(best.get(t2, math.inf), best[s] + gain)
                dp = best[(1 << k) - 1] + sum(default[i] for i in range(m) if not M[i])
                self.assertEqual(dp, brute, (k, t))


class EnumerationCounts(unittest.TestCase):
    def test_expected_first_position(self):
        # PROOFS.md section 5.1: sum over all k! orders of the position of the first of t given rules is
        # k! (k + 1)/(t + 1).
        for k in range(1, 13):
            for t in range(1, k + 1):
                self.assertEqual(sum(math.comb(k - j + 1, t) for j in range(1, k + 1)), math.comb(k + 1, t + 1))
                self.assertEqual(math.factorial(k) * (k + 1) % (t + 1), 0)
        for k in range(1, 7):
            for t in range(1, k + 1):
                rules = set(range(t))
                total = sum(next(p for p, r in enumerate(o, 1) if r in rules) for o in itertools.permutations(range(k)))
                self.assertEqual(total, math.factorial(k) * (k + 1) // (t + 1))

    def test_truth_tests_on_arbitrary_instances(self):
        for inst in instances(range(1, 7), 8, "proofs-fm-enum"):
            k, match = inst[0], inst[1]
            m = len(match)
            f = math.factorial(k)
            expected_truth = 0
            for row in match:
                t = sum(row)
                expected_truth += f * (k + 1) // (t + 1) if t else f * k
            ci = counted(inst)
            H.reset_counter()
            EN(ci)
            ops = H.counts_by_kind()
            self.assertEqual(ops["truth"], expected_truth)
            self.assertEqual(ops["add"], f * m)
            self.assertEqual(ops["compare"], f - 1 if m else 0)
            self.assertEqual(ops["bit"], 0)
            c = max((sum(row) for row in match), default=0)
            self.assertGreaterEqual(ops["truth"] * (c + 1), f * m * k)      # the lower bound k! m k/(c + 1)


class DPWork(unittest.TestCase):
    def test_per_subset_work(self):
        # PROOFS.md section 5.2: m capture tests per subset, sum_i t_i 2^(k - t_i) <= m 2^(k-1) gain additions,
        # k - |S| transitions per subset.
        capture, gain_line, trans = line_numbers(DP_MOD, "if not (masks[i] & s):               # item i is not captured by the rules in s",
                                                 "gain[r] = gain[r] + cost[i][r]", "value = best_s + gain[r]")
        for inst in instances(range(0, 9), 4, "proofs-fm-dpwork"):
            k, match = inst[0], inst[1]
            m = len(match)
            c = count_lines(DP, [capture, gain_line, trans], inst)
            gains = sum(sum(row) * 2 ** (k - sum(row)) for row in match if sum(row))
            self.assertEqual(c[capture], m * 2 ** k)
            self.assertEqual(c[gain_line], gains)
            self.assertLessEqual(gains, m * 2 ** k // 2 if k else 0)
            self.assertEqual(c[trans], k * 2 ** (k - 1) if k else 0)


class Reduction(unittest.TestCase):
    @staticmethod
    def min_fas(n, arcs):
        """Minimum feedback arc set size of a digraph (arcs may include loops), by brute force."""
        for size in range(len(arcs) + 1):
            for F in itertools.combinations(range(len(arcs)), size):
                rest = [a for i, a in enumerate(arcs) if i not in F]
                if any(u == v for u, v in rest):
                    continue
                if any(all(order.index(u) < order.index(v) for u, v in rest)
                       for order in itertools.permutations(range(n))):
                    return size
        raise AssertionError

    def test_decision_thresholds_with_loops(self):
        for n in range(1, 7):
            for t in range(6):
                rng = random.Random(f"proofs-fm-fas|{n}|{t}")
                arcs = sorted({(rng.randrange(n), rng.randrange(n)) for _ in range(rng.randint(0, 10))})
                loops = sum(1 for u, v in arcs if u == v)
                match, cost = [], []
                for u, v in arcs:
                    if u == v:
                        continue                        # loops lie in every feedback arc set: deleted, K lowered
                    row = [0] * n
                    row[u] = row[v] = 1
                    c = [0] * n
                    c[v] = 1
                    match.append(row)
                    cost.append(c)
                inst = H._freeze(n, match, cost, [0] * len(match))
                opt = DP(inst)[0]
                fas = self.min_fas(n, arcs)
                self.assertEqual(EN(inst)[0], opt)
                self.assertEqual(fas, opt + loops)
                for K in range(0, len(arcs) + 1):
                    self.assertEqual(fas <= K, K - loops >= 0 and opt <= K - loops)


class LinearOrdering(unittest.TestCase):
    def test_at_most_two_rules_is_constant_plus_forward_weight(self):
        for inst in instances(range(1, 7), 6, "proofs-fm-lop-a"):
            k, match, cost, default = inst
            rows = [[r for r in range(k) if match[i][r]] for i in range(len(match))]
            if any(len(rs) > 2 for rs in rows):
                continue
            C, W = 0, [[0] * k for _ in range(k)]
            for i, rs in enumerate(rows):
                if not rs:
                    C += default[i]
                elif len(rs) == 1:
                    C += cost[i][rs[0]]
                else:
                    a, b = rs
                    C += cost[i][b]
                    W[a][b] += cost[i][a] - cost[i][b]
            for order in itertools.permutations(range(k)):
                pos = {r: p for p, r in enumerate(order)}
                fw = sum(W[a][b] for a in range(k) for b in range(k) if a != b and pos[a] < pos[b])
                self.assertEqual(H.order_cost(inst, order), C + fw)

    def test_every_linear_ordering_instance_is_a_two_rule_instance(self):
        for k in range(1, 7):
            for t in range(5):
                rng = random.Random(f"proofs-fm-lop-b|{k}|{t}")
                W = [[rng.randint(-9, 9) for _ in range(k)] for _ in range(k)]
                off = [W[a][b] for a in range(k) for b in range(k) if a != b] or [0]
                wmax = max(off)
                match, cost = [], []
                for a, b in itertools.combinations(range(k), 2):
                    row = [0] * k
                    row[a] = row[b] = 1
                    c = [0] * k
                    c[a], c[b] = wmax - W[a][b], wmax - W[b][a]
                    match.append(row)
                    cost.append(c)
                inst = H._freeze(k, match, cost, [0] * len(match))
                lop_max = max(sum(W[o[p]][o[q]] for p in range(k) for q in range(p + 1, k))
                              for o in itertools.permutations(range(k)))
                self.assertEqual(DP(inst)[0], len(match) * wmax - lop_max)


class Oracle(unittest.TestCase):
    def test_lower_bound_and_branch_and_bound(self):
        for inst in instances(range(0, 8), 5, "proofs-fm-oracle"):
            opt = DP(inst)[0]
            self.assertLessEqual(H.lower_bound(inst), opt)
            self.assertEqual(H.branch_and_bound(inst), opt)


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
        for k in range(8, 16):
            match = H.cyclic_items(k)
            rng = random.Random(k)
            inst = H._freeze(k, match, [[rng.randint(1, 9) for _ in range(k)] for _ in range(k)], [1] * k)
            per = self._peak(DP, inst) / 2 ** k
            self.assertTrue(16 <= per <= 160, (k, per))                  # best and last: two 2^k tables
        for k in range(2, 9):
            inst = H._freeze(k, H.cyclic_items(k), [[1] * k for _ in range(k)], [1] * k)
            self.assertLessEqual(self._peak(EN, inst), 4096 + 64 * k)   # no growth with k!


if __name__ == "__main__":
    unittest.main()
