"""Guessing linear recurrences from exact terms, and reading off the asymptotic shape of their solutions.

Two guessers, both exact over Q:

* `berlekamp_massey(seq)`: the shortest linear recurrence with CONSTANT coefficients (C-finite) that generates
  the given prefix. Massey (1969), Shift-register synthesis and BCH decoding, IEEE Trans. Inf. Theory 15,
  doi:10.1109/TIT.1969.1054260. Over a field the algorithm is exact; we run it over Q with Fractions.
* `guess_p_recursive(seq, order, degree)`: a recurrence sum_{i=0..r} p_i(n) a(n-i) = 0 with POLYNOMIAL
  coefficients of degree <= d (P-recursive / holonomic sequences, Stanley 1980, doi:10.1016/S0195-6698(80)80051-5),
  found as the nullspace of a linear system in the (r+1)(d+1) unknown coefficients. This is the "guessing" of
  computer algebra (e.g. GFUN, Salvy & Zimmermann 1994, doi:10.1145/178365.178368; Kauers & Paule, The Concrete
  Tetrahedron, 2011 [book]).

A guess is only a conjecture: it is accepted here only if the system is OVERDETERMINED by a stated margin
(`extra` equations beyond the number of unknowns), the nullspace is one-dimensional, and the recurrence then
also reproduces held-out terms that were not used to find it. A proof needs more (e.g. creative telescoping, or
a structural argument from the program text, as for the call counts of plain recursions).

Asymptotics. For a C-finite sequence the growth is lambda^n n^(m-1) with lambda the dominant root of the
characteristic polynomial and m its multiplicity (if the coefficient of that term is nonzero). For a P-recursive
sequence whose coefficients p_i all have the same degree D (no factorial growth), the formal solutions behave
like lambda^n n^theta with sum_i alpha_i lambda^(-i) = 0 and

    theta = sum_i beta_i lambda^(-i) / sum_i i alpha_i lambda^(-i),

where p_i(n) = alpha_i n^D + beta_i n^(D-1) + ... (Birkhoff-Trjitzinsky theory; see Wimp & Zeilberger 1985,
Resurrecting the asymptotics of linear recurrences, J. Math. Anal. Appl. 111, doi:10.1016/0022-247X(85)90209-4,
and Flajolet & Sedgewick, Analytic Combinatorics, 2009 [book]). The formula is the order-1/n balance of the
ansatz a(n) = lambda^n n^theta (1 + O(1/n)); it holds for a simple root lambda. Which formal solution the actual
sequence follows (a zero coefficient on the dominant one is possible) is not decided by the recurrence alone,
so the result is cross-checked numerically against the terms (`theta_numeric`).
"""
from __future__ import annotations

from fractions import Fraction
from math import log

from . import exactalg as ea


# --------------------------------------------------------------------------------------------------------------
# C-finite: Berlekamp-Massey over Q
# --------------------------------------------------------------------------------------------------------------


def berlekamp_massey(seq: list) -> list[Fraction]:
    """Return c = [c_1, ..., c_L] with a(n) = sum_{i=1..L} c_i a(n-i) for all L <= n < len(seq), L minimal.

    Exact over Q (Massey 1969). With 2L <= len(seq) the recurrence is the unique shortest one for the prefix."""
    s = [Fraction(x) for x in seq]
    C, B = [Fraction(1)], [Fraction(1)]
    L, m, b = 0, 1, Fraction(1)
    for n in range(len(s)):
        d = s[n] + sum(C[i] * s[n - i] for i in range(1, L + 1))
        if d == 0:
            m += 1
            continue
        coef = d / b
        T = C[:]
        Bs = [Fraction(0)] * m + B
        if len(Bs) > len(C):
            C = C + [Fraction(0)] * (len(Bs) - len(C))
        for i, x in enumerate(Bs):
            C[i] -= coef * x
        if 2 * L <= n:
            L, B, b, m = n + 1 - L, T, d, 1
        else:
            m += 1
    C = C + [Fraction(0)] * (L + 1 - len(C))
    return [-C[i] for i in range(1, L + 1)]


def guess_c_finite(seq: list, holdout: int = 4) -> dict | None:
    """Run Berlekamp-Massey on seq[:-holdout], require 2L + 2 <= len(train), and check the holdout terms."""
    train = seq[:-holdout] if holdout else seq
    c = berlekamp_massey(train)
    L = len(c)
    if L == 0 or 2 * L + 2 > len(train):
        return None
    ok = all(Fraction(seq[n]) == sum(c[i - 1] * Fraction(seq[n - i]) for i in range(1, L + 1))
             for n in range(L, len(seq)))
    if not ok:
        return None
    charpoly = [-x for x in reversed(c)] + [Fraction(1)]  # x^L - c_1 x^(L-1) - ... - c_L (lowest first)
    return {"kind": "C-finite", "order": L, "coeffs": c, "charpoly": charpoly,
            "terms_used": len(train), "terms_checked": len(seq)}


# --------------------------------------------------------------------------------------------------------------
# P-recursive (holonomic) guessing
# --------------------------------------------------------------------------------------------------------------


def guess_p_recursive(seq: list, order: int, degree: int, start: int = 0, extra: int = 4,
                      holdout: int = 3) -> dict | None:
    """Find sum_{i=0..order} p_i(n) a(n-i) = 0 with deg p_i <= degree, where seq[k] = a(start + k).

    Uses seq[:-holdout] to set up the equations (n from start+order on); requires at least
    (#unknowns - 1) + extra equations and a one-dimensional nullspace; then checks the holdout terms."""
    unknowns = (order + 1) * (degree + 1)
    train = seq[:-holdout] if holdout else seq
    rows = []
    for k in range(order, len(train)):
        n = start + k
        rows.append([Fraction(n) ** j * Fraction(train[k - i]) for i in range(order + 1) for j in range(degree + 1)])
    if len(rows) < unknowns - 1 + extra:
        return None
    ns = ea.nullspace(rows)
    if len(ns) != 1:
        return None
    v = ns[0]
    polys = [ea.ptrim(v[i * (degree + 1):(i + 1) * (degree + 1)]) for i in range(order + 1)]
    if not polys[0]:
        return None

    def residual(k):
        n = start + k
        return sum(ea.peval(polys[i], Fraction(n)) * Fraction(seq[k - i]) for i in range(order + 1))

    if any(residual(k) != 0 for k in range(order, len(seq))):
        return None
    return {"kind": "P-recursive", "order": order, "degree": degree, "polys": polys, "start": start,
            "equations": len(rows), "unknowns": unknowns, "terms_used": len(train), "terms_checked": len(seq)}


def search_p_recursive(seq: list, max_order: int = 4, max_degree: int = 4, start: int = 0, extra: int = 4,
                       holdout: int = 3) -> dict | None:
    """Smallest (order + degree, then order) recurrence found by `guess_p_recursive`, or None."""
    for total in range(0, max_order + max_degree + 1):
        for order in range(1, max_order + 1):
            degree = total - order
            if 0 <= degree <= max_degree:
                g = guess_p_recursive(seq, order, degree, start, extra, holdout)
                if g:
                    return g
    return None


# --------------------------------------------------------------------------------------------------------------
# Asymptotic shape
# --------------------------------------------------------------------------------------------------------------


def p_recursive_characteristic(g: dict) -> tuple[list[Fraction], int, list[Fraction], list[Fraction]]:
    """(chi, D, alpha, beta): chi(x) = sum_i alpha_i x^(r-i) (lowest first), alpha_i / beta_i the coefficients of
    n^D / n^(D-1) in p_i(n) (expanded in powers of n)."""
    polys, r = g["polys"], g["order"]
    D = max(ea.pdeg(p) for p in polys)
    alpha = [p[D] if len(p) > D else Fraction(0) for p in polys]
    beta = [p[D - 1] if D >= 1 and len(p) > D - 1 else Fraction(0) for p in polys]
    chi = ea.ptrim([alpha[r - k] for k in range(r + 1)])  # coefficient of x^k is alpha_(r-k)
    return chi, D, alpha, beta


def growth_from_charpoly(chi: list, width=Fraction(1, 10 ** 30)) -> dict:
    """Dominant real root of chi with its exact minimal polynomial and multiplicity in chi."""
    iv = ea.dominant_real_root(chi, width)
    if iv is None:
        return {"lambda": None}
    mp = ea.minimal_polynomial_of_root(chi, iv)
    mult, q = 0, ea.ptrim(chi)
    while True:
        quo, rem = ea.pdivmod(q, mp)
        if rem:
            break
        mult, q = mult + 1, quo
    return {"lambda_interval": iv, "lambda": float((iv[0] + iv[1]) / 2), "minpoly": mp, "multiplicity": mult,
            "dominance": ea.dominance_certificate(chi, mp, iv)}


def theta_p_recursive(g: dict, minpoly: list) -> list[Fraction]:
    """theta in Q(lambda) as a reduced polynomial in lambda (exact); a constant list means theta is rational."""
    chi, D, alpha, beta = p_recursive_characteristic(g)
    K = ea.NumberField(minpoly)
    lam_inv = K.inv([Fraction(0), Fraction(1)])
    num, den = [], []
    for i in range(g["order"] + 1):
        li = K.power(lam_inv, i)
        num = ea.padd(num, [beta[i] * c for c in li])
        den = ea.padd(den, [i * alpha[i] * c for c in li])
    return K.div(num, den)


def theta_numeric(seq: list, lam: float, start: int = 0, tail: int = 6) -> float:
    """Least-squares slope of log(a(n) / lam^n) against log n over the last `tail` terms (floating point)."""
    pts = [(log(start + k), log(float(Fraction(seq[k]))) - (start + k) * log(lam))
           for k in range(len(seq) - tail, len(seq)) if start + k > 0 and seq[k] > 0]
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    return sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)


def ratio_estimates(seq: list) -> list[Fraction]:
    """Successive ratios a(n)/a(n-1) (exact). The ratio method of series analysis: for a(n) ~ C lambda^n n^theta,
    r_n = lambda (1 + theta/n + O(1/n^2)), so a linear fit of r_n against 1/n estimates lambda and lambda*theta
    (Guttmann (ed.), Polygons, Polyominoes and Polycubes, 2009 [book])."""
    return [Fraction(seq[k]) / Fraction(seq[k - 1]) for k in range(1, len(seq)) if seq[k - 1] != 0]


def ratio_method(seq: list, start: int = 0, use: int = 6) -> tuple[Fraction, Fraction]:
    """Exact rational (lambda, theta) estimates from the last `use` ratios: least squares r_n = lam + lam*theta/n."""
    pts = []
    for k in range(len(seq) - use, len(seq)):
        n = start + k
        pts.append((Fraction(1, n), Fraction(seq[k]) / Fraction(seq[k - 1])))
    mx = sum(p[0] for p in pts) / len(pts)
    my = sum(p[1] for p in pts) / len(pts)
    slope = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    lam = my - slope * mx
    return lam, slope / lam


def richardson(seq_r: list, start: int, order: int = 3) -> Fraction:
    """Richardson extrapolation of r_n = lam + c1/n + c2/n^2 + ... from the last order+1 ratios (exact)."""
    k0 = len(seq_r) - order - 1
    rows, rhs = [], []
    for k in range(k0, len(seq_r)):
        n = start + k + 1  # r_k = a(n)/a(n-1) with n = start + k + 1
        rows.append([Fraction(1)] + [Fraction(1, n ** j) for j in range(1, order + 1)] + [-seq_r[k]])
    m, piv = ea.rref(rows)
    return -m[0][-1]


def richardson_with_error(seq: list, start: int, order: int = 3) -> tuple[Fraction, Fraction]:
    """Richardson estimate of lambda from the ratios, with an error ESTIMATE |R(all terms) - R(all but the last)|.

    The estimate uses only the counts (no knowledge of the exact lambda)."""
    rs = ratio_estimates(seq)
    r1 = richardson(rs, start, order)
    r0 = richardson(rs[:-1], start, order)
    return r1, max(abs(r1 - r0), Fraction(1, 10 ** 30))
