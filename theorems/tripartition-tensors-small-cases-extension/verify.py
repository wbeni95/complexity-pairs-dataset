#!/usr/bin/env python3
"""Verifier for theorems/tripartition-tensors-small-cases-extension (see README.md in this folder).

Notation as in the README and in the public notes tripartition-tensors-small-cases and
tripartition-tensor-p2-border-rank-at-least-26: T_{a,b,c} with each factor's coordinates the subsets of the right
size of [n] in increasing bitmask order (bit e-1 <-> element e); K_p(PHI; T) the Koszul-Young flattening of
(PHI x 1 x 1) T (rows (U, k), columns (S, j), entry sgn(i,S) T'[i][j][k] when U = S + {i}), applied to the tensor with
its factors in the stated order (the first listed factor is projected). Row (U, k) is row u * n_3 + k and column
(S, j) is column s * n_2 + j, U and S in lexicographic order.

Rank routines (standard library): an exclusive-or basis over F_2 (rows as bitmasks), and an elimination over F_q on
rows packed into Python integers (one 32-bit field per column, entries kept nonnegative; at most one elimination per
basis row, so no field exceeds (columns) (q-1)^2 + q - 1 < 2^32, which is asserted).

What it checks, in order:
  1. the projections printed in the README equal the constants below;
  2. the rank routines on 45 fixed planted-rank integer matrices against dense elimination modulo every prime q <= 31,
     dense elimination modulo 2^31 - 1 against the exact rank over Q, and diag(q, 1) (rank 2 over Q, 1 modulo q);
  3. the flattening code on the public values: T_{1,1,2} with [I_5 | 1] (factor 3 projected, p = 2) has rank 40
     modulo every prime q <= 31 except 39 modulo 5; T_{1,2,2} with I_5 (p = 2) has rank 76; rank-one tensors give
     C(2p, p) and unit tensors give (dimension) * C(2p, p) for the projections used here;
  4. the upper bounds: for T_{1,2,3}, T_{1,2,4}, T_{1,3,3}, T_{2,2,3} and T_{1,1,c} (1 <= c <= 12), a decomposition of
     character type (Theorem 1 of partial-fourier-bound-tripartition-tensors) with 26, 42, 56, 57 and C(c+2,2) + 1
     terms, solved over Q, is checked entry by entry; every coefficient has a power of 2 as denominator, so the
     identity holds over Z[1/2] and hence over every field of characteristic != 2;
  5. T_{1,2,3} >= 21: K_2 with factor 1 projected by [I_5 | 1] (200 x 150) has rank 121 modulo every prime q <= 31;
  6. T_{1,3,3} >= 42: K_2 with factor 1 projected by the 5 x 7 matrix of the README (350 x 350) has rank 248 modulo
     every odd prime q <= 31 and 242 modulo 2 (no claim in characteristic 2);
  7. T_{2,2,3} >= 39: K_5 with factor 3 projected by the 11 x 35 matrix of the README (9702 x 9702) has rank 9646
     modulo 2, 9700 modulo 11, 9702 modulo every other prime q <= 31, all > 9576 = 38 * 252; and a fixed sum of
     38 rank-one tensors of the same format gives rank 9552 modulo 2 and 9576 modulo 3 (<= 38 * 252: not certified);
  8. T_{1,2,4} >= 35 and T_{1,1,c} >= C(c+2,2) (1 <= c <= 20): the rows of the flattening along factor 3 are nonzero
     with pairwise disjoint supports, and the rank modulo every prime q <= 31 equals the number of rows.
  9. rank >= C(n,c) + 1 (Theorem part 3): the exchange step of the proof holds for every disjoint pair in
     (1,2,3), (1,2,4), (1,3,3), (2,2,3) and (1,1,c), c <= 8; and, as a sanity check of the conclusion, no nonzero
     slice of T_{1,1,c} has rank one, exhaustively over F_2 for c <= 4 and over F_3 for c <= 2.
With --quick, check 7 uses q = 2 and q = 3 only. Every check prints a [PASS]/[FAIL] line with what it covered and an
exact step count; the wall-clock seconds follow on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):
    python theorems/tripartition-tensors-small-cases-extension/verify.py            (about 5 minutes)
    python theorems/tripartition-tensors-small-cases-extension/verify.py --quick    (about a minute)
Deterministic and offline, standard library only. Memory: about 0.5 GB.
"""
import re
import sys
import time
from array import array
from fractions import Fraction
from itertools import combinations, product
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
BIG = 2 ** 31 - 1
W = 32
assert array('I').itemsize == 4

PHI_123 = [[1, 0, 0, 0, 0, 1], [0, 1, 0, 0, 0, 1], [0, 0, 1, 0, 0, 1], [0, 0, 0, 1, 0, 1], [0, 0, 0, 0, 1, 1]]
PHI_133 = [[1, 0, 0, 0, 0, 1, 1], [0, 1, 0, 0, 0, 1, -1], [0, 0, 1, 0, 0, 1, 1], [0, 0, 0, 1, 0, 1, -1],
           [0, 0, 0, 0, 1, 1, 1]]
# the 11 x 35 projection for T_{2,2,3}, written by columns: PHI_223_T[a] is column a (the a-th 3-subset of [7])
PHI_223_T = [
    [ 1,  1, -1, -1,  0,  0,  1,  1, -1,  0, -1],
    [ 0,  0,  1,  0,  1,  0,  1, -1, -1,  1, -1],
    [ 1,  1,  0,  1,  1,  1,  0,  0,  1,  0,  1],
    [-1,  0,  0,  1,  1, -1, -1, -1, -1, -1,  1],
    [-1,  1,  1,  0,  0,  0,  1,  1,  0, -1,  1],
    [ 0,  1,  0,  0, -1,  0, -1, -1,  1,  0,  1],
    [ 0,  0,  0,  0, -1, -1, -1,  1,  1,  0, -1],
    [-1, -1, -1, -1, -1, -1,  0,  0, -1,  0,  0],
    [ 1,  0,  0,  0,  0,  0,  0, -1, -1,  0,  1],
    [ 1,  1,  0,  1,  1,  1,  1,  0, -1,  0, -1],
    [-1,  0,  0,  0, -1,  1,  0,  0,  0,  0,  1],
    [ 1,  0,  1,  1,  1,  0,  0,  1,  0,  1, -1],
    [-1,  0,  1, -1, -1,  1,  1, -1,  1,  0,  0],
    [ 0,  0,  1, -1, -1,  0,  0,  1,  1,  1,  1],
    [ 0,  1,  1,  0, -1, -1,  0, -1,  1,  0,  1],
    [ 1,  1, -1, -1, -1,  0, -1,  0,  0, -1,  1],
    [ 0,  0,  1, -1,  0, -1, -1,  1, -1,  1, -1],
    [ 0,  1, -1,  1, -1,  0,  0,  0,  1,  0,  0],
    [-1,  1,  1,  1,  0,  0,  1,  0,  0,  0,  0],
    [-1, -1,  0, -1, -1,  1,  1,  0,  0,  0,  1],
    [ 1,  1,  1,  0,  0,  1,  0,  1,  1,  1,  0],
    [ 1,  1,  0, -1, -1, -1, -1,  1, -1, -1,  0],
    [-1,  1, -1,  1,  1,  1,  0,  0,  0,  0,  1],
    [-1,  0,  1,  0,  0,  1,  0,  1,  0,  1, -1],
    [-1,  0, -1,  0, -1,  0,  0,  1,  1,  1, -1],
    [ 1,  1,  1,  0,  1,  1,  1, -1, -1,  0,  0],
    [-1,  1,  1,  0, -1,  0, -1,  1, -1,  0, -1],
    [ 0, -1,  1,  0,  0,  1,  0,  1,  0, -1,  0],
    [-1, -1,  1,  1,  1,  0,  1,  1, -1, -1, -1],
    [ 0, -1,  1, -1,  0, -1,  1, -1, -1, -1, -1],
    [ 0, -1, -1,  1,  0,  0,  0,  0,  1, -1, -1],
    [-1,  1,  0,  1,  1,  1,  0,  1, -1,  0,  1],
    [ 1,  0, -1,  1,  1,  0,  1,  1, -1,  0, -1],
    [ 0,  1, -1,  1,  1,  0,  1, -1,  0,  1,  1],
    [ 0, -1,  1,  0,  0,  1,  1, -1,  0, -1, -1],
]
PHI_223 = [[PHI_223_T[a][i] for a in range(35)] for i in range(11)]
PHI_112 = PHI_123     # [I_5 | 1], as in the public note

EXP_123 = {q: 121 for q in PRIMES}
EXP_133 = {q: (242 if q == 2 else 248) for q in PRIMES}
EXP_223 = {q: 9702 for q in PRIMES}
EXP_223[2], EXP_223[11] = 9646, 9700

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)", flush=True)


class LCG:
    """A fixed linear congruential generator (deterministic test data)."""

    def __init__(self, seed):
        self.s = seed

    def next(self, lo, hi):
        self.s = (6364136223846793005 * self.s + 1442695040888963407) % 2 ** 64
        return lo + (self.s >> 33) % (hi - lo + 1)


# ------------------------------------------------------------------------------------------------ tensors
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
    return T, (len(SA), len(SB), len(SC))


def permute(T, dims, order):
    """The tensor with its factors listed in the given order (order[r] = original factor in position r)."""
    return {tuple(key[o] for o in order): v for key, v in T.items()}, tuple(dims[o] for o in order)


def project(T, dims, phi):
    m = len(phi)
    _, n2, n3 = dims
    Tp = [[[0] * n2 for _ in range(n3)] for _ in range(m)]
    for (a, j, k), v in T.items():
        for i in range(m):
            if phi[i][a]:
                Tp[i][k][j] += phi[i][a] * v
    return Tp


def project_rank_ones(phi, terms, n2, n3):
    m = len(phi)
    Tp = [[[0] * n2 for _ in range(n3)] for _ in range(m)]
    for alpha, beta, gamma in terms:
        pa = [sum(phi[i][a] * alpha[a] for a in range(len(alpha))) for i in range(m)]
        for i in range(m):
            if pa[i]:
                for k in range(n3):
                    f = pa[i] * gamma[k]
                    if f:
                        row = Tp[i][k]
                        for j in range(n2):
                            if beta[j]:
                                row[j] += f * beta[j]
    return Tp


def flattening_rows(Tp, p, q):
    """Rows of K_p of Tp: bitmasks if q == 2, else packed 32-bit fields with entries in [0, q)."""
    m = 2 * p + 1
    assert len(Tp) == m
    n3, n2 = len(Tp[0]), len(Tp[0][0])
    src = list(combinations(range(m), p))
    sidx = {S: n for n, S in enumerate(src)}
    cache = {}

    def block(i, k, sign):
        key = (i, k, sign)
        if key not in cache:
            vals = Tp[i][k]
            if q == 2:
                cache[key] = sum(1 << j for j, v in enumerate(vals) if v % 2)
            else:
                cache[key] = int.from_bytes(array('I', [(sign * v) % q for v in vals]).tobytes(), 'little')
        return cache[key]

    rows, placed = [], 0
    for U in combinations(range(m), p + 1):
        parts = []
        for i in U:
            S = tuple(e for e in U if e != i)
            sign = -1 if sum(1 for s in S if s < i) % 2 else 1
            parts.append((i, sidx[S], sign))
        for k in range(n3):
            r = 0
            for i, si, sign in parts:
                b = block(i, k, sign)
                if b:
                    r += b << (si * n2 * (1 if q == 2 else W))
                    placed += 1
            rows.append(r)
    return rows, len(src) * n2, placed


def rank_gf2(rows):
    basis, ops = {}, 0
    for r in rows:
        while r:
            h = r.bit_length() - 1
            b = basis.get(h)
            if b is None:
                basis[h] = r
                break
            r ^= b
            ops += 1
    return len(basis), ops


def rank_packed(rows, ncols, q):
    assert ncols * (q - 1) ** 2 + q < 2 ** W
    nbytes = ncols * 4
    basis, ops = {}, 0
    for r in rows:
        while r:
            h = (r.bit_length() - 1) // W
            s = h * W
            V = r >> s
            r -= V << s
            v = V % q
            if not v:
                continue
            b = basis.get(h)
            if b is None:
                inv = pow(v, q - 2, q) if q > 2 else 1
                fields = array('I', r.to_bytes(nbytes, 'little'))
                basis[h] = int.from_bytes(array('I', [(x * inv) % q for x in fields]).tobytes(), 'little')
                break
            r += (q - v) * b
            ops += 1
    return len(basis), ops


def dense_to_rows(M, q, packed=False):
    if q == 2 and not packed:
        return [sum(1 << c for c, x in enumerate(r) if x % 2) for r in M]
    return [int.from_bytes(array('I', [x % q for x in r]).tobytes(), 'little') for r in M]


def rank_dense_mod(M, q):
    rows = [[x % q for x in r] for r in M]
    ncols = len(M[0]) if M else 0
    rank = 0
    for c in range(ncols):
        piv = next((i for i in range(rank, len(rows)) if rows[i][c]), None)
        if piv is None:
            continue
        rows[rank], rows[piv] = rows[piv], rows[rank]
        inv = pow(rows[rank][c], q - 2, q)
        pr = [(x * inv) % q for x in rows[rank]]
        rows[rank] = pr
        for i in range(rank + 1, len(rows)):
            f = rows[i][c]
            if f:
                rows[i] = [(x - f * y) % q for x, y in zip(rows[i], pr)]
        rank += 1
    return rank


def rank_exact(M):
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


def flat_rank(Tp, p, q):
    rows, ncols, placed = flattening_rows(Tp, p, q)
    r, ops = rank_gf2(rows) if q == 2 else rank_packed(rows, ncols, q)
    return r, ops + placed, len(rows), ncols


# ------------------------------------------------------------------------------------------------ upper bounds
def popcount(v):
    return bin(v).count("1")


def char_type_decomposition(a, b, c):
    """A decomposition of character type of T_{a,b,c} in factors 1 and 2 of length |D_{a,b}| (Theorem 1 of the
    partial-Fourier note), solved over Q. Sign vectors t with t_n = +1 (encoded by y = {i : t_i = -1} subset of [n-1]),
    taken in order of |y| and then y, keeping those whose character columns on D_{a,b} are independent.
    Returns (list of (y, W_y)), D, and the number of field operations."""
    n = a + b + c
    SA, SB, SC = ksubsets(n, a), ksubsets(n, b), ksubsets(n, c)
    D = sorted({s ^ t for s in SA for t in SB})
    full = (1 << n) - 1
    icol = {u: i for i, u in enumerate(SC)}
    chi = lambda v, y: -1 if popcount(v & y) % 2 else 1
    ys = sorted(range(1 << (n - 1)), key=lambda y: (popcount(y), y))
    # greedy independent columns (exact elimination over Q on the column vectors)
    chosen, basis, ops = [], [], 0
    for y in ys:
        col = [Fraction(chi(v, y)) for v in D]
        for piv, bvec in basis:
            f = col[piv]
            if f:
                col = [x - f * z for x, z in zip(col, bvec)]
                ops += len(col)
        piv = next((i for i, x in enumerate(col) if x != 0), None)
        if piv is None:
            continue
        inv = 1 / col[piv]
        basis.append((piv, [x * inv for x in col]))
        chosen.append(y)
        if len(chosen) == len(D):
            break
    m = len(D)
    # solve X Wmat = Tau, X[v][l] = chi_v(t_l), Tau[v] = e_{[n] \ v} if |v| = a + b else 0 (Lemma 3 of the note)
    X = [[Fraction(chi(v, y)) for y in chosen] + [Fraction(1 if (popcount(v) == a + b and u == full ^ v) else 0)
                                                    for u in SC] for v in D]
    for col in range(m):
        piv = next(i for i in range(col, m) if X[i][col] != 0)
        X[col], X[piv] = X[piv], X[col]
        inv = 1 / X[col][col]
        X[col] = [x * inv for x in X[col]]
        for i in range(m):
            if i != col and X[i][col] != 0:
                f = X[i][col]
                X[i] = [x - f * z for x, z in zip(X[i], X[col])]
                ops += len(X[i])
    Wmat = [[X[l][m + icol[u]] for u in SC] for l in range(m)]
    return list(zip(chosen, Wmat)), D, ops


def check_decomposition(a, b, c, order):
    """Build the decomposition for T_{a,b,c} with the pair of factors (order[0], order[1]) carrying the characters,
    check it entry by entry over Q against T_{a,b,c}; return (ok, length, all denominators powers of 2, steps)."""
    sizes = (a, b, c)
    pa, pb, pc = (sizes[o] for o in order)
    terms, D, ops = char_type_decomposition(pa, pb, pc)
    n = a + b + c
    S1, S2, S3 = ksubsets(n, pa), ksubsets(n, pb), ksubsets(n, pc)
    T, dims = tripartition_tensor(pa, pb, pc)
    chi = lambda v, y: -1 if popcount(v & y) % 2 else 1
    ok, steps = True, ops
    for i, s in enumerate(S1):
        for j, t in enumerate(S2):
            for k in range(len(S3)):
                val = sum(chi(s, y) * chi(t, y) * Wy[k] for y, Wy in terms)
                steps += len(terms)
                ok &= val == T.get((i, j, k), 0)
    pow2 = all((x.denominator & (x.denominator - 1)) == 0 for _, Wy in terms for x in Wy)
    return ok, len(terms), pow2, steps


def main():
    quick = "--quick" in sys.argv[1:]
    t_start = time.perf_counter()

    # 1. projections as printed
    t0 = time.perf_counter()
    text = (HERE / "README.md").read_text(encoding="utf-8")
    blocks = text.split("<!-- PHI -->")
    ok = len(blocks) == 7
    parsed = []
    for bi in (1, 3, 5):
        blk = blocks[bi] if ok else ""
        parsed.append([[int(t) for t in re.findall(r"-?\d+", ln.split("[", 1)[1].split("]", 1)[0])]
                       for ln in blk.splitlines() if "[" in ln])
    S73 = ksubsets(7, 3)
    labels = ["{" + ",".join(str(e) for e in range(1, 8) if s >> (e - 1) & 1) + "}" for s in S73]
    lab_printed = [re.search(r"\{[0-9,]+\}", ln).group(0) for ln in (blocks[5] if ok else "").splitlines() if "[" in ln]
    ok = ok and parsed[0] == PHI_123 and parsed[1] == PHI_133 and parsed[2] == PHI_223_T and lab_printed == labels
    ok = ok and all(x in (-1, 0, 1) for col in PHI_223_T for x in col) and all(any(col) for col in PHI_223_T)
    check("projections: the three matrices printed in the README equal the constants used here", ok,
          f"steps = {5 * 6 + 5 * 7 + 35 * 11} entries")
    timed(t0)

    # 2. rank routines
    t0 = time.perf_counter()
    rng = LCG(20261008)
    ok, steps, tested = True, 0, 0
    for planted in range(9):
        for rep in range(5):
            nr, nc = rng.next(planted + 1, 9), rng.next(planted + 1, 11)
            X = [[rng.next(-3, 3) for _ in range(planted)] for _ in range(nr)]
            Y = [[rng.next(-3, 3) for _ in range(nc)] for _ in range(planted)]
            M = [[sum(X[i][t] * Y[t][j] for t in range(planted)) for j in range(nc)] for i in range(nr)]
            rq = rank_exact(M)
            ok &= rank_dense_mod(M, BIG) == rq and rq <= planted
            for q in PRIMES:
                ref = rank_dense_mod(M, q)
                r2, o2 = rank_packed(dense_to_rows(M, q, packed=True), nc, q)
                r1, o1 = rank_gf2(dense_to_rows(M, 2)) if q == 2 else (ref, 0)
                steps += o1 + o2
                ok &= ref <= rq and r1 == ref and r2 == ref
            tested += 1
    strict = all(rank_exact([[q, 0], [0, 1]]) == 2 and rank_dense_mod([[q, 0], [0, 1]], q) == 1 and
                 rank_packed(dense_to_rows([[q, 0], [0, 1]], q, packed=True), 2, q)[0] == 1 for q in PRIMES)
    check("rank routines: XOR basis and packed elimination = dense elimination mod q (q <= 31); dense mod 2^31-1 = "
          "exact rank over Q; diag(q,1)", ok and strict, f"{tested} matrices x 11 primes, steps = {steps}")
    timed(t0)

    # 3. flattening code on the public values and on rank-one / unit tensors
    t0 = time.perf_counter()
    ok, steps, got = True, 0, {}
    T, dims = tripartition_tensor(1, 1, 2)
    Tq, dq = permute(T, dims, (2, 0, 1))
    Tp = project(Tq, dq, PHI_112)
    for q in PRIMES:
        r, st, nr, nc = flat_rank(Tp, 2, q)
        steps += st
        got[("T112", q)] = r
        ok &= (nr, nc) == (40, 40) and r == (39 if q == 5 else 40)
    T, dims = tripartition_tensor(1, 2, 2)
    Tp = project(T, dims, [[int(i == j) for j in range(5)] for i in range(5)])
    for q in PRIMES:
        r, st, nr, nc = flat_rank(Tp, 2, q)
        steps += st
        ok &= (nr, nc) == (100, 100) and r == 76
    for phi, n1, n2, n3, p in ((PHI_123, 6, 15, 20, 2), (PHI_133, 7, 35, 35, 2), (PHI_223, 35, 21, 21, 5)):
        g = LCG(1000 + n1)
        one = [([0] * (n1 - 1) + [1], [g.next(-1, 1) or 1 for _ in range(n2)], [g.next(-1, 1) or 1 for _ in range(n3)])]
        Tp1 = project_rank_ones(phi, one, n2, n3)
        unit = {(x, x, x): 1 for x in range(min(n1, n2, n3))}
        Tpu = project(unit, (n1, n2, n3), phi)
        for q in ([2, 3] if p == 5 else PRIMES):
            r1, st1, _, _ = flat_rank(Tp1, p, q)
            ru, stu, _, _ = flat_rank(Tpu, p, q)
            steps += st1 + stu
            # the unit tensor <min(n1,n2,n3)> embedded diagonally: its columns of phi are nonzero modulo q
            ok &= r1 == comb(2 * p, p) and ru == min(n1, n2, n3) * comb(2 * p, p)
    check("flattening code: T_{1,1,2} ranks 40 (39 mod 5), T_{1,2,2} rank 76 (public values); rank-one tensors give "
          "C(2p,p) and diagonal unit tensors give (size) C(2p,p) with the three projections (mod every q <= 31; "
          "mod 2, 3 for p = 5)", ok, f"steps = {steps}")
    timed(t0)

    # 4. upper bounds
    t0 = time.perf_counter()
    ok, steps, rows = True, 0, []
    for (a, b, c), order, expect in (((1, 2, 3), (0, 1, 2), 26), ((1, 2, 4), (0, 1, 2), 42),
                                     ((1, 3, 3), (0, 1, 2), 56), ((2, 2, 3), (0, 1, 2), 57)):
        good, length, pow2, st = check_decomposition(a, b, c, order)
        steps += st
        n = a + b + c
        sizes = (a, b, c)
        dmin = min(sum(comb(n, sizes[i] + sizes[j] - 2 * t) for t in range(min(sizes[i], sizes[j]) + 1))
                   for i, j in ((0, 1), (0, 2), (1, 2)))
        rows.append((f"T_{a}{b}{c}", length))
        ok &= good and pow2 and length == expect == dmin
    for c in range(1, 13):
        good, length, pow2, st = check_decomposition(1, 1, c, (0, 1, 2))
        steps += st
        ok &= good and pow2 and length == comb(c + 2, 2) + 1
    check("upper bounds: decompositions of character type with 26, 42, 56, 57 terms and C(c+2,2)+1 terms "
          "(1 <= c <= 12) are exact over Q, with power-of-2 denominators; lengths = min |D|", ok,
          f"{rows}, steps = {steps}")
    timed(t0)

    # 5. T_{1,2,3}
    t0 = time.perf_counter()
    T, dims = tripartition_tensor(1, 2, 3)
    Tp = project(T, dims, PHI_123)
    ok, steps, got = True, 0, {}
    for q in PRIMES:
        r, st, nr, nc = flat_rank(Tp, 2, q)
        steps += st
        got[q] = r
        ok &= (nr, nc) == (200, 150) and r == EXP_123[q] and r > 20 * 6
    check("T_{1,2,3}: K_2([I_5|1]; T) (factor 1, 200 x 150) has rank 121 mod every prime q <= 31; > 120, so border "
          "rank >= 21", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 6. T_{1,3,3}
    t0 = time.perf_counter()
    T, dims = tripartition_tensor(1, 3, 3)
    Tp = project(T, dims, PHI_133)
    ok, steps, got = True, 0, {}
    for q in PRIMES:
        r, st, nr, nc = flat_rank(Tp, 2, q)
        steps += st
        got[q] = r
        ok &= (nr, nc) == (350, 350) and r == EXP_133[q] and ((r > 41 * 6) == (q != 2))
    check("T_{1,3,3}: K_2(PHI_133; T) (factor 1, 350 x 350) has rank 248 mod every odd prime q <= 31 (> 246, border "
          "rank >= 42) and 242 mod 2 (no claim)", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 7. T_{2,2,3}
    T, dims = tripartition_tensor(2, 2, 3)
    Tq, dq = permute(T, dims, (2, 0, 1))
    Tp = project(Tq, dq, PHI_223)
    for q in ([2, 3] if quick else PRIMES):
        t0 = time.perf_counter()
        r, st, nr, nc = flat_rank(Tp, 5, q)
        check(f"T_{{2,2,3}}: K_5(PHI_223; T) (factor 3 projected, {nr} x {nc}) has rank {EXP_223[q]} mod {q}; "
              f"> 9576 = 38 * 252, so border rank >= 39", (nr, nc) == (9702, 9702) and r == EXP_223[q] and r > 9576,
              f"rank {r}, steps = {st}")
        timed(t0)
    t0 = time.perf_counter()
    g = LCG(38)
    terms = [([g.next(-1, 1) for _ in range(35)], [g.next(-1, 1) for _ in range(21)], [g.next(-1, 1) for _ in range(21)])
             for _ in range(38)]
    Tpr = project_rank_ones(PHI_223, terms, 21, 21)
    got, steps = {}, 0
    for q in (2, 3):
        r, st, _, _ = flat_rank(Tpr, 5, q)
        got[q] = r
        steps += st
    check("control: a fixed sum of 38 rank-one tensors of format 35 x 21 x 21 gives rank 9552 mod 2 and 9576 mod 3, "
          "<= 38 * 252 (not certified)", got == {2: 9552, 3: 9576}, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 8. flattening along factor 3: T_{1,2,4} and T_{1,1,c}
    t0 = time.perf_counter()
    ok, steps, cases = True, 0, 0
    for (a, b, c) in [(1, 2, 4)] + [(1, 1, cc) for cc in range(1, 21)]:
        T, dims = tripartition_tensor(a, b, c)
        rows = [[0] * (dims[0] * dims[1]) for _ in range(dims[2])]
        for (i, j, k), v in T.items():
            rows[k][i * dims[1] + j] = v
        supports = [frozenset(x for x, val in enumerate(r) if val) for r in rows]
        disjoint = all(supports) and sum(len(s) for s in supports) == len(frozenset().union(*supports))
        steps += dims[2] * dims[0] * dims[1]
        expect = comb(a + b + c, c)
        ok &= disjoint and len(rows) == expect
        for q in PRIMES:
            r, ops = rank_packed(dense_to_rows(rows, q, packed=True), dims[0] * dims[1], q)
            steps += ops
            ok &= r == expect
        cases += 1
    check("T_{1,2,4} >= 35 and T_{1,1,c} >= C(c+2,2) (1 <= c <= 20): factor-3 flattening rows nonzero with disjoint "
          "supports; rank = number of rows mod every prime q <= 31", ok, f"{cases} tensors, steps = {steps}")
    timed(t0)

    # 9. rank one above the dimension: the exchange step of the proof, and small slice spaces without rank one
    t0 = time.perf_counter()
    ok, steps = True, 0
    for (a, b, c) in [(1, 2, 3), (1, 2, 4), (1, 3, 3), (2, 2, 3)] + [(1, 1, cc) for cc in range(1, 9)]:
        n = a + b + c
        for S0 in combinations(range(n), a):
            for W in combinations(range(n), b):
                if set(S0) & set(W):
                    continue
                for s in S0:
                    for t in W:
                        S1 = (set(S0) - {s}) | {t}
                        W1 = (set(W) - {t}) | {s}
                        ok &= (len(S1) == a and len(W1) == b and not (S1 & W1) and S1 | W1 == set(S0) | set(W)
                               and s in W1 and s in S0)
                        steps += 1
    check("rank >= C(n,c) + 1: for (1,2,3), (1,2,4), (1,3,3), (2,2,3) and (1,1,c), c <= 8, every exchange "
          "(S0, W) -> (S0 - s + t, W - t + s) with S0, W disjoint keeps the sizes and the union, stays disjoint, and "
          "puts s in W' (the two cases of the proof)", ok, f"steps = {steps} exchanges")
    ok, steps, got = True, 0, {}
    for q, cmax in ((2, 4), (3, 2)):
        for cc in range(1, cmax + 1):
            T, dims = tripartition_tensor(1, 1, cc)
            n3 = dims[2]
            smallest = None
            for gamma in product(range(q), repeat=n3):
                if not any(gamma):
                    continue
                M = [[0] * dims[1] for _ in range(dims[0])]
                for (i, j, k), v in T.items():
                    M[i][j] += v * gamma[k]
                r = rank_dense_mod(M, q)
                smallest = r if smallest is None else min(smallest, r)
                steps += 1
            got[(q, cc)] = smallest
            ok &= smallest == 2
    check("T_{1,1,c}: every nonzero slice T(gamma) has rank >= 2 (no rank-one matrix in the slice space), exhaustively "
          "over F_2 for c <= 4 and over F_3 for c <= 2; smallest slice rank 2 in every case", ok,
          f"smallest ranks {got}, steps = {steps} slices")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED" + (" (quick mode: T_{2,2,3} checked modulo 2 and 3 only)" if quick else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
