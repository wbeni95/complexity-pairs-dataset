"""Instances: pairs (a, b) of non-negative integers with max(a, b) of bit length exactly n.

The oracle is math.gcd, used here only as a reference, never as an implementation under test.
"""
import math


def generate(n, rng):
    if n == 0:
        return (0, 0)
    while True:
        kind = rng.random()
        if kind < 0.4:                      # a non-trivial common factor g
            k = rng.randint(1, n)
            g = rng.getrandbits(k - 1) | (1 << (k - 1))
            a, b = g * rng.getrandbits(n - k + 1), g * rng.getrandbits(n - k + 1)
        elif kind < 0.5:                    # one zero argument
            a, b = rng.getrandbits(n), 0
        else:                               # two random n-bit-or-less integers
            a, b = rng.getrandbits(n), rng.getrandbits(n)
        if max(a, b).bit_length() == n:
            return (a, b) if rng.random() < 0.5 else (b, a)


def check(instance, output):
    return output == math.gcd(*instance)


def generate_scaling(n, rng):
    """Consecutive Fibonacci numbers (F(k+1), F(k)), F(k+1) the largest Fibonacci number below 2^n.

    They are coprime, so trial division runs all the way down to d = 1 (F(k) >= 2^(n-2) iterations),
    and they are the worst case for Euclid (PROOFS.md section 5): k - 1 ~ 1.44 n division steps for n >= 2, every
    quotient but the last equal to 1.
    """
    a, b = 1, 1                             # (F(k+1), F(k)) for k = 1
    while a + b < (1 << n):
        a, b = a + b, a
    return (a, b)
