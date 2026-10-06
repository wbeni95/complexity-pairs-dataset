"""Tests for pairs/planar-perfect-matchings-enumeration-vs-kasteleyn (implementations, oracle, exact counts).

Run:  python -m unittest tests.test_entries_2026_10_06f_planar   (a few seconds)
"""
import importlib.util
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "planar-perfect-matchings-enumeration-vs-kasteleyn"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "t06f_ppm_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "t06f_ppm_enum")
KB = _load(ENTRY / "implementations" / "kasteleyn_bareiss.py", "t06f_ppm_kast")
enum_count = EN.count_perfect_matchings_enumeration
kasteleyn = KB.count_perfect_matchings_kasteleyn


def unit(a, b):
    return (a, b, H._matrix(a, b, lambda: 1))


class KnownValues(unittest.TestCase):
    def test_domino_tilings(self):
        # unit rectangles: 2 x 2 -> 2, 3 x 4 -> 11, 4 x 4 -> 36, 6 x 6 -> 6728, 8 x 8 -> 12988816
        for (a, b), z in {(2, 2): 2, (3, 4): 11, (4, 4): 36, (6, 6): 6728, (8, 8): 12988816}.items():
            self.assertEqual(kasteleyn(unit(a, b)), z)
            self.assertEqual(H.transfer_matrix_count(*unit(a, b)), z)
        self.assertEqual(enum_count(unit(6, 6)), 6728)

    def test_conventions(self):
        for inst in [(0, 3, ()), (2, 0, ()), (0, 0, ())]:
            self.assertEqual(kasteleyn(inst), 1)
            self.assertEqual(enum_count(inst), 1)
            self.assertTrue(H.check(inst, 1))
        for a, b in [(1, 1), (3, 3), (3, 5), (1, 7)]:
            self.assertEqual(kasteleyn(unit(a, b)), 0)
            self.assertEqual(enum_count(unit(a, b)), 0)

    def test_ladders_are_fibonacci(self):
        f = [0, 1]
        for _ in range(30):
            f.append(f[-1] + f[-2])
        for m in range(1, 20):
            self.assertEqual(kasteleyn(unit(m, 2)), f[m + 1])
            self.assertEqual(enum_count(unit(2, m)), f[m + 1])


class Agreement(unittest.TestCase):
    def test_random_instances(self):
        for n in range(0, 31):
            for t in range(4):
                inst = H.generate(n, random.Random(f"t06f|{n}|{t}"))
                k = kasteleyn(inst)
                self.assertEqual(enum_count(inst), k, (n, t))
                self.assertIs(H.check(inst, k), True, (n, t))


class OracleRejects(unittest.TestCase):
    def test_wrong_outputs(self):
        inst = unit(4, 4)
        self.assertIs(H.check(inst, 36), True)
        for wrong in (35, 37, -36, 36.0, True, 0):
            self.assertIs(H.check(inst, wrong), False, wrong)
        # the unsigned determinant of the 2 x 2 grid is 0, the answer is 2
        self.assertIs(H.check(unit(2, 2), 0), False)


class ExactCounts(unittest.TestCase):
    def test_closed_forms(self):
        luc = [2, 1]
        for _ in range(40):
            luc.append(luc[-1] + luc[-2])
        for n in range(2, 41, 2):
            out = enum_count(H.generate_scaling(n, None))
            self.assertEqual(H.reported_cost(out), luc[n // 2 + 2] - 3, n)
            out = kasteleyn(H.generate_scaling(n, None))
            self.assertEqual(H.reported_cost(out), (n - 2) * n * (n - 1) // 8, n)


if __name__ == "__main__":
    unittest.main()
