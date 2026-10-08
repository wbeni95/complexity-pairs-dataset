#!/usr/bin/env python3
"""Verifier for theorems/binary-powering-exactness-in-magmas (see README.md in this folder).

Exhaustive and seeded checks of the theorems on small magmas; the proofs are in the README. Computations are
evidence, not proof. Standard library only, deterministic, offline; a few seconds on a laptop.

Objects (as in the README). A magma is a table T on {0..m-1}, x*y = T[x][y]. Left powers p_1 = x,
p_(k+1) = p_k * x; mu, lambda = the smallest preperiod and period of (p_k).
  LTR:   B(1) = x, B(2a) = B(a)*B(a), B(2a+1) = B(2a)*x.
  RTL-L / RTL-R: s_0 = x, s_(k+1) = s_k*s_k; over the bits of e from the lowest: at the first set bit r = s_k, at
         every later set bit r = r*s_k (RTL-L) or r = s_k*r (RTL-R).
  SQ(x): p_a*p_a = p_2a for all a >= 1.   CL(x): p_a*p_(2^k) = p_(a+2^k) for k >= 0, 1 <= a <= 2^k.
  CR(x): p_(2^k)*p_a = p_(a+2^k), same range.   PA(x): p_a*p_b = p_(a+b) for all a, b >= 1.

Checks:
  Theorems 1 and 3 (LTR), pointwise exhaustive: LTR and SQ at x read only column x and the diagonal (2m - 1
     cells), so enumerating these cells with x = 0 covers every magma of order m and every x. Orders m = 2..5
     (8 + 243 + 16 384 + 1 953 125 assignments). For E <= 4m + 4: the first exponent
     e with B(e) != p_e is exactly 2a*, where a* is the first a with p_a*p_a != p_2a (Theorem 1(b)), and
     a* <= mu + lambda - 1 <= m whenever some a <= 2m + 2 fails (Theorem 3).
  Tightness of Theorem 3: the magma of the README for m = 2..12.
  Theorem 2 (RTL), finite form (b): [RTL-L(e) = p_e for all e <= 2^(K+1)] == [CL(k, a) for all k <= K,
     1 <= a <= 2^k] for K = 0..5, mirror for RTL-R: all tables of order 2 and 3 and every x, and 1500 seeded random
     tables each of order 4 and 5 (RTL values by the recursion of the proof of Theorem 2, which a further check
     compares with the literal bit loop on all order-2 tables and every 7th order-3 table, e <= 64). The infinite
     conditions, decided by Proposition 4 (finite check), agree with RTL on 4 seeded random exponents below 2^120
     per (table, x) on a sample, and with simulation up to the bound.
  Proposition 5: the 8 per-element witnesses of the README (conditions and simulation of the three
     algorithms), the witness with SQ, CL, CR at every element but not power-associative, and the witness that is
     power-associative but not associative.
  Remark 5: the number of products made by the literal LTR and RTL loops, for all e <= 4096.
Exit code 0 only if every check passes.
Usage (from the repository root): python theorems/binary-powering-exactness-in-magmas/verify.py
"""
import argparse
import itertools
import random
import sys
import time

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ basics
def powers_from_column(col, x, upto):
    """p[1..upto] with p_(k+1) = col[p_k], col[v] = v * x."""
    p = [None, x]
    for _ in range(upto - 1):
        p.append(col[p[-1]])
    return p


def preperiod_period(col, x):
    """Smallest mu, lambda with p_(k+lambda) = p_k for all k >= mu."""
    first, v, k = {}, x, 1
    while v not in first:
        first[v] = k
        v = col[v]
        k += 1
    mu = first[v]
    return mu, k - mu


def power(p, mu, lam, e):
    return p[e] if e < len(p) else p[mu + (e - mu) % lam]


def rtl(T, x, e, left):
    """RTL-L (left=True) or RTL-R as a bit loop; used for values only. It squares s after every bit, including
    the highest one, so it makes one product more than the count of Remark 5 (s_(K+1) is never used)."""
    s, r = x, None
    while e:
        if e & 1:
            r = s if r is None else (T[r][s] if left else T[s][r])
        s = T[s][s]
        e >>= 1
    return r


def conditions(T, x):
    """SQ, CL, CR, PA at x, decided exactly with the finite bounds of Theorem 3 and Proposition 4."""
    m = len(T)
    col = [T[v][x] for v in range(m)]
    mu, lam = preperiod_period(col, x)
    h = mu + lam - 1
    p = powers_from_column(col, x, h + 2)
    pw = lambda e: power(p, mu, lam, e)  # noqa: E731
    sq = all(T[pw(a)][pw(a)] == pw(2 * a) for a in range(1, h + 1))
    K1 = (h - 1).bit_length()  # ceil(log2(h)) for h >= 1
    kmax = K1 + lam - 1
    cl = all(T[pw(a)][pw(2 ** k)] == pw(a + 2 ** k) for k in range(kmax + 1) for a in range(1, min(2 ** k, h) + 1))
    cr = all(T[pw(2 ** k)][pw(a)] == pw(a + 2 ** k) for k in range(kmax + 1) for a in range(1, min(2 ** k, h) + 1))
    pa = all(T[pw(a)][pw(b)] == pw(a + b) for a in range(1, h + 1) for b in range(1, h + 1))
    return sq, cl, cr, pa


def associative(T):
    r = range(len(T))
    return all(T[T[a][b]][c] == T[a][T[b][c]] for a in r for b in r for c in r)


# --------------------------------------------------------------------------------------------- LTR (Theorems 1 and 3)
def part_ltr(orders):
    for m in orders:
        t0 = time.time()
        E = 4 * m + 4
        half = E // 2
        n_assign = n_sq = n_bad = 0
        hist = {}
        for col in itertools.product(range(m), repeat=m):
            p = powers_from_column(col, 0, E)
            mu, lam = preperiod_period(col, 0)
            bound = mu + lam - 1
            if bound > m:
                n_bad += 1
            p2 = [None] + [p[2 * a] for a in range(1, half + 1)]
            for rest in itertools.product(range(m), repeat=m - 1):
                diag = (col[0],) + rest
                n_assign += 1
                a_star = 0
                for a in range(1, half + 1):
                    if diag[p[a]] != p2[a]:
                        a_star = a
                        break
                # simulate LTR up to E, first wrong exponent
                B = [None, 0]
                e_wrong = 0
                for e in range(2, E + 1):
                    v = diag[B[e >> 1]] if e % 2 == 0 else col[B[e - 1]]
                    B.append(v)
                    if v != p[e]:
                        e_wrong = e
                        break
                if a_star == 0:
                    n_sq += 1
                    if e_wrong:
                        n_bad += 1
                else:
                    hist[a_star] = hist.get(a_star, 0) + 1
                    if e_wrong != 2 * a_star or a_star > bound:
                        n_bad += 1
        check(f"Theorems 1(b), 3, m = {m}: first wrong LTR exponent = 2a* and a* <= mu + lambda - 1 <= m "
              f"(all e <= {E})",
              n_bad == 0, f"{n_assign} assignments, SQ up to {half} on {n_sq}, first failing a: "
              f"{dict(sorted(hist.items()))}, {time.time() - t0:.1f} s")


# --------------------------------------------------------------------------------------------- tightness of Theorem 3
def tight_magma(m):
    T = [[0] * m for _ in range(m)]
    for k in range(m):
        T[k][0] = min(k + 1, m - 1)
    for a in range(1, m):
        T[a - 1][a - 1] = min(2 * a, m) - 1
    T[m - 1][m - 1] = 0
    return T


def part_tightness():
    bad = []
    for m in range(2, 13):
        T = tight_magma(m)
        col = [T[v][0] for v in range(m)]
        p = powers_from_column(col, 0, 4 * m)
        mu, lam = preperiod_period(col, 0)
        sq_fail = [a for a in range(1, 2 * m) if T[p[a]][p[a]] != p[2 * a]]
        B = [None, 0]
        for e in range(2, 4 * m):
            B.append(T[B[e // 2]][B[e // 2]] if e % 2 == 0 else T[B[e - 1]][0])
        e_wrong = next(e for e in range(1, 4 * m) if B[e] != p[e])
        ok = (all(p[k] == min(k, m) - 1 for k in range(1, 4 * m)) and (mu, lam) == (m, 1) and sq_fail[0] == m
              and e_wrong == 2 * m)
        if not ok:
            bad.append(m)
    check("Theorem 3 tightness: p_k = min(k, m) - 1, mu = m, lambda = 1, SQ first fails at a = m, LTR first wrong at "
          "e = 2m, for m = 2..12", not bad, f"failures {bad}")


# ------------------------------------------------------------------------------------- RTL (Theorem 2, Proposition 4)
def rtl_finite_agree(T, x, Kmax=5):
    """Compare the first K at which RTL fails (e <= 2^(K+1)) with the first k at which CL / CR fails."""
    m = len(T)
    col = [T[v][x] for v in range(m)]
    N = 2 ** (Kmax + 1)
    p = powers_from_column(col, x, 2 * N + 2)
    ok = True
    for left in (True, False):
        # RTL values for all e <= N by the recursion RTL(2^k + a) = RTL(a)*s_k (or s_k*RTL(a)), RTL(2^k) = s_k
        s = [x]
        for _ in range(Kmax + 1):
            s.append(T[s[-1]][s[-1]])
        R = [None] * (N + 1)
        for e in range(1, N + 1):
            k = e.bit_length() - 1
            a = e - (1 << k)
            R[e] = s[k] if a == 0 else (T[R[a]][s[k]] if left else T[s[k]][R[a]])
        k_sim = next((K for K in range(Kmax + 1) if any(R[e] != p[e] for e in range(1, 2 ** (K + 1) + 1))), None)
        if left:
            fails = lambda k, a: T[p[a]][p[2 ** k]] != p[a + 2 ** k]  # noqa: E731
        else:
            fails = lambda k, a: T[p[2 ** k]][p[a]] != p[a + 2 ** k]  # noqa: E731
        k_cond = next((k for k in range(Kmax + 1) if any(fails(k, a) for a in range(1, 2 ** k + 1))), None)
        ok &= (k_sim == k_cond)
    return ok


def all_tables(m):
    for cells in itertools.product(range(m), repeat=m * m):
        yield [list(cells[i * m:(i + 1) * m]) for i in range(m)]


def part_rtl(rng):
    t0 = time.time()
    total = agree = 0
    for m in (2, 3):
        for T in all_tables(m):
            for x in range(m):
                total += 1
                agree += rtl_finite_agree(T, x)
    for m in (4, 5):
        for i in range(1500):
            T = [[rng.randrange(m) for _ in range(m)] for _ in range(m)]
            if i % 2:  # make the diagonal agree with left powers of x = 0 more often (more SQ/CL/CR cases)
                col = [T[v][0] for v in range(m)]
                p = powers_from_column(col, 0, 2 * m + 2)
                for a in range(1, m + 1):
                    if rng.random() < 0.8:
                        T[p[a]][p[a]] = p[2 * a]
            for x in range(m):
                total += 1
                agree += rtl_finite_agree(T, x)
    check("Theorem 2(b), finite RTL theorem (K = 0..5, both variants): all tables of order 2, 3 and every x; 1500 "
          "random tables each of order 4, 5", agree == total, f"{agree}/{total} agree, {time.time() - t0:.1f} s")

    # the check above computes RTL by the recursion RTL(2^k) = s_k, RTL(2^k + a) = RTL(a)*s_k (or s_k*RTL(a)) of
    # the proof of Theorem 2; here the recursion is compared with the literal bit loop rtl()
    t0 = time.time()
    n_cmp = n_diff = 0
    sample = [T for T in all_tables(2)] + [T for i, T in enumerate(all_tables(3)) if i % 7 == 0]
    for T in sample:
        for x in range(len(T)):
            s = [x]
            for _ in range(6):
                s.append(T[s[-1]][s[-1]])
            for left in (True, False):
                R = [None] * 65
                for e in range(1, 65):
                    k = e.bit_length() - 1
                    a = e - (1 << k)
                    R[e] = s[k] if a == 0 else (T[R[a]][s[k]] if left else T[s[k]][R[a]])
                    n_cmp += 1
                    n_diff += R[e] != rtl(T, x, e, left)
    check("Theorem 2: the recursion used above equals the literal RTL bit loop (both variants, all e <= 64) on all "
          "tables of order 2 and every 7th table of order 3, every x", n_diff == 0,
          f"{n_cmp} (table, x, variant, e) comparisons, {n_diff} differences, {time.time() - t0:.1f} s")

    # infinite conditions (Proposition 4) against RTL at large exponents, on a sample
    t0 = time.time()
    bad = n = 0
    tabs = list(all_tables(3))
    for idx in range(0, len(tabs), 7):
        T = tabs[idx]
        for x in range(3):
            sq, cl, cr, pa = conditions(T, x)
            col = [T[v][x] for v in range(3)]
            mu, lam = preperiod_period(col, x)
            p = powers_from_column(col, x, 70)
            small_l = all(rtl(T, x, e, True) == p[e] for e in range(1, 65))
            small_r = all(rtl(T, x, e, False) == p[e] for e in range(1, 65))
            big = [rng.randrange(1, 2 ** 120) for _ in range(4)]
            big_l = all(rtl(T, x, e, True) == power(p, mu, lam, e) for e in big)
            big_r = all(rtl(T, x, e, False) == power(p, mu, lam, e) for e in big)
            n += 1
            # CL decided by Proposition 4 must equal correctness of RTL-L on e <= 64 (the bound is <= 16 here),
            # and if CL holds, RTL-L must also be correct at the random large exponents
            if cl != small_l or cr != small_r or (cl and not big_l) or (cr and not big_r):
                bad += 1
    check("Proposition 4 (finite check of CL, CR) agrees with RTL simulation (e <= 64 and 4 random e < 2^120) "
          "on every 7th table of order 3, every x", bad == 0, f"{n} (table, x), {bad} disagreements, "
          f"{time.time() - t0:.1f} s")


# ------------------------------------------------------------------------------------------ relations (Proposition 5)
def part_relations():
    t0 = time.time()
    # per-element witnesses of the README: (SQ(x), CL(x), CR(x)) -> (table as rows T[a][b], x)
    witnesses = {
        (0, 0, 0): ([[1, 0], [0, 0]], 0),
        (0, 0, 1): ([[0, 0, 1], [0, 1, 0], [0, 1, 1]], 2),
        (0, 1, 0): ([[0, 0, 1], [1, 1, 0], [0, 0, 1]], 2),
        (0, 1, 1): ([[0, 0, 1], [0, 1, 0], [0, 0, 1]], 2),
        (1, 0, 0): ([[0, 0, 1], [0, 0, 0], [0, 0, 0]], 2),
        (1, 0, 1): ([[0, 0], [1, 0]], 1),
        (1, 1, 0): ([[0, 0, 1], [0, 2, 0], [0, 0, 0]], 1),
        (1, 1, 1): ([[0, 0], [0, 0]], 0),
    }
    bad = []
    for want, (T, x) in witnesses.items():
        sq, cl, cr, _ = conditions(T, x)
        col = [T[v][x] for v in range(len(T))]
        p = powers_from_column(col, x, 70)
        B = [None, x]
        for e in range(2, 65):
            B.append(T[B[e // 2]][B[e // 2]] if e % 2 == 0 else T[B[e - 1]][x])
        sim = (int(all(B[e] == p[e] for e in range(1, 65))),
               int(all(rtl(T, x, e, True) == p[e] for e in range(1, 65))),
               int(all(rtl(T, x, e, False) == p[e] for e in range(1, 65))))
        if (int(sq), int(cl), int(cr)) != want or sim != want:
            bad.append(want)
    check("Proposition 5: the 8 per-element witnesses: (SQ, CL, CR) at x as stated, and LTR / RTL-L / RTL-R exact "
          "on e <= 64 exactly when SQ / CL / CR holds", not bad, f"failures {bad}")
    T = [[0, 1, 1], [1, 0, 0], [1, 1, 0]]
    cs = [conditions(T, xx) for xx in range(3)]
    check("Proposition 5 witness: SQ, CL, CR hold at every x, PA fails at some x (order 3)",
          all(c[0] and c[1] and c[2] for c in cs) and not all(c[3] for c in cs))
    T = [[0, 0, 0], [0, 0, 0], [0, 1, 0]]
    check("Proposition 5 witness: PA at every x without associativity (order 3)",
          all(conditions(T, xx)[3] for xx in range(3)) and not associative(T))
    T = [[0, 0], [1, 0]]
    check("Scope example: in [[0,0],[1,0]] with x = 1, x*(x*x) = 1 and (x*x)*x = 0",
          T[1][T[1][1]] == 1 and T[T[1][1]][1] == 0)
    print(f"   (part D: {time.time() - t0:.1f} s)")


# ------------------------------------------------------------------------------------------ product counts (Remark 5)
def part_counts(emax=4096):
    """Remark 5: the literal loops make floor(log2 e) + popcount(e) - 1 products (at most 2 floor(log2 e)), and the
    LTR loop returns B(e) of the recursive definition. Counted on one fixed magma (the counts do not depend on it)."""
    T = [[0, 0, 1], [1, 0, 0], [2, 1, 0]]  # an arbitrary order-3 table; only the number of products is counted
    x = 2
    B = [None, x]
    for e in range(2, emax + 1):
        B.append(T[B[e // 2]][B[e // 2]] if e % 2 == 0 else T[B[e - 1]][x])
    bad = 0
    for e in range(1, emax + 1):
        want = (e.bit_length() - 1) + bin(e).count("1") - 1
        # LTR loop: r = x; for each bit after the leading one: square, then multiply by x if the bit is 1
        r, cnt = x, 0
        for bit in bin(e)[3:]:
            r, cnt = T[r][r], cnt + 1
            if bit == "1":
                r, cnt = T[r][x], cnt + 1
        bad += cnt != want or r != B[e] or want > 2 * (e.bit_length() - 1)
        # RTL loop (both variants): s_1, ..., s_K with K = floor(log2 e), and one product per later set bit
        for left in (True, False):
            s, rr, cnt, ee = x, None, 0, e
            while ee:
                if ee & 1:
                    if rr is None:
                        rr = s
                    else:
                        rr, cnt = (T[rr][s] if left else T[s][rr]), cnt + 1
                ee >>= 1
                if ee:
                    s, cnt = T[s][s], cnt + 1
            bad += cnt != want or rr != rtl(T, x, e, left)
    check(f"Remark 5: LTR and both RTL loops make exactly floor(log2 e) + popcount(e) - 1 <= 2 floor(log2 e) "
          f"products, and the LTR loop returns B(e) (all e <= {emax})", bad == 0, f"{3 * emax} runs, {bad} failures")


# ------------------------------------------------------------------------------------------------ main
def main():
    argparse.ArgumentParser(description=__doc__.split("\n")[0]).parse_args()
    t0 = time.time()
    rng = random.Random("binary-powering-exactness-in-magmas")
    part_ltr((2, 3, 4, 5))
    part_tightness()
    part_rtl(rng)
    part_relations()
    part_counts()
    print(f"total {time.time() - t0:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
