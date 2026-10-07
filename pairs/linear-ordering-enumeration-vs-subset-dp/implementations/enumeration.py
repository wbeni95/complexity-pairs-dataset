"""Linear ordering problem by enumerating all n! orders.

Instance: an n x n integer matrix W (tuple of tuples; the diagonal is ignored). The value of an order is the sum of
W[a][b] over all pairs with a before b. Output (maximum value, an order attaining it).
Each order is summed from scratch over its n(n-1)/2 ordered pairs: Theta(n! n^2) on every input, given the
documented cost of itertools.permutations (amortised O(n) per order; PROOFS.md section 6).
"""
from itertools import permutations


def linear_ordering_enumeration(w):
    n = len(w)
    best = None
    best_order = None
    for order in permutations(range(n)):
        value = 0
        for p in range(n):
            row = w[order[p]]
            for q in range(p + 1, n):
                value = value + row[order[q]]
        if best is None or value > best:
            best, best_order = value, order
    return best, best_order
