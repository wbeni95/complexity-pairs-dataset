#!/usr/bin/env python3
"""Run every repository check in one go and print a summary.

Steps (in order):
  1. validator self-tests      python -m unittest discover -s tests
  2. validation                python tools/validate.py --scaling [--record]
  3. index freshness           python tools/build_index.py --check
     chart freshness           python tools/make_charts.py --check
  4. citations (optional)      python tools/check_sources.py        (network)

Usage:
  python tools/check_all.py                    # steps 1-3
  python tools/check_all.py --record           # also store the validation run in ledger/runs/
  python tools/check_all.py --sources          # also check every DOI / arXiv id online
  python tools/check_all.py --quick            # no scaling measurements (fast)
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--record", action="store_true", help="pass --record to the validator")
    ap.add_argument("--sources", action="store_true", help="also run the online citation check")
    ap.add_argument("--quick", action="store_true", help="skip scaling measurements")
    args = ap.parse_args(argv)

    py = sys.executable
    validate = [py, "tools/validate.py"] + ([] if args.quick else ["--scaling"]) + (["--record"] if args.record else [])
    steps = [
        ("unit tests", [py, "-m", "unittest", "discover", "-s", "tests"]),
        ("validation" + ("" if args.quick else " + scaling"), validate),
        ("index freshness", [py, "tools/build_index.py", "--check"]),
        ("chart freshness", [py, "tools/make_charts.py", "--check"]),
    ]
    if args.sources:
        steps.append(("citations", [py, "tools/check_sources.py"]))

    results = []
    for name, cmd in steps:
        print(f"\n=== {name}: {' '.join(Path(c).name if i == 0 else c for i, c in enumerate(cmd))}", flush=True)
        t0 = time.perf_counter()
        code = subprocess.run(cmd, cwd=REPO).returncode
        results.append((name, code, time.perf_counter() - t0))

    print("\n=== summary")
    for name, code, dt in results:
        print(f"  {'OK  ' if code == 0 else 'FAIL'}  {name:28s} {dt:6.1f} s")
    return 0 if all(code == 0 for _, code, _ in results) else 1


if __name__ == "__main__":
    sys.exit(main())
