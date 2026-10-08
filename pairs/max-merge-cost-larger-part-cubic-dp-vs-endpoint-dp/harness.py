"""Harness for the entry "worst-case merging of adjacent piles, merge cost = larger part".

Instance: a tuple of n + 1 non-negative pile sizes s_0..s_n (int, or Fraction in one family). Output: the largest
total cost, over all merge orders, of merging the row into one pile when a merge of adjacent blocks of sizes L and R
costs max(L, R); i.e. the maximum over all full binary trees with the leaves s_0..s_n in order of the sum, over the
internal nodes, of max(L, R), where L and R are the sizes of the node's left and right block.

V1 battery (generate): one of 12 families of non-negative sizes, chosen by the rng: bits (0/1), small (0..3, many
ties), all zero, constant, wide (0..10^6), one heavy pile, geometric (increasing or decreasing), ramp (increasing or
decreasing), sparse (mostly zero), valley, peak, and exact rationals.

check(): an oracle written separately from the implementations, with two tiers.
  n <= BRUTE_MAX_N   every merge tree on the n + 1 piles is enumerated explicitly (Catalan(n) trees); its cost is
                     the sum over its merges of max(L, R), with L and R summed directly from the sizes. No recurrence.
  n <= CERT_MAX_N    an exact certificate, checked here. Lower bound: an explicit caterpillar (every merge joins a
                     single pile to a block), built top-down and costed from direct sums. Upper bound: the table U of
                     best caterpillar values per row (U(a, a) = 0 by construction), accepted only if
                     U(a, b) >= max(S(a, k-1), S(k, b)) + U(a, k-1) + U(k, b) for EVERY split a < k <= b; then, by
                     induction over the last merge, every merge tree of the row a..b costs at most U(a, b), however U
                     was obtained. If the bounds meet, the output must equal them. A valid certificate is an
                     instance-wise check of the endpoint law, not an assumption of it.
  larger n           None.
The oracle is valid for any real sizes (it never uses s >= 0).

V2 (measure "reported"): generate_scaling draws a family (every integer family) and builds the instance from
CountingInt, a number type that counts every COMPARISON of two size-derived values (<, <=, >, >=) made by the
unchanged implementations, and separately every addition and subtraction; reported_cost returns the comparison
count. Both counts depend on n only.
"""
from fractions import Fraction

# --------------------------------------------------------------------------------------------------
# The objective
# --------------------------------------------------------------------------------------------------

MAXIMISE = True


def cost(left, right):
    return max(left, right)


# --------------------------------------------------------------------------------------------------
# V1 instances
# --------------------------------------------------------------------------------------------------

FAMILIES = ("bits", "small", "zero", "constant", "wide", "one_heavy", "geometric", "ramp", "sparse", "valley",
            "peak", "rational")
SCALING_FAMILIES = tuple(f for f in FAMILIES if f != "rational")


def instance_of(family, n, rng):
    m = n + 1  # number of piles
    if family == "bits":
        s = [rng.randint(0, 1) for _ in range(m)]
    elif family == "small":
        s = [rng.randint(0, 3) for _ in range(m)]
    elif family == "zero":
        s = [0] * m
    elif family == "constant":
        s = [rng.randint(0, 5)] * m
    elif family == "wide":
        s = [rng.randint(0, 10 ** 6) for _ in range(m)]
    elif family == "one_heavy":
        s = [rng.randint(0, 3) for _ in range(m)]
        s[rng.randrange(m)] = rng.randint(10, 10 * m * m + 10)
    elif family == "geometric":
        s = [2 ** t for t in range(m)]
        if rng.random() < 0.5:
            s.reverse()
    elif family == "ramp":
        s = [t + rng.randint(0, 1) for t in range(m)]
        if rng.random() < 0.5:
            s.reverse()
    elif family == "sparse":
        s = [rng.randint(1, 50) if rng.random() < 0.15 else 0 for _ in range(m)]
    elif family == "valley":
        mid = rng.randrange(m)
        s = [abs(t - mid) + rng.randint(0, 1) for t in range(m)]
    elif family == "peak":
        mid = rng.randrange(m)
        s = [m - abs(t - mid) + rng.randint(0, 1) for t in range(m)]
    elif family == "rational":
        den = rng.choice((2, 3, 7))
        s = [Fraction(rng.randint(0, 20), den) for _ in range(m)]
    else:
        raise ValueError(family)
    return tuple(s)


def generate(n, rng):
    return instance_of(FAMILIES[rng.randrange(len(FAMILIES))], n, rng)


# --------------------------------------------------------------------------------------------------
# Independent oracle, tier 1: every merge tree
# --------------------------------------------------------------------------------------------------

BRUTE_MAX_N = 9
CERT_MAX_N = 150
_tree_cache = {}
_result_cache = {}


def merge_trees(m):
    """Every merge tree on piles 0..m-1, as the tuple of its merges (lo, k, hi): the blocks lo..k-1 and k..hi."""
    if m not in _tree_cache:
        def trees(lo, hi):
            if lo == hi:
                return [()]
            out = []
            for k in range(lo + 1, hi + 1):
                for left in trees(lo, k - 1):
                    for right in trees(k, hi):
                        out.append(((lo, k, hi),) + left + right)
            return out
        _tree_cache[m] = trees(0, m - 1)
    return _tree_cache[m]


def tree_cost(sizes, tree):
    return sum(cost(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in tree)


def brute_force(sizes):
    vals = [tree_cost(sizes, t) for t in merge_trees(len(sizes))]
    return max(vals) if MAXIMISE else min(vals)


# --------------------------------------------------------------------------------------------------
# Independent oracle, tier 2: a checked certificate
# --------------------------------------------------------------------------------------------------

def certificate(sizes):
    """Return {'lower', 'upper', 'valid', 'tree'} for the maximum (see the module docstring)."""
    m = len(sizes)
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)

    def S(a, b):
        return pre[b + 1] - pre[a]

    U = [[0] * m for _ in range(m)]  # best caterpillar value of the row a..b
    for d in range(1, m):
        for a in range(m - d):
            b = a + d
            if d == 1:
                U[a][b] = cost(sizes[a], sizes[b])
            else:
                U[a][b] = max(cost(sizes[a], S(a + 1, b)) + U[a + 1][b], cost(S(a, b - 1), sizes[b]) + U[a][b - 1])
    # lower bound: the explicit caterpillar, costed from direct sums
    tree, a, b = [], 0, m - 1
    while b > a:
        if b - a == 1 or cost(sizes[a], S(a + 1, b)) + U[a + 1][b] >= cost(S(a, b - 1), sizes[b]) + U[a][b - 1]:
            tree.append((a, a + 1, b))
            a += 1
        else:
            tree.append((a, b, b))
            b -= 1
    lower = sum(cost(sum(sizes[lo:k]), sum(sizes[k:hi + 1])) for lo, k, hi in tree)
    # upper bound: the dual inequalities for every row and every split
    valid = True
    for lo in range(m):
        for hi in range(lo + 1, m):
            for k in range(lo + 1, hi + 1):
                if U[lo][hi] < cost(S(lo, k - 1), S(k, hi)) + U[lo][k - 1] + U[k][hi]:
                    valid = False
                    break
            if not valid:
                break
        if not valid:
            break
    return {"lower": lower, "upper": U[0][m - 1] if valid else None, "valid": valid, "tree": tuple(tree)}


def _normalise(instance):
    try:
        s = tuple(instance)
    except TypeError:
        return None
    if not s or any(isinstance(x, bool) or not isinstance(x, (int, Fraction)) for x in s):
        return None
    return s


def _oracle(sizes):
    if sizes not in _result_cache:
        if len(_result_cache) > 256:
            _result_cache.clear()
        n = len(sizes) - 1
        if n <= BRUTE_MAX_N:
            v = brute_force(sizes)
            res = ("brute", v, v)
        elif n <= CERT_MAX_N:
            cert = certificate(sizes)
            res = ("certificate", cert["lower"], cert["upper"])
        else:
            res = ("none", None, None)
        _result_cache[sizes] = res
    return _result_cache[sizes]


def check(instance, output):
    sizes = _normalise(instance)
    if sizes is None:
        return False
    if isinstance(output, bool) or not isinstance(output, (int, Fraction)):
        return False
    kind, lower, upper = _oracle(sizes)
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
# Every comparison of two size-derived values is counted: the one inside each merge cost and the one between a new
# candidate value and the running maximum. Additions and subtractions are counted separately (caveats; tests).

_comparisons = 0
_arithmetic = 0


class CountingInt:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __add__(self, other):
        global _arithmetic
        _arithmetic += 1
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        global _arithmetic
        _arithmetic += 1
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        global _arithmetic
        _arithmetic += 1
        return CountingInt(self._val(other) - self.v)

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
    global _comparisons, _arithmetic
    _comparisons = 0
    _arithmetic = 0


def counters():
    """(comparisons, additions + subtractions) since the last reset."""
    return _comparisons, _arithmetic


def wrap_counting(sizes):
    return tuple(CountingInt(x) for x in sizes)


def generate_scaling(n, rng):
    """An instance of a random integer family, built from CountingInt; resets the counters."""
    inst = wrap_counting(instance_of(SCALING_FAMILIES[rng.randrange(len(SCALING_FAMILIES))], n, rng))
    reset_counters()
    return inst


def reported_cost(output):
    """Number of comparisons performed since the instance was generated."""
    return _comparisons
