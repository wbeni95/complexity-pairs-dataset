"""Counterfactual check (research/2026-10-06c_kernel_deadends.md): would the OLD kernel (no dead-end escape) have
produced the same walks as the new one, seed for seed?

Reasoning: dead-end detection draws no random numbers and changes nothing until a dead end is reported. So up to the
first dead end, a walk of the new kernel follows exactly the trajectory of the old kernel with the same seed
(--dead-end 0 reproduces the old kernel exactly: 17/17 in experiments/2026-10-06c_kernel_throughput.py). In the main
run (experiments/2026-10-06c_4x4_deadend_stats.py), the four rank-47 walks (seeds 610, 617, 618, 622) reached
ranks 49, 48 and 47 at the same moment. If they met no dead end before that, the old kernel would have produced the
same rank 47 at the same step, and the 4/24 would owe nothing to the escape.

Test: for each seed, run the new kernel with --dead-end 0 (= old kernel), step-limited (no time cut-off) to the step at
which the main-run walk reached its last logged improvement (plus 1 000 steps), with --target-rank set to that rank.
Compare the improvement history (rank, step) and, for the rank-47 walks, the final scheme with the main run's log
and saved file. Seeds: 610, 617, 618, 622 (rank 47) and, as a control of the reasoning, 612 and 614 (dead_ends = 0
in the main run, so they must be identical over their whole logged history).
6 processes at once (fewer than 8), below-normal priority, run after the main run had finished.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_counterfactual_old_kernel.py
RESULT (2026-10-06, 12:30:50-12:43:17): all six identical. Seeds 610, 617, 618 and 622 reach rank 47 with the old
kernel at exactly the same steps (16 849 618 541, 13 249 771 120, 3 618 583 155, 12 415 779 886), with the same
improvement histories and the same rank-47 schemes. The controls 612 and 614 are identical up to their last
improvement (rank 50). So the four rank-47 walks met no dead end before 47: the escape contributed nothing to them.
"""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, rust_kernel as rk  # noqa: E402

SEEDS = [610, 617, 618, 622, 612, 614]

if __name__ == "__main__":
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    log = {}
    with open(ROOT / "search/runs/2026-10-06c_4x4_deadend.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            log[d["seed"]] = d
    rk.build()
    fmt = (4, 4, 4)
    start = gf2mm.standard_scheme(fmt)
    path = rk._write_input(start)
    procs = []
    try:
        for seed in SEEDS:
            imp = log[seed]["improvements"]
            last_rank, last_step = imp[-1][0], imp[-1][1]
            cmd = rk._command(path, seed, last_step + 1000, 3600, 50_000, 3, 0, last_rank, dead_end=False)
            procs.append((seed, imp, rk._popen(cmd)))
        for seed, imp, proc in procs:
            out, err = proc.communicate()
            assert proc.returncode == 0, err
            res = rk.parse_output(out)
            rk.check_result(fmt, res["best"], seed)
            got = [(r, s) for r, s, _ in res["improvements"]]
            want = [(r, s) for r, s, _ in imp]
            same_hist = got == want
            line = (f"seed {seed}: main run (escape on) dead_ends {int(log[seed]['stats']['dead_ends'])}, last improvement "
                    f"rank {want[-1][0]} at step {want[-1][1]} | old kernel (--dead-end 0): best rank {len(res['best'])}, "
                    f"steps {int(res['stats']['steps'])}, last improvement {got[-1] if got else None} | "
                    f"identical improvement history: {same_hist}")
            saved = ROOT / f"search/schemes/rust-2026-10-06c/4x4x4_rank{want[-1][0]}_seed{seed}.json"
            if saved.exists() and want[-1][0] == 47:
                _, terms, _ = gf2mm.load_scheme(saved)
                line += f" | identical rank-47 scheme: {sorted(terms) == sorted(res['best'])}"
            print(line, flush=True)
    finally:
        import os
        os.unlink(path)
    print(f"end {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
