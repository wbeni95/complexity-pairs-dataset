"""Classical unstructured search: query the N = 2^n positions in random order until the marked one is found.

Expected (N + 1) / 2 queries; no classical algorithm, deterministic or randomized, does better than Omega(N).
"""
import random

from lib.qsim import Oracle


def search_classical(instance):
    n, table = instance
    oracle = Oracle(table)
    order = list(range(1 << n))
    random.shuffle(order)
    for x in order:
        if oracle(x):
            return x, oracle.queries
    raise ValueError("no marked element (instance violates the promise)")
