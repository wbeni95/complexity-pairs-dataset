#!/usr/bin/env python3
"""Systematic alpha patterns of the timing fits, by kind of claimed cost (deviation analysis, 2026-10-07b).

Groups every TIMING fit of the latest ledger run (20261006T070542Z at the time of writing) by its claimed cost:
  exp      exponential / factorial costs (contains '**n', '**(n', 'factorial'; the slow algorithms)
  poly3+   polynomial with effective exponent >= 2.5 (n^3, n^4, n^2.5 ...)
  poly2    effective exponent in [1.5, 2.5)
  lin      effective exponent below 1.5 (n, n log n); Karatsuba's n^log2(3) = n^1.585 falls in poly2
  log      log n
For each group: count, mean alpha, number with alpha < 1, mean (alpha_second_half - alpha_first_half) where the
halves are as in experiments/2026-10-07b_ledger_stability.py, and the number with a positive half-difference.
The same statistics over ALL five ledger runs (each run counted separately) show whether the pattern is stable.
Deterministic; ledger only.

Result (2026-10-06): exponent >= 2.5: 10/10 alpha < 1 with rising slope (40/40 pooled over 5 runs); log n:
5/5 alpha > 1 with falling slope (17/17 pooled); quadratic mean alpha 1.014; exponential mean 0.992; 60 of 74
latest-run timing fits have |second-half - first-half alpha| <= 0.05. Quoted in the report section 6.
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


def group(m):
    c = m["cost"]
    if c == "log(n)":
        return "log"
    if any(s in c for s in ("**n", "**(n", "factorial")):
        return "exp"
    ns = m["n_values"]
    p = fit_slope([math.log(n) for n in ns], [math.log(eval_cost(c, n)) for n in ns])
    return "poly3+" if p >= 2.5 else ("poly2" if p >= 1.5 else "lin")


def halves(m):
    ns, vs = m["n_values"], m["values"]
    xs = [math.log(eval_cost(m["cost"], n)) for n in ns]
    ys = [math.log(v) for v in vs]
    k = len(ns)
    h = (k + 1) // 2
    return fit_slope(xs[k - h:], ys[k - h:]) - fit_slope(xs[:h], ys[:h])


def stats(rows):
    out = {}
    for g, lst in rows.items():
        al = [a for a, _, _ in lst]
        dh = [d for _, d, _ in lst]
        out[g] = (len(al), sum(al) / len(al), sum(a < 1 for a in al), sum(dh) / len(dh), sum(d > 0 for d in dh),
                  min(al), max(al))
    return out


def main():
    all_rows = defaultdict(list)
    latest_rows = defaultdict(list)
    for i, p in enumerate(RUNS):
        d = json.loads(p.read_text(encoding="utf-8"))
        for e in d["entries"]:
            for m in e.get("v2") or []:
                if m["measure"] != "time":
                    continue
                g = group(m)
                row = (m["alpha"], halves(m), f"{e['id']} / {m['algorithm']}")
                all_rows[g].append(row)
                if i == len(RUNS) - 1:
                    latest_rows[g].append(row)
    for title, rows in (("latest run " + RUNS[-1].stem, latest_rows), ("all runs pooled", all_rows)):
        print(f"== {title}")
        print(f"   {'group':7s} {'fits':>4s} {'mean a':>7s} {'a<1':>4s} {'mean d(a2-a1)':>13s} {'d>0':>4s}  range")
        for g, (n, ma, lt1, md, dpos, lo, hi) in sorted(stats(rows).items()):
            print(f"   {g:7s} {n:4d} {ma:7.3f} {lt1:4d} {md:+13.3f} {dpos:4d}  [{lo:.3f}, {hi:.3f}]")
    lat = [d for lst in latest_rows.values() for _, d, _ in lst]
    print(f"\nlatest run: timing fits with |second-half - first-half alpha| <= 0.05: "
          f"{sum(abs(d) <= 0.05 for d in lat)} of {len(lat)}")
    print("\n== latest run, members of each group (alpha, second-half minus first-half alpha)")
    for g, lst in sorted(latest_rows.items()):
        print(f"   [{g}]")
        for a, d, name in sorted(lst):
            print(f"      {a:.3f}  {d:+.3f}  {name}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
