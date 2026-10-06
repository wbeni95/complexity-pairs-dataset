#!/usr/bin/env python3
"""Noise-free rival margins of every declared rival in the CURRENT entry files (deviation analysis, 2026-10-07b).

For every algorithm whose harness.scaling declares `rivals`, compute the alpha that data following the
CLAIMED cost exactly (no noise, no lower-order terms) would give against each rival over the declared n values,
and the margin |alpha - 1| - tolerance. A small margin means that a modest pre-asymptotic deviation of the real
counts from the claimed cost could make the rival "fit" and fail the claim (or, worse, make a wrong claim pass).

Scope note: at the time of this analysis (2026-10-06, ~10:00 local) another agent was editing entries; this
script reads whatever entry.json files exist when it runs. The 2026-10-06 output is quoted in
research/2026-10-07b_deviations.md section 4 with that caveat. Deterministic; no timing.

Result (2026-10-06, ~10:05 local): no declared rival is accepted by noise-free data. Smallest margins:
n^2 vs rival n^2 log n +0.035..+0.041 (tolerance 0.03; element distinctness, inversion counting, sorting);
Strassen +0.044 / schoolbook +0.049 (tolerance 0.02); n log n vs n log^2 n +0.059..+0.062 and vs n
+0.078..+0.083; XOR convolution naive vs n 4^n +0.065.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402


def main():
    for loc in ("pairs", "synthetic"):
        for d in sorted((REPO / loc).iterdir()):
            ej = d / "entry.json"
            if not ej.is_file():
                continue
            e = json.loads(ej.read_text(encoding="utf-8"))
            for a in e["algorithms"]:
                sc = a.get("harness", {}).get("scaling") or {}
                if not sc.get("rivals"):
                    continue
                ns, tol = sc["n_values"], sc.get("tolerance", 0.25)
                ys = [math.log(eval_cost(sc["cost"], n)) for n in ns]
                for r in sc["rivals"]:
                    xs = [math.log(eval_cost(r, n)) for n in ns]
                    al = fit_slope(xs, ys)
                    margin = abs(al - 1) - tol
                    print(f"{e['id'][:45]:45s} {a['name'][:30]:30s} claim {sc['cost']:12s} rival {r:18s} "
                          f"alpha {al:7.4f}  tol {tol:.3f}  margin {margin:+.4f}{'  <-- NOT rejected' if margin <= 0 else ''}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
