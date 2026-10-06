"""Try every assignment: all n! permutations, Theta(n) to cost each, Theta(n * n!) time in total."""
from itertools import permutations


def assignment_brute(C) -> int:
    n = len(C)
    best = None
    for perm in permutations(range(n)):
        cost = sum(C[i][perm[i]] for i in range(n))
        if best is None or cost < best:
            best = cost
    return best
