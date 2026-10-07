"""Fast tests for pairs/first-match-rule-ordering-enumeration-vs-subset-dp (a few seconds).

The two implementations agree on seeded instances, check() accepts correct outputs and rejects deliberately wrong
ones, the exact V2 counts equal the closed forms stated in entry.json, the feedback-arc-set reduction gives the
minimum feedback arc set on a small digraph, and items matched by at most two rules give a linear ordering
instance.
"""
import importlib.util
import itertools
import math
import random
import sys
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


H = _load(ENTRY / "harness.py", "test_fm_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "test_fm_enum").first_match_order_enumeration
DP = _load(ENTRY / "implementations" / "subset_dp.py", "test_fm_dp").first_match_order_subset_dp


class FirstMatchRuleOrdering(unittest.TestCase):
    def test_agree_and_check(self):
        for k in range(0, 7):
            for t in range(6):
                inst = H.generate(k, random.Random(f"fm-test|{k}|{t}"))
                a, b = EN(inst), DP(inst)
                self.assertEqual(a[0], b[0])
                self.assertIs(H.check(inst, a), True)
                self.assertIs(H.check(inst, b), True)
                self.assertIs(H.check(inst, (b[0] + 1, b[1])), False)
                if k >= 2:
                    self.assertIs(H.check(inst, (b[0], (b[1][0],) * k)), False)

    def test_empty_rule_set(self):
        inst = (0, ((), ()), ((), ()), (3, 4))
        self.assertEqual(EN(inst), (7, ()))
        self.assertEqual(DP(inst), (7, ()))
        self.assertIs(H.check(inst, (7, ())), True)

    def test_order_matters_and_worse_order_rejected(self):
        # two rules, one item matched by both: cost 0 if rule 0 comes first, 5 if rule 1 does
        inst = (2, ((1, 1),), ((0, 5),), (7,))
        self.assertEqual(DP(inst), (0, (0, 1)))
        self.assertEqual(EN(inst), (0, (0, 1)))
        self.assertIs(H.check(inst, (5, (1, 0))), False)      # honest cost of a worse order
        self.assertIs(H.check(inst, (0, (1, 0))), False)      # optimal cost claimed for the worse order

    def test_costs_at_non_matching_positions_ignored(self):
        # rule 1 does not match the item; its cost entry 0 must not be used
        inst = (2, ((1, 0),), ((4, 0),), (9,))
        self.assertEqual(EN(inst)[0], 4)
        self.assertEqual(DP(inst)[0], 4)

    def test_closed_forms(self):
        for k in range(2, 8):
            inst = H.generate_scaling(k, random.Random(k))
            EN(inst)
            self.assertEqual(H.reported_cost(None), math.factorial(k) * (k + 1) * (k + 3) // 3 - 1)
        for k in range(2, 12):
            inst = H.generate_scaling(k, random.Random(k))
            DP(inst)
            self.assertEqual(H.reported_cost(None), 3 * k * k + (7 * k - 2) * 2 ** (k - 1) + 2)

    def test_feedback_arc_set_reduction(self):
        # directed 3-cycle 0 -> 1 -> 2 -> 0 plus the arc 0 -> 2 (weight 4): minimum feedback arc set weight 1
        arcs = [(0, 1, 1), (1, 2, 1), (2, 0, 1), (0, 2, 4)]
        match = tuple(tuple(1 if r in (u, v) else 0 for r in range(3)) for u, v, _ in arcs)
        cost = tuple(tuple(w if r == v else 0 for r in range(3)) for u, v, w in arcs)
        inst = (3, match, cost, (0,) * len(arcs))
        self.assertEqual(DP(inst)[0], 1)
        self.assertEqual(EN(inst)[0], 1)
        for order in itertools.permutations(range(3)):
            pos = {r: p for p, r in enumerate(order)}
            backward = sum(w for u, v, w in arcs if pos[v] < pos[u])
            self.assertEqual(H.order_cost(inst, order), backward)

    def test_at_most_two_rules_is_linear_ordering(self):
        rng = random.Random("fm-test|lop")
        for _ in range(30):
            k = rng.randint(1, 5)
            match, cost, default = [], [], []
            for _ in range(rng.randint(0, 2 * k + 2)):
                rs = rng.sample(range(k), min(rng.choice((0, 1, 2, 2)), k))
                match.append(tuple(1 if r in rs else 0 for r in range(k)))
                cost.append(tuple(rng.randint(0, 9) for _ in range(k)))
                default.append(rng.randint(0, 9))
            inst = (k, tuple(match), tuple(cost), tuple(default))
            const, w = 0, [[0] * k for _ in range(k)]
            for i, row in enumerate(match):
                rs = [r for r in range(k) if row[r]]
                if not rs:
                    const += default[i]
                elif len(rs) == 1:
                    const += cost[i][rs[0]]
                else:
                    a, b = rs
                    w[a][b] += cost[i][a]
                    w[b][a] += cost[i][b]
            for order in itertools.permutations(range(k)):
                lop = const + sum(w[order[p]][order[q]] for p in range(k) for q in range(p + 1, k))
                self.assertEqual(H.order_cost(inst, order), lop)


if __name__ == "__main__":
    unittest.main()
