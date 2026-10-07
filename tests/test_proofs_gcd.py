"""Deterministic checks of pairs/gcd-trial-vs-euclid/PROOFS.md (iteration and step counts, bounds, space)."""
import importlib.util
import math
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "gcd-trial-vs-euclid"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


trial = load("implementations/trial.py", "proofs_gcd_trial")
euclid = load("implementations/euclid.py", "proofs_gcd_euclid")
harness = load("harness.py", "proofs_gcd_harness")


class CountA(int):
    """An int that counts every `%` it performs as the left operand (trial divisors' a)."""
    calls = 0

    def __mod__(self, other):
        CountA.calls += 1
        return int.__mod__(self, other)


class CountB(int):
    calls = 0

    def __mod__(self, other):
        CountB.calls += 1
        return int.__mod__(self, other)


class Step(int):
    """An int whose `%` counts a Euclid step and returns a Step, so the count follows the loop."""
    steps = 0
    quotients = []

    def __mod__(self, other):
        Step.steps += 1
        Step.quotients.append(int(self) // int(other))
        return Step(int.__mod__(self, other))


def count_trial(a, b):
    CountA.calls = CountB.calls = 0
    out = trial.gcd_trial((CountA(a), CountB(b)))
    return int(out), CountA.calls, CountA.calls + CountB.calls


def count_euclid(a, b):
    Step.steps, Step.quotients = 0, []
    out = euclid.gcd_euclid((Step(a), Step(b)))
    return int(out), Step.steps, list(Step.quotients)


_FIB = [0, 1]
while len(_FIB) < 1000:
    _FIB.append(_FIB[-1] + _FIB[-2])


def fib(j):
    return _FIB[j]       # F_j, F_1 = F_2 = 1


PHI_LOG2 = math.log2((1 + math.sqrt(5)) / 2)


class TrialDivisorTests(unittest.TestCase):
    def test_exact_iteration_count(self):
        rng = random.Random(20261007)
        pairs = [(a, b) for a in range(81) for b in range(81)]
        pairs += [(rng.randrange(1 << 12), rng.randrange(1 << 12)) for _ in range(300)]
        for a, b in pairs:
            out, iterations, divisions = count_trial(a, b)
            self.assertEqual(out, math.gcd(a, b))
            if a == 0 or b == 0:
                self.assertEqual((iterations, divisions), (0, 0))
                continue
            g, lo = math.gcd(a, b), min(a, b)
            self.assertEqual(iterations, lo - g + 1)
            self.assertEqual(divisions, iterations + sum(1 for d in range(g, lo + 1) if a % d == 0))
            self.assertLessEqual(iterations, lo)

    def test_maximum_over_n_bit_inputs(self):
        for n in range(1, 8):
            best = 0
            for a in range(1 << n):
                for b in range(1 << n):
                    if max(a, b).bit_length() == n:
                        best = max(best, 0 if a == 0 or b == 0 else min(a, b) - math.gcd(a, b) + 1)
            self.assertEqual(best, 1 if n == 1 else (1 << n) - 2)
            if n >= 2:
                self.assertEqual(count_trial((1 << n) - 1, (1 << n) - 2)[1], (1 << n) - 2)

    def test_fibonacci_pairs(self):
        for n in range(1, 301):
            a, b = harness.generate_scaling(n, random.Random(n))
            k = _FIB.index(b, 1)                                              # b = F_k (F_1 for b = 1)
            self.assertEqual(a, fib(k + 1))
            self.assertTrue(fib(k + 1) < (1 << n) <= fib(k + 2))
            self.assertEqual(a.bit_length(), n)
            self.assertEqual(math.gcd(a, b), 1)
            self.assertLessEqual(fib(k + 2), 3 * fib(k))
            self.assertTrue(3 * b >= (1 << n) and 4 * b > (1 << n))
            if n <= 16:
                self.assertEqual(count_trial(a, b)[1], b)


class EuclidTests(unittest.TestCase):
    def test_step_bounds(self):
        for a in range(1 << 8):
            for b in range(1 << 8):
                out, k, _ = count_euclid(a, b)
                self.assertEqual(out, math.gcd(a, b))
                if b == 0:
                    self.assertEqual(k, 0)
                elif a == 0:
                    self.assertEqual(k, 1)
                elif a >= b:
                    self.assertGreaterEqual(b, fib(k + 1))                     # Lemma 5.1
                    if a > b:
                        self.assertGreaterEqual(a, fib(k + 2))
                    self.assertLessEqual(k, 5 * len(str(b)))                   # Corollary 5.4
                else:
                    self.assertGreaterEqual(a, fib(k))                         # Theorem 5.2, a < b
                n = max(a, b).bit_length()
                self.assertLess(k, 1.4405 * n + 2 + 1e-9)

    def test_fibonacci_pairs(self):
        for j in range(2, 401):
            _, k, qs = count_euclid(fib(j + 1), fib(j))
            self.assertEqual(k, j - 1)
            self.assertEqual(qs, [1] * (j - 2) + [2])
        self.assertEqual(count_euclid(*harness.generate_scaling(1, random.Random(1)))[1], 1)   # (1, 1)
        for n in list(range(2, 301)) + [4000, 8000, 16000, 32000, 64000]:
            a, b = harness.generate_scaling(n, random.Random(n))
            _, steps, _ = count_euclid(a, b)
            k = steps + 1                                                     # the pair is (F_(k+1), F_k)
            if n <= 300:
                self.assertEqual((fib(k + 1), fib(k)), (a, b))
            self.assertLessEqual(n / PHI_LOG2 - 2 - 1e-9, steps)
            self.assertLess(steps, n / PHI_LOG2)

    def test_quotient_product(self):
        rng = random.Random(4096)
        pairs = [(a, b) for a in range(1 << 8) for b in range(1 << 8)]
        for _ in range(200):
            bits = rng.randrange(64, 4097)
            pairs.append((rng.getrandbits(bits), rng.getrandbits(rng.randrange(1, bits + 1))))
        for a, b in pairs:
            _, k, qs = count_euclid(a, b)
            prod = 1
            for q in qs:
                prod *= max(q, 1)
            self.assertLessEqual(prod, max(a, b, 1))
            n = max(a, b).bit_length()
            self.assertLessEqual(sum(q.bit_length() + 2 for q in qs), 3 * k + n)


class SpaceTests(unittest.TestCase):
    @staticmethod
    def max_local_bits(fn, instance):
        code, peak = fn.__code__, [0]

        def tracer(frame, event, arg):
            if frame.f_code is code:
                for v in frame.f_locals.values():
                    if isinstance(v, int):
                        peak[0] = max(peak[0], int(v).bit_length())
                return tracer
            return None

        sys.settrace(tracer)
        try:
            fn(instance)
        finally:
            sys.settrace(None)
        return peak[0]

    def test_locals_have_at_most_n_bits(self):
        rng = random.Random(7)
        for _ in range(40):
            n = rng.randrange(1, 13)
            a, b = rng.getrandbits(n) | 1 << (n - 1), rng.getrandbits(n)
            self.assertLessEqual(self.max_local_bits(trial.gcd_trial, (a, b)), n)
        for _ in range(40):
            n = rng.randrange(1, 4097)
            a, b = rng.getrandbits(n), rng.getrandbits(n) | 1 << (n - 1)
            self.assertLessEqual(self.max_local_bits(euclid.gcd_euclid, (a, b)), n)


if __name__ == "__main__":
    unittest.main()
