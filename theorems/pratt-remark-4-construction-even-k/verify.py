#!/usr/bin/env python3
"""Verifier for theorems/pratt-remark-4-construction-even-k (see README.md in this folder).

Notation as in the README. A k-subset S of [3k] is a bitmask (bit e-1 <-> element e). For a map f from k-subsets
to a group Z_2^m and x in Z_2^m, a *hit* is an ordered triple (S, T, U) of k-subsets with f(S)+f(T)+f(U) = x;
(f, x) is *valid* if the hits are exactly the ordered partitions of [3k]. The maps tested (m = 3k - 1 unless noted):
    obvious  G = Z_2^(3k), f(S) = 1_S, x = all-ones (the first instantiation printed in the remark);
    deletion f(S) = 1_{S minus {1}} on the coordinates [3k] minus {1}, x = all-ones (the corrected construction);
    R1..R4   the four readings of the printed improved instantiation (README, "Readings").

What it checks, in order:
  1. for each map and 1 <= k <= 5, exhaustively: injectivity, the number of hits (by a set lookup over all
     C(3k,k)^2 ordered pairs (S, T); U is unique because f is injective), the number of partitions that are hits
     (over all (3k)!/(k!)^3 ordered partitions), hence the false positives and the missed partitions; and the
     verdict of the README: obvious and deletion valid for every k; R1 valid exactly for odd k; R2 not valid for
     any k (false positives); R3 and R4 not valid for any k (no partition is a hit);
  2. R1, k = 2 and k = 4: the false-positive triples, listed by a pair loop, are exactly the ordered triples
     (A u B, A u C, B u C) with A, B, C pairwise disjoint (k/2)-sets; their number is (3k)!/(((k/2)!)^3 (3k/2)!)
     = 120 and 83160, all with three distinct sets, so 20 and 13860 unordered; the example ({1,2},{1,3},{2,3});
     the counts of check 1 for R1 at k = 2, 4 agree;
  3. R2: the witness families of the README are false positives for k = 1..5 (all members);
  4. Lemma 1: sum_y (-1)^(y.z) = 2^m [z = 0] for all z in Z_2^m, m = 2, 5, 8; Theorem 1: for all six maps and
     k = 1, 2, sum_y (-1)^(y.x) u_y (x) u_y (x) u_y = 2^m H_f entry by entry, with u_y(S) = (-1)^(y.f(S)) and H_f the
     0/1 tensor of the hits (so 2^(3k-1) P_k for the deletion map, and 2^(3k-1) (P_2 + E_2) with 120 false
     positives in E_2 for R1), consistent with the counts of check 1.
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count; the wall-clock seconds
follow on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):  python theorems/pratt-remark-4-construction-even-k/verify.py
Deterministic and offline, standard library only; well under a minute.
"""
import sys
import time
from itertools import combinations
from math import comb, factorial

KMAX = 5
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


def project(S, missing, n):
    """The vector of S on the coordinates [n] minus {missing}, in increasing order, as a bitmask of n-1 bits."""
    low = S & ((1 << (missing - 1)) - 1)
    high = S >> missing
    return low | (high << (missing - 1))


def make_map(name, k):
    """(f as a dict on k-subsets, x, number of group coordinates)."""
    n = 3 * k
    ones = (1 << (n - 1)) - 1
    subs = ksubsets(n, k)
    has1 = lambda S: S & 1
    if name == "obvious":
        return {S: S for S in subs}, (1 << n) - 1, n
    if name == "deletion":
        return {S: project(S, 1, n) for S in subs}, ones, n - 1
    missing = 1 if name in ("R1", "R3") else n          # R2, R4: the element 3k has no coordinate
    star = 0 if name in ("R1", "R2") else ones          # what the symbol e_missing stands for
    f = {}
    for S in subs:
        vec = project(S, missing, n) ^ (star if S >> (missing - 1) & 1 else 0)   # sum_{s in S} e_s
        f[S] = vec if has1(S) else ones ^ vec                                     # printed case split
    return f, ones, n - 1


def partitions(k):
    """All ordered partitions (S, T, U) of [3k] into k-sets."""
    n = 3 * k
    full = (1 << n) - 1
    pats = list(combinations(range(2 * k), k))
    for S in ksubsets(n, k):
        rest = [e for e in range(n) if not S >> e & 1]
        for pat in pats:
            T = sum(1 << rest[i] for i in pat)
            yield S, T, full ^ S ^ T


def analyse(name, k):
    """(injective, hits, partition hits, number of partitions, steps)."""
    f, x, _ = make_map(name, k)
    vals = list(f.values())
    img = set(vals)
    injective = len(img) == len(vals)
    steps = 0
    hits = 0
    if injective:            # U is determined by f(U): count the pairs (S, T) whose required value is an image
        for S, fS in f.items():
            need = {x ^ fS ^ fT for fT in vals}
            hits += len(need & img)
            steps += len(vals)
    else:                    # count with multiplicities
        mult = {}
        for v in vals:
            mult[v] = mult.get(v, 0) + 1
        for S, fS in f.items():
            hits += sum(mult.get(x ^ fS ^ fT, 0) for fT in vals)
            steps += len(vals)
    phits, nparts = 0, 0
    for S, T, U in partitions(k):
        nparts += 1
        phits += (f[S] ^ f[T] ^ f[U]) == x
    steps += nparts
    return injective, hits, phits, nparts, steps


def main():
    t_start = time.perf_counter()
    verdicts = {
        "obvious": lambda k, st: st["valid"],
        "deletion": lambda k, st: st["valid"],
        "R1": lambda k, st: st["valid"] == (k % 2 == 1) and st["missed"] == 0 and st["inj"],
        "R2": lambda k, st: st["fp"] > 0,
        "R3": lambda k, st: st["phits"] == 0,
        "R4": lambda k, st: st["phits"] == 0,
    }
    summary = {}

    # 1. exhaustive analysis of every map for k = 1..KMAX
    for name in ("obvious", "deletion", "R1", "R2", "R3", "R4"):
        t0 = time.perf_counter()
        ok, steps, rows = True, 0, []
        for k in range(1, KMAX + 1):
            inj, hits, phits, nparts, st = analyse(name, k)
            steps += st
            stats = {"inj": inj, "phits": phits, "fp": hits - phits, "missed": nparts - phits,
                     "valid": inj and hits == phits == nparts}
            ok &= nparts == factorial(3 * k) // factorial(k) ** 3 and verdicts[name](k, stats)
            summary[(name, k)] = stats
            rows.append(f"k={k}: {'injective' if inj else 'not injective'}, {stats['fp']} false positives, "
                        f"{stats['missed']} of {nparts} partitions missed")
        want = {"obvious": "valid for k = 1..5", "deletion": "valid for k = 1..5",
                "R1": "valid exactly for odd k", "R2": "false positives for every k",
                "R3": "no partition is a hit, every k", "R4": "no partition is a hit, every k"}[name]
        check(f"map {name}: {want}", ok, "; ".join(rows) + f"; steps = {steps} lookups and partition tests")
        timed(t0)

    # 2. R1 false positives for k = 2, 4
    t0 = time.perf_counter()
    ok, steps, rows = True, 0, []
    for k in (2, 4):
        n = 3 * k
        f, x, _ = make_map("R1", k)
        inv = {v: S for S, v in f.items()}
        full = (1 << n) - 1
        fps = set()
        for S, fS in f.items():
            for T, fT in f.items():
                steps += 1
                U = inv.get(x ^ fS ^ fT)
                if U is not None and not ((S & T) == 0 and U == full ^ S ^ T):
                    fps.add((S, T, U))
        h = k // 2
        family = set()
        for A in ksubsets(n, h):
            for B in ksubsets(n, h):
                if A & B:
                    continue
                for C in ksubsets(n, h):
                    steps += 1
                    if not (A & C or B & C):
                        family.add((A | B, A | C, B | C))
        formula = factorial(n) // (factorial(h) ** 3 * factorial(n - 3 * h))
        distinct = all(len({S, T, U}) == 3 for S, T, U in fps)
        unordered = len({frozenset(t) for t in fps})
        ok &= fps == family and len(fps) == formula and distinct and unordered == formula // 6
        ok &= summary[("R1", k)]["fp"] == len(fps)
        rows.append(f"k={k}: {len(fps)} ordered, {unordered} unordered (formula {formula})")
    ex = (0b011, 0b101, 0b110)                      # ({1,2}, {1,3}, {2,3})
    f2, x2, _ = make_map("R1", 2)
    ok &= (f2[ex[0]] ^ f2[ex[1]] ^ f2[ex[2]]) == x2
    ok &= [len(r) for r in rows] != [] and rows[0].startswith("k=2: 120 ordered, 20 unordered")
    ok &= rows[1].startswith("k=4: 83160 ordered, 13860 unordered")
    check("R1, k = 2 and 4: false positives = {(A u B, A u C, B u C)}, A, B, C pairwise disjoint (k/2)-sets; "
          "example ({1,2},{1,3},{2,3})", ok, "; ".join(rows) + f"; steps = {steps}")
    timed(t0)

    # 3. R2 witness families
    t0 = time.perf_counter()
    ok, steps, counted = True, 0, 0
    for k in range(1, KMAX + 1):
        n = 3 * k
        f, x, _ = make_map("R2", k)
        full = (1 << n) - 1
        m = 1 << (n - 1)                             # the element 3k (no coordinate in R2)
        if k % 2 == 0:
            h, base, avoid = k // 2, 0, 0
        else:
            h, base, avoid = (k - 1) // 2, m, m | 1  # A, B, C avoid the elements 1 and 3k
        pool = [S for S in ksubsets(n, h) if not S & avoid]
        for A in pool:
            for B in pool:
                if A & B:
                    continue
                for C in pool:
                    steps += 1
                    if A & C or B & C:
                        continue
                    S, T, U = base | A | B, base | A | C, base | B | C
                    part = not (S & T) and (S | T | U) == full and not (S & U) and not (T & U)
                    ok &= (f[S] ^ f[T] ^ f[U]) == x and not part
                    counted += 1
    check("R2: the README's witness triples are false positives (k = 1..5)", ok,
          f"{counted} witness triples, steps = {steps}")
    timed(t0)

    # 4. Lemma 1 and the decompositions
    t0 = time.perf_counter()
    ok, steps = True, 0
    for mdim in (2, 5, 8):
        for z in range(1 << mdim):
            s = sum((-1) ** pc(y & z) for y in range(1 << mdim))
            steps += 1 << mdim
            ok &= s == ((1 << mdim) if z == 0 else 0)
    check("Lemma 1: sum_y (-1)^(y.z) = 2^m [z = 0] for all z in Z_2^m (m = 2, 5, 8)", ok, f"steps = {steps} terms")
    timed(t0)
    t0 = time.perf_counter()
    ok, steps, rows = True, 0, []
    for name in ("obvious", "deletion", "R1", "R2", "R3", "R4"):
        for k in (1, 2):
            n = 3 * k
            f, x, mdim = make_map(name, k)
            subs = ksubsets(n, k)
            full = (1 << n) - 1
            U = {y: [(-1) ** pc(y & f[S]) for S in subs] for y in range(1 << mdim)}
            sign = {y: (-1) ** pc(y & x) for y in U}
            nhits, nparts = 0, 0
            for i, S in enumerate(subs):
                for j, T in enumerate(subs):
                    for l, W in enumerate(subs):
                        val = sum(sign[y] * U[y][i] * U[y][j] * U[y][l] for y in U)
                        steps += len(U)
                        hit = (f[S] ^ f[T] ^ f[W]) == x
                        part = not (S & T) and not (S & W) and not (T & W) and (S | T | W) == full
                        nhits += hit
                        nparts += hit and part
                        ok &= val == (1 << mdim) * hit
            st = summary[(name, k)]
            ok &= nhits - nparts == st["fp"] and nparts == st["phits"]
            rows.append(f"{name} k={k}: {len(subs) ** 3} entries, {1 << mdim} terms, {nhits} hits")
    ok &= summary[("deletion", 1)]["valid"] and summary[("deletion", 2)]["valid"]
    check("Theorem 1: sum_y (-1)^(y.x) u_y (x) u_y (x) u_y = 2^m H_f (H_f = indicator of the hits) entry by entry, "
          "all six maps, k = 1, 2; equal to 2^(3k-1) P_k for deletion", ok, "; ".join(rows) + f"; steps = {steps} "
                                                                                           f"terms")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
