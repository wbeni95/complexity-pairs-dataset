#!/usr/bin/env python3
"""Replay the checks behind every item that carries the check mark (✅ Proved), deterministically.

For each entry (pairs/, synthetic/) and theorem note (theorems/) with a `proof` field, this runs:
  - for entries: the V1 correctness runs, `python tools/validate.py <entry>` (seeded, deterministic);
  - every file named in `proof.checks`: a tests/test_*.py file as a unittest module, any other .py file as a script,
    always from the repository root.
Each distinct command runs once, and its result counts for every item that lists it. The written proofs are in the
files named in `proof.documents`; this tool re-runs the computations they rely on. Timing fits are measurements, not
proofs, and are not replayed here (`python tools/check_all.py` runs them; see REPRODUCING.md).

  python tools/replay_proofs.py              # every marked item
  python tools/replay_proofs.py SLUG ...     # only these items (folder names)
  python tools/replay_proofs.py --list       # print the commands without running them

Every command runs with PYTHONHASHSEED=0. A command passes only if it exits 0 AND its output (stdout and stderr) has
no line starting with "[FAIL]" (the prefix every check script gives a failed check); a command that exits 0 with such
a line is reported as "FAIL (output contains [FAIL] lines)". Exit code 0 only if every command passes.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def marked_items() -> list[dict]:
    """Every entry or theorem note with a `proof` field: {"slug", "path", "kind", "proof"}."""
    items = []
    for loc in ("pairs", "synthetic", "staging"):
        for f in sorted((REPO / loc).glob("*/entry.json")):
            proof = json.loads(f.read_text(encoding="utf-8")).get("proof")
            if proof:
                items.append({"slug": f.parent.name, "path": f.parent, "kind": "entry", "proof": proof})
    for f in sorted((REPO / "theorems").glob("*/meta.json")):
        proof = json.loads(f.read_text(encoding="utf-8")).get("proof")
        if proof:
            items.append({"slug": f.parent.name, "path": f.parent, "kind": "theorem", "proof": proof})
    return items


def command_for(check_file: Path) -> tuple[str, ...]:
    """The command (run from the repository root) that executes one listed check file."""
    rel = check_file.resolve().relative_to(REPO)
    if rel.parts[0] == "tests" and rel.name.startswith("test_") and rel.suffix == ".py":
        return ("-m", "unittest", ".".join(rel.with_suffix("").parts))
    return (rel.as_posix(),)


FAIL_PREFIX = "[FAIL]"


def fail_lines(output: str) -> list[str]:
    """The lines of a command's output that start with [FAIL] (a failed check reported by a check script)."""
    return [line for line in output.splitlines() if line.startswith(FAIL_PREFIX)]


def verdict(returncode: int, output: str) -> tuple[bool, str]:
    """(passed, reason). A command passes only if it exits 0 and prints no line starting with [FAIL]."""
    if returncode != 0:
        return False, f"FAIL (exit code {returncode})"
    if fail_lines(output):
        return False, "FAIL (output contains [FAIL] lines)"
    return True, "PASS"


def commands_for(item: dict) -> list[tuple[str, ...]]:
    cmds = []
    if item["kind"] == "entry":
        cmds.append(("tools/validate.py", item["path"].relative_to(REPO).as_posix()))
    for rel in item["proof"].get("checks", []):
        cmds.append(command_for(item["path"] / rel))
    return cmds


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("slugs", nargs="*", help="replay only these items (folder names)")
    ap.add_argument("--list", action="store_true", help="print the commands and exit")
    args = ap.parse_args(argv)

    items = marked_items()
    if args.slugs:
        unknown = set(args.slugs) - {it["slug"] for it in items}
        if unknown:
            print(f"not marked or not found: {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        items = [it for it in items if it["slug"] in args.slugs]
    if not items:
        print("no item carries the check mark yet")
        return 0

    plan: dict[tuple[str, ...], list[str]] = {}
    for it in items:
        for cmd in commands_for(it):
            plan.setdefault(cmd, []).append(it["slug"])
    if args.list:
        for cmd, slugs in plan.items():
            print(f"python {' '.join(cmd)}    # {len(slugs)} item(s): {', '.join(slugs[:4])}{' ...' if len(slugs) > 4 else ''}")
        return 0

    env = dict(os.environ, PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1")
    failed_cmds = set()
    for i, cmd in enumerate(plan, 1):
        t0 = time.perf_counter()
        res = subprocess.run([sys.executable, *cmd], cwd=REPO, env=env, capture_output=True, text=True,
                             encoding="utf-8", errors="replace")
        output = res.stdout + res.stderr
        ok, reason = verdict(res.returncode, output)
        print(f"[{'PASS' if ok else 'FAIL'}] ({i}/{len(plan)}) python {' '.join(cmd)}  [{time.perf_counter() - t0:.1f}s]"
              + ("" if ok else f"  {reason}"), flush=True)
        if not ok:
            failed_cmds.add(cmd)
            shown = fail_lines(output)[:15] if res.returncode == 0 else output.strip().splitlines()[-15:]
            print("    " + "\n    ".join(shown))

    bad_items = sorted({slug for cmd in failed_cmds for slug in plan[cmd]})
    print(f"\n{len(plan) - len(failed_cmds)}/{len(plan)} commands passed; "
          f"{len(items) - len(bad_items)}/{len(items)} items fully replayed")
    if bad_items:
        print("items with a failing check: " + ", ".join(bad_items))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
