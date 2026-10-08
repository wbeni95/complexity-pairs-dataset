#!/usr/bin/env python3
"""Verifier for theorems/tripartition-tensors-small-cases (see README.md in this folder).

Notation as in the README: T_{a,b,c} with each factor's coordinates the subsets of the right size of [n] in
increasing bitmask order (bit e-1 <-> element e). K_p(PHI; T) is the Koszul-Young flattening of the companion note
tripartition-tensor-p2-border-rank-at-least-26 (rows (U, k), columns (S, j), entry sgn(i,S) T'[i][j][k] when
U = S + {i}), applied to the tensor with its factors in the order given (the first listed factor is projected).

What it checks, in order (exact integer arithmetic; ranks over F_q by Gaussian elimination modulo q):
  1. the SHA-256 of the three data files, before anything else is read from them;
  2. the format of each file: keys, tensor name, "scale": "1/4", the rank, the matrix shapes, entries in {-1,0,1};
  3. the three identities 4 T_{a,b,c} = sum_r a_r (x) b_r (x) c_r over Z, entry by entry
     (96, 250 and 500 entries);
  4. the flattening code on cases the companion note proves: rank-one tensors give C(4,2) = 6 (p = 2), the unit
     tensor <5> gives 5 * 6 = 30 (p = 2), for every prime q <= 31;
  5. T_{1,1,2}: K_2(PHI; T) with factor 3 projected by PHI = [I_5 | 1] (a 40 x 40 matrix) has rank 40 modulo every
     prime q <= 31 except q = 5, where it is 39; every value exceeds 36 = 6 * 6, so border rank >= 7;
  6. T_{1,2,2}: K_2(I_5; T) with factor 1 unprojected (a 100 x 100 matrix) has rank 76 modulo every prime q <= 31;
     76 > 72 = 12 * 6, so border rank >= 13;
  7. T_{1,1,3}: the rows of its flattening along factor 3 (10 x 25) are nonzero with pairwise disjoint supports
     (rank 10 over every field), and the rank modulo every prime q <= 31 is 10;
  8. the two upper bounds that also follow from the companion note partial-fourier-bound-tripartition-tensors:
     1 + C(4, 2) = 7 and 1 + C(5, 2) = 11.
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count; the wall-clock seconds
follow on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):  python theorems/tripartition-tensors-small-cases/verify.py
Deterministic and offline, standard library only; about a second.
"""
import hashlib
import json
import sys
import time
from itertools import combinations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
FILES = {
    (1, 1, 2): ("T112_rank7.json", "3abe699cf9167c78c1e32172343ccd18cc61fe0d0d26c9df672792afb1b99eda", 7),
    (1, 1, 3): ("T113_rank11.json", "5d4274b46b0f4182362ecaa5b005d8fc46b3d63a3d7ff7dc17a99a0b5af8f011", 11),
    (1, 2, 2): ("T122_rank14.json", "2a30f2bdbfbb4ea99bd8d28f6c93da0016a0dfb905300ab5c479a6d0d692b635", 14),
}
SCALE = 4
PHI_112 = [[1, 0, 0, 0, 0, 1], [0, 1, 0, 0, 0, 1], [0, 0, 1, 0, 0, 1], [0, 0, 0, 1, 0, 1], [0, 0, 0, 0, 1, 1]]
EXPECTED_112 = {q: (39 if q == 5 else 40) for q in PRIMES}
EXPECTED_122 = {q: 76 for q in PRIMES}
BOUND_112, BOUND_122, BOUND_113 = 7, 13, 10

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


def tripartition_tensor(a, b, c):
    n = a + b + c
    SA, SB, SC = ksubsets(n, a), ksubsets(n, b), ksubsets(n, c)
    ic = {m: i for i, m in enumerate(SC)}
    full = (1 << n) - 1
    T = {}
    for i, x in enumerate(SA):
        for j, y in enumerate(SB):
            if not x & y:
                T[(i, j, ic[full ^ x ^ y])] = 1
    return T, (len(SA), len(SB), len(SC)), (SA, SB, SC)


def permute(T, dims, order):
    """The tensor with its factors listed in the given order (order[r] = original factor in position r)."""
    return {tuple(key[o] for o in order): v for key, v in T.items()}, tuple(dims[o] for o in order)


def koszul_matrix(T, dims, phi, p):
    _, db, dc = dims
    k = 2 * p + 1
    proj = {}
    for (a, j, kk), v in T.items():
        for i in range(k):
            w = phi[i][a] * v
            if w:
                proj[(i, j, kk)] = proj.get((i, j, kk), 0) + w
    by_i = {}
    for (i, j, kk), v in proj.items():
        if v:
            by_i.setdefault(i, []).append((j, kk, v))
    src = list(combinations(range(k), p))
    dst = {U: n for n, U in enumerate(combinations(range(k), p + 1))}
    M = [[0] * (len(src) * db) for _ in range(len(dst) * dc)]
    entries = 0
    for si, S in enumerate(src):
        for i in range(k):
            if i in S:
                continue
            sign = -1 if sum(1 for s in S if s < i) % 2 else 1
            ui = dst[tuple(sorted(S + (i,)))]
            for j, kk, v in by_i.get(i, []):
                M[ui * dc + kk][si * db + j] += sign * v
                entries += 1
    return M, entries


def rank_mod(M, q):
    rows = [[x % q for x in r] for r in M]
    rows = [r for r in rows if any(r)]
    ncols = len(M[0]) if M else 0
    rank, ops = 0, 0
    for c in range(ncols):
        piv = next((i for i in range(rank, len(rows)) if rows[i][c]), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        pr = rows[rank]
        inv = pow(pr[c], q - 2, q)
        tail = [(x * inv) % q for x in pr[c:]]
        ops += len(tail)
        for i in range(rank + 1, len(rows)):
            r = rows[i]
            f = r[c]
            if f:
                rows[i] = r[:c] + [(x - f * y) % q for x, y in zip(r[c:], tail)]
                ops += len(tail)
        rank += 1
    return rank, ops


def identity(m):
    return [[int(i == j) for j in range(m)] for i in range(m)]


def main():
    t_start = time.perf_counter()

    # 1. SHA-256
    raw = {}
    for abc, (name, sha, _) in FILES.items():
        t0 = time.perf_counter()
        data = (HERE / "data" / name).read_bytes()
        raw[abc] = data
        check(f"SHA-256 of data/{name}", hashlib.sha256(data).hexdigest() == sha, f"{len(data)} bytes, steps = 1 hash")
        timed(t0)
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1

    # 2. format and 3. identities
    for (a, b, c), (name, _, rank) in FILES.items():
        t0 = time.perf_counter()
        D = json.loads(raw[(a, b, c)].decode("utf-8"))
        T, dims, (SA, SB, SC) = tripartition_tensor(a, b, c)
        A, B, C = D.get("A"), D.get("B"), D.get("C")
        fmt = (set(D) == {"tensor", "scale", "rank", "A", "B", "C"} and D["tensor"] == f"T_{a},{b},{c}"
               and D["scale"] == f"1/{SCALE}" and D["rank"] == rank
               and all(isinstance(M, list) and len(M) == dm and all(isinstance(r, list) and len(r) == rank for r in M)
                       for M, dm in zip((A, B, C), dims)))
        fmt = fmt and all(type(x) is int and x in (-1, 0, 1) for M in (A, B, C) for r in M for x in r)
        check(f"format of data/{name}: T_{{{a},{b},{c}}}, scale 1/4, {rank} terms, shapes {dims[0]}/{dims[1]}/{dims[2]} "
              f"x {rank}, entries in {{-1,0,1}}", fmt, f"steps = {rank * sum(dims)} entry tests")
        timed(t0)
        if not fmt:
            continue
        t0 = time.perf_counter()
        bad, steps = 0, 0
        full = (1 << (a + b + c)) - 1
        for i, x in enumerate(SA):
            for j, y in enumerate(SB):
                AB = [A[i][r] * B[j][r] for r in range(rank)]
                for k, z in enumerate(SC):
                    v = sum(AB[r] * C[k][r] for r in range(rank))
                    steps += 2 * rank
                    part = not (x & y) and not (x & z) and not (y & z) and (x | y | z) == full
                    bad += v != SCALE * part
        check(f"identity 4*T_{{{a},{b},{c}}} = sum of the {rank} terms over Z, every entry", bad == 0,
              f"{dims[0] * dims[1] * dims[2]} entries, {len(T)} nonzero entries of the tensor, {bad} mismatches, "
              f"steps = {steps} integer products")
        timed(t0)

    # 4. flattening code on proved cases
    t0 = time.perf_counter()
    ok, steps, cases = True, 0, 0
    for alpha, beta, gamma in (([1, 1, 1, 1, 1], [1, 0, 2, -1], [0, 1, 3]), ([0, 0, 0, 0, 1], [1], [1, -1])):
        R1 = {(i, j, k): x * y * z for i, x in enumerate(alpha) for j, y in enumerate(beta)
              for k, z in enumerate(gamma) if x * y * z}
        K, ent = koszul_matrix(R1, (5, len(beta), len(gamma)), identity(5), 2)
        steps += ent
        for q in PRIMES:
            r, ops = rank_mod(K, q)
            steps += ops
            ok &= r == comb(4, 2)
            cases += 1
    unit = {(i, i, i): 1 for i in range(5)}
    K, ent = koszul_matrix(unit, (5, 5, 5), identity(5), 2)
    steps += ent
    for q in PRIMES:
        r, ops = rank_mod(K, q)
        steps += ops
        ok &= r == 30
        cases += 1
    check("flattening code: rank-one tensors give C(4,2) = 6 and <5> gives 30 (p = 2)", ok,
          f"{cases} (tensor, prime) cases, steps = {steps}")
    timed(t0)

    # 5. T_{1,1,2} >= 7
    t0 = time.perf_counter()
    T, dims, _ = tripartition_tensor(1, 1, 2)
    Tp, dp = permute(T, dims, (2, 0, 1))
    K, ent = koszul_matrix(Tp, dp, PHI_112, 2)
    ok, steps, got = (len(K), len(K[0])) == (40, 40), ent, {}
    for q in PRIMES:
        r, ops = rank_mod(K, q)
        steps += ops
        got[q] = r
        ok &= r == EXPECTED_112[q] and r > (BOUND_112 - 1) * comb(4, 2) and -(-r // comb(4, 2)) == BOUND_112
    check("T_{1,1,2}: K_2([I_5|1]; T) (factor 3 projected, 40 x 40) has rank 40 mod q, 39 mod 5; > 36, so border "
          "rank >= 7", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 6. T_{1,2,2} >= 13
    t0 = time.perf_counter()
    T, dims, _ = tripartition_tensor(1, 2, 2)
    K, ent = koszul_matrix(T, dims, identity(5), 2)
    ok, steps, got = (len(K), len(K[0])) == (100, 100), ent, {}
    for q in PRIMES:
        r, ops = rank_mod(K, q)
        steps += ops
        got[q] = r
        ok &= r == EXPECTED_122[q] and r > (BOUND_122 - 1) * comb(4, 2) and -(-r // comb(4, 2)) == BOUND_122
    check("T_{1,2,2}: K_2(I_5; T) (factor 1, 100 x 100) has rank 76 mod every prime q <= 31; > 72, so border "
          "rank >= 13", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 7. T_{1,1,3} >= 10 (flattening along factor 3)
    t0 = time.perf_counter()
    T, dims, _ = tripartition_tensor(1, 1, 3)
    rows = [[0] * (dims[0] * dims[1]) for _ in range(dims[2])]
    for (i, j, k), v in T.items():
        rows[k][i * dims[1] + j] = v
    supports = [{c for c, x in enumerate(r) if x} for r in rows]
    disjoint = all(supports[u] and not (supports[u] & supports[w])
                   for u in range(len(rows)) for w in range(u + 1, len(rows)))
    steps, got = len(rows) * len(rows[0]), {}
    ok = disjoint and len(rows) == BOUND_113
    for q in PRIMES:
        r, ops = rank_mod(rows, q)
        steps += ops
        got[q] = r
        ok &= r == BOUND_113
    check("T_{1,1,3}: the 10 rows of the flattening along factor 3 (10 x 25) are nonzero with disjoint supports; "
          "rank 10 mod every prime q <= 31", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 8. consistency with the partial Fourier bound
    t0 = time.perf_counter()
    check("upper bounds 7 and 11 also equal 1 + C(c+2, 2) for c = 2, 3 (companion note, Corollary 2)",
          1 + comb(4, 2) == FILES[(1, 1, 2)][2] and 1 + comb(5, 2) == FILES[(1, 1, 3)][2], "steps = 2 comparisons")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.3f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
