"""Experiment (research/2026-10-07_search_flipgraph.md, run group G3a): which walk policy works best for 4x4x4
over GF(2) in pure Python, starting from the standard algorithm (rank 64)?

Context: a 90-second smoke test (plateau 200,000, plus transitions) reached rank 54 after 2.2M flips and then
stalled for 19M flips. This calibration compares six policies on two seeds each, with an identical flip budget,
to choose the policy for the main runs (experiments/2026-10-07_flipgraph_4x4.py) and to record the variants that
underperform (NEAR-MISSES / IDEAS sections of the report).

Policies (escape, plateau, slack, reduction):
  P1 plus,    200,000, 1, linear     (baseline of the smoke test)
  P2 plus,  1,000,000, 1, linear     (longer patience)
  P3 plus,     50,000, 1, linear     (shorter patience)
  P4 restart, 1,000,000, -, linear   (restarts from a pool of best-rank schemes, no plus transitions)
  P5 plus,    200,000, 1, pair       (R1+R2 only, no linear-dependence shortcut R3)
  P6 plus,    200,000, 2, linear     (plus transitions may go two above the best rank)
Budget: 20,000,000 flips per run (about 90-100 s each at ~220k flips/s), seeds 1 and 2, 12 runs in total.
A wall-clock cap of 400 s per run is a safety net only; if it triggers, the summary says "stopped by time".

Run from the repository root:  python experiments/2026-10-07_flipgraph_4x4_calibration.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.driver import WalkConfig  # noqa: E402
from search.experiment import run_batch  # noqa: E402

POLICIES = [
    ("P1", "plus", 200_000, 1, "linear"),
    ("P2", "plus", 1_000_000, 1, "linear"),
    ("P3", "plus", 50_000, 1, "linear"),
    ("P4", "restart", 1_000_000, 1, "linear"),
    ("P5", "plus", 200_000, 1, "pair"),
    ("P6", "plus", 200_000, 2, "linear"),
]
configs = []
for seed in (1, 2):
    for tag, escape, plateau, slack, reduction in POLICIES:
        configs.append(WalkConfig(fmt=(4, 4, 4), seed=seed, max_flips=20_000_000, plateau=plateau, escape=escape,
                                  slack=slack, reduction=reduction, max_seconds=400, verify_every=1_000_000,
                                  log_every=1_000_000, extra={"tag": tag}))
run_batch("2026-10-07_flipgraph_4x4_calibration", "experiments/2026-10-07_flipgraph_4x4_calibration.py",
          configs, best_known=47)
