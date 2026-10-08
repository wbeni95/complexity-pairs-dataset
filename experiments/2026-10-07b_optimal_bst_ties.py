"""Ties in the root choice and Knuth's speed-up (pairs/optimal-bst-recursion-vs-dp-vs-knuth); deterministic.

Run from the repository root:  python experiments/2026-10-07b_optimal_bst_ties.py

Question: the monotonicity r[i][j-1] <= r[i][j] <= r[i+1][j] is usually stated for a consistent choice among
optimal roots (e.g. always the largest). Does Knuth's restricted search break with other tie rules?

Battery: 6006 tie-heavy instances, n = 2..14, families 'bits' (frequencies in {0, 1}), 'small' ([0, 3]),
'zero', 'constant', 'gaps_only', 'keys_only' from the entry's harness, 77 seeds 'ties|<family>|<n>|<s>' each.
Reference value: the entry's cubic DP (which tries every root).

Variants of Knuth's loop (local copies, same recurrence and root range r[i][j-1]..r[i+1][j]); each keeps, among
the roots of the range that attain the minimum,
  max         the largest ('<=')          -- the entry's implementation
  min         the smallest ('<')
  random      a uniformly random one (rng seeded per instance)
  parity_i    the largest if i is even, else the smallest   (deliberately inconsistent)
  parity_len  the largest if j - i is even, else the smallest
Also checked on the full sets of optimal roots (computed by trying every root): whether the table of the largest
and the table of the smallest optimal roots are monotone, and whether a MIXED table (largest for even i, smallest
for odd i, chosen from the full sets) is monotone.

Outcome (2026-10-07, this script's output): 5464 of the 6006 instances have at least one tied interval. Every
variant (max, min, random, parity_i, parity_len) gives the correct value on all 6006 instances and never meets an
empty root range; the entry's knuth.py is correct on all of them. The largest-root and smallest-root tables are
monotone on every instance; the mixed table chosen from the full optimal sets is NOT monotone on 3417 instances
(e.g. all-zero weights, n >= 4: r[i][j-1] = j-1 > i+2 = r[i+1][j]).
An earlier draft of the entry claimed that a random tie rule can make the restricted search return a wrong value;
this script refuted that (0 wrong values with random choice; part2() below, a wider probe on 6840 instances,
n = 2..20, 60 seeds per family and n, rules parity_i, parity_j, parity_len, 'middle' (median minimiser) and
random: 0 wrong values, 0 empty ranges).
part3() is a negative control of the harness oracle on the entry's V1 battery (same seeds as the validator): the
cubic DP's value is accepted on all 168 instances with n <= 60 (132 by shape enumeration, 36 by the memoised
recursion; the 24 with n = 70, 100 get None), and value + 1 is rejected on every one of them with n >= 1. The reason (derivation, ours): if every chosen root lies in its
range, r[i][j-1] <= r[i+1][j-1] <= r[i+1][j] by induction, so no range is empty; and the quadrangle inequality of c
gives, for ANY optimal root k' of (i, j-1) and any k < k', c_k'(i, j) <= c_k(i, j) (symmetrically for the upper
end), so the range always contains an optimal root of (i, j). What does fail is mixing tie rules in a table of
roots chosen from the full optimal sets (the mixed table above); Knuth's algorithm never builds such a table.

Check lines start with [PASS] or [FAIL]: the entry's knuth.py and every variant correct with non-empty ranges (main
and part2), the largest-root and smallest-root tables monotone and the mixed table non-monotone on exactly 3417 of
the 6006 instances, the published count (main), and the oracle control (part3: 168 checked instances, 24 returning
None, value + 1 rejected on all 156 with n >= 1). The run ends with ALL CHECKS PASSED
(exit code 0) or lists the failed checks (exit code 1). The tie count is reported, not checked.
"""
import importlib.util
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "optimal-bst-recursion-vs-dp-vs-knuth"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "obst_harness_t")
CUB = load(ENTRY / "implementations" / "cubic_dp.py", "obst_cub_t").obst_cubic
KNU = load(ENTRY / "implementations" / "knuth.py", "obst_knu_t").obst_knuth

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


class EmptyRange(Exception):
    pass


def knuth_variant(inst, rule, rng=None):
    p, q = inst
    n = len(p)
    w = [[0] * (n + 1) for _ in range(n + 1)]
    c = [[0] * (n + 1) for _ in range(n + 1)]
    r = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
    for i in range(n):
        w[i][i + 1] = q[i] + p[i] + q[i + 1]
        c[i][i + 1] = w[i][i + 1]
        r[i][i + 1] = i + 1
    for L in range(2, n + 1):
        for i in range(n - L + 1):
            j = i + L
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
            ks = list(range(r[i][j - 1], r[i + 1][j] + 1))
            if not ks:
                raise EmptyRange
            vals = {k: c[i][k - 1] + c[k][j] for k in ks}
            m = min(vals.values())
            opt = [k for k in ks if vals[k] == m]
            if rule == "max":
                r[i][j] = max(opt)
            elif rule == "min":
                r[i][j] = min(opt)
            elif rule == "random":
                r[i][j] = rng.choice(opt)
            elif rule == "parity_i":
                r[i][j] = max(opt) if i % 2 == 0 else min(opt)
            elif rule == "parity_len":
                r[i][j] = max(opt) if (j - i) % 2 == 0 else min(opt)
            else:
                raise ValueError(rule)
            c[i][j] = w[i][j] + m
    return c[0][n]


def root_sets(inst):
    p, q = inst
    n = len(p)
    w = [[0] * (n + 1) for _ in range(n + 1)]
    c = [[0] * (n + 1) for _ in range(n + 1)]
    R = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
    for L in range(1, n + 1):
        for i in range(n - L + 1):
            j = i + L
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
            vals = {k: c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1)}
            m = min(vals.values())
            R[i][j] = [k for k, v in vals.items() if v == m]
            c[i][j] = w[i][j] + m
    return R


def monotone(table, n):
    return all(table[i][j - 1] <= table[i][j] <= table[i + 1][j] for i in range(n + 1) for j in range(i + 2, n + 1))


def main():
    fams = ("bits", "small", "zero", "constant", "gaps_only", "keys_only")
    stats = {rule: {"wrong": 0, "empty": 0} for rule in ("max", "min", "random", "parity_i", "parity_len")}
    impl_wrong = 0
    mono_max = mono_min = mono_mixed = 0
    total = 0
    ties = 0
    first_bad = None
    for fam in fams:
        for n in range(2, 15):
            for s in range(77):
                inst = H._instance(n, random.Random(f"ties|{fam}|{n}|{s}"), fam)
                total += 1
                ref = CUB(inst)
                impl_wrong += KNU(inst) != ref
                for rule in stats:
                    try:
                        val = knuth_variant(inst, rule, random.Random(f"ties-rule|{fam}|{n}|{s}"))
                        if val != ref:
                            stats[rule]["wrong"] += 1
                            if first_bad is None:
                                first_bad = (fam, n, s, inst, val, ref)
                    except EmptyRange:
                        stats[rule]["empty"] += 1
                R = root_sets(inst)
                ties += any(len(R[i][j]) > 1 for i in range(n + 1) for j in range(i + 1, n + 1))
                tmax = [[None if x is None else max(x) for x in row] for row in R]
                tmin = [[None if x is None else min(x) for x in row] for row in R]
                mono_max += not monotone(tmax, n)
                mono_min += not monotone(tmin, n)
                tmix = [[None if x is None else (max(x) if i % 2 == 0 else min(x)) for x in row] for i, row in enumerate(R)]
                mono_mixed += not monotone(tmix, n)
    print(f"instances: {total} (with at least one tied interval: {ties})")
    check_line(impl_wrong == 0, f"entry's knuth.py wrong values: {impl_wrong}")
    for rule, st in stats.items():
        check_line(st["wrong"] == 0 and st["empty"] == 0,
                   f"variant {rule:6s}: wrong values {st['wrong']}, empty root ranges {st['empty']}")
    check_line(mono_max == 0 and mono_min == 0 and mono_mixed == 3417 and total == 6006,
               f"non-monotone largest-root tables: {mono_max}; non-monotone smallest-root tables: {mono_min}; "
               f"non-monotone mixed tables (largest for even i, smallest for odd i): {mono_mixed}")
    if first_bad:
        fam, n, s, inst, val, ref = first_bad
        print(f"first wrong value: family {fam}, n={n}, seed {s}, p={inst[0]}, q={inst[1]}: "
              f"{val} instead of {ref}")


def part2():
    rules = {
        "parity_i": lambda i, j, o, g: max(o) if i % 2 == 0 else min(o),
        "parity_j": lambda i, j, o, g: max(o) if j % 2 == 0 else min(o),
        "parity_len": lambda i, j, o, g: max(o) if (j - i) % 2 == 0 else min(o),
        "middle": lambda i, j, o, g: o[len(o) // 2],
        "random": lambda i, j, o, g: g.choice(o),
    }
    bad = {k: [0, 0] for k in rules}
    total = 0
    for fam in ("bits", "small", "zero", "constant", "gaps_only", "keys_only"):
        for n in range(2, 21):
            for s in range(60):
                inst = H._instance(n, random.Random(f"probe|{fam}|{n}|{s}"), fam)
                total += 1
                ref = CUB(inst)
                for name, rule in rules.items():
                    g = random.Random(f"probe-rule|{fam}|{n}|{s}|{name}")
                    v = generic_variant(inst, lambda i, j, o: rule(i, j, o, g))
                    if v is None:
                        bad[name][1] += 1
                    elif v != ref:
                        bad[name][0] += 1
    check_line(all(v == [0, 0] for v in bad.values()),
               f"part2: {total} instances; [wrong values, empty ranges] per rule: {bad}")


def generic_variant(inst, choose):
    p, q = inst
    n = len(p)
    w = [[0] * (n + 1) for _ in range(n + 1)]
    c = [[0] * (n + 1) for _ in range(n + 1)]
    r = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
    for i in range(n):
        w[i][i + 1] = q[i] + p[i] + q[i + 1]
        c[i][i + 1] = w[i][i + 1]
        r[i][i + 1] = i + 1
    for L in range(2, n + 1):
        for i in range(n - L + 1):
            j = i + L
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
            ks = list(range(r[i][j - 1], r[i + 1][j] + 1))
            if not ks:
                return None
            vals = {k: c[i][k - 1] + c[k][j] for k in ks}
            m = min(vals.values())
            r[i][j] = choose(i, j, [k for k in ks if vals[k] == m])
            c[i][j] = w[i][j] + m
    return c[0][n]


def part3():
    import json
    e = json.load(open(ENTRY / "entry.json", encoding="utf-8"))
    th = e["test_harness"]
    accepted = rejected_wrong = none = checked = checked_n1 = 0
    for n in th["v1_sizes"]:
        for trial in range(th["trials"]):
            inst = H.generate(n, random.Random(f"{e['id']}|v1|{n}|{trial}"))
            val = CUB(inst)
            verdict = H.check(inst, val)
            if verdict is None:
                none += 1
                continue
            checked += 1
            accepted += verdict is True
            if n >= 1:
                checked_n1 += 1
                rejected_wrong += H.check(inst, val + 1) is False
    check_line(accepted == checked and rejected_wrong == checked_n1 and (checked, none, checked_n1) == (168, 24, 156),
               f"part3: oracle accepted {accepted}/{checked} checked V1 instances ({none} returned None); "
               f"value + 1 rejected on {rejected_wrong} (all checked instances with n >= 1)"
               + ("" if rejected_wrong == checked_n1 else f" | FAIL: {checked_n1} checked instances with n >= 1"))


if __name__ == "__main__":
    main()
    part2()
    part3()
    finish_checks()
