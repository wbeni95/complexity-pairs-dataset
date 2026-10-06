"""Harness for the optimal binary search tree entry.

Instance: (p, q), p = (p_1, ..., p_n) key access frequencies, q = (q_0, ..., q_n) gap frequencies, all
non-negative integers. Output: the minimum over all BSTs on k_1 < ... < k_n of
    sum_m p_m * (level(k_m) + 1) + sum_j q_j * level(gap j)          (levels from the root, root = 0),
an exact integer (Knuth 1971's cost).

V1 battery (generate): ten families chosen by the rng, most of them full of ties (frequencies in {0, 1},
in [0, 3], all zero, all equal), plus wide random weights, one heavy key, geometric weights, p = 0
(gaps only), q = 0 (keys only) and the two-heavy-ends family used for V2.

check(): an oracle written separately from the implementations. For n <= BRUTE_MAX_N it enumerates every BST
shape on n keys explicitly (Catalan(n) shapes), records the level of every key and every gap, and takes the
minimum cost computed directly from those levels (no w(i, j), no interval recurrence). For
BRUTE_MAX_N < n <= MEMO_MAX_N it uses a separately written top-down memoised recursion with prefix sums (same
recurrence as the DPs, independent code). Above that it returns None.

V2 (measure "reported"): generate_scaling builds instances from CountingInt, a number type that counts every
COMPARISON of two cost values (<, <=, >, >=) made by the unchanged implementations; reported_cost returns the
count. The family is the worst case for Knuth's algorithm (see generate_scaling).
"""

# --------------------------------------------------------------------------------------------------
# V1 instances
# --------------------------------------------------------------------------------------------------

FAMILIES = ("bits", "small", "zero", "constant", "wide", "one_heavy", "geometric", "gaps_only",
            "keys_only", "heavy_ends")


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
    elif family == "one_heavy":
        p = [rng.randint(0, 3) for _ in range(n)]
        q = [rng.randint(0, 3) for _ in range(n + 1)]
        if n:
            p[rng.randrange(n)] = rng.randint(10, 10 * n * n + 10)
    elif family == "geometric":
        p = [2 ** m for m in range(n)]
        q = [rng.randint(0, 1) for _ in range(n + 1)]
        if rng.random() < 0.5:
            p.reverse()
    elif family == "gaps_only":
        p = [0] * n
        q = [rng.randint(0, 5) for _ in range(n + 1)]
    elif family == "keys_only":
        p = [rng.randint(0, 5) for _ in range(n)]
        q = [0] * (n + 1)
    elif family == "heavy_ends":
        return _heavy_ends(n, rng, int)
    else:
        raise ValueError(family)
    return tuple(p), tuple(q)


def generate(n, rng):
    return _instance(n, rng, FAMILIES[rng.randrange(len(FAMILIES))])


# --------------------------------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------------------------------

BRUTE_MAX_N = 10
MEMO_MAX_N = 60
_profiles_cache = {}


def _profiles(size):
    """All BST shapes on `size` keys, each as (key_levels, gap_levels) in symmetric (in-order) order."""
    if size in _profiles_cache:
        return _profiles_cache[size]
    if size == 0:
        result = [((), (0,))]  # no key, one gap at the root position
    else:
        result = []
        for left in range(size):  # the root is the (left + 1)-th smallest key
            for lk, lg in _profiles(left):
                for rk, rg in _profiles(size - 1 - left):
                    keys = tuple(x + 1 for x in lk) + (0,) + tuple(x + 1 for x in rk)
                    gaps = tuple(x + 1 for x in lg) + tuple(x + 1 for x in rg)
                    result.append((keys, gaps))
    _profiles_cache[size] = result
    return result


def brute_force_cost(p, q):
    """Minimum cost over every explicit tree shape, cost evaluated from the levels."""
    best = None
    for keys, gaps in _profiles(len(p)):
        cost = sum(pm * (lev + 1) for pm, lev in zip(p, keys)) + sum(qj * lev for qj, lev in zip(q, gaps))
        if best is None or cost < best:
            best = cost
    return best


def memo_cost(p, q):
    """Top-down memoised recursion with prefix sums (separately written; same recurrence as the DPs)."""
    n = len(p)
    pre_p, pre_q = [0], [0]
    for x in p:
        pre_p.append(pre_p[-1] + x)
    for x in q:
        pre_q.append(pre_q[-1] + x)
    memo = {}

    def solve(lo, hi):  # keys lo+1..hi, gaps lo..hi
        if lo == hi:
            return 0
        key = (lo, hi)
        if key not in memo:
            weight = (pre_p[hi] - pre_p[lo]) + (pre_q[hi + 1] - pre_q[lo])
            memo[key] = weight + min(solve(lo, root - 1) + solve(root, hi) for root in range(lo + 1, hi + 1))
        return memo[key]

    return solve(0, n)


def check(instance, output):
    p, q = instance
    n = len(p)
    if len(q) != n + 1:
        return False
    if n <= BRUTE_MAX_N:
        return output == brute_force_cost(p, q)
    if n <= MEMO_MAX_N:
        return output == memo_cost(p, q)
    return None


# --------------------------------------------------------------------------------------------------
# V2: exact comparison counts
# --------------------------------------------------------------------------------------------------
# Every algorithm keeps a running minimum over candidate roots; the first candidate initialises it and each
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


def _heavy_ends(n, rng, num):
    """Small random weights in [0, 9], except p_1 = p_n = M with M = n * S + 1, S = sum of all other weights.

    Then k_1 is the unique optimal root of every prefix interval (0, m), m <= n - 1 (any other root puts k_1 in a
    subtree, costing >= M, while root k_1 costs at most w + m * S < w + M), and k_n is the unique optimal root of
    every suffix interval (m, n), m >= 1. Knuth's comparison count is sum_{L=2..n} (r[n-L+1][n] - r[0][L-1]),
    so it attains its maximum (n - 1)^2 on this family.
    """
    p = [rng.randint(0, 9) for _ in range(n)]
    q = [rng.randint(0, 9) for _ in range(n + 1)]
    if n:
        p[0] = p[-1] = 0
        heavy = n * (sum(p) + sum(q)) + 1
        p[0] = p[-1] = heavy
    return tuple(num(x) for x in p), tuple(num(x) for x in q)


def generate_scaling(n, rng):
    """Worst case for Knuth's algorithm (two heavy end keys), built from CountingInt; resets the counters."""
    reset_counters()
    return _heavy_ends(n, rng, CountingInt)


def reported_cost(output):
    """Number of cost comparisons performed since the instance was generated."""
    return _comparisons
