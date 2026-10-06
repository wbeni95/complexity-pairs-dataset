#!/usr/bin/env python3
"""Diagnostic (research/2026-10-06d_exotic_formats.md, section 6): why did the (2,5,6) walks not improve at all?

(a) Identity: the pre-round kernel (experiments/2026-10-06d_flipwalk_before.rs) and the current kernel with
    --full-reduce 0 on (2,5,6) from the standard algorithm, seeds 1001-1002, 2*10^8 steps each: identical output means
    the stall is a property of the walk policy, not of this round's change.
(b) Variants, 4 walks x 30 s each (seeds 5001-5004), from the standard algorithm: the format in another orientation,
    (6,2,5) (same tensor up to the cyclic symmetry), and (2,5,6) with plateau 2 000 and slack 1. Every result is
    re-verified by the exact verifier (search/rust_kernel.py).

Run from the repository root: ./.venv/Scripts/python experiments/2026-10-06d_fmt_256_probe.py
RESULT: printed; console copy search/runs/2026-10-06d_256_probe.console.txt.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, rust_kernel  # noqa: E402
from search.machine import set_below_normal_priority  # noqa: E402

set_below_normal_priority()
BEFORE_BIN = rust_kernel.BUILD_DIR / ("flipwalk_before6d.exe" if sys.platform == "win32" else "flipwalk_before6d")
subprocess.run(["rustc", "-O", "--edition", "2021", "-o", str(BEFORE_BIN),
                str(ROOT / "experiments" / "2026-10-06d_flipwalk_before.rs")], check=True)
rust_kernel.build()


def norm(text):
    out = []
    for line in text.splitlines():
        if line.startswith("IMPROVED "):
            out.append(" ".join(line.split()[:3]))
        elif line.startswith("STATS "):
            out.append(" ".join(x for x in line.split() if not x.startswith(("seconds=", "dep_reductions="))))
        else:
            out.append(line)
    return out


start = gf2mm.standard_scheme((2, 5, 6))
path = tempfile.mktemp(suffix=".txt")
Path(path).write_text(f"{len(start)}\n" + "".join(f"{a} {b} {c}\n" for a, b, c in start))
for seed in (1001, 1002):
    args = ["--input", path, "--seed", str(seed), "--max-steps", "200000000", "--max-seconds", "1e9"]
    old = subprocess.run([str(BEFORE_BIN)] + args, capture_output=True, text=True, check=True,
                         creationflags=0x4000 if sys.platform == "win32" else 0).stdout
    new = subprocess.run([str(rust_kernel.BIN)] + args + ["--full-reduce", "0"], capture_output=True, text=True,
                         check=True, creationflags=0x4000 if sys.platform == "win32" else 0).stdout
    stats = [line for line in new.splitlines() if line.startswith(("STATS", "BEST"))]
    print(f"(a) (2,5,6) seed {seed}, 2e8 steps: identical {norm(old) == norm(new)}; {stats}")
Path(path).unlink()

for label, fmt, kw in (("(6,2,5) orientation", (6, 2, 5), {}),
                       ("(2,5,6) plateau 2000 slack 1", (2, 5, 6), {"plateau": 2000, "slack": 1})):
    res = rust_kernel.run_parallel(fmt, gf2mm.standard_scheme(fmt), [5001, 5002, 5003, 5004], 4, max_seconds=30, **kw)
    print(f"(b) {label}: best ranks {[len(r['best']) for r in res]}; verified {[r.get('verified') for r in res]}; "
          f"first improvements {[r['improvements'][:2] for r in res]}")
