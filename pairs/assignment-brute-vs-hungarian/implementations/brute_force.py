"""Try every assignment: all n! permutations, Theta(n) to cost each.

Omega(n * n!) time on every input; Theta(n * n!) in total assuming itertools.permutations does O(n * n!) work over
the whole run, as its documented equivalent code does (see PROOFS.md, section 1).
"""
from itertools import permutations


def assignment_brute(C) -> int:
    n = len(C)
    best = None
    for perm in permutations(range(n)):
        cost = sum(C[i][perm[i]] for i in range(n))
        if best is None or cost < best:
            best = cost
    return best
