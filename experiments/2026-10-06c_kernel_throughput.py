"""Experiment (research/2026-10-06c_kernel_deadends.md): does the dead-end change of search/kernel/flipwalk.rs keep
the old behaviour when switched off, and what does it do to throughput?

Kernels compared (all built here with `rustc -O --edition 2021`, no other flags):
  before   experiments/2026-10-06c_flipwalk_before.rs, a verbatim copy of the kernel before this round
           (sha256 6f306293...ad644, the kernel that produced the RL-054 and RL-059 runs; see their logs);
  off      search/kernel/flipwalk.rs with --dead-end 0;
  on       search/kernel/flipwalk.rs with --dead-end 1 (the new default).

Part 1, identity (deterministic): step-limited walks (no time cut-off) of `before` and `off` must give identical
output apart from the timing fields and the new dead_ends counter: same best scheme, steps, flips, rejected,
plus transitions, restarts and improvement history (rank, step). Cases: 2x2x2, 3x3x3, 4x4x4 from the standard
algorithm and 4x4x4 from Strassen (x) Strassen, several seeds and plateaus.

Part 2, throughput (timing; run with nothing else CPU-heavy on the machine): 8 walk processes at a time, below-normal
priority, seeds 701-708, no weight cap, plateau 50 000, slack 3 (the RL-059 settings):
  (a) 4x4x4 from the standard algorithm, 45 s per walk, for each of before / off / on;
  (b) 4x4x4 from Strassen (x) Strassen (a dead end from step 1), 20 s per walk, for each of before / off / on.
Per walk: steps/s, flips/s, plus transitions/s, restarts, dead-end detections/s, best rank, first time at 49.
Every result is re-verified with the exact verifier (rust_kernel.check_result) before it is logged.
Log: search/runs/2026-10-06c_throughput.jsonl (one line per walk).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_kernel_throughput.py

RESULT (2026-10-06, 11:40:49-11:44:17; console copy search/runs/2026-10-06c_throughput.console.txt):
  identity: 17/17 cases identical (before vs new --dead-end 0).
  Medians over 8 walks (steps/s | flips/s | plus transitions/s):
    standard, 45 s:   before 1.493e7 | 2.147e6 | 290    off 1.463e7 | 2.128e6 | 284    on 1.403e7 | 2.092e6 | 272
    S(x)S, 20 s:      before 2.243e7 | 1.907e4 | 440    off 2.276e7 | 1.928e4 | 446    on 1.575e7 | 9.405e5 | 22 000
  At the dead end (S(x)S start) the escape gives 49x more flips/s and 50x more plus transitions/s; steps/s falls
  by 30% because steps now do work. On identical trajectories (seeds 702-708 never met a dead end) steps/s was
  off/before 0.981 and on/off 0.964 (medians; experiments/2026-10-06c_paired_overhead.py): about 5% overhead in
  total, with machine drift not separated (the groups ran one after the other). Seed 707 with the old kernel (and
  identically with off) reached rank 47 at 43.6 s (43.97 s for off). With the escape on, the same seed had 0
  detections, i.e. the same trajectory, but at 1.372e7 steps/s it reached only step 6.17e8 of the 6.29e8 needed
  within 45 s, so it ended at 50. CORRECTED here: a first note said "different trajectory". The improvement
  history and scheme were not logged here; experiments/2026-10-06c_reproduce_before_seed707.py reproduces them.
"""
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, rust_kernel as rk  # noqa: E402

BEFORE_SRC = ROOT / "experiments" / "2026-10-06c_flipwalk_before.rs"
BEFORE_BIN = rk.BUILD_DIR / ("flipwalk_before.exe" if os.name == "nt" else "flipwalk_before")
LOG = ROOT / "search" / "runs" / "2026-10-06c_throughput.jsonl"
SEEDS = list(range(701, 709))


def build_before():
    rk.BUILD_DIR.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(["rustc", "-O", "--edition", "2021", "-o", str(BEFORE_BIN), str(BEFORE_SRC)],
                       capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(p.stderr)


def command(kind, path, seed, max_steps, max_seconds, plateau, slack=3):
    base = [str(BEFORE_BIN if kind == "before" else rk.BIN), "--input", path, "--seed", str(seed),
            "--max-steps", str(max_steps), "--max-seconds", str(max_seconds), "--plateau", str(plateau),
            "--slack", str(slack), "--max-weight", "0", "--target-rank", "0"]
    if kind != "before":
        base += ["--dead-end", "1" if kind == "on" else "0"]
    return base


def strip(res):
    st = res["stats"]
    return ([tuple(t) for t in res["best"]], [(r, s) for r, s, _ in res["improvements"]],
            {k: int(st[k]) for k in ("steps", "flips", "rejected_weight", "plus", "restarts")})


def identity_checks():
    _, ss = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), (2, 2, 2), gf2mm.strassen_scheme())
    cases = [((2, 2, 2), gf2mm.standard_scheme((2, 2, 2)), "standard", s, 200_000, pl) for s in (1, 2, 3) for pl in (50, 50_000)]
    cases += [((3, 3, 3), gf2mm.standard_scheme((3, 3, 3)), "standard", s, 2_000_000, pl) for s in (1, 2) for pl in (500, 50_000)]
    cases += [((4, 4, 4), gf2mm.standard_scheme((4, 4, 4)), "standard", s, 30_000_000, 50_000) for s in (1, 2, 3)]
    cases += [((4, 4, 4), ss, "strassen_squared", s, 5_000_000, pl) for s in (1, 2) for pl in (5_000, 50_000)]
    ok = 0
    for fmt, start, name, seed, steps, plateau in cases:
        path = rk._write_input(start)
        try:
            outs = {}
            for kind in ("before", "off"):
                p = subprocess.run(command(kind, path, seed, steps, 1e9, plateau), capture_output=True, text=True)
                assert p.returncode == 0, p.stderr
                res = rk.parse_output(p.stdout)
                rk.check_result(fmt, res["best"], seed)
                outs[kind] = res
        finally:
            os.unlink(path)
        same = strip(outs["before"]) == strip(outs["off"]) and int(outs["off"]["stats"]["dead_ends"]) == 0
        ok += same
        b = strip(outs["before"])
        print(f"identity {fmt} {name} seed {seed} steps {steps} plateau {plateau}: "
              f"{'IDENTICAL' if same else 'DIFFERENT'} (best rank {len(b[0])}, flips {b[2]['flips']}, "
              f"plus {b[2]['plus']}, restarts {b[2]['restarts']})", flush=True)
    print(f"identity: {ok}/{len(cases)} cases identical", flush=True)
    return ok == len(cases)


def throughput(label, fmt, start, kind, max_seconds):
    path = rk._write_input(start)
    procs = []
    try:
        t0 = time.perf_counter()
        for seed in SEEDS:  # 8 processes at once
            procs.append((seed, rk._popen(command(kind, path, seed, 10**15, max_seconds, 50_000))))
        rows = []
        for seed, proc in procs:
            out, err = proc.communicate()
            assert proc.returncode == 0, err
            res = rk.parse_output(out)
            rk.check_result(fmt, res["best"], seed)
            st = res["stats"]
            first49 = next((s for r, _, s in res["improvements"] if r <= 49), None)
            row = {"experiment": "2026-10-06c_kernel_throughput", "start": label, "kernel": kind, "seed": seed,
                   "max_seconds": max_seconds, "best_rank": len(res["best"]), "verified": True,
                   "first_49_seconds": first49, "stats": st,
                   "steps_per_s": st["steps"] / st["seconds"], "flips_per_s": st["flips"] / st["seconds"],
                   "plus_per_s": st["plus"] / st["seconds"], "dead_ends_per_s": st.get("dead_ends", 0) / st["seconds"],
                   "kernel_sha256": rk.source_hash() if kind != "before" else
                   __import__("hashlib").sha256(BEFORE_SRC.read_bytes()).hexdigest()}
            rows.append(row)
            with open(LOG, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(row) + "\n")
        wall = time.perf_counter() - t0
    finally:
        os.unlink(path)
    med = {k: statistics.median(r[k] for r in rows) for k in ("steps_per_s", "flips_per_s", "plus_per_s", "dead_ends_per_s")}
    print(f"{label:17s} {kind:6s} {max_seconds:4.0f}s x8 (wall {wall:.1f}s): median steps/s {med['steps_per_s']:.3e}  "
          f"flips/s {med['flips_per_s']:.3e}  plus/s {med['plus_per_s']:.3e}  dead-ends/s {med['dead_ends_per_s']:.3e}  "
          f"best ranks {sorted(r['best_rank'] for r in rows)}  first 49 (s) "
          f"{[None if r['first_49_seconds'] is None else round(r['first_49_seconds'], 1) for r in rows]}", flush=True)
    return rows


if __name__ == "__main__":
    print(f"start {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    build_before()
    print(f"build new: {rk.build()}", flush=True)
    if not identity_checks():
        print("IDENTITY FAILED: the throughput comparison is not meaningful", flush=True)
    _, ss = gf2mm.kron_scheme((2, 2, 2), gf2mm.strassen_scheme(), (2, 2, 2), gf2mm.strassen_scheme())
    for label, start, secs in (("standard", gf2mm.standard_scheme((4, 4, 4)), 45.0), ("strassen_squared", ss, 20.0)):
        for kind in ("before", "off", "on"):
            throughput(label, (4, 4, 4), start, kind, secs)
    print(f"end {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
