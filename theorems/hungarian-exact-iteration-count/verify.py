#!/usr/bin/env python3
"""Verifier for theorems/hungarian-exact-iteration-count (see README.md in this folder).

Computations are evidence; the proofs are in the README. Standard library only, no network, deterministic (fixed
seeds). Exit code 0 only if every check passes. --full adds the exhaustive 6 x 6 case over {0, 1}.

The square checks run the UNCHANGED implementation pairs/assignment-brute-vs-hungarian/implementations/hungarian.py.
It is given a matrix object that records every entry read: the code reads one row object per iteration
(`row = C[i0 - 1]`) and one entry per evaluation of `cur` (`row[j - 1]`), plus n rows and n entries for the final sum.
From this record the script recovers, per inserted row, the number of iterations, the columns scanned by each
iteration, and the column selected by each iteration except the last (the column that disappears from the scan).

Checks:
  F  closed forms: sum_{i<=m} sum_{t<=i} (n - t + 1) = (n+1)m(m+1)/2 - m(m+1)(m+2)/6 = m(m+1)(3n - m + 1)/6.
  H  Theorem 2 (square): exhaustive over small value sets, seeded random row-monotone matrices (ties, negative,
     constant rows; also exact rational entries), the entry's generate_scaling family, and the validator's six V2
     instances (exact counts).
  L  Lemma 1 and Proposition 6 on general matrices (at most i iterations, n - t + 1 evaluations in iteration t, the
     optimal value), and the Remark's 2 x 2 example where row 2 stops after one iteration.
  I  Lemma D, Lemma T and the invariants (I1)-(I3) on the internal state of the rectangular form (an exact copy of the
     entry's code for m = n, see R), with distances in the digraph D from an independent Bellman-Ford.
  R  the rectangular form (rows 1..m, columns 1..n, m <= n): equal to the entry code when m = n; Proposition 4
     (first m columns suffice), exact counts of Corollary 3 on exhaustive scopes and at large sizes.
  S  Proposition 5 (the column shift M j).
Usage (from the repository root): python theorems/hungarian-exact-iteration-count/verify.py [--full]
"""
import importlib.util
import itertools
import random
import sys
import time
from array import array
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIR = ROOT / "pairs" / "assignment-brute-vs-hungarian"
FULL = "--full" in sys.argv[1:]
FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, PAIR / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HUNGARIAN = load("implementations/hungarian.py", "as_hungarian").assignment_hungarian
HARNESS = load("harness.py", "as_harness")


def total_cur(m, n):
    return (n + 1) * m * (m + 1) // 2 - m * (m + 1) * (m + 2) // 6


# ------------------------------------------------------------------------------------------------ recording matrix
class _Row:
    __slots__ = ("data", "log")

    def __init__(self, data, log):
        self.data, self.log = data, log

    def __getitem__(self, j):
        self.log.append(j + 1)          # entry read: column j + 1 (1-based)
        return self.data[j]

    def __len__(self):
        return len(self.data)


class _Matrix:
    __slots__ = ("rows", "log")

    def __init__(self, C, log):
        self.log = log
        self.rows = [_Row(r, log) for r in C]

    def __getitem__(self, i):
        self.log.append(-(i + 1))       # row object read: row i + 1 (1-based)
        return self.rows[i]

    def __len__(self):
        return len(self.rows)


FINAL_READ_ANOMALIES = []     # runs whose last 2n reads are not (row object, column k), k = 1..n; see main()


def run_recorded(C):
    """Runs the unchanged entry code. Returns (value, searches), where searches[i - 1] is the list of iterations of
    row i's search and each iteration is the list of columns whose `cur` it evaluated, in order."""
    log = array("i")
    value = HUNGARIAN(_Matrix(C, log))
    n = len(C)
    body, final = log[:len(log) - 2 * n], log[len(log) - 2 * n:]
    if not all(final[2 * k] < 0 and final[2 * k + 1] == k + 1 for k in range(n)):
        FINAL_READ_ANOMALIES.append(n)
        return value, []            # an empty record makes every statement about this run fail as well
    searches = []
    nxt = 1
    for x in body:
        if x < 0:
            if -x == nxt:               # the first read of row nxt starts its search (it is never read earlier)
                searches.append([])
                nxt += 1
            searches[-1].append([])
        else:
            searches[-1][-1].append(x)
    return value, searches


def selections(search):
    """Columns selected by iterations 1..T-1 (the column missing from the next iteration's scan)."""
    out = []
    for a, b in zip(search, search[1:]):
        gone = set(a) - set(b)
        if len(gone) != 1 or not set(b) <= set(a):
            return None
        out.append(gone.pop())
    return out


def theorem_h_holds(C):
    """Row i: exactly i iterations; iteration t scans the n - t + 1 unused columns in increasing order; iterations
    1..i-1 select columns 1..i-1 (in some order); total cur = n(n+1)(2n+1)/6. Also returns the value."""
    n = len(C)
    value, searches = run_recorded(C)
    ok = len(searches) == n
    for i, srch in enumerate(searches, start=1):
        ok &= len(srch) == i and all(len(it) == n - t + 1 and it == sorted(it) for t, it in enumerate(srch, 1))
        sel = selections(srch)
        ok &= sel is not None and sorted(sel) == list(range(1, i))
    ok &= sum(len(it) for s in searches for it in s) == n * (n + 1) * (2 * n + 1) // 6
    return ok, value, searches


def nondecreasing_rows(n, values):
    return [r for r in itertools.combinations_with_replacement(values, n)]


# ------------------------------------------------------------------------------------------------ F: closed forms
def part_forms():
    ok = all(sum(n - t + 1 for i in range(1, m + 1) for t in range(1, i + 1)) == total_cur(m, n)
             == m * (m + 1) * (3 * n - m + 1) // 6 for n in range(0, 61) for m in range(0, n + 1))
    ok &= all(total_cur(n, n) == n * (n + 1) * (2 * n + 1) // 6 for n in range(0, 200))
    check("sum_{i<=m} sum_{t<=i} (n - t + 1) = (n+1)m(m+1)/2 - m(m+1)(m+2)/6 = m(m+1)(3n - m + 1)/6 for all "
          "0 <= m <= n <= 60; = n(n+1)(2n+1)/6 at m = n", ok)
    ok = all(m * (m + 1) * (2 * n + 1) <= 6 * total_cur(m, n) <= m * (m + 1) * (3 * n + 1)
             for n in range(1, 61) for m in range(1, n + 1))
    check("m(m+1)(2n+1)/6 <= that count <= m(m+1)(3n+1)/6 for 1 <= m <= n <= 60 (so it is Theta(m^2 n))", ok)


# ------------------------------------------------------------------------------------------------ H: Theorem 2
def part_theorem():
    scopes = [(2, range(-1, 2)), (3, range(-1, 2)), (4, range(-1, 2)), (2, range(0, 4)), (3, range(0, 4)),
              (5, range(0, 2))] + ([(6, range(0, 2))] if FULL else [])
    for n, vals in scopes:
        rows = nondecreasing_rows(n, vals)
        good = total = 0
        for C in itertools.product(rows, repeat=n):
            ok, value, _ = theorem_h_holds(C)
            good += ok
            total += 1
        check(f"exhaustive, n = {n}, entries in {{{vals.start}..{vals.stop - 1}}}, all {total} matrices with "
              f"non-decreasing rows: Theorem 2 holds", good == total)
    rng = random.Random(20261007)
    good = total = correct = 0
    for lo, hi in ((-3, 3), (-100, 100), (0, 1), (-10 ** 6, -10 ** 6 + 2), (5, 5)):
        for _ in range(60):
            n = rng.randint(1, 12)
            C = tuple(tuple(sorted(rng.randint(lo, hi) for _ in range(n))) for _ in range(n))
            ok, value, _ = theorem_h_holds(C)
            good += ok
            correct += value == HARNESS._subset_dp(C)
            total += 1
    for n in (50, 80):
        for _ in range(3):
            C = tuple(tuple(sorted(rng.randint(-50, 50) for _ in range(n))) for _ in range(n))
            ok, value, _ = theorem_h_holds(C)
            good += ok
            total += 1
            correct += 1
    check(f"{total} seeded random row-monotone matrices (ties, negative and constant rows; n <= 12, and n = 50, 80): "
          f"Theorem 2 holds, and the value equals the subset DP of the entry's harness (n <= 12)",
          good == total == correct)
    from fractions import Fraction
    good = total = 0
    for _ in range(200):
        n = rng.randint(1, 10)
        C = tuple(tuple(sorted(Fraction(rng.randint(-30, 30), rng.randint(1, 6)) for _ in range(n))) for _ in range(n))
        ok, value, _ = theorem_h_holds(C)
        good += ok and value == HARNESS._subset_dp(C)
        total += 1
    check(f"{total} seeded random row-monotone matrices with exact rational entries (Fraction, n <= 10, many ties): "
          f"Theorem 2 holds and the value equals the subset DP", good == total)
    good = total = 0
    for n in range(1, 41):
        for k in range(3):
            C = HARNESS.generate_scaling(n, random.Random(f"hungarian-exact|{n}|{k}"))
            good += theorem_h_holds(C)[0]
            total += 1
    check(f"generate_scaling (C[i][j] = 1000 j + r, r in 0..999), n = 1..40, 3 seeds each ({total} matrices): "
          f"Theorem 2 holds", good == total)
    expect = {30: (465, 9455), 50: (1275, 42925), 75: (2850, 143450), 100: (5050, 338350), 150: (11325, 1136275),
              200: (20100, 2686700)}
    got = {}
    for n in expect:
        C = HARNESS.generate_scaling(n, random.Random(f"assignment-brute-vs-hungarian|v2|{n}"))
        ok, _, searches = theorem_h_holds(C)
        got[n] = (sum(len(s) for s in searches), sum(len(it) for s in searches for it in s)) if ok else None
    check("the validator's V2 instances (seed '<entry id>|v2|n'), (n, iterations, cur evaluations): "
          + ", ".join(f"({n}, {a}, {b})" for n, (a, b) in expect.items()), got == expect)


# ------------------------------------------------------------------------------------------------ L: Lemma 1
def part_lemma():
    rng = random.Random(7)
    bad = total = 0
    for kind in range(3):
        for _ in range(300):
            n = rng.randint(1, 12)
            if kind == 0:
                C = tuple(tuple(rng.randint(0, 99) for _ in range(n)) for _ in range(n))
            elif kind == 1:
                C = tuple(tuple(rng.randint(-3, 3) for _ in range(n)) for _ in range(n))
            else:
                C = tuple(tuple(rng.randint(-10 ** 9, 10 ** 9) for _ in range(n)) for _ in range(n))
            value, searches = run_recorded(C)
            ok = len(searches) == n and value == HARNESS._subset_dp(C)
            for i, srch in enumerate(searches, start=1):
                ok &= len(srch) <= i and all(len(it) == n - t + 1 for t, it in enumerate(srch, 1))
            bad += not ok
            total += 1
    check(f"Lemma 1 and Proposition 6 on {total} general seeded matrices (n <= 12; entries in 0..99, -3..3, +-10^9): "
          f"row i takes <= i iterations, iteration t evaluates cur n - t + 1 times; value = subset DP", bad == 0)
    value, searches = run_recorded(((0, 1), (1, 0)))
    check("Remark: for C = ((0, 1), (1, 0)) the search for row 2 runs 1 iteration (not 2); value 0",
          [len(x) for x in searches] == [1, 1] and value == 0)


# ------------------------------------------------------------------------------------------------ R: rectangular
def hungarian_rect(C, n):
    """The entry's code with rows 1..m and columns 1..n (m = len(C) <= n): the same statements, loops over columns
    run to n. Returns (value, per-row iteration counts, per-row cur counts, per-row selected columns)."""
    m = len(C)
    INF = float("inf")
    u = [0] * (m + 1)
    v = [0] * (n + 1)
    match = [0] * (n + 1)
    way = [0] * (n + 1)
    iters, curs, sels = [], [], []
    for i in range(1, m + 1):
        match[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        it = cu = 0
        sel = []
        while True:
            it += 1
            used[j0] = True
            i0 = match[j0]
            row = C[i0 - 1]
            ui0 = u[i0]
            delta = INF
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = row[j - 1] - ui0 - v[j]
                    cu += 1
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[match[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            sel.append(j0)
            if match[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            match[j0] = match[j1]
            j0 = j1
        iters.append(it)
        curs.append(cu)
        sels.append(sel)
    return sum(C[match[j] - 1][j - 1] for j in range(1, n + 1) if match[j]), iters, curs, sels


def brute_rect(C, n):
    m = len(C)
    return min(sum(C[i][p[i]] for i in range(m)) for p in itertools.permutations(range(n), m))


def run_with_state_checks(C, n, fails):
    """hungarian_rect with the internal state checked against Lemma D, Lemma T and the invariants (I1)-(I3); every
    violated statement is counted in fails[name]. Distances in the digraph D come from an independent Bellman-Ford."""
    m = len(C)
    INF = float("inf")
    u = [0] * (m + 1)
    v = [0] * (n + 1)
    match = [0] * (n + 1)
    way = [0] * (n + 1)

    def red(x, y):
        return C[x - 1][y - 1] - u[x] - v[y]

    def invariants(i):
        ok = all(red(x, y) >= 0 for x in range(1, i) for y in range(1, n + 1))
        fails["(I1)"] += not ok
        fails["(I2)"] += not all(red(match[c], c) == 0 for c in range(1, n + 1) if match[c])
        fails["(I3) and u_i = 0"] += not (all(v[y] == 0 for y in range(1, n + 1) if not match[y])
                                         and (i > m or u[i] == 0))

    prev_final = None
    for i in range(1, m + 1):
        invariants(i)
        if prev_final is not None:                       # Lemma T for row i - 1 (hypothesis: i - 1 iterations)
            j_star, it_prev = prev_final
            if it_prev == i - 1:
                seen = {j_star}
                stack = [j_star]
                while stack:
                    c = stack.pop()
                    for y in range(1, n + 1):
                        if y not in seen and y != c and match[c] and red(match[c], y) == 0:
                            seen.add(y)
                            stack.append(y)
                fails["Lemma T"] += not all(c in seen for c in range(1, n + 1) if match[c])
        # distances from column 0 in D (arcs from 0 with row i, and from matched columns with their rows)
        dist = [INF] * (n + 1)
        dist[0] = 0
        tails = [(0, i)] + [(c, match[c]) for c in range(1, n + 1) if match[c]]
        for _ in range(n + 1):
            for c, x in tails:
                if dist[c] < INF:
                    for y in range(1, n + 1):
                        if y != c and dist[c] + red(x, y) < dist[y]:
                            dist[y] = dist[c] + red(x, y)
        match[0] = i
        j0 = 0
        minv = [INF] * (n + 1)
        used = [False] * (n + 1)
        acc = 0
        labels = []
        it = 0
        while True:
            it += 1
            used[j0] = True
            i0 = match[j0]
            row = C[i0 - 1]
            ui0 = u[i0]
            delta = INF
            j1 = 0
            for j in range(1, n + 1):
                if not used[j]:
                    cur = row[j - 1] - ui0 - v[j]
                    if cur < minv[j]:
                        minv[j] = cur
                        way[j] = j0
                    if minv[j] < delta:
                        delta = minv[j]
                        j1 = j
            for j in range(n + 1):
                if used[j]:
                    u[match[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            acc += delta
            labels.append(acc)
            fails["Lemma D(a): label at selection = distance in D"] += acc != dist[j1]
            j0 = j1
            if match[j0] == 0:
                break
        fails["Lemma D(a): labels non-decreasing"] += any(a > b for a, b in zip(labels, labels[1:]))
        tree = [j for j in range(1, n + 1) if used[j]] + [j0]
        fails["Lemma D(b): tree arcs tight, v = 0 at the final column"] += not (
            all(red(match[way[j]], j) == 0 for j in tree) and v[j0] == 0)
        prev_final = (j0, it)
        while j0:
            j1 = way[j0]
            match[j0] = match[j1]
            j0 = j1
    invariants(m + 1)


def part_state():
    from collections import Counter
    fails = Counter()
    count = 0
    for m, n, vals in ((2, 3, range(-1, 2)), (2, 4, range(0, 3)), (3, 4, range(0, 3)), (3, 5, range(0, 3))):
        for C in itertools.product(nondecreasing_rows(n, vals), repeat=m):
            run_with_state_checks(C, n, fails)
            count += 1
    rng = random.Random(17)
    for _ in range(400):
        n = rng.randint(1, 8)
        m = rng.randint(1, n)
        C = tuple(tuple(rng.randint(-20, 20) for _ in range(n)) for _ in range(m))
        run_with_state_checks(C, n, fails)
        count += 1
    for name in ("(I1)", "(I2)", "(I3) and u_i = 0", "Lemma D(a): label at selection = distance in D",
                 "Lemma D(a): labels non-decreasing", "Lemma D(b): tree arcs tight, v = 0 at the final column",
                 "Lemma T"):
        check(f"{name}: {count} matrices (all row-monotone m x n of four exhaustive scopes, 400 seeded general ones)",
              fails[name] == 0, f"{fails[name]} violations")


def part_rect():
    rng = random.Random(11)
    same = 0
    for _ in range(200):
        n = rng.randint(1, 9)
        C = tuple(tuple(rng.randint(-5, 20) for _ in range(n)) for _ in range(n))
        val, searches = run_recorded(C)
        rv, iters, curs, sels = hungarian_rect(C, n)
        same += (rv == val and iters == [len(s) for s in searches]
                 and curs == [sum(len(it) for it in s) for s in searches]
                 and all(selections(s) == sl[:-1] for s, sl in zip(searches, sels)))
    check("rectangular form with m = n reproduces the entry code exactly (value, iterations, cur evaluations, "
          "selections; 200 seeded general matrices)", same == 200)
    scopes = [(1, 4, range(0, 3)), (2, 3, range(-1, 2)), (2, 4, range(0, 3)), (3, 4, range(0, 3)), (2, 5, range(0, 3)),
              (3, 5, range(0, 3))]
    total = good = 0
    for m, n, vals in scopes:
        rows = nondecreasing_rows(n, vals)
        for C in itertools.product(rows, repeat=m):
            rv, iters, curs, sels = hungarian_rect(C, n)
            sub = tuple(r[:m] for r in C)
            sv, s_iters, s_curs, _ = hungarian_rect(sub, m)
            opt = brute_rect(C, n)
            ok = rv == opt == sv == brute_rect(sub, m)
            ok &= iters == list(range(1, m + 1)) and sum(curs) == total_cur(m, n)
            ok &= all(sorted(sl[:-1]) == list(range(1, i)) and sl[-1] == i for i, sl in enumerate(sels, start=1))
            ok &= s_iters == list(range(1, m + 1)) and sum(s_curs) == m * (m + 1) * (2 * m + 1) // 6
            good += ok
            total += 1
    check(f"exhaustive rectangular scopes (m, n, entries) = (1,4,0..2), (2,3,-1..1), (2,4,0..2), (3,4,0..2), "
          f"(2,5,0..2), (3,5,0..2): all {total} row-monotone matrices: optimum over all columns = optimum over the "
          f"first m columns (brute force) = both runs; row i takes exactly i iterations, selecting 1..i-1 then i; "
          f"cur counts (n+1)m(m+1)/2 - m(m+1)(m+2)/6 and m(m+1)(2m+1)/6", good == total == 13417)
    good = 0
    for _ in range(300):
        m = rng.randint(1, 5)
        n = rng.randint(m, 7)
        C = tuple(tuple(sorted(rng.randint(-20, 20) for _ in range(n))) for _ in range(m))
        rv, iters, curs, _ = hungarian_rect(C, n)
        good += rv == brute_rect(C, n) == brute_rect(tuple(r[:m] for r in C), m) and iters == list(range(1, m + 1)) \
            and sum(curs) == total_cur(m, n)
    check("300 seeded random row-monotone m x n matrices (m <= n <= 7, ties and negatives): same statements", good == 300)
    out = []
    ok = True
    for m, n, full_e, restr_e in ((10, 1000, 54835, 385), (30, 300, 135005, 9455), (40, 41, 22960, 22140)):
        C = tuple(tuple(sorted(rng.randint(0, 10 ** 6) for _ in range(n))) for _ in range(m))
        rv, iters, curs, _ = hungarian_rect(C, n)
        sv, _, s_curs, _ = hungarian_rect(tuple(r[:m] for r in C), m)
        ok &= sum(curs) == total_cur(m, n) == full_e and sum(s_curs) == restr_e and rv == sv
        out.append(f"({m}, {n}): {sum(curs)} vs {sum(s_curs)}")
    check("large sizes, cur evaluations full vs first m columns: " + ", ".join(out), ok)


# ------------------------------------------------------------------------------------------------ S: column shift
def part_shift():
    rng = random.Random(5)
    good = 0
    for _ in range(300):
        n = rng.randint(1, 6)
        lo = rng.choice((-50, -3, 0, 7))
        C = tuple(tuple(rng.randint(lo, lo + rng.choice((0, 3, 60))) for _ in range(n)) for _ in range(n))
        flat = [x for r in C for x in r]
        Mk = max(flat) - min(flat) + 1
        Cs = tuple(tuple(C[i][j] + Mk * (j + 1) for j in range(n)) for i in range(n))      # column j + 1 gets M(j+1)
        inc = all(r[j] < r[j + 1] for r in Cs for j in range(n - 1))
        perms = list(itertools.permutations(range(n)))
        cost = {p: sum(C[i][p[i]] for i in range(n)) for p in perms}
        costs = {p: sum(Cs[i][p[i]] for i in range(n)) for p in perms}
        shift = Mk * n * (n + 1) // 2
        same_shift = all(costs[p] - cost[p] == shift for p in perms)
        opt = {p for p in perms if cost[p] == min(cost.values())}
        opts = {p for p in perms if costs[p] == min(costs.values())}
        ok_h, val, _ = theorem_h_holds(Cs)
        good += inc and same_shift and opt == opts and ok_h and val == min(cost.values()) + shift
    check("Proposition 5 on 300 seeded matrices (n <= 6, negative and constant ranges included): adding M j to column j "
          "(columns 1..n, M = max - min + 1) gives strictly increasing rows, shifts every permutation's cost by "
          "M n(n+1)/2, keeps the optimal permutations, and the entry code then runs exactly i iterations per row",
          good == 300)


def main():
    t0 = time.time()
    for name, fn in (("F", part_forms), ("H", part_theorem), ("L", part_lemma), ("I", part_state), ("R", part_rect),
                     ("S", part_shift)):
        t = time.time()
        print(f"== part {name}")
        fn()
        print(f"   ({time.time() - t:.1f} s)")
    check("the recording method: in every recorded run the code's last 2n reads are the final sum's (row object, then "
          "column k, for k = 1..n), so the search record is parsed correctly", not FINAL_READ_ANOMALIES,
          f"{len(FINAL_READ_ANOMALIES)} runs with other final reads")
    print(f"total {time.time() - t0:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
