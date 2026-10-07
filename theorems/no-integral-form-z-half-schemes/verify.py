#!/usr/bin/env python3
"""Verifier for theorems/no-integral-form-z-half-schemes (see README.md in this folder).

What it does, in order:
  1. reads the two scheme files and AlphaEvolve's results notebook from data/ in this folder (copies of the pinned
     public files, kept under their licences), or with --download from their pinned public URLs (three downloads,
     nothing else is sent), or from local copies (--cache DIR), and checks their SHA-256 in every case;
  2. parses them (Maple "TriadSet" format) into exact rational matrices and checks the format and that every
     coefficient lies in Z[1/2] (denominators are powers of 2);
  3. checks over Q, exactly, that each file is a valid scheme: all n^2 m^2 p^2 Brent equations;
  4. forms the term matrices M_j = a_j b_j c_j (terms numbered 1..R in file order) and computes, with
     fractions.Fraction, the certificate of the note, the trace of a product of term matrices: tr(M_1) = 3/2 for
     <3,3,6;40> and tr(M_2 M_5) = 1/2 for <2,4,5;32>; for <2,4,5;32> it also checks that every single trace
     tr(M_j) is 1 or 2 (an integer), so that a one-factor certificate does not exist there;
  5. as an illustration of the invariance (not part of the proof), applies a seeded random rational sandwich with
     random term scalings to each scheme, re-checks the Brent equations and recomputes the certificate, which must
     be unchanged;
  6. reads the matrices printed in the proof of README.md (term 1 of <3,3,6;40> with M_1; terms 2 and 5 of
     <2,4,5;32> with M_2, M_5 and M_2 M_5) and the printed certificate values, and checks that they equal the file's
     terms and the products computed from them;
  7. parses decomposition_245 from AlphaEvolve's notebook (mathematical_results.ipynb at the pinned commit) and
     checks that it equals the <2,4,5;32> file term by term, in the same order.
Exit code 0 only if every check passes; 1 otherwise.

Usage (from the repository root):
    python theorems/no-integral-form-z-half-schemes/verify.py              # offline, the copies in data/
    python theorems/no-integral-form-z-half-schemes/verify.py --download   # fetch the pinned URLs instead
    python theorems/no-integral-form-z-half-schemes/verify.py --cache DIR
With --cache, nothing is downloaded: each file is read from DIR/<sha1 hex of its URL> or, if that does not exist,
from DIR/<file name> (2x4x5_tensor.mpl, 3x3x6_tensor.mpl, mathematical_results.ipynb). Standard library only;
deterministic.

Conventions. A scheme for <n,m,p> is a list of terms (a_r, b_r, c_r) with a_r of size n x m, b_r of size m x p and
c_r of size p x n, such that sum_r a_r[i][j] * b_r[j'][k] * c_r[k'][i'] = [j = j'] [k = k'] [i = i'] for all
indices (the Brent equations). The files state this as A.B = sum_r <a_r, A> <b_r, B> c_r^T, where <X, A> is the sum
of the entrywise products; this is the same condition.
"""
import argparse
import ast
import hashlib
import itertools
import json
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
    "<2,4,5;32>": {"terms": [2, 5], "trace": Fraction(1, 2), "single_traces": {Fraction(1), Fraction(2)}},
}
# AlphaEvolve's published results notebook at a pinned commit; decomposition_245 is the <2,4,5> rank-32 scheme.
ALPHAEVOLVE = {
    "url": ("https://raw.githubusercontent.com/google-deepmind/alphaevolve_results/"
            "4226acbf237ff9ad10ba7673a2af127a2d8a5971/mathematical_results.ipynb"),
    "sha256": "2cce2543e48c89aa3e91614272a698a0147dd2548ea11cf92f1292b7435d38ff",
    "variable": "decomposition_245",
}
README = Path(__file__).resolve().with_name("README.md")
USER_AGENT = "complexity-pairs-dataset theorems verifier (python urllib)"

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ input
DATA = Path(__file__).resolve().with_name("data")


def obtain(url, cache, download=False):
    name = url.rsplit("/", 1)[1]
    if cache is None and not download:
        path = DATA / name
        print(f"reading {name} from data/")
        return path.read_bytes()
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


# ------------------------------------------------------------------------------------------------ README data
def parse_printed(text):
    """Matrices printed in a part of the README proof: 'NAME = [ r1 ; r2 ; ... ]' (rows separated by semicolons; for a
    term matrix also 'M_j = a_j b_j c_j = [ ... ]') and 'NAME = the R×C matrix with a single nonzero entry, V, in row I
    and column J'."""
    out = {}
    for name, body in re.findall(r"\b([abcM]_\d+(?: M_\d+)?) = (?:a_\d+ b_\d+ c_\d+ = )?\[([^\]]*)\]", text):
        out[name] = [[Fraction(tok) for tok in row.split()] for row in body.split(";")]
    for name, r, c, v, i, j in re.findall(
            r"\b([abc]_\d+) = the (\d+)×(\d+) matrix with a single nonzero entry, (-?[\d/]+), in row (\d+) and "
            r"column (\d+)", text):
        M = [[Fraction(0)] * int(c) for _ in range(int(r))]
        M[int(i) - 1][int(j) - 1] = Fraction(v)
        out[name] = M
    return out


def readme_parts():
    """The printed data of Part 2 (<3,3,6;40>) and Part 1 (<2,4,5;32>) of the README proof, and the full text."""
    text = README.read_text(encoding="utf-8")
    proof = text[text.index("**Proof of the Theorem.**"):text.index("## Relation to the source")]
    part2 = proof[proof.index("*Part 2 (S₂"):proof.index("*Part 1 (S₁")]
    part1 = proof[proof.index("*Part 1 (S₁"):]
    return {"<3,3,6;40>": parse_printed(part2), "<2,4,5;32>": parse_printed(part1)}, proof


def check_printed(name, terms, printed, proof_text):
    """The README's printed terms and products equal the file's terms and the products computed from them."""
    cert = CERTIFICATES[name]
    js = cert["terms"]
    same_terms = all(printed.get(f"{x}_{j}") == terms[j - 1][idx] for j in js for idx, x in enumerate("abc"))
    check(f"{name} README: printed " + ", ".join(f"a_{j}, b_{j}, c_{j}" for j in js)
          + " equal the file's term" + ("s " if len(js) > 1 else " ") + " and ".join(str(j) for j in js), same_terms)
    M = term_matrices(terms)
    products = {f"M_{j}": M[j - 1] for j in js}
    if len(js) == 2:
        products[f"M_{js[0]} M_{js[1]}"] = matmul(M[js[0] - 1], M[js[1] - 1])
    same_products = all(printed.get(key) == val for key, val in products.items())
    check(f"{name} README: printed " + ", ".join(products) + " equal the products computed from the file",
          same_products)
    label = "tr(" + " ".join(f"M_{j}" for j in js) + f") = {cert['trace']}"
    check(f"{name} README: printed certificate value '{label}'", label in proof_text)


# ------------------------------------------------------------------------------------------------ AlphaEvolve
def parse_alphaevolve(raw, fmt):
    """decomposition_245 from the notebook: three factor matrices of shapes (n*m, R), (m*p, R), (p*n, R); column r
    gives a_r[i][j] = F1[i*m + j][r], b_r[j][k] = F2[j*p + k][r], c_r[k][i] = F3[k*n + i][r] (the notebook's own
    verification builds T[i*m + j][j*p + k][k*n + i] = 1, the convention of the files)."""
    n, m, p = fmt
    nb = json.loads(raw.decode("utf-8"))
    var = ALPHAEVOLVE["variable"]
    src = next("".join(c["source"]) for c in nb["cells"]
               if c.get("cell_type") == "code" and f"{var} = " in "".join(c["source"]))
    src = src[src.index(f"{var} = "):]
    arrays = []
    for _ in range(3):
        i = src.index("np.array(")
        k = src.index("[", i)
        depth, e = 0, k
        while True:
            if src[e] == "[":
                depth += 1
            elif src[e] == "]":
                depth -= 1
                if depth == 0:
                    break
            e += 1
        arrays.append([[Fraction(x) for x in row] for row in ast.literal_eval(src[k:e + 1])])
        src = src[e + 1:]
    F1, F2, F3 = arrays
    R = len(F1[0])
    if (len(F1), len(F2), len(F3)) != (n * m, m * p, p * n) or any(len(row) != R for F in arrays for row in F):
        raise ValueError("unexpected factor matrix shapes in the notebook")
    return [([[F1[i * m + j][r] for j in range(m)] for i in range(n)],
             [[F2[j * p + k][r] for k in range(p)] for j in range(m)],
             [[F3[k * n + i][r] for i in range(n)] for k in range(p)]) for r in range(R)]


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cache", metavar="DIR", help="read the files from DIR instead of data/")
    ap.add_argument("--download", action="store_true", help="fetch the files from their pinned URLs instead of data/")
    args = ap.parse_args()
    printed, proof_text = readme_parts()
    parsed = {}
    for name, spec in SCHEMES.items():
        print(f"== {name}")
        rng = random.Random("no-integral-form-z-half-schemes|" + name)
        raw = obtain(spec["url"], args.cache, args.download)
        digest = hashlib.sha256(raw).hexdigest()
        if not check(f"{name} SHA-256", digest == spec["sha256"], digest):
            continue
        terms = parse_triadset(raw.decode("utf-8"))
        parsed[name] = terms
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
            expected = cert["single_traces"]
            check(f"{name} every single trace tr(M_j) is " + " or ".join(str(x) for x in sorted(expected))
                  + " (an integer), so one factor does not suffice",
                  set(singles) == expected and all(x.denominator == 1 for x in singles),
                  "values " + ", ".join(str(x) for x in sorted(set(singles))))
        value = certificate_value(terms, cert)
        check(f"{name} certificate {label} = {cert['trace']}, not an integer",
              value == cert["trace"] and value.denominator != 1, f"{value}")
        T2 = sandwich(terms, spec["format"], rng)
        dens2 = max(x.denominator for t in T2 for M in t for row in M for x in row)
        value2 = certificate_value(T2, cert)
        check(f"{name} illustration: random sandwich + term scalings is valid and keeps {label}",
              brent_ok(spec["format"], T2) and value2 == value, f"largest denominator {dens2}, {label} = {value2}")
        check_printed(name, terms, printed[name], proof_text)
    print("== AlphaEvolve's decomposition_245")
    raw = obtain(ALPHAEVOLVE["url"], args.cache, args.download)
    digest = hashlib.sha256(raw).hexdigest()
    if check("AlphaEvolve notebook SHA-256", digest == ALPHAEVOLVE["sha256"], digest) and "<2,4,5;32>" in parsed:
        ae = parse_alphaevolve(raw, SCHEMES["<2,4,5;32>"]["format"])
        file_terms = parsed["<2,4,5;32>"]
        check("<2,4,5;32> file equals AlphaEvolve's decomposition_245 term by term, in the same order",
              ae == file_terms, f"{len(ae)} terms in the notebook, {len(file_terms)} in the file")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
