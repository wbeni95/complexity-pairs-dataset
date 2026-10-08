#!/usr/bin/env python3
"""Verifier for theorems/max-flow-random-dense-trivial-min-cut (see README.md in this folder).

Computations are evidence; the proof is in the README. Standard library only, no network, deterministic (fixed
seeds). Exit code 0 only if every check passes.

Model (README): vertices 0..n-1, s = 0, t = n - 1, M = the other m = n - 2 vertices; every ordered pair (u, v),
u != v, is an edge with probability 1/2, with a capacity uniform on 1..100, all independent. X = capacity of one
ordered pair (0 if absent). This is generate_scaling of pairs/max-flow-edmonds-karp-vs-dinic with ideal random bits.

Checks:
  K  exact constants (fractions): E X, Var X, P(a = b), P(a != b), 2 (q - 1/2)^2.
  C  the union bound B(n) of Theorem 1(b) for P(not C), certified in 50-digit decimal arithmetic: the table values
     (upper bounds rounded up), the computed bound >= 1 for n in [4, 21], B(n) < 1 for n in [22, 201], B(n) < 5.48e-5
     and B(n) <= 1/n for n in [40, 201], and the explicit tail bound (theta = 1/2) for every n >= 202.
  T  the tie bound of Theorem 1(c): Littlewood-Offord count (brute force), the binomial inequality
     C(k, floor(k/2))^2 k <= 4^k (exact, k <= 2000), and exact tie probabilities at n = 20, 40 against the bound.
  D  Lemma 0 and Theorem 1(a) on seeded instances of the entry's own generator: the cut identities for every cut;
     by enumerating every cut, that both implementations return the minimum cut capacity; the event C by enumeration,
     and on C: the minimum cuts are exactly the trivial cuts attaining the minimum.
  W  Lemma 0(i) on larger seeded instances: both implementations agree and return at most min(c_out(s), c_in(t)).
  A  the appendix facts A1-A4 on finite cases (exact distributions, exact binomial tails, all antichains).
Usage (from the repository root): python theorems/max-flow-random-dense-trivial-min-cut/verify.py [--full]
(--full adds instances with n = 320, 640 to part W.)
"""
import importlib.util
import math
import random
import sys
import time
from decimal import Decimal, getcontext
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIR = ROOT / "pairs" / "max-flow-edmonds-karp-vs-dinic"
FULL = "--full" in sys.argv[1:]
FAILURES = []
CAPS = range(1, 101)
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
    pmf = {0: Fraction(1, 2)}
    pmf.update({c: Fraction(1, 200) for c in CAPS})
    ex = sum(c * p for c, p in pmf.items())
    var = sum(c * c * p for c, p in pmf.items()) - ex * ex
    p_eq = sum(p * p for p in pmf.values())
    q = 1 - p_eq
    check("E X = 101/4 and Var X = 16867/16", ex == Fraction(101, 4) and var == Fraction(16867, 16),
          f"E X = {ex}, Var X = {var}")
    check("P(a_v = b_v) = 101/400, so q = P(a_v != b_v) = 299/400", p_eq == Fraction(101, 400) and q == Fraction(299, 400))
    val = 2 * (q - Fraction(1, 2)) ** 2
    check("2 (q - 1/2)^2 = 19602/160000 = 0.1225125 >= 0.1225", val == Fraction(19602, 160000) and val >= Fraction(1225, 10000))


# ------------------------------------------------------------------------------------------------ C: P(not C)
def log_phi(th):
    """log E exp(-th X), direct sum."""
    return math.log(0.5 + math.fsum(math.exp(-th * c) for c in CAPS) / 200)


def tilted_mean(th):
    """E[X e^{-th X}] / E[e^{-th X}] (decreasing in th; equals E X = 25.25 at th = 0)."""
    w = [math.exp(-th * c) for c in CAPS]
    return (math.fsum(c * x for c, x in zip(CAPS, w)) / 200) / (0.5 + math.fsum(w) / 200)


def rate(k):
    """(theta_k, g_k) with g_k = 100 theta/k + log phi(theta) evaluated at theta_k, an approximate minimiser found by
    bisection. Any theta >= 0 gives a valid Chernoff bound, so only the final evaluation matters."""
    rho = 100 / k
    if rho >= 25.25:
        return 0.0, 0.0
    lo, hi = 0.0, 1.0
    while tilted_mean(hi) > rho:
        lo, hi = hi, 2 * hi
    for _ in range(50):
        mid = (lo + hi) / 2
        if tilted_mean(mid) > rho:
            lo = mid
        else:
            hi = mid
    th = (lo + hi) / 2
    return th, min(0.0, rho * th + log_phi(th))


RATES = {}


def get_rate(k):
    if k not in RATES:
        RATES[k] = rate(k)
    return RATES[k]


def log_binom(a, b):
    return math.lgamma(a + 1) - math.lgamma(b + 1) - math.lgamma(a - b + 1)


def lse(xs):
    mx = max(xs)
    return mx + math.log(math.fsum(math.exp(x - mx) for x in xs))


def fmt(logv):
    e = math.floor(logv / LN10)
    return f"{10 ** (logv / LN10 - e):.4f}e{e}"


# Certified evaluation (README, "Computed values"): every value that a claim rests on is recomputed in 50-digit
# decimal arithmetic. Python's decimal module rounds +, -, *, / and the functions exp and ln correctly; the theta of
# each term is the double-precision bisection value above, converted to decimal exactly (any theta >= 0 gives a valid
# Chernoff bound). phi(theta) is evaluated in closed form (a geometric sum). The accumulated relative error of a
# computed sum is far below 1e-25; every comparison uses the margin REL = 1e-20.
getcontext().prec = 50
REL = Decimal("1e-20")
D_LNFACT = [Decimal(0)]
for _i in range(1, 1601):
    D_LNFACT.append(D_LNFACT[-1] + Decimal(_i).ln())
_D_LNPHI = {}
SMALL_THETAS = []          # thetas with 0 < theta < 1e-6 (the README's error bound assumes none); reported by a check


def d_ln_phi(th):
    """ln phi(theta) = ln(1/2 + (1/200) q (1 - q^100)/(1 - q)), q = e^-theta, in 50-digit decimal."""
    if th not in _D_LNPHI:
        if th == 0.0:
            _D_LNPHI[th] = Decimal(0)
        else:
            if th < 1e-6:                  # the cancellation in 1 - q is harmless only for theta >= 1e-6
                SMALL_THETAS.append(th)
            T = Decimal(th)
            q, Q = (-T).exp(), (-100 * T).exp()
            _D_LNPHI[th] = (Decimal(1) / 2 + q * (1 - Q) / (1 - q) / 200).ln()
    return _D_LNPHI[th]


def d_terms(n):
    """Natural logs (decimal) of the terms of the union bound, j = 1..floor(m/2), the factor 2 for j != m/2."""
    m = n - 2
    out = []
    for j in range(1, m // 2 + 1):
        k = m - j
        th, _g = get_rate(k)
        mult = Decimal(1) if 2 * j == m else Decimal(2)
        out.append(mult.ln() + D_LNFACT[m] - D_LNFACT[j] - D_LNFACT[k] + 100 * j * Decimal(th) + j * k * d_ln_phi(th))
    return out


def d_bound(n):
    """The union bound of Theorem 1(b) with the script's thetas, as a decimal (summed term by term)."""
    return sum((t.exp() for t in d_terms(n)), Decimal(0))


def round_up_4(x):
    """x rounded up to 4 significant digits (decimal)."""
    e = x.adjusted()
    q = Decimal(1).scaleb(e - 3)
    return x.quantize(q, rounding="ROUND_CEILING")


def part_cut():
    raw = {}
    for n in (20, 30, 40, 60, 80, 160, 400, 800, 1200):
        m = n - 2
        terms = []
        for j in range(1, m // 2 + 1):
            k = m - j
            _th, g = get_rate(k)
            terms.append(math.log(1 if 2 * j == m else 2) + log_binom(m, j) + j * k * g)
        raw[n] = lse(terms)
    line = ", ".join(f"n={n}: {fmt(raw[n])}" for n in raw)
    print(f"       union bound for P(not C), double precision (for display): {line}")
    # table of the README: upper bounds rounded up to 4 significant digits, certified in decimal
    table = {20: "7.238", 30: "7.215E-3", 40: "5.474E-5", 60: "1.385E-9", 80: "1.881E-14", 160: "3.962E-35",
             400: "4.876E-101", 800: "9.785E-215", 1200: "3.120E-330"}
    got = {n: d_bound(n) for n in table}
    ok = all(got[n] * (1 + REL) <= Decimal(v) and round_up_4(got[n]) == Decimal(v) for n, v in table.items())
    check(f"README table of Theorem 1(b): B(n) <= the listed value (the decimal sum rounded up to 4 significant "
          f"digits) at the {len(table)} listed n", ok, ", ".join(f"n={n}: {got[n]:.6E}" for n in table))
    small = {n: d_bound(n) for n in range(4, 22)}
    print("       computed bound for n = 4..21: " + ", ".join(f"{float(v):.3g}" for v in small.values()))
    check("the computed bound is >= 1 for every n in [4, 21] (part (b) gives nothing there; 18 values)",
          all(v * (1 - REL) >= 1 for v in small.values()))
    mid = {n: d_bound(n) for n in range(22, 202)}
    nterms = sum(n // 2 - 1 for n in mid)
    worst40 = max(range(40, 202), key=lambda n: mid[n])
    check(f"B(n) < 1 for every n in [22, 201], and B(n) < 5.48e-5 and B(n) <= 1/n for every n in [40, 201] "
          f"(180 values of n, {nterms} terms summed in decimal)",
          all(v * (1 + REL) < 1 for v in mid.values())
          and all(mid[n] * (1 + REL) < Decimal("5.48E-5") and mid[n] * n * (1 + REL) <= 1 for n in range(40, 202)),
          f"B(22) <= {mid[22]:.6f}; the largest value on [40, 201] is at n = {worst40}: {mid[worst40]:.6E}")
    check(f"every theta used in the decimal evaluations is 0 or >= 1e-6, as the README's error bound assumes "
          f"({len(_D_LNPHI)} distinct thetas)", not SMALL_THETAS, f"{len(SMALL_THETAS)} smaller thetas")
    # tail n >= 202 (m >= 200): theta = 1/2
    lph = d_ln_phi(0.5)
    lr = Decimal(200).ln() + 50 + 100 * lph
    r = lr.exp()
    tail = 2 * r / (1 - r)
    check("tail, m >= 200 (theta = 1/2): ln r(m) = ln m + 50 + (m/2) ln phi(1/2) is about -12.487 at m = 200 and "
          "decreasing in m (1/m + (1/2) ln phi(1/2) < 0 for m >= 3), so B(n) <= 2r/(1 - r) < 7.6e-6 for every n >= 202; "
          "ln(n r) + ln(1/(1 - r)) is decreasing as well and n 2r/(1 - r) <= 1 at n = 202, so B(n) <= 1/n for n >= 202",
          Decimal(1) / 3 + lph / 2 < 0 and tail * (1 + REL) < Decimal("7.6E-6") and 202 * tail * (1 + REL) <= 1
          and Decimal(1) / 202 + Decimal(1) / 200 + lph / 2 < 0,
          f"phi(1/2) = {lph.exp():.12f}, ln r(200) = {lr:.6f}, 2r/(1 - r) = {tail:.6E}, 202 * 2r/(1 - r) = "
          f"{202 * tail:.3E}")


# ------------------------------------------------------------------------------------------------ T: ties
def part_ties():
    rng = random.Random(1)
    bad = 0
    for _ in range(300):
        k = rng.randint(1, 12)
        d = [rng.randint(1, 6) for _ in range(k)]
        zero = sum(1 for mask in range(1 << k) if sum(x if mask >> i & 1 else -x for i, x in enumerate(d)) == 0)
        bad += zero > math.comb(k, k // 2)
    check("Littlewood-Offord count: #{eps in {+1,-1}^k : sum eps_i d_i = 0} <= C(k, floor(k/2)) "
          "(300 seeded vectors of positive integers, k <= 12)", bad == 0)
    check("C(k, floor(k/2))^2 * k <= 4^k for every k = 1..2000 (exact integers)",
          all(math.comb(k, k // 2) ** 2 * k <= 4 ** k for k in range(1, 2001)))
    for n, ex_lb, ex_ub in ((20, 0.00203, 0.00205), (40, 0.00140, 0.00142)):
        m = n - 2
        # A = sum of m iid copies of a_v (weight 100 at 0, weight 1 at 1..100; total 200), exact integer counts
        cnt = [1]
        for _ in range(m):
            pre = [0]
            for x in cnt:
                pre.append(pre[-1] + x)
            new = []
            for s_ in range(len(cnt) + 100):
                lo_ = max(0, s_ - 100)
                hi_ = min(len(cnt), s_)          # indices s_-100 .. s_-1
                v = (pre[hi_] - pre[lo_]) if hi_ > lo_ else 0
                if s_ < len(cnt):
                    v += 100 * cnt[s_]
                new.append(v)
            cnt = new
        tie = Fraction(sum(x * x for x in cnt), 200 ** (2 * m))
        bound = math.sqrt(2 / m) + math.exp(-0.1225 * m)
        pre = [0]
        for x in cnt:
            pre.append(pre[-1] + x)
        less = sum(cnt[y] * pre[y] for y in range(len(cnt)))                  # weight of {B < A}
        greater = sum(cnt[y] * (pre[-1] - pre[y + 1]) for y in range(len(cnt)))  # weight of {B > A}
        check(f"n = {n}: exact P(c_out(s) = c_in(t)) = sum_x P(A = x)^2 = {float(tie):.5f} <= sqrt(2/m) + "
              f"e^(-0.1225 m) = {bound:.3f}, and P(Delta < 0) = P(Delta > 0) = (1 - P(Delta = 0))/2 exactly",
              ex_lb < float(tie) < ex_ub and float(tie) <= bound and less == greater
              and Fraction(less, 200 ** (2 * m)) == (1 - tie) / 2)


# ------------------------------------------------------------------------------------------------ D: small instances
def matrix_of(net):
    n, s, t, edges = net
    c = [[0] * n for _ in range(n)]
    for u, v, cap in edges:
        c[u][v] = cap
    return c


def part_small():
    # D1: the cut identities, every cut, direct capacities from the edge list
    n_total = n_ident = 0
    for n in (6, 8, 10, 12):
        for i in range(30):
            net = HARNESS.generate_scaling(n, random.Random(f"trivial-min-cut|small|{n}|{i}"))
            _, s, t, edges = net
            M = list(range(1, n - 1))
            m = len(M)
            c = matrix_of(net)
            a = [c[s][v] for v in range(n)]
            b = [c[v][t] for v in range(n)]
            cout = sum(c[s])
            cin = sum(c[v][t] for v in range(n))
            ident = True
            for mask in range(1 << m):
                Sp = [M[i_] for i_ in range(m) if mask >> i_ & 1]
                Rest = [M[i_] for i_ in range(m) if not mask >> i_ & 1]
                inner = sum(c[x][y] for x in Sp for y in Rest)
                cap_s = c[s][t] + sum(a[v] for v in Rest) + sum(b[x] for x in Sp) + inner
                side = set(Sp) | {s}
                direct = sum(cap for u, v, cap in edges if u in side and v not in side)
                ident &= direct == cap_s
                ident &= cap_s - cout == inner - sum(a[x] - b[x] for x in Sp)
                ident &= cap_s - cin == inner - sum(b[v] - a[v] for v in Rest)
            n_ident += ident
            n_total += 1
    check(f"cut identities cap(S) = c(s,t) + a(M - S') + b(S') + c(S', M - S') and the two difference formulas, "
          f"for every cut of {n_total} seeded instances (n = 6, 8, 10, 12)", n_ident == n_total)
    # D2: the event C by enumeration (Gray code), the set of minimum cuts, the flow value of the entry code
    n_c = n_min_ok = n_flow_ok = n_tot2 = n_lemma0 = 0
    for n, reps in ((14, 30), (16, 30), (18, 20)):
        for i in range(reps):
            net = HARNESS.generate_scaling(n, random.Random(f"trivial-min-cut|event|{n}|{i}"))
            _, s, t, edges = net
            M = list(range(1, n - 1))
            m = len(M)
            c = matrix_of(net)
            cout = sum(c[s])
            cin = sum(c[v][t] for v in range(n))
            in_s = [False] * n
            inner = size = diff_ab = 0
            prev = 0
            cond_c = True
            best = cout                       # S' = empty
            argmins = {0}
            for k in range(1, 1 << m):
                g = k ^ (k >> 1)
                x = M[(g ^ prev).bit_length() - 1]
                prev = g
                if not in_s[x]:
                    inner += sum(c[x][y] for y in M if not in_s[y] and y != x) - sum(c[u][x] for u in M if in_s[u])
                    in_s[x] = True
                    size += 1
                    diff_ab += c[s][x] - c[x][t]
                else:
                    in_s[x] = False
                    size -= 1
                    diff_ab -= c[s][x] - c[x][t]
                    inner -= sum(c[x][y] for y in M if not in_s[y] and y != x) - sum(c[u][x] for u in M if in_s[u])
                if 0 < size < m and not inner > 100 * min(size, m - size):
                    cond_c = False
                cap_s = cout + inner - diff_ab
                if cap_s < best:
                    best, argmins = cap_s, {g}
                elif cap_s == best:
                    argmins.add(g)
            n_tot2 += 1
            Fd, Fe = DINIC(net), EK(net)
            n_lemma0 += Fd == Fe == best
            if cond_c:
                n_c += 1
                trivial = ({0} if cout == best else set()) | ({(1 << m) - 1} if cin == best else set())
                n_min_ok += best == min(cout, cin) and argmins == trivial
                n_flow_ok += Fd == Fe == min(cout, cin)
    check(f"Lemma 0: on all {n_tot2} instances (n = 14, 16, 18) both implementations return the minimum cut capacity "
          f"(every cut enumerated)", n_lemma0 == n_tot2)
    check(f"on the event C ({n_c} of {n_tot2} seeded instances, n = 14, 16, 18): the minimum cuts are exactly the "
          f"trivial cuts attaining min(c_out(s), c_in(t))", n_min_ok == n_c and n_c >= 20)
    check("on the event C: Edmonds-Karp and Dinic (entry code) both return min(c_out(s), c_in(t))", n_flow_ok == n_c)


# ------------------------------------------------------------------------------------------------ W: weak duality
def part_weak():
    plan = ((20, 400), (40, 300), (80, 150), (160, 60)) + (((320, 30), (640, 8)) if FULL else ())
    total = good = 0
    for n, reps in plan:
        for i in range(reps):
            net = HARNESS.generate_scaling(n, random.Random(f"trivial-min-cut|sim|{n}|{i}"))
            _, s, t, edges = net
            cout = sum(cap for u, v, cap in edges if u == s)
            cin = sum(cap for u, v, cap in edges if v == t)
            F = DINIC(net)
            good += F == EK(net) and F <= min(cout, cin)
            total += 1
    check(f"Lemma 0(i) on {total} seeded instances (n = " + ", ".join(str(n) for n, _ in plan)
          + "): both implementations agree and return at most min(c_out(s), c_in(t))", good == total)


# ------------------------------------------------------------------------------------------------ A: appendix
def sum_counts(N):
    """Integer weights of the sum of N iid copies of X (weight 100 at 0, weight 1 at 1..100; total 200^N)."""
    cnt = [1]
    for _ in range(N):
        pre = [0]
        for x in cnt:
            pre.append(pre[-1] + x)
        new = []
        for s_ in range(len(cnt) + 100):
            lo_, hi_ = max(0, s_ - 100), min(len(cnt), s_)
            v = (pre[hi_] - pre[lo_]) if hi_ > lo_ else 0
            if s_ < len(cnt):
                v += 100 * cnt[s_]
            new.append(v)
        cnt = new
    return cnt


def part_appendix():
    bad = cases = 0
    for N in range(1, 7):
        cnt = sum_counts(N)
        tot = 200 ** N
        pre = [0]
        for x in cnt:
            pre.append(pre[-1] + x)
        for T in range(0, 100 * N + 1, 7):
            lower = pre[T + 1] / tot                  # P(sum <= T)
            upper = (pre[-1] - pre[T]) / tot          # P(sum >= T)
            for th in (0.001, 0.01, 0.03, 0.1, 0.3, 1.0, 3.0):
                lphi = math.log(0.5 + math.fsum(math.exp(-th * c) for c in CAPS) / 200)
                lpsi = math.log(0.5 + math.fsum(math.exp(th * c) for c in CAPS) / 200)
                if lower > 0:
                    bad += math.log(lower) > th * T + N * lphi + 1e-12
                if upper > 0:
                    bad += math.log(upper) > -th * T + N * lpsi + 1e-12
                cases += 2
    check(f"A1 (Chernoff): exact lower and upper tails of sums of N = 1..6 copies of X, T on a grid, 7 values of "
          f"theta ({cases} cases)", bad == 0)
    rng = random.Random(3)
    bad = 0
    for _ in range(300):
        k = rng.randint(2, 6)
        vals = [rng.uniform(-5, 5) for _ in range(k)]
        w = [rng.random() + 1e-3 for _ in range(k)]
        tw = sum(w)
        pr = [x / tw for x in w]
        mean = sum(p_ * v for p_, v in zip(pr, vals))
        ys = [v - mean for v in vals]
        a, b = min(ys), max(ys)
        for lam in (-3, -1, -0.3, -0.05, 0.05, 0.3, 1, 3):
            lhs = math.fsum(p_ * math.exp(lam * y) for p_, y in zip(pr, ys))
            bad += lhs > math.exp(lam * lam * (b - a) ** 2 / 8) * (1 + 1e-12)
    check("A2 (Hoeffding's lemma): 300 seeded discrete distributions with mean 0, 8 values of lambda", bad == 0)
    bad = cases = 0
    for N in range(1, 81):
        for p_ in (0.1, 0.25, 0.295, 0.37375, 0.5, 0.7475):
            pmf = [math.comb(N, k) * p_ ** k * (1 - p_) ** (N - k) for k in range(N + 1)]
            cdf = 0.0
            for k in range(N + 1):
                cdf += pmf[k]
                if k <= N * p_:
                    bad += cdf > math.exp(-2 * (N * p_ - k) ** 2 / N) * (1 + 1e-9)
                    cases += 1
                if k >= N * p_:
                    bad += math.fsum(pmf[k:]) > math.exp(-2 * (k - N * p_) ** 2 / N) * (1 + 1e-9)
                    cases += 1
    check(f"A3 (Hoeffding's inequality): exact binomial tails, N <= 80, six values of p ({cases} cases)", bad == 0)
    for k in (4, 5):
        best = count = 0
        stack = [(0, [])]
        while stack:
            start, fam = stack.pop()
            count += 1
            best = max(best, len(fam))
            for x in range(start, 1 << k):
                if all((x & y) != x and (x & y) != y for y in fam):
                    stack.append((x + 1, fam + [x]))
        check(f"A4 (Sperner): all {count} antichains of subsets of a {k}-set (the empty family included) have at most "
              f"C({k}, {k // 2}) = {math.comb(k, k // 2)} members",
              best == math.comb(k, k // 2) and count == {4: 168, 5: 7581}[k])


def main():
    t0 = time.time()
    for name, fn in (("K", part_constants), ("C", part_cut), ("T", part_ties), ("D", part_small), ("W", part_weak),
                     ("A", part_appendix)):
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
