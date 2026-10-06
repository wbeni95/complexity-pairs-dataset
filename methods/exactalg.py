"""Exact algebra over Q: matrices, univariate polynomials, real roots, factoring, LLL, number fields.

Conventions: a polynomial is a list of coefficients, LOWEST degree first, as Fractions (or ints); the zero
polynomial is []. All routines are exact except `real_root_approx`, which returns a rational interval of a
requested width around an exactly isolated real root.

Sources:
  * Sturm sequences for counting real roots: standard; e.g. Basu, Pollack, Roy, "Algorithms in Real Algebraic
    Geometry" [book, recalled].
  * Kronecker's factoring method (1882): evaluate at deg/2 + 1 integer points, try every divisor combination,
    interpolate and test divisibility. Exponential, but exact and fine for small degree and small coefficients
    [recalled; textbook, e.g. van der Waerden, Algebra I].
  * LLL: Lenstra, Lenstra, Lovasz (1982), Factoring polynomials with rational coefficients, Math. Ann. 261,
    doi:10.1007/BF01457454. The integer-relation use (finding a minimal polynomial from a numerical value) is the
    standard application described there and in Kannan, Lenstra, Lovasz (1988) [recalled].
"""
from __future__ import annotations

from fractions import Fraction
from itertools import product
from math import gcd, isqrt

# --------------------------------------------------------------------------------------------------------------
# Linear algebra over Q
# --------------------------------------------------------------------------------------------------------------


def rref(rows: list[list]) -> tuple[list[list[Fraction]], list[int]]:
    """Reduced row echelon form over Q. Returns (matrix, pivot columns)."""
    m = [[Fraction(x) for x in r] for r in rows]
    if not m:
        return m, []
    ncols = len(m[0])
    piv, r = [], 0
    for c in range(ncols):
        p = next((i for i in range(r, len(m)) if m[i][c] != 0), None)
        if p is None:
            continue
        m[r], m[p] = m[p], m[r]
        inv = 1 / m[r][c]
        m[r] = [x * inv for x in m[r]]
        for i in range(len(m)):
            if i != r and m[i][c] != 0:
                f = m[i][c]
                m[i] = [a - f * b for a, b in zip(m[i], m[r])]
        piv.append(c)
        r += 1
        if r == len(m):
            break
    return m, piv


def nullspace(rows: list[list]) -> list[list[Fraction]]:
    """A basis of {v : rows . v = 0} over Q (each vector scaled to coprime integers, first nonzero > 0)."""
    if not rows:
        return []
    ncols = len(rows[0])
    m, piv = rref(rows)
    free = [c for c in range(ncols) if c not in piv]
    basis = []
    for f in free:
        v = [Fraction(0)] * ncols
        v[f] = Fraction(1)
        for i, c in enumerate(piv):
            v[c] = -m[i][f]
        basis.append(primitive(v))
    return basis


def rank(rows: list[list]) -> int:
    return len(rref(rows)[1]) if rows else 0


def primitive(v: list) -> list[Fraction]:
    """Scale a rational vector to coprime integers with the first nonzero entry positive."""
    v = [Fraction(x) for x in v]
    den = 1
    for x in v:
        den = den * x.denominator // gcd(den, x.denominator)
    ints = [int(x * den) for x in v]
    g = 0
    for x in ints:
        g = gcd(g, abs(x))
    if g == 0:
        return v
    ints = [x // g for x in ints]
    first = next(x for x in ints if x != 0)
    if first < 0:
        ints = [-x for x in ints]
    return [Fraction(x) for x in ints]


def det_bareiss(mat: list[list[int]]) -> int:
    """Exact determinant of an integer matrix by Bareiss' fraction-free elimination."""
    a = [list(map(int, r)) for r in mat]
    n = len(a)
    if n == 0:
        return 1
    sign, prev = 1, 1
    for k in range(n - 1):
        if a[k][k] == 0:
            sw = next((i for i in range(k + 1, n) if a[i][k] != 0), None)
            if sw is None:
                return 0
            a[k], a[sw] = a[sw], a[k]
            sign = -sign
        for i in range(k + 1, n):
            for j in range(k + 1, n):
                a[i][j] = (a[i][j] * a[k][k] - a[i][k] * a[k][j]) // prev
        prev = a[k][k]
    return sign * a[n - 1][n - 1]


# --------------------------------------------------------------------------------------------------------------
# Univariate polynomials over Q (lowest degree first)
# --------------------------------------------------------------------------------------------------------------


def ptrim(p: list) -> list[Fraction]:
    p = [Fraction(x) for x in p]
    while p and p[-1] == 0:
        p.pop()
    return p


def pdeg(p: list) -> int:
    return len(ptrim(p)) - 1


def padd(p: list, q: list) -> list[Fraction]:
    n = max(len(p), len(q))
    return ptrim([(p[i] if i < len(p) else 0) + (q[i] if i < len(q) else 0) for i in range(n)])


def psub(p: list, q: list) -> list[Fraction]:
    return padd(p, [-x for x in q])


def pmul(p: list, q: list) -> list[Fraction]:
    p, q = ptrim(p), ptrim(q)
    if not p or not q:
        return []
    out = [Fraction(0)] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        if a:
            for j, b in enumerate(q):
                out[i + j] += a * b
    return ptrim(out)


def pdivmod(p: list, q: list) -> tuple[list[Fraction], list[Fraction]]:
    p, q = ptrim(p), ptrim(q)
    if not q:
        raise ZeroDivisionError("polynomial division by zero")
    quo = [Fraction(0)] * max(0, len(p) - len(q) + 1)
    r = p[:]
    while len(r) >= len(q) and r:
        c = r[-1] / q[-1]
        k = len(r) - len(q)
        quo[k] = c
        for i, b in enumerate(q):
            r[i + k] -= c * b
        r = ptrim(r)
    return ptrim(quo), r


def pmonic(p: list) -> list[Fraction]:
    p = ptrim(p)
    return [x / p[-1] for x in p] if p else []


def pgcd(p: list, q: list) -> list[Fraction]:
    a, b = ptrim(p), ptrim(q)
    while b:
        a, b = b, pdivmod(a, b)[1]
    return pmonic(a)


def pderiv(p: list) -> list[Fraction]:
    return ptrim([i * Fraction(c) for i, c in enumerate(p)][1:])


def peval(p: list, x):
    acc = 0
    for c in reversed(p):
        acc = acc * x + c
    return acc


def pint(p: list) -> list[int]:
    """Scale to a primitive integer polynomial with positive leading coefficient."""
    p = ptrim(p)
    if not p:
        return []
    v = primitive(list(reversed(p)))
    return [int(x) for x in reversed(v)]


def squarefree_part(p: list) -> list[Fraction]:
    p = ptrim(p)
    return pmonic(pdivmod(p, pgcd(p, pderiv(p)))[0]) if pdeg(p) > 0 else pmonic(p)


def pstr(p: list, var: str = "x") -> str:
    """Human-readable form, highest degree first, e.g. 'x^2 - 6x + 1'."""
    p = ptrim(p)
    if not p:
        return "0"
    terms = []
    for k in range(len(p) - 1, -1, -1):
        c = p[k]
        if c == 0:
            continue
        sign = "-" if c < 0 else "+"
        a = -c if c < 0 else c
        if k == 0:
            body = str(a)
        else:
            coef = "" if a == 1 else str(a)
            body = coef + (var if k == 1 else f"{var}^{k}")
        terms.append((sign, body))
    s = ("-" if terms[0][0] == "-" else "") + terms[0][1]
    for sign, body in terms[1:]:
        s += f" {sign} {body}"
    return s


# --------------------------------------------------------------------------------------------------------------
# Real roots: Sturm sequences and bisection (exact rational intervals)
# --------------------------------------------------------------------------------------------------------------


def sturm_sequence(p: list) -> list[list[Fraction]]:
    p = squarefree_part(p)
    seq = [p, pderiv(p)]
    while seq[-1] and pdeg(seq[-1]) > 0:
        r = pdivmod(seq[-2], seq[-1])[1]
        if not r:
            break
        seq.append([-x for x in r])
    return [s for s in seq if s]


def _sign_changes(seq, x) -> int:
    signs = [v for v in (peval(s, x) for s in seq) if v != 0]
    return sum(1 for a, b in zip(signs, signs[1:]) if (a > 0) != (b > 0))


def count_real_roots(p: list, lo, hi) -> int:
    """Number of distinct real roots in the half-open interval (lo, hi]."""
    seq = sturm_sequence(p)
    return _sign_changes(seq, Fraction(lo)) - _sign_changes(seq, Fraction(hi))


def root_bound(p: list) -> Fraction:
    """Cauchy bound: every complex root has |z| < 1 + max |a_i / a_n|."""
    p = ptrim(p)
    return 1 + max(abs(c / p[-1]) for c in p[:-1]) if len(p) > 1 else Fraction(1)


def real_roots_isolated(p: list) -> list[tuple[Fraction, Fraction]]:
    """Disjoint intervals (lo, hi], each containing exactly one distinct real root, in increasing order."""
    p = squarefree_part(p)
    if pdeg(p) < 1:
        return []
    seq = sturm_sequence(p)
    b = root_bound(p)
    out = []

    def rec(lo, hi, clo, chi):
        k = clo - chi
        if k == 0:
            return
        if k == 1:
            out.append((lo, hi))
            return
        mid = (lo + hi) / 2
        cm = _sign_changes(seq, mid)
        rec(lo, mid, clo, cm)
        rec(mid, hi, cm, chi)

    rec(-b, b, _sign_changes(seq, -b), _sign_changes(seq, b))
    return out


def real_root_approx(p: list, interval: tuple, width=Fraction(1, 10 ** 40)) -> tuple[Fraction, Fraction]:
    """Shrink an isolating interval (lo, hi] of the square-free part of p by bisection to the given width."""
    q = squarefree_part(p)
    lo, hi = Fraction(interval[0]), Fraction(interval[1])
    seq = sturm_sequence(q)
    while hi - lo > width:
        mid = (lo + hi) / 2
        if _sign_changes(seq, lo) - _sign_changes(seq, mid) >= 1:
            hi = mid
        else:
            lo = mid
    return lo, hi


def dominant_real_root(p: list, width=Fraction(1, 10 ** 40)):
    """The largest real root of p as a rational interval of the given width, or None if p has no real root.

    Note: this does not check that the root also dominates the COMPLEX roots in modulus; callers that need
    that (growth constants) should check it separately, e.g. with `dominates_in_modulus`."""
    iv = real_roots_isolated(p)
    return None if not iv else real_root_approx(p, iv[-1], width)


def schur_sum_sq_bound(p: list) -> Fraction:
    """Upper bound on sum |z_i|^2 over all complex roots of p: the squared Frobenius norm of the companion matrix
    (Schur's inequality sum |eigenvalue|^2 <= ||A||_F^2). Exact."""
    c = pmonic(p)
    n = pdeg(c)
    return Fraction(n - 1) + sum(x * x for x in c[:-1]) if n >= 1 else Fraction(0)


def dominance_certificate(p: list, minpoly: list, lam_interval: tuple) -> str:
    """Is the real root lam (in lam_interval, a root of the irreducible factor `minpoly` of p) strictly larger in
    modulus than every other root of p?

    Returns "certified" when an exact sufficient test passes: for every irreducible factor f != minpoly of p, the
    Schur bound gives sum |z|^2 < lo^2; and for minpoly itself, Schur bound - lo^2 < lo^2 bounds its other roots.
    Returns "numeric" when only a floating-point root computation (Durand-Kerner, double precision) confirms it
    with a relative margin of 1e-9, and "fails" when the numeric check finds a root of modulus >= lam."""
    lo = Fraction(lam_interval[0])
    ok = True
    for f in factor_kronecker(p):
        if pint(f) == pint(minpoly):
            if pdeg(f) > 1 and not schur_sum_sq_bound(f) - lo * lo < lo * lo:
                ok = False
        elif not schur_sum_sq_bound(f) < lo * lo:
            ok = False
    if ok:
        return "certified"
    roots = durand_kerner(p)
    lam = float((Fraction(lam_interval[0]) + Fraction(lam_interval[1])) / 2)
    others = [z for z in roots if abs(z - lam) > 1e-7 * max(1.0, lam)]
    return "numeric" if all(abs(z) < lam * (1 - 1e-9) for z in others) else "fails"


def durand_kerner(p: list, iters: int = 500) -> list[complex]:
    """All complex roots of p in floating point (Weierstrass / Durand-Kerner iteration). NOT exact."""
    c = [complex(float(x)) for x in pmonic(p)]
    n = len(c) - 1
    z = [(0.4 + 0.9j) ** k for k in range(n)]
    for _ in range(iters):
        new = []
        for i in range(n):
            num = sum(c[k] * z[i] ** k for k in range(n + 1))
            den = 1
            for j in range(n):
                if j != i:
                    den *= (z[i] - z[j])
            new.append(z[i] - num / den if den != 0 else z[i] + 1e-6)
        z = new
    return z


# --------------------------------------------------------------------------------------------------------------
# Factoring over Z: rational roots and Kronecker's method
# --------------------------------------------------------------------------------------------------------------


def _divisors(n: int) -> list[int]:
    n = abs(n)
    if n == 0:
        return [0]
    small = [d for d in range(1, isqrt(n) + 1) if n % d == 0]
    ds = sorted(set(small + [n // d for d in small]))
    return ds + [-d for d in ds]


def rational_roots(p: list) -> list[Fraction]:
    """All rational roots of p (exact), by the rational root theorem."""
    q = pint(p)
    if not q:
        return []
    roots = set()
    while q and q[0] == 0:  # root 0
        roots.add(Fraction(0))
        q = q[1:]
    if len(q) <= 1:
        return sorted(roots)
    for a in _divisors(q[0]):
        for b in _divisors(q[-1]):
            if b > 0 and peval(q, Fraction(a, b)) == 0:
                roots.add(Fraction(a, b))
    return sorted(roots)


def _interpolate(xs: list[int], ys: list[int]) -> list[Fraction]:
    """Lagrange interpolation over Q."""
    out: list[Fraction] = []
    for i, (xi, yi) in enumerate(zip(xs, ys)):
        term = [Fraction(yi)]
        den = Fraction(1)
        for j, xj in enumerate(xs):
            if j != i:
                term = pmul(term, [-xj, 1])
                den *= xi - xj
        out = padd(out, [c / den for c in term])
    return out


def factor_kronecker(p: list) -> list[list[int]]:
    """Complete factorisation of a nonzero integer polynomial into irreducible factors over Z (Kronecker).

    Returns primitive integer factors (positive leading coefficient), with multiplicity, up to the content.
    Exact; exponential in the degree, intended for degree <= 8 with small coefficients."""
    q = pint(p)
    if pdeg(q) <= 0:
        return []
    for r in rational_roots(q):
        lin = pint([-r, 1])
        quo, rem = pdivmod(q, lin)
        if not rem:
            return [lin] + factor_kronecker(quo)
    n = pdeg(q)
    for k in range(2, n // 2 + 1):
        xs = list(range(-(k // 2), k + 1 - (k // 2)))  # k + 1 distinct integer points
        vals = [int(peval(q, x)) for x in xs]
        if any(v == 0 for v in vals):  # cannot happen: no rational roots left
            continue
        for choice in product(*[_divisors(v) for v in vals]):
            cand = _interpolate(xs, list(choice))
            if pdeg(cand) != k or any(c.denominator != 1 for c in cand):
                continue
            quo, rem = pdivmod(q, cand)
            if not rem:
                return factor_kronecker(cand) + factor_kronecker(quo)
    return [q]


def is_irreducible(p: list) -> bool:
    f = factor_kronecker(p)
    return len(f) == 1


def minimal_polynomial_of_root(p: list, interval: tuple) -> list[int]:
    """The irreducible factor of p over Z that vanishes at the real root isolated by `interval` (exact)."""
    for f in factor_kronecker(p):
        if count_real_roots(f, interval[0], interval[1]) >= 1:
            return f
    raise ValueError("no factor has a root in the interval")


# --------------------------------------------------------------------------------------------------------------
# LLL and integer relations
# --------------------------------------------------------------------------------------------------------------


def lll(basis: list[list[int]], delta=Fraction(3, 4)) -> list[list[int]]:
    """LLL-reduce the rows of an integer basis (exact rational Gram-Schmidt). Textbook version (LLL 1982)."""
    b = [list(map(int, r)) for r in basis]
    n = len(b)

    def dot(u, v):
        return sum(x * y for x, y in zip(u, v))

    def gso():
        bs, mu = [], [[Fraction(0)] * n for _ in range(n)]
        for i in range(n):
            v = [Fraction(x) for x in b[i]]
            for j in range(i):
                mu[i][j] = Fraction(dot(b[i], bs[j])) / dot(bs[j], bs[j]) if any(bs[j]) else Fraction(0)
                v = [a - mu[i][j] * c for a, c in zip(v, bs[j])]
            bs.append(v)
        return bs, mu

    bs, mu = gso()
    k = 1
    while k < n:
        for j in range(k - 1, -1, -1):
            q = round(mu[k][j])
            if q:
                b[k] = [x - q * y for x, y in zip(b[k], b[j])]
                bs, mu = gso()
        if dot(bs[k], bs[k]) >= (delta - mu[k][k - 1] ** 2) * dot(bs[k - 1], bs[k - 1]):
            k += 1
        else:
            b[k], b[k - 1] = b[k - 1], b[k]
            bs, mu = gso()
            k = max(k - 1, 1)
    return b


def integer_relation(xs: list[Fraction], scale: int) -> list[int]:
    """Find small integers c with sum c_i x_i ~ 0 (LLL on [I | round(scale * x)]). Returns the first row's c."""
    n = len(xs)
    basis = [[1 if j == i else 0 for j in range(n)] + [round(scale * xs[i])] for i in range(n)]
    red = lll(basis)
    return red[0][:n]


def minpoly_by_lll(x: Fraction, max_degree: int, err: Fraction) -> list[int] | None:
    """Guess the minimal polynomial of a real number from an approximation x with estimated error err
    (experimental mathematics; LLL 1982 used as an integer-relation finder).

    For d = 1..max_degree: reduce the lattice [I | round(10^D x^i)] with D = floor(-log10 err) and take the
    shortest row c. Accept p(t) = sum c_i t^i only if (1) the residual is explained by the error,
    |p(x)| <= 10 |p'(x)| err, and (2) the relation is "information-theoretically meaningful": (d + 1) log10(max|c_i|)
    + 1 <= D, i.e. the coefficients use clearly fewer digits than the precision supplies (a random real admits
    relations with (d + 1) log10|c| ~ D). The result is a GUESS that must be verified exactly elsewhere."""
    from math import floor, log10
    D = floor(-log10(float(err))) if err > 0 else 30
    scale = 10 ** max(D, 1)
    for d in range(1, max_degree + 1):
        powers = [x ** i for i in range(d + 1)]
        c = integer_relation(powers, scale)
        if all(v == 0 for v in c) or c[-1] == 0:
            continue
        p = pint(c)
        resid = abs(peval(p, x))
        slope = abs(peval(pderiv(p), x))
        big = max(abs(v) for v in p)
        if resid <= 10 * slope * err + Fraction(1, scale) and (d + 1) * log10(big + 1) + 1 <= D:
            return p
    return None


# --------------------------------------------------------------------------------------------------------------
# Number field Q[x]/(m) for exact algebraic arithmetic
# --------------------------------------------------------------------------------------------------------------


class NumberField:
    """Arithmetic in Q(alpha) = Q[x]/(m(x)) for an irreducible m. Elements are reduced polynomials in alpha."""

    def __init__(self, minpoly: list):
        self.m = pmonic(minpoly)
        if not is_irreducible(pint(self.m)):
            raise ValueError("minimal polynomial must be irreducible")

    def red(self, a: list) -> list[Fraction]:
        return pdivmod(ptrim(a), self.m)[1]

    def mul(self, a, b):
        return self.red(pmul(a, b))

    def inv(self, a):
        # extended Euclid in Q[x]: s*a + t*m = 1
        r0, r1 = self.m[:], self.red(a)
        if not r1:
            raise ZeroDivisionError("inverse of zero")
        s0, s1 = [], [Fraction(1)]
        while pdeg(r1) > 0:
            q, r = pdivmod(r0, r1)
            r0, r1 = r1, r
            s0, s1 = s1, psub(s0, pmul(q, s1))
        c = r1[0]
        return self.red([x / c for x in s1])

    def div(self, a, b):
        return self.mul(a, self.inv(b))

    def power(self, a, k: int):
        if k < 0:
            return self.power(self.inv(a), -k)
        out, base = [Fraction(1)], self.red(a)
        while k:
            if k & 1:
                out = self.mul(out, base)
            base = self.mul(base, base)
            k >>= 1
        return out
