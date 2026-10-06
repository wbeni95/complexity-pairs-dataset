"""Unit tests for the exact shape diagnostic engine (methods/shape.py), added in round 2026-10-06f.

Synthetic exact sequences cover every outcome category and every UNDETERMINED reason; wrong claims must give
MISMATCH with the right component. Run:  python -m unittest discover -s tests
"""
from __future__ import annotations

import math
import sys
import unittest
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from methods import exactalg as ea  # noqa: E402
from methods import shape as S  # noqa: E402


def run(cost, block, f, **kw):
    grid = S.grid_from_block(block)
    return S.run(cost, block, grid, [f(n) for n in grid.ns], **kw)


@lru_cache(None)
def fib_calls(n):  # calls of the naive Fibonacci recursion: Theta(phi^n)
    return 1 if n < 2 else 1 + fib_calls(n - 1) + fib_calls(n - 2)


def edit_calls(n):  # calls of the plain edit-distance recursion on two length-n strings: (3+2 sqrt 2)^n / sqrt n
    @lru_cache(None)
    def d(i, j):
        return 1 if i == n or j == n else 1 + d(i + 1, j) + d(i, j + 1) + d(i + 1, j + 1)
    return d(0, 0)


def merge_like(n):  # an exact n log2 n + lower-order count at n = 2^k
    k = n.bit_length() - 1
    return n * k + 3 * n + 1


DOUBLING = {"sequence": "doubling", "n_range": [2, 4096]}
CONSEC = {"sequence": "consecutive", "n_range": [1, 24]}


class CostParsing(unittest.TestCase):
    def expected(self, cost, seq):
        e = S.expected_on_grid(S.parse_cost(cost), seq)
        return ea.pstr(S.minpoly(e.lam)), e.theta

    def test_examples_from_the_design(self):
        self.assertEqual(self.expected("n**log2(7)", "doubling"), ("x - 7", 0))
        self.assertEqual(self.expected("n*log2(n)", "doubling"), ("x - 2", 1))
        self.assertEqual(self.expected("2**n*n", "consecutive"), ("x - 2", 1))
        self.assertEqual(self.expected("((3+2*sqrt(2))**n)/sqrt(n)", "consecutive"), ("x^2 - 6x + 1", Fraction(-1, 2)))

    def test_more_dataset_costs(self):
        self.assertEqual(self.expected("n*(3*log2(n) + 5)", "doubling"), ("x - 2", 1))      # NTT exact form
        self.assertEqual(self.expected("n**2 * (n-1)**2", "consecutive"), ("x - 1", 4))     # Bellman-Ford
        self.assertEqual(self.expected("2**(n-1) + 1", "consecutive"), ("x - 2", 0))        # Deutsch-Jozsa
        self.assertEqual(self.expected("((1 + sqrt(33)) / 4)**n", "consecutive"), ("2x^2 - x - 4", 0))
        self.assertEqual(self.expected("2**(n/3)", "consecutive"), ("x^3 - 2", 0))
        self.assertEqual(self.expected("n**2.5", "doubling"), ("x^2 - 32", 0))
        self.assertEqual(self.expected("phi**n", "consecutive"), ("x^2 - x - 1", 0))
        self.assertEqual(self.expected("1", "consecutive"), ("x - 1", 0))
        self.assertEqual(self.expected("n*log(n)", "doubling"), ("x - 2", 1))

    def test_outside_grid_family(self):
        for cost, seq in (("n*log(n)", "consecutive"), ("n**log2(7)", "consecutive"), ("2**n", "doubling")):
            with self.assertRaises(S.OutsideGridFamily, msg=(cost, seq)):
                S.expected_on_grid(S.parse_cost(cost), seq)

    def test_not_parseable(self):
        for cost in ("factorial(n)", "1.4655712319**n", "n**n", "exp(n)", "n - n", "log(log(n))", "e**n",
                     "n**2.807", "__import__('os')"):
            with self.assertRaises(S.NotParseable, msg=cost):
                S.parse_cost(cost)

    def test_expect_override(self):
        s = S.parse_expect({"base": {"minpoly": [1, -1, 0, -1], "approx": 1.4656}})
        self.assertEqual(ea.pstr(S.minpoly(s.base)), "x^3 - x^2 - 1")
        s = S.parse_expect({"polynomial_factor": "log2(7)", "log_power": "1"})
        e = S.expected_on_grid(s, "doubling")
        self.assertEqual((ea.pstr(S.minpoly(e.lam)), e.theta), ("x - 7", 1))
        with self.assertRaises(S.InvalidBlock):
            S.parse_expect({"base": {"minpoly": [1, 0, -2], "approx": 0.0}})  # +-sqrt 2: approx does not decide


class Matches(unittest.TestCase):
    def assertMatch(self, r):
        self.assertEqual((r["category"], r["reason"]), ("MATCH", "exact_shape_agrees"), r.get("detail"))

    def test_n_log_n_on_doubling(self):
        self.assertMatch(run("n*log2(n)", DOUBLING, merge_like))

    def test_strassen_power_7(self):
        r = run("n**log2(7)", {"sequence": "doubling", "n_range": [16, 512], "holdout": 2},
                lambda n: 4096 * 7 ** (n.bit_length() - 5))
        self.assertMatch(r)
        self.assertEqual(r["found_recurrence"]["holdout"], 2)

    def test_fibonacci_phi(self):
        self.assertMatch(run("phi**n", CONSEC, fib_calls))

    def test_edit_distance_exact_inverse_sqrt(self):
        r = run("((3+2*sqrt(2))**n)/sqrt(n)", CONSEC, edit_calls)
        self.assertMatch(r)
        self.assertEqual(r["found_recurrence"]["recurrence_kind"], "P-recursive")
        self.assertEqual(r["found_recurrence"]["theta"], "-1/2")

    def test_exponential_times_polynomial_and_constant(self):
        self.assertMatch(run("n**2 * 2**n", {"sequence": "consecutive", "n_range": [2, 18]},
                             lambda n: n * n * 2 ** n + 3 * n * 2 ** n + 7))
        self.assertMatch(run("1", CONSEC, lambda n: 20))

    def test_parity_term_is_dominated(self):
        # floor(n/2) = n/2 - 1/4 + (-1)^n/4: root -1 has the modulus of the root 1 but a lower multiplicity
        self.assertMatch(run("n", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: n // 2))

    def test_step_grid(self):
        self.assertMatch(run("2**n", {"sequence": "consecutive", "n_range": [2, 30], "step": 2}, lambda n: 2 ** n + n))


class Mismatches(unittest.TestCase):
    def assertMismatch(self, r, differs):
        self.assertEqual((r["category"], r["reason"]), ("MISMATCH", "differs"), r.get("detail"))
        self.assertEqual(r["differs"], differs)

    def test_n_squared_claimed_for_n_log_n(self):
        r = run("n**2", DOUBLING, merge_like)
        self.assertMismatch(r, ["polynomial_factor", "log_power"])
        self.assertEqual(r["found"]["polynomial_factor"], "n^1")
        self.assertEqual(r["claimed"]["polynomial_factor"], "n^2")

    def test_two_to_the_n_claimed_for_phi(self):
        r = run("2**n", CONSEC, fib_calls)
        self.assertMismatch(r, ["base"])
        self.assertIn("x^2 - x - 1", r["found"]["base"])

    def test_missing_inverse_sqrt(self):
        r = run("(3+2*sqrt(2))**n", CONSEC, edit_calls)
        self.assertMismatch(r, ["polynomial_factor"])
        self.assertEqual(r["found"]["polynomial_factor"], "n^(-1/2)")

    def test_missing_log_factor(self):
        self.assertMismatch(run("n", DOUBLING, merge_like), ["log_power"])

    def test_wrong_polynomial_degree_and_conjugate_root(self):
        self.assertMismatch(run("n**2", CONSEC, lambda n: n ** 3 - n), ["polynomial_factor"])
        # 3 - 2 sqrt 2 has the same minimal polynomial as 3 + 2 sqrt 2 but is a different root
        r = run("(3-2*sqrt(2))**n/sqrt(n)", CONSEC, edit_calls)
        self.assertMismatch(r, ["base"])

    def test_subdominant_claim_central_binomial(self):
        # C(2n, n) ~ 4^n / sqrt(pi n): claiming the edit-distance shape must fail on the base, not pass
        self.assertMismatch(run("((3+2*sqrt(2))**n)/sqrt(n)", CONSEC,
                                lambda n: math.factorial(2 * n) // math.factorial(n) ** 2), ["base"])


class Undetermined(unittest.TestCase):
    def assertReason(self, r, reason):
        self.assertEqual((r["category"], r["reason"]), ("UNDETERMINED", reason), r.get("detail"))

    def test_too_few_terms(self):
        self.assertReason(run("2**n", {"sequence": "consecutive", "n_range": [1, 7]}, lambda n: 2 ** n + n),
                          "too_few_terms")
        # n^4 + 1 has order 5 ((x-1)^5); 8 training terms show only order 4, so "needed" is a lower bound:
        # 2*4 + 2 + 4 = 14 (the true requirement is 2*5 + 2 + 4 = 16)
        r = run("n**4", {"sequence": "consecutive", "n_range": [1, 12]}, lambda n: n ** 4 + 1)
        self.assertReason(r, "too_few_terms")
        self.assertEqual(r["search"]["c_finite"]["needed"], 14)
        self.assertEqual(run("n**4", {"sequence": "consecutive", "n_range": [1, 16]}, lambda n: n ** 4 + 1)["category"],
                         "MATCH")

    def test_no_recurrence_within_limits(self):
        primes = [p for p in range(2, 400) if all(p % d for d in range(2, int(p ** 0.5) + 1))]
        self.assertReason(run("n", {"sequence": "consecutive", "n_range": [1, 30]}, lambda n: primes[n]),
                          "no_recurrence_within_limits")

    def test_holdout_not_reproduced(self):
        self.assertReason(run("2**n", {"sequence": "consecutive", "n_range": [1, 14]},
                              lambda n: 2 ** n if n < 12 else 2 ** n + 5), "holdout_not_reproduced")

    def test_solution_space_not_one_dimensional(self):
        real = S.ea.nullspace

        def two_dim(rows):
            ns = real(rows)
            return ns + [[Fraction(1)] * len(rows[0])] if ns else [[Fraction(1)] * len(rows[0]), [Fraction(2)] * len(rows[0])]

        with mock.patch.object(S.ea, "nullspace", two_dim):
            r = run("factorial(n)", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: math.factorial(n))
        self.assertReason(r, "solution_space_not_one_dimensional")

    def test_factorial_type_growth(self):
        self.assertReason(run("n", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: math.factorial(n) + 1),
                          "factorial_type_growth")

    def test_dominance_not_certified(self):
        r = run("2**n", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: 3 * 2 ** n + (-2) ** n)
        self.assertReason(r, "dominance_not_certified")
        self.assertEqual(r["found_recurrence"]["dominance"], "fails")

    def test_asymptotics_not_determined_by_theta_guard(self):
        with mock.patch.object(S.rc, "theta_numeric", lambda *a, **k: 0.5):  # pretend the data disagree
            r = run("((3+2*sqrt(2))**n)/sqrt(n)", CONSEC, edit_calls)
        self.assertReason(r, "asymptotics_not_determined")

    def test_randomised_non_integer_instance_and_version(self):
        sq = {"sequence": "consecutive", "n_range": [1, 20]}
        self.assertReason(run("n**2", sq, lambda n: n * n, samples=5), "randomised_counts")
        self.assertReason(run("n**2", sq, lambda n: n * n + 0.5), "non_integer_counts")
        self.assertReason(run("n**2", sq, lambda n: n * n, probe={"n_values": [3], "identical": False, "detail": "x"}),
                          "instance_dependent_counts")
        r = run("n**2", {**sq, "python_version_dependent": True}, lambda n: n * n)
        self.assertReason(r, "python_version_dependent")
        self.assertIn("found", r)  # what was found is still recorded

    def test_claim_problems(self):
        self.assertReason(run("factorial(n) + 2**n", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: 2 ** n),
                          "cost_not_parseable")
        self.assertReason(run("n*log(n)", {"sequence": "consecutive", "n_range": [1, 20]}, lambda n: n * n),
                          "cost_outside_grid_family")
        r = run("1.4655712319**n", {"sequence": "consecutive", "n_range": [1, 30]},
                lambda n: S.ea and _narayana(n))
        self.assertReason(r, "cost_not_parseable")
        r = run("1.4655712319**n", {"sequence": "consecutive", "n_range": [1, 30],
                                    "expect": {"base": {"minpoly": [1, -1, 0, -1], "approx": 1.4656}}}, _narayana)
        self.assertEqual(r["category"], "MATCH", r.get("detail"))

    def test_invalid_blocks(self):
        for block in ({"sequence": "doubling", "n_range": [3, 64]},
                      {"sequence": "consecutive", "n_range": [3, 30], "step": 2},
                      {"sequence": "consecutive", "n_range": [1, 100]},
                      {"sequence": "consecutive", "n_range": [10, 5]},
                      {"sequence": "consecutive", "n_range": [1, 20], "holdout": 1},
                      {"sequence": "spiral", "n_range": [1, 20]}):
            with self.assertRaises(S.InvalidBlock, msg=block):
                S.grid_from_block(block)
        r = run("n", {"sequence": "consecutive", "n_range": [1, 20], "expect": {"base": "n"}}, lambda n: n)
        self.assertReason(r, "invalid_shape_block")


@lru_cache(None)
def _narayana(n):  # calls of a naive recursion a(n) = a(n-1) + a(n-3): lambda = root of x^3 - x^2 - 1
    return 1 if n < 3 else 1 + _narayana(n - 1) + _narayana(n - 3)


class Bookkeeping(unittest.TestCase):
    def test_every_reason_belongs_to_one_category(self):
        for reason, (cat, text) in S.REASONS.items():
            self.assertIn(cat, S.CATEGORIES)
            self.assertTrue(text)
        with self.assertRaises(AssertionError):
            S.outcome("MATCH", "too_few_terms")

    def test_probe_points(self):
        g = S.grid_from_block({"sequence": "consecutive", "n_range": [1, 20]})
        self.assertEqual(S.probe_points(g), [3, 4, 5])
        g = S.grid_from_block({"sequence": "doubling", "n_range": [2, 1024]})
        self.assertEqual(S.probe_points(g), [4, 8, 16])


if __name__ == "__main__":
    unittest.main()
