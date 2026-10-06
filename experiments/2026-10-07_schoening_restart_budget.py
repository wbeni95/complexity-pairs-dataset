"""Computation (deterministic, exact rational arithmetic): the per-try success lower bound p(n) used by
pairs/3sat-brute-force-vs-schoening/implementations/schoening.py, its relation to (3/4)^n / sqrt(n), and the
restart budget T(n) = ceil(ln(10^6) / p(n)) for an error probability <= 10^-6.

  p(n) = sum_{j=0..n} C(n, j) 2^-n C(3j, j) (1/3)^(2j) (2/3)^j

(distance j from a fixed solution after the random start, then a run of 3j flips with exactly j steps away
from it, each flip moving toward it with probability >= 1/3).

Outcome (2026-10-07): p(n) / ((3/4)^n / sqrt(n)) = 0.9996, 0.9715, 0.9392, 0.9152, 0.8987, 0.8877, 0.8801,
0.8709 for n = 3, 6, 8, 10, 12, 14, 16, 20, so it lies between 0.87 and 0.89 for n = 14..20.
T(n) = 57, 196, 416, 848, 1682, 3269, 6265, 22371 tries; T(n) * 3n = 513 ... 1342260 flips.
The values printed for n = 4..12 match the T used in experiments/2026-10-07_3sat_timing_probe.py
(88, 196, 416, 848, 1682 for n = 4, 6, 8, 10, 12).

Run from the repository root:  python experiments/2026-10-07_schoening_restart_budget.py
"""
from fractions import Fraction
from math import ceil, comb, log, sqrt


def p_lower(n):
    return sum(Fraction(comb(n, j), 2 ** n) * comb(3 * j, j) * Fraction(1, 3) ** (2 * j) * Fraction(2, 3) ** j
               for j in range(n + 1))


for n in [3, 4, 6, 8, 10, 12, 14, 16, 20]:
    p = float(p_lower(n))
    T = ceil(log(1e6) / p)
    print(f"n={n}: p(n) = {p:.5g}; (3/4)^n = {0.75 ** n:.4g}; p / ((3/4)^n / sqrt(n)) = {p / 0.75 ** n * sqrt(n):.4f}; "
          f"T(n) = {T}; T(n) * 3n = {T * 3 * n}")
