"""Unit tests for the mutation engine (mutations/). Fast: a few seconds in total."""
import hashlib
import sys
import time
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from mutations import algebra as A  # noqa: E402
from mutations import engine, rewrite  # noqa: E402
from mutations.engine import Mutant  # noqa: E402

MM = "pairs/matrix-multiplication-naive-vs-strassen/implementations/"
RQ = "pairs/range-minimum-queries-naive-vs-sparse-table/implementations/"


def _sha(rel):
    return hashlib.sha256((REPO / rel).read_bytes()).hexdigest()


class TestRewrite(unittest.TestCase):
    def test_copy_does_not_touch_source(self):
        before = _sha(MM + "strassen.py")
        mod = rewrite.load_copy(MM + "strassen.py", [("const", {"CUTOFF": 1})])
        self.assertEqual(mod.CUTOFF, 1)
        self.assertEqual(_sha(MM + "strassen.py"), before)
        self.assertEqual(mod.__mutation__["sha256"], before)

    def test_unmatched_pattern_is_an_error(self):
        with self.assertRaises(rewrite.RewriteError):
            rewrite.load_copy(MM + "naive.py", [("flip", ["a < b"])])

    def test_compare_flip_turns_kadane_into_min_subarray(self):
        mod = rewrite.load_copy("pairs/maximum-subarray/implementations/kadane.py",
                                [("flip", ["ending_here < 0", "ending_here > best"])])
        self.assertEqual(mod.max_subarray_kadane([3, -4, 2, -5, 1]), -7)

    def test_relax_to_accumulate(self):
        mod = rewrite.load_copy(RQ + "naive_scan.py", [("relax_accumulate", ["x < m"])])
        S = A.monoids()["Sum"]
        TE = A.make_tropical_elem(S, "min")
        out = mod.rmq_naive(((TE(1), TE(2), TE(3)), ((0, 2), (1, 1))))
        self.assertEqual([o.v for o in out], [6, 2])


class TestAlgebra(unittest.TestCase):
    def test_tropical_properties(self):
        p = A.check_properties(A.MinPlus())
        self.assertTrue(p["add_idempotent"]["holds"])
        self.assertTrue(p["add_selective"]["holds"])
        self.assertFalse(p["add_inverse_exists"]["holds"])
        self.assertTrue(p["distributive_left"]["holds"])
        self.assertTrue(p["absorptive_one_plus_a_is_one"]["holds"])
        self.assertFalse(A.check_properties(A.MaxPlus())["absorptive_one_plus_a_is_one"]["holds"])

    def test_max_times_with_negatives_is_not_distributive(self):
        p = A.check_properties(A.MaxTimesZ())
        self.assertFalse(p["distributive_left"]["holds"])
        self.assertIsNotNone(p["distributive_left"]["witness"])

    def test_octonions_power_associative_not_associative(self):
        p = A.check_properties(A.mul_magmas()["Octonion"])
        self.assertFalse(p["mul_associative"]["holds"])
        self.assertTrue(p["mul_power_associative_to_6"]["holds"])

    def test_roots_of_unity(self):
        w17 = A.check_properties(A.Zp(17))["primitive_roots_of_unity"]["witness"]
        self.assertIsNotNone(w17["16"])
        w = A.check_properties(A.Zp(1000003))["primitive_roots_of_unity"]["witness"]
        self.assertIsNotNone(w["2"])
        self.assertIsNone(w["4"])
        self.assertIsNone(A.check_properties(A.IntRing())["primitive_roots_of_unity"]["witness"]["4"])

    def test_gf2_two_not_invertible(self):
        self.assertFalse(A.check_properties(A.GF2())["two_invertible"]["holds"])
        self.assertTrue(A.check_properties(A.Zp(7))["two_invertible"]["holds"])

    def test_ring_elem_needs_negation(self):
        RE = A.make_ring_elem(A.MinPlus())
        with self.assertRaises(A.UndefinedOp):
            RE(3) - RE(1)
        self.assertEqual((RE(3) + RE(1)).v, 1)          # ⊕ = min
        self.assertEqual((RE(3) * RE(1)).v, 4)          # ⊗ = +
        self.assertEqual((0 + RE(5)).v, 5)              # literal 0 lifts to the zero (+inf), min(inf, 5) = 5

    def test_tropical_elem_order_needs_selectivity(self):
        TE = A.make_tropical_elem(A.IntRing(), "min")
        with self.assertRaises(A.OrderError):
            TE(2) < TE(3)
        TE2 = A.make_tropical_elem(A.MaxMin(), "min")
        self.assertTrue(TE2(5) < TE2(3))                # "better" = larger under ⊕ = max


def _strassen_mutant(S, fallback=None):
    from mutations.targets import gen_matrix_pair, ring_runner
    naive = rewrite.load_copy(MM + "naive.py").matmul_naive
    st = rewrite.load_copy(MM + "strassen.py", [("const", {"CUTOFF": 1})]).matmul_strassen
    return Mutant(pair="mm", family="OPSWAP", operator=S.name, mode="inject", subject_name="strassen",
                  description="test", subject=ring_runner(st, S, fallback), oracle=ring_runner(naive, S),
                  gen=gen_matrix_pair(S), sizes=[1, 2, 3, 4], trials=4,
                  simplify=engine.simplify_pair(engine.simplify_matrix([0, 1], keep_diag=False),
                                                engine.simplify_matrix([0, 1], keep_diag=False)))


class TestEngine(unittest.TestCase):
    def test_strassen_survives_over_a_ring(self):
        r = engine.run_mutant(_strassen_mutant(A.Zp(7)), seed="test")
        self.assertEqual(r["status"], "SURVIVED")
        self.assertEqual(r["tests"]["tests"], 16)

    def test_strassen_invalid_without_subtraction(self):
        r = engine.run_mutant(_strassen_mutant(A.MinPlus()), seed="test")
        self.assertEqual(r["status"], "INVALID")
        self.assertIn("UndefinedOp", r["reason"])

    def test_strassen_killed_when_signs_are_dropped(self):
        r = engine.run_mutant(_strassen_mutant(A.MinPlus(), "add"), seed="test")
        self.assertEqual(r["status"], "KILLED")
        self.assertLessEqual(r["counterexample"]["size"], 2)

    def test_watchdog_turns_an_infinite_loop_into_invalid(self):
        def loop(_):
            while True:
                pass
        m = Mutant(pair="x", family="MIRROR", operator="o", mode="io", subject_name="loop", description="",
                   subject=loop, oracle=lambda x: x, gen=lambda n, rng: n, sizes=[1], trials=1)
        old = engine.CALL_TIMEOUT_S
        engine.CALL_TIMEOUT_S = 0.3
        try:
            t0 = time.perf_counter()
            r = engine.run_mutant(m, seed="test")
        finally:
            engine.CALL_TIMEOUT_S = old
        self.assertEqual(r["status"], "INVALID")
        self.assertIn("timeout", r["reason"])
        self.assertLess(time.perf_counter() - t0, 5)

    def test_fit_cost_reuses_validate(self):
        cost = {"run": lambda n: {"add": 0, "mul": n ** 3, "neg": 0, "inv": 0, "cmp": 0}, "n_values": [8, 16, 32, 64],
                "measure": "mul", "claimed": "n**3", "library": ["n**2", "n**3", "n**4"]}
        f = engine.fit_cost(cost)
        self.assertEqual(f["alphas"]["n**3"], 1.0)
        self.assertTrue(f["discriminating"])
        self.assertIn("n**2", f["rejected_rivals"])


if __name__ == "__main__":
    unittest.main()
