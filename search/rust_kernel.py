"""Run the Rust flip-graph kernel (search/kernel/flipwalk.rs) from Python, safely.

* build(): compiles the single-file kernel with `rustc -O` (no cargo, no dependencies), cached by the
  source's SHA-256; a rebuild happens only when the source changes (about 0.2-0.9 s, RL-051).
* run(): one walk in a separate process at below-normal priority; the result is RE-VERIFIED with the exact
  Python verifier (gf2mm.verify) and a random-matrix check before it is returned.
* run_parallel(): many independent seeds at once (one process each, `workers` at a time).

Nothing produced by the kernel is trusted: a result that fails verification raises KernelResultError.

CLI (from the repository root):
  python -m search.rust_kernel --format 4 4 4 --seeds 1-12 --workers 12 --max-seconds 1800 \\
      --max-weight 4 --best-known 47 --save-dir search/schemes/rust-2026-10-07 --log search/runs/rust.jsonl
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from . import gf2mm
from .experiment import status_label

HERE = Path(__file__).resolve().parent
SRC = HERE / "kernel" / "flipwalk.rs"
BUILD_DIR = HERE / "kernel" / "build"  # gitignored
BIN = BUILD_DIR / ("flipwalk.exe" if os.name == "nt" else "flipwalk")
STAMP = BUILD_DIR / "flipwalk.sha256"
BELOW_NORMAL_PRIORITY_CLASS = 0x00004000


class KernelResultError(RuntimeError):
    """The kernel produced output that does not pass exact verification (never accepted)."""


def rustc_available() -> bool:
    return shutil.which("rustc") is not None


def source_hash() -> str:
    return hashlib.sha256(SRC.read_bytes()).hexdigest()


def build(force: bool = False) -> dict:
    """Compile the kernel if the source changed. Returns {"binary", "rebuilt", "seconds", "rustc"}."""
    BUILD_DIR.mkdir(parents=True, exist_ok=True)
    h = source_hash()
    if not force and BIN.exists() and STAMP.exists() and STAMP.read_text().strip() == h:
        return {"binary": str(BIN), "rebuilt": False, "seconds": 0.0, "source_sha256": h}
    t0 = time.perf_counter()
    proc = subprocess.run(["rustc", "-O", "--edition", "2021", "-o", str(BIN), str(SRC)],
                          capture_output=True, text=True)
    dt = time.perf_counter() - t0
    if proc.returncode != 0:
        raise RuntimeError(f"rustc failed:\n{proc.stderr}")
    STAMP.write_text(h)
    version = subprocess.run(["rustc", "--version"], capture_output=True, text=True).stdout.strip()
    return {"binary": str(BIN), "rebuilt": True, "seconds": round(dt, 3), "source_sha256": h, "rustc": version}


def _write_input(terms) -> str:
    fd, path = tempfile.mkstemp(prefix="flipwalk_", suffix=".txt")
    with os.fdopen(fd, "w", encoding="ascii", newline="\n") as f:
        f.write(f"{len(terms)}\n")
        for a, b, c in terms:
            f.write(f"{a} {b} {c}\n")
    return path


def _command(input_path, seed, max_steps, max_seconds, plateau, slack, max_weight, target_rank):
    return [str(BIN), "--input", input_path, "--seed", str(seed), "--max-steps", str(max_steps),
            "--max-seconds", str(max_seconds), "--plateau", str(plateau), "--slack", str(slack),
            "--max-weight", str(max_weight), "--target-rank", str(target_rank)]


def _popen(cmd):
    kwargs = {"stdout": subprocess.PIPE, "stderr": subprocess.PIPE, "text": True}
    if os.name == "nt":
        kwargs["creationflags"] = BELOW_NORMAL_PRIORITY_CLASS
    else:
        kwargs["preexec_fn"] = lambda: os.nice(10)
    return subprocess.Popen(cmd, **kwargs)


def parse_output(text: str) -> dict:
    improvements, best, stats, expect = [], [], {}, None
    lines = text.splitlines()
    k = 0
    while k < len(lines):
        line = lines[k]
        if line.startswith("IMPROVED "):
            _, rank, step, secs = line.split()
            improvements.append((int(rank), int(step), float(secs)))
        elif line.startswith("STATS "):
            stats = {kv.split("=")[0]: float(kv.split("=")[1]) for kv in line.split()[1:]}
        elif line.startswith("BEST "):
            expect = int(line.split()[1])
            best = [tuple(int(x) for x in ln.split()) for ln in lines[k + 1:k + 1 + expect]]
            k += expect
        k += 1
    if expect is None or len(best) != expect:
        raise KernelResultError("kernel output incomplete")
    return {"improvements": improvements, "best": best, "stats": stats}


def check_result(fmt, terms, seed: int) -> None:
    """Exact verification of a kernel result. Raises KernelResultError on any failure."""
    try:
        gf2mm.check_factor_ranges(fmt, terms)
    except Exception as e:  # noqa: BLE001
        raise KernelResultError(f"factor out of range: {e}") from e
    if not gf2mm.verify(fmt, terms):
        raise KernelResultError("scheme fails the exact Brent-equation verifier")
    if not gf2mm.random_check(fmt, terms, trials=8, seed=seed):
        raise KernelResultError("scheme fails the random-matrix check")


def run(fmt, start, seed=1, max_steps=10**9, max_seconds=60.0, plateau=50_000, slack=3, max_weight=0,
        target_rank=0) -> dict:
    fmt = tuple(fmt)
    if max(gf2mm.dims(fmt)) > 64:
        raise ValueError("the kernel stores factors in u64: each factor must have at most 64 bits")
    build()
    path = _write_input(start)
    try:
        t0 = time.perf_counter()
        proc = _popen(_command(path, seed, max_steps, max_seconds, plateau, slack, max_weight, target_rank))
        out, err = proc.communicate()
        wall = time.perf_counter() - t0
    finally:
        os.unlink(path)
    if proc.returncode != 0:
        raise KernelResultError(f"kernel exited with {proc.returncode}: {err.strip()}")
    res = parse_output(out)
    check_result(fmt, res["best"], seed)
    res.update(seed=seed, wall_seconds=round(wall, 3), verified=True, format=fmt)
    return res


def run_parallel(fmt, start, seeds, workers, **kw) -> list[dict]:
    """Independent walks, `workers` processes at a time. Every result is verified as in run()."""
    fmt = tuple(fmt)
    build()
    pending = list(seeds)
    active, results = [], []
    path = _write_input(start)
    try:
        while pending or active:
            while pending and len(active) < workers:
                seed = pending.pop(0)
                cmd = _command(path, seed, kw.get("max_steps", 10**12), kw.get("max_seconds", 60.0),
                               kw.get("plateau", 50_000), kw.get("slack", 3), kw.get("max_weight", 0),
                               kw.get("target_rank", 0))
                active.append((seed, time.perf_counter(), _popen(cmd)))
            still = []
            for seed, t0, proc in active:
                if proc.poll() is None:
                    still.append((seed, t0, proc))
                    continue
                out, err = proc.communicate()
                entry = {"seed": seed, "wall_seconds": round(time.perf_counter() - t0, 3), "format": fmt}
                if proc.returncode != 0:
                    entry.update(error=f"exit {proc.returncode}: {err.strip()}")
                else:
                    try:
                        res = parse_output(out)
                        check_result(fmt, res["best"], seed)
                        entry.update(res, verified=True)
                    except KernelResultError as e:
                        entry.update(error=str(e), verified=False)
                results.append(entry)
            active = still
            if active:
                time.sleep(0.5)
    finally:
        os.unlink(path)
    return sorted(results, key=lambda e: e["seed"])


def _parse_seeds(spec: str) -> list[int]:
    out = []
    for part in spec.split(","):
        if "-" in part:
            lo, hi = part.split("-")
            out.extend(range(int(lo), int(hi) + 1))
        else:
            out.append(int(part))
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--format", nargs=3, type=int, required=True)
    ap.add_argument("--start", help="scheme JSON to start from (default: the standard algorithm)")
    ap.add_argument("--seeds", default="1")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--max-seconds", type=float, default=60.0)
    ap.add_argument("--max-steps", type=int, default=10**12)
    ap.add_argument("--plateau", type=int, default=50_000)
    ap.add_argument("--slack", type=int, default=3)
    ap.add_argument("--max-weight", type=int, default=0)
    ap.add_argument("--target-rank", type=int, default=0)
    ap.add_argument("--best-known", type=int)
    ap.add_argument("--save-dir")
    ap.add_argument("--log", help="append one JSON line per walk")
    args = ap.parse_args(argv)
    fmt = tuple(args.format)
    start = gf2mm.load_scheme(args.start)[1] if args.start else gf2mm.standard_scheme(fmt)
    info = build()
    print(json.dumps({"build": info}))
    results = run_parallel(fmt, start, _parse_seeds(args.seeds), args.workers, max_seconds=args.max_seconds,
                           max_steps=args.max_steps, plateau=args.plateau, slack=args.slack,
                           max_weight=args.max_weight, target_rank=args.target_rank)
    env = {"python": platform.python_version(), "platform": platform.platform(), "cpus": os.cpu_count(),
           "kernel_sha256": info["source_sha256"]}
    for res in results:
        summary = {k: v for k, v in res.items() if k != "best"}
        summary["best_rank"] = len(res["best"]) if "best" in res else None
        summary.update(start=args.start or "standard", params=vars(args), environment=env)
        print(json.dumps(summary, default=str))
        if args.log:
            Path(args.log).parent.mkdir(parents=True, exist_ok=True)
            with open(args.log, "a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(summary, default=str) + "\n")
        if args.save_dir and res.get("verified"):
            os.makedirs(args.save_dir, exist_ok=True)
            r = len(res["best"])
            p = os.path.join(args.save_dir, f"{fmt[0]}x{fmt[1]}x{fmt[2]}_rank{r}_seed{res['seed']}.json")
            gf2mm.save_scheme(p, fmt, res["best"], status=status_label(r, args.best_known),
                              best_known_rank=args.best_known,
                              provenance={"kernel": "search/kernel/flipwalk.rs", "kernel_sha256": info["source_sha256"],
                                          "seed": res["seed"], "stats": res.get("stats"),
                                          "improvements": res.get("improvements"), "environment": env})
    bad = [r for r in results if not r.get("verified")]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
