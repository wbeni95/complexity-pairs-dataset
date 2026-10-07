"""First-match rule ordering entry (pairs/first-match-rule-ordering-enumeration-vs-subset-dp): the numbers the
entry cites.

Deterministic (fixed seeds, no wall-clock measurements). Run from the repository root:
    .venv/Scripts/python.exe experiments/2026-10-07_first_match_checks.py [section ...]

Sections:
 1. Exact V2 counts on the cyclic family (m = k, item i matched by rules i and i+1 mod k) against the closed forms
        enumeration  k! (k+1)(k+3)/3 - 1   (k = 2..8)      subset DP  3k^2 + (7k - 2) 2^(k-1) + 2   (k = 2..18)
    with the split by kind (truth tests, additions, comparisons, bit operations), and the same counts for other
    drawn costs.
 2. Agreement of both implementations with each other and with harness.check on extra seeded instances
    (k = 0..8 for the enumeration, k = 0..12 for the DP), with the verdict counts.
 3. The feedback-arc-set reduction: for random weighted digraphs with at most 14 arcs, the optimum of the reduced
    instance equals the minimum weight of a feedback arc set found by brute force over all arc subsets (acyclicity
    by Kahn's algorithm); and for every order the reduced cost equals the weight of the backward arcs.
 4. Items matching at most 2 rules give linear ordering instances: for every order, the cost equals a constant plus
    the sum of W[a][b] over the pairs with a before b (W[a][b] = costs of the items {a, b} captured by a).
 5. Oracle control: deliberately wrong outputs presented to harness.check; correct outputs must be accepted.

Result (console, 2026-10-07, CPython 3.14.2; about 10 s):
 1. Both closed forms hold for every k checked (at k = 1, a degenerate case, the enumeration count differs); the
    counts do not depend on the drawn costs.
 2. 476 implementation runs: 436 accepted exactly (k <= 7), 38 accepted and 2 undecided at k >= 8; 0 failures.
 3. 300 digraphs (n = 2..6): optimum == brute-force minimum feedback arc set weight in all 300;
    39314 orders: reduced cost == backward-arc weight in all.
 4. 25741 (instance, order) pairs: first-match cost == constant + forward linear-ordering weight in all.
 5. Wrong outputs: 2515 rejected, 0 accepted, 0 undecided. Correct outputs: 216 accepted, 0 undecided, 0 rejected.
"""
from __future__ import annotations

import importlib.util
import itertools
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
E = ROOT / "pairs" / "first-match-rule-ordering-enumeration-vs-subset-dp"
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(E / "harness.py", "fm_harness")
EN = _load(E / "implementations" / "enumeration.py", "fm_enum").first_match_order_enumeration
DP = _load(E / "implementations" / "subset_dp.py", "fm_dp").first_match_order_subset_dp


def closed_enum(k):
    return math.factorial(k) * (k + 1) * (k + 3) // 3 - 1


def closed_dp(k):
    return 3 * k * k + (7 * k - 2) * 2 ** (k - 1) + 2


def count(fn, k, seed="v2"):
    inst = H.generate_scaling(k, random.Random(f"{seed}|{k}"))
    fn(inst)
    return H.reported_cost(None), H.counts_by_kind()


def section1():
    print("== 1. exact counts on the cyclic family ==")
    bad = 0
    for k in range(1, 9):
        c, kinds = count(EN, k)
        ok = c == closed_enum(k)
        bad += (not ok) and k >= 2
        print(f"  enumeration k={k}: {c} (closed form {closed_enum(k)}) {'OK' if ok else 'differs'} {kinds}")
    for k in range(1, 19):
        c, kinds = count(DP, k)
        ok = c == closed_dp(k)
        bad += (not ok) and k >= 2
        print(f"  subset DP   k={k}: {c} (closed form {closed_dp(k)}) {'OK' if ok else 'differs'} {kinds}")
    # the counts do not depend on the costs drawn: other seeds give the same counts
    same = all(count(DP, k, f"other{j}")[0] == closed_dp(k) for k in (5, 9) for j in range(3))
    same &= all(count(EN, k, f"other{j}")[0] == closed_enum(k) for k in (5, 7) for j in range(3))
    print(f"  closed forms hold for k >= 2 (k = 1 is degenerate: one item matched by one rule): {bad == 0}; "
          f"independent of the drawn costs: {same}")
    return bad == 0 and same


def section2():
    print("== 2. agreement and oracle on extra instances ==")
    verdicts = Counter()
    fails = 0
    runs = 0
    for k in range(0, 13):
        trials = 30 if k <= 6 else 8 if k <= 8 else 6
        for t in range(trials):
            inst = H.generate(k, random.Random(f"exp2|{k}|{t}"))
            outs = []
            if k <= 8:
                outs.append(EN(inst))
            outs.append(DP(inst))
            runs += len(outs)
            if len({o[0] for o in outs}) != 1:
                fails += 1
                print(f"  DISAGREE k={k} t={t}: {outs}")
            for o in outs:
                v = H.check(inst, o)
                verdicts[(k <= H.BB_EXACT_UP_TO, v)] += 1
                fails += v is False
    print(f"  {runs} implementation runs; verdicts (k <= 7 exact?, verdict): {dict(verdicts)}; failures: {fails}")
    return fails == 0


def _acyclic(n, arcs):
    indeg = [0] * n
    out = [[] for _ in range(n)]
    for u, v in arcs:
        out[u].append(v)
        indeg[v] += 1
    todo = [v for v in range(n) if indeg[v] == 0]
    seen = 0
    while todo:
        v = todo.pop()
        seen += 1
        for w in out[v]:
            indeg[w] -= 1
            if indeg[w] == 0:
                todo.append(w)
    return seen == n


def reduce_fas(n, arcs):
    """Weighted digraph (arcs: list of (u, v, w)) -> first-match instance on n rules."""
    match, cost = [], []
    for u, v, w in arcs:
        row = [0] * n
        row[u] = row[v] = 1
        c = [0] * n
        c[v] = w
        match.append(row)
        cost.append(c)
    return (n, tuple(map(tuple, match)), tuple(map(tuple, cost)), tuple(0 for _ in arcs))


def section3():
    print("== 3. feedback arc set reduction ==")
    rng = random.Random("exp3")
    graphs = mism = order_checks = order_bad = 0
    while graphs < 300:
        n = rng.randint(2, 6)
        arcs = [(u, v, rng.randint(1, 5)) for u in range(n) for v in range(n) if u != v and rng.random() < 0.45]
        if len(arcs) > 14:
            continue
        graphs += 1
        best_fas = min(sum(a[2] for j, a in enumerate(arcs) if mask >> j & 1)
                       for mask in range(1 << len(arcs))
                       if _acyclic(n, [(a[0], a[1]) for j, a in enumerate(arcs) if not mask >> j & 1]))
        inst = reduce_fas(n, arcs)
        if DP(inst)[0] != best_fas:
            mism += 1
            print(f"  MISMATCH n={n} arcs={arcs}: DP {DP(inst)[0]} vs min FAS {best_fas}")
        for order in itertools.permutations(range(n)):
            pos = {r: p for p, r in enumerate(order)}
            backward = sum(w for u, v, w in arcs if pos[v] < pos[u])
            order_checks += 1
            order_bad += H.order_cost(inst, order) != backward
    print(f"  {graphs} digraphs (n = 2..6, <= 14 arcs): optimum == brute-force minimum FAS weight in all but {mism}; "
          f"{order_checks} orders: reduced cost == backward-arc weight in all but {order_bad}")
    return mism == 0 and order_bad == 0


def section4():
    print("== 4. items matching <= 2 rules are linear ordering instances ==")
    rng = random.Random("exp4")
    checked = bad = 0
    for _ in range(200):
        k = rng.randint(1, 6)
        match, cost, default = [], [], []
        for _ in range(rng.randint(0, 2 * k + 2)):
            size = rng.choice((0, 1, 2, 2))
            rs = rng.sample(range(k), min(size, k))
            match.append(tuple(1 if r in rs else 0 for r in range(k)))
            cost.append(tuple(rng.randint(0, 9) for _ in range(k)))
            default.append(rng.randint(0, 9))
        inst = (k, tuple(match), tuple(cost), tuple(default))
        const = 0
        W = [[0] * k for _ in range(k)]
        for i, row in enumerate(match):
            rs = [r for r in range(k) if row[r]]
            if not rs:
                const += default[i]
            elif len(rs) == 1:
                const += cost[i][rs[0]]
            else:
                a, b = rs
                W[a][b] += cost[i][a]
                W[b][a] += cost[i][b]
        for order in itertools.permutations(range(k)):
            lop = const + sum(W[order[p]][order[q]] for p in range(k) for q in range(p + 1, k))
            checked += 1
            bad += lop != H.order_cost(inst, order)
    print(f"  {checked} (instance, order) pairs: first-match cost == constant + forward LOP weight in all but {bad}")
    return bad == 0


def section5():
    print("== 5. oracle control ==")
    rng = random.Random("exp5")
    stats = Counter()
    for k in range(0, 10):
        for t in range(25 if k <= 7 else 8):
            inst = H.generate(k, random.Random(f"exp5|{k}|{t}"))
            good = DP(inst)
            v = H.check(inst, good)
            stats[("correct", v)] += 1
            cost, order = good
            wrong = {
                "cost + 1": (cost + 1, order),
                "cost - 1": (cost - 1, order),
                "bool cost": (True, order),
                "float cost": (float(cost), order),
                "None": None,
                "bare cost": cost,
                "order as list": (cost, list(order)),
            }
            if k >= 2:  # for k = 1, (order[0],) * k is the correct order itself
                wrong["repeated rule"] = (cost, (order[0],) * k)
            if k >= 1:
                wrong["missing rule"] = (cost, order[:-1])
                wrong["extra rule"] = (cost, order + (k,))
            # honest cost of a worse order (if one exists)
            worse = [o for o in itertools.permutations(range(k)) if H.order_cost(inst, o) > cost] if k <= 6 else []
            if not worse and k > 6:
                for _ in range(50):
                    o = tuple(rng.sample(range(k), k))
                    if H.order_cost(inst, o) > cost:
                        worse = [o]
                        break
            if worse:
                o = worse[rng.randrange(len(worse))]
                wrong["worse order, honest cost"] = (H.order_cost(inst, o), o)
                wrong["worse order, optimal cost"] = (cost, o)
            # last-match semantics instead of first-match
            last = H.order_cost(inst, tuple(reversed(order)))
            if last != cost:
                wrong["cost of the reversed order"] = (last, order)
            # defaults ignored
            dsum = sum(inst[3][i] for i in range(len(inst[1])) if not any(inst[1][i]))
            if dsum:
                wrong["defaults ignored"] = (cost - dsum, order)
            for name, out in wrong.items():
                verdict = H.check(inst, out)
                stats[(name, verdict)] += 1
    rejected = sum(v for (name, verdict), v in stats.items() if name != "correct" and verdict is False)
    accepted = sum(v for (name, verdict), v in stats.items() if name != "correct" and verdict is True)
    undecided = sum(v for (name, verdict), v in stats.items() if name != "correct" and verdict is None)
    for key in sorted(stats, key=str):
        print(f"  {key}: {stats[key]}")
    print(f"  wrong outputs: {rejected} rejected, {accepted} accepted, {undecided} undecided; "
          f"correct outputs: {stats[('correct', True)]} accepted, {stats[('correct', None)]} undecided, "
          f"{stats[('correct', False)]} rejected")
    return accepted == 0 and stats[("correct", False)] == 0


if __name__ == "__main__":
    t0 = time.time()
    only = sys.argv[1:]
    results = {}
    for name, fn in (("1", section1), ("2", section2), ("3", section3), ("4", section4), ("5", section5)):
        if not only or name in only:
            results[name] = fn()
    print(f"\nsections passed: {results}  [{time.time() - t0:.1f}s]")
    sys.exit(0 if all(results.values()) else 1)
