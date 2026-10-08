#!/usr/bin/env python3
"""Verifier for theorems/power-plus-offset-four-candidates (see README.md in this folder).

Deterministic exhaustive and seeded checks of the theorems and the facts their proofs use; computations are
evidence, the proofs are in the README. Standard library only; no network; well under a minute on a laptop. Exit code
0 only if every check passes.

Objects (as in the README). L(v) = number of binary digits of |v|, L(0) = 1. For d >= 2 and k >= 0:
f_k(X) = L(X) + L(C) + [C < 0] with C = k - X^d; r = iroot_d(k) = largest r with r^d <= k.
S_n = {0 <= k < 2^n : min over X of f_k(X) <= n - 4}; v = n - 4, B = 2^n - 1, T = iroot_d(B) + 1.
For a root X with w = v - L(X) >= 1: J_X = [X^d - m, X^d + 2^w - 1], m = 2^(w-1) - 1 (w >= 2) or 0 (w = 1).

Checks:
  F  Corollary 2: the example d = 3, k = 16 (hand values, unique minimiser X = 1); for d = 3..8 and every k < 2^KA,
     every k at which the three candidates {0, r, r+1} miss the minimum is a power of two >= 2, with X = 1 the only
     minimiser (all roots in the window of Lemma 0 compared); the values k = 2^(d+1), d = 3..400 (r = 2, the four
     costs, and X = 1 the only minimiser in the window of Lemma 0).
  A  Theorem 1 (four candidates {0, 1, r, r+1}) against a brute force over all roots in the window X^d < k + 2^L(k)
     (Lemma 0), every k < 2^KA, d = 3..8; Lemma 0 itself; the case-(iii) inequality (u-1)^d + 2u^(d-1) - 1 < u^d for
     u = 2^a, a = 2..40, d = 3..60 (and equality u^2 for d = 2); f_k(1) < f_k(0) iff k = 2^p with p >= 1.
  B  Theorem 3 (one interval per root): sorted union of the clipped intervals = brute-force count, d = 3..8,
     n = 0..KA; the one-pass sweep in X order (Theorem 3 with Lemma C) = sorted union, d = 3..8, n = 0..40.
  C  Theorem 4 (algorithm A3_d) = brute-force count for d = 3..8, n = 0..KA; = sorted union (which uses neither the
     monotone left ends nor the grouping): d = 2 for n <= 40, d = 3 for n <= 57, d = 4..7 for n <= 76; d = 2
     reproduces the values of the X^2 + C pair entry.
  S  structure used by A3_d: left ends strictly increasing over all roots with w >= 1, and the component-starting
     roots of every group form a suffix (d = 3..5, n = 6..36); D(X) = X^d - (X-1)^d strictly increasing (X = 1..2000,
     d = 2..12); L(x_top) <= floor(n/d) + 2 (d = 2..11, n = 6..200).
  O  cost facts used by the operation count: integer d-th roots by bisection are exact (seeded q < 2^700, d = 2..40)
     and take exactly ceil(L(q)/d) steps (equality checked for every q); a d-th power takes
     floor(log2 d) + popcount(d) - 1 <= 2 floor(log2 d) multiplications; inside A3_d every product, root argument
     (B, B + m, H + 1 + m), run of isolated intervals, |U| and H stays below 2^(n+2), every group makes at most l
     D-evaluations, the number of groups is at most floor(n/d) + 2 (d = 3, 4, 5; n = 64, 256, 1024, 2048); the
     inequalities ceil((n + 2)/d) <= floor(n/d) + 2 (d = 2..200, n = 0..2000) and floor(n/d) + 2 <= 3n/d
     (d = 2..200, n = d..2000) used in the cost proof.
  W  word sizes of Theorem 4: an instrumented copy of power, power_le, iroot and a3 (this file's own source,
     rewritten so that every integer value an expression evaluates to is recorded, except reads of the exponent d)
     returns the same results, and every recorded value is below 2^(n+2) in absolute value for n = 1..200 and at most
     5 for n = 0 (d = 2..8).
Usage (from the repository root): python theorems/power-plus-offset-four-candidates/verify.py
"""
import ast
import random
import sys
import time
from pathlib import Path

KA = 18
FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ core objects
def L(v):
    v = -v if v < 0 else v
    return v.bit_length() if v else 1


def f(k, x, d):
    c = k - x ** d
    return L(x) + (L(c) if c >= 0 else L(c) + 1)


def power(x, d, st=None):
    """x^d by left-to-right binary exponentiation, counting multiplications and the largest product."""
    if x <= 1:
        return x
    acc = x
    for bit in bin(d)[3:]:
        acc = acc * acc
        if st is not None:
            st["mults"] = st.get("mults", 0) + 1
            st["max_bits"] = max(st.get("max_bits", 0), acc.bit_length())
        if bit == "1":
            acc = acc * x
            if st is not None:
                st["mults"] = st.get("mults", 0) + 1
                st["max_bits"] = max(st.get("max_bits", 0), acc.bit_length())
    return acc


def power_le(x, d, q, st=None):
    """True iff x^d <= q (q >= 0), computed without any product above q: before a*b, test a > q // b."""
    if x <= 1:
        return x <= q
    acc, mults, result = x, 0, x <= q
    if result:
        for bit in bin(d)[3:]:
            if acc > q // acc:
                result = False
                break
            acc = acc * acc
            mults += 1
            if bit == "1":
                if acc > q // x:
                    result = False
                    break
                acc = acc * x
                mults += 1
    if st is not None:
        st["mults"] = st.get("mults", 0) + mults
        st["max_mults_per_power"] = max(st.get("max_mults_per_power", 0), mults)
        st["max_bits"] = max(st.get("max_bits", 0), acc.bit_length())
    return result


def iroot(q, d, st=None):
    """Largest x >= 0 with x^d <= q, by bisection on [0, 2^ceil(L(q)/d)]: exactly ceil(L(q)/d) steps."""
    if q < 1:
        return 0
    lo, hi = 0, 1 << -(-q.bit_length() // d)           # hi^d >= 2^L(q) > q
    steps = 0
    while hi - lo > 1:
        mid = (lo + hi) // 2
        steps += 1
        if power_le(mid, d, q, st):
            lo = mid
        else:
            hi = mid
    if st is not None:
        excess = steps - (-(-q.bit_length() // d))
        st["root_steps"] = st.get("root_steps", 0) + steps
        st["roots"] = st.get("roots", 0) + 1
        st["max_root_step_excess"] = max(st.get("max_root_step_excess", -99), excess)
        st["min_root_step_excess"] = min(st.get("min_root_step_excess", 99), excess)
        st["max_bits"] = max(st.get("max_bits", 0), q.bit_length())       # the root argument itself
    return lo


def interval(x, v, d):
    w = v - L(x)
    if w < 1:
        return None
    m = (1 << (w - 1)) - 1 if w >= 2 else 0
    p = x ** d
    return p - m, p + (1 << w) - 1


def brute_minima(d, K):
    """min over all roots of f_k, for every k < 2^K, over the window X^d < k + 2^L(k) (Lemma 0)."""
    out = []
    for k in range(1 << K):
        bound = k + (1 << L(k))
        best = f(k, 0, d)
        x = 1
        while x ** d < bound:
            c = f(k, x, d)
            if c < best:
                best = c
            x += 1
        out.append(best)
    return out


def counts_from_minima(mins, n):
    return sum(1 for k in range(1 << n) if mins[k] <= n - 4)


def sorted_union(n, d):
    B = (1 << n) - 1
    v = n - 4
    ivs = []
    for x in range(iroot(B, d) + 2):
        iv = interval(x, v, d)
        if iv is None:
            continue
        lo, hi = max(0, iv[0]), min(iv[1], B)
        if lo <= hi:
            ivs.append((lo, hi))
    ivs.sort()
    total, a, b = 0, None, None
    for lo, hi in ivs:
        if a is None:
            a, b = lo, hi
        elif lo <= b + 1:
            b = max(b, hi)
        else:
            total += b - a + 1
            a, b = lo, hi
    if a is not None:
        total += b - a + 1
    return total


def a3(n, d, st=None):
    """Algorithm A3_d of the README (Theorem 4): |S_n| from one O(1)-step pass per group of equal bit length."""
    v = n - 4
    B = (1 << n) - 1
    T = iroot(B, d, st) + 1
    U, H, m0, groups, x_top = 0, None, 0, 0, None
    l = 1
    while True:
        gs = 0 if l == 1 else 1 << (l - 1)
        w = v - l
        if w < 1 or gs > T:
            break
        m = (1 << (w - 1)) - 1 if w >= 2 else 0
        s = (1 << w) - 1
        ge = min((1 << l) - 1, T, iroot(B + m, d, st))       # last root of the group with left end <= B
        if ge < gs:
            break
        groups += 1
        x_top = ge
        if l == 1:
            m0 = m
        p = power(gs, d, st)
        lo, hi = p - m, p + s
        if H is None:
            U, H = hi - lo + 1, hi
        elif lo > H + 1:
            U, H = U + hi - lo + 1, hi
        elif hi > H:
            U, H = U + hi - H, hi
        if ge > gs:
            t_a = iroot(H + 1 + m, d, st) + 1               # X^d - m > H + 1
            K = s + 1 + m                                   # D(X) > 2^w + m
            a, b = gs + 1, ge + 1
            evals = 0
            while a < b:                                    # smallest X in (gs, ge] with D(X) > K, else ge + 1
                mid = (a + b) // 2
                evals += 1
                if power(mid, d, st) - power(mid - 1, d, st) > K:
                    b = mid
                else:
                    a = mid + 1
            if st is not None:
                st["d_evals"] = st.get("d_evals", 0) + evals
                st["max_d_evals_over_l"] = max(st.get("max_d_evals_over_l", 0), evals / l)
            x_s = max(gs + 1, t_a, a)
            if x_s - 1 >= gs + 1:
                h = power(min(x_s - 1, ge), d, st) + s
                if h > H:
                    U, H = U + h - H, h
            if x_s <= ge:
                run = (ge - x_s + 1) * (s + m + 1)
                if st is not None:
                    st["max_bits"] = max(st.get("max_bits", 0), run.bit_length())
                U += run
                H = power(ge, d, st) + s
        l += 1
    if st is not None:
        st["groups"] = groups
        st["x_top"] = x_top
        st["max_bits"] = max(st.get("max_bits", 0), (U + 1).bit_length(), (H or 0).bit_length())
    if H is None:
        return 0
    return U - m0 - max(0, H - B)


# ------------------------------------------------------------------------------------------------ sections
MINIMA = {}
FOUR_MISMATCHES = {}


def section_f_a():
    vals = [f(16, x, 3) for x in range(5)]
    check("F  d = 3, k = 16: f(0..4) = 6, 5, 6, 7, 10 and r = 2", vals == [6, 5, 6, 7, 10] and iroot(16, 3) == 2,
          str(vals))
    t = time.perf_counter()
    for d in range(3, 9):
        MINIMA[d] = brute_minima(d, KA)
    print(f"     (brute-force minima for d = 3..8, k < 2^{KA}: {time.perf_counter() - t:.1f} s)")
    check("F  d = 3, k = 16: the minimum over all roots is 5, attained only at X = 1",
          MINIMA[3][16] == 5 and [x for x in range(4) if f(16, x, 3) == 5] == [1])
    for d in range(3, 9):
        mins = MINIMA[d]
        fails, bad4, r = [], 0, 0
        for k in range(1 << KA):
            while (r + 1) ** d <= k:                        # r = iroot_d(k), kept incrementally
                r += 1
            three = min(f(k, 0, d), f(k, r, d), f(k, r + 1, d))
            if three != mins[k]:
                fails.append(k)
            if min(three, f(k, 1, d)) != mins[k]:
                bad4 += 1
        FOUR_MISMATCHES[d] = bad4
        pow2 = all(k >= 2 and k & (k - 1) == 0 for k in fails)
        unique = all([x for x in range(iroot(k + (1 << L(k)) - 1, d) + 1) if f(k, x, d) == mins[k]] == [1]
                     for k in fails)
        check(f"F  Corollary 2, d = {d}: every k < 2^{KA} where {{0, r, r+1}} miss the minimum is a power of two >= 2 "
              f"with X = 1 the only minimiser ({1 << KA} values of k; {len(fails)} such k, each checked)",
              pow2 and unique and len(fails) > 0)
    bad = []
    for d in range(3, 401):
        k = 1 << (d + 1)
        window = range(iroot(k + (1 << L(k)) - 1, d) + 1)            # Lemma 0: every minimiser lies in it
        fx = {x: f(k, x, d) for x in window}
        ok = (iroot(k, d) == 2 and f(k, 0, d) == d + 3 and f(k, 1, d) == d + 2 and f(k, 2, d) == d + 3
              and f(k, 3, d) >= d + 3 and 3 ** d - (1 << (d + 1)) >= 1 << (d - 1)
              and [x for x in window if fx[x] == min(fx.values())] == [1])
        if not ok:
            bad.append(d)
    check("F  Corollary 2, k = 2^(d+1) for every d = 3..400 (398 values): r = 2, f(0) = d + 3, f(1) = d + 2, "
          "f(2) = d + 3, f(3) >= d + 3 (3^d - 2^(d+1) >= 2^(d-1)), and X = 1 is the only minimiser in the window of "
          "Lemma 0", not bad, f"violations {bad[:10]}")
    for d in range(3, 9):
        bad = FOUR_MISMATCHES[d]
        check(f"A  Theorem 1, d = {d}: four candidates = minimum over all roots, every k < 2^{KA} "
              f"({1 << KA} values of k)", bad == 0, f"mismatches {bad}")
    ok = all(f(k, x, d) > f(k, 0, d) for d in range(3, 6) for k in range(1 << 10)
             for x in range(iroot(k + (1 << L(k)) - 1, d) + 1, iroot(k + (1 << L(k)) - 1, d) + 20))
    check("A  Lemma 0: roots with X^d >= k + 2^L(k) cost more than X = 0 (d = 3..5, k < 2^10, 19 roots past the window;"
          " 58368 triples (d, k, X))", ok)
    ok = all((u - 1) ** d + 2 * u ** (d - 1) - 1 < u ** d for a in range(2, 41) for d in range(3, 61) for u in [1 << a])
    eq2 = all((u - 1) ** 2 + 2 * u - 1 == u ** 2 for u in (1 << a for a in range(2, 41)))
    check("A  case (iii): (u-1)^d + 2u^(d-1) - 1 < u^d for u = 2^a, a = 2..40, d = 3..60; equality for d = 2",
          ok and eq2, "2262 pairs")
    ok = all((f(k, 1, 3) < f(k, 0, 3)) == (k >= 2 and k & (k - 1) == 0) for k in range(1 << 16))
    check("A  f_k(1) < f_k(0) iff k = 2^p with p >= 1 (every k < 2^16; f_k(0) and f_k(1) do not depend on d)", ok)


def one_pass_sweep(n, d):
    """The simpler exact method of Theorem 3 with Lemma C: one merge pass over X = 0..T in X order (no sorting)."""
    B = (1 << n) - 1
    v = n - 4
    total, a, b = 0, None, None
    for x in range(iroot(B, d) + 2):
        iv = interval(x, v, d)
        if iv is None:
            continue
        lo, hi = max(0, iv[0]), min(iv[1], B)
        if lo > hi:
            continue
        if a is None:
            a, b = lo, hi
        elif lo <= b + 1:
            b = max(b, hi)
        else:
            total += b - a + 1
            a, b = lo, hi
    if a is not None:
        total += b - a + 1
    return total


def section_b_c():
    bad_b, bad_c = [], []
    for d in range(3, 9):
        for n in range(0, KA + 1):
            bc = counts_from_minima(MINIMA[d], n)
            if bc != sorted_union(n, d):
                bad_b.append((d, n))
            if bc != a3(n, d):
                bad_c.append((d, n))
    check(f"B  Theorem 3: sorted union = brute-force count, d = 3..8, n = 0..{KA} ({6 * (KA + 1)} pairs (d, n))",
          not bad_b, f"mismatches {bad_b}")
    check(f"C  Theorem 4: A3_d = brute-force count, d = 3..8, n = 0..{KA} ({6 * (KA + 1)} pairs (d, n))", not bad_c,
          f"mismatches {bad_c}")
    bad = [(d, n) for d in range(3, 9) for n in range(0, 41) if one_pass_sweep(n, d) != sorted_union(n, d)]
    check("B  Theorem 3 with Lemma C: one merge pass in X order = sorted union, d = 3..8, n = 0..40 (246 pairs)",
          not bad, f"mismatches {bad}")
    t = time.perf_counter()
    bad = []
    for d, nmax in ((2, 40), (3, 57), (4, 76), (5, 76), (6, 76), (7, 76)):
        for n in range(0, nmax + 1):
            if a3(n, d) != sorted_union(n, d):
                bad.append((d, n))
    check("C  Theorem 4: A3_d = sorted union for d = 2 (n <= 40), 3 (n <= 57), 4..7 (n <= 76)", not bad,
          f"mismatches {bad} ({time.perf_counter() - t:.1f} s)")
    known = {13: 1104, 15: 4578, 29: 77512574, 39: 79393042353}
    check("C  d = 2 reproduces the X^2 + C pair entry: |S_13| = 1104, |S_15| = 4578, |S_29| = 77512574, "
          "|S_39| = 79393042353", all(a3(n, 2) == val for n, val in known.items()))


def structure(n, d):
    v = n - 4
    T = iroot((1 << n) - 1, d) + 1
    starts, end, prev, strict = {}, None, None, True
    for x in range(T + 1):
        iv = interval(x, v, d)
        if iv is None:
            continue
        lo, hi = iv
        if prev is not None and lo <= prev:
            strict = False
        prev = lo
        starts[x] = end is None or lo > end + 1
        end = hi if end is None else max(end, hi)
    groups = {}
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
    return strict, bad


def section_s():
    nonstrict, badg = [], 0
    for d in range(3, 6):
        for n in range(6, 37):
            strict, bad = structure(n, d)
            if not strict:
                nonstrict.append((d, n))
            badg += bad
    check("S  left ends strictly increasing over all roots with w >= 1 (d = 3..5, n = 6..36)", not nonstrict)
    check("S  component-starting roots form a suffix of every group (d = 3..5, n = 6..36)", badg == 0,
          f"violating groups {badg}")
    ok = all((x + 1) ** d - 2 * x ** d + (x - 1) ** d > 0 for d in range(2, 13) for x in range(1, 2001))
    check("S  D(X) = X^d - (X-1)^d strictly increasing for X >= 1 (X = 1..2000, d = 2..12)", ok)
    bad = []
    for d in range(2, 12):
        for n in range(6, 201):
            st = {}
            a3(n, d, st)
            if st["x_top"] is not None and L(st["x_top"]) > n // d + 2:
                bad.append((d, n))
    check("S  L(x_top) <= floor(n/d) + 2 (d = 2..11, n = 6..200)", not bad, f"violations {bad[:5]}")


def section_o():
    rng = random.Random("power-plus-offset|iroot")
    bad, not_exact = 0, 0
    for _ in range(4000):
        d = rng.randint(2, 40)
        q = rng.getrandbits(rng.randint(1, 700))
        st = {}
        r = iroot(q, d, st)
        if not (r ** d <= q < (r + 1) ** d):
            bad += 1
        if q >= 1 and not st["min_root_step_excess"] == st["max_root_step_excess"] == 0:
            not_exact += 1
    check("O  integer d-th root by bisection: r^d <= q < (r+1)^d on 4000 seeded (q < 2^700, d = 2..40), "
          "steps = ceil(L(q)/d) exactly for every q", bad == 0 and not_exact == 0,
          f"wrong roots {bad}, step counts differing from ceil(L(q)/d) {not_exact}")
    ok = True
    for d in range(2, 200):
        st = {}
        power(3, d, st)
        ok &= st.get("mults", 0) == (d.bit_length() - 1) + (bin(d).count("1") - 1) <= 2 * (d.bit_length() - 1)
    check("O  a d-th power takes floor(log2 d) + popcount(d) - 1 <= 2 floor(log2 d) multiplications (d = 2..199)", ok)
    allok = True
    for d in (3, 4, 5):
        for n in (64, 256, 1024, 2048):
            st = {}
            a3(n, d, st)
            g = st["groups"]
            ok = (g <= n // d + 2 and st["max_bits"] <= n + 2 and st["max_d_evals_over_l"] <= 1
                  and st["max_root_step_excess"] == st["min_root_step_excess"] == 0
                  and st["max_mults_per_power"] <= 2 * (d.bit_length() - 1))
            allok &= ok
    check("O  inside A3_d: groups <= floor(n/d) + 2, <= l D-evaluations in group l, bisection steps = ceil(L(q)/d) "
          "for every root, products, root arguments, runs, |U| and H below 2^(n+2) (d = 3, 4, 5; n = 64, 256, 1024, "
          "2048)", allok)
    pairs1 = [(d, n) for d in range(2, 201) for n in range(0, 2001)]
    pairs2 = [(d, n) for d in range(2, 201) for n in range(d, 2001)]
    ok1 = all(-(-(n + 2) // d) <= n // d + 2 for d, n in pairs1)
    ok2 = all(d * (n // d + 2) <= 3 * n for d, n in pairs2)
    check(f"O  cost-proof inequalities: ceil((n + 2)/d) <= floor(n/d) + 2 (d = 2..200, n = 0..2000; {len(pairs1)} "
          f"pairs) and floor(n/d) + 2 <= 3n/d (d = 2..200, n = d..2000; {len(pairs2)} pairs)", ok1 and ok2)


class _Instrument(ast.NodeTransformer):
    """Wrap every expression that can carry an integer in _rec_(...), which records it and returns it unchanged.
    Reads of the parameter d (the exponent, an input of the algorithm, not a value it computes) are not recorded."""

    @staticmethod
    def _wrap(node):
        return ast.Call(func=ast.Name(id="_rec_", ctx=ast.Load()), args=[node], keywords=[])

    def visit_Name(self, node):
        return self._wrap(node) if isinstance(node.ctx, ast.Load) and node.id != "d" else node

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


def section_w():
    """Word sizes of Theorem 4: an instrumented copy of power, power_le, iroot and a3 (taken from this file) records
    every integer value of every expression except the exponent d itself; the copy must return the same results."""
    box = [0]

    def _rec_(value):
        if type(value) is int:                       # bool excluded
            a = -value if value < 0 else value
            if a > box[0]:
                box[0] = a
        return value

    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef)
             and node.name in ("power", "power_le", "iroot", "a3")]
    module = _Instrument().visit(ast.Module(body=funcs, type_ignores=[]))
    ast.fix_missing_locations(module)
    ns = {"_rec_": _rec_}
    exec(compile(module, "verify.py (instrumented)", "exec"), ns)
    bad, same, worst0, seen_2n, runs = [], True, 0, True, 0
    for d in range(2, 9):
        for n in range(0, 201):
            box[0] = 0
            same &= ns["a3"](n, d) == a3(n, d)
            runs += 1
            if n == 0:
                worst0 = max(worst0, box[0])
                continue
            if box[0] >= 1 << (n + 2):
                bad.append((d, n))
            seen_2n &= box[0] >= 1 << n               # control: the copy forms 2^n itself
    check(f"W  Theorem 4 sizes: every integer value of every expression of A3_d other than the exponent d is below "
          f"2^(n+2) in absolute value for n = 1..200, at most 5 for n = 0 (d = 2..8; {runs} runs of an instrumented "
          f"copy, same results)",
          not bad and worst0 <= 5 and same and seen_2n,
          f"violations {bad[:5]}, largest |value| at n = 0: {worst0}, control (largest value >= 2^n): {seen_2n}")


def main():
    t = time.perf_counter()
    section_f_a()
    section_b_c()
    section_s()
    section_o()
    section_w()
    print(f"elapsed {time.perf_counter() - t:.1f} s")
    if FAILURES:
        print("FAILED CHECKS:")
        for lab in FAILURES:
            print("  " + lab)
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
