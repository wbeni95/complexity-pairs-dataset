#!/usr/bin/env python3
"""Do the numbers quoted in RESEARCH_LOG.md match the ledger files they cite? (deviation analysis, 2026-10-07b)

Recomputes from ledger/runs/*.json, per run: number of entries and OK entries, V1 entries / instances /
implementation runs, number of V2 measurements, how many passed, min and max alpha, the number of fits with a
computable log-factor diagnostic and how many resolve the log factor; and, for consecutive runs, the largest
|change| of a timing alpha (same configuration) and whether all reported-count series are identical.
Also compares every alpha in the RL-021 table (transcribed below from RESEARCH_LOG.md, 3 decimals) with
ledger 20261006T005329Z rounded to 3 decimals.

Claims checked (RESEARCH_LOG.md): RL-021 (55 V2, alpha 0.924..1.121, V1 on 28 entries, 1830 instances, 3714 runs),
RL-022 (alpha 0.924..1.128, largest change 0.028, 5 count fits identical), RL-044 (54/54, V1 43 entries,
2812 instances, 5917 runs, 88 V2, alpha 0.886..1.164, largest unchanged-entry change 0.033), RL-045 (88 V2,
0.886..1.164, largest change 0.015 matrix-chain plain recursion, 14 count series identical), RL-048/RL-050
(90 V2, 82 diagnostics computable, 5 resolve, all count-based).

Deterministic; ledger only. Result (2026-10-06): every checked claim holds; RL-021 table 54/54 alphas match
20261006T005329Z to 3 decimals; consecutive-run largest timing changes 0.0277, 0.0329, 0.0149, 0.0139; reported
series identical 6/6, 6/6, 14/14, 14/14; 070542Z: 82 diagnostics, 5 resolving, all reported counts.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RUNS = sorted((REPO / "ledger" / "runs").glob("*.json"))

RL021 = {  # (entry id, algorithm name prefix) -> alpha as printed in RL-021
    ("assignment-brute-vs-hungarian", "permutation"): 0.971, ("assignment-brute-vs-hungarian", "Hungarian"): 0.966,
    ("bernstein-vazirani-classical-vs-quantum", "classical"): 1.000,
    ("closest-pair-brute-vs-divide-conquer", "all pairs"): 1.011, ("closest-pair-brute-vs-divide-conquer", "Shamos"): 0.998,
    ("determinant-cofactor-vs-gaussian", "Laplace"): 1.009, ("determinant-cofactor-vs-gaussian", "Gaussian"): 0.972,
    ("edit-distance-brute-vs-dp", "plain"): 0.995, ("edit-distance-brute-vs-dp", "Wagner"): 1.046,
    ("fibonacci-naive-vs-dp", "naive"): 1.004, ("fibonacci-naive-vs-dp", "bottom-up"): 0.997, ("fibonacci-naive-vs-dp", "fast"): 1.100,
    ("gcd-trial-vs-euclid", "trial"): 1.044, ("gcd-trial-vs-euclid", "Euclid"): 0.961,
    ("grover-search-classical-vs-quantum", "classical"): 0.992, ("grover-search-classical-vs-quantum", "Grover"): 0.924,
    ("integer-multiplication-schoolbook-vs-karatsuba", "schoolbook"): 1.004, ("integer-multiplication-schoolbook-vs-karatsuba", "Karatsuba"): 1.022,
    ("inversion-counting-quadratic-vs-merge", "all pairs"): 1.043, ("inversion-counting-quadratic-vs-merge", "merge"): 1.028,
    ("knapsack-01-brute-vs-dp", "subset"): 0.978, ("knapsack-01-brute-vs-dp", "meet"): 0.992, ("knapsack-01-brute-vs-dp", "capacity"): 1.055,
    ("lcs-brute-vs-dp", "subsequence"): 0.984, ("lcs-brute-vs-dp", "dynamic"): 1.022,
    ("longest-increasing-subsequence", "subset"): 0.986, ("longest-increasing-subsequence", "quadratic"): 1.015,
    ("longest-increasing-subsequence", "patience"): 1.012,
    ("matrix-chain-recursion-vs-dp", "plain"): 0.998, ("matrix-chain-recursion-vs-dp", "bottom-up"): 0.950,
    ("maximum-subarray", "brute"): 0.982, ("maximum-subarray", "running"): 1.030, ("maximum-subarray", "Kadane"): 0.966,
    ("minimum-spanning-tree-brute-vs-kruskal", "enumeration"): 0.980, ("minimum-spanning-tree-brute-vs-kruskal", "Kruskal"): 1.015,
    ("minimum-spanning-tree-brute-vs-kruskal", "Prim"): 1.008,
    ("modular-exponentiation-repeated-vs-square-multiply", "repeated"): 1.002,
    ("modular-exponentiation-repeated-vs-square-multiply", "left-to-right"): 0.999,
    ("permanent-naive-vs-ryser", "sum"): 0.988, ("permanent-naive-vs-ryser", "Ryser"): 0.987,
    ("polynomial-multiplication-naive-vs-ntt", "schoolbook"): 1.035, ("polynomial-multiplication-naive-vs-ntt", "number"): 0.984,
    ("shortest-path-enumeration-vs-dijkstra", "simple"): 0.966, ("shortest-path-enumeration-vs-dijkstra", "Dijkstra"): 1.005,
    ("simon-classical-vs-quantum", "classical"): 0.993, ("simon-classical-vs-quantum", "Simon"): 1.121,
    ("sorting-insertion-vs-merge", "insertion"): 0.987, ("sorting-insertion-vs-merge", "merge"): 0.980,
    ("string-matching-naive-vs-kmp", "naive"): 1.021, ("string-matching-naive-vs-kmp", "Knuth"): 1.003,
    ("three-sum-cubic-vs-quadratic", "all"): 0.946, ("three-sum-cubic-vs-quadratic", "sort"): 1.012,
    ("tsp-brute-vs-held-karp", "permutation"): 0.988, ("tsp-brute-vs-held-karp", "Held"): 1.007,
}


def key(m):
    return (m["measure"], m["cost"], tuple(m["n_values"]), m["samples"], m["tolerance"])


def main():
    runs = [(p.stem, json.loads(p.read_text(encoding="utf-8"))) for p in RUNS]
    prev = None
    for stem, d in runs:
        es = d["entries"]
        v1 = [e["v1"] for e in es if e.get("v1")]
        v2 = [(e["id"], m) for e in es for m in (e.get("v2") or [])]
        al = [m["alpha"] for _, m in v2 if m["alpha"] is not None]
        diag = [m["diagnostics"] for _, m in v2 if m.get("diagnostics")]
        res = [(i, m["algorithm"], m["measure"]) for i, m in v2 if m.get("diagnostics", {}).get("resolves_log_factor")]
        print(f"{stem}: entries {len(es)} OK {sum(e['status'] == 'OK' for e in es)}; V1 entries {len(v1)}, "
              f"instances {sum(x['instances'] for x in v1)}, runs {sum(x['algorithm_runs'] for x in v1)}; "
              f"V2 {len(v2)} passed {sum(m['passed'] for _, m in v2)}; alpha {min(al):.3f}..{max(al):.3f}; "
              f"diagnostics {len(diag)}, resolving {len(res)}")
        for r in res:
            print(f"      resolves log factor: {r}")
        cur = {(i, m["algorithm"]): m for i, m in v2}
        if prev is not None:
            best, cnt_same, cnt_rep = (0.0, None), 0, 0
            for k, m in cur.items():
                p = prev.get(k)
                if p is None or key(p) != key(m):
                    continue
                if m["measure"] == "time":
                    dlt = abs(m["alpha"] - p["alpha"])
                    if dlt > best[0]:
                        best = (dlt, k, p["alpha"], m["alpha"])
                else:
                    cnt_rep += 1
                    cnt_same += p["values"] == m["values"]
            print(f"      vs previous run: largest timing |d alpha| = {best[0]:.4f} at {best[1]} "
                  f"({best[2]:.4f} -> {best[3]:.4f}); reported series identical {cnt_same}/{cnt_rep}")
        prev = cur
    # RL-021 table
    stem, d = runs[0]
    bad = 0
    n = 0
    for e in d["entries"]:
        for m in e.get("v2") or []:
            for (eid, pre), a in RL021.items():
                if eid == e["id"] and m["algorithm"].startswith(pre) and m["alpha"] is not None:
                    n += 1
                    if round(m["alpha"], 3) != a:
                        bad += 1
                        print(f"   RL-021 mismatch: {eid} / {m['algorithm']}: log {a} vs ledger {m['alpha']:.4f}")
    print(f"RL-021 table vs {stem}: {n} alphas compared, {bad} mismatches")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
