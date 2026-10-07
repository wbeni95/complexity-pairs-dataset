"""Deterministic checks of pairs/modular-exponentiation-repeated-vs-square-multiply/PROOFS.md (the modulus,
exact multiplication counts, the addition-chain bounds, space)."""
import importlib.util
import math
import random
import tracemalloc
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "modular-exponentiation-repeated-vs-square-multiply"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


repeated = load("implementations/repeated.py", "proofs_modexp_repeated")
square_multiply = load("implementations/square_multiply.py", "proofs_modexp_sm")
harness = load("harness.py", "proofs_modexp_harness")
M = harness.M


class Counted(int):
    """A residue that counts products: x * x (the same object) as a squaring, any other product as a
    multiplication. Products and reductions return Counted, so the count follows the loop."""
    squarings = 0
    mults = 0

    def __mul__(self, other):
        if other is self:
            Counted.squarings += 1
        else:
            Counted.mults += 1
        return Counted(int(self) * int(other))

    __rmul__ = __mul__

    def __mod__(self, other):
        return Counted(int(self) % int(other))

    def __rmod__(self, other):                  # `1 % m` with a Counted modulus gives a Counted 1
        return Counted(int(other) % int(self))


def run(fn, a, e):
    Counted.squarings = Counted.mults = 0
    out = fn((Counted(a), e, Counted(M)))
    return int(out), Counted.squarings, Counted.mults


class ModulusTests(unittest.TestCase):
    FACTORS = [2, 2, 11, 137, 547, 5594472617641]
    # a divisor strictly between 1 and x of every odd x = 2^64 - k, k = 1, 3, ..., 57
    ODD_DIVISORS = {1: 3, 3: 13, 5: 11, 7: 3, 9: 7, 11: 5, 13: 3, 15: 53, 17: 19, 19: 3, 21: 5, 23: 7, 25: 3, 27: 11,
                    29: 13, 31: 3, 33: 827, 35: 17, 37: 3, 39: 139646831, 41: 5, 43: 3, 45: 11071, 47: 31, 49: 3,
                    51: 5, 53: 29, 55: 3, 57: 41}

    @staticmethod
    def trial_prime(x):
        if x < 2 or x % 2 == 0:
            return x == 2
        return all(x % d for d in range(3, math.isqrt(x) + 1, 2))

    def test_modulus_is_prime(self):
        self.assertEqual(M, 2 ** 64 - 59)
        self.assertEqual(math.prod(self.FACTORS), M - 1)
        self.assertEqual(math.isqrt(5594472617641), 2365263)
        for q in set(self.FACTORS):
            self.assertTrue(self.trial_prime(q), q)
        self.assertEqual(pow(2, M - 1, M), 1)
        for q in set(self.FACTORS):
            self.assertNotEqual(pow(2, (M - 1) // q, M), 1, q)

    def test_no_prime_between_m_and_2_64(self):
        for k in range(1, 59):
            x = 2 ** 64 - k
            d = 2 if x % 2 == 0 else self.ODD_DIVISORS[k]
            self.assertTrue(1 < d < x and x % d == 0, k)


class CountTests(unittest.TestCase):
    def test_repeated(self):
        rng = random.Random(1)
        for e in range(1 << 10):
            a = rng.randrange(M)
            out, sq, mu = run(repeated.modpow_repeated, a, e)
            self.assertEqual(out, pow(a, e, M))
            self.assertEqual(sq + mu, e)
        for n in range(1, 17):
            self.assertEqual(sum(run(repeated.modpow_repeated, 3, (1 << n) - 1)[1:]), (1 << n) - 1)

    def test_square_multiply(self):
        rng = random.Random(2)
        for e in range(1 << 12):
            a = rng.randrange(M)
            out, sq, mu = run(square_multiply.modpow_square_multiply, a, e)
            self.assertEqual(out, pow(a, e, M))
            if e == 0:
                self.assertEqual((sq, mu), (1, 0))
            else:
                self.assertEqual((sq, mu), (e.bit_length(), bin(e).count("1")))
                self.assertLessEqual(sq + mu, 2 * e.bit_length())
        for n in list(range(1, 65)) + [1000, 2000, 4000, 8000, 16000, 32000, 64000]:
            a, e, _ = harness.generate_scaling(n, random.Random(n))
            out, sq, mu = run(square_multiply.modpow_square_multiply, a, e)
            self.assertEqual((sq, mu), (n, n))
            if n <= 64:
                self.assertEqual(out, pow(a, e, M))


class AdditionChainTests(unittest.TestCase):
    def test_doubling_bound(self):
        frontier = [(1,)]
        for s in range(1, 7):
            nxt = []
            for seq in frontier:
                for i in range(len(seq)):
                    for j in range(i, len(seq)):
                        nxt.append(seq + (seq[i] + seq[j],))
            frontier = nxt
            self.assertLessEqual(max(max(seq) for seq in frontier), 2 ** s)
        # so no e <= 128 is reached in fewer than ceil(log2 e) <= 7 steps
        for e in range(1, 129):
            self.assertEqual((e - 1).bit_length(), math.ceil(math.log2(e)))

    def test_square_multiply_chain(self):
        for e in range(1, 1 << 12):
            bits = bin(e)[2:]
            chain, k = [1], 1                      # after the two trivial products: exponent 1 (= a)
            for b in bits[1:]:
                chain.append(k + k)
                k += k
                if b == "1":
                    chain.append(k + 1)
                    k += 1
            self.assertEqual(k, e)
            for idx in range(1, len(chain)):           # every element is a sum of two earlier ones
                self.assertTrue(any(chain[idx] - x in chain[:idx] for x in chain[:idx]))
            n = e.bit_length()
            length = len(chain) - 1
            self.assertEqual(length, (n - 1) + (bin(e).count("1") - 1))
            self.assertLessEqual(length, 2 * (n - 1))
            self.assertLessEqual(2 * (n - 1), 2 * (e - 1).bit_length())   # 2 ceil(log2 e)
        out, sq, mu = run(square_multiply.modpow_square_multiply, 5, 2)
        self.assertEqual((sq + mu, (2 - 1).bit_length()), (3, 1))


class SpaceTests(unittest.TestCase):
    def test_peak_memory(self):
        for n in (1000, 2000, 4000, 8000, 16000, 32000, 64000):
            a, e, m = harness.generate_scaling(n, random.Random(n))
            tracemalloc.start()
            try:
                square_multiply.modpow_square_multiply((a, e, m))
                peak = tracemalloc.get_traced_memory()[1]
            finally:
                tracemalloc.stop()
            self.assertLessEqual(peak, 3 * n + 1024, n)


if __name__ == "__main__":
    unittest.main()
