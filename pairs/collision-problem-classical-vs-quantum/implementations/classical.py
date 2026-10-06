"""Classical birthday algorithm: query distinct points in uniformly random order until a value repeats.

For ANY fixed 2-to-1 function, the random order makes the number of queries Q distributed exactly as
P(Q > q) = prod_{i=1}^{q-1} (N - 2i) / (N - i): after i collision-free queries, i of the N - i unqueried points
are partners of queried ones. E[Q] ~ sqrt(pi N / 2) = Theta(sqrt N). The same conditional probability
i / (N - i) holds for every next query of every classical algorithm on a uniformly random 2-to-1 function,
which is the birthday lower bound recorded in entry.json. At most N/2 + 1 queries (pigeonhole).
"""
import random

from lib.qsim import Oracle


def collision_classical(instance):
    n, table = instance
    oracle = Oracle(table)
    seen = {}
    order = list(range(1 << n))
    random.shuffle(order)
    for x in order:
        fx = oracle(x)
        if fx in seen:
            a, b = sorted((seen[fx], x))
            return (a, b), oracle.queries
        seen[fx] = x
    raise ValueError("no collision (instance violates the 2-to-1 promise)")
