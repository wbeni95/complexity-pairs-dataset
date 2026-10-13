#!/usr/bin/env python3
"""Verifier for theorems/tripartition-tensor-p3-border-rank-at-least-150 (see README.md in this folder).

Notation as in the README: P_3 = T_{3,3,3} is the 84 x 84 x 84 tensor of ordered partitions of {1..9} into three
3-sets, each factor's coordinates the 3-subsets in increasing bitmask order (bit e-1 <-> element e). For a tensor T,
a (2p+1) x n_1 integer matrix PHI and p >= 1, K_p(PHI; T) is the Koszul-Young flattening of (PHI x 1 x 1) T of the
public note tripartition-tensor-p2-border-rank-at-least-26, with rows (U, k) and columns (S, j):
    K[(U,k),(S,j)] = sgn(i,S) * T'[i][j][k]  if U = S + {i}, i not in S,   else 0,
where T'[i][j][k] = sum_a PHI[i][a] T[a][j][k] and sgn(i,S) = (-1)^#{s in S : s < i}. Row (U, k) is row number
u * n_3 + k and column (S, j) is column number s * n_2 + j, with U and S numbered in lexicographic order.

Two rank routines, both standard library:
  * rank over F_2: each row is a Python integer (bit c = column c); an exclusive-or basis keyed by the highest set bit;
  * rank over F_q: each row is a Python integer holding one 32-bit field per column (entries kept nonnegative and
    reduced modulo q when a row enters the basis); the leading field of a row is read, reduced modulo q, cleared, and
    eliminated with the basis row of that column. A row receives at most one elimination per basis row, so no field
    exceeds (number of columns) (q-1)^2 + q - 1 < 2^32, which the routine asserts.

What it checks, in order:
  1. the matrix PHI printed in the README (as 84 columns of 9 entries) equals the constant PHI_T below; the entries
     are -1, 0, 1 and every column has an entry +-1 (so no column is zero modulo any prime);
  2. the rank routines on 45 fixed integer matrices with planted ranks 0..8: both routines agree with Gaussian
     elimination modulo q for every prime q <= 31, and elimination modulo 2^31 - 1 agrees with the exact rank over Q
     (Fractions); diag(q, 1) has rank 2 over Q and 1 modulo q;
  3. the flattening code against the public P_2 note: with that note's 7 x 15 projection and p = 3, the 525 x 525
     flattening of P_2 has rank 502 modulo 2 and 504 modulo 3;
  4. Lemma 2 of the P_2 note: a rank-one tensor gives rank exactly C(8, 4) = 70 (p = 4, PHI), modulo every q <= 31;
  5. the Example of the P_2 note: the unit tensor <84> gives rank 84 * 70 = 5 880 (PHI, p = 4), modulo every q <= 31;
  6. controls at the threshold: a fixed sum of 149 rank-one tensors (entries -1, 0, 1) gives rank 10 430 = 149 * 70,
     so the method does not certify 150 for it, and a fixed sum of 150 rank-one tensors gives rank 10 500 = 150 * 70
     (modulo 2; also modulo 3 unless --quick);
  7. the theorem's computation: P_3 has 1 680 nonzero coefficients, M = K_4(PHI; P_3) is 10 584 x 10 584, and its rank
     modulo q is 10 498 for q = 2 and 10 500 for every odd prime q <= 31; each exceeds
     10 430 = 149 * 70, so the bound ceil(rank / 70) is 150. Modulo 2 both routines are run (cross-check).
With --quick, steps 4-7 use q = 2 only for the large matrices (the characteristic-0 and characteristic-2 claims).
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count (row eliminations of the rank
routines, entries or rows built); the wall-clock seconds follow on a separate line. Exit code 0 only if every check
passes.

Usage (from the repository root):
    python theorems/tripartition-tensor-p3-border-rank-at-least-150/verify.py            (about 15 minutes)
    python theorems/tripartition-tensor-p3-border-rank-at-least-150/verify.py --quick    (well under a minute)
Deterministic and offline, standard library only. Memory: about 1 GB.
"""
import re
import sys
import time
from array import array
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31]
BIG = 2 ** 31 - 1
P = 4                         # Koszul-Young parameter: dim A' = 2P + 1 = 9, divisor C(2P, P) = 70
DIV = comb(2 * P, P)
BOUND = 150
THRESH = (BOUND - 1) * DIV    # 10 430: rank > THRESH certifies border rank >= BOUND
EXPECTED = {q: 10500 for q in PRIMES}
EXPECTED[2] = 10498
W = 32
assert array('I').itemsize == 4

# the projection A -> A' = F^9, written by columns: PHI_T[a] is column a (coordinate a of the first factor)
PHI_T = [
    [-1,  1,  1, -1,  0,  1, -1,  1,  1],
    [ 0,  0, -1,  1, -1, -1,  0,  1,  1],
    [ 1,  1,  0,  1, -1,  1, -1, -1, -1],
    [ 0,  0,  0, -1, -1, -1,  0,  1, -1],
    [ 0,  0, -1,  0,  1, -1,  0, -1,  1],
    [ 0,  1,  0,  1,  1,  0, -1,  1,  0],
    [ 0, -1,  0, -1,  1,  0,  1,  0,  0],
    [ 1, -1,  1,  1, -1,  0, -1,  0,  1],
    [ 1,  1,  0,  1,  1,  1,  0, -1,  1],
    [ 0,  1,  1,  0,  1, -1, -1, -1,  1],
    [ 0,  1,  0,  1,  1, -1,  0, -1,  0],
    [-1,  1, -1,  1, -1,  0, -1,  1,  0],
    [ 1, -1,  0, -1, -1, -1,  1,  0,  0],
    [-1, -1,  0,  1, -1,  1,  1, -1,  1],
    [-1,  0,  1,  0,  0, -1, -1,  0,  0],
    [ 1,  0,  1,  1,  0,  0,  1,  0,  1],
    [ 1, -1,  1, -1, -1, -1,  0,  0,  0],
    [ 0, -1, -1,  0,  1,  1,  0, -1, -1],
    [ 1,  1,  1, -1, -1, -1,  1,  0,  0],
    [-1, -1,  0, -1,  0, -1, -1,  1,  1],
    [-1,  0, -1,  1,  1,  1,  0,  0,  1],
    [ 0, -1, -1,  1,  1,  1, -1,  1,  0],
    [ 1, -1,  0, -1, -1,  1, -1,  1, -1],
    [ 1,  1,  1,  1,  0,  0,  1,  0, -1],
    [-1, -1, -1, -1,  0,  1,  0, -1,  1],
    [ 0, -1,  1,  0, -1, -1,  0,  1,  0],
    [ 1,  1,  0,  0,  1, -1,  1, -1, -1],
    [ 1, -1,  0, -1,  1,  1,  1,  1,  1],
    [ 1,  1, -1,  0,  1, -1,  0,  1, -1],
    [-1, -1,  1,  0,  1,  1,  1,  1, -1],
    [-1, -1, -1,  0,  1,  0,  0,  0,  1],
    [-1,  1, -1,  0,  0, -1, -1,  1,  1],
    [ 1,  1, -1,  0,  1,  0,  1, -1,  1],
    [ 0,  0,  0,  1,  0,  0,  0, -1,  1],
    [ 0, -1, -1,  0, -1, -1,  0,  1,  1],
    [ 1,  0,  1, -1, -1,  0, -1,  0,  1],
    [ 0,  0,  1, -1,  1, -1, -1,  1, -1],
    [-1,  1, -1,  0,  0,  0,  1, -1, -1],
    [ 1,  1,  0,  0, -1,  1,  1,  0, -1],
    [ 1,  1,  1,  1,  1,  0,  1,  1,  1],
    [ 0, -1, -1, -1,  1,  0,  0,  1,  0],
    [ 1,  1,  1, -1,  0, -1,  0,  0, -1],
    [ 1,  1,  0, -1,  1, -1,  1, -1,  1],
    [ 1,  0,  0,  0, -1,  1,  1,  0,  0],
    [ 0,  1,  0,  0, -1, -1, -1, -1, -1],
    [-1,  1, -1, -1,  1,  1, -1,  0, -1],
    [ 1,  0,  1,  0,  0, -1,  0,  0,  0],
    [ 0, -1, -1,  0,  1, -1,  1,  0, -1],
    [ 1, -1,  1,  0,  1,  1,  1, -1, -1],
    [ 1, -1,  0,  1, -1, -1, -1, -1, -1],
    [ 0,  0, -1, -1,  1,  0,  1, -1, -1],
    [ 1,  1, -1,  0,  0,  1,  1,  0, -1],
    [ 1,  0,  1,  1,  1, -1, -1,  0, -1],
    [ 1,  1,  0,  1,  1,  1,  1,  1,  0],
    [-1,  0,  1,  1,  1,  1, -1,  0,  0],
    [ 1, -1,  0,  1,  1, -1, -1,  1, -1],
    [ 1, -1,  1, -1,  0, -1,  1,  1, -1],
    [ 0, -1,  0, -1,  0, -1, -1,  0, -1],
    [ 0,  0,  1, -1,  1, -1,  1,  0,  1],
    [ 1,  0, -1,  1,  0,  0, -1,  1,  0],
    [-1,  0,  1, -1, -1,  0,  1,  0, -1],
    [ 1,  1,  0, -1, -1,  0,  1,  0, -1],
    [ 0,  0, -1, -1, -1, -1, -1,  0,  1],
    [ 1,  0, -1,  1,  1,  0, -1, -1,  1],
    [ 0,  1,  1, -1,  1, -1,  1, -1,  1],
    [ 1,  1,  0, -1,  1,  0, -1, -1,  1],
    [ 1, -1,  1,  0,  0,  0,  0, -1,  0],
    [-1,  1,  0,  0,  1,  0, -1,  0,  1],
    [ 1, -1,  0,  1,  0, -1,  0,  0, -1],
    [ 1,  0,  0, -1, -1, -1, -1, -1,  1],
    [ 0, -1, -1,  1,  0, -1, -1,  0,  1],
    [ 1,  0, -1,  1, -1,  1,  0,  0,  1],
    [-1,  1, -1,  1,  0,  1, -1,  0,  1],
    [-1, -1,  1, -1,  1,  1,  0, -1, -1],
    [ 0, -1,  0,  1,  0,  1,  1,  1, -1],
    [-1, -1, -1,  0,  0,  0, -1,  1,  0],
    [ 1, -1, -1,  0, -1,  1, -1,  0,  0],
    [ 0,  1, -1,  0, -1,  1,  0, -1,  1],
    [ 0,  1,  0,  0,  1, -1,  1, -1,  0],
    [-1, -1,  1,  1,  1,  1,  0,  0,  1],
    [-1, -1,  1,  1,  0,  1,  1,  1, -1],
    [-1, -1, -1,  0, -1, -1,  0,  1, -1],
    [-1,  1, -1,  0, -1,  0,  0,  0,  0],
    [ 0,  1,  1, -1,  1, -1, -1,  0,  0],
]
PHI = [[PHI_T[a][i] for a in range(84)] for i in range(9)]

# the projection of the public note tripartition-tensor-p2-border-rank-at-least-26 (7 x 15), for check 3
PHI_P2 = [
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
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)", flush=True)


class LCG:
    """A fixed linear congruential generator (deterministic test data, independent of PYTHONHASHSEED)."""

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


def project(T, dims, phi):
    """T' = (phi x 1 x 1) T as Tp[i][k][j] (lists of integers)."""
    m = len(phi)
    _, n2, n3 = dims
    Tp = [[[0] * n2 for _ in range(n3)] for _ in range(m)]
    for (a, j, k), v in T.items():
        for i in range(m):
            if phi[i][a]:
                Tp[i][k][j] += phi[i][a] * v
    return Tp


def project_rank_ones(phi, terms, n2, n3):
    """(phi x 1 x 1) sum_r alpha_r (x) beta_r (x) gamma_r as Tp[i][k][j]."""
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


def flattening_rows(Tp, p, q, packed=False):
    """Rows of K_p of the projected tensor Tp: bitmasks if q == 2 (unless packed), else packed 32-bit fields with
    entries in [0, q). Returns (rows, number of columns, number of block placements)."""
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
            if q == 2 and not packed:
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
                    r += b << (si * n2 * (1 if q == 2 and not packed else W))   # distinct S: no overlap
                    placed += 1
            rows.append(r)
    return rows, len(src) * n2, placed


# ------------------------------------------------------------------------------------------------ ranks
def rank_gf2(rows):
    """Rank over F_2 of rows given as bitmasks. Returns (rank, row eliminations)."""
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
    """Rank over F_q of rows given as packed 32-bit fields (entries in [0, q)). Returns (rank, row eliminations)."""
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
            if b is None:                      # normalise: leading entry 1 (stored implicitly), fields reduced mod q
                inv = pow(v, q - 2, q) if q > 2 else 1
                fields = array('I', r.to_bytes(nbytes, 'little'))
                basis[h] = int.from_bytes(array('I', [(x * inv) % q for x in fields]).tobytes(), 'little')
                break
            r += (q - v) * b                   # r - v * (e_h + b), with e_h already removed
            ops += 1
    return len(basis), ops


def dense_to_rows(M, q, packed=False):
    """Rows of a dense integer matrix: bitmasks for q == 2 (unless packed), else packed 32-bit fields mod q."""
    if q == 2 and not packed:
        return [sum(1 << c for c, x in enumerate(r) if x % 2) for r in M]
    return [int.from_bytes(array('I', [x % q for x in r]).tobytes(), 'little') for r in M]


def rank_dense_mod(M, q):
    """Reference: Gaussian elimination modulo q on a dense integer matrix."""
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
    """(rank, steps) of K_p(Tp) modulo q with the routine for q (XOR basis for q = 2)."""
    rows, ncols, placed = flattening_rows(Tp, p, q)
    r, ops = rank_gf2(rows) if q == 2 else rank_packed(rows, ncols, q)
    return r, ops + placed, len(rows), ncols


def main():
    quick = "--quick" in sys.argv[1:]
    t_start = time.perf_counter()
    big_primes = [2] if quick else PRIMES

    # 1. PHI as printed in the README
    t0 = time.perf_counter()
    text = (HERE / "README.md").read_text(encoding="utf-8")
    parts = text.split("<!-- PHI -->")
    block = parts[1] if len(parts) == 3 else ""
    S3 = ksubsets(9, 3)
    labels = ["{" + ",".join(str(e) for e in range(1, 10) if s >> (e - 1) & 1) + "}" for s in S3]
    printed, printed_labels = [], []
    for line in block.splitlines():
        if "[" in line:
            printed.append([int(t) for t in re.findall(r"-?\d+", line.split("[", 1)[1].split("]", 1)[0])])
            lab = re.search(r"\{[0-9,]+\}", line)
            printed_labels.append(lab.group(0) if lab else None)
    entries_ok = all(x in (-1, 0, 1) for col in PHI_T for x in col) and len(PHI_T) == 84 and all(
        len(col) == 9 for col in PHI_T)
    nonzero_cols = all(any(x != 0 for x in col) for col in PHI_T)
    check("PHI: the 84 columns printed in the README equal PHI_T (labels in coordinate order); entries in {-1,0,1}; "
          "every column has an entry +-1", printed == PHI_T and printed_labels == labels and entries_ok and nonzero_cols,
          f"{len(printed)} columns compared, steps = {84 * 9} entries")
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
                r1, o1 = rank_gf2(dense_to_rows(M, 2)) if q == 2 else (None, 0)
                r2, o2 = rank_packed(dense_to_rows(M, q, packed=True), nc, q)
                steps += o1 + o2
                ok &= ref <= rq and r2 == ref and (q != 2 or r1 == ref)
            tested += 1
    strict = all(rank_exact([[q, 0], [0, 1]]) == 2 and rank_dense_mod([[q, 0], [0, 1]], q) == 1 and
                 rank_packed(dense_to_rows([[q, 0], [0, 1]], q, packed=True), 2, q)[0] == 1 for q in PRIMES)
    check("rank routines: XOR basis (q = 2) and packed elimination (q <= 31) = dense elimination mod q; dense mod "
          "2^31-1 = exact rank over Q; diag(q,1) has rank 2 over Q and 1 mod q", ok and strict,
          f"{tested} planted-rank matrices x 11 primes, steps = {steps} row eliminations")
    timed(t0)

    # 3. the flattening code against the public P_2 note
    t0 = time.perf_counter()
    T2, dims2 = tripartition_tensor(2, 2, 2)
    Tp2 = project(T2, dims2, PHI_P2)
    got, steps = {}, 0
    for q in (2, 3):
        r, st, nr, nc = flat_rank(Tp2, 3, q)
        got[q] = (r, nr, nc)
        steps += st
    check("flattening code reproduces the public P_2 note: K_3 of P_2 with its projection is 525 x 525 of rank 502 mod 2 "
          "and 504 mod 3", got == {2: (502, 525, 525), 3: (504, 525, 525)}, f"{got}, steps = {steps}")
    timed(t0)

    # 4. Lemma 2: rank-one tensors
    t0 = time.perf_counter()
    alpha = [1] + [0] * 83
    beta = [1, 0, 0, 0, 0, 2] + [0] * 78
    gamma = [0, 1, 0, -1] + [0] * 80
    Tp1 = project_rank_ones(PHI, [(alpha, beta, gamma)], 84, 84)
    ok, steps, got = True, 0, {}
    for q in big_primes:
        r, st, _, _ = flat_rank(Tp1, P, q)
        got[q] = r
        steps += st
        ok &= r == DIV
    check("Lemma 2: a rank-one tensor gives rank C(8,4) = 70 (PHI, p = 4)", ok, f"ranks {got}, steps = {steps}")
    timed(t0)

    # 5. Example: the unit tensor <84>
    t0 = time.perf_counter()
    unit = {(a, a, a): 1 for a in range(84)}
    Tpu = project(unit, (84, 84, 84), PHI)
    ok, steps, got = True, 0, {}
    for q in big_primes:
        r, st, _, _ = flat_rank(Tpu, P, q)
        got[q] = r
        steps += st
        ok &= r == 84 * DIV
    check("Example: the unit tensor <84> gives rank 84 * 70 = 5880 (PHI, p = 4), bound 84", ok,
          f"ranks {got}, steps = {steps}")
    timed(t0)

    # 6. controls at the threshold
    for r_terms, seed, expect in ((149, 149, 10430), (150, 150, 10500)):
        t0 = time.perf_counter()
        g = LCG(seed)
        terms = [([g.next(-1, 1) for _ in range(84)], [g.next(-1, 1) for _ in range(84)],
                  [g.next(-1, 1) for _ in range(84)]) for _ in range(r_terms)]
        Tpr = project_rank_ones(PHI, terms, 84, 84)
        ok, steps, got = True, 0, {}
        for q in ([2] if quick else [2, 3]):
            r, st, _, _ = flat_rank(Tpr, P, q)
            got[q] = r
            steps += st
            ok &= r == expect and r <= r_terms * DIV
        check(f"control: a fixed sum of {r_terms} rank-one tensors gives rank {expect} = {r_terms} * 70 "
              f"({'not ' if r_terms < BOUND else ''}above the threshold {THRESH})", ok, f"ranks {got}, steps = {steps}")
        timed(t0)

    # 7. the theorem's computation
    t0 = time.perf_counter()
    T3, dims3 = tripartition_tensor(3, 3, 3)
    Tp3 = project(T3, dims3, PHI)
    rows2, ncols, placed = flattening_rows(Tp3, P, 2)
    check("P_3 and its flattening: 1680 nonzero coefficients; M = K_4(PHI; P_3) is 10584 x 10584",
          len(T3) == 1680 and dims3 == (84, 84, 84) and len(rows2) == 10584 and ncols == 10584,
          f"steps = {placed} block placements")
    timed(t0)
    t0 = time.perf_counter()
    r2, ops2 = rank_gf2(rows2)
    check(f"rank over F_2 of M (XOR basis) = {EXPECTED[2]} > {THRESH}, so border rank >= ceil(rank/70) = {BOUND}",
          r2 == EXPECTED[2] and r2 > THRESH and -(-r2 // DIV) == BOUND,
          f"rank {r2}, steps = {ops2} row eliminations")
    timed(t0)
    for q in big_primes:
        t0 = time.perf_counter()
        if q == 2:
            if quick:
                continue
            rows, nc, placed = flattening_rows(Tp3, P, 2, packed=True)
            r, ops = rank_packed(rows, nc, 2)
            st = ops + placed
            label = "rank over F_2 of M (packed routine, cross-check)"
        else:
            r, st, _, _ = flat_rank(Tp3, P, q)
            label = f"rank over F_{q} of M (packed routine)"
        check(f"{label} = {EXPECTED[q]} > {THRESH}, so border rank >= {BOUND}",
              r == EXPECTED[q] and r > THRESH and -(-r // DIV) == BOUND, f"rank {r}, steps = {st}")
        timed(t0)

    print(f"total {time.perf_counter() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED" + (" (quick mode: odd primes not checked for the large matrices)" if quick else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
