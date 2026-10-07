"""Permanent from the definition: sum over all n! permutations, Theta(n) per product; Theta(n * n!) time given
the documented cost of itertools.permutations (amortised O(n) per tuple; PROOFS.md section 0.1)."""
from itertools import permutations


def permanent_naive(A) -> int:
    n = len(A)
    total = 0
    for p in permutations(range(n)):
        prod = 1
        for i in range(n):
            prod *= A[i][p[i]]
        total += prod
    return total
