"""Maximum-weight independent set on k x n grids with diagonals
(pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp): the numbers the entry cites.

Deterministic (fixed seeds, no wall-clock measurements). Run from the repository root:
    .venv/Scripts/python.exe experiments/2026-10-06f_entries_mis_pathwidth.py

Sections:
 1. The validator's own V1 battery (same seeds as tools/validate.py): k, diagonal kinds, answers, agreement,
    check verdicts, and how often the two algorithms return different optimal sets (ties).
 2. Extended battery: 50 seeded instances per n = 0..5 (both algorithms) and 30 per n = 6..60 step 6 (DP only).
 3. Oracle control: deliberately wrong outputs must be rejected, correct ones accepted.
 4. Exact addition counts: exhaustive search N 2^(N-1) on every instance (any k, diagonals, zero weights);
    column DP n P_k + (n-1) F_{k+2} on instances with positive weights (any k, any diagonals), and what happens
    with zero weights.
 5. Fits with the validator's own eval_cost / fit_slope: claimed cost, rivals, other forms, log diagnostics.
 6. k-dependence at fixed n = 20 (king's graph): states, P_k, additions, compatibility tests, compatible pairs.
 7. Square grids k = n (king's graph): the DP's additions grow exponentially in n.

Result (console, 2026-10-06, CPython 3.14.2; about 5 s):
 1. 88 instances, 136 implementation runs, 48 compared; 0 failures; 0 instances with different optimal sets.
 2. n = 0..5: 300 instances (both algorithms), n = 6..60: 300 instances (DP); 0 failures; 0 different sets.
 3. 3393 wrong outputs on 330 instances: 3393 rejected, 0 undecided, 0 accepted; 510 correct outputs accepted.
 4. Exhaustive search: N 2^(N-1) additions on 77 random instances (N <= 15, zero weights included) and on the
    V2 family n = 1..6. Column DP: n P_k + (n-1) F_(k+2) on 420 random instances (positive weights), 10n - 5 on
    the V2 family; with weights in {0, 1} up to 6 additions are uncounted (59 of 420 instances).
    Comparisons (not part of the count): exhaustive search 4, 10, 34, 92, 268, 746 for n = 1..6 (one per
    non-empty independent set); DP 6n - 2.
 5. alpha = 1.0000 for both claims; rivals: 8^n 1.1302, n^2 8^n 0.8962, 4^n 1.6953; n^2 0.5006, n log n 0.8623.
    Other forms: n^1.5 8^n 0.9453 (rejected); plain n for the DP 1.0013 (fits).
 6. DP additions at n = 20, k = 1..8: 58, 97, 195, 352, 647, 1159, 2066, 3645 (all equal to the formula).
 7. Square king's grids k = n = 2..10: DP additions 7, 25, 64, 152, 333, 701, 1425, 2827, 5496.
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
ENTRY_ID = "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"
ENTRY = REPO / "pairs" / ENTRY_ID


def load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "mis_harness")
BF = load(ENTRY / "implementations" / "brute_force.py", "mis_bf").mwis_brute_force
DP = load(ENTRY / "implementations" / "column_dp.py", "mis_dp").mwis_column_dp
V = load(REPO / "tools" / "validate.py", "mis_validate")
BF_MAX_N = 5


def states_of(k):
    return [s for s in range(1 << k) if s & (s >> 1) == 0]


def p_k(k):
    return sum(bin(s).count("1") for s in states_of(k))


def diag_kind(inst):
    k, n, _, d = inst
    codes = [x for row in d for x in row]
    if not codes:
        return "none possible"
    if all(x == 3 for x in codes):
        return "king"
    if all(x == 0 for x in codes):
        return "plain"
    if all(x == 1 for x in codes):
        return "all 1"
    if all(x == 2 for x in codes):
        return "all 2"
    return "mixed"


def battery(sizes, trials, seed_fmt):
    fails = differ = runs = compared = 0
    per_n = {}
    for n in sizes:
        ks, kinds, values = [], {}, []
        for trial in range(trials):
            inst = H.generate(n, random.Random(seed_fmt.format(n=n, trial=trial)))
            outs = [DP(inst)] + ([BF(inst)] if n <= BF_MAX_N else [])
            runs += len(outs)
            compared += len(outs) == 2
            verdicts = [H.check(inst, o) for o in outs]
            if any(v is not True for v in verdicts) or len({o[0] for o in outs}) != 1:
                fails += 1
                print(f"   FAIL n={n} trial={trial}: {outs} {verdicts}")
            if len(outs) == 2 and outs[0][1] != outs[1][1]:
                differ += 1
            ks.append(inst[0])
            kinds[diag_kind(inst)] = kinds.get(diag_kind(inst), 0) + 1
            values.append(outs[0][0])
        per_n[n] = (sorted(set(ks)), kinds, min(values), max(values))
    return fails, differ, runs, compared, per_n


def section1():
    print("1. Validator V1 battery (seeds as in tools/validate.py)")
    entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
    th = entry["test_harness"]
    fails, differ, runs, compared, per_n = battery(th["v1_sizes"], th["trials"], ENTRY_ID + "|v1|{n}|{trial}")
    for n, (ks, kinds, lo, hi) in per_n.items():
        print(f"   n={n:2d}: k in {ks}; diagonals {kinds}; optimum {lo}..{hi}")
    total = sum(len(range(th['trials'])) for _ in th["v1_sizes"])
    print(f"   instances {total}, implementation runs {runs}, compared {compared}; different optimal sets with equal "
          f"value {differ}; failures {fails}")


def section2():
    print("2. Extended battery")
    f1, d1, _, c1, _ = battery(range(0, 6), 50, "mis-extended|{n}|{trial}")
    f2, _, _, _, _ = battery(range(6, 61, 6), 30, "mis-extended|{n}|{trial}")
    print(f"   n = 0..5: 300 instances, both algorithms + check, different optimal sets {d1}, failures {f1}")
    print(f"   n = 6..60 step 6: 300 instances, DP + check, failures {f2}")


def neighbours_of(inst, v):
    k, n, _, d = inst
    pairs = H.adjacent_pairs(k, n, d)
    return [u for pair in pairs if v in pair for u in pair if u != v]


def wrong_outputs(inst, value, chosen):
    k, n, w, d = inst
    weight = lambda s: sum(w[r][c] for r, c in s)
    out = {}
    out["value + 1, same set"] = (value + 1, chosen)
    if value > 0:
        out["value - 1, same set"] = (value - 1, chosen)
    positive = [v for v in chosen if w[v[0]][v[1]] > 0]
    if positive:
        smaller = tuple(v for v in chosen if v != positive[0])
        out["drop a vertex (suboptimal, honest weight)"] = (weight(smaller), smaller)
    if chosen:
        nb = [u for u in neighbours_of(inst, chosen[0]) if u not in chosen]
        if nb:
            bigger = tuple(sorted(chosen + (nb[0],)))
            out["add a neighbour (not independent, honest weight)"] = (weight(bigger), bigger)
        out["duplicate vertex"] = (value + w[chosen[0][0]][chosen[0][1]], chosen + (chosen[0],))
    if value > 0:
        out["empty set, value 0"] = (0, ())
    out["vertex outside the grid"] = (value, chosen + ((k, 0),))
    out["float value"] = (float(value), chosen)
    out["list instead of tuple"] = (value, list(chosen))
    out["value only"] = value
    # optimum of the same weights without the diagonals: wrong whenever its set is not independent here
    plain = (k, n, w, tuple(tuple(0 for _ in row) for row in d))
    pv, ps = DP(plain)
    pairs = H.adjacent_pairs(k, n, d)
    if any(frozenset((a, b)) in pairs for i, a in enumerate(ps) for b in ps[i + 1:]):
        out["optimum ignoring the diagonals (set not independent)"] = (pv, ps)
    # greedy by weight: wrong whenever it is suboptimal
    order = sorted(((w[r][c], r, c) for r in range(k) for c in range(n)), reverse=True)
    greedy = []
    for _, r, c in order:
        if all(frozenset(((r, c), g)) not in pairs for g in greedy):
            greedy.append((r, c))
    gv = weight(greedy)
    if gv < value:
        out["greedy by weight (suboptimal, honest weight)"] = (gv, tuple(sorted(greedy)))
    return out


def section3():
    print("3. Oracle control")
    tallies = {}
    correct = {"True": 0, "None": 0, "False": 0}
    instances = 0
    for n in list(range(0, 9)) + [12, 20]:
        for trial in range(30):
            inst = H.generate(n, random.Random(f"mis-control|{n}|{trial}"))
            instances += 1
            out = DP(inst)
            correct[str(H.check(inst, out))] += 1
            if n <= BF_MAX_N:
                correct[str(H.check(inst, BF(inst)))] += 1
            for name, wrong in wrong_outputs(inst, *out).items():
                t = tallies.setdefault(name, {"rejected": 0, "None": 0, "accepted": 0})
                v = H.check(inst, wrong)
                t["rejected" if v is False else "None" if v is None else "accepted"] += 1
    for name, t in tallies.items():
        print(f"   wrong output '{name}': {t}")
    print(f"   instances {instances}; wrong outputs: rejected {sum(t['rejected'] for t in tallies.values())}, "
          f"undecided {sum(t['None'] for t in tallies.values())}, accepted {sum(t['accepted'] for t in tallies.values())}")
    print(f"   correct outputs (DP on all, exhaustive search on n <= 5): {correct}")


def counted(fn, inst):
    H.reset_counters()
    out = fn(inst)
    return int(out[0]), H._ops["add"], H._ops["compare"]


def wrap_instance(inst):
    k, n, w, d = inst
    return k, n, tuple(tuple(H.CountingInt(x) for x in row) for row in w), d


def section4():
    print("4. Exact addition counts")
    ok_bf = ok_dp = True
    zero_dev = []
    checked_bf = checked_dp = 0
    for n in range(0, 7):
        for trial in range(12):
            rng = random.Random(f"mis-counts|{n}|{trial}")
            inst = H.generate(n, rng)
            k = inst[0]
            if k * n <= 15:
                _, adds, _ = counted(BF, wrap_instance(inst))
                ok_bf &= adds == k * n * 2 ** max(k * n - 1, 0) if k * n else adds == 0
                checked_bf += 1
    for n in range(1, 41, 3):
        for k in range(1, 7):
            for diag in (0, 1, 2, 3, None):
                rng = random.Random(f"mis-dpcounts|{n}|{k}|{diag}")
                w = tuple(tuple(H.CountingInt(rng.randint(1, 50)) for _ in range(n)) for _ in range(k))
                d = tuple(tuple(rng.randrange(4) if diag is None else diag for _ in range(n - 1)) for _ in range(k - 1))
                val, adds, _ = counted(DP, (k, n, w, d))
                ok_dp &= adds == n * p_k(k) + (n - 1) * len(states_of(k))
                ok_dp &= val == H.profile_dp_value((k, n, tuple(tuple(int(x) for x in row) for row in w), d))
                checked_dp += 1
                wz = tuple(tuple(H.CountingInt(0 if rng.random() < 0.5 else 1) for _ in range(n)) for _ in range(k))
                _, adds_z, _ = counted(DP, (k, n, wz, d))
                zero_dev.append(n * p_k(k) + (n - 1) * len(states_of(k)) - adds_z)
    print(f"   exhaustive search: count == N 2^(N-1) on {checked_bf} random instances (N <= 15, zero weights "
          f"included): {ok_bf}")
    print(f"   column DP, positive weights: count == n P_k + (n-1) F_(k+2) and value == oracle on {checked_dp} "
          f"instances (n = 1..40, k = 1..6, all diagonal patterns): {ok_dp}")
    print(f"   column DP, weights in {{0, 1}}: uncounted additions (formula - count): min {min(zero_dev)}, "
          f"max {max(zero_dev)}, nonzero in {sum(1 for x in zero_dev if x)} of {len(zero_dev)}")
    rows = []
    for n in range(1, 7):
        _, a_bf, c_bf = counted(BF, H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}")))
        _, a_dp, c_dp = counted(DP, H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}")))
        rows.append((n, a_bf, 3 * n * 2 ** (3 * n - 1), c_bf, a_dp, 10 * n - 5, c_dp))
    for r in rows:
        print(f"   king k=3 n={r[0]}: exhaustive adds {r[1]} (formula {r[2]}), comparisons {r[3]}; "
              f"DP adds {r[4]} (formula {r[5]}), comparisons {r[6]}")


def section5():
    print("5. Fits (validator eval_cost / fit_slope)")
    entry = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))
    extra = {"exhaustive search over all vertex subsets": ["3*n * 2**(3*n - 1)", "8**n * n**1.5"],
             "DP over the columns (path decomposition of width 2k-1)": ["n"]}
    for alg in entry["algorithms"]:
        sc = alg["harness"]["scaling"]
        fn = BF if alg["name"].startswith("exhaustive") else DP
        ns = sc["n_values"]
        ys = []
        for n in ns:
            _, adds, _ = counted(fn, H.generate_scaling(n, random.Random(f"{ENTRY_ID}|v2|{n}")))
            ys.append(math.log(adds))
        print(f"   {alg['name']}: n_values {ns}, tolerance {sc['tolerance']}")
        for label, exprs in (("claim", [sc["cost"]]), ("rival", sc["rivals"]), ("other", extra[alg["name"]])):
            for e in exprs:
                xs = [math.log(V.eval_cost(e, n)) for n in ns]
                a = V.fit_slope(xs, ys)
                print(f"      {label} {e}: alpha = {a:.4f} ({'fits' if abs(a - 1) <= sc['tolerance'] else 'rejected'})")


def section6():
    print("6. k-dependence at fixed n = 20 (king's graph, seeded weights 1..9)")
    n = 20
    for k in range(1, 9):
        states = states_of(k)
        compat = sum(1 for s in states for t in states if not ((t | (t << 1) | (t >> 1)) & s))
        _, adds, comps = counted(DP, H.king_instance(k, n, random.Random(f"mis-k|{k}")))
        print(f"   k={k}: states F_(k+2) = {len(states)}, P_k = {p_k(k)}, DP additions {adds} "
              f"(formula {n * p_k(k) + (n - 1) * len(states)}), comparisons {comps}, compatibility tests "
              f"{(n - 1) * len(states) ** 2}, compatible king pairs per column {compat}; exhaustive search would "
              f"need N 2^(N-1) = {k * n * 2 ** (k * n - 1):.3e} additions")


def section7():
    print("7. Square king's grids k = n")
    for n in range(2, 11):
        _, adds, _ = counted(DP, H.king_instance(n, n, random.Random(f"mis-square|{n}")))
        print(f"   k = n = {n}: DP additions {adds}, states per column {len(states_of(n))}, "
              f"compatibility tests {(n - 1) * len(states_of(n)) ** 2}")


if __name__ == "__main__":
    try:
        from search.machine import set_below_normal_priority
        print("below-normal priority:", set_below_normal_priority())
    except Exception as exc:  # noqa: BLE001
        print("priority not changed:", exc)
    for sec in (section1, section2, section3, section4, section5, section6, section7):
        sec()
