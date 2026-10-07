"""Bernstein-Vazirani: one quantum query recovers s exactly (in exact arithmetic).

H^n |0> = uniform superposition; the phase oracle gives sum_x (-1)^(s.x) |x>; H^n maps that to |s>.
Simulated with lib.qsim, exact up to floating-point rounding: the intended outcome has probability 1 - O(1e-15)
(PROOFS.md, "Exact arithmetic"). The simulation is exponential in n; the algorithm uses 1 query.
"""
import random

from lib.qsim import Oracle, State


def bv_quantum(instance):
    n, table = instance
    oracle = Oracle(table)
    state = State(n)
    state.h_all()
    oracle.apply_phase(state)
    state.h_all()
    s = state.measure_all(random)
    return s, oracle.queries
