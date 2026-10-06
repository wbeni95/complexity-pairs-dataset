"""Probes used to design the dead-end tests (research/2026-10-06c_kernel_deadends.md, section 2), consolidated here so
that they can be re-run with the final kernel. During development they were run as scratch scripts. Their outcome
then was the same as below for part A. Part B was run then with an intermediate kernel without the completion sweep;
those numbers are quoted in the report and cannot be reproduced from the repository.

A. Can a dead end be left through a RESTART (that needs a dead end above best + slack)?
   A1. Rust kernel (escape on), plateau 1e9 (so every restart comes from a dead end), slack 0, from the standard
       algorithm for 2x2x2, 2x2x3, 2x3x3, 3x3x3 and 2x2x4, seeds 1-30, 200 000 steps each: count walks with restarts.
   A2. Python mirror with the on_dead_end hook, formats 2x2x2, 2x2x3, 3x3x3, plateau 20/40/100, slack 0/1/2,
       seeds 1-10, 4 000 steps: count detections at a rank above best + slack.
B. Strassen (x) Strassen (4x4x4, rank 49), Python mirror, escape on, plateau 1e9, slack 0, seeds 1-8, 20 000 steps:
   flips, plus transitions and dead-end detections per walk (how long one escape cycle is).

Single process, a few seconds. Run from the repository root (after the main run had finished):
  ./.venv/Scripts/python experiments/2026-10-06c_test_design_probes.py
RESULT (2026-10-06, after the main run, 7.2 s): A1: no walk with a restart in any format (dead-end detections in
total: 2x2x2 9469, 2x3x3 1846, the others 0). A2: 0 detections above best + slack in 270 walks. So a dead end left
through a restart was never observed, and the tests do not assert it. B (final kernel): 7-42 detections and
1146-1399 flips per 20 000 steps, best 49. The intermediate kernel without the sweep had given 12-24 detections and
45-626 flips (scratch run, quoted in the report).
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, kernel_reference as kr, rust_kernel as rk  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    print("A1: Rust, plateau 1e9, slack 0, seeds 1-30, 200 000 steps")
    for fmt in ((2, 2, 2), (2, 2, 3), (2, 3, 3), (3, 3, 3), (2, 2, 4)):
        start = gf2mm.standard_scheme(fmt)
        with_restart, detections = [], 0
        for seed in range(1, 31):
            res = rk.run(fmt, start, seed=seed, max_steps=200_000, max_seconds=1e9, plateau=10**9, slack=0)
            detections += int(res["stats"]["dead_ends"])
            if res["stats"]["restarts"] > 0:
                with_restart.append(seed)
        print(f"  {fmt}: walks with a restart {len(with_restart)}/30 {with_restart}; dead-end detections in total "
              f"{detections}", flush=True)
    print("A2: mirror, detections above best + slack")
    above = 0
    for fmt in ((2, 2, 2), (2, 2, 3), (3, 3, 3)):
        for plateau in (20, 40, 100):
            for slack in (0, 1, 2):
                for seed in range(1, 11):
                    def hook(terms, best_rank, slack=slack):
                        global above
                        above += len(terms) > best_rank + slack
                    kr.walk(gf2mm.standard_scheme(fmt), seed, 4000, plateau=plateau, slack=slack, on_dead_end=hook)
    print(f"  detections above best + slack: {above} (in 270 walks)", flush=True)
    print("B: mirror from Strassen (x) Strassen, plateau 1e9, slack 0, 20 000 steps")
    s = gf2mm.strassen_scheme()
    _, ss = gf2mm.kron_scheme((2, 2, 2), s, (2, 2, 2), s)
    for seed in range(1, 9):
        res = kr.walk(ss, seed, 20000, plateau=10**9, slack=0)
        print(f"  seed {seed}: best {len(res['best'])}, flips {res['flips']}, plus {res['plus']}, "
              f"restarts {res['restarts']}, dead ends {res['dead_ends']}", flush=True)
    print(f"{time.time() - t0:.1f} s")
