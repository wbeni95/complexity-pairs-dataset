"""Hamiltonian-cycle counting entry (pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion): the numbers
the entry cites.

Deterministic (fixed seeds, no wall-clock measurements). Run from the repository root:
    .venv/Scripts/python.exe experiments/2026-10-06f_entries_hamiltonian.py

Sections:
 1. The validator's own V1 battery (same seeds as tools/validate.py): per n, which oracle rule judged each
    instance and the range of answers; all implementations that run at that n must agree with check.
 2. Extended battery: 40 more seeded instances per n for n = 3..12 (enumeration up to n = 9).
 3. Closed forms against the exhaustive depth-first count: complete digraph, minus one arc, directed and
    undirected cycles, K_{m,m}, unequal K_{a,b}, Petersen graph.
 4. Oracle control: deliberately wrong outputs (off by one, a factor 2, the undirected count, the count per
    start vertex, (n-1)!, wrong types) must be rejected; correct outputs must be accepted.
 5. Exact counts on K_n against the hand-derived closed forms, for every n in a range.
 6. The two dynamic programmes count the same number of operations on random graphs as on K_n (input-oblivious);
    the enumeration's count on random graphs is printed for information.
 7. Fits with the validator's own eval_cost / fit_slope: claimed cost, rivals, leading terms, log diagnostics.
 8. Memory: table cells of the Held-Karp count vs walk-vector cells of inclusion-exclusion.
 9. The uncounted membership tests of the Held-Karp inner loop: (n-1)^2 (2^(n-2) - 1).

Result (console, 2026-10-06, CPython 3.14.2; about 35 s):
 1. 112 instances, 296 implementation runs, 104 instances with >= 2 implementations compared; 109 judged exactly,
    3 (n = 14) by necessary conditions only; 0 failures.
 2. 400 instances, 388 judged exactly; 0 failures.
 3. 39 graphs, 0 mismatches; the Petersen graph gives 0 in the three methods that run at n = 10
    (inclusion-exclusion, Held-Karp and the oracle's depth-first count; the enumeration is capped at n = 9).
 4. 3535 wrong outputs on 410 instances: 3471 rejected, 64 undecided (n = 11: 4, 12: 30, 13: 16, 14: 14),
    0 accepted. Correct outputs: 398 accepted, 12 undecided, 0 rejected.
 5. Counts equal the closed forms for every n: enumeration n = 2..10 (n!), inclusion-exclusion n = 2..13,
    Held-Karp n = 2..16.
 6. On random graphs the two DP counts are identical to those on K_n; the enumeration's are smaller.
 7. alpha = 1.0000 for all three claims; rivals: enumeration (n-1)! 1.0707, n n! 0.9379, n^2 2^n 2.1297;
    inclusion-exclusion n^2 2^n 1.1124, n^4 2^n 0.8969, 3^n 0.9226 (leading term n^3 2^n: 0.9932);
    Held-Karp n 2^n 1.1441, n^3 2^n 0.9375, 3^n 0.8111 (bare n^2 2^n: 1.0306).
 9. True for n = 3..16.
Two earlier generator versions gave answer 0 on 8 and then 7 of the validator's 8 instances at n = 2 (seed luck);
the generator now draws the 2-cycle with probability 1/2 as its first random number (5 of 8 have answer 1).

Check lines start with [PASS] or [FAIL]: 1 and 2 (0 failures; 109 of the 112 validator instances judged exactly,
3 by necessary conditions only; 400 extended instances, 388 judged exactly), 3 (39 graphs, 0 mismatches), 4 (3535
wrong outputs on 410 instances: 3471 rejected, 64 undecided, all at n = 11..14, 0 accepted; correct outputs 398
accepted, 12 undecided, 0 rejected), every line of 5, the counts in 6 (both dynamic programmes equal to their K_n counts, the enumeration's smaller), and
9. The run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The battery
composition, the fits (7) and the memory table (8) are reported, not checked.
"""
from __future__ import annotations

import importlib.util
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ENTRY_ID = "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"
ENTRY = REPO / "pairs" / ENTRY_ID


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "ham_harness")
EN = load(ENTRY / "implementations" / "enumeration.py", "ham_en").count_hamiltonian_cycles_enumeration
IE = load(ENTRY / "implementations" / "inclusion_exclusion.py", "ham_ie").count_hamiltonian_cycles_inclusion_exclusion
HK = load(ENTRY / "implementations" / "held_karp_counting.py", "ham_hk").count_hamiltonian_cycles_held_karp
V = load(REPO / "tools" / "validate.py", "ham_validate")

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

ALGS = (("enumeration", EN, 9), ("inclusion-exclusion", IE, 12), ("Held-Karp counting", HK, None))

FORMS = {
    "enumeration": lambda n: math.factorial(n),
    "inclusion-exclusion": lambda n: n * (n - 1) * (n + 2) * 2 ** (n - 2) + 2 ** (n - 1) - 1,
    "Held-Karp counting": lambda n: (n - 1) * (n - 2) * 2 ** (n - 2) + 2 * (n - 1),
}


RUNS = {"runs": 0, "compared": 0}


def run_battery(sizes, trials, seed_fmt):
    failures = 0
    per_n = {}
    for n in sizes:
        rules, answers = {}, []
        for trial in range(trials):
            rng = random.Random(seed_fmt.format(n=n, trial=trial))
            inst = H.generate(n, rng)
            outs = [fn(inst) for _, fn, cap in ALGS if cap is None or n <= cap]
            RUNS["runs"] += len(outs)
            RUNS["compared"] += len(outs) >= 2
            expected, rule = H.exact_count(inst)
            rules[rule] = rules.get(rule, 0) + 1
            verdicts = [H.check(inst, o) for o in outs]
            if len(set(outs)) != 1 or False in verdicts:
                failures += 1
                print(f"   FAIL n={n} trial={trial}: outputs {outs}, verdicts {verdicts}")
            answers.append(outs[0])
        per_n[n] = (rules, min(answers), max(answers))
    return failures, per_n


def section1():
    print("1. Validator V1 battery (seeds as in tools/validate.py)")
    import json
    entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
    th = entry["test_harness"]
    RUNS.update(runs=0, compared=0)
    fails, per_n = run_battery(th["v1_sizes"], th["trials"], ENTRY_ID + "|v1|{n}|{trial}")
    print(f"   implementation runs {RUNS['runs']}; instances with >= 2 implementations compared {RUNS['compared']}")
    judged = none = 0
    for n, (rules, lo, hi) in per_n.items():
        k_none = rules.get("no exact rule", 0)
        none += k_none
        judged += sum(rules.values()) - k_none
        print(f"   n={n:2d}: answers {lo}..{hi}; rules {dict(sorted(rules.items()))}")
    check_line(fails == 0 and (judged, none) == (109, 3),
               f"   instances {judged + none}: exactly judged {judged}, only necessary conditions {none}; failures {fails}")


def section2():
    print("2. Extended battery: 40 instances per n = 3..12")
    fails, per_n = run_battery(range(3, 13), 40, "ham-extended|{n}|{trial}")
    total = sum(sum(r.values()) for r, _, _ in per_n.values())
    none = sum(r.get("no exact rule", 0) for r, _, _ in per_n.values())
    check_line(fails == 0 and (total, total - none) == (400, 388),
               f"   instances {total} (exactly judged {total - none}); failures {fails}")


def section3():
    print("3. Closed forms vs exhaustive depth-first count (and the three implementations)")
    rows = []
    for n in range(3, 10):
        rows.append((f"complete K_{n}", H.complete_digraph(n), math.factorial(n - 1)))
        a = H.complete_digraph(n)
        a[1][2] = 0
        rows.append((f"K_{n} minus an arc", a, math.factorial(n - 1) - math.factorial(n - 2)))
        c = H._empty(n)
        for i in range(n):
            c[i][(i + 1) % n] = 1
        rows.append((f"directed C_{n}", c, 1))
        u = [row[:] for row in c]
        for i in range(n):
            u[(i + 1) % n][i] = 1
        rows.append((f"undirected C_{n}", u, 2))
    for m in range(1, 6):
        rows.append((f"K_{{{m},{m}}}", H.complete_bipartite(m, m), math.factorial(m) * math.factorial(m - 1)))
    for a_, b_ in ((1, 2), (2, 3), (3, 4), (2, 5), (4, 5)):
        rows.append((f"K_{{{a_},{b_}}}", H.complete_bipartite(a_, b_), 0))
    rows.append(("Petersen", H.petersen(), None))
    bad = 0
    for name, a, formula in rows:
        inst = tuple(tuple(r) for r in a)
        dfs = H.dfs_count(inst)
        outs = [fn(inst) for _, fn, cap in ALGS if cap is None or len(inst) <= cap]
        cf = H.closed_form(inst)
        ok = (formula is None or dfs == formula) and all(o == dfs for o in outs) and (cf is None or cf[0] == dfs)
        bad += not ok
        if name.startswith(("K_{", "Petersen")) or len(inst) in (3, 9):
            print(f"   {name}: formula {formula}, DFS {dfs}, implementations {outs}, check rule {cf}")
    check_line(bad == 0 and len(rows) == 39, f"   {len(rows)} graphs, mismatches {bad}")


def wrong_outputs(inst, true):
    n = len(inst)
    cands = {
        "plus one": true + 1,
        "minus one": true - 1,
        "times two": 2 * true,
        "half (undirected count)": true // 2,
        "times n (per start vertex)": n * true,
        "(n-1)!": math.factorial(max(n - 1, 0)),
        "negative": -1,
        "float": float(true),
        "bool": bool(true),
        "None": None,
    }
    return {k: v for k, v in cands.items() if not (type(v) is int and v == true)}


def section4():
    print("4. Oracle control")
    tallies = {}
    correct = {"True": 0, "None": 0, "False": 0}
    undecided_n = {}
    instances = 0
    for n in range(0, 15):
        for trial in range(30 if n <= 12 else 10):
            inst = H.generate(n, random.Random(f"ham-control|{n}|{trial}"))
            instances += 1
            true = HK(inst)
            correct[str(H.check(inst, true))] += 1
            for name, out in wrong_outputs(inst, true).items():
                t = tallies.setdefault(name, {"rejected": 0, "None": 0, "accepted": 0})
                v = H.check(inst, out)
                t["rejected" if v is False else "None" if v is None else "accepted"] += 1
                if v is None:
                    undecided_n[n] = undecided_n.get(n, 0) + 1
    print(f"   instances {instances} (n = 0..12: 30 each, n = 13, 14: 10 each); undecided wrong outputs by n: {undecided_n}")
    for name, t in tallies.items():
        print(f"   wrong output '{name}': {t}")
    acc = sum(t["accepted"] for t in tallies.values())
    rej = sum(t["rejected"] for t in tallies.values())
    non = sum(t["None"] for t in tallies.values())
    check_line(acc == 0 and (instances, rej, non) == (410, 3471, 64) and all(11 <= k <= 14 for k in undecided_n),
               f"   wrong outputs: rejected {rej}, undecided (None) {non}, accepted {acc}")
    check_line(correct == {"True": 398, "None": 12, "False": 0}, f"   correct outputs: {correct}")


def counts_on(fn, inst):
    out = fn(inst)
    return int(out), dict(H._ops), H.reported_cost(out)


def section5():
    print("5. Exact counts on K_n vs closed forms")
    for name, fn, _ in ALGS:
        top = {"enumeration": 10, "inclusion-exclusion": 13, "Held-Karp counting": 16}[name]
        ok = True
        for n in range(2, top + 1):
            ans, split, total = counts_on(fn, H.generate_scaling(n, None))
            ok &= total == FORMS[name](n) and ans == math.factorial(n - 1)
        last = split
        check_line(ok, f"   {name}: n = 2..{top}: count == closed form and answer == (n-1)! for all n: {ok}; "
                       f"split at n={top}: {last}")


def section6():
    print("6. Counts on random 0/1 digraphs (CountingInt entries) vs K_n")
    for n in (6, 8, 10):
        for trial in range(3):
            rng = random.Random(f"ham-oblivious|{n}|{trial}")
            a = H.generate(n, rng)
            inst = tuple(tuple(H.CountingInt(x) for x in row) for row in a)
            line = []
            dp_same = True          # the two dynamic programmes are input-oblivious; the enumeration counts less
            for name, fn, cap in ALGS:
                if cap is not None and n > cap:
                    continue
                H.reset_counter()
                ans, _, total = counts_on(fn, inst)
                line.append(f"{name} {total} (K_n: {FORMS[name](n)})")
                if name != "enumeration":
                    dp_same &= total == FORMS[name](n)
                else:
                    dp_same &= total < FORMS[name](n)
            check_line(dp_same, f"   n={n} trial {trial} answer {ans}: " + "; ".join(line))


def section7():
    print("7. Fits (validator eval_cost / fit_slope; claimed cost first, then rivals, then other forms)")
    import json
    entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
    extra = {
        "enumeration": [],
        "inclusion-exclusion": ["n**3 * 2**n"],
        "Held-Karp counting": ["n**2 * 2**n"],
    }
    for alg in entry["algorithms"]:
        sc = alg["harness"]["scaling"]
        name = alg["name"]
        fn = {"permutation enumeration": EN, "inclusion-exclusion over vertex subsets": IE,
              "Held-Karp counting DP": HK}[name]
        key = {"permutation enumeration": "enumeration", "inclusion-exclusion over vertex subsets":
               "inclusion-exclusion", "Held-Karp counting DP": "Held-Karp counting"}[name]
        ns = sc["n_values"]
        ys = []
        for n in ns:
            _, _, total = counts_on(fn, H.generate_scaling(n, None))
            ys.append(math.log(total))
        print(f"   {name}: n_values {ns}, tolerance {sc['tolerance']}")
        for label, exprs in (("claim", [sc["cost"]]), ("rival", sc["rivals"]), ("other", extra[key])):
            for e in exprs:
                xs = [math.log(V.eval_cost(e, n)) for n in ns]
                a = V.fit_slope(xs, ys)
                verdict = "fits" if abs(a - 1) <= sc["tolerance"] else "rejected"
                print(f"      {label} {e}: alpha = {a:.4f} ({verdict})")
        lx = [math.log(math.log(n)) for n in ns]
        xs = [math.log(V.eval_cost(sc["cost"], n)) for n in ns]
        up = V.fit_slope([x + l for x, l in zip(xs, lx)], ys)
        down = V.fit_slope([x - l for x, l in zip(xs, lx)], ys)
        print(f"      diagnostic: vs cost*log n {up:.4f}, vs cost/log n {down:.4f}")


def section8():
    print("8. Memory (numbers stored)")
    for n in (10, 16, 20, 25):
        print(f"   n={n}: Held-Karp table (n-1)*2^(n-1) = {(n - 1) * 2 ** (n - 1)}; inclusion-exclusion walk vectors <= 2n = {2 * n}")


def section9():
    print("9. Uncounted bookkeeping of the Held-Karp loops (plain-integer membership tests in the inner loop)")
    ok = True
    for n in range(3, 17):
        m = n - 1
        tests = 0
        for mask in range(1, 1 << m):
            if mask & (mask - 1) == 0:
                continue
            for b in range(m):
                if (mask >> b) & 1:
                    tests += m
        ok &= tests == m * m * (2 ** (m - 1) - 1)
    check_line(ok, f"   inner-loop membership tests == (n-1)^2 (2^(n-2) - 1) for n = 3..16: {ok}")


if __name__ == "__main__":
    try:
        from search.machine import set_below_normal_priority
        print("below-normal priority:", set_below_normal_priority())
    except Exception as exc:  # noqa: BLE001
        print("priority not changed:", exc)
    for sec in (section1, section2, section3, section4, section5, section6, section7, section8, section9):
        sec()
    finish_checks()
