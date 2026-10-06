"""Experiment (RESEARCH_LOG RL-054): first time-boxed parallel run of the Rust flip-graph kernel.

Question: with the Rust kernel (RL-052) on 12 of 16 logical cores for 30 minutes, does the walk reach
  * 4x4x4 rank <= 48 over GF(2) (Strassen (x) Strassen gives 49; best known 47, AlphaTensor), or
  * 3x3x3 rank 22 over GF(2) (best known 23, Laderman; rank 22 open over GF(2))?
A NULL result only bounds what this search found (START_HERE section 6).

Three jobs run concurrently, 4 walk processes each, every walk limited to 1800 s, below-normal priority:
  A  4x4x4 from the standard algorithm, weight cap 4, seeds 1-4
  B  4x4x4 from the standard algorithm, no cap,       seeds 5-8
  C  3x3x3 from a saved rank-23 scheme, target 22,    seeds 1-4
Every result is re-verified by the exact Python verifier before it is logged or saved (search/rust_kernel.py).
Run from the repository root:  python experiments/2026-10-07_rust_parallel_30min.py
"""
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SAVE = "search/schemes/rust-2026-10-07"
BUDGET = "1800"
JOBS = {
    "A_4x4_cap4": ["--format", "4", "4", "4", "--seeds", "1-4", "--workers", "4", "--max-seconds", BUDGET,
                   "--max-weight", "4", "--best-known", "47", "--save-dir", SAVE,
                   "--log", "search/runs/2026-10-07_rust_4x4_cap4.jsonl"],
    "B_4x4_nocap": ["--format", "4", "4", "4", "--seeds", "5-8", "--workers", "4", "--max-seconds", BUDGET,
                    "--best-known", "47", "--save-dir", SAVE, "--log", "search/runs/2026-10-07_rust_4x4_nocap.jsonl"],
    "C_3x3_from23": ["--format", "3", "3", "3", "--start", "search/schemes/2026-10-07_flipgraph_3x3_3x3x3_seed1_rank23.json",
                     "--seeds", "1-4", "--workers", "4", "--max-seconds", BUDGET, "--plateau", "20000",
                     "--best-known", "23", "--target-rank", "22", "--save-dir", SAVE,
                     "--log", "search/runs/2026-10-07_rust_3x3_from23.jsonl"],
}

t0 = time.time()
procs = {name: subprocess.Popen([sys.executable, "-m", "search.rust_kernel", *args], cwd=ROOT,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
         for name, args in JOBS.items()}
for name, p in procs.items():
    out, _ = p.communicate()
    print(f"=== job {name}: exit {p.returncode}")
    for line in out.splitlines():
        if line.startswith("{"):
            d = json.loads(line)
            if "build" in d:
                continue
            st = d.get("stats") or {}
            rate = st.get("steps", 0) / st["seconds"] if st.get("seconds") else 0
            print(f"  seed {d['seed']}: best rank {d.get('best_rank')}  verified {d.get('verified')}  "
                  f"steps {int(st.get('steps', 0))}  {rate:.3e} steps/s  flips {int(st.get('flips', 0))}  "
                  f"plus {int(st.get('plus', 0))}  restarts {int(st.get('restarts', 0))}  "
                  f"first-reached {d.get('improvements', [])[-1:]}  error {d.get('error')}")
        elif line.strip():
            print("  " + line[:200])
print(f"total wall clock {time.time() - t0:.0f} s")
