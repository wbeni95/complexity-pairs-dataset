"""Experiment (search report research/2026-10-07b_search_formats.md): how often, and how fast, does an
uncapped Rust flip-graph walk from the standard 4x4x4 algorithm reach rank 47 over GF(2)?

Background: in RL-054 one of four uncapped walks (seed 8) reached rank 47, the best known rank over GF(2)
(Fawzi et al. 2022), after 726.7 s; the other three ended at 49, 49 and 50 after 1800 s. That is a single
anecdote. This run collects a count: 24 fresh seeds (101-124), each walk limited to 900 s, 8 walk processes
at a time (3 rounds, about 45 minutes wall clock), below-normal priority, kernel parameters as in RL-054
job B (no weight cap, plateau 50 000, slack 3, target rank 0 so that a walk at 47 keeps trying for 46).
Every result is re-verified by the exact Python verifier before it is logged or saved (search/rust_kernel.py).

Rank 46 would be below the best known rank over GF(2): it would be reported as a candidate needing
independent checks, never as a discovery. A NULL result bounds only this search (START_HERE section 6).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_4x4_nocap_stats.py
Output: search/runs/2026-10-07b_4x4_nocap.jsonl (one line per walk) and
        search/schemes/rust-2026-10-07b/4x4x4_rank<r>_seed<s>.json (verified best scheme of every walk).

RESULT (2026-10-06, 09:56:20-10:41:21, 2701 s): 0/24 walks reached 48 or 47 (95% CI for reaching 47 within
900 s: 0-0.142). Final ranks: 49 in 20 walks (first reached at 0.3-774.6 s, median 13.8 s), 50 in 1, 51 in 2,
52 in 1. 5.135e11 steps; 1.364-2.683e7 steps/s per walk. 19 of the 20 rank-49 endpoints have no two terms sharing
a factor (no flip possible). All 24 results verified. NULL for rank <= 48 in this scope.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ARGS = ["--format", "4", "4", "4", "--seeds", "101-124", "--workers", "8", "--max-seconds", "900",
        "--best-known", "47", "--save-dir", "search/schemes/rust-2026-10-07b",
        "--log", "search/runs/2026-10-07b_4x4_nocap.jsonl"]

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
              f"last improvements {imp[-3:]}  error {d.get('error')}")
    print(f"total wall clock {time.time() - t0:.0f} s  end {time.strftime('%Y-%m-%d %H:%M:%S')}")
