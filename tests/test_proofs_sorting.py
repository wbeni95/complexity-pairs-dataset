"""Checks of the proofs in pairs/sorting-insertion-vs-merge/PROOFS.md (sections 4 to 9).

Every test runs the UNCHANGED implementations (with instrumented keys where comparisons are counted or recorded) on
fixed inputs and seeds, or on all inputs of the stated small sizes. The written proofs cover the general statements;
these tests re-run their computable facts.
"""
import importlib.util
import itertools
import math
import random
import tracemalloc
import unittest
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "sorting-insertion-vs-merge"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


H = load(ENTRY / "harness.py", "proofs_sort_harness")
INS = load(ENTRY / "implementations" / "insertion_sort.py", "proofs_sort_ins").insertion_sort
MERGE = load(ENTRY / "implementations" / "merge_sort.py", "proofs_sort_merge").merge_sort


def kinds(n, rng):
    """Random with ties, increasing, decreasing, constant, random distinct."""
    return [[rng.randint(-n, n) for _ in range(n)], list(range(n)), list(range(n, 0, -1)), [5] * n,
            rng.sample(range(10 * n + 1), n)]


def inversions(xs):
    return sum(1 for p in range(len(xs)) for q in range(p + 1, len(xs)) if xs[p] > xs[q])


def count(fn, xs):
    keys = [H.CountingKey(x) for x in xs]
    H._comparisons = 0
    out = fn(keys)
    return H._comparisons, [k.v for k in out]


class Rec:
    """A key whose comparisons append their outcome to Rec.log (to read the path in the comparison tree)."""
    __slots__ = ("v",)
    log = []

    def __init__(self, v):
        self.v = v

    def __lt__(self, o):
        r = self.v < o.v
        Rec.log.append(r)
        return r

    def __gt__(self, o):
        r = self.v > o.v
        Rec.log.append(r)
        return r


class Tagged:
    """A key compared by `key` only; `tag` records the input position (to test stability)."""
    __slots__ = ("key", "tag")

    def __init__(self, key, tag):
        self.key, self.tag = key, tag

    def __lt__(self, o):
        return self.key < o.key

    def __gt__(self, o):
        return self.key > o.key


def peak_bytes(fn, arg):
    tracemalloc.start()
    try:
        base = tracemalloc.get_traced_memory()[0]
        out = fn(arg)
        peak = tracemalloc.get_traced_memory()[1] - base
    finally:
        tracemalloc.stop()
    del out
    return peak


class CorrectnessTests(unittest.TestCase):
    """PROOFS.md sections 4 and 5: both return the sorted list without modifying the input; merge sort is stable
    (equal keys keep their input order). n = 0..60, 100, 500, five input kinds each."""

    def test_sorted(self):
        for n in list(range(61)) + [100, 500]:
            rng = random.Random(f"sort-proofs|{n}")
            for xs in kinds(n, rng):
                before = list(xs)
                for fn in (INS, MERGE):
                    out = fn(xs)
                    self.assertEqual(out, sorted(before), (n, fn.__name__))
                    self.assertEqual(xs, before)
                    self.assertIsNot(out, xs)

    def test_merge_stable(self):
        for n in range(0, 80):
            rng = random.Random(f"sort-stable|{n}")
            items = [Tagged(rng.randint(0, 3), i) for i in range(n)]
            out = MERGE(items)
            self.assertEqual([(t.key, t.tag) for t in out], sorted((t.key, t.tag) for t in items), n)


class InsertionAverageTests(unittest.TestCase):
    """PROOFS.md section 6: exact expectations by exhaustive enumeration. Over all n! orders of n distinct keys
    (n = 1..8): E[I] = n(n-1)/4 and E[comparisons] = n(n-1)/4 + n - H_n. Over all (2n+1)^n lists with entries in
    [-n, n] (the harness distribution, n = 1..5): E[I] = n(n-1)/4 * 2n/(2n+1), and the comparisons follow the instance
    formula of section 1 on every list."""

    def test_permutations(self):
        for n in range(1, 9):
            tot_i = tot_c = 0
            for perm in itertools.permutations(range(n)):
                c, out = count(INS, perm)
                self.assertEqual(out, list(range(n)))
                tot_i += inversions(perm)
                tot_c += c
            fact = math.factorial(n)
            harmonic = sum(Fraction(1, k) for k in range(1, n + 1))
            self.assertEqual(Fraction(tot_i, fact), Fraction(n * (n - 1), 4), n)
            self.assertEqual(Fraction(tot_c, fact), Fraction(n * (n - 1), 4) + n - harmonic, n)

    def test_harness_distribution(self):
        for n in range(1, 6):
            tot_i, total = 0, 0
            for xs in itertools.product(range(-n, n + 1), repeat=n):
                c, _ = count(INS, xs)
                g = [sum(1 for p in range(i) if xs[p] > xs[i]) for i in range(n)]
                self.assertEqual(c, sum(gi + (gi < i) for i, gi in enumerate(g) if i >= 1), xs)
                tot_i += sum(g)
                total += 1
            self.assertEqual(Fraction(tot_i, total), Fraction(n * (n - 1), 4) * Fraction(2 * n, 2 * n + 1), n)


class MergeBoundsTests(unittest.TestCase):
    """PROOFS.md section 7: for every n >= 2 and every input, merge sort makes between (n/3) floor(log2 n) and
    n ceil(log2 n) comparisons. n = 2..300, 511, 512, 513, 1000, 1024, five input kinds each."""

    def test_bounds(self):
        for n in list(range(2, 301)) + [511, 512, 513, 1000, 1024]:
            rng = random.Random(f"sort-merge|{n}")
            lo = Fraction(n, 3) * (n.bit_length() - 1)
            hi = n * (n - 1).bit_length()          # ceil(log2 n) = bit_length(n - 1) for n >= 2
            for xs in kinds(n, rng):
                c, out = count(MERGE, xs)
                self.assertEqual(out, sorted(xs))
                self.assertTrue(lo <= c <= hi, (n, c, lo, hi))


class LowerBoundTests(unittest.TestCase):
    """PROOFS.md section 8. (a) n log2 n - n log2 e <= log2 n! <= n log2 n for n = 1..2000. (b) For both
    implementations and every n = 1..8, the comparison outcomes on the n! orders of n distinct keys are n! distinct
    sequences, no one a prefix of another; their lengths satisfy the Kraft inequality sum 2^-len <= 1, the longest is
    at least ceil(log2 n!) and the mean at least log2 n!."""

    def test_log_factorial(self):
        lf = 0.0
        for n in range(1, 2001):
            lf += math.log2(n)
            self.assertLessEqual(n * math.log2(n) - n * math.log2(math.e), lf + 1e-9)
            self.assertLessEqual(lf, n * math.log2(n) + 1e-9)

    def test_comparison_trees(self):
        for fn in (INS, MERGE):
            for n in range(1, 9):
                paths = []
                for perm in itertools.permutations(range(n)):
                    Rec.log = []
                    out = fn([Rec(x) for x in perm])
                    self.assertEqual([r.v for r in out], list(range(n)))
                    paths.append(tuple(Rec.log))
                fact = math.factorial(n)
                self.assertEqual(len(set(paths)), fact, (fn.__name__, n))
                ps = set(paths)
                for p in paths:
                    for k in range(len(p)):
                        self.assertNotIn(p[:k], ps)
                self.assertLessEqual(sum(Fraction(1, 2 ** len(p)) for p in paths), 1)
                self.assertGreaterEqual(max(map(len, paths)), math.ceil(math.log2(fact)) if fact > 1 else 0)
                self.assertGreaterEqual(Fraction(sum(map(len, paths)), fact), math.log2(fact) - 1e-12)


class CountingSortTests(unittest.TestCase):
    """PROOFS.md section 10 (c): counting sort on [-n, n] (written here; plain integers, no element comparison) returns
    sorted(xs) with at most 6n + 2 counted steps, on the harness inputs and the five input kinds, n = 0..299."""

    @staticmethod
    def counting_sort(xs, n):
        steps = 0
        counts = [0] * (2 * n + 1)
        steps += 2 * n + 1
        for x in xs:
            counts[x + n] += 1
            steps += 1
        out = []
        for v in range(-n, n + 1):
            steps += 1
            for _ in range(counts[v + n]):
                out.append(v)
                steps += 1
        return out, steps

    def test_counting_sort(self):
        for n in range(300):
            rng = random.Random(f"sort-counting|{n}")
            for xs in [H.generate(n, rng)] + [x for x in kinds(n, rng) if all(-n <= v <= n for v in x)]:
                out, steps = self.counting_sort(xs, n)
                self.assertEqual(out, sorted(xs), n)
                self.assertLessEqual(steps, 6 * n + 2, n)


class SpaceTests(unittest.TestCase):
    """PROOFS.md section 9: Theta(n) space. For n = 1000, 2000, 4000, 8000, 16000 the peak traced allocation during the
    call (instance built before tracing) divided by n is at least 8 (the output) and at most 200, and varies by a
    factor of at most 1.5 (n log n would vary by 1.4 here, so the written proof excludes it; n^2 by 16)."""

    def test_peaks(self):
        for fn in (INS, MERGE):
            per = []
            for n in (1000, 2000, 4000, 8000, 16000):
                if fn is INS and n > 4000:
                    xs = list(range(n))           # sorted input keeps insertion sort fast; its space does not depend on the order
                else:
                    xs = H.generate(n, random.Random(f"sort-space|{n}"))
                per.append(peak_bytes(fn, xs) / n)
            self.assertGreaterEqual(min(per), 8, fn.__name__)
            self.assertLessEqual(max(per), 200, fn.__name__)
            self.assertLessEqual(max(per) / min(per), 1.5, (fn.__name__, per))


if __name__ == "__main__":
    unittest.main()
