"""Mutation pilot 2026-10-06d: MIRROR and OPSWAP (semiring / monoid substitution) over the pairs in pairs/.

Runs every mutant defined in mutations/targets.py (differential testing on seeded instances, shrinking, cost fits for
survivors) and writes one JSONL record per mutant to mutations/records/2026-10-06d/<builder>.jsonl, then the
mechanical property table (properties.jsonl). Deterministic: every instance is drawn from random.Random seeded with
"2026-10-06d|<mutant id>|<n>|<trial>"; operation counts are exact. Wall-clock fields (elapsed_s) are informational.

At most 4 worker processes, below-normal priority, per-call watchdog of 5 s (mutations/engine.py).

Usage:  python experiments/2026-10-06d_mut_pilot.py [--only matmul,apsp,...]
Result of the recorded run: see research/2026-10-06d_mutation_pilot.md.
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from search.machine import set_below_normal_priority  # noqa: E402
from mutations.__main__ import main  # noqa: E402

if __name__ == "__main__":
    set_below_normal_priority()
    args = sys.argv[1:]
    rc = main(["run", "--workers", "4", *args])
    if rc == 0 and not args:
        rc = main(["props"])
    sys.exit(rc)
