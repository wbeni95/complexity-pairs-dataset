"""Instances: (n, table) with table a uniformly random permutation of {0, ..., N-1}, N = 2^n.

Values are distinct, as assumed in Durr & Hoyer's analysis (their remark covers ties too). Outputs are
(answer, queries) with answer = the index of the minimum, which is unique, so implementations must agree.
"""


def generate(n, rng):
    values = list(range(1 << n))
    rng.shuffle(values)
    return n, tuple(values)


def equal(a, b):
    return a[0] == b[0]


def check(instance, output):
    """Independent check: the returned index holds the smallest value of the table."""
    _, table = instance
    return table[output[0]] == min(table)


def reported_cost(output):
    return output[1]
