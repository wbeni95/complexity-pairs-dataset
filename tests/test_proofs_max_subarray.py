"""Deterministic checks of pairs/maximum-subarray/PROOFS.md (exact read counts, Kadane's invariant, space,
caveats, and the divide-and-conquer oracle)."""
import importlib.util
import itertools
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "maximum-subarray"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


brute = load("implementations/brute_force.py", "proofs_msub_brute")
running = load("implementations/running_sum.py", "proofs_msub_running")
kadane = load("implementations/kadane.py", "proofs_msub_kadane")
harness = load("harness.py", "proofs_msub_harness")


class CountingList(list):
    """A list that counts every element read a[index]."""

    def __init__(self, *args):
        super().__init__(*args)
        self.reads = 0

    def __getitem__(self, index):
        self.reads += 1
        return list.__getitem__(self, index)


def best_sum(a):
    return max(sum(a[i:j + 1]) for i in range(len(a)) for j in range(i, len(a)))


def instance(n, seed):
    return harness.generate(n, random.Random(seed))


class CountTests(unittest.TestCase):
    def check_reads(self, fn, sizes, expected):
        for n in sizes:
            a = CountingList(instance(n, 1000 + n))
            out = fn(a)
            self.assertEqual(a.reads, expected(n), (fn.__name__, n))
            if n <= 60:
                self.assertEqual(out, best_sum(list(a)))

    def test_brute_force_reads(self):
        self.check_reads(brute.max_subarray_brute, range(1, 61), lambda n: 1 + n * (n + 1) * (n + 2) // 6)

    def test_running_sum_reads(self):
        self.check_reads(running.max_subarray_quadratic, range(1, 201), lambda n: 1 + n * (n + 1) // 2)

    def test_kadane_reads(self):
        self.check_reads(kadane.max_subarray_kadane, range(1, 2001), lambda n: n)


class KadaneInvariantTests(unittest.TestCase):
    def test_invariant(self):
        code = kadane.max_subarray_kadane.__code__
        rng = random.Random(51)
        for _ in range(300):
            n = rng.randrange(1, 31)
            a = [rng.randint(-20, 20) for _ in range(n)]
            seen = {}

            def tracer(frame, event, arg):
                if frame.f_code is code:
                    loc = frame.f_locals
                    if "j" in loc and "x" in loc and "best" in loc:
                        seen[loc["j"]] = (loc["ending_here"], loc["best"])  # last state of iteration j
                    return tracer
                return None

            sys.settrace(tracer)
            try:
                out = kadane.max_subarray_kadane(a)
            finally:
                sys.settrace(None)
            for j, (ending, best) in seen.items():
                e_j = max(sum(a[i:j + 1]) for i in range(j + 1))       # best sum ending at j
                m_j = best_sum(a[:j + 1])                                # best sum within a[0..j]
                self.assertEqual((ending, best), (e_j, m_j))
            self.assertEqual(set(seen), set(range(1, n)))
            self.assertEqual(out, best_sum(a))


class SpaceTests(unittest.TestCase):
    def test_only_integer_locals(self):
        for fn in (brute.max_subarray_brute, running.max_subarray_quadratic, kadane.max_subarray_kadane):
            code = fn.__code__
            for n in range(1, 61):
                a = instance(n, 77 + n)
                worst = [0, 0]

                def tracer(frame, event, arg):
                    if frame.f_code is code:
                        names = [k for k in frame.f_locals if k != "a"]
                        worst[1] = max(worst[1], len(names) + 1)
                        for k in names:
                            v = frame.f_locals[k]
                            self.assertIs(type(v), int, (fn.__name__, k))
                            worst[0] = max(worst[0], abs(v))
                        return tracer
                    return None

                sys.settrace(tracer)
                try:
                    fn(a)
                finally:
                    sys.settrace(None)
                self.assertLessEqual(worst[0], 100 * n)
                self.assertLessEqual(worst[1], 7)


class CaveatTests(unittest.TestCase):
    def test_empty_subarray_variant(self):
        for n in range(1, 6):
            for a in itertools.product(range(-3, 4), repeat=n):
                m = best_sum(a)
                self.assertEqual(max(0, m) != m, all(x < 0 for x in a))

    def test_every_element_matters(self):
        for n in range(1, 5):
            for a in itertools.product(range(-2, 3), repeat=n):
                v = 1 + sum(abs(x) for x in a)
                for i in range(n):
                    b = list(a)
                    b[i] = v
                    self.assertNotEqual(best_sum(b), best_sum(a))


class OracleTests(unittest.TestCase):
    def test_reads_and_bounds(self):
        t = {1: 1}
        for m in range(2, 2001):
            t[m] = m + t[m // 2] + t[(m + 1) // 2]
        for n in list(range(1, 601)) + [1000, 1023, 1024, 1025, 2000]:
            a = CountingList(instance(n, 5000 + n))
            harness._divide_and_conquer(a, 0, n)
            self.assertEqual(a.reads, t[n])
            lo = n * (math.floor(math.log2(n)) + 1)
            hi = n * ((n - 1).bit_length() + 1)                      # ceil(log2 n) = bit_length(n - 1)
            self.assertTrue(lo <= a.reads <= hi, n)

    def test_oracle_correct(self):
        rng = random.Random(40)
        for _ in range(500):
            n = rng.randrange(1, 41)
            a = [rng.randint(-50, 50) for _ in range(n)]
            self.assertTrue(harness.check(a, best_sum(a)))


if __name__ == "__main__":
    unittest.main()
