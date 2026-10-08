#!/usr/bin/env python3
"""Verifier for theorems/max-flow-random-dense-dinic-short-residual-paths (see README.md in this folder).

Computations are evidence; the proofs are in the README. Standard library only, no network, deterministic (fixed
seeds). Exit code 0 only if every check passes. Default run: about a minute on a laptop; --full adds seeded
instances with n = 240, 320, 400 to part S (about two and a half minutes).

Model (README): vertices 0..n-1, s = 0, t = n - 1, M = the other m = n - 2 vertices; every ordered pair is an edge
with probability 1/2 and a capacity uniform on 1..100, all independent (generate_scaling of
pairs/max-flow-edmonds-karp-vs-dinic with ideal random bits). X = capacity of one ordered pair (0 if absent).

Checks:
  K  exact constants (fractions): the choice c0 = 42 in Lemma 3(b), 59/200, 299/800; the reachability probability
     of Corollary 7 and (3/4)^m of Proposition 9(ii) by exhaustive enumeration; the bound of Proposition 9(iii); the
     explicit rates used in Corollary 7 and Proposition 9.
  A  Theorem 5 (analytic bound), certified in exact integer arithmetic with decimal bounds on the logarithms: every
     n in [4, 10^6] is scanned for p = 1e-3 (bound <= 0.01 from n = 21 437 on) and for p = 1/n (bound <= 2/n from
     n = 21 793 on); the value at n = 21 436; the numbers of the argument for n > 10^6.
  P  the computed bounds (Lemma 3(a) with order-statistics bounds, exact-MGF Chernoff bounds), certified (decimal
     sums, directed rounding of epsilon): Proposition 6 at the five n of the README and Theorem 8 at the twelve n.
  V  the instrumented copies of the entry's Dinic and Edmonds-Karp reproduce the line-execution counts of the
     unchanged code (sys.settrace) on small seeded instances.
  S  seeded instances of generate_scaling (n = 20, 40, 80, 160; more with --full), deterministic statements checked
     instance by instance: Lemma 1; Lemma 0(ii) of the trivial-min-cut note; Lemma 2, Lemma 3, the |X_2| step and the
     partition-level step of Theorem 4 at every Dinic phase start; the read bounds of Corollary 7 and of the remark after it; the phase
     structure of Proposition 9 and the exact identity of Proposition 10 (Dinic and Edmonds-Karp).
  R  Lemmas 2 and 3 on random feasible flows that neither algorithm produces.
Usage (from the repository root): python theorems/max-flow-random-dense-dinic-short-residual-paths/verify.py [--full]
"""
import importlib.util
import inspect
import math
import random
import sys
import time
from collections import Counter, deque
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIR = ROOT / "pairs" / "max-flow-edmonds-karp-vs-dinic"
FULL = "--full" in sys.argv[1:]
FAILURES = []
CAPS = range(1, 101)
MU = 25.25
LN10 = math.log(10)


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, PAIR / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HARNESS = load("harness.py", "mf_harness")
EK = load("implementations/edmonds_karp.py", "mf_ek").max_flow_edmonds_karp
DINIC = load("implementations/dinic.py", "mf_dinic").max_flow_dinic


# ------------------------------------------------------------------------------------------------ K: constants
def part_constants():
    vals = {c0: Fraction(c0, 100 + c0) * Fraction(101 - c0, 200) for c0 in CAPS}
    best = max(vals, key=vals.get)
    check("c0 = 42 maximises c0/(100 + c0) * P(an ordered pair is an edge of capacity >= c0) over c0 = 1..100; "
          "P(capacity >= 42 and edge) = 59/200; value 1239/14200 = 0.087254",
          best == 42 and Fraction(101 - 42, 200) == Fraction(59, 200) and vals[42] == Fraction(1239, 14200),
          f"value {float(vals[42]):.6f}")
    pmf = {0: Fraction(1, 2)}
    pmf.update({c: Fraction(1, 200) for c in CAPS})
    p_gt = sum(pa * pb for a, pa in pmf.items() for b, pb in pmf.items() if a > b)
    check("P(a_v > b_v) = 299/800 = 0.37375", p_gt == Fraction(299, 800))
    # reachability: P(d(s, v) > 2) = (1/2)(3/4)^(n-2), by enumerating every digraph on n = 3, 4 vertices
    ok = True
    for n in (3, 4):
        pairs = [(u, v) for u in range(n) for v in range(n) if u != v]
        far = [0] * n
        for mask in range(1 << len(pairs)):
            arcs = {pairs[i] for i in range(len(pairs)) if mask >> i & 1}
            for v in range(1, n):
                if (0, v) not in arcs and not any((0, w) in arcs and (w, v) in arcs for w in range(1, n) if w != v):
                    far[v] += 1
        ok &= all(Fraction(far[v], 1 << len(pairs)) == Fraction(1, 2) * Fraction(3, 4) ** (n - 2) for v in range(1, n))
    check("P(vertex v is at distance > 2 from s) = (1/2)(3/4)^(n-2): every digraph on 3 and 4 vertices", ok)
    # Proposition 9(ii): P(no v in M with a_v > 0 and b_v > 0) = (3/4)^m (only the pairs at s and t matter)
    ok = True
    for m in range(1, 7):
        none = sum(1 for mask in range(1 << (2 * m))
                   if not any(mask >> (2 * i) & 1 and mask >> (2 * i + 1) & 1 for i in range(m)))
        ok &= Fraction(none, 1 << (2 * m)) == Fraction(3, 4) ** m
    check("Proposition 9(ii): P(no length-2 path) = (3/4)^m, all edge sets at s and t, m = 1..6", ok)
    # Proposition 9(iii): 2 P(Bin(m, 299/800) < 0.3 m) + 2^(-(0.3 m)^2) at n = 40, 100, 400
    # (exact binomial tail as a fraction; 2^(-(0.3 m)^2) in 50-digit decimal; README displays rounded up)
    getcontext().prec = 50
    vals = []
    for n in (40, 100, 400):
        m = n - 2
        q = Fraction(299, 800)
        cdf = sum(Fraction(math.comb(m, i)) * q ** i * (1 - q) ** (m - i) for i in range(m + 1) if i < Fraction(3, 10) * m)
        vals.append(Decimal(2 * cdf.numerator) / Decimal(cdf.denominator)
                    + (-(Decimal("0.09") * m * m) * Decimal(2).ln()).exp())
    shown = [Decimal("0.367"), Decimal("0.134"), Decimal("0.00212")]
    check("Proposition 9(iii) bound at n = 40, 100, 400 is <= 0.367, <= 0.134, <= 2.12e-3 (the README values, each the "
          "value rounded up to 3 significant digits)",
          all(v <= w and v >= w * Decimal("0.99") for v, w in zip(vals, shown)), ", ".join(f"{v:.6f}" for v in vals))
    # explicit rates (README, Corollary 7 and Proposition 9), 50-digit decimal
    rate = 2 * (Fraction(299, 800) - Fraction(3, 10)) ** 2
    getcontext().prec = 50
    n = 21793
    m = n - 2
    p9 = (Decimal(3) / 4) ** m + 2 * (-Decimal(rate.numerator) / rate.denominator * m).exp() \
        + (-(Decimal("0.09") * m * m) * Decimal(2).ln()).exp()
    n2 = 40
    reach = Decimal(n2 - 1) / 2 * (Decimal(3) / 4) ** (n2 - 2) + (-Decimal(n2 * (n2 - 1)) / 8).exp()
    check("explicit rates: 2(299/800 - 3/10)^2 = 0.010878125; at n = 21 793, n ((3/4)^m + 2 e^(-0.010878125 m) + "
          "2^(-0.09 m^2)) <= 4.92e-99 <= 1; at n = 40, n ((n - 1)/2 (3/4)^(n-2) + e^(-n(n-1)/8)) <= 0.01395 <= 1 (the "
          "README values; n times each of these decreases in n from n = 92 resp. n = 8 on)",
          rate == Fraction(10878125, 10 ** 9) and p9 * n <= Decimal("4.92e-99") and reach * n2 <= Decimal("0.01395"),
          f"n p9 = {p9 * n:.6E}, 40 * reach = {reach * n2:.6f}")


# ------------------------------------------------------------------------------------------------ A: Theorem 5
def analytic(n, p=1e-3):
    """(x, natural log of 2 n 2^(2n-3) exp(-2 h^2 / (1e4 x n))) of Theorem 5; the ceiling is made conservative
    (a smaller x only weakens the bound)."""
    m = n - 2
    lam = math.sqrt((n - 1) / 2 * math.log(2 * m / p))
    ks = (42 / 142) * (0.295 * (n - 1) - lam)
    if ks <= 0:
        return None, math.inf
    x = math.ceil(ks - 1e-9) + 1
    h = MU * x * (x - 1) - 100 * n
    if h <= 0:
        return x, math.inf
    return x, math.log(2 * n) + (2 * n - 3) * math.log(2) - 2 * h * h / (1e4 * x * n)


# Certified scan of Theorem 5 (README, "Evaluation"). Every logarithm is replaced by an integer upper or lower bound
# in units of 10^-30, obtained from 50-digit decimal values (decimal's ln is correctly rounded) plus one unit; for
# k > SCAN_EXACT, ln k is bounded above by the tangent ln k0 + (k - k0)/k0 at the start k0 of its block of 1000 (ln is
# concave). The rest is exact integer arithmetic: k_cert(n) is the largest integer k with
#   A = 1239(n - 1) - 14200(k - 1) > 0 and 2 A^2 10^30 > 4200^2 (n - 1) L_up,
# which certifies k - 1 < (42/142)(0.295(n - 1) - lambda) since lambda^2 <= ((n - 1)/2) L_up 10^-30; so
# k_cert(n) <= k_s(n), and a smaller x only weakens the bound (g increases where f > 0). With x = k_cert + 1 and
# H = 4h = 101 x(x - 1) - 400 n > 0, the second summand of the bound is <= the target iff
#   H^2 10^30 >= R_up 8 10^4 x n,  R_up >= (ln(2n) + (2n - 3) ln 2 + ln(1/target)) 10^30.
getcontext().prec = 50
SC = 10 ** 30
SCAN_EXACT = 70000
SCAN_BLOCK = 1000


def _up(x):
    return int((x * SC).to_integral_value(rounding="ROUND_CEILING")) + 1


def _lo(x):
    return int((x * SC).to_integral_value(rounding="ROUND_FLOOR")) - 1


LN2_UP = _up(Decimal(2).ln())
LN2000_UP = _up(Decimal(2000).ln())
LN_1_OVER_0009_UP = _up((1 / Decimal("0.009")).ln())
_LN_UP = None
_LN_BLOCK = {}


def ln_up(k):
    """Integer >= ln(k) * 10^30."""
    global _LN_UP
    if _LN_UP is None:
        _LN_UP = [0, 0] + [_up(Decimal(i).ln()) for i in range(2, SCAN_EXACT + 1)]
    if k <= SCAN_EXACT:
        return _LN_UP[k]
    k0 = k - (k - SCAN_EXACT) % SCAN_BLOCK
    if k0 not in _LN_BLOCK:
        _LN_BLOCK[k0] = _up(Decimal(k0).ln())
    return _LN_BLOCK[k0] - (-(k - k0) * SC // k0)


def k_cert(n, l_up):
    lam = math.sqrt((n - 1) / 2 * l_up / SC)
    k = max(1, math.ceil((42 / 142) * (0.295 * (n - 1) - lam)))
    rhs = 4200 * 4200 * (n - 1) * l_up

    def ok(kk):
        a = 1239 * (n - 1) - 14200 * (kk - 1)
        return a > 0 and 2 * a * a * SC > rhs

    while ok(k + 1):
        k += 1
    while k >= 1 and not ok(k):
        k -= 1
    return k


def theorem5_certified(n, mode):
    """True if the certified bound proves: second summand <= 0.009 (mode 'p3': p = 1e-3, total <= 0.01) or <= 1/n
    (mode 'pn': p = 1/n, total <= 2/n). Returns (ok, x)."""
    m = n - 2
    if mode == "p3":
        l_up = LN2000_UP + ln_up(m)                                     # ln(2m/p) = ln 2000 + ln m
        r_up = LN2_UP + ln_up(n) + (2 * n - 3) * LN2_UP + LN_1_OVER_0009_UP
    else:
        l_up = LN2_UP + ln_up(m) + ln_up(n)                             # ln(2m/p) = ln 2 + ln m + ln n
        r_up = LN2_UP + ln_up(n) + (2 * n - 3) * LN2_UP + ln_up(n)
    k = k_cert(n, l_up)
    if k < 1:
        return False, None
    x = k + 1
    big_h = 101 * x * (x - 1) - 400 * n
    if big_h <= 0:
        return False, x
    return big_h * big_h * SC >= r_up * 8 * 10 ** 4 * x * n, x


def part_analytic():
    xs = {n: analytic(n) for n in (10 ** 4, 2 * 10 ** 4, 3 * 10 ** 4, 5 * 10 ** 4, 10 ** 5, 10 ** 6)}
    print("       (double precision, for display) x and log10 of the forward term: " + ", ".join(
        f"n={n}: x={x}, {(L - math.log(2)) / LN10:.1f}" for n, (x, L) in xs.items()))
    top = 10 ** 6
    for mode, claim_n, label in (("p3", 21437, "p = 1e-3: bound <= 0.01"), ("pn", 21793, "p = 1/n: bound <= 2/n")):
        fails = [n for n in range(4, top + 1) if not theorem5_certified(n, mode)[0]]
        check(f"Theorem 5 with {label} for every n in [{claim_n}, 10^6] (certified integer scan of all n in "
              f"[4, 10^6], {top - 3} values; ln k exact to 10^-30 for k <= {SCAN_EXACT}, tangent bounds above)",
              max(fails) == claim_n - 1, f"largest n in [4, 10^6] not certified: {max(fails)}; x at n = {claim_n}: "
              f"{theorem5_certified(claim_n, mode)[1]}")
    # n = 21 436, p = 1e-3: the formula's own value exceeds 0.01 (k_s = 1742 exactly, x = 1743)
    n = 21436
    m = n - 2
    lam = (Decimal(n - 1) / 2 * (Decimal(2000) * m).ln()).sqrt()
    K = Decimal(42) / 142 * (Decimal("0.295") * (n - 1) - lam)
    x = 1743
    h = Decimal(101) / 4 * x * (x - 1) - 100 * n
    second = ((2 * Decimal(n)).ln() + (2 * n - 3) * Decimal(2).ln() - 2 * h * h / (Decimal(10) ** 4 * x * n)).exp()
    check("Theorem 5 at n = 21 436, p = 1e-3: k_s = 1742 (1741 < K < 1742 by more than 1e-6), x = 1743, and the "
          "bound 1e-3 + 2n 2^(2n-3) exp(-2h^2/(1e4 x n)) exceeds 0.01 (50-digit decimal)",
          Decimal(1741) + Decimal("1e-6") < K < Decimal(1742) - Decimal("1e-6") and second > Decimal("0.0091"),
          f"K = {K:.9f}, bound = {Decimal('0.001') + second:.6f}")
    # n > 10^6 (both values of p), README: lambda/n decreases; x >= 0.08 n; exponent >= (0.1616 n - 102.02)^2/400
    n = Decimal(10) ** 6
    lam3 = (n / 2 * (2000 * n).ln()).sqrt() / n                        # p = 1e-3: lambda^2 <= (n/2) ln(2000 n)
    lamn = (n / 2 * (2 * n * n).ln()).sqrt() / n                       # p = 1/n:  lambda^2 <= (n/2) ln(2 n^2)
    c = Decimal(42) / 142
    ks3 = c * (Decimal("0.295") - lam3 - Decimal("0.295") / n)
    ksn = c * (Decimal("0.295") - lamn - Decimal("0.295") / n)
    e = (Decimal("0.1616") * n - Decimal("102.02")) ** 2 / 400
    ent = (2 * n).ln() + (2 * n - 3) * Decimal(2).ln()
    check("n > 10^6: lambda/n <= 0.003273 (p = 1e-3) and <= 0.003764 (p = 1/n) at n = 10^6 and decreasing in n, so "
          "k_s/n >= 0.0862 (p = 1e-3) and >= 0.0861 (p = 1/n), so x >= 0.08 n; the exponent bound (0.1616 n - 102.02)^2/400 >= 6.5e-5 n^2 exceeds "
          "ln(2n) + (2n - 3) ln 2 + ln n by more than 6e7 at n = 10^6, and the difference increases with n",
          lam3 <= Decimal("0.003273") and lamn <= Decimal("0.003764") and ks3 >= Decimal("0.0862")
          and ksn >= Decimal("0.0861")
          and e >= Decimal("6.5e-5") * n * n and e - ent - n.ln() > Decimal("6e7")
          and Decimal("1.3e-4") * n - 1 / n - Decimal("1.3863") - 1 / n > 0,
          f"lambda/n = {lam3:.6f} and {lamn:.6f}, k_s/n >= {ks3:.5f} and {ksn:.5f}, exponent {e:.4E}, "
          f"ln(2n 2^(2n-3)) = {ent:.4E}")


# ------------------------------------------------------------------------------------------------ P: computed bounds
def tilt_minus(th):
    w = [math.exp(-th * c) for c in CAPS]
    return (math.fsum(c * x for c, x in zip(CAPS, w)) / 200) / (0.5 + math.fsum(w) / 200)


def tilt_plus(th):
    w = [math.exp(-th * (100 - c)) for c in CAPS]
    return (math.fsum(c * x for c, x in zip(CAPS, w)) / 200) / (0.5 * math.exp(-100 * th) + math.fsum(w) / 200)


def chernoff_theta(N1, N2, T, iters=40):
    """An approximate minimiser theta >= 0 of theta T + N1 ln E e^{-theta X} + N2 ln E e^{theta X} (the exponent of the
    Chernoff bound for P(S <= T), S = sum of N1 iid copies of X minus N2 iid copies), by bisection on the derivative in
    double precision. Called only when T < (N1 - N2) E X. Any theta >= 0 gives a valid bound."""
    def dg(th):
        return T - N1 * tilt_minus(th) + (N2 * tilt_plus(th) if N2 else 0.0)
    lo, hi = 0.0, 0.5
    while dg(hi) < 0 and hi < 64:
        lo, hi = hi, 2 * hi
    for _ in range(iters):
        mid = (lo + hi) / 2
        if dg(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def kappa_lo(N, Np, eps):
    """Lower bound for min over feasible j of max(N - j, i*(j)) when the empirical CDFs of the N small-side and the
    Np big-side capacities are within eps of c/100 (README, computed bounds). Ceilings conservative by 1e-9."""
    lo = [max(1, math.ceil(100 * (r / N - eps) - 1e-9)) for r in range(1, N + 1)]
    hi = [min(100, math.ceil(100 * ((Np - r + 1) / Np + eps) + 1e-9)) for r in range(1, Np + 1)]
    best = N
    sig = tau = i = 0
    for j in range(1, N + 1):
        sig += lo[j - 1]
        while i < Np and tau < sig:
            tau += hi[i]
            i += 1
        if tau < sig:
            break
        best = min(best, max(N - j, i))
    return best


# Certified computation of Proposition 6 and Theorem 8 (README). N_lo, N_hi and epsilon come from 50-digit decimal
# values: N_lo, N_hi are certified by the distance of (n - 1)/2 -+ lambda_d to the nearest integer, and epsilon is
# rounded UP to a double (a larger epsilon only weakens the CDF event, whose failure probability stays <= p_cdf).
# kappa_lo then uses only IEEE double +, -, *, / (relative error 2^-53 each, absolute error < 1e-12 here) with the
# conservative shifts -+1e-9 before each ceiling, so its order-statistic bounds are valid. f2 is summed in 50-digit
# decimal arithmetic with phi and psi in closed form (geometric sums), the theta of each term from the double-precision
# bisection above (any theta >= 0 is valid), converted exactly.
_D_MGF = {}
SMALL_THETAS = []          # thetas below 1e-9 (the README's error bound assumes none); reported by a check
_D_LNFACT = [Decimal(0)]


def d_lnfact(i):
    while len(_D_LNFACT) <= i:
        _D_LNFACT.append(_D_LNFACT[-1] + Decimal(len(_D_LNFACT)).ln())
    return _D_LNFACT[i]


def d_ln_mgfs(th):
    """(ln E e^{-th X}, ln E e^{th X}) in 50-digit decimal, X = capacity of one ordered pair."""
    if th not in _D_MGF:
        if th < 1e-9:
            SMALL_THETAS.append(th)
        T = Decimal(th)
        q, Q = (-T).exp(), (-100 * T).exp()
        geo = (1 - Q) / (1 - q)                                   # sum_{c=0}^{99} q^c
        _D_MGF[th] = ((Decimal(1) / 2 + q * geo / 200).ln(), 100 * T + (Q / 2 + geo / 200).ln())
    return _D_MGF[th]


def p1_cert(n, p_deg=Decimal("0.001"), p_cdf=Decimal("0.001")):
    m = n - 2
    lam = (Decimal(n - 1) / 2 * (4 * m / p_deg).ln()).sqrt()
    edges = (Decimal(n - 1) / 2 - lam, Decimal(n - 1) / 2 + lam)
    gap = min(abs(v - v.to_integral_value()) for v in edges)
    N_lo = int(edges[0].to_integral_value(rounding="ROUND_CEILING"))
    N_hi = int(edges[1].to_integral_value(rounding="ROUND_FLOOR"))
    eps = ((400 * m / p_cdf).ln() / (2 * N_lo)).sqrt()
    eps_f = math.nextafter(math.nextafter(float(eps), 1.0), 1.0)
    return N_lo, N_hi, eps, eps_f, gap


def sharp_k_cert(n):
    N_lo, N_hi, eps, eps_f, gap = p1_cert(n)
    k = min(kappa_lo(N, N_hi, eps_f) for N in range(N_lo, N_hi + 1))
    return k, N_lo, N_hi, eps, eps_f, gap


def p2_cert(n, x, y):
    """Decimal ln of sum_{a=x}^{n-y} C(n-2, a-1) 2^(n-a-1) e^{100(n-a) th} phi(th)^{a(y-1)} psi(th)^{a(n-a-y)}: the
    forward half of P2(x, y), each term with its own theta (the trivial bound 1 on the probability if the mean is
    not above the threshold). Also returns the number of terms."""
    ln2 = Decimal(2).ln()
    terms = []
    for a in range(x, n - y + 1):
        N1, N2, T = a * (y - 1), a * (n - a - y), 100 * (n - a)
        base = d_lnfact(n - 2) - d_lnfact(a - 1) - d_lnfact(n - a - 1) + (n - a - 1) * ln2
        if T >= (N1 - N2) * MU:
            terms.append(base)
            continue
        th = chernoff_theta(N1, N2, T)
        lp, lq = d_ln_mgfs(th)
        terms.append(base + T * Decimal(th) + N1 * lp + N2 * lq)
    mx = max(terms)
    return mx + sum(((t - mx).exp() for t in terms), Decimal(0)).ln(), len(terms)


def d_log10_up2(v):
    """v / ln 10 rounded UP to 2 decimals."""
    return (v / Decimal(10).ln()).quantize(Decimal("0.01"), rounding="ROUND_CEILING")


def part_computed():
    fi = sys.float_info
    check("platform floats are IEEE 754 binary64 (radix 2, 53-bit significand), as the order-statistic bounds assume",
          fi.radix == 2 and fi.mant_dig == 53 and fi.max_exp == 1024, f"radix {fi.radix}, mant_dig {fi.mant_dig}")
    table6 = {3000: (1344, 1655, "0.0882", 320, "-53.88"), 4000: (1818, 2181, "0.0763", 444, "-1133.47"),
              5000: (2295, 2704, "0.0683", 571, "-2873.36"), 10 ** 4: (4704, 5295, "0.0485", 1226, "-22233.38"),
              2 * 10 ** 4: (9573, 10426, "0.0345", 2581, "-119197.53")}
    for n, (lo_e, hi_e, eps_e, k_e, l_e) in table6.items():
        t = time.time()
        k, N_lo, N_hi, eps, eps_f, gap = sharp_k_cert(n)
        lf2, nt = p2_cert(n, k + 1, math.ceil(n / 2))
        extra = ""
        ok = (N_lo, N_hi, k) == (lo_e, hi_e, k_e) and gap > Decimal("1e-30") and Decimal(eps_f) > eps             and eps.quantize(Decimal("0.0001")) == Decimal(eps_e) and d_log10_up2(lf2) == Decimal(l_e)
        if n == 3000:
            two_f2 = 2 * lf2.exp()
            ok &= two_f2 * (1 + Decimal("1e-20")) <= Decimal("2.6e-54")
            extra = f", 2 f2 = {two_f2:.4E} <= 2.6e-54"
        check(f"Proposition 6, n = {n}: degrees in [{N_lo}, {N_hi}] (distance to the next integer > 1e-30), eps = "
              f"{eps:.4f} (rounded up to a double), k = {k}; log10 f2 <= {d_log10_up2(lf2)} ({nt} terms){extra}; "
              f"failure <= 0.002 + 2 f2", ok, f"{time.time() - t:.1f} s")
    table8 = {350: (21, 263, "-49.29"), 400: (26, 300, "-151.38"), 500: (35, 375, "-352.58"),
              560: (41, 420, "-488.76"), 600: (45, 435, "-613.34"), 700: (55, 508, "-1048.20"),
              800: (65, 580, "-1565.01"), 900: (76, 653, "-2261.04"), 1000: (87, 700, "-2328.70"),
              1200: (108, 870, "-4758.79"), 1500: (142, 1050, "-6885.82"), 2000: (200, 1400, "-14154.69")}
    worst = Decimal(0)
    for n, (k_e, y3, l_e) in table8.items():
        t = time.time()
        k, N_lo, N_hi, eps, eps_f, gap = sharp_k_cert(n)
        l1, nt1 = p2_cert(n, k + 1, y3)
        l2, nt2 = p2_cert(n, n - y3 + 1, math.ceil(n / 2))
        mx = max(l1, l2)
        lf2 = mx + ((l1 - mx).exp() + (l2 - mx).exp()).ln()
        worst = max(worst, 2 * lf2.exp())
        check(f"Theorem 8, n = {n}: k = {k}, y3 = {y3}, log10 f2 <= {d_log10_up2(lf2)} ({nt1 + nt2} terms); "
              f"failure <= 0.002 + 2 f2", k == k_e and gap > Decimal("1e-30") and d_log10_up2(lf2) == Decimal(l_e),
              f"{time.time() - t:.1f} s")
    check("Theorem 8: 2 f2 <= 1.1e-49 at each of the twelve n", worst * (1 + Decimal("1e-20")) <= Decimal("1.1e-49"),
          f"largest 2 f2 = {worst:.4E}")
    check(f"every theta of the decimal Chernoff evaluations is >= 1e-9, as the error bound assumes ({len(_D_MGF)} "
          f"distinct thetas)", not SMALL_THETAS, f"{len(SMALL_THETAS)} smaller thetas")
    n = 400
    N_lo, N_hi, _eps, eps, _gap = p1_cert(n)
    # monotonicity of kappa_lo in the big-side size (used to take N' = N_hi)
    viol = sum(1 for N in range(N_lo, N_hi + 1, 5) for Np in range(N_lo, N_hi)
               if kappa_lo(N, Np + 1, eps) > kappa_lo(N, Np, eps))
    check("kappa_lo(N, N', eps) is non-increasing in N' (n = 400, every 5th N, every N')", viol == 0)
    # soundness of kappa_lo against the exact kappa on random capacity samples
    rng = random.Random(20261007)
    bad = 0
    for _ in range(1500):
        N, Np = rng.randint(3, 200), rng.randint(3, 200)
        outc = [rng.randint(1, 100) for _ in range(N)]
        inc = [rng.randint(1, 100) for _ in range(Np)]
        eps = 0.0
        for sample in (outc, inc):
            cnt = Counter(sample)
            run = 0
            for c in CAPS:
                run += cnt[c]
                eps = max(eps, abs(run / len(sample) - c / 100))
        bad += kappa_lo(N, Np, eps + 1e-12) > kappa_exact(outc, inc)
    check("kappa_lo <= exact kappa of Lemma 3(a) on 1500 random capacity samples (eps = observed CDF distance)",
          bad == 0)


# ------------------------------------------------------------------------------------------------ copies with counters
def arcs_of(n, edges):
    to, cap, adj = [], [], [[] for _ in range(n)]
    for u, v, c in edges:
        adj[u].append(len(to))
        to.append(v)
        cap.append(c)
        adj[v].append(len(to))
        to.append(u)
        cap.append(0)
    return to, cap, adj


def dinic_copy(net, hook=None):
    """Line-for-line copy of max_flow_dinic with counters. hook(to, cap, adj) is called at every phase start."""
    n, s, t, edges = net
    to, cap, adj = arcs_of(n, edges)
    flow = 0
    phases = []
    while True:
        if hook is not None:
            hook(to, cap, adj)
        level = [-1] * n
        level[s] = 0
        queue = deque([s])
        bfs = 0
        while queue:
            u = queue.popleft()
            for e in adj[u]:
                bfs += 1
                v = to[e]
                if cap[e] > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    queue.append(v)
        if level[t] == -1:
            phases.append({"lt": -1, "bfs": bfs, "scan": 0, "adv": 0, "ret": 0, "lens": []})
            return flow, phases
        it = [0] * n
        path = []
        u = s
        scan = adv = ret = 0
        lens = []
        while True:
            if u == t:
                f = min(cap[e] for e in path)
                lens.append(len(path))
                for e in path:
                    cap[e] -= f
                    cap[e ^ 1] += f
                flow += f
                path = []
                u = s
                continue
            arcs = adj[u]
            while it[u] < len(arcs):
                e = arcs[it[u]]
                scan += 1
                if cap[e] > 0 and level[to[e]] == level[u] + 1:
                    break
                it[u] += 1
            if it[u] < len(arcs):
                e = arcs[it[u]]
                path.append(e)
                adv += 1
                u = to[e]
            else:
                if not path:
                    break
                e = path.pop()
                ret += 1
                u = to[e ^ 1]
                it[u] += 1
        phases.append({"lt": level[t], "bfs": bfs, "scan": scan, "adv": adv, "ret": ret, "lens": lens})


def ek_copy(net):
    """Line-for-line copy of max_flow_edmonds_karp with counters: per BFS (reads, dequeued, path length)."""
    n, s, t, edges = net
    to, cap, adj = arcs_of(n, edges)
    flow = 0
    rec = []
    while True:
        parent_edge = [-1] * n
        parent_edge[s] = -2
        queue = deque([s])
        reads = deq = 0
        while queue and parent_edge[t] == -1:
            u = queue.popleft()
            deq += 1
            for e in adj[u]:
                reads += 1
                v = to[e]
                if cap[e] > 0 and parent_edge[v] == -1:
                    parent_edge[v] = e
                    queue.append(v)
        if parent_edge[t] == -1:
            rec.append((reads, deq, 0))
            return flow, rec
        bottleneck = None
        plen = 0
        v = t
        while v != s:
            e = parent_edge[v]
            plen += 1
            if bottleneck is None or cap[e] < bottleneck:
                bottleneck = cap[e]
            v = to[e ^ 1]
        v = t
        while v != s:
            e = parent_edge[v]
            cap[e] -= bottleneck
            cap[e ^ 1] += bottleneck
            v = to[e ^ 1]
        flow += bottleneck
        rec.append((reads, deq, plen))


# ------------------------------------------------------------------------------------------------ V: validation
def line_of(func, text, occurrence=1):
    src, start = inspect.getsourcelines(func)
    hits = [start + i for i, line in enumerate(src) if line.strip() == text]
    return hits[occurrence - 1]


def traced_counts(func, lines, net):
    lnmap = {line_of(func, text, k): name for name, (text, k) in lines.items()}
    counts = dict.fromkeys(lines, 0)
    code = func.__code__

    def local(frame, event, arg):
        if event == "line":
            name = lnmap.get(frame.f_lineno)
            if name is not None:
                counts[name] += 1
        return local

    def glob(frame, event, arg):
        return local if frame.f_code is code else None

    sys.settrace(glob)
    try:
        value = func(net)
    finally:
        sys.settrace(None)
    return value, counts


def part_validate():
    dl = {"phase": ("level = [-1] * n", 1), "read": ("v = to[e]", 1), "scan": ("e = arcs[it[u]]", 1),
          "adv": ("path.append(e)", 1), "ret": ("e = path.pop()", 1), "aug": ("flow += f", 1)}
    el = {"bfs": ("parent_edge = [-1] * n", 1), "deq": ("u = queue.popleft()", 1), "read": ("v = to[e]", 1),
          "aug": ("flow += bottleneck", 1)}
    ok_d = ok_e = 0
    cases = [(n, i) for n in (10, 20, 30, 40) for i in range(3)]
    for n, i in cases:
        net = HARNESS.generate_scaling(n, random.Random(f"dinic-short-paths|validate|{n}|{i}"))
        val, cnt = traced_counts(DINIC, dl, net)
        f, ph = dinic_copy(net)
        mine = {"phase": len(ph), "read": sum(p["bfs"] for p in ph), "scan": sum(p["scan"] for p in ph),
                "adv": sum(p["adv"] for p in ph), "ret": sum(p["ret"] for p in ph),
                "aug": sum(len(p["lens"]) for p in ph)}
        ok_d += val == f and cnt == mine
        val, cnt = traced_counts(EK, el, net)
        f, rec = ek_copy(net)
        mine = {"bfs": len(rec), "deq": sum(r[1] for r in rec), "read": sum(r[0] for r in rec), "aug": len(rec) - 1}
        ok_e += val == f and cnt == mine
    check(f"Dinic copy = unchanged code (phases, BFS reads, current-arc scans, advances, retreats, augmentations; "
          f"sys.settrace line counts) on {len(cases)} seeded instances, n = 10..40", ok_d == len(cases))
    check(f"Edmonds-Karp copy = unchanged code (BFS passes, dequeues, reads, augmentations) on {len(cases)} instances",
          ok_e == len(cases))


# ------------------------------------------------------------------------------------------------ lemma checks
def kappa_exact(outc, inc):
    """Lemma 3(a): min over feasible j of max(d - j, i*(j)) (small side = outc, big side = inc)."""
    small = sorted(outc)
    big = sorted(inc, reverse=True)
    best = len(small)
    sig = tau = i = 0
    for j in range(1, len(small) + 1):
        sig += small[j - 1]
        while i < len(big) and tau < sig:
            tau += big[i]
            i += 1
        if tau < sig:
            break
        best = min(best, max(len(small) - j, i))
    return best


def kappas(net):
    n, s, t, edges = net
    outc = [[] for _ in range(n)]
    inc = [[] for _ in range(n)]
    for u, v, c in edges:
        outc[u].append(c)
        inc[v].append(c)
    kp, km = [None] * n, [None] * n
    for v in range(n):
        if v not in (s, t):
            kp[v] = kappa_exact(outc[v], inc[v])
            km[v] = kappa_exact(inc[v], outc[v])
    return kp, km, outc, inc


def dist(n, src, to, cap, adj, reverse=False):
    d = [-1] * n
    d[src] = 0
    q = deque([src])
    while q:
        x = q.popleft()
        for e in adj[x]:
            y = to[e]
            r = cap[e ^ 1] if reverse else cap[e]
            if r > 0 and d[y] == -1:
                d[y] = d[x] + 1
                q.append(y)
    return d


class Tally:
    def __init__(self):
        self.cases = Counter()
        self.fails = Counter()

    def add(self, name, ok):
        self.cases[name] += 1
        if not ok:
            self.fails[name] += 1


# Names of the instance-level statements. REQUIRED ones must occur at least once in their part (the README states
# that they are checked there); OPTIONAL ones are reported with their count, which may be 0.
T_FEAS = "feasible"
T_VAL = "v(f) <= F"
T_L1A = "Lemma 1(a): no flow on edges into s or out of t"
T_L3A = "Lemma 3(a)"
T_L3B = "Lemma 3(b) via kappa"
T_X2 = "Theorem 4 step: |X_2| >= 1 + kappa+(u)"
T_PART = "Theorem 4 partition step: c(X2, Y3 - t) - c(L3, X2) <= 100(n - |X2|) and the backward mirror"
T_L2A = "Lemma 2(a)"
T_L2B = "Lemma 2(b)"
T_FLOW = "flow of copy = unchanged Dinic = unchanged Edmonds-Karp"
T_L0 = "Lemma 0(ii): at the end, the vertices reachable from s form a cut of capacity F"
T_LEV = "Lemma 1: level[t] strictly increasing, final BFS without t"
T_LEN = "Lemma 1: every augmenting path of a phase has exactly level[t] arcs"
T_DIST = "level[t] at a phase start = residual s-t distance"
T_L1C = ("Lemma 1(c) per non-final phase: at least one augmentation, BFS reads <= 2E, scans <= 2E + A_p l_p, "
         "advances = retreats + A_p l_p")
T_REM = "remark after Corollary 7: P - 1 <= F <= 100 min(n - 1, E) and reads <= 700 n E"
T_COR7 = "Corollary 7: reads <= 4E(P - 1) + 2E + sum_p A_p l_p <= 4E(P - 1) + 2E + (max level[t]) F"
T_P9I = "Prop 9(i): a phase / an EK path of length 1 iff (s, t) is an edge"
T_P923 = ("Prop 9: a length-2 phase iff some v has a_v, b_v > 0; a length-3 phase iff some edge goes from "
          "U = {a > b} to W = {b > a}")
T_P9P = "Prop 9: P = 1[(s,t) in E] + 1[length 2] + 1[length 3] + #(phases of length >= 4) + 1"
T_EKMON = "EK path lengths non-decreasing"
T_P10 = "Prop 10: phase lengths (Dinic) and path lengths (EK) with and without the edge (s, t)"
REQUIRED_S = [T_FEAS, T_VAL, T_L1A, T_L3A, T_L3B, T_X2, T_PART, T_L2A, T_L2B, T_FLOW, T_L0, T_LEV, T_LEN, T_DIST,
              T_L1C, T_REM, T_COR7, T_P9I, T_P923, T_P9P, T_EKMON, T_P10]
REQUIRED_R = [T_FEAS, T_VAL, T_L3A, T_L3B, T_L2A, T_L2B]
OPTIONAL_R = [T_X2, T_PART]


def report_tally(tally, required, optional=(), prefix=""):
    """One check line per name, zeros included: a required name fails if it never occurred; an optional name only
    reports its count. A name outside both lists (a typo) is treated as required."""
    names = list(required) + [x for x in optional if x not in required]
    names += sorted(x for x in tally.cases if x not in names)
    for name in names:
        cases, fails = tally.cases[name], tally.fails[name]
        if name in optional:
            check(f"{prefix}{name} ({cases} cases; reported, may be 0)", fails == 0, f"{fails} failures")
        else:
            check(f"{prefix}{name} ({cases} cases; must occur)", fails == 0 and cases >= 1, f"{fails} failures")


def lemma_checks(net, to, cap, adj, kp, km, outc, inc, F, tally, algorithm_flow=True):
    """Lemma 2 (i = 2, 3 forward; j = 2, 3 backward, when applicable), Lemma 3 and the |X_2| step of Theorem 4, for
    the flow stored in cap. Returns d_f(s, t) (-1 if t is unreachable)."""
    n, s, t, edges = net
    f = [cap[2 * i + 1] for i in range(len(edges))]
    tally.add(T_FEAS, all(0 <= fi <= c for fi, (_u, _v, c) in zip(f, edges)))
    val = sum(fi for fi, (u, v, c) in zip(f, edges) if u == s) - sum(fi for fi, (u, v, c) in zip(f, edges) if v == s)
    tally.add(T_VAL, val <= F)
    if algorithm_flow:
        tally.add(T_L1A, all(fi == 0 for fi, (u, v, c) in zip(f, edges) if v == s or u == t))
    ds = dist(n, s, to, cap, adj)
    dt = dist(n, t, to, cap, adj, reverse=True)
    big = 10 ** 9
    dsv = [x if x >= 0 else big for x in ds]
    dtv = [x if x >= 0 else big for x in dt]
    for v in range(n):
        if v in (s, t):
            continue
        nplus = {to[e] for e in adj[v] if cap[e] > 0}
        nminus = {to[e] for e in adj[v] if cap[e ^ 1] > 0}
        tally.add(T_L3A, len(nplus) >= kp[v] and len(nminus) >= km[v])
        hp = sum(1 for c in outc[v] if c >= 42)
        hm = sum(1 for c in inc[v] if c >= 42)
        tally.add(T_L3B, 142 * kp[v] >= 42 * hp and 142 * km[v] >= 42 * hm)
    if 3 <= dsv[t] < big:
        x2 = sum(1 for x in dsv if x <= 2)
        tally.add(T_X2, all(x2 >= 1 + kp[u] for u in range(n) if dsv[u] == 1))
    if 4 <= dsv[t] < big:
        # partition-level step of Theorem 4: for the actual (X2, L3, Y3) the forward P2 inequality fails, and for the
        # actual (Z3, S3, B2) the backward one fails (consequences of Lemma 2 and the bounds on c_in(t), c_out(s))
        fwd = sum(c for u, v, c in edges if dsv[u] <= 2 and dsv[v] > 3 and v != t) \
            - sum(c for u, v, c in edges if dsv[u] == 3 and dsv[v] <= 2)
        bwd = sum(c for u, v, c in edges if dtv[u] > 3 and u != s and dtv[v] <= 2) \
            - sum(c for u, v, c in edges if dtv[u] <= 2 and dtv[v] == 3)
        tally.add(T_PART, fwd <= 100 * (n - sum(1 for x in dsv if x <= 2)) and bwd <= 100 * (n - sum(1 for x in dtv if x <= 2)))
    for i in (2, 3):
        if dsv[t] > i:
            cXY = fXY = fYX = fLX = 0
            for fi, (u, v, c) in zip(f, edges):
                xu, xv = dsv[u], dsv[v]
                if xu <= i - 1 and xv > i:
                    cXY += c
                    fXY += fi
                if xu > i and xv <= i - 1:
                    fYX += fi
                if xu == i and xv <= i - 1:
                    fLX += fi
            tally.add(T_L2A, fXY == cXY and fYX == 0 and cXY <= val + fLX)
        if dtv[s] > i:
            cZB = fZB = fBZ = fBS = 0
            for fi, (u, v, c) in zip(f, edges):
                bu, bv = dtv[u], dtv[v]
                if bu > i and bv <= i - 1:
                    cZB += c
                    fZB += fi
                if bu <= i - 1 and bv > i:
                    fBZ += fi
                if bu <= i - 1 and bv == i:
                    fBS += fi
            tally.add(T_L2B, fZB == cZB and fBZ == 0 and cZB <= val + fBS)
    return ds[t]


# ------------------------------------------------------------------------------------------------ S: simulation
def toggled(net):
    """The same network with the edge (s, t) removed if present, or appended with capacity 50 if absent."""
    n, s, t, edges = net
    if any(u == s and v == t for u, v, c in edges):
        return n, s, t, tuple(e for e in edges if not (e[0] == s and e[1] == t)), True
    return n, s, t, edges + ((s, t, 50),), False


def part_sim():
    tally = Tally()
    plan = [(20, 300), (40, 200), (80, 80), (160, 25)]
    if FULL:
        plan += [(240, 40), (320, 20), (400, 10)]
    for n, reps in plan:
        t0 = time.time()
        for i in range(reps):
            net = HARNESS.generate_scaling(n, random.Random(f"dinic-short-paths|{n}|{i}"))
            _, s, t, edges = net
            E = len(edges)
            kp, km, outc, inc = kappas(net)
            F = DINIC(net)
            seen = []

            final_cut = []

            def hook(to, cap, adj):
                seen.append(lemma_checks(net, to, cap, adj, kp, km, outc, inc, F, tally))
                ds = dist(n, s, to, cap, adj)
                if ds[t] == -1:
                    side = [d >= 0 for d in ds]
                    final_cut.append(sum(c for u, v, c in edges if side[u] and not side[v]))

            flow, ph = dinic_copy(net, hook)
            tally.add(T_FLOW, flow == F == EK(net))
            tally.add(T_L0, final_cut == [F])
            lts = [p["lt"] for p in ph]
            tally.add(T_LEV, lts[-1] == -1 and all(a < b for a, b in zip(lts[:-2], lts[1:-1])))
            tally.add(T_LEN, all(all(L == p["lt"] for L in p["lens"]) for p in ph[:-1]))
            tally.add(T_DIST, [d for d in seen] == lts)
            for p in ph[:-1]:
                al = sum(p["lens"])
                tally.add(T_L1C,
                          len(p["lens"]) >= 1 and p["scan"] <= 2 * E + al and p["adv"] == p["ret"] + al
                          and p["bfs"] <= 2 * E)
            reads = sum(p["bfs"] + p["scan"] for p in ph)
            P = len(ph)
            maxlen = max(lts)
            tally.add(T_REM,
                      P - 1 <= F <= 100 * min(n - 1, E) and reads <= 700 * n * E)
            tally.add(T_COR7,
                      reads <= 4 * E * (P - 1) + 2 * E + sum(sum(p["lens"]) for p in ph)
                      <= 4 * E * (P - 1) + 2 * E + maxlen * F)
            # Proposition 9: phase structure
            a = {v: 0 for v in range(n)}
            b = {v: 0 for v in range(n)}
            st = False
            mid = []
            for u, v, c in edges:
                if u == s and v == t:
                    st = True
                elif u == s:
                    a[v] = c
                elif v == t:
                    b[u] = c
                elif u not in (s, t) and v not in (s, t):
                    mid.append((u, v))
            M = range(1, n - 1)
            has2 = any(a[v] > 0 and b[v] > 0 for v in M)
            has3 = any(a[u] > b[u] and b[w] > a[w] for u, w in mid)
            ekrec = ek_copy(net)[1]
            eklens = [r[2] for r in ekrec[:-1]]
            tally.add(T_P9I, (1 in lts) == st == (1 in eklens))
            tally.add(T_P923, (2 in lts) == has2 and (3 in lts) == has3
                      and (2 in eklens) == has2 and (3 in eklens) == has3)
            tally.add(T_P9P,
                      P == st + has2 + has3 + sum(1 for x in lts if x >= 4) + 1)
            tally.add(T_EKMON, all(x <= y for x, y in zip(eklens, eklens[1:])))
            # Proposition 10: the edge (s, t) adds exactly one phase / one path of length 1
            n2, s2, t2, e2, had = toggled(net)
            lts2 = [p["lt"] for p in dinic_copy((n2, s2, t2, e2))[1]]
            ek2 = [r[2] for r in ek_copy((n2, s2, t2, e2))[1][:-1]]
            if had:
                ok = lts == [1] + lts2 and eklens == [1] + ek2
            else:
                ok = lts2 == [1] + lts and ek2 == [1] + eklens
            tally.add(T_P10, ok)
        print(f"       n = {n}: {reps} instances checked ({time.time() - t0:.1f} s)")
    report_tally(tally, REQUIRED_S)


# ------------------------------------------------------------------------------------------------ R: random flows
def random_path(n, s, t, to, cap, adj, rng):
    seen = [False] * n
    seen[s] = True
    stack = [s]
    par = {}
    while stack:
        x = stack.pop()
        if x == t:
            path = []
            v = t
            while v != s:
                path.append(par[v])
                v = to[par[v] ^ 1]
            return path
        arcs = [e for e in adj[x] if cap[e] > 0 and not seen[to[e]]]
        rng.shuffle(arcs)
        for e in arcs:
            seen[to[e]] = True
            par[to[e]] = e
            stack.append(to[e])
    return None


def random_cycle(n, to, cap, adj, rng):
    v0 = rng.randrange(n)
    pos = {v0: 0}
    walk = []
    v = v0
    for _ in range(4 * n):
        arcs = [e for e in adj[v] if cap[e] > 0]
        if not arcs:
            return None
        e = rng.choice(arcs)
        walk.append(e)
        v = to[e]
        if v in pos:
            return walk[pos[v]:]
        pos[v] = len(walk)
    return None


def push(path, cap):
    amount = min(cap[e] for e in path)
    for e in path:
        cap[e] -= amount
        cap[e ^ 1] += amount


def ek_prefix(net, k):
    n, s, t, edges = net
    to, cap, adj = arcs_of(n, edges)
    for _ in range(k):
        parent = [-1] * n
        parent[s] = -2
        q = deque([s])
        while q and parent[t] == -1:
            u = q.popleft()
            for e in adj[u]:
                if cap[e] > 0 and parent[to[e]] == -1:
                    parent[to[e]] = e
                    q.append(to[e])
        if parent[t] == -1:
            break
        path = []
        v = t
        while v != s:
            path.append(parent[v])
            v = to[parent[v] ^ 1]
        push(path, cap)
    return to, cap, adj


def part_random_flows():
    tally = Tally()
    for n, reps in ((40, 8), (80, 4)):
        for i in range(reps):
            net = HARNESS.generate_scaling(n, random.Random(f"dinic-short-paths|rf|{n}|{i}"))
            _, s, t, edges = net
            kp, km, outc, inc = kappas(net)
            F = DINIC(net)
            A = len(ek_copy(net)[1]) - 1
            rng = random.Random(f"dinic-short-paths|rf-rng|{n}|{i}")
            for kind in (0, 1, 2) * 3:
                if kind == 0:          # random Ford-Fulkerson prefix (random residual paths, full bottleneck)
                    to, cap, adj = arcs_of(n, edges)
                    for _ in range(rng.randint(1, 2 * n)):
                        p = random_path(n, s, t, to, cap, adj, rng)
                        if p is None:
                            break
                        push(p, cap)
                else:                  # an EK prefix (kind 1) or a maximum flow (kind 2), then random residual cycles
                    to, cap, adj = ek_prefix(net, rng.randint(0, A) if kind == 1 else A + 1)
                    for _ in range(rng.randint(1, 2 * n)):
                        c = random_cycle(n, to, cap, adj, rng)
                        if c:
                            push(c, cap)
                lemma_checks(net, to, cap, adj, kp, km, outc, inc, F, tally, algorithm_flow=False)
    report_tally(tally, REQUIRED_R, OPTIONAL_R, prefix="random feasible flows: ")


def main():
    t0 = time.time()
    for name, fn in (("K", part_constants), ("A", part_analytic), ("P", part_computed), ("V", part_validate),
                     ("S", part_sim), ("R", part_random_flows)):
        t = time.time()
        print(f"== part {name}")
        fn()
        print(f"   ({time.time() - t:.1f} s)")
    print(f"total {time.time() - t0:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
