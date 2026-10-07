"""Schoolbook (long) multiplication of digit lists: Theta(n^2) digit operations.

Numbers are little-endian lists of base-2^15 digits (a[0] is the least significant digit).
Every value computed from digits stays below 2^30, so each step is a single-word operation.
"""

BITS = 15
BASE = 1 << BITS
MASK = BASE - 1


def multiply_schoolbook(instance):
    """Return the product of two digit lists as a list of len(a) + len(b) digits (high digits may be 0)."""
    a, b = instance
    res = [0] * (len(a) + len(b))
    for i, ai in enumerate(a):
        carry = 0
        k = i
        for bj in b:
            t = res[k] + ai * bj + carry  # < BASE^2: one word
            res[k] = t & MASK
            carry = t >> BITS
            k += 1
        res[k] = carry  # position i + len(b) has not been written by earlier rows
    return res
