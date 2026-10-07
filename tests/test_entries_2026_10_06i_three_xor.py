"""Tests for the entry pairs/three-xor-all-triples-vs-patricia-trie (round 2026-10-06i).

Both implementations agree on seeded instances and pass the independent check(); check() rejects deliberately
wrong outputs, including a repeated index whose XOR is 0 and negative indices that alias a real solution; the
three kinds of solution (0,0,0), (x,x,0) and three distinct nonzero values are each found; and the exact V2 counts
equal the closed forms stated in entry.json at small n. Runs in a few seconds.
"""
import importlib.util
import random
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = "pairs/three-xor-all-triples-vs-patricia-trie/"


def _load(rel, name):
    spec = importlib.util.spec_from_file_location(name, REPO / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class ThreeXor(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.H = _load(E + "harness.py", "t6i_txor_h")
        cls.A = staticmethod(_load(E + "implementations/all_triples.py", "t6i_txor_a").three_xor_all_triples)
        cls.P = staticmethod(_load(E + "implementations/patricia_trie.py", "t6i_txor_p").three_xor_patricia_trie)

    def test_agree_and_check(self):
        yes = no = 0
        for n in list(range(0, 13)) + [16, 32, 64]:
            for t in range(10):
                inst = self.H.generate(n, random.Random(f"t6i-txor|{n}|{t}"))
                a, b = self.A(inst), self.P(inst)
                self.assertTrue(self.H.equal(a, b), (inst, a, b))
                self.assertIs(self.H.check(inst, a), True)
                self.assertIs(self.H.check(inst, b), True)
                yes += a is not None
                no += a is None
        self.assertGreater(yes, 30)
        self.assertGreater(no, 30)

    def test_rejects_wrong_outputs(self):
        inst = (3, (5, 0, 5, 3))           # (0, 1, 2) is a solution: 5 ^ 0 ^ 5 = 0
        check = self.H.check
        self.assertIs(check(inst, (0, 1, 2)), True)
        self.assertIs(check(inst, (0, 0, 1)), False)        # repeated index, XOR 5 ^ 5 ^ 0 = 0
        self.assertIs(check(inst, (1, 2, 2)), False)        # repeated index, XOR 0 ^ 5 ^ 5 = 0
        self.assertIs(check(inst, (0, 2, 1)), False)        # unsorted
        self.assertIs(check(inst, (-4, -3, -2)), False)     # negative indices alias (0, 1, 2)
        self.assertIs(check(inst, (2, 3, 4)), False)        # out of range
        self.assertIs(check(inst, (False, True, 2)), False)  # bools alias (0, 1, 2)
        self.assertIs(check(inst, (0.0, 1.0, 2.0)), False)
        self.assertIs(check(inst, ("0", "1", "2")), False)
        self.assertIs(check(inst, [0, 1, 2]), False)
        self.assertIs(check(inst, (0, 1)), False)
        self.assertIs(check(inst, (0, 1, 2, 3)), False)
        self.assertIs(check(inst, (0, 2, 3)), False)        # 5 ^ 5 ^ 3 != 0
        self.assertIs(check(inst, None), False)             # None on a yes-instance
        odd = (3, (1, 2, 4, 7))                             # odd Hamming weight: no solution
        self.assertIs(check(odd, None), True)
        self.assertIs(check(odd, (0, 1, 2)), False)         # a triple on a no-instance

    def test_solution_kinds(self):
        cases = [
            ((4, (3, 0, 9, 0, 0)), True),       # (0, 0, 0)
            ((4, (3, 9, 0, 3)), True),          # (x, x, 0)
            ((4, (3, 9, 3, 9)), False),         # repeats without a zero
            ((4, (0, 0, 3, 9)), False),         # two zeros, distinct values
            ((4, (0, 3, 5, 6)), True),          # 3 ^ 5 ^ 6 = 0 next to a single zero
            ((2, (1, 2, 3)), True),
            ((1, (1, 1, 1)), False),
            ((1, ()), False),
        ]
        for inst, found in cases:
            for fn in (self.A, self.P):
                out = fn(inst)
                self.assertEqual(out is not None, found, (inst, fn.__name__, out))
                self.assertIs(self.H.check(inst, out), True)

    def test_closed_forms(self):
        for k in range(0, 7):
            n = 2 ** k
            inst = self.H.generate_scaling(n, random.Random(f"t6i-txor-count|{n}"))
            self.assertIsNone(self.A(inst))
            self.assertEqual(self.H.reported_cost(None), (n ** 3 - n) // 6)
        for k in range(0, 9):
            n = 2 ** k
            inst = self.H.generate_scaling(n, random.Random(f"t6i-txor-count|{n}"))
            self.assertIsNone(self.P(inst))
            self.assertEqual(self.H.reported_cost(None), 7 * n * n + 2 * n * k - 3 * n)


if __name__ == "__main__":
    unittest.main()
