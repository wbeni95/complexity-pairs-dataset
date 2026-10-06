"""Matrix multiplication tensors and multiplication schemes over GF(2), with an exact verifier.

Convention (cyclic). For the format (n, m, p), A is n x m, B is m x p,
C = AB is n x p, and the matrix multiplication tensor is

    T<n,m,p> = sum_{i<n, j<m, k<p}  a_ij (x) b_jk (x) c_ki .

A *scheme* of rank r is a list of r rank-one terms (alpha, beta, gamma) with

    sum_r alpha_r (x) beta_r (x) gamma_r = T<n,m,p>     over GF(2)            (the Brent equations).

Each factor is a 0/1 matrix stored as an int bitmask:

    alpha: n x m, entry (i, j) is bit i*m + j
    beta:  m x p, entry (j, k) is bit j*p + k
    gamma: p x n, entry (k, i) is bit k*n + i     (note the transpose)

Read as an algorithm: M_r = (sum_ij alpha_r[i,j] A[i,j]) * (sum_jk beta_r[j,k] B[j,k]) and
C[i,k] = sum_r gamma_r[k,i] M_r. A scheme of rank r for (k, k, k) applied recursively to blocks multiplies
N x N matrices with O(N^(log_k r)) ring operations, over every ring in which the scheme is valid; a scheme
verified over GF(2) is valid in characteristic 2 (it is valid over Z only if it happens to satisfy the Brent
equations over Z, which is checked separately by `verify_over_integers`).

Two independent exact verifiers are provided:
  * `verify` builds the tensor slice by slice with bit operations and compares it with `mm_tensor`;
  * `verify_explicit` evaluates every Brent equation one coefficient at a time (slow, written differently on
    purpose, used for the separate re-verification of saved schemes).
"""
from __future__ import annotations

import json
import random
from typing import Iterable, Sequence

Format = tuple  # (n, m, p)
Term = tuple  # (alpha, beta, gamma) bitmasks


def dims(fmt: Sequence[int]) -> tuple[int, int, int]:
    """Number of bits of the three factors: (n*m, m*p, p*n)."""
    n, m, p = fmt
    return n * m, m * p, p * n


def _bits(x: int):
    while x:
        low = x & -x
        yield low.bit_length() - 1
        x ^= low


# --------------------------------------------------------------------------------------------- tensors

def mm_tensor(fmt: Sequence[int]) -> list[int]:
    """The matrix multiplication tensor as nm slices; slice x = i*m + j is an int whose bit y*(p*n) + z is the
    coefficient of a_x (x) b_y (x) c_z (y = j'*p + k, z = k'*n + i')."""
    n, m, p = fmt
    pn = p * n
    T = [0] * (n * m)
    for i in range(n):
        for j in range(m):
            s = 0
            for k in range(p):
                y = j * p + k
                z = k * n + i
                s |= 1 << (y * pn + z)
            T[i * m + j] = s
    return T


def _outer_bc(b: int, c: int, pn: int) -> int:
    s = 0
    while b:
        low = b & -b
        s ^= c << ((low.bit_length() - 1) * pn)
        b ^= low
    return s


def scheme_tensor(fmt: Sequence[int], terms: Iterable[Term]) -> list[int]:
    """Sum of the rank-one terms over GF(2), in the slice layout of `mm_tensor`."""
    n, m, p = fmt
    pn = p * n
    T = [0] * (n * m)
    for a, b, c in terms:
        bc = _outer_bc(b, c, pn)
        while a:
            low = a & -a
            T[low.bit_length() - 1] ^= bc
            a ^= low
    return T


def check_factor_ranges(fmt: Sequence[int], terms: Iterable[Term]) -> None:
    """Raise ValueError if a factor has bits outside its matrix (or is negative / not an int)."""
    na, nb, nc = dims(fmt)
    for t in terms:
        if len(t) != 3:
            raise ValueError(f"term {t!r} does not have three factors")
        for f, size in zip(t, (na, nb, nc)):
            if not isinstance(f, int) or isinstance(f, bool) or f < 0 or f >> size:
                raise ValueError(f"factor {f!r} out of range for format {tuple(fmt)}")


def residual(fmt: Sequence[int], terms: Iterable[Term]) -> int:
    """Number of Brent equations violated over GF(2) (0 iff the scheme is correct)."""
    terms = list(terms)
    check_factor_ranges(fmt, terms)
    got = scheme_tensor(fmt, terms)
    want = mm_tensor(fmt)
    return sum(bin(g ^ w).count("1") for g, w in zip(got, want))


def verify(fmt: Sequence[int], terms: Iterable[Term]) -> bool:
    """Exact verifier: True iff the terms satisfy all Brent equations of format fmt over GF(2)."""
    return residual(fmt, terms) == 0


def verify_explicit(fmt: Sequence[int], terms: Iterable[Term]) -> bool:
    """Independent (slow) exact verifier: evaluates each Brent equation
        sum_r alpha_r[i1,j1] beta_r[j2,k2] gamma_r[k3,i3] = [j1 == j2][k2 == k3][i3 == i1]   (mod 2)
    one coefficient at a time, with no shared code with `verify`."""
    n, m, p = fmt
    terms = [tuple(t) for t in terms]
    check_factor_ranges(fmt, terms)

    def bit(x, idx):
        return (x >> idx) & 1

    for i1 in range(n):
        for j1 in range(m):
            for j2 in range(m):
                for k2 in range(p):
                    for k3 in range(p):
                        for i3 in range(n):
                            s = 0
                            for a, b, c in terms:
                                s += bit(a, i1 * m + j1) * bit(b, j2 * p + k2) * bit(c, k3 * n + i3)
                            want = 1 if (j1 == j2 and k2 == k3 and i3 == i1) else 0
                            if s % 2 != want:
                                return False
    return True


def verify_over_integers(fmt: Sequence[int], terms: Iterable[Term]) -> bool:
    """True iff the 0/1 coefficients, read as integers, satisfy the Brent equations over Z (i.e. the scheme is
    valid over every commutative ring without any sign changes). GF(2) schemes found by search usually are not;
    lifting them needs sign choices (Hensel lifting), which is not attempted here."""
    n, m, p = fmt
    terms = [tuple(t) for t in terms]
    check_factor_ranges(fmt, terms)
    for i1 in range(n):
        for j1 in range(m):
            for j2 in range(m):
                for k2 in range(p):
                    for k3 in range(p):
                        for i3 in range(n):
                            s = 0
                            for a, b, c in terms:
                                s += ((a >> (i1 * m + j1)) & 1) * ((b >> (j2 * p + k2)) & 1) * ((c >> (k3 * n + i3)) & 1)
                            if s != (1 if (j1 == j2 and k2 == k3 and i3 == i1) else 0):
                                return False
    return True


# --------------------------------------------------------------------------------------------- evaluation

def evaluate(fmt: Sequence[int], terms: Iterable[Term], A, B, modulus: int | None = 2):
    """Run the scheme as an algorithm on matrices A (n x m) and B (m x p); arithmetic mod `modulus`
    (None = integers). Returns C as a list of lists."""
    n, m, p = fmt
    C = [[0] * p for _ in range(n)]
    for a, b, c in terms:
        left = sum(A[i][j] for i in range(n) for j in range(m) if (a >> (i * m + j)) & 1)
        right = sum(B[j][k] for j in range(m) for k in range(p) if (b >> (j * p + k)) & 1)
        prod = left * right
        for k in range(p):
            for i in range(n):
                if (c >> (k * n + i)) & 1:
                    C[i][k] += prod
    if modulus is not None:
        C = [[x % modulus for x in row] for row in C]
    return C


def matmul(A, B, modulus: int | None = 2):
    n, m, p = len(A), len(B), len(B[0]) if B else 0
    C = [[sum(A[i][j] * B[j][k] for j in range(m)) for k in range(p)] for i in range(n)]
    if modulus is not None:
        C = [[x % modulus for x in row] for row in C]
    return C


def random_check(fmt: Sequence[int], terms: Iterable[Term], trials: int, seed: int) -> bool:
    """Functional cross-check: the scheme computes AB over GF(2) for `trials` random 0/1 matrices."""
    n, m, p = fmt
    terms = list(terms)
    rng = random.Random(seed)
    for _ in range(trials):
        A = [[rng.randrange(2) for _ in range(m)] for _ in range(n)]
        B = [[rng.randrange(2) for _ in range(p)] for _ in range(m)]
        if evaluate(fmt, terms, A, B) != matmul(A, B):
            return False
    return True


# --------------------------------------------------------------------------------------------- known schemes

def standard_scheme(fmt: Sequence[int]) -> list[Term]:
    """The schoolbook algorithm: one product a_ij * b_jk per (i, j, k); rank n*m*p."""
    n, m, p = fmt
    return [(1 << (i * m + j), 1 << (j * p + k), 1 << (k * n + i))
            for i in range(n) for j in range(m) for k in range(p)]


def scheme_from_products(fmt: Sequence[int], products) -> list[Term]:
    """Build terms from human-oriented products. Each product is (A_entries, B_entries, C_entries) where
    A_entries are (i, j) pairs (0-based) summed on the left, B_entries are (j, k) pairs summed on the right
    and C_entries are the (i, k) entries of C the product is added to. Signs are dropped (GF(2))."""
    n, m, p = fmt
    terms = []
    for A_e, B_e, C_e in products:
        a = b = c = 0
        for i, j in A_e:
            a ^= 1 << (i * m + j)
        for j, k in B_e:
            b ^= 1 << (j * p + k)
        for i, k in C_e:
            c ^= 1 << (k * n + i)
        terms.append((a, b, c))
    return terms


def strassen_scheme() -> list[Term]:
    """Strassen (1969), rank 7 for (2, 2, 2), with signs dropped (valid over GF(2))."""
    A11, A12, A21, A22 = (0, 0), (0, 1), (1, 0), (1, 1)
    B11, B12, B21, B22 = (0, 0), (0, 1), (1, 0), (1, 1)
    C11, C12, C21, C22 = (0, 0), (0, 1), (1, 0), (1, 1)
    products = [
        ([A11, A22], [B11, B22], [C11, C22]),   # M1 = (A11 + A22)(B11 + B22)
        ([A21, A22], [B11], [C21, C22]),        # M2 = (A21 + A22) B11
        ([A11], [B12, B22], [C12, C22]),        # M3 = A11 (B12 - B22)
        ([A22], [B21, B11], [C11, C21]),        # M4 = A22 (B21 - B11)
        ([A11, A12], [B22], [C11, C12]),        # M5 = (A11 + A12) B22
        ([A21, A11], [B11, B12], [C22]),        # M6 = (A21 - A11)(B11 + B12)
        ([A12, A22], [B21, B22], [C11]),        # M7 = (A12 - A22)(B21 + B22)
    ]
    return scheme_from_products((2, 2, 2), products)


def kron_scheme(fmt1: Sequence[int], terms1, fmt2: Sequence[int], terms2):
    """Tensor (Kronecker) product of two schemes: a scheme for (n1 n2, m1 m2, p1 p2) of rank r1 * r2.
    Block indices: i = i1*n2 + i2, j = j1*m2 + j2, k = k1*p2 + k2 (recursive application of scheme 1 to
    blocks multiplied by scheme 2)."""
    n1, m1, p1 = fmt1
    n2, m2, p2 = fmt2
    n, m, p = n1 * n2, m1 * m2, p1 * p2

    def kron_factor(x1, rows1, cols1, x2, rows2, cols2):
        out = 0
        for r1 in range(rows1):
            for c1 in range(cols1):
                if (x1 >> (r1 * cols1 + c1)) & 1:
                    for r2 in range(rows2):
                        for c2 in range(cols2):
                            if (x2 >> (r2 * cols2 + c2)) & 1:
                                out |= 1 << ((r1 * rows2 + r2) * (cols1 * cols2) + (c1 * cols2 + c2))
        return out

    terms = []
    for a1, b1, c1 in terms1:
        for a2, b2, c2 in terms2:
            terms.append((kron_factor(a1, n1, m1, a2, n2, m2),
                          kron_factor(b1, m1, p1, b2, m2, p2),
                          kron_factor(c1, p1, n1, c2, p2, n2)))
    return (n, m, p), terms


# --------------------------------------------------------------------------------------------- I/O

def describe_term(fmt: Sequence[int], term: Term) -> str:
    """Human-readable product, e.g. '(A11+A22)*(B11+B22) -> C11 C22' (1-based indices)."""
    n, m, p = fmt
    a, b, c = term
    left = "+".join(f"A{i + 1}{j + 1}" for i in range(n) for j in range(m) if (a >> (i * m + j)) & 1)
    right = "+".join(f"B{j + 1}{k + 1}" for j in range(m) for k in range(p) if (b >> (j * p + k)) & 1)
    outs = " ".join(f"C{i + 1}{k + 1}" for i in range(n) for k in range(p) if (c >> (k * n + i)) & 1)
    return f"({left})*({right}) -> {outs}"


CONVENTION = ("T<n,m,p> = sum a_ij (x) b_jk (x) c_ki over GF(2); alpha bit i*m+j, beta bit j*p+k, "
              "gamma bit k*n+i (gamma[k][i] = coefficient of the product in C[i][k])")


def scheme_to_json(fmt: Sequence[int], terms, **meta) -> dict:
    terms = sorted(tuple(t) for t in terms)
    return {
        "format": list(fmt),
        "field": "GF(2)",
        "rank": len(terms),
        "convention": CONVENTION,
        **meta,
        "terms": [list(t) for t in terms],
        "products": [describe_term(fmt, t) for t in terms],
    }


def save_scheme(path, fmt, terms, **meta) -> dict:
    if not verify(fmt, terms):
        raise ValueError("refusing to save a scheme that fails the exact verifier")
    doc = scheme_to_json(fmt, terms, **meta)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    return doc


def load_scheme(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    return tuple(doc["format"]), [tuple(t) for t in doc["terms"]], doc
