"""Experiment (research/2026-10-07b_search_formats.md): a short, dedicated attempt at rank 46 for 4x4x4 over
GF(2), starting from a verified rank-47 scheme instead of the standard algorithm.

Start: search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json (found in RL-054; re-verified by the analysis
script). Rank 47 is the best known rank over GF(2) (Fawzi et al. 2022; the published AlphaTensor and
Kauers-Moosbauer rank-47 files verify too, see experiments/2026-10-07b_sources.py). Rank 46 would be BELOW the
best known: it would be reported only as a candidate needing independent checks.

Design (revised before launch, after the 4x4 statistics run): the analysis of that run showed that the start
scheme has NO pair of terms sharing a factor (0 flippable pairs), like the Strassen (x) Strassen-like rank-49
endpoints where 20 of 24 walks stalled. At such a scheme every step finds no flip partner, and the walk moves only
through a plus transition once per `plateau` steps. So two jobs run at once, 4 walk processes each (8 in total,
the concurrency limit), 120 s per walk, below-normal priority, no weight cap, slack 3, target rank 46 (a walk
stops early only if it reaches 46):
  A  seeds 1-4, plateau 50 000 (the default, as in all other runs)
  B  seeds 5-8, plateau 5 000  (ten times more plus transitions per step at a dead end)
The walk leaves the rank-47 scheme through plus transitions (rank +1) and flips; a restart returns it to the best
scheme when it drifts more than 3 above it. This was the last 2 minutes of the 60-minute search budget.
Every result is re-verified by the exact Python verifier before it is logged or saved (search/rust_kernel.py).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_4x4_from47.py
Output: search/runs/2026-10-07b_4x4_from47_p50000.jsonl, search/runs/2026-10-07b_4x4_from47_p5000.jsonl; schemes
under search/schemes/rust-2026-10-07b/from47/ named 4x4x4_rank<r>_seed<s>.json (seeds 1-8). A walk that never
goes below 47 saves the unchanged start scheme (the kernel replaces `best` only on a strict improvement).

RESULT (2026-10-06, 10:53:29-10:55:29, 120 s): all 8 walks stayed at 47 (no improvement, 0 restarts);
2.825e10 steps in total; plateau 5 000 gave ten times the flips and plus transitions of plateau 50 000 and no
other visible difference. NULL for rank 46 in this scope; the 8 saved files equal the start scheme.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
COMMON = ["--format", "4", "4", "4", "--start", "search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json",
          "--workers", "4", "--max-seconds", "120", "--target-rank", "46", "--best-known", "47",
          "--save-dir", "search/schemes/rust-2026-10-07b/from47"]
JOBS = {
    "A_plateau50000": COMMON + ["--seeds", "1-4", "--plateau", "50000",
                                "--log", "search/runs/2026-10-07b_4x4_from47_p50000.jsonl"],
    "B_plateau5000": COMMON + ["--seeds", "5-8", "--plateau", "5000",
                               "--log", "search/runs/2026-10-07b_4x4_from47_p5000.jsonl"],
}

if __name__ == "__main__":
    t0 = time.time()
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    procs = {name: subprocess.Popen([sys.executable, "-m", "search.rust_kernel", *args], cwd=ROOT,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
             for name, args in JOBS.items()}
    for name, p in procs.items():
        out, _ = p.communicate()
        print(f"=== job {name}: exit {p.returncode}")
        for line in out.splitlines():
            if not line.startswith("{"):
                if line.strip():
                    print("  " + line[:300])
                continue
            d = json.loads(line)
            if "build" in d:
                continue
            st = d.get("stats") or {}
            rate = st.get("steps", 0) / st["seconds"] if st.get("seconds") else 0
            print(f"  seed {d['seed']}: best rank {d.get('best_rank')}  verified {d.get('verified')}  "
                  f"steps {int(st.get('steps', 0))}  {rate:.3e} steps/s  flips {int(st.get('flips', 0))}  "
                  f"plus {int(st.get('plus', 0))}  restarts {int(st.get('restarts', 0))}  "
                  f"improvements {d.get('improvements', [])}  error {d.get('error')}")
    print(f"total wall clock {time.time() - t0:.0f} s  end {time.strftime('%Y-%m-%d %H:%M:%S')}")
