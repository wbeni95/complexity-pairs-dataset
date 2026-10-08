#!/usr/bin/env python3
"""Verifier for theorems/max-flow-random-dense-edmonds-karp-cubic-reads (see README.md in this folder).

Computations are evidence; the proofs are in the README. Standard library only, no network, deterministic (fixed
seeds). Exit code 0 only if every check passes. --full adds seeded instances with n = 240, 320, 400 to part S.

Model (README): vertices 0..n-1, s = 0, t = n - 1, M = the other m = n - 2 vertices; every ordered pair is an edge
with probability 1/2 and a capacity uniform on 1..100, all independent (generate_scaling of
pairs/max-flow-edmonds-karp-vs-dinic with ideal random bits). a_v = c(s, v), b_v = c(v, t).

Checks:
  K  exact constants (fractions): mu, mu' = E(a - b)^+ = 13433/800, mu'^2/20000, mu'/(200 mu), mu'/200.
  B  the numbers of Theorem 2 (tail bound), in 50-digit decimal arithmetic: the table for p1 = p2 = 0.01 (each value a
     lower bound), the two Hoeffding identities behind y and x, and ell(1000), ell(21 793) for p1 = p2 = 1/n.
  V  the instrumented copy of the entry's Edmonds-Karp reproduces the line-execution counts of the unchanged code
     (sys.settrace) on small seeded instances.
  S  seeded instances of generate_scaling (n = 20, 40, 80, 160; more with --full), deterministic statements checked
     instance by instance: the stages of lengths 1 and 2, every step of the chain of Theorem 1 (per BFS pass and per
     instance), the formula for D on the event F = min(c_out(s), c_in(t)), Corollary 3, and the upper bounds of
     Theorem 4 and of the remark after it.
Usage (from the repository root): python theorems/max-flow-random-dense-edmonds-karp-cubic-reads/verify.py [--full]
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
MU_PRIME = Fraction(13433, 800)


# ------------------------------------------------------------------------------------------------ K: constants
def part_constants():
    pmf = {0: Fraction(1, 2)}
    pmf.update({c: Fraction(1, 200) for c in CAPS})
    mu = sum(c * p for c, p in pmf.items())
    mup = sum(pa * pb * max(a - b, 0) for a, pa in pmf.items() for b, pb in pmf.items())
    check("mu = E c(u, v) = 101/4 and mu' = E(a_v - b_v)^+ = 13433/800 = 16.79125 (enumeration of all pairs)",
          mu == Fraction(101, 4) and mup == MU_PRIME)
    c = mup * mup / 20000
    check("mu'^2/20000 = 180445489/12800000000 = 0.0140973 (to 7 digits)",
          c == Fraction(180445489, 12800000000) and abs(float(c) - 0.0140973) < 5e-8, f"{float(c):.9f}")
    f1, f2 = mup / (200 * mu), mup / 200
    check("mu'/(200 mu) = 13433/4040000 = 0.0033250 and mu'/200 = 13433/160000 = 0.08395625 (so 0.0839 rounds down)",
          f1 == Fraction(13433, 4040000) and f2 == Fraction(13433, 160000) and float(f2) > 0.0839,
          f"{float(f1):.7f}, {float(f2):.8f}")


# ------------------------------------------------------------------------------------------------ B: Theorem 2
def part_tail():
    # 50-digit decimal arithmetic (+, -, *, /, exp, ln correctly rounded); square roots are certified by squaring
    getcontext().prec = 50
    mup = Decimal(MU_PRIME.numerator) / MU_PRIME.denominator
    rel = Decimal("1e-20")
    table = {400: ("333.9", "3435.8", "1.971e5", "0.00308"), 800: ("704.0", "8801.5", "2.726e6", "0.00532"),
             1200: ("1080.5", "14482.3", "1.133e7", "0.00655"), 2000: ("1842.8", "26273.6", "6.360e7", "0.00795"),
             10 ** 4: ("9627.3", "151604.3", "1.106e10", "0.01106"),
             10 ** 5: ("98729.4", "1627621.9", "1.307e13", "0.01307")}
    ok = True
    for n, (dm_e, D_e, lb_e, r_e) in table.items():
        m = n - 2
        y2 = (n - 1) * (Decimal(m) / Decimal("0.01")).ln()
        x2 = Decimal(10 ** 4) * m * (Decimal(2) / Decimal("0.01")).ln() / 2
        y, x = y2.sqrt() * (1 + rel), x2.sqrt() * (1 + rel)         # upper bounds for y and x
        ok &= y * y >= y2 and x * x >= x2
        dm, D = n - 1 - y, mup * m - x
        lb = dm * D * D / 20000
        ok &= Decimal(dm_e) <= dm and Decimal(D_e) <= D and Decimal(lb_e) <= lb and Decimal(r_e) <= lb / Decimal(n) ** 3
        print(f"       n={n}: delta_M > {dm:.4f}, D > {D:.4f}, reads >= {lb:.6E} = {lb / Decimal(n) ** 3:.7f} n^3")
    check("Theorem 2 with p1 = p2 = 0.01: every value of the six rows of the README table is a lower bound (the rows are "
          "rounded down; 50-digit decimal, 24 values)", ok)
    ok = True
    for n in (400, 10 ** 5):
        m = n - 2
        y2 = (n - 1) * (Decimal(m) / Decimal("0.01")).ln()
        x2 = Decimal(10 ** 4) * m * (Decimal(2) / Decimal("0.01")).ln() / 2
        ok &= abs(m * (-y2 / (n - 1)).exp() - Decimal("0.01")) < Decimal("1e-40") \
            and abs(2 * (-2 * x2 / (Decimal(10 ** 4) * m)).exp() - Decimal("0.01")) < Decimal("1e-40")
    check("Hoeffding identities: m exp(-y^2/(n - 1)) = p1 and 2 exp(-2 x^2/(1e4 m)) = p2 (p1 = p2 = 0.01; n = 400 "
          "and 10^5; 50-digit decimal)", ok)

    # Theorem 2 with p1 = p2 = 1/n: ell(n) = (1 - 1/n - Y(n)) (mu'(1 - 2/n) - X(n))^2 / 20000 with
    # Y(n) = sqrt(2 ln n / n) >= y/n and X(n) = sqrt(5000 ln(2n)/n) >= x/n
    def ell(n):
        n = Decimal(n)
        Y = (2 * n.ln() / n).sqrt() * (1 + rel)
        X = (5000 * (2 * n).ln() / n).sqrt() * (1 + rel)
        a, b = 1 - 1 / n - Y, mup * (1 - 2 / n) - X
        return a * b * b / 20000 if a > 0 and b > 0 else Decimal(0)

    def factors(n):
        n = Decimal(n)
        return (1 - 1 / n - (2 * n.ln() / n).sqrt(), mup * (1 - 2 / n) - (5000 * (2 * n).ln() / n).sqrt())

    f97, f98 = factors(97), factors(98)
    check("the two factors of ell(n): both positive at n = 98 (and, increasing, for every n >= 98); the second is "
          "negative at n = 97, so the ell bound is stated only from n = 98 on (50-digit decimal)",
          f98[0] > 0 and f98[1] > Decimal("1e-6") and f97[1] < 0 and all(factors(n)[0] > 0 for n in range(40, 99)),
          f"second factor at 97: {f97[1]:.5f}, at 98: {f98[1]:.5f}")
    l1000, l21793 = ell(1000), ell(21793)
    lim = mup * mup / 20000
    grid = [ell(n) for n in range(100, 5001, 7)]
    check("ell(n) of Theorem 2 (p1 = p2 = 1/n): ell(1000) >= 0.0049, ell(21 793) >= 0.0112, ell(n) < mu'^2/20000; "
          "ell is non-decreasing on the grid n = 100, 107, ..., 4999 (a check; the README proves monotonicity)",
          l1000 >= Decimal("0.0049") and l21793 >= Decimal("0.0112") and l21793 < lim
          and all(a <= b for a, b in zip(grid, grid[1:])),
          f"ell(1000) = {l1000:.6f}, ell(21793) = {l21793:.6f}, limit {lim:.7f}")
    # the two functions bounding y/n and x/n, and B(n) <= 1/n for n >= 40 (trivial-min-cut note)
    ok = True
    for n in (1000, 21793, 10 ** 6):
        m = n - 2
        y = ((n - 1) * Decimal(m * n).ln()).sqrt()
        x = (Decimal(5000) * m * (2 * Decimal(n)).ln()).sqrt()
        ok &= y / n <= (2 * Decimal(n).ln() / n).sqrt() and x / n <= (5000 * (2 * Decimal(n)).ln() / n).sqrt()
    check("y/n <= sqrt(2 ln n / n) and x/n <= sqrt(5000 ln(2n)/n) for p1 = p2 = 1/n (n = 1000, 21 793, 10^6; "
          "proved in the README for all n)", ok)


# ------------------------------------------------------------------------------------------------ copy with counters
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


def ek_copy(net):
    """Line-for-line copy of max_flow_edmonds_karp with counters. Per BFS pass: (reads, dequeued, |U|,
    sum of |adj| over U, R, path length, bottleneck), where U = the vertices enqueued while s is scanned and
    R = sum over the arcs out of s of their residual capacity at the start of the pass."""
    n, s, t, edges = net
    to, cap, adj = arcs_of(n, edges)
    flow = 0
    rec = []
    while True:
        R = sum(cap[e] for e in adj[s])
        parent_edge = [-1] * n
        parent_edge[s] = -2
        queue = deque([s])
        reads = deq = 0
        u_size = u_adj = -1
        while queue and parent_edge[t] == -1:
            u = queue.popleft()
            deq += 1
            for e in adj[u]:
                reads += 1
                v = to[e]
                if cap[e] > 0 and parent_edge[v] == -1:
                    parent_edge[v] = e
                    queue.append(v)
            if u_size < 0:
                u_size = len(queue)
                u_adj = sum(len(adj[x]) for x in queue)
        if parent_edge[t] == -1:
            rec.append((reads, deq, u_size, u_adj, R, 0, 0))
            return flow, rec, adj
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
        rec.append((reads, deq, u_size, u_adj, R, plen, bottleneck))


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
    el = {"bfs": ("parent_edge = [-1] * n", 1), "deq": ("u = queue.popleft()", 1), "read": ("v = to[e]", 1),
          "aug": ("flow += bottleneck", 1)}
    cases = [(n, i) for n in (10, 20, 30, 40) for i in range(3)]
    ok = 0
    for n, i in cases:
        net = HARNESS.generate_scaling(n, random.Random(f"ek-cubic|validate|{n}|{i}"))
        val, cnt = traced_counts(EK, el, net)
        f, rec, _ = ek_copy(net)
        mine = {"bfs": len(rec), "deq": sum(r[1] for r in rec), "read": sum(r[0] for r in rec), "aug": len(rec) - 1}
        ok += val == f and cnt == mine
    check(f"Edmonds-Karp copy = unchanged code (BFS passes, dequeues, reads `v = to[e]`, augmentations; "
          f"sys.settrace line counts) on {len(cases)} seeded instances, n = 10..40", ok == len(cases))


# ------------------------------------------------------------------------------------------------ S: simulation
class Tally:
    def __init__(self):
        self.cases = Counter()
        self.fails = Counter()

    def add(self, name, ok):
        self.cases[name] += 1
        if not ok:
            self.fails[name] += 1


def part_sim():
    tally = Tally()
    plan = [(20, 300), (40, 200), (80, 100), (160, 30)]
    if FULL:
        plan += [(240, 40), (320, 20), (400, 12)]
    for n, reps in plan:
        t0 = time.time()
        for i in range(reps):
            net = HARNESS.generate_scaling(n, random.Random(f"ek-cubic|{n}|{i}"))
            _, s, t, edges = net
            E = len(edges)
            a = [0] * n
            b = [0] * n
            cst = 0
            outdeg_s = 0
            for u, v, c in edges:
                if u == s:
                    outdeg_s += 1
                if u == s and v == t:
                    cst = c
                elif u == s:
                    a[v] = c
                elif v == t:
                    b[u] = c
            M = range(1, n - 1)
            cout = cst + sum(a[v] for v in M)
            cin = cst + sum(b[v] for v in M)
            K2 = sum(1 for v in M if a[v] > 0 and b[v] > 0)
            phi2 = sum(min(a[v], b[v]) for v in M)
            flow, rec, adj = ek_copy(net)
            F = flow
            tally.add("flow of the copy = unchanged Edmonds-Karp = unchanged Dinic", F == EK(net) == DINIC(net))
            D = F - cst - phi2
            deltaM = min(len(adj[v]) for v in M)
            aug = rec[:-1]
            lens = [r[5] for r in aug]
            tally.add("path lengths non-decreasing (Edmonds-Karp lemma)", all(x <= y for x, y in zip(lens, lens[1:])))
            tally.add("stage 1: #length-1 augmentations = 1[(s, t) in E], pushing c(s, t)",
                      sum(1 for L in lens if L == 1) == (1 if cst else 0)
                      and sum(r[6] for r in aug if r[5] == 1) == cst)
            tally.add("stage 2: #length-2 augmentations = #{v : a_v, b_v > 0}, pushing Phi_2 in total",
                      sum(1 for L in lens if L == 2) == K2 and sum(r[6] for r in aug if r[5] == 2) == phi2)
            tally.add("D = F - c(s,t) - Phi_2 >= 0 is the flow of the augmentations of length >= 3",
                      D >= 0 and sum(r[6] for r in aug if r[5] >= 3) == D)
            pushed = 0
            chain_reads = chain_adj = chain_u = chain_ceil = 0
            for (reads, deq, us, uadj, R, plen, bot) in aug:
                if plen >= 3:
                    tally.add("pass of length >= 3: R = c_out(s) - v(f), |U| >= R/100, dequeued >= |U| + 1, "
                              "reads >= |adj[s]| + sum_U |adj|, bottleneck in [1, 100]",
                              R == cout - pushed and 100 * us >= R and deq >= us + 1
                              and reads >= len(adj[s]) + uadj and 1 <= bot <= 100)
                    chain_reads += reads
                    chain_adj += len(adj[s]) + uadj
                    chain_u += us
                    chain_ceil += -(-R // 100)
                pushed += bot
            tally.add("Theorem 1 chain: reads(length >= 3) >= sum(|adj[s]| + sum_U |adj|) >= delta_M sum|U| >= "
                      "delta_M sum ceil(R/100) >= delta_M D^2/20000",
                      chain_reads >= chain_adj >= deltaM * chain_u >= deltaM * chain_ceil
                      and 20000 * chain_ceil >= D * D)
            total_reads = sum(r[0] for r in rec)
            lb = Fraction(deltaM * D * D, 20000)
            tally.add("Theorem 1: total reads >= delta_M D^2/20000", total_reads >= lb)
            if F == min(cout, cin):
                tally.add("on F = min(c_out(s), c_in(t)): D = min(sum (a-b)^+, sum (b-a)^+)",
                          D == min(sum(max(a[v] - b[v], 0) for v in M), sum(max(b[v] - a[v], 0) for v in M)))
            if D >= 200:
                big = sum(1 for r in rec if r[1] >= 1 + D / 200)
                tally.add("Corollary 3 (D >= 200): at least floor(D/200) + 1 passes dequeue >= 1 + D/200 vertices",
                          big >= D // 200 + 1)
            A = len(aug)
            tally.add("Theorem 4 and remark: A <= F <= 100 outdeg(s) <= 100(n - 1), reads <= 2E(A + 1) <= 2E(F + 1) "
                      "<= 2n(n - 1)(100n - 99), reads/(V E^2) <= 202/V",
                      A <= F <= 100 * outdeg_s <= 100 * (n - 1) and total_reads <= 2 * E * (A + 1) <= 2 * E * (F + 1)
                      <= 2 * n * (n - 1) * (100 * n - 99) and total_reads <= 202 * E * E)
        print(f"       n = {n}: {reps} instances checked ({time.time() - t0:.1f} s)")
    required = [
        "flow of the copy = unchanged Edmonds-Karp = unchanged Dinic",
        "path lengths non-decreasing (Edmonds-Karp lemma)",
        "stage 1: #length-1 augmentations = 1[(s, t) in E], pushing c(s, t)",
        "stage 2: #length-2 augmentations = #{v : a_v, b_v > 0}, pushing Phi_2 in total",
        "D = F - c(s,t) - Phi_2 >= 0 is the flow of the augmentations of length >= 3",
        "pass of length >= 3: R = c_out(s) - v(f), |U| >= R/100, dequeued >= |U| + 1, "
        "reads >= |adj[s]| + sum_U |adj|, bottleneck in [1, 100]",
        "Theorem 1 chain: reads(length >= 3) >= sum(|adj[s]| + sum_U |adj|) >= delta_M sum|U| >= "
        "delta_M sum ceil(R/100) >= delta_M D^2/20000",
        "Theorem 1: total reads >= delta_M D^2/20000",
        "on F = min(c_out(s), c_in(t)): D = min(sum (a-b)^+, sum (b-a)^+)",
        "Corollary 3 (D >= 200): at least floor(D/200) + 1 passes dequeue >= 1 + D/200 vertices",
        "Theorem 4 and remark: A <= F <= 100 outdeg(s) <= 100(n - 1), reads <= 2E(A + 1) <= 2E(F + 1) "
        "<= 2n(n - 1)(100n - 99), reads/(V E^2) <= 202/V",
    ]
    # every name is printed, zeros included; each must occur at least once (the README states that each statement is
    # checked on these instances); a name outside the list (a typo) is printed and treated the same way
    for name in required + sorted(x for x in tally.cases if x not in required):
        check(f"{name} ({tally.cases[name]} cases; must occur)", tally.fails[name] == 0 and tally.cases[name] >= 1,
              f"{tally.fails[name]} failures")


def main():
    t0 = time.time()
    for name, fn in (("K", part_constants), ("B", part_tail), ("V", part_validate), ("S", part_sim)):
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
