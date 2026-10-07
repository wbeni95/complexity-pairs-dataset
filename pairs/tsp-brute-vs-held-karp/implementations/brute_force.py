"""Try every tour that starts at city 0: (n-1)! permutations, Theta(n!) time in total.

The time bound assumes that itertools.permutations behaves as its documented equivalent code (PROOFS.md).
"""
from itertools import permutations


def tsp_brute(W) -> int:
    n = len(W)
    if n <= 1:
        return 0
    best = None
    for perm in permutations(range(1, n)):
        cost = W[0][perm[0]] + W[perm[-1]][0]
        for a, b in zip(perm, perm[1:]):
            cost += W[a][b]
        if best is None or cost < best:
            best = cost
    return best
