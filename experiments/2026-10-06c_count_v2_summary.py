"""Summary of the entries converted to count-based V2 in round 2026-10-06c, computed with the validator's own run_v2.

Entries: range-minimum-queries-naive-vs-sparse-table, polynomial-multiplication-naive-vs-ntt,
minimum-spanning-tree-brute-vs-kruskal (7 algorithm fits). For every fit it prints alpha, |alpha - 1|, each
declared rival's alpha, the smallest rival distance, the log-factor diagnostic, and the common tolerance
window [max |alpha - 1|, min rival distance). It also prints a SHA-256 over all count series, so that the run
can be repeated under another Python version and compared (Kruskal's count includes comparisons made inside
CPython's sorted(), which could differ between versions; RL-057 saw such a difference for closest pair).

Run from the repository root:
  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-06c_count_v2_summary.py      (3.14.2)
  PYTHONIOENCODING=utf-8 py -3.12 experiments/2026-10-06c_count_v2_summary.py                    (3.12, CI's version)
run_v2 needs no third-party package, so both work. Deterministic.

Outcome (runs 2026-10-06):
  Python 3.14.2: all 7 fits pass at tolerance 0.03 and all 18 declared rivals are rejected. Largest
  |alpha - 1| = 0.0073 (RMQ sparse table), smallest rival distance 0.0652 (MST enumeration vs C(m, n-1)),
  smallest diagnostic distance 0.0363 (MST enumeration); common window [0.0073, 0.0652). Log factor resolved
  in all 7 fits. sha256 aa48df69a47a716036573a53737f6ec51f409c3a8ff88d076463f66e5556a042.
  Python 3.12.10: sha256 e6c29336b2423f3f3c14f863e7a719f20c229aef3498ab323e117d60778903cb. The ONLY difference is
  the Kruskal series: 14766 / 69346 / 318302 / 1435596 / 6388918 (3.14.2: 14811 / 69526 / 319007 / 1438399 /
  6400007), alpha 0.9982 (3.14.2: 0.9980), rivals n**2 1.0943, n**2*log(n)**2 0.9175, n**3 0.7295, all rejected.
  The other 6 series are identical. 2026-10-06c_mst_counts.py under 3.12 shows the difference is entirely in
  the comparisons inside sorted().
"""
import hashlib
import importlib.util
import json
import platform
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

ENTRIES = [
    "range-minimum-queries-naive-vs-sparse-table",
    "polynomial-multiplication-naive-vs-ntt",
    "minimum-spanning-tree-brute-vs-kruskal",
]

print("Python", platform.python_version())
rows, series = [], []
for eid in ENTRIES:
    d = H.REPO / "pairs" / eid
    entry = json.loads((d / "entry.json").read_text(encoding="utf-8"))
    rec = {}
    errors = H.V.run_v2(entry, d, False, rec)
    if errors:
        print("ERRORS", eid, errors)
    for m in rec["v2"]:
        dev = abs(m["alpha"] - 1)
        rmin = min(abs(r["alpha"] - 1) for r in m["rivals"])
        dg = m["diagnostics"]
        dmin = min(abs(dg["alpha_vs_cost_times_log"] - 1), abs(dg["alpha_vs_cost_over_log"] - 1))
        rows.append((eid, m["algorithm"], m["cost"], m["alpha"], dev, rmin, dmin, m["tolerance"], m["passed"],
                     dg["resolves_log_factor"], ", ".join(f"{r['cost'][:28]}={r['alpha']:.4f}" for r in m["rivals"])))
        series.append([eid, m["algorithm"], m["n_values"], [int(v) for v in m["values"]]])
        print(f"{eid} / {m['algorithm']}: n={m['n_values']} counts={[int(v) for v in m['values']]}")

print()
for eid, alg, cost, a, dev, rmin, dmin, tol, ok, res, rv in rows:
    print(f"{(eid[:22] + '/' + alg)[:48]:48s} {cost[:22]:22s} alpha={a:.4f} |a-1|={dev:.4f} minRival={rmin:.4f} "
          f"minDiag={dmin:.4f} tol={tol} pass={ok} logResolved={res}\n      rivals: {rv}")
print(f"\nlargest |alpha - 1| = {max(r[4] for r in rows):.4f}; smallest rival distance = {min(r[5] for r in rows):.4f}; "
      f"smallest diagnostic distance = {min(r[6] for r in rows):.4f}")
print("common tolerance window: [%.4f, %.4f)" % (max(r[4] for r in rows), min(r[5] for r in rows)))
blob = json.dumps(series, sort_keys=True).encode()
print("sha256 of all count series:", hashlib.sha256(blob).hexdigest())
