"""Tests for pairs/linear-ordering-enumeration-vs-subset-dp (round 2026-10-06i).

The implementations agree on seeded instances, check() accepts correct outputs and rejects deliberately wrong ones,
and the exact V2 counts equal the closed forms stated in entry.json. Runs in a few seconds.
"""
import importlib.util
import math
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/linear-ordering-enumeration-vs-subset-dp/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class LinearOrdering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "t6i_lop_h")
        cls.enum = staticmethod(_load(E + "implementations/enumeration.py", "t6i_lop_e").linear_ordering_enumeration)
        cls.dp = staticmethod(_load(E + "implementations/subset_dp.py", "t6i_lop_d").linear_ordering_subset_dp)

    def test_agree_and_check(self):
        for n in range(0, 8):
            for t in range(6):
                w = self.H.generate(n, random.Random(f"t6i-lop|{n}|{t}"))
                a, b = self.enum(w), self.dp(w)
                self.assertEqual(a[0], b[0])
                self.assertIs(self.H.check(w, a), True)
                self.assertIs(self.H.check(w, b), True)
                self.assertIs(self.H.check(w, (b[0] + 1, b[1])), False)

    def test_diagonal_ignored_and_worse_order_rejected(self):
        w = ((100, 3), (5, -100))
        self.assertEqual(self.dp(w), (5, (1, 0)))
        self.assertIs(self.H.check(w, (3, (0, 1))), False)
        self.assertIs(self.H.check(w, (5, (0, 1))), False)

    def test_closed_forms(self):
        for n in range(2, 8):
            w = self.H.generate_scaling(n, random.Random(n))
            self.enum(w)
            self.assertEqual(self.H.reported_cost(None), math.factorial(n) * (n * (n - 1) // 2 + 1) - 1)
        for n in range(2, 12):
            w = self.H.generate_scaling(n, random.Random(n))
            self.dp(w)
            self.assertEqual(self.H.reported_cost(None), 2 ** (n - 2) * (n + 4) * (n - 1) + 1)


if __name__ == "__main__":
    unittest.main()
