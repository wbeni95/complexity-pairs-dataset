"""Deterministic exact classical algorithm: query x = 0, 1, 2, ... in this fixed order.

Stop with "balanced" as soon as two different values have been seen; stop with "constant" once 2^(n-1) + 1
equal values have been seen (more than half of the table, so no balanced function is consistent with them).
Never wrong. Worst case exactly 2^(n-1) + 1 queries, which is optimal for every deterministic exact
algorithm (adversary argument in entry.json). On a uniformly random balanced function it stops much earlier
(after 1 + G queries, where G is the waiting time for the first value different from f(0)).
"""
from lib.qsim import Oracle


def dj_classical(instance):
    n, table = instance
    oracle = Oracle(table)
    first = oracle(0)
    for x in range(1, (1 << (n - 1)) + 1):
        if oracle(x) != first:
            return "balanced", oracle.queries
    return "constant", oracle.queries
