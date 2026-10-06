"""Tests for four entries added in round 2026-10-06f: Horn-SAT, XOR-SAT, Boolean matrix multiplication, OR convolution.

For each entry: the implementations agree on seeded instances, the independent check() accepts correct outputs and
rejects deliberately wrong ones, and the exact V2 counts equal the closed forms stated in entry.json at small n.
Runs in a few seconds.
"""
import importlib.util
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _count(harness, fn, n, rng=None):
    inst = harness.generate_scaling(n, rng)
    fn(inst)
    return harness.reported_cost(None)


class HornSat(unittest.TestCase):
    E = "pairs/horn-sat-brute-force-vs-unit-propagation/"

    @classmethod
    def setUpClass(cls):
        cls.H = _load(cls.E + "harness.py", "t6f_horn_h")
        cls.B = _load(cls.E + "implementations/brute_force.py", "t6f_horn_b")
        cls.U = _load(cls.E + "implementations/unit_propagation.py", "t6f_horn_u")

    def test_agree_and_check(self):
        for n in range(0, 11):
            for t in range(6):
                inst = self.H.generate(n, random.Random(f"t6f-horn|{n}|{t}"))
                out = self.U.horn_sat_unit_propagation(inst)
                self.assertEqual(out, self.B.horn_sat_brute_force(inst))
                self.assertIs(self.H.check(inst, out), True)
                if out is None:
                    self.assertIs(self.H.check(inst, (False,) * n), False)
                else:
                    self.assertIs(self.H.check(inst, None), False)

    def test_rejects_non_least_model(self):
        # x1 -> x2, no facts: least model all-false; all-true is a model but not the least one
        inst = (2, ((-1, 2),))
        self.assertIs(self.H.check(inst, (False, False)), True)
        self.assertIs(self.H.check(inst, (True, True)), False)

    def test_rejects_non_horn_clause(self):
        with self.assertRaises(ValueError):
            self.U.horn_sat_unit_propagation((2, ((1, 2),)))

    def test_closed_forms(self):
        for n in range(3, 11):
            self.assertEqual(_count(self.H, self.B.horn_sat_brute_force, n),
                             6 * ((2 * n + 13) * 2 ** (n - 2) - 2 * n - 4))
        for n in (3, 10, 100, 1000):
            self.assertEqual(_count(self.H, self.U.horn_sat_unit_propagation, n), 12 * n - 7)


class XorSat(unittest.TestCase):
    E = "pairs/xor-sat-brute-force-vs-gaussian-elimination/"

    @classmethod
    def setUpClass(cls):
        cls.H = _load(cls.E + "harness.py", "t6f_xor_h")
        cls.B = _load(cls.E + "implementations/brute_force.py", "t6f_xor_b")
        cls.G = _load(cls.E + "implementations/gaussian_elimination.py", "t6f_xor_g")

    def test_agree_and_check(self):
        for n in range(0, 10):
            for t in range(6):
                inst = self.H.generate(n, random.Random(f"t6f-xor|{n}|{t}"))
                a, b = self.B.xor_sat_brute_force(inst), self.G.xor_sat_gauss(inst)
                self.assertTrue(self.H.equal(a, b))
                self.assertIs(self.H.check(inst, a), True)
                self.assertIs(self.H.check(inst, b), True)
                self.assertIs(self.H.check(inst, (a[0] + 1, a[1] or (0,) * n)), False)

    def test_certificate_path_rejects_wrong_counts(self):
        # n > 10: no exhaustive count, only certificates decide
        for t in range(6):
            inst = self.H.generate(16, random.Random(f"t6f-xor-big|{t}"))
            c, w = self.G.xor_sat_gauss(inst)
            self.assertIs(self.H.check(inst, (c, w)), True)
            if c:
                self.assertIs(self.H.check(inst, (2 * c, w)), False)
                self.assertIs(self.H.check(inst, (0, None)), False)
            else:
                self.assertIs(self.H.check(inst, (1, (0,) * 16)), False)

    def test_closed_forms(self):
        for n in range(1, 10):
            self.assertEqual(_count(self.H, self.B.xor_sat_brute_force, n), (2 * n + 1) * (2 ** (n + 1) - 2))
        for n in (1, 2, 5, 16, 40):
            self.assertEqual(3 * _count(self.H, self.G.xor_sat_gauss, n), n * (n * n + 6 * n - 4))


class BooleanMatmul(unittest.TestCase):
    E = "pairs/boolean-matrix-multiplication-naive-vs-strassen/"

    @classmethod
    def setUpClass(cls):
        cls.H = _load(cls.E + "harness.py", "t6f_bmm_h")
        cls.N = _load(cls.E + "implementations/naive.py", "t6f_bmm_n")
        cls.S = _load(cls.E + "implementations/strassen_over_integers.py", "t6f_bmm_s")

    def test_agree_and_check(self):
        for n in (0, 1, 2, 5, 17, 33):
            inst = self.H.generate(n, random.Random(f"t6f-bmm|{n}"))
            c = self.N.bmm_naive(inst)
            self.assertEqual(c, self.S.bmm_strassen(inst))
            self.assertIs(self.H.check(inst, c), True)
            if n:
                c[0][0] ^= 1
                self.assertIs(self.H.check(inst, c), False)

    def test_closed_forms(self):
        for n in (16, 32, 64):
            rng = random.Random(f"t6f-bmm-count|{n}")
            self.assertEqual(_count(self.H, self.N.bmm_naive, n, rng), n ** 3)
            rng = random.Random(f"t6f-bmm-count|{n}")
            self.assertEqual(_count(self.H, self.S.bmm_strassen, n, rng), 7 ** (n.bit_length() - 5) * 16 ** 3)


class OrConvolution(unittest.TestCase):
    E = "pairs/or-convolution-naive-vs-zeta-mobius/"

    @classmethod
    def setUpClass(cls):
        cls.H = _load(cls.E + "harness.py", "t6f_orc_h")
        cls.N = _load(cls.E + "implementations/naive.py", "t6f_orc_n")
        cls.Z = _load(cls.E + "implementations/zeta_mobius.py", "t6f_orc_z")

    def test_agree_and_check(self):
        for n in range(0, 9):
            inst = self.H.generate(n, random.Random(f"t6f-orc|{n}"))
            h = self.Z.or_convolution_zeta_mobius(inst)
            self.assertEqual(h, self.N.or_convolution_naive(inst))
            self.assertIs(self.H.check(inst, h), True)
            wrong = list(h)
            wrong[-1] += 1
            self.assertIs(self.H.check(inst, wrong), False)

    def test_check_complete_above_sampling_range(self):
        # a single wrong entry at n = 11 must be caught (an earlier sampled check could miss it)
        inst = self.H.generate(11, random.Random("t6f-orc-big"))
        h = self.Z.or_convolution_zeta_mobius(inst)
        for i in (0, 1023, 2047):
            wrong = list(h)
            wrong[i] -= 1
            self.assertIs(self.H.check(inst, wrong), False)

    def test_closed_forms(self):
        for n in range(0, 8):
            self.assertEqual(_count(self.H, self.N.or_convolution_naive, n, random.Random(n)), 2 * 4 ** n)
        for n in range(1, 13):
            self.assertEqual(2 * _count(self.H, self.Z.or_convolution_zeta_mobius, n, random.Random(n)),
                             (3 * n + 2) * 2 ** n)


if __name__ == "__main__":
    unittest.main()
