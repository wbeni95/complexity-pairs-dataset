"""Deutsch-Jozsa, one-query version (Cleve, Ekert, Macchiavello & Mosca 1998): exactly 1 query, zero error.

H^n |0> gives the uniform superposition; one phase-oracle query gives sum_x (-1)^f(x) |x> / sqrt(N); a second
H^n maps it to a state whose amplitude on |0...0> is sum_x (-1)^f(x) / N, which is +-1 if f is constant and 0
if f is balanced. Measuring therefore yields 0 with probability 1 (constant) or 0 (balanced).
Simulated exactly with lib.qsim (floating-point residue on |0> for balanced f is at the 1e-16 level; see
experiments/2026-10-07_deutsch_jozsa_checks.py).
"""
import random

from lib.qsim import Oracle, State


def dj_quantum(instance):
    n, table = instance
    oracle = Oracle(table)
    state = State(n)
    state.h_all()
    oracle.apply_phase(state)
    state.h_all()
    outcome = state.measure_all(random)
    return ("constant" if outcome == 0 else "balanced"), oracle.queries
