"""First-match rule ordering entry (pairs/first-match-rule-ordering-enumeration-vs-subset-dp): the numbers the entry
cites for its third algorithm, the subset DP with zeta-transformed gains (implementations/zeta_dp.py). Cited by
RESEARCH_LOG RL-127.

Deterministic (fixed seeds, no wall-clock measurements). Run from the repository root:
    .venv/Scripts/python.exe experiments/2026-10-13_first_match_zeta_checks.py [section ...]

Sections (PROOFS.md section 11):
 1. Exact V2 counts on the cyclic family (m = k, item i matched by rules i and i+1 mod k) against the closed form
        k^2 + 2k + 2 + (k^2 + 2k - 2) 2^(k-1)   (k = 2..17; Corollary 11.6),
    with the split by kind (k^2 truth tests, 2k + 1 + (k^2 + k) 2^(k-1) additions, k 2^(k-1) - 2^k + 1 comparisons,
    no bit operations), the values 0, 5 at k = 0, 1, and the same counts for other drawn costs.
 2. Theorem 11.5 on seeded instances of all six kinds of the harness generator (k = 0..8, every entry a
    CountingInt): for k, m >= 1 exactly k m truth tests, no bit operations, L + m0 + k^2 2^(k-1) + k 2^(k-1) + 1
    additions and k 2^(k-1) - 2^k + 1 comparisons; no counted operation for m = 0; m + 1 additions for k = 0.
 3. Agreement on extra seeded instances, k = 0..12: the variant returns exactly the pair (cost and order) of the
    subset DP; for k <= 7 its cost equals the minimum over all k! orders (enumeration.py) and its order attains it;
    harness.check verdicts.
 4. Executed operations (Section 11.7), by line-execution counts of the unchanged code on seeded instances, k = 0..9:
    the transform addition runs exactly k^2 2^(k-1) times after k^2 2^k bit tests, the table addition L times, the
    default addition m0 times, the transition and the comparison line k 2^(k-1) times each.
 5. Negative controls: modified copies of zeta_dp.py must each be caught by the check that targets it: the gain
    read at s instead of its complement, one transform pass left out, the defaults left out (wrong costs); ties
    resolved by <= instead of < (an order different from the subset DP's); one extra counted addition per
    transition, and tables built from the plain 0, so that additions of two plain zeros go uncounted (V2 counts
    different from the closed form).

Result (console, 2026-10-13, CPython 3.14.2; about 15 s):
 1. The closed form and the split by kind hold for k = 2..17; k = 0, 1 give 0, 5; the counts do not depend on the
    drawn costs.
 2. 270 instances, 0 mismatches: 229 with k, m >= 1 (the exact counts of Theorem 11.5), 18 with m = 0 (no counted
    operation), 23 with k = 0 and m >= 1 (m + 1 additions).
 3. 250 runs of the variant: identical to the subset DP in all 250; equal to the brute-force optimum, with an
    attaining order, in all 218 with k <= 7; check(): 218 accepted exactly (k <= 7), 30 accepted and 2 undecided at
    k >= 8 (the subset DP's identical outputs get the same verdicts).
 4. 300 instances: every line count as stated.
 5. Every modified copy is caught: wrong costs on 149 of 218 instances (gain read at s), 101 of 218 (a pass left
    out), 76 of 218 (defaults left out); ties resolved by <= give 0 wrong costs but 129 of 250 orders different from
    the subset DP's; an extra addition per transition, and tables built from the plain 0, each change the V2 count at
    all 13 sizes k = 2..14.

Check lines start with [PASS] or [FAIL] (section 1: every count line and the summary; sections 2-4: the summary line
with the pinned instance numbers; section 5: one line per control, with the pinned numbers above). The run ends with
ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1).
"""
from __future__ import annotations

import importlib.util
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "pairs" / "first-match-rule-ordering-enumeration-vs-subset-dp"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load(path, name, source=None):
    """Load a module from `path`, or from `source` (a modified copy of that file's text) under the same file name."""
    if source is None:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod
    mod = type(sys)(name)
    mod.__file__ = str(path)
    exec(compile(source, str(path), "exec"), mod.__dict__)
    return mod


H = _load(E / "harness.py", "fmz_harness")
EN = _load(E / "implementations" / "enumeration.py", "fmz_enum").first_match_order_enumeration
DP = _load(E / "implementations" / "subset_dp.py", "fmz_dp").first_match_order_subset_dp
ZETA_PATH = E / "implementations" / "zeta_dp.py"
ZETA_MOD = _load(ZETA_PATH, "fmz_zeta")
ZETA = ZETA_MOD.first_match_order_zeta_dp

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


def closed_v2(k):
    """Corollary 11.6: counted operations on the V2 family (k >= 2)."""
    return k * k + 2 * k + 2 + (k * k + 2 * k - 2) * 2 ** (k - 1)


def kinds_v2(k):
    return {"truth": k * k, "compare": k * 2 ** (k - 1) - 2 ** k + 1, "add": 2 * k + 1 + (k * k + k) * 2 ** (k - 1),
            "bit": 0}


def counted(inst):
    k, match, cost, default = inst
    C = H.CountingInt
    return (k, tuple(tuple(C(x) for x in row) for row in match), tuple(tuple(C(x) for x in row) for row in cost),
            tuple(C(x) for x in default))


def section1():
    print("== 1. exact counts on the cyclic family ==")
    bad = 0
    for k in range(0, 18):
        inst = H.generate_scaling(k, random.Random(f"zeta-v2|{k}"))
        ZETA(inst)
        c, kinds = H.reported_cost(None), H.counts_by_kind()
        if k >= 2:
            ok = c == closed_v2(k) and kinds == kinds_v2(k)
            bad += not ok
            check_line(ok, f"  k={k}: {c} (closed form {closed_v2(k)}) {kinds}")
        else:
            ok = c == (0, 5)[k]
            bad += not ok
            check_line(ok, f"  k={k}: {c} (stated {(0, 5)[k]}) {kinds}")
    same = True
    for k in (5, 9):
        for j in range(3):
            ZETA(H.generate_scaling(k, random.Random(f"other{j}|{k}")))
            same &= H.reported_cost(None) == closed_v2(k)
    return check_line(bad == 0 and same,
                      f"  closed form and split by kind hold for k = 2..17, small cases 0, 5: {bad == 0}; "
                      f"independent of the drawn costs: {same}")


def section2():
    print("== 2. Theorem 11.5 on seeded instances (every entry a CountingInt) ==")
    classes = Counter()
    bad = 0
    for k in range(0, 9):
        for t in range(30):
            inst = H.generate(k, random.Random(f"zeta-thm|{k}|{t}"))
            match = inst[1]
            m = len(match)
            L = sum(sum(row) for row in match)
            m0 = sum(1 for row in match if not any(row))
            H.reset_counter()
            ZETA(counted(inst))
            ops = H.counts_by_kind()
            if k >= 1 and m >= 1:
                classes["k, m >= 1"] += 1
                want = {"truth": k * m, "compare": k * 2 ** (k - 1) - 2 ** k + 1,
                        "add": L + m0 + k * k * 2 ** (k - 1) + k * 2 ** (k - 1) + 1, "bit": 0}
            elif m == 0:
                classes["m = 0"] += 1
                want = {"truth": 0, "compare": 0, "add": 0, "bit": 0}
            else:
                classes["k = 0, m >= 1"] += 1
                want = {"truth": 0, "compare": 0, "add": m + 1, "bit": 0}
            if ops != want:
                bad += 1
                print(f"  MISMATCH k={k} t={t}: {ops} vs {want}")
    return check_line(bad == 0 and dict(classes) == {"k, m >= 1": 229, "m = 0": 18, "k = 0, m >= 1": 23},
                      f"  {sum(classes.values())} instances (k = 0..8): {dict(classes)}; mismatches: {bad}")


def section3():
    print("== 3. agreement with the subset DP, brute force and the oracle ==")
    verdicts = Counter()
    runs = same = brute_checked = brute_ok = 0
    fails = 0
    for k in range(0, 13):
        trials = 30 if k <= 6 else 8 if k <= 8 else 6
        for t in range(trials):
            inst = H.generate(k, random.Random(f"zeta-exp3|{k}|{t}"))
            out = ZETA(inst)
            runs += 1
            if out == DP(inst):
                same += 1
            else:
                fails += 1
                print(f"  DIFFERS FROM THE SUBSET DP k={k} t={t}: {out} vs {DP(inst)}")
            if k <= 7:
                brute_checked += 1
                opt = EN(inst)[0]
                if out[0] == opt and H.order_cost(inst, out[1]) == opt:
                    brute_ok += 1
                else:
                    fails += 1
                    print(f"  NOT OPTIMAL k={k} t={t}: {out}, optimum {opt}")
            v = H.check(inst, out)
            verdicts[(k <= H.BB_EXACT_UP_TO, v)] += 1
            fails += v is False
    return check_line(fails == 0 and same == runs == 250 and brute_ok == brute_checked == 218,
                      f"  {runs} runs: identical to the subset DP in {same}; optimal with an attaining order in "
                      f"{brute_ok} of {brute_checked} (k <= 7); verdicts (k <= 7 exact?, verdict): {dict(verdicts)}; "
                      f"failures: {fails}")


def line_numbers(path, *texts):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    out = []
    for text in texts:
        hits = [i + 1 for i, line in enumerate(lines) if line.strip() == text]
        assert len(hits) == 1, (text, hits)
        out.append(hits[0])
    return out


def count_lines(func, lines, arg):
    code = func.__code__
    counts = {line: 0 for line in lines}

    def local(frame, event, a):
        if event == "line" and frame.f_lineno in counts:
            counts[frame.f_lineno] += 1
        return local

    def glob(frame, event, a):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        func(arg)
    finally:
        sys.settrace(None)
    return counts


def section4():
    print("== 4. executed operations (line-execution counts of the unchanged code) ==")
    texts = ("u |= 1 << r                      # the match set of item i as a bit mask (plain integers)",
             "a[r][u] = a[r][u] + cost[i][r]",
             "base = base + default[i]",
             "if w & bit:",
             "z[w] = z[w] + z[w ^ bit]",
             "value = best_s + a[r][rest]      # gain(s, r) = zeta a_r [complement of s]",
             "if best[t] is None or value < best[t]:")
    lines = line_numbers(ZETA_PATH, *texts)
    bad = n = 0
    for k in range(0, 10):
        for t in range(30):
            inst = H.generate(k, random.Random(f"zeta-lines|{k}|{t}"))
            match = inst[1]
            L = sum(sum(row) for row in match)
            m0 = sum(1 for row in match if not any(row))
            c = count_lines(ZETA, lines, inst)
            got = [c[x] for x in lines]
            want = [L, L, m0, k * k * 2 ** k, k * k * 2 ** k // 2, k * 2 ** k // 2, k * 2 ** k // 2]
            n += 1
            if got != want:
                bad += 1
                print(f"  MISMATCH k={k} t={t}: {got} vs {want}")
    return check_line(bad == 0 and n == 300,
                      f"  {n} instances (k = 0..9): mask and table lines L, default line m0, bit tests k^2 2^k, "
                      f"transform additions k^2 2^(k-1), transitions and comparisons k 2^(k-1); mismatches: {bad}")


MUTANTS = {
    "gain read at s instead of its complement": ("value = best_s + a[r][rest]", "value = best_s + a[r][s]"),
    "one transform pass left out": ("for b in range(k):", "for b in range(k - 1):"),
    "defaults left out": ("return best[full] + base, tuple(order)", "return best[full], tuple(order)"),
    "ties resolved by <=": ("value < best[t]", "value <= best[t]"),
    "an extra counted addition per transition": ("value = best_s + a[r][rest]", "value = (best_s + a[r][rest]) + 0"),
    "tables from the plain 0": ("zero = type(cost[0][0])(0) if k and m else 0", "zero = 0"),
}


def mutant(name):
    old, new = MUTANTS[name]
    src = ZETA_PATH.read_text(encoding="utf-8")
    assert src.count(old) == 1, (name, src.count(old))
    return _load(ZETA_PATH, f"fmz_mutant_{len(name)}", src.replace(old, new)).first_match_order_zeta_dp


def section5():
    print("== 5. negative controls ==")
    insts = []
    for k in range(0, 13):
        trials = 30 if k <= 6 else 8 if k <= 8 else 6
        insts += [H.generate(k, random.Random(f"zeta-exp3|{k}|{t}")) for t in range(trials)]
    small = [inst for inst in insts if inst[0] <= 7]
    opt = [EN(inst)[0] for inst in small]
    results = []
    for name, pinned in (("gain read at s instead of its complement", 149), ("one transform pass left out", 101),
                         ("defaults left out", 76)):
        fn = mutant(name)
        wrong = sum(fn(inst)[0] != o for inst, o in zip(small, opt))
        results.append(check_line(wrong == pinned and wrong > 0,
                                  f"  {name}: wrong cost on {wrong} of {len(small)} instances (k <= 7)"))
    fn = mutant("ties resolved by <=")
    wrong = sum(fn(inst)[0] != o for inst, o in zip(small, opt))
    differ = sum(fn(inst) != DP(inst) for inst in insts)
    results.append(check_line(wrong == 0 and differ == 129,
                              f"  ties resolved by <=: wrong cost on {wrong} of {len(small)} (still optimal), order "
                              f"different from the subset DP on {differ} of {len(insts)} (caught by section 3)"))
    for name in ("an extra counted addition per transition", "tables from the plain 0"):
        fn = mutant(name)
        off, seen = 0, []
        for k in range(2, 15):
            fn(H.generate_scaling(k, random.Random(f"zeta-v2|{k}")))
            seen.append(H.reported_cost(None))
            off += seen[-1] != closed_v2(k)
        results.append(check_line(off == 13, f"  {name}: V2 count differs from the closed form at {off} of 13 sizes "
                                             f"(k = 2..14; recorded {seen[:4]} ... against "
                                             f"{[closed_v2(k) for k in range(2, 6)]} ...)"))
    return all(results)


if __name__ == "__main__":
    only = sys.argv[1:]
    results = {}
    for name, fn in (("1", section1), ("2", section2), ("3", section3), ("4", section4), ("5", section5)):
        if not only or name in only:
            results[name] = fn()
    print(f"\nsections passed: {results}")
    finish_checks()
