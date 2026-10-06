#!/usr/bin/env python3
"""Mass generation and screening of rule-mined candidates (round 2026-10-06d).

For each of the 7 rules in generators/rules/, generate COUNTS[rule] candidates with generator seed 1, screen
every one (correctness on seeded instances -> EXACT / NEAR-MISS / WRONG / INVALID; exact operation counts and
log-log fits with rivals for EXACT candidates), deduplicate by canonical form and cluster.

Outputs:
  candidates/2026-10-06d/<rule>.jsonl   compact candidate store (committed; reproducible from generator + seed)
  candidates/2026-10-06d/summary.json   per-rule statistics
  results/2026-10-06d/<rule>_full.jsonl full records incl. per-n counts (gitignored)

Deterministic: generator seed 1, screen seed 0, instance seeds derived from candidate ids. Runs at below-normal
priority with at most 4 worker processes (one rule per task). Wall time on the maintainer's machine: see the
report (about a minute).

Usage: python experiments/2026-10-06d_rules_mass_screen.py [--max-seconds 1200]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

COUNTS = {"memo": 300, "convolution": 300, "magma_power": 320, "greedy": 260, "knuth": 260, "bilinear": 260,
          "mitm": 220}
GEN_SEED = 1


def _init():
    from search.machine import set_below_normal_priority
    set_below_normal_priority()


def _work(rule):
    from generators.rules.runner import run_rule
    t0 = time.perf_counter()
    recs = run_rule(rule, GEN_SEED, COUNTS[rule])
    return rule, recs, time.perf_counter() - t0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-seconds", type=float, default=1200)
    args = ap.parse_args(argv)
    _init()
    from generators.rules.common import write_jsonl
    from generators.rules.runner import compact, summarise
    t0 = time.perf_counter()
    cand_dir = REPO / "candidates" / "2026-10-06d"
    res_dir = REPO / "results" / "2026-10-06d"
    summary = {"generator_seed": GEN_SEED, "screen_seed": 0, "counts_requested": COUNTS, "rules": {}}
    with ProcessPoolExecutor(max_workers=4, initializer=_init) as ex:
        futs = [ex.submit(_work, r) for r in COUNTS]
        for f in futs:
            rule, recs, secs = f.result(timeout=max(1.0, args.max_seconds - (time.perf_counter() - t0)))
            write_jsonl(res_dir / f"{rule}_full.jsonl", recs)
            write_jsonl(cand_dir / f"{rule}.jsonl", [compact(r) for r in recs])
            s = summarise(recs)
            s["seconds"] = round(secs, 1)
            summary["rules"][rule] = s
            print(f"{rule}: {s['candidates']} candidates, {s['verdicts']}, unique {s['unique_canonical']}, "
                  f"scaling resolved {s['scaling_resolved']}/{s['exact_with_scaling']} "
                  f"({s['distinct_scaling_keys']} keys), {secs:.1f}s", flush=True)
    tot = {"candidates": sum(s["candidates"] for s in summary["rules"].values()),
           "unique_canonical": sum(s["unique_canonical"] for s in summary["rules"].values())}
    for v in ("EXACT", "NEAR-MISS", "WRONG", "INVALID"):
        tot[v] = sum(s["verdicts"].get(v, 0) for s in summary["rules"].values())
    summary["total"] = tot
    summary["wall_seconds"] = round(time.perf_counter() - t0, 1)
    (cand_dir / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("TOTAL", json.dumps(tot), f"wall {summary['wall_seconds']}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
