#!/usr/bin/env python3
"""Verifier for theorems/tripartition-tensor-p2-border-rank-at-least-26 (see README.md in this folder).

Notation as in the README: P_2 is the 15 x 15 x 15 tensor of ordered partitions of {1..6} into three 2-sets, with
the coordinates of the companion note tripartition-tensor-p2-rank-at-most-29 (2-subsets in increasing bitmask
order). For a tensor T with first factor of dimension m, a (2p+1) x m integer matrix PHI and p >= 1, K_p(PHI; T) is
the Koszul-Young flattening matrix of (PHI x 1 x 1) T, with rows (U, k) and columns (S, j):
    K[(U,k),(S,j)] = sgn(i,S) * T'[i][j][k]  if U = S + {i}, i not in S,   else 0,
where T'[i][j][k] = sum_a PHI[i][a] T[a][j][k] and sgn(i,S) = (-1)^#{s in S : s < i}.

What it checks, in order (exact integer arithmetic; ranks over F_q by Gaussian elimination modulo q):
  1. the projection PHI printed in the README equals the constant PHI below; no column of PHI is zero;
  2. the rank routines: on 45 fixed integer matrices (planted ranks 0..8, sizes up to 9 x 11) the rank over F_q
     equals the exact rank over Q (Fraction elimination) for q = 2^31 - 1, and is <= it for every prime q <= 31;
     the 2 x 2 matrix diag(q, 1) has rank 2 over Q and 1 over F_q (the inequality can be strict);
  3. Lemma 2 (rank-one tensors): for p = 1, 2, 3 and fixed integer vectors with a coordinate equal to 1, the
     flattening of alpha (x) beta (x) gamma has rank exactly C(2p, p) over F_q for every prime q <= 31;
  4. Example (unit tensors): <2p+1> with PHI = identity (p = 1, 2, 3) has flattening rank (2p+1) C(2p,p), and
     <15> with the projection PHI has rank 15 * 20 = 300 (p = 3), over F_q for every prime q <= 31;
  5. Lemma 3 on real data: with the 29-term identity of the companion note (its data file, SHA-256 checked),
     K_3(PHI; 4 P_2) = sum_r K_3(PHI; a_r (x) b_r (x) c_r) entry by entry, and the partial sums of the first
     1, 3 and 10 terms have rank <= 20, 60, 200 over F_3;
  6. the theorem's computation: P_2 has 90 nonzero entries; K_3(PHI; P_2) is a 525 x 525 integer matrix, and its
     rank over F_q is 502 for q = 2 and 504 for every prime 3 <= q <= 31; each is > 500 = 25 * C(6, 3), so the
     bound ceil(rank / 20) = 26.
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count (field operations in the
eliminations, or entries built); the wall-clock seconds follow on a separate line. Exit code 0 only if every check
passes.

Usage (from the repository root):
    python theorems/tripartition-tensor-p2-border-rank-at-least-26/verify.py
Deterministic and offline, standard library only; a few seconds.
"""
import hashlib
import json
import re
import sys
import time
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMPANION = HERE.parent / "tripartition-tensor-p2-rank-at-most-29" / "data" / "P2_rank29.json"
COMPANION_SHA256 = "3a46395da0783d3b315509261ea69fb4bb511ce2418a05b432e4bd0bfea32351"
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
BIG = 2 ** 31 - 1
P = 3                       # Koszul-Young parameter: dim A' = 2P + 1 = 7, divisor C(2P, P) = 20
BOUND = 26                  # the claimed lower bound on the border rank of P_2
EXPECTED = {q: (502 if q == 2 else 504) for q in PRIMES}
# the projection A -> A' (7 x 15), columns indexed by the 15 coordinates of P_2
PHI = [
    [0, 1, 0, -1, 0, -1, 1, 1, 1, 0, 1, 0, 0, -1, 1],
    [-1, 0, -1, -1, 0, -1, 0, -1, 0, -1, 1, 1, 1, 0, -1],
    [0, 0, -1, 0, -1, 0, 1, 0, -1, 0, -1, 1, 1, 1, 1],
    [-1, -1, -1, -1, -1, 0, -1, 0, 1, -1, 1, -1, -1, 1, -1],
    [0, 0, 0, 0, -1, -1, 1, 0, -1, 1, 1, -1, -1, -1, -1],
    [0, 0, -1, 1, 1, 1, 0, -1, -1, -1, 1, 1, -1, 0, 1],
    [1, 1, 1, 1, -1, -1, 0, 0, 1, -1, -1, 1, 1, -1, 0],
]

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)")


# ------------------------------------------------------------------------------------------------ tensors
def ksubsets(n, k):
    """k-subsets of {1..n} as bitmasks (bit e-1 <-> element e) in increasing numeric order."""
    return sorted(sum(1 << (e - 1) for e in c) for c in combinations(range(1, n + 1), k))


def tripartition_tensor(a, b, c):
    """T_{a,b,c} as {(i, j, k): 1} with the coordinates in increasing bitmask order, and its dimensions."""
    n = a + b + c
    SA, SB, SC = ksubsets(n, a), ksubsets(n, b), ksubsets(n, c)
    ic = {m: i for i, m in enumerate(SC)}
    full = (1 << n) - 1
    T = {}
    for i, x in enumerate(SA):
        for j, y in enumerate(SB):
            if not x & y:
                T[(i, j, ic[full ^ x ^ y])] = 1
    return T, (len(SA), len(SB), len(SC))


def rank_one(alpha, beta, gamma):
    return {(i, j, k): x * y * z for i, x in enumerate(alpha) for j, y in enumerate(beta)
            for k, z in enumerate(gamma) if x * y * z}


def koszul_matrix(T, dims, phi, p):
    """The Koszul-Young flattening K_p(phi; T) as a dense list of integer rows; also the number of entries set."""
    _, db, dc = dims
    k = 2 * p + 1
    assert len(phi) == k
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


# ------------------------------------------------------------------------------------------------ ranks
def rank_mod(M, q):
    """Rank over F_q of an integer matrix (Gaussian elimination modulo q). Returns (rank, field operations)."""
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


def rank_exact(M):
    """Rank over Q (Fraction Gaussian elimination)."""
    rows = [[Fraction(x) for x in r] for r in M]
    ncols = len(M[0]) if M else 0
    rank = 0
    for c in range(ncols):
        piv = next((i for i in range(rank, len(rows)) if rows[i][c] != 0), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        pr = rows[rank]
        for i in range(rank + 1, len(rows)):
            f = rows[i][c] / pr[c]
            if f:
                rows[i] = [x - f * y for x, y in zip(rows[i], pr)]
        rank += 1
    return rank


class LCG:
    """A fixed linear congruential generator (deterministic test matrices, independent of PYTHONHASHSEED)."""

    def __init__(self, seed):
        self.s = seed

    def next(self, lo, hi):
        self.s = (6364136223846793005 * self.s + 1442695040888963407) % 2 ** 64
        return lo + (self.s >> 33) % (hi - lo + 1)


def main():
    t_start = time.perf_counter()

    # 1. PHI as printed in the README
    t0 = time.perf_counter()
    text = (HERE / "README.md").read_text(encoding="utf-8")
    block = text.split("<!-- PHI -->")[1] if text.count("<!-- PHI -->") == 2 else ""
    printed = [[int(t) for t in re.findall(r"-?\d+", line)] for line in block.splitlines() if "[" in line]
    zero_cols = [a for a in range(15) if all(PHI[i][a] == 0 for i in range(7))]
    check("PHI: the 7 x 15 projection printed in the README equals the one used here; no zero column",
          printed == PHI and not zero_cols, f"{len(printed)} rows compared, zero columns {zero_cols}, steps = 105 "
                                            f"entries")
    timed(t0)

    # 2. rank routines
    t0 = time.perf_counter()
    rng = LCG(20261008)
    ok_big, ok_le, steps, tested = True, True, 0, 0
    for planted in range(9):
        for rep in range(5):
            nr, nc = rng.next(planted + 1, 9), rng.next(planted + 1, 11)
            X = [[rng.next(-3, 3) for _ in range(planted)] for _ in range(nr)]
            Y = [[rng.next(-3, 3) for _ in range(nc)] for _ in range(planted)]
            M = [[sum(X[i][t] * Y[t][j] for t in range(planted)) for j in range(nc)] for i in range(nr)]
            rq = rank_exact(M)
            rb, ops = rank_mod(M, BIG)
            steps += ops
            ok_big &= rb == rq and rq <= planted
            for q in PRIMES:
                rp, ops = rank_mod(M, q)
                steps += ops
                ok_le &= rp <= rq
            tested += 1
    strict = all(rank_exact([[q, 0], [0, 1]]) == 2 and rank_mod([[q, 0], [0, 1]], q)[0] == 1 for q in PRIMES)
    check("rank routines: rank over F_q = rank over Q for q = 2^31-1 and <= it for every prime q <= 31, on "
          "fixed planted-rank matrices; diag(q,1) has rank 2 over Q and 1 over F_q",
          ok_big and ok_le and strict, f"{tested} matrices x 12 primes, steps = {steps} field operations")
    timed(t0)

    # 3. Lemma 2: rank-one tensors give rank C(2p, p)
    t0 = time.perf_counter()
    ok, steps, cases = True, 0, 0
    for p in (1, 2, 3):
        m = 2 * p + 1
        for alpha, beta, gamma in (([1] * m, [1, 0, 2, -1], [0, 1, 3, 1, -2]),
                                   ([1, -1] + [0] * (m - 2), [2, 1, 0, 0, 1], [1, 4, -1]),
                                   ([0] * (m - 1) + [1], [1], [1, 1])):
            T = rank_one(alpha, beta, gamma)
            K, ent = koszul_matrix(T, (m, len(beta), len(gamma)), [[int(i == a) for a in range(m)] for i in range(m)], p)
            steps += ent
            for q in PRIMES:
                r, ops = rank_mod(K, q)
                steps += ops
                ok &= r == comb(2 * p, p)
                cases += 1
    check("Lemma 2: the flattening of a rank-one tensor has rank C(2p,p) (p = 1, 2, 3)", ok,
          f"{cases} (tensor, prime) cases, steps = {steps}")
    timed(t0)

    # 4. Example: unit tensors
    t0 = time.perf_counter()
    ok, steps, cases = True, 0, 0
    for p in (1, 2, 3):
        m = 2 * p + 1
        unit = {(i, i, i): 1 for i in range(m)}
        K, ent = koszul_matrix(unit, (m, m, m), [[int(i == a) for a in range(m)] for i in range(m)], p)
        steps += ent
        for q in PRIMES:
            r, ops = rank_mod(K, q)
            steps += ops
            ok &= r == m * comb(2 * p, p)
            cases += 1
    unit15 = {(i, i, i): 1 for i in range(15)}
    K, ent = koszul_matrix(unit15, (15, 15, 15), PHI, P)
    steps += ent
    for q in PRIMES:
        r, ops = rank_mod(K, q)
        steps += ops
        ok &= r == 15 * comb(2 * P, P)
        cases += 1
    check("Example: unit tensors <2p+1> (identity projection, p = 1, 2, 3) have rank (2p+1)C(2p,p); <15> with PHI "
          "(p = 3) has rank 300, bound 15", ok, f"{cases} (tensor, prime) cases, steps = {steps}")
    timed(t0)

    # 5. Lemma 3 on the companion decomposition
    t0 = time.perf_counter()
    raw = COMPANION.read_bytes()
    sha_ok = hashlib.sha256(raw).hexdigest() == COMPANION_SHA256
    check("SHA-256 of the companion note's data/P2_rank29.json", sha_ok, f"{len(raw)} bytes, steps = 1 hash")
    timed(t0)
    t0 = time.perf_counter()
    P2, dims = tripartition_tensor(2, 2, 2)
    if sha_ok:
        D = json.loads(raw.decode("utf-8"))
        A, B, C = D["A"], D["B"], D["C"]
        terms = [rank_one([A[i][r] for i in range(15)], [B[j][r] for j in range(15)], [C[k][r] for k in range(15)])
                 for r in range(29)]
        K4, steps = koszul_matrix({key: 4 * v for key, v in P2.items()}, dims, PHI, P)
        acc = [[0] * len(K4[0]) for _ in K4]
        part_ok = True
        for r, Tr in enumerate(terms):
            Kr, ent = koszul_matrix(Tr, dims, PHI, P)
            steps += ent
            for u, row in enumerate(Kr):
                accu = acc[u]
                for v, x in enumerate(row):
                    if x:
                        accu[v] += x
            if r + 1 in (1, 3, 10):
                rk, ops = rank_mod(acc, 3)
                steps += ops
                part_ok &= rk <= comb(2 * P, P) * (r + 1)
        check("Lemma 3 on data: K_3(PHI; 4 P_2) = sum of the 29 term flattenings entry by entry; partial sums of "
              "1, 3, 10 terms have rank <= 20, 60, 200 over F_3", acc == K4 and part_ok,
              f"525 x 525 = 275625 entries compared, steps = {steps}")
    timed(t0)

    # 6. the theorem's computation
    t0 = time.perf_counter()
    K, ent = koszul_matrix(P2, dims, PHI, P)
    shape = (len(K), len(K[0]))
    check("P_2 and its flattening: 90 nonzero entries; K_3(PHI; P_2) is 525 x 525",
          len(P2) == 90 and dims == (15, 15, 15) and shape == (525, 525), f"{ent} entries set, steps = {ent}")
    timed(t0)
    divisor = comb(2 * P, P)
    for q in PRIMES:
        t0 = time.perf_counter()
        r, ops = rank_mod(K, q)
        bound = -(-r // divisor)
        check(f"rank over F_{q} of K_3(PHI; P_2) = {EXPECTED[q]} > {(BOUND - 1) * divisor}, so border rank >= "
              f"ceil(rank/{divisor}) = {BOUND}", r == EXPECTED[q] and r > (BOUND - 1) * divisor and bound == BOUND,
              f"rank {r} of a 525 x 525 matrix, bound {bound}, steps = {ops} field operations")
        timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
