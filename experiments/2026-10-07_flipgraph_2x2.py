"""Experiment (research/2026-10-07_search_flipgraph.md, run group G1): pipeline validation on 2x2x2 over GF(2).

Question: starting from the standard algorithm (rank 8), does the flip-graph random walk reach rank 7 (Strassen's
rank, optimal: no rank-6 scheme exists; see experiments/2026-10-07_rank_2x2_exhaustive.py and the cited sources)?
This is a REDISCOVERY of a known result, i.e. a validation of the pipeline, not a new pair.

Budget: 10 seeds (1..10), at most 1,000,000 flips each, plateau 2,000 flips, plus transitions (slack 1), linear
reductions; a run stops as soon as rank 7 is reached (target_rank = 7, since rank 6 is impossible).
Deterministic: fixed seeds and flip budgets, no time limit.

Run from the repository root:  python experiments/2026-10-07_flipgraph_2x2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.driver import WalkConfig  # noqa: E402
from search.experiment import run_batch  # noqa: E402

configs = [WalkConfig(fmt=(2, 2, 2), seed=s, max_flips=1_000_000, plateau=2_000, escape="plus", slack=1,
                      reduction="linear", target_rank=7, verify_every=4096, log_every=0)
           for s in range(1, 11)]
run_batch("2026-10-07_flipgraph_2x2", "experiments/2026-10-07_flipgraph_2x2.py", configs, best_known=7)
