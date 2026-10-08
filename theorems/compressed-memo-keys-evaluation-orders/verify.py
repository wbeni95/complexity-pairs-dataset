#!/usr/bin/env python3
"""Verifier for theorems/compressed-memo-keys-evaluation-orders (see README.md in this folder).

The proofs are in the README. This script checks every finite fact the proofs use, and it is the checker of the
computer-assisted part: it reads the public certificate file certificates.txt.gz (next to this script) and checks
every certificate in it together with the coverage claims. Standard library only; deterministic; offline.

Usage (from the repository root):
    python theorems/compressed-memo-keys-evaluation-orders/verify.py               # all checks, under half a minute
    python theorems/compressed-memo-keys-evaluation-orders/verify.py --regenerate  # also re-runs the deterministic
                                                                                   # certificate search and requires
                                                                                   # the identical file content
    python theorems/compressed-memo-keys-evaluation-orders/verify.py --write FILE  # write regenerated certificates

The family F (README, "Setting"): ordered move lists (d_i, f_i), k = 2 or 3 moves, d_i in 1..4, f_i in {0, 1};
delta in {0, 1, 2}; combine sum (mod P = 1 000 003), min or max; coefficients c_i in 1..9; data in {0..9}^17,
D[m] = data[m mod 17]; base b = max d_i. Leaves (m < b): V(m, p) = D[m] + delta p. Sum: V(m, p) = D[m](1 + delta p)
+ sum_i c_i V(m - d_i, p xor f_i) mod P. Min/max: V(m, p) = opt_i [V(m - d_i, p xor f_i) + w_i(m)(1 + delta p)],
w_i(m) = (c_i D[m] + i) mod 10.

Parts (one line per check):
  Setting: the modulus P = 1 000 003 is prime (trial division).
  Theorem 1 (value-constancy on fibres => exact for every supported assignment): seeded random instances;
      the stack lemma (explicit stack = per-node DFS, supported) and the error lemma (sum-mode error formula) on
      random instances.
  Proposition 2 (lattice criterion) on all 156 move multisets.
  Proposition 3 (exactness for one fixed order does not imply PF or VF): the counterexample, all data.
  Theorem 4 (model G): the counterexample, exact under all 6 global orders for all data (affine
      evaluation), broken by a model-D order; and Remark (model S is larger than model D).
  Theorem 5 (model S, sum mode): the finite fact N(m*) < P, the depth closure, the domination lemma on a
      range, and the construction of the proof run on all instances with n <= b + 24.
  Theorem 6 (min/max, model D): every cycle certificate, the class coverage, every small-n certificate,
      every coefficient-vector certificate of the residual instances, and the coverage of all instances.
  Theorem 7 (sum, model D): every large-n pair certificate (with its translation threshold) and every small-n
      pair certificate, coverage, relabelling, and end-to-end mod-P evaluations on a sample.
Exit code 0 only if every check passes.
"""
import argparse
import gzip
import hashlib
import itertools
import math
import sys
import time
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
CERT_FILE = HERE / "certificates.txt.gz"
CERT_SHA256 = "f7e71f2bd218a1099cac6caa257c176fb4a1702337847a3f1101a219344a2172"  # of the decompressed text
P = 1_000_003
DLEN = 17
EXTRA = 80          # direct checks for b <= n <= b + EXTRA
NCLS = 24           # residue classes of n used by the cycle certificates (2e divides 24 for e = 1..4)
MOVES = [(d, f) for d in (1, 2, 3, 4) for f in (0, 1)]
PERMS = {2: [(0, 1), (1, 0)], 3: list(itertools.permutations(range(3)))}
MASK = (1 << 64) - 1
FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""), flush=True)
    if not ok:
        FAILURES.append(label)
    return ok


class XorShift:
    """xorshift64 pseudo-random generator (independent of the Python version)."""

    def __init__(self, seed):
        self.s = (seed & MASK) or 1

    def next(self):
        s = self.s
        s ^= (s << 13) & MASK
        s ^= s >> 7
        s ^= (s << 17) & MASK
        self.s = s
        return s

    def below(self, m):
        return self.next() % m


def seed_of(*parts):
    return zlib.crc32("|".join(map(str, parts)).encode()) * 2654435761 + 1


# ------------------------------------------------------------------------------------------------ the family
def ordered_lists():
    return [tuple(t) for k in (2, 3) for t in itertools.product(MOVES, repeat=k)]


def multisets():
    return [s for s in ordered_lists() if all(s[i - 1] <= s[i] for i in range(1, len(s)))]


def name(st):
    return ",".join(f"{d}{f}" for d, f in st)


def parse_name(s):
    return tuple((int(x[0]), int(x[1])) for x in s.split(","))


def base(st):
    return max(d for d, _ in st)


def gcd_of(st):
    g = 0
    for d, _ in st:
        g = math.gcd(g, d)
    return g


def criterion(st):
    """Lattice criterion: f_i = c d_i / g (mod 2) for all i, for one c in {0, 1}."""
    g = gcd_of(st)
    return any(all(f == (c * (d // g)) % 2 for d, f in st) for c in (0, 1))


def flag_sets(st, n):
    """fl[m]: bit 0 if (m, 0) is reachable from (n, 0), bit 1 if (m, 1) is; 0 if m is not in M(n)."""
    b = base(st)
    fl = [0] * (n + 1)
    fl[n] = 1
    for m in range(n, b - 1, -1):
        x = fl[m]
        if x:
            sw = ((x & 1) << 1) | (x >> 1)
            for d, f in st:
                fl[m - d] |= sw if f else x
    return fl


def is_pf(fl):
    return 3 not in fl


def paths(k, maxlen=3):
    out = [()]
    for length in range(1, maxlen + 1):
        out += list(itertools.product(range(k), repeat=length))
    return out


def candidates(k):
    return [(p, r) for p in paths(k) for r in PERMS[k]]


def pstr(p):
    return "".join(map(str, p)) or "-"


def pparse(s):
    return () if s == "-" else tuple(int(c) for c in s)


def all_cases():
    return [(st, delta, comb) for st in ordered_lists() if not criterion(st)
            for delta in (1, 2) for comb in ("min", "max")]


# ------------------------------------------------------------------------------------------------ orders
def dfs_assign(st, n, path, rule):
    """Flags induced by the order O(path, rule): a recursive DFS from (n, 0) that marks a node at its first visit
    and skips marked nodes; the path nodes x_0 = n, x_t = x_(t-1) - d_(path[t-1]) visit their path child first and
    then the others in the order `rule`; every other node visits its children in the order `rule`. -1 = not in M(n)."""
    b = base(st)
    pathpos = {}
    x = n
    for i in path:
        if x < b:
            break
        pathpos[x] = i
        x -= st[i][0]
    asg = [-1] * (n + 1)
    asg[n] = 0
    if n < b:
        return asg
    rule = tuple(rule)
    orders = {}

    def order(m):
        i = pathpos.get(m)
        if i is None:
            return rule
        if m not in orders:
            orders[m] = (i,) + tuple(j for j in rule if j != i)
        return orders[m]
    stack = [[n, 0, order(n), 0]]
    while stack:
        fr = stack[-1]
        m, p, od, pos = fr
        if pos == len(od):
            stack.pop()
            continue
        fr[3] = pos + 1
        i = od[pos]
        c = m - st[i][0]
        if asg[c] >= 0:
            continue
        q = p ^ st[i][1]
        asg[c] = q
        if c >= b:
            stack.append([c, q, order(c), 0])
    return asg


def dfs_table(st, n, table):
    """Flags induced by per-node visit orders: node m visits its children in the order PERMS[k][table[m]]."""
    b = base(st)
    pk = PERMS[len(st)]
    asg = [-1] * (n + 1)
    asg[n] = 0
    if n < b:
        return asg
    stack = [[n, 0, 0]]
    while stack:
        fr = stack[-1]
        m, p, pos = fr
        if pos == len(st):
            stack.pop()
            continue
        fr[2] = pos + 1
        i = pk[table[m]][pos]
        c = m - st[i][0]
        if asg[c] >= 0:
            continue
        q = p ^ st[i][1]
        asg[c] = q
        if c >= b:
            stack.append([c, q, 0])
    return asg


def explicit_stack(st, n, push_order):
    """The explicit-stack procedure of the stack lemma: stack of (m, p); when the top entry's node is not yet
    evaluated and is internal, push its children that are not yet evaluated, in the order push_order(m) (a
    permutation of the move indices, possibly repeated targets); evaluate (fix the flag of) m when all its children
    are evaluated.
    Returns the flags with which the nodes are evaluated."""
    b = base(st)
    flag = [-1] * (n + 1)
    stack = [(n, 0)]
    while stack:
        m, p = stack[-1]
        if flag[m] >= 0:
            stack.pop()
            continue
        if m < b:
            flag[m] = p
            stack.pop()
            continue
        missing = [(m - st[i][0], p ^ st[i][1]) for i in push_order(m) if flag[m - st[i][0]] < 0]
        if missing:
            stack.extend(missing)
            continue
        flag[m] = p
        stack.pop()
    return flag


# ------------------------------------------------------------------------------------------------ evaluation
def zero_weights(k):
    return [tuple(range(k))] * DLEN, [0] * DLEN


def weights(st, coef, data):
    k = len(st)
    return [tuple((coef[i] * data[r] + i) % 10 for i in range(k)) for r in range(DLEN)], list(data)


def truth_mm(st, n, delta, is_min, W, L):
    b = base(st)
    opt = min if is_min else max
    k = len(st)
    V0 = [0] * (n + 1)
    V1 = [0] * (n + 1)
    for m in range(n + 1):
        r = m % DLEN
        if m < b:
            V0[m] = L[r]
            V1[m] = L[r] + delta
        else:
            w = W[r]
            V0[m] = opt([(V1 if st[i][1] else V0)[m - st[i][0]] + w[i] for i in range(k)])
            V1[m] = opt([(V0 if st[i][1] else V1)[m - st[i][0]] + w[i] * (1 + delta) for i in range(k)])
    return V0, V1


def comp_mm(st, n, delta, is_min, W, L, asg):
    b = base(st)
    opt = min if is_min else max
    k = len(st)
    mm = [0] * (n + 1)
    for m in range(n + 1):
        p = asg[m]
        if p < 0:
            continue
        r = m % DLEN
        if m < b:
            mm[m] = L[r] + delta * p
        else:
            w = W[r]
            s = 1 + delta * p
            mm[m] = opt([mm[m - st[i][0]] + w[i] * s for i in range(k)])
    return mm[n]


def truth_sum(st, n, delta, coef, data):
    b = base(st)
    V0 = [0] * (n + 1)
    V1 = [0] * (n + 1)
    for m in range(n + 1):
        D = data[m % DLEN]
        if m < b:
            V0[m], V1[m] = D, D + delta
        else:
            V0[m] = (D + sum(coef[i] * (V1 if st[i][1] else V0)[m - st[i][0]] for i in range(len(st)))) % P
            V1[m] = (D * (1 + delta) + sum(coef[i] * (V0 if st[i][1] else V1)[m - st[i][0]]
                                           for i in range(len(st)))) % P
    return V0, V1


def comp_sum(st, n, delta, coef, data, asg):
    b = base(st)
    mm = [0] * (n + 1)
    for m in range(n + 1):
        p = asg[m]
        if p < 0:
            continue
        D = data[m % DLEN]
        if m < b:
            mm[m] = D + delta * p
        else:
            mm[m] = (D * (1 + delta * p) + sum(coef[i] * mm[m - st[i][0]] for i in range(len(st)))) % P
    return mm[n]


def aff_add(x, y, c=1):
    return tuple((a + c * b) % P for a, b in zip(x, y))


def unit_aff(r, scale):
    v = [0] * (DLEN + 1)
    v[1 + r] = scale % P
    return tuple(v)


def const_aff(c):
    return tuple([c % P] + [0] * DLEN)


def truth_sum_aff(st, n, delta, coef):
    """Sum-mode truth as affine forms (constant, coefficient of data[0..16]) mod P."""
    b = base(st)
    V = [[None, None] for _ in range(n + 1)]
    for m in range(n + 1):
        r = m % DLEN
        for p in (0, 1):
            if m < b:
                V[m][p] = aff_add(unit_aff(r, 1), const_aff(delta * p))
            else:
                acc = unit_aff(r, 1 + delta * p)
                for i, (d, f) in enumerate(st):
                    acc = aff_add(acc, V[m - d][p ^ f], coef[i])
                V[m][p] = acc
    return V


def comp_sum_aff(st, n, delta, coef, asg):
    b = base(st)
    mm = [None] * (n + 1)
    for m in range(n + 1):
        p = asg[m]
        if p < 0:
            continue
        r = m % DLEN
        if m < b:
            mm[m] = aff_add(unit_aff(r, 1), const_aff(delta * p))
        else:
            acc = unit_aff(r, 1 + delta * p)
            for i, (d, _) in enumerate(st):
                acc = aff_add(acc, mm[m - d], coef[i])
            mm[m] = acc
    return mm[n]


def path_weights(st, n, fl, coef):
    """N_q[m]: sum over call-tree paths from (n, 0) to (m, q) of the product of the coefficients used (exact)."""
    b = base(st)
    N = [[0, 0] for _ in range(n + 1)]
    N[n][0] = 1
    for m in range(n, b - 1, -1):
        if not fl[m]:
            continue
        for i, (d, f) in enumerate(st):
            for q in (0, 1):
                if N[m][q]:
                    N[m - d][q ^ f] += coef[i] * N[m][q]
    return N


def supported(st, n, asg):
    """p_n = 0 and every other m in M(n) has a parent m' (internal, in M(n)) with p_m = p_m' xor f_i."""
    b = base(st)
    if asg[n] != 0:
        return False
    for m in range(n):
        if asg[m] < 0:
            continue
        if not any(m + d <= n and m + d >= b and asg[m + d] >= 0 and asg[m] == asg[m + d] ^ f for d, f in st):
            return False
    return True


def requested(st, n, asg, m):
    b = base(st)
    return {asg[m + d] ^ f for d, f in st if b <= m + d <= n and asg[m + d] >= 0}


# ----------------------------------------------------------------------------- Theorem 1, Propositions 2-3, Theorem 4
def part_theorem1():
    rng = XorShift(seed_of("theorem1"))
    lists = ordered_lists()
    n_inst = n_vf = n_exact_vf = n_assign = 0
    bad = 0
    for _ in range(3000):
        st = lists[rng.below(len(lists))]
        k = len(st)
        delta = rng.below(3)
        comb = ("sum", "min", "max")[rng.below(3)]
        coef = [1 + rng.below(9) for _ in range(k)]
        data = [rng.below(10) for _ in range(DLEN)]
        b = base(st)
        n = b + rng.below(15)
        fl = flag_sets(st, n)
        if comb == "sum":
            V0, V1 = truth_sum(st, n, delta, coef, data)
        else:
            W, L = weights(st, coef, data)
            V0, V1 = truth_mm(st, n, delta, comb == "min", W, L)
        vf = all(V0[m] == V1[m] for m in range(n + 1) if fl[m] == 3)
        n_inst += 1
        for _ in range(4):
            asg = [-1] * (n + 1)
            asg[n] = 0
            for m in range(n - 1, -1, -1):
                if fl[m]:
                    req = sorted(requested(st, n, asg, m))
                    asg[m] = req[rng.below(len(req))]
            if comb == "sum":
                val = comp_sum(st, n, delta, coef, data, asg)
            else:
                val = comp_mm(st, n, delta, comb == "min", W, L, asg)
            n_assign += 1
            if vf:
                n_vf += 1
                n_exact_vf += val == V0[n]
                bad += val != V0[n] or not supported(st, n, asg)
    check("Theorem 1: every random supported assignment on an instance with VF is exact",
          bad == 0 and n_exact_vf == n_vf, f"{n_inst} instances, {n_assign} assignments, {n_vf} with VF, "
          f"{n_exact_vf} exact")
    # delta = 0 => V(m, 0) = V(m, 1) for every reachable m: all ordered lists, n <= b + 10, all modes, seeded data
    ok, cnt = True, 0
    for st in ordered_lists():
        b = base(st)
        k = len(st)
        for n in range(b, b + 11):
            fl = flag_sets(st, n)
            for comb in ("sum", "min", "max"):
                for _ in range(3):
                    coef = [1 + rng.below(9) for _ in range(k)]
                    data = [rng.below(10) for _ in range(DLEN)]
                    if comb == "sum":
                        V0, V1 = truth_sum(st, n, 0, coef, data)
                    else:
                        V0, V1 = truth_mm(st, n, 0, comb == "min", *weights(st, coef, data))
                    ok &= all(V0[m] == V1[m] for m in range(n + 1) if fl[m])
                    cnt += 1
    check("Theorem 1: delta = 0 gives V(m, 0) = V(m, 1) for every m in M(n) (all 576 ordered lists, b <= n <= b + 10, "
          "sum, min and max, 3 seeded (coefficient, data) pairs each)", ok, f"{cnt} instances")


def part_lemmas():
    """Stack lemma (explicit stack = per-node DFS; supported; result = memo_p) and error lemma, seeded instances."""
    rng = XorShift(seed_of("lemmas"))
    lists = ordered_lists()
    bad0 = badp2 = 0
    n_inst = 0
    for _ in range(2000):
        st = lists[rng.below(len(lists))]
        k = len(st)
        b = base(st)
        n = b + rng.below(25)
        table = [rng.below(len(PERMS[k])) for _ in range(n + 1)]
        # explicit stack: push order at node m = reverse of the visit order PERMS[k][table[m]]
        flags = explicit_stack(st, n, lambda m: tuple(reversed(PERMS[k][table[m]])))
        asg = dfs_table(st, n, table)
        delta = 1 + rng.below(2)
        coef = [1 + rng.below(9) for _ in range(k)]
        data = [rng.below(10) for _ in range(DLEN)]
        fl = flag_sets(st, n)
        n_inst += 1
        bad0 += flags != asg or not supported(st, n, asg) or any((asg[m] >= 0) != bool(fl[m]) for m in range(n + 1))
        # the error lemma for the induced assignment and for an arbitrary (unsupported) assignment
        V0, _ = truth_sum(st, n, delta, coef, data)
        Nq = path_weights(st, n, fl, coef)
        for p in (asg, [(-1 if not fl[m] else rng.below(2)) for m in range(n + 1)]):
            lhs = (comp_sum(st, n, delta, coef, data, p) - V0[n]) % P
            rhs = delta * sum((data[m % DLEN] if m >= b else 1) * (p[m] * sum(Nq[m]) - Nq[m][1])
                              for m in range(n + 1) if fl[m]) % P
            badp2 += lhs != rhs % P
    check("Stack lemma: the explicit-stack procedure with push order = reverse visit order induces the same flags as "
          "the per-node DFS, every node of M(n) is evaluated, and the assignment is supported (2000 seeded instances, "
          "n <= b + 24)", bad0 == 0, f"{n_inst} instances")
    check("Error lemma: memo_p[n] - V(n, 0) equals the formula mod P, for the induced assignment and for a random "
          "assignment of the same instances", badp2 == 0, f"{2 * n_inst} assignments")


def part_criterion():
    bad_a = bad_b = 0
    cnt_a = cnt_b = 0
    maxD = 0
    for st in multisets():
        b = base(st)
        if criterion(st):
            bad_a += sum(not is_pf(flag_sets(st, n)) for n in range(b, b + 61))
            cnt_a += 61
            continue
        k = len(st)
        best = None
        for z in itertools.product(range(-12, 13), repeat=k):
            if any(z) and sum(z[i] * st[i][0] for i in range(k)) == 0 and sum(z[i] * st[i][1] for i in range(k)) % 2:
                D = sum(z[i] * st[i][0] for i in range(k) if z[i] > 0)
                if best is None or D < best:
                    best = D
        if best is None:
            bad_b += 1
            continue
        maxD = max(maxD, best)
        bad_b += sum(is_pf(flag_sets(st, n)) for n in range(b + best, b + 61))
        cnt_b += 61 - best
    check("Proposition 2(a): criterion => PF at every n in [b, b + 60] (all multisets satisfying it)", bad_a == 0,
          f"{cnt_a} (multiset, n) pairs")
    check("Proposition 2(b): criterion fails => a vector z with sum z_i d_i = 0, sum z_i f_i odd exists, and PF "
          "fails at every n in [b + D, b + 60], D = sum of z_i d_i over z_i > 0 (all multisets failing it)",
          bad_b == 0,
          f"largest D needed: {maxD}; z searched in [-12, 12]^k; {cnt_b} (multiset, n) pairs with PF failing")
    nfail = sum(1 for s in multisets() if not criterion(s))
    nord = sum(1 for s in ordered_lists() if not criterion(s))
    check("Proposition 2, counts: 156 multisets (96 fail the criterion); 576 ordered lists (416 fail it)",
          (len(multisets()), nfail, len(ordered_lists()), nord) == (156, 96, 576, 416))


def part_onlyif():
    st, delta, coef, n = ((1, 0), (1, 1)), 2, (4, 4), 1
    fl = flag_sets(st, n)
    good = bad = 0
    for d0, d1 in itertools.product(range(10), repeat=2):
        data = [d0, d1] + [0] * (DLEN - 2)
        W, L = weights(st, coef, data)
        V0, V1 = truth_mm(st, n, delta, False, W, L)
        e1 = comp_mm(st, n, delta, False, W, L, [1, 0]) - V0[n]
        e0 = comp_mm(st, n, delta, False, W, L, [0, 0]) - V0[n]
        good += e1 == 0 and V0[0] != V1[0]
        bad += e0 == -2
    stack_flag = explicit_stack(st, n, lambda m: (0, 1))
    check("Proposition 3: moves (1,0),(1,1), delta 2, max, c = (4,4), n = 1: node 0 is ambiguous, VF fails for "
          "every data vector, the order that evaluates node 0 with flag 1 is exact for every data vector, and the "
          "order with flag 0 is off by -2 for every data vector", fl[0] == 3 and good == 100 and bad == 100
          and stack_flag[0] == 1, f"{good}/100, {bad}/100; push in move order evaluates node 0 with flag "
          f"{stack_flag[0]}")


def part_model_g():
    st, delta, coef, n = ((1, 1), (3, 0), (3, 1)), 1, (1, 1, 1), 4
    fl = flag_sets(st, n)
    T = truth_sum_aff(st, n, delta, coef)
    exact_global = []
    for R in PERMS[3]:
        asg = dfs_assign(st, n, (), R)
        flag2 = explicit_stack(st, n, lambda m, R=R: tuple(reversed(R)))
        exact_global.append(comp_sum_aff(st, n, delta, coef, asg) == T[n][0] and flag2 == asg)
    errs = set()
    for table in itertools.product(range(6), repeat=n + 1):
        asg = dfs_table(st, n, table)
        e = aff_add(comp_sum_aff(st, n, delta, coef, asg), T[n][0], -1)
        errs.add((tuple(asg), e))
    nonzero = [(a, e) for a, e in errs if any(e)]
    consts = sorted({e[0] if e[0] < P // 2 else e[0] - P for _, e in nonzero})
    check("Theorem 4: moves (1,1),(3,0),(3,1), delta 1, sum, c = (1,1,1), n = 4: PF fails, and each of the 6 "
          "global orders is exact for every data vector (affine evaluation mod P; the explicit stack with the reversed "
          "push order gives the same flags)", not is_pf(fl) and all(exact_global))
    check("Theorem 4 ... while some per-node visit order (model D) is wrong for every data vector (constant error)",
          bool(nonzero) and all(not any(e[1:]) for _, e in nonzero), f"{len(errs)} D-assignments, errors {consts}")
    # model S is larger than model D
    st2, n2 = ((1, 0), (2, 0), (2, 1)), 4
    target = [0, 0, 1, 0, 0]  # flags of nodes 0..4
    realised = {tuple(dfs_table(st2, n2, t)) for t in itertools.product(range(6), repeat=n2 + 1)}
    check("Remark (model S is larger than model D): for moves (1,0),(2,0),(2,1), n = 4, the assignment "
          "{4:0, 3:0, 2:1, 1:0, 0:0} is supported but no per-node visit order realises it (all 6^5 tables)",
          supported(st2, n2, target) and tuple(target) not in realised, f"{len(realised)} distinct D-assignments")


# ------------------------------------------------------------------------------------------------ Theorem 5
def reach_avoiding(st, n, fl, avoid):
    b = base(st)
    seen = [False] * (n + 1)
    seen[n] = True
    for m in range(n, b - 1, -1):
        if seen[m] and m != avoid:
            for d, _ in st:
                seen[m - d] = True
    seen[avoid] = False
    return seen


def part_theorem5():
    t0 = time.time()
    best = (0, None)
    bad_depth = bad_const = 0
    n_ms = n_const = 0
    for st in multisets():
        if criterion(st):
            continue
        n_ms += 1
        b = base(st)
        ref = None
        for n in range(b, b + 61):
            fl = flag_sets(st, n)
            amb = [m for m in range(n + 1) if fl[m] == 3]
            if not amb:
                if n >= b + 12:
                    bad_depth += 1
                continue
            ms = max(amb)
            N = path_weights(st, n, fl, [9] * len(st))
            if n <= b + 12 and sum(N[ms]) > best[0]:
                best = (sum(N[ms]), f"{name(st)}, n = {n}, m* = {ms}")
            if n == b + 12 and n - ms > 12:
                bad_depth += 1
            if n >= b + 12:
                key = (n - ms, N[ms][0], N[ms][1])
                if ref is None:
                    ref = key
                bad_const += key != ref
                n_const += 1
    check("Theorem 5 finite fact: max of N(m*) at coefficients 9 over the 96 failing multisets and b <= n <= b + 12 is "
          "105705 < P", best[0] == 105705 and best[0] < P, best[1])
    check("Theorem 5 closure: at n = b + 12 every failing multiset has an ambiguous node of depth <= 12 (and PF fails "
          "for every n in [b + 12, b + 60])", bad_depth == 0, f"{n_ms} multisets")
    check("Theorem 5 consistency of the depth-translation lemma: (depth of m*, N_0(m*), N_1(m*)) constant over n in "
          "[b + 12, b + 60]", bad_const == 0, f"{n_const} (multiset, n) pairs")
    # domination lemma
    viol = pairs = 0
    for st in multisets():
        if len({d for d, _ in st}) < 2:
            continue
        b = base(st)
        for n in range(b + 17, b + 31):
            fl = flag_sets(st, n)
            for m in range(n - 1, b, -1):
                seen = reach_avoiding(st, n, fl, m)
                for c in range(b, min(m, n - 16)):
                    if fl[c] and c <= n - 17:
                        pairs += 1
                        viol += not seen[c]
    check("Theorem 5 domination lemma: two distinct offsets, c >= b in M(n), n - c >= 17, c < m < n: a root path to c "
          "avoids m (all such multisets, b + 17 <= n <= b + 30)", viol == 0, f"{pairs} (c, m) pairs")
    # the construction of the proof
    n_inst = bad = 0
    for st in multisets():
        if criterion(st):
            continue
        b = base(st)
        k = len(st)
        for n in range(b, b + 25):
            fl = flag_sets(st, n)
            amb = [m for m in range(n + 1) if fl[m] == 3]
            if not amb:
                continue
            ms = max(amb)
            p0 = [-1] * (n + 1)
            p1 = [-1] * (n + 1)
            p0[n] = p1[n] = 0
            for m in range(n - 1, -1, -1):
                if not fl[m]:
                    continue
                if m == ms:
                    p0[m], p1[m] = 0, 1
                    continue
                r0, r1 = requested(st, n, p0, m), requested(st, n, p1, m)
                common = r0 & r1
                if common:
                    p0[m] = p1[m] = min(common)
                else:
                    p0[m], p1[m] = min(r0), min(r1)
            n_inst += 1
            Dset = [m for m in range(n + 1) if p0[m] >= 0 and p0[m] != p1[m]]
            seen = reach_avoiding(st, n, fl, ms)
            dom_ok = all(m == ms or (fl[m] and not seen[m]) for m in Dset)
            res_ok = ms < b or not any(m != ms and m >= b and m % DLEN == ms % DLEN for m in Dset)
            broke = True
            for coef in ([1] * k, [9] * k):
                for delta in (1, 2):
                    found = False
                    for data in ([0] * DLEN, [int(r == ms % DLEN) for r in range(DLEN)]):
                        V0, _ = truth_sum(st, n, delta, coef, data)
                        if (comp_sum(st, n, delta, coef, data, p0) != V0[n]
                                or comp_sum(st, n, delta, coef, data, p1) != V0[n]):
                            found = True
                            break
                    broke &= found
            bad += not (supported(st, n, p0) and supported(st, n, p1) and dom_ok and res_ok and broke)
    check("Theorem 5: the construction of the proof (all failing multisets, b <= n <= b + 24): both assignments "
          "supported, the differing set lies in {m*} and the nodes dominated by m*, no other internal differing node "
          "in the residue class of m*, and data 0 or the unit vector of m*'s residue breaks one of them (coefficients "
          "all 1 and all 9, delta 1 and 2)", bad == 0, f"{n_inst} instances, {time.time() - t0:.1f} s")


# ------------------------------------------------------------------------------------------------ Theorem 6 machinery
def semigroup(st, e, lim=400):
    sg = [False] * (lim + 1)
    sg[0] = True
    for s in range(1, lim + 1):
        sg[s] = any(s >= d and sg[s - d] for d, _ in st)
    g = gcd_of(st)
    F = max((s for s in range(lim + 1) if s % g == 0 and not sg[s]), default=-1)
    A = max(s for s in range(lim + 1) if sg[s] and (s < e or not sg[s - e]))
    return F, A


def cert_params(st, path, rule):
    b = base(st)
    e = st[rule[0]][0]
    per = 2 * e
    J = sum(st[i][0] for i in path)
    F, A = semigroup(st, e)
    M0 = b + A + 4
    K = J + F + 1
    N0 = max(K + M0 + per + 7, J + F + 4 + b)
    return b, e, per, J, F, A, M0, K, N0


def cycle_cert(st, delta, is_min, path, rule, cls, maxlev=3000):
    """Certificate theorem: a cycle certificate for the class n = cls (mod 2e), zero data, order O(path, rule)."""
    b, e, per, J, F, A, M0, K, N0 = cert_params(st, path, rule)
    k = len(st)
    out = {"ok": False, "N0": N0, "K": K}
    nrep = max(N0, 150) + 2 * per
    while nrep % per != cls % per:
        nrep += 1
    asg = dfs_assign(st, nrep, path, rule)
    asg2 = dfs_assign(st, nrep + per, path, rule)
    lim = nrep - K
    if not (all(asg[nrep - j] == asg2[nrep + per - j] for j in range(K))
            and all(asg[u] == asg2[u] for u in range(lim + 1))
            and all(asg[u] == asg[u + per] for u in range(M0, lim - per + 1))):
        out["why"] = "structure corollary consistency"
        return out
    top = [asg[nrep - j] for j in range(K)]

    def Ac(u):
        if u > lim:
            u -= ((u - lim + per - 1) // per) * per
        return asg[u]
    opt = min if is_min else max
    d = [x for x, _ in st]
    f = [y for _, y in st]
    mu, V0, V1 = [], [], []
    phase = (cls - K) % per
    start = N0 - K
    seen = {}
    m1 = m2 = None
    for u in range(maxlev):
        a = Ac(u)
        if a < 0:
            mu.append(None)
            V0.append(None)
            V1.append(None)
        elif u < b:
            mu.append(delta * a)
            V0.append(0)
            V1.append(delta)
        else:
            s = 1 + delta * a
            mu.append(opt([mu[u - d[i]] + i * s for i in range(k)]))
            V0.append(opt([(V1 if f[i] else V0)[u - d[i]] + i for i in range(k)]))
            V1.append(opt([(V0 if f[i] else V1)[u - d[i]] + i * (1 + delta) for i in range(k)]))
        if u >= start and u % per == phase:
            rs = [x for x in range(u - b + 1, u + 1) if mu[x] is not None]
            r = rs[0]
            key = tuple((x - u, mu[x] - mu[r], V0[x] - V0[r], V1[x] - V0[r]) for x in rs)
            if key in seen:
                m1, m2 = seen[key], u
                break
            seen[key] = u
    if m1 is None:
        out["why"] = "no cycle"
        return out

    def offset(m):
        r = [x for x in range(m - b + 1, m + 1) if mu[x] is not None][0]
        return V0[r] - mu[r]

    def err_at(m):
        n = m + K
        mm = {x: mu[x] for x in range(m - b + 1, m + 1)}
        v0 = {x: V0[x] for x in range(m - b + 1, m + 1)}
        v1 = {x: V1[x] for x in range(m - b + 1, m + 1)}
        for node in range(m + 1, n + 1):
            a = top[n - node]
            if a < 0:
                mm[node] = v0[node] = v1[node] = None
                continue
            s = 1 + delta * a
            mm[node] = opt([mm[node - d[i]] + i * s for i in range(k)])
            v0[node] = opt([(v1 if f[i] else v0)[node - d[i]] + i for i in range(k)])
            v1[node] = opt([(v0 if f[i] else v1)[node - d[i]] + i * (1 + delta) for i in range(k)])
        return mm[n] - v0[n]
    drift = offset(m2) - offset(m1)
    T = m2 - m1
    exc = []
    m = start
    while m % per != phase:
        m += 1
    while m < m2:
        er = err_at(m)
        if m < m1:
            if er == 0:
                exc.append(m + K)
        elif drift == 0:
            if er == 0:
                out["why"] = "zero error on the cycle"
                return out
        elif er % drift == 0 and er // drift >= 0:
            exc.append(m + K + (er // drift) * T)
        m += per

    def predicted(n):
        ml = n - K
        if ml < m2:
            return err_at(ml)
        t = (ml - m1) // T
        return err_at(ml - t * T) - t * drift
    out.update(m1=m1, m2=m2, drift=drift, T=T, exc=sorted(exc), predicted=predicted, per=per)
    out["ok"] = N0 <= b + EXTRA + 1 and all(x <= b + EXTRA for x in exc)
    if not out["ok"]:
        out["why"] = "bounds"
    return out


def residual_tables(st, n, key):
    """Visit-order tables tried for a residual instance: the k! constant ones, then 300 seeded random ones,
    deduplicated by the induced assignment."""
    k = len(st)
    npk = len(PERMS[k])
    rng = XorShift(seed_of("tables", *key, n))
    tabs, asgs, seen = [], [], set()
    for t in [[c] * (n + 1) for c in range(npk)] + [[rng.below(npk) for _ in range(n + 1)] for _ in range(300)]:
        a = dfs_table(st, n, t)
        if tuple(a) not in seen:
            seen.add(tuple(a))
            tabs.append(t)
            asgs.append(a)
    return tabs, asgs, rng


def structured_data(st, delta, is_min, n, coef, asgs, rng, maxpaths=5000, trials=12):
    """Data making one root-to-leaf path extreme and the rest quiet, with perturbations (generation only)."""
    k = len(st)
    b = base(st)

    def wv(dv, i):
        return (coef[i] * dv + i) % 10
    best = [max(range(10), key=lambda dv: (-wv(dv, i) if is_min else wv(dv, i))) for i in range(k)]
    quiet = min(range(10), key=lambda dv: (-min(wv(dv, i) for i in range(k)) if is_min
                                           else max(wv(dv, i) for i in range(k))))
    pths, stack = [], [(n, ())]
    while stack and len(pths) < maxpaths:
        m, pth = stack.pop()
        if m < b:
            pths.append(pth + ((m, -1),))
            continue
        for i in range(k):
            stack.append((m - st[i][0], pth + ((m, i),)))
    for pth in pths:
        for trial in range(trials):
            data = [quiet] * DLEN
            if trial > 0:
                for r in range(DLEN):
                    if rng.below(3) == 0:
                        data[r] = rng.below(10)
            for r in range(min(b, DLEN)):
                data[r] = 9 if is_min else 0
            for m, i in reversed(pth):
                data[m % DLEN] = (0 if is_min else 9) if i < 0 else best[i]
            W, L = weights(st, coef, data)
            tv = truth_mm(st, n, delta, is_min, W, L)[0][n]
            for ai, a in enumerate(asgs):
                if comp_mm(st, n, delta, is_min, W, L, a) != tv:
                    return data, ai
    return None


ID_CHARS = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"


# ------------------------------------------------------------------------------------------------ Theorem 7 machinery
def isolated(st, a0, a1, N):
    """An isolated differing node c (pair lemma) with 1 <= N(c) < P; the one with the smallest N(c), else None."""
    b = base(st)
    D = [m for m in range(len(a0)) if a0[m] >= 0 and a0[m] != a1[m]]
    best = None
    for c in D:
        if c >= b:
            alone = all(x == c or x < b or x % DLEN != c % DLEN for x in D)
        else:
            alone = all(x == c or x >= b for x in D)
        if alone and 0 < N[c] < P and (best is None or N[c] < best[1]):
            best = (c, N[c])
    return best


def n9(st, n):
    fl = flag_sets(st, n)
    return [sum(x) for x in path_weights(st, n, fl, [9] * len(st))], fl


def sum_threshold(st, p0, rule):
    F, _ = semigroup(st, st[rule[0]][0])
    return sum(st[i][0] for i in p0) + F + 4 + base(st)


def sum_pattern(st, n, p0, p1, rule):
    N, _ = n9(st, n)
    a0, a1 = dfs_assign(st, n, p0, rule), dfs_assign(st, n, p1, rule)
    iso = isolated(st, a0, a1, N)
    D = tuple(n - m for m in range(n + 1) if a0[m] >= 0 and a0[m] != a1[m])
    return iso, D, a0, a1


# ------------------------------------------------------------------------------------------------ generation
def generate(log=print):
    lines = ["# Certificates for theorems/compressed-memo-keys-evaluation-orders (format: see README.md).",
             "# C list delta comb path rule class | Z list delta comb tokens(n = b..b+80) | T list delta comb n id "
             "table | R list delta comb n tokens(coefficient vectors in lexicographic order) | X list delta comb n "
             "coef data id | S multiset path0 path1 rule | s multiset n path0:rule0 path1:rule1"]
    t0 = time.time()
    resid = []
    for st, delta, comb in all_cases():
        is_min = comb == "min"
        cands = candidates(len(st))
        covered = [False] * NCLS
        for p, r in cands:
            if all(covered):
                break
            per = 2 * st[r[0]][0]
            for cls in range(per):
                if all(covered[c] for c in range(NCLS) if c % per == cls):
                    continue
                if cycle_cert(st, delta, is_min, p, r, cls)["ok"]:
                    for c in range(NCLS):
                        if c % per == cls:
                            covered[c] = True
                    lines.append(f"C\t{name(st)}\t{delta}\t{comb}\t{pstr(p)}\t{pstr(r)}\t{cls}")
    log(f"   generated cycle certificates ({time.time() - t0:.1f} s)")
    t0 = time.time()
    W0 = {k: zero_weights(k) for k in (2, 3)}
    for st, delta, comb in all_cases():
        is_min = comb == "min"
        k = len(st)
        b = base(st)
        cands = candidates(k)
        toks = []
        for n in range(b, b + EXTRA + 1):
            if is_pf(flag_sets(st, n)):
                toks.append(".")
                continue
            W, L = W0[k]
            tv = truth_mm(st, n, delta, is_min, W, L)[0][n]
            hit = next(((p, r) for p, r in cands
                        if comp_mm(st, n, delta, is_min, W, L, dfs_assign(st, n, p, r)) != tv), None)
            if hit is None:
                toks.append("*")
                resid.append((st, delta, comb, n))
            else:
                toks.append(f"{pstr(hit[0])}:{pstr(hit[1])}")
        lines.append(f"Z\t{name(st)}\t{delta}\t{comb}\t{' '.join(toks)}")
    log(f"   generated small-n zero-data certificates; {len(resid)} residual instances ({time.time() - t0:.1f} s)")
    t0 = time.time()
    for st, delta, comb, n in resid:
        is_min = comb == "min"
        k = len(st)
        key = (name(st), delta, comb)
        tabs, asgs, rng = residual_tables(st, n, key)
        cache = {}
        toks, xs, used = [], [], {}

        def tid(ai):
            if ai not in used:
                used[ai] = len(used)
            return ID_CHARS[used[ai]]
        for coef in itertools.product(range(1, 10), repeat=k):
            hit = None
            for v in range(10):
                wt = tuple((coef[i] * v + i) % 10 for i in range(k))
                if (v, wt) not in cache:
                    W, L = [wt] * DLEN, [v] * DLEN
                    tv = truth_mm(st, n, delta, is_min, W, L)[0][n]
                    cache[(v, wt)] = next((ai for ai, a in enumerate(asgs)
                                           if comp_mm(st, n, delta, is_min, W, L, a) != tv), None)
                if cache[(v, wt)] is not None:
                    hit = (v, cache[(v, wt)])
                    break
            if hit is not None:
                toks.append(f"{hit[0]}{tid(hit[1])}")
                continue
            sd = structured_data(st, delta, is_min, n, coef, asgs, rng)
            if sd is None:
                toks.append("??")
                continue
            data, ai = sd
            toks.append(f"x{tid(ai)}")
            xs.append(f"X\t{key[0]}\t{delta}\t{comb}\t{n}\t{''.join(map(str, coef))}\t{''.join(map(str, data))}\t"
                      f"{tid(ai)}")
        for ai, j in sorted(used.items(), key=lambda t: t[1]):
            lines.append(f"T\t{key[0]}\t{delta}\t{comb}\t{n}\t{ID_CHARS[j]}\t{''.join(map(str, tabs[ai]))}")
        lines.append(f"R\t{key[0]}\t{delta}\t{comb}\t{n}\t{''.join(toks)}")
        lines.extend(xs)
    log(f"   generated residual certificates ({time.time() - t0:.1f} s)")
    t0 = time.time()
    for st in multisets():
        if criterion(st):
            continue
        k = len(st)
        b = base(st)
        ps = paths(k)
        found = None
        for R in PERMS[k]:
            for i0, p0 in enumerate(ps):
                for p1 in ps[i0 + 1:]:
                    if (sum(st[i][0] for i in p0) != sum(st[i][0] for i in p1)
                            or sum(st[i][1] for i in p0) % 2 != sum(st[i][1] for i in p1) % 2):
                        continue
                    nT = sum_threshold(st, p0, R)
                    if nT <= b + EXTRA + 1 and sum_pattern(st, nT, p0, p1, R)[0] is not None:
                        found = (p0, p1, R)
                        break
                if found:
                    break
            if found:
                break
        if found:
            lines.append(f"S\t{name(st)}\t{pstr(found[0])}\t{pstr(found[1])}\t{pstr(found[2])}")
        cands = candidates(k)
        for n in range(b, b + EXTRA + 1):
            if is_pf(flag_sets(st, n)):
                continue
            N, _ = n9(st, n)
            asgs, seen = [], set()
            for p, r in cands:
                a = dfs_assign(st, n, p, r)
                if tuple(a) not in seen:
                    seen.add(tuple(a))
                    asgs.append(((p, r), a))
            hit = None
            for x in range(len(asgs)):
                for y in range(x + 1, len(asgs)):
                    if isolated(st, asgs[x][1], asgs[y][1], N):
                        hit = (asgs[x][0], asgs[y][0])
                        break
                if hit:
                    break
            if hit:
                lines.append(f"s\t{name(st)}\t{n}\t{pstr(hit[0][0])}:{pstr(hit[0][1])}\t"
                             f"{pstr(hit[1][0])}:{pstr(hit[1][1])}")
    log(f"   generated sum-mode certificates ({time.time() - t0:.1f} s)")
    return "\n".join(lines) + "\n"


# ------------------------------------------------------------------------------------------------ checking
def check_certificates(text):
    cyc, zero, tabs, rco, xdat, sumL, sumS = {}, {}, {}, {}, {}, {}, {}
    for line in text.splitlines():
        if not line or line.startswith("#"):
            continue
        t = line.split("\t")
        case = (t[1], int(t[2]), t[3]) if t[0] in "CZTRX" else None
        if t[0] == "C":
            cyc.setdefault(case, []).append((pparse(t[4]), pparse(t[5]), int(t[6])))
        elif t[0] == "Z":
            zero[case] = t[4].split(" ")
        elif t[0] == "T":
            tabs.setdefault((case, int(t[4])), {})[t[5]] = [int(c) for c in t[6]]
        elif t[0] == "R":
            rco[(case, int(t[4]))] = [t[5][i:i + 2] for i in range(0, len(t[5]), 2)]
        elif t[0] == "X":
            xdat[(case, int(t[4]), tuple(int(c) for c in t[5]))] = ([int(c) for c in t[6]], t[7])
        elif t[0] == "S":
            sumL[t[1]] = (pparse(t[2]), pparse(t[3]), pparse(t[4]))
        elif t[0] == "s":
            a, b_ = t[3].split(":"), t[4].split(":")
            sumS[(t[1], int(t[2]))] = ((pparse(a[0]), pparse(a[1])), (pparse(b_[0]), pparse(b_[1])))

    # ---- Theorem 6: cycle certificates and class coverage
    t0 = time.time()
    cases = all_cases()
    n_cert = n_bad = n_direct = n_direct_bad = 0
    uncovered = []
    stats = {"maxN0b": 0, "maxK": 0, "maxm2": 0, "drift": 0, "exc": 0}
    for st, delta, comb in cases:
        key = (name(st), delta, comb)
        covered = [False] * NCLS
        b = base(st)
        for path, rule, cls in cyc.get(key, []):
            n_cert += 1
            c = cycle_cert(st, delta, comb == "min", path, rule, cls)
            if not c["ok"]:
                n_bad += 1
                continue
            per = c["per"]
            for cc in range(NCLS):
                if cc % per == cls:
                    covered[cc] = True
            stats["maxN0b"] = max(stats["maxN0b"], c["N0"] - b)
            stats["maxK"] = max(stats["maxK"], c["K"])
            stats["maxm2"] = max(stats["maxm2"], c["m2"])
            stats["drift"] += c["drift"] != 0
            stats["exc"] += len(c["exc"])
            # one direct evaluation of the order at the first n >= max(N0, b + 81) in the class
            n = max(c["N0"], b + EXTRA + 1)
            while n % per != cls:
                n += 1
            W, L = zero_weights(len(st))
            direct = (comp_mm(st, n, delta, comb == "min", W, L, dfs_assign(st, n, path, rule))
                      - truth_mm(st, n, delta, comb == "min", W, L)[0][n])
            n_direct += 1
            n_direct_bad += direct != c["predicted"](n) or direct == 0
        if not all(covered):
            uncovered.append(key)
    check(f"Theorem 6 cycle certificates: all {n_cert} valid (cycle found, window errors nonzero apart from exceptions "
          f"<= b + 80, N0 <= b + 81, structure corollary consistent between two representatives)",
          n_cert > 0 and n_bad == 0,
          f"invalid {n_bad}; max N0 - b = {stats['maxN0b']}, max K = {stats['maxK']}, max m2 = {stats['maxm2']}, "
          f"{stats['drift']} with nonzero drift, {stats['exc']} exception values")
    check(f"Theorem 6 class coverage: every one of the {len(cases)} cases (416 ordered lists x delta x combine) has "
          f"all 24 classes of n mod 24 certified", not uncovered and len(cases) == 1664, f"uncovered {uncovered[:3]}")
    check("Theorem 6 direct evaluation agrees with the certificate's prediction at one n >= b + 81 per certificate "
          "and is nonzero", n_direct_bad == 0, f"{n_direct} evaluations, {time.time() - t0:.1f} s")

    # ---- Theorem 6: small n
    t0 = time.time()
    n_inst = n_zero = n_resid = bad = 0
    n_coef = n_coef_const = n_coef_x = 0
    for st, delta, comb in cases:
        key = (name(st), delta, comb)
        is_min = comb == "min"
        k = len(st)
        b = base(st)
        toks = zero.get(key)
        if toks is None or len(toks) != EXTRA + 1:
            bad += 1
            continue
        W0, L0 = zero_weights(k)
        for n, tok in zip(range(b, b + EXTRA + 1), toks):
            pf = is_pf(flag_sets(st, n))
            if pf:
                bad += tok != "."
                continue
            n_inst += 1
            if tok == "." :
                bad += 1
            elif tok != "*":
                p, r = (pparse(x) for x in tok.split(":"))
                n_zero += 1
                bad += (comp_mm(st, n, delta, is_min, W0, L0, dfs_assign(st, n, p, r))
                        == truth_mm(st, n, delta, is_min, W0, L0)[0][n])
            else:
                n_resid += 1
                tt = tabs.get((key, n), {})
                asg = {j: dfs_table(st, n, t) for j, t in tt.items()}
                rt = rco.get((key, n), [])
                coefs = list(itertools.product(range(1, 10), repeat=k))
                if len(rt) != len(coefs):
                    bad += 1
                    continue
                cache = {}
                for coef, tk in zip(coefs, rt):
                    n_coef += 1
                    if tk[1] not in asg:
                        bad += 1
                        continue
                    if tk[0] == "x":
                        xd = xdat.get((key, n, coef))
                        if xd is None or xd[1] != tk[1]:
                            bad += 1
                            continue
                        W, L = weights(st, coef, xd[0])
                        n_coef_x += 1
                        bad += truth_mm(st, n, delta, is_min, W, L)[0][n] == comp_mm(st, n, delta, is_min, W, L,
                                                                                    asg[tk[1]])
                    else:
                        v = int(tk[0])
                        wt = tuple((coef[i] * v + i) % 10 for i in range(k))
                        ck = (v, wt, tk[1])
                        if ck not in cache:
                            W, L = [wt] * DLEN, [v] * DLEN
                            cache[ck] = (truth_mm(st, n, delta, is_min, W, L)[0][n]
                                         != comp_mm(st, n, delta, is_min, W, L, asg[tk[1]]))
                        n_coef_const += 1
                        bad += not cache[ck]
    check("Theorem 6 small n (b <= n <= b + 80, flag not functional): every instance has a zero-data certificate or a "
          "certificate for every coefficient vector, and every certificate breaks its instance",
          bad == 0 and n_inst == n_zero + n_resid,
          f"{n_inst} instances = {n_zero} zero-data + {n_resid} residual; {n_coef} coefficient vectors "
          f"({n_coef_const} with constant data, {n_coef_x} with explicit data); {time.time() - t0:.1f} s")

    # ---- Theorem 7: sum mode
    t0 = time.time()
    bad_l = bad_inv = 0
    maxN = maxNT = 0
    e2e = e2e_bad = rel_bad = 0
    n_inv = n_rel = 0
    rng = XorShift(seed_of("e2e"))
    ms_fail = [st for st in multisets() if not criterion(st)]
    for st in ms_fail:
        b = base(st)
        cert = sumL.get(name(st))
        if cert is None:
            bad_l += 1
            continue
        p0, p1, R = cert
        if (sum(st[i][0] for i in p0) != sum(st[i][0] for i in p1)
                or sum(st[i][1] for i in p0) % 2 != sum(st[i][1] for i in p1) % 2):
            bad_l += 1
            continue
        nT = sum_threshold(st, p0, R)
        iso, D, a0, a1 = sum_pattern(st, nT, p0, p1, R)
        if iso is None or nT > b + EXTRA + 1:
            bad_l += 1
            continue
        maxN = max(maxN, iso[1])
        maxNT = max(maxNT, nT - b)
        ref = (nT - iso[0], iso[1], D)
        for n in range(nT + 1, nT + 41):  # consistency with the translation lemma
            iso2, D2, _, _ = sum_pattern(st, n, p0, p1, R)
            bad_inv += iso2 is None or (n - iso2[0], iso2[1], D2) != ref
            n_inv += 1
        for n in (nT, nT + 7, nT + 23):  # end to end, mod P
            _, _, a0, a1 = sum_pattern(st, n, p0, p1, R)
            for _ in range(3):
                coef = [1 + rng.below(9) for _ in st]
                delta = 1 + rng.below(2)
                e2e += 1
                hit = False
                for data in [[0] * DLEN] + [[int(r == j) for r in range(DLEN)] for j in range(DLEN)]:
                    V0, _ = truth_sum(st, n, delta, coef, data)
                    if comp_sum(st, n, delta, coef, data, a0) != V0[n] or comp_sum(st, n, delta, coef, data, a1) != V0[n]:
                        hit = True
                        break
                e2e_bad += not hit
        # relabelling: the certificate orders, mapped along each permutation of the moves, give the same flags
        k = len(st)
        for tau in itertools.permutations(range(k)):
            inv = [tau.index(i) for i in range(k)]
            st2 = tuple(st[tau[j]] for j in range(k))
            for n in (nT, nT + 5):
                rel_bad += (dfs_assign(st2, n, [inv[i] for i in p0], [inv[i] for i in R]) != dfs_assign(st, n, p0, R)
                            or dfs_assign(st2, n, [inv[i] for i in p1], [inv[i] for i in R]) != dfs_assign(st, n, p1, R))
                n_rel += 1
    check(f"Theorem 7 large n: each of the {len(ms_fail)} failing multisets has a pair certificate (equal descent "
          f"total and parity, same rule) with an isolated differing node at the translation threshold "
          f"J + F + 4 + b <= b + 81",
          bad_l == 0 and len(ms_fail) == 96, f"max N9 = {maxN} < P, max threshold - b = {maxNT}")
    check("Theorem 7 consistency of the translation lemma: the relative pattern (isolated node, N9, differing set) is "
          "the same for the next 40 values of n", bad_inv == 0, f"{n_inv} (multiset, n) pairs")
    n_s = bad_s = 0
    maxNs = 0
    for st in ms_fail:
        b = base(st)
        for n in range(b, b + EXTRA + 1):
            if is_pf(flag_sets(st, n)):
                bad_s += (name(st), n) in sumS
                continue
            n_s += 1
            cert = sumS.get((name(st), n))
            if cert is None:
                bad_s += 1
                continue
            (p0, r0), (p1, r1) = cert
            N, _ = n9(st, n)
            a0, a1 = dfs_assign(st, n, p0, r0), dfs_assign(st, n, p1, r1)
            iso = isolated(st, a0, a1, N)
            if iso is None:
                bad_s += 1
                continue
            maxNs = max(maxNs, iso[1])
            if n_s % 10 == 0:
                coef = [1 + rng.below(9) for _ in st]
                delta = 1 + rng.below(2)
                e2e += 1
                hit = False
                for data in [[0] * DLEN] + [[int(r == j) for r in range(DLEN)] for j in range(DLEN)]:
                    V0, _ = truth_sum(st, n, delta, coef, data)
                    if comp_sum(st, n, delta, coef, data, a0) != V0[n] or comp_sum(st, n, delta, coef, data, a1) != V0[n]:
                        hit = True
                        break
                e2e_bad += not hit
    check("Theorem 7 small n (b <= n <= b + 80, flag not functional): every instance has a pair of D-orders with an "
          "isolated differing node c, 1 <= N9(c) < P", bad_s == 0, f"{n_s} instances, max N9 = {maxNs}")
    check("Theorem 7 relabelling: the certificate orders mapped along every permutation of the moves induce the same "
          "flags (large-n certificates, two values of n)", rel_bad == 0, f"{n_rel} (multiset, permutation, n) triples")
    check("Theorem 7 end to end (sample): data 0 or a unit vector gives a wrong result for one of the two orders, by "
          "direct mod-P evaluation", e2e_bad == 0, f"{e2e} trials, {time.time() - t0:.1f} s")


# ------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--regenerate", action="store_true", help="re-run the certificate search and require the same "
                                                              "content as the shipped file")
    ap.add_argument("--write", metavar="FILE", help="write regenerated certificates (gzip) to FILE and exit")
    args = ap.parse_args()
    t_start = time.time()
    if args.write:
        text = generate()
        Path(args.write).write_bytes(gzip.compress(text.encode("utf-8"), mtime=0))
        print(f"wrote {args.write}: {len(text.splitlines())} lines, sha256 {hashlib.sha256(text.encode()).hexdigest()}")
        return 0
    print("== Setting")
    divisors = [d for d in range(2, math.isqrt(P) + 1) if P % d == 0]
    check("P = 1000003 is prime (trial division by every d with 2 <= d <= isqrt(P) = 1000)", not divisors,
          f"{math.isqrt(P) - 1} trial divisors, divisors found: {divisors}")
    print("== Theorem 1, Propositions 2-3, Theorem 4")
    part_theorem1()
    part_lemmas()
    part_criterion()
    part_onlyif()
    part_model_g()
    print("== Theorem 5 (model S, sum mode)")
    part_theorem5()
    print("== Theorems 6-7 (model D): certificates")
    text = gzip.decompress(CERT_FILE.read_bytes()).decode("utf-8")
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    check("certificate file present, SHA-256 of its content as recorded in verify.py",
          CERT_SHA256 is None or digest == CERT_SHA256, f"{digest}, {len(text.splitlines())} lines")
    if args.regenerate:
        t0 = time.time()
        regen = generate(log=lambda s: print(s, flush=True))
        check("regenerated certificates are identical to the shipped file", regen == text,
              f"{time.time() - t0:.1f} s")
    check_certificates(text)
    print(f"total {time.time() - t_start:.1f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
