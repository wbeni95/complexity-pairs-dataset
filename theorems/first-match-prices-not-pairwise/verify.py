#!/usr/bin/env python3
"""Verifier for theorems/first-match-prices-not-pairwise (see README.md in this folder).

Exact rational checks (fractions.Fraction) of every computed fact in the note; the proof is in the README.
Standard library only, deterministic (fixed seeds), offline, well under a second.

Objects. k rules; item i is matched by the set M_i and pays cost[i][r] if r is the first rule of the order that
matches it (a fixed default if M_i is empty). price(order) = sum over items. "Pairwise form": there are C and
w_xy (x != y) with price(order) = C + sum_{x != y} w_xy [x before y] for every order.

Checks:
  P  the 6-order parametrisation: order -> (s_ab, s_ac, s_bc) is injective and misses exactly the two cyclic
     sign vectors (+,-,+) and (-,+,-);
  T  Theorem: one item matched by a, b, c with costs (1, 0, 0) has price [a first], and the linear system
     "price = pairwise form" over the 6 orders has no rational solution (rank test);
  L  least squares: the minimum over (C, w) of sum_order (price - fit)^2 is exactly 1/3, attained by
     -1/6 + ([a before b] + [a before c]) / 2;
  R  Remark 1: costs (x, y, z) on one item matched by a, b, c give a pairwise price iff x = y = z
     (all 4^3 integer triples in 0..3);
  K  Remark 2: for k = 4, 5 the same item plus k - 3 rules that match nothing is not pairwise (rank test over
     all k! orders);
  Q  Proposition 1: if every item is matched by at most two rules, the explicit pairwise weights of the proof
     reproduce the price on every order (k = 2..5, 300 seeded random instances).
Exit code 0 only if every check passes.
Usage (from the repository root): python theorems/first-match-prices-not-pairwise/verify.py
"""
import itertools
import random
import sys
from fractions import Fraction

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


# ------------------------------------------------------------------------------------------------ model
def price(order, items):
    """items: list of (match_set, cost_dict, default). The first rule of the order in match_set captures."""
    total = 0
    for match, cost, default in items:
        first = next((r for r in order if r in match), None)
        total += default if first is None else cost[first]
    return total


def before(order, x, y):
    return 1 if order.index(x) < order.index(y) else 0


# ------------------------------------------------------------------------------------------------ exact algebra
def rank(rows):
    """Rank of a matrix of Fractions (Gaussian elimination)."""
    A = [list(map(Fraction, r)) for r in rows]
    rk, cols = 0, (len(A[0]) if A else 0)
    for c in range(cols):
        piv = next((i for i in range(rk, len(A)) if A[i][c] != 0), None)
        if piv is None:
            continue
        A[rk], A[piv] = A[piv], A[rk]
        for i in range(len(A)):
            if i != rk and A[i][c] != 0:
                f = A[i][c] / A[rk][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[rk])]
        rk += 1
    return rk


def solve(M, v):
    """Solve the square system M x = v exactly (M invertible)."""
    n = len(M)
    A = [list(map(Fraction, M[i])) + [Fraction(v[i])] for i in range(n)]
    for c in range(n):
        piv = next(i for i in range(c, n) if A[i][c] != 0)
        A[c], A[piv] = A[piv], A[c]
        A[c] = [x / A[c][c] for x in A[c]]
        for i in range(n):
            if i != c and A[i][c] != 0:
                f = A[i][c]
                A[i] = [a - f * b for a, b in zip(A[i], A[c])]
    return [A[i][n] for i in range(n)]


def pairwise_design(rules):
    """Rows: orders of `rules`; columns: constant and [x before y] for every ordered pair x != y."""
    pairs = [(x, y) for x in rules for y in rules if x != y]
    orders = list(itertools.permutations(rules))
    X = [[1] + [before(o, x, y) for x, y in pairs] for o in orders]
    return orders, pairs, X


def is_pairwise(rules, items):
    orders, _, X = pairwise_design(rules)
    y = [price(o, items) for o in orders]
    return rank(X) == rank([row + [yy] for row, yy in zip(X, y)])


# ------------------------------------------------------------------------------------------------ main
def main():
    R3 = ("a", "b", "c")
    orders = list(itertools.permutations(R3))

    # P: parametrisation
    sign = {o: tuple(1 if before(o, x, y) else -1 for x, y in (("a", "b"), ("a", "c"), ("b", "c")))
            for o in orders}
    image = set(sign.values())
    check("P the map order -> (s_ab, s_ac, s_bc) is injective on the 6 orders", len(image) == 6)
    check("P its image misses exactly the cyclic vectors (+,-,+) and (-,+,-)",
          set(itertools.product((1, -1), repeat=3)) - image == {(1, -1, 1), (-1, 1, -1)})

    # T: the theorem
    item = [({"a", "b", "c"}, {"a": 1, "b": 0, "c": 0}, 0)]
    prices = {"".join(o): price(o, item) for o in orders}
    check("T price = [a first] on the 6 orders",
          all(prices["".join(o)] == (1 if o[0] == "a" else 0) for o in orders), str(prices))
    check("T no C, w_xy with price = C + sum w_xy [x before y] (rank test over Q)", not is_pairwise(R3, item))
    # the hand proof: pairs of orders that differ in exactly one sign
    pairs_used = [(("a", "b", "c"), ("a", "c", "b"), 2), (("b", "a", "c"), ("b", "c", "a"), 1),
                  (("c", "a", "b"), ("c", "b", "a"), 0)]
    check("T the three order pairs of the proof differ in exactly one sign (s_bc, s_ac, s_ab) and have equal price",
          all([i for i in range(3) if sign[o1][i] != sign[o2][i]] == [j] and price(o1, item) == price(o2, item)
              for o1, o2, j in pairs_used))

    # L: least squares in the basis 1, s_ab, s_ac, s_bc (same span as 1 and all [x before y])
    X = [[1, *sign[o]] for o in orders]
    y = [price(o, item) for o in orders]
    XtX = [[sum(X[r][i] * X[r][j] for r in range(6)) for j in range(4)] for i in range(4)]
    Xty = [sum(X[r][i] * y[r] for r in range(6)) for i in range(4)]
    coef = solve(XtX, Xty)
    fit = [sum(c * x for c, x in zip(coef, row)) for row in X]
    rss = sum((a - b) ** 2 for a, b in zip(y, fit))
    D = pairwise_design(R3)[2]  # rows in the same order as `orders`
    check("L span{1, s_ab, s_ac, s_bc} = span{1, [x before y]} as functions on the 6 orders (ranks 4, 4, 4)",
          rank(X) == 4 and rank(D) == 4 and rank([X[i] + D[i] for i in range(6)]) == 4)
    check("L least-squares coefficients (C, alpha, beta, gamma) = (1/3, 1/4, 1/4, 0)",
          coef == [Fraction(1, 3), Fraction(1, 4), Fraction(1, 4), Fraction(0)], str([str(c) for c in coef]))
    check("L minimum sum of squared residuals over the 6 orders = 1/3", rss == Fraction(1, 3), str(rss))
    alt = [Fraction(-1, 6) + Fraction(before(o, "a", "b") + before(o, "a", "c"), 2) for o in orders]
    check("L the fit equals -1/6 + ([a before b] + [a before c])/2", alt == fit,
          "fitted " + ", ".join(f"{''.join(o)}:{v}" for o, v in zip(orders, fit)))

    # R: costs (x, y, z)
    bad = []
    for x, yv, z in itertools.product(range(4), repeat=3):
        it = [({"a", "b", "c"}, {"a": x, "b": yv, "c": z}, 0)]
        if is_pairwise(R3, it) != (x == yv == z):
            bad.append((x, yv, z))
    check("R pairwise iff x = y = z, for all 64 cost triples in {0..3}^3", not bad, f"exceptions {bad}")

    # K: more rules
    for k in (4, 5):
        rules = tuple("abcdefg"[:k])
        it = [({"a", "b", "c"}, {"a": 1, "b": 0, "c": 0}, 0)]
        check(f"K k = {k}: the same item, {k - 3} rule(s) matching nothing: not pairwise (over all {len(list(itertools.permutations(rules)))} orders)",
              not is_pairwise(rules, it))

    # Q: at most two matching rules -> explicit pairwise weights
    rng = random.Random("first-match-prices-not-pairwise|Q")
    nbad, ntot = 0, 0
    for _ in range(300):
        k = rng.randint(2, 5)
        rules = tuple(range(k))
        items = []
        for _ in range(rng.randint(1, 6)):
            t = rng.choice([0, 1, 2, 2])
            match = set(rng.sample(rules, t))
            items.append((match, {r: rng.randint(0, 9) for r in rules}, rng.randint(0, 9)))
        C, w = 0, {}
        for match, cost, default in items:
            if not match:
                C += default
            elif len(match) == 1:
                C += cost[next(iter(match))]
            else:
                u, v = sorted(match)
                C += cost[v]
                w[(u, v)] = w.get((u, v), 0) + cost[u] - cost[v]
        for o in itertools.permutations(rules):
            ntot += 1
            if price(o, items) != C + sum(c * before(o, u, v) for (u, v), c in w.items()):
                nbad += 1
    check("Q at most two matching rules per item: price = C + sum w_uv [u before v] with the weights of the proof",
          nbad == 0, f"{ntot} (instance, order) pairs, {nbad} mismatches")

    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
