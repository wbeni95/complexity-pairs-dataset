"""Summary of the eight entries (17 fits) converted to count-based V2 on 2026-10-07b, computed with the validator's own run_v2.

For every algorithm of the eight converted entries this prints the fitted alpha, the deviation |alpha - 1|,
every declared rival's alpha, the smallest rival distance min |alpha_rival - 1|, the log-factor diagnostic
and the resulting "tolerance window": any tolerance t with |alpha - 1| <= t < min rival distance would give
the same pass/reject verdicts (and t < min(|diag - 1|) also resolves the log factor). The chosen tolerance
is 0.03 everywhere; the window shows how much room it has on each side.

Uses tools/validate.run_v2 unchanged (exact counts, measure "reported"), so the numbers are those of
`tools/validate.py <entry> --scaling`. Deterministic.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_summary.py
(run_v2 does not need jsonschema, so this runs with the project venv as it is)

Outcome (run 2026-10-06 local date, Python 3.14.2): all 17 fits pass at tolerance 0.03; largest
|alpha - 1| = 0.0140 (LIS subset enumeration), smallest declared-rival distance 0.0644 (element distinctness,
all pairs vs n^2 log n), so every tolerance in [0.0140, 0.0644) gives the same verdicts. The log-factor
diagnostic is resolved for 16 of 17 fits; the exception is the LIS subset enumeration (distance 0.0184).
"""
import importlib.util
import json
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

ENTRIES = [
    "sorting-insertion-vs-merge",
    "element-distinctness-pairs-vs-sorting",
    "bipartite-matching-kuhn-vs-hopcroft-karp",
    "inversion-counting-quadratic-vs-merge",
    "longest-increasing-subsequence",
    "closest-pair-brute-vs-divide-conquer",
    "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall",
    "string-matching-naive-vs-kmp",
]

rows = []
for eid in ENTRIES:
    d = H.REPO / "pairs" / eid
    entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
    rec = {}
    errors = H.V.run_v2(entry, d, False, rec)
    for m in rec["v2"]:
        dev = abs(m["alpha"] - 1)
        rmin = min(abs(r["alpha"] - 1) for r in m["rivals"]) if m["rivals"] else float("nan")
        dg = m["diagnostics"]
        dmin = min(abs(dg["alpha_vs_cost_times_log"] - 1), abs(dg["alpha_vs_cost_over_log"] - 1)) if dg else float("nan")
        rows.append((eid, m["algorithm"], m["cost"], m["alpha"], dev, rmin, dmin, m["tolerance"], m["passed"],
                     ", ".join(f"{r['cost']}={r['alpha']:.3f}" for r in m["rivals"])))
    if errors:
        print("ERRORS", eid, errors)

print(f"{'entry / algorithm':70s} {'cost':16s} {'alpha':>7s} {'|a-1|':>7s} {'minRiv':>7s} {'minDiag':>7s} tol  ok  rivals")
for eid, alg, cost, a, dev, rmin, dmin, tol, ok, rv in rows:
    print(f"{(eid[:34] + ' / ' + alg)[:70]:70s} {cost:16s} {a:7.4f} {dev:7.4f} {rmin:7.4f} {dmin:7.4f} {tol} {ok}  {rv}")
devs = [r[4] for r in rows]
rmins = [r[5] for r in rows]
dmins = [r[6] for r in rows]
print(f"\nlargest |alpha - 1| = {max(devs):.4f}; smallest rival distance = {min(rmins):.4f}; "
      f"smallest log-diagnostic distance = {min(dmins):.4f}")
print("tolerance window common to all fits: [%.4f, %.4f)" % (max(devs), min(rmins)))

