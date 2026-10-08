"""Deterministic checks for pairs/lz77-repeat-slots-enumeration-vs-slot-dp (entry.json and PROOFS.md; a few seconds).

Ranges (fixed inputs and seeds; standard library only):
- correctness (PROOFS.md sections 4, 5, 8): the two implementations and the independent oracle agree on every binary
  string of length <= 7 (k = 1, 2, 3; REPMIN = 1, 2, 3) and on seeded instances up to n = 24; check() rejects wrong
  outputs; the match-length table equals its definition on every binary string of length <= 8 (section 6.1);
- the exact V2 counts (sections 2, 3): enumeration on F1(m) for m <= 8 (k = 2) and m <= 7 (k = 1, 3), the sandwich for
  m = 3..29; DP on F1(m) for m <= 40 (k = 2) and m <= 15 (k = 1, 3); the parse counts of F1 (padded, every k and
  REPMIN in 1..3, m <= 6) and its symbol count (sections 1, 6.4);
- the bounds on every input (sections 6, 7): per-position and total state bounds of the DP (REPMIN = 1, 2, 3) and the
  lower bound on a^n; relaxations and search-tree nodes against their bounds on every binary string of length 1..7;
  the maximum stack of the enumeration; the uncounted work of both algorithms (sections 6.3, 6.6).
"""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "lz77-repeat-slots-enumeration-vs-slot-dp"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "test_lz_harness")
ENM = _load(ENTRY / "implementations" / "enumeration.py", "test_lz_enum")
DPM = _load(ENTRY / "implementations" / "slot_dp.py", "test_lz_dp")
EN = ENM.lz77_slots_enumeration
DP = DPM.lz77_slots_dp


def _enumeration_stats(instance):
    """Same push discipline as enumeration.py (PROOFS.md 6.6, 7). Returns token evaluations, maximum stack length,
    nodes popped, nodes expanded (popped at a position < n), slot tests and distance tests."""
    s, k, repmin = instance
    n = len(s)
    ml = ENM.match_lengths(s)
    evaluations, peak, popped, expanded, slot_tests, dist_tests = 0, 1, 0, 0, 0, 0
    stack = [(0, (1,) * k)]
    while stack:
        i, slots = stack.pop()
        popped += 1
        if i == n:
            continue
        expanded += 1
        row = ml[i]
        evaluations += 1
        stack.append((i + 1, slots))
        for j in range(k):
            slot_tests += 1
            r = slots[j]
            if r <= i and row[r] >= repmin:
                moved = (r,) + slots[:j] + slots[j + 1:]
                for length in range(repmin, row[r] + 1):
                    evaluations += 1
                    stack.append((i + length, moved))
        for d in range(1, i + 1):
            dist_tests += 1
            if row[d] >= 2:
                pushed = (d,) + slots[:-1]
                for length in range(2, row[d] + 1):
                    evaluations += 1
                    stack.append((i + length, pushed))
        peak = max(peak, len(stack))
    return {"evaluations": evaluations, "peak": peak, "popped": popped, "expanded": expanded,
            "slot_tests": slot_tests, "dist_tests": dist_tests}


def _dp_work(instance):
    """Same loops as slot_dp.py (PROOFS.md 6.3), with every step counted; values as in slot_dp."""
    s, k, repmin = instance
    n = len(s)
    ml = DPM.match_lengths(s)
    best = [dict() for _ in range(n + 1)]
    best[0][(1,) * k] = 0
    w = {"relax": 0, "lit": 0, "rep": 0, "new": 0, "slot_tests": 0, "dist_tests": 0, "rep_builds": 0,
         "group_dist": 0, "states_below_n": 0}
    for i in range(n):
        row = ml[i]
        distances = []
        for d in range(1, i + 1):
            w["dist_tests"] += 1
            if row[d] >= 2:
                distances.append(d)
        groups = {}
        for slots, cost in best[i].items():
            w["states_below_n"] += 1
            w["lit"] += 1
            DPM._offer(best[i + 1], slots, cost + 9)
            for j in range(k):
                w["slot_tests"] += 1
                r = slots[j]
                if r <= i and row[r] >= repmin:
                    w["rep_builds"] += 1
                    moved = (r,) + slots[:j] + slots[j + 1:]
                    for length in range(repmin, row[r] + 1):
                        w["rep"] += 1
                        DPM._offer(best[i + length], moved, cost + 3 + j + DPM.gamma_len(length))
            prefix = slots[:-1]
            if prefix not in groups or cost < groups[prefix]:
                groups[prefix] = cost
        for prefix, cost in groups.items():
            for d in distances:
                w["group_dist"] += 1
                pushed = (d,) + prefix
                for length in range(2, row[d] + 1):
                    w["new"] += 1
                    DPM._offer(best[i + length], pushed, cost + 2 + DPM.gamma_len(length - 1) + DPM.gamma_len(d))
    w["relax"] = w["lit"] + w["rep"] + w["new"]
    w["states_at_n"] = len(best[n])
    w["opt"] = min(best[n].values())
    return w


def _states_per_position(instance):
    """Number of states the DP holds at every position (same recurrence as slot_dp, values discarded)."""
    s, k, repmin = instance
    n = len(s)
    ml = DPM.match_lengths(s)
    levels = [set() for _ in range(n + 1)]
    levels[0].add((1,) * k)
    for i in range(n):
        for R in levels[i]:
            levels[i + 1].add(R)
            for j, r in enumerate(R):
                if r <= i and ml[i][r] >= repmin:
                    for L in range(repmin, ml[i][r] + 1):
                        levels[i + L].add((r,) + R[:j] + R[j + 1:])
            for d in range(1, i + 1):
                for L in range(2, ml[i][d] + 1):
                    levels[i + L].add((d,) + R[:-1])
    return [len(x) for x in levels]


def _count_parses(s, k, repmin):
    """Number of complete parses of s (memoised over states)."""
    ml = DPM.match_lengths(s)
    memo = {}

    def parses(i, R):
        if i == len(s):
            return 1
        key = (i, R)
        if key not in memo:
            total = parses(i + 1, R)
            for j, r in enumerate(R):
                if r <= i:
                    for L in range(repmin, ml[i][r] + 1):
                        total += parses(i + L, (r,) + R[:j] + R[j + 1:])
            for d in range(1, i + 1):
                for L in range(2, ml[i][d] + 1):
                    total += parses(i + L, (d,) + R[:-1])
            memo[key] = total
        return memo[key]

    return parses(0, (1,) * k)


class Lz77RepeatSlots(unittest.TestCase):
    def test_agree_and_check(self):
        for n in range(0, 9):
            for t in range(8):
                inst = H.generate(n, random.Random(f"lz-test|{n}|{t}"))
                a, b = EN(inst), DP(inst)
                self.assertEqual(a[0], b[0])
                self.assertIs(H.check(inst, a), True)
                self.assertIs(H.check(inst, b), True)
                self.assertIs(H.check(inst, (b[0] + 1, b[1])), False)
                if b[0] > 0:
                    self.assertIs(H.check(inst, (b[0] - 1, b[1])), False)
        for n in (12, 16, 20, 24):
            for t in range(4):
                inst = H.generate(n, random.Random(f"lz-test-big|{n}|{t}"))
                self.assertIs(H.check(inst, DP(inst)), True)

    def test_all_short_binary_strings(self):
        for n in range(0, 8):
            for s in itertools.product((0, 1), repeat=n):
                for k in (1, 2, 3):
                    for repmin in (1, 2, 3):
                        inst = (s, k, repmin)
                        opt = H.oracle_optimum(inst)
                        en, dp = EN(inst), DP(inst)
                        self.assertEqual(en[0], opt)
                        self.assertEqual(dp[0], opt)
                        self.assertLessEqual(opt, 9 * n)
                        if n >= 1:
                            # search-tree nodes (= evaluations + 1) and relaxations against the bounds in PROOFS.md 6
                            self.assertLessEqual(en[1] + 1, (n + 1) * 2 ** (n - 1) * (n + k + 1) ** n)
                            self.assertLessEqual(dp[1], n * (n ** k * (1 + k * n) + n ** (k + 1)))

    def test_known_values(self):
        self.assertEqual(DP(((), 2, 2)), (0, 0))
        self.assertEqual(EN(((), 2, 2)), (0, 0))
        a, b = 0, 1
        s = (a, a, a, a, b, a)                       # 'aaaaba': optimum 32 with one-symbol repeats, 33 without
        for k in (1, 2, 3):
            self.assertEqual(DP((s, k, 1))[0], 32)
            self.assertEqual(EN((s, k, 1))[0], 32)
        self.assertEqual(DP((s, 1, 2))[0], 33)

    def test_wrong_outputs_rejected(self):
        inst = ((0, 0, 0, 0), 1, 2)
        opt = H.oracle_optimum(inst)
        self.assertIs(H.check(inst, (opt, 5)), True)
        for bad in [(opt,), opt, (opt + 1, 5), (opt - 1, 5), (True, 5), (opt, -1), (opt, 1.0), (float(opt), 5),
                    (37, 0)]:
            self.assertIs(H.check(inst, bad), False, bad)

    def test_match_table(self):
        # ml[i][d] = largest L with i + L <= n and s[i+t] == s[i+t-d] for t < L (1 <= d <= i <= n); both copies
        for n in range(0, 9):
            for s in itertools.product((0, 1), repeat=n):
                for mod in (ENM, DPM):
                    ml = mod.match_lengths(s)
                    self.assertEqual(sum(len(row) for row in ml), (n + 1) * (n + 2) // 2)
                    for i in range(n + 1):
                        for d in range(1, i + 1):
                            L = 0
                            while i + L < n and s[i + L] == s[i + L - d]:
                                L += 1
                            self.assertEqual(ml[i][d], L)

    def test_v2_closed_forms(self):
        for m in range(1, 9):
            inst = H.generate_scaling(3 * m, None)
            self.assertEqual(EN(inst)[1], sum(math.factorial(j - 1) * (j + 2) for j in range(1, m + 1)))
        for k in (1, 3):                             # the enumeration count does not depend on k
            for m in range(1, 8):
                self.assertEqual(EN((H.f1_string(m), k, 3))[1], H.enumeration_count_f1(m))
        fact = math.factorial
        for m in range(3, 30):                       # m! + 3(m-1)! <= count <= m! + 3(m-1)! + 6(m-2)!
            count = H.enumeration_count_f1(m)
            self.assertEqual(count, sum(fact(j) for j in range(1, m + 1)) + 2 * sum(fact(j) for j in range(m)))
            self.assertLessEqual(fact(m) + 3 * fact(m - 1), count)
            self.assertLessEqual(count, fact(m) + 3 * fact(m - 1) + 6 * fact(m - 2))
            self.assertLessEqual(sum(fact(j) for j in range(m - 1)), 2 * fact(m - 2))
        for m in range(1, 41):
            inst = H.generate_scaling(3 * m, None)
            self.assertEqual(DP(inst)[1], (4 * m ** 3 - 15 * m ** 2 + 29 * m - 9) // 3)
            self.assertEqual(3 * (DP(inst)[1]), 4 * m ** 3 - 15 * m ** 2 + 29 * m - 9)
        for k in (1, 3):
            for m in range(1, 16):
                inst = (H.f1_string(m), k, 3)
                self.assertEqual(DP(inst)[1], H.dp_count_f1(m, k))
                self.assertEqual(DP(inst)[0], 27 + 15 * (m - 1))
        for k in (1, 2, 3):                          # the slot tuples of block j (PROOFS.md 3.1), m <= 9
            for m in range(1, 10):
                sizes = _states_per_position((H.f1_string(m), k, 3))
                for j in range(1, m + 1):
                    for x in (3 * j - 3, 3 * j - 2, 3 * j - 1):
                        self.assertEqual(sizes[x], H.dp_states_f1(j, k))

    def test_f1_has_m_factorial_parses(self):
        for m in range(1, 7):
            for pad in range(3):
                s = H.f1_string(m, pad)
                self.assertEqual(len(set(s)), m + 2 + pad)
                for k in (1, 2, 3):
                    for repmin in (1, 2, 3):
                        p = _count_parses(s, k, repmin)
                        if repmin == 3:
                            self.assertEqual(p, math.factorial(m))
                        else:
                            self.assertGreaterEqual(p, math.factorial(m))
                        if m <= 4:                   # every complete parse ends with its own token evaluation
                            self.assertGreaterEqual(EN((s, k, repmin))[1], p)

    def test_state_bound(self):
        rng = random.Random("lz-test|states")
        for _ in range(60):
            n = rng.randint(0, 14)
            k = rng.choice((1, 2, 3))
            repmin = rng.choice((1, 2, 3))
            s = tuple(rng.randrange(2) for _ in range(n))
            sizes = _states_per_position((s, k, repmin))
            for i, size in enumerate(sizes):
                self.assertLessEqual(size, 1 if i <= 2 else (i - 2) ** k)
            self.assertLessEqual(sum(sizes), 3 + sum(j ** k for j in range(1, n - 1)))
        for n in range(0, 9):                        # total states stored by the DP, every binary string
            for s in itertools.product((0, 1), repeat=n):
                for k in (1, 2, 3):
                    for repmin in (1, 2, 3):
                        self.assertLessEqual(sum(_states_per_position((s, k, repmin))),
                                             3 + sum(j ** k for j in range(1, n - 1)))
        for k in (1, 2, 3):
            n = 12
            for repmin in (1, 2, 3):
                sizes = _states_per_position(((0,) * n, k, repmin))
                for i in range(2 * k + 1, n + 1):
                    self.assertGreaterEqual(sizes[i], math.prod(i - 2 * t for t in range(1, k + 1)))

    def test_enumeration_stack_bound(self):
        cases = [(s, k, repmin) for n in range(1, 9) for s in itertools.product((0, 1), repeat=n)
                 for k in (1, 2, 3) for repmin in (1, 2, 3)]
        cases += [((0,) * n, k, repmin) for n in range(1, 12) for k in (1, 2, 3) for repmin in (1, 2, 3)
                  if repmin >= 2 or k == 1 or n <= 9]       # a^n, n <= 11 (n <= 9 for k >= 2 with REPMIN = 1)
        cases += [(H.f1_string(m), k, repmin) for m in range(1, 8) for k in (1, 2, 3) for repmin in (1, 2, 3)]
        for inst in cases:
            s, k, repmin = inst
            n = len(s)
            stats = _enumeration_stats(inst)
            if n <= 8:
                self.assertEqual(stats["evaluations"], EN(inst)[1])     # same discipline as the implementation
            self.assertLessEqual(4 * stats["peak"], 4 * n * (1 + k * n) + n ** 3 + 4)
            # PROOFS.md 6.6: every node is popped once; the work besides the pushes is k slot tests and i distance
            # tests per expanded node
            self.assertEqual(stats["popped"], stats["evaluations"] + 1)
            self.assertEqual(stats["slot_tests"], k * stats["expanded"])
            self.assertLessEqual(stats["dist_tests"], (n - 1) * stats["expanded"])

    def test_dp_uncounted_work(self):
        cases = [(s, k, repmin) for n in range(0, 8) for s in itertools.product((0, 1), repeat=n)
                 for k in (1, 2, 3) for repmin in (1, 2, 3)]
        cases += [((0,) * n, k, repmin) for n in (10, 16) for k in (1, 2, 3) for repmin in (1, 2, 3)]
        cases += [(H.f1_string(m), k, 3) for m in (5, 9) for k in (1, 2, 3)]
        for inst in cases:
            s, k, repmin = inst
            n = len(s)
            w = _dp_work(inst)
            self.assertEqual((w["opt"], w["relax"]), DP(inst))      # same loops as the implementation
            self.assertEqual(w["lit"], w["states_below_n"])
            self.assertEqual(w["slot_tests"], k * w["states_below_n"])
            self.assertEqual(w["dist_tests"], n * (n - 1) // 2)
            self.assertLessEqual(w["rep_builds"], w["rep"])
            self.assertLessEqual(w["group_dist"], w["new"])
            self.assertLessEqual(w["states_at_n"], w["relax"] + 1)


if __name__ == "__main__":
    unittest.main()
