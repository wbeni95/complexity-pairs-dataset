"""Classical minimum finding: read all N = 2^n values, keep the index of the smallest. Exactly N queries.

Optimal for exact algorithms (an unread entry could hold the minimum), and Theta(N) is necessary even for
bounded-error randomized algorithms (reduction from unstructured search; see entry.json).
"""
from lib.qsim import Oracle


def minimum_scan(instance):
    n, table = instance
    oracle = Oracle(table)
    best, best_value = 0, oracle(0)
    for x in range(1, 1 << n):
        v = oracle(x)
        if v < best_value:
            best, best_value = x, v
    return best, oracle.queries
