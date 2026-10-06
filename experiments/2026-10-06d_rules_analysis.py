#!/usr/bin/env python3
"""Cluster-level analysis of the 2026-10-06d candidate store (reads candidates/2026-10-06d/*.jsonl only).

Prints, per rule:
  * verdict counts, unique canonical forms, duplicates;
  * per cluster: size, verdicts, near-miss metrics (mean exact-rate, mean closeness, worst closeness = worst-case
    approximation ratio / coordinate agreement), precondition agreement;
  * for EXACT clusters with fits: the exponent change -- alpha of each side against its own claim, the cross alpha
    (fast counts against the slow claim), and the interval of local log-log slopes [local_min, local_max] as the
    uncertainty interval of alpha;
  * the precondition-vs-verdict confusion and the precision/recall of "precondition => EXACT".
Writes candidates/2026-10-06d/analysis.json.

Usage: python experiments/2026-10-06d_rules_analysis.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from generators.rules import RULES  # noqa: E402
from generators.rules.common import read_jsonl  # noqa: E402

D = REPO / "candidates" / "2026-10-06d"


def main() -> int:
    out = {}
    for rule in RULES:
        recs = read_jsonl(D / f"{rule}.jsonl")
        cl = defaultdict(list)
        for r in recs:
            cl[r.get("cluster", "?")].append(r)
        rows = []
        for name, rs in sorted(cl.items()):
            v = Counter(r["verdict"] for r in rs)
            nm = [r for r in rs if r["verdict"] in ("NEAR-MISS", "WRONG")]
            row = {"cluster": name, "n": len(rs), "unique": len({r.get("canonical") for r in rs}), "verdicts": dict(v)}
            if nm:
                row["nearness"] = {
                    "mean_exact_rate": round(sum(r["exact_rate"] for r in nm) / len(nm), 4),
                    "mean_closeness": round(sum(r["closeness_mean"] for r in nm) / len(nm), 4),
                    "worst_closeness": round(min(r["closeness_min"] for r in nm), 4),
                }
            ex = [r for r in rs if r["verdict"] == "EXACT" and r.get("scaling") and "slow" in r["scaling"]]
            if ex:
                s = ex[0]["scaling"]
                cross = [x for x in s["fast"]["rivals"] if x[0] == s["slow"]["cost"]]
                row["exponent"] = {
                    "slow_claim": s["slow"]["cost"], "slow_alpha": s["slow"]["alpha"],
                    "slow_local": [s["slow"]["local_min"], s["slow"]["local_max"]],
                    "fast_claim": s["fast"]["cost"], "fast_alpha": s["fast"]["alpha"],
                    "fast_local": [s["fast"]["local_min"], s["fast"]["local_max"]],
                    "cross_alpha_fast_vs_slow_claim": cross[0][1] if cross else None,
                    "resolved_fraction": f"{sum(r['scaling']['resolved'] for r in ex)}/{len(ex)}",
                }
            rows.append(row)
        conf = Counter((r.get("precondition"), r["verdict"]) for r in recs)
        tp = conf[(True, "EXACT")]
        fp = sum(c for (p, v), c in conf.items() if p is True and v != "EXACT")
        fn = conf[(False, "EXACT")]
        out[rule] = {
            "candidates": len(recs), "verdicts": dict(Counter(r["verdict"] for r in recs)),
            "unique": len({r.get("canonical") for r in recs}),
            "precondition_precision": round(tp / (tp + fp), 4) if tp + fp else None,
            "precondition_recall_of_exact": round(tp / (tp + fn), 4) if tp + fn else None,
            "exact_without_precondition": fn, "clusters": rows,
        }
        print(f"== {rule}: {len(recs)} candidates, {out[rule]['verdicts']}, unique {out[rule]['unique']}, "
              f"precondition precision {out[rule]['precondition_precision']}, recall {out[rule]['precondition_recall_of_exact']} "
              f"(EXACT without precondition: {fn})")
        for row in rows:
            extra = ""
            if "nearness" in row:
                extra += f" near={row['nearness']}"
            if "exponent" in row:
                e = row["exponent"]
                extra += (f" slow {e['slow_claim']} a={e['slow_alpha']} {e['slow_local']}; fast {e['fast_claim']} "
                          f"a={e['fast_alpha']} {e['fast_local']}; cross={e['cross_alpha_fast_vs_slow_claim']}; "
                          f"resolved {e['resolved_fraction']}")
            print(f"   {row['cluster']} n={row['n']} uniq={row['unique']} {row['verdicts']}{extra}")
    (D / "analysis.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
