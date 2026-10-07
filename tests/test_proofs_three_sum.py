"""Checks for pairs/three-sum-cubic-vs-quadratic/PROOFS.md.

All triples: exactly C(n, 3) equality tests and C(n, 2) target computations on every no-instance, at most that on
every input. Sort + two pointers: exactly (n - 1)(n - 2)/2 pointer steps on every no-instance with n >= 1, at most
that on every input. Both against an independent oracle on inputs with duplicates, zeros and repeated values; the
scaling instances are no-instances; space bounds. Counting uses an integer type that counts additions, negations and
equality tests (the implementations are unchanged). All inputs come from fixed seeds. Runs in a few seconds.
"""
import importlib.util
import math
import random
import sys
import unittest
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "three-sum-cubic-vs-quadratic"
sys.path.insert(0, str(REPO / "tests"))

from proof_space import peak_words  # noqa: E402


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "tp_3s_h")
BRUTE_FILE = E / "implementations" / "brute_force.py"
TP_FILE = E / "implementations" / "sort_two_pointers.py"
BRUTE = _load(BRUTE_FILE, "tp_3s_b").three_sum_brute
TP = _load(TP_FILE, "tp_3s_tp").three_sum_quadratic

TALLY = Counter()


def _v(x):
    return x.v if isinstance(x, Num) else x


class Num:
    """An integer that counts additions, negations and equality tests (order comparisons are not counted)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __add__(self, o):
        TALLY["add"] += 1
        return Num(self.v + _v(o))

    __radd__ = __add__

    def __neg__(self):
        TALLY["neg"] += 1
        return Num(-self.v)

    def __eq__(self, o):
        TALLY["eq"] += 1
        return self.v == _v(o)

    def __lt__(self, o):
        return self.v < _v(o)

    def __gt__(self, o):
        return self.v > _v(o)

    def __le__(self, o):
        return self.v <= _v(o)

    def __ge__(self, o):
        return self.v >= _v(o)

    __hash__ = None


def has_triple(values):
    n = len(values)
    return any(values[i] + values[j] + values[k] == 0
               for i in range(n) for j in range(i + 1, n) for k in range(j + 1, n))


def instances(tag, count, max_n=40):
    rng = random.Random(f"tp-3s|{tag}")
    for t in range(count):
        n = rng.randint(0, max_n)
        kind = t % 4
        if kind == 0:
            yield tuple(H.generate(n, rng))
        elif kind == 1:
            yield tuple(rng.randint(-5, 5) for _ in range(n))           # zeros and repeats
        elif kind == 2:
            yield tuple(H.generate_scaling(n, rng))                     # all positive: no-instances
        else:
            yield tuple(rng.choice((-2, 1, 1, 0, 4, -8)) for _ in range(n))


class ThreeSumProofChecks(unittest.TestCase):
    def test_correct(self):
        yes = no = 0
        for vals in instances("correct", 600):
            truth = has_triple(vals)
            self.assertEqual(BRUTE(vals), truth, vals)
            self.assertEqual(TP(vals), truth, vals)
            self.assertIs(H.check(vals, truth), True)
            yes += truth
            no += not truth
        for vals, truth in (((0, 0, 0), True), ((0, 0), False), ((1, -2), False), ((3, 3, -6), True),
                            ((3, -6), False), ((-1, 0, 1), True), ((2, 2, 2, -4), True), ((5,), False), ((), False)):
            self.assertEqual(BRUTE(vals), truth)
            self.assertEqual(TP(vals), truth)
        self.assertGreater(yes, 100)
        self.assertGreater(no, 100)

    def test_scaling_instances_are_no_instances(self):
        for n in (0, 1, 2, 3, 10, 40, 60, 80):
            vals = H.generate_scaling(n, random.Random(f"tp-3s|scal|{n}"))
            self.assertTrue(all(v >= 1 for v in vals))
            self.assertFalse(has_triple(vals))

    def test_counts(self):
        for vals in instances("counts", 400, max_n=45):
            n = len(vals)
            truth = has_triple(vals)
            nums = tuple(Num(v) for v in vals)
            TALLY.clear()
            self.assertEqual(BRUTE(nums), truth)
            brute_eq, brute_neg = TALLY["eq"], TALLY["neg"]
            TALLY.clear()
            self.assertEqual(TP(nums), truth)
            steps = TALLY["eq"]                    # one `s == 0` test per pointer step; the sort uses only <
            self.assertEqual(TALLY["add"], 2 * steps)
            if truth:
                self.assertLessEqual(brute_eq, math.comb(n, 3))
                self.assertLessEqual(brute_neg, math.comb(n, 2))
                self.assertLessEqual(steps, (n - 1) * (n - 2) // 2 if n >= 2 else 0)
            else:
                self.assertEqual(brute_eq, math.comb(n, 3), vals)
                self.assertEqual(brute_neg, math.comb(n, 2), vals)
                self.assertEqual(steps, (n - 1) * (n - 2) // 2 if n >= 2 else 0, vals)

    def test_space(self):
        for vals in instances("space", 40, max_n=60):
            n = len(vals)
            _, pb = peak_words(BRUTE, (vals,), BRUTE_FILE)
            self.assertEqual(pb, 0)
            _, pt = peak_words(TP, (vals,), TP_FILE)
            self.assertEqual(pt, n)


if __name__ == "__main__":
    unittest.main()
