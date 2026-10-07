"""Harness for the entry "interval DP with inclusion-monotone weights (maximum-cost BST)".

Instances come in two forms (the implementations accept both):
  (sense, w)  sense "max" or "min"; w = tuple of n + 1 rows, w[i][j] the weight of the interval (i, j) for
              0 <= i < j <= n (entries with j <= i are None). Precondition: w monotone under inclusion for "max"
              (w(b, c) <= w(a, d) whenever a <= b < c <= d), anti-monotone for "min".
  (p, q)      the maximum-cost BST: p = (p_1..p_n) key frequencies, q = (q_0..q_n) gap frequencies, all
              non-negative integers here; it stands for "max" with w(i, j) = q_i + sum_{l=i+1..j} (p_l + q_l).
Output: c(0, n) for c(i, i) = 0, c(i, j) = w(i, j) + opt_{i<k<=j} [c(i, k-1) + c(k, j)], opt = max or min, i.e. the
max (min) over all binary trees with in-order nodes 1..n of sum_v w(I_v), I_v the interval spanned by v's subtree;
an exact number (int, or Fraction for the rational families).

V1 battery (generate): the rng picks one of three categories with equal probability, then a family in it.
  BST families (14, form (p, q), all frequencies >= 0): many full of ties (frequencies in {0, 1}, in [0, 3], all
      zero, all equal, mostly zero), wide random weights, one heavy key, one heavy gap, geometric weights, ramps,
      gaps only, keys only, two heavy end keys, and a boundary pattern for the (max,+) recurrence (p = 0, q = (0, ..., 0, 1)).
  General monotone families (11, form ("max", w)): maxima of random values over sub-intervals, sums of sparse
      non-negative values over sub-intervals, non-decreasing functions of the length, capped and squared frequency
      sums, range maxima, random monotone tables built upwards (generic, and "tight" ones with many equalities),
      all-negative monotone tables, exact rationals, products. Most instances with n >= 3 are not BST weights of
      any frequencies (not separable as F(j) - G(i)); experiments/2026-10-07_max_cost_bst_checks.py counts this.
  Anti-monotone MIN families (7, form ("min", w)): constant minus a monotone table (sub-interval maxima, sums,
      upward-built tables, tight tables), non-increasing functions of the length, reciprocals R / (1 + S) of
      frequency sums, and negated BST weights.

check(): an oracle written separately from the implementations, with two tiers.
  n <= BRUTE_MAX_N   every tree shape on n nodes is enumerated explicitly (Catalan(n) shapes). BST form: the level
                     of every key and gap is recorded and the cost is computed from the levels (no w, no
                     recurrence). Table form: the interval spanned by every node is recorded and the value is the
                     sum of the table entries of those intervals (no recurrence). The output must equal the optimum.
  n <= CERT_MAX_N    an exact certificate, checked here. For "max": lower bound = an explicit path tree, built
                     top-down, valued from its levels (BST) or its node intervals (table); upper bound = a table
                     U(a, b) with U(a, a) = 0 and U(a, b) >= W(a, b) + U(a, k-1) + U(k, b) for EVERY root
                     a < k <= b, all checked, W summed directly from p and q (BST) or read from the input (table).
                     By induction over a tree's root, every tree on (a, b) is worth at most U(a, b), however U was
                     obtained. For "min" the roles are mirrored (explicit path = upper bound, table L with every
                     L(a, b) <= W(a, b) + L(a, k-1) + L(k, b) = lower bound). If the bounds meet, the optimum is
                     certified and the output must equal it; outputs outside the bounds are rejected; otherwise None.
                     The table is the best-path value per interval, so a valid certificate is an instance-wise check
                     of Theorem E', not an assumption of it.
  larger n           None.

V2 (measure "reported"): generate_scaling draws a family from SCALING_FAMILIES (all BST families and every integer
family of the other two categories) and builds the instance from CountingInt, a number type that counts every
COMPARISON of two cost values (<, <=, >, >=) made by the unchanged implementations; reported_cost returns the
count. The counts depend on n only (every interval is processed the same way on every input, in both forms and
both senses); the validator's shape probe re-draws the instance, and with it the family, at small n.
"""
from fractions import Fraction

# --------------------------------------------------------------------------------------------------
# V1 instances: the maximum-cost BST (form (p, q))
# --------------------------------------------------------------------------------------------------

FAMILIES = ("bits", "small", "zero", "constant", "wide", "one_heavy_key", "one_heavy_gap", "geometric",
            "ramp", "sparse", "gaps_only", "keys_only", "heavy_ends", "near_miss")


def _instance(n, rng, family):
    if family == "bits":
        p = [rng.randint(0, 1) for _ in range(n)]
        q = [rng.randint(0, 1) for _ in range(n + 1)]
    elif family == "small":
        p = [rng.randint(0, 3) for _ in range(n)]
        q = [rng.randint(0, 3) for _ in range(n + 1)]
    elif family == "zero":
        p, q = [0] * n, [0] * (n + 1)
    elif family == "constant":
        a, b = rng.randint(0, 5), rng.randint(0, 5)
        p, q = [a] * n, [b] * (n + 1)
    elif family == "wide":
        p = [rng.randint(0, 1000) for _ in range(n)]
        q = [rng.randint(0, 1000) for _ in range(n + 1)]
    elif family == "one_heavy_key":
        p = [rng.randint(0, 3) for _ in range(n)]
        q = [rng.randint(0, 3) for _ in range(n + 1)]
        if n:
            p[rng.randrange(n)] = rng.randint(10, 10 * n * n + 10)
    elif family == "one_heavy_gap":
        p = [rng.randint(0, 3) for _ in range(n)]
        q = [rng.randint(0, 3) for _ in range(n + 1)]
        q[rng.randrange(n + 1)] = rng.randint(10, 10 * n * n + 10)
    elif family == "geometric":
        p = [2 ** m for m in range(n)]
        q = [rng.randint(0, 1) for _ in range(n + 1)]
        if rng.random() < 0.5:
            p.reverse()
    elif family == "ramp":
        p = [m + 1 for m in range(n)]
        q = [rng.randint(0, 2) for _ in range(n + 1)]
        if rng.random() < 0.5:
            p.reverse()
    elif family == "sparse":
        p = [rng.randint(1, 50) if rng.random() < 0.15 else 0 for _ in range(n)]
        q = [rng.randint(1, 50) if rng.random() < 0.15 else 0 for _ in range(n + 1)]
    elif family == "gaps_only":
        p = [0] * n
        q = [rng.randint(0, 5) for _ in range(n + 1)]
    elif family == "keys_only":
        p = [rng.randint(0, 5) for _ in range(n)]
        q = [0] * (n + 1)
    elif family == "heavy_ends":
        p = [rng.randint(0, 9) for _ in range(n)]
        q = [rng.randint(0, 9) for _ in range(n + 1)]
        if n:
            heavy = n * (sum(p) + sum(q)) + 1
            p[0] = p[-1] = heavy
    elif family == "near_miss":
        p = [0] * n
        q = [0] * (n + 1)
        q[n if rng.random() < 0.5 else 0] = rng.randint(1, 3)
    else:
        raise ValueError(family)
    return tuple(p), tuple(q)


# --------------------------------------------------------------------------------------------------
# V1 instances: general monotone tables ("max") and anti-monotone tables ("min")
# --------------------------------------------------------------------------------------------------

GENERAL_FAMILIES = ("g_submax", "g_subsum", "g_length", "g_capped", "g_square", "g_rangemax", "g_upward",
                    "g_tight", "g_negative", "g_rational", "g_product")
MIN_FAMILIES = ("a_neg_submax", "a_c_minus_subsum", "a_decreasing_length", "a_neg_upward", "a_neg_tight",
                "a_reciprocal", "a_neg_bst")
ALL_FAMILIES = FAMILIES + GENERAL_FAMILIES + MIN_FAMILIES
SCALING_FAMILIES = tuple(f for f in ALL_FAMILIES if f not in ("g_rational", "g_product", "a_reciprocal"))


def _table(n):
    return [[None] * (n + 1) for _ in range(n + 1)]


def _freeze(w):
    return tuple(tuple(row) for row in w)


def _upward(n, rng, base_max, inc_max, p_zero):
    """Random monotone table built by increasing length: w(i, j) = max(w(i+1, j), w(i, j-1)) + increment >= 0."""
    w = _table(n)
    for i in range(n):
        w[i][i + 1] = rng.randint(0, base_max)
    for d in range(2, n + 1):
        for i in range(n - d + 1):
            j = i + d
            inc = 0 if rng.random() < p_zero else rng.randint(0, inc_max)
            w[i][j] = max(w[i + 1][j], w[i][j - 1]) + inc
    return w


def _submax(n, rng, vmax):
    """w(i, j) = max of independent random values v(b, c) over the sub-intervals (b, c) of (i, j)."""
    w = _table(n)
    for d in range(1, n + 1):
        for i in range(n - d + 1):
            j = i + d
            v = rng.randint(0, vmax)
            w[i][j] = v if d == 1 else max(v, w[i + 1][j], w[i][j - 1])
    return w


def _subsum(n, rng, mmax, density):
    """w(i, j) = sum of sparse values m(x, y) >= 0 over all sub-intervals i <= x < y <= j (inclusion-exclusion)."""
    w = _table(n)

    def g(a, b):
        return w[a][b] if b > a else 0

    for d in range(1, n + 1):
        for i in range(n - d + 1):
            j = i + d
            m = rng.randint(1, mmax) if rng.random() < density else 0
            w[i][j] = m + g(i + 1, j) + g(i, j - 1) - g(i + 1, j - 1)
    return w


def _increments(n, rng):
    """h(0..n), h(0) = 0, non-decreasing, with a random increment profile."""
    kind = rng.choice(("random", "concave", "convex", "steps"))
    h = [0]
    for d in range(1, n + 1):
        if kind == "random":
            inc = rng.randint(0, 3)
        elif kind == "concave":
            inc = max(0, n - d + rng.randint(-1, 1))
        elif kind == "convex":
            inc = d + rng.randint(0, 1)
        else:
            inc = 5 if rng.random() < 0.3 else 0
        h.append(h[-1] + inc)
    return h


def _length(n, rng):
    h = _increments(n, rng)
    w = _table(n)
    for i in range(n + 1):
        for j in range(i + 1, n + 1):
            w[i][j] = h[j - i]
    return w


def _sums(n, rng, vmax):
    """S(i, j) = sum of x_i..x_j with x >= 0 random (the shape of BST weights)."""
    x = [rng.randint(0, vmax) for _ in range(n + 1)]
    pre = [0]
    for v in x:
        pre.append(pre[-1] + v)
    return lambda i, j: pre[j + 1] - pre[i]


def _from_function(n, f):
    w = _table(n)
    for i in range(n + 1):
        for j in range(i + 1, n + 1):
            w[i][j] = f(i, j)
    return w


def _general(n, rng, family):
    if family == "g_submax":
        w = _submax(n, rng, rng.choice((1, 3, 20, 1000)))
    elif family == "g_subsum":
        w = _subsum(n, rng, rng.choice((3, 10)), rng.choice((0.1, 0.3, 0.6)))
    elif family == "g_length":
        w = _length(n, rng)
    elif family == "g_capped":
        s = _sums(n, rng, rng.choice((1, 5, 20)))
        cap = rng.randint(0, s(0, n) if n else 0)
        w = _from_function(n, lambda i, j: min(cap, s(i, j)))
    elif family == "g_square":
        s = _sums(n, rng, rng.choice((1, 3, 10)))
        w = _from_function(n, lambda i, j: s(i, j) ** 2)
    elif family == "g_rangemax":
        a = [rng.randint(0, rng.choice((2, 10, 100))) for _ in range(n + 1)]
        w = _table(n)
        for i in range(n + 1):
            m = a[i]
            for j in range(i + 1, n + 1):
                m = max(m, a[j])
                w[i][j] = m
    elif family == "g_upward":
        w = _upward(n, rng, rng.choice((0, 5, 50)), rng.choice((1, 5, 50)), 0.3)
    elif family == "g_tight":
        w = _upward(n, rng, 2, 1, 0.85)
    elif family == "g_negative":
        a = _upward(n, rng, 20, 10, 0.3)
        shift = (a[0][n] if n else 0) + rng.randint(1, 50)
        w = _from_function(n, lambda i, j: a[i][j] - shift)
    elif family == "g_rational":
        a = _submax(n, rng, rng.choice((3, 20)))
        h = _increments(n, rng)
        den = rng.choice((2, 3, 7))
        w = _from_function(n, lambda i, j: Fraction(a[i][j], den) + Fraction(h[j - i], 3))
    elif family == "g_product":
        x = [rng.choice((0, 0, 1, 2)) for _ in range(n)]
        w = _table(n)
        for i in range(n + 1):
            acc = 1
            for j in range(i + 1, n + 1):
                acc *= 1 + x[j - 1]
                w[i][j] = acc
    else:
        raise ValueError(family)
    return "max", _freeze(w)


def _anti(n, rng, family):
    if family == "a_neg_submax":
        a = _submax(n, rng, rng.choice((1, 3, 20)))
        k = rng.randint(0, 20)
        w = _from_function(n, lambda i, j: k - a[i][j])
    elif family == "a_c_minus_subsum":
        a = _subsum(n, rng, rng.choice((3, 10)), rng.choice((0.1, 0.3, 0.6)))
        top = (a[0][n] if n else 0) + rng.randint(0, 5)
        w = _from_function(n, lambda i, j: top - a[i][j])
    elif family == "a_decreasing_length":
        h = _increments(n, rng)
        top = h[n] + rng.randint(0, 3)
        w = _from_function(n, lambda i, j: top - h[j - i])
    elif family == "a_neg_upward":
        a = _upward(n, rng, rng.choice((0, 5, 50)), rng.choice((1, 5, 50)), 0.3)
        w = _from_function(n, lambda i, j: -a[i][j])
    elif family == "a_neg_tight":
        a = _upward(n, rng, 2, 1, 0.85)
        w = _from_function(n, lambda i, j: 3 - a[i][j])
    elif family == "a_reciprocal":
        s = _sums(n, rng, rng.choice((1, 5)))
        r = rng.choice((1, 6, 60))
        w = _from_function(n, lambda i, j: Fraction(r, 1 + s(i, j)))
    elif family == "a_neg_bst":
        p, q = _instance(n, rng, rng.choice(FAMILIES))
        b = bst_weights(p, q)
        w = _from_function(n, lambda i, j: -b[i][j])
    else:
        raise ValueError(family)
    return "min", _freeze(w)


def instance_of(family, n, rng):
    """One instance of the named family (any category)."""
    if family in FAMILIES:
        return _instance(n, rng, family)
    if family in GENERAL_FAMILIES:
        return _general(n, rng, family)
    if family in MIN_FAMILIES:
        return _anti(n, rng, family)
    raise ValueError(family)


def generate(n, rng):
    category = (FAMILIES, GENERAL_FAMILIES, MIN_FAMILIES)[rng.randrange(3)]
    return instance_of(category[rng.randrange(len(category))], n, rng)


# --------------------------------------------------------------------------------------------------
# Helpers: forms, weights, the precondition
# --------------------------------------------------------------------------------------------------

def is_table_form(instance):
    return isinstance(instance[0], str)


def bst_weights(p, q):
    """w(i, j) = q_i + sum_{l=i+1..j} (p_l + q_l) as a table (None for j <= i)."""
    n = len(p)
    w = _table(n)
    for i in range(n + 1):
        acc = q[i]
        for j in range(i + 1, n + 1):
            acc += p[j - 1] + q[j]
            w[i][j] = acc
    return _freeze(w)


def as_table(instance):
    """(sense, w) for either form."""
    if is_table_form(instance):
        return instance[0], instance[1]
    return "max", bst_weights(*instance)


def is_monotone(w):
    """Local test, O(n^2): w(i, j) >= w(i+1, j) and w(i, j) >= w(i, j-1) for j - i >= 2. Equivalent to monotonicity
    under inclusion, because a nested pair (b, c) inside (a, d) is reached from (a, d) by single-step shrinks that
    keep the interval non-empty (a, d) -> (a+1, d) -> ... -> (b, d) -> (b, d-1) -> ... -> (b, c)."""
    n = len(w) - 1
    for d in range(2, n + 1):
        for i in range(n - d + 1):
            j = i + d
            if w[i][j] < w[i + 1][j] or w[i][j] < w[i][j - 1]:
                return False
    return True


def satisfies_precondition(instance):
    sense, w = as_table(instance)
    if sense == "max":
        return is_monotone(w)
    return is_monotone(tuple(tuple(None if x is None else -x for x in row) for row in w))


# --------------------------------------------------------------------------------------------------
# Independent oracle, tier 1: every tree shape
# --------------------------------------------------------------------------------------------------

BRUTE_MAX_N = 10
CERT_MAX_N = 200
_shape_cache = {}
_interval_shape_cache = {}
_result_cache = {}


def _shapes(size):
    """Every BST shape on `size` keys as (key_levels, gap_levels), both in symmetric (in-order) order."""
    if size not in _shape_cache:
        if size == 0:
            out = [((), (0,))]  # an empty tree: its single gap sits at the root position
        else:
            out = []
            for left in range(size):  # the root is the (left + 1)-th smallest key
                for lk, lg in _shapes(left):
                    for rk, rg in _shapes(size - 1 - left):
                        out.append((tuple(x + 1 for x in lk) + (0,) + tuple(x + 1 for x in rk),
                                    tuple(x + 1 for x in lg) + tuple(x + 1 for x in rg)))
        _shape_cache[size] = out
    return _shape_cache[size]


def _interval_shapes(size):
    """Every tree shape on nodes 1..size as the tuple of the intervals (lo, hi) spanned by its nodes' subtrees."""
    if size not in _interval_shape_cache:
        if size == 0:
            out = [()]
        else:
            out = []
            for root in range(1, size + 1):
                for left in _interval_shapes(root - 1):
                    for right in _interval_shapes(size - root):
                        out.append(((0, size),) + left + tuple((lo + root, hi + root) for lo, hi in right))
        _interval_shape_cache[size] = out
    return _interval_shape_cache[size]


def cost_from_levels(p, q, key_levels, gap_levels):
    return sum(pm * (lev + 1) for pm, lev in zip(p, key_levels)) + sum(qj * lev for qj, lev in zip(q, gap_levels))


def brute_force_max(p, q):
    """Maximum BST cost over every explicit tree shape, each cost evaluated from the levels."""
    return max(cost_from_levels(p, q, k, g) for k, g in _shapes(len(p)))


def brute_force_table(sense, w):
    """Optimum over every explicit tree shape of the sum of w over the node intervals."""
    vals = (sum(w[lo][hi] for lo, hi in shape) for shape in _interval_shapes(len(w) - 1))
    return max(vals) if sense == "max" else min(vals)


# --------------------------------------------------------------------------------------------------
# Independent oracle, tier 2: a checked certificate (explicit path tree + dual table)
# --------------------------------------------------------------------------------------------------

def path_certificate(p, q):
    """BST form. Return {'lower', 'upper', 'valid', 'tree'}.

    lower: cost of an explicit path tree (from its levels). upper: U(0, n) if the table U passes every inequality
    U(a, a) >= 0, U(a, b) >= W(a, b) + U(a, k-1) + U(k, b) (a < k <= b), else None. valid: upper is not None."""
    n = len(p)
    memo = {}

    def best_path(a, b):  # cost of the best path tree on keys a+1..b, gaps a..b (direct sums)
        if a == b:
            return 0
        if (a, b) not in memo:
            here = sum(q[a:b + 1]) + sum(p[a:b])
            memo[(a, b)] = here + (0 if b == a + 1 else max(best_path(a + 1, b), best_path(a, b - 1)))
        return memo[(a, b)]

    # lower bound: build the path explicitly and read off every level
    key_levels, gap_levels = [None] * n, [None] * (n + 1)
    a, b, depth = 0, n, 0
    while b - a >= 1:
        if b - a == 1:
            key_levels[a] = depth
            gap_levels[a] = gap_levels[b] = depth + 1
            break
        if best_path(a + 1, b) >= best_path(a, b - 1):  # root k_(a+1); its left child is gap a
            key_levels[a] = depth
            gap_levels[a] = depth + 1
            a += 1
        else:  # root k_b; its right child is gap b
            key_levels[b - 1] = depth
            gap_levels[b] = depth + 1
            b -= 1
        depth += 1
    if n == 0:
        gap_levels[0] = 0
    lower = cost_from_levels(p, q, key_levels, gap_levels)

    # upper bound: check the dual inequalities for every interval and every root
    def U(x, y):
        return 0 if x == y else best_path(x, y)

    valid = True
    for lo in range(n + 1):
        for hi in range(lo + 1, n + 1):
            W = sum(q[lo:hi + 1]) + sum(p[lo:hi])
            u = U(lo, hi)
            for k in range(lo + 1, hi + 1):
                if u < W + U(lo, k - 1) + U(k, hi):
                    valid = False
                    break
            if not valid:
                break
        if not valid:
            break
    return {"lower": lower, "upper": U(0, n) if valid else None, "valid": valid,
            "tree": (tuple(key_levels), tuple(gap_levels))}


def table_certificate(sense, w):
    """Table form. Return {'lower', 'upper', 'valid', 'path'}.

    The best path value P(a, b) per interval is the dual table. "max": lower = value of an explicit path tree (sum
    of w over its node intervals), upper = P(0, n) if P(a, b) >= w(a, b) + P(a, k-1) + P(k, b) for every
    a < k <= b, else None. "min": upper = the explicit path's value, lower = P(0, n) if every
    P(a, b) <= w(a, b) + P(a, k-1) + P(k, b), else None. valid: the inequalities hold."""
    n = len(w) - 1
    maximise = sense == "max"
    P = [[0] * (n + 1) for _ in range(n + 1)]
    for d in range(1, n + 1):
        for a in range(n - d + 1):
            b = a + d
            if d == 1:
                P[a][b] = w[a][b]
            else:
                x, y = P[a + 1][b], P[a][b - 1]
                P[a][b] = w[a][b] + ((x if x >= y else y) if maximise else (x if x <= y else y))
    # the explicit path tree: its node intervals, then its value summed directly from the input
    nodes = []
    a, b = 0, n
    while b > a:
        nodes.append((a, b))
        if b - a == 1:
            break
        x, y = P[a + 1][b], P[a][b - 1]
        if (x >= y) if maximise else (x <= y):
            a += 1  # root a+1, the rest is (a+1, b)
        else:
            b -= 1  # root b, the rest is (a, b-1)
    path_value = sum(w[lo][hi] for lo, hi in nodes)
    valid = True
    for lo in range(n + 1):
        for hi in range(lo + 1, n + 1):
            u, W = P[lo][hi], w[lo][hi]
            for k in range(lo + 1, hi + 1):
                s = W + P[lo][k - 1] + P[k][hi]
                if (u < s) if maximise else (u > s):
                    valid = False
                    break
            if not valid:
                break
        if not valid:
            break
    bound = P[0][n] if valid else None
    if maximise:
        return {"lower": path_value, "upper": bound, "valid": valid, "path": tuple(nodes)}
    return {"lower": bound, "upper": path_value, "valid": valid, "path": tuple(nodes)}


def _oracle(instance):
    if instance not in _result_cache:
        if len(_result_cache) > 256:
            _result_cache.clear()
        if is_table_form(instance):
            sense, w = instance
            n = len(w) - 1
            if n <= BRUTE_MAX_N:
                v = brute_force_table(sense, w)
                res = ("brute", v, v)
            elif n <= CERT_MAX_N:
                cert = table_certificate(sense, w)
                res = ("certificate", cert["lower"], cert["upper"])
            else:
                res = ("none", None, None)
        else:
            p, q = instance
            n = len(p)
            if n <= BRUTE_MAX_N:
                v = brute_force_max(p, q)
                res = ("brute", v, v)
            elif n <= CERT_MAX_N:
                cert = path_certificate(p, q)
                res = ("certificate", cert["lower"], cert["upper"])
            else:
                res = ("none", None, None)
        _result_cache[instance] = res
    return _result_cache[instance]


def _normalise(instance):
    """Hashable canonical instance, or None if malformed."""
    try:
        a, b = instance
        if isinstance(a, str):
            if a not in ("max", "min"):
                return None
            w = tuple(tuple(row) for row in b)
            if not w or any(len(row) != len(w) for row in w):
                return None
            return a, w
        p, q = tuple(a), tuple(b)
        return (p, q) if len(q) == len(p) + 1 else None
    except (TypeError, ValueError):
        return None


def check(instance, output):
    inst = _normalise(instance)
    if inst is None:
        return False
    if isinstance(output, bool) or not isinstance(output, (int, Fraction)):
        return False
    kind, lower, upper = _oracle(inst)
    if kind == "none":
        return None
    if lower is not None and output < lower:
        return False
    if upper is not None and output > upper:
        return False
    if lower is not None and upper is not None and lower == upper:
        return output == lower
    return None


# --------------------------------------------------------------------------------------------------
# V2: exact comparison counts
# --------------------------------------------------------------------------------------------------
# Every algorithm keeps a running optimum over candidate roots; the first candidate initialises it and each
# further candidate costs one comparison of two cost values. CountingInt counts those comparisons (and,
# separately, additions, which the experiments report but V2 does not use). The implementations are unchanged.

_comparisons = 0
_additions = 0


class CountingInt:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __add__(self, other):
        global _additions
        _additions += 1
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __neg__(self):
        return CountingInt(-self.v)

    def _cmp(self, other, op):
        global _comparisons
        _comparisons += 1
        return op(self.v, self._val(other))

    def __lt__(self, other):
        return self._cmp(other, lambda a, b: a < b)

    def __le__(self, other):
        return self._cmp(other, lambda a, b: a <= b)

    def __gt__(self, other):
        return self._cmp(other, lambda a, b: a > b)

    def __ge__(self, other):
        return self._cmp(other, lambda a, b: a >= b)

    def __eq__(self, other):
        return self.v == self._val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counters():
    global _comparisons, _additions
    _comparisons = 0
    _additions = 0


def counters():
    return _comparisons, _additions


def wrap_counting(instance):
    """The same instance with every number replaced by a CountingInt."""
    if is_table_form(instance):
        sense, w = instance
        return sense, tuple(tuple(None if x is None else CountingInt(x) for x in row) for row in w)
    p, q = instance
    return tuple(CountingInt(x) for x in p), tuple(CountingInt(x) for x in q)


def generate_scaling(n, rng):
    """An instance of a random family from SCALING_FAMILIES, built from CountingInt; resets the counters. The
    counts depend on n only, whatever the family, form and sense (experiments/2026-10-07_max_cost_bst_checks.py checks this
    value by value; the shape diagnostic's instance probe re-draws the family at small n)."""
    inst = wrap_counting(instance_of(SCALING_FAMILIES[rng.randrange(len(SCALING_FAMILIES))], n, rng))
    reset_counters()
    return inst


def reported_cost(output):
    """Number of cost comparisons performed since the instance was generated."""
    return _comparisons
