"""Unit tests for the methods/ package (exact recurrence guessing, algebra, LP, Boolean measures, CSP predictor).

Added 2026-10-06 (round 2026-10-06d). Each test checks an exact, independently known value.
"""
from __future__ import annotations

import math
import random
import sys
import unittest
from fractions import Fraction
from itertools import product
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from methods import boolean as bf  # noqa: E402
from methods import csp  # noqa: E402
from methods import exactalg as ea  # noqa: E402
from methods import fitting as ft  # noqa: E402
from methods import recurrences as rc  # noqa: E402
from methods.lp import solve_lp  # noqa: E402


class TestRecurrences(unittest.TestCase):
    def test_berlekamp_massey_fibonacci(self):
        fib = [0, 1]
        for _ in range(20):
            fib.append(fib[-1] + fib[-2])
        self.assertEqual(rc.berlekamp_massey(fib), [1, 1])

    def test_c_finite_double_root_gives_log_power(self):
        seq = [n * 2 ** n for n in range(16)]  # n 2^n: charpoly (x - 2)^2
        g = rc.guess_c_finite(seq)
        gr = rc.growth_from_charpoly(g["charpoly"])
        self.assertEqual(ea.pint(gr["minpoly"]), [-2, 1])
        self.assertEqual(gr["multiplicity"], 2)

    def test_holonomic_guess_and_theta_central_delannoy(self):
        D = [1, 3]
        for n in range(2, 26):
            D.append((3 * (2 * n - 1) * D[-1] - (n - 1) * D[-2]) // n)
        g = rc.search_p_recursive(D)
        self.assertEqual((g["order"], g["degree"]), (2, 1))
        chi = rc.p_recursive_characteristic(g)[0]
        gr = rc.growth_from_charpoly(chi)
        self.assertEqual(ea.pint(gr["minpoly"]), [1, -6, 1])
        self.assertEqual(rc.theta_p_recursive(g, gr["minpoly"]), [Fraction(-1, 2)])

    def test_no_guess_without_enough_terms(self):
        self.assertIsNone(rc.guess_p_recursive([1, 2, 3, 5, 8], order=2, degree=2))


class TestExactAlgebra(unittest.TestCase):
    def test_kronecker_factors(self):
        p = ea.pmul([-1, 1], [1, -6, 1])
        self.assertEqual(sorted(map(tuple, ea.factor_kronecker(p))), sorted([(-1, 1), (1, -6, 1)]))
        self.assertTrue(ea.is_irreducible([-1, -1, -1, -1, 1]))
        self.assertFalse(ea.is_irreducible([4, 0, 0, 0, 1]))  # x^4 + 4 = (x^2 + 2x + 2)(x^2 - 2x + 2)

    def test_real_root_isolation(self):
        lo, hi = ea.dominant_real_root([-2, 0, 1], Fraction(1, 10 ** 20))
        self.assertTrue(lo * lo < 2 < hi * hi)
        self.assertEqual(ea.count_real_roots([-1, 0, 0, 1], -10, 10), 1)

    def test_lll_minimal_polynomial(self):
        x = 1 + Fraction(14142135623730950488, 10 ** 19)  # 1 + sqrt 2 to 19 digits
        self.assertEqual(ea.minpoly_by_lll(x, 4, Fraction(1, 10 ** 18)), [-1, -2, 1])

    def test_number_field_inverse(self):
        K = ea.NumberField([-2, 0, 1])  # Q(sqrt 2)
        a = [Fraction(1), Fraction(1)]  # 1 + sqrt 2
        self.assertEqual(K.mul(a, K.inv(a)), [Fraction(1)])


class TestLP(unittest.TestCase):
    def test_optimal(self):
        # max 3x + 2y s.t. x + y <= 4, x + 3y <= 6, x <= 3 -> (3, 1), value 11
        r = solve_lp([3, 2], [[1, 1], [1, 3], [1, 0]], [4, 6, 3])
        self.assertEqual(r["status"], "optimal")
        self.assertEqual(r["value"], 11)

    def test_infeasible_and_unbounded(self):
        self.assertEqual(solve_lp([1], [[1], [-1]], [1, -2])["status"], "infeasible")
        self.assertEqual(solve_lp([1, 0], [[-1, 1]], [1])["status"], "unbounded")

    def test_free_variables_and_equalities(self):
        r = solve_lp([-1, 0], A_eq=[[1, 1]], b_eq=[Fraction(-5, 2)], A_ub=[[0, 1]], b_ub=[0], free=[0, 1])
        self.assertEqual(r["x"][0], Fraction(-5, 2))


class TestBoolean(unittest.TestCase):
    def test_basic_measures(self):
        self.assertEqual(bf.D(bf.OR(3), 3), 3)
        self.assertEqual(bf.deg(bf.PARITY(4), 4), 4)
        self.assertEqual(bf.deg(bf.AND(3), 3), 3)
        self.assertEqual(bf.sensitivity(bf.OR(4), 4), 4)
        self.assertEqual(bf.block_sensitivity(bf.MAJ(3), 3), 2)
        self.assertEqual(bf.certificate_complexity(bf.MAJ(3), 3), 2)

    def test_npn_class_counts(self):
        self.assertEqual(len(bf.npn_classes(2)), 4)
        self.assertEqual(len(bf.npn_classes(3)), 14)

    def test_exchange_certified_and_matches_lp(self):
        r = bf.best_uniform_error([0, 1, 1, 1, 1, 1], 1)
        self.assertTrue(r["certified"])
        self.assertEqual(r["error"], Fraction(2, 5))  # (n-1)/(2n) for n = 5
        self.assertEqual(bf.best_multilinear_error(bf.OR(3), 3, 1), Fraction(1, 3))

    def test_approximate_degree_values(self):
        self.assertEqual(bf.adeg_symmetric([0, 1, 1, 1, 1])[0], 2)          # OR_4
        self.assertEqual(bf.adeg_symmetric([k % 2 for k in range(7)])[0], 6)  # PARITY_6
        self.assertEqual(bf.adeg_general(bf.OR(4), 4), 2)


class TestCSP(unittest.TestCase):
    def test_polymorphic_equals_syntactic_arity_2(self):
        for R in csp.all_relations(2):
            self.assertEqual(csp.polymorphism_classes(R), csp.syntactic_classes(R, 2))

    def test_predictions(self):
        cl = lambda s: frozenset(t for t in product((0, 1), repeat=len(s)) if any(t[i] == s[i] for i in range(len(s))))  # noqa: E731
        self.assertEqual(csp.predict([cl(s) for s in product((0, 1), repeat=2)]), "P (bijunctive)")
        self.assertEqual(csp.predict([cl(s) for s in product((0, 1), repeat=3)]), "NP-complete")
        one_in_three = frozenset({(1, 0, 0), (0, 1, 0), (0, 0, 1)})
        self.assertEqual(csp.predict([one_in_three]), "NP-complete")

    def test_solvers_agree_with_brute_force(self):
        xor0 = frozenset(t for t in product((0, 1), repeat=3) if sum(t) % 2 == 0)
        xor1 = frozenset(t for t in product((0, 1), repeat=3) if sum(t) % 2 == 1)
        rng = random.Random(1)
        for _ in range(20):
            inst = csp.random_instance([xor0, xor1], 8, 6, rng)
            bs, _, cnt = csp.brute_force(inst)
            s, w, c = csp.solve_affine(inst)
            self.assertEqual((s, c), (bs, cnt))
            if s:
                self.assertTrue(csp.satisfies(inst, w))
        neq = frozenset({(0, 1), (1, 0)})
        odd_cycle = (3, [(neq, (0, 1)), (neq, (1, 2)), (neq, (2, 0))])
        self.assertFalse(csp.solve_2sat(odd_cycle)[0])
        self.assertFalse(csp.brute_force(odd_cycle)[0])


class TestFitting(unittest.TestCase):
    def test_log_factor_needs_tight_tolerance(self):
        ns = ft.geometric_grid(1000, 100000, 8)
        cost = lambda n: n * math.log(n)  # noqa: E731
        self.assertFalse(ft.noise_free_diagnostic(cost, ns, 0.25)["resolves"])
        self.assertTrue(ft.noise_free_diagnostic(cost, ns, 0.03)["resolves"])

    def test_slope_matches_validator(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
        from validate import fit_slope
        xs, ys = [1.0, 2.0, 4.0], [2.0, 3.5, 9.0]
        self.assertAlmostEqual(ft.slope(xs, ys), fit_slope(xs, ys), places=12)


if __name__ == "__main__":
    unittest.main()
