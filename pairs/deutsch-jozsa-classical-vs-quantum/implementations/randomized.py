"""Randomized classical algorithm with one-sided bounded error: K = 20 uniformly random queries.

Query K independent uniformly random points (with replacement). If two answers differ the function is
certainly not constant, so answer "balanced" (never wrong). If all K answers agree, answer "constant":
always right for a constant function, and wrong for a balanced function with probability exactly
2 * (1/2)^K = 2^(1-K) (each answer of a balanced function is an independent fair bit), here 2^-19 < 2e-6.

The cost is K = 20 queries for every n: O(1), or O(log(1/eps)) queries for error eps. This is why the
Deutsch-Jozsa separation is a separation from EXACT (zero-error) classical computation only.
"""
import random

from lib.qsim import Oracle

K = 20


def dj_randomized(instance):
    n, table = instance
    oracle = Oracle(table)
    answers = {oracle(random.randrange(1 << n)) for _ in range(K)}
    return ("balanced" if len(answers) > 1 else "constant"), oracle.queries
