"""Instances: (n, table) with table[x] = s.x mod 2 for a hidden random n-bit string s.

Outputs are (answer, queries); V1 compares answers, and V2 fits the query counts.
"""


def generate(n, rng):
    s = rng.getrandbits(n) if n else 0
    return n, tuple(bin(s & x).count("1") & 1 for x in range(1 << n))


def equal(a, b):
    return a[0] == b[0]


def check(instance, output):
    """Independent check: the answer must reproduce the whole truth table."""
    n, table = instance
    s = output[0]
    return all(table[x] == bin(s & x).count("1") & 1 for x in range(1 << n))


def reported_cost(output):
    return output[1]
