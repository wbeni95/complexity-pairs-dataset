#!/usr/bin/env python3
"""Verifier for theorems/endpoint-law-split-dependent-weights (see README.md in this folder).

Deterministic exhaustive and seeded checks of Theorem 1 and Corollary 2, Lemmas 3 and 4, Remarks (i)-(iii), the
section on interval weights (Corollary 5, Propositions 6-9), Lemmas 10 and 11, and the controls of the README;
computations are evidence, the proofs are in the README. Standard library only; no network;
well under a minute. Exit code 0 only if every check passes.

Objects (as in the README). Split-dependent weights w(i, k, j), 0 <= i < k <= j <= n. Max-recurrence c(i, i) = 0,
c(i, j) = max_{i<k<=j} [w(i, k, j) + c(i, k-1) + c(k, j)]; min-recurrence likewise. For 0 <= i < a < k < b <= j <= n:
  Delta_R = w(i, a, j) + w(a, k, j) - w(i, k, j) - w(i, a, k-1),
  Delta_L = w(i, b, j) + w(i, k, b-1) - w(i, k, j) - w(k, b, j).
RS3: Delta_R + Delta_L >= 0 at every index tuple. RS3w: Delta_R <= 0 and Delta_L <= 0 imply Delta_R = 0. Two-sided
RS3w: they imply Delta_R = Delta_L = 0. The endpoint law on a table: every interval has an optimal split in {i+1, j}
and the endpoint DP equals the full DP on every interval. Merge weights: w(i, k, j) = f(S(i, k-1), S(k, j)) for pile
sizes s_0..s_n, S(x, y) = s_x + ... + s_y. Interval weights w(i, j) (lists w[i][j]): c(i, j) = w(i, j) +
max_{i<k<=j} [c(i, k-1) + c(k, j)]; RS: w(a, j) + w(i, b-1) >= w(k, j) + w(i, k-1) for all 0 <= i < a < k < b <= j <= n.

Checks:
  T  Theorem 1 and Corollary 2, exhaustive: every table with n = 3 and values 0..2; seeded random tables with n = 4, 5.
  A  the proof as an algorithm: from every optimal tree with an interior root, the rotation changes equal the explicit
     change of the tree value (Lemma 4), Delta_R = 0, and right rotations reach an optimal tree with root i+1.
  K  Remarks (i)-(iii): interval weights (RS3 = RS); non-negative combinations; root-only terms.
  E  Lemma 10 (max(L, R)) and Lemma 11 (|L - R|) on a grid and on seeded random rationals, with the formulas of the
     proofs and the symmetry; the merge instances exhaustively as tables.
  S  the Setting: merge trees, enumerated as nested pairs of leaves and costed from leaf sums, against the trees on
     (0, n) with the merge weights: the same number (Catalan(n)), the same maximum and minimum, and caterpillars
     against path trees.
  C  controls: |L - R| violates RS3; min(L, R) under min violates the mirrored RS3 and RS3w; the matrix chain under max
     violates the endpoint law and RS3w; negative sizes. Every control value is also computed by hand in the README.
  G  Proposition 7: Theorem 1 and Corollary 2 over Z^2 with the lexicographic order (seeded split-dependent tables,
     n = 3), and Lemmas 3 and 4 there.
  Interval weights:
  IR    Proposition 9: the O(n^3) test of RS equals the definition (all index tuples) on seeded random tables, with
        its exact numbers of comparisons and additions.
  IP/IT Proposition 6 and Corollary 5, exhaustive: every interval table with n = 3 and values 0..2, n = 4 and values
        0..2, n = 5 and values 0..1; for every RS table the endpoint law (and an optimal path tree) under max with w and
        the endpoint law under min with -w; monotone => RS; the two n = 3 examples; n <= 2.
  IS    seeded random interval tables that satisfy RS and are not monotone, n = 5..9.
  IG    Proposition 7 for Corollary 5 and Proposition 6(a): every interval table with n = 3 and values in a
        4-element subset of Z^2.
  IC    Lemmas 3 and 4 for interval weights and the rotation chain from every optimal tree with an interior root.
  II    Proposition 8: every interval table with n = 1..4 and values in {0, 1, 2, +inf} that is monotone in the
        extended order, and the example of its proof.
Usage (from the repository root): python theorems/endpoint-law-split-dependent-weights/verify.py
"""
import itertools
import random
import sys
import time
from fractions import Fraction

FAILURES = []
INF = float("inf")


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ core objects
def intervals(n):
    return [(i, i + d) for d in range(1, n + 1) for i in range(n - d + 1)]


def triples(n):
    return [(i, k, j) for i, j in intervals(n) for k in range(i + 1, j + 1)]


def quintuples(n):
    return [(i, a, k, b, j) for i, a, k, b in itertools.combinations(range(n + 1), 4) for j in range(b, n + 1)]


def full_dp(n, w, maximise=True):
    c = {(i, i): 0 for i in range(n + 1)}
    arg = {}
    for i, j in intervals(n):
        vals = {k: w[(i, k, j)] + c[(i, k - 1)] + c[(k, j)] for k in range(i + 1, j + 1)}
        best = max(vals.values()) if maximise else min(vals.values())
        c[(i, j)] = best
        arg[(i, j)] = {k for k, v in vals.items() if v == best}
    return c, arg


def endpoint_dp(n, w, maximise=True):
    c = {(i, i): 0 for i in range(n + 1)}
    for i, j in intervals(n):
        ks = (i + 1, j) if j - i >= 2 else (j,)
        vals = [w[(i, k, j)] + c[(i, k - 1)] + c[(k, j)] for k in ks]
        c[(i, j)] = max(vals) if maximise else min(vals)
    return c


def endpoint_law(n, w, maximise=True):
    c, arg = full_dp(n, w, maximise)
    e = endpoint_dp(n, w, maximise)
    return all(arg[iv] & {iv[0] + 1, iv[1]} for iv in intervals(n)) and c == e


def deltas(w, i, a, k, b, j):
    d_r = w[(i, a, j)] + w[(a, k, j)] - w[(i, k, j)] - w[(i, a, k - 1)]
    d_l = w[(i, b, j)] + w[(i, k, b - 1)] - w[(i, k, j)] - w[(k, b, j)]
    return d_r, d_l


def classify(n, w, quints):
    """(RS3, RS3w, two-sided RS3w) of the table."""
    rs3 = rs3w = two = True
    for q in quints:
        d_r, d_l = deltas(w, *q)
        if d_r + d_l < 0:
            rs3 = False
        if d_r <= 0 and d_l <= 0:
            if d_r != 0:
                rs3w = False
            if d_r != 0 or d_l != 0:
                two = False
        if not (rs3 or rs3w or two):
            break
    return rs3, rs3w, two


def negate(w):
    return {key: -v for key, v in w.items()}


def merge_weights(sizes, f):
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)
    n = len(sizes) - 1
    return {(i, k, j): f(pre[k] - pre[i], pre[j + 1] - pre[k]) for i, k, j in triples(n)}


def merge_deltas(f, X, Y, Z, U):
    """Delta_R, Delta_L of a merge weight at the block sums X = S(i, a-1), Y = S(a, k-1), Z = S(k, b-1), U = S(b, j)."""
    L, R = X + Y, Z + U
    return f(X, Y + R) + f(Y, R) - f(L, R) - f(X, Y), f(L + Z, U) + f(L, Z) - f(L, R) - f(Z, U)


F_MAX = max


def F_ABS(x, y):
    return abs(x - y)


F_MIN = min


# ------------------------------------------------------------------------------------------------ T: theorems
def part_theorems():
    n = 3
    quints = quintuples(n)
    trip = triples(n)
    tot = rs3 = rs3_split = rs3w = rs3w_not_rs3 = two = chain_bad = 0
    law_max = law_min = law_fail = law_fail_rs3w = 0
    for values in itertools.product(range(3), repeat=len(trip)):
        w = dict(zip(trip, values))
        tot += 1
        a, b, c2 = classify(n, w, quints)
        chain_bad += (a and not c2) or (c2 and not b)
        if a:
            rs3 += 1
            rs3_split += any(w[(i, k, j)] != w[(i, i + 1, j)] for i, k, j in trip)
        two += c2
        ok_max = endpoint_law(n, w, True)
        law_fail += not ok_max
        if b:
            rs3w += 1
            rs3w_not_rs3 += not a
            law_max += ok_max and optimal_path_everywhere(n, w)
            law_min += endpoint_law(n, negate(w), False)
            law_fail_rs3w += not ok_max
    check("definitions, every table n = 3 with values 0..2: RS3 implies two-sided RS3w implies RS3w", chain_bad == 0,
          f"{tot} tables: {rs3} RS3 ({rs3_split} of them depend on the split), {two} two-sided RS3w, {rs3w} RS3w")
    check("Theorem 1 and Corollary 2, same scope: on every RS3w table an endpoint maximiser and an exact endpoint DP on "
          "every interval, and an optimal path tree on every interval (max, w)", law_max == rs3w,
          f"{law_max}/{rs3w} ({rs3w_not_rs3} of them not RS3)")
    check("Theorem 1 (min form), same scope: endpoint law on every RS3w table, min with -w", law_min == rs3w,
          f"{law_min}/{rs3w}")
    check("control: the endpoint-law check is not vacuous on this scope (it fails on some table, never on an RS3w "
          "table)", law_fail > 0 and law_fail_rs3w == 0,
          f"the law fails on {law_fail} of {tot} tables, on {law_fail_rs3w} of the {rs3w} RS3w tables")
    rng = random.Random(41)
    for n, count in ((4, 40000), (5, 60000)):
        quints = quintuples(n)
        trip = triples(n)
        found = found_not_rs3 = ok = oracle_ok = oracle_runs = 0
        for t in range(count):
            w = {key: rng.randint(0, 2) for key in trip}
            a, b, _ = classify(n, w, quints)
            if not b:
                continue
            found += 1
            found_not_rs3 += not a
            ok += endpoint_law(n, w, True) and endpoint_law(n, negate(w), False)
            if oracle_runs < 200:
                oracle_runs += 1
                oracle_ok += full_dp(n, w)[0][(0, n)] == max(tree_value(t_, 0, n, w) for t_ in trees(0, n))
        check(f"Theorem 1 / Corollary 2 on seeded random tables n = {n}, values 0..2, filtered by RS3w; Lemma 3 "
              f"(DP = maximum over all trees) on 200 of them", ok == found > 0 and oracle_ok == oracle_runs == 200,
              f"{ok}/{found} RS3w tables among {count} ({found_not_rs3} not RS3); DP = maximum over all trees on "
              f"{oracle_ok}/{oracle_runs}")


# ------------------------------------------------------------------------------------------------ A: proof steps
def trees(i, j):
    if i == j:
        return [None]
    return [(k, l, r) for k in range(i + 1, j + 1) for l in trees(i, k - 1) for r in trees(k, j)]


def tree_value(t, i, j, w):
    if t is None:
        return 0
    k, l, r = t
    return w[(i, k, j)] + tree_value(l, i, k - 1, w) + tree_value(r, k, j, w)


def is_path(t):
    return t is None or ((t[1] is None or t[2] is None) and is_path(t[1]) and is_path(t[2]))


def optimal_path_everywhere(n, w):
    """Part (a) by enumeration: on every interval some maximum-value tree is a path tree."""
    for i, j in intervals(n):
        all_t = trees(i, j)
        vals = [tree_value(t, i, j, w) for t in all_t]
        best = max(vals)
        if not any(is_path(t) for t, v in zip(all_t, vals) if v == best):
            return False
    return True


def rot_right(t):
    k, (a, la, ra), r = t
    return (a, la, (k, ra, r))


def rot_left(t):
    k, l, (b, lb, rb) = t
    return (b, (k, l, lb), rb)


def proof_chain(n, w, stats, both_zero):
    ok = True
    for i, j in intervals(n):
        if j - i < 3:
            continue
        all_t = trees(i, j)
        vals = [tree_value(t, i, j, w) for t in all_t]
        best = max(vals)
        for t, v in zip(all_t, vals):
            if v != best or not i + 1 < t[0] < j:
                continue
            steps = 0
            while i + 1 < t[0] < j:
                k, l, r = t
                a, b = l[0], r[0]
                d_r = tree_value(rot_right(t), i, j, w) - best
                d_l = tree_value(rot_left(t), i, j, w) - best
                ok &= (d_r, d_l) == deltas(w, i, a, k, b, j)  # Lemma 4
                ok &= d_r == 0 and (d_l == 0 or not both_zero)
                t = rot_right(t)
                ok &= tree_value(t, i, j, w) == best
                steps += 1
            ok &= t[0] == i + 1
            stats["cases"] += 1
            stats["steps"] += steps
    return ok


def part_proof():
    rng = random.Random(7)
    stats = {"cases": 0, "steps": 0}
    ok = True
    tables = 0
    for n, count in ((3, 3000), (4, 20000)):
        quints = quintuples(n)
        trip = triples(n)
        for _ in range(count):
            w = {key: rng.randint(0, 2) for key in trip}
            a, b, _ = classify(n, w, quints)
            if b:
                tables += 1
                ok &= proof_chain(n, w, stats, both_zero=a)
    for sizes in ((3, 1, 4, 1, 5), (2, 7, 1, 8, 2, 8), (0, 0, 1, 0, 2)):
        for f in (F_MAX, F_ABS):
            tables += 1
            ok &= proof_chain(len(sizes) - 1, merge_weights(sizes, f), stats, both_zero=True)
    check("proof as an algorithm (Lemma 4, Delta_R = 0, chain to root i+1) on seeded RS3w tables n = 3, 4 and on "
          "merge tables", ok and stats["cases"] > 0,
          f"{tables} tables, {stats['cases']} optimal trees with an interior root, {stats['steps']} rotations")


# ------------------------------------------------------------------------------------------------ K: remarks
def is_rs(n, v):
    return all(v[(a, j)] + v[(i, b - 1)] >= v[(k, j)] + v[(i, k - 1)] for i, a, k, b, j in quintuples(n))


def part_remarks():
    n = 4
    quints = quintuples(n)
    agree = tot = 0
    for values in itertools.product(range(3), repeat=len(intervals(n))):
        v = dict(zip(intervals(n), values))
        w = {(i, k, j): v[(i, j)] for i, k, j in triples(n)}
        tot += 1
        agree += classify(n, w, quints)[0] == is_rs(n, v)
    check("Remark (i): for interval weights w(i,k,j) = v(i,j), RS3 = RS (every table n = 4, values 0..2)",
          agree == tot, f"{agree}/{tot}")
    rng = random.Random(3)
    combos = phi_ok = 0
    pool = []
    while len(pool) < 40:
        w = {key: rng.randint(0, 3) for key in triples(4)}
        if classify(4, w, quints)[0]:
            pool.append(w)
    for _ in range(200):
        w1, w2 = rng.sample(pool, 2)
        a1, a2 = rng.randint(0, 3), rng.randint(0, 3)
        combos += classify(4, {key: a1 * w1[key] + a2 * w2[key] for key in w1}, quints)[0]
    for _ in range(200):
        w = {key: rng.randint(-3, 3) for key in triples(4)}
        phi = [rng.randint(-9, 9) for _ in range(5)]
        w2 = {(i, k, j): x + phi[k] for (i, k, j), x in w.items()}
        phi_ok += all(deltas(w, *q) == deltas(w2, *q) for q in quints)
    check("Remark (ii): non-negative combinations of RS3 tables are RS3 (200 seeded combinations, n = 4)",
          combos == 200, f"{combos}/200")
    check("Remark (iii): adding a root-only term phi(k) leaves Delta_R and Delta_L unchanged (200 seeded tables)",
          phi_ok == 200, f"{phi_ok}/200")


# ------------------------------------------------------------------------------------------------ E: lemmas
def part_lemmas():
    grid = list(itertools.product(range(13), repeat=4))
    rng = random.Random(17)
    rand = [tuple(Fraction(rng.randint(0, 400), rng.randint(1, 30)) for _ in range(4)) for _ in range(5000)]
    bad_sum = bad_formula = bad_sym = 0
    for q in grid + rand:
        X, Y, Z, U = q
        L, R = X + Y, Z + U
        d_r, d_l = merge_deltas(F_MAX, *q)
        bad_sum += d_r + d_l < 0
        if L <= R:
            bad_formula += d_r != Y + R - max(X, Y) or d_l < L - R
        bad_sym += merge_deltas(F_MAX, U, Z, Y, X) != (d_l, d_r)
    check("Lemma 10: Delta_R + Delta_L >= 0 for max(L, R), grid 0..12 (28 561) and 5 000 random rationals >= 0",
          bad_sum == 0, f"{bad_sum} violations")
    check("Lemma 10 proof steps: for L <= R, Delta_R = Y + R - max(X, Y) and Delta_L >= L - R; the symmetry "
          "(X,Y,Z,U) -> (U,Z,Y,X) swaps Delta_R and Delta_L", bad_formula == 0 and bad_sym == 0,
          f"{bad_formula} formula, {bad_sym} symmetry mismatches")
    bad_imp = bad_formula = bad_sym = 0
    for q in grid + rand:
        X, Y, Z, U = q
        L, R = X + Y, Z + U
        d_r, d_l = merge_deltas(F_ABS, *q)
        bad_imp += d_r <= 0 and d_l <= 0 and (d_r, d_l) != (0, 0)
        if L <= R:
            bad_formula += d_r != R + Y - abs(X - Y)
        bad_sym += merge_deltas(F_ABS, U, Z, Y, X) != (d_l, d_r)
    check("Lemma 11: for |L - R|, Delta_R <= 0 and Delta_L <= 0 imply both = 0, same grid and rationals",
          bad_imp == 0, f"{bad_imp} violations")
    check("Lemma 11 proof steps: for L <= R, Delta_R = R + Y - |X - Y|; the symmetry swaps Delta_R and Delta_L",
          bad_formula == 0 and bad_sym == 0, f"{bad_formula} formula, {bad_sym} symmetry mismatches")
    # the merge instances as tables, exhaustively
    vectors = [v for n, top in ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 3), (6, 2))
               for v in itertools.product(range(top + 1), repeat=n + 1)]
    quint_cache = {}
    res = {"max": [0, 0], "abs": [0, 0]}
    for sizes in vectors:
        n = len(sizes) - 1
        quints = quint_cache.setdefault(n, quintuples(n))
        for name, f in (("max", F_MAX), ("abs", F_ABS)):
            w = merge_weights(sizes, f)
            rs3, _, two = classify(n, w, quints)
            hyp = rs3 if name == "max" else two
            res[name][0] += hyp
            res[name][1] += endpoint_law(n, w, True) and (n > 5 or optimal_path_everywhere(n, w))
    tot = len(vectors)
    check(f"merge cost max(L, R): RS3 and the endpoint law on every size vector (n <= 4 sizes 0..4, n = 5 sizes 0..3, "
          f"n = 6 sizes 0..2; optimal caterpillars checked by enumeration for n <= 5)", res["max"] == [tot, tot], f"RS3 {res['max'][0]}/{tot}, law {res['max'][1]}/{tot}")
    check("merge cost |L - R|: two-sided RS3w and the endpoint law on the same vectors", res["abs"] == [tot, tot],
          f"two-sided RS3w {res['abs'][0]}/{tot}, law {res['abs'][1]}/{tot}")


# ------------------------------------------------------------------------------------------------ C: controls
def merge_trees_nested(sizes):
    """Every merge tree of the row, as a nested pair structure over the leaf indices (independent of trees())."""
    def rec(lo, hi):
        if lo == hi:
            return [lo]
        return [(left, right) for k in range(lo + 1, hi + 1) for left in rec(lo, k - 1) for right in rec(k, hi)]
    return rec(0, len(sizes) - 1)


def merge_tree_cost(t, sizes, f):
    """(cost, block size, is_caterpillar) of a nested merge tree: a merge of blocks of sizes L and R costs f(L, R)."""
    if not isinstance(t, tuple):
        return 0, sizes[t], True
    cl, sl, kl = merge_tree_cost(t[0], sizes, f)
    cr, sr, kr = merge_tree_cost(t[1], sizes, f)
    single = not isinstance(t[0], tuple) or not isinstance(t[1], tuple)
    return cl + cr + f(sl, sr), sl + sr, kl and kr and single


def path_tree_extremes(n, w):
    """(max, min) value over all trees on (0, n), and (max, min) over the path trees, by enumeration."""
    vals = [(tree_value(t, 0, n, w), is_path(t)) for t in trees(0, n)]
    allv = [v for v, _ in vals]
    pathv = [v for v, p in vals if p]
    return (max(allv), min(allv)), (max(pathv), min(pathv)), len(vals)


def part_setting():
    """The merge-tree correspondence of the Setting, for f = max, |.|, min and signed sizes."""
    catalan = [1, 1, 2, 5, 14, 42]
    rng = random.Random(29)
    vectors = [v for n, top in ((0, 3), (1, 3), (2, 3), (3, 3), (4, 2)) for v in itertools.product(range(top + 1), repeat=n + 1)]
    vectors += [tuple(rng.randint(-4, 6) for _ in range(rng.randint(1, 6))) for _ in range(300)]
    ok = runs = 0
    for sizes in vectors:
        n = len(sizes) - 1
        nested = merge_trees_nested(sizes)
        for f in (F_MAX, F_ABS, F_MIN):
            costs = [merge_tree_cost(t, sizes, f) for t in nested]
            mt_all = [c for c, _, _ in costs]
            mt_cat = [c for c, _, cat in costs if cat]
            if n == 0:
                ok += mt_all == [0]
                runs += 1
                continue
            w = merge_weights(sizes, f)
            (tmax, tmin), (pmax, pmin), count = path_tree_extremes(n, w)
            c_max, _ = full_dp(n, w, True)
            c_min, _ = full_dp(n, w, False)
            ok += (len(nested) == count == catalan[n] and max(mt_all) == tmax == c_max[(0, n)]
                   and min(mt_all) == tmin == c_min[(0, n)] and max(mt_cat) == pmax and min(mt_cat) == pmin)
            runs += 1
    check("Setting: merge trees (nested pairs, costed from leaf sums) vs trees on (0, n) with w(i,k,j) = f(S(i,k-1), "
          "S(k,j)): same number Catalan(n), same maximum and minimum (= the DP), caterpillars vs path trees; f = max, "
          "|.|, min; every vector n <= 3 sizes 0..3, n = 4 sizes 0..2, and 300 seeded signed vectors n <= 5",
          ok == runs, f"{ok}/{runs} (vector, f) pairs")


def part_controls():
    check("|L - R| violates RS3: sizes (1, 0, 1, 2), (i,a,k,b,j) = (0,1,2,3,3): Delta_R = 2, Delta_L = -3",
          merge_deltas(F_ABS, 1, 0, 1, 2) == (2, -3) and deltas(merge_weights((1, 0, 1, 2), F_ABS), 0, 1, 2, 3, 3)
          == (2, -3))
    # min(L, R) under min: the min forms need RS3 / RS3w for -w
    ex = {q: merge_deltas(F_MIN, *q) for q in ((0, 1, 1, 2), (1, 1, 2, 4), (1, 9, 5, 15), (2, 1, 0, 1))}
    check("min(L, R): RS3 for -w fails (Delta_R + Delta_L > 0 for w) on (0,1,1,2): (0, 1), (1,1,2,4): (-1, 2), "
          "(1,9,5,15): (-1, 5)", ex[(0, 1, 1, 2)] == (0, 1) and ex[(1, 1, 2, 4)] == (-1, 2)
          and ex[(1, 9, 5, 15)] == (-1, 5))
    check("min(L, R): RS3w for -w fails (Delta_R >= 0, Delta_L >= 0, Delta_R != 0 for w) on (2,1,0,1): (1, 0)",
          ex[(2, 1, 0, 1)] == (1, 0))
    law = 0
    vectors = [v for n, top in ((0, 4), (1, 4), (2, 4), (3, 4), (4, 4), (5, 3)) for v in
               itertools.product(range(top + 1), repeat=n + 1)]
    for sizes in vectors:
        law += endpoint_law(len(sizes) - 1, merge_weights(sizes, F_MIN), False)
    check("min(L, R) under min: the endpoint law holds anyway on every size vector n <= 4 sizes 0..4, n = 5 sizes 0..3",
          law == len(vectors), f"{law}/{len(vectors)}")
    # matrix chain M_0..M_3 with dimensions p = (1, 1, 2, 1, 1): w(i, k, j) = p_i p_k p_(j+1)
    p = (1, 1, 2, 1, 1)
    w = {(i, k, j): p[i] * p[k] * p[j + 1] for i, k, j in triples(3)}
    c, arg = full_dp(3, w)
    e = endpoint_dp(3, w)
    check("matrix chain under max, p = (1,1,2,1,1): optimum 6 (only split 2), endpoint DP 5, and at (0,1,2,3,3) "
          "Delta_R = Delta_L = -1 (RS3w fails)", c[(0, 3)] == 6 and arg[(0, 3)] == {2} and e[(0, 3)] == 5
          and deltas(w, 0, 1, 2, 3, 3) == (-1, -1))
    # the five products / merge trees of four items, merge by merge, in the README's order
    five = (((0, 1, 1), (2, 3, 3), (0, 2, 3)), ((0, 1, 1), (0, 2, 2), (0, 3, 3)), ((1, 2, 2), (0, 1, 2), (0, 3, 3)),
            ((1, 2, 2), (1, 3, 3), (0, 1, 3)), ((2, 3, 3), (1, 2, 3), (0, 1, 3)))
    chain = [[w[m] for m in t] for t in five]
    check("matrix chain: the five products cost 2+2+2, 2+2+1, 2+1+1, 2+1+1, 2+2+1 (README order)",
          chain == [[2, 2, 2], [2, 2, 1], [2, 1, 1], [2, 1, 1], [2, 2, 1]], str(chain))
    for sizes, f, expect in (((-2, -1, -2, 1), F_MAX, [[-1, 1, -1], [-1, -2, 1], [-1, -2, 1], [-1, 1, -2], [1, -1, -2]]),
                             ((0, -1, 1, 0), F_ABS, [[1, 1, 2], [1, 2, 0], [2, 0, 0], [2, 0, 0], [1, 2, 0]])):
        ww = merge_weights(sizes, f)
        got = [[ww[m] for m in t] for t in five]
        check(f"negative sizes {sizes}: the five merge trees cost (merge by merge) {expect}", got == expect, str(got))
    for sizes, f, name, opt, end in (((-2, -1, -2, 1), F_MAX, "max(L, R)", -1, -2), ((0, -1, 1, 0), F_ABS, "|L - R|", 4, 3)):
        w = merge_weights(sizes, f)
        c, _ = full_dp(3, w)
        e = endpoint_dp(3, w)
        check(f"negative sizes: {name}, sizes {sizes}: optimum {opt}, endpoint DP {end}",
              c[(0, 3)] == opt and e[(0, 3)] == end)


# ================================================================================================ interval weights
# The checks of the section "Interval weights: the rotation-sum condition RS". Interval tables are lists w[i][j]
# (not dicts keyed by (i, k, j)); the functions with the prefix iv_ are the interval-weight versions.


def table_from(n, values):
    """w[i][j] from a flat sequence of values, one per interval in the order of intervals(n)."""
    w = [[None] * (n + 1) for _ in range(n + 1)]
    for (i, j), v in zip(intervals(n), values):
        w[i][j] = v
    return w


def iv_full_dp(n, w, maximise=True):
    """c[i][j] and the set of optimal splits of every interval (full recurrence)."""
    c = [[None] * (n + 1) for _ in range(n + 1)]
    arg = {}
    for i in range(n + 1):
        c[i][i] = ZERO[0]
    for i, j in intervals(n):
        vals = {k: c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1)}
        best = max(vals.values()) if maximise else min(vals.values())
        c[i][j] = w[i][j] + best
        arg[(i, j)] = {k for k, v in vals.items() if v == best}
    return c, arg


def iv_endpoint_dp(n, w, maximise=True):
    c = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        c[i][i] = ZERO[0]
    for i, j in intervals(n):
        if j - i == 1:
            c[i][j] = w[i][j] + ZERO[0]
        else:
            x, y = c[i + 1][j], c[i][j - 1]
            c[i][j] = w[i][j] + ((x if x >= y else y) if maximise else (x if x <= y else y))
    return c


ZERO = [0]  # the neutral element of the value group (changed for the Z^2 checks)


def iv_endpoint_law(n, w, maximise=True):
    c, arg = iv_full_dp(n, w, maximise)
    e = iv_endpoint_dp(n, w, maximise)
    return all(arg[(i, j)] & {i + 1, j} for i, j in intervals(n)) and all(
        c[i][j] == e[i][j] for i, j in intervals(n))


def rs_tuples(n):
    return [(i, a, k, b, j) for i, a, k, b in itertools.combinations(range(n + 1), 4) for j in range(b, n + 1)]


def iv_is_rs(n, w, tuples=None):
    """The definition: every index tuple."""
    for i, a, k, b, j in (tuples if tuples is not None else rs_tuples(n)):
        if w[a][j] + w[i][b - 1] < w[k][j] + w[i][k - 1]:
            return False
    return True


def is_rs_fast(n, w, ops=None):
    """Proposition 9: for fixed i < j and every k with i+1 < k < j, min_{i<a<k} w(a, j) + min_{k<=c<j} w(i, c) must be
    >= w(k, j) + w(i, k-1); running minima over a and suffix minima over c give O(n) per (i, j), O(n^3) in all.
    Every comparison and addition of weight values is explicit; if ops is a dict, their numbers are stored in
    ops["cmp"] and ops["add"]."""
    cmp_ = add = 0
    result = True
    for i in range(n + 1):
        for j in range(i + 3, n + 1):
            suffix = [None] * (j + 1)  # suffix[c] = min_{c <= c' < j} w(i, c')
            for cc in range(j - 1, i, -1):
                if cc == j - 1:
                    suffix[cc] = w[i][cc]
                else:
                    cmp_ += 1
                    suffix[cc] = w[i][cc] if w[i][cc] < suffix[cc + 1] else suffix[cc + 1]
            run = None  # min_{i < a < k} w(a, j)
            for k in range(i + 2, j):
                if run is None:
                    run = w[k - 1][j]
                else:
                    cmp_ += 1
                    run = w[k - 1][j] if w[k - 1][j] < run else run
                add += 2
                cmp_ += 1
                if run + suffix[k] < w[k][j] + w[i][k - 1]:
                    result = False
                    break
            if not result:
                break
        if not result:
            break
    if ops is not None:
        ops["cmp"], ops["add"] = cmp_, add
    return result


def rs_test_counts(n):
    """The counts of Proposition 9 when no violation is found: the sums over d = 3..n of (n - d + 1)(3d - 7)
    comparisons and of (n - d + 1) 2(d - 2) additions."""
    return (sum((n - d + 1) * (3 * d - 7) for d in range(3, n + 1)),
            sum((n - d + 1) * 2 * (d - 2) for d in range(3, n + 1)))


def is_monotone(n, w):
    return all(w[i][j] >= w[i + 1][j] and w[i][j] >= w[i][j - 1] for i, j in intervals(n) if j - i >= 2)


def iv_negate(n, w):
    return [[None if x is None else -x for x in row] for row in w]


def iv_part_remark():
    rng = random.Random(11)
    agree = rs_count = count_exact = count_bounded = 0
    for t in range(3000):
        n = rng.randint(1, 9)
        if t % 3 == 0:
            w = perturbed_monotone(n, rng)
        else:
            w = table_from(n, [rng.randint(0, 3) for _ in intervals(n)])
        ops = {}
        a, b = iv_is_rs(n, w), is_rs_fast(n, w, ops)
        agree += a == b
        rs_count += a
        exact_cmp, exact_add = rs_test_counts(n)
        if a:
            count_exact += (ops["cmp"], ops["add"]) == (exact_cmp, exact_add)
        else:
            count_bounded += ops["cmp"] <= exact_cmp and ops["add"] <= exact_add
    check("Proposition 9 (interval weights): O(n^3) RS test = definition on 3000 seeded tables (n = 1..9)", agree == 3000,
          f"{agree}/3000 agree, {rs_count} RS")
    bound_ok = all(rs_test_counts(m)[0] <= 3 * m ** 3 for m in range(0, 201))
    check("Proposition 9: the test makes exactly sum_(d=3..n) (n-d+1)(3d-7) comparisons and (n-d+1)2(d-2) additions on "
          "every RS table and at most that on the others; the first sum is <= 3n^3 for n = 0..200",
          count_exact == rs_count and count_bounded == 3000 - rs_count and bound_ok,
          f"exact on {count_exact}/{rs_count} RS tables, bounded on {count_bounded}/{3000 - rs_count} others")


def perturbed_monotone(n, rng):
    """A random monotone table (built upwards) with 1-3 entries changed by +-1 or +-2."""
    w = [[None] * (n + 1) for _ in range(n + 1)]
    for i, j in intervals(n):
        lb = 0 if j - i == 1 else max(w[i + 1][j], w[i][j - 1])
        w[i][j] = lb + (rng.randint(0, 3) if rng.random() < 0.5 else 0)
    for _ in range(rng.randint(1, 3)):
        i, j = rng.choice(intervals(n))
        w[i][j] += rng.choice((-2, -1, 1, 2))
    return w


def iv_part_exhaustive():
    results = {}
    for n, vals in ((3, range(3)), (4, range(3)), (5, range(2))):
        tuples = rs_tuples(n)
        tot = rs = rs_not_m = mono = mono_not_rs = law_max = law_min = 0
        for values in itertools.product(vals, repeat=len(intervals(n))):
            w = table_from(n, values)
            tot += 1
            r = iv_is_rs(n, w, tuples)
            m = is_monotone(n, w)
            mono += m
            mono_not_rs += m and not r
            if r:
                rs += 1
                rs_not_m += not m
                law_max += iv_endpoint_law(n, w, True) and iv_optimal_path_everywhere(n, w)
                law_min += iv_endpoint_law(n, iv_negate(n, w), False)
        results[n] = (tot, rs, rs_not_m, mono)
        check(f"Corollary 5 (RS), every interval table n = {n}, values 0..{max(vals)}: endpoint law and an optimal path "
              f"tree (max, w) on every RS table",
              law_max == rs, f"{law_max}/{rs} RS tables ({rs_not_m} of them not monotone; {tot} tables in all)")
        check(f"Corollary 5, min form, same scope: endpoint law (min, -w) on every RS table", law_min == rs, f"{law_min}/{rs}")
        check(f"Proposition 6(a), same scope: every monotone table satisfies RS", mono_not_rs == 0,
              f"{mono} monotone tables, {mono_not_rs} without RS")
    # the two examples of Proposition 6, and n <= 2
    w1 = [[None] * 4 for _ in range(4)]
    for i, j in intervals(3):
        w1[i][j] = 1 if (i, j) == (1, 3) else 0
    check("Proposition 6(b): n = 3, w(1,3) = 1, others 0: RS holds, not monotone, endpoint law holds",
          iv_is_rs(3, w1) and not is_monotone(3, w1) and iv_endpoint_law(3, w1) and rs_tuples(3) == [(0, 1, 2, 3, 3)])
    w2 = [[None] * 4 for _ in range(4)]
    for i, j in intervals(3):
        w2[i][j] = 1 if (i, j) == (2, 3) else 0
    c, arg = iv_full_dp(3, w2)
    check("Proposition 6(c): n = 3, w(2,3) = 1, others 0: RS fails, endpoint law holds, c(0,3) = 1 with optimal "
          "splits {1, 2}", not iv_is_rs(3, w2) and iv_endpoint_law(3, w2) and c[0][3] == 1 and arg[(0, 3)] == {1, 2})
    check("RS is vacuous for n <= 2 (no index tuple)", rs_tuples(0) == rs_tuples(1) == rs_tuples(2) == [])
    return results


def iv_part_random():
    rng = random.Random(2026)
    found = held = tries = 0
    sizes = {}
    while found < 300 and tries < 40000:
        tries += 1
        n = rng.randint(5, 9)
        w = perturbed_monotone(n, rng)
        if is_monotone(n, w) or not is_rs_fast(n, w):
            continue
        found += 1
        sizes[n] = sizes.get(n, 0) + 1
        held += iv_endpoint_law(n, w, True) and iv_endpoint_law(n, iv_negate(n, w), False)
    check("Corollary 5 (max and min form) on seeded random RS tables that are not monotone, n = 5..9",
          found == 300 and held == found, f"{held}/{found} (found in {tries} tries; per n {dict(sorted(sizes.items()))})")


class Lex:
    """An element of Z^2 with componentwise addition and the lexicographic order (a non-archimedean ordered group).
    A plain integer x is read as (x, 0); the code only ever mixes in the integer 0 (empty trees, comparisons with 0)."""
    __slots__ = ("p",)

    def __init__(self, a, b):
        self.p = (a, b)

    @staticmethod
    def _p(o):
        return o.p if isinstance(o, Lex) else (o, 0)

    def __add__(self, o):
        q = Lex._p(o)
        return Lex(self.p[0] + q[0], self.p[1] + q[1])

    __radd__ = __add__

    def __sub__(self, o):
        q = Lex._p(o)
        return Lex(self.p[0] - q[0], self.p[1] - q[1])

    def __neg__(self):
        return Lex(-self.p[0], -self.p[1])

    def __lt__(self, o):
        return self.p < Lex._p(o)

    def __le__(self, o):
        return self.p <= Lex._p(o)

    def __gt__(self, o):
        return self.p > Lex._p(o)

    def __ge__(self, o):
        return self.p >= Lex._p(o)

    def __eq__(self, o):
        return self.p == Lex._p(o)

    def __hash__(self):
        return hash(self.p)


def iv_part_group():
    ZERO[0] = Lex(0, 0)
    try:
        vals = [Lex(0, 0), Lex(0, 1), Lex(1, -5), Lex(1, 0)]
        tot = rs = rs_not_m = law = law_min = mono = mono_rs = 0
        tuples = rs_tuples(3)
        for values in itertools.product(vals, repeat=6):
            w = table_from(3, values)
            tot += 1
            if is_monotone(3, w):
                mono += 1
                mono_rs += iv_is_rs(3, w, tuples)
            if iv_is_rs(3, w, tuples):
                rs += 1
                rs_not_m += not is_monotone(3, w)
                law += iv_endpoint_law(3, w, True) and iv_optimal_path_everywhere(3, w)
                law_min += iv_endpoint_law(3, iv_negate(3, w), False)
        # non-archimedean: no multiple of (0, 1) reaches (1, -5)
        archimedean_fails = all(Lex(0, m) < Lex(1, -5) for m in range(1000))
        check("Proposition 7: Corollary 5 (max and min form) over Z^2 (lexicographic), every interval table n = 3 with values "
              "{(0,0), (0,1), (1,-5), (1,0)} (max form also: an optimal path tree on every interval)", law == rs and law_min == rs and archimedean_fails,
              f"{law}/{rs} RS tables (max), {law_min}/{rs} (min, -w); {rs_not_m} not monotone; {tot} tables")
        check("Proposition 7: Proposition 6(a) over Z^2 (lexicographic), same 4 096 interval tables: every monotone "
              "table satisfies RS", mono_rs == mono > 0, f"{mono_rs}/{mono} monotone tables satisfy RS")
    finally:
        ZERO[0] = 0


def tval(t, i, j, w):
    if t is None:
        return ZERO[0]
    k, l, r = t
    return w[i][j] + tval(l, i, k - 1, w) + tval(r, k, j, w)


def iv_optimal_path_everywhere(n, w):
    """Corollary 5(a) by enumeration: on every interval some maximum-value tree is a path tree."""
    for i, j in intervals(n):
        all_t = trees(i, j)
        vals = [tval(t, i, j, w) for t in all_t]
        best = max(vals)
        if not any(is_path(t) for t, v in zip(all_t, vals) if v == best):
            return False
    return True


def claim_chain(n, w, stats):
    """For every interval and every optimal tree on it whose root is interior: follow right rotations to root i+1,
    checking the formulas of Lemma 4 (interval weights) against explicit tree values, Delta_R = Delta_L = 0 and optimality."""
    ok = True
    for i, j in intervals(n):
        all_t = trees(i, j)
        vals = [tval(t, i, j, w) for t in all_t]
        best = max(vals)
        ok &= any(is_path(t) for t, v in zip(all_t, vals) if v == best)  # Corollary 5(a)
        for t, v in zip(all_t, vals):  # RS = RS3: Delta_R + Delta_L >= 0 at EVERY tree with an interior root
            if i + 1 < t[0] < j:
                ok &= tval(rot_right(t), i, j, w) + tval(rot_left(t), i, j, w) - 2 * v >= 0
                stats["lemma_c"] += 1
        for t, v in zip(all_t, vals):
            if v != best or not i + 1 < t[0] < j:
                continue
            steps = 0
            while i + 1 < t[0] < j:
                kk, l, r = t
                kl, kr = l[0], r[0]
                d_r = tval(rot_right(t), i, j, w) - best
                d_l = tval(rot_left(t), i, j, w) - best
                ok &= d_r == w[kl][j] - w[i][kk - 1] and d_l == w[i][kr - 1] - w[kk][j]  # Lemma 4 for interval weights
                ok &= d_r == 0 and d_l == 0
                t = rot_right(t)
                steps += 1
                ok &= tval(t, i, j, w) == best
            ok &= t[0] == i + 1
            stats["cases"] += 1
            stats["steps"] += steps
    return ok


def iv_part_claim():
    stats = {"cases": 0, "steps": 0, "lemma_c": 0}
    ok = True
    tables = 0
    tuples = rs_tuples(4)
    rng = random.Random(5)
    for values in itertools.product(range(3), repeat=10):
        if rng.random() > 0.15:
            continue
        w = table_from(4, values)
        if iv_is_rs(4, w, tuples) and not is_monotone(4, w):
            tables += 1
            ok &= claim_chain(4, w, stats)
    found = 0
    while found < 40:
        n = rng.randint(5, 6)
        w = perturbed_monotone(n, rng)
        if is_monotone(n, w) or not is_rs_fast(n, w):
            continue
        found += 1
        ok &= claim_chain(n, w, stats)
    check("interval weights, proof as an algorithm on RS tables that are not monotone (a seeded 15% sample of n = 4, values 0..2, and "
          "40 seeded tables with n = 5, 6): from every optimal tree with an interior root; an optimal path tree on "
          "every interval", ok and stats["cases"] > 0,
          f"{tables} + 40 tables, {stats['cases']} starting trees, {stats['steps']} rotations; rotation sum >= 0 on "
          f"{stats['lemma_c']} trees with an interior root")
    # Lemma 3 (interval weights): the recurrence equals the largest tree value
    agree = runs = 0
    for _ in range(300):
        n = rng.randint(0, 6)
        w = table_from(n, [rng.randint(-5, 9) for _ in intervals(n)])
        c, _ = iv_full_dp(n, w)
        runs += 1
        agree += (c[0][n] if n else 0) == max(tval(t, 0, n, w) for t in trees(0, n))
    check("Lemma 3 for interval weights: the recurrence equals the largest value over all explicitly enumerated trees (300 seeded tables, "
          "n = 0..6, values -5..9)", agree == runs, f"{agree}/{runs}")


def monotone_tables_ext(n, vals):
    """Every table with entries in vals that is monotone under inclusion (local test), built by increasing length."""
    ivs = intervals(n)
    out = []
    w = [[None] * (n + 1) for _ in range(n + 1)]

    def rec(t):
        if t == len(ivs):
            out.append([row[:] for row in w])
            return
        i, j = ivs[t]
        lb = None if j - i == 1 else max(w[i + 1][j], w[i][j - 1])
        for v in vals:
            if lb is None or v >= lb:
                w[i][j] = v
                rec(t + 1)
        w[i][j] = None

    rec(0)
    return out


def iv_part_infinity():
    tot = with_inf = ok = 0
    for n in range(1, 5):
        for w in monotone_tables_ext(n, (0, 1, 2, INF)):
            tot += 1
            with_inf += any(w[i][j] == INF for i, j in intervals(n))
            c, _ = iv_full_dp(n, w, True)
            e = iv_endpoint_dp(n, w, True)
            ok += all(c[i][j] == e[i][j] for i, j in intervals(n)) and iv_optimal_path_everywhere(n, w)
    # the example of the proof of Proposition 8: Lemma 3's second and third statements fail when w(i, j) = +inf
    w = [[None] * 4 for _ in range(4)]
    for i, j in intervals(3):
        w[i][j] = {(0, 3): INF, (1, 3): 5, (2, 3): 1}.get((i, j), 0)
    c, arg = iv_full_dp(3, w, True)
    cands = [c[0][k - 1] + c[k][3] for k in (1, 2, 3)]
    all_inf = all(tval(t, 0, 3, w) == INF for t in trees(0, 3))
    sub = (3, (2, None, None), None)  # root 3 on (1, 3) with node 2 as its left child
    check("Proposition 8, example of the proof: monotone; candidates 6, 1, 0 (only k = 1 maximises); every tree on "
          "(0, 3) is worth +inf; the subtree 'root 3 on (1, 3)' has value 5 < c(1, 3) = 6",
          is_monotone(3, w) and cands == [6, 1, 0] and arg[(0, 3)] == {1} and all_inf
          and tval(sub, 1, 3, w) == 5 and c[1][3] == 6 and tval((1, None, sub), 0, 3, w) == INF)
    check("Proposition 8: every table n = 1..4 with values {0, 1, 2, +inf}, monotone in the extended order: the "
          "endpoint recurrence gives c on every interval (max), and every interval has an optimal path tree", ok == tot, f"{ok}/{tot} tables, {with_inf} with +inf")


def part_group_split():
    """Proposition 7 for split-dependent weights: Theorem 1 and Corollary 2 over Z^2 with the lexicographic order."""
    rng = random.Random(23)
    vals = [Lex(0, 0), Lex(0, 1), Lex(1, -5), Lex(1, 0)]
    n = 3
    quints = quintuples(n)
    trip = triples(n)
    tot = found = found_not_rs3 = ok = oracle_ok = oracle_runs = 0
    rot_ok = rot_trees = 0
    for _ in range(20000):
        w = {key: rng.choice(vals) for key in trip}
        tot += 1
        for i, j in intervals(n):  # Lemma 4 over Z^2: every tree with an interior root, explicit rotated values
            for t in trees(i, j):
                if i + 1 < t[0] < j:
                    v = tree_value(t, i, j, w)
                    d_r, d_l = deltas(w, i, t[1][0], t[0], t[2][0], j)
                    rot_trees += 1
                    rot_ok += (tree_value(rot_right(t), i, j, w) == v + d_r
                               and tree_value(rot_left(t), i, j, w) == v + d_l)
        if oracle_runs < 200:
            oracle_runs += 1
            oracle_ok += full_dp(n, w)[0][(0, n)] == max(tree_value(t_, 0, n, w) for t_ in trees(0, n))
        a, b, _ = classify(n, w, quints)
        if not b:
            continue
        found += 1
        found_not_rs3 += not a
        ok += endpoint_law(n, w, True) and optimal_path_everywhere(n, w) and endpoint_law(n, negate(w), False)
    check("Proposition 7: Theorem 1 / Corollary 2 (max and min form) over Z^2 (lexicographic), 20 000 seeded split-dependent "
          "tables n = 3 with values {(0,0), (0,1), (1,-5), (1,0)}: endpoint law and an optimal path tree on every "
          "RS3w table; Lemma 3 (DP = maximum over all trees) on the first 200 tables",
          ok == found > 0 and oracle_ok == oracle_runs == 200,
          f"{ok}/{found} RS3w tables ({found_not_rs3} not RS3) among {tot}; Lemma 3 on {oracle_ok}/{oracle_runs}")
    check("Proposition 7: Lemma 4 over Z^2 (lexicographic), same 20 000 tables: at every tree with an interior root the "
          "explicit values of both rotated trees equal val(T) + Delta_R and val(T) + Delta_L",
          rot_ok == rot_trees > 0, f"{rot_ok}/{rot_trees} trees with an interior root")


def main():
    t0 = time.time()
    for name, fn in (("T", part_theorems), ("A", part_proof), ("K", part_remarks), ("E", part_lemmas),
                     ("S", part_setting), ("C", part_controls), ("G", part_group_split), ("IR", iv_part_remark),
                     ("IP/IT", iv_part_exhaustive), ("IS", iv_part_random), ("IG", iv_part_group),
                     ("IC", iv_part_claim), ("II", iv_part_infinity)):
        t = time.time()
        print(f"== part {name}")
        fn()
        print(f"   ({time.time() - t:.1f} s)")
    print(f"total {time.time() - t0:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
