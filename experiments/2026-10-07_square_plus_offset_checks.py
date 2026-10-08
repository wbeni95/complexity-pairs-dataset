"""Checks for pairs/square-plus-offset-count-enumeration-vs-intervals-vs-groups: every number the entry quotes.

Problem. L(v) = number of binary digits of |v| (L(0) = 1). Writing k >= 0 as X^2 + C (X >= 0, C = k - X^2) costs
f_k(X) = L(X) + L(C) + [C < 0] bits. S_n = {0 <= k < 2^n : min over X of f_k(X) <= n - 4}; the entry counts |S_n|.

Deterministic (fixed string seeds, which do not depend on PYTHONHASHSEED; the only run-dependent output is the elapsed
seconds). Standard library only, no network. Run from the repository root:
    python experiments/2026-10-07_square_plus_offset_checks.py [section ...]

Sections (computations are evidence; the proofs are in the entry's PROOFS.md, whose section numbers are given):
  A  Lemma A (three candidates 0, r, r+1 with r = isqrt(k)) against a brute force over ALL roots in the window of
     Lemma 0 (X^2 < k + 2^L(k)), for every k < 2^KA; Lemma 0 itself; the two boundary cases k = 8 and k = 32 of
     case (iii); the example k = 80, where X = 7 is cheaper than X = r = 8 and r + 1 = 9 is the minimiser (PROOFS 2).
  B  Lemma B: the union of the clipped intervals (sorted, then merged) equals the brute-force count of S_n
     (every k, all roots) for n <= NB; the empty clipped interval of the example n = 13, X = 91 (PROOFS 3).
  C  The three implementations agree: enumeration = interval sweep = groups for n <= NC, and interval sweep =
     groups = sorted union for n <= NU (PROOFS 4, 5).
  S  Structure behind A3 (PROOFS 5, 1.3): left ends strictly increasing over all roots with w >= 1 and the roots
     that start a new component forming a suffix of every group (n = 5..NS); the part below 0 has exactly m_1
     elements (n = 6..60, every root); at most 2 roots X <= T reach above 2^n - 1, both as recorded by the
     implementation (n = 5..400) and by a direct count that does not use it (n = 6..3000); L(T) = floor(n/2) + 1
     (n = 2..3000); the number of groups is max(0, min(L(T), n - 5)) (n = 0..400).
  N  Newton's integer square root (PROOFS 6): equal to math.isqrt for every q < 2^16 and for 20000 seeded random
     q < 2^600; the number of iterations never exceeds floor(log2(2 + log2 q)) + 2 (q >= 1; computed in exact
     integers), on those q and on every square root A3 computes for n = 1..400.
  V  Exact work counts (PROOFS 1, 7, 8): enumeration 3 * 2^n (n = 0..NC), interval sweep isqrt(2^n - 1) + 2
     (n = 0..NU; equal to 2^(n/2) + 1 for even n), groups floor(n/2) + 1 (n = 11..400); integer square roots in A3,
     counted by a wrapper around the function (n + 2 for n = 11..400, each of an argument below 2^(n+2), each within
     floor(log2(n + 4)) + 2 iterations for n = 1..400); the enumeration's other counts in an instrumented copy of
     its source (isqrt(2^n - 1) increments of r, 2^n + isqrt(2^n - 1) evaluations of the loop test, 2^n budget
     comparisons, n = 0..16); the implementation's own record of the integers it handles (below 2^(n+2),
     n = 6..400); T^2 < 2^(n+2) (n = 0..400) and T^2 + 2^(n-5) < 2^(n+1) (n = 6..400); the bit-size inequality
     floor(n/2) + 1 >= 2^(L(n)-2) (n = 1..100000).
  W  Word sizes by instrumentation (PROOFS 8): the source of each implementation is rewritten so that every
     integer value an expression evaluates to (names read, constants, operators, calls, subscripts, and the target of
     every augmented assignment) is recorded; the rewritten code returns the same results. For n >= 1 every recorded
     value is below 2^(n+2) in absolute value (A1: n = 1..16, A2: n = 1..34, A3: n = 1..400); for n = 0 every value
     is at most 5 in absolute value.
  T  The values |S_n| in the entry's README and notes (n = 6..16, 20, 24, 29, 32, 40) and in the unit tests,
     computed by the interval sweep and by A3; |S_n| = 0 for n <= 5; A3 processes 101 groups at n = 200
     (PROOFS 11).

Result (console, 2026-10-07, CPython 3.14.2; defaults KA = 18, NB = 16, NC = 22, NU = 42, NS = 36): every check
passes (0 mismatches in A, B, C; all structural facts, bounds and exact counts hold). Runs took 34-48 s on a laptop
(timing varies with load and is not a result).
"""
from __future__ import annotations

import ast
import importlib.util
import math
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ENTRY = REPO / "pairs" / "square-plus-offset-count-enumeration-vs-intervals-vs-groups"
KA, NB, NC, NU, NS = 18, 16, 22, 42, 36

FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


H = _load(ENTRY / "harness.py", "spo_harness")
A1 = _load(ENTRY / "implementations" / "enumeration.py", "spo_a1").count_by_enumeration
A2 = _load(ENTRY / "implementations" / "interval_sweep.py", "spo_a2").count_by_interval_sweep
G = _load(ENTRY / "implementations" / "groups.py", "spo_a3")


def L(v: int) -> int:
    v = -v if v < 0 else v
    return v.bit_length() if v else 1


def f(k: int, x: int) -> int:
    c = k - x * x
    return L(x) + (L(c) if c >= 0 else L(c) + 1)


def three(k: int) -> int:
    r = math.isqrt(k)
    return min(f(k, 0), f(k, r), f(k, r + 1))


def interval(x: int, v: int):
    """Unclipped J_X = (lo, hi) for w = v - L(x) >= 1, else None."""
    w = v - L(x)
    if w < 1:
        return None
    m = (1 << (w - 1)) - 1 if w >= 2 else 0
    return x * x - m, x * x + (1 << w) - 1


def T_of(n: int) -> int:
    return math.isqrt((1 << n) - 1) + 1


# ------------------------------------------------------------------------------------------------------------- A
def section_a() -> None:
    t = time.perf_counter()
    bad, evals = [], 0
    for k in range(1 << KA):
        top = math.isqrt(k + (1 << L(k)) - 1)
        evals += top + 1
        best = min(f(k, x) for x in range(top + 1))
        if best != three(k):
            bad.append(k)
    check(f"A  Lemma A vs all roots in the Lemma 0 window, every k < 2^{KA} ({1 << KA} values of k)", not bad,
          f"mismatches {len(bad)}, root evaluations {evals} ({time.perf_counter() - t:.1f} s)")
    # Lemma 0 itself on a smaller range: no root beyond the window is ever cheaper than X = 0
    pairs = 0
    worse = True
    for k in range(1 << 10):
        top = math.isqrt(k + (1 << L(k)) - 1)          # largest X inside the window
        for x in range(top + 1, top + 41):
            pairs += 1
            worse &= f(k, x) > f(k, 0)
    check(f"A  Lemma 0: roots with X^2 >= k + 2^L(k) cost more than X = 0 (k < 2^10, 40 roots past the window; "
          f"{pairs} pairs (k, X))", worse)
    # boundary cases of case (iii), sub-case X = 1, p = 2q + 1
    for q, k, need in ((1, 8, "d2 = 1 < 2^q"), (2, 32, "d1 = 7 < 2^(q+1)")):
        r = math.isqrt(k)
        d1, d2 = k - r * r, (r + 1) ** 2 - k
        ok = (L(r) == q + 1 and L(r + 1) == q + 1 and (1 << q) <= r
              and min(f(k, r), f(k, r + 1)) <= f(k, 1) == 2 * q + 2)
        check(f"A  case (iii), k = {k} (q = {q}): r = {r}, d1 = {d1}, d2 = {d2} ({need}); "
              f"f(1) = {f(k, 1)}, f(r) = {f(k, r)}, f(r+1) = {f(k, r + 1)}", ok)
    check("A  k = 8: r = 2 = 2^q, so the bound 2^q <= r is attained (a strict 2^q < r would fail)",
          math.isqrt(8) == 2)
    vals = {x: f(80, x) for x in range(15)}           # 0..14 is the window of Lemma 0 for k = 80
    check("A  k = 80: f(0) = 8, f(7) = 8, f(8) = 9, f(9) = 6, minimum 6 at X = 9 only (X = 0..14)",
          vals[0] == 8 and vals[7] == 8 and vals[8] == 9 and vals[9] == 6 and min(vals.values()) == 6
          and [x for x in vals if vals[x] == 6] == [9] and all(vals[x] >= 8 for x in vals if x != 9), str(vals))
    check("A  k = 80: the window of Lemma 0 is X <= 14 (14^2 = 196 < 80 + 2^L(80) = 208 <= 15^2), and X = 7 falls "
          "under case (iii) (1 <= 7 <= r - 1 = 7, L(7) = 3 < L(8) = 4)",
          L(80) == 7 and 14 * 14 < 80 + (1 << L(80)) <= 15 * 15 and math.isqrt(80) == 8 and L(7) < L(8))


# ------------------------------------------------------------------------------------------------------------- B
def section_b() -> None:
    t = time.perf_counter()
    bad = [n for n in range(1, NB + 1) if H.brute_force_count(n) != H.sorted_union_count(n)]
    check(f"B  Lemma B: sorted union of clipped intervals = brute force over all roots, n = 1..{NB} ({NB} values)",
          not bad, f"mismatches {bad} ({time.perf_counter() - t:.1f} s)")
    T13 = T_of(13)
    lo91, _ = interval(91, 13 - 4)
    check("B  n = 13: T = 91, L(91) = 7, w = 2, m = 1, and X = 91 has X^2 - m = 8280 > B = 8191 (empty clipped "
          "interval)", T13 == 91 and L(91) == 7 and lo91 == 8280 > (1 << 13) - 1)


# ------------------------------------------------------------------------------------------------------------- C
def section_c() -> None:
    t = time.perf_counter()
    bad = []
    for n in range(0, NC + 1):
        a, b, c = A1(n)[0], A2(n)[0], G.count_by_groups(n)[0]
        if not a == b == c:
            bad.append(n)
    check(f"C  enumeration = interval sweep = groups, n = 0..{NC} ({NC + 1} values)", not bad,
          f"mismatches {bad} ({time.perf_counter() - t:.1f} s)")
    t = time.perf_counter()
    bad = []
    for n in range(0, NU + 1):
        b, c, u = A2(n)[0], G.count_by_groups(n)[0], H.sorted_union_count(n)
        if not b == c == u:
            bad.append(n)
    check(f"C  interval sweep = groups = sorted union, n = 0..{NU} ({NU + 1} values)", not bad,
          f"mismatches {bad} ({time.perf_counter() - t:.1f} s)")


# ------------------------------------------------------------------------------------------------------------- S
def structure(n: int):
    """(left ends strictly increasing?, number of groups violating the suffix property, roots examined)."""
    v = n - 4
    T = T_of(n)
    starts, end, prev = {}, None, None
    strict = True
    for x in range(T + 1):
        iv = interval(x, v)
        if iv is None:
            continue
        lo, hi = iv
        if prev is not None and lo <= prev:
            strict = False
        prev = lo
        starts[x] = end is None or lo > end + 1
        end = hi if end is None else max(end, hi)
    groups: dict[int, list] = {}
    for x, new in starts.items():
        groups.setdefault(L(x), []).append((x, new))
    bad = 0
    for g in groups.values():
        g.sort()
        seen = False
        for _, new in g[1:]:
            if new:
                seen = True
            elif seen:
                bad += 1
                break
    return strict, bad, len(starts)


def above_range_direct(n: int) -> int:
    """Number of roots X <= T with w = n - 4 - L(X) >= 1 and X^2 + 2^w - 1 >= 2^n, counted group by group with
    math.isqrt (independent of groups.py)."""
    v, T, top = n - 4, T_of(n), 1 << n
    count, l = 0, 1
    while True:
        a = 0 if l == 1 else 1 << (l - 1)
        w = v - l
        if a > T or w < 1:
            break
        b = min((1 << l) - 1, T)
        s = (1 << w) - 1
        if b * b + s >= top:                                   # the group can reach 2^n at all
            first = math.isqrt(top - s - 1) + 1                # smallest X with X^2 >= 2^n - s
            count += max(0, b - max(a, first) + 1)
        l += 1
    return count


def section_s() -> None:
    nonstrict, bad_groups, roots = [], 0, 0
    for n in range(5, NS + 1):
        strict, bad, cnt = structure(n)
        if not strict:
            nonstrict.append(n)
        bad_groups += bad
        roots += cnt
    check(f"S  left ends X^2 - m strictly increasing over all roots with w >= 1, n = 5..{NS} ({roots} roots)",
          not nonstrict, f"violations at n = {nonstrict}")
    check(f"S  component-starting roots form a suffix of every group, n = 5..{NS}", bad_groups == 0,
          f"violating groups {bad_groups}")
    ok_below = True
    for n in range(6, 61):
        # complete scan without Lemma C: inside group l the left end X^2 - m_l is smallest at the first root a_l,
        # so the left ends of all roots X >= 1 exceed -m_1 iff 1 - m_1 > -m_1 (X = 1) and a_l^2 - m_l > -m_1 for
        # every group l >= 2 with a_l <= T and w_l >= 1
        v = n - 4
        T = T_of(n)
        lo0, hi0 = interval(0, v)
        m1 = -lo0
        firsts = [interval(1, v)[0]]
        l = 2
        while (1 << (l - 1)) <= T and v - l >= 1:
            firsts.append(interval(1 << (l - 1), v)[0])
            l += 1
        ok_below &= hi0 >= 0 and all(lo > -m1 for lo in firsts)
    check("S  part below 0 = [-m_1, -1] (X = 0 has the smallest left end and right end >= 0), n = 6..60, all roots",
          ok_below)
    mx = 0
    for n in range(5, 401):
        st: dict = {}
        G.count_groups(n, st)
        mx = max(mx, st["above_range_roots"])
    check("S  Lemma E(c), as recorded by groups.py: at most 2 roots X <= T have X^2 + 2^w - 1 > 2^n - 1, n = 5..400",
          mx <= 2, f"maximum {mx}")
    direct = [above_range_direct(n) for n in range(6, 3001)]
    same = True
    for n in range(6, 401):
        st = {}
        G.count_groups(n, st)
        same &= direct[n - 6] == st["above_range_roots"]
    check("S  Lemma E(c), direct count without groups.py: at most 2 such roots, n = 6..3000 (2995 values); equal to "
          "the count recorded by groups.py for n = 6..400", max(direct) <= 2 and same, f"maximum {max(direct)}")
    bad_lt = [n for n in range(2, 3001) if L(T_of(n)) != n // 2 + 1]
    check("S  L(T) = floor(n/2) + 1, n = 2..3000 (2999 values)", not bad_lt, f"violations at n = {bad_lt[:10]}")
    bad_g = []
    for n in range(0, 401):
        want = max(0, min(L(T_of(n)), n - 5))
        got = G.count_by_groups(n)[1]
        if got != want or (n >= 11 and got != n // 2 + 1):
            bad_g.append(n)
    check("S  groups = max(0, min(L(T), n - 5)) for n = 0..400, and = floor(n/2) + 1 for n = 11..400", not bad_g,
          f"violations at n = {bad_g[:10]}")


# ------------------------------------------------------------------------------------------------------------- N
def newton_bound(q: int) -> int:
    """floor(log2(2 + log2 q)) + 2 in exact integers: t = largest t with 2^(2^t - 2) <= q (q >= 1)."""
    t = 0
    while (1 << (t + 1)) - 2 <= q.bit_length() - 1:
        t += 1
    return t + 2


def section_n() -> None:
    bad, worst = [], 0.0
    rng = random.Random("square-plus-offset|newton")
    qs = list(range(1 << 16)) + [rng.getrandbits(rng.randint(1, 600)) for _ in range(20000)]
    for q in qs:
        st: dict = {}
        r = G.isqrt_newton(q, st)
        if r != math.isqrt(q):
            bad.append(q)
        if q >= 1:
            worst = max(worst, st["newton_steps"] / newton_bound(q))
    check(f"N  Newton isqrt = math.isqrt on all q < 2^16 and 20000 seeded q < 2^600 ({len(qs)} values)", not bad,
          f"mismatches {len(bad)}")
    check("N  Newton iterations <= floor(log2(2 + log2 q)) + 2 on those q (q >= 1)", worst <= 1,
          f"max iterations/bound = {worst:.3f}")
    worst_a3, calls = 0.0, 0
    orig = G.isqrt_newton

    def wrapped(q, stats=None):
        nonlocal worst_a3, calls
        st: dict = {}
        r = orig(q, st)
        calls += 1
        if q >= 1:
            worst_a3 = max(worst_a3, st["newton_steps"] / newton_bound(q))
        if stats is not None:
            for key, val in st.items():
                stats[key] = stats.get(key, 0) + val
        return r

    G.isqrt_newton = wrapped
    try:
        for n in range(1, 401):
            G.count_groups(n, {})
    finally:
        G.isqrt_newton = orig
    check(f"N  every square root computed by A3 for n = 1..400 within the step bound ({calls} calls)", worst_a3 <= 1,
          f"max iterations/bound = {worst_a3:.3f}")


# ------------------------------------------------------------------------------------------------------------- V
class _CountA1(ast.NodeTransformer):
    """Instrument enumeration.py: count evaluations of the while-test, increments of r and budget comparisons."""

    def __init__(self):
        self.found = {"test": 0, "inc": 0, "budget": 0}

    @staticmethod
    def _count(kind, node):
        return ast.Call(func=ast.Name(id="_cnt_", ctx=ast.Load()), args=[ast.Constant(kind), node], keywords=[])

    def visit_While(self, node):
        self.generic_visit(node)
        node.test = self._count("test", node.test)
        self.found["test"] += 1
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if isinstance(node.target, ast.Name) and node.target.id == "r":
            self.found["inc"] += 1
            return [node, ast.Expr(self._count("inc", ast.Constant(None)))]
        return node

    def visit_Compare(self, node):
        self.generic_visit(node)
        if (isinstance(node.left, ast.Name) and node.left.id == "best" and len(node.comparators) == 1
                and isinstance(node.comparators[0], ast.Name) and node.comparators[0].id == "budget"):
            self.found["budget"] += 1
            return self._count("budget", node)
        return node


def a1_counts():
    """Return (instrumented count_by_enumeration, counter dict, transformer) built from the original source."""
    counts = {"test": 0, "inc": 0, "budget": 0}

    def _cnt_(kind, value):
        counts[kind] += 1
        return value

    path = ENTRY / "implementations" / "enumeration.py"
    tr = _CountA1()
    tree = tr.visit(ast.parse(path.read_text(encoding="utf-8")))
    ast.fix_missing_locations(tree)
    ns = {"_cnt_": _cnt_, "__name__": "counted_enumeration"}
    exec(compile(tree, str(path), "exec"), ns)
    return ns["count_by_enumeration"], counts, tr


def section_v() -> None:
    bad1 = [n for n in range(0, NC + 1) if A1(n)[1] != 3 * (1 << n)]
    check(f"V  enumeration: exactly 3 * 2^n cost evaluations, n = 0..{NC}", not bad1, f"violations {bad1}")
    fn, counts, tr = a1_counts()
    bad_c = []
    for n in range(0, 17):
        for key in counts:
            counts[key] = 0
        same = fn(n) == A1(n)
        i = math.isqrt((1 << n) - 1)
        if not (same and counts["test"] == (1 << n) + i and counts["inc"] == i and counts["budget"] == 1 << n):
            bad_c.append(n)
    check("V  enumeration, counted in an instrumented copy: exactly isqrt(2^n - 1) increments of r, "
          "2^n + isqrt(2^n - 1) evaluations of the loop test, 2^n budget comparisons, same results, n = 0..16",
          not bad_c and tr.found == {"test": 1, "inc": 1, "budget": 1},
          f"violations {bad_c}; instrumented sites {tr.found}")
    bad2 = [n for n in range(0, NU + 1) if A2(n)[1] != math.isqrt((1 << n) - 1) + 2]
    bad2e = [n for n in range(0, NU + 1, 2) if A2(n)[1] != (1 << (n // 2)) + 1]
    check(f"V  interval sweep: exactly isqrt(2^n - 1) + 2 roots (n = 0..{NU}), 2^(n/2) + 1 for even n (0..{NU})",
          not bad2 and not bad2e, f"violations {bad2 + bad2e}")
    bad3 = [n for n in range(11, 401) if G.count_by_groups(n)[1] != n // 2 + 1]
    check("V  groups: exactly floor(n/2) + 1 root groups, n = 11..400", not bad3, f"violations {bad3}")
    # square roots counted by a wrapper around the module function (independent of the implementation's stats)
    orig = G.isqrt_newton
    rec = {"calls": 0, "max_q": 0, "steps": 0}

    def wrapped(q, stats=None):
        st: dict = {}
        r = orig(q, st)
        rec["calls"] += 1
        rec["max_q"] = max(rec["max_q"], q)
        rec["steps"] = max(rec["steps"], st.get("newton_steps", 0))
        return r

    bad4, bad5, bad6, total_calls = [], [], [], 0
    G.isqrt_newton = wrapped
    try:
        for n in range(1, 401):
            rec.update(calls=0, max_q=0, steps=0)
            G.count_by_groups(n)
            total_calls += rec["calls"]
            if n >= 11 and rec["calls"] != n + 2:
                bad4.append(n)
            if rec["max_q"] >= 1 << (n + 2):
                bad5.append(n)
            if rec["steps"] > (n + 4).bit_length() - 1 + 2:            # floor(log2(n + 4)) + 2, exact
                bad6.append(n)
    finally:
        G.isqrt_newton = orig
    check("V  groups: exactly n + 2 integer square roots (one for T, two per group, one fewer for even n), "
          "n = 11..400", not bad4, f"violations {bad4[:10]}")
    check(f"V  groups: every square-root argument is below 2^(n+2) and needs at most floor(log2(n + 4)) + 2 "
          f"iterations, n = 1..400 ({total_calls} calls)", not bad5 and not bad6,
          f"violations {bad5[:10]} {bad6[:10]}")
    bad7 = []
    for n in range(6, 401):
        st: dict = {}
        G.count_groups(n, st)
        if st["max_value_bits"] > n + 2:
            bad7.append(n)
    check("V  groups, as recorded by the implementation: the integers it records (incl. Newton's x + floor(q/x)) are "
          "below 2^(n+2) in absolute value, n = 6..400", not bad7, f"violations {bad7[:10]}")
    bad8 = [n for n in range(6, 401) if T_of(n) ** 2 + (1 << (n - 5)) >= 1 << (n + 1)]
    check("V  T^2 + 2^(n-5) < 2^(n+1) (bound for the right ends), n = 6..400", not bad8, f"violations {bad8}")
    bad9 = [n for n in range(0, 401) if T_of(n) ** 2 >= 1 << (n + 2)]
    check("V  T^2 < 2^(n+2) (bound for the squares in A1), n = 0..400", not bad9, f"violations {bad9}")
    bad10 = [n for n in range(1, 100001) if (n // 2 + 1) * 4 < 1 << L(n)]
    check("V  bit-size view: floor(n/2) + 1 >= 2^(L(n)-2), n = 1..100000", not bad10, f"violations {bad10[:10]}")


# ------------------------------------------------------------------------------------------------------------- W
class _Instrument(ast.NodeTransformer):
    """Wrap every expression that can carry an integer in a call _rec_(...) that records it and returns it."""

    @staticmethod
    def _wrap(node):
        return ast.Call(func=ast.Name(id="_rec_", ctx=ast.Load()), args=[node], keywords=[])

    def visit_Name(self, node):
        return self._wrap(node) if isinstance(node.ctx, ast.Load) else node

    def visit_Constant(self, node):
        return self._wrap(node) if type(node.value) is int else node

    def _wrap_after_children(self, node):
        self.generic_visit(node)
        return self._wrap(node)

    visit_BinOp = visit_UnaryOp = visit_Call = _wrap_after_children

    def visit_Subscript(self, node):
        self.generic_visit(node)
        return self._wrap(node) if isinstance(node.ctx, ast.Load) else node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if isinstance(node.target, ast.Name):
            return [node, ast.Expr(self._wrap(ast.Name(id=node.target.id, ctx=ast.Load())))]
        return node


def traced_module(path: Path):
    """Execute an instrumented copy of the module at `path`; return (namespace, box), box[0] = largest |int| seen."""
    box = [0]

    def _rec_(value):
        if type(value) is int:                       # bool excluded
            a = -value if value < 0 else value
            if a > box[0]:
                box[0] = a
        return value

    tree = _Instrument().visit(ast.parse(path.read_text(encoding="utf-8")))
    ast.fix_missing_locations(tree)
    ns = {"_rec_": _rec_, "__name__": "traced_" + path.stem}
    exec(compile(tree, str(path), "exec"), ns)
    return ns, box


def section_w() -> None:
    impl = ENTRY / "implementations"
    plan = (("A1", "enumeration.py", "count_by_enumeration", A1, 16),
            ("A2", "interval_sweep.py", "count_by_interval_sweep", A2, 34),
            ("A3", "groups.py", "count_by_groups", G.count_by_groups, 400))
    for name, fname, func, original, nmax in plan:
        ns, box = traced_module(impl / fname)
        fn = ns[func]
        bad, same, worst0, seen_2n, margin = [], True, None, True, -10 ** 9
        for n in range(0, nmax + 1):
            box[0] = 0
            out = fn(n)
            same &= out == original(n)
            if n == 0:
                worst0 = box[0]
                continue
            if box[0] >= 1 << (n + 2):
                bad.append(n)
            seen_2n &= box[0] >= 1 << n                 # control: the tracer sees 2^n, which every algorithm forms
            margin = max(margin, box[0].bit_length() - (n + 2))
        check(f"W  {name} ({fname}) instrumented: every integer value of every expression is below 2^(n+2) in "
              f"absolute value for n = 1..{nmax}, at most 5 for n = 0; same results as the original", not bad
              and worst0 <= 5 and same and seen_2n,
              f"violations {bad[:10]}, max over n of (bit length of the largest value) - (n + 2) = {margin}, "
              f"largest |value| at n = 0: {worst0}, control (largest value >= 2^n for every n >= 1): {seen_2n}")


# ------------------------------------------------------------------------------------------------------------- T
README_TABLE = {6: 3, 7: 8, 8: 21, 9: 51, 10: 127, 11: 257, 12: 565, 13: 1104, 14: 2378, 15: 4578, 16: 9748,
                20: 158800, 24: 2552128, 29: 77512574, 32: 654251008, 40: 167502757888}
TEST_VALUES = {5: 0, 26: 10216064, 39: 79393042353}


def section_t() -> None:
    wanted = {**README_TABLE, **TEST_VALUES}
    bad = []
    for n, val in sorted(wanted.items()):
        b, c = A2(n)[0], G.count_by_groups(n)[0]
        if not b == c == val:
            bad.append((n, b, c, val))
    check(f"T  README table and test values: interval sweep = groups = stated value (n = 5..16, 20, 24, 26, 29, 32, "
          f"39, 40; {len(wanted)} values)", not bad, f"mismatches {bad}")
    bad0 = [n for n in range(0, 6) if A1(n)[0] or A2(n)[0] or G.count_by_groups(n)[0]]
    check("T  |S_n| = 0 for n = 0..5 (all three algorithms)", not bad0, f"violations {bad0}")
    check("T  n = 200: A3 processes 101 = 200/2 + 1 groups", G.count_by_groups(200)[1] == 101)


SECTIONS = {"A": section_a, "B": section_b, "C": section_c, "S": section_s, "N": section_n, "V": section_v,
            "W": section_w, "T": section_t}


def main(argv: list[str]) -> int:
    t = time.perf_counter()
    wanted = [s.upper() for s in argv] or list(SECTIONS)
    for s in wanted:
        SECTIONS[s]()
    print(f"elapsed {time.perf_counter() - t:.1f} s")
    if FAILURES:
        print("FAILED: " + "; ".join(FAILURES))
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
