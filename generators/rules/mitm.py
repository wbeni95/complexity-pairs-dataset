"""Rule R7: meet in the middle.

Problem (one per combining operation (+) on a finite value set and an interaction model): given n item values
v_1..v_n, optional pairwise interaction terms u_ij on a graph E (additive families only) and a target t, count
the subsets S with  fold_(+){v_i : i in S}  (+ sum of u_ij over edges inside S) = t; the empty fold is the
identity element.
Slow: enumerate all 2^n subsets incrementally (one counted operation per item added, plus one per
interaction term). Fast (rule): split the items into halves L | R, enumerate each half (2^(n/2) each), and for
every distinct left value s look up the right value y solving s (+) y = t (the first solution in table order,
precomputed; one counted operation per lookup). Cross-split interactions are ignored by the rule.

Stated precondition: (+) is a group operation on the values that occur (unique solution y = s^-1 (+) t), and no
interaction edge crosses the split.
Repairs (evaluated in the hypothesis experiment):
  fast_all       sum over ALL solutions y of s (+) y = t: exact for every associative commutative operation
                 (a convolution of the two half-histograms over the monoid, rule composition R7 o R2)
  fast_boundary  condition on the left-half endpoints B of crossing edges: for each assignment of B the crossing
                 terms become per-item constants on the right; exact, cost 2^|B| * 2^(n/2)

Operations: add (Z_M), xor (Z_2^k), mul_unit (Z_p^* with values != 0), mul_zero (Z_p with zero),
mul_comp (Z_M, M composite), max, addsat (min(a + b, M - 1)), add_inter (Z_M + random interactions),
add_inter_local (interactions only inside the halves).
"""
from __future__ import annotations

import random
from collections import Counter

from .common import Candidate, short_hash

RULE = "mitm"

CATALOGUE = {
    "name": "meet in the middle",
    "precondition": "the objective is a fold of per-item contributions in a group (unique completion y = s^-1 + t), "
                    "with no interaction between the two halves of the split",
    "transformation": "enumerate both halves, store one half's values, look up the completing value for each of the other",
    "cost_change": "Theta(2^n) -> Theta(2^(n/2)) operations (time; Theta(2^(n/2)) memory)",
    "failure_mode": "non-unique completion (monoids with zero, max, saturating addition, zero divisors) undercounts; "
                    "crossing interactions make the half values wrong",
    "repair": "all-solutions lookup (exact for any commutative monoid; cost x max #solutions or + M^2), or conditioning "
              "on the boundary of the crossing edges (exact; cost x 2^|B|, a gain iff |B| < n/2)",
    "literature": "Horowitz-Sahni 1974 (doi:10.1145/321812.321823) [recalled]; dataset entry knapsack-01-brute-vs-dp",
}

OPS = ["add", "xor", "mul_unit", "mul_zero", "mul_comp", "max", "addsat", "add_inter", "add_inter_local"]
WEIGHTS = [20, 12, 15, 15, 12, 10, 10, 20, 16]
PRIMES = [5, 7, 11, 13, 17]
COMPOSITES = [6, 8, 9, 10, 12, 15]


def op_table(op, M):
    R = range(M)
    if op in ("add", "add_inter", "add_inter_local"):
        return [[(a + b) % M for b in R] for a in R], 0
    if op == "xor":
        return [[a ^ b for b in R] for a in R], 0
    if op in ("mul_unit", "mul_zero", "mul_comp"):
        return [[(a * b) % M for b in R] for a in R], 1
    if op == "max":
        return [[max(a, b) for b in R] for a in R], 0
    if op == "addsat":
        return [[min(a + b, M - 1) for b in R] for a in R], 0
    raise ValueError(op)


def make_spec(op, rng):
    if op in ("mul_unit", "mul_zero"):
        M = rng.choice(PRIMES)
    elif op == "mul_comp":
        M = rng.choice(COMPOSITES)
    elif op == "xor":
        M = rng.choice([4, 8, 16])
    else:
        M = rng.choice([5, 8, 12, 16, 31])
    s = {"family": op, "M": M}
    if op.startswith("add_inter"):
        s["density"] = rng.choice([0.05, 0.1, 0.2, 0.4])
    return s


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|mitm|{seed}")
    return [make_spec(rng.choices(OPS, WEIGHTS)[0], rng) for _ in range(count)]


def build(spec: dict) -> Candidate:
    return MitmCandidate(spec)


def enumerate_folds(items, edges, u, T, e, ops, offset=0, extra=None):
    """Values of all subsets of `items` (list of (index, value)); edges among these items only.
    extra[i] (optional): additive per-item constant from conditioning (additive families)."""
    vals = [(0, e)]
    for pos, (idx, v) in enumerate(items):
        add = v if extra is None else (v + extra.get(idx, 0))
        nbr = [(q, u[(min(idx, items[q][0]), max(idx, items[q][0]))]) for q in range(pos)
               if (min(idx, items[q][0]), max(idx, items[q][0])) in edges]
        new = []
        for mask, val in vals:
            x = T[val][add % len(T)]
            ops.n += 1
            for q, w in nbr:
                if mask >> q & 1:
                    x = T[x][w]
                    ops.n += 1
            new.append((mask | 1 << pos, x))
        vals += new
    return Counter(val for _, val in vals)


class MitmCandidate(Candidate):
    rule = RULE
    trials = 20
    screen_sizes = (8, 10, 12)

    def __init__(self, spec):
        super().__init__(spec)
        self.op = spec["family"]
        self.M = spec["M"]
        self.T, self.e = op_table(self.op, self.M)
        M, T = self.M, self.T
        self.solve = [[next((y for y in range(M) if T[s][y] == t), None) for t in range(M)] for s in range(M)]
        self.nsol = [[sum(T[s][y] == t for y in range(M)) for t in range(M)] for s in range(M)]

    def instance(self, rng, n):
        M = self.M
        lo = 1 if self.op == "mul_unit" else 0
        vals = [rng.randrange(lo, M) for _ in range(n)]
        t = rng.randrange(lo, M)
        edges, u = set(), {}
        if self.op.startswith("add_inter"):
            h = n // 2
            for i in range(n):
                for j in range(i + 1, n):
                    if self.op == "add_inter_local" and (i < h) != (j < h):
                        continue
                    if rng.random() < self.spec["density"]:
                        edges.add((i, j))
                        u[(i, j)] = rng.randrange(M)
        return (n, vals, t, frozenset(edges), u)

    def slow(self, inst, ops):
        n, vals, t, edges, u = inst
        return enumerate_folds(list(enumerate(vals)), edges, u, self.T, self.e, ops)[t]

    def _halves(self, inst):
        n, vals, t, edges, u = inst
        h = n // 2
        return list(enumerate(vals))[:h], list(enumerate(vals))[h:]

    def fast(self, inst, ops):
        n, vals, t, edges, u = inst
        L, R = self._halves(inst)
        cl = enumerate_folds(L, edges, u, self.T, self.e, ops)
        cr = enumerate_folds(R, edges, u, self.T, self.e, ops)
        total = 0
        for s, c in cl.items():
            ops.n += 1
            y = self.solve[s][t]
            if y is not None:
                total += c * cr.get(y, 0)
        return total

    def fast_all(self, inst, ops):
        n, vals, t, edges, u = inst
        L, R = self._halves(inst)
        cl = enumerate_folds(L, edges, u, self.T, self.e, ops)
        cr = enumerate_folds(R, edges, u, self.T, self.e, ops)
        total = 0
        for s, c in cl.items():
            for y in range(self.M):
                ops.n += 1
                if self.T[s][y] == t:
                    total += c * cr.get(y, 0)
        return total

    def fast_boundary(self, inst, ops):
        """Condition on the left endpoints of crossing edges (additive families only)."""
        n, vals, t, edges, u = inst
        L, R = self._halves(inst)
        h = len(L)
        cross = [(i, j) for (i, j) in edges if i < h <= j]
        B = sorted({i for i, _ in cross})
        total = 0
        for beta in range(2 ** len(B)):
            chosen = {B[q] for q in range(len(B)) if beta >> q & 1}
            # left subsets consistent with beta: force chosen B items in, other B items out
            forced_in = [(i, v) for i, v in L if i in chosen]
            free = [(i, v) for i, v in L if i not in B]
            b0 = self.e  # fold of exactly the forced-in items, with their mutual interactions
            for pos, (i, v) in enumerate(forced_in):
                b0 = self.T[b0][v]
                ops.n += 1
                for k, _ in forced_in[:pos]:
                    key = (min(i, k), max(i, k))
                    if key in edges:
                        b0 = self.T[b0][u[key]]
                        ops.n += 1
            # interactions between forced-in items and free items are added per free item
            extra_l = {i: sum(u[(min(i, k), max(i, k))] for k in chosen if (min(i, k), max(i, k)) in edges)
                       for i, _ in free}
            cl = enumerate_folds(free, edges, u, self.T, b0, ops, extra=extra_l)
            extra_r = {j: sum(u[(i, j)] for (i, jj) in cross if jj == j and i in chosen) for j, _ in R}
            cr = enumerate_folds(R, edges, u, self.T, self.e, ops, extra=extra_r)
            for s, c in cl.items():
                ops.n += 1
                y = self.solve[s][t]
                if y is not None:
                    total += c * cr.get(y, 0)
        return total

    def score(self, inst, a, b):
        if a == b:
            return True, 1.0
        return False, max(0.0, 1 - abs(b - a) / max(a, 1))

    def is_group(self):
        M, T, e = self.M, self.T, self.e
        vals = range(1, M) if self.op == "mul_unit" else range(M)
        return all(any(T[s][y] == e for y in vals) for s in vals) and all(
            T[s][y] in vals for s in vals for y in vals)

    def precondition(self):
        return self.is_group() and self.op not in ("add_inter",)

    def predicates(self):
        M = self.M
        lo = 1 if self.op == "mul_unit" else 0
        uniq = all(self.nsol[s][t] <= 1 for s in range(lo, M) for t in range(lo, M))
        maxsol = max(self.nsol[s][t] for s in range(lo, M) for t in range(lo, M))
        return {"group": self.is_group(), "unique_completion": uniq, "max_solutions": maxsol,
                "interactions": self.op.startswith("add_inter"),
                "crossing_edges_possible": self.op == "add_inter"}

    def scaling(self):
        if self.op.startswith("add_inter"):
            return None
        return {"slow": {"n_values": [8, 10, 12, 14, 16, 18], "cost": "2**n", "rivals": ["n*2**n"]},
                "fast": {"n_values": [8, 12, 16, 20, 24, 28], "cost": "2**(n/2)", "rivals": ["n*2**(n/2)"]},
                "tolerance": 0.05}

    def scale_instance(self, rng, n, side):
        return self.instance(rng, n)

    def scaling_key(self):
        return f"mitm|{self.op}|{self.M}"

    def canonical(self):
        return short_hash(self.spec)

    def cluster(self):
        return f"mitm:{self.op}:{'group' if self.is_group() else 'non-group'}"
