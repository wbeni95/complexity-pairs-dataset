#!/usr/bin/env python3
"""Regex entry (pairs/regex-matching-backtracking-vs-thompson): exact comparison counts, agreement battery, V2 design.

Questions:
 1. On P_n = ((a?)^n a^n, a^n), how many symbol-character comparisons do the unchanged matchers make (counted by
    the harness's CountingChar)? Hand derivation (in entry.json): backtracking (n + 2) 2^(n-1) - 1; memoised
    backtracking n(n + 1); Thompson n(n + 1).
 2. Do the three matchers agree with Python's re.fullmatch on a large seeded random battery?
 3. Which tolerance separates each claim from its rivals (validator's fit_slope on exact counts)?

Deterministic. Outcome (console run 2026-10-07, CPython 3.14):
  - all three closed forms hold at every measured n (backtracking 0..16; memoised and Thompson 0..16, 24, 32, 48,
    64); e.g. n = 16: 589823 vs 272 vs 272. All answers on P_n are True (all-skip is the accepting branch).
  - battery: 0 disagreements in 3300 instances (2275 matches) against re.fullmatch.
  - backtracking on n = 4..16 even: alpha 0.9739 vs n*2^n; 2^n 1.1311, n^2*2^n 0.8541, n^2 3.3856.
  - memoised/Thompson on n = 4..64 (powers of 2): alpha 0.9638 vs n^2; n 1.9275, n^3 0.6425, n^2 log n 0.8054.
    The entry uses n = 8..128 instead, where the validator gives 0.981 (smaller lower-order effect).
  NEAR-MISS: at tolerance 0.06 the validator's log-factor diagnostic for backtracking was NOT resolved
  (1.044 against n 2^n / log n); the entry uses 0.035, which exceeds the exact deviation 0.026 and resolves it.

Check lines (the closed forms and the answer True of all three matchers over the whole table, n = 0..16, 24, 32,
48, 64; the battery) start with [PASS] or [FAIL]; the run ends with ALL CHECKS PASSED (exit code 0) or lists the
failed checks (exit code 1). The table rows and the alphas are reported.
"""
import importlib.util
import math
import random
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402

ENTRY = REPO / "pairs" / "regex-matching-backtracking-vs-thompson"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "rx_harness")
BT = load(ENTRY / "implementations" / "backtracking.py", "rx_bt").match_backtracking
MEMO = load(ENTRY / "implementations" / "memoized.py", "rx_memo").match_memoized
TH = load(ENTRY / "implementations" / "thompson.py", "rx_th").match_thompson

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


def count(fn, n):
    inst = H.generate_scaling(n, random.Random(0))
    out = fn(inst)
    return H.reported_cost(out), out


def alphas(ns, counts, exprs):
    ys = [math.log(c) for c in counts]
    return {k: round(fit_slope([math.log(f(n)) for n in ns], ys), 4) for k, f in exprs.items()}


def main():
    ok = True
    print(" n  backtracking  (n+2)2^(n-1)-1   memoised  thompson  n(n+1)  answers")
    for n in range(0, 17):
        cb, ob = count(BT, n)
        cm, om = count(MEMO, n)
        ct, ot = count(TH, n)
        fb = (n + 2) * 2 ** n // 2 - 1 if n else 0
        ok &= cb == fb and cm == n * (n + 1) and ct == n * (n + 1) and ob is om is ot is True
        print(f"{n:2d} {cb:>13d} {fb:>16d} {cm:>10d} {ct:>9d} {n * (n + 1):>7d}  {ob} {om} {ot}")
    for n in (24, 32, 48, 64):
        cm, om = count(MEMO, n)
        ct, ot = count(TH, n)
        ok &= cm == ct == n * (n + 1) and om is True and ot is True
        print(f"{n:2d} {'-':>13s} {'-':>16s} {cm:>10d} {ct:>9d} {n * (n + 1):>7d}")
    check_line(ok, "closed forms hold:", ok)

    # Random battery against re.fullmatch (sizes as in V1; harness.generate).
    dis, total, trues = 0, 0, 0
    for n in range(0, 11):
        for t in range(300):
            inst = H.generate(n, random.Random(f"rx-battery|{n}|{t}"))
            ref = re.fullmatch(inst[0], inst[1]) is not None
            outs = (BT(inst), MEMO(inst), TH(inst))
            total += 1
            trues += ref
            if any(o != ref for o in outs):
                dis += 1
                print("DISAGREE", inst, ref, outs)
    check_line(dis == 0, f"battery: {dis} disagreements in {total} instances ({trues} matches)")

    ns = [4, 6, 8, 10, 12, 14, 16]
    print("backtracking alphas on", ns, alphas(ns, [(n + 2) * 2 ** n // 2 - 1 for n in ns], {
        "n*2**n (claim)": lambda n: n * 2 ** n, "2**n": lambda n: 2 ** n, "n**2*2**n": lambda n: n * n * 2 ** n,
        "n**2": lambda n: n * n}))
    ns = [4, 8, 16, 32, 64]
    print("thompson/memo alphas on", ns, alphas(ns, [n * (n + 1) for n in ns], {
        "n**2 (claim)": lambda n: n * n, "n": lambda n: n, "n**3": lambda n: n ** 3,
        "n**2*log(n)": lambda n: n * n * math.log(n), "2**n": lambda n: 2 ** n}))
    finish_checks()


if __name__ == "__main__":
    main()
