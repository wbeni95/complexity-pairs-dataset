"""Classical algorithm for Simon's problem: query random distinct points until two collide.

f(x) = f(y) with x != y happens exactly when y = x XOR s, so the first collision reveals s.
Birthday bound: Theta(2^(n/2)) queries in expectation, which is optimal classically (Simon 1997).
"""
import random

from lib.qsim import Oracle


def simon_classical(instance):
    n, table = instance
    oracle = Oracle(table)
    seen = {}
    order = list(range(1 << n))
    random.shuffle(order)
    for x in order:
        fx = oracle(x)
        if fx in seen:
            return seen[fx] ^ x, oracle.queries
        seen[fx] = x
    raise ValueError("no collision (instance violates the promise)")
