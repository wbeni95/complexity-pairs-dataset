"""Rule R4: greedy on matroids (Rado-Edmonds).

Problem (one per downward-closed set system F on a ground set E, |E| = g <= 7): given non-negative integer
weights w on E, find the maximum total weight of a member of F.
Slow: test every subset of E with the membership oracle (2^g oracle calls). Fast (rule): sort by weight
(descending, ties by index) and add an element whenever the result stays in F (g oracle calls; the
O(g log g) sort comparisons are not counted). Only oracle calls are counted.

Stated precondition: (E, F) is a matroid (exchange axiom, checked exactly). Recorded alongside:
  rank_quotient  q(F) = min over A of (smallest maximal member inside A) / (largest member inside A)
  adversarial    the greedy/optimum ratio on weights built from each A (M+1 on a smallest maximal member
                 S of A, M on A \\ S, 0 elsewhere, M = 1000), minimised over A
The literature bound (Jenkyns 1976; Korte-Hausmann 1978) [recalled] says greedy/opt >= q(F) for all weights,
with equality attainable; the screen tests this on every candidate.

Families: uniform, partition, graphic, linear (GF(2)) -- matroids; matching, indset, knapsack, downclosure,
two_partition (intersection of two partition matroids), basis_removed (a matroid minus one basis) -- usually not.
"""
from __future__ import annotations

import itertools
import math
import random

from .common import Candidate, short_hash

RULE = "greedy"

CATALOGUE = {
    "name": "greedy on matroids",
    "precondition": "the feasible sets form a matroid (downward closed + exchange axiom)",
    "transformation": "enumerate all feasible sets -> sort by weight and add greedily while feasible",
    "cost_change": "2^g oracle calls -> g oracle calls (+ O(g log g) comparisons)",
    "failure_mode": "a non-matroid independence system: greedy can stop at a light maximal set; worst ratio = rank "
                    "quotient (k-systems: >= 1/k)",
    "literature": "Rado 1957 / Edmonds 1971 (doi:10.1007/BF01584082) [recalled]; Korte-Hausmann 1978 rank quotient "
                  "[recalled]; dataset entry minimum-spanning-tree (graphic matroid)",
}

MATROID_FAMILIES = ["uniform", "partition", "graphic", "linear"]
OTHER_FAMILIES = ["matching", "indset", "knapsack", "downclosure", "two_partition", "basis_removed"]


def _popcount(x):
    return bin(x).count("1")


def _gf2_rank(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def make_predicate(spec):
    """Membership predicate for a family spec (a bitmask over the g elements)."""
    fam, g = spec["family"], spec["g"]
    if fam == "uniform":
        r = spec["r"]
        return lambda S: _popcount(S) <= r
    if fam in ("partition", "two_partition"):
        blocks = spec["blocks"]
        caps = spec["caps"]
        blocks2, caps2 = spec.get("blocks2"), spec.get("caps2")

        def ok(S, bl, cp):
            cnt = [0] * len(cp)
            for i in range(g):
                if S >> i & 1:
                    cnt[bl[i]] += 1
                    if cnt[bl[i]] > cp[bl[i]]:
                        return False
            return True
        if fam == "partition":
            return lambda S: ok(S, blocks, caps)
        return lambda S: ok(S, blocks, caps) and ok(S, blocks2, caps2)
    if fam == "graphic" or fam == "matching":
        edges = spec["edges"]
        v = spec["v"]
        if fam == "matching":
            def match(S):
                used = 0
                for i in range(g):
                    if S >> i & 1:
                        a, b = edges[i]
                        if used >> a & 1 or used >> b & 1:
                            return False
                        used |= (1 << a) | (1 << b)
                return True
            return match

        def forest(S):
            parent = list(range(v))

            def find(x):
                while parent[x] != x:
                    parent[x] = parent[parent[x]]
                    x = parent[x]
                return x
            for i in range(g):
                if S >> i & 1:
                    a, b = find(edges[i][0]), find(edges[i][1])
                    if a == b:
                        return False
                    parent[a] = b
            return True
        return forest
    if fam == "linear":
        vecs = spec["vectors"]
        return lambda S: _gf2_rank([vecs[i] for i in range(g) if S >> i & 1]) == _popcount(S)
    if fam == "indset":
        edges = spec["edges"]
        return lambda S: not any(S >> a & 1 and S >> b & 1 for a, b in edges)
    if fam == "knapsack":
        sizes, cap = spec["sizes"], spec["cap"]
        return lambda S: sum(sizes[i] for i in range(g) if S >> i & 1) <= cap
    if fam == "downclosure":
        maxs = spec["maximal"]
        return lambda S: any(S & ~M == 0 for M in maxs)
    if fam == "basis_removed":
        base = make_predicate(spec["base"])
        B = spec["removed"]
        return lambda S: base(S) and S != B
    raise ValueError(fam)


def make_spec(fam, rng, g):
    if fam == "uniform":
        return {"family": fam, "g": g, "r": rng.randint(1, g - 1)}
    if fam in ("partition", "two_partition"):
        nb = rng.randint(1, max(1, g // 2))
        s = {"family": fam, "g": g, "blocks": [rng.randrange(nb) for _ in range(g)],
             "caps": [rng.randint(1, 2) for _ in range(nb)]}
        if fam == "two_partition":
            nb2 = rng.randint(2, max(2, g // 2))
            s.update(blocks2=[rng.randrange(nb2) for _ in range(g)], caps2=[1] * nb2)
        return s
    if fam in ("graphic", "matching"):
        v = rng.randint(3, 5) if fam == "graphic" else rng.randint(4, 6)
        pairs = [(a, b) for a in range(v) for b in range(a + 1, v)]
        if fam == "graphic":
            edges = [list(rng.choice(pairs)) for _ in range(g)]  # parallel edges allowed
        else:
            edges = [list(p) for p in rng.sample(pairs, min(g, len(pairs)))]
            g = len(edges)
        return {"family": fam, "g": g, "v": v, "edges": edges}
    if fam == "linear":
        d = rng.randint(2, 4)
        return {"family": fam, "g": g, "vectors": [rng.randint(1, 2 ** d - 1) for _ in range(g)]}
    if fam == "indset":
        p = rng.choice([0.2, 0.35, 0.5])
        return {"family": fam, "g": g,
                "edges": [[a, b] for a in range(g) for b in range(a + 1, g) if rng.random() < p]}
    if fam == "knapsack":
        sizes = [rng.randint(1, 5) for _ in range(g)]
        return {"family": fam, "g": g, "sizes": sizes, "cap": rng.randint(max(sizes), sum(sizes) - 1)}
    if fam == "downclosure":
        return {"family": fam, "g": g, "maximal": [rng.randrange(1, 2 ** g) for _ in range(rng.randint(1, 4))]}
    if fam == "basis_removed":
        base = make_spec(rng.choice(["uniform", "linear", "graphic"]), rng, g)
        pred = make_predicate(base)
        members = [S for S in range(2 ** base["g"]) if pred(S)]
        maximal = [S for S in members if not any(pred(S | 1 << i) for i in range(base["g"]) if not S >> i & 1)]
        return {"family": fam, "g": base["g"], "base": base, "removed": rng.choice(maximal)}
    raise ValueError(fam)


def generate(seed: int, count: int) -> list[dict]:
    rng = random.Random(f"rules|greedy|{seed}")
    fams = MATROID_FAMILIES * 3 + OTHER_FAMILIES * 2
    return [make_spec(rng.choice(fams), rng, rng.choice([5, 6, 7])) for _ in range(count)]


def build(spec: dict) -> Candidate:
    return GreedyCandidate(spec)


def brute_opt(pred, w, g, ops=None):
    best = 0
    for S in range(2 ** g):
        if ops is not None:
            ops.n += 1
        if pred(S):
            val = sum(w[i] for i in range(g) if S >> i & 1)
            if val > best:
                best = val
    return best


def greedy_value(pred, w, g, ops=None):
    order = sorted(range(g), key=lambda i: (-w[i], i))
    S = 0
    for i in order:
        if ops is not None:
            ops.n += 1
        if pred(S | 1 << i):
            S |= 1 << i
    return sum(w[i] for i in range(g) if S >> i & 1)


def analyse(pred, g):
    members = [S for S in range(2 ** g) if pred(S)]
    mset = set(members)
    exchange = True
    for I in members:
        for J in members:
            if _popcount(I) < _popcount(J) and not any((J >> x & 1) and not (I >> x & 1) and (I | 1 << x) in mset
                                                        for x in range(g)):
                exchange = False
                break
        if not exchange:
            break
    q = 1.0
    worst_A = None
    adv = 1.0
    for A in range(1, 2 ** g):
        inside = [S for S in members if S & ~A == 0]
        maximal = [S for S in inside if not any((A >> x & 1) and not (S >> x & 1) and (S | 1 << x) in mset
                                                 for x in range(g))]
        up = max(_popcount(S) for S in inside)
        if up == 0:
            continue
        smin = min(maximal, key=_popcount)
        ratio = _popcount(smin) / up
        if ratio < q:
            q, worst_A = ratio, A
        M = 1000
        w = [(M + 1) if smin >> i & 1 else (M if A >> i & 1 else 0) for i in range(g)]
        opt = brute_opt(pred, w, g)
        if opt:
            adv = min(adv, greedy_value(pred, w, g) / opt)
    return {"matroid": exchange, "members": len(members), "rank_quotient": round(q, 6),
            "adversarial_ratio": round(adv, 6), "worst_A": worst_A}


class GreedyCandidate(Candidate):
    rule = RULE
    trials = 40
    screen_sizes = (0,)

    def __init__(self, spec):
        super().__init__(spec)
        self.g = spec["g"]
        self.pred = make_predicate(spec)
        self._an = analyse(self.pred, self.g)

    def instance(self, rng, n):
        kind = rng.choice(["u100", "01", "small", "exp"])
        g = self.g
        if kind == "u100":
            w = [rng.randint(1, 100) for _ in range(g)]
        elif kind == "01":
            w = [rng.randint(0, 1) for _ in range(g)]
        elif kind == "small":
            w = [rng.randint(1, 3) for _ in range(g)]
        else:
            w = [2 ** rng.randint(0, 10) for _ in range(g)]
        return (g, w, None)

    def slow(self, inst, ops):
        g, w, pred = inst
        return brute_opt(pred or self.pred, w, g, ops)

    def fast(self, inst, ops):
        g, w, pred = inst
        return greedy_value(pred or self.pred, w, g, ops)

    def score(self, inst, a, b):
        return a == b, (b / a if a else 1.0)

    def precondition(self):
        return self._an["matroid"]

    def predicates(self):
        return dict(self._an)

    def scaling(self):
        return {"slow": {"n_values": [6, 8, 10, 12, 14, 16], "cost": "2**n", "rivals": ["n**3"]},
                "fast": {"n_values": [6, 8, 10, 12, 14, 16, 32, 64], "cost": "n", "rivals": ["log(n)", "n**2"]},
                "tolerance": 0.05}

    def scaling_key(self):
        return "greedy|oracle-calls"

    def scale_instance(self, rng, n, side):
        # Oracle-call counts depend only on g; a uniform matroid U(g/2, g) is used at every size.
        return (n, [rng.randint(1, 100) for _ in range(n)], make_predicate({"family": "uniform", "g": n, "r": n // 2}))

    def expected_counts(self, side, ns):
        return [2 ** n for n in ns] if side == "slow" else list(ns)

    def canonical(self):
        g = self.g
        members = [S for S in range(2 ** g) if self.pred(S)]
        inv = []
        for x in range(g):
            prof = [0] * (g + 1)
            for S in members:
                if S >> x & 1:
                    prof[_popcount(S)] += 1
            inv.append(tuple(prof))
        classes = {}
        for x in range(g):
            classes.setdefault(inv[x], []).append(x)
        keys = sorted(classes)
        total = math.prod(math.factorial(len(classes[k])) for k in keys)
        if total > 5040:
            return "inv:" + short_hash([g, sorted(inv), len(members)], 16)
        best = None
        for combo in itertools.product(*[itertools.permutations(classes[k]) for k in keys]):
            order = [x for part in combo for x in part]  # new position i <- old element order[i]
            pos = {old: i for i, old in enumerate(order)}
            mapped = tuple(sorted(sum(1 << pos[x] for x in range(g) if S >> x & 1) for S in members))
            if best is None or mapped < best:
                best = mapped
        return "exact:" + short_hash([g, best], 16)

    def cluster(self):
        a = self._an
        return f"greedy:{self.family}:{'matroid' if a['matroid'] else 'non-matroid'}"
