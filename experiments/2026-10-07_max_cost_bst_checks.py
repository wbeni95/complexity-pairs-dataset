#!/usr/bin/env python3
"""Checks for pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp. Every number quoted in the entry's README and
entry.json is printed by this script.

Problem. Weights w(i, j) for 0 <= i < j <= n and the interval recurrence
    c(i, i) = 0,   c(i, j) = w(i, j) + opt_{i<k<=j} [c(i, k-1) + c(k, j)],
with opt = max when w is monotone under inclusion (w(b, c) <= w(a, d) whenever a <= b < c <= d) and opt = min when
w is anti-monotone. Theorem E' (the endpoint law): under this precondition every interval (i, j) has an optimal
root k in {i+1, j}, so c(i, j) = w(i, j) + opt(c(i+1, j), c(i, j-1)). The maximum-cost BST is the instance
opt = max, w(i, j) = q_i + sum_{l=i+1..j} (p_l + q_l).

The DP code in sections E1-E5, B and C is written here and does not import the entry's implementations; the
random families come from the entry's harness (instance_of). Sections O and N run the implementations themselves.

Sections
  E1  exhaustive: every monotone table with values 0..V-1 on n nodes for 13 scopes (n, V), enumerated by
      increasing interval length with the lower bound max(w(i+1, j), w(i, j-1)). Per table, max form with w and min
      form with -w: an endpoint optimum in every interval, and the endpoint DP equal to the full DP on every
      interval. Also: tables with an interior maximiser somewhere, strictly monotone tables, and tables that are
      not separable as F(j) - G(i) (i.e. not BST weights of any signed frequencies).
  E2  strict monotonicity: every STRICTLY monotone table with values 0..6, n = 4 and 5: no interior optimum, max
      form with w and min form with -w.
  E3  the proof of Theorem E' run as an algorithm, over every monotone table of 7 scopes (n = 3..7): from every
      optimal tree with an interior root (subtrees replaced by optimal path trees), Delta_R and Delta_L from the
      formulas and from the explicit tree values; Delta_R, Delta_L <= 0, Delta_R + Delta_L >= 0, hence both 0;
      right rotations until the root is i+1, every rotated tree optimal (with path subtrees while its root is
      interior); finally an optimal path tree.
  E4  -inf entries: every table with values in {-inf, 0, 1, 2} that is monotone in the extended order, n = 1..4,
      and the mirror (values {+inf, 0, -1, -2}, anti-monotone, under min).
  E5  random families of the harness: every general monotone family (max) and every anti-monotone family (min),
      400 instances each with n = 1..14 (full sets of optimal roots) and 40 each with n = 15..60 (every interval);
      separability counts; the O(n^2) local test of the harness against the O(n^4) definition on random tables.
  B   BST weights: the adjacent-sum condition against monotonicity by the definition, exhaustively for n = 2, 3
      (values -2..2) and n = 4 (values -1..1); the endpoint DP on the instances that satisfy it and on those that
      do not; strict adjacent sums (two exhaustive families): no interior maximiser; an example with a negative
      frequency.
  C   controls outside the precondition: monotone families under MIN, anti-monotone families under MAX, iid random
      tables under max and min, the smallest n = 3 counterexamples, the optimal BST with p = (1, 1, 1), q = 0,
      exhaustive BST frequencies -2..2 at n = 3, a larger counterexample, random BST frequencies -20..20.
  O   the oracle harness.check: composition of the validator's V1 battery and the verdicts on every implementation
      output; wrong values presented on the battery plus extra seeds and on every family; the certificate tier;
      inputs outside the precondition.
  N   exact counts of the implementations (CountingInt): comparisons, additions, calls of the plain recursion,
      checked value by value against the closed forms; a SHA-256 digest of the count series (compare it across
      Python versions); the validator's own V2 fits, rivals and shape diagnostic.

Deterministic (fixed seed strings). Run from the repository root:
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_max_cost_bst_checks.py [--sections E1,E2,...] [--json OUT]

The tallies are printed as dictionaries. After each section, one line per check starts with [PASS] or [FAIL]:
E1, E2, E4 (endpoint optimum and exact endpoint DP on every table; no interior optimum under strict monotonicity),
E3 (the proof's procedure succeeds in every case), E5 (precondition, endpoint law and endpoint DP on every family
instance; the harness's local test equals the definition), B (adjacent-sum condition equals monotonicity; exact
endpoint DP on every monotone instance; no interior maximiser under strict adjacent sums; the signed example), C
(exhaustive n = 3 BST scope, values -2..2: 8831 of the 78125 instances fail, all outside the precondition, 383 with
negative frequencies only in q and 383 only in p, and p = (0, -1, 0), q = 0 is the only failure with total absolute
frequency 1, as published), O (every implementation output on the V1 battery accepted; every true value accepted and
every wrong value rejected; the certificate tier valid and tight; outside the precondition no true value rejected, no
wrong value accepted and every wrong value with n <= 10 rejected), N (every count equals its closed form). The run
ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1); with --sections, only the chosen
sections are checked. The other tallies (interior maximisers, separability, the other controls of section C, the
battery composition, the digest and the validator's V2 fits) are reported, not checked.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
import math
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp"
sys.path.insert(0, str(ROOT))
INF = math.inf


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "mcb_checks_harness")
REC_MOD = _load(ENTRY / "implementations" / "recursion.py", "mcb_checks_rec")
REC = REC_MOD.maxbst_recursive
CUB = _load(ENTRY / "implementations" / "cubic_dp.py", "mcb_checks_cub").maxbst_cubic
END = _load(ENTRY / "implementations" / "endpoint_dp.py", "mcb_checks_end").maxbst_endpoint
ENTRY_JSON = json.loads((ENTRY / "entry.json").read_text(encoding="utf-8"))


def say(*parts):
    print(*parts, flush=True)


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


# ------------------------------------------------------------------------------------------------
# DP code written here (lists of lists, w[i][j] for i < j)
# ------------------------------------------------------------------------------------------------

def full_dp(w, n, maximise=True):
    """c table and the list of optimal roots of every interval (all roots tried)."""
    c = [[0] * (n + 1) for _ in range(n + 1)]
    opt = [[None] * (n + 1) for _ in range(n + 1)]
    for d in range(1, n + 1):
        for i in range(n - d + 1):
            j = i + d
            best, arg = None, None
            for k in range(i + 1, j + 1):
                v = c[i][k - 1] + c[k][j]
                if best is None or (v > best if maximise else v < best):
                    best, arg = v, [k]
                elif v == best:
                    arg.append(k)
            c[i][j] = w[i][j] + best
            opt[i][j] = arg
    return c, opt


def endpoint_dp(w, n, maximise=True):
    e = [[0] * (n + 1) for _ in range(n + 1)]
    for d in range(1, n + 1):
        for i in range(n - d + 1):
            j = i + d
            if d == 1:
                e[i][j] = w[i][j]
            else:
                a, b = e[i + 1][j], e[i][j - 1]
                e[i][j] = w[i][j] + ((a if a >= b else b) if maximise else (a if a <= b else b))
    return e


def endpoint_report(w, n, maximise=True):
    """(an endpoint optimum in every interval, endpoint DP equal on every interval, intervals with an interior
    optimal root)."""
    c, opt = full_dp(w, n, maximise)
    e = endpoint_dp(w, n, maximise)
    ends = total = interior = 0
    eq = True
    for i in range(n + 1):
        for j in range(i + 1, n + 1):
            total += 1
            ends += (i + 1 in opt[i][j]) or (j in opt[i][j])
            interior += any(i + 1 < k < j for k in opt[i][j])
            eq = eq and e[i][j] == c[i][j]
    return ends == total, eq, interior


def is_monotone_def(w, n):
    """Monotone under inclusion by the definition, O(n^4)."""
    for a in range(n + 1):
        for d in range(a + 1, n + 1):
            for b in range(a, d):
                for c in range(b + 1, d + 1):
                    if w[b][c] > w[a][d]:
                        return False
    return True


def is_monotone_local(w, n, strict=False):
    for d in range(2, n + 1):
        for i in range(n - d + 1):
            j = i + d
            m = max(w[i + 1][j], w[i][j - 1])
            if w[i][j] < m or (strict and w[i][j] == m):
                return False
    return True


def is_separable(w, n):
    """w(i, j) = F(j) - G(i) for some F, G  <=>  w(a, c) + w(b, d) = w(a, d) + w(b, c) for all a < b < c < d."""
    for a in range(n + 1):
        for b in range(a + 1, n + 1):
            for c in range(b + 1, n + 1):
                for d in range(c + 1, n + 1):
                    if w[a][c] + w[b][d] != w[a][d] + w[b][c]:
                        return False
    return True


def neg(w):
    return [[None if x is None else -x for x in row] for row in w]


def bst_w(p, q):
    n = len(p)
    w = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        acc = q[i]
        for j in range(i + 1, n + 1):
            acc += p[j - 1] + q[j]
            w[i][j] = acc
    return w


def bst_adjacent_sums(p, q):
    """q_(l-1) + p_l >= 0 (l = 1..n-1) and p_l + q_l >= 0 (l = 2..n); p[l-1] is p_l."""
    n = len(p)
    return all(q[l - 1] + p[l - 1] >= 0 for l in range(1, n)) and all(p[l - 1] + q[l] >= 0 for l in range(2, n + 1))


def monotone_tables(n, values, strict=False):
    """Every table that is monotone (strictly, if asked) in the order of the list `values`."""
    ivs = [(i, i + d) for d in range(1, n + 1) for i in range(n - d + 1)]
    idx = [[None] * (n + 1) for _ in range(n + 1)]
    V = len(values)

    def rec(t):
        if t == len(ivs):
            yield [[None if x is None else values[x] for x in row] for row in idx]
            return
        i, j = ivs[t]
        lb = 0 if j - i == 1 else max(idx[i + 1][j], idx[i][j - 1]) + (1 if strict else 0)
        for v in range(lb, V):
            idx[i][j] = v
            yield from rec(t + 1)
        idx[i][j] = None

    yield from rec(0)


def table_lists(inst):
    sense, w = H.as_table(inst)
    return sense, [list(row) for row in w], len(w) - 1


# ------------------------------------------------------------------------------------------------
# E1, E2: Theorem E' exhaustively; the strict corollary
# ------------------------------------------------------------------------------------------------

E1_SCOPES = [(1, 4), (2, 4), (3, 4), (4, 3), (4, 4), (5, 3), (5, 4), (6, 3), (7, 3), (7, 2), (8, 2), (9, 2), (10, 2)]


def section_E1():
    out, tot = [], Counter()
    for n, V in E1_SCOPES:
        r = Counter()
        for w in monotone_tables(n, list(range(V))):
            r["tables"] += 1
            ends, eq, interior = endpoint_report(w, n, True)
            r["max_endpoint_optimum_every_interval"] += ends
            r["max_endpoint_dp_equal_every_interval"] += eq
            r["tables_with_an_interior_maximiser"] += interior > 0
            ends2, eq2, _ = endpoint_report(neg(w), n, False)
            r["min_neg_endpoint_optimum_every_interval"] += ends2
            r["min_neg_endpoint_dp_equal_every_interval"] += eq2
            if is_monotone_local(w, n, strict=True):
                r["strictly_monotone"] += 1
                r["strictly_monotone_without_interior_maximiser"] += interior == 0
            r["not_separable"] += not is_separable(w, n)
        out.append({"n": n, "values": f"0..{V - 1}", **r})
        tot.update(r)
        say("E1", out[-1])
    say("E1 totals", dict(tot))
    check_line(tot["max_endpoint_optimum_every_interval"] == tot["max_endpoint_dp_equal_every_interval"] == tot["tables"],
               f"E1: max form with w: an endpoint optimum and an exact endpoint DP in every interval of all "
               f"{tot['tables']} monotone tables")
    check_line(tot["min_neg_endpoint_optimum_every_interval"] == tot["min_neg_endpoint_dp_equal_every_interval"]
               == tot["tables"], f"E1: min form with -w: an endpoint optimum and an exact endpoint DP in every interval "
                                 f"of all {tot['tables']} tables")
    check_line(tot["strictly_monotone_without_interior_maximiser"] == tot["strictly_monotone"],
               f"E1: none of the {tot['strictly_monotone']} strictly monotone tables has an interior maximiser")
    return {"scopes": out, "totals": dict(tot)}


def section_E2():
    out, tot = [], Counter()
    for n, V in ((4, 7), (5, 7)):
        r = Counter()
        for w in monotone_tables(n, list(range(V)), strict=True):
            r["strict_tables"] += 1
            _, eq, interior = endpoint_report(w, n, True)
            r["max_no_interior_maximiser"] += interior == 0
            r["max_endpoint_dp_equal_every_interval"] += eq
            _, eq2, interior2 = endpoint_report(neg(w), n, False)
            r["min_neg_no_interior_minimiser"] += interior2 == 0
            r["min_neg_endpoint_dp_equal_every_interval"] += eq2
        out.append({"n": n, "values": f"0..{V - 1}", **r})
        tot.update(r)
        say("E2", out[-1])
    say("E2 totals", dict(tot))
    check_line(tot["max_no_interior_maximiser"] == tot["max_endpoint_dp_equal_every_interval"] == tot["strict_tables"]
               and tot["min_neg_no_interior_minimiser"] == tot["min_neg_endpoint_dp_equal_every_interval"]
               == tot["strict_tables"],
               f"E2: no interior optimum and an exact endpoint DP on all {tot['strict_tables']} strictly monotone tables, "
               f"max form with w and min form with -w")
    return {"scopes": out, "totals": dict(tot)}


# ------------------------------------------------------------------------------------------------
# E3: the proof run as an algorithm. A tree on (lo, hi) is None (lo == hi) or (k, left, right).
# ------------------------------------------------------------------------------------------------

def tree_value(t, lo, hi, w):
    if t is None:
        return 0
    k, L, R = t
    return w[lo][hi] + tree_value(L, lo, k - 1, w) + tree_value(R, k, hi, w)


def is_path(t):
    while t is not None:
        _, L, R = t
        if L is not None and R is not None:
            return False
        t = L if L is not None else R
    return True


def optimal_path(lo, hi, e):
    """A path tree on (lo, hi) that follows the endpoint table e (max; ties: the left end)."""
    if lo == hi:
        return None
    if hi - lo == 1:
        return (hi, None, None)
    if e[lo + 1][hi] >= e[lo][hi - 1]:
        return (lo + 1, None, optimal_path(lo + 1, hi, e))
    return (hi, optimal_path(lo, hi - 1, e), None)


def rotate_right(t):
    k, (kl, A, B), R = t
    return (kl, A, (k, B, R))


def rotate_left(t):
    k, L, (kr, B, C) = t
    return (kr, (k, L, B), C)


def run_proof(w, i, j, k, c, e):
    """The proof's procedure from an optimal tree on (i, j) with interior root k. Returns (ok, rotations, detail)."""
    T = (k, optimal_path(i, k - 1, e), optimal_path(k, j, e))
    best = c[i][j]
    if tree_value(T, i, j, w) != best:
        return False, 0, "start tree not optimal"
    rotations = 0
    while True:
        root, L, R = T
        if root == i + 1 or root == j:
            break
        if not (is_path(L) and is_path(R)):
            return False, rotations, "subtrees not paths"
        kl, kr = L[0], R[0]
        dR = w[kl][j] - w[i][root - 1]
        dL = w[i][kr - 1] - w[root][j]
        TR, TL = rotate_right(T), rotate_left(T)
        vT = tree_value(T, i, j, w)
        if tree_value(TR, i, j, w) - vT != dR or tree_value(TL, i, j, w) - vT != dL:
            return False, rotations, "delta formula"
        if not (dR <= 0 and dL <= 0):
            return False, rotations, "optimality"
        if dR + dL < 0:
            return False, rotations, "monotonicity sum"
        if not (dR == 0 and dL == 0):
            return False, rotations, "deltas not both zero"
        T = TR
        rotations += 1
        if tree_value(T, i, j, w) != best:
            return False, rotations, "rotated tree not optimal"
    root = T[0]
    T = (root, None, optimal_path(i + 1, j, e)) if root == i + 1 else (root, optimal_path(i, j - 1, e), None)
    if not is_path(T) or tree_value(T, i, j, w) != best:
        return False, rotations, "final tree"
    return True, rotations, ""


E3_SCOPES = ((3, 4), (4, 4), (5, 3), (5, 4), (6, 3), (6, 2), (7, 2))


def section_E3():
    out, tot, rot_tot = [], Counter(), Counter()
    for n, V in E3_SCOPES:
        r, rot, fails = Counter(), Counter(), []
        for w in monotone_tables(n, list(range(V))):
            c, opt = full_dp(w, n, True)
            e = endpoint_dp(w, n, True)
            for i in range(n + 1):
                for j in range(i + 3, n + 1):
                    for k in opt[i][j]:
                        if i + 1 < k < j:
                            ok, nr, detail = run_proof(w, i, j, k, c, e)
                            r["cases"] += 1
                            r["ok"] += ok
                            rot[nr] += 1
                            if not ok and len(fails) < 5:
                                fails.append({"w": w, "i": i, "j": j, "k": k, "detail": detail})
        out.append({"n": n, "values": f"0..{V - 1}", **r, "rotations": dict(sorted(rot.items())), "failures": fails})
        tot.update(r)
        rot_tot.update(rot)
        say("E3", out[-1])
    say("E3 totals", dict(tot), "rotations needed:", dict(sorted(rot_tot.items())))
    check_line(tot["cases"] > 0 and tot["ok"] == tot["cases"],
               f"E3: the proof's procedure succeeds in all {tot['cases']} cases (optimal trees with an interior root)")
    return {"scopes": out, "totals": dict(tot), "rotations": dict(sorted(rot_tot.items()))}


# ------------------------------------------------------------------------------------------------
# E4: -inf entries
# ------------------------------------------------------------------------------------------------

def section_E4():
    out = {"minus_inf_under_max": Counter(), "plus_inf_under_min": Counter()}
    for n in range(1, 5):
        r = out["minus_inf_under_max"]
        for w in monotone_tables(n, [-INF, 0, 1, 2]):
            r["tables"] += 1
            r["with_a_minus_inf_entry"] += any(x == -INF for row in w for x in row if x is not None)
            ends, eq, _ = endpoint_report(w, n, True)
            r["endpoint_optimum_every_interval"] += ends
            r["endpoint_dp_equal_every_interval"] += eq
        r = out["plus_inf_under_min"]
        for w in monotone_tables(n, [INF, 0, -1, -2]):  # anti-monotone in the usual order
            r["tables"] += 1
            r["with_a_plus_inf_entry"] += any(x == INF for row in w for x in row if x is not None)
            ends, eq, _ = endpoint_report(w, n, False)
            r["endpoint_optimum_every_interval"] += ends
            r["endpoint_dp_equal_every_interval"] += eq
    out = {k: dict(v) for k, v in out.items()}
    say("E4", out)
    for key, label in (("minus_inf_under_max", "-inf entries under max"), ("plus_inf_under_min", "+inf entries under min")):
        r = out[key]
        check_line(r["endpoint_optimum_every_interval"] == r["endpoint_dp_equal_every_interval"] == r["tables"],
                   f"E4: {label}: an endpoint optimum and an exact endpoint DP in every interval of all {r['tables']} "
                   f"tables")
    return out


# ------------------------------------------------------------------------------------------------
# E5: random families; the local test against the definition
# ------------------------------------------------------------------------------------------------

def section_E5():
    out, tot = {}, Counter()
    for fam in H.GENERAL_FAMILIES + H.MIN_FAMILIES:
        r = Counter()
        rng = random.Random(f"mcb-checks|E5|{fam}")
        for _ in range(400):
            sense, w, n = table_lists(H.instance_of(fam, rng.randint(1, 14), rng))
            maximise = sense == "max"
            r["precondition_holds"] += is_monotone_local(w if maximise else neg(w), n)
            ends, eq, interior = endpoint_report(w, n, maximise)
            r["small_instances"] += 1
            r["small_endpoint_optimum_every_interval"] += ends
            r["small_endpoint_dp_equal_every_interval"] += eq
            r["small_with_an_interior_optimum"] += interior > 0
            if n >= 3:
                r["small_n_ge_3"] += 1
                r["small_n_ge_3_not_separable"] += not is_separable(w, n)
        for _ in range(40):
            sense, w, n = table_lists(H.instance_of(fam, rng.randint(15, 60), rng))
            maximise = sense == "max"
            r["precondition_holds"] += is_monotone_local(w if maximise else neg(w), n)
            c, _ = full_dp(w, n, maximise)
            e = endpoint_dp(w, n, maximise)
            r["large_instances"] += 1
            r["large_endpoint_dp_equal_every_interval"] += all(
                e[i][j] == c[i][j] for i in range(n + 1) for j in range(i + 1, n + 1))
        out[fam] = dict(r)
        tot.update(r)
        say("E5", fam, out[fam])
    by_cat = {}
    for cat, fams in (("general_max", H.GENERAL_FAMILIES), ("anti_min", H.MIN_FAMILIES)):
        c = Counter()
        for f in fams:
            c.update(out[f])
        by_cat[cat] = {k: c[k] for k in ("small_n_ge_3", "small_n_ge_3_not_separable")}
    # the O(n^2) local test of the harness against the O(n^4) definition
    rng = random.Random("mcb-checks|E5|local")
    loc = Counter()
    for _ in range(3000):
        n = rng.randint(1, 6)
        w = tuple(tuple(rng.randint(0, 2) + (j - i) if j > i else None for j in range(n + 1)) for i in range(n + 1))
        d = is_monotone_def(w, n)
        loc["tables"] += 1
        loc["monotone"] += d
        loc["harness_local_test_equals_definition"] += H.is_monotone(w) == d
    res = {"families": out, "totals": dict(tot), "separability_by_category": by_cat, "local_test": dict(loc)}
    say("E5 totals", dict(tot))
    say("E5 separability (n >= 3)", by_cat)
    say("E5 local test", dict(loc))
    check_line(tot["precondition_holds"] == tot["small_instances"] + tot["large_instances"],
               f"E5: the precondition holds on all {tot['small_instances'] + tot['large_instances']} family instances")
    check_line(tot["small_endpoint_optimum_every_interval"] == tot["small_endpoint_dp_equal_every_interval"]
               == tot["small_instances"] and tot["large_endpoint_dp_equal_every_interval"] == tot["large_instances"],
               f"E5: an endpoint optimum and an exact endpoint DP in every interval of all {tot['small_instances']} "
               f"instances with n <= 14; an exact endpoint DP on all {tot['large_instances']} with n = 15..60")
    check_line(loc["harness_local_test_equals_definition"] == loc["tables"],
               f"E5: the harness's O(n^2) local test equals the O(n^4) definition on all {loc['tables']} tables")
    return res


# ------------------------------------------------------------------------------------------------
# B: BST weights
# ------------------------------------------------------------------------------------------------

def section_B():
    out, tot = [], Counter()
    for n, vals in ((2, range(-2, 3)), (3, range(-2, 3)), (4, range(-1, 2))):
        r = Counter()
        for t in itertools.product(vals, repeat=2 * n + 1):
            p, q = t[:n], t[n:]
            w = bst_w(p, q)
            loc = bst_adjacent_sums(p, q)
            mono = is_monotone_def(w, n)
            r["instances"] += 1
            r["adjacent_sum_condition_equals_definition"] += loc == mono
            if mono:
                r["monotone"] += 1
                r["monotone_with_a_negative_frequency"] += any(x < 0 for x in t)
                _, eq, _ = endpoint_report(w, n, True)
                r["monotone_endpoint_dp_exact_every_interval"] += eq
            else:
                c, _ = full_dp(w, n, True)
                r["not_monotone"] += 1
                r["not_monotone_endpoint_dp_exact_at_root"] += endpoint_dp(w, n, True)[0][n] == c[0][n]
        out.append({"n": n, "values": f"{vals.start}..{vals.stop - 1}", **r})
        tot.update(r)
        say("B", out[-1])
    say("B totals", dict(tot))
    # strict adjacent sums: no interval has an interior maximiser
    cases = [(n, (0,) * n, q) for n in range(3, 7) for q in itertools.product((1, 2), repeat=n + 1)]
    cases += [(n, p, q) for n in (3, 4) for p in itertools.product((1, 2), repeat=n)
              for q in itertools.product((0, 1), repeat=n + 1)]
    strict = Counter()
    for n, p, q in cases:
        w = bst_w(p, q)
        _, eq, interior = endpoint_report(w, n, True)
        strict["instances"] += 1
        strict["strict_local_inequalities"] += is_monotone_local(w, n, strict=True)
        strict["no_interior_maximiser"] += interior == 0
    say("B strict adjacent sums (p = 0, q in {1,2}, n = 3..6; p in {1,2}, q in {0,1}, n = 3, 4)", dict(strict))
    check_line(tot["adjacent_sum_condition_equals_definition"] == tot["instances"],
               f"B: the adjacent-sum condition equals monotonicity by the definition on all {tot['instances']} instances")
    check_line(tot["monotone_endpoint_dp_exact_every_interval"] == tot["monotone"],
               f"B: an exact endpoint DP in every interval of all {tot['monotone']} monotone instances")
    check_line(strict["strict_local_inequalities"] == strict["no_interior_maximiser"] == strict["instances"],
               f"B: strict adjacent sums: strict local inequalities and no interior maximiser on all "
               f"{strict['instances']} instances")
    p, q = (1, -1, 1), (0, 1, 1, 0)
    w = bst_w(p, q)
    c, opt = full_dp(w, 3, True)
    example = {"p": p, "q": q, "adjacent_sum_condition": bst_adjacent_sums(p, q), "optimum": c[0][3],
               "endpoint_dp": endpoint_dp(w, 3, True)[0][3], "optimal_roots_of_(0,3)": opt[0][3]}
    say("B example with a negative frequency", example)
    check_line(example["adjacent_sum_condition"] and example["endpoint_dp"] == example["optimum"],
               "B: the example p = (1, -1, 1), q = (0, 1, 1, 0) satisfies the adjacent-sum condition and the endpoint "
               "DP gives the maximum")
    return {"scopes": out, "totals": dict(tot), "strict": dict(strict), "example": example}


# ------------------------------------------------------------------------------------------------
# C: controls outside the precondition
# ------------------------------------------------------------------------------------------------

def section_C():
    out = {"monotone_under_min": {}, "antimonotone_under_max": {}}
    for key, fams, maximise in (("monotone_under_min", H.GENERAL_FAMILIES, False),
                                ("antimonotone_under_max", H.MIN_FAMILIES, True)):
        for fam in fams:
            rng = random.Random(f"mcb-checks|C|{key}|{fam}")
            ok = 0
            for _ in range(300):
                _, w, n = table_lists(H.instance_of(fam, rng.randint(3, 12), rng))
                c, _ = full_dp(w, n, maximise)
                ok += endpoint_dp(w, n, maximise)[0][n] == c[0][n]
            out[key][fam] = {"instances": 300, "endpoint_dp_exact_at_root": ok}
        out[key + "_total"] = {"instances": 300 * len(fams),
                               "endpoint_dp_exact_at_root": sum(v["endpoint_dp_exact_at_root"]
                                                                for v in out[key].values())}
        say("C", key, out[key + "_total"])
    for sense in ("max", "min"):
        rng = random.Random(f"mcb-checks|C|iid|{sense}")
        maximise = sense == "max"
        ok = holds = 0
        for _ in range(3000):
            n = rng.randint(3, 12)
            w = [[rng.randint(0, 20) if j > i else None for j in range(n + 1)] for i in range(n + 1)]
            holds += is_monotone_local(w if maximise else neg(w), n)
            c, _ = full_dp(w, n, maximise)
            ok += endpoint_dp(w, n, maximise)[0][n] == c[0][n]
        out[f"iid_0_20_under_{sense}"] = {"instances": 3000, "endpoint_dp_exact_at_root": ok,
                                          "precondition_holds": holds}
        say("C", f"iid random tables 0..20 under {sense}", out[f"iid_0_20_under_{sense}"])
    # smallest counterexamples among all n = 3 tables with values 0..2 (smallest sum of entries, first found)
    n = 3
    ivs = [(i, j) for i in range(n + 1) for j in range(i + 1, n + 1)]
    best = {"monotone_under_min": None, "any_under_max": None}
    cnt = Counter()
    for vals in itertools.product(range(3), repeat=len(ivs)):
        w = [[None] * (n + 1) for _ in range(n + 1)]
        for (i, j), v in zip(ivs, vals):
            w[i][j] = v
        mono = is_monotone_local(w, n)
        cnt["tables"] += 1
        cnt["monotone_tables"] += mono
        for key, maximise, need_mono in (("monotone_under_min", False, True), ("any_under_max", True, False)):
            if need_mono and not mono:
                continue
            c, opt = full_dp(w, n, maximise)
            e = endpoint_dp(w, n, maximise)
            if e[0][n] != c[0][n]:
                cnt[key + "_failures"] += 1
                if best[key] is None or sum(vals) < best[key]["sum"]:
                    best[key] = {"sum": sum(vals), "nonzero": {f"{i},{j}": w[i][j] for i, j in ivs if w[i][j]},
                                 "optimum": c[0][n], "optimal_roots_of_(0,3)": opt[0][n], "endpoint_dp": e[0][n],
                                 "monotone": mono}
    out["n3_tables_0_2"] = {**cnt, "smallest": best}
    say("C n = 3 tables 0..2", out["n3_tables_0_2"])
    # the optimal BST (min) with p = (1, 1, 1), q = 0: w(i, j) = j - i
    w = bst_w((1, 1, 1), (0, 0, 0, 0))
    check_line(all(w[i][j] == j - i for i in range(4) for j in range(i + 1, 4)),
               "C: p = (1, 1, 1), q = 0 gives w(i, j) = j - i")
    c, opt = full_dp(w, 3, False)
    out["optimal_bst_p111"] = {"minimum": c[0][3], "minimising_roots_of_(0,3)": opt[0][3],
                               "endpoint_dp_min": endpoint_dp(w, 3, False)[0][3]}
    say("C optimal BST p = (1, 1, 1), q = 0 under min", out["optimal_bst_p111"])
    # BST frequencies -2..2, n = 3, exhaustive
    cnt, fails = Counter(), []
    for t in itertools.product(range(-2, 3), repeat=7):
        p, q = t[:3], t[3:]
        w = bst_w(p, q)
        c, _ = full_dp(w, 3, True)
        e = endpoint_dp(w, 3, True)[0][3]
        cnt["instances"] += 1
        if e != c[0][3]:
            cnt["failures"] += 1
            cnt["failures_outside_the_precondition"] += not bst_adjacent_sums(p, q)
            cnt["failures_with_p_nonnegative"] += min(p) >= 0
            cnt["failures_with_q_nonnegative"] += min(q) >= 0
            fails.append((sum(abs(x) for x in t), p, q, c[0][3], e))
    fails.sort()
    l1_min = fails[0][0]
    out["bst_n3_values_-2_2"] = {**cnt, "smallest_total_absolute_frequency": l1_min,
                                 "failures_at_that_total": [{"p": f[1], "q": f[2], "optimum": f[3], "endpoint_dp": f[4]}
                                                            for f in fails if f[0] == l1_min]}
    for p, q in (((0, -1, 0), (0, 0, 0, 0)), ((0, 0, 0), (0, -1, -1, 0)), ((-11, -3, 11), (18, -8, -12, -7))):
        w = bst_w(p, q)
        c, opt = full_dp(w, 3, True)
        out.setdefault("bst_examples", []).append({"p": p, "q": q, "maximum": c[0][3], "maximising_roots": opt[0][3],
                                                   "endpoint_dp": endpoint_dp(w, 3, True)[0][3],
                                                   "adjacent_sum_condition": bst_adjacent_sums(p, q)})
    say("C BST n = 3, values -2..2", out["bst_n3_values_-2_2"])
    check_line(cnt["failures_outside_the_precondition"] == cnt["failures"],
               f"C: BST n = 3, values -2..2: all {cnt['failures']} failures of the endpoint DP lie outside the "
               f"precondition")
    check_line(cnt["instances"] == 78125 and cnt["failures"] == 8831,
               f"C: BST n = 3, values -2..2: {cnt['failures']} of the {cnt['instances']} instances fail (published: "
               f"8831 of 78125)")
    check_line(cnt["failures_with_p_nonnegative"] == 383 and cnt["failures_with_q_nonnegative"] == 383,
               f"C: BST n = 3, values -2..2: failures with negative frequencies only in q (p >= 0) "
               f"{cnt['failures_with_p_nonnegative']}, only in p (q >= 0) {cnt['failures_with_q_nonnegative']} "
               f"(published: 383 and 383)")
    at_min = out["bst_n3_values_-2_2"]["failures_at_that_total"]
    check_line(l1_min == 1 and at_min == [{"p": (0, -1, 0), "q": (0, 0, 0, 0), "optimum": -1, "endpoint_dp": -2}],
               f"C: BST n = 3, values -2..2: failures with the smallest total absolute frequency {l1_min}: {at_min} "
               f"(published: only p = (0, -1, 0), q = (0, 0, 0, 0), maximum -1, endpoint DP -2)")
    for ex in out["bst_examples"]:
        say("C BST example", ex)
    rng = random.Random("mcb-checks|C|bst-signed")
    ok = 0
    for _ in range(3000):
        n = rng.randint(1, 14)
        p = tuple(rng.randint(-20, 20) for _ in range(n))
        q = tuple(rng.randint(-20, 20) for _ in range(n + 1))
        w = bst_w(p, q)
        c, _ = full_dp(w, n, True)
        ok += endpoint_dp(w, n, True)[0][n] == c[0][n]
    out["bst_signed_-20_20"] = {"instances": 3000, "endpoint_dp_exact_at_root": ok}
    say("C BST frequencies -20..20, n = 1..14", out["bst_signed_-20_20"])
    return out


# ------------------------------------------------------------------------------------------------
# O: the oracle harness.check
# ------------------------------------------------------------------------------------------------

def to_dict_table(inst):
    """(maximise, n, w as a dict over (i, j)); BST weights summed here."""
    a, b = inst
    if isinstance(a, str):
        n = len(b) - 1
        return a == "max", n, {(i, j): b[i][j] for i in range(n + 1) for j in range(i + 1, n + 1)}
    n = len(a)
    w = {}
    for i in range(n + 1):
        s = b[i]
        for j in range(i + 1, n + 1):
            s += a[j - 1] + b[j]
            w[(i, j)] = s
    return True, n, w


def category(inst):
    if not isinstance(inst[0], str):
        return "bst"
    return "general_max" if inst[0] == "max" else "anti_min"


def dict_dp(maximise, n, w):
    c = {(i, i): 0 for i in range(n + 1)}
    for d in range(1, n + 1):
        for i in range(n - d + 1):
            j = i + d
            vals = [c[(i, k - 1)] + c[(k, j)] for k in range(i + 1, j + 1)]
            c[(i, j)] = w[(i, j)] + (max(vals) if maximise else min(vals))
    return c


def knuth_window(maximise, n, w):
    """Knuth's root-range restriction (root of (i, j) between the roots of (i, j-1) and (i+1, j)), largest optimum."""
    c = {(i, i): 0 for i in range(n + 1)}
    r = {}
    for i in range(n):
        c[(i, i + 1)] = w[(i, i + 1)]
        r[(i, i + 1)] = i + 1
    for d in range(2, n + 1):
        for i in range(n - d + 1):
            j = i + d
            best, arg = None, None
            lo, hi = r[(i, j - 1)], r[(i + 1, j)]
            if lo > hi:
                lo, hi = i + 1, j
            for k in range(lo, hi + 1):
                v = c[(i, k - 1)] + c[(k, j)]
                if best is None or (v >= best if maximise else v <= best):
                    best, arg = v, k
            c[(i, j)] = w[(i, j)] + best
            r[(i, j)] = arg
    return c[(0, n)]


def tree_sum(n, w, choose):
    total, stack = 0, [(0, n)]
    while stack:
        i, j = stack.pop()
        if i == j:
            continue
        k = choose(i, j)
        total += w[(i, j)]
        stack.append((i, k - 1))
        stack.append((k, j))
    return total


def wrong_values(inst, ref, rng):
    maximise, n, w = to_dict_table(inst)
    c = dict_dp(maximise, n, w)

    def better(x, y):
        return x >= y if maximise else x <= y

    def worse_end(i, j):
        if j - i == 1:
            return j
        return j if better(c[(i + 1, j)], c[(i, j - 1)]) else i + 1

    def greedy_w(i, j):
        if j - i == 1:
            return j
        return i + 1 if better(w[(i + 1, j)], w[(i, j - 1)]) else j

    return {
        "plus1": ref + 1,
        "minus1": ref - 1,
        "opposite_direction": dict_dp(not maximise, n, w)[(0, n)],
        "knuth_window": knuth_window(maximise, n, w),
        "left_path": tree_sum(n, w, lambda i, j: i + 1),
        "right_path": tree_sum(n, w, lambda i, j: j),
        "median_roots": tree_sum(n, w, lambda i, j: (i + 1 + j) // 2),
        "random_tree": tree_sum(n, w, lambda i, j: rng.randint(i + 1, j)),
        "worse_end_path": tree_sum(n, w, worse_end),
        "greedy_w_path": tree_sum(n, w, greedy_w),
    }


def judge(stats, inst, rng):
    maximise, n, w = to_dict_table(inst)
    ref = dict_dp(maximise, n, w)[(0, n)]
    cat = category(inst)
    stats["true_value"][cat][str(H.check(inst, ref))] += 1
    for kind, val in wrong_values(inst, ref, rng).items():
        s = stats["wrong"][(cat, kind)]
        if val == ref:
            s["equal_to_reference"] += 1
            continue
        s["presented"] += 1
        r = H.check(inst, val)
        s["rejected" if r is False else "accepted" if r is True else "undecided"] += 1


def new_stats():
    return {"true_value": defaultdict(Counter), "wrong": defaultdict(Counter)}


def merge_stats(*all_stats):
    tv, tot, kinds = defaultdict(Counter), defaultdict(Counter), defaultdict(Counter)
    for st in all_stats:
        for cat, v in st["true_value"].items():
            tv[cat].update(v)
            tv["all"].update(v)
        for (cat, kind), s in st["wrong"].items():
            tot[cat].update(s)
            tot["all"].update(s)
            kinds[kind].update(s)
    return {"true_value": {k: dict(v) for k, v in tv.items()}, "wrong_by_category": {k: dict(v) for k, v in tot.items()},
            "wrong_by_kind": {k: dict(v) for k, v in kinds.items()}}


def certificate(inst):
    return H.table_certificate(*inst) if isinstance(inst[0], str) else H.path_certificate(*inst)


def section_O():
    th = ENTRY_JSON["test_harness"]
    rec_max = ENTRY_JSON["algorithms"][0]["harness"]["v1_max_n"]
    res = {}
    # O1: the validator's V1 battery (seeds "<id>|v1|<n>|<trial>")
    comp = {"category": Counter(), "family": Counter(), "tier": Counter(), "verdicts": Counter()}
    redraw_bad = 0
    for n in th["v1_sizes"]:
        for trial in range(th.get("trials", 3)):
            seed = f"{ENTRY_JSON['id']}|v1|{n}|{trial}"
            inst = H.generate(n, random.Random(seed))
            r2 = random.Random(seed)  # re-draw to read the family name
            cat_list = (H.FAMILIES, H.GENERAL_FAMILIES, H.MIN_FAMILIES)[r2.randrange(3)]
            fam = cat_list[r2.randrange(len(cat_list))]
            redraw_bad += H.instance_of(fam, n, r2) != inst
            comp["category"][category(inst)] += 1
            comp["family"][fam] += 1
            comp["tier"]["enumeration" if n <= H.BRUTE_MAX_N else "certificate" if n <= H.CERT_MAX_N else "none"] += 1
            for name, fn in (("recursion", REC), ("cubic", CUB), ("endpoint", END)):
                if name == "recursion" and n > rec_max:
                    continue
                comp["verdicts"][f"{name}:{H.check(inst, fn(inst))}"] += 1
    res["O1_battery"] = {k: dict(v) for k, v in comp.items()}
    res["O1_battery"]["instances"] = sum(comp["category"].values())
    res["O1_battery"]["families_present"] = len(comp["family"])
    say("O1 V1 battery", {k: v for k, v in res["O1_battery"].items() if k != "family"})
    check_line(redraw_bad == 0, f"O1: re-drawing the family reproduces every battery instance ({redraw_bad} differ)")
    check_line(all(k.endswith(":True") for k in comp["verdicts"]),
               f"O1: every implementation output on the V1 battery is accepted (verdicts {dict(comp['verdicts'])}; "
               f"published: all 408 of each DP and all 264 of the recursion)")
    # O2: wrong values on the battery plus 40 extra seeds per size, and on every family at 15 sizes x 3 seeds
    st_a, st_b = new_stats(), new_stats()
    rng = random.Random("mcb-checks|O2|wrong-a")
    count_a = Counter()
    for n in th["v1_sizes"]:
        for trial in range(th.get("trials", 3)):
            inst = H.generate(n, random.Random(f"{ENTRY_JSON['id']}|v1|{n}|{trial}"))
            judge(st_a, inst, rng)
            count_a[category(inst)] += 1
        for s in range(40):
            inst = H.generate(n, random.Random(f"mcb-checks|O2|{n}|{s}"))
            judge(st_a, inst, rng)
            count_a[category(inst)] += 1
    rng = random.Random("mcb-checks|O2|wrong-b")
    count_b = 0
    for fam in H.ALL_FAMILIES:
        for n in list(range(1, 11)) + [11, 14, 20, 30, 50]:
            for s in range(3):
                judge(st_b, H.instance_of(fam, n, random.Random(f"mcb-checks|O2|{fam}|{n}|{s}")), rng)
                count_b += 1
    res["O2_wrong_values"] = {"instances_battery_plus_extra": sum(count_a.values()),
                              "instances_battery_plus_extra_by_category": dict(count_a),
                              "instances_every_family": count_b, **merge_stats(st_a, st_b)}
    say("O2 instances", sum(count_a.values()), "+", count_b, "=", sum(count_a.values()) + count_b)
    say("O2 true value", res["O2_wrong_values"]["true_value"])
    say("O2 wrong values by category", res["O2_wrong_values"]["wrong_by_category"])
    say("O2 wrong values by kind", res["O2_wrong_values"]["wrong_by_kind"])
    tv_all = res["O2_wrong_values"]["true_value"]["all"]
    wr_all = res["O2_wrong_values"]["wrong_by_category"]["all"]
    check_line(tv_all.get("True", 0) == sum(tv_all.values()) and wr_all.get("rejected", 0) == wr_all.get("presented", 0),
               f"O2: true values accepted {tv_all.get('True', 0)} of {sum(tv_all.values())}; wrong values rejected "
               f"{wr_all.get('rejected', 0)} of {wr_all.get('presented', 0)} (accepted {wr_all.get('accepted', 0)}, "
               f"undecided {wr_all.get('undecided', 0)})")
    # O3: the certificate tier
    small, large = Counter(), Counter()
    for fam in H.ALL_FAMILIES:
        for n in range(0, 11):
            inst = H.instance_of(fam, n, random.Random(f"mcb-checks|O3|{fam}|{n}"))
            maximise, nn, w = to_dict_table(inst)
            brute = (H.brute_force_table(*inst) if isinstance(inst[0], str) else H.brute_force_max(*inst))
            cert = certificate(inst)
            small["instances"] += 1
            small["valid_and_tight_equal_enumeration"] += cert["valid"] and cert["lower"] == cert["upper"] == brute
            small["enumeration_equals_reference"] += brute == dict_dp(maximise, nn, w)[(0, nn)]
    rng = random.Random("mcb-checks|O3|large")
    ns = []
    for cat, fams in (("bst", H.FAMILIES), ("general_max", H.GENERAL_FAMILIES), ("anti_min", H.MIN_FAMILIES)):
        for n in [rng.randint(11, 120) for _ in range(40)] + [rng.randint(150, 200) for _ in range(5)]:
            inst = H.instance_of(fams[rng.randrange(len(fams))], n, rng)
            maximise, nn, w = to_dict_table(inst)
            ref = dict_dp(maximise, nn, w)[(0, nn)]
            cert = certificate(inst)
            ok = cert["valid"] and cert["lower"] == cert["upper"] == ref
            large["instances"] += 1
            large[f"{cat}_instances"] += 1
            large["valid_and_tight_equal_reference"] += ok
            large[f"{cat}_valid_and_tight_equal_reference"] += ok
            ns.append(n)
    res["O3_certificate"] = {"small": dict(small), "large": dict(large), "large_n_range": [min(ns), max(ns)]}
    say("O3 certificate", res["O3_certificate"])
    check_line(small["valid_and_tight_equal_enumeration"] == small["enumeration_equals_reference"] == small["instances"]
               and large["valid_and_tight_equal_reference"] == large["instances"],
               f"O3: the certificate is valid and tight and equals the reference on all {small['instances']} small and "
               f"{large['instances']} large instances")
    # O4: outside the precondition
    rng = random.Random("mcb-checks|O4")

    def random_table(n, sense):
        return sense, tuple(tuple(rng.randint(0, 20) if j > i else None for j in range(n + 1)) for i in range(n + 1))

    def flipped(n, fams, sense):
        return sense, H.instance_of(fams[rng.randrange(len(fams))], n, rng)[1]

    makers = {
        "iid_random_under_max": lambda n: random_table(n, "max"),
        "iid_random_under_min": lambda n: random_table(n, "min"),
        "monotone_under_min": lambda n: flipped(n, H.GENERAL_FAMILIES, "min"),
        "antimonotone_under_max": lambda n: flipped(n, H.MIN_FAMILIES, "max"),
        "bst_frequencies_-20_20": lambda n: (tuple(rng.randint(-20, 20) for _ in range(n)),
                                             tuple(rng.randint(-20, 20) for _ in range(n + 1))),
    }
    outside, tot = {}, Counter()
    for name, make in makers.items():
        r = Counter()
        for _ in range(150):
            inst = make(rng.randint(3, 30))
            maximise, nn, w = to_dict_table(inst)
            ref = dict_dp(maximise, nn, w)[(0, nn)]
            e = END(inst)
            tier = "enumeration" if nn <= H.BRUTE_MAX_N else "certificate"
            r[f"{tier}_instances"] += 1
            r[f"{tier}_true_value_{H.check(inst, ref)}"] += 1
            if e != ref:
                r[f"{tier}_endpoint_wrong"] += 1
                r[f"{tier}_endpoint_wrong_judged_{H.check(inst, e)}"] += 1
        outside[name] = dict(r)
        tot.update(r)
    res["O4_outside_precondition"] = {"per_input_class": outside, "totals": dict(tot)}
    say("O4 outside the precondition", outside)
    say("O4 totals", dict(tot))
    true_rejected = sum(v for k, v in tot.items() if k.endswith("_true_value_False"))
    wrong_accepted = sum(v for k, v in tot.items() if k.endswith("_endpoint_wrong_judged_True"))
    check_line(true_rejected == 0 and wrong_accepted == 0
               and tot["enumeration_endpoint_wrong_judged_False"] == tot["enumeration_endpoint_wrong"],
               f"O4: outside the precondition, true values rejected {true_rejected}, wrong endpoint values accepted "
               f"{wrong_accepted}; wrong endpoint values with n <= 10 rejected "
               f"{tot['enumeration_endpoint_wrong_judged_False']} of {tot['enumeration_endpoint_wrong']}")
    return res


# ------------------------------------------------------------------------------------------------
# N: exact counts; the validator's V2 fits and shape diagnostic
# ------------------------------------------------------------------------------------------------

def closed(alg, n, form):
    """(comparisons, additions); the BST form adds n(n+1) additions for building w from p and q."""
    extra = n * (n + 1) if form == "bst" else 0
    if alg == "recursion":
        cmp_ = (3 ** (n - 1) - 1) // 2 if n >= 1 else 0
        add = (11 * 3 ** (n - 2) - 1) // 2 if n >= 2 else n
        return cmp_, add + extra
    if alg == "cubic":
        return (n + 1) * n * (n - 1) // 6, n * (n + 1) * (n + 2) // 6 - n + n * (n + 1) // 2 + extra
    return n * (n - 1) // 2, 3 * n * (n - 1) // 2 + extra


def count_calls(inst):
    calls = 0
    target = REC_MOD.__file__

    def prof(frame, event, arg):
        nonlocal calls
        if event == "call" and frame.f_code.co_name == "cost" and frame.f_code.co_filename == target:
            calls += 1

    sys.setprofile(prof)
    try:
        REC(inst)
    finally:
        sys.setprofile(None)
    return calls


def section_N():
    fns = {"recursion": REC, "cubic": CUB, "endpoint": END}
    reps = ("small", "g_submax", "a_neg_submax")  # one family per category for the larger n
    plan = {"recursion": (range(0, 10), range(10, 13)),
            "cubic": (range(0, 41), range(41, 61)),
            "endpoint": (range(0, 81), (100, 128, 150, 200, 256, 512))}
    series = {alg: {} for alg in plan}
    calls = {}
    mism, runs = 0, Counter()
    for alg, (all_ns, rep_ns) in plan.items():
        for ns, fams in ((all_ns, H.ALL_FAMILIES), (rep_ns, reps)):
            for n in ns:
                for fam in fams:
                    form = "bst" if fam in H.FAMILIES else "table"
                    sense = "min" if fam in H.MIN_FAMILIES else "max"
                    seed = f"mcb-checks|N|{alg}|{n}|{fam}"
                    inst = H.wrap_counting(H.instance_of(fam, n, random.Random(seed)))
                    H.reset_counters()
                    fns[alg](inst)
                    got = H.counters()
                    runs[alg] += 1
                    series[alg].setdefault(n, {}).setdefault(f"{form}/{sense}", set()).add(got)
                    if got != closed(alg, n, form):
                        mism += 1
                        say(f"   MISMATCH {alg} n={n} {fam}: {got} vs {closed(alg, n, form)}")
                    if alg == "recursion":
                        k = count_calls(H.wrap_counting(H.instance_of(fam, n, random.Random(seed))))
                        calls.setdefault(n, set()).add(k)
                        if k != 3 ** n:
                            mism += 1
                            say(f"   MISMATCH calls n={n} {fam}: {k}")
    identical = all(len({ca[0] for s in d.values() for ca in s}) == 1 for alg in series for d in series[alg].values())
    canon = {alg: {str(n): {k: sorted(v) for k, v in sorted(d.items())} for n, d in sorted(series[alg].items())}
             for alg in series}
    canon["recursion_calls"] = {str(n): sorted(v) for n, v in sorted(calls.items())}
    digest = hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()
    res = {"runs": dict(runs), "runs_total": sum(runs.values()), "mismatches": mism,
           "comparisons_identical_across_families_forms_directions": identical, "series_sha256": digest,
           "python": sys.version.split()[0]}
    say("N counts", res)
    check_line(mism == 0 and identical, f"N: every count equals its closed form ({res['runs_total']} runs, {mism} "
                                        f"mismatches); comparisons identical across families, forms and directions: "
                                        f"{identical}")
    say("N recursion comparisons n = 0..12:", [closed("recursion", n, "table")[0] for n in range(13)])
    say("N recursion calls n = 0..12:", [sorted(calls[n]) for n in range(13)])
    # the validator's own V2 run (alphas, rivals, shape diagnostic)
    try:
        V = _load(ROOT / "tools" / "validate.py", "mcb_checks_validate")
        rec = {}
        errors = V.run_v2(ENTRY_JSON, ENTRY, verbose=False, rec=rec)
        fits = []
        for m in rec.get("v2", []):
            fits.append({"algorithm": m["algorithm"], "cost": m["cost"], "n_values": m["n_values"],
                         "values": [int(v) for v in m["values"]], "alpha": float(f"{m['alpha']:.3f}"),
                         "passed": m["passed"],
                         "rivals": {rr["cost"]: float(f"{rr['alpha']:.3f}") for rr in m["rivals"]},
                         "shape": V.shape_line(m["shape"]) if "shape" in m else None})
            say("N V2", fits[-1])
        res["validator_v2"] = {"errors": errors, "fits": fits}
    except Exception as e:  # noqa: BLE001 -- recorded, e.g. a Python without the validator's dependencies
        res["validator_v2"] = {"unavailable": f"{type(e).__name__}: {e}"}
        say("N V2 unavailable:", res["validator_v2"]["unavailable"])
    return res


SECTIONS = (("E1", section_E1), ("E2", section_E2), ("E3", section_E3), ("E4", section_E4), ("E5", section_E5),
            ("B", section_B), ("C", section_C), ("O", section_O), ("N", section_N))


def main():
    ap = argparse.ArgumentParser(description="Checks for the max-cost BST / endpoint-law entry.")
    ap.add_argument("--sections", type=str, default="", help="comma-separated subset of " +
                    ",".join(s for s, _ in SECTIONS))
    ap.add_argument("--json", type=str, default=None, help="write all results to this JSON file")
    args = ap.parse_args()
    wanted = {s for s in args.sections.split(",") if s} or {s for s, _ in SECTIONS}
    unknown = wanted - {s for s, _ in SECTIONS}
    if unknown:
        ap.error(f"unknown sections: {sorted(unknown)}")
    out = {"python": sys.version.split()[0]}
    t0 = time.perf_counter()
    for name, fn in SECTIONS:
        if name not in wanted:
            continue
        t = time.perf_counter()
        say(f"== {name}")
        out[name] = fn()
        out[name + "_seconds"] = float(f"{time.perf_counter() - t:.1f}")
        say(f"== {name} done ({out[name + '_seconds']} s)")
    out["total_seconds"] = float(f"{time.perf_counter() - t0:.1f}")
    say("total seconds", out["total_seconds"])
    if args.json:
        Path(args.json).write_text(json.dumps(out, indent=1, default=str), encoding="utf-8")
    finish_checks()


if __name__ == "__main__":
    main()
