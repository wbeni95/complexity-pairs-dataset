"""Schöning's random walk for 3-SAT, as a Monte Carlo algorithm with one-sided error.

One try: draw a uniformly random assignment; then 3n times: if it satisfies the formula, answer True;
otherwise take the first falsified clause (in input order) and flip one of its literals' variables, chosen
uniformly at random. A final check follows the last flip.

Success probability of one try. Fix a satisfying assignment a*. A falsified clause has all its literals
false under the current assignment and at least one literal true under a*, so each flip decreases the
Hamming distance to a* with probability >= 1/3 (and otherwise increases it by 1). From distance j, a run of
3j flips with exactly j increases reaches a* (or another satisfying assignment earlier), which by comparison
with a walk of success probability exactly 1/3 per step gives probability >= C(3j, j) (1/3)^(2j) (2/3)^j.
Averaging over the random start (distance j with probability C(n, j) / 2^n):
    p(n) = sum_{j=0..n} C(n, j) 2^-n C(3j, j) (1/3)^(2j) (2/3)^j,
which lies between 0.87 and 0.89 times (3/4)^n / sqrt(n) for n = 14..20 (computed), the (3/4)^n / poly(n)
order of Schöning 1999.

Error control: T(n) = ceil(ln(1/DELTA) / p(n)) independent tries. A satisfiable formula is then reported
unsatisfiable with probability <= (1 - p(n))^T(n) <= exp(-p(n) T(n)) <= DELTA = 10^-6. An unsatisfiable
formula is always reported unsatisfiable (no try can succeed).

Cost: at most T(n) (3n + 1) clause scans of O(m) each: O((4/3)^n sqrt(n) n m) time on every input. On
unsatisfiable formulas every try runs to the end (all T(n) (3n + 1) scans); a scan stops at the first falsified
clause, so how many of the m clauses it checks depends on the formula.

Uses the global `random` module (the validator re-seeds it before every call, so runs are reproducible).
Formula format as in brute_force.py. Returns True iff a satisfying assignment was found.
"""
import math
import random

DELTA = 1e-6


def success_lower_bound(n):
    return sum(math.comb(n, j) / 2 ** n * math.comb(3 * j, j) * (1 / 3) ** (2 * j) * (2 / 3) ** j
               for j in range(n + 1))


def tries_needed(n, delta=DELTA):
    return math.ceil(math.log(1 / delta) / success_lower_bound(n))


def sat_schoening(formula) -> bool:
    n, clauses = formula
    if any(len(c) == 0 for c in clauses):
        return False
    for _ in range(tries_needed(n)):
        value = [False] + [random.random() < 0.5 for _ in range(n)]   # value[v] for v = 1..n
        for step in range(3 * n + 1):
            falsified = None
            for clause in clauses:
                for lit in clause:
                    if value[abs(lit)] == (lit > 0):
                        break
                else:
                    falsified = clause
                    break
            if falsified is None:
                return True
            if step < 3 * n:
                v = abs(random.choice(falsified))
                value[v] = not value[v]
    return False
