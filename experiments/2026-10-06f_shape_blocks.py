#!/usr/bin/env python3
"""The shape blocks added to existing entries in round 2026-10-06f, and the tool that inserted them.

Each block is inserted as ONE new line (`"shape": {...}`) at the end of the algorithm's harness.scaling object;
nothing else in entry.json changes. --check verifies, for every listed (entry, algorithm), that the parsed entry
equals the parsed entry without the block plus exactly this block, and that the file differs from its git HEAD
version only by added lines (needs git; skipped if unavailable).

Grid choices (evidence: experiments/2026-10-06f_shape_survey.py and the per-entry validator runs listed in
research/2026-10-06f_shape_diagnostic.md):
  * polynomial and exponential counts: consecutive n from the smallest n the harness accepts, with a few more
    terms than the guessed recurrence needs (order L needs 2L + 2 + 4 terms);
  * counts with a log factor or an irrational power of n: doubling n = 2^k from the first n where the count is
    regular (Karatsuba and Strassen: their schoolbook cutoffs, 32 and 16);
  * instance-dependent counts (sorting-based steps, random queries): a small doubling grid, kept so that the ledger
    records WHY the diagnostic cannot decide (the probe fails at small n, so the grid is never counted).

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06f_shape_blocks.py --check
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06f_shape_blocks.py --apply   # idempotent
"""
from __future__ import annotations

import argparse
import copy
import difflib
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

C = "consecutive"
D = "doubling"
INSTANCE = "count depends on the drawn instance; kept so the record says why the diagnostic cannot decide"

# (entry id, algorithm name prefix) -> block
BLOCKS: dict[tuple[str, str], dict] = {
    ("all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall", "Bellman-Ford"): {"sequence": C, "n_range": [1, 20]},
    ("all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall", "Floyd-Warshall"): {"sequence": C, "n_range": [1, 20]},
    ("bernstein-vazirani-classical-vs-quantum", "classical"): {"sequence": C, "n_range": [1, 16]},
    ("bernstein-vazirani-classical-vs-quantum", "Bernstein-Vazirani quantum"): {"sequence": C, "n_range": [1, 10]},
    ("closest-pair-brute-vs-divide-conquer", "all pairs"): {"sequence": C, "n_range": [2, 20]},
    ("closest-pair-brute-vs-divide-conquer", "Shamos-Hoey"): {"sequence": D, "n_range": [2, 4096], "note": INSTANCE},
    ("deutsch-jozsa-classical-vs-quantum", "classical deterministic"): {"sequence": C, "n_range": [1, 16]},
    ("deutsch-jozsa-classical-vs-quantum", "classical randomized"): {"sequence": C, "n_range": [1, 12]},
    ("deutsch-jozsa-classical-vs-quantum", "Deutsch-Jozsa quantum"): {"sequence": C, "n_range": [1, 10]},
    ("element-distinctness-pairs-vs-sorting", "all pairs"): {"sequence": C, "n_range": [1, 20]},
    ("element-distinctness-pairs-vs-sorting", "sort, then"): {"sequence": D, "n_range": [2, 4096], "note": INSTANCE},
    ("global-min-cut-brute-vs-stoer-wagner", "brute force"): {"sequence": C, "n_range": [2, 17]},
    ("global-min-cut-brute-vs-stoer-wagner", "Stoer-Wagner"): {"sequence": C, "n_range": [2, 21]},
    ("integer-multiplication-schoolbook-vs-karatsuba", "schoolbook"): {"sequence": C, "n_range": [1, 16]},
    ("integer-multiplication-schoolbook-vs-karatsuba", "Karatsuba"): {
        "sequence": D, "n_range": [32, 4096],
        "note": "starts at the schoolbook cutoff (32 digits); below it the count is n^2"},
    ("inversion-counting-quadratic-vs-merge", "all pairs"): {"sequence": C, "n_range": [1, 20]},
    ("inversion-counting-quadratic-vs-merge", "merge-sort"): {"sequence": D, "n_range": [2, 4096], "note": INSTANCE},
    ("longest-increasing-subsequence", "subset enumeration"): {"sequence": C, "n_range": [1, 18]},
    ("longest-increasing-subsequence", "quadratic dynamic"): {"sequence": C, "n_range": [1, 20]},
    ("longest-increasing-subsequence", "patience sorting"): {"sequence": D, "n_range": [2, 65536]},
    ("matrix-multiplication-naive-vs-strassen", "schoolbook"): {"sequence": C, "n_range": [1, 18]},
    ("matrix-multiplication-naive-vs-strassen", "Strassen"): {
        "sequence": D, "n_range": [16, 512], "holdout": 2,
        "note": "starts at the schoolbook cutoff (16); 6 terms, so the holdout is lowered to 2 (n = 1024 would cost "
                "about 7 times n = 512)"},
    ("minimum-finding-classical-vs-quantum", "classical scan"): {"sequence": C, "n_range": [1, 14]},
    ("minimum-spanning-tree-brute-vs-kruskal", "Kruskal"): {
        "sequence": D, "n_range": [2, 2048], "python_version_dependent": True,
        "note": "comparisons inside sorted() (RL-069); also " + INSTANCE},
    ("minimum-spanning-tree-brute-vs-kruskal", "Prim"): {"sequence": C, "n_range": [1, 20]},
    ("nand-tree-evaluation-deterministic-vs-randomized", "deterministic"): {"sequence": C, "n_range": [1, 14]},
    ("optimal-bst-recursion-vs-dp-vs-knuth", "plain recursion"): {"sequence": C, "n_range": [1, 12]},
    ("optimal-bst-recursion-vs-dp-vs-knuth", "cubic interval"): {"sequence": C, "n_range": [1, 20]},
    ("optimal-bst-recursion-vs-dp-vs-knuth", "Knuth"): {"sequence": C, "n_range": [1, 20]},
    ("polynomial-multiplication-naive-vs-ntt", "schoolbook"): {"sequence": C, "n_range": [1, 20]},
    ("polynomial-multiplication-naive-vs-ntt", "number-theoretic"): {"sequence": D, "n_range": [2, 16384]},
    ("range-minimum-queries-naive-vs-sparse-table", "scan each range"): {"sequence": C, "n_range": [1, 20],
                                                                        "note": INSTANCE},
    ("range-minimum-queries-naive-vs-sparse-table", "sparse table"): {"sequence": D, "n_range": [2, 65536]},
    ("regex-matching-backtracking-vs-thompson", "backtracking"): {"sequence": C, "n_range": [1, 16]},
    ("regex-matching-backtracking-vs-thompson", "memoised"): {"sequence": C, "n_range": [1, 20]},
    ("regex-matching-backtracking-vs-thompson", "Thompson"): {"sequence": C, "n_range": [1, 20]},
    ("sorting-insertion-vs-merge", "merge sort"): {"sequence": D, "n_range": [2, 4096], "note": INSTANCE},
    ("spanning-tree-count-enumeration-vs-kirchhoff", "Kirchhoff"): {"sequence": C, "n_range": [1, 20]},
    ("string-matching-naive-vs-kmp", "naive"): {"sequence": C, "n_range": [2, 24]},
    ("string-matching-naive-vs-kmp", "Knuth-Morris-Pratt"): {
        "sequence": C, "n_range": [6, 30],
        "note": "m = n // 2; for n <= 5 the pattern is degenerate and the count is irregular"},
    ("subset-sum-zeta-transform-naive-vs-yates", "submask"): {"sequence": C, "n_range": [1, 12]},
    ("subset-sum-zeta-transform-naive-vs-yates", "Yates"): {"sequence": C, "n_range": [1, 16]},
    ("two-sat-brute-force-vs-scc", "brute force"): {"sequence": C, "n_range": [3, 16]},
    ("two-sat-brute-force-vs-scc", "Aspvall"): {"sequence": C, "n_range": [3, 20]},
    ("xor-convolution-naive-vs-walsh-hadamard", "all index pairs"): {"sequence": C, "n_range": [1, 10]},
    ("xor-convolution-naive-vs-walsh-hadamard", "fast Walsh"): {"sequence": C, "n_range": [1, 14]},
}


def locate(entry: dict, prefix: str) -> int:
    idx = [i for i, a in enumerate(entry["algorithms"]) if a["name"].startswith(prefix)]
    if len(idx) != 1:
        raise SystemExit(f"algorithm prefix {prefix!r} matches {len(idx)} algorithms")
    return idx[0]


def insert_block(text: str, alg_name: str, block: dict) -> str:
    """Insert `"shape": {...}` as the last property of the named algorithm's harness.scaling object."""
    lines = text.split("\n")
    key = f'"name": {json.dumps(alg_name, ensure_ascii=False)}'
    name_line = next(i for i, ln in enumerate(lines) if key in ln)
    sc = next(i for i in range(name_line, len(lines)) if '"scaling": {' in lines[i])
    body = lines[sc].rstrip()
    if body.endswith("}") or body.endswith("},"):  # one-line form: "scaling": { ... }
        tail = "," if body.endswith(",") else ""
        core = body[:-1] if tail else body
        assert core.endswith("}")
        core = core[:-1].rstrip()
        lines[sc] = core + ', "shape": ' + json.dumps(block, ensure_ascii=False) + " }" + tail
        return "\n".join(lines)
    indent = lines[sc][:len(lines[sc]) - len(lines[sc].lstrip())]
    close = next(i for i in range(sc + 1, len(lines)) if lines[i] == indent + "}")
    last = close - 1
    if lines[last].rstrip().endswith(","):
        raise SystemExit("unexpected formatting")
    lines[last] = lines[last] + ","
    lines.insert(close, indent + "  " + '"shape": ' + json.dumps(block, ensure_ascii=False))
    return "\n".join(lines)


def text_change_is_insertion_only(old: list[str], new: list[str]) -> bool:
    """Every difference is (a) an old line that gained a trailing comma, followed by an inserted `"shape": ...`
    line, or (b) an old one-line scaling object with `, "shape": {...}` inserted before its closing brace."""
    sm = difflib.SequenceMatcher(a=old, b=new, autojunk=False)
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        olds, news = old[i1:i2], new[j1:j2]
        if tag == "insert":
            if not all(ln.lstrip().startswith('"shape": ') for ln in news):
                return False
            continue
        if tag != "replace":
            return False
        k = 0
        for ln in olds:
            if k < len(news) and news[k] == ln + ",":
                k += 1
                if k < len(news) and news[k].lstrip().startswith('"shape": '):
                    k += 1
                continue
            if k < len(news) and ', "shape": ' in news[k]:
                before, _, after = news[k].partition(', "shape": ')
                if ln.rstrip().rstrip(",").endswith("}") and ln.rstrip().rstrip(",")[:-1].rstrip() == before \
                        and after.rstrip().rstrip(",").endswith("}"):
                    k += 1
                    continue
            return False
        if k != len(news):
            return False
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    problems = 0
    for (eid, prefix), block in BLOCKS.items():
        path = REPO / "pairs" / eid / "entry.json"
        text = path.read_text(encoding="utf-8")
        entry = json.loads(text)
        i = locate(entry, prefix)
        alg = entry["algorithms"][i]
        sc = alg["harness"]["scaling"]
        if args.apply and "shape" not in sc:
            if sc.get("measure") != "reported":
                raise SystemExit(f"{eid} / {alg['name']}: not an exact-count claim")
            new = insert_block(text, alg["name"], block)
            expect = copy.deepcopy(entry)
            expect["algorithms"][i]["harness"]["scaling"]["shape"] = block
            if json.loads(new) != expect:
                raise SystemExit(f"{eid}: insertion changed more than the block")
            path.write_text(new, encoding="utf-8", newline="")
            print(f"added  {eid} / {alg['name']}")
            entry = json.loads(new)
            sc = entry["algorithms"][i]["harness"]["scaling"]
        if args.check:
            ok = sc.get("shape") == block
            try:
                head = subprocess.run(["git", "show", f"HEAD:pairs/{eid}/entry.json"], cwd=REPO, capture_output=True,
                                      text=True, encoding="utf-8", timeout=20)
                if head.returncode == 0:
                    old = json.loads(head.stdout)
                    j = locate(old, prefix)
                    want = copy.deepcopy(old)
                    want["algorithms"][j]["harness"]["scaling"]["shape"] = block
                    cur = json.loads(path.read_text(encoding="utf-8"))
                    # other blocks of the same entry are allowed; compare after removing every listed block
                    for (e2, p2), _ in BLOCKS.items():
                        if e2 == eid:
                            k = locate(cur, p2)
                            cur["algorithms"][k]["harness"]["scaling"].pop("shape", None)
                            want["algorithms"][locate(want, p2)]["harness"]["scaling"].pop("shape", None)
                    ok = ok and cur == want
                    ok = ok and text_change_is_insertion_only(head.stdout.split("\n"),
                                                              path.read_text(encoding="utf-8").split("\n"))
            except (OSError, subprocess.SubprocessError):
                pass
            print(f"{'ok   ' if ok else 'DIFF '} {eid} / {alg['name']}")
            problems += not ok
    print(f"{len(BLOCKS)} blocks listed; problems: {problems}")
    return 1 if problems else 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
