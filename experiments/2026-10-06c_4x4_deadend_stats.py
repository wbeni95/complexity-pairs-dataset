"""Experiment (research/2026-10-06c_kernel_deadends.md): with dead-end detection and escape in the Rust kernel
(search/kernel/flipwalk.rs, --dead-end 1), how often, and how fast, does an uncapped walk from the standard 4x4x4
algorithm reach ranks 49, 48 and 47 over GF(2)?

Baseline (RL-059, experiments/2026-10-07b_4x4_nocap_stats.py, kernel sha256 6f306293...ad644 without dead-end
escape): 24 seeds (101-124) x 900 s, 8 processes at a time: 20/24 reached 49 (median 13.8 s), 0/24 reached 48 or
47; pooled with RL-054, 1/28 reached 47 within 900 s. 19 of the 20 rank-49 endpoints admitted no flip.

This run repeats that design exactly, with the new kernel: 24 NEW seeds (601-624; no earlier 4x4 Rust walk used
them), each walk limited to 900 s, 8 walk processes at a time (3 rounds, about 45 minutes wall clock, inside the
60-minute box), below-normal priority, no weight cap, plateau 50 000, slack 3, target rank 0 (a walk at 47 keeps
trying for 46), dead-end escape on. Every result is re-verified with the exact Python verifier before it is
logged or saved (search/rust_kernel.py).

Rank 46 would be below the best known rank over GF(2): it would be re-verified separately and reported as a
candidate needing independent checks, never as a discovery. A NULL result bounds only this search.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_4x4_deadend_stats.py
Output: search/runs/2026-10-06c_4x4_deadend.jsonl (one line per walk; console copy in
        search/runs/2026-10-06c_4x4_deadend.console.txt) and
        search/schemes/rust-2026-10-06c/4x4x4_rank<r>_seed<s>.json (verified best scheme of every walk).
Analysis: experiments/2026-10-06c_analysis.py.

RESULT (2026-10-06, 11:44:27-12:29:28, 2701 s; exit 0; all 24 results verified): 4/24 walks reached rank 47
(seeds 610, 617, 618, 622 at 890.5, 842.9, 209.8 and 796.1 s; 95% CI 0.047-0.374), against 0/24 in RL-059
(Fisher two-sided p = 0.109). 14/24 reached <= 49 (baseline 20/24, p = 0.111). Final ranks: 47 x4, 49 x10, 50 x7,
52 x3. In all four rank-47 walks, ranks 49, 48 and 47 were first reached within 481-17 109 steps of each other:
they did not come out of a rank-49 dead end. The 10 walks that sat at a rank-49 dead end (all with the invariant
of Strassen (x) Strassen) made 1.94e8 escapes in 8298 s and never improved. No rank below 47. 3.589e11 steps,
3.70e10 flips in total. Whether the escape caused any of the four 47s: NO. Re-run with --dead-end 0 (the old
kernel), all four reach the same rank-47 scheme at the same step (experiments/2026-10-06c_counterfactual_old_kernel.py),
so the 0/24 -> 4/24 difference to RL-059 is a difference between seed sets.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARGS = ["--format", "4", "4", "4", "--seeds", "601-624", "--workers", "8", "--max-seconds", "900",
        "--dead-end", "1", "--best-known", "47", "--save-dir", "search/schemes/rust-2026-10-06c",
        "--log", "search/runs/2026-10-06c_4x4_deadend.jsonl"]

if __name__ == "__main__":
    t0 = time.time()
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}  args {' '.join(ARGS)}", flush=True)
    p = subprocess.run([sys.executable, "-m", "search.rust_kernel", *ARGS], cwd=ROOT,
                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    print(f"exit {p.returncode}")
    for line in p.stdout.splitlines():
        if not line.startswith("{"):
            if line.strip():
                print("  " + line[:300])
            continue
        d = json.loads(line)
        if "build" in d:
            print(f"build {d['build']}")
            continue
        st = d.get("stats") or {}
        rate = st.get("steps", 0) / st["seconds"] if st.get("seconds") else 0
        imp = d.get("improvements", [])
        print(f"  seed {d['seed']}: best rank {d.get('best_rank')}  verified {d.get('verified')}  "
              f"steps {int(st.get('steps', 0))}  {rate:.3e} steps/s  flips {int(st.get('flips', 0))}  "
              f"plus {int(st.get('plus', 0))}  restarts {int(st.get('restarts', 0))}  "
              f"dead_ends {int(st.get('dead_ends', 0))}  last improvements {imp[-3:]}  error {d.get('error')}")
    print(f"total wall clock {time.time() - t0:.0f} s  end {time.strftime('%Y-%m-%d %H:%M:%S')}")
