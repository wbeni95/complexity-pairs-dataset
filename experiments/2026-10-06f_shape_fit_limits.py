#!/usr/bin/env python3
"""What the V2 slope fit cannot see, on the dataset's own grids, with PERFECT (noise-free) data (round 2026-10-06f).

For a pair (truth, claim) the validator's fit regresses log(truth(n)) on log(claim(n)) over n_values and accepts
|alpha - 1| <= tolerance. Here truth(n) is evaluated exactly (no noise), so any acceptance is a property of the
fit itself, not of measurement error. Each row prints alpha and whether the fit would accept the claim at the
stated tolerance. Below each row: what the exact shape diagnostic (methods/shape.py) reports for an exact integer
count with the true shape (call counts of the plain recursions, the NTT and Strassen closed forms).

Deterministic, standard library only, < 1 s.
Usage:  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06f_shape_fit_limits.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from functools import lru_cache  # noqa: E402

from methods import shape as S  # noqa: E402


@lru_cache(None)
def fib_calls(n):
    return 1 if n < 2 else 1 + fib_calls(n - 1) + fib_calls(n - 2)


def edit_calls(n):
    @lru_cache(None)
    def d(i, j):
        return 1 if i == n or j == n else 1 + d(i + 1, j) + d(i, j + 1) + d(i + 1, j + 1)
    return d(0, 0)


def nlogn_count(n):  # an exact n log2 n + lower-order count at n = 2^k
    k = n.bit_length() - 1
    return n * k + 3 * n + 1


def ntt_count(n):  # the NTT entry's exact count 3 n log2 n + 5 n at n = 2^k (RL-068)
    return 3 * n * (n.bit_length() - 1) + 5 * n


def strassen_count(n):  # 4096 * 7^(k-4) for n = 2^k >= 16 (RL-047)
    return 4096 * 7 ** (n.bit_length() - 5)


CONS24 = {"sequence": "consecutive", "n_range": [1, 24]}
FIB = {"sequence": "consecutive", "n_range": [1, 25]}
DBL = {"sequence": "doubling", "n_range": [2, 4096]}

# label, fit truth, fit claim, V2 n_values, tolerance, (integer count with the truth's shape, shape block)
ROWS = [
    ("edit distance: true (3+2 sqrt 2)^n/sqrt n, claim without 1/sqrt n, entry's V2 grid",
     "(3 + 2*sqrt(2))**n / sqrt(n)", "(3 + 2*sqrt(2))**n", [5, 6, 7, 8, 9], 0.25, (edit_calls, CONS24)),
    ("edit distance: same pair on n = 1..24", "(3 + 2*sqrt(2))**n / sqrt(n)", "(3 + 2*sqrt(2))**n",
     list(range(1, 25)), 0.03, (edit_calls, CONS24)),
    ("edit distance: base 5.8 instead of 3+2 sqrt 2 = 5.8284 (cost as written)", "(3 + 2*sqrt(2))**n / sqrt(n)",
     "5.8**n / sqrt(n)", list(range(1, 25)), 0.03, (edit_calls, CONS24)),
    ("edit distance: base 5.8 given exactly via expect (base 29/5, n^(-1/2))", "(3 + 2*sqrt(2))**n / sqrt(n)",
     "5.8**n / sqrt(n)", list(range(1, 25)), 0.03,
     (edit_calls, {**CONS24, "expect": {"base": "29/5", "polynomial_factor": "-1/2"}})),
    ("Fibonacci: true phi^n, claim 1.7^n (undeclared rival), entry's V2 grid", "phi**n", "1.7**n",
     [18, 20, 22, 24, 26, 28], 0.25, (fib_calls, {**FIB, "expect": {"base": "17/10"}})),
    ("Fibonacci: true phi^n, claim 2^n", "phi**n", "2**n", [18, 20, 22, 24, 26, 28], 0.25, (fib_calls, FIB)),
    ("n log n vs claim n^1.1, 8 points on [1e3, 1e5] (RL-082 part 3)", "n*log(n)", "n**1.1",
     [1000, 1931, 3728, 7197, 13895, 26827, 51795, 100000], 0.25, (nlogn_count, DBL)),
    ("NTT: true n(3 log2 n + 5), claim n, entry's V2 grid, tolerance 0.25", "n*(3*log2(n) + 5)", "n",
     [512, 1024, 2048, 4096, 8192, 16384], 0.25, (ntt_count, DBL)),
    ("NTT: same at the entry's tolerance 0.03", "n*(3*log2(n) + 5)", "n",
     [512, 1024, 2048, 4096, 8192, 16384], 0.03, (ntt_count, DBL)),
    ("Strassen: true n^log2(7), claim n^2.8, entry's V2 grid and tolerance", "n**log2(7)", "n**2.8",
     [32, 64, 128, 256], 0.02, (strassen_count, {"sequence": "doubling", "n_range": [16, 512], "holdout": 2})),
]


def main() -> int:
    print(f"{'alpha':>8s} {'tol':>5s}  fit accepts  pair")
    for label, truth, claim, ns, tol, (count, block) in ROWS:
        xs = [math.log(eval_cost(claim, n)) for n in ns]
        ys = [math.log(eval_cost(truth, n)) for n in ns]
        a = fit_slope(xs, ys)
        grid = S.grid_from_block(block)
        r = S.run(claim, block, grid, [count(n) for n in grid.ns])
        diag = r["category"] + (f" ({', '.join(r['differs'])})" if r.get("differs") else f" ({r['reason']})")
        print(f"{a:8.4f} {tol:5.2f}  {'yes' if abs(a - 1) <= tol else 'no ':11s}  {label}")
        print(f"{'':28s}shape diagnostic on an exact count of the true shape: {diag}")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
