"""Tests for pairs/multi-pattern-matching-naive-vs-aho-corasick (round 2026-10-06i).

The three implementations agree on seeded instances, check() accepts correct outputs and rejects deliberately wrong
ones (including non-overlapping counts), and the exact V2 counts equal the closed forms stated in entry.json.
Runs in about a second.
"""
import importlib.util
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/multi-pattern-matching-naive-vs-aho-corasick/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class MultiPatternMatching(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "t6i_ac_h")
        cls.naive = staticmethod(_load(E + "implementations/naive.py", "t6i_ac_n").count_occurrences_naive)
        cls.kmp = staticmethod(_load(E + "implementations/kmp_each.py", "t6i_ac_k").count_occurrences_kmp_each)
        cls.ac = staticmethod(_load(E + "implementations/aho_corasick.py", "t6i_ac_a").count_occurrences_aho_corasick)

    def test_agree_and_check(self):
        for n in range(0, 12):
            for t in range(8):
                inst = self.H.generate(n, random.Random(f"t6i-ac|{n}|{t}"))
                a = self.ac(inst)
                self.assertEqual(a, self.naive(inst))
                self.assertEqual(a, self.kmp(inst))
                self.assertIs(self.H.check(inst, a), True)
                if n:
                    self.assertIs(self.H.check(inst, (a[0] + 1,) + a[1:]), False)

    def test_overlaps_and_nested_patterns(self):
        inst = ("aaaa", ("aa", "a", "aaa", "b", "aa"))
        self.assertEqual(self.ac(inst), (3, 4, 2, 0, 3))
        self.assertIs(self.H.check(inst, (2, 4, 1, 0, 2)), False)    # non-overlapping counts (str.count)

    def test_closed_forms(self):
        def count(fn, n):
            fn(self.H.generate_scaling(n, None))
            return self.H.reported_cost(None)
        for n in range(1, 13):
            self.assertEqual(count(self.naive, n), n * (n + 1) * (3 * n * n - 2 * n + 2) // 6)
            self.assertEqual(count(self.ac, n), 4 * n * n - 3)
            if n >= 2:
                self.assertEqual(count(self.kmp, n), 3 * n ** 3 - 2 * n ** 2 - 5 * n + 6)


if __name__ == "__main__":
    unittest.main()
