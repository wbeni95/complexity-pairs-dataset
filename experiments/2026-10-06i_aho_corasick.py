"""Experiment (research/2026-10-06i_new_entries.md, section 2): checks behind the entry
pairs/multi-pattern-matching-naive-vs-aho-corasick.

Sections (deterministic):
  1  exact character-comparison counts on the V2 family (text a^(n^2), patterns a^(j-1) b, j = 1..n) against
       naive         n(n+1)(3n^2 - 2n + 2)/6      (n >= 1)
       KMP each      3n^3 - 2n^2 - 5n + 6          (n >= 2)
       Aho-Corasick  4n^2 - 3                      (n >= 1)
     and the Aho-Corasick split into building (trie + failure links: n^2 + n - 4 for n >= 2, from a run with an
     empty text) and scanning (3n^2 - n + 1);
  2  agreement of the three implementations with each other and with harness.check on extra instances;
  3  many occurrences: text a^N with patterns a, aa, ..., a^n has sum_j (N - j + 1) occurrences, but Aho-Corasick's
     comparison count stays linear in N + L (the counts are propagated along failure links, not reported one by one);
  4  oracle control: deliberately wrong outputs presented to harness.check;
  5  the V2 count series with a SHA-256, for the cross-version comparison.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06i_aho_corasick.py
RESULT (2026-10-06, CPython 3.14.2): see the report; every section prints its totals.

Check lines start with [PASS] or [FAIL] (section 1: every line; section 2: the summary; section 3: every line, whose
check is "comparisons <= 3 (N + L)"; section 4: the summary); the run ends with ALL CHECKS PASSED (exit code 0) or
lists the failed checks (exit code 1). The verdict tallies and the count series with its SHA-256 (section 5) are
reported, not checked.
"""
from __future__ import annotations

import hashlib
import importlib.util
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "pairs" / "multi-pattern-matching-naive-vs-aho-corasick"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "ac_harness")
NA = _load(E / "implementations" / "naive.py", "ac_naive").count_occurrences_naive
KM = _load(E / "implementations" / "kmp_each.py", "ac_kmp").count_occurrences_kmp_each
AC = _load(E / "implementations" / "aho_corasick.py", "ac_ac").count_occurrences_aho_corasick
ALGS = (("naive", NA), ("kmp_each", KM), ("aho_corasick", AC))

FAILED = []


def check_line(ok, *parts):
    """Print one check line with a [PASS] or [FAIL] prefix and remember the failures."""
    print("[PASS]" if ok else "[FAIL]", *parts, flush=True)
    if not ok:
        FAILED.append(" ".join(str(p) for p in parts).strip())
    return ok


def finish_checks():
    """End of the run: ALL CHECKS PASSED (exit code 0), or the failed checks and exit code 1."""
    if FAILED:
        print(f"FAILED: {len(FAILED)} check(s):")
        for label in FAILED:
            print(f"  {label}")
        sys.exit(1)
    print("ALL CHECKS PASSED")

FORMS = {
    "naive": (1, lambda n: n * (n + 1) * (3 * n * n - 2 * n + 2) // 6),
    "kmp_each": (2, lambda n: 3 * n ** 3 - 2 * n ** 2 - 5 * n + 6),
    "aho_corasick": (1, lambda n: 4 * n * n - 3),
}


def counted(fn, inst_strings):
    text, patterns = inst_strings
    H._comparisons = 0
    inst = (tuple(H.CountingChar(c) for c in text), tuple(tuple(H.CountingChar(c) for c in p) for p in patterns))
    H._comparisons = 0
    out = fn(inst)
    return H.reported_cost(out)


def scaling_count(fn, n):
    inst = H.generate_scaling(n, None)
    fn(inst)
    return H.reported_cost(None)


def section1():
    print("== 1. exact counts on the V2 family ==")
    ok = True
    for name, fn in ALGS:
        lo, form = FORMS[name]
        top = {"naive": 40, "kmp_each": 70, "aho_corasick": 300}[name]
        ns = list(range(1, 21)) + [n for n in (24, 32, 40, 48, 64, 70, 128, 256, 300) if n <= top]
        diffs = [(n, c, form(n)) for n in ns for c in [scaling_count(fn, n)] if c != form(n)]
        held = [n for n in ns if n >= lo and n not in {d[0] for d in diffs}]
        bad = [d for d in diffs if d[0] >= lo]
        ok &= not bad
        span = f"{held[0]}..{held[-1]}" if held else "none of the sizes"   # held is empty if the form fails everywhere
        check_line(not bad, f"  {name}: closed form holds for n = {span} ({len(held)} values); "
                            f"differs below n = {lo}: {[d for d in diffs if d[0] < lo]}; differs at n >= {lo}: {bad}")
    for n in (2, 5, 10, 50):
        text, patterns = H.scaling_strings(n)
        build = counted(AC, ("", patterns))
        total = scaling_count(AC, n)
        line_ok = build == n * n + n - 4 and total - build == 3 * n * n - n + 1
        ok &= line_ok
        check_line(line_ok, f"  Aho-Corasick n={n}: build {build} (n^2 + n - 4 = {n * n + n - 4}), scan {total - build} "
                            f"(3n^2 - n + 1 = {3 * n * n - n + 1})")
    return ok


def section2():
    print("== 2. agreement and oracle on extra instances ==")
    fails = 0
    runs = 0
    nonzero = 0
    for n in range(0, 25):
        for t in range(60):
            inst = H.generate(n, random.Random(f"ac-exp2|{n}|{t}"))
            outs = [fn(inst) for _, fn in ALGS]
            runs += len(outs)
            nonzero += any(outs[0])
            if len(set(outs)) != 1 or not all(H.check(inst, o) for o in outs):
                fails += 1
                print(f"  FAIL n={n} t={t}: {inst} {outs}")
    return check_line(fails == 0, f"  {runs} implementation runs on {runs // 3} instances ({nonzero} with at least one "
                                  f"occurrence); failures: {fails}")


def section3():
    print("== 3. many occurrences ==")
    ok = True
    for n in (4, 8, 16, 32):
        text = "a" * (n * n)
        patterns = tuple("a" * j for j in range(1, n + 1))
        occ = sum(AC((text, patterns)))
        c = counted(AC, (text, patterns))
        length = n * n + n * (n + 1) // 2
        check_line(c <= 3 * length, f"  n={n}: text {n * n}, total pattern length {n * (n + 1) // 2}, occurrences {occ}, "
                                    f"Aho-Corasick comparisons {c} ({c / length:.3f} per character of input)")
        ok &= c <= 3 * length
    return ok


def section4():
    print("== 4. oracle control ==")
    stats = Counter()
    for n in range(0, 16):
        for t in range(30):
            inst = H.generate(n, random.Random(f"ac-exp4|{n}|{t}"))
            text, patterns = inst
            good = AC(inst)
            stats[("correct", H.check(inst, good))] += 1
            wrong = {"list instead of tuple": list(good), "total count": sum(good), "None": None,
                     "one pattern too many": good + (0,)}
            if n >= 1:
                i = t % n
                wrong["count + 1 on one pattern"] = good[:i] + (good[i] + 1,) + good[i + 1:]
                wrong["bool entry"] = good[:i] + (True,) + good[i + 1:]
                wrong["float entry"] = good[:i] + (float(good[i]),) + good[i + 1:]
                wrong["one pattern missing"] = good[:-1]
            nonover = tuple(text.count(p) for p in patterns)
            if nonover != good:
                wrong["non-overlapping counts (str.count)"] = nonover
            if good[::-1] != good:  # a palindromic tuple such as (1, 2, 1) is its own reverse (control bug fixed 2026-10-06)
                wrong["counts reversed"] = good[::-1]
            rev = tuple(sum(1 for i in range(len(text) - len(p) + 1) if text[i:i + len(p)] == p[::-1]) for p in patterns)
            if rev != good:
                wrong["counts of the reversed patterns"] = rev
            for name, out in wrong.items():
                stats[(name, H.check(inst, out))] += 1
    rejected = sum(v for (k, verdict), v in stats.items() if k != "correct" and verdict is False)
    accepted = sum(v for (k, verdict), v in stats.items() if k != "correct" and verdict is True)
    for key in sorted(stats, key=str):
        print(f"  {key}: {stats[key]}")
    return check_line(accepted == 0 and stats[("correct", False)] == 0,
                      f"  wrong outputs: {rejected} rejected, {accepted} accepted; correct outputs: "
                      f"{stats[('correct', True)]} accepted, {stats[('correct', False)]} rejected")


def section5():
    print("== 5. V2 count series (cross-version) ==")
    lines = [f"{name} {n} {scaling_count(fn, n)}" for name, fn in ALGS for n in range(1, 17)]
    lines += [f"aho_corasick {n} {scaling_count(AC, n)}" for n in (32, 64, 128, 256)]
    blob = "\n".join(lines)
    print(f"  {len(lines)} values; python {sys.version.split()[0]} sha256 {hashlib.sha256(blob.encode()).hexdigest()}")
    return True


if __name__ == "__main__":
    t0 = time.time()
    only = sys.argv[1:]
    results = {}
    for name, fn in (("1", section1), ("2", section2), ("3", section3), ("4", section4), ("5", section5)):
        if not only or name in only:
            results[name] = fn()
    print(f"\nsections passed: {results}  [{time.time() - t0:.1f}s]")
    finish_checks()
