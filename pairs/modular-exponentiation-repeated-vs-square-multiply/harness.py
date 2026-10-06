"""Instances: (a, e, m) with the fixed 64-bit prime modulus m = 2^64 - 59 and n = bit length of e.

The oracle is Python's built-in three-argument pow, used here only as a reference, never as an
implementation under test.
"""

M = 2 ** 64 - 59  # the largest prime below 2^64; every residue fits in one 64-bit word


def _exponent(n, rng):
    """A uniformly random exponent of bit length exactly n (n = 0 gives e = 0)."""
    if n == 0:
        return 0
    return rng.getrandbits(n - 1) | (1 << (n - 1))


def generate(n, rng):
    r = rng.random()
    if r < 0.1:
        a = rng.choice((0, 1, M - 1))      # edge bases
    elif r < 0.2:
        a = rng.getrandbits(80)            # base larger than m: must be reduced first
    else:
        a = rng.randrange(M)
    return (a, _exponent(n, rng), M)


def check(instance, output):
    a, e, m = instance
    return output == pow(a, e, m)


def generate_scaling(n, rng):
    """e = 2^n - 1 (all n bits set): the worst case for both algorithms at bit length n.

    Repeated multiplication does 2^n - 1 multiplications; square-and-multiply does n squarings
    and n multiplications.
    """
    return (rng.randrange(2, M), (1 << n) - 1, M)
