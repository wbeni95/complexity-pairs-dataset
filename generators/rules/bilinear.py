"""Rule R6: bilinear algorithms with fewer multiplications (Karatsuba / Strassen pattern), over GF(2).

Problem (one per small bilinear map B: GF(2)^a x GF(2)^b -> GF(2)^c with tensor T, a*b*c <= 18): evaluate
the d-th tensor power B^(x)d on x in GF(2)^(a^d), y in GF(2)^(b^d) (size parameter n = d).
Slow: the naive bilinear form, one product per support pair (i, j) with T[i][j][:] != 0, applied
recursively: m^d products, m = |support|. Fast (rule): a rank-r decomposition T = sum_t u_t (x) v_t (x) w_t
applied recursively: r^d products. Only leaf products (AND of two bits) are counted; additions (XOR) are not.

The exact GF(2) rank of every tensor of a format is computed once by breadth-first search over all 2^(abc)
tensors (generators: the rank-1 tensors), which also yields a minimal decomposition.
Stated precondition: r < m. Cost change: m^d -> r^d, i.e. exponent log_a(m) -> log_a(r) in the input length.
Near-miss attempt when r = m: the best (m-1)-term decomposition (the rank <= m-1 tensor nearest to T in
Hamming distance); the screen measures the fraction of correct output bits.

Named members (pipeline checks): karatsuba (2-term polynomial product, (2,2,3)), gf4 (multiplication in GF(4)),
gf2_complex (x * y mod t^2 + 1), truncated (x * y mod t^2).
"""
from __future__ import annotations

import itertools
import random

from .common import Candidate, short_hash

RULE = "bilinear"
FORMATS = [(2, 2, 2), (2, 2, 3), (2, 3, 2), (3, 2, 2), (2, 2, 4), (2, 3, 3)]

CATALOGUE = {
    "name": "bilinear algorithm with fewer multiplications, applied recursively",
    "precondition": "the tensor rank r of the base bilinear map is below its naive product count m (support size)",
    "transformation": "replace the m naive products by r products of linear combinations; recurse on tensor powers",
    "cost_change": "m^d -> r^d products, exponent log_a m -> log_a r in the input length a^d",
    "failure_mode": "r = m (no cheaper decomposition); an (m-1)-term approximation is wrong on the outputs fed by the "
                    "residual tensor, and repairing it costs at least rank(residual) >= 1 extra products, i.e. no gain",
    "literature": "Karatsuba-Ofman 1962/63 [recalled]; Strassen 1969 (doi:10.1007/BF02165411) [recalled]; dataset entries "
                  "integer-multiplication-schoolbook-vs-karatsuba, matrix-multiplication-naive-vs-strassen",
}

_BFS = {}


def bit(a, b, c, i, j, k):
    return 1 << ((i * b + j) * c + k)


def rank_table(fmt):
    """(gens, rank bytearray, parent bytearray) for all tensors of a format; cached per process."""
    if fmt in _BFS:
        return _BFS[fmt]
    a, b, c = fmt
    gens = []
    for u in range(1, 2 ** a):
        for v in range(1, 2 ** b):
            for w in range(1, 2 ** c):
                mask = 0
                for i in range(a):
                    if u >> i & 1:
                        for j in range(b):
                            if v >> j & 1:
                                for k in range(c):
                                    if w >> k & 1:
                                        mask |= bit(a, b, c, i, j, k)
                gens.append((mask, u, v, w))
    size = 1 << (a * b * c)
    rank = bytearray([255]) * size
    par = bytearray(size)
    rank[0] = 0
    frontier, r = [0], 0
    masks = [g[0] for g in gens]
    while frontier:
        nxt = []
        for s in frontier:
            for gi, g in enumerate(masks):
                t = s ^ g
                if rank[t] == 255:
                    rank[t] = r + 1
                    par[t] = gi
                    nxt.append(t)
        frontier = nxt
        r += 1
    _BFS[fmt] = (gens, rank, par)
    return _BFS[fmt]


def decomposition(fmt, T):
    gens, rank, par = rank_table(fmt)
    terms = []
    while T:
        g = gens[par[T]]
        terms.append((g[1], g[2], g[3]))
        T ^= g[0]
    return terms


def support(fmt, T):
    a, b, c = fmt
    return [(i, j, [k for k in range(c) if T & bit(a, b, c, i, j, k)]) for i in range(a) for j in range(b)
            if any(T & bit(a, b, c, i, j, k) for k in range(c))]


def named_tensors():
    out = {}
    a, b, c = 2, 2, 3
    out["karatsuba"] = ((2, 2, 3), sum(bit(a, b, c, i, j, i + j) for i in range(2) for j in range(2)))
    a, b, c = 2, 2, 2
    gf4 = bit(a, b, c, 0, 0, 0) | bit(a, b, c, 1, 1, 0) | bit(a, b, c, 0, 1, 1) | bit(a, b, c, 1, 0, 1) | bit(a, b, c, 1, 1, 1)
    out["gf4"] = ((2, 2, 2), gf4)
    out["gf2_complex"] = ((2, 2, 2), bit(a, b, c, 0, 0, 0) | bit(a, b, c, 1, 1, 0) | bit(a, b, c, 0, 1, 1) | bit(a, b, c, 1, 0, 1))
    out["truncated"] = ((2, 2, 2), bit(a, b, c, 0, 0, 0) | bit(a, b, c, 0, 1, 1) | bit(a, b, c, 1, 0, 1))
    return out


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|bilinear|{seed}")
    out = [{"family": "named", "name": k, "fmt": list(f), "tensor": t} for k, (f, t) in sorted(named_tensors().items())]
    while len(out) < count:
        fmt = rng.choice(FORMATS)
        dens = rng.choice([0.15, 0.25, 0.35, 0.5])
        nb = fmt[0] * fmt[1] * fmt[2]
        T = sum(1 << q for q in range(nb) if rng.random() < dens)
        out.append({"family": "random", "fmt": list(fmt), "density": dens, "tensor": T})
    return out[:count]


def build(spec: dict) -> Candidate:
    return BilinearCandidate(spec)


def naive_power(fmt, supp, d, x, y, ops):
    a, b, c = fmt
    if d == 0:
        ops.n += 1
        return [x[0] & y[0]]
    bx, by, bz = a ** (d - 1), b ** (d - 1), c ** (d - 1)
    out = [0] * (c * bz)
    for i, j, ks in supp:
        z = naive_power(fmt, supp, d - 1, x[i * bx:(i + 1) * bx], y[j * by:(j + 1) * by], ops)
        for k in ks:
            o = k * bz
            for t in range(bz):
                out[o + t] ^= z[t]
    return out


def fast_power(fmt, terms, d, x, y, ops):
    a, b, c = fmt
    if d == 0:
        ops.n += 1
        return [x[0] & y[0]]
    bx, by, bz = a ** (d - 1), b ** (d - 1), c ** (d - 1)
    out = [0] * (c * bz)
    for u, v, w in terms:
        X = [0] * bx
        for i in range(a):
            if u >> i & 1:
                X = [p ^ q for p, q in zip(X, x[i * bx:(i + 1) * bx])]
        Y = [0] * by
        for j in range(b):
            if v >> j & 1:
                Y = [p ^ q for p, q in zip(Y, y[j * by:(j + 1) * by])]
        z = fast_power(fmt, terms, d - 1, X, Y, ops)
        for k in range(c):
            if w >> k & 1:
                o = k * bz
                for t in range(bz):
                    out[o + t] ^= z[t]
    return out


class BilinearCandidate(Candidate):
    rule = RULE
    trials = 6
    screen_sizes = (1, 2, 3)

    def __init__(self, spec):
        super().__init__(spec)
        self.fmt = tuple(spec["fmt"])
        self.T = spec["tensor"]
        _, rank, _ = rank_table(self.fmt)
        self.r = rank[self.T]
        self.supp = support(self.fmt, self.T)
        self.m = len(self.supp)
        if self.r < self.m:
            self.terms = decomposition(self.fmt, self.T)
            self.residual = 0
        else:
            self.terms, self.residual = self._best_approx()

    def _best_approx(self):
        """Nearest tensor of rank <= m - 1 (Hamming distance), and its decomposition."""
        _, rank, _ = rank_table(self.fmt)
        target = max(self.m - 1, 0)
        best = None
        for S in range(len(rank)):
            if rank[S] <= target:
                dist = bin(S ^ self.T).count("1")
                if best is None or dist < best[0]:
                    best = (dist, S)
        return decomposition(self.fmt, best[1]), best[0]

    def instance(self, rng, n):
        a, b, _ = self.fmt
        return (n, [rng.randint(0, 1) for _ in range(a ** n)], [rng.randint(0, 1) for _ in range(b ** n)])

    def slow(self, inst, ops):
        d, x, y = inst
        return naive_power(self.fmt, self.supp, d, x, y, ops)

    def fast(self, inst, ops):
        d, x, y = inst
        return fast_power(self.fmt, self.terms, d, x, y, ops)

    def score(self, inst, a, b):
        agree = sum(p == q for p, q in zip(a, b)) / len(a)
        return agree == 1.0, agree

    def degenerate(self):
        if self.m <= 1:
            return "at most one product: nothing to save"
        return None

    def precondition(self):
        return self.r < self.m

    def predicates(self):
        return {"rank": self.r, "naive_products": self.m, "residual_weight": self.residual,
                "entries": self.fmt[0] * self.fmt[1] * self.fmt[2], "weight": bin(self.T).count("1")}

    def scaling(self):
        if self.r >= self.m:
            return None
        s_ns = [d for d in range(1, 9) if self.m ** d <= 200_000]
        f_ns = [d for d in range(1, 12) if self.r ** d <= 200_000][:8]
        if len(s_ns) < 3 or self.m ** s_ns[-1] < 3 * self.m ** s_ns[0]:
            return None
        return {"slow": {"n_values": s_ns, "cost": f"{self.m}**n", "rivals": []},
                "fast": {"n_values": f_ns, "cost": f"{self.r}**n", "rivals": []}, "tolerance": 0.02}

    def expected_counts(self, side, ns):
        base = self.m if side == "slow" else self.r
        return [base ** d for d in ns]

    def scaling_key(self):
        return f"bilinear|m{self.m}|r{self.r}|{self.fmt}"

    def canonical(self):
        a, b, c = self.fmt
        cells = [(i, j, k) for i in range(a) for j in range(b) for k in range(c) if self.T & bit(a, b, c, i, j, k)]
        best = None
        swaps = [False, True] if a == b else [False]
        for sw in swaps:
            for p in itertools.permutations(range(a)):
                for q in itertools.permutations(range(b)):
                    for s in itertools.permutations(range(c)):
                        mask = 0
                        for i, j, k in cells:
                            ii, jj = (p[i], q[j]) if not sw else (q[j], p[i])
                            mask |= bit(a, b, c, ii, jj, s[k])
                        if best is None or mask < best:
                            best = mask
        return f"{a}x{b}x{c}:{best}"

    def cluster(self):
        return f"bilinear:{self.fmt[0]}x{self.fmt[1]}x{self.fmt[2]}:m{self.m}:r{self.r}"
