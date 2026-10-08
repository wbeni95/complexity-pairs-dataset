#!/usr/bin/env python3
"""Verifier for theorems/partial-fourier-bound-tripartition-tensors (see README.md in this folder).

Notation as in the README. Subsets of [n] = {1..n} are bitmasks (bit i-1 <-> element i). A sign vector t with
t_n = +1 is encoded by y = {i : t_i = -1}, a subset of [n-1]; then u_t(S) = prod_{i in S} t_i and
chi_v(t) = (-1)^{|v & y|}. D = D_{a,b} = {S xor T : |S| = a, |T| = b}.

What it checks, in order (exact arithmetic: integers and fractions.Fraction; one prime field only to choose columns):
  1. Lemma 1 (description and size of D) for every (a, b, c) with a, b, c >= 0 and 1 <= n <= 10: D computed by
     brute force equals {v : |v| = a+b (mod 2), |a-b| <= |v| <= a+b}, and |D| = sum_j C(n, a+b-2j);
     Lemma 4 (the bijection v -> v minus {n} from D onto the sets of size <= r) for the cases with |a-b| <= 1;
  2. Corollary 1 values: |D_{d,d}| = sum_k C(3d, 2k) = sum_{i<=2d} C(3d-1, i) for d <= 12, brute force for
     d <= 4 (4, 31, 247, 1981); Corollary 2: |D_{1,1}| = 1 + C(c+2, 2) for 0 <= c <= 20 (brute force);
  3. Theorem 1 (constructive part) for every (a, b, c) with a, b, c >= 0 and 1 <= n <= 7, for (3, 3, 3) and for
     (1, 1, c) with 6 <= c <= 10: the decomposition with |Gamma| = |D| terms is built and checked exactly.
     For |a-b| <= 1 it is the explicit one of Theorem 2 (Gamma_0, W from the Moebius formula), and the check is
     the integer identity 2^r T_{a,b,c} = sum_t u_t (x) u_t (x) (2^r W_t) with 2^r W_t integral; for |a-b| >= 2
     the columns are chosen by elimination (the first |D| independent ones in a fixed order) and the identity is
     checked over Q. The identity is checked (i) entry by entry for every case except (3, 3, 3), and (ii) for
     every case through the three facts of the proof: u_t(S) u_t(T) = chi_{S xor T}(t) for all S, T, t;
     sum_t chi_v(t) W_t = tau_v for all v in D; tau_{S xor T}(U) = [(S, T, U) is a partition] for all S, T, U;
  4. Theorem 3 (optimality) on small cases, exhaustively: for (1,1,1), (1,1,2), (2,1,1), (1,1,3), (2,1,2) and
     (2,2,2), no set of |D| - 1 sign vectors with t_n = +1 admits weights W_t (the system X W = tau is
     inconsistent), over F_3 and over F_(2^31-1); every set of |D| sign vectors that the elimination of check 3
     selects does admit them;
  5. Proposition 4, in exact integer arithmetic for 1 <= d <= 200: 8^d/2 - (27/4)^d <= |D_{d,d}| <= 8^d/2 (strict
     on the right for d >= 2), 8^d/2 - |D_{d,d}| = sum_{k > d} C(3d, 2k), sum_{i<=d} C(3d, i) <= (27/4)^d, and
     (27/4)^d / (3d+1) <= C(3d, d).
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count; the wall-clock seconds
follow on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):  python theorems/partial-fourier-bound-tripartition-tensors/verify.py
Deterministic and offline, standard library only; well under a minute.
"""
import sys
import time
from fractions import Fraction
from itertools import combinations
from math import comb

BIG = 2 ** 31 - 1
FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)")


def pc(x):
    return bin(x).count("1")


def ksubsets(n, k):
    return sorted(sum(1 << (e - 1) for e in c) for c in combinations(range(1, n + 1), k))


def triples(nmax, nmin=1):
    return [(a, b, n - a - b) for n in range(nmin, nmax + 1) for a in range(n + 1) for b in range(n + 1 - a)]


def D_set(n, a, b):
    return {x ^ y for x in ksubsets(n, a) for y in ksubsets(n, b)}


# ------------------------------------------------------------------------------------------------ construction
class Case:
    """Everything about T_{a,b,c}: coordinates, D, targets tau_v."""

    def __init__(self, a, b, c):
        self.a, self.b, self.c = a, b, c
        self.n = n = a + b + c
        self.SA, self.SB, self.SC = ksubsets(n, a), ksubsets(n, b), ksubsets(n, c)
        self.ic = {m: i for i, m in enumerate(self.SC)}
        self.full = (1 << n) - 1
        self.D = sorted(D_set(n, a, b))
        # tau_v: index of the coordinate [n] \ v in the third factor if |v| = a + b, else None (the zero vector)
        self.tau = {v: (self.ic[self.full ^ v] if pc(v) == a + b else None) for v in self.D}


def explicit_decomposition(cs):
    """|a-b| <= 1: Gamma_0 = all y in [n-1] with |y| <= r; returns (r, Gamma, {y: integer vector 2^r W_y}, steps)."""
    n, a, b = cs.n, cs.a, cs.b
    r = min(a + b, n - 1)
    low = (1 << (n - 1)) - 1
    F = [w for w in range(1 << (n - 1)) if pc(w) <= r]
    v_of = {}
    for v in cs.D:
        v_of[v & low] = v
    if sorted(v_of) != F:          # Lemma 4 bijection
        return r, F, None, 0
    steps = 0
    # G[z] = sum_{w subset z} (-1)^{|z|-|w|} tau'_w  (sparse vectors {coordinate: integer})
    G = {}
    for z in F:
        g = {}
        for w in F:
            steps += 1
            if w & z == w:
                k = cs.tau[v_of[w]]
                if k is not None:
                    g[k] = g.get(k, 0) + (-1) ** (pc(z) - pc(w))
        G[z] = g
    # 2^r W[y] = sum_{z superset y} (-1)^{|z|-|y|} 2^(r-|z|) (-1)^{|z|} G[z]
    W = {}
    for y in F:
        vec = [0] * len(cs.SC)
        for z in F:
            steps += 1
            if z & y == y:
                f = (-1) ** (pc(z) - pc(y)) * (-1) ** pc(z) * 2 ** (r - pc(z))
                for k, x in G[z].items():
                    vec[k] += f * x
        W[y] = vec
    return r, F, W, steps


def rank_columns_mod(cols, q):
    """Indices of the columns chosen greedily (first independent ones) over F_q, and the operation count."""
    basis = []          # list of (pivot position, reduced vector)
    chosen, steps = [], 0
    for idx, col in enumerate(cols):
        v = [x % q for x in col]
        for piv, bv in basis:
            if v[piv]:
                f = v[piv]
                v = [(x - f * y) % q for x, y in zip(v, bv)]
                steps += len(v)
        piv = next((i for i, x in enumerate(v) if x), None)
        if piv is not None:
            inv = pow(v[piv], q - 2, q)
            basis.append((piv, [(x * inv) % q for x in v]))
            chosen.append(idx)
    return chosen, steps


def solve_exact(X, Bm):
    """Solve X W = Bm over Q for a square invertible X (Gauss-Jordan with Fractions).
    Returns (solution or None if singular, number of Fraction operations)."""
    m = len(X)
    A = [[Fraction(x) for x in X[i]] + [Fraction(x) for x in Bm[i]] for i in range(m)]
    ops = 0
    for col in range(m):
        piv = next((i for i in range(col, m) if A[i][col] != 0), None)
        if piv is None:
            return None, ops
        A[col], A[piv] = A[piv], A[col]
        f = A[col][col]
        A[col] = [x / f for x in A[col]]
        ops += len(A[col])
        for i in range(m):
            if i != col and A[i][col] != 0:
                g = A[i][col]
                A[i] = [x - g * y for x, y in zip(A[i], A[col])]
                ops += len(A[col])
    return [row[m:] for row in A], ops


def general_decomposition(cs):
    """Columns y in [n-1] in order (|y|, y); the first |D| independent ones over F_BIG; W solved over Q."""
    n = cs.n
    ys = sorted(range(1 << (n - 1)), key=lambda y: (pc(y), y))
    cols = [[(-1) ** pc(v & y) for v in cs.D] for y in ys]
    chosen, steps = rank_columns_mod(cols, BIG)
    Gamma = [ys[i] for i in chosen]
    X = [[(-1) ** pc(v & y) for y in Gamma] for v in cs.D]
    Bm = [[int(cs.tau[v] == k) for k in range(len(cs.SC))] for v in cs.D]
    sol, ops = solve_exact(X, Bm) if len(Gamma) == len(cs.D) else (None, 0)
    if sol is None:
        return None, Gamma, None, steps + ops
    W = {y: sol[i] for i, y in enumerate(Gamma)}
    return 0, Gamma, W, steps + ops


def u_vector(subsets, y, n):
    """u_t over the given subsets for the sign vector t encoded by y (t_n = +1), as a product of signs."""
    t = [(-1 if (y >> i) & 1 else 1) for i in range(n - 1)] + [1]
    out = []
    for S in subsets:
        p = 1
        for i in range(n):
            if S >> i & 1:
                p *= t[i]
        out.append(p)
    return out


def check_identity(cs, Gamma, W, scale, direct):
    """(ok_direct or None, ok_staged, steps). scale * T_{a,b,c} = sum_t u_t (x) u_t (x) W_t, exactly."""
    n = cs.n
    UA = {y: u_vector(cs.SA, y, n) for y in Gamma}
    UB = {y: u_vector(cs.SB, y, n) for y in Gamma}
    steps = 0
    ok_direct = None
    if direct:
        ok_direct = True
        for i, x in enumerate(cs.SA):
            for j, z in enumerate(cs.SB):
                coef = [UA[y][i] * UB[y][j] for y in Gamma]
                vec = [0] * len(cs.SC)
                for cf, y in zip(coef, Gamma):
                    Wy = W[y]
                    for k in range(len(cs.SC)):
                        vec[k] += cf * Wy[k]
                steps += len(Gamma) * len(cs.SC)
                for k, w in enumerate(cs.SC):
                    part = not (x & z) and not (x & w) and not (z & w) and (x | z | w) == cs.full
                    if vec[k] != scale * part:
                        ok_direct = False
    # staged: (a) u_t(S) u_t(T) = chi_{S xor T}(t)
    ok = True
    for i, x in enumerate(cs.SA):
        for j, z in enumerate(cs.SB):
            v = x ^ z
            for y in Gamma:
                ok &= UA[y][i] * UB[y][j] == (-1) ** pc(v & y)
            steps += len(Gamma)
    # (b) sum_t chi_v(t) W_t = scale * tau_v for every v in D
    for v in cs.D:
        vec = [0] * len(cs.SC)
        for y in Gamma:
            s = (-1) ** pc(v & y)
            Wy = W[y]
            for k in range(len(cs.SC)):
                vec[k] += s * Wy[k]
        steps += len(Gamma) * len(cs.SC)
        want = [scale * int(cs.tau[v] == k) for k in range(len(cs.SC))]
        ok &= vec == want
    # (c) tau_{S xor T}(U) = [(S, T, U) is an ordered partition]
    for x in cs.SA:
        for z in cs.SB:
            for k, w in enumerate(cs.SC):
                part = not (x & z) and not (x & w) and not (z & w) and (x | z | w) == cs.full
                ok &= (cs.tau[x ^ z] == k) == part
            steps += len(cs.SC)
    return ok_direct, ok, steps


def consistent(cs, Gamma, q):
    """Does X W = tau have a solution over F_q? Row reduction of [X | tau] with the columns of X first: the system
    is inconsistent iff some pivot falls in a tau column (rank [X | tau] > rank X). Returns (answer, operations)."""
    ncx = len(Gamma)
    rows = [[(-1) ** pc(v & y) % q for y in Gamma] + [int(cs.tau[v] == k) for k in range(len(cs.SC))]
            for v in cs.D]
    rk, ops = 0, 0
    for c in range(len(rows[0])):
        piv = next((i for i in range(rk, len(rows)) if rows[i][c]), None)
        if piv is None:
            continue
        if c >= ncx:
            return False, ops
        rows[rk], rows[piv] = rows[piv], rows[rk]
        inv = pow(rows[rk][c], q - 2, q)
        pr = [(x * inv) % q for x in rows[rk]]
        rows[rk] = pr
        ops += len(pr)
        for i in range(rk + 1, len(rows)):
            f = rows[i][c]
            if f:
                rows[i] = [(x - f * y) % q for x, y in zip(rows[i], pr)]
                ops += len(pr)
        rk += 1
    return True, ops


def main():
    t_start = time.perf_counter()

    # 1. Lemma 1 and Lemma 4
    t0 = time.perf_counter()
    ok, ok4, steps, cases = True, True, 0, 0
    for a, b, c in triples(10):
        n = a + b + c
        D = D_set(n, a, b)
        steps += comb(n, a) * comb(n, b)
        desc = {v for v in range(1 << n) if (pc(v) - a - b) % 2 == 0 and abs(a - b) <= pc(v) <= a + b}
        steps += 1 << n
        ok &= D == desc and len(D) == sum(comb(n, a + b - 2 * j) for j in range(min(a, b) + 1))
        if abs(a - b) <= 1:
            r = min(a + b, n - 1)
            low = (1 << (n - 1)) - 1
            img = sorted(v & low for v in D)
            ok4 &= img == sorted(w for w in range(1 << (n - 1)) if pc(w) <= r)
        cases += 1
    check("Lemma 1: D_{a,b} = {v : |v| = a+b mod 2, |a-b| <= |v| <= a+b}, |D| = sum_j C(n, a+b-2j); Lemma 4: "
          "v -> v minus {n} maps D onto the sets of size <= r when |a-b| <= 1", ok and ok4,
          f"all {cases} triples (a,b,c) >= 0 with 1 <= n <= 10, steps = {steps} set operations")
    timed(t0)

    # 2. Corollary values
    t0 = time.perf_counter()
    vals = [sum(comb(3 * d, 2 * k) for k in range(d + 1)) for d in range(1, 13)]
    alt = [sum(comb(3 * d - 1, i) for i in range(2 * d + 1)) for d in range(1, 13)]
    brute = [len(D_set(3 * d, d, d)) for d in range(1, 5)]
    t11 = all(len(D_set(c + 2, 1, 1)) == 1 + comb(c + 2, 2) for c in range(21))
    steps = sum(comb(3 * d, d) ** 2 for d in range(1, 5)) + sum((c + 2) ** 2 for c in range(21))
    check("Corollaries: |D_{d,d}| = sum_k C(3d,2k) = sum_{i<=2d} C(3d-1,i) (d <= 12), brute force 4, 31, 247, 1981 "
          "(d <= 4); |D_{1,1}| = 1 + C(c+2,2) (c <= 20, brute force)",
          vals == alt and brute == vals[:4] == [4, 31, 247, 1981] and t11,
          f"values d = 1..6: {vals[:6]}; steps = {steps} pairs")
    timed(t0)

    # 3. Theorem 1: build and check the decompositions
    t0 = time.perf_counter()
    todo = triples(7) + [(3, 3, 3)] + [(1, 1, c) for c in range(6, 11)]
    stats = {"explicit": 0, "general": 0, "direct": 0, "entries": 0}
    ok_all, steps, failed = True, 0, []
    for a, b, c in todo:
        cs = Case(a, b, c)
        if abs(a - b) <= 1:
            r, Gamma, W, st = explicit_decomposition(cs)
            scale = 2 ** r
            kind = "explicit"
        else:
            r, Gamma, W, st = general_decomposition(cs)
            scale = 1
            kind = "general"
        steps += st
        good = W is not None and len(Gamma) == len(cs.D)
        if good:
            direct = (a, b, c) != (3, 3, 3)
            okd, oks, st = check_identity(cs, Gamma, W, scale, direct)
            steps += st
            good = oks and (okd is None or okd)
            if okd is not None:
                stats["direct"] += 1
                stats["entries"] += len(cs.SA) * len(cs.SB) * len(cs.SC)
            if kind == "explicit":
                good &= all(type(x) is int for y in Gamma for x in W[y])
        stats[kind] += 1
        if not good:
            failed.append((a, b, c))
        ok_all &= good
    check("Theorem 1: T_{a,b,c} = sum over |D_{a,b}| terms u_t (x) u_t (x) W_t, built and checked exactly",
          ok_all, f"{len(todo)} triples (all with n <= 7, (3,3,3), (1,1,c) for c = 6..10): {stats['explicit']} "
                  f"explicit (integer identity scaled by 2^r), {stats['general']} with |a-b| >= 2 (over Q); "
                  f"{stats['direct']} also checked entry by entry ({stats['entries']} entries); failures {failed}; "
                  f"steps = {steps}")
    timed(t0)

    # 4. Theorem 3 (optimality), exhaustive on small cases
    t0 = time.perf_counter()
    ok, steps, detail = True, 0, []
    for a, b, c in [(1, 1, 1), (1, 1, 2), (2, 1, 1), (1, 1, 3), (2, 1, 2), (2, 2, 2)]:
        cs = Case(a, b, c)
        classes = list(range(1 << (cs.n - 1)))
        m = len(cs.D)
        tested = 0
        for G in combinations(classes, m - 1):
            for q in (3, BIG):
                res, ops = consistent(cs, list(G), q)
                ok &= not res
                steps += ops
            tested += 1
        _, Gsel, _, _ = general_decomposition(cs)
        for q in (3, BIG):
            res, ops = consistent(cs, Gsel, q)
            ok &= len(Gsel) == m and res
            steps += ops
        detail.append(f"({a},{b},{c}): |D| = {m}, {tested} sets of size {m - 1}")
    check("Theorem 3 on small cases: no |D|-1 sign vectors admit weights (over F_3 and F_(2^31-1)); the selected "
          "|D| do", ok, "; ".join(detail) + f"; steps = {steps} field operations")
    timed(t0)

    # 5. Proposition 4
    t0 = time.perf_counter()
    ok, steps = True, 0
    for d in range(1, 201):
        Dd = sum(comb(3 * d, 2 * k) for k in range(d + 1))
        half = 8 ** d // 2
        tail = sum(comb(3 * d, i) for i in range(d + 1))
        ok &= Dd <= half and (Dd < half or d == 1)
        ok &= 4 ** d * (half - Dd) <= 27 ** d                     # 8^d/2 - (27/4)^d <= D_d
        ok &= 4 ** d * tail <= 27 ** d                             # sum_{i<=d} C(3d,i) <= (27/4)^d
        ok &= 27 ** d <= (3 * d + 1) * 4 ** d * comb(3 * d, d)     # (27/4)^d / (3d+1) <= C(3d,d)
        ok &= half - Dd == sum(comb(3 * d, 2 * k) for k in range(d + 1, 3 * d // 2 + 1))
        steps += 6
    check("Proposition 4: 8^d/2 - (27/4)^d <= |D_{d,d}| <= 8^d/2 (strict for d >= 2), sum_{i<=d} C(3d,i) <= "
          "(27/4)^d, (27/4)^d/(3d+1) <= C(3d,d), exactly", ok, f"1 <= d <= 200, steps = {steps} exact "
                                                               f"comparisons")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
