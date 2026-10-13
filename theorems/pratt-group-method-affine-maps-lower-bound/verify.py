#!/usr/bin/env python3
"""Verifier for theorems/pratt-group-method-affine-maps-lower-bound (see README.md in this folder).

Notation as in the README: k >= 1, the k-subsets of [3k] as bitmasks (bit e-1 <-> element e), 1_S in F_2^{3k} as the
same bitmask, ONE = 1_[3k], E = the even-weight vectors. A triple of maps (f1, f2, f3) into an abelian group G with
x in G is *valid* if f1(S) + f2(T) + f3(U) = x exactly when (S, T, U) is an ordered partition of [3k].

What it checks, in order (exact integer / bit arithmetic):
  1. Theorem 2 (sums of three k-sets): for k = 1, 2, 3, over all ordered triples of k-subsets, the set of vectors
     ONE + 1_S + 1_T + 1_U is exactly E, and the zero vector arises exactly from the (3k)!/(k!)^3 ordered partitions;
     for k = 1, ..., 8 the explicit triple of the proof (Lemma 2.2) gives ONE + w for one vector w of every even
     weight 2t <= 3k, with three sets of size k;
  2. Theorem 3, single map, by brute force over all ordered triples, for k = 1, 2: a linear map with kernel K is
     valid (with x = L(ONE)) iff K contains no nonzero even-weight vector; every 1-dimensional kernel <a> is valid
     iff |a| is odd, and every 2-dimensional kernel fails (all 7 + 651 of them);
  3. Theorem 3, three affine maps, for k = 1, 2: on a fixed list of structured and pseudo-random triples of affine
     maps (m = 3k - 1 and m = 3k), validity by brute force agrees with the criterion (i)-(iii) of the theorem;
  4. negative and positive controls: the deletion map is valid and the kernel <e_1 + e_2> is not (with the explicit
     false positive of the proof) for k = 1, ..., 4; the kernel <ONE> (the reading R1 of the companion note) is valid
     exactly for odd k, k = 1, ..., 4;
  5. Proposition 5: exhaustively, no valid triple of arbitrary maps exists for k = 1 into Z_2 (2^9 * 2 cases) or Z_3
     (3^9 * 3 cases), both of order < 4 = 2 C(3,1) - C(2,1); the ingredients of the proof on the deletion map,
     k = 1, 2, 3; the numbers 2 C(3k,k) - C(2k,k) give m >= 3k - 1 exactly for k <= 3, and C(3k,k) <= 2^{3k-3}
     for 4 <= k <= 60 (so 2 C(3k,k) - C(2k,k) < 2^{3k-2} there, too weak to give m >= 3k - 1).
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count; the wall-clock seconds follow
on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):
    python theorems/pratt-group-method-affine-maps-lower-bound/verify.py
Deterministic and offline, standard library only; well under a minute.
"""
import sys
import time
from itertools import combinations, product
from math import comb, factorial

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)")


def ksubsets(n, k):
    return sorted(sum(1 << (e - 1) for e in c) for c in combinations(range(1, n + 1), k))


def weight(v):
    return bin(v).count("1")


class LCG:
    """A fixed linear congruential generator (deterministic test data)."""

    def __init__(self, seed):
        self.s = seed

    def next(self, lo, hi):
        self.s = (6364136223846793005 * self.s + 1442695040888963407) % 2 ** 64
        return lo + (self.s >> 33) % (hi - lo + 1)


# ---------------------------------------------------------------- linear maps F_2^n -> F_2^m as column lists
def apply(L, v):
    """L is a list of n column bitmasks (images of e_1, ..., e_n); returns L(v)."""
    out = 0
    i = 0
    while v:
        if v & 1:
            out ^= L[i]
        v >>= 1
        i += 1
    return out


def kernel_quotient(n, K):
    """A linear map F_2^n -> F_2^(n - dim K) with kernel span(K) (K a list of independent vectors).
    Built by reducing every e_i modulo span(K) and coordinatising the quotient."""
    piv = {}  # pivot bit -> reduced basis vector of span(K)
    for v in K:
        for b, w in piv.items():
            if v >> b & 1:
                v ^= w
        assert v
        b = v.bit_length() - 1
        for bb in list(piv):
            if piv[bb] >> b & 1:
                piv[bb] ^= v
        piv[b] = v
    free = [i for i in range(n) if i not in piv]          # coordinates of the quotient
    cols = []
    for i in range(n):
        v = 1 << i
        for b, w in piv.items():
            if v >> b & 1:
                v ^= w
        cols.append(sum(1 << j for j, f in enumerate(free) if v >> f & 1))
    return cols, len(free)


def is_valid_three(k, f1, f2, f3, x, subsets):
    """Brute force: (f1, f2, f3, x) valid? Returns (valid, triples evaluated, first false positive or missed)."""
    full = (1 << (3 * k)) - 1
    steps = 0
    for S in subsets:
        a = f1[S]
        for T in subsets:
            b = a ^ f2[T]
            for U in subsets:
                steps += 1
                hit = (b ^ f3[U]) == x
                part = not (S & T) and not (S & U) and not (T & U) and (S | T | U) == full
                if hit != part:
                    return False, steps, (S, T, U)
    return True, steps, None


def lemma_witness(k, t):
    """The explicit triple of Lemma 2.2: w = 1_{1..2t}; returns (S, T, U, w)."""
    n = 3 * k
    D = list(range(1, t + 1))               # in two sets
    Z1 = list(range(2 * t + 1, n + 1))       # in one set
    a, r = divmod(t, 3)
    d = [a + (1 if r >= 1 else 0), a + (1 if r >= 2 else 0), a]   # pairs (S,T), (S,U), (T,U)
    S, T, U = set(), set(), set()
    pos = 0
    for cnt, (X, Y) in zip(d, ((S, T), (S, U), (T, U))):
        for _ in range(cnt):
            X.add(D[pos]); Y.add(D[pos]); pos += 1
    for X in (S, T, U):
        while len(X) < k:
            X.add(Z1.pop())
    assert not Z1
    bm = lambda X: sum(1 << (e - 1) for e in X)
    return bm(S), bm(T), bm(U), (1 << (2 * t)) - 1


def main():
    t_start = time.perf_counter()

    # 1. Theorem 2
    t0 = time.perf_counter()
    ok, steps = True, 0
    for k in (1, 2, 3):
        n = 3 * k
        ONE = (1 << n) - 1
        subs = ksubsets(n, k)
        seen, zeros = set(), 0
        for S in subs:
            for T in subs:
                st = S ^ T
                for U in subs:
                    w = ONE ^ st ^ U
                    seen.add(w)
                    zeros += w == 0
                    steps += 1
        even = {v for v in range(1 << n) if weight(v) % 2 == 0}
        ok &= seen == even and zeros == factorial(n) // factorial(k) ** 3
    check("Theorem 2: {1 + 1_S + 1_T + 1_U} = even-weight vectors, zero exactly from partitions (k = 1, 2, 3)", ok,
          f"steps = {steps} ordered triples")
    timed(t0)
    t0 = time.perf_counter()
    ok, cases = True, 0
    for k in range(1, 9):
        n = 3 * k
        ONE = (1 << n) - 1
        for t in range(0, n // 2 + 1):
            S, T, U, w = lemma_witness(k, t)
            ok &= weight(S) == weight(T) == weight(U) == k and (ONE ^ S ^ T ^ U) == w and weight(w) == 2 * t
            cases += 1
    check("Lemma 2.2: the explicit triple gives 1 + w for every even weight 2t <= 3k, three k-sets (k = 1..8)", ok,
          f"steps = {cases} witnesses")
    timed(t0)

    # 2. Theorem 3, single map, all kernels of dimension 1 and 2, k = 1, 2
    t0 = time.perf_counter()
    ok, steps, counts = True, 0, {}
    for k in (1, 2):
        n = 3 * k
        ONE = (1 << n) - 1
        subs = ksubsets(n, k)
        full = ONE
        # the set of vectors 1 + v over non-partition triples (computed once by brute force)
        bad = set()
        for S in subs:
            for T in subs:
                for U in subs:
                    steps += 1
                    part = not (S & T) and not (S & U) and not (T & U) and (S | T | U) == full
                    if not part:
                        bad.add(ONE ^ S ^ T ^ U)
        one_dim_ok, valid1 = True, 0
        for a in range(1, 1 << n):
            valid = a not in bad                      # kernel {0, a}: valid iff no non-partition gives 1+v in K\0
            one_dim_ok &= valid == (weight(a) % 2 == 1)
            valid1 += valid
            steps += 1
        planes, valid2 = set(), 0
        for a in range(1, 1 << n):
            for b in range(a + 1, 1 << n):
                P = frozenset((a, b, a ^ b))
                if P in planes:
                    continue
                planes.add(P)
                valid2 += not (P & bad)
                steps += 1
        counts[k] = (valid1, len(planes), valid2)
        ok &= one_dim_ok and valid2 == 0 and valid1 == 2 ** (n - 1)
    # the brute-force rule 'valid iff K meets no 1+v of a non-partition' is checked against the definition directly
    for k in (1, 2):
        n = 3 * k
        subs = ksubsets(n, k)
        for K in ([1], [3], [7], [1, 2]):
            L, m = kernel_quotient(n, K)
            f = {S: apply(L, S) for S in subs}
            val, st, _ = is_valid_three(k, f, f, f, apply(L, (1 << n) - 1), subs)
            steps += st
            expect = len(K) == 1 and weight(K[0]) % 2 == 1
            ok &= val == expect
    check("Theorem 3 (single map): kernel <a> valid iff |a| odd; no 2-dimensional kernel valid (k = 1, 2)", ok,
          f"(valid 1-dim, 2-dim kernels, valid 2-dim) = {counts}, steps = {steps}")
    timed(t0)

    # 3. Theorem 3, three affine maps
    t0 = time.perf_counter()
    ok, steps, cases, nvalid = True, 0, 0, 0
    rng = LCG(20261008)
    for k in (1, 2):
        n = 3 * k
        ONE = (1 << n) - 1
        subs = ksubsets(n, k)
        EV = [v for v in range(1 << n) if weight(v) % 2 == 0]
        for m in (n - 1, n):
            for trial in range(12):
                kind = trial % 4
                # base linear map L1
                if kind in (0, 1, 2):
                    # a surjection with odd kernel vector (m = n-1) or an injection (m = n)
                    a = 1 | (rng.next(0, (1 << n) - 1) & ~1)
                    while weight(a) % 2 == 0:
                        a ^= 1 << rng.next(1, n - 1) if n > 1 else 1
                    L1, mm = kernel_quotient(n, [a]) if m == n - 1 else (list(1 << i for i in range(n)), n)
                else:
                    L1 = [rng.next(0, (1 << m) - 1) for _ in range(n)]
                    mm = m
                d2, d3 = rng.next(0, (1 << mm) - 1), rng.next(0, (1 << mm) - 1)
                L2 = [c ^ d2 for c in L1]                 # L2(v) = L1(v) + lambda(v) d2 (agrees on E)
                L3 = [c ^ d3 for c in L1]
                if kind == 1:                              # break agreement on E
                    L2 = list(L2)
                    L2[0] ^= 1
                b1, b2, b3 = (rng.next(0, (1 << mm) - 1) for _ in range(3))
                f1 = {S: apply(L1, S) ^ b1 for S in subs}
                f2 = {S: apply(L2, S) ^ b2 for S in subs}
                f3 = {S: apply(L3, S) ^ b3 for S in subs}
                S0 = (1 << k) - 1
                T0 = ((1 << (2 * k)) - 1) ^ S0
                U0 = ONE ^ S0 ^ T0
                x = f1[S0] ^ f2[T0] ^ f3[U0]
                if kind == 2:
                    x ^= 1                                # wrong x
                val, st, _ = is_valid_three(k, f1, f2, f3, x, subs)
                steps += st
                agree = all(apply(L1, v) == apply(L2, v) == apply(L3, v) for v in EV)
                inj = len({apply(L1, v) for v in EV}) == len(EV)
                xok = x == (f1[S0] ^ f2[T0] ^ f3[U0])
                crit = agree and inj and xok
                ok &= val == crit
                cases += 1
                nvalid += val
    check("Theorem 3 (three affine maps): brute-force validity = criterion (i)-(iii) (k = 1, 2; m = 3k-1, 3k)",
          ok and 0 < nvalid < cases, f"{cases} cases, {nvalid} valid, steps = {steps} triples")
    timed(t0)

    # 4. controls
    t0 = time.perf_counter()
    ok, steps, rows = True, 0, []
    for k in (1, 2, 3, 4):
        n = 3 * k
        ONE = (1 << n) - 1
        subs = ksubsets(n, k)
        idx = {}
        for name, K in (("deletion <e_1>", [1]), ("<e_1+e_2>", [3]), ("<1> (R1)", [ONE])):
            L, m = kernel_quotient(n, K)
            f = {S: apply(L, S) for S in subs}
            x = apply(L, ONE)
            inv = {}
            for U in subs:
                inv.setdefault(f[U], []).append(U)
            hits, parts = 0, 0
            for S in subs:
                for T in subs:
                    steps += 1
                    for U in inv.get(x ^ f[S] ^ f[T], []):
                        hits += 1
                        parts += not (S & T) and not (S & U) and not (T & U)
            npart = factorial(n) // factorial(k) ** 3
            valid = hits == parts == npart
            expect = weight(K[0]) % 2 == 1
            ok &= valid == expect
            rows.append((k, name, valid))
        S, T, U, w = lemma_witness(k, 1)
        Lb, _ = kernel_quotient(n, [3])
        fp = (apply(Lb, S) ^ apply(Lb, T) ^ apply(Lb, U)) == apply(Lb, ONE) and (S & T or S & U or T & U)
        ok &= bool(fp) and w == 3
    check("controls: deletion map valid, <e_1+e_2> invalid (explicit false positive), <1> valid iff k odd (k = 1..4)",
          ok, f"{len(rows)} (k, map) cases, steps = {steps} ordered pairs")
    timed(t0)

    # 5. Proposition 5
    t0 = time.perf_counter()
    ok, steps = True, 0
    subs = ksubsets(3, 1)
    full = 7
    for G, add in ((2, lambda a, b: a ^ b), (3, lambda a, b: (a + b) % 3)):
        found = 0
        for vals in product(range(G), repeat=9):
            f1, f2, f3 = vals[0:3], vals[3:6], vals[6:9]
            for x in range(G):
                steps += 1
                good = True
                for i, S in enumerate(subs):
                    for j, T in enumerate(subs):
                        for l, U in enumerate(subs):
                            hit = add(add(f1[i], f2[j]), f3[l]) == x
                            part = (S | T | U) == full
                            if hit != part:
                                good = False
                                break
                        if not good:
                            break
                    if not good:
                        break
                found += good
        ok &= found == 0
    check("Proposition 5, k = 1: no valid triple of arbitrary maps into Z_2 or Z_3 (|G| < 4)", ok,
          f"steps = {steps} (maps, x) cases")
    timed(t0)
    t0 = time.perf_counter()
    ok, steps = True, 0
    for k in (1, 2, 3):
        n = 3 * k
        ONE = (1 << n) - 1
        subs = ksubsets(n, k)
        L, m = kernel_quotient(n, [1])
        f = {S: apply(L, S) for S in subs}
        x = apply(L, ONE)
        A3 = {x ^ f[U] for U in subs}
        N, D = len(subs), comb(2 * k, k)
        inj = len(set(f.values())) == N
        nondisjoint = [(S, T) for S in subs for T in subs if S & T]
        steps += N * N
        avoid = all((f[S] ^ f[T]) not in A3 for S, T in nondisjoint)
        ok &= inj and avoid and len(nondisjoint) == N * N - N * D and N * N - N * D <= (2 ** m - N) * N
    for k in range(1, 61):
        N, D = comb(3 * k, k), comb(2 * k, k)
        B = 2 * N - D
        mmin = (B - 1).bit_length()        # least m with 2^m >= B
        steps += 1
        if k <= 3:
            ok &= mmin == 3 * k - 1
        else:
            ok &= N <= 2 ** (3 * k - 3) and mmin <= 3 * k - 2
    check("Proposition 5: proof ingredients on the deletion map (k = 1..3); 2C(3k,k) - C(2k,k) forces m >= 3k-1 "
          "exactly for k <= 3; C(3k,k) <= 2^(3k-3) for 4 <= k <= 60", ok, f"steps = {steps}")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
