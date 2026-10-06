"""Rule R3: repeated squaring for an associative operation (binary powering).

Problem (one per finite magma (M, *), |M| = m <= 6): given x in M and an n-bit exponent e >= 1, compute the
left power x^e defined by p_1 = x, p_(i+1) = p_i * x.
Slow: the definition, e - 1 operations. Fast (rule): left-to-right square-and-multiply, 2(n - 1) operations
for e = 2^n - 1. Both reach the magma only through a counted operation oracle.

Stated precondition: * is associative. The screen also records weaker properties:
  power_assoc   p_a * p_b = p_(a+b) for all a, b >= 1, all x (all bracketings of x^n agree)
  square_cond   p_a * p_a = p_(2a) for all a >= 1, all x
Because the left-to-right method only ever squares a left power (r <- r * r) or multiplies it by x
(r <- r * x, which IS the definition), it returns p_e for every e iff square_cond holds (induction on the bits
of e; every a >= 1 occurs as a prefix). Both conditions are checked for a, b <= 2m + 2, which suffices
because the left-power sequence is eventually periodic with pre-period + period <= m + 1.

Families: random, comm, idem, idem_comm, semigroup (closures of random transformations of [3]), group
(Z_m, Z_2 x Z_2, S_3), band_left, band_right, rect_band, null, chain (max), latin, perturbed_semigroup.

Caveat recorded in the report: for a FIXED finite magma the left powers are eventually periodic, so x^e can
also be found with at most m + 1 operations plus arithmetic on e (`fast_cycle`); the family "fixed carrier,
growing e" is therefore degenerate as a complexity statement (T7 at most), as is any fixed-size carrier.
"""
from __future__ import annotations

import itertools
import random

from .common import Candidate, canon_table_exact, relabel_table

RULE = "magma_power"

CATALOGUE = {
    "name": "repeated squaring (binary powering) for an associative operation",
    "precondition": "the operation is associative (sufficient); the screen tests the weaker power-associativity and the "
                    "'square condition' p_a * p_a = p_(2a)",
    "transformation": "x^e by e - 1 sequential operations -> square-and-multiply over the bits of e",
    "cost_change": "Theta(e) = Theta(2^n) -> Theta(n) operations (n = bit length of e)",
    "failure_mode": "non-associative operation: the bracketing ((xx)(xx))... differs from the left fold",
    "literature": "Knuth, TAOCP Vol. 2, section 4.6.3 (evaluation of powers) [book, recalled section]; dataset entries "
                  "modular-exponentiation, fibonacci (fast doubling)",
}

FAMILIES = ["random", "comm", "idem", "idem_comm", "semigroup", "group", "band_left", "band_right", "rect_band",
            "null", "chain", "latin", "perturbed_semigroup"]
WEIGHTS = [60, 40, 25, 25, 50, 15, 5, 5, 5, 5, 5, 20, 40]


def _transformation_semigroup(rng, r=3, max_size=6, tries=40):
    for _ in range(tries):
        gens = [tuple(rng.randrange(r) for _ in range(r)) for _ in range(rng.choice([1, 2]))]
        elems = set(gens)
        frontier = list(gens)
        while frontier and len(elems) <= max_size:
            new = []
            for f in frontier:
                for g in list(elems):
                    for h in (tuple(f[g[x]] for x in range(r)), tuple(g[f[x]] for x in range(r))):
                        if h not in elems:
                            elems.add(h)
                            new.append(h)
            frontier = new
        if 2 <= len(elems) <= max_size:
            el = sorted(elems)
            idx = {e: i for i, e in enumerate(el)}
            return [[idx[tuple(a[b[x]] for x in range(r))] for b in el] for a in el]
    return None


def _group(rng):
    kind = rng.choice(["cyclic", "cyclic", "klein", "s3"])
    if kind == "cyclic":
        m = rng.choice([2, 3, 4, 5])
        return [[(a + b) % m for b in range(m)] for a in range(m)]
    if kind == "klein":
        return [[a ^ b for b in range(4)] for a in range(4)]
    perms = sorted(itertools.permutations(range(3)))
    idx = {p: i for i, p in enumerate(perms)}
    return [[idx[tuple(p[q[x]] for x in range(3))] for q in perms] for p in perms]


def make_table(family, rng, m):
    if family == "random":
        return [[rng.randrange(m) for _ in range(m)] for _ in range(m)]
    if family in ("comm", "idem_comm"):
        T = [[0] * m for _ in range(m)]
        for a in range(m):
            for b in range(a, m):
                T[a][b] = T[b][a] = rng.randrange(m)
        if family == "idem_comm":
            for a in range(m):
                T[a][a] = a
        return T
    if family == "idem":
        T = [[rng.randrange(m) for _ in range(m)] for _ in range(m)]
        for a in range(m):
            T[a][a] = a
        return T
    if family == "semigroup":
        return _transformation_semigroup(rng) or _group(rng)
    if family == "group":
        return _group(rng)
    if family == "band_left":
        return [[a for _ in range(m)] for a in range(m)]
    if family == "band_right":
        return [[b for b in range(m)] for _ in range(m)]
    if family == "rect_band":  # (a1, a2)(b1, b2) = (a1, b2) on 2 x 2
        return [[2 * (a // 2) + (b % 2) for b in range(4)] for a in range(4)]
    if family == "null":
        c = rng.randrange(m)
        return [[c] * m for _ in range(m)]
    if family == "chain":
        return [[max(a, b) for b in range(m)] for a in range(m)]
    if family == "latin":
        p1, p2, p3 = (rng.sample(range(m), m) for _ in range(3))
        return [[p3[(p1[a] + p2[b]) % m] for b in range(m)] for a in range(m)]
    if family == "perturbed_semigroup":
        T = _transformation_semigroup(rng) or _group(rng)
        k = len(T)
        for _ in range(rng.choice([1, 2])):
            a, b = rng.randrange(k), rng.randrange(k)
            T[a][b] = rng.choice([x for x in range(k) if x != T[a][b]] or [T[a][b]])
        return T
    raise ValueError(family)


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|magma_power|{seed}")
    out = []
    for _ in range(count):
        fam = rng.choices(FAMILIES, WEIGHTS)[0]
        m = rng.choice([2, 3, 3, 4, 4, 5])
        T = make_table(fam, rng, m)
        perm = rng.sample(range(len(T)), len(T))
        out.append({"family": fam, "m": len(T), "table": relabel_table(T, perm)})
    return out


def build(spec: dict) -> Candidate:
    return MagmaCandidate(spec)


def left_powers(T, x, upto):
    p = [None, x]
    for _ in range(upto - 1):
        p.append(T[p[-1]][x])
    return p


def properties(T):
    m = len(T)
    R = range(m)
    L = 2 * m + 2
    assoc = all(T[T[a][b]][c] == T[a][T[b][c]] for a in R for b in R for c in R)
    comm = all(T[a][b] == T[b][a] for a in R for b in R)
    idem = all(T[a][a] == a for a in R)
    pa_x, sq_x = [], []
    for x in R:
        p = left_powers(T, x, 2 * L + 2)
        pa_x.append(all(T[p[a]][p[b]] == p[a + b] for a in range(1, L + 1) for b in range(1, L + 1)))
        sq_x.append(all(T[p[a]][p[a]] == p[2 * a] for a in range(1, L + 1)))
    return {"associative": assoc, "commutative": comm, "idempotent": idem, "power_assoc": all(pa_x),
            "square_cond": all(sq_x), "power_assoc_fraction": sum(pa_x) / m, "square_cond_fraction": sum(sq_x) / m}


class MagmaCandidate(Candidate):
    rule = RULE
    trials = 60
    screen_sizes = (12,)

    def __init__(self, spec):
        super().__init__(spec)
        self.T = spec["table"]
        self.m = len(self.T)
        self._props = properties(self.T)

    def instance(self, rng, n):
        e = rng.randint(1, 40) if rng.random() < 0.5 else rng.randint(1, 2 ** n)
        return (self.T, rng.randrange(self.m), e)

    @staticmethod
    def _op(T, ops):
        def op(a, b):
            ops.n += 1
            return T[a][b]
        return op

    def slow(self, inst, ops):
        T, x, e = inst
        op = self._op(T, ops)
        r = x
        for _ in range(e - 1):
            r = op(r, x)
        return r

    def fast(self, inst, ops):
        T, x, e = inst
        op = self._op(T, ops)
        r = x
        for bit in bin(e)[3:]:
            r = op(r, r)
            if bit == "1":
                r = op(r, x)
        return r

    def fast_cycle(self, inst, ops):
        """Repaired rule for any finite magma: walk the left powers until one repeats (<= m + 1 operations)."""
        T, x, e = inst
        op = self._op(T, ops)
        seq, seen = [x], {x: 1}
        while True:
            nxt = op(seq[-1], x)
            if len(seq) + 1 > e:
                return seq[e - 1]
            if nxt in seen:
                mu, lam = seen[nxt], len(seq) + 1 - seen[nxt]
                return seq[mu - 1 + (e - mu) % lam] if e >= mu else seq[e - 1]
            seq.append(nxt)
            seen[nxt] = len(seq)

    def precondition(self):
        return self._props["associative"]

    def predicates(self):
        return dict(self._props)

    def scaling(self):
        return {"slow": {"n_values": [4, 6, 8, 10, 12, 14], "cost": "2**n - 2", "rivals": ["n**3", "3**n"]},
                "fast": {"n_values": [8, 16, 32, 64, 128], "cost": "n - 1", "rivals": ["log(n)", "n**2"]},
                "tolerance": 0.05}

    def scaling_key(self):
        return "magma_power|left-fold-vs-binary"

    def scale_instance(self, rng, n, side):
        return (self.T, 0, 2 ** n - 1)

    def expected_counts(self, side, ns):
        return [2 ** n - 2 for n in ns] if side == "slow" else [2 * (n - 1) for n in ns]

    def canonical(self):
        return "exact:" + ",".join(map(str, canon_table_exact(self.T)))

    def cluster(self):
        p = self._props
        cls = ("assoc" if p["associative"] else "power-assoc" if p["power_assoc"]
               else "square-cond" if p["square_cond"] else "none")
        return f"magma:{cls}:{'comm' if p['commutative'] else 'noncomm'}"
