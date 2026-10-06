"""Experiment (research/2026-10-06c_kernel_deadends.md): reproduce and save the rank-47 4x4x4 scheme that the OLD kernel
(no dead-end escape) reached with seed 707 during the throughput benchmark.

Why: experiments/2026-10-06c_kernel_throughput.py ran 8 walks x 45 s from the standard 4x4x4 algorithm with the
kernel as it was before this round (experiments/2026-10-06c_flipwalk_before.rs, sha256 6f306293...ad644) and with
the new kernel in --dead-end 0 mode (identical trajectories). In both, seed 707 reached rank 47 (the best known
GF(2) rank) at about 43.6-44.0 s. That benchmark logged counters but not the scheme or the improvement history.
The kernel is deterministic per seed apart from the time cut-off, so this script re-runs the same walk with a
step budget instead of a time budget and stops at rank 47 (--target-rank 47): identical up to that step.

It runs ONE process (below-normal priority) and must be started after the 8-process main run had finished.
The walk is run with both binaries (before, and new with --dead-end 0) to confirm that they agree; the scheme is
verified with the exact verifier, saved to search/schemes/rust-2026-10-06c/4x4x4_rank47_before_seed707.json and
re-verified by experiments/2026-10-06c_analysis.py (verify, verify_explicit, 200 random checks).
A rank of 47 equals the best known rank over GF(2): a rediscovery, not a new result.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_reproduce_before_seed707.py
RESULT (2026-10-06, 12:29:50-12:30:54): both binaries reached rank 47 at step 628 866 994 (31.0 s and 32.4 s as a
single process; 98 739 943 flips, 12 192 plus transitions), via 50 at step 542 643 415, 49 at 628 850 710 and 48 at
628 850 779. The two were identical (improvement history and scheme). The scheme passed the exact verifier and was saved;
the analysis re-verified it (verify, verify_explicit, 200 random checks: all True; not valid over Z). Its factor-rank
invariant equals that of the four rank-47 schemes of the main run and differs from AlphaTensor's, Kauers-Moosbauer's
and RL-054's.
"""
import hashlib
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, rust_kernel as rk  # noqa: E402
from search.experiment import status_label  # noqa: E402

BEFORE_SRC = ROOT / "experiments" / "2026-10-06c_flipwalk_before.rs"
BEFORE_BIN = rk.BUILD_DIR / ("flipwalk_before.exe" if os.name == "nt" else "flipwalk_before")
SAVE = ROOT / "search" / "schemes" / "rust-2026-10-06c" / "4x4x4_rank47_before_seed707.json"
SEED, MAX_STEPS = 707, 3_000_000_000

if __name__ == "__main__":
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    p = subprocess.run(["rustc", "-O", "--edition", "2021", "-o", str(BEFORE_BIN), str(BEFORE_SRC)],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    rk.build()
    fmt = (4, 4, 4)
    path = rk._write_input(gf2mm.standard_scheme(fmt))
    results = {}
    try:
        for kind in ("before", "new_off"):
            binary = BEFORE_BIN if kind == "before" else rk.BIN
            cmd = [str(binary), "--input", path, "--seed", str(SEED), "--max-steps", str(MAX_STEPS),
                   "--max-seconds", "600", "--plateau", "50000", "--slack", "3", "--max-weight", "0",
                   "--target-rank", "47"]
            if kind == "new_off":
                cmd += ["--dead-end", "0"]
            proc = rk._popen(cmd)
            out, err = proc.communicate()
            assert proc.returncode == 0, err
            res = rk.parse_output(out)
            rk.check_result(fmt, res["best"], SEED)
            results[kind] = res
            print(f"{kind}: best rank {len(res['best'])}  stats {res['stats']}  improvements {res['improvements']}",
                  flush=True)
    finally:
        os.unlink(path)
    a, b = results["before"], results["new_off"]
    same = (a["best"] == b["best"] and [(r, s) for r, s, _ in a["improvements"]] == [(r, s) for r, s, _ in b["improvements"]])
    print(f"before and new --dead-end 0 identical: {same}")
    r = len(a["best"])
    if r <= 47:
        SAVE.parent.mkdir(parents=True, exist_ok=True)
        gf2mm.save_scheme(SAVE, fmt, a["best"], status=status_label(r, 47), best_known_rank=47,
                          provenance={"kernel": "experiments/2026-10-06c_flipwalk_before.rs",
                                      "kernel_sha256": hashlib.sha256(BEFORE_SRC.read_bytes()).hexdigest(),
                                      "seed": SEED, "params": {"plateau": 50000, "slack": 3, "max_weight": 0,
                                                               "target_rank": 47, "max_steps": MAX_STEPS},
                                      "stats": a["stats"], "improvements": a["improvements"],
                                      "script": "experiments/2026-10-06c_reproduce_before_seed707.py",
                                      "environment": {"python": platform.python_version(),
                                                      "platform": platform.platform()}})
        print(f"saved {SAVE.relative_to(ROOT)}")
    print(f"end {time.strftime('%Y-%m-%d %H:%M:%S')}")
