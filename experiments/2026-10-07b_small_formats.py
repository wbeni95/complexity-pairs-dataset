"""Experiment (search report research/2026-10-07b_search_formats.md): time-boxed Rust flip-graph walks on
ten small rectangular formats, each from the standard algorithm, over GF(2).

Question: does the Rust kernel (search/kernel/flipwalk.rs, unchanged since RL-052/RL-054) rediscover the best
known GF(2) rank of each format within a short budget, and does any walk go below it?

Best known ranks over GF(2) used for the status labels (sources and verification in
experiments/2026-10-07b_sources.py and the report's table):
  (2,2,3) 11, (2,2,4) 14, (2,3,3) 15, (2,3,4) 20, (2,4,4) 26, (3,3,4) 29, (3,3,5) 36, (3,4,4) 38,
  (3,4,5) 47, (4,4,5) 60 (60 is a characteristic-2 scheme of Kauers & Moosbauer; 61 over general rings).

Design: the formats run one after another; each format runs seeds 1-8 at once (8 walk processes, the
concurrency limit), below-normal priority, no weight cap, plateau 50 000, slack 3. The target rank is
best known - 1, so every walk uses its full budget and keeps trying to go below the best known rank; the
time and step at which the best known rank was first reached come from the kernel's IMPROVED lines.
Budgets per walk: 30 s for (2,2,3), (2,2,4), (2,3,3), (2,3,4); 60 s for (2,4,4), (3,3,4), (3,3,5), (3,4,4);
180 s for (3,4,5) and (4,4,5). Total wall clock about 4*30 + 4*60 + 2*180 = 720 s plus overhead.
Every result is re-verified by the exact Python verifier before it is logged or saved (search/rust_kernel.py).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_small_formats.py
Output: search/runs/2026-10-07b_small_<n>x<m>x<p>.jsonl and search/schemes/rust-2026-10-07b/*.json

RESULT (2026-10-06, 10:41:25-10:53:28, 722 s): best known rank reached by 8/8 seeds for (2,2,3), (2,2,4),
(2,3,3), (2,3,4), (2,4,4), (3,3,4), (3,3,5); 6/8 for (3,4,4) (others 39); 1/8 for (3,4,5) (47 at 97.2 s; others
48-51); 0/8 for (4,4,5) (best 64 vs 60). All 80 results verified. Nothing below a best known rank (NULL).
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVE = "search/schemes/rust-2026-10-07b"
SEEDS = "1-8"
WORKERS = "8"
JOBS = [  # (format, best known rank over GF(2), seconds per walk)
    ((2, 2, 3), 11, 30), ((2, 2, 4), 14, 30), ((2, 3, 3), 15, 30), ((2, 3, 4), 20, 30),
    ((2, 4, 4), 26, 60), ((3, 3, 4), 29, 60), ((3, 3, 5), 36, 60), ((3, 4, 4), 38, 60),
    ((3, 4, 5), 47, 180), ((4, 4, 5), 60, 180),
]

if __name__ == "__main__":
    t_all = time.time()
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    for fmt, best_known, secs in JOBS:
        name = "x".join(map(str, fmt))
        args = ["--format", *map(str, fmt), "--seeds", SEEDS, "--workers", WORKERS, "--max-seconds", str(secs),
                "--target-rank", str(best_known - 1), "--best-known", str(best_known), "--save-dir", SAVE,
                "--log", f"search/runs/2026-10-07b_small_{name}.jsonl"]
        t0 = time.time()
        p = subprocess.run([sys.executable, "-m", "search.rust_kernel", *args], cwd=ROOT,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        print(f"=== {name} (best known {best_known}, {secs} s per walk): exit {p.returncode}, "
              f"{time.time() - t0:.1f} s", flush=True)
        for line in p.stdout.splitlines():
            if not line.startswith("{"):
                if line.strip():
                    print("  " + line[:300])
                continue
            d = json.loads(line)
            if "build" in d:
                continue
            st = d.get("stats") or {}
            imp = d.get("improvements", [])
            first_bk = next(((s, t) for r, s, t in imp if r <= best_known), None)
            rate = st.get("steps", 0) / st["seconds"] if st.get("seconds") else 0
            print(f"  seed {d['seed']}: best {d.get('best_rank')}  verified {d.get('verified')}  "
                  f"first<=best_known (step, s) {first_bk}  steps {int(st.get('steps', 0))}  {rate:.3e} steps/s  "
                  f"flips {int(st.get('flips', 0))}  plus {int(st.get('plus', 0))}  restarts {int(st.get('restarts', 0))}  "
                  f"error {d.get('error')}", flush=True)
    print(f"total wall clock {time.time() - t_all:.0f} s  end {time.strftime('%Y-%m-%d %H:%M:%S')}")
