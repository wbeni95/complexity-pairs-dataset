"""Classical algorithm: query the n unit vectors. f(e_i) = s_i, so n queries recover s.

Optimal for classical algorithms: each query returns one bit, and s carries n bits.
"""
from lib.qsim import Oracle


def bv_classical(instance):
    n, table = instance
    oracle = Oracle(table)
    s = 0
    for i in range(n):
        s |= oracle(1 << i) << i
    return s, oracle.queries
