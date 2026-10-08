#!/usr/bin/env python3
"""Verifier for theorems/lz77-repeat-slots-exact-pruning (see README.md in this folder).

Deterministic exhaustive and seeded checks of the theorems, propositions and remarks; computations are evidence, the
proofs are in the README. Standard library only; no network; well under a minute on a laptop. Exit code 0 only if
every check passes.

Model (as in the README). Tokens at position i with slot tuple R (initially (1, ..., 1)):
  literal 9; repeat of slot j, length L >= REPMIN (R[j] <= i, text matches at distance R[j]): rep(L, j), slot j moves to
  the front; new match (1 <= d <= i, L >= 2, text matches at distance d): new(L, d), d pushed to the front, last slot
  dropped. Default costs: rep(L, j) = 3 + j + gamma(L), new(L, d) = 2 + gamma(L-1) + gamma(d), gamma(x) = 2 floor(log2 x) + 1.
Pruned DP: at each position i < n one cheapest state R* is chosen (by a comparator rule) and every R != R* with
c(R) >= c(R*) + margin(R, R*) is deleted.

Parts:
  M  the DP machinery: forward DP with and without prefix grouping = backward recursion = enumeration of all parses.
  G  Theorem 1 directly: V(i, R') <= V(i, R) + D(R, R') for all tuples with entries in [1, i].
Ranges written "binary" / "ternary" in parts G, P, S run over the strings in which the letters first occur in order
(binary: strings starting with a); renaming the letters maps them onto all strings and changes no cost.
  P  Theorem 2: G3-pruned DP = unpruned optimum (four comparator rules, with and without grouping; also G3*).
  S  Theorem 3 in three cost models: continuation bound, pruned = unpruned, the gamma formula with lambda_i.
  T  Proposition 4 (tightness instance).
  R  Remark 5 (the j = a version of G3* is false).
  H  Proposition 6 (REPMIN = 1; adaptive costs, exact rationals).
  N  Remark 7 (naive margins), along every sequence of comparator choices.
Usage (from the repository root): python theorems/lz77-repeat-slots-exact-pruning/verify.py
"""
import itertools
import math
import random
import sys
import time
from fractions import Fraction
from functools import lru_cache

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


GAMMA_COSTS = (9, lambda L, j: 3 + j + gamma(L), lambda L, d: 2 + gamma(L - 1) + gamma(d))
NONMONO_COSTS = (9, lambda L, j: 2 + (4, 2, 5, 3)[j] + gamma(L), lambda L, d: 3 + gamma(L - 1) + 2 * gamma(d))
THIRD_COSTS = (9, lambda L, j: (3, 9, 3)[j] + gamma(L), lambda L, d: 2 + gamma(L - 1) + gamma(d))


def word(text):
    return tuple(ord(c) - 97 for c in text)


def match_table(s):
    n = len(s)
    ml = [[0] * (i + 1) for i in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for d in range(1, i + 1):
            if s[i] == s[i - d]:
                ml[i][d] = 1 + ml[i + 1][d]
    return ml


def tokens(s, ml, i, R, repmin, costs):
    """(next position, next slots, cost) of every token allowed at (i, R)."""
    lit, rep, new = costs
    out = [(i + 1, R, lit)]
    for j, r in enumerate(R):
        if r <= i:
            for L in range(repmin, ml[i][r] + 1):
                out.append((i + L, (r,) + R[:j] + R[j + 1:], rep(L, j)))
    for d in range(1, i + 1):
        for L in range(2, ml[i][d] + 1):
            out.append((i + L, (d,) + R[:-1], new(L, d)))
    return out


def enumerate_optimum(s, k, repmin, costs=GAMMA_COSTS):
    """Exact method 1: every parse, explicit stack."""
    n = len(s)
    ml = match_table(s)
    best = None
    stack = [(0, (1,) * k, 0)]
    while stack:
        i, R, c = stack.pop()
        if i == n:
            best = c if best is None or c < best else best
            continue
        for i2, R2, tc in tokens(s, ml, i, R, repmin, costs):
            stack.append((i2, R2, c + tc))
    return best


def value_function(s, k, repmin, costs=GAMMA_COSTS):
    """Exact method 2: V(i, R) by backward memoised recursion (arbitrary tuples allowed)."""
    n = len(s)
    ml = match_table(s)

    @lru_cache(maxsize=None)
    def V(i, R):
        if i == n:
            return 0
        return min(tc + V(i2, R2) for i2, R2, tc in tokens(s, ml, i, R, repmin, costs))
    return V


def margin_D(R, Rb):
    a0 = next((a for a in range(len(R)) if R[a] != Rb[a]), len(R))
    return sum(max(0, gamma(R[a]) - 1 - a) for a in range(a0, len(R)))


def margin_Dstar(costs, repmin, remaining, only_j_equal_a=False):
    """D*_i as a function of (R, Rb), from its definition (max over j >= a and REPMIN <= L <= remaining)."""
    lit, rep, new = costs
    memo = {}

    def E(a, x, k):
        key = (a, x, k)
        if key not in memo:
            js = [a] if only_j_equal_a else range(a, k)
            vals = [new(L, x) - rep(L, j) for j in js for L in range(repmin, remaining + 1)]
            memo[key] = max(vals) if vals else 0
        return memo[key]

    def m(R, Rb):
        k = len(R)
        a0 = next((a for a in range(k) if R[a] != Rb[a]), k)
        return sum(max(0, E(a, R[a], k)) for a in range(a0, k))
    return m


def chooser(rule, seed=0):
    rng = random.Random(seed)

    def pick(i, cheapest):
        if rule == "lexmin":
            return cheapest[0]
        if rule == "lexmax":
            return cheapest[-1]
        if rule == "alt":
            return cheapest[0] if i % 3 == 0 else cheapest[-1]
        return rng.choice(cheapest)
    return pick


def forward_dp(s, k, repmin, costs=GAMMA_COSTS, margin=None, pick=None, group=True, log=None):
    """Forward DP over (position, slots). margin(i, R, Rb) -> number, or None for no pruning."""
    lit, rep, new = costs
    n = len(s)
    ml = match_table(s)
    cand = [[d for d in range(1, i + 1) if ml[i][d] >= 2] for i in range(n + 1)]
    st = [dict() for _ in range(n + 1)]
    st[0][(1,) * k] = 0
    for i in range(n):
        cur = st[i]
        if margin is not None and len(cur) > 1:
            cmin = min(cur.values())
            cheapest = sorted(R for R, c in cur.items() if c == cmin)
            Rb = pick(i, cheapest)
            kept = {R: c for R, c in cur.items() if R == Rb or c < cmin + margin(i, R, Rb)}
            if log is not None:
                log.append((i, dict(cur), Rb, kept))
            st[i] = cur = kept
        groups = {}
        for R, c in cur.items():
            if c + lit < st[i + 1].get(R, BIG):
                st[i + 1][R] = c + lit
            for j, r in enumerate(R):
                if r <= i:
                    R2 = (r,) + R[:j] + R[j + 1:]
                    for L in range(repmin, ml[i][r] + 1):
                        v = c + rep(L, j)
                        if v < st[i + L].get(R2, BIG):
                            st[i + L][R2] = v
            key = R[:-1] if group else R
            if c < groups.get(key, BIG):
                groups[key] = c
        for key, c in groups.items():
            base = key if group else key[:-1]
            for d in cand[i]:
                R2 = (d,) + base
                for L in range(2, ml[i][d] + 1):
                    v = c + new(L, d)
                    if v < st[i + L].get(R2, BIG):
                        st[i + L][R2] = v
    return min(st[n].values()), st


def all_choice_results(s, k, repmin, margin, costs=GAMMA_COSTS):
    """Set of outputs of the pruned DP over every sequence of comparator choices (one per position with ties)."""
    lit, rep, new = costs
    n = len(s)
    ml = match_table(s)
    out = set()

    def relax(st, i):
        for R, c in st[i].items():
            for i2, R2, tc in tokens(s, ml, i, R, repmin, costs):
                if c + tc < st[i2].get(R2, BIG):
                    st[i2][R2] = c + tc

    def rec(st, i):
        if i == n:
            out.add(min(st[n].values()))
            return
        cur = st[i]
        cmin = min(cur.values())
        for Rb in sorted(R for R, c in cur.items() if c == cmin):
            st2 = [dict(x) for x in st]
            st2[i] = {R: c for R, c in cur.items() if R == Rb or c < cmin + margin(i, R, Rb)}
            relax(st2, i)
            rec(st2, i + 1)

    st0 = [dict() for _ in range(n + 1)]
    st0[0][(1,) * k] = 0
    rec(st0, 0)
    return out


def G3(i, R, Rb):
    return margin_D(R, Rb)


def strings(alphabet, nmin, nmax, canonical_first=True):
    """All strings over {0..alphabet-1} of length nmin..nmax; with canonical_first, letters first occur in order."""
    for n in range(nmin, nmax + 1):
        for s in itertools.product(range(alphabet), repeat=n):
            if canonical_first:
                seen = -1
                ok = True
                for c in s:
                    if c > seen + 1:
                        ok = False
                        break
                    seen = max(seen, c)
                if not ok:
                    continue
            yield s


# ------------------------------------------------------------------------------------------------ parts
def part_machinery():
    bad = cnt = 0
    for s in strings(2, 0, 9, canonical_first=False):
        for k in (1, 2, 3):
            for repmin in (1, 2, 3):
                a, _ = forward_dp(s, k, repmin)
                b, _ = forward_dp(s, k, repmin, group=False)
                c = value_function(s, k, repmin)(0, (1,) * k)
                ok = a == b == c
                if len(s) <= 6:
                    ok &= enumerate_optimum(s, k, repmin) == a
                bad += not ok
                cnt += 1
    check("DP machinery: grouped DP = per-state DP = backward recursion (every binary string, n <= 9) "
          "= enumeration of all parses (n <= 6); k = 1, 2, 3; REPMIN = 1, 2, 3", bad == 0, f"{cnt} cases, {bad} bad")


def part_theorem1():
    for k, nmax in ((2, 7), (3, 6)):
        for repmin in (2, 3):
            pairs = viol = 0
            for s in strings(2, 2, nmax):
                V = value_function(s, k, repmin)
                n = len(s)
                for i in range(1, n):
                    tuples = list(itertools.product(range(1, i + 1), repeat=k))
                    vals = {R: V(i, R) for R in tuples}
                    for R in tuples:
                        for R2 in tuples:
                            pairs += 1
                            viol += vals[R2] > vals[R] + margin_D(R, R2)
            check(f"Theorem 1: V(i,R') <= V(i,R) + D(R,R'), k = {k}, REPMIN = {repmin}, every binary string of length "
                  f"2..{nmax} (first letter a), every position, all tuples in [1,i]^k", viol == 0,
                  f"{pairs} pairs, {viol} violations")


def part_theorem2():
    t = time.perf_counter()
    for k in (1, 2, 3):
        bad = cnt = 0
        for s in strings(2, 1, 13):
            opt, _ = forward_dp(s, k, 2)
            n = len(s)
            for rule in ("lexmin", "lexmax", "alt", "rand"):
                got, _ = forward_dp(s, k, 2, margin=G3, pick=chooser(rule, f"{s}|{k}"))
                bad += got != opt
                cnt += 1
            got, _ = forward_dp(s, k, 2, margin=G3, pick=chooser("lexmin"), group=False)
            bad += got != opt
            dstar = [margin_Dstar(GAMMA_COSTS, 2, n - i) for i in range(n + 1)]
            got, _ = forward_dp(s, k, 2, margin=lambda i, R, Rb: dstar[i](R, Rb), pick=chooser("alt"))
            bad += got != opt
            cnt += 2
        check(f"Theorem 2: G3-pruned DP = optimum, k = {k}, REPMIN = 2, every binary string of length 1..13 "
              f"(first letter a); comparators lexmin, lexmax, position-dependent, seeded random; also without "
              f"grouping, and G3*", bad == 0, f"{cnt} runs, {bad} wrong")
    bad = cnt = 0
    for s in strings(3, 1, 8):
        for k in (1, 2, 3):
            for repmin in (2, 3):
                opt, _ = forward_dp(s, k, repmin)
                for rule in ("lexmin", "lexmax"):
                    got, _ = forward_dp(s, k, repmin, margin=G3, pick=chooser(rule))
                    bad += got != opt
                    cnt += 1
    check("Theorem 2: every ternary string of length 1..8 (letters first occur in order), k = 1, 2, 3, REPMIN = 2, 3",
          bad == 0, f"{cnt} runs, {bad} wrong ({time.perf_counter() - t:.1f} s for part P)")


def part_theorem3():
    models = (("gamma", GAMMA_COSTS), ("non-monotone", NONMONO_COSTS), ("third", THIRD_COSTS))
    for name, costs in models:
        pairs = viol = viol_ja = 0
        for s in strings(2, 2, 8):
            V = value_function(s, 2, 2, costs)
            n = len(s)
            for i in range(1, n):
                m = margin_Dstar(costs, 2, n - i)
                mja = margin_Dstar(costs, 2, n - i, only_j_equal_a=True)
                tuples = list(itertools.product(range(1, i + 1), repeat=2))
                vals = {R: V(i, R) for R in tuples}
                for R in tuples:
                    for R2 in tuples:
                        pairs += 1
                        viol += vals[R2] > vals[R] + m(R, R2)
                        viol_ja += vals[R2] > vals[R] + mja(R, R2)
        if name == "non-monotone":
            check("Remark 5: in the non-monotone model the j = a margin is violated by exactly 10 pairs (same range)",
                  viol_ja == 10, f"{viol_ja} violations")
        check(f"Theorem 3 ({name} costs): continuation bound with D*_i, k = 2, REPMIN = 2, every binary string of "
              f"length 2..8, all tuples in [1,i]^2", viol == 0, f"{pairs} pairs, {viol} violations "
              f"(j = a margin: {viol_ja} violations)")
        bad = cnt = 0
        for s in strings(2, 1, 11):
            n = len(s)
            dstar = [margin_Dstar(costs, 2, n - i) for i in range(n + 1)]
            for k in (1, 2, 3):
                opt, _ = forward_dp(s, k, 2, costs)
                got, _ = forward_dp(s, k, 2, costs, margin=lambda i, R, Rb: dstar[i](R, Rb), pick=chooser("lexmin"))
                bad += got != opt
                cnt += 1
        check(f"Theorem 3 ({name} costs): D*-pruned DP = optimum, k = 1, 2, 3, every binary string of length 1..11",
              bad == 0, f"{cnt} runs, {bad} wrong")
    # gamma formula, D* <= D, equality when n - i >= REPMIN + 1
    rng = random.Random(7)
    bad = 0
    for _ in range(4000):
        k = rng.randint(1, 4)
        repmin = rng.randint(2, 5)
        rem = rng.randint(0, 12)
        R = tuple(rng.randint(1, 40) for _ in range(k))
        Rb = tuple(rng.randint(1, 40) for _ in range(k))
        dstar = margin_Dstar(GAMMA_COSTS, repmin, rem)(R, Rb)
        ls = [gamma(L - 1) - gamma(L) for L in range(repmin, rem + 1)]
        if ls:
            lam = max(ls)
            a0 = next((a for a in range(k) if R[a] != Rb[a]), k)
            formula = sum(max(0, gamma(R[a]) - 1 - a + lam) for a in range(a0, k))
            bad += dstar != formula or lam not in (0, -2)
        else:
            bad += dstar != 0
        bad += dstar > margin_D(R, Rb)
        if rem >= repmin + 1 or (rem >= 3 and repmin <= 3):
            bad += dstar != margin_D(R, Rb)
    check("Theorem 3, gamma costs: D*_i from its definition = formula with lambda_i in {0, -2}; D*_i <= D; D*_i = D "
          "when n - i >= REPMIN + 1 or (n - i >= 3 and REPMIN <= 3) (4000 seeded random cases)", bad == 0, f"{bad} bad")


def part_tightness():
    s = word("aabbbbabbaabaaaab")
    V = value_function(s, 2, 2)
    _, st = forward_dp(s, 2, 2)
    c11 = st[11]
    ok = c11.get((9, 5)) == 53 and c11.get((3, 5)) == 56 and min(c11.values()) == 53
    ok &= V(11, (3, 5)) == 13 and V(11, (9, 5)) == 18 and margin_D((3, 5), (9, 5)) == 5
    rep, new = GAMMA_COSTS[1], GAMMA_COSTS[2]
    ok &= rep(3, 0) + rep(3, 1) == 13 and new(3, 3) + new(3, 5) == 18
    ok &= s[11:14] == s[8:11] and s[14:17] == s[9:12]                      # the two repeats are allowed
    opt = enumerate_optimum(s, 2, 2)
    ok &= opt == V(0, (1, 1)) == 69 == 56 + 13
    check("Proposition 4: values 53 and 56 at position 11, V(11,(3,5)) = 13, V(11,(9,5)) = 18 = 13 + D, OPT = 69",
          ok, f"V = {V(11, (3, 5))}, {V(11, (9, 5))}; D = {margin_D((3, 5), (9, 5))}; OPT = {opt}")

    def NB(i, R, Rb):
        return sum(gamma(R[a]) - 1 for a in range(len(R)) if R[a] != Rb[a])

    def NB0(i, R, Rb):
        return sum(max(0, gamma(R[a]) - 1 - a) for a in range(len(R)) if R[a] != Rb[a])
    ok = True
    for mg in (NB, NB0):
        log = []
        got, _ = forward_dp(s, 2, 2, margin=mg, pick=chooser("lexmin"), log=log)
        entry = [e for e in log if e[0] == 11][0]
        ok &= got == 71 and (3, 5) in entry[1] and (3, 5) not in entry[3] and mg(11, (3, 5), (9, 5)) == 2
    check("Proposition 4: NB and NB0 give the pair margin 2, delete (3,5) at position 11 and return 71", ok)


def part_remark5():
    s = word("aaaababa")
    V = value_function(s, 2, 2, NONMONO_COSTS)
    lit, rep, new = NONMONO_COSTS
    m_full = margin_Dstar(NONMONO_COSTS, 2, len(s) - 2)
    m_ja = margin_Dstar(NONMONO_COSTS, 2, len(s) - 2, only_j_equal_a=True)
    ok = V(2, (2, 1)) == 22 and V(2, (1, 1)) == 27
    ok &= new(2, 1) + lit + rep(3, 1) == 22 and new(2, 1) + lit + new(3, 2) == 27
    ok &= m_ja((2, 1), (1, 1)) == 4 and m_full((2, 1), (1, 1)) == 6
    _, st = forward_dp(s, 2, 2, NONMONO_COSTS)
    ok &= set(st[2]) == {(1, 1)}
    check("Remark 5: V(2,(2,1)) = 22, V(2,(1,1)) = 27; j = a margin 4 < 5 <= 6 = D*; (2,1) not reachable at "
          "position 2", ok, f"V = {V(2, (2, 1))}, {V(2, (1, 1))}; margins {m_ja((2, 1), (1, 1))}, "
          f"{m_full((2, 1), (1, 1))}")


def part_hypotheses():
    for text in ("aaaaba", "bbbbab"):
        s = word(text)
        ok = True
        for k in (1, 2, 3):
            opt = enumerate_optimum(s, k, 1)
            ok &= opt == value_function(s, k, 1)(0, (1,) * k) == 32
            ok &= all_choice_results(s, k, 1, G3) == {33}
        check(f"Proposition 6(a): '{text}', REPMIN = 1, k = 1, 2, 3: OPT = 32 (two methods), G3-pruned DP = 33 for "
              f"every comparator choice", ok)
    s = word("aaaaba")
    lit, rep, new = GAMMA_COSTS
    ok = lit + rep(1, 0) + new(2, 2) + lit + rep(1, 0) == 32
    ok &= s[1] == s[0] and s[2:4] == s[0:2] and s[5] == s[3]
    log = []
    forward_dp(s, 1, 1, margin=G3, pick=chooser("lexmin"), log=log)
    pos4 = [e for e in log if e[0] == 4][0]
    ok &= pos4[1].get((2,)) == 19 and pos4[1].get((1,)) == 15 and pos4[2] == (1,) and (2,) not in pos4[3]
    V1 = value_function(s, 1, 1)
    ok &= V1(4, (2,)) == 13 and V1(4, (1,)) == 18 and margin_D((2,), (1,)) == 2      # Theorem 1 fails: 18 > 13 + 2
    for text in ("aaaaba", "bbbbab"):                                                 # the states of the hand proof
        for k in (1, 2, 3):
            one, two = (1,) * k, (2,) + (1,) * (k - 1)
            _, st = forward_dp(word(text), k, 1)
            ok &= all(set(st[x]) == {one} for x in (1, 2, 3)) and st[2][one] == 13
            ok &= st[4] == {one: 15, two: 19} and margin_D(two, one) == 2
    check("Proposition 6(a): the optimal parse costs 9 + 4 + 6 + 9 + 4 = 32; at position 4, (2) = 19 is deleted "
          "against (1) = 15 (margin 2); V(4,(1)) = 18 > V(4,(2)) + D = 13 + 2 (k = 1); positions 1-3 hold only 1^k "
          "and position 4 exactly {1^k: 15, (2,1^(k-1)): 19} (both strings, k = 1, 2, 3)", ok)

    # (b) adaptive costs on 'bbba', k = 1, REPMIN = 2
    s = word("bbba")
    n = len(s)
    ml = match_table(s)

    def parses():
        out = []

        def rec(i, R, toks):
            if i == n:
                out.append(tuple(toks))
                return
            rec(i + 1, R, toks + [("lit", s[i], 0)])
            r = R[0]
            if r <= i:
                for L in range(2, ml[i][r] + 1):
                    rec(i + L, R, toks + [("rep", None, 1 + gamma(L))])
            for d in range(1, i + 1):
                for L in range(2, ml[i][d] + 1):
                    rec(i + L, (d,), toks + [("new", None, gamma(L - 1) + gamma(d))])
        rec(0, (1,), [])
        return out

    def price(toks):
        """(probability, static bits); the cost in bits is static - log2(probability)."""
        cnt = {"lit": 0, "rep": 0, "new": 0}
        sym = {}
        p = Fraction(1)
        stat = 0
        for typ, ch, bits in toks:
            p *= Fraction(cnt[typ] + 1, sum(cnt.values()) + 3)
            if typ == "lit":
                p *= Fraction(sym.get(ch, 0) + 1, cnt["lit"] + 4)
                sym[ch] = sym.get(ch, 0) + 1
            stat += bits
            cnt[typ] += 1
        return p, stat

    def key(toks):
        """2^cost as an exact rational: comparing keys compares costs exactly."""
        p, stat = price(toks)
        return Fraction(2 ** stat) / p

    allp = parses()
    keys = sorted(key(t) for t in allp)
    ok = len(allp) == 3 and keys == [Fraction(2100), Fraction(4 * 600), Fraction(16 * 600)]
    # one-label DP over (position, slots)
    labels = [dict() for _ in range(n + 1)]
    labels[0][(1,)] = ()
    ties = 0
    for i in range(n):
        for R, tk in list(labels[i].items()):
            cands = [(i + 1, R, tk + (("lit", s[i], 0),))]
            if R[0] <= i:
                cands += [(i + L, R, tk + (("rep", None, 1 + gamma(L)),)) for L in range(2, ml[i][R[0]] + 1)]
            for d in range(1, i + 1):
                cands += [(i + L, (d,), tk + (("new", None, gamma(L - 1) + gamma(d)),)) for L in range(2, ml[i][d] + 1)]
            for i2, R2, t2 in cands:
                old = labels[i2].get(R2)
                if old is not None and key(t2) == key(old):
                    ties += 1
                if old is None or key(t2) < key(old):
                    labels[i2][R2] = t2
    dp_key = min(key(t) for t in labels[n].values())
    kept3 = labels[3][(1,)]
    ok &= dp_key == Fraction(2400) and ties == 0 and [t[0] for t in kept3] == ["lit", "new"]
    ok &= key(kept3) == Fraction(192) and key((("lit", 1, 0),) * 3) == Fraction(200)
    ok &= Fraction(2400) / 192 == Fraction(25, 2) and Fraction(2100) / 200 == Fraction(21, 2)   # cost of the last literal
    bits = lambda x: math.log2(x)
    check("Proposition 6(b): 'bbba' has 3 parses, 2^cost = 2100, 2400, 9600 (11.0362, 11.2288, 13.2288 bits); the "
          "one-label DP keeps 'literal, new match' at (3,(1)) (2^cost 192 < 200) and returns 11.2288 bits; no ties", ok,
          f"optimum {bits(keys[0]):.4f} bits, one-label DP {bits(dp_key):.4f} bits")


def part_naive():
    def K1(i, R, Rb):
        return gamma(R[0]) - 1

    def NS(i, R, Rb):
        return sum(gamma(x) - 1 for x in set(R) - set(Rb))

    def NB(i, R, Rb):
        return sum(gamma(R[a]) - 1 for a in range(len(R)) if R[a] != Rb[a])

    def NB0(i, R, Rb):
        return sum(max(0, gamma(R[a]) - 1 - a) for a in range(len(R)) if R[a] != Rb[a])
    rows = (("K1", K1, 2, "abaababbbbab", 52, {53}), ("K1", K1, 3, "abaababbbbab", 52, {53}),
            ("NS", NS, 2, "abbbbabbbaaabba", 54, {56}), ("NS", NS, 3, "abbaabbbbbaaabaa", 71, {72}),
            ("NB", NB, 2, "aabbbbabbaabaaaab", 69, {71}), ("NB0", NB0, 2, "aabbbbabbaabaaaab", 69, {71}),
            ("K1", K1, 3, "aaabbaaaaba", 50, {50, 51}))
    for name, mg, k, text, opt, pruned in rows:
        s = word(text)
        o1 = enumerate_optimum(s, k, 2)
        o2 = value_function(s, k, 2)(0, (1,) * k)
        res = all_choice_results(s, k, 2, mg)
        g3 = all_choice_results(s, k, 2, G3)
        check(f"Remark 7: {name}, k = {k}, '{text}': OPT = {opt} (two methods), pruned DP over every comparator "
              f"choice = {sorted(pruned)}; G3 = OPT for every choice", o1 == o2 == opt and res == pruned and g3 == {opt},
              f"OPT {o1}/{o2}, pruned {sorted(res)}, G3 {sorted(g3)}")
    pairs1 = [(R, Rb) for R in itertools.product(range(1, 9), repeat=1)
              for Rb in itertools.product(range(1, 9), repeat=1) if R != Rb]
    ok = all(mg(0, R, Rb) == margin_D(R, Rb) for mg in (K1, NS, NB, NB0) for R, Rb in pairs1)
    check("Remark 7: for k = 1 the four margins equal D (tuples with entries 1..8)", ok,
          f"{len(pairs1)} ordered pairs, 4 margins")


def main():
    t0 = time.time()
    for name, fn in (("M", part_machinery), ("G", part_theorem1), ("P", part_theorem2), ("S", part_theorem3),
                     ("T", part_tightness), ("R", part_remark5), ("H", part_hypotheses), ("N", part_naive)):
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
