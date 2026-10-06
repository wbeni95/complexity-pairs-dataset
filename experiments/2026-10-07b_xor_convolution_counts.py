#!/usr/bin/env python3
"""XOR convolution entry (pairs/xor-convolution-naive-vs-walsh-hadamard): exact operation counts and V2 design.

Questions:
 1. Do the unchanged implementations, run on the harness's CountingInt instances, perform exactly
    naive 2 * 4^n and FWHT (3n + 2) * 2^n ring operations (+, -, *, //)?
 2. Do the counting runs give the same vectors as plain-integer runs (the instrumentation changes nothing)?
 3. Which tolerance separates each claim from its rivals, using the validator's own fit_slope on these exact
    counts over the chosen n_values?

Deterministic (seeded instances, exact counts). Outcome of the run on 2026-10-07 (CPython 3.14):
  - counts equal the closed forms at every n tested (naive n = 0..9, FWHT n = 0..14); outputs identical;
  - naive on n = 3..9 against 4^n: alpha = 1.0000; rivals n*2^n 1.5874, n*4^n 0.8852, 8^n 0.6667;
  - FWHT on n = 4,6,..,14 against n*2^n: alpha = 0.9875 (the exact lower-order term 2*2^n); rivals 2^n 1.1620,
    n^2*2^n 0.8577, 4^n 0.5810; n log n 2^n 0.9175, n/log n 2^n 1.0682.
  Hence tolerance 0.05 in the entry: 4x the FWHT's exact deviation, below every rival gap (smallest 0.0682).
  The validator (scratch venv with jsonschema 4.26, see the report) printed the same values rounded to 3 decimals.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402

ENTRY = REPO / "pairs" / "xor-convolution-naive-vs-walsh-hadamard"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "xor_harness")
NAIVE = load(ENTRY / "implementations" / "naive.py", "xor_naive").xor_convolution_naive
FWHT = load(ENTRY / "implementations" / "fwht.py", "xor_fwht").xor_convolution_fwht


def counted(fn, n):
    inst = H.generate_scaling(n, random.Random(f"xorexp|{n}"))
    out = fn(inst)
    cnt = H.reported_cost(out)
    plain = tuple(tuple(x.v for x in v) for v in inst)
    return cnt, [int(x) for x in out], plain


def alphas(ns, counts, cost_exprs):
    ys = [math.log(c) for c in counts]
    res = {}
    for name, f in cost_exprs.items():
        xs = [math.log(f(n)) for n in ns]
        res[name] = fit_slope(xs, ys)
    return res


def main():
    ok = True
    print("naive: n, count, 2*4^n, same output as plain ints")
    for n in range(0, 10):
        cnt, out, plain = counted(NAIVE, n)
        same = out == NAIVE(plain) == FWHT(plain)
        ok &= cnt == 2 * 4 ** n and same
        print(f"  {n:2d} {cnt:>10d} {2 * 4 ** n:>10d} {same}")
    print("FWHT: n, count, (3n+2)*2^n, same output as plain ints")
    for n in range(0, 15):
        cnt, out, plain = counted(FWHT, n)
        same = out == FWHT(plain) and (n > 9 or out == NAIVE(plain))
        ok &= cnt == (3 * n + 2) * 2 ** n and same
        print(f"  {n:2d} {cnt:>10d} {(3 * n + 2) * 2 ** n:>10d} {same}")
    print("all closed forms and outputs match:", ok)

    ns_naive = [3, 4, 5, 6, 7, 8, 9]
    a = alphas(ns_naive, [2 * 4 ** n for n in ns_naive],
               {"4**n (claim)": lambda n: 4 ** n, "n*2**n": lambda n: n * 2 ** n, "n*4**n": lambda n: n * 4 ** n,
                "8**n": lambda n: 8 ** n})
    print("naive alphas on", ns_naive, {k: round(v, 4) for k, v in a.items()})

    ns_fast = [4, 6, 8, 10, 12, 14]
    a = alphas(ns_fast, [(3 * n + 2) * 2 ** n for n in ns_fast],
               {"n*2**n (claim)": lambda n: n * 2 ** n, "2**n": lambda n: 2 ** n,
                "n**2*2**n": lambda n: n * n * 2 ** n, "4**n": lambda n: 4 ** n,
                "n*log(n)*2**n": lambda n: n * math.log(n) * 2 ** n, "n/log(n)*2**n": lambda n: n / math.log(n) * 2 ** n})
    print("FWHT alphas on", ns_fast, {k: round(v, 4) for k, v in a.items()})


if __name__ == "__main__":
    main()
