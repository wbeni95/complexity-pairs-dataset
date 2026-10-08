#!/usr/bin/env python3
"""Verifier for theorems/lz77-repeat-slots-state-bounds (see README.md in this folder).

Deterministic exhaustive and seeded checks of Theorems C, A, F1, F2, Proposition F1', Fact P and Corollary W;
computations are evidence, the proofs are in the README. Standard library only; no network; well under a minute on a
laptop. Exit code 0 only if every check passes.

Model (as in the README): literal 9; repeat of slot j, length L >= REPMIN: 3 + j + gamma(L), slot j to the front;
new match (1 <= d <= i, L >= 2): 2 + gamma(L-1) + gamma(d), d pushed to the front, last slot dropped; initial slots
(1, ..., 1). Pruning (G3 / G3*): at each position i < n one cheapest state R* is chosen by a comparator rule and every
R != R* with c(R) >= c(R*) + margin(R, R*) is deleted; position n is not pruned (unless prune_n is set).

Parts:
  C   Theorem C (all binary strings n <= 12, ternary n <= 8, REPMIN 1..3; a^n; the sums of item 3).
  A   Theorem A (a^n, k = 1..5, G3 and G3*, five comparator rules, REPMIN 2, 3, 5).
  F1  Theorem F1, Fact P and Proposition F1' on F1(m) = x_1 ab x_2 ab ... x_m ab.
  F2  Theorem F2, Fact P and Lemma Q3 on F2(k, 2, m, T), k = 1, 2, 3; condition (K).
  W   Corollary W: lengths and the displayed inequality over a range of n.
Usage (from the repository root): python theorems/lz77-repeat-slots-state-bounds/verify.py
"""
import itertools
import math
import random
import sys
import time

FAILURES = []
BIG = 1 << 60


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ model
def gamma(x):
    return 2 * (x.bit_length() - 1) + 1


def rep_cost(L, j):
    return 3 + j + gamma(L)


def new_cost(L, d):
    return 2 + gamma(L - 1) + gamma(d)


def match_rows(s):
    """rows[i] = {d: ml(i, d)} for the distances d with s[i] == s[i - d] (ml >= 1); ml(i, d) = 0 otherwise."""
    n = len(s)
    where = {}
    for p, c in enumerate(s):
        where.setdefault(c, []).append(p)
    rows = [None] * n + [{}]
    for i in range(n - 1, -1, -1):
        nxt = rows[i + 1]
        row = {}
        for p in where[s[i]]:
            if p >= i:
                break
            d = i - p
            row[d] = 1 + nxt.get(d, 0)
        rows[i] = row
    return rows


def margin_D(R, Rb):
    a0 = next((a for a in range(len(R)) if R[a] != Rb[a]), len(R))
    return sum(max(0, gamma(R[a]) - 1 - a) for a in range(a0, len(R)))


def lam(repmin, remaining):
    """lambda = max over REPMIN <= L <= remaining of gamma(L-1) - gamma(L); None if the range is empty."""
    if repmin > remaining:
        return None
    return max(gamma(L - 1) - gamma(L) for L in range(repmin, min(remaining, repmin + 2) + 1))


def margin_Dstar(R, Rb, repmin, remaining):
    lm = lam(repmin, remaining)
    if lm is None:
        return 0
    a0 = next((a for a in range(len(R)) if R[a] != Rb[a]), len(R))
    return sum(max(0, gamma(R[a]) - 1 - a + lm) for a in range(a0, len(R)))


def chooser(rule, seed="0"):
    rng = random.Random(seed)

    def pick(i, cheapest):
        if rule == "lexmin":
            return cheapest[0]
        if rule == "lexmax":
            return cheapest[-1]
        if rule == "revlex":
            return min(cheapest, key=lambda R: R[::-1])
        if rule == "alt":
            return cheapest[0] if i % 3 == 0 else cheapest[-1]
        return rng.choice(cheapest)
    return pick


RULES = ("lexmin", "lexmax", "revlex", "alt", "rand")


def run(s, k, repmin, rule=None, pick=None, prune_n=False):
    """Forward DP with prefix grouping. Returns dict with
    present[i] (values before pruning), kept[i] (after pruning), groups[i], relax (relaxation count), opt."""
    n = len(s)
    rows = match_rows(s)
    st = [dict() for _ in range(n + 1)]
    st[0][(1,) * k] = 0
    present, kept, ngroups = [None] * (n + 1), [None] * (n + 1), [0] * (n + 1)
    relax = 0
    for i in range(n + 1):
        cur = st[i]
        present[i] = dict(cur)
        if rule is not None and (i < n or prune_n) and len(cur) > 1:
            cmin = min(cur.values())
            Rb = pick(i, sorted(R for R, c in cur.items() if c == cmin))
            if rule == "G3":
                cur = {R: c for R, c in cur.items() if R == Rb or c < cmin + margin_D(R, Rb)}
            else:
                cur = {R: c for R, c in cur.items() if R == Rb or c < cmin + margin_Dstar(R, Rb, repmin, n - i)}
            st[i] = cur
        kept[i] = cur
        ngroups[i] = len({R[:-1] for R in cur})
        if i == n:
            break
        row = rows[i]
        dists = [(d, L) for d, L in row.items() if L >= 2]
        groups = {}
        for R, c in cur.items():
            relax += 1
            if c + 9 < st[i + 1].get(R, BIG):
                st[i + 1][R] = c + 9
            for j, r in enumerate(R):
                if r <= i:
                    M = row.get(r, 0)
                    if M >= repmin:
                        R2 = (r,) + R[:j] + R[j + 1:]
                        for L in range(repmin, M + 1):
                            relax += 1
                            v = c + rep_cost(L, j)
                            if v < st[i + L].get(R2, BIG):
                                st[i + L][R2] = v
            pre = R[:-1]
            if c < groups.get(pre, BIG):
                groups[pre] = c
        for pre, c in groups.items():
            for d, M in dists:
                R2 = (d,) + pre
                for L in range(2, M + 1):
                    relax += 1
                    v = c + new_cost(L, d)
                    if v < st[i + L].get(R2, BIG):
                        st[i + L][R2] = v
    return {"present": present, "kept": kept, "groups": ngroups, "relax": relax, "opt": min(st[n].values()), "n": n}


def strings(alphabet, nmin, nmax):
    """All strings over {0..alphabet-1} of length nmin..nmax in which letters first occur in order."""
    for n in range(nmin, nmax + 1):
        for s in itertools.product(range(alphabet), repeat=n):
            seen, ok = -1, True
            for c in s:
                if c > seen + 1:
                    ok = False
                    break
                seen = max(seen, c)
            if ok:
                yield s


def kept_total(res):
    n = res["n"]
    return sum(len(res["kept"][i]) for i in range(n)) + len(res["present"][n])


# ------------------------------------------------------------------------------------------------ part C
def part_C():
    bad = cnt = 0
    for alphabet, nmax in ((2, 12), (3, 8)):
        for s in strings(alphabet, 0, nmax):
            n = len(s)
            for k in (1, 2, 3):
                for repmin in (1, 2, 3):
                    delta = 1 if repmin == 1 else 0
                    res = run(s, k, repmin)
                    S = [len(x) for x in res["present"]]
                    G = res["groups"]
                    ok = all(S[i] <= (1 if i <= 2 else (i - 2) ** k) for i in range(n + 1))
                    ok &= all(G[i] <= max(1, (i - 2) ** (k - 1)) for i in range(n + 1))
                    ok &= sum(S) <= 3 + sum(j ** k for j in range(1, n - 1))
                    ok &= res["relax"] <= S[0] + sum(S[i] * (1 + k * (n - i - 1 + delta)) + G[i] * i * (n - i - 1)
                                                     for i in range(1, n))
                    bad += not ok
                    cnt += 1
    check("Theorem C(1): S_i <= max(1,(i-2)^k), G_i <= max(1,(i-2)^(k-1)), S <= 3 + sum j^k, T <= bound; every binary "
          "string n <= 12 and ternary n <= 8 (up to renaming), k = 1, 2, 3, REPMIN = 1, 2, 3", bad == 0,
          f"{cnt} cases, {bad} bad")
    bad = cnt = 0
    lines = []
    for k, ns in ((1, (1, 2, 3, 10, 20, 40, 80)), (2, (1, 2, 5, 10, 20, 30)), (3, (1, 2, 7, 10, 14, 18)),
                  (4, (1, 2, 9, 12, 15))):
        for n in ns:
            for repmin in (1, 2, 3):
                delta = 1 if repmin == 1 else 0
                res = run((0,) * n, k, repmin)
                S = [len(x) for x in res["present"]]
                G = res["groups"]
                ok = all(S[i] >= math.prod(i - 2 * t for t in range(1, k + 1)) for i in range(2 * k + 1, n + 1))
                ok &= all(G[i] >= math.prod(i - 2 * t for t in range(1, k)) for i in range(2 * k + 1, n + 1))
                ident = S[0] + sum(S[i] * (1 + k * (n - i - 1 + delta)) + G[i] * i * (n - i - 1) for i in range(1, n))
                ok &= res["relax"] == ident if repmin <= 2 else res["relax"] <= ident
                if k == 1 and n >= 2:
                    ok &= sum(S) == 3 + sum(range(1, n - 1))
                bad += not ok
                cnt += 1
                if repmin == 2 and n >= 3:
                    lines.append(f"k={k},n={n}: S={sum(S)}, T={res['relax']}")
        res0 = run((), k, 1)                                  # n = 0: T = 0 < 1 = S_0, so the identity needs n >= 1
        bad += not (res0["relax"] == 0 and len(res0["present"][0]) == 1)
    check("Theorem C(2) on a^n: S_i >= prod (i-2t), G_i >= prod_{t<k} (i-2t), T identity (REPMIN = 1, 2; n >= 1), "
          "k = 1: S = 3 + sum j (REPMIN = 1, 2, 3); n = 0: T = 0, S_0 = 1", bad == 0,
          f"{cnt} (k, n, REPMIN) cases; " + "; ".join(lines[:6]) + " ...")
    bad = 0
    for k in range(1, 6):
        for N in range(1, 400):
            sk = sum(j ** k for j in range(1, N + 1))
            sk1 = sum(j ** (k + 1) for j in range(1, N + 1))
            lhs = sum(j ** k * (N - j) for j in range(1, N + 1))
            bad += lhs != N * sk - sk1
            bad += not (N ** (k + 1) / (k + 1) <= sk <= (N + 1) ** (k + 1) / (k + 1))
            bad += abs(lhs - N ** (k + 2) / ((k + 1) * (k + 2))) > N ** (k + 1)
            bad += 1 + k * (N - 1) > N ** k                                   # Bernoulli step of item 3
    check("Theorem C(3): (Sigma*) identity, integral bounds N^(k+1)/(k+1) <= sum j^k <= (N+1)^(k+1)/(k+1), "
          "|sum j^k (N-j) - N^(k+2)/((k+1)(k+2))| <= N^(k+1), and 1 + k(N-1) <= N^k; k = 1..5, N < 400", bad == 0,
          f"{5 * 399} (k, N) values, {bad} bad")


# ------------------------------------------------------------------------------------------------ part A
def f_a(i):
    return (0, 9, 18)[i] if i <= 2 else 12 + gamma(i - 2)


def part_A():
    bad = cnt = 0
    small_opt = {}
    for k in range(1, 6):
        for n in range(3, 41):
            s = (0,) * n
            for repmin in (2, 3, 5):
                for rule in ("G3", "G3*"):
                    for r in RULES:
                        res = run(s, k, repmin, rule, chooser(r, f"A|{k}|{n}|{repmin}|{rule}"))
                        ok = all(res["kept"][i] == {(1,) * k: f_a(i)} for i in range(n))
                        ok &= set(res["present"][n]) == {(1,) * k} | {(d,) + (1,) * (k - 1) for d in range(2, n - 1)}
                        ok &= kept_total(res) == 2 * n - 2 and len(res["present"][n]) == n - 2
                        ok &= res["opt"] == f_a(n)
                        if repmin == 2:
                            ok &= res["relax"] == n + k * (n - 1) * (n - 2) // 2 + n * (n - 1) * (n - 2) // 6
                        res2 = run(s, k, repmin, rule, chooser(r, f"A|{k}|{n}"), prune_n=True)
                        ok &= sum(len(x) for x in res2["kept"]) == n + 1
                        bad += not ok
                        cnt += 1
                if k <= 3 and n <= 17:
                    small_opt[(k, n, repmin)] = run(s, k, repmin)["opt"] == f_a(n)
    check("Theorem A: K_i = {1^k} with value f(i) for i < n, st'[n] as stated (n - 2 states), total 2n - 2, relaxations "
          "n + k(n-1)(n-2)/2 + n(n-1)(n-2)/6 (REPMIN = 2), n + 1 with position n pruned; k = 1..5, every n = 3..40, G3 "
          "and G3*, five comparator rules, REPMIN 2, 3, 5", bad == 0, f"{cnt} runs, {bad} bad")
    check("Theorem A: the pruned optimum f(n) equals the unpruned optimum (k <= 3, n <= 17)", all(small_opt.values()),
          f"{sum(small_opt.values())}/{len(small_opt)}")


# ------------------------------------------------------------------------------------------------ part F1
def F1(m):
    s = []
    for j in range(1, m + 1):
        s += [j + 1, 0, 1]                  # x_j = j + 1 (fresh), a = 0, b = 1
    return tuple(s)


def prefix_minima(s, k, repmin):
    res = run(s, k, repmin)
    return [min(v.values()) for v in res["present"]]


def part_F1():
    bad_states = bad_cheap = bad_count = bad_p = cnt = n_claims = n_cheap = n_count = n_p = 0
    for k, ms in ((1, (10, 20, 30)), (2, (8, 12, 16)), (3, (8, 11)), (4, (8, 10))):
        for m in ms:
            s = F1(m)
            n = 3 * m
            for repmin in (2, 3):
                f = prefix_minima(s, k, repmin)
                bad_p += any(f[3 * j] != 27 + 15 * (j - 1) for j in range(1, m + 1))
                for rule in ("G3", "G3*"):
                    for r in RULES:
                        res = run(s, k, repmin, rule, chooser(r, f"F1|{k}|{m}|{repmin}|{rule}"))
                        cnt += 1
                        bad_p += any(min(res["present"][x].values()) != f[x] for x in range(n + 1))
                        n_p += n + 1
                        for x in range(6, n):
                            cmin = min(res["present"][x].values())
                            for R, c in res["present"][x].items():
                                if c == cmin:
                                    n_cheap += 1
                                    if not (R[0] == 3 and set(R) <= {1, 3}):
                                        bad_cheap += 1
                        for j in range(k + 2, m):
                            need = [tuple(3 * t for t in ts)
                                    for ts in itertools.product(*[range(2, j - a) for a in range(k)])]
                            for x in (3 * j, 3 * j + 1, 3 * j + 2):
                                if rule == "G3*" and n - x < repmin + 1:
                                    continue
                                n_claims += len(need)
                                bad_states += sum(1 for R in need if R not in res["kept"][x])
                        if rule == "G3":
                            n_count += 1
                            lb = 3 * math.factorial(k) * math.comb(m - 2, k + 1)
                            alt = 3 * sum(math.prod(j - a - 2 for a in range(k)) for j in range(k + 2, m))
                            bad_count += lb != alt or sum(len(res["kept"][x]) for x in range(n)) < lb
    check("Theorem F1: every claimed state kept at every claimed position (k = 1..4, several m, REPMIN 2, 3, G3 and G3*, "
          "five comparator rules)", bad_states == 0, f"{cnt} runs, {n_claims} (state, position) claims, "
                                                     f"{bad_states} missing")
    check("Theorem F1, step 2: every cheapest state at x >= 6 has first entry 3 and entries in {1, 3}", bad_cheap == 0,
          f"{n_cheap} cheapest states in {cnt} runs, {bad_cheap} exceptions")
    check("Theorem F1: kept count >= 3 k! C(m-2, k+1) = 3 sum_j prod (j-a-2) under G3", bad_count == 0,
          f"{n_count} G3 runs, {bad_count} bad")
    check("Fact P on F1: the smallest value at every position equals the prefix optimum f(x) (and f(3j) = 27 + 15(j-1))",
          bad_p == 0, f"{n_p} positions in {cnt} runs, {bad_p} bad")
    worst, worst_n = {}, {}
    for k, m in ((1, 20), (2, 14), (3, 12), (4, 11), (5, 10), (6, 10)):
        s = F1(m)
        w = wn = 0
        for rule in ("G3", "G3*"):
            for r in ("lexmin", "lexmax", "alt"):
                res = run(s, k, 2, rule, chooser(r))
                for x in range(3 * m):
                    for R in res["kept"][x]:
                        w = max(w, sum(1 for v in R if v not in (1, 3)))
                for R in res["present"][3 * m]:
                    wn = max(wn, sum(1 for v in R if v not in (1, 3)))
        worst[k], worst_n[k] = w, wn
    check("Proposition F1': at most 4 entries outside {1, 3} in any kept state at every position x < n, and at most 5 in "
          "a state at position n (k = 1..6)", all(w <= 4 for w in worst.values()) and all(w <= 5 for w in worst_n.values()),
          f"maximum by k, x < n: {worst}; x = n: {worst_n}")


# ------------------------------------------------------------------------------------------------ part F2
def f2_params(k, L):
    M = k + L
    e = 0
    while gamma(1 << e) < 9 * L - 1:
        e += 1
    Gmin = 1 << e
    G = M * -(-max(Gmin, k) // M)
    span = G * (2 ** (k - 1) - 1) + (k - 1)
    Bp = M * -(-max(Gmin, span + 1) // M)
    return {"M": M, "Gmin": Gmin, "G": G, "span": span, "Bp": Bp, "C": Bp + span + L}


def F2(k, L, m, T):
    p = f2_params(k, L)
    M = p["M"]
    fresh = [L - 1]

    def fr():
        fresh[0] += 1
        return fresh[0]
    w = list(range(L))
    s, PD = [], []
    for t in range(m):
        s += [fr() for _ in range(M - L)]
        PD.append(len(s))
        s += w
    s += [fr() for _ in range(p["Bp"])]
    Q0 = len(s)
    q = [Q0 + p["G"] * (2 ** (i - 1) - 1) + (i - 1) for i in range(1, k + 1)]
    for i in range(k):
        while len(s) < q[i]:
            s.append(fr())
        s += w
    s += [fr() for _ in range(T)]
    return tuple(s), PD, q, p


def part_F2():
    L = 2
    bad = cnt = 0
    details = []
    for k, m, T in ((1, 5, 6), (1, 9, 4), (2, 3, 5), (2, 6, 4), (3, 3, 4), (3, 4, 3), (4, 2, 4), (5, 2, 3)):
        s, PD, q, p = F2(k, L, m, T)
        n, M = len(s), p["M"]
        ok = n == p["C"] + M * m + T and n == q[-1] + L + T and (M * m + p["Bp"]) % M == 0
        ok &= all(qi % M == i for i, qi in enumerate(q)) and all(pd % M == k for pd in PD)
        diffs = [q[b] - q[a] for a in range(k) for b in range(a + 1, k)]
        ok &= len(diffs) == len(set(diffs)) and q[0] - max(PD) >= p["Gmin"] and q[0] - p["span"] > M * m
        ok &= len(set(s)) == n - (m + k - 1) * L
        ok &= all(s[o:o + L] == tuple(range(L)) and s[o - 1] >= L for o in PD + q)               # words, fresh gaps
        ok &= all(q[i + 1] - (q[i] + L) >= 1 for i in range(k - 1))
        need = [tuple(q[k - 1 - a] - pp[a] for a in range(k)) for pp in itertools.product(PD, repeat=k)]
        ok &= len(set(need)) == m ** k
        for repmin in ((2, 3) if k <= 3 else (2,)):
            f = prefix_minima(s, k, repmin)
            ok &= all(f[x] == f[M * m] + 9 * (x - M * m) for x in range(M * m, n + 1))        # Lemma Q3
            configs = [("G3", r) for r in (("lexmin", "alt", "rand") if k <= 3 else ("alt",))]
            if T >= repmin + 1:
                configs += [("G3*", "lexmin"), ("G3*", "alt")] if k <= 3 else [("G3*", "lexmin")]
            for rule, r in configs:
                res = run(s, k, repmin, rule, chooser(r, f"F2|{k}|{m}|{T}|{repmin}"))
                cnt += 1
                ok &= all(min(res["present"][x].values()) == f[x] for x in range(n + 1))       # Fact P
                for x in range(M * m, n):
                    cmin = min(res["present"][x].values())
                    ok &= all(R[0] == 1 or R[0] % M == 0 for R, c in res["present"][x].items() if c == cmin)
                for x in range(q[-1] + L, n):
                    if rule == "G3*" and n - x < repmin + 1:
                        continue
                    ok &= all(R in res["kept"][x] for R in need)
                if rule == "G3":
                    ok &= sum(len(res["kept"][x]) for x in range(n)) >= T * m ** k
        bad += not ok
        details.append(f"k={k},m={m},T={T}: n={n}")
    check("Theorem F2 (L = 2): construction (length, residues, distinct differences, gaps, symbol count n - (m+k-1)L), "
          "Lemma Q3, Fact P, cheapest first entry in {1} + MZ, all m^k claimed states kept on the claimed positions, "
          "kept count >= T m^k; k = 1..3: G3 (3 comparator rules) and G3* (2), REPMIN 2, 3; k = 4, 5: G3 and G3*, "
          "REPMIN 2", bad == 0,
          f"{cnt} runs; " + "; ".join(details))
    kmax2 = max(k for k in range(1, 200) if (k - 1) / 2 < 9 * 2 - 3 - gamma(1))
    allk = all((k - 1) / 2 < 9 * (k + 1) - 3 - gamma(k) for k in range(1, 1001))
    check("Theorem F2: condition (K) holds for L = 2 exactly when k <= 28, and for L = k + 1 for all k <= 1000; "
          "G_min = 256 for L = 2", kmax2 == 28 and allk and f2_params(1, 2)["Gmin"] == 256,
          f"L = 2: k tested 1..199, largest k with (K) = {kmax2}; L = k + 1: 1000 values of k")


# ------------------------------------------------------------------------------------------------ part W
def part_W():
    bad = cnt = 0
    for k in (1, 2, 3, 4):
        L = 2
        p = f2_params(k, L)
        M, C = p["M"], p["C"]
        for repmin, extra in ((2, 0), (2, 2), (3, 3), (5, 5)):        # extra = 0: G3; extra = REPMIN: G3*
            for n in range(C + extra + 2 * M, C + extra + 2 * M + 600):
                m = (n - C - extra) // (2 * M)
                T = n - C - M * m
                counted = (T - extra) * m ** k
                ok = m >= 1 and M * m + extra <= T <= M * m + extra + 2 * M - 1 and C + M * m + T == n
                if extra:
                    ok &= T >= repmin + 1
                ok &= counted * 2 ** (k + 1) * M ** k >= (n - C - extra - 2 * M + 1) ** (k + 1)
                bad += not ok
                cnt += 1
    check("Corollary W: for every n in a 600-wide range above the threshold, F2 with m = floor((n - C [- REPMIN])/(2M)) "
          "has length n and counts (T [- REPMIN]) m^k >= (n - C [- REPMIN] - 2M + 1)^(k+1)/(2^(k+1) M^k); k = 1..4, "
          "G3 and G3* with REPMIN 2, 3, 5", bad == 0, f"{cnt} values, {bad} bad")


def main():
    t0 = time.time()
    for name, fn in (("C", part_C), ("A", part_A), ("F1", part_F1), ("F2", part_F2), ("W", part_W)):
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
