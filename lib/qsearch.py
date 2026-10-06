"""Quantum search subroutines on top of lib/qsim.py, for query-model (T9) entries. Added 2026-10-06.

Both searches look for a marked x in {0, ..., N-1}, N = 2^n. The caller supplies two callables:

  phase(state)   applies the phase oracle |x> -> (-1)^[x marked] |x> once and charges its own queries
                 (Oracle.apply_phase for a Boolean f: 1 query; Oracle.apply_phase_where for a property
                 of a non-Boolean f: 2 queries, compute + uncompute);
  check(x)       decides classically whether a measured candidate x is marked, charging its own queries
                 (normally one classical query).

One Grover iteration is phase(state) followed by the query-free diffusion (reflection about the uniform
superposition, State.reflect_about_uniform).

  search_known_count   t = number of marked elements is KNOWN: floor(pi / (4 theta)) iterations with
                       sin^2(theta) = t / N, measure, check; repeat on failure. Las Vegas.
                       (Boyer, Brassard, Hoyer & Tapp 1998, section 3: failure probability <= t / N.)
  exponential_search   t is UNKNOWN (BBHT 1998, section 4): m = 1, lambda = 6/5; draw j uniformly from the
                       integers 0 <= j < m; j iterations from the uniform superposition; measure; check;
                       otherwise m = min(lambda m, sqrt N) and repeat. Expected O(sqrt(N / t)) iterations
                       (BBHT Theorem 3: at most (9/2) m0 with m0 = N / (2 sqrt((N - t) t)), for 1 <= t <= 3N/4).
                       Optional iteration budget (time-out), as needed by Durr-Hoyer minimum finding.

expected_cost_known and expected_cost_exponential return the EXACT expected number of queries of these two
procedures (for the precise schedules implemented here), so that simulations can be compared with theory
by z-scores and not only by a fitted slope. tests/test_qsim.py checks the formulas against BBHT's closed
form (Lemma 2) and against simulation.
"""
from __future__ import annotations

import math

from lib.qsim import State

LAMBDA = 6 / 5  # BBHT: any value strictly between 1 and 4/3 works; 6/5 is the paper's choice.
_EPS = 1e-9     # guards floor() against rounding when pi / (4 theta) is mathematically an integer (t = N/2)


def grover_angle(N: int, t: int) -> float:
    """theta with sin^2(theta) = t / N."""
    return math.asin(math.sqrt(t / N))


def known_count_iterations(N: int, t: int) -> int:
    """BBHT section 3: m = floor(pi / (4 theta)); after m iterations the failure probability is <= t / N."""
    return math.floor(math.pi / (4 * grover_angle(N, t)) + _EPS)


def success_probability(N: int, t: int, j: int) -> float:
    """Probability of measuring a marked element after j Grover iterations: sin^2((2j + 1) theta)."""
    return math.sin((2 * j + 1) * grover_angle(N, t)) ** 2


def bbht_schedule(N: int):
    """The values of m used by exponential_search: 1, then min(lambda m, sqrt N) forever."""
    m, root = 1.0, math.sqrt(N)
    while True:
        yield m
        m = min(LAMBDA * m, root)


def grover_iteration(state: State, phase) -> None:
    phase(state)
    state.reflect_about_uniform()


def search_known_count(n: int, phase, check, t: int, rng, max_attempts: int = 10_000):
    """Find a marked element when exactly t >= 1 are marked. Returns (x, attempts).

    Each attempt: uniform superposition, known_count_iterations(N, t) Grover iterations, measure, check(x).
    """
    if t < 1:
        raise ValueError("search_known_count needs t >= 1 marked elements")
    iterations = known_count_iterations(1 << n, t)
    for attempt in range(1, max_attempts + 1):
        state = State.uniform(n)
        for _ in range(iterations):
            grover_iteration(state, phase)
        x = state.measure_all(rng)
        if check(x):
            return x, attempt
    raise RuntimeError(f"no marked element found in {max_attempts} attempts (is t = {t} correct?)")


def exponential_search(n: int, phase, check, rng, budget: float | None = None):
    """BBHT exponential search for an unknown number of marked elements. Returns (x, iterations, interrupted).

    x is a checked marked element, or None. Without a budget the search runs until it finds one (forever if
    nothing is marked). With a budget (a maximum number of Grover iterations):
      - an iteration is performed only if iterations + 1 <= budget; when the next iteration of the current
        attempt would exceed the budget, the CURRENT state is measured and checked, and the search stops
        with interrupted = True (this is the time-out of Durr & Hoyer, whose step 2(c) then observes
        the register);
      - a new attempt is started only while iterations < budget; otherwise the search stops with
        interrupted = True and x = None, without a further measurement.
    """
    N = 1 << n
    iterations = 0
    for m in bbht_schedule(N):
        if budget is not None and iterations >= budget:
            return None, iterations, True
        j = rng.randrange(math.ceil(m))  # uniform over the integers 0 <= j < m
        state = State.uniform(n)
        interrupted = False
        for _ in range(j):
            if budget is not None and iterations + 1 > budget:
                interrupted = True
                break
            grover_iteration(state, phase)
            iterations += 1
        x = state.measure_all(rng)
        if check(x):
            return x, iterations, interrupted
        if interrupted:
            return None, iterations, True


def expected_cost_known(N: int, t: int, q_iter: float, q_check: float) -> float:
    """Exact expected cost of search_known_count: (q_iter * m + q_check) / sin^2((2m + 1) theta)."""
    m = known_count_iterations(N, t)
    return (q_iter * m + q_check) / success_probability(N, t, m)


def expected_cost_exponential(N: int, t: int, q_iter: float, q_check: float) -> float:
    """Exact expected cost of exponential_search without a budget, for t >= 1 marked elements.

    Attempt s draws j uniformly from {0, ..., M_s - 1} with M_s = ceil(m_s), costs q_iter * j + q_check, and
    succeeds with probability p_s = mean_j sin^2((2j + 1) theta). Once m_s has reached sqrt(N) all later
    attempts are identical, so the remaining expectation is a geometric series, summed in closed form.
    With q_iter = 1 and q_check = 0 this is the expected number of Grover iterations.
    """
    if t < 1:
        raise ValueError("expected cost is infinite when nothing is marked")
    root = math.sqrt(N)
    total, reach = 0.0, 1.0
    for m in bbht_schedule(N):
        M = math.ceil(m)
        p = sum(success_probability(N, t, j) for j in range(M)) / M
        cost = q_iter * (M - 1) / 2 + q_check
        if m >= root:
            return total + reach * cost / p
        total += reach * cost
        reach *= 1 - p
        if reach < 1e-300:
            return total


def bbht_lemma2(N: int, t: int, M: int) -> float:
    """BBHT Lemma 2 closed form for the success probability with j uniform in {0, ..., M-1}, 1 <= t < N:
    1/2 - sin(4 M theta) / (4 M sin(2 theta))."""
    theta = grover_angle(N, t)
    return 0.5 - math.sin(4 * M * theta) / (4 * M * math.sin(2 * theta))


def bbht_theorem3_bound(N: int, t: int) -> float:
    """BBHT Theorem 3 upper bound on the expected number of Grover iterations: (9/2) m0, m0 = N / (2 sqrt((N-t) t)).
    Proven for 1 <= t <= 3N/4."""
    return 4.5 * N / (2 * math.sqrt((N - t) * t))
