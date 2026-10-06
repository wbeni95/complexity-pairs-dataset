"""Experiment (research/2026-10-07_search_flipgraph.md, NEAR-MISSES / G3d): how strongly does the Strassen-squared
scheme (rank 49 for 4x4x4) attract the walk?

Strassen (x) Strassen has 49 pairwise distinct factors in every position, so no flip is available: the walk must
start with a plus transition (rank 50). Question: how often does the walk fall back into a rank-49 state with no
available flip (a "dead end"), for 1, 2 or 3 plus transitions per escape (slack = the same number)?
Budget: seed 1, 1,000,000 steps per setting, plateau 200,000, linear reductions. Deterministic.

Run from the repository root:  python experiments/2026-10-07_flipgraph_4x4_strassen2_probe.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search import gf2mm  # noqa: E402
from search.driver import WalkConfig, run_walk  # noqa: E402
from search.machine import CpuMeter, set_below_normal_priority  # noqa: E402

print("below-normal priority:", set_below_normal_priority())
fmt, s49 = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), (2, 2, 2), gf2mm.strassen_scheme())
assert len(s49) == 49 and gf2mm.verify(fmt, s49)
for k in (1, 2, 3):
    meter = CpuMeter().start()
    r = run_walk(WalkConfig(fmt=fmt, seed=1, max_flips=1_000_000, plateau=200_000, slack=k, plus_per_escape=k),
                 start=s49)
    load = meter.stop()
    dead = r["no_flip_available_events"]
    print(f"plus per escape {k} (slack {k}): best rank {r['best_rank']}; {r['flips']:,} flips + {dead:,} dead ends; "
          f"plus transitions {r['plus_transitions']:,}; restarts {r['restarts']}; one dead end per "
          f"{r['flips'] / max(dead, 1):.1f} flips; {load['wall_seconds']} s, system CPU {load['system_cpu_utilisation']}")
