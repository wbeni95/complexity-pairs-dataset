"""Grover search for the unique marked element among N = 2^n: about (pi/4) sqrt(N) queries.

Each attempt runs k = floor(pi/4 * sqrt(N)) Grover iterations (phase-oracle query + diffusion), measures,
and confirms the candidate with one classical query; on the rare failure it repeats. Simulated exactly
with lib.qsim.
"""
import math
import random

from lib.qsim import Oracle, State


def search_grover(instance):
    n, table = instance
    oracle = Oracle(table)
    iterations = math.floor(math.pi / 4 * math.sqrt(1 << n))
    while True:
        state = State(n)
        state.h_all()
        for _ in range(iterations):
            oracle.apply_phase(state)
            state.reflect_about_uniform()
        candidate = state.measure_all(random)
        if oracle(candidate):  # one classical query to confirm
            return candidate, oracle.queries
