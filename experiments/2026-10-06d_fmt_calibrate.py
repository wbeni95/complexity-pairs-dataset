#!/usr/bin/env python3
"""Calibration (research/2026-10-06d_exotic_formats.md, section 4): how often does the kernel reach the best known
GF(2) rank, before and after the two method changes of this round?

Changes compared (2 x 2 design, same seeds in every arm):
  * start: the standard algorithm, or a block start (best single split of one dimension into two smaller formats,
    each realised by a verified scheme from earlier rounds; search/blocks.py);
  * reduction: the earlier kernel (--full-reduce 0), or the linear-dependence reduction (--full-reduce 1).
All other parameters as in RL-059 / RL-072: no weight cap, plateau 50 000, slack 3, dead-end escape on, 4 walk
processes at a time, below-normal priority. Every result is re-verified by the exact verifier before it is logged.

Usage (from the repository root; each invocation is one background job of at most 20 minutes):
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 345     # (3,4,5), record 47: 4 arms x 8 x 120 s
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 345v2   # the two full-reduce arms again (faster kernel)
  ./.venv/Scripts/python experiments/2026-10-06d_fmt_calibrate.py 445     # (4,4,5), record 60: 2 arms x 8 x 180 s
Logs: search/runs/2026-10-06d_cal_<fmt>.jsonl; schemes: search/schemes/rust-2026-10-06d/cal/.

RESULT: see the report, section 4 (printed summary per arm; console copy search/runs/2026-10-06d_cal_<fmt>.console.txt).
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import campaign  # noqa: E402
from search.machine import set_below_normal_priority  # noqa: E402

PLANS = {
    "345": dict(fmt=(3, 4, 5), record=47, seconds=120, seeds=list(range(1, 9)),
                arms=[("std_off", "standard", False), ("std_full", "standard", True),
                      ("blk_off", "block", False), ("blk_full", "block", True)]),
    # Re-run of the two --full-reduce arms after the allocation-free group scan (kernel 6933efaf..., identical
    # trajectories, 1.3-3.5x faster with the flag on; report section 4.3). Same seeds, same log file.
    "345v2": dict(fmt=(3, 4, 5), record=47, seconds=120, seeds=list(range(1, 9)),
                  arms=[("std_full_v2", "standard", True), ("blk_full_v2", "block", True)]),
    "445": dict(fmt=(4, 4, 5), record=60, seconds=180, seeds=list(range(1, 9)),
                arms=[("blk_off", "block", False), ("blk_full", "block", True)]),
}


def main(key):
    set_below_normal_priority()
    plan = PLANS[key]
    fmt, record = plan["fmt"], plan["record"]
    name = "x".join(map(str, fmt))
    log = ROOT / "search" / "runs" / f"2026-10-06d_cal_{name}.jsonl"
    save = ROOT / "search" / "schemes" / "rust-2026-10-06d" / "cal"
    starts = ROOT / "search" / "schemes" / "rust-2026-10-06d" / "starts"
    print(f"# calibration {fmt}, best known GF(2) rank {record}; {len(plan['seeds'])} seeds x {plan['seconds']} s per arm;"
          f" started {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    for arm, kind, full in plan["arms"]:
        start, label = campaign.build_start(fmt, kind, starts)
        t0 = time.time()
        res = campaign.run_arm(arm, fmt, start, label, plan["seeds"], plan["seconds"], record, log, save,
                               full_reduce=full)
        print(f"{arm:9s} start rank {len(start):3d} ({label}); full_reduce={full}; wall {time.time() - t0:.0f} s",
              flush=True)
        print(f"          {campaign.describe(res, record)}", flush=True)
        bad = [s for s in res if not s.get("verified")]
        if bad:
            print(f"          UNVERIFIED RESULTS: {bad}", flush=True)
    print(f"# finished {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
