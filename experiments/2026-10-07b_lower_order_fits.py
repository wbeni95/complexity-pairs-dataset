#!/usr/bin/env python3
"""Can one lower-order term explain the alpha < 1 of the polynomial n^2.5+ timing fits? (deviation analysis, 2026-10-07b)

For every timing fit in the latest ledger run whose claimed cost is a pure power n^p with p >= 2.5, fit the
two-term model T(n) = a n^p + b n^(p-1) to the recorded times by least squares on T/n^(p-1) = a n + b
(ordinary least squares, every point weighted by 1/(T/n^(p-1))^2, i.e. relative errors). Report b/a (the n at
which the lower-order term equals the leading one), the relative RMS residual of the two-term model vs the
one-term model T = c n^p (c fitted the same way), the alpha that the fitted two-term model reproduces over the
same n values (should match the recorded alpha), and the n range over which the model predicts the local slope
to exceed 0.99 (local slope of a n^p + b n^(p-1) against n^p is (p a n + (p-1) b) / (p (a n + b))).
This is a consistency check of the "lower-order term" explanation, not proof of it.
Deterministic; ledger only.

Result (2026-10-06, ledger 20261006T070542Z): b/a = 6.85-21.76; residual ratio one-term/two-term 4.68-21.80
for 8 of 9 fits, 1.39 for max-subarray brute force (instance mix); model alpha matches recorded alpha within
+-0.001 except max-subarray brute (0.966 vs 0.974). Floyd-Warshall: b/a 21.76, local slope > 0.99 only for
n > 703 (measured up to 200). Quoted in the report sections 2 and 6.
"""
from __future__ import annotations

import json
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402

LATEST = sorted((REPO / "ledger" / "runs").glob("*.json"))[-1]


def wls(xs, ys, ws):
    sw = sum(ws)
    mx = sum(w * x for w, x in zip(ws, xs)) / sw
    my = sum(w * y for w, y in zip(ws, ys)) / sw
    sxx = sum(w * (x - mx) ** 2 for w, x in zip(ws, xs))
    a = sum(w * (x - mx) * (y - my) for w, x, y in zip(ws, xs, ys)) / sxx
    return a, my - a * mx


def main():
    d = json.loads(LATEST.read_text(encoding="utf-8"))
    print(f"ledger: {LATEST.name}")
    for e in d["entries"]:
        for m in e.get("v2") or []:
            mt = re.fullmatch(r"n\*\*([0-9.]+)", m["cost"])
            if m["measure"] != "time" or not mt or float(mt.group(1)) < 2.5:
                continue
            p = float(mt.group(1))
            ns, ts = m["n_values"], m["values"]
            u = [t / n ** (p - 1) for n, t in zip(ns, ts)]
            a, b = wls([float(n) for n in ns], u, [1 / x ** 2 for x in u])
            c = sum(t / n ** p for n, t in zip(ns, ts)) / len(ns)  # rough one-term scale (geometric would do too)
            c = math.exp(sum(math.log(t / n ** p) for n, t in zip(ns, ts)) / len(ns))
            r2 = math.sqrt(sum(((a * n ** p + b * n ** (p - 1)) / t - 1) ** 2 for n, t in zip(ns, ts)) / len(ns))
            r1 = math.sqrt(sum((c * n ** p / t - 1) ** 2 for n, t in zip(ns, ts)) / len(ns))
            model = [a * n ** p + b * n ** (p - 1) for n in ns]
            al_model = fit_slope([p * math.log(n) for n in ns], [math.log(x) for x in model]) if min(model) > 0 else float("nan")
            # local slope > 0.99  <=>  (p a n + (p-1) b) >= 0.99 p (a n + b)  <=>  n >= b (0.99 p - p + 1) / (0.01 p a)
            n99 = b * (0.99 * p - p + 1) / (0.01 * p * a) if a > 0 else float("nan")
            print(f"{e['id'][:50]:50s} {m['algorithm'][:36]:36s} p={p:g} recorded alpha {m['alpha']:.3f}  "
                  f"b/a = {b / a:8.2f}  rel.RMS two-term {r2:.3f} vs one-term {r1:.3f} (ratio {r1 / r2:.2f})  model alpha {al_model:.3f}  "
                  f"local slope > 0.99 for n > {n99:.0f} (max measured n {ns[-1]})")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
