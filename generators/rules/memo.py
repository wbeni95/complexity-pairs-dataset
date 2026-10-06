"""Rule R1: memoisation of overlapping subproblems (and R1c: memoisation with a compressed key).

Family generator: random recurrences from a small grammar.
  memo1d      f(n) = combine over moves of f(child(n)) and an instance-dependent weight; moves are
              subtractive (s1..s4: n - d) and/or divisive (h: n // 2, t: n // 3), with repetition allowed.
  memo2d      f(i, j) on two random strings s, t of length n; moves are vectors (a, b) from
              {(1,0),(0,1),(1,1),(2,0),(0,2),(2,1),(1,2)}; weights depend on s[i-1] == t[j-1].
  compress1d  a 1-D recurrence with a hidden flag p (moves may flip it; weights scale by 1 + delta*p);
              the rule memoises on n alone, dropping p (state compression, the shortest-path trick of
              research/2026-10-07_patterns.md section 1.2).

Slow: naive recursion, counted per call. Fast: memoisation (iterative, explicit stack), counted per state
evaluation. Both counts are "executions of the recurrence body", so they share a unit.

Cost claims from the specification (never from the fit):
  subtractive moves S (multiset, |S| >= 2): naive calls Theta(lambda^n), lambda the largest real root of
      x^D = sum_{d in S} x^(D-d) (as in generators/linear_recurrence.py); memo Theta(n) states.
  divisive moves only: naive calls Theta(n^p), sum_b b^(-p) = 1 (Akra-Bazzi); memo Theta(log n) states if all
      bases are equal, Theta(log^2 n) for bases 2 and 3.
  2-D, (1,1) strictly inside the cone of the moves: naive calls Theta(lambda^n / sqrt(n)) or Theta(lambda^n),
      lambda = the largest directional growth rate over endpoint directions (growth_2d; CORRECTED in this
      round: the first version used only the diagonal coefficient, min 1/(x y) on sum x^a y^b = 1, which is a
      lower bound and was up to 5.3% too small); memo Theta(n^2).
  2-D otherwise (all moves weakly on one side of the diagonal): the binding coordinate's 1-D root.
  exactly one subtractive move plus divisive moves: super-polynomial, sub-exponential; no closed form is
      claimed (EXACT is recorded without a fit).
  one move only: no overlap, no cost change -> INVALID (degenerate).
"""
from __future__ import annotations

import math
import random
from functools import lru_cache

from .common import Candidate, short_hash

RULE = "memo"
P = 1_000_003
SUB = {"s1": 1, "s2": 2, "s3": 3, "s4": 4}
DIV = {"h": 2, "t": 3}
MOVES2D = [(1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2)]
DATA_LEN = 17

CATALOGUE = {
    "name": "memoisation of overlapping subproblems",
    "precondition": "a recursive definition whose call tree is exponentially (or polynomially) larger than its set of "
                    "distinct arguments, i.e. subproblems overlap; the function is pure (result depends only on the key)",
    "transformation": "cache results by argument (top-down) or evaluate the distinct states in topological order",
    "cost_change": "calls: |call tree| -> |distinct states| x fan-in; e.g. Theta(lambda^n) -> Theta(n), "
                   "Theta(lambda^n/sqrt n) -> Theta(n^2), Theta(n^p) -> Theta(log^2 n)",
    "failure_mode": "no overlap (one child per call): no gain; key too small (state compression that drops a "
                    "coordinate the result depends on): wrong answers",
    "variant": "R1c compress: memoise on a projection of the state; exact iff the result does not depend on the "
               "dropped coordinate",
    "literature": "Bellman 1957, Dynamic Programming [book]; dataset entries fibonacci, edit-distance, matrix-chain",
}


# ----------------------------------------------------------------------------------------------
# Spec-derived growth constants
# ----------------------------------------------------------------------------------------------

def root_1d(offsets) -> float:
    """Largest real root of x^D = sum_{d in offsets} x^(D-d) (offsets with multiplicity); needs |offsets| >= 2."""
    D = max(offsets)
    f = lambda x: x ** D - sum(x ** (D - d) for d in offsets)  # noqa: E731
    lo, hi = 1.0, float(len(offsets)) + 1.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if f(mid) < 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def akra_bazzi(bases) -> float:
    """p with sum_b b^(-p) = 1."""
    g = lambda p: sum(b ** (-p) for b in bases) - 1  # noqa: E731
    lo, hi = -5.0, 10.0
    for _ in range(200):
        mid = (lo + hi) / 2
        if g(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def acsv_lambda(moves) -> float:
    """min 1/(x y) on sum x^a y^b = 1, x, y > 0, via u = log x, v = log y: maximise u + v on a convex set."""
    def G(u, v):
        return sum(math.exp(a * u + b * v) for a, b in moves)

    def v_of(u):
        if G(u, -80.0) >= 1:
            return None
        lo, hi = -80.0, 80.0
        for _ in range(120):
            mid = (lo + hi) / 2
            if G(u, mid) < 1:
                lo = mid
            else:
                hi = mid
        return lo

    def obj(u):
        v = v_of(u)
        return -math.inf if v is None else u + v

    lo, hi = -40.0, 40.0
    for _ in range(200):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if obj(m1) < obj(m2):
            lo = m1
        else:
            hi = m2
    return math.exp(-obj((lo + hi) / 2))


def _dir_rate(moves, r, s):
    """Exponential growth of the walk counts towards endpoint direction (r, s): exp(-max(r u + s v)) over
    sum exp(a u + b v) <= 1 (u = log x, v = log y)."""
    def G(u, v):
        return sum(math.exp(a * u + b * v) for a, b in moves)

    def v_of(u):
        if G(u, -80.0) >= 1:
            return None
        lo, hi = -80.0, 80.0
        for _ in range(60):
            mid = (lo + hi) / 2
            if G(u, mid) < 1:
                lo = mid
            else:
                hi = mid
        return lo

    def obj(u):
        v = v_of(u)
        return -math.inf if v is None else r * u + s * v

    lo, hi = -40.0, 40.0
    for _ in range(70):
        m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
        if obj(m1) < obj(m2):
            lo = m1
        else:
            hi = m2
    return math.exp(-obj((lo + hi) / 2))


@lru_cache(maxsize=None)
def _growth_2d_cached(moves_key):
    return _growth_2d(list(moves_key))


def growth_2d(moves):
    """Cached per move set (the numeric search costs about a second)."""
    return _growth_2d_cached(tuple(sorted(tuple(m) for m in moves)))


def _growth_2d(moves):
    """Growth rate of the naive call count C(n, n) of a 2-D recurrence (CORRECTED in this round): C counts walks
    to ALL endpoints, so the rate is the maximum of the directional rates over endpoint directions (r, 1) and
    (1, r), r in [0, 1] (each a convex minimisation in r, solved by ternary search). Returns (lambda, r_star,
    at_corner); at_corner means the maximum sits at the diagonal direction r = 1, where the endpoint sum is
    geometric and the 1/sqrt(n) factor of the diagonal coefficient survives; otherwise the sum is Gaussian
    around r_star and no polynomial factor is claimed. The method is [recalled] (analytic combinatorics in
    several variables) and is checked against the exact counting DP (experiment H-R1)."""
    best = None
    for orient in (0, 1):
        f = (lambda r: _dir_rate(moves, r, 1.0)) if orient == 0 else (lambda r: _dir_rate(moves, 1.0, r))
        lo, hi = 0.0, 1.0
        for _ in range(36):
            m1, m2 = lo + (hi - lo) / 3, hi - (hi - lo) / 3
            if f(m1) > f(m2):
                hi = m2
            else:
                lo = m1
        r = (lo + hi) / 2
        for cand in (r, 1.0, 0.0):
            val = f(cand)
            if best is None or val > best[0] * (1 + 1e-9):
                best = (val, cand, orient)
    lam, r, _ = best
    return lam, r, r > 1 - 1e-4


# ----------------------------------------------------------------------------------------------
# Generation
# ----------------------------------------------------------------------------------------------

def _gen_1d(rng, kind):
    if kind == "sub":
        k = rng.choice([1, 2, 2, 3, 3])
        moves = [rng.choice(list(SUB)) for _ in range(k)]
    elif kind == "div":
        k = rng.choice([1, 2, 2, 3])
        moves = [rng.choice(list(DIV)) for _ in range(k)]
    else:
        moves = [rng.choice(list(SUB)) for _ in range(rng.choice([1, 2]))] + \
                [rng.choice(list(DIV)) for _ in range(rng.choice([1, 2]))]
    combine = rng.choice(["sum", "min", "max"])
    coef = [rng.randint(1, 9) for _ in moves]
    return {"family": "memo1d", "kind": kind, "moves": moves, "combine": combine, "coef": coef}


def _gen_2d(rng):
    k = rng.choice([1, 2, 2, 3, 3, 4])
    moves = [list(m) for m in rng.sample(MOVES2D, k)]
    combine = rng.choice(["sum", "min", "max"])
    coef = [rng.randint(0, 9) for _ in moves]
    return {"family": "memo2d", "moves": moves, "combine": combine, "coef": coef}


def _gen_compress(rng):
    k = rng.choice([2, 2, 3])
    moves = [rng.choice(list(SUB)) for _ in range(k)]
    flips = [rng.choice([0, 0, 1]) for _ in moves]
    delta = rng.choice([0, 0, 1, 2])
    combine = rng.choice(["sum", "min", "max"])
    coef = [rng.randint(1, 9) for _ in moves]
    return {"family": "compress1d", "moves": moves, "flips": flips, "delta": delta, "combine": combine, "coef": coef}


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|memo|{seed}")
    out = []
    for i in range(count):
        r = rng.random()
        if r < 0.30:
            s = _gen_1d(rng, "sub")
        elif r < 0.42:
            s = _gen_1d(rng, "div")
        elif r < 0.50:
            s = _gen_1d(rng, "mixed")
        elif r < 0.75:
            s = _gen_2d(rng)
        else:
            s = _gen_compress(rng)
        out.append(s)
    return out


def build(spec: dict) -> Candidate:
    return {"memo1d": Memo1D, "memo2d": Memo2D, "compress1d": Compress1D}[spec["family"]](spec)


# ----------------------------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------------------------

def _combine(kind, vals):
    if kind == "sum":
        return sum(vals) % P
    if kind == "min":
        return min(vals)
    return max(vals)


def _choose_ns(count_fn, lo=300, hi=300_000, k=6, step=1, start=1, limit=10**15, geometric=False):
    """n values whose spec-derived count lies in [lo, hi]."""
    ns = []
    n = start
    while n <= limit:
        c = count_fn(n)
        if c > hi:
            break
        if c >= lo:
            ns.append(n)
        n = n * 2 if geometric else n + step
    if len(ns) > k:
        idx = [round(i * (len(ns) - 1) / (k - 1)) for i in range(k)]
        ns = [ns[i] for i in sorted(set(idx))]
    return ns


class Memo1D(Candidate):
    rule = RULE
    trials = 6

    def __init__(self, spec):
        super().__init__(spec)
        self.sub = [SUB[m] for m in spec["moves"] if m in SUB]
        self.div = [DIV[m] for m in spec["moves"] if m in DIV]
        self.children = [(("s", SUB[m]) if m in SUB else ("d", DIV[m])) for m in spec["moves"]]
        self.base = max(self.sub + [2 if self.div else 1])
        self.L = 1
        for d in self.sub:
            self.L = self.L * d // math.gcd(self.L, d)
        sizes = [n for n in range(self.base, 400) if self.spec_count(n) <= 20000]
        if self.div and not self.sub:
            sizes = [n for n in (7, 31, 200, 1000, 5000) if self.spec_count(n) <= 20000]
        self.screen_sizes = tuple(sizes[-3:]) if sizes else (self.base,)

    def _kids(self, m):
        return [m - v if t == "s" else m // v for t, v in self.children]

    @lru_cache(maxsize=None)
    def spec_count(self, n):
        """Exact naive call count from the recurrence C(n) = 1 + sum C(child) (spec-derived)."""
        if n < self.base:
            return 1
        return 1 + sum(self.spec_count(c) for c in self._kids(n))

    def __hash__(self):
        return hash(self.id)

    def instance(self, rng, n):
        return (n, tuple(rng.randint(0, 9) for _ in range(DATA_LEN)))

    def _w(self, data, m, i):
        return (self.spec["coef"][i] * data[m % DATA_LEN] + i) % 10

    def slow(self, inst, ops):
        n, data = inst
        comb, coef, base = self.spec["combine"], self.spec["coef"], self.base

        def f(m):
            ops.n += 1
            if m < base:
                return data[m % DATA_LEN]
            kids = self._kids(m)
            if comb == "sum":
                return (data[m % DATA_LEN] + sum(coef[i] * f(c) for i, c in enumerate(kids))) % P
            return _combine(comb, [f(c) + self._w(data, m, i) for i, c in enumerate(kids)])
        return f(n)

    def fast(self, inst, ops):
        n, data = inst
        comb, coef, base = self.spec["combine"], self.spec["coef"], self.base
        memo = {}
        stack = [n]
        while stack:
            m = stack[-1]
            if m in memo:
                stack.pop()
                continue
            if m < base:
                ops.n += 1
                memo[m] = data[m % DATA_LEN]
                stack.pop()
                continue
            kids = self._kids(m)
            missing = [c for c in kids if c not in memo]
            if missing:
                stack.extend(missing)
                continue
            ops.n += 1
            if comb == "sum":
                memo[m] = (data[m % DATA_LEN] + sum(coef[i] * memo[c] for i, c in enumerate(kids))) % P
            else:
                memo[m] = _combine(comb, [memo[c] + self._w(data, m, i) for i, c in enumerate(kids)])
            stack.pop()
        return memo[n]

    def precondition(self):
        """Overlap: the naive call tree outgrows the distinct states (checked on the spec counts)."""
        n = self.screen_sizes[-1]
        return self.spec_count(n) > self._states(n)

    def _states(self, n):
        seen, stack = set(), [n]
        while stack:
            m = stack.pop()
            if m in seen:
                continue
            seen.add(m)
            if m >= self.base:
                stack.extend(self._kids(m))
        return len(seen)

    def predicates(self):
        n = self.screen_sizes[-1]
        return {"tree_over_states": round(self.spec_count(n) / self._states(n), 3), "n": n}

    def degenerate(self):
        if len(self.spec["moves"]) == 1:
            return "one move: no overlapping subproblems, memoisation cannot change the cost"
        return None

    def claims(self):
        if len(self.sub) >= 2:
            lam = root_1d(self.sub)
            return f"{lam:.10f}**n", "n", lam
        if not self.sub and len(self.div) >= 2:
            p = akra_bazzi(self.div)
            fast = "log(n)" if len(set(self.div)) == 1 else "log(n)**2"
            return f"n**{p:.10f}", fast, p
        return None, None, None

    def scaling(self):
        slow_c, fast_c, _ = self.claims()
        if slow_c is None:
            return None
        if self.div and not self.sub:
            s_ns = _choose_ns(self.spec_count, start=16, geometric=True)
            f_ns = [10 ** k for k in (3, 5, 7, 9, 11, 13, 15)]
            s_riv = ["n", "log(n)**2", "sqrt(n)"]
            f_riv = ["log(n)", "n**0.25"] if fast_c == "log(n)**2" else ["log(n)**2", "n**0.25"]
        else:
            g = 0
            for d in self.sub:
                g = math.gcd(g, d)
            s_ns = _choose_ns(self.spec_count, start=self.base + 2 * self.L, step=g)
            f_ns = [1000 * self.L * 2 ** k for k in range(5)]
            s_riv = ["n**3", "n*2**n"] if root_1d(self.sub) < 1.9 else ["n**3", "1.5**n", "3**n"]
            f_riv = ["n**2", "n*log(n)", "log(n)**2"]
        if len(s_ns) < 3:
            return None
        return {"slow": {"n_values": s_ns, "cost": slow_c, "rivals": s_riv},
                "fast": {"n_values": f_ns, "cost": fast_c, "rivals": f_riv}, "tolerance": 0.05}

    def expected_counts(self, side, ns):
        return [self.spec_count(n) for n in ns] if side == "slow" else None

    def scaling_key(self):
        return "memo1d|" + short_hash([sorted(self.spec["moves"])])

    def canonical(self):
        s = self.spec
        return short_hash(["memo1d", s["combine"], sorted(zip(s["moves"], s["coef"]))])

    def cluster(self):
        return f"memo1d:{self.spec['kind']}:" + "+".join(sorted(self.spec["moves"]))


class Memo2D(Candidate):
    rule = RULE
    trials = 6

    def __init__(self, spec):
        super().__init__(spec)
        self.moves = [tuple(m) for m in spec["moves"]]
        self.maxA = max(a for a, _ in self.moves)
        self.maxB = max(b for _, b in self.moves)
        self._cnt = {}
        sizes = [n for n in range(1, 60) if self.spec_count(n) <= 20000]
        self.screen_sizes = tuple(sizes[-3:]) if sizes else (2,)

    def __hash__(self):
        return hash(self.id)

    def _is_base(self, i, j):
        return i < self.maxA or j < self.maxB

    def _count(self, i, j):
        key = (i, j)
        if key in self._cnt:
            return self._cnt[key]
        if self._is_base(i, j):
            v = 1
        else:
            v = 1 + sum(self._count(i - a, j - b) for a, b in self.moves)
        self._cnt[key] = v
        return v

    def spec_count(self, n):
        # fill bottom-up to keep recursion shallow
        for i in range(n + 1):
            for j in range(n + 1):
                self._count(i, j)
        return self._cnt[(n, n)]

    def instance(self, rng, n):
        return (n, tuple(rng.randint(0, 2) for _ in range(n)), tuple(rng.randint(0, 2) for _ in range(n)))

    def _w(self, s, t, i, j, k):
        c = self.spec["coef"][k]
        return c if s[i - 1] == t[j - 1] else (c + 3) % 10

    @staticmethod
    def _base_val(i, j):
        return (3 * i + 5 * j) % 7

    def slow(self, inst, ops):
        n, s, t = inst
        comb, coef, moves = self.spec["combine"], self.spec["coef"], self.moves

        def f(i, j):
            ops.n += 1
            if self._is_base(i, j):
                return self._base_val(i, j)
            if comb == "sum":
                return (self._w(s, t, i, j, 0) + sum(coef[k] * f(i - a, j - b) for k, (a, b) in enumerate(moves))) % P
            return _combine(comb, [f(i - a, j - b) + self._w(s, t, i, j, k) for k, (a, b) in enumerate(moves)])
        return f(n, n)

    def fast(self, inst, ops):
        n, s, t = inst
        comb, coef, moves = self.spec["combine"], self.spec["coef"], self.moves
        memo = {}
        stack = [(n, n)]
        while stack:
            st = stack[-1]
            if st in memo:
                stack.pop()
                continue
            i, j = st
            if self._is_base(i, j):
                ops.n += 1
                memo[st] = self._base_val(i, j)
                stack.pop()
                continue
            kids = [(i - a, j - b) for a, b in moves]
            missing = [c for c in kids if c not in memo]
            if missing:
                stack.extend(missing)
                continue
            ops.n += 1
            if comb == "sum":
                memo[st] = (self._w(s, t, i, j, 0) + sum(coef[k] * memo[c] for k, c in enumerate(kids))) % P
            else:
                memo[st] = _combine(comb, [memo[c] + self._w(s, t, i, j, k) for k, c in enumerate(kids)])
            stack.pop()
        return memo[(n, n)]

    def geometry(self):
        if all(b == 0 for _, b in self.moves):
            return "1d_i", [a for a, _ in self.moves]
        if all(a == 0 for a, _ in self.moves):
            return "1d_j", [b for _, b in self.moves]
        if all(a == b for a, b in self.moves):
            return "1d_diag", [a for a, _ in self.moves]
        if any(a > b for a, b in self.moves) and any(a < b for a, b in self.moves):
            return "interior", None
        if all(a >= b for a, b in self.moves):
            return "boundary_i", [a for a, _ in self.moves]
        return "boundary_j", [b for _, b in self.moves]

    def degenerate(self):
        if len(self.moves) == 1:
            return "one move: no overlapping subproblems"
        return None

    def precondition(self):
        n = self.screen_sizes[-1]
        return self.spec_count(n) > len(self._states(n))

    def _states(self, n):
        seen, stack = set(), [(n, n)]
        while stack:
            st = stack.pop()
            if st in seen:
                continue
            seen.add(st)
            if not self._is_base(*st):
                stack.extend((st[0] - a, st[1] - b) for a, b in self.moves)
        return seen

    def predicates(self):
        geo, _ = self.geometry()
        n = self.screen_sizes[-1]
        out = {"geometry": geo, "tree_over_states": round(self.spec_count(n) / len(self._states(n)), 3), "n": n}
        if geo == "interior":
            out["lambda_acsv_diagonal_only"] = round(acsv_lambda(self.moves), 6)
            lam, rstar, corner = growth_2d(self.moves)
            out.update(lambda_corrected=round(lam, 6), r_star=round(rstar, 4), at_corner=corner)
            a, b = 120, 240
            out["lambda_dp_ratio"] = round((self.spec_count(b) / self.spec_count(a)) ** (1 / (b - a)), 6)
            out["alpha_claim_n100_200"] = self.large_n_check()
        return out

    def claims(self):
        geo, offs = self.geometry()
        if geo == "interior":
            lam, _, corner = growth_2d(self.moves)
            return (f"{lam:.10f}**n/sqrt(n)" if corner else f"{lam:.10f}**n"), "n**2", geo
        if len(offs) >= 2:
            lam = root_1d(offs)
            return f"{lam:.10f}**n", ("n" if geo.startswith("1d") else "n**2"), geo
        return None, None, geo

    def scaling(self):
        slow_c, fast_c, geo = self.claims()
        if slow_c is None:
            return None
        s_ns = _choose_ns(self.spec_count, start=self.maxA + self.maxB + 1, hi=200_000)
        if len(s_ns) < 3:
            return None
        f_ns = [16, 32, 64, 128]
        return {"slow": {"n_values": s_ns, "cost": slow_c, "rivals": ["n**3", "n**4"]},
                "fast": {"n_values": f_ns, "cost": fast_c,
                         "rivals": ["n**3", "n*log(n)"] if fast_c == "n**2" else ["n**2", "log(n)"]},
                "tolerance": 0.05}

    def expected_counts(self, side, ns):
        return [self.spec_count(n) for n in ns] if side == "slow" else None

    def large_n_check(self):
        """Fit of the spec-derived exact counts at n = 100..200 against the claim (separates a wrong lambda
        from a pre-asymptotic small-n fit)."""
        from .common import fit_claim
        slow_c, _, _ = self.claims()
        if slow_c is None:
            return None
        ns = list(range(100, 201, 20))
        return fit_claim(ns, [self.spec_count(n) for n in ns], slow_c, (), 0.05)["alpha"]

    def scaling_key(self):
        return "memo2d|" + short_hash([sorted(self.spec["moves"])])

    def canonical(self):
        s = self.spec
        a = sorted([list(m), c] for m, c in zip(s["moves"], s["coef"]))
        b = sorted([[m[1], m[0]], c] for m, c in zip(s["moves"], s["coef"]))
        return short_hash(["memo2d", s["combine"], min(a, b)])

    def cluster(self):
        mv = sorted(tuple(m) for m in self.moves)
        tr = sorted((b, a) for a, b in self.moves)
        return "memo2d:" + str(min(mv, tr)).replace(" ", "")


class Compress1D(Memo1D):
    """Hidden flag p; the rule memoises on n only."""

    def __init__(self, spec):
        super().__init__(spec)
        self.flips = spec["flips"]
        self.delta = spec["delta"]

    def slow(self, inst, ops):
        n, data = inst
        comb, coef, base, dl = self.spec["combine"], self.spec["coef"], self.base, self.delta

        def f(m, p):
            ops.n += 1
            if m < base:
                return data[m % DATA_LEN] + dl * p
            kids = self._kids(m)
            if comb == "sum":
                return (data[m % DATA_LEN] * (1 + dl * p)
                        + sum(coef[i] * f(c, p ^ self.flips[i]) for i, c in enumerate(kids))) % P
            return _combine(comb, [f(c, p ^ self.flips[i]) + self._w(data, m, i) * (1 + dl * p)
                                   for i, c in enumerate(kids)])
        return f(n, 0)

    def fast(self, inst, ops):
        n, data = inst
        comb, coef, base, dl = self.spec["combine"], self.spec["coef"], self.base, self.delta
        memo = {}
        stack = [(n, 0)]
        while stack:
            m, p = stack[-1]
            if m in memo:
                stack.pop()
                continue
            if m < base:
                ops.n += 1
                memo[m] = data[m % DATA_LEN] + dl * p
                stack.pop()
                continue
            kids = self._kids(m)
            missing = [(c, p ^ self.flips[i]) for i, c in enumerate(kids) if c not in memo]
            if missing:
                stack.extend(missing)
                continue
            ops.n += 1
            if comb == "sum":
                memo[m] = (data[m % DATA_LEN] * (1 + dl * p) + sum(coef[i] * memo[c] for i, c in enumerate(kids))) % P
            else:
                memo[m] = _combine(comb, [memo[c] + self._w(data, m, i) * (1 + dl * p) for i, c in enumerate(kids)])
            stack.pop()
        return memo[n]

    def precondition(self):
        """Stated precondition of state compression: the dropped flag cannot influence the value."""
        return self.delta == 0 or not any(self.flips)

    def p_functional(self, n=None):
        """Refined precondition found in this round: on the states reachable from (n, 0), the dropped flag p is a
        function of the kept coordinate m (then the compressed key loses nothing, whatever delta is)."""
        n = self.screen_sizes[-1] if n is None else n
        seen, stack, pm = set(), [(n, 0)], {}
        while stack:
            m, q = stack.pop()
            if (m, q) in seen:
                continue
            seen.add((m, q))
            pm.setdefault(m, set()).add(q)
            if m >= self.base:
                stack.extend((c, q ^ self.flips[i]) for i, c in enumerate(self._kids(m)))
        return all(len(v) == 1 for v in pm.values())

    def predicates(self):
        d = super().predicates()
        d.update(delta=self.delta, any_flip=any(self.flips), p_functional=self.p_functional())
        return d

    def scaling_key(self):
        return "compress1d|" + short_hash([sorted(self.spec["moves"])])

    def canonical(self):
        s = self.spec
        return short_hash(["compress1d", s["combine"], s["delta"], sorted(zip(s["moves"], s["flips"], s["coef"]))])

    def cluster(self):
        pre = "pre" if self.precondition() else "nopre"
        return f"compress1d:{pre}:" + "+".join(sorted(self.spec["moves"]))
