"""Instances: (n, table) where table has 2^n entries and exactly one 1 (the marked element).

Outputs are (answer, queries).
"""


def generate(n, rng):
    marked = rng.randrange(1 << n)
    return n, tuple(1 if x == marked else 0 for x in range(1 << n))


def equal(a, b):
    return a[0] == b[0]


def check(instance, output):
    _, table = instance
    return table[output[0]] == 1


def reported_cost(output):
    return output[1]
