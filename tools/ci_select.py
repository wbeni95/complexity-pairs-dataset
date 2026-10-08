#!/usr/bin/env python3
"""Choose what CI checks for a push or pull request: everything, or only what the change can affect.

Full run (every check) when:
  - the event is the weekly schedule, a manual run or a release tag;
  - the base commit is unknown (a new branch, a force push, a shallow history), or git is not available;
  - a changed path is shared code or configuration (tools/, schema/, lib/, methods/, search/, generators/,
    mutations/, tests/ helpers, requirements.txt, .github/, ...), an experiments/ file that no proof and no listed
    check names, or any path this script does not know;
  - an item folder was removed or renamed, or an item's entry.json / meta.json cannot be read.
Otherwise the run is selective:
  - affected entries (V1 runs, V2 re-measurement, replay): every entry or theorem note with a changed file in its
    folder, and every item whose proof, implementation or test harness names a changed file (code may live in another
    item's folder);
  - extra replays: for every check file (proof.checks) that reads a changed file -- it names the slug of the item
    folder the file is in, or the file name of a helper it loads -- one item that lists the check is replayed too;
  - the unit tests always run in full (several tests read items or files they do not name), the schema and folder
    rules (validate.py --static) and the generated-files check (build_index.py --check) always run.

  python tools/ci_select.py --event push --ref refs/heads/main --base <sha> --head <sha>
  python tools/ci_select.py --files README.md pairs/x/entry.json      # explain a selection for given paths

Output: lines key=value for $GITHUB_OUTPUT (mode, entries, slugs, sources), then a readable summary on stderr.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ITEM_DIRS = ("pairs", "staging", "synthetic", "theorems")
ENTRY_DIRS = ("pairs", "staging", "synthetic")
HELPER_DIRS = ("experiments", "tests")  # where check files load sibling helpers from
DOC_PREFIXES = ("notes/", "research/", "docs/", "ledger/", "candidates/", "results/")
DOC_FILES = {"README.md", "RESEARCH_LOG.md", "CONTRIBUTING.md", "REPRODUCING.md", "START_HERE.txt", "CITATION.cff",
             "NOTICE", "LICENSE", "LICENSE-DATA", "index.json", "theorems/README.md", ".gitignore"}
FULL_EVENTS = {"schedule", "workflow_dispatch"}


def _rel(repo: Path, p: Path) -> str | None:
    try:
        return p.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return None


def items(repo: Path = REPO) -> dict[str, dict]:
    """Every item folder: {"<dir>/<slug>": {"slug", "kind", "files", "checks", "marked"}}.
    files = repo paths named by the proof, the implementations and the test harness; checks = the .py files of
    proof.checks; marked = it has a proof field (it carries the check mark). Raises on an unreadable file."""
    out = {}
    for d in ITEM_DIRS:
        name = "meta.json" if d == "theorems" else "entry.json"
        for f in sorted((repo / d).glob(f"*/{name}")):
            folder = f.parent
            data = json.loads(f.read_text(encoding="utf-8"))
            proof = data.get("proof") or {}
            refs = list(proof.get("documents", [])) + list(proof.get("checks", []))
            refs += [a["implementation"].rsplit(":", 1)[0] for a in data.get("algorithms", []) if a.get("implementation")]
            if (data.get("test_harness") or {}).get("module"):
                refs.append(data["test_harness"]["module"])
            files = {r for r in (_rel(repo, folder / x) for x in refs) if r}
            checks = {r for r in (_rel(repo, folder / x) for x in proof.get("checks", [])) if r and r.endswith(".py")}
            out[f"{d}/{folder.name}"] = {"slug": folder.name, "kind": "entry" if d in ENTRY_DIRS else "theorem",
                                         "files": files, "checks": checks, "marked": bool(proof)}
    return out


def check_reads(known: dict[str, dict], repo: Path = REPO) -> dict[str, set[str]]:
    """{check file: the item folders and helper files it reads}, from its text: every item slug it names, every
    experiments/ or tests/ file whose name (or module name) it names; closed transitively over helpers."""
    folder_of = {it["slug"]: f for f, it in known.items()}
    slug_re = re.compile("|".join(re.escape(s) for s in sorted(folder_of, key=len, reverse=True)))
    helpers = {}
    for d in HELPER_DIRS:
        for p in (repo / d).glob("*.py"):
            rel = p.relative_to(repo).as_posix()
            helpers[p.name] = rel
            if d == "tests":
                helpers[p.stem] = rel  # imported by module name
    helper_re = re.compile(r"(?<![\w.-])(" + "|".join(re.escape(n) for n in sorted(helpers, key=len, reverse=True)) + r")(?![\w-])")

    def direct(rel: str) -> set[str]:
        p = repo / rel
        if not p.is_file():
            return set()
        text = p.read_text(encoding="utf-8", errors="replace")
        return {folder_of[s] for s in slug_re.findall(text)} | {helpers[n] for n in helper_re.findall(text)} - {rel}

    all_checks = {c for it in known.values() for c in it["checks"]}
    cache: dict[str, set[str]] = {}
    for c in all_checks:
        seen, todo = set(), [c]
        while todo:
            x = todo.pop()
            for y in cache.setdefault(x, direct(x)):
                if y not in seen:
                    seen.add(y)
                    if y.endswith(".py"):
                        todo.append(y)
        cache[c] = seen
    return {c: cache[c] for c in all_checks}


def _under(path: str, dep: str) -> bool:
    return path == dep or path.startswith(dep + "/")


def classify(path: str, named: set[str], read: set[str]) -> str:
    """'item', 'test', 'check' (a file some proof or check names), 'doc' or 'shared' for one changed path."""
    parts = path.split("/")
    if parts[0] in ITEM_DIRS and len(parts) >= 3:
        return "item"
    if parts[0] == "tests" and len(parts) == 2 and re.fullmatch(r"test_\w+\.py", parts[1]):
        return "test"  # the unit tests always run in full; a proof that names it selects its item below
    if parts[0] == "experiments" and (path in named or path in read):
        return "check"
    if path in DOC_FILES or path.startswith(DOC_PREFIXES):
        return "doc"
    return "shared"  # tools/, schema/, lib/, ..., unnamed experiments/, tests/ helpers, unknown paths


def _full(reasons: list[str]) -> dict:
    return {"mode": "full", "entries": [], "slugs": [], "sources": True, "reasons": reasons}


def select(changed: list[str], repo: Path = REPO) -> dict:
    """The selection for a list of changed paths (repo-relative, forward slashes)."""
    try:
        known = items(repo)
        reads = check_reads(known, repo)
    except (OSError, ValueError, TypeError, AttributeError, KeyError) as e:  # JSONDecodeError is a ValueError
        return _full([f"cannot read the items ({type(e).__name__}: {e}); validate.py reports it"])
    named = {p for it in known.values() for p in it["files"]}
    read = {p for deps in reads.values() for p in deps}
    reasons, affected = [], set()
    for path in changed:
        kind = classify(path, named, read)
        if kind == "shared":
            return _full([f"shared or unknown path: {path}"])
        if kind == "item":
            folder = "/".join(path.split("/")[:2])
            if folder not in known:
                return _full([f"item folder removed, renamed or incomplete: {folder}"])
            affected.add(folder)
        affected |= {f for f, it in known.items() if path in it["files"]}
    # checks that read a changed path but would not run: replay one item that lists each of them
    extra = set()
    for _ in range(len(known)):
        running = {c for f in affected | extra for c in known[f]["checks"]}
        missing = sorted(c for c, deps in reads.items() if c not in running
                         and not c.startswith("tests/")  # the unit tests run in full in the validate job
                         and any(_under(p, d) for p in changed for d in deps))
        if not missing:
            break
        for c in missing:
            lister = min(f for f, it in known.items() if c in it["checks"])
            extra.add(lister)
            reasons.append(f"{c} reads a changed file: replay {known[lister]['slug']}")
    entries = sorted(a for a in affected if known[a]["kind"] == "entry")
    slugs = sorted({known[a]["slug"] for a in affected | extra if known[a]["marked"]})
    return {"mode": "items" if affected | extra else "docs", "entries": entries, "slugs": slugs,
            "sources": bool(affected), "reasons": reasons}


def changed_files(base: str, head: str) -> list[str] | None:
    """Paths changed between base and head, or None when the base commit (or git) is not available."""
    if not base or set(base) == {"0"}:
        return None
    try:
        if subprocess.run(["git", "cat-file", "-e", f"{base}^{{commit}}"], cwd=REPO, capture_output=True).returncode:
            return None
        out = subprocess.run(["git", "diff", "--name-only", "--no-renames", "-z", base, head],  # -z: paths unquoted
                             cwd=REPO, capture_output=True, check=True).stdout
    except (OSError, subprocess.CalledProcessError):
        return None
    return [p for p in out.decode("utf-8", errors="surrogateescape").split("\0") if p]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--event", default="push")
    ap.add_argument("--ref", default="")
    ap.add_argument("--base", default="")
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--files", nargs="*", help="select for these paths instead of a git diff")
    a = ap.parse_args(argv)
    if a.files is not None:
        sel = select([p.replace("\\", "/") for p in a.files])
    elif a.event in FULL_EVENTS or a.ref.startswith("refs/tags/"):
        sel = _full([f"event {a.event} {a.ref}".strip()])
    else:
        files = changed_files(a.base, a.head)
        sel = select(files) if files is not None else _full([f"base commit {a.base or '(none)'} not available"])
    print(f"mode={sel['mode']}")
    print(f"entries={' '.join(sel['entries'])}")
    print(f"slugs={' '.join(sel['slugs'])}")
    print(f"sources={'true' if sel['sources'] else 'false'}")
    print(f"selection: {sel['mode']}; {len(sel['entries'])} entries, {len(sel['slugs'])} marked items to replay"
          + "".join(f"\n  {r}" for r in sel["reasons"]), file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
