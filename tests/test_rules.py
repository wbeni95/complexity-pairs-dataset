"""Tests for generators/rules/ (round 2026-10-06d): the screening harness and the seven rule modules.

The tests pin known verdicts (a rule must be EXACT where its precondition holds and must be caught where it
fails), exact operation counts against the spec-derived counts, determinism of the generators, and the
relabelling invariance of the canonical forms used for deduplication.

Run:  python -m unittest discover -s tests
"""
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from generators.rules import RULES, bilinear, common, convolution, greedy, knuth, load, magma_power, memo, mitm  # noqa: E402


class HarnessTests(unittest.TestCase):
    def test_fitting_is_imported_from_validator(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("v_check", ROOT / "tools" / "validate.py")
        v = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(v)
        self.assertEqual(common.fit_slope([0, 1, 2], [0, 2, 4]), v.fit_slope([0, 1, 2], [0, 2, 4]))
        self.assertEqual(common.eval_cost("n**2", 7), 49)

    def test_log_cost_overflow_fallback(self):
        self.assertAlmostEqual(common.log_cost("n*4**n", 10 ** 15), math.log(1e15) + 1e15 * math.log(4), places=3)
        self.assertAlmostEqual(common.log_cost("n**2", 10), math.log(100))

    def test_fit_claim_constant_and_rivals(self):
        f = common.fit_claim([1, 2, 3, 4], [5, 5, 5, 5], "1")
        self.assertTrue(f["ok"])
        ns = [8, 16, 32, 64]
        f = common.fit_claim(ns, [n ** 2 for n in ns], "n**2", ["n**3"], 0.05)
        self.assertTrue(f["ok"])
        self.assertTrue(f["rivals"][0]["rejected"])
        f = common.fit_claim(ns, [n ** 2 for n in ns], "n**2", ["n**2*1.0001"], 0.05)
        self.assertFalse(f["ok"])  # an indistinguishable rival must fail the claim

    def test_canonical_table_invariant_under_relabelling(self):
        rng = random.Random(5)
        for N in (3, 4):
            T = [[rng.randrange(N) for _ in range(N)] for _ in range(N)]
            perm = rng.sample(range(N), N)
            T2 = common.relabel_table(T, perm)
            self.assertEqual(common.canon_table_exact(T), common.canon_table_exact(T2))
            self.assertEqual(common.table_fingerprint(T), common.table_fingerprint(T2))

    def test_all_rules_have_catalogue_and_generators(self):
        for r in RULES:
            mod = load(r)
            for k in ("precondition", "transformation", "cost_change", "failure_mode"):
                self.assertIn(k, mod.CATALOGUE)
            self.assertEqual(mod.generate(7, 5), mod.generate(7, 5))  # deterministic in the seed


class MemoTests(unittest.TestCase):
    def test_fibonacci_shape_exact_and_counts(self):
        c = memo.build({"family": "memo1d", "kind": "sub", "moves": ["s1", "s2"], "combine": "sum", "coef": [1, 1]})
        r = common.screen(c)
        self.assertEqual(r["verdict"], "EXACT")
        self.assertTrue(r["scaling"]["resolved"])
        self.assertTrue(r["scaling"]["slow"]["counts_equal_spec"])
        self.assertTrue(r["scaling"]["slow"]["cost"].startswith("1.6180339887"))

    def test_single_move_is_degenerate(self):
        c = memo.build({"family": "memo1d", "kind": "sub", "moves": ["s1"], "combine": "min", "coef": [3]})
        self.assertEqual(common.screen(c)["verdict"], "INVALID")

    def test_lossy_key_caught(self):
        c = memo.build({"family": "compress1d", "moves": ["s1", "s2"], "flips": [0, 1], "delta": 2,
                        "combine": "sum", "coef": [1, 1]})
        self.assertFalse(c.precondition())
        self.assertFalse(c.p_functional())
        self.assertIn(common.screen(c)["verdict"], ("WRONG", "NEAR-MISS"))

    def test_redundant_flag_compresses_exactly(self):
        # s1 flips p, s2 does not: p = (n - m) mod 2 on every reachable state, so dropping p is exact
        c = memo.build({"family": "compress1d", "moves": ["s1", "s2"], "flips": [1, 0], "delta": 2,
                        "combine": "sum", "coef": [1, 1]})
        self.assertFalse(c.precondition())
        self.assertTrue(c.p_functional())
        self.assertEqual(common.screen(c, do_scaling=False)["verdict"], "EXACT")

    def test_acsv_lambda_edit_distance_moves(self):
        lam = memo.acsv_lambda([(1, 0), (0, 1), (1, 1)])
        self.assertAlmostEqual(lam, 3 + 2 * math.sqrt(2), places=6)


class ConvolutionTests(unittest.TestCase):
    def _spec(self, fam, N, seed=0):
        rng = random.Random(seed)
        T = convolution.base_table(fam, N, rng)
        return {"family": fam, "N": N, "table": common.relabel_table(T, rng.sample(range(N), N))}

    def test_structures_detected_and_exact(self):
        for fam, S in (("xor", "xor"), ("cyclic", "cyclic"), ("or", "or"), ("and", "or"), ("max", "max"),
                       ("min", "max"), ("sat", "sat")):
            c = convolution.build(self._spec(fam, 8))
            self.assertEqual(c.S, S, fam)
            self.assertEqual(common.screen(c, do_scaling=False)["verdict"], "EXACT", fam)

    def test_latin_square_not_exact_but_repair_is(self):
        c = convolution.build(self._spec("latin", 8, seed=3))
        if c.score_struct == 1.0:
            self.skipTest("this Latin square happens to be a group")
        r = common.screen(c, do_scaling=False)
        self.assertNotEqual(r["verdict"], "EXACT")
        inst = c.instance(random.Random(1), 8)
        self.assertEqual(c.fast_repaired(inst, common.Ops()), c.slow(inst, common.Ops()))


class MagmaTests(unittest.TestCase):
    def test_group_exact_and_counts(self):
        T = [[(a + b) % 5 for b in range(5)] for a in range(5)]
        r = common.screen(magma_power.build({"family": "group", "m": 5, "table": T}))
        self.assertEqual(r["verdict"], "EXACT")
        self.assertTrue(r["scaling"]["slow"]["counts_equal_spec"] and r["scaling"]["fast"]["counts_equal_spec"])

    def test_square_condition_characterises_binary_powering(self):
        rng = random.Random(11)
        for _ in range(60):
            T = magma_power.make_table(rng.choice(["random", "comm", "idem"]), rng, 3)
            c = magma_power.build({"family": "x", "m": 3, "table": T})
            exact = all(c.slow((T, x, e), common.Ops()) == c.fast((T, x, e), common.Ops())
                        for x in range(3) for e in range(1, 20))
            self.assertEqual(exact, c.predicates()["square_cond"])
            self.assertTrue(all(c.slow((T, x, e), common.Ops()) == c.fast_cycle((T, x, e), common.Ops())
                                for x in range(3) for e in range(1, 20)))


class GreedyTests(unittest.TestCase):
    def test_uniform_matroid_exact(self):
        c = greedy.build({"family": "uniform", "g": 6, "r": 3})
        self.assertTrue(c.precondition())
        self.assertEqual(common.screen(c, do_scaling=False)["verdict"], "EXACT")
        self.assertEqual(c.predicates()["rank_quotient"], 1.0)

    def test_matching_on_path_is_not_a_matroid(self):
        # path a-b-c-d: matchings {ab, cd} (size 2) and {bc} (maximal, size 1): rank quotient 1/2
        c = greedy.build({"family": "matching", "g": 3, "v": 4, "edges": [[0, 1], [1, 2], [2, 3]]})
        p = c.predicates()
        self.assertFalse(p["matroid"])
        self.assertAlmostEqual(p["rank_quotient"], 0.5)
        self.assertAlmostEqual(p["adversarial_ratio"], 0.5, places=2)


class KnuthTests(unittest.TestCase):
    def test_bst_weights_satisfy_yao_and_are_exact(self):
        c = knuth.build({"family": "bst", "fmax": 10, "seed": 1})
        r = common.screen(c)
        self.assertTrue(r["precondition"])
        self.assertEqual(r["verdict"], "EXACT")
        self.assertTrue(r["scaling"]["slow"]["counts_equal_spec"])

    def test_random_weights_break_knuth(self):
        c = knuth.build({"family": "random", "wmax": 100, "seed": 2})
        self.assertNotEqual(common.screen(c, do_scaling=False)["verdict"], "EXACT")


class BilinearTests(unittest.TestCase):
    def test_karatsuba_rediscovered(self):
        (fmt, T) = bilinear.named_tensors()["karatsuba"]
        c = bilinear.build({"family": "named", "name": "karatsuba", "fmt": list(fmt), "tensor": T})
        self.assertEqual((c.m, c.r), (4, 3))
        r = common.screen(c)
        self.assertEqual(r["verdict"], "EXACT")
        self.assertTrue(r["scaling"]["resolved"])

    def test_decompositions_reconstruct_tensor(self):
        for name, (fmt, T) in bilinear.named_tensors().items():
            S = 0
            for u, v, w in bilinear.decomposition(fmt, T):
                for i in range(fmt[0]):
                    for j in range(fmt[1]):
                        for k in range(fmt[2]):
                            if u >> i & 1 and v >> j & 1 and w >> k & 1:
                                S ^= bilinear.bit(*fmt, i, j, k)
            self.assertEqual(S, T, name)


class MitmTests(unittest.TestCase):
    def test_group_exact_monoid_caught_and_repaired(self):
        self.assertEqual(common.screen(mitm.build({"family": "add", "M": 12}), do_scaling=False)["verdict"], "EXACT")
        c = mitm.build({"family": "max", "M": 8})
        self.assertNotEqual(common.screen(c, do_scaling=False)["verdict"], "EXACT")
        for n in (8, 10):
            inst = c.instance(random.Random(n), n)
            self.assertEqual(c.fast_all(inst, common.Ops()), c.slow(inst, common.Ops()))

    def test_boundary_conditioning_exact(self):
        c = mitm.build({"family": "add_inter", "M": 31, "density": 0.3})
        for n in (8, 10):
            inst = c.instance(random.Random(n), n)
            self.assertEqual(c.fast_boundary(inst, common.Ops()), c.slow(inst, common.Ops()))


if __name__ == "__main__":
    unittest.main()
