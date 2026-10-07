"""Tests for pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp.

The entry's problem is the interval DP with inclusion-monotone weights (max) or anti-monotone weights (min); the
maximum-cost BST (form (p, q)) is its main instance. Checked here: the three implementations agree on every family
and both forms; both oracle tiers accept the true optimum and reject wrong values, and the certificate never vouches
for a wrong value outside the precondition; Theorem E' (the endpoint law) holds exhaustively for small monotone
tables (max) and their negations (min), and for small non-negative frequencies; the BST precondition is exactly the
adjacent-sum condition; strict adjacent sums leave no interior maximiser; the stated counterexamples and controls
fail as stated; -inf entries; the exact V2 counts equal the closed forms in every form and direction; the
implementations leave their input unchanged. Runs in a few seconds.
"""
import importlib.util
import itertools
import math
import random
import unittest
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _table(n, entries):
    """Weight table with w[i][j] = entries[(i, j)] for i < j (None elsewhere); the direction is added by the caller."""
    return tuple(tuple(entries.get((i, j)) if j > i else None for j in range(n + 1)) for i in range(n + 1))


def _neg(w):
    return tuple(tuple(None if x is None else -x for x in row) for row in w)


def _monotone_tables(n, values):
    """Every table that is monotone under inclusion in the order of the list `values`."""
    ivs = [(i, i + d) for d in range(1, n + 1) for i in range(n - d + 1)]
    idx = {}

    def rec(t):
        if t == len(ivs):
            yield _table(n, {iv: values[k] for iv, k in idx.items()})
            return
        i, j = ivs[t]
        lb = 0 if j - i == 1 else max(idx[(i + 1, j)], idx[(i, j - 1)])
        for v in range(lb, len(values)):
            idx[(i, j)] = v
            yield from rec(t + 1)
        del idx[(i, j)]

    yield from rec(0)


class MaxCostBSTEntry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "test_mcb_harness")
        cls.rec = staticmethod(_load(E + "implementations/recursion.py", "test_mcb_rec").maxbst_recursive)
        cls.cub = staticmethod(_load(E + "implementations/cubic_dp.py", "test_mcb_cub").maxbst_cubic)
        cls.end = staticmethod(_load(E + "implementations/endpoint_dp.py", "test_mcb_end").maxbst_endpoint)

    # ---------------------------------------------------------------- agreement and the oracle
    def test_agree_and_enumeration_tier(self):
        for n in range(0, 10):
            for t in range(6):
                inst = self.H.generate(n, random.Random(f"test-mcb|agree|{n}|{t}"))
                a, b, c = self.rec(inst), self.cub(inst), self.end(inst)
                self.assertEqual(a, b)
                self.assertEqual(b, c)
                self.assertIs(self.H.check(inst, c), True)
                self.assertIs(self.H.check(inst, c + 1), False)
                self.assertIs(self.H.check(inst, c - 1), False)
            p, q = self.H.instance_of("small", n, random.Random(f"test-mcb|bst|{n}"))
            self.assertEqual(self.end((p, q)), self.H.brute_force_max(p, q))

    def test_every_family(self):
        for fam in self.H.ALL_FAMILIES:
            for n in range(0, 9):
                inst = self.H.instance_of(fam, n, random.Random(f"test-mcb|family|{fam}|{n}"))
                self.assertTrue(self.H.satisfies_precondition(inst), (fam, n))
                v = self.cub(inst)
                self.assertEqual(self.end(inst), v, (fam, n))
                if n <= 7:
                    self.assertEqual(self.rec(inst), v)
                self.assertIs(self.H.check(inst, v), True, (fam, n))
                self.assertIs(self.H.check(inst, v + 1), False)
                self.assertIs(self.H.check(inst, v - Fraction(1, 2)), False)
        inst = self.H.instance_of("g_rational", 5, random.Random(1))
        self.assertIs(self.H.check(inst, 1.5), False)  # a float is never an exact output

    def test_certificate_tier(self):
        for fam in ("small", "heavy_ends", "g_submax", "g_tight", "g_rational", "a_neg_tight", "a_reciprocal"):
            for n in (11, 15, 24, 40):
                inst = self.H.instance_of(fam, n, random.Random(f"test-mcb|cert|{fam}|{n}"))
                v = self.cub(inst)
                self.assertEqual(v, self.end(inst))
                cert = (self.H.table_certificate(*inst) if self.H.is_table_form(inst)
                        else self.H.path_certificate(*inst))
                self.assertTrue(cert["valid"])
                self.assertEqual(cert["lower"], v)
                self.assertEqual(cert["upper"], v)
                self.assertIs(self.H.check(inst, v), True)
                self.assertIs(self.H.check(inst, v + 1), False)
                self.assertIs(self.H.check(inst, v - 1), False)

    def test_certificate_never_vouches_outside_the_precondition(self):
        rng = random.Random("test-mcb|outside")
        for t in range(60):
            n = rng.randint(11, 18)
            if t % 3 == 0:
                inst = (tuple(rng.randint(-20, 20) for _ in range(n)),
                        tuple(rng.randint(-20, 20) for _ in range(n + 1)))
            else:
                sense = "max" if t % 3 == 1 else "min"
                inst = (sense, _table(n, {(i, j): rng.randint(0, 20)
                                          for i in range(n + 1) for j in range(i + 1, n + 1)}))
            true, e = self.cub(inst), self.end(inst)
            self.assertIn(self.H.check(inst, true), (True, None))
            if e != true:
                self.assertIn(self.H.check(inst, e), (False, None))

    # ---------------------------------------------------------------- Theorem E' and its consequences
    def test_endpoint_law_exhaustive_small(self):
        counts = []
        for n in range(1, 5):
            k = 0
            for w in _monotone_tables(n, list(range(3))):
                k += 1
                self.assertTrue(self.H.is_monotone(w))
                self.assertEqual(self.end(("max", w)), self.cub(("max", w)))
                self.assertEqual(self.end(("min", _neg(w))), self.cub(("min", _neg(w))))
            counts.append(k)
        self.assertEqual(counts, [3, 14, 84, 594])

    def test_bst_corollary_exhaustive_small(self):
        for n in range(1, 5):
            for t in itertools.product(range(3), repeat=2 * n + 1):
                inst = (t[:n], t[n:])
                self.assertEqual(self.end(inst), self.cub(inst), inst)

    def test_bst_precondition_is_the_adjacent_sum_condition(self):
        n = 3
        for t in itertools.product(range(-1, 2), repeat=2 * n + 1):
            p, q = t[:n], t[n:]
            local = (all(q[l - 1] + p[l - 1] >= 0 for l in range(1, n))
                     and all(p[l - 1] + q[l] >= 0 for l in range(2, n + 1)))
            self.assertEqual(self.H.satisfies_precondition((p, q)), local)
            if local:
                self.assertEqual(self.end((p, q)), self.cub((p, q)))
        inst = ((1, -1, 1), (0, 1, 1, 0))  # a negative frequency, monotone weights
        self.assertTrue(self.H.satisfies_precondition(inst))
        self.assertEqual(self.end(inst), 7)
        self.assertEqual(self.cub(inst), 7)

    def test_strict_adjacent_sums_give_no_interior_maximiser(self):
        def interior_maximiser(w, n):
            c = {(i, i): 0 for i in range(n + 1)}
            found = False
            for d in range(1, n + 1):
                for i in range(n - d + 1):
                    j = i + d
                    vals = {k: c[(i, k - 1)] + c[(k, j)] for k in range(i + 1, j + 1)}
                    best = max(vals.values())
                    found = found or any(vals[k] == best for k in range(i + 2, j))
                    c[(i, j)] = w[i][j] + best
            return found

        cases = [(n, (0,) * n, q) for n in range(3, 7) for q in itertools.product((1, 2), repeat=n + 1)]
        cases += [(n, p, q) for n in (3, 4) for p in itertools.product((1, 2), repeat=n)
                  for q in itertools.product((0, 1), repeat=n + 1)]
        for n, p, q in cases:
            self.assertFalse(interior_maximiser(self.H.bst_weights(p, q), n), (p, q))
        self.assertEqual(len(cases), 880)

    def test_local_monotonicity_test_equals_definition(self):
        rng = random.Random("test-mcb|local")
        for _ in range(300):
            n = rng.randint(1, 6)
            w = _table(n, {(i, j): rng.randint(0, 2) + (j - i) for i in range(n + 1) for j in range(i + 1, n + 1)})
            definition = all(w[b][c] <= w[a][d] for a in range(n + 1) for d in range(a + 1, n + 1)
                             for b in range(a, d) for c in range(b + 1, d + 1))
            self.assertEqual(self.H.is_monotone(w), definition)

    def test_minus_infinity_entries(self):
        for n in range(1, 4):
            for w in _monotone_tables(n, [-math.inf, 0, 1, 2]):
                self.assertEqual(self.end(("max", w)), self.cub(("max", w)))
            for w in _monotone_tables(n, [math.inf, 0, -1, -2]):  # anti-monotone, under min
                self.assertEqual(self.end(("min", w)), self.cub(("min", w)))

    # ---------------------------------------------------------------- outside the precondition
    def test_negative_frequency_counterexamples(self):
        for inst, best, endpoint in ((((0, -1, 0), (0, 0, 0, 0)), -1, -2),      # smallest: middle key at the root
                                     (((0, 0, 0), (0, -1, -1, 0)), -4, -5),     # only gap frequencies negative
                                     (((-11, -3, 11), (18, -8, -12, -7)), -21, -29)):
            self.assertEqual(self.cub(inst), best)
            self.assertEqual(self.rec(inst), best)
            self.assertEqual(self.H.brute_force_max(*inst), best)
            self.assertEqual(self.end(inst), endpoint)
            self.assertFalse(self.H.satisfies_precondition(inst))

    def test_controls(self):
        w = _table(3, {(i, j): j - i for i in range(4) for j in range(i + 1, 4)})  # monotone, under MIN
        self.assertEqual(w, self.H.bst_weights((1, 1, 1), (0, 0, 0, 0)))
        self.assertEqual(self.cub(("min", w)), 5)  # the optimal BST with p = (1, 1, 1), q = 0
        self.assertEqual(self.end(("min", w)), 6)
        self.assertIs(self.H.check(("min", w), 6), False)
        w = _table(3, {(0, 2): 1, (0, 3): 1, (1, 3): 1, (0, 1): 0, (1, 2): 0, (2, 3): 0})  # monotone, under MIN
        self.assertTrue(self.H.is_monotone(w))
        self.assertEqual(self.cub(("min", w)), 1)
        self.assertEqual(self.end(("min", w)), 2)
        w = _table(3, {(i, j): 1 if (i, j) in ((0, 1), (2, 3)) else 0 for i in range(4) for j in range(i + 1, 4)})
        self.assertFalse(self.H.is_monotone(w))  # arbitrary weights, under max
        self.assertEqual(self.cub(("max", w)), 2)
        self.assertEqual(self.end(("max", w)), 1)
        self.assertIs(self.H.check(("max", w), 1), False)

    def test_single_heavy_end_gap(self):
        inst = ((0, 0, 0), (0, 0, 0, 1))  # the maximum needs the root k_1 at (0, 3); 2 is a wrong value
        self.assertEqual(self.rec(inst), 3)
        self.assertEqual(self.cub(inst), 3)
        self.assertEqual(self.end(inst), 3)
        self.assertIs(self.H.check(inst, 2), False)

    # ---------------------------------------------------------------- V2 counts and hygiene
    def test_closed_forms(self):
        def counts(fn, n, fam=None):
            if fam is None:
                inst = self.H.generate_scaling(n, random.Random(f"test-mcb|cf|{n}"))
            else:
                inst = self.H.wrap_counting(self.H.instance_of(fam, n, random.Random(f"test-mcb|cf|{fam}|{n}")))
                self.H.reset_counters()
            fn(inst)
            return self.H.reported_cost(None)

        for fam in (None, "small", "g_upward", "a_neg_upward"):
            for n in range(1, 9):
                self.assertEqual(counts(self.rec, n, fam), (3 ** (n - 1) - 1) // 2)
            for n in range(0, 31):
                self.assertEqual(counts(self.cub, n, fam), (n + 1) * n * (n - 1) // 6)
            for n in range(0, 61):
                self.assertEqual(counts(self.end, n, fam), n * (n - 1) // 2)

    def test_input_unchanged_and_seeded_generator(self):
        for n in (0, 1, 5, 9):
            for t in range(4):
                a = self.H.generate(n, random.Random(f"test-mcb|gen|{n}|{t}"))
                b = self.H.generate(n, random.Random(f"test-mcb|gen|{n}|{t}"))
                self.assertEqual(a, b)
                if self.H.is_table_form(a):
                    inst = (a[0], [list(row) for row in a[1]])
                    snap = (a[0], [list(row) for row in a[1]])
                else:
                    inst = (list(a[0]), list(a[1]))
                    snap = (list(a[0]), list(a[1]))
                for fn in (self.rec, self.cub, self.end):
                    fn(inst)
                    self.assertEqual(inst, snap)
        for fam in self.H.FAMILIES:
            p, q = self.H.instance_of(fam, 7, random.Random(fam))
            self.assertEqual(len(q), len(p) + 1)
            self.assertTrue(all(x >= 0 for x in p + q))
        for fam in self.H.GENERAL_FAMILIES + self.H.MIN_FAMILIES:
            sense, w = self.H.instance_of(fam, 7, random.Random(fam))
            self.assertEqual(sense, "max" if fam in self.H.GENERAL_FAMILIES else "min")
            self.assertEqual(len(w), 8)


if __name__ == "__main__":
    unittest.main()
