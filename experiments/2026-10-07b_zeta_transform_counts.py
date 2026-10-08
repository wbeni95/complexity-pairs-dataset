#!/usr/bin/env python3
"""Zeta-transform entry (pairs/subset-sum-zeta-transform-naive-vs-yates): exact addition counts and V2 design.

Questions:
 1. Do the unchanged implementations, on the harness's CountingInt instances, perform exactly 3^n (naive) and
    n * 2^(n-1) (Yates) additions?
 2. Are the outputs identical to plain-integer runs, and do both agree?
 3. With the validator's fit_slope on these exact counts, which tolerance separates each claim from its rivals?

Deterministic. Outcome (console run 2026-10-07, CPython 3.14):
  - counts equal 3^n and n * 2^(n-1) at every n = 0..12; outputs identical to plain-integer runs, both agree;
  - naive on n = 4..11: alpha 1.0000 vs 3^n; n*2^n 1.3153, 4^n 0.7925, n*3^n 0.8856, 2^n 1.585;
  - Yates on n = 4,6,..,16: alpha 1.0000 vs n*2^n; 2^n 1.1612, n^2*2^n 0.8772, 3^n 0.7327, n log n 2^n 0.9362.
  So tolerance 0.02 (alpha is exactly 1; smallest rival gap 0.0638). The validator reproduced these values.

Check lines (every n: both counts equal their closed forms and the outputs agree; the summary) start with [PASS] or
[FAIL]; the run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The alphas are
reported, not checked.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402

ENTRY = REPO / "pairs" / "subset-sum-zeta-transform-naive-vs-yates"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "zeta_harness")
NAIVE = load(ENTRY / "implementations" / "naive.py", "zeta_naive").zeta_naive
YATES = load(ENTRY / "implementations" / "yates.py", "zeta_yates").zeta_yates

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


def counted(fn, n):
    inst = H.generate_scaling(n, random.Random(f"zetaexp|{n}"))
    out = fn(inst)
    return H.reported_cost(out), [int(x) for x in out], tuple(x.v for x in inst)


def alphas(ns, counts, exprs):
    ys = [math.log(c) for c in counts]
    return {k: round(fit_slope([math.log(f(n)) for n in ns], ys), 4) for k, f in exprs.items()}


def main():
    ok = True
    for n in range(0, 13):
        cn, on, plain = counted(NAIVE, n)
        cy, oy, _ = counted(YATES, n)
        same = on == oy == NAIVE(plain) == YATES(plain)
        line_ok = (cn == 3 ** n and cy == n * 2 ** (n - 1) if n else cn == 1 and cy == 0) and same
        ok &= line_ok
        check_line(line_ok, f"n={n:2d} naive={cn:>8d} (3^n={3 ** n:>8d})  yates={cy:>7d} "
                            f"(n*2^(n-1)={n * 2 ** n // 2:>7d})  same={same}")
    check_line(ok, "all closed forms and outputs match:", ok)

    ns = [4, 5, 6, 7, 8, 9, 10, 11]
    print("naive alphas on", ns, alphas(ns, [3 ** n for n in ns], {
        "3**n (claim)": lambda n: 3 ** n, "n*2**n": lambda n: n * 2 ** n, "4**n": lambda n: 4 ** n,
        "n*3**n": lambda n: n * 3 ** n, "2**n": lambda n: 2 ** n}))
    ns = [4, 6, 8, 10, 12, 14, 16]
    print("yates alphas on", ns, alphas(ns, [n * 2 ** (n - 1) for n in ns], {
        "n*2**n (claim)": lambda n: n * 2 ** n, "2**n": lambda n: 2 ** n, "n**2*2**n": lambda n: n * n * 2 ** n,
        "3**n": lambda n: 3 ** n, "n*log(n)*2**n": lambda n: n * math.log(n) * 2 ** n}))
    finish_checks()


if __name__ == "__main__":
    main()
