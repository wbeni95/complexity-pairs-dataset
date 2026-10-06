#!/usr/bin/env python3
"""Could the V2 slope test tell each candidate pair's two cost claims apart? (pattern mining, 2026-10-07)

Question: tools/validate.py accepts a claimed cost f(n) if the log-log slope alpha of measured cost against f(n)
satisfies |alpha - 1| <= 0.25 over the timed n values. For a candidate pair (slow cost g, fast cost f), would a
FAST implementation that secretly behaved like the SLOW cost g be caught by the V2 fit against f? If not, V2 can
confirm that the fast algorithm is "fast enough" only up to the gap the test cannot resolve, and the pair has to
stay at V1 for the separation (as RL-006 found for Strassen).

Method (idealised, noise-free, no timing): over the n range on which the FAST algorithm would be timed, compute
rho = least-squares slope of log g(n) against log f(n), i.e. the alpha that noise-free data following g would
produce in a fit against f. "caught" means |rho - 1| > 0.25. The n range is ESTIMATED: all n with
1e-4 s <= U * f(n) <= 0.3 s, assuming U = 1e-7 s per unit of the cost expression (a rough CPython figure; the
validator's own calibration note gives ~3.5e-8 s per naive Fibonacci call). For pure power laws and pure
exponentials rho does not depend on the range; for log factors and mixed terms it does, so treat those rows as
indicative. Cost expressions use the validator's own evaluator (tools/validate.eval_cost) and slope fit
(tools/validate.fit_slope). Deterministic: no randomness, no timing.

Rows marked [existing] re-derive known dataset findings as a sanity check: Strassen n^3 vs n^log2(7) gives
rho = 1.069 (not caught, consistent with RL-006); Karatsuba n^2 vs n^log2(3) gives 1.262 (caught narrowly,
consistent with that entry's caveat); n log n vs n is not caught (consistent with RL-018's log-factor finding).

Result (run 2026-10-07; deterministic, a rerun prints the same table): the [existing] sanity rows
reproduce the known findings (Strassen 1.069 NOT caught; Karatsuba 1.262 caught, borderline; TSP n! vs n^2 2^n
2.505 caught; n log n vs n 1.095
NOT caught). Among the candidates, NOT caught: subset convolution 3^n vs n^2 2^n over the feasible n = 6..13
(rho = 1.205: the n^2 factor eats most of the gap at small n), Stoer-Wagner n^3 vs Karger-Stein n^2 log^3 n
(1.050), and the near-misses Toom-3 vs Karatsuba (1.082), Held-Karp vs Bjorklund 1.657^n (1.082) and
Max-2-CSP brute vs Williams-with-Strassen (1.069). Every other candidate row is caught; the smallest margins
are NAND tree 1.327, partitions DP vs pentagonal 1.333, Faddeev-LeVerrier vs Hessenberg 1.333, three collinear
points 1.352 and zeta transform 1.415. Borderline rows (|rho - 1| within 0.02 of 0.25) are flagged.
The report (research/2026-10-07_patterns.md, section 3) copies rho and the verdict for every ranked candidate.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402

U = 1e-7          # assumed seconds per unit of the cost expression (rough, see docstring)
T_LO, T_HI = 1e-4, 0.3
TOL = 0.25

# (label, meaning of n, slow cost g, fast cost f). Query-model rows (reported counts, not time) get an explicit
# n range in NS_OVERRIDE: there the limit is what the classical/quantum SIMULATION can reach, not 0.3 s.
NS_OVERRIDE = {
    "C NAND tree: deterministic vs randomized (queries)": list(range(6, 21, 2)),
    "C mean estimation (queries): classical vs quantum": list(range(3, 11)),
    "C order finding (queries): classical LB vs quantum": list(range(4, 13)),
}


def _log_binom(a: int, b: int) -> float:
    return math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)


# Slow costs whose value overflows a float inside eval_cost: give log g(n) directly.
LOG_G = {
    "C spanning-tree count: enumeration vs Kirchhoff": lambda n: math.log(n) + _log_binom(n * (n - 1) // 2, n - 1),
}
ROWS = [
    ("[existing] Strassen", "matrix dim", "n**3", "n**log2(7)"),
    ("[existing] Karatsuba", "digits", "n**2", "n**log2(3)"),
    ("[existing] log factor: n log n vs n", "length", "n*log(n)", "n"),
    ("[existing] TSP brute vs Held-Karp", "cities", "factorial(n)", "n**2 * 2**n"),
    ("C subset convolution: naive vs ranked zeta", "ground set size", "3**n", "n**2 * 2**n"),
    ("C zeta (subset sums): naive vs Yates", "ground set size", "3**n", "n * 2**n"),
    ("C XOR convolution: naive vs FWHT", "bits", "4**n", "n * 2**n"),
    ("C regex (a?)^n a^n: backtracking vs Thompson", "n", "2**n", "n**2"),
    ("C multi-pattern: naive vs Aho-Corasick", "text length", "n**2", "n"),
    ("C global min cut: brute vs Stoer-Wagner", "vertices", "2**n * n**2", "n**3"),
    ("C global min cut: Stoer-Wagner vs Karger-Stein", "vertices", "n**3", "n**2 * log(n)**3"),
    ("C row minima totally monotone: naive vs SMAWK", "n x n", "n**2", "n"),
    ("C optimal BST: recursion vs DP", "keys", "3**n", "n**3"),
    ("C optimal BST: DP vs Knuth", "keys", "n**3", "n**2"),
    ("C longest common substring: DP vs suffix automaton", "length", "n**2", "n"),
    ("C LCS on permutations: DP vs Hunt-Szymanski", "length", "n**2", "n*log(n)"),
    ("C NAND tree: deterministic vs randomized (queries)", "height", "2**n", "((1+sqrt(33))/4)**n"),  # ns override
    ("C 2-SAT: brute vs implication graph SCC", "variables (m=Theta(n))", "2**n * n", "n"),
    ("C partitions p(n): enumeration vs DP", "n (value)", "exp(pi*sqrt(2*n/3))/n", "n**2"),
    ("C partitions p(n): DP vs pentagonal", "n (value)", "n**2", "n**1.5"),
    ("C convex hull: brute vs Graham", "points", "n**3", "n*log(n)"),
    ("C smallest enclosing circle: brute vs Welzl", "points", "n**4", "n"),
    ("C MIS: brute vs simple branching", "vertices", "2**n * n", "1.3803**n * n"),
    ("C verify AB=C: recompute vs Freivalds", "matrix dim", "n**3", "n**2"),
    ("C bridges: naive vs Tarjan low-link", "vertices (m=Theta(n))", "n**2", "n"),
    ("C k-th term, order-k recurrence: companion vs Fiduccia", "order k", "n**3", "n**2"),
    ("C minimal recurrence: Gaussian vs Berlekamp-Massey", "length", "n**3", "n**2"),
    ("C sparse system: dense Gauss vs Wiedemann", "dim (O(n) nonzeros)", "n**3", "n**2"),
    ("C Toeplitz system: Gauss vs Levinson", "dim", "n**3", "n**2"),
    ("C char. polynomial: Faddeev-LeVerrier vs Hessenberg", "dim", "n**4", "n**3"),
    ("C char. polynomial: cofactor vs Hessenberg", "dim", "factorial(n)", "n**3"),
    ("C spanning-tree count: enumeration vs Kirchhoff", "vertices",
     "n * C(n(n-1)/2, n-1) [log via lgamma]", "n**3"),
    ("C HMM/Viterbi (2 states): enumeration vs DP", "length", "2**n * n", "n"),
    ("C CFG recognition: derivation search vs CYK", "length", "4**n / n**1.5", "n**3"),
    ("C divisor summatory D(x): naive vs hyperbola", "bits of x", "2**n", "2**(n/2)"),
    ("C divisor summatory D(x): hyperbola vs x^(1/3)", "bits of x", "2**(n/2)", "2**(n/3)"),
    ("C pi(x): sieve vs Meissel-Lehmer-type x^(2/3)", "bits of x", "2**n * log(n)", "2**(2*n/3)"),
    ("C factoring: trial division vs Lehman", "bits of N", "2**(n/2)", "2**(n/3)"),
    ("C triangles, sparse: all triples vs Chiba-Nishizeki", "vertices (m=Theta(n))", "n**3", "n**1.5"),
    ("C 2-machine flow shop: brute vs Johnson", "jobs", "factorial(n) * n", "n*log(n)"),
    ("C general matching: enumeration vs blossom", "vertices", "factorial(n)", "n**3"),
    ("C min mean cycle: cycle enumeration vs Karp", "vertices (dense)", "factorial(n)", "n**3"),
    ("C 2D LP: vertex enumeration vs Seidel", "constraints", "n**3", "n"),
    ("C mean estimation (queries): classical vs quantum", "log2(1/eps)", "4**n", "2**n"),
    ("C order finding (queries): classical LB vs quantum", "bits", "2**(n/3)", "n"),
    ("C union-find: quick-find vs rank+compression", "operations", "n**2", "n"),
    ("C dynamic prefix sums: naive vs Fenwick", "operations", "n**2", "n*log(n)"),
    ("C selection k=n/2: repeated min vs quickselect", "length", "n**2", "n"),
    ("C edit distance <= k: DP vs Ukkonen (k fixed)", "length", "n**2", "n"),
    ("C suffix array: naive sort vs prefix doubling", "length", "n**2 * log(n)", "n * log(n)**2"),
    ("C three collinear points: triples vs angular sort", "points", "n**3", "n**2 * log(n)"),
    ("C tridiagonal system: Gauss vs Thomas", "dim", "n**3", "n"),
    ("C single machine sum w_j C_j: brute vs Smith", "jobs", "factorial(n) * n", "n*log(n)"),
    ("C late jobs: brute vs Moore-Hodgson", "jobs", "2**n * n", "n*log(n)"),
    ("C Euler circuit: edge orders vs Hierholzer", "edges", "factorial(n)", "n"),
    ("N Toom-3 vs Karatsuba (near-miss)", "digits", "n**log2(3)", "n**(log(5)/log(3))"),
    ("N Held-Karp vs Bjorklund 1.657^n (near-miss)", "vertices", "n**2 * 2**n", "1.657**n * n**3"),
    ("N Max-2-CSP: brute vs Williams with Strassen (near-miss)", "variables", "2**n", "2**(log2(7)*n/3)"),
    ("N matrix chain: DP vs Hu-Shing", "matrices", "n**3", "n*log(n)"),
]


def n_range(f: str) -> list[int]:
    """Integers n >= 2 with T_LO <= U f(n) <= T_HI, thinned to at most 8 roughly geometric points."""
    def t(n):
        try:
            return U * eval_cost(f, n)
        except (OverflowError, ValueError, ZeroDivisionError):
            return math.inf
    ns, n = [], 2
    while n < 10 ** 8:
        v = t(n)
        if v > T_HI:
            break
        if v >= T_LO:
            ns.append(n)
        n = n + 1 if n < 64 else int(n * 1.05) + 1
    if len(ns) > 8:
        idx = sorted({round(i * (len(ns) - 1) / 7) for i in range(8)})
        ns = [ns[i] for i in idx]
    return ns


def main() -> int:
    print(f"assumed U = {U:g} s per cost unit; timed window {T_LO:g}..{T_HI:g} s; tolerance {TOL}")
    print("* = n range set by hand (query-model rows: limited by simulation, not by time)")
    print(f"{'pair':<58} {'g (slow)':<26} {'f (fast)':<22} {'n range of f':<18} {'rho':>6}  verdict")
    for label, nmeaning, g, f in ROWS:
        ns = NS_OVERRIDE.get(label) or n_range(f)
        if len(ns) < 3:
            print(f"{label:<58} {g[:26]:<26} {f[:22]:<22} {'(no range)':<18} {'':>6}  n/a")
            continue
        try:
            xs = [math.log(eval_cost(f, n)) for n in ns]
            ys = [LOG_G[label](n) if label in LOG_G else math.log(eval_cost(g, n)) for n in ns]
        except (OverflowError, ValueError) as e:
            print(f"{label:<58} error {e}")
            continue
        rho = fit_slope(xs, ys)
        caught = abs(rho - 1) > TOL
        border = abs(abs(rho - 1) - TOL) < 0.02
        verdict = ("caught" if caught else "NOT caught") + (" (borderline)" if border else "")
        rng = f"{ns[0]}..{ns[-1]}" + ("*" if label in NS_OVERRIDE else "")
        print(f"{label:<58} {g[:26]:<26} {f[:22]:<22} {rng:<18} {rho:>6.3f}  {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
