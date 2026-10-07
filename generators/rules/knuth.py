"""Rule R5: monotonicity pruning -- Knuth's optimisation of interval DP (Knuth 1971; Yao 1980).

Problem (one per random family of interval weights w): for 0 <= i < j <= n,
    c(i, i) = 0,   c(i, j) = w(i, j) + min_{i < k <= j} ( c(i, k-1) + c(k, j) ),   answer c(0, n).
Slow: the cubic DP (every split k). Fast (rule): Knuth's restriction K(i, j-1) <= k <= K(i+1, j), with K the
largest optimal split. Counted: split evaluations (one addition + one comparison each).

Stated precondition (Yao 1980) [recalled]: w satisfies the quadrangle inequality (QI)
    w(a, c) + w(b, d) <= w(a, d) + w(b, c)   for a <= b <= c <= d
and is monotone on the lattice of intervals: w(b, c) <= w(a, d) whenever [b, c] is inside [a, d].
Recorded per instance: QI violations, monotonicity violations, and whether the largest optimal roots of the
cubic DP are monotone (root_monotone; this is sufficient, not necessary, for the restricted search to see the
optimum: research/2026-10-06d_rule_mining.md section 5.3 records exact runs without it).

Families (n = number of keys):
  bst            prefix sums of random positive frequencies (QI with equality, monotone)
  subint         sum over sub-intervals of a sparse non-negative matrix (QI and monotone)
  convex_len     h(j - i) with h convex non-decreasing (QI and monotone)
  concave_len    h(j - i) with h concave increasing (QI usually fails)
  subint_lin     subint - lambda (j - i): QI holds (linear terms are QI-neutral), monotonicity fails for large lambda
  subint_sep     subint + g(i) - g(j) with arbitrary g: QI holds, monotonicity may fail (held-out family)
  random_len     h(j - i) with arbitrary random h >= 0 (held-out family for the translation-invariance hypothesis)
  random         iid random w (neither)
  monotone_rand  random but monotone under inclusion (QI usually fails)
  perturbed      subint with t random entries increased by A (near-misses)
"""
from __future__ import annotations

import random

from .common import Candidate, short_hash

RULE = "knuth"

CATALOGUE = {
    "name": "monotone split points (Knuth-Yao quadrangle-inequality speed-up)",
    "precondition": "w satisfies the quadrangle inequality and is monotone on the interval lattice (Yao 1980); then the "
                    "largest optimal split points are monotone: K(i, j-1) <= K(i, j) <= K(i+1, j)",
    "transformation": "search split k only in [K(i, j-1), K(i+1, j)] instead of (i, j]",
    "cost_change": "Theta(n^3) -> Theta(n^2) split evaluations (telescoping sum)",
    "failure_mode": "split points not monotone: the restricted range can miss the optimum, giving a too-large cost",
    "literature": "Knuth 1971 Acta Informatica (doi:10.1007/BF00264289) [recalled]; Yao 1980 STOC "
                  "(doi:10.1145/800141.804691) [recalled]; dataset entry optimal-bst-recursion-vs-dp-vs-knuth",
}

FAMILIES = ["bst", "subint", "convex_len", "concave_len", "subint_lin", "random", "monotone_rand", "perturbed"]
HELD_OUT = ["subint_sep", "random_len"]


def make_w(spec, rng, n):
    fam = spec["family"]
    N = n + 1
    w = [[0] * N for _ in range(N)]
    if fam == "bst":
        f = [rng.randint(1, spec["fmax"]) for _ in range(n)]
        pre = [0]
        for x in f:
            pre.append(pre[-1] + x)
        for i in range(N):
            for j in range(i + 1, N):
                w[i][j] = pre[j] - pre[i]
        return w
    if fam in ("subint", "subint_lin", "subint_sep", "perturbed"):
        m = [[(rng.randint(1, spec["mmax"]) if rng.random() < spec["density"] else 0) for _ in range(N)]
             for _ in range(N)]
        # w(i, j) = sum of m(x, y) over i <= x <= y <= j, via 2-D prefix sums over the triangle
        for i in range(N - 1, -1, -1):
            for j in range(i + 1, N):
                w[i][j] = m[i][j] + (w[i + 1][j] if i + 1 <= j else 0) + (w[i][j - 1] if i <= j - 1 else 0) - \
                    (w[i + 1][j - 1] if i + 1 <= j - 1 else 0)
        if fam == "subint_lin":
            lam = spec["lam"]
            for i in range(N):
                for j in range(i + 1, N):
                    w[i][j] -= lam * (j - i)
        if fam == "subint_sep":
            # g(i) - g(j) vanishes on the diagonal and cancels in every QI quadruple (QI-neutral, incl. b = c)
            g = [rng.randint(-spec["sep"], spec["sep"]) for _ in range(N)]
            for i in range(N):
                for j in range(i + 1, N):
                    w[i][j] += g[i] - g[j]
        if fam == "perturbed":
            cells = [(i, j) for i in range(N) for j in range(i + 1, N)]
            for i, j in rng.sample(cells, min(spec["t"], len(cells))):
                w[i][j] += spec["A"]
        return w
    if fam == "convex_len":
        a, b = spec["a"], spec["b"]
        for i in range(N):
            for j in range(i + 1, N):
                d = j - i
                w[i][j] = a * d * d + b * d
        return w
    if fam == "concave_len":
        a = spec["a"]
        for i in range(N):
            for j in range(i + 1, N):
                w[i][j] = int(a * (j - i) ** 0.5 * 10)
        return w
    if fam == "random_len":  # translation-invariant, arbitrary h (held-out family for hypothesis H-K2)
        h = [0] + [rng.randint(0, spec["wmax"]) for _ in range(n)]
        for i in range(N):
            for j in range(i + 1, N):
                w[i][j] = h[j - i]
        return w
    if fam == "random":
        for i in range(N):
            for j in range(i + 1, N):
                w[i][j] = rng.randint(0, spec["wmax"])
        return w
    if fam == "monotone_rand":
        for d in range(1, N):
            for i in range(0, N - d):
                j = i + d
                inner = max(w[i + 1][j] if d > 1 else 0, w[i][j - 1] if d > 1 else 0)
                w[i][j] = inner + rng.randint(0, spec["wmax"])
        return w
    raise ValueError(fam)


def make_spec(fam, rng):
    s = {"family": fam}
    if fam == "bst":
        s["fmax"] = rng.choice([3, 10, 100])
    elif fam in ("subint", "subint_lin", "subint_sep", "perturbed"):
        s.update(mmax=rng.choice([3, 10]), density=rng.choice([0.1, 0.3, 0.6]))
        if fam == "subint_lin":
            s["lam"] = rng.choice([1, 3, 10, 30])
        if fam == "subint_sep":
            s["sep"] = rng.choice([1, 5, 20])
        if fam == "perturbed":
            s.update(t=rng.choice([1, 2, 4]), A=rng.choice([1, 5, 20]))
    elif fam == "convex_len":
        s.update(a=rng.randint(0, 3), b=rng.randint(1, 5))
    elif fam == "concave_len":
        s["a"] = rng.randint(1, 5)
    elif fam in ("random", "monotone_rand", "random_len"):
        s["wmax"] = rng.choice([5, 20, 100])
    s["seed"] = rng.randrange(10 ** 9)
    return s


def generate(seed: int, count: int, families=None) -> list[dict]:
    rng = random.Random(f"rules|knuth|{seed}")
    fams = families or FAMILIES
    return [make_spec(rng.choice(fams), rng) for _ in range(count)]


def build(spec: dict) -> Candidate:
    return KnuthCandidate(spec)


def cubic(w, n, ops):
    N = n + 1
    c = [[0] * N for _ in range(N)]
    K = [[i if i == j else 0 for j in range(N)] for i in range(N)]
    for d in range(1, N):
        for i in range(0, N - d):
            j = i + d
            best, arg = None, None
            for k in range(i + 1, j + 1):
                v = c[i][k - 1] + c[k][j]
                if best is None or v <= best:
                    best, arg = v, k
            ops.n += d
            c[i][j] = w[i][j] + best
            K[i][j] = arg
    return c, K


def knuth(w, n, ops):
    N = n + 1
    c = [[0] * N for _ in range(N)]
    K = [[i if i == j else 0 for j in range(N)] for i in range(N)]
    for d in range(1, N):
        for i in range(0, N - d):
            j = i + d
            lo = max(K[i][j - 1], i + 1)
            hi = min(K[i + 1][j], j)
            if lo > hi:
                lo, hi = i + 1, j  # defensive; never triggered when roots are monotone
            best, arg = None, None
            for k in range(lo, hi + 1):
                v = c[i][k - 1] + c[k][j]
                if best is None or v <= best:
                    best, arg = v, k
            ops.n += hi - lo + 1
            c[i][j] = w[i][j] + best
            K[i][j] = arg
    return c, K


def violations(w, n):
    N = n + 1
    qi = mono = 0
    for a in range(N):
        for b in range(a, N):
            for c_ in range(b, N):
                for d in range(c_, N):
                    if a < c_ and b < d and a < d:
                        if w[a][c_] + w[b][d] > w[a][d] + w[b][c_]:
                            qi += 1
                    if (a, d) != (b, c_) and b < c_ and w[b][c_] > w[a][d]:
                        mono += 1
    return qi, mono


def root_monotone(K, n):
    N = n + 1
    for d in range(2, N):
        for i in range(0, N - d):
            j = i + d
            if not (K[i][j - 1] <= K[i][j] <= K[i + 1][j]):
                return False
    return True


class KnuthCandidate(Candidate):
    rule = RULE
    trials = 10
    screen_sizes = (6, 8, 10)

    def instance(self, rng, n):
        return (n, make_w(self.spec, rng, n))

    def slow(self, inst, ops):
        n, w = inst
        return cubic(w, n, ops)[0][0][n]

    def fast(self, inst, ops):
        n, w = inst
        return knuth(w, n, ops)[0][0][n]

    def score(self, inst, a, b):
        if a == b:
            return True, 1.0
        return False, max(0.0, 1 - abs(b - a) / max(abs(a), 1))

    def instance_profile(self, rng, n):
        """Per-instance structural data for the hypothesis tests."""
        n_, w = self.instance(rng, n)
        qi, mono = violations(w, n)
        from .common import Ops
        c, K = cubic(w, n, Ops())
        ck, _ = knuth(w, n, Ops())
        return {"qi_viol": qi, "mono_viol": mono, "root_monotone": root_monotone(K, n), "exact": c[0][n] == ck[0][n]}

    def precondition(self):
        """Yao's conditions on every screened instance (they depend on the random draw for most families)."""
        ok = True
        for n in self.screen_sizes:
            for t in range(self.trials):
                rng = random.Random(f"{self.id}|screen|0|{n}|{t}")
                qi, mono = violations(self.instance(rng, n)[1], n)
                ok = ok and qi == 0 and mono == 0
        return ok

    def predicates(self):
        tot = {"qi_ok": 0, "mono_ok": 0, "root_monotone": 0, "instances": 0}
        from .common import Ops
        for n in self.screen_sizes:
            for t in range(self.trials):
                rng = random.Random(f"{self.id}|screen|0|{n}|{t}")
                _, w = self.instance(rng, n)
                qi, mono = violations(w, n)
                _, K = cubic(w, n, Ops())
                tot["qi_ok"] += qi == 0
                tot["mono_ok"] += mono == 0
                tot["root_monotone"] += root_monotone(K, n)
                tot["instances"] += 1
        return tot

    def scaling(self):
        return {"slow": {"n_values": [16, 24, 32, 48, 64, 96], "cost": "n*(n+1)*(n+2)/6", "rivals": ["n**2*log(n)", "n**4"]},
                "fast": {"n_values": [16, 32, 64, 128, 256], "cost": "n**2", "rivals": ["n*log(n)", "n**2*log(n)"]},
                "tolerance": 0.05}

    def expected_counts(self, side, ns):
        return [n * (n + 1) * (n + 2) // 6 for n in ns] if side == "slow" else None

    def scaling_key(self):
        return "knuth|" + short_hash({k: v for k, v in self.spec.items() if k != "seed"})

    def canonical(self):
        return short_hash({k: v for k, v in self.spec.items() if k != "seed"})

    def cluster(self):
        return f"knuth:{self.family}"
