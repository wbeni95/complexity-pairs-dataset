"""Instances: a chain of n matrices, given as n + 1 dimensions in [1, 50]."""


def generate(n, rng):
    return tuple(rng.randint(1, 50) for _ in range(n + 1))


def check(dims, output):
    n = len(dims) - 1
    if n <= 1:
        return output == 0
    if n == 2:
        return output == dims[0] * dims[1] * dims[2]
    # Upper bound: the left-to-right parenthesisation is one valid order.
    left_to_right = sum(dims[0] * dims[k] * dims[k + 1] for k in range(1, n))
    return 0 < output <= left_to_right
