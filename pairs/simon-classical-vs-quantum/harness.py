"""Instances: (n, table) for a random 2-to-1 function with f(x) = f(x XOR s), hidden s != 0.

The values are a random relabelling of the cosets {x, x XOR s}. Outputs are (answer, queries).
"""


def generate(n, rng):
    if n < 1:
        raise ValueError("Simon's problem needs n >= 1")
    s = rng.randrange(1, 1 << n)
    labels = list(range(1 << n))
    rng.shuffle(labels)
    return n, tuple(labels[min(x, x ^ s)] for x in range(1 << n))


def equal(a, b):
    return a[0] == b[0]


def check(instance, output):
    """Independent check of the promise structure: s != 0 and f(x) = f(x XOR s) for every x."""
    n, table = instance
    s = output[0]
    return 0 < s < (1 << n) and all(table[x] == table[x ^ s] for x in range(1 << n))


def reported_cost(output):
    return output[1]
