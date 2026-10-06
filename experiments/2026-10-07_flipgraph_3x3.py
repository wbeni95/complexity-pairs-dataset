"""Experiment (research/2026-10-07_search_flipgraph.md, run group G2): 3x3x3 over GF(2).

Questions:
  (a) Pipeline validation: starting from the standard algorithm (rank 27), does the walk reach rank 23 (Laderman
      1976; the best known rank)? Reaching 23 is a REDISCOVERY, not a new result.
  (b) Bounded search for rank 22 (whether a rank-22 scheme exists is open as far as the cited sources say; see the
      report). Finding nothing is a NULL result with the stated scope and proves nothing.

Budget: seeds 1..10, at most 10,000,000 flips per seed (about 45 s each at ~220k flips/s), plateau 50,000
flips, plus transitions with slack 1, linear reductions, target rank 22 (a run stops early only if rank 22 is
reached). The first rank-23 scheme of every run and the best scheme of every run are saved to search/schemes/.
Deterministic: fixed seeds and flip budgets; the 600 s wall-clock cap per run is a safety net only.

Run from the repository root:  python experiments/2026-10-07_flipgraph_3x3.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.driver import WalkConfig  # noqa: E402
from search.experiment import run_batch  # noqa: E402

configs = [WalkConfig(fmt=(3, 3, 3), seed=s, max_flips=10_000_000, plateau=50_000, escape="plus", slack=1,
                      reduction="linear", target_rank=22, max_seconds=600, verify_every=1_000_000,
                      log_every=1_000_000)
           for s in range(1, 11)]
run_batch("2026-10-07_flipgraph_3x3", "experiments/2026-10-07_flipgraph_3x3.py", configs, best_known=23)
