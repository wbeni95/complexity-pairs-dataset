"""Durr-Hoyer quantum minimum finding (arXiv quant-ph/9607014): O(sqrt N) queries, success probability >= 1/2.

The algorithm exactly as published:
  1. Choose a threshold index y uniformly at random.
  2. Repeat, and interrupt when the total running time exceeds 22.5 sqrt(N) + 1.4 lg^2 N; then go to 2(c):
     (a) prepare the uniform superposition and mark every j with T[j] < T[y];
     (b) run the BBHT exponential search (lib.qsearch.exponential_search);
     (c) observe the register; if the outcome y' has T[y'] < T[y], set y = y'.
  3. Return y.
"Running time" uses the paper's convention: stage 2(a) costs lg N time steps, one BBHT (Grover) iteration
costs one time step, and stages 1, 2(c) and 3 cost nothing. The time-out is applied in exactly these units, so
Theorem 1 (success probability >= 1/2) applies to this implementation as written.

Query accounting (what reported_cost measures, separately from the paper's time units):
  - 1 classical query for T[y] at step 1 (the threshold value defining the marking);
  - 2 queries per Grover iteration: the marking "T[j] < T[y]" is a property of the VALUE T[j], so each
    iteration computes T[j] with U_T, flips the phase, and uncomputes T[j] with U_T (Oracle.apply_phase_where;
    BBHT 1998, sections 3.1 and 7);
  - 1 classical query per observed candidate (the comparison in BBHT's step 5 and Durr-Hoyer's 2(c)).

durr_hoyer_run exposes the internals for experiments/2026-10-07_minimum_finding.py: with budget=None and
stop_value set, it runs the paper's "infinite algorithm" until the threshold holds the given value, so the
time to reach the minimum can be compared with Lemma 2 (m0 = 45/4 sqrt N + 7/10 lg^2 N).
"""
import math
import random

from lib import qsearch
from lib.qsim import Oracle, State


def durr_hoyer_budget(n):
    """22.5 sqrt(N) + 1.4 lg^2 N time steps (Durr & Hoyer, step 2)."""
    return 22.5 * math.sqrt(1 << n) + 1.4 * n * n


def durr_hoyer_run(instance, rng, budget="paper", stop_value=None):
    """Returns dict(index, queries, time, thresholds, measurements)."""
    n, table = instance
    N = 1 << n
    if budget == "paper":
        budget = durr_hoyer_budget(n)
    oracle = Oracle(table)
    lg = n  # lg N
    time = 0.0
    y = rng.randrange(N)  # step 1
    ty = oracle(y)
    thresholds, measurements = 1, 0

    def result():
        return {"index": y, "queries": oracle.queries, "time": time,
                "thresholds": thresholds, "measurements": measurements}

    while True:
        if stop_value is not None and ty == stop_value:
            return result()
        if budget is not None and time + lg > budget:
            # Interrupted during stage 2(a): the register holds the uniform superposition; 2(c) observes it.
            x = State.uniform(n).measure_all(rng)
            measurements += 1
            tx = oracle(x)
            if tx < ty:
                y, ty, thresholds = x, tx, thresholds + 1
            return result()
        time += lg  # stage 2(a)
        threshold = ty
        last = {}

        def phase(state):
            oracle.apply_phase_where(state, lambda j, tj: tj < threshold)

        def check(x):
            nonlocal measurements
            measurements += 1
            last["value"] = tx = oracle(x)
            return tx < threshold

        remaining = None if budget is None else budget - time
        x, iterations, interrupted = qsearch.exponential_search(n, phase, check, rng, budget=remaining)  # 2(b)
        time += iterations
        if x is not None:  # 2(c)
            y, ty, thresholds = x, last["value"], thresholds + 1
        if interrupted:
            return result()


def minimum_durr_hoyer(instance):
    out = durr_hoyer_run(instance, random)
    return out["index"], out["queries"]
