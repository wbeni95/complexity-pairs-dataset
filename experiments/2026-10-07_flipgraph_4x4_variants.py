"""Experiment (research/2026-10-07_search_flipgraph.md, run group G3b): do two of our own heuristics help the
4x4x4 GF(2) walk from the standard algorithm?

Context (G3a, experiments/2026-10-07_flipgraph_4x4_calibration.py): all six policies reached only rank 52-54 in
20M flips; at rank ~54 only ~15 (p, value) keys are shared, so few flips exist and reductions are rare (a probe
found 0 of 2000 consecutive states with a reducing flip). Variants tested here, all on the base policy P2
(plus transitions, plateau 1,000,000, slack 1, linear reductions):
  V1 lookahead every 16 flips (scan all flips, take one that enables a reduction; search.flipgraph.reducing_flips)
  V2 weight cap 6  (reject flips creating a factor with more than 6 of 16 bits set)
  V3 weight cap 4
Budget: 20,000,000 flips per run (same as G3a, so P2 is the baseline), seeds 1 and 2, 6 runs.
Safety cap 600 s per run (lookahead makes flips slower); a run cut by it says "stopped by time".

Run from the repository root:  python experiments/2026-10-07_flipgraph_4x4_variants.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.driver import WalkConfig  # noqa: E402
from search.experiment import run_batch  # noqa: E402

VARIANTS = [("V1", dict(lookahead_every=16)), ("V2", dict(max_weight=6)), ("V3", dict(max_weight=4))]
configs = []
for seed in (1, 2):
    for tag, kw in VARIANTS:
        configs.append(WalkConfig(fmt=(4, 4, 4), seed=seed, max_flips=20_000_000, plateau=1_000_000, escape="plus",
                                  slack=1, reduction="linear", max_seconds=600, verify_every=1_000_000,
                                  log_every=1_000_000, extra={"tag": tag}, **kw))
run_batch("2026-10-07_flipgraph_4x4_variants", "experiments/2026-10-07_flipgraph_4x4_variants.py", configs,
          best_known=47)
