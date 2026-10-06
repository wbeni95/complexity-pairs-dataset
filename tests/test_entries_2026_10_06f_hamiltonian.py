"""Fast tests for pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion (well under 10 s)."""
import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "t06f_ham_harness")
EN = _load(ENTRY / "implementations" / "enumeration.py", "t06f_ham_en").count_hamiltonian_cycles_enumeration
IE = _load(ENTRY / "implementations" / "inclusion_exclusion.py",
           "t06f_ham_ie").count_hamiltonian_cycles_inclusion_exclusion
HK = _load(ENTRY / "implementations" / "held_karp_counting.py", "t06f_ham_hk").count_hamiltonian_cycles_held_karp


def _tup(a):
    return tuple(tuple(r) for r in a)


class Conventions(unittest.TestCase):
    def test_small_n(self):
        for fn in (EN, IE, HK):
            self.assertEqual(fn(()), 0)
            self.assertEqual(fn(((1,),)), 0)                 # a self-loop is not a cycle
            self.assertEqual(fn(((1, 1), (1, 1))), 1)        # 0 -> 1 -> 0, diagonal ignored
            self.assertEqual(fn(((0, 1), (0, 0))), 0)

    def test_diagonal_ignored(self):
        rng = random.Random(1)
        for n in range(3, 8):
            a = [list(r) for r in H.generate(n, rng)]
            b = [r[:] for r in a]
            for v in range(n):
                b[v][v] = 1 - b[v][v]
            for fn in (EN, IE, HK):
                self.assertEqual(fn(_tup(a)), fn(_tup(b)))


class ClosedForms(unittest.TestCase):
    def test_complete_and_bipartite(self):
        for n in range(2, 9):
            k = _tup(H.complete_digraph(n))
            for fn in (EN, IE, HK):
                self.assertEqual(fn(k), math.factorial(n - 1))
        for m in range(1, 5):
            g = _tup(H.complete_bipartite(m, m))
            for fn in (EN, IE, HK):
                self.assertEqual(fn(g), math.factorial(m) * math.factorial(m - 1))

    def test_petersen_computed(self):
        p = _tup(H.petersen())
        self.assertEqual(IE(p), 0)
        self.assertEqual(HK(p), 0)
        self.assertEqual(H.dfs_count(p), 0)

    def test_undirected_is_twice(self):
        rng = random.Random(7)
        for n in range(3, 9):
            a = H._random_graph(n, 0.6, rng)
            self.assertEqual(HK(_tup(a)) % 2, 0)


class Agreement(unittest.TestCase):
    def test_random_battery(self):
        for n in range(0, 9):
            for t in range(10):
                inst = H.generate(n, random.Random(f"unit|{n}|{t}"))
                outs = {EN(inst), IE(inst), HK(inst)}
                self.assertEqual(len(outs), 1)
                self.assertIs(H.check(inst, outs.pop()), True)


class Oracle(unittest.TestCase):
    def test_rejects_wrong_outputs(self):
        for n in range(3, 10):
            for t in range(5):
                inst = H.generate(n, random.Random(f"unit-oracle|{n}|{t}"))
                true = HK(inst)
                self.assertIs(H.check(inst, true), True)
                for wrong in (true + 1, 2 * true + 1, -1, float(true), None):
                    self.assertIs(H.check(inst, wrong), False)
                if true:
                    self.assertIs(H.check(inst, 2 * true), False)
                    self.assertIs(H.check(inst, true - 1), False)


class Counts(unittest.TestCase):
    def test_exact_counts(self):
        for n in range(2, 9):
            for fn, form in ((EN, math.factorial(n)),
                             (IE, n * (n - 1) * (n + 2) * 2 ** (n - 2) + 2 ** (n - 1) - 1),
                             (HK, (n - 1) * (n - 2) * 2 ** (n - 2) + 2 * (n - 1))):
                out = fn(H.generate_scaling(n, None))
                self.assertEqual(int(out), math.factorial(n - 1))
                self.assertEqual(H.reported_cost(out), form)

    def test_no_mutation(self):
        inst = H.generate(7, random.Random(3))
        snap = [list(r) for r in inst]
        for fn in (EN, IE, HK):
            fn(inst)
        self.assertEqual([list(r) for r in inst], snap)


if __name__ == "__main__":
    unittest.main()
