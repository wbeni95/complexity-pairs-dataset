"""Analysis (research/2026-10-06c_kernel_deadends.md): cost of the dead-end bookkeeping on IDENTICAL trajectories.

In the throughput benchmark (search/runs/2026-10-06c_throughput.jsonl, 4x4x4 from the standard algorithm, 45 s, 8
walks at once, seeds 701-708), a walk of the new kernel with the escape on that never detected a dead end follows
exactly the same trajectory as with the escape off and as the old kernel (detection draws no random numbers). For
those seeds, steps/s compares the same work with and without the bookkeeping (stamping and completion sweeps).
Prints per seed: steps/s before / off / on, and the ratios on/off and off/before. Deterministic given the log.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_paired_overhead.py
RESULT: see the report, section 3.
"""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
rows = [json.loads(line) for line in open(ROOT / "search/runs/2026-10-06c_throughput.jsonl", encoding="utf-8")]
by = {(r["start"], r["kernel"], r["seed"]): r for r in rows}
on_off, off_before = [], []
for seed in range(701, 709):
    b, f, o = (by[("standard", k, seed)] for k in ("before", "off", "on"))
    if o["stats"]["dead_ends"] != 0:
        print(f"seed {seed}: escape on detected {int(o['stats']['dead_ends'])} dead ends -> trajectories differ, skipped")
        continue
    on_off.append(o["steps_per_s"] / f["steps_per_s"])
    off_before.append(f["steps_per_s"] / b["steps_per_s"])
    print(f"seed {seed}: steps/s before {b['steps_per_s']:.4e}  off {f['steps_per_s']:.4e}  on {o['steps_per_s']:.4e}  "
          f"on/off {on_off[-1]:.4f}  off/before {off_before[-1]:.4f}  (flips/step on {o['stats']['flips'] / o['stats']['steps']:.4f})")
print(f"median on/off {statistics.median(on_off):.4f} (range {min(on_off):.4f}-{max(on_off):.4f}, n={len(on_off)}); "
      f"median off/before {statistics.median(off_before):.4f} (range {min(off_before):.4f}-{max(off_before):.4f})")
