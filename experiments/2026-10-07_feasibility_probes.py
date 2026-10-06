#!/usr/bin/env python3
"""Feasibility probes for six top-ranked transfer candidates (pattern mining, 2026-10-07).

Question: research/2026-10-07_patterns.md ranks candidate pairs partly on "is V1/V2 feasible in pure Python?".
For six of the top candidates, is that true in practice: do minimal implementations agree with each other, and
does each one's measured growth fit its claimed cost (and NOT fit the other algorithm's cost) at sizes that run
in roughly 0.1-300 ms?

These are PROBES, not dataset entries: minimal code, a small correctness battery, one timing pass. They do not
replace an entry's harness, independent oracle or recorded run.

Method: each probe implements a slow and a fast algorithm, cross-checks them on seeded random instances
(random.Random with a fixed string seed per probe and size), then times them with the validator's own
tools/validate.time_call (best of 3, looped to >= 20 ms) and fits slopes with tools/validate.fit_slope, exactly
like V2: alpha = slope of log(measured) against log(cost). For the NAND tree (a query-model claim) the measure is
the number of leaves read, averaged over 40 seeded instances, not time.
  P1 XOR convolution mod p: naive Theta(4^n) vs fast Walsh-Hadamard Theta(n 2^n)
  P2 subset convolution mod p: naive Theta(3^n) vs ranked zeta/Moebius Theta(n^2 2^n) (Bjorklund et al. 2007);
     also the plain zeta transform (subset sums): naive Theta(3^n) vs Yates Theta(n 2^n)
  P3 regex (a?)^n a^n on a^n (full match): backtracking matcher vs Thompson NFA simulation Theta(n^2)
  P4 global minimum cut: all 2^(n-1) - 1 bipartitions Theta(2^n n^2) vs Stoer-Wagner (array) Theta(n^3)
  P5 NAND tree of height h, "reluctant" worst-case inputs: left-first deterministic evaluation (2^h leaves)
     vs random-order evaluation (expected Theta(((1+sqrt 33)/4)^h) leaves)
  P6 longest common substring: DP Theta(n^2) vs suffix automaton Theta(n)

Determinism: all inputs and all internal randomness are seeded, so correctness results and the NAND leaf
counts are identical on rerun. Wall-clock timings (P1-P4, P6) vary between runs and machines; the alpha values
in the docstring summary below are from one console run and may move by a few hundredths.

FAILURE RECORDED (first run): the P3 battery reported 72 disagreements out of 320. Cause: a bug in this script's
Thompson closure, `atoms[s][1] in "?*"`, which is True for the empty quantifier "" (the empty string is a
substring of every string), so plain atoms were treated as optional. Fixed to `in ("?", "*")`; the second run
below has 0 disagreements. The bug was in the probe, not in any dataset code.

Result (second console run 2026-10-07, CPython 3.14.2, Windows 11; timings vary between runs):
  P1 XOR conv:   0/24 disagreements. naive alpha = 0.987 vs 4^n; FWHT alpha = 0.994 vs n 2^n, and 0.560 if fitted
                 against 4^n -> V2 feasible and the gap is resolved.
  P2 subset conv: 0/27. naive 1.033 vs 3^n; ranked zeta 0.983 vs n^2 2^n, BUT 0.836 if fitted against 3^n, i.e.
                 within the 0.25 tolerance: the timing CANNOT separate the two claims at n <= 12 (matches the
                 analytic rho = 1.205 of experiments/2026-10-07_v2_resolvability.py).
                 zeta transform: 0/33. naive 1.033 vs 3^n; Yates 1.012 vs n 2^n and 0.710 vs 3^n -> resolved.
  P3 regex:      0/320 (backtracking, Thompson and Python's re.fullmatch agree on random tiny patterns).
                 Backtracking steps on (a?)^n a^n, n = 2..20 even: 11, 63, 319, 1535, 7167, 32767, 147455, 655359,
                 2883583, 12582911, which equals (n/2 + 2) 2^n - 1 at every measured n (read off the data, not
                 proven), i.e. Theta(n 2^n), not 2^n. Time: backtracking 1.072 vs 2^n; Thompson 0.997 vs n^2.
  P4 min cut:    0/45. brute 0.951 vs 2^n n^2; Stoer-Wagner 0.922 vs n^3 (0.065 vs 2^n n^2).
  P5 NAND tree:  0/110. Leaves read, mean of 40 reluctant instances, h = 6..20 even: left-first exactly 2^h
                 (alpha 1.000); random order 20.6 ... 29535.6, alpha 1.011 vs ((1+sqrt 33)/4)^h, and 0.762 if
                 fitted against 2^h, which is INSIDE the tolerance: the converse direction is not resolved
                 (analytic rho = 1.327, so a secretly-2^h implementation would still be caught by the fit).
  P6 LCSubstr:   0/104 against an O(n^3) brute-force oracle, 0/5 at n = 200. DP 1.009 vs n^2; suffix automaton
                 1.239 vs n (close to the 1.25 edge: dict-per-state memory effects, cf. the Kruskal note in
                 RL-018), 0.620 vs n^2.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope, time_call  # noqa: E402

sys.setrecursionlimit(10000)
P = 998244353


# ---------------------------------------------------------------- P1 XOR convolution
def xor_conv_naive(inst):
    a, b = inst
    N = len(a)
    c = [0] * N
    for i in range(N):
        ai = a[i]
        if ai:
            for j in range(N):
                c[i ^ j] += ai * b[j]
    return [x % P for x in c]


def _fwht(v):
    v = list(v)
    N, h = len(v), 1
    while h < N:
        for i in range(0, N, 2 * h):
            for j in range(i, i + h):
                x, y = v[j], v[j + h]
                v[j], v[j + h] = (x + y) % P, (x - y) % P
        h *= 2
    return v


def xor_conv_fwht(inst):
    a, b = inst
    N = len(a)
    fa, fb = _fwht(a), _fwht(b)
    c = _fwht([x * y % P for x, y in zip(fa, fb)])
    inv = pow(N, P - 2, P)
    return [x * inv % P for x in c]


def gen_pair(n, rng):
    N = 1 << n
    return ([rng.randrange(P) for _ in range(N)], [rng.randrange(P) for _ in range(N)])


# ---------------------------------------------------------------- P2 subset convolution, zeta
def subset_conv_naive(inst):
    f, g = inst
    N = len(f)
    h = [0] * N
    for S in range(N):
        T, acc = S, 0
        while True:                      # all submasks T of S, including 0
            acc += f[T] * g[S ^ T]
            if T == 0:
                break
            T = (T - 1) & S
        h[S] = acc % P
    return h


def _zeta_ranked(f, n):
    N = 1 << n
    F = [[0] * N for _ in range(n + 1)]
    for S in range(N):
        F[bin(S).count("1")][S] = f[S]
    for k in range(n + 1):
        row = F[k]
        for i in range(n):
            bit = 1 << i
            for S in range(N):
                if S & bit:
                    row[S] = (row[S] + row[S ^ bit]) % P
    return F


def subset_conv_ranked(inst):
    f, g = inst
    N = len(f)
    n = N.bit_length() - 1
    Fz, Gz = _zeta_ranked(f, n), _zeta_ranked(g, n)
    pc = [bin(S).count("1") for S in range(N)]
    h = [0] * N
    for k in range(n + 1):
        Hk = [0] * N
        for j in range(k + 1):
            A, B = Fz[j], Gz[k - j]
            for S in range(N):
                Hk[S] += A[S] * B[S]
        Hk = [x % P for x in Hk]
        for i in range(n):                # Moebius (inverse zeta) on rank k
            bit = 1 << i
            for S in range(N):
                if S & bit:
                    Hk[S] = (Hk[S] - Hk[S ^ bit]) % P
        for S in range(N):
            if pc[S] == k:
                h[S] = Hk[S]
    return h


def zeta_naive(f):
    N = len(f)
    out = [0] * N
    for S in range(N):
        T, acc = S, 0
        while True:
            acc += f[T]
            if T == 0:
                break
            T = (T - 1) & S
        out[S] = acc % P
    return out


def zeta_yates(f):
    v = list(f)
    N = len(v)
    bit = 1
    while bit < N:
        for S in range(N):
            if S & bit:
                v[S] = (v[S] + v[S ^ bit]) % P
        bit <<= 1
    return v


def gen_vec(n, rng):
    return [rng.randrange(P) for _ in range(1 << n)]


# ---------------------------------------------------------------- P3 regex
def parse(pattern):
    """Tiny syntax: a sequence of atoms 'c', 'c?' or 'c*' over single characters."""
    atoms, i = [], 0
    while i < len(pattern):
        c = pattern[i]
        q = pattern[i + 1] if i + 1 < len(pattern) and pattern[i + 1] in "?*" else ""
        atoms.append((c, q))
        i += 2 if q else 1
    return atoms


def match_backtrack(inst):
    """Perl-style greedy backtracking (tries 'consume' before 'skip'). Returns (matched, steps)."""
    pattern, text = inst
    atoms = parse(pattern)
    steps = 0

    def m(ai, ti):
        nonlocal steps
        steps += 1
        if ai == len(atoms):
            return ti == len(text)
        c, q = atoms[ai]
        if q == "":
            return ti < len(text) and text[ti] == c and m(ai + 1, ti + 1)
        if q == "?":
            return (ti < len(text) and text[ti] == c and m(ai + 1, ti + 1)) or m(ai + 1, ti)
        # '*': greedy, then back off
        k = ti
        while k < len(text) and text[k] == c:
            k += 1
        for end in range(k, ti - 1, -1):
            if m(ai + 1, end):
                return True
        return False

    return m(0, 0), steps


def match_thompson(inst):
    """Simulate the NFA with one set of positions per text character: Theta(|atoms| * |text|)."""
    pattern, text = inst
    atoms = parse(pattern)
    L = len(atoms)

    def closure(states):
        out, stack = set(states), list(states)
        while stack:
            s = stack.pop()
            if s < L and atoms[s][1] in ("?", "*") and s + 1 not in out:
                out.add(s + 1)
                stack.append(s + 1)
        return out

    cur = closure({0})
    for ch in text:
        nxt = set()
        for s in cur:
            if s < L and atoms[s][0] == ch:
                nxt.add(s + 1 if atoms[s][1] != "*" else s)
        cur = closure(nxt)
        if not cur:
            return False
    return L in cur


def gen_regex_worst(n, rng):
    return ("a?" * n + "a" * n, "a" * n)


# ---------------------------------------------------------------- P4 global min cut
def mincut_brute(W):
    n = len(W)
    if n < 2:
        return 0
    best = math.inf
    for mask in range(1, 1 << (n - 1)):       # vertex n-1 always on side 0; side 1 non-empty
        side = [(mask >> v) & 1 for v in range(n - 1)] + [0]
        w = 0
        for u in range(n):
            if side[u]:
                Wu = W[u]
                for v in range(n):
                    if not side[v]:
                        w += Wu[v]
        best = min(best, w)
    return best


def mincut_stoer_wagner(W):
    n = len(W)
    if n < 2:
        return 0
    G = [list(r) for r in W]
    alive = list(range(n))
    best = math.inf
    while len(alive) > 1:
        wsum = {v: 0 for v in alive}
        added = {v: False for v in alive}
        prev = last = None
        for _ in range(len(alive)):
            sel = max((v for v in alive if not added[v]), key=lambda v: wsum[v])
            added[sel] = True
            prev, last = last, sel
            for v in alive:
                if not added[v]:
                    wsum[v] += G[sel][v]
        best = min(best, wsum[last])
        for v in alive:                        # merge last into prev
            G[prev][v] += G[last][v]
            G[v][prev] = G[prev][v]
        alive.remove(last)
    return best


def gen_graph(n, rng):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = rng.randint(0, 9)
    return W


# ---------------------------------------------------------------- P5 NAND tree (query counts)
def gen_reluctant(h, rng, value=1, right_zero=False):
    """Leaves of a height-h NAND tree with root `value`; at value-1 nodes exactly one child is 0.
    right_zero=True always puts the 0 child on the right (worst case for left-first evaluation)."""
    if h == 0:
        return [value]
    if value == 0:
        kids = (1, 1)
    else:
        kids = (1, 0) if (right_zero or rng.random() < 0.5) else (0, 1)
    return gen_reluctant(h - 1, rng, kids[0], right_zero) + gen_reluctant(h - 1, rng, kids[1], right_zero)


def nand_eval(leaves, rng=None):
    """Short-circuit evaluation; rng=None: left child first; else random child order. Returns (value, reads)."""
    reads = 0

    def ev(lo, hi):
        nonlocal reads
        if hi - lo == 1:
            reads += 1
            return leaves[lo]
        mid = (lo + hi) // 2
        first, second = ((lo, mid), (mid, hi))
        if rng is not None and rng.random() < 0.5:
            first, second = second, first
        if ev(*first) == 0:
            return 1
        return 1 - ev(*second)

    return ev(0, len(leaves)), reads


# ---------------------------------------------------------------- P6 longest common substring
def lcsubstr_dp(inst):
    a, b = inst
    best, prev = 0, [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        cur = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                v = prev[j - 1] + 1
                cur[j] = v
                if v > best:
                    best = v
        prev = cur
    return best


def lcsubstr_sam(inst):
    a, b = inst
    link, length, nxt = [-1], [0], [{}]
    last = 0
    for ch in a:                                # standard online suffix-automaton construction
        cur = len(length)
        length.append(length[last] + 1); link.append(-1); nxt.append({})
        p = last
        while p != -1 and ch not in nxt[p]:
            nxt[p][ch] = cur
            p = link[p]
        if p == -1:
            link[cur] = 0
        else:
            q = nxt[p][ch]
            if length[p] + 1 == length[q]:
                link[cur] = q
            else:
                clone = len(length)
                length.append(length[p] + 1); link.append(link[q]); nxt.append(dict(nxt[q]))
                while p != -1 and nxt[p].get(ch) == q:
                    nxt[p][ch] = clone
                    p = link[p]
                link[q] = link[cur] = clone
        last = cur
    v, l, best = 0, 0, 0
    for ch in b:
        while v and ch not in nxt[v]:
            v = link[v]
            l = length[v]
        if ch in nxt[v]:
            v = nxt[v][ch]
            l += 1
        if l > best:
            best = l
    return best


def lcsubstr_brute(inst):
    a, b = inst
    subs = {b[i:j] for i in range(len(b)) for j in range(i + 1, len(b) + 1)}
    return max((j - i for i in range(len(a)) for j in range(i + 1, len(a) + 1) if a[i:j] in subs), default=0)


def gen_strings(n, rng, alphabet="ab"):
    return ("".join(rng.choice(alphabet) for _ in range(n)), "".join(rng.choice(alphabet) for _ in range(n)))


# ---------------------------------------------------------------- harness
def agree(name, fns, gen, sizes, trials, seed):
    bad = total = 0
    for n in sizes:
        for t in range(trials):
            inst = gen(n, random.Random(f"{seed}|v1|{n}|{t}"))
            outs = [f(inst) for f in fns]
            total += 1
            bad += any(o != outs[0] for o in outs)
    print(f"  V1-style check {name}: {total} instances, {bad} disagreements")
    return bad


def timing(name, fn, gen, ns, own_cost, other_cost, seed):
    vals = []
    for n in ns:
        inst = gen(n, random.Random(f"{seed}|v2|{n}"))
        vals.append(time_call(fn, inst))
    xs_own = [math.log(eval_cost(own_cost, n)) for n in ns]
    xs_other = [math.log(eval_cost(other_cost, n)) for n in ns]
    ys = [math.log(v) for v in vals]
    a_own, a_other = fit_slope(xs_own, ys), fit_slope(xs_other, ys)
    detail = ", ".join(f"n={n}: {v * 1e3:.3g}ms" for n, v in zip(ns, vals))
    print(f"  {name}: alpha vs {own_cost} = {a_own:.3f}; alpha vs {other_cost} = {a_other:.3f}   [{detail}]")
    return a_own, a_other


def main() -> int:
    print(f"CPython {sys.version.split()[0]}")

    print("\nP1 XOR convolution mod p")
    agree("naive vs FWHT", [xor_conv_naive, xor_conv_fwht], gen_pair, range(0, 8), 3, "P1")
    timing("naive", xor_conv_naive, gen_pair, [5, 6, 7, 8, 9], "4**n", "n * 2**n", "P1")
    timing("FWHT", xor_conv_fwht, gen_pair, [9, 10, 11, 12, 13, 14], "n * 2**n", "4**n", "P1")

    print("\nP2 subset convolution and zeta transform mod p")
    agree("subset conv naive vs ranked", [subset_conv_naive, subset_conv_ranked], gen_pair, range(0, 9), 3, "P2")
    agree("zeta naive vs Yates", [zeta_naive, zeta_yates], gen_vec, range(0, 11), 3, "P2z")
    timing("subset conv naive", subset_conv_naive, gen_pair, [7, 8, 9, 10, 11, 12], "3**n", "n**2 * 2**n", "P2")
    timing("subset conv ranked", subset_conv_ranked, gen_pair, [6, 7, 8, 9, 10, 11], "n**2 * 2**n", "3**n", "P2")
    timing("zeta naive", zeta_naive, gen_vec, [8, 9, 10, 11, 12, 13], "3**n", "n * 2**n", "P2z")
    timing("zeta Yates", zeta_yates, gen_vec, [10, 11, 12, 13, 14, 15, 16], "n * 2**n", "3**n", "P2z")

    print("\nP3 regex (a?)^n a^n on a^n")
    # independent oracle for the battery: Python's re.fullmatch on the same tiny syntax
    import re

    def gen_small_regex(n, rng):
        atoms = "".join(rng.choice("ab") + rng.choice(["", "?", "*"]) for _ in range(n))
        return (atoms, "".join(rng.choice("ab") for _ in range(rng.randint(0, n + 2))))

    bad = total = 0
    for n in range(0, 8):
        for t in range(40):
            inst = gen_small_regex(n, random.Random(f"P3|v1|{n}|{t}"))
            ref = re.fullmatch(inst[0], inst[1]) is not None
            total += 1
            bad += not (match_backtrack(inst)[0] == ref == match_thompson(inst))
    print(f"  V1-style check backtracking vs Thompson vs re.fullmatch: {total} instances, {bad} disagreements")
    steps = [match_backtrack(gen_regex_worst(n, None))[1] for n in range(2, 21, 2)]
    print("  backtracking steps on (a?)^n a^n, n = 2, 4, ..., 20: " + ", ".join(str(s) for s in steps))
    ns = list(range(2, 21, 2))
    print(f"  slope of log(steps) against n*log(2): {fit_slope([n * math.log(2) for n in ns], [math.log(s) for s in steps]):.3f}")
    timing("backtracking", match_backtrack, gen_regex_worst, [12, 13, 14, 15, 16, 17], "2**n", "n**2", "P3")
    timing("Thompson", match_thompson, gen_regex_worst, [50, 100, 200, 400, 800], "n**2", "2**n", "P3")

    print("\nP4 global minimum cut")
    agree("brute vs Stoer-Wagner", [mincut_brute, mincut_stoer_wagner], gen_graph, range(2, 11), 5, "P4")
    timing("brute", mincut_brute, gen_graph, [8, 9, 10, 11, 12, 13], "2**n * n**2", "n**3", "P4")
    timing("Stoer-Wagner", mincut_stoer_wagner, gen_graph, [20, 30, 45, 60, 90, 120], "n**3", "2**n * n**2", "P4")

    print("\nP5 NAND tree, reluctant inputs; measure = leaves read (40 instances per h)")
    bad = 0
    for h in range(0, 11):
        for t in range(10):
            rng = random.Random(f"P5|v1|{h}|{t}")
            leaves = gen_reluctant(h, rng, value=rng.randint(0, 1))
            full = leaves[:]
            while len(full) > 1:
                full = [1 - (full[i] & full[i + 1]) for i in range(0, len(full), 2)]
            bad += not (nand_eval(leaves)[0] == full[0] == nand_eval(leaves, random.Random(f"P5|alg|{h}|{t}"))[0])
    print(f"  V1-style check (left-first, random-order, bottom-up full evaluation): 110 instances, {bad} disagreements")
    hs = list(range(6, 21, 2))
    det, rnd = [], []
    for h in hs:
        d_sum = r_sum = 0
        for t in range(40):
            leaves = gen_reluctant(h, random.Random(f"P5|v2|{h}|{t}"), value=1, right_zero=True)
            d_sum += nand_eval(leaves)[1]
            r_sum += nand_eval(leaves, random.Random(f"P5|alg|v2|{h}|{t}"))[1]
        det.append(d_sum / 40)
        rnd.append(r_sum / 40)
    lam = (1 + math.sqrt(33)) / 4
    a_det = fit_slope([h * math.log(2) for h in hs], [math.log(v) for v in det])
    a_rnd = fit_slope([h * math.log(lam) for h in hs], [math.log(v) for v in rnd])
    a_rnd2 = fit_slope([h * math.log(2) for h in hs], [math.log(v) for v in rnd])
    print("  h:            " + " ".join(f"{h:>9}" for h in hs))
    print("  left-first:   " + " ".join(f"{v:>9.0f}" for v in det))
    print("  random order: " + " ".join(f"{v:>9.1f}" for v in rnd))
    print(f"  alpha left-first vs 2^h = {a_det:.3f}; random order vs ((1+sqrt33)/4)^h = {a_rnd:.3f}; "
          f"random order vs 2^h = {a_rnd2:.3f}")

    print("\nP6 longest common substring")
    agree("DP vs suffix automaton vs brute", [lcsubstr_dp, lcsubstr_sam, lcsubstr_brute], gen_strings,
          range(0, 13), 8, "P6")
    agree("DP vs suffix automaton (n = 200, alphabet ab)", [lcsubstr_dp, lcsubstr_sam], gen_strings, [200], 5, "P6b")
    timing("DP", lcsubstr_dp, gen_strings, [100, 200, 300, 400, 600, 800], "n**2", "n", "P6")
    timing("suffix automaton", lcsubstr_sam, gen_strings, [2000, 4000, 8000, 16000, 32000, 64000], "n", "n**2", "P6")
    return 0


if __name__ == "__main__":
    sys.exit(main())
