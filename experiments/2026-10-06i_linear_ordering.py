"""Experiment (research/2026-10-06i_new_entries.md, section 3): checks behind the entry
pairs/linear-ordering-enumeration-vs-subset-dp.

Sections (deterministic):
  1  exact V2 counts against the closed forms (n >= 2)
       enumeration  n! (n(n-1)/2 + 1) - 1        subset DP  2^(n-2) (n+4)(n-1) + 1
     on several random matrices per n (the counts must not depend on the entries);
  2  agreement of both implementations with each other and with harness.check on extra instances;
  3  oracle control: deliberately wrong outputs presented to harness.check;
  4  the V2 count series with a SHA-256, for the cross-version comparison.

Run from the repository root:  .venv/Scripts/python.exe experiments/2026-10-06i_linear_ordering.py
RESULT (2026-10-06, CPython 3.14.2): see the report; every section prints its totals.

Check lines start with [PASS] or [FAIL] (section 1: every count line and the summary; sections 2 and 3: the summary
line; in 3 every wrong output rejected (2460), none accepted or undecided, every correct output accepted (212)); the run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The verdict tallies
and the count series with its SHA-256 (section 4) are reported, not checked.
"""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "pairs" / "linear-ordering-enumeration-vs-subset-dp"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "lop_harness")
EN = _load(E / "implementations" / "enumeration.py", "lop_enum").linear_ordering_enumeration
DP = _load(E / "implementations" / "subset_dp.py", "lop_dp").linear_ordering_subset_dp

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


def closed_enum(n):
    return math.factorial(n) * (n * (n - 1) // 2 + 1) - 1


def closed_dp(n):
    return 2 ** (n - 2) * (n + 4) * (n - 1) + 1


def count(fn, n, seed):
    inst = H.generate_scaling(n, random.Random(seed))
    fn(inst)
    return H.reported_cost(None)


def section1():
    print("== 1. exact counts ==")
    ok = True
    for n in range(2, 16):
        if n <= 8:
            cs = {count(EN, n, f"s{j}|{n}") for j in range(3)}
            ok &= cs == {closed_enum(n)}
            check_line(cs == {closed_enum(n)}, f"  enumeration n={n}: {sorted(cs)} (closed form {closed_enum(n)})")
        cs = {count(DP, n, f"s{j}|{n}") for j in range(3 if n <= 12 else 1)}
        ok &= cs == {closed_dp(n)}
        check_line(cs == {closed_dp(n)}, f"  subset DP   n={n}: {sorted(cs)} (closed form {closed_dp(n)})")
    return check_line(ok, f"  closed forms hold on every n and seed tried: {ok}")


def section2():
    print("== 2. agreement and oracle on extra instances ==")
    verdicts = Counter()
    fails = runs = 0
    for n in range(0, 13):
        for t in range(25 if n <= 7 else 6):
            w = H.generate(n, random.Random(f"lop-exp2|{n}|{t}"))
            outs = ([EN(w)] if n <= 8 else []) + [DP(w)]
            runs += len(outs)
            if len({o[0] for o in outs}) != 1:
                fails += 1
                print(f"  DISAGREE n={n} t={t}: {outs}")
            for o in outs:
                v = H.check(w, o)
                verdicts[(n <= H.BB_EXACT_UP_TO, v)] += 1
                fails += v is False
    return check_line(fails == 0,
                      f"  {runs} implementation runs; verdicts (n <= 8 exact?, verdict): {dict(verdicts)}; failures: {fails}")


def section3():
    print("== 3. oracle control ==")
    rng = random.Random("lop-exp3")
    stats = Counter()
    for n in range(0, 10):
        for t in range(25 if n <= 7 else 6):
            w = H.generate(n, random.Random(f"lop-exp3|{n}|{t}"))
            value, order = DP(w)
            stats[("correct", H.check(w, (value, order)))] += 1
            wrong = {"value + 1": (value + 1, order), "value - 1": (value - 1, order), "bool value": (True, order),
                     "float value": (float(value), order), "None": None, "bare value": value,
                     "order as list": (value, list(order))}
            if n >= 2:
                wrong["repeated element"] = (value, (order[0],) * n)
            if n >= 1:
                wrong["missing element"] = (value, order[:-1])
            diag = sum(w[a][a] for a in range(n))
            if diag:
                wrong["diagonal added"] = (value + diag, order)
            rev = tuple(reversed(order))
            if H.order_value(w, rev) != value:
                wrong["value of the reversed order"] = (H.order_value(w, rev), order)
            cands = list(itertools.permutations(range(n))) if n <= 6 else [tuple(rng.sample(range(n), n)) for _ in range(40)]
            worse = [o for o in cands if H.order_value(w, o) < value]
            if worse:
                o = worse[rng.randrange(len(worse))]
                wrong["worse order, honest value"] = (H.order_value(w, o), o)
                wrong["worse order, optimal value"] = (value, o)
            for name, out in wrong.items():
                stats[(name, H.check(w, out))] += 1
    rejected = sum(v for (k, verdict), v in stats.items() if k != "correct" and verdict is False)
    accepted = sum(v for (k, verdict), v in stats.items() if k != "correct" and verdict is True)
    undecided = sum(v for (k, verdict), v in stats.items() if k != "correct" and verdict is None)
    for key in sorted(stats, key=str):
        print(f"  {key}: {stats[key]}")
    return check_line(accepted == 0 and undecided == 0 and stats[("correct", None)] == 0
                      and stats[("correct", False)] == 0 and rejected == 2460 and stats[("correct", True)] == 212,
                      f"  wrong outputs: {rejected} rejected, {accepted} accepted, {undecided} undecided; correct outputs: "
                      f"{stats[('correct', True)]} accepted, {stats[('correct', None)]} undecided, "
                      f"{stats[('correct', False)]} rejected")


def section4():
    print("== 4. V2 count series (cross-version) ==")
    lines = [f"enumeration {n} {count(EN, n, f'v2|{n}')}" for n in range(2, 9)]
    lines += [f"subset_dp {n} {count(DP, n, f'v2|{n}')}" for n in range(2, 16)]
    blob = "\n".join(lines)
    print(f"  {len(lines)} values; python {sys.version.split()[0]} sha256 {hashlib.sha256(blob.encode()).hexdigest()}")
    return True


if __name__ == "__main__":
    t0 = time.time()
    only = sys.argv[1:]
    results = {}
    for name, fn in (("1", section1), ("2", section2), ("3", section3), ("4", section4)):
        if not only or name in only:
            results[name] = fn()
    print(f"\nsections passed: {results}  [{time.time() - t0:.1f}s]")
    finish_checks()
