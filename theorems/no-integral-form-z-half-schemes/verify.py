#!/usr/bin/env python3
"""Verifier for theorems/no-integral-form-z-half-schemes (see README.md in this folder).

What it does, in order:
  1. obtains the two scheme files, either from their pinned public URLs (two downloads, nothing else is sent)
     or from local copies (--cache DIR), and checks their SHA-256;
  2. parses them (Maple "TriadSet" format) into exact rational matrices and checks the format and that every
     coefficient lies in Z[1/2] (denominators are powers of 2);
  3. checks over Q, exactly, that each file is a valid scheme: all n^2 m^2 p^2 Brent equations;
  4. forms the term matrices M_j = a_j b_j c_j (terms numbered 1..R in file order) and computes, with
     fractions.Fraction, the certificate of the note, the trace of a product of term matrices: tr(M_1) = 3/2 for
     <3,3,6;40> and tr(M_2 M_5) = 1/2 for <2,4,5;32>; for <2,4,5;32> it also checks that every single trace
     tr(M_j) is an integer, so that a one-factor certificate does not exist there;
  5. as an illustration of the invariance (not part of the proof), applies a seeded random rational sandwich with
     random term scalings to each scheme, re-checks the Brent equations and recomputes the certificate, which must
     be unchanged.
Exit code 0 only if every check passes; 1 otherwise.

Usage (from the repository root):
    python theorems/no-integral-form-z-half-schemes/verify.py
    python theorems/no-integral-form-z-half-schemes/verify.py --cache DIR
With --cache, nothing is downloaded: each file is read from DIR/<sha1 hex of its URL> or, if that does not exist,
from DIR/<file name> (2x4x5_tensor.mpl, 3x3x6_tensor.mpl). Standard library only; deterministic.

Conventions. A scheme for <n,m,p> is a list of terms (a_r, b_r, c_r) with a_r of size n x m, b_r of size m x p and
c_r of size p x n, such that sum_r a_r[i][j] * b_r[j'][k] * c_r[k'][i'] = [j = j'] [k = k'] [i = i'] for all
indices (the Brent equations). The files state this as A.B = sum_r <a_r, A> <b_r, B> c_r^T, where <X, A> is the sum
of the entrywise products; this is the same condition.
"""
import argparse
import hashlib
import itertools
import random
import re
import sys
import urllib.request
from fractions import Fraction
from pathlib import Path

BASE = ("https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/"
        "64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/known/")
SCHEMES = {
    "<2,4,5;32>": {
        "url": BASE + "tensor/2x4x5_tensor.mpl",
        "sha256": "e03c7743a60f53ae21a3413af4a5f019600a12befc8ed22ffdf2baa8b0f7dd4b",
        "format": (2, 4, 5),
        "rank": 32,
    },
    "<3,3,6;40>": {
        "url": BASE + "tensor/3x3x6_tensor.mpl",
        "sha256": "3e79357c5d2540e5c54c2a5f484f17009f70799b10bd45ed8e4bf893b5e223ab",
        "format": (3, 3, 6),
        "rank": 40,
    },
}
# Certificates: term numbers j_1, ..., j_k (from 1) and the expected value of tr(M_{j_1} ... M_{j_k}), where
# M_j = a_j b_j c_j (the certificate type of Moran-Schwartz-Yuan 2026, Proposition 3).
CERTIFICATES = {
    "<3,3,6;40>": {"terms": [1], "trace": Fraction(3, 2)},
    "<2,4,5;32>": {"terms": [2, 5], "trace": Fraction(1, 2)},
}
USER_AGENT = "complexity-pairs-dataset theorems verifier (python urllib)"

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ input
def obtain(url, cache):
    name = url.rsplit("/", 1)[1]
    if cache is not None:
        for p in (Path(cache) / hashlib.sha1(url.encode("utf-8")).hexdigest(), Path(cache) / name):
            if p.is_file():
                print(f"reading {name} from {p}")
                return p.read_bytes()
        sys.exit(f"--cache given, but neither DIR/<sha1(url)> nor DIR/{name} exists in {cache}")
    print(f"downloading {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def parse_triadset(text):
    """Return the list of matrices (lists of rows of Fraction) inside 'TriadSet(...)', in file order."""
    body = text[text.index("TriadSet("):]
    mats = []
    pos = 0
    while True:
        i = body.find("Matrix(", pos)
        if i < 0:
            break
        head_end = body.index("[", i)
        rows_dim, cols_dim = (int(x) for x in body[i + len("Matrix("):head_end].split(",")[:2])
        depth, k = 0, head_end
        while True:  # find the bracket that closes the outer list
            if body[k] == "[":
                depth += 1
            elif body[k] == "]":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        inner = body[head_end + 1:k]
        rows = [[Fraction(tok.strip()) for tok in row.split(",")] for row in re.findall(r"\[([^\[\]]*)\]", inner)]
        if len(rows) != rows_dim or any(len(row) != cols_dim for row in rows):
            raise ValueError(f"matrix at offset {i}: declared {rows_dim}x{cols_dim}, found other dimensions")
        mats.append(rows)
        pos = k + 1
    if len(mats) % 3:
        raise ValueError("number of matrices is not a multiple of 3")
    return [tuple(mats[3 * r:3 * r + 3]) for r in range(len(mats) // 3)]


# ------------------------------------------------------------------------------------------------ algebra
def shape(M):
    return len(M), len(M[0])


def matmul(X, Y):
    return [[sum((X[i][l] * Y[l][j] for l in range(len(Y))), Fraction(0)) for j in range(len(Y[0]))]
            for i in range(len(X))]


def trace(X):
    return sum((X[i][i] for i in range(len(X))), Fraction(0))


def term_matrices(terms):
    """M_j = a_j b_j c_j (n x n) for every term."""
    return [matmul(matmul(a, b), c) for a, b, c in terms]


def brent_ok(fmt, terms):
    """Exact check of all n^2 m^2 p^2 Brent equations over Q."""
    n, m, p = fmt
    acc = {}
    for a, b, c in terms:
        nza = [(i, j, a[i][j]) for i in range(n) for j in range(m) if a[i][j]]
        nzb = [(j, k, b[j][k]) for j in range(m) for k in range(p) if b[j][k]]
        nzc = [(k, i, c[k][i]) for k in range(p) for i in range(n) if c[k][i]]
        for (i1, j1, x), (j2, k2, y), (k3, i3, z) in itertools.product(nza, nzb, nzc):
            key = (i1, j1, j2, k2, k3, i3)
            acc[key] = acc.get(key, 0) + x * y * z
    for i1, j1, j2, k2, k3, i3 in itertools.product(range(n), range(m), range(m), range(p), range(p), range(n)):
        want = 1 if (j1 == j2 and k2 == k3 and i3 == i1) else 0
        if acc.get((i1, j1, j2, k2, k3, i3), 0) != want:
            return False
    return True


def is_power_of_two(q):
    return q > 0 and q & (q - 1) == 0


def inverse(M):
    k = len(M)
    A = [list(row) + [Fraction(int(i == j)) for j in range(k)] for i, row in enumerate(M)]
    for col in range(k):
        piv = next((r for r in range(col, k) if A[r][col] != 0), None)
        if piv is None:
            return None
        A[col], A[piv] = A[piv], A[col]
        f = A[col][col]
        A[col] = [x / f for x in A[col]]
        for r in range(k):
            if r != col and A[r][col] != 0:
                g = A[r][col]
                A[r] = [x - g * y for x, y in zip(A[r], A[col])]
    return [row[k:] for row in A]


def random_invertible(k, rng):
    while True:
        M = [[Fraction(rng.randint(-3, 3), rng.choice([1, 1, 2, 3, 5])) for _ in range(k)] for _ in range(k)]
        Mi = inverse(M)
        if Mi is not None:
            return M, Mi


def sandwich(terms, fmt, rng):
    """(lambda_r P a_r Q^-1, mu_r Q b_r R^-1, (lambda_r mu_r)^-1 R c_r P^-1) with seeded random P, Q, R, scalars."""
    n, m, p = fmt
    P, Pi = random_invertible(n, rng)
    Q, Qi = random_invertible(m, rng)
    R, Ri = random_invertible(p, rng)
    out = []
    for a, b, c in terms:
        lam = Fraction(rng.choice([1, 2, 3, 5, 7]), rng.choice([1, 2, 3, 4])) * rng.choice([1, -1])
        mu = Fraction(rng.choice([1, 2, 3, 5]), rng.choice([1, 3, 4, 7])) * rng.choice([1, -1])
        out.append(([[lam * x for x in row] for row in matmul(matmul(P, a), Qi)],
                    [[mu * x for x in row] for row in matmul(matmul(Q, b), Ri)],
                    [[x / (lam * mu) for x in row] for row in matmul(matmul(R, c), Pi)]))
    return out


def certificate_value(terms, cert):
    """tr(M_{j_1} ... M_{j_k}) for the term numbers j_1, ..., j_k of the certificate."""
    M = term_matrices(terms)
    prod = M[cert["terms"][0] - 1]
    for j in cert["terms"][1:]:
        prod = matmul(prod, M[j - 1])
    return trace(prod)


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", metavar="DIR", help="read the scheme files from DIR instead of downloading them")
    args = ap.parse_args()
    for name, spec in SCHEMES.items():
        print(f"== {name}")
        rng = random.Random("no-integral-form-z-half-schemes|" + name)
        raw = obtain(spec["url"], args.cache)
        digest = hashlib.sha256(raw).hexdigest()
        if not check(f"{name} SHA-256", digest == spec["sha256"], digest):
            continue
        terms = parse_triadset(raw.decode("utf-8"))
        n, m, p = spec["format"]
        check(f"{name} number of terms", len(terms) == spec["rank"], str(len(terms)))
        check(f"{name} factor shapes",
              all(shape(a) == (n, m) and shape(b) == (m, p) and shape(c) == (p, n) for a, b, c in terms))
        dens = sorted({x.denominator for t in terms for M in t for row in M for x in row})
        check(f"{name} coefficients in Z[1/2], not all integers",
              all(is_power_of_two(d) for d in dens) and dens[-1] > 1, f"denominators {dens}")
        check(f"{name} valid over Q (all {n * n * m * m * p * p} Brent equations, exact)",
              brent_ok(spec["format"], terms))
        cert = CERTIFICATES[name]
        label = "tr(" + " ".join(f"M_{j}" for j in cert["terms"]) + ")"
        if len(cert["terms"]) > 1:  # a product of two factors is used only where every tr(M_j) is an integer
            singles = [trace(M) for M in term_matrices(terms)]
            check(f"{name} every single trace tr(M_j) is an integer, so one factor does not suffice",
                  all(x.denominator == 1 for x in singles),
                  "values " + ", ".join(str(x) for x in sorted(set(singles))))
        value = certificate_value(terms, cert)
        check(f"{name} certificate {label} = {cert['trace']}, not an integer",
              value == cert["trace"] and value.denominator != 1, f"{value}")
        T2 = sandwich(terms, spec["format"], rng)
        dens2 = max(x.denominator for t in T2 for M in t for row in M for x in row)
        value2 = certificate_value(T2, cert)
        check(f"{name} illustration: random sandwich + term scalings is valid and keeps {label}",
              brent_ok(spec["format"], T2) and value2 == value, f"largest denominator {dens2}, {label} = {value2}")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
