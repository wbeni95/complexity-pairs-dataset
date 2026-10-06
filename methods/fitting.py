"""Cost-shape fitting and the identifiability of logarithmic factors.

The V2 test of tools/validate.py fits y = log(measured) against x = log(cost(n)) and requires the least-squares
slope alpha to be 1 +- tol; its log-factor diagnostic refits against cost*log n and cost/log n and calls the log
factor "resolved" when both of those slopes leave the band (RL-048). This module reproduces that fit and adds:

* `noise_free_diagnostic(cost, ns, tol)`: the diagnostic slopes for PERFECT data (measured == cost exactly). If the
  log factor is not resolved even then, no amount of repetition or noise reduction can resolve it on that grid at
  that tolerance: the tolerance and the n-range are the binding constraint, not the noise.
* `alpha_se(cost, ns, sigma)`: the standard error of alpha under i.i.d. multiplicative noise
  (log y = log c + log cost + eps, eps ~ N(0, sigma^2)): SE = sigma / sqrt(sum (x_i - xbar)^2).
* `loglog_se(ns, sigma)`: the standard error of b in the free model log y = c + a log n + b log log n, i.e. how well
  a log exponent can be estimated when the power is ALSO free. It is large because log n and log log n are almost
  collinear on any practical range (variance inflation 1 / (1 - rho^2)).
* `select_model(ns, ys, candidates)`: least-squares selection among fixed shapes with a free constant (equal
  parameter counts, so BIC/AIC reduce to the residual sum of squares; Schwarz 1978, doi:10.1214/aos/1176344136).

The connection to empirical algorithmics: trend-prof (Goldsmith, Aiken, Wilkerson 2007,
doi:10.1145/1287624.1287681) fits power laws to basic-block counts; McGeoch's guide (2012, [book]) discusses the
same identifiability problem. The exact remedy used here is recurrence guessing on exact counts at n = 2^k
(see methods/recurrences.py and experiments/2026-10-06d_meth_log_identifiability.py).
"""
from __future__ import annotations

import math
from typing import Callable


def slope(xs: list[float], ys: list[float]) -> float:
    """Least-squares slope, identical to tools/validate.fit_slope."""
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def diagnostic(cost: Callable[[int], float], ns: list[int], values: list[float], tol: float) -> dict:
    """The validator's fit and log-factor diagnostic for given measured values."""
    xs = [math.log(cost(n)) for n in ns]
    ys = [math.log(v) for v in values]
    lx = [math.log(math.log(n)) for n in ns]
    a = slope(xs, ys)
    a_up = slope([x + l for x, l in zip(xs, lx)], ys)
    a_down = slope([x - l for x, l in zip(xs, lx)], ys)
    return {"alpha": a, "alpha_up": a_up, "alpha_down": a_down,
            "passes": abs(a - 1) <= tol, "resolves": abs(a_up - 1) > tol and abs(a_down - 1) > tol}


def noise_free_diagnostic(cost: Callable[[int], float], ns: list[int], tol: float) -> dict:
    return diagnostic(cost, ns, [cost(n) for n in ns], tol)


def min_resolving_tol(cost: Callable[[int], float], ns: list[int]) -> float:
    """Largest tolerance at which perfect data still resolve the log factor: min(|a_up - 1|, |a_down - 1|)."""
    d = noise_free_diagnostic(cost, ns, 0.0)
    return min(abs(d["alpha_up"] - 1), abs(d["alpha_down"] - 1))


def alpha_se(cost: Callable[[int], float], ns: list[int], sigma: float) -> float:
    xs = [math.log(cost(n)) for n in ns]
    mx = sum(xs) / len(xs)
    return sigma / math.sqrt(sum((x - mx) ** 2 for x in xs))


def loglog_se(ns: list[int], sigma: float) -> tuple[float, float]:
    """(SE of b, correlation of log n and log log n) in log y = c + a log n + b log log n with noise sigma."""
    u = [math.log(n) for n in ns]
    v = [math.log(math.log(n)) for n in ns]
    mu, mv = sum(u) / len(u), sum(v) / len(v)
    suu = sum((x - mu) ** 2 for x in u)
    svv = sum((x - mv) ** 2 for x in v)
    suv = sum((x - mu) * (y - mv) for x, y in zip(u, v))
    rho = suv / math.sqrt(suu * svv)
    ssr_v = svv - suv * suv / suu  # residual variation of log log n after regressing on (1, log n)
    return sigma / math.sqrt(ssr_v), rho


def select_model(ns: list[int], ys_log: list[float], candidates: dict[str, Callable[[int], float]]) -> str:
    """Name of the candidate shape f minimising sum (log y - log f(n) - c)^2 over the constant c."""
    best, best_rss = None, math.inf
    for name, f in candidates.items():
        r = [y - math.log(f(n)) for n, y in zip(ns, ys_log)]
        m = sum(r) / len(r)
        rss = sum((x - m) ** 2 for x in r)
        if rss < best_rss:
            best, best_rss = name, rss
    return best


def geometric_grid(n1: int, n2: int, k: int) -> list[int]:
    """k integers spaced geometrically from n1 to n2 (inclusive), strictly increasing."""
    out = []
    for i in range(k):
        v = round(n1 * (n2 / n1) ** (i / (k - 1)))
        if not out or v > out[-1]:
            out.append(v)
    return out
