"""Instances: complete digraph on n vertices, positive integer weights in [1, 100]; source 0, target n-1."""


def generate(n, rng):
    return tuple(tuple(0 if i == j else rng.randint(1, 100) for j in range(n)) for i in range(n))


def check(W, output):
    n = len(W)
    if n == 1:
        return output == 0
    # The direct edge is one path, so it bounds the optimum from above.
    return 0 < output <= W[0][n - 1]
