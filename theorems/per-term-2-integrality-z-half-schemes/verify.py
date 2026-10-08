#!/usr/bin/env python3
"""Verifier for theorems/per-term-2-integrality-z-half-schemes (see README.md in this folder).

What it does, in order (exact rational arithmetic throughout; the proof is in the README):
  1. reads the two pinned scheme files from the data/ folder of theorems/no-integral-form-z-half-schemes (the
     unmodified copies kept there under their licence; nothing is copied into this folder), or with --download from
     their pinned public URLs (two downloads, nothing else is sent), or from local copies (--cache DIR), and checks
     their SHA-256 in every case;
  2. parses them, checks the format, that all coefficients lie in Z[1/2], and all Brent equations over Q;
  3. <3,3,6;40>: every single trace t(r,r,r) = tr(a_r b_r c_r) has negative 2-adic valuation (3/2 x16, 5/4 x24),
     and t(1,1,1) = 3/2 is the certificate tr(M_1) of theorems/no-integral-form-z-half-schemes;
  4. <2,4,5;32>: the table t(r,s,t) = tr(a_r b_s c_t) for all 32^3 index triples; the balanced products of the
     README (singles, a-, b- and c-pairs, 3-cycles) with negative 2-adic valuation; the certificates quoted
     in the README; that every product type has matching index multisets;
  5. the edge counts (196 and 218) and the minimum hitting sets of the two obstruction hypergraphs, 18 (without the
     c-pairs) and 20 (with them),
     each by two different exact algorithms, with witnesses;
  6. the explicit equivalent form of the README (U = I_2, V, W, power-of-two term scalings): obtained from
     <2,4,5;32> by (E) (checked through relations without inverses), valid scheme, exactly 12 terms 2-integral
     (numbers 5, 6, 8, 9, 10, 11, 13, 21, 28, 29, 30, 31), all coefficients of these 12 terms integers, and its
     2-integral terms contain no obstructed set (as the theorem requires);
  7. Lemma 1 exactly after a seeded random rational sandwich with random term scalings: every t'(r,s,t) equals
     lambda_r mu_s / (lambda_t mu_t) t(r,s,t), and every balanced product is unchanged (illustration);
  8. a negative control: the standard <2,4,5> algorithm (40 integer terms) after a seeded random rational sandwich
     with term scalings has no balanced product of these types with negative 2-adic valuation.
Exit code 0 only if every check passes; 1 otherwise.

Usage (from the repository root):
    python theorems/per-term-2-integrality-z-half-schemes/verify.py              # offline (vendored copies)
    python theorems/per-term-2-integrality-z-half-schemes/verify.py --download   # fetch the two pinned URLs instead
    python theorems/per-term-2-integrality-z-half-schemes/verify.py --cache DIR
With --cache, nothing is downloaded: each file is read from DIR/<sha1 hex of its URL> or, if that does not exist,
from DIR/<file name> (2x4x5_tensor.mpl, 3x3x6_tensor.mpl). Standard library only; deterministic; a few seconds.

Conventions as in theorems/no-integral-form-z-half-schemes: a term (a, b, c) has a: n x m, b: m x p, c: p x n;
terms are numbered 1..R in file order; the Brent equations are sum_r a_r[i][j] b_r[j'][k] c_r[k'][i'] =
[j = j'][k = k'][i = i'].
"""
import argparse
import hashlib
import itertools
import random
import re
import sys
import time
import urllib.request
from collections import Counter
from fractions import Fraction
from pathlib import Path

BASE = ("https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/"
        "64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/known/")
SCHEMES = {
    "<2,4,5;32>": {"url": BASE + "tensor/2x4x5_tensor.mpl", "format": (2, 4, 5), "rank": 32,
                   "sha256": "e03c7743a60f53ae21a3413af4a5f019600a12befc8ed22ffdf2baa8b0f7dd4b"},
    "<3,3,6;40>": {"url": BASE + "tensor/3x3x6_tensor.mpl", "format": (3, 3, 6), "rank": 40,
                   "sha256": "3e79357c5d2540e5c54c2a5f484f17009f70799b10bd45ed8e4bf893b5e223ab"},
}
USER_AGENT = "complexity-pairs-dataset theorems verifier (python urllib)"
# the explicit equivalent form of <2,4,5;32> (README): U = I_2, these V and W, power-of-two scalings
V_MAT = [[0, 0, 0, 2], [1, 0, 0, -1], [0, 1, 0, -1], [0, 0, 1, -1]]
W_MAT = [[2, -2, -2, -2, 0], [0, 2, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 2, 0], [-1, 1, 1, 1, 2]]
FORM_INTEGRAL = [5, 6, 8, 9, 10, 11, 13, 21, 28, 29, 30, 31]

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ input
# the unmodified copies of the pinned files, kept (with their licence) in the data/ folder of the published note
DATA = Path(__file__).resolve().parent.parent / "no-integral-form-z-half-schemes" / "data"


def obtain(url, cache, download=False):
    name = url.rsplit("/", 1)[1]
    if cache is None and not download:
        path = DATA / name
        print(f"reading {name} from theorems/no-integral-form-z-half-schemes/data/")
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
    """Matrices inside 'TriadSet(...)' in file order, grouped into terms (a, b, c)."""
    body = text[text.index("TriadSet("):]
    mats, pos = [], 0
    while True:
        i = body.find("Matrix(", pos)
        if i < 0:
            break
        head_end = body.index("[", i)
        rows_dim, cols_dim = (int(x) for x in body[i + len("Matrix("):head_end].split(",")[:2])
        depth, k = 0, head_end
        while True:
            if body[k] == "[":
                depth += 1
            elif body[k] == "]":
                depth -= 1
                if depth == 0:
                    break
            k += 1
        rows = [[Fraction(tok.strip()) for tok in row.split(",")]
                for row in re.findall(r"\[([^\[\]]*)\]", body[head_end + 1:k])]
        if len(rows) != rows_dim or any(len(row) != cols_dim for row in rows):
            raise ValueError(f"matrix at offset {i}: declared {rows_dim}x{cols_dim}, found other dimensions")
        mats.append(rows)
        pos = k + 1
    if len(mats) % 3:
        raise ValueError("number of matrices is not a multiple of 3")
    return [tuple(mats[3 * r:3 * r + 3]) for r in range(len(mats) // 3)]


# ------------------------------------------------------------------------------------------------ algebra
def matmul(X, Y):
    return [[sum((X[i][l] * Y[l][j] for l in range(len(Y))), Fraction(0)) for j in range(len(Y[0]))]
            for i in range(len(X))]


def inverse(M):
    k = len(M)
    A = [[Fraction(x) for x in row] + [Fraction(int(i == j)) for j in range(k)] for i, row in enumerate(M)]
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


def brent_ok(fmt, terms):
    n, m, p = fmt
    acc = {}
    for a, b, c in terms:
        nza = [(i, j, a[i][j]) for i in range(n) for j in range(m) if a[i][j]]
        nzb = [(j, k, b[j][k]) for j in range(m) for k in range(p) if b[j][k]]
        nzc = [(k, i, c[k][i]) for k in range(p) for i in range(n) if c[k][i]]
        for (i1, j1, x), (j2, k2, y), (k3, i3, z) in itertools.product(nza, nzb, nzc):
            key = (i1, j1, j2, k2, k3, i3)
            acc[key] = acc.get(key, 0) + x * y * z
    for key in itertools.product(range(n), range(m), range(m), range(p), range(p), range(n)):
        i1, j1, j2, k2, k3, i3 = key
        if acc.get(key, 0) != (1 if (j1 == j2 and k2 == k3 and i3 == i1) else 0):
            return False
    return True


def v2(x):
    """2-adic valuation of a nonzero rational; None for 0."""
    if x == 0:
        return None
    num, den, v = abs(x.numerator), x.denominator, 0
    while num % 2 == 0:
        num //= 2
        v += 1
    while den % 2 == 0:
        den //= 2
        v -= 1
    return v


def neg(x):
    k = v2(x)
    return k is not None and k < 0


def trace_table(terms):
    """t[r][s][u] = tr(a_r b_s c_u) (0-based indices)."""
    R = len(terms)
    n = len(terms[0][0])
    AB = [[matmul(terms[r][0], terms[s][1]) for s in range(R)] for r in range(R)]
    return [[[sum((AB[r][s][i][k] * terms[u][2][k][i] for i in range(n) for k in range(len(terms[u][2]))),
                  Fraction(0)) for u in range(R)] for s in range(R)] for r in range(R)]


# balanced products: name -> list of index triples (r, s, t), as functions of the term numbers involved
PRODUCTS = {
    "single": lambda r: [(r, r, r)],
    "a_pair": lambda r, t: [(r, t, t), (t, r, r)],
    "b_pair": lambda r, t: [(t, r, t), (r, t, r)],
    "c_pair": lambda r, t: [(r, r, t), (t, t, r)],
    "cycle": lambda r, s, t: [(r, s, t), (t, r, s), (s, t, r)],
}


def balanced(triples):
    return (sorted(x[0] for x in triples) == sorted(x[1] for x in triples) == sorted(x[2] for x in triples))


def product(tt, triples):
    out = Fraction(1)
    for r, s, u in triples:
        out *= tt[r][s][u]
    return out


def obstructions(tt):
    """Obstructed index sets (0-based) of each product type."""
    R = len(tt)
    ob = {"single": [frozenset([r]) for r in range(R) if neg(product(tt, PRODUCTS["single"](r)))]}
    for name in ("a_pair", "b_pair", "c_pair"):
        ob[name] = {frozenset((r, t)) for r, t in itertools.combinations(range(R), 2)
                    if neg(product(tt, PRODUCTS[name](r, t)))}
    ob["cycle_ordered"] = [(r, s, t) for r in range(R) for s in range(R) for t in range(R)
                           if neg(product(tt, PRODUCTS["cycle"](r, s, t)))]
    ob["cycle"] = {frozenset(c) for c in ob["cycle_ordered"]}
    return ob


# ------------------------------------------------------------------------------------------------ hitting sets
def max_free_set(R, edges):
    """Largest vertex set containing no edge: bitmask branch and bound over the vertices in order."""
    emask = sorted({sum(1 << v for v in e) for e in edges})
    by_top = [[] for _ in range(R)]
    for em in emask:
        by_top[em.bit_length() - 1].append(em)
    best = [0, 0]

    def rec(v, chosen, size):
        if size + (R - v) <= best[0]:
            return
        if v == R:
            best[0], best[1] = size, chosen
            return
        new = chosen | (1 << v)
        if all((em & new) != em for em in by_top[v]):
            rec(v + 1, new, size + 1)
        rec(v + 1, chosen, size)
    rec(0, 0, 0)
    return best[0], [v for v in range(R) if best[1] >> v & 1]


def hitting_set_exists(edges, k):
    """Is there a hitting set of size <= k? Branch on the vertices of an unhit edge (smallest edges first);
    prune with a greedy packing of pairwise disjoint unhit edges (a lower bound)."""
    E = sorted({sum(1 << v for v in e) for e in edges}, key=lambda m: (bin(m).count("1"), m))

    def lower_bound(hit):
        used = cnt = 0
        for m in E:
            if m & hit == 0 and m & used == 0:
                used |= m
                cnt += 1
        return cnt

    def rec(hit, k):
        unhit = next((m for m in E if m & hit == 0), None)
        if unhit is None:
            return True
        if k == 0 or lower_bound(hit) > k:
            return False
        x = unhit
        while x:
            low = x & -x
            if rec(hit | low, k - 1):
                return True
            x ^= low
        return False
    return rec(0, k)


# ------------------------------------------------------------------------------------------------ transforms
def random_invertible(k, rng):
    while True:
        M = [[Fraction(rng.randint(-3, 3), rng.choice([1, 1, 2, 3, 5])) for _ in range(k)] for _ in range(k)]
        if inverse(M) is not None:
            return M


def sandwich(terms, fmt, rng):
    """(lam_r U a_r V^-1, mu_r V b_r W^-1, (lam_r mu_r)^-1 W c_r U^-1) with seeded random U, V, W and scalars."""
    n, m, p = fmt
    U, V, W = random_invertible(n, rng), random_invertible(m, rng), random_invertible(p, rng)
    Ui, Vi, Wi = inverse(U), inverse(V), inverse(W)
    out, lams, mus = [], [], []
    for a, b, c in terms:
        lam = Fraction(rng.choice([1, 2, 3, 5, 7]), rng.choice([1, 2, 3, 4])) * rng.choice([1, -1])
        mu = Fraction(rng.choice([1, 2, 3, 5]), rng.choice([1, 3, 4, 8])) * rng.choice([1, -1])
        lams.append(lam)
        mus.append(mu)
        out.append(([[lam * x for x in row] for row in matmul(matmul(U, a), Vi)],
                    [[mu * x for x in row] for row in matmul(matmul(V, b), Wi)],
                    [[x / (lam * mu) for x in row] for row in matmul(matmul(W, c), Ui)]))
    return out, lams, mus


def standard_scheme(fmt):
    n, m, p = fmt
    unit = lambda rows, cols, i, j: [[Fraction(int((x, y) == (i, j))) for y in range(cols)] for x in range(rows)]  # noqa
    return [(unit(n, m, i, j), unit(m, p, j, k), unit(p, n, k, i))
            for i, j, k in itertools.product(range(n), range(m), range(p))]


def det(M):
    A = [[Fraction(x) for x in row] for row in M]
    k, d = len(A), Fraction(1)
    for c in range(k):
        piv = next((r for r in range(c, k) if A[r][c] != 0), None)
        if piv is None:
            return Fraction(0)
        if piv != c:
            A[c], A[piv] = A[piv], A[c]
            d = -d
        d *= A[c][c]
        for r in range(c + 1, k):
            f = A[r][c] / A[c][c]
            A[r] = [x - f * y for x, y in zip(A[r], A[c])]
    return d


def min_v2(M):
    return min(v2(x) for row in M for x in row if x != 0)


def explicit_form(terms):
    """The form of the README: U = I_2, V = V_MAT, W = W_MAT, lam_r = 2^-nu(a_r V^-1), mu_r = 2^-nu(V b_r W^-1)."""
    V = [[Fraction(x) for x in row] for row in V_MAT]
    W = [[Fraction(x) for x in row] for row in W_MAT]
    Vi, Wi = inverse(V), inverse(W)
    out = []
    for a, b, c in terms:
        A = matmul(a, Vi)
        B = matmul(matmul(V, b), Wi)
        C = matmul(W, c)
        lam, mu = Fraction(2) ** (-min_v2(A)), Fraction(2) ** (-min_v2(B))
        out.append(([[lam * x for x in row] for row in A], [[mu * x for x in row] for row in B],
                    [[x / (lam * mu) for x in row] for row in C], lam, mu))
    return out


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--download", action="store_true",
                     help="fetch the two pinned files from their URLs instead of reading the vendored copies")
    src.add_argument("--cache", metavar="DIR", help="read the scheme files from DIR (no network)")
    args = ap.parse_args()
    t_start = time.time()
    schemes = {}
    for name, spec in SCHEMES.items():
        raw = obtain(spec["url"], args.cache, args.download)
        digest = hashlib.sha256(raw).hexdigest()
        if not check(f"{name} SHA-256", digest == spec["sha256"], digest):
            continue
        terms = parse_triadset(raw.decode("utf-8"))
        n, m, p = spec["format"]
        dens = sorted({x.denominator for t in terms for M in t for row in M for x in row})
        check(f"{name} {len(terms)} terms of shapes {n}x{m}, {m}x{p}, {p}x{n}; coefficients in Z[1/2]",
              len(terms) == spec["rank"] and all(len(a) == n and len(a[0]) == m and len(b) == m and len(b[0]) == p
                                                 and len(c) == p and len(c[0]) == n for a, b, c in terms)
              and all(d & (d - 1) == 0 for d in dens), f"denominators {dens}")
        check(f"{name} valid over Q (all {n * n * m * m * p * p} Brent equations, exact)", brent_ok(spec["format"], terms))
        schemes[name] = terms
    if len(schemes) < 2:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1

    # 3. <3,3,6;40>: single traces
    s2 = schemes["<3,3,6;40>"]
    singles = [matmul(matmul(a, b), c) for a, b, c in s2]
    vals = [sum((M[i][i] for i in range(3)), Fraction(0)) for M in singles]
    hist = Counter(str(x) for x in vals)
    check("<3,3,6;40> every t(r,r,r) = tr(a_r b_r c_r) has negative 2-adic valuation: 3/2 x16, 5/4 x24 (all 40 terms)",
          all(neg(x) for x in vals) and hist == Counter({"3/2": 16, "5/4": 24}), str(dict(hist)))
    check("<3,3,6;40> t(1,1,1) = 3/2, the certificate tr(M_1) of theorems/no-integral-form-z-half-schemes",
          vals[0] == Fraction(3, 2), str(vals[0]))

    # 4. <2,4,5;32>: trace table and obstructions
    s1 = schemes["<2,4,5;32>"]
    R = len(s1)
    tt = trace_table(s1)
    ob = obstructions(tt)
    single_hist = Counter(str(tt[r][r][r]) for r in range(R))
    check("<2,4,5;32> every single trace t(r,r,r) is an integer (1 x24, 2 x8): no single obstruction",
          not ob["single"] and single_hist == Counter({"1": 24, "2": 8}), str(dict(single_hist)))
    check("<2,4,5;32> obstructed pairs: a-pairs 76, b-pairs 0, c-pairs 54 (32 also a-pairs, 22 c-pairs only)",
          (len(ob["a_pair"]), len(ob["b_pair"]), len(ob["c_pair"]), len(ob["c_pair"] & ob["a_pair"]),
           len(ob["c_pair"] - ob["a_pair"] - ob["b_pair"])) == (76, 0, 54, 32, 22),
          f"{len(ob['a_pair'])}, {len(ob['b_pair'])}, {len(ob['c_pair'])}, {len(ob['c_pair'] & ob['a_pair'])}, "
          f"{len(ob['c_pair'] - ob['a_pair'] - ob['b_pair'])}")
    check("<2,4,5;32> obstructed 3-cycles: 384 ordered triples (r,s,t), all with distinct indices, 120 index sets",
          len(ob["cycle_ordered"]) == 384 and all(len(set(c)) == 3 for c in ob["cycle_ordered"])
          and len(ob["cycle"]) == 120, f"{len(ob['cycle_ordered'])}, {len(ob['cycle'])}")
    t = lambda r, s, u: tt[r - 1][s - 1][u - 1]  # noqa: E731  (1-based term numbers)
    cert = [("a-pair(1,3) = t(1,3,3) t(3,1,1)", [t(1, 3, 3), t(3, 1, 1)], [-1, Fraction(-1, 2)], Fraction(1, 2)),
            ("c-pair(3,10) = t(3,3,10) t(10,10,3)", [t(3, 3, 10), t(10, 10, 3)], [-1, Fraction(-1, 2)], Fraction(1, 2)),
            ("cycle(1,3,17) = t(1,3,17) t(17,1,3) t(3,17,1)", [t(1, 3, 17), t(17, 1, 3), t(3, 17, 1)],
             [1, Fraction(-1, 4), Fraction(-1, 2)], Fraction(1, 8))]
    for label, got, want, prod in cert:
        pv = got[0]
        for g in got[1:]:
            pv *= g
        check(f"<2,4,5;32> certificate {label} = {' * '.join(str(x) for x in want)} = {prod}",
              got == want and pv == prod)
    check("<2,4,5;32> c-pair(3,10) is not an a- or b-pair", frozenset((2, 9)) not in ob["a_pair"] | ob["b_pair"])
    check("all five product types have matching index multisets (balanced), for every choice of their term numbers "
          "in {1, 2, 3, 4} (4 + 3 x 16 + 64 index tuples; the property depends only on the pattern of equal numbers)",
          all(balanced(PRODUCTS["single"](r)) for r in range(4))
          and all(balanced(PRODUCTS[k](r, s)) for k in ("a_pair", "b_pair", "c_pair")
                  for r in range(4) for s in range(4))
          and all(balanced(PRODUCTS["cycle"](r, s, u)) for r in range(4) for s in range(4) for u in range(4)))

    # 5. hitting sets
    H1 = list(ob["single"]) + list(ob["a_pair"] | ob["b_pair"]) + list(ob["cycle"])
    H2 = H1 + list(ob["c_pair"])
    for label, H, tau, n_edges in (("without c-pairs", H1, 18, 196), ("with c-pairs", H2, 20, 218)):
        size, free = max_free_set(R, H)
        free_ok = all(not e <= set(free) for e in H)
        m1 = R - size
        m2_ok = hitting_set_exists(H, tau) and not hitting_set_exists(H, tau - 1)
        check(f"minimum hitting set {label} = {tau} ({n_edges} distinct edges): branch and bound on edge-free sets, "
              f"and branching on unhit edges", m1 == tau and free_ok and m2_ok and len(set(H)) == n_edges,
              f"largest edge-free set {size}: terms {[v + 1 for v in free]}")

    # 6. the explicit form
    form = explicit_form(s1)
    fterms = [(A, B, C) for A, B, C, _, _ in form]
    V = [[Fraction(x) for x in row] for row in V_MAT]
    W = [[Fraction(x) for x in row] for row in W_MAT]

    def ratio(X, Y):
        """The scalar s with X = s Y (Y nonzero), or None."""
        s = None
        for rx, ry in zip(X, Y):
            for x, y in zip(rx, ry):
                if y == 0:
                    if x != 0:
                        return None
                elif s is None:
                    s = x / y
                elif x != s * y:
                    return None
        return s

    def power_of_two(q):
        return q > 0 and q.numerator & (q.numerator - 1) == 0 and q.denominator & (q.denominator - 1) == 0

    # (E) with U = I_2 is equivalent to a' V = lam a, b' W = mu V b, lam mu c' = W c (no inverses used here)
    is_e, scal = True, []
    for (a, b, c), (A, B, C) in zip(s1, fterms):
        lam = ratio(matmul(A, V), a)
        mu = ratio(matmul(B, W), matmul(V, b))
        ok = lam is not None and mu is not None and power_of_two(lam) and power_of_two(mu)
        ok = ok and [[lam * mu * x for x in row] for row in C] == matmul(W, c)
        is_e &= ok
        scal.append((lam, mu))
    check("explicit form: a'_r V = lam_r a_r, b'_r W = mu_r V b_r and lam_r mu_r c'_r = W c_r for every term, with "
          "lam_r, mu_r powers of 2, i.e. (E) with U = I_2 and the stated V, W (det V = -2, det W = 32)",
          is_e and det(V) == -2 and det(W) == 32,
          f"det V = {det(V)}, det W = {det(W)}, scalings {sorted({str(x) for s in scal for x in s if x is not None})}")
    check("explicit form: valid over Q (all 1600 Brent equations)", brent_ok((2, 4, 5), fterms))
    two_int = [r + 1 for r, (A, B, C) in enumerate(fterms)
               if all(x.denominator % 2 == 1 for M in (A, B, C) for row in M for x in row)]
    check("explicit form: exactly the 12 terms 5, 6, 8, 9, 10, 11, 13, 21, 28, 29, 30, 31 are 2-integral "
          "(all coefficients in Z_(2)); the other 20 are not", two_int == FORM_INTEGRAL, f"2-integral: {two_int}")
    z_int = all(x.denominator == 1 for r in FORM_INTEGRAL for M in fterms[r - 1] for row in M for x in row)
    check("explicit form: every coefficient of a'_r, b'_r, c'_r in these 12 terms is an integer (Corollary 1)",
          z_int, f"denominators in the other 20 terms: "
          f"{sorted({x.denominator for r in range(1, R + 1) if r not in FORM_INTEGRAL for M in fterms[r - 1] for row in M for x in row})}")
    ab_int = all(x.denominator % 2 == 1 for A, B, C in fterms for M in (A, B) for row in M for x in row)
    worst = Counter(min_v2(C) for A, B, C in fterms if min_v2(C) < 0)
    check("explicit form: every a'_r and b'_r is 2-integral; in the other 20 terms c'_r has a coefficient of "
          "2-adic valuation -1 (16 terms) or -2 (4 terms)", ab_int and worst == Counter({-1: 16, -2: 4}),
          str(dict(worst)))
    inside = [sorted(v + 1 for v in e) for e in H2 if all(v + 1 in FORM_INTEGRAL for v in e)]
    check("explicit form: its 12 2-integral terms contain no obstructed set (consistent with the theorem)",
          not inside, f"obstructed sets inside: {inside}")

    # 7. Lemma 1 and invariance after a random sandwich with term scalings (illustration)
    rng = random.Random("per-term-2-integrality-z-half-schemes")
    T2, lams, mus = sandwich(s1, (2, 4, 5), rng)
    tt2 = trace_table(T2)
    p1 = all(tt2[r][s][u] == lams[r] * mus[s] / (lams[u] * mus[u]) * tt[r][s][u]
             for r in range(R) for s in range(R) for u in range(R))
    changed = sum(tt2[r][s][u] != tt[r][s][u] for r in range(R) for s in range(R) for u in range(R))
    inv = all(product(tt2, PRODUCTS[k](r, s)) == product(tt, PRODUCTS[k](r, s))
              for k in ("a_pair", "b_pair", "c_pair") for r in range(R) for s in range(R))
    inv &= all(product(tt2, PRODUCTS["cycle"](r, s, u)) == product(tt, PRODUCTS["cycle"](r, s, u))
               for r in range(R) for s in range(R) for u in range(R))
    check("illustration: after a random sandwich with term scalings the form is valid, "
          "t'(r,s,t) = lam_r mu_s / (lam_t mu_t) t(r,s,t) for all 32768 triples (Lemma 1), "
          "and every balanced product is unchanged (Lemma 2)",
          brent_ok((2, 4, 5), T2) and p1 and inv, f"{changed} of 32768 traces changed")

    # 8. negative control
    std, _, _ = sandwich(standard_scheme((2, 4, 5)), (2, 4, 5), rng)
    obc = obstructions(trace_table(std))
    flagged = sum(len(obc[k]) for k in ("single", "a_pair", "b_pair", "c_pair", "cycle"))
    maxden = max(x.denominator for tm in std for M in tm for row in M for x in row)
    check("negative control: the standard <2,4,5> algorithm after a random sandwich with scalings is valid and "
          "has no obstruction of these types", brent_ok((2, 4, 5), std) and flagged == 0,
          f"largest denominator {maxden}, obstructed sets {flagged}")

    print(f"total {time.time() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
