#!/usr/bin/env python3
"""Verifier for theorems/knuth-window-concave-length-weights (see README.md in this folder).

Deterministic exhaustive and seeded checks of the theorem and its lemmas; computations are evidence, the proof is in
the README. Standard library only; no network; well under a minute on a laptop. Exit code 0 only if every check
passes.

Objects (as in the README). For h on {1..N}: C(0) = 0, C(d) = h(d) + min_{0<=t<=d-1} F_d(t), F_d(t) = C(t) + C(d-1-t),
T(d) = argmin F_d. Knuth's run: tau'(0) = -1, W(d) = [max(tau'(d-1), 0), min(tau'(d-1) + 1, d - 1)],
C'(d) = h(d) + min over W(d) of C'(t) + C'(d-1-t), tau'(d) = largest (or smallest) minimiser on W(d).
L(d) = keys in the left subtree of the heap-shaped tree with d keys (array layout 1..d, children 2v and 2v+1),
HR(d) = d - 1 - L(d), k_max = last j >= 2 with h(j) > h(j-1) (1 if h is constant), Q = 2^floor(log2 k_max),
tau*(d) = d - 1 - min(HR(d), Q - 1).

Checks:
  H  heap facts: leaf-split formula, Lemma H (a)-(c).
  L  lemmas B, C (closed form), D, F, G against the dynamic program; steps F1, F2 of Lemma C by direct
     evaluation of the closed forms; A and E on seeded random h.
  T  theorem (largest rule exact, trajectory = tau*, smallest rule exact, smallest = mirror) on
       - all supports of (c_2..c_{N-1}, a), N = 2..16, unit weights and seeded random weights 1..7;
       - all integer h with h(1) = 0 and nonincreasing differences in [0, B] for several (B, N);
       - seeded random h (integer and Fraction values) up to N = 200;
     and tau*_N(d) independent of N >= d.
  X  the 2-D interval run (own implementation, both tie rules) against the full cubic DP, K(i,j) formula.
  B  boundary controls: specific functions outside the hypotheses where the run fails, an exhaustive class table
     (all h on {1..7} with h(1) = 0 and differences in [-2, 2]), the tie-rule example h = min(s,5) - 1 (and that
     C is not convex there), N = 1, 2, the non-monotone largest optimal roots of h = min(s, 2), and the reverse
     quadrangle inequality for concave h.
Usage (from the repository root): python theorems/knuth-window-concave-length-weights/verify.py
"""
import itertools
import random
import sys
import time
from fractions import Fraction

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ core objects
def heap_left(d):
    """Keys in the subtree rooted at array index 2 of the heap with keys at indices 1..d (computed from the layout)."""
    cnt, start, width = 0, 2, 1
    while start <= d:
        cnt += min(d, start + width - 1) - start + 1
        start, width = 2 * start, 2 * width
    return cnt


def HR(d):
    return d - 1 - heap_left(d)


def dp(h, N):
    """C[0..N] and T[1..N] (sets of optimal left sizes) of the unrestricted recurrence; h[1..N], h[0] unused."""
    C = [0] * (N + 1)
    T = [None] * (N + 1)
    for d in range(1, N + 1):
        F = [C[t] + C[d - 1 - t] for t in range(d)]
        m = min(F)
        C[d] = h[d] + m
        T[d] = {t for t in range(d) if F[t] == m}
    return C, T


def knuth_run(h, N, rule="largest", pick=None):
    """Knuth's restricted run. rule: 'largest', 'smallest' or 'custom' (pick(d, minimisers) chooses)."""
    C = [0] * (N + 1)
    tau = [-1] + [None] * N
    for d in range(1, N + 1):
        lo, hi = max(tau[d - 1], 0), min(tau[d - 1] + 1, d - 1)
        F = {t: C[t] + C[d - 1 - t] for t in range(lo, hi + 1)}
        m = min(F.values())
        mins = sorted(t for t in F if F[t] == m)
        tau[d] = mins[-1] if rule == "largest" else mins[0] if rule == "smallest" else pick(d, mins)
        C[d] = h[d] + m
    return C, tau


def k_max(h, N):
    ks = [j for j in range(2, N + 1) if h[j] > h[j - 1]]
    return max(ks) if ks else 1


def tau_star(h, N, d):
    Q = 1 << (k_max(h, N).bit_length() - 1)
    return d - 1 - min(HR(d), Q - 1)


def theorem_holds(h, N):
    """(largest exact, largest trajectory = tau*, smallest exact, smallest trajectory = d - 1 - tau*)."""
    C, _ = dp(h, N)
    CL, tl = knuth_run(h, N, "largest")
    CS, ts = knuth_run(h, N, "smallest")
    star = [None] + [tau_star(h, N, d) for d in range(1, N + 1)]
    return (CL == C, all(tl[d] == star[d] for d in range(1, N + 1)), CS == C,
            all(ts[d] == d - 1 - star[d] for d in range(1, N + 1)))


def from_diffs(h1, diffs):
    h = [0, h1]
    for x in diffs:
        h.append(h[-1] + x)
    return h


def is_concave(h, N):
    return all(h[j + 1] - h[j] <= h[j] - h[j - 1] for j in range(2, N))


def is_nondecreasing(h, N):
    return all(h[j] >= h[j - 1] for j in range(2, N + 1))


# ------------------------------------------------------------------------------------------------ H: heap facts
def part_heap():
    bad_split = bad_a = bad_b = bad_c = 0
    for d in range(1, 20001):
        n = d + 1
        H = n.bit_length() - 1
        e = n - (1 << H)
        left_leaves = (1 << (H - 1)) + min(e, 1 << (H - 1))
        right_leaves = (1 << (H - 1)) + max(0, e - (1 << (H - 1)))
        bad_split += (heap_left(d) + 1 != left_leaves) + (HR(d) + 1 != right_leaves)
        for J in range(0, 16):
            Q = 1 << J
            bad_c += (HR(d) >= Q) != (n >= 3 * Q + 1)
        if d >= 2:
            inc = HR(d) - HR(d - 1)
            bad_a += inc not in (0, 1)
            Ds = [D for D in range(1, 16) if 3 * (1 << (D - 1)) < n <= (1 << (D + 1))]
            bad_b += (inc == 1) != bool(Ds)
            if inc == 1 and Ds:
                bad_b += heap_left(d) + 1 != (1 << Ds[0])
    check("heap leaf-split formula, d <= 20000", bad_split == 0, f"{bad_split} mismatches")
    check("Lemma H(a): HR steps in {0, 1}, 2 <= d <= 20000", bad_a == 0, f"{bad_a} violations")
    check("Lemma H(b): step iff n in (3*2^(D-1), 2^(D+1)], left subtree then has 2^D leaves", bad_b == 0,
          f"{bad_b} violations")
    check("Lemma H(c): HR(d) >= 2^J iff n >= 3*2^J + 1, J <= 15, d <= 20000", bad_c == 0, f"{bad_c} violations")


# ------------------------------------------------------------------------------------------------ L: lemmas
def E(lam):
    D = lam.bit_length() - 1
    return lam * (D + 1) - (1 << (D + 1)) + 1


def g_cap(k, n):
    J = (k + 1).bit_length() - 1
    P = 1 << J
    delta = k + 1 - P
    return (n // P) * delta + min(n % P, delta)


def cap_closed(k, n):
    J = (k + 1).bit_length() - 1
    return J * n + g_cap(k, n) - k


def part_lemmas(KMAX=64, NMAX=520):
    Nlin = 1200
    Clin, Tlin = dp([0] + list(range(1, Nlin + 1)), Nlin)
    bad = sum(Clin[lam - 1] != E(lam) for lam in range(1, Nlin + 2))
    bad += sum(E(lam + 1) - E(lam) != (lam.bit_length() - 1) + 1 for lam in range(1, 5000))
    check(f"Lemma B: E(lambda) = optimum of h(s) = s for lambda <= {Nlin + 1}; increments", bad == 0, f"{bad}")
    capC, capT = {}, {}
    for k in range(1, KMAX + 1):
        capC[k], capT[k] = dp([0] + [min(s, k) for s in range(1, NMAX + 1)], NMAX)
    bad = 0
    for k in range(1, KMAX + 1):
        P = 1 << ((k + 1).bit_length() - 1)
        for n in range(1, NMAX + 2):
            A = capC[k][n - 1]
            bad += (n <= k + 1 and A != E(n)) + (n >= P and A != cap_closed(k, n))
    check(f"Lemma C: closed form of A_k(n) vs DP, k <= {KMAX}, n <= {NMAX + 1}", bad == 0, f"{bad} mismatches")
    bad1 = bad2 = 0
    for k in range(1, 300):
        J = (k + 1).bit_length() - 1
        P = 1 << J
        for lam in range(1, k + 2):
            lhs, rhs = k + E(lam), J * lam + g_cap(k, lam)
            bad1 += lhs < rhs or (P <= lam and lhs != rhs)
        if k <= 24:
            for a in range(1, 120):
                for b in range(1, 120):
                    bad2 += g_cap(k, a + b) > g_cap(k, a) + g_cap(k, b)
    check("Lemma C (F1): k + E(l) >= J l + g(l), equality on [P, k+1], k < 300", bad1 == 0, f"{bad1}")
    check("Lemma C (F2): g subadditive, k <= 24, a, b < 120", bad2 == 0, f"{bad2}")
    bad = 0
    for k in list(range(1, KMAX + 1)) + [None]:
        hc = [0] * (NMAX + 1)
        for d in range(1, NMAX + 1):
            L = heap_left(d)
            hc[d] = (d if k is None else min(d, k)) + hc[L] + hc[d - 1 - L]
            bad += hc[d] != (Clin[d] if k is None else capC[k][d])
    check(f"Lemma D: heap cost = optimum, caps k <= {KMAX} and linear, d <= {NMAX}", bad == 0, f"{bad}")
    bad = cases = 0
    for D in range(1, 9):
        for k in [kk for kk in range(1, KMAX + 1) if kk >= (1 << D)] + [None]:
            A = (lambda x: Clin[x - 1]) if k is None else (lambda x, k=k: capC[k][x - 1])
            for n in range(3 * (1 << (D - 1)) + 1, min((1 << (D + 1)), NMAX) + 1):
                cases += 1
                bad += (A((1 << D) + 1) + A(n - (1 << D) - 1)) - (A(1 << D) + A(n - (1 << D))) != 1
    check("Lemma F: forcing difference = 1", bad == 0 and cases > 0, f"{cases} cases, {bad} violations")
    bad = cases = 0
    for k in range(1, KMAX + 1):
        for Jp in range(0, 10):
            if k < (1 << (Jp + 1)):
                Q = 1 << Jp
                for n in range(3 * Q, NMAX + 2):
                    cases += 1
                    bad += capC[k][n - 1] != capC[k][n - Q - 1] + capC[k][Q - 1] + k
    check("Lemma G: A_k(n) = A_k(n - Q) + A_k(Q) + k", bad == 0 and cases > 0, f"{cases} cases, {bad} violations")
    rng = random.Random(77)
    badA = badE = 0
    for _ in range(200):
        N = rng.randint(2, 100)
        a = rng.choice([0, 0, rng.randint(1, 5)])
        c = {k: (rng.randint(1, 9) if rng.random() < 0.25 else 0) for k in range(2, min(N, KMAX + 1))}
        kappa = rng.randint(-5, 5)
        h = [0] + [kappa + a * s + sum(ck * min(s, k) for k, ck in c.items()) for s in range(1, N + 1)]
        dh = {j: h[j] - h[j - 1] for j in range(2, N + 1)}
        a2, c2 = dh[N], {k: dh[k] - dh[k + 1] for k in range(2, N)}
        kap2 = h[1] - a2 - sum(c2.values())
        badA += any(h[s] != kap2 + a2 * s + sum(ck * min(s, k) for k, ck in c2.items()) for s in range(1, N + 1))
        C, T = dp(h, N)
        for d in range(1, N + 1):
            val = kappa * d + a * Clin[d] + sum(ck * capC[k][d] for k, ck in c.items())
            inter = set(range(d))
            for k, ck in c.items():
                if ck > 0:
                    inter &= capT[k][d]
            if a > 0:
                inter &= Tlin[d]
            badE += (C[d] != val) + (T[d] != inter) + (heap_left(d) not in T[d])
    check("Lemma A: representation recovered, 200 seeded random h", badA == 0, f"{badA}")
    check("Lemma E: C = kappa d + a C_lin + sum c_k C_k and T = intersection, 200 seeded random h", badE == 0,
          f"{badE}")


# ------------------------------------------------------------------------------------------------ T: theorem
def part_theorem(NSUP=16):
    rng = random.Random(2026)
    tot = ok_u = ok_r = 0
    for N in range(2, NSUP + 1):
        ks = list(range(2, N))
        for bits in range(1 << (len(ks) + 1)):
            a = bits & 1
            ck = {k: (bits >> (i + 1)) & 1 for i, k in enumerate(ks)}
            h = [0] + [a * s + sum(v * min(s, k) for k, v in ck.items()) for s in range(1, N + 1)]
            ok_u += all(theorem_holds(h, N))
            ar = a * rng.randint(1, 7)
            cr = {k: v * rng.randint(1, 7) for k, v in ck.items()}
            hr = [0] + [ar * s + sum(v * min(s, k) for k, v in cr.items()) for s in range(1, N + 1)]
            ok_r += all(theorem_holds(hr, N))
            tot += 1
    check(f"Theorem, all supports N = 2..{NSUP}, unit weights", ok_u == tot, f"{ok_u}/{tot}")
    check(f"Theorem, all supports N = 2..{NSUP}, seeded random weights 1..7", ok_r == tot, f"{ok_r}/{tot}")
    for B, N in ((3, 16), (4, 14), (6, 12), (8, 10)):
        tot = ok = 0
        for diffs in itertools.combinations_with_replacement(range(B, -1, -1), N - 1):
            h = from_diffs(0, diffs)
            tot += 1
            ok += all(theorem_holds(h, N))
        check(f"Theorem, all integer h with h(1) = 0, nonincreasing differences in [0, {B}], N = {N}", ok == tot,
              f"{ok}/{tot}")
    tot = ok = cons_bad = 0
    for it in range(150):
        N = rng.randint(2, 200)
        style = it % 5
        if style == 0:
            h = from_diffs(rng.randint(-5, 5), sorted((rng.randint(0, 50) for _ in range(N - 1)), reverse=True))
        elif style == 1:
            diffs = [int(1000 / (j ** 0.5)) for j in range(1, N)]
            h = from_diffs(0, [min(diffs[:i + 1]) for i in range(len(diffs))])
        elif style == 2:
            K = rng.randint(2, max(2, N // 3))
            h = [0] + [3 * min(s, K) + min(s, max(2, K // 2)) for s in range(1, N + 1)]
        elif style == 3:
            h = from_diffs(Fraction(rng.randint(-9, 9), 7),
                           sorted((Fraction(rng.randint(0, 30), rng.randint(1, 7)) for _ in range(N - 1)),
                                  reverse=True))
        else:
            h = from_diffs(0, sorted((rng.randint(1, 20) for _ in range(N - 1)), reverse=True))
        assert is_concave(h, N) and is_nondecreasing(h, N)
        tot += 1
        ok += all(theorem_holds(h, N))
        for d in rng.sample(range(1, N + 1), min(6, N)):
            for N2 in range(d, N + 1, max(1, (N - d) // 5)):
                cons_bad += tau_star(h, N2, d) != tau_star(h, N, d)
    check("Theorem, 150 seeded random h (integer and Fraction), N <= 200", ok == tot, f"{ok}/{tot}")
    check("tau*_N(d) does not depend on N >= d (same 150 h, sampled d and N)", cons_bad == 0, f"{cons_bad}")


# ------------------------------------------------------------------------------------------------ X: 2-D
def interval_runs(w, n):
    """Full cubic DP c and Knuth's restricted runs (largest and smallest tie rule) on the interval recurrence
    c(i,i) = 0, c(i,j) = w(i,j) + min_{i<k<=j} c(i,k-1) + c(k,j). Returns c, (cL, KL), (cS, KS)."""
    M = n + 1
    c = [[0] * M for _ in range(M)]
    for d in range(1, M):
        for i in range(M - d):
            j = i + d
            c[i][j] = w[i][j] + min(c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1))
    runs = []
    for rule in ("largest", "smallest"):
        cr = [[0] * M for _ in range(M)]
        K = [[i if i == j else None for j in range(M)] for i in range(M)]
        for d in range(1, M):
            for i in range(M - d):
                j = i + d
                lo, hi = max(K[i][j - 1], i + 1), min(K[i + 1][j], j)
                if lo > hi:
                    raise AssertionError("empty window")
                vals = {k: cr[i][k - 1] + cr[k][j] for k in range(lo, hi + 1)}
                m = min(vals.values())
                ks = [k for k in vals if vals[k] == m]
                K[i][j] = max(ks) if rule == "largest" else min(ks)
                cr[i][j] = w[i][j] + m
        runs.append((cr, K))
    return c, runs[0], runs[1]


def part_2d():
    rng = random.Random(99)
    tot = ok = 0
    for _ in range(200):
        n = rng.randint(1, 30)
        h = from_diffs(rng.randint(-3, 3), sorted((rng.randint(0, 9) for _ in range(n - 1)), reverse=True))
        w = [[(h[j - i] if j > i else 0) for j in range(n + 1)] for i in range(n + 1)]
        c, (cL, KL), (cS, KS) = interval_runs(w, n)
        good = True
        for i in range(n + 1):
            for j in range(i + 1, n + 1):
                d = j - i
                ts = tau_star(h, n, d)
                good &= cL[i][j] == c[i][j] and cS[i][j] == c[i][j]
                good &= KL[i][j] == i + 1 + ts and KS[i][j] == i + 1 + (d - 1 - ts)
        tot += 1
        ok += good
    check("2-D interval run: exact for both tie rules, K(i,j) = i+1+tau*(j-i) (largest), "
          "i+1+min(HR, Q-1) (smallest), 200 seeded h, n <= 30", ok == tot, f"{ok}/{tot}")


# ------------------------------------------------------------------------------------------------ B: boundary
def first_failure(h, N, rule):
    C, _ = dp(h, N)
    Cr, _ = knuth_run(h, N, rule)
    return next((d for d in range(1, N + 1) if Cr[d] != C[d]), None)


def part_boundary():
    controls = [("concave, not monotone", [0, 0, 1, -2, -5], 4),
                ("nondecreasing, not concave", [0, 0, 1, 1, 1, 2, 2, 2], 7),
                ("convex, not monotone", [0, 0, -3, -2, 0, 2], 5)]
    for label, h, d_expected in controls:
        N = len(h) - 1
        fl, fs = first_failure(h, N, "largest"), first_failure(h, N, "smallest")
        check(f"control ({label}) h = {tuple(h[1:])}: run not exact, first at d = {d_expected}, both rules",
              fl == d_expected and fs == d_expected, f"first failure largest {fl}, smallest {fs}")
    N = 7
    cls = {}
    for diffs in itertools.product(range(-2, 3), repeat=N - 1):
        h = from_diffs(0, diffs)
        conc, nondec = is_concave(h, N), is_nondecreasing(h, N)
        key = ("concave" if conc else "not concave") + ", " + ("nondecreasing" if nondec else "not nondecreasing")
        C, _ = dp(h, N)
        exact = knuth_run(h, N, "largest")[0] == C and knuth_run(h, N, "smallest")[0] == C
        st = cls.setdefault(key, [0, 0])
        st[0] += 1
        st[1] += exact
    for key in sorted(cls):
        print(f"       class {key}: {cls[key][0]} functions, {cls[key][1]} exact under both rules")
    th = cls["concave, nondecreasing"]
    check("class table (h on {1..7}, h(1) = 0, differences in [-2, 2]): every concave nondecreasing h exact",
          th[0] == th[1] and th[0] > 0, f"{th[1]}/{th[0]}")
    check("class table: some failure when concavity fails, and some when monotonicity fails",
          cls["not concave, nondecreasing"][1] < cls["not concave, nondecreasing"][0]
          and cls["concave, not nondecreasing"][1] < cls["concave, not nondecreasing"][0])
    # tie rule: h = min(s, 5) - 1
    N = 10
    h = [0] + [min(s, 5) - 1 for s in range(1, N + 1)]
    C, T = dp(h, N)
    _, tl = knuth_run(h, N, "largest")
    Cd, td = knuth_run(h, N, "custom", pick=lambda d, mins: mins[0] if d == 9 else mins[-1])
    check("tie rule matters: h = min(s,5) - 1, T(9) = {1..7}, T(10) = {2,3,6,7}, largest rule tau'(8), tau'(9) = 4, 5;"
          " taking 4 at d = 9 gives window {4,5} at d = 10 and is not exact",
          sorted(T[9]) == list(range(1, 8)) and sorted(T[10]) == [2, 3, 6, 7] and tl[8:10] == [4, 5]
          and td[9] == 4 and Cd != C and Cd[10] != C[10])
    inc = [C[d] - C[d - 1] for d in range(1, N + 1)]
    check("C is not convex for h = min(s,5) - 1: increments C(d) - C(d-1), d = 1..10, are (0,1,1,2,2,1,1,2,2,1)",
          inc == [0, 1, 1, 2, 2, 1, 1, 2, 2, 1], str(tuple(inc)))
    small = sum(1 for N in (1, 2) for vals in itertools.product(range(-3, 4), repeat=N)
                if all(knuth_run([0] + list(vals), N, r)[0] == dp([0] + list(vals), N)[0]
                       for r in ("largest", "smallest")))
    check("N = 1, 2: every h with values in -3..3 exact under both rules", small == 7 + 49, f"{small}/56")
    # largest optimal roots are not monotone: h = min(s, 2), N = 4
    h = [0] + [min(s, 2) for s in range(1, 5)]
    _, T = dp(h, 4)
    check("largest optimal roots not monotone: h = min(s,2), T(3) = {1}, T(4) = {0,1,2,3} (max T(4) > max T(3) + 1)",
          T[3] == {1} and T[4] == {0, 1, 2, 3})
    check("theorem still holds for h = min(s,2), N = 4", all(theorem_holds(h, 4)))
    # reverse quadrangle inequality for concave h: w(a,c) + w(b,d) >= w(a,d) + w(b,c), a <= b < c <= d
    bad = 0
    for diffs in itertools.combinations_with_replacement(range(4, -1, -1), 7):
        h = from_diffs(0, diffs)
        for a, b, c, d in itertools.combinations_with_replacement(range(9), 4):
            if b < c:
                bad += h[c - a] + h[d - b] < h[d - a] + h[c - b]
    check("reverse quadrangle inequality for concave h (all h on {1..8}, differences nonincreasing in [0, 4])",
          bad == 0, f"{bad} violations")


def main():
    t0 = time.time()
    for name, fn in (("H", part_heap), ("L", part_lemmas), ("T", part_theorem), ("X", part_2d),
                     ("B", part_boundary)):
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
