"""Instances: complete directed graph on n cities, integer distances in [1, 100] (not necessarily symmetric)."""


def generate(n, rng):
    return tuple(tuple(0 if i == j else rng.randint(1, 100) for j in range(n)) for i in range(n))


def check(W, output):
    n = len(W)
    if n <= 1:
        return output == 0
    # The identity tour 0 -> 1 -> ... -> n-1 -> 0 is feasible: an upper bound.
    identity = sum(W[i][(i + 1) % n] for i in range(n))
    return n <= output <= identity
