#!/usr/bin/env python3
"""(b) Identifiability of log factors: when can a fit tell n^a from n^a log n, and what resolves it exactly?

Questions:
  1. RL-048 found that 0 of 77 timing fits resolved a log factor. Is that caused by timing NOISE, or would even
     PERFECT data on the same n-grids fail at tolerance 0.25? (Re-analysis of the recorded run
     ledger/runs/20261006T105123Z.json, read-only: every V2 measurement's cost expression, n_values and tolerance.)
  2. For geometric grids, how does the noise-free separation |alpha_up - 1| depend on the n-range and exponent a, and
     what are the noise standard errors for alpha (fixed shape) and for b (free model c + a log n + b log log n)?
  3. Monte Carlo (fixed seeds): how often does least-squares model selection among fixed shapes pick n log n when
     the truth is n log n, under multiplicative log-normal noise sigma?
  4. Exact remedy: exact counts at n = 2^k form a C-finite sequence in k for divide-and-conquer costs; Berlekamp-
     Massey over Q gives the characteristic polynomial, whose dominant root lambda = 2^a gives the exponent and
     whose multiplicity m gives the log power (log n)^(m-1) EXACTLY (checked on held-out terms). Run on the harness
     counts of Karatsuba, Strassen and the NTT.

Deterministic: fixed seeds for the Monte Carlo; counts are exact. Runtime about 5 s, one process,
below-normal priority.

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06d_meth_log_identifiability.py
"""
from __future__ import annotations

import json
import math
import random
import sys
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))

from methods import exactalg as ea  # noqa: E402
from methods import fitting as ft  # noqa: E402
from methods import recurrences as rc  # noqa: E402
from validate import eval_cost, load_callable, load_entry, load_module, resolve_in_repo  # noqa: E402

try:
    from search.machine import set_below_normal_priority
    set_below_normal_priority()
except Exception:  # pragma: no cover
    pass

LEDGER = REPO / "ledger" / "runs" / "20261006T105123Z.json"


def part1() -> None:
    print("=== Part 1: re-analysis of the recorded V2 fits (noise-free diagnostic on the same grids and tolerances)")
    run = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = []
    for e in run["entries"]:
        for m in e.get("v2", []):
            d = m.get("diagnostics") or {}
            if not d or min(m["n_values"]) < 2:
                continue
            cost = lambda n, c=m["cost"]: eval_cost(c, n)  # noqa: E731
            try:
                nf = ft.noise_free_diagnostic(cost, m["n_values"], m["tolerance"])
                mt = ft.min_resolving_tol(cost, m["n_values"])
            except (ValueError, ZeroDivisionError, OverflowError):
                continue
            rows.append({"id": e["id"], "alg": m["algorithm"], "measure": m["measure"], "tol": m["tolerance"],
                         "ledger_resolves": d["resolves_log_factor"], "perfect_resolves": nf["resolves"],
                         "min_tol": mt, "span": max(m["n_values"]) / min(m["n_values"])})
    for meas in ("time", "reported"):
        sub = [r for r in rows if r["measure"] == meas]
        lr = sum(r["ledger_resolves"] for r in sub)
        pr = sum(r["perfect_resolves"] for r in sub)
        both = sum(r["ledger_resolves"] and r["perfect_resolves"] for r in sub)
        print(f"  measure={meas}: {len(sub)} fits with a diagnostic; resolved in the ledger: {lr}; "
              f"resolvable with PERFECT data at the same grid and tolerance: {pr}; both: {both}")
        if sub:
            mts = sorted(r["min_tol"] for r in sub)
            q = lambda p: mts[min(len(mts) - 1, int(p * len(mts)))]  # noqa: E731
            print(f"    largest tolerance that would still resolve the log factor with perfect data: min {mts[0]:.4f}, "
                  f"median {q(0.5):.4f}, max {mts[-1]:.4f}")
    t = [r for r in rows if r["measure"] == "time"]
    worst = sorted(t, key=lambda r: -r["min_tol"])[:5]
    print("  timing fits whose grids separate the log factor best (noise-free |alpha_up/down - 1|):")
    for r in worst:
        print(f"    {r['id'][:44]:44s} {r['alg'][:34]:34s} min-tol {r['min_tol']:.4f}  n-span x{r['span']:.0f}")
    gap = [r for r in rows if r["measure"] == "reported" and r["perfect_resolves"] != r["ledger_resolves"]]
    print(f"  count fits where the ledger verdict differs from the perfect-data verdict: {len(gap)}")
    for r in gap:
        print(f"    {r['id'][:44]:44s} {r['alg'][:34]:34s} tol {r['tol']} ledger={r['ledger_resolves']} "
              f"perfect={r['perfect_resolves']} (min-tol {r['min_tol']:.4f})")


def part2() -> None:
    print("\n=== Part 2: geometric grids, k = 8 points; cost n^a vs n^a log n")
    print("  range            a   noise-free sep.  SE(alpha) s=0.05  SE(b) free model s=0.05  corr(log n, loglog n)")
    for n1, n2 in [(10, 10 ** 3), (10 ** 2, 10 ** 4), (10 ** 3, 10 ** 5), (10 ** 3, 10 ** 6), (10 ** 4, 10 ** 7),
                   (2 ** 5, 2 ** 20)]:
        ns = ft.geometric_grid(n1, n2, 8)
        for a in (1, 2, 3):
            cost = lambda n, a=a: n ** a  # noqa: E731
            sep = ft.min_resolving_tol(cost, ns)
            se = ft.alpha_se(cost, ns, 0.05)
            seb, rho = ft.loglog_se(ns, 0.05)
            print(f"  [{n1:>6}, {n2:>8}]  {a}   {sep:.4f}           {se:.4f}            {seb:.3f}                    "
                  f"{rho:.5f}")


def part3() -> None:
    print("\n=== Part 3: Monte Carlo model selection (truth n log n), k = 8 points on [10^3, 10^5], 400 seeds per sigma")
    ns = ft.geometric_grid(10 ** 3, 10 ** 5, 8)
    cands = {"n": lambda n: n, "n log n": lambda n: n * math.log(n), "n log^2 n": lambda n: n * math.log(n) ** 2,
             "n^1.1": lambda n: n ** 1.1, "n^1.2": lambda n: n ** 1.2, "n^1.25": lambda n: n ** 1.25}
    for truth in ("n log n", "n^1.1"):
        f = cands[truth]
        for sigma in (0.0, 0.01, 0.03, 0.1, 0.3):
            picks: dict[str, int] = {}
            for seed in range(400):
                rng = random.Random(f"meth-b|{truth}|{sigma}|{seed}")
                ys = [math.log(f(n)) + rng.gauss(0.0, sigma) for n in ns]
                p = ft.select_model(ns, ys, cands)
                picks[p] = picks.get(p, 0) + 1
            share = picks.get(truth, 0) / 400
            other = ", ".join(f"{k}: {v}" for k, v in sorted(picks.items(), key=lambda kv: -kv[1]) if k != truth)
            print(f"  truth {truth:8s} sigma {sigma:<5}: correct {share:6.1%}   others: {other or '-'}")
    # the V2 test itself, on the same data: does n log n data pass a claim of n^1.1 (tol 0.25)?
    f = cands["n log n"]
    d = ft.noise_free_diagnostic(f, ns, 0.25)
    a11 = ft.slope([math.log(n ** 1.1) for n in ns], [math.log(f(n)) for n in ns])
    print(f"  noise-free n log n data fitted against claim n^1.1: alpha = {a11:.4f} (passes tol 0.25: "
          f"{abs(a11 - 1) <= 0.25}); diagnostic for claim n log n: alpha_up {d['alpha_up']:.4f}, "
          f"alpha_down {d['alpha_down']:.4f}")


def harness_counts(entry_rel: str, alg_prefix: str, ns: list[int]) -> list[int]:
    d = REPO / entry_rel
    e = load_entry(d)
    alg = next(a for a in e["algorithms"] if a["name"].startswith(alg_prefix))
    fn = load_callable(d, alg["implementation"])
    harness = load_module(resolve_in_repo(d, e["test_harness"]["module"]))
    out = []
    for n in ns:
        rng = random.Random(f"{e['id']}|meth-b|{n}")
        out.append(int(harness.reported_cost(fn(harness.generate_scaling(n, rng)))))
    return out


def doubling_analysis(label: str, ks: list[int], seq: list[int], claim: str, holdout: int, var: str = "n") -> None:
    print(f"\n  {label}: counts at {var} = 2^k, k = {ks[0]}..{ks[-1]}: {seq}")
    g = rc.guess_c_finite(seq, holdout=holdout)
    if not g:
        print("    no C-finite recurrence accepted (too few terms for the margin)")
        return
    gr = rc.growth_from_charpoly(g["charpoly"])
    lam = Fraction(gr["lambda_interval"][0] + gr["lambda_interval"][1]) / 2
    exact_lam = ea.rational_roots(gr["minpoly"])
    lam_s = str(exact_lam[0]) if exact_lam else f"{float(lam):.12g}"
    a = math.log2(float(lam))
    m = gr["multiplicity"]
    a_s = (str(int(round(a))) if exact_lam and exact_lam[0].denominator == 1 and
           (exact_lam[0].numerator & (exact_lam[0].numerator - 1)) == 0 else f"(log2 {lam_s} = {a:.6f})")
    print(f"    Berlekamp-Massey: order {g['order']}, charpoly {ea.pstr(g['charpoly'])} = "
          + " * ".join(f"({ea.pstr(f)})" for f in ea.factor_kronecker(g["charpoly"]))
          + f"; found from {g['terms_used']} terms, reproduces all {g['terms_checked']}")
    print(f"    -> dominant root {lam_s} with multiplicity {m}: cost = Theta({var}^{a_s} (log {var})^{m - 1}) on {var} = 2^k; "
          f"claim: {claim}")


def part4() -> None:
    print("\n=== Part 4: exact identification from exact counts at n = 2^k (recurrence in k)")
    ks = list(range(1, 15))
    seq = harness_counts("pairs/polynomial-multiplication-naive-vs-ntt", "number-theoretic", [2 ** k for k in ks])
    doubling_analysis("NTT (polynomial multiplication)", ks, seq, "n*(3*log2(n) + 5) (entry: Theta(n log n))", 3)
    ks = list(range(5, 13))
    seq = harness_counts("pairs/integer-multiplication-schoolbook-vs-karatsuba", "Karatsuba", [2 ** k for k in ks])
    doubling_analysis("Karatsuba (integer multiplication)", ks, seq, "Theta(n^log2(3))", 2)
    ks = list(range(4, 8))
    seq = harness_counts("pairs/matrix-multiplication-naive-vs-strassen", "Strassen", [2 ** k for k in ks])
    run = json.loads(LEDGER.read_text(encoding="utf-8"))
    led = next(m for e in run["entries"] if e["id"] == "matrix-multiplication-naive-vs-strassen"
               for m in e["v2"] if m["algorithm"] == "Strassen")
    seq.append(int(led["values"][led["n_values"].index(256)]))
    doubling_analysis("Strassen (matrix multiplication; k = 8 value from the ledger)", list(range(4, 9)), seq,
                      "Theta(n^log2(7))", 1)
    ks = list(range(1, 15))
    seq = harness_counts("pairs/subset-sum-zeta-transform-naive-vs-yates", "Yates", ks)
    doubling_analysis("Yates' zeta transform (table size N = 2^n; the sequence index is n = log2 N)", ks, seq,
                      "Theta(n 2^n) = Theta(N log N)", 3, var="N")


def main() -> int:
    part1()
    part2()
    part3()
    part4()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
