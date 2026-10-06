#!/usr/bin/env python3
"""Identity check (research/2026-10-06d_exotic_formats.md, section 4.1): the kernel with --full-reduce 0 follows the
pre-round kernel's trajectories exactly.

"Before" = experiments/2026-10-06d_flipwalk_before.rs, a verbatim copy of search/kernel/flipwalk.rs at the start of
this round (SHA-256 69837abe..., the kernel of research/2026-10-06c_kernel_deadends.md). Both binaries are run on the
same step-limited configurations; the full output (improvements without timings, STATS without seconds, best scheme)
must be identical. The new kernel prints one more STATS field (dep_reductions), which must be 0.

Run from the repository root: ./.venv/Scripts/python experiments/2026-10-06d_fmt_identity.py
RESULT (2026-10-06): printed per case; all identical (see the report).
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
BEFORE_SRC = ROOT / "experiments" / "2026-10-06d_flipwalk_before.rs"
BEFORE_BIN = rust_kernel.BUILD_DIR / ("flipwalk_before6d.exe" if sys.platform == "win32" else "flipwalk_before6d")
subprocess.run(["rustc", "-O", "--edition", "2021", "-o", str(BEFORE_BIN), str(BEFORE_SRC)], check=True)
rust_kernel.build()


def normalise(text, drop_dep):
    out = []
    for line in text.splitlines():
        if line.startswith("IMPROVED "):
            out.append(" ".join(line.split()[:3]))
        elif line.startswith("STATS "):
            kv = [x for x in line.split()[1:] if not x.startswith("seconds=")]
            if drop_dep:
                assert kv[-1] == "dep_reductions=0", kv[-1]
                kv = kv[:-1]
            out.append("STATS " + " ".join(kv))
        else:
            out.append(line)
    return out


cases = []
for fmt, seeds, steps, plateaus in (((2, 2, 2), (1, 2, 3), 200_000, (50, 50_000)),
                                     ((3, 3, 3), (1, 2), 2_000_000, (500, 50_000)),
                                     ((3, 4, 5), (1, 2), 30_000_000, (50_000,)),
                                     ((4, 4, 4), (1, 2), 30_000_000, (50_000,))):
    for seed in seeds:
        for plateau in plateaus:
            cases.append((fmt, seed, steps, plateau))
same = 0
for fmt, seed, steps, plateau in cases:
    path = tempfile.mktemp(suffix=".txt")
    start = gf2mm.standard_scheme(fmt)
    Path(path).write_text(f"{len(start)}\n" + "".join(f"{a} {b} {c}\n" for a, b, c in start))
    args = ["--input", path, "--seed", str(seed), "--max-steps", str(steps), "--max-seconds", "1e9",
            "--plateau", str(plateau)]
    old = subprocess.run([str(BEFORE_BIN)] + args, capture_output=True, text=True, check=True).stdout
    new = subprocess.run([str(rust_kernel.BIN)] + args + ["--full-reduce", "0"], capture_output=True, text=True,
                         check=True).stdout
    Path(path).unlink()
    ok = normalise(old, False) == normalise(new, True)
    same += ok
    print(f"{fmt} seed {seed} steps {steps} plateau {plateau}: {'identical' if ok else 'DIFFERENT'}")
print(f"identical: {same}/{len(cases)}")
