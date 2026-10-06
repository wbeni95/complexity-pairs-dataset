"""Instances: n x n integer cost matrices (tuples of tuples).

generate mixes three kinds so that V1 sees ties, negative costs and the worst case:
uniform costs in [0, 99], costs in [-3, 3] (many ties, negatives), and the column-dominant
family used for timing (below).

generate_scaling: C[i][j] = 1000 j + r(i, j) with r uniform in [0, 999]. Every row ranks the columns
in the same order, so each newly inserted row's shortest-path search visits every already matched
column before it reaches a free one: ~n^2/2 search steps of Theta(n) each, the Theta(n^3) worst case
of the Hungarian implementation. (On uniformly random matrices the search usually stops much earlier.)
"""


def generate(n, rng):
    kind = rng.randrange(3)
    if kind == 0:
        return tuple(tuple(rng.randint(0, 99) for _ in range(n)) for _ in range(n))
    if kind == 1:
        return tuple(tuple(rng.randint(-3, 3) for _ in range(n)) for _ in range(n))
    return generate_scaling(n, rng)


def generate_scaling(n, rng):
    return tuple(tuple(1000 * j + rng.randint(0, 999) for j in range(n)) for _ in range(n))


def _subset_dp(C):
    """Exact optimum by DP over column subsets, O(n 2^n): an algorithm independent of both implementations.
    best[S] = cheapest way to assign rows 0..|S|-1 to exactly the columns in S."""
    n = len(C)
    best = [None] * (1 << n)
    best[0] = 0
    for S in range(1, 1 << n):
        i = bin(S).count("1") - 1  # the row assigned last
        best[S] = min(best[S ^ (1 << j)] + C[i][j] for j in range(n) if S >> j & 1)
    return best[-1]


def check(C, output):
    n = len(C)
    if n == 0:
        return output == 0
    if n <= 12:
        return output == _subset_dp(C)
    # Larger n: the identity assignment is feasible (upper bound); every row and every column
    # must be assigned somewhere (two lower bounds).
    upper = sum(C[i][i] for i in range(n))
    row_lb = sum(min(r) for r in C)
    col_lb = sum(min(col) for col in zip(*C))
    return max(row_lb, col_lb) <= output <= upper
