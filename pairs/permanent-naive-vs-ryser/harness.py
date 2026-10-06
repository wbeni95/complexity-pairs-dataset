"""Instances: n x n integer matrices (tuples of tuples) with small entries.

generate alternates between 0/1 matrices (the permanent then counts the perfect matchings of a
bipartite graph, the #P-complete case) and entries in [-2, 3] (negative entries and cancellation).
generate_scaling uses entries in [1, 4] so that no product is trivially zero.
"""


def generate(n, rng):
    if rng.random() < 0.5:
        return tuple(tuple(rng.randint(0, 1) for _ in range(n)) for _ in range(n))
    return tuple(tuple(rng.randint(-2, 3) for _ in range(n)) for _ in range(n))


def generate_scaling(n, rng):
    return tuple(tuple(rng.randint(1, 4) for _ in range(n)) for _ in range(n))


def _subset_dp(A):
    """Exact permanent by DP over column subsets, O(n 2^n), independent of both implementations:
    ways[S] = sum over assignments of rows 0..|S|-1 to exactly the columns in S of the product of entries."""
    n = len(A)
    ways = [0] * (1 << n)
    ways[0] = 1
    for S in range(1, 1 << n):
        i = bin(S).count("1") - 1
        ways[S] = sum(ways[S ^ (1 << j)] * A[i][j] for j in range(n) if S >> j & 1)
    return ways[-1]


def _det_mod2(A):
    """Determinant over GF(2) by Gaussian elimination on bitmask rows."""
    rows = [sum((A[i][j] & 1) << j for j in range(len(A))) for i in range(len(A))]
    for c in range(len(A)):
        piv = next((r for r in range(c, len(rows)) if rows[r] >> c & 1), None)
        if piv is None:
            return 0
        rows[c], rows[piv] = rows[piv], rows[c]
        for r in range(c + 1, len(rows)):
            if rows[r] >> c & 1:
                rows[r] ^= rows[c]
    return 1


def check(A, output):
    # Over GF(2), +1 = -1, so the permanent and the determinant agree mod 2 (a cheap, exact invariant).
    if output % 2 != _det_mod2(A):
        return False
    if len(A) <= 12:
        return output == _subset_dp(A)
    return True
