"""Exact query-complexity measures of small Boolean functions f: {0,1}^n -> {0,1}.

A function is a truth table `tt` (tuple of 0/1 of length 2^n, index = input with bit i = x_i).

Measures (definitions as in Buhrman & de Wolf 2002, Complexity measures and decision tree complexity: a survey,
Theoret. Comput. Sci. 288, doi:10.1016/S0304-3975(01)00144-X):
  D(f)    deterministic query complexity: minimax over decision trees, computed by dynamic programming over the
          3^n subcubes (restrictions): D(rho) = 0 if f is constant on rho, else 1 + min_i max_b D(rho[x_i = b]).
  deg(f)  exact degree of the unique multilinear real polynomial equal to f (Moebius transform, exact integers).
  s, bs, C  sensitivity, block sensitivity, certificate complexity (brute force; n <= 5).
  adeg_eps(f)  approximate degree: least d such that some real polynomial of degree <= d is within eps of f on
          every input. For SYMMETRIC f, Minsky-Papert symmetrisation (Perceptrons, 1969 [book]) reduces this to a
          univariate discrete Chebyshev problem on k = |x| in {0, ..., n}, solved here EXACTLY by the Stiefel
          exchange algorithm with a primal certificate (the polynomial) and a dual certificate (alternating weights
          phi orthogonal to all polynomials of degree <= d: a "dual polynomial"), which together prove optimality.
          For general f on few variables, an exact LP over multilinear polynomials (methods/lp.py).

Quantum connections (Beals, Buhrman, Cleve, Mosca, de Wolf 2001, Quantum lower bounds by polynomials, J. ACM 48,
doi:10.1145/502090.502097): Q_E(f) >= deg(f)/2 and Q_eps(f) >= adeg_eps(f)/2 (proven theorems).
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache
from itertools import combinations, permutations

from . import exactalg as ea

# --------------------------------------------------------------------------------------------------------------
# Basic constructions
# --------------------------------------------------------------------------------------------------------------


def from_function(n: int, fn) -> tuple[int, ...]:
    return tuple(int(bool(fn(tuple((x >> i) & 1 for i in range(n))))) for x in range(1 << n))


def symmetric(n: int, F) -> tuple[int, ...]:
    """Truth table of the symmetric function with f(x) = F(|x|)."""
    return tuple(int(F(bin(x).count("1"))) for x in range(1 << n))


def OR(n):
    return symmetric(n, lambda k: k > 0)


def AND(n):
    return symmetric(n, lambda k: k == n)


def PARITY(n):
    return symmetric(n, lambda k: k % 2)


def MAJ(n):
    return symmetric(n, lambda k: 2 * k > n)


# --------------------------------------------------------------------------------------------------------------
# Deterministic query complexity, degree, sensitivity measures
# --------------------------------------------------------------------------------------------------------------


def D(tt: tuple, n: int) -> int:
    """Exact deterministic (decision-tree) query complexity by DP over subcubes."""

    @lru_cache(None)
    def rec(fixed_mask: int, fixed_vals: int) -> int:
        free = [i for i in range(n) if not fixed_mask >> i & 1]
        vals = set()
        for sub in range(1 << len(free)):
            x = fixed_vals
            for k, i in enumerate(free):
                if sub >> k & 1:
                    x |= 1 << i
            vals.add(tt[x])
            if len(vals) > 1:
                break
        if len(vals) == 1:
            return 0
        return 1 + min(max(rec(fixed_mask | 1 << i, fixed_vals), rec(fixed_mask | 1 << i, fixed_vals | 1 << i))
                       for i in free)

    return rec(0, 0)


def fourier_moebius(tt: tuple, n: int) -> list[int]:
    """Coefficients a_S of f(x) = sum_S a_S prod_{i in S} x_i (S as a bitmask), exact integers."""
    a = list(tt)
    for i in range(n):
        for S in range(1 << n):
            if S >> i & 1:
                a[S] -= a[S ^ (1 << i)]
    return a


def deg(tt: tuple, n: int) -> int:
    a = fourier_moebius(tt, n)
    return max((bin(S).count("1") for S in range(1 << n) if a[S] != 0), default=0)


def sensitivity(tt: tuple, n: int) -> int:
    return max(sum(tt[x] != tt[x ^ (1 << i)] for i in range(n)) for x in range(1 << n))


def block_sensitivity(tt: tuple, n: int) -> int:
    best = 0
    for x in range(1 << n):
        blocks = [B for B in range(1, 1 << n) if tt[x] != tt[x ^ B]]
        # minimal sensitive blocks suffice for a maximum disjoint family
        minimal = [B for B in blocks if not any(C != B and C & B == C for C in blocks)]

        def pack(i, used):
            if i == len(minimal):
                return 0
            r = pack(i + 1, used)
            if not minimal[i] & used:
                r = max(r, 1 + pack(i + 1, used | minimal[i]))
            return r

        best = max(best, pack(0, 0))
    return best


def certificate_complexity(tt: tuple, n: int) -> int:
    worst = 0
    for x in range(1 << n):
        found = None
        for size in range(n + 1):
            for S in combinations(range(n), size):
                mask = sum(1 << i for i in S)
                if all(tt[y] == tt[x] for y in range(1 << n) if (y ^ x) & mask == 0):
                    found = size
                    break
            if found is not None:
                break
        worst = max(worst, found)
    return worst


# --------------------------------------------------------------------------------------------------------------
# NPN equivalence classes (orbit enumeration)
# --------------------------------------------------------------------------------------------------------------


def npn_classes(n: int) -> list[tuple[int, ...]]:
    """One representative (the first in index order) per NPN class: input negations, input permutations, output
    negation. Orbit enumeration over all 2^(2^n) functions; n <= 4."""
    N = 1 << n
    perms = list(permutations(range(n)))
    maps = []
    for p in perms:
        for neg in range(N):
            maps.append([sum(((x ^ neg) >> i & 1) << p[i] for i in range(n)) for x in range(N)])
    seen = bytearray(1 << N)
    reps = []
    for code in range(1 << N):
        if seen[code]:
            continue
        tt = tuple(code >> x & 1 for x in range(N))
        reps.append(tt)
        for mp in maps:
            for out in (0, 1):
                c2 = 0
                for x in range(N):
                    if tt[x] ^ out:
                        c2 |= 1 << mp[x]
                seen[c2] = 1
    return reps


# --------------------------------------------------------------------------------------------------------------
# Approximate degree: symmetric functions (exact exchange algorithm with certificates)
# --------------------------------------------------------------------------------------------------------------


def _solve(rows, rhs):
    m, piv = ea.rref([list(r) + [b] for r, b in zip(rows, rhs)])
    return [m[i][-1] for i in range(len(rows))]


def best_uniform_error(F: list, d: int, max_iter: int = 500) -> dict:
    """Exact best uniform approximation error E_d = min_{deg q <= d} max_k |F(k) - q(k)| on k = 0..N, N = len(F)-1.

    Stiefel's single-exchange algorithm in exact arithmetic (finite, since |h| strictly increases under the Haar
    condition, which polynomials satisfy on distinct points). Returns the error, the optimal polynomial (lowest
    degree first, in the variable k), the reference set, and a dual certificate phi (weights on the reference
    points, alternating in sign, sum |phi| = 1, sum phi_r k_r^j = 0 for j <= d) with lower bound
    sum phi_r F(k_r) = E_d. Optimality is certified when max error == |h| == dual bound."""
    N = len(F) - 1
    F = [Fraction(v) for v in F]
    if d >= N:
        return {"error": Fraction(0), "poly": None, "certified": True, "reference": None, "dual": None}
    ref = sorted({round(i * N / (d + 1)) for i in range(d + 2)})
    if len(ref) < d + 2:
        ref = list(range(d + 2))
    for _ in range(max_iter):
        rows = [[Fraction(k) ** j for j in range(d + 1)] + [Fraction((-1) ** r)] for r, k in enumerate(ref)]
        sol = _solve(rows, [F[k] for k in ref])
        q, h = sol[:d + 1], sol[d + 1]
        err = [F[k] - ea.peval(q, Fraction(k)) for k in range(N + 1)]
        kmax = max(range(N + 1), key=lambda k: abs(err[k]))
        M = abs(err[kmax])
        if M == abs(h):
            break
        # single exchange keeping sign alternation of err on the reference
        sgn = lambda v: (v > 0) - (v < 0)  # noqa: E731
        s = sgn(err[kmax])
        if kmax < ref[0]:
            ref = [kmax] + ref[1:] if sgn(err[ref[0]]) == s else [kmax] + ref[:-1]
        elif kmax > ref[-1]:
            ref = ref[:-1] + [kmax] if sgn(err[ref[-1]]) == s else ref[1:] + [kmax]
        else:
            i = max(r for r in range(len(ref)) if ref[r] < kmax)
            if sgn(err[ref[i]]) == s:
                ref[i] = kmax
            else:
                ref[i + 1] = kmax
    else:
        raise RuntimeError("exchange algorithm did not converge")
    # dual certificate: nullspace of the (d+1) x (d+2) Vandermonde on the reference
    V = [[Fraction(k) ** j for k in ref] for j in range(d + 1)]
    ns = ea.nullspace(V)
    phi = ns[0]
    tot = sum(abs(v) for v in phi)
    phi = [v / tot for v in phi]
    alternating = all(phi[r] * phi[r + 1] < 0 for r in range(len(phi) - 1))
    lower = abs(sum(p * F[k] for p, k in zip(phi, ref)))
    return {"error": M, "h": abs(h), "poly": q, "reference": ref, "dual": phi, "dual_bound": lower,
            "certified": alternating and lower == M}


def adeg_symmetric(F: list, eps=Fraction(1, 3)) -> tuple[int, list]:
    """Least d with E_d <= eps for the univariate profile F(0..n) (exact), and the list of E_d up to that d."""
    errs = []
    for d in range(len(F)):
        r = best_uniform_error(F, d)
        if not r["certified"]:
            raise RuntimeError(f"uncertified optimum at d = {d}")
        errs.append(r["error"])
        if r["error"] <= eps:
            return d, errs
    return len(F) - 1, errs


# --------------------------------------------------------------------------------------------------------------
# Approximate degree: general small functions (exact LP over multilinear polynomials)
# --------------------------------------------------------------------------------------------------------------


def best_multilinear_error(tt: tuple, n: int, d: int) -> Fraction:
    """min over multilinear p with deg <= d of max_x |f(x) - p(x)| (exact LP, methods/lp.py)."""
    from .lp import solve_lp
    monos = [S for S in range(1 << n) if bin(S).count("1") <= d]
    nv = len(monos) + 1  # coefficients (free) and eps
    A, b = [], []
    for x in range(1 << n):
        row = [1 if S & x == S else 0 for S in monos]
        A.append(row + [-1]); b.append(tt[x])          # p(x) - eps <= f(x)
        A.append([-v for v in row] + [-1]); b.append(-tt[x])  # -p(x) - eps <= -f(x)
    c = [0] * len(monos) + [-1]  # maximise -eps
    res = solve_lp(c, A, b, free=range(len(monos)))
    return -res["value"]


def adeg_general(tt: tuple, n: int, eps=Fraction(1, 3)) -> int:
    for d in range(n + 1):
        if best_multilinear_error(tt, n, d) <= eps:
            return d
    return n
