#!/usr/bin/env python3
"""How discriminating is each recorded V2 fit? Post-hoc rivals from ledger data (deviation analysis, 2026-10-07b).

Two questions, answered only from recorded values (no timing, no randomness):

A. Cross-fits inside each entry. For every V2 entry in the LATEST ledger run and every ordered pair (A, B) of its
   measured algorithms with different claimed costs, fit A's recorded values (over A's own n values) against
   B's claimed cost with tools/validate.fit_slope. If |alpha_AB - 1| <= A's tolerance, A's measurements would
   also "pass" B's cost, i.e. the data do not exclude that A behaves like B. The interesting case is A = the
   faster algorithm and B = the slower one: then the fast algorithm's V2 evidence does not, on its own, exclude
   the slow cost (the separation rests on the claim text, not on the measurement). This is exactly the
   RL-047 rival rule applied after the fact with the entry's other algorithm(s) as rivals.
   The same is repeated for every ledger run that has both series, to show the verdict is not one run's noise.

B. Passing band. For each timing fit, the range of alternative costs that the same data would accept:
   - effective exponent p_eff = least-squares slope of ln cost(n) against ln n over the n values; an
     alternative n^q passes iff alpha * p_eff / q lies in [1 - tol, 1 + tol], i.e.
     q in [alpha p_eff / (1 + tol), alpha p_eff / (1 - tol)];
   - for exponential-type costs, the effective base b_eff = exp(slope of ln cost against n); an alternative
     c^n passes iff ln c in [alpha ln b_eff / (1 + tol), alpha ln b_eff / (1 - tol)].
   Both are first-order (they treat the alternative as a pure power or pure exponential over the range).

Deterministic. Output is copied into research/2026-10-07b_deviations.md sections 4 and 5.

Result (2026-10-06 local time, latest ledger 20261006T070542Z): 103 cross-fits, 97 rejected, 6 ALSO PASS:
Kuhn data vs n^2.5 (1.170), Hopcroft-Karp data vs n^3 (0.819), BBHT collision data vs 2^(n/2) (0.776),
Karatsuba data vs n^2 (0.806), Kruskal vs n^2 (1.100), Prim vs n^2 log n (0.915); each verdict is the same in
every earlier run that has both series. Narrowest rejection: schoolbook multiplication data vs n^log2(3), 1.273
(margin 0.023). Passing bands: n^3 timing fits accept q in about [2.2, 3.9]; n log n fits about [0.87, 1.49].
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402

RUNS = sorted((REPO / "ledger" / "runs").glob("*.json"))


def safe_log_cost(expr, n):
    try:
        v = eval_cost(expr, n)
        return math.log(v) if v > 0 else None
    except (OverflowError, ValueError, ZeroDivisionError):
        return None


def cross(m_a, cost_b):
    xs = [safe_log_cost(cost_b, n) for n in m_a["n_values"]]
    if any(x is None for x in xs) or max(xs) - min(xs) < 1e-12:
        return None
    return fit_slope(xs, [math.log(v) for v in m_a["values"]])


def main():
    runs = [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in RUNS]
    latest_stem, latest = runs[-1]
    print(f"latest run: {latest_stem}")
    print("\n=== A. cross-fits: algorithm A's recorded values against algorithm B's claimed cost ===")
    print(f"{'entry':52s} {'A (data)':34s} {'B (cost)':24s} {'alpha_AB':>8s}  verdict      (all runs)")
    for e in latest["entries"]:
        ms = [m for m in (e.get("v2") or []) if m["alpha"] is not None]
        for a in ms:
            for b in ms:
                if a is b or a["cost"] == b["cost"]:
                    continue
                al = cross(a, b["cost"])
                if al is None:
                    continue
                passes = abs(al - 1) <= a["tolerance"]
                hist = []
                for stem, d in runs:
                    for e2 in d["entries"]:
                        if e2["id"] != e["id"]:
                            continue
                        for a2 in e2.get("v2") or []:
                            if a2["algorithm"] == a["algorithm"] and a2["alpha"] is not None:
                                x = cross(a2, b["cost"])
                                if x is not None:
                                    hist.append(f"{x:.3f}")
                tag = "ALSO PASSES" if passes else "rejected"
                print(f"{e['id'][:52]:52s} {a['algorithm'][:34]:34s} {b['cost'][:24]:24s} {al:8.3f}  {tag:12s} [{' '.join(hist)}]")

    print("\n=== B. passing band of each timing fit (latest run) ===")
    print(f"{'entry':52s} {'algorithm':34s} {'cost':22s} alpha  span   p_eff  q-band (power)         b_eff   base-band (exp)")
    for e in latest["entries"]:
        for m in e.get("v2") or []:
            if m["alpha"] is None:
                continue
            ns = m["n_values"]
            lc = [safe_log_cost(m["cost"], n) for n in ns]
            tol = m["tolerance"]
            p_eff = fit_slope([math.log(n) for n in ns], lc)
            lb = fit_slope([float(n) for n in ns], lc)
            span = math.exp(max(lc) - min(lc))
            a = m["alpha"]
            qlo, qhi = a * p_eff / (1 + tol), a * p_eff / (1 - tol)
            blo, bhi = math.exp(a * lb / (1 + tol)), math.exp(a * lb / (1 - tol))
            print(f"{e['id'][:52]:52s} {m['algorithm'][:34]:34s} {m['cost'][:22]:22s} {a:.3f} {span:8.3g} {p_eff:6.3f}  "
                  f"[{qlo:6.3f}, {qhi:6.3f}]   {math.exp(lb):7.4f} [{blo:.4f}, {bhi:.4f}]  {m['measure']}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
