#!/usr/bin/env python3
"""Run-to-run stability and local-slope curvature of every recorded V2 fit (deviation analysis, 2026-10-07b).

Question 1 (stability): for every (entry, algorithm) that has a V2 measurement in ledger/runs/*.json, how much
does the recorded alpha move between runs, and how close does it come to the tolerance edge?
  - spread = max(alpha) - min(alpha) over all runs that recorded the fit WITH THE SAME configuration
    (same measure, cost, n_values, samples, tolerance); a configuration change is reported separately,
    because then the alpha change is not noise.
  - margin = tol - |alpha - 1| (smallest over all runs); a small margin means "close to failing".
Question 2 (curvature): from the recorded values of the LATEST run, the local slope between consecutive
n values, s_i = (ln y_{i+1} - ln y_i) / (ln c(n_{i+1}) - ln c(n_i)), where c is the claimed cost evaluated
with tools/validate.eval_cost. Reported: first, last, min, max local slope, the drift (last - first), and
the alpha of a fit over the first half vs. the second half of the n values (halves overlap in the middle
point when the count is odd). The same is computed for every run; the drift's sign consistency across runs
tells real curvature from noise.

Only ledger data is used (no timing, no randomness); the cost function and slope fit are imported from
tools/validate.py so that the numbers use exactly the validator's arithmetic. Deterministic.

Output: a stability table, a curvature table, and a short JSON dump (scratch use) on stdout.

Result (run 2026-10-06 local time, on the five ledger files 20261006T005329Z, 005747Z, 025704Z, 030338Z,
070542Z): 90 series, 0 configuration changes between runs. Largest timing spreads 0.044 (inversion counting,
merge-sort counting), 0.040 (Fibonacci fast doubling), 0.031 (inversion counting, all pairs); all others <= 0.017.
Smallest margins: BBHT collision 0.086, fast doubling 0.122, Simon quantum 0.129, Durr-Hoyer 0.136. Largest
curvature: Simon quantum (first-half alpha 1.478, second-half 0.888), max-subarray brute, fast doubling and the
companion-matrix log n fits (falling slopes), Floyd-Warshall (slopes rising 0.894 -> 0.965). Tables are copied into
research/2026-10-07b_deviations.md sections 1 and 2.
"""
from __future__ import annotations

import json
import math
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402

RUNS = sorted((REPO / "ledger" / "runs").glob("*.json"))


def load_runs():
    out = []
    for p in RUNS:
        d = json.loads(p.read_text(encoding="utf-8"))
        out.append((p.stem, d))
    return out


def config_key(m):
    return (m["measure"], m["cost"], tuple(m["n_values"]), m["samples"], m["tolerance"])


def local_slopes(m):
    ns, vs = m["n_values"], m["values"]
    xs = [math.log(eval_cost(m["cost"], n)) for n in ns]
    ys = [math.log(v) for v in vs]
    s = []
    for i in range(len(ns) - 1):
        dx = xs[i + 1] - xs[i]
        s.append((ys[i + 1] - ys[i]) / dx if abs(dx) > 1e-12 else float("nan"))
    k = len(ns)
    h = (k + 1) // 2
    a1 = fit_slope(xs[:h], ys[:h]) if h >= 2 and max(xs[:h]) - min(xs[:h]) > 1e-12 else float("nan")
    a2 = fit_slope(xs[k - h:], ys[k - h:]) if h >= 2 and max(xs[k - h:]) - min(xs[k - h:]) > 1e-12 else float("nan")
    span = math.exp(max(xs) - min(xs))
    return s, a1, a2, span


def main():
    runs = load_runs()
    series = defaultdict(list)  # (entry, alg) -> [(run, m)]
    for stem, d in runs:
        for e in d["entries"]:
            for m in e.get("v2", []) or []:
                series[(e["id"], m["algorithm"])].append((stem, m))

    print(f"ledger files: {[s for s, _ in runs]}")
    print(f"(entry, algorithm) pairs with a V2 record: {len(series)}")
    print()
    print("=== STABILITY (alpha per run; spread within identical configuration) ===")
    rows = []
    for (eid, alg), lst in series.items():
        if lst[0][1]["alpha"] is None:
            ratios = [m["max_over_min"] for _, m in lst]
            rows.append((eid, alg, lst[0][1]["measure"], "const", ratios, 0.0, None, len({config_key(m) for _, m in lst}), lst[-1][1]["tolerance"]))
            continue
        by_cfg = defaultdict(list)
        for stem, m in lst:
            by_cfg[config_key(m)].append((stem, m["alpha"]))
        spreads = [max(a for _, a in v) - min(a for _, a in v) for v in by_cfg.values()]
        alphas = [m["alpha"] for _, m in lst]
        tol = lst[-1][1]["tolerance"]
        margin = min(m["tolerance"] - abs(m["alpha"] - 1) for _, m in lst)
        rows.append((eid, alg, lst[0][1]["measure"], "fit", alphas, max(spreads), margin, len(by_cfg), tol))
    rows.sort(key=lambda r: -r[5])
    print(f"{'entry':58s} {'algorithm':38s} meas  nrun ncfg  tol   spread  margin  alphas")
    for eid, alg, meas, kind, vals, spread, margin, ncfg, tol in rows:
        vs = " ".join(f"{v:.3f}" for v in vals)
        mg = "  -   " if margin is None else f"{margin:.3f}"
        print(f"{eid[:58]:58s} {alg[:38]:38s} {meas[:4]:4s}  {len(vals):3d}  {ncfg:3d}  {tol:.2f}  {spread:.3f}   {mg}   {vs}")

    print()
    print("=== CONFIGURATION CHANGES between runs (alpha change not attributable to noise) ===")
    nchg = 0
    for (eid, alg), lst in series.items():
        keys = []
        for stem, m in lst:
            k = config_key(m)
            if not keys or keys[-1][1] != k:
                keys.append((stem, k))
        if len(keys) > 1:
            nchg += 1
            for stem, k in keys:
                print(f"  {eid} / {alg}: from {stem}: measure={k[0]} cost={k[1]} n={list(k[2])} samples={k[3]} tol={k[4]}")
    print(f"  total (entry, algorithm) with a configuration change: {nchg}")

    print()
    print("=== CURVATURE (latest run per series): local slopes against the claimed cost ===")
    crow = []
    for (eid, alg), lst in series.items():
        stem, m = lst[-1]
        if m["alpha"] is None:
            continue
        s, a1, a2, span = local_slopes(m)
        fin = [x for x in s if not math.isnan(x)]
        # drift sign across all runs with the same config as latest
        signs = []
        for st2, m2 in lst:
            if config_key(m2) == config_key(m):
                s2, _, _, _ = local_slopes(m2)
                f2 = [x for x in s2 if not math.isnan(x)]
                signs.append(f2[-1] - f2[0])
        crow.append((eid, alg, m["measure"], stem, m["alpha"], fin[0], fin[-1], min(fin), max(fin), fin[-1] - fin[0], a1, a2, span, signs, s))
    crow.sort(key=lambda r: -abs(r[11] - r[10]) if not math.isnan(r[11] - r[10]) else 0)
    print(f"{'entry':50s} {'algorithm':34s} meas alpha  first  last   min    max    a_1st  a_2nd  d(a2-a1) span     drift(last-first) per run")
    for r in crow:
        eid, alg, meas, stem, a, f0, fl, mn, mx, dr, a1, a2, span, signs, s = r
        sg = " ".join(f"{x:+.2f}" for x in signs)
        print(f"{eid[:50]:50s} {alg[:34]:34s} {meas[:4]:4s} {a:.3f}  {f0:.3f}  {fl:.3f}  {mn:.3f}  {mx:.3f}  {a1:.3f}  {a2:.3f}  {a2 - a1:+.3f}   {span:9.3g}  {sg}")
    print()
    print("=== LOCAL SLOPE SEQUENCES (latest run) ===")
    for r in sorted(crow, key=lambda r: (r[0], r[1])):
        eid, alg, meas, stem, a, *_rest = r
        s = r[-1]
        m = series[(eid, alg)][-1][1]
        print(f"{eid} / {alg} [{stem}] n={m['n_values']}")
        print("    local slopes: " + " ".join("nan" if math.isnan(x) else f"{x:.3f}" for x in s))


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
