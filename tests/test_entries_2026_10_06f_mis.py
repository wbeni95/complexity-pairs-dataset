"""Fast tests for pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp (well under 10 s)."""
import importlib.util
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "t06f_mis_harness")
BF = _load(ENTRY / "implementations" / "brute_force.py", "t06f_mis_bf").mwis_brute_force
DP = _load(ENTRY / "implementations" / "column_dp.py", "t06f_mis_dp").mwis_column_dp


def _grid(weights, code):
    k, n = len(weights), len(weights[0])
    diag = tuple(tuple(code for _ in range(n - 1)) for _ in range(k - 1))
    return k, n, tuple(tuple(r) for r in weights), diag


class SmallCases(unittest.TestCase):
    def test_empty_and_single(self):
        for fn in (BF, DP):
            self.assertEqual(fn((3, 0, ((), (), ()), ((), ()))), (0, ()))
            self.assertEqual(fn((1, 1, ((7,),), ())), (7, ((0, 0),)))

    def test_square_with_and_without_diagonals(self):
        w = ((5, 1), (1, 5))
        for fn in (BF, DP):
            self.assertEqual(fn(_grid(w, 0))[0], 10)     # plain 4-cycle: opposite corners
            self.assertEqual(fn(_grid(w, 1))[0], 5)      # diagonal (0,0)-(1,1) blocks them
            self.assertEqual(fn(_grid(w, 2))[0], 10)     # the other diagonal does not
            self.assertEqual(fn(_grid(w, 3))[0], 5)      # king's graph K_4

    def test_king_graph_uniform(self):
        # unit weights on the 3 x 3 king's graph: the four corners
        g = _grid(((1, 1, 1), (1, 1, 1), (1, 1, 1)), 3)
        for fn in (BF, DP):
            self.assertEqual(fn(g)[0], 4)


class Agreement(unittest.TestCase):
    def test_battery(self):
        for n in range(0, 5):
            for t in range(12):
                inst = H.generate(n, random.Random(f"unit|{n}|{t}"))
                a, b = BF(inst), DP(inst)
                self.assertEqual(a[0], b[0])
                self.assertIs(H.check(inst, a), True)
                self.assertIs(H.check(inst, b), True)

    def test_dp_vs_oracle_larger(self):
        for n in (10, 25):
            for t in range(5):
                inst = H.generate(n, random.Random(f"unit-large|{n}|{t}"))
                self.assertIs(H.check(inst, DP(inst)), True)


class Oracle(unittest.TestCase):
    def test_rejects_wrong_outputs(self):
        for n in range(1, 6):
            for t in range(6):
                inst = H.generate(n, random.Random(f"unit-oracle|{n}|{t}"))
                k, _, w, d = inst
                value, chosen = DP(inst)
                self.assertIs(H.check(inst, (value + 1, chosen)), False)
                self.assertIs(H.check(inst, (value, chosen + ((k, 0),))), False)
                self.assertIs(H.check(inst, value), False)
                pos = [v for v in chosen if w[v[0]][v[1]] > 0]
                if pos:
                    rest = tuple(v for v in chosen if v != pos[0])
                    self.assertIs(H.check(inst, (sum(w[r][c] for r, c in rest), rest)), False)
                pairs = H.adjacent_pairs(k, n, d)
                if chosen:
                    nb = [u for p in pairs if chosen[0] in p for u in p if u != chosen[0] and u not in chosen]
                    if nb:
                        bigger = tuple(sorted(chosen + (nb[0],)))
                        self.assertIs(H.check(inst, (sum(w[r][c] for r, c in bigger), bigger)), False)


class Counts(unittest.TestCase):
    def test_exact_counts(self):
        for n in range(1, 5):
            H.reset_counters()
            BF(H.generate_scaling(n, random.Random(n)))
            self.assertEqual(H.reported_cost(None), 3 * n * 2 ** (3 * n - 1))
        for n in (1, 2, 7, 30):
            H.reset_counters()
            out = DP(H.generate_scaling(n, random.Random(n)))
            self.assertEqual(H.reported_cost(out), 10 * n - 5)

    def test_no_mutation(self):
        inst = H.generate(4, random.Random(5))
        import copy
        snap = copy.deepcopy(inst)
        BF(inst)
        DP(inst)
        self.assertEqual(inst, snap)


if __name__ == "__main__":
    unittest.main()
