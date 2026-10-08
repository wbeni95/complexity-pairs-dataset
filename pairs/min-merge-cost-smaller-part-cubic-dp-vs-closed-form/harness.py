"""Harness for the entry "merging adjacent piles at the cost of the smaller part (min sum of min(L, R))".

Instance: a tuple of n + 1 non-negative pile sizes s_0..s_n (int, or Fraction in one family). Output: the smallest
total cost, over all merge orders, of merging the row into one pile when a merge of adjacent blocks of sizes L and R
costs min(L, R); i.e. the minimum over all full binary trees with the leaves s_0..s_n in order of the sum, over the
internal nodes, of min(L, R), where L and R are the sizes of the node's left and right block.

V1 battery (generate): one of 12 families of non-negative sizes, chosen by the rng: bits (0/1), small (0..3, many
ties), all zero, constant, wide (0..10^6), one heavy pile, geometric (increasing or decreasing), ramp (increasing or
decreasing), sparse (mostly zero), valley, peak, and exact rationals.

check(): an oracle written separately from the implementations, with two tiers.
  n <= BRUTE_MAX_N   every merge tree on the n + 1 piles is enumerated explicitly (Catalan(n) trees); its cost is
                     the sum over its merges of min(L, R), with L and R summed directly from the sizes. No recurrence.
  n <= CERT_MAX_N    an exact certificate, checked here. Upper bound: an explicit caterpillar that starts at a pile of
                     largest size and adds the left neighbours, then the right neighbours, one at a time, costed from
                     direct sums. Lower bound: the table B(a, b) = S(a, b) - max(s_a..s_b), computed from direct sums
                     and maxima, accepted only if B(a, a) = 0 and B(a, b) <= min(S(a, k-1), S(k, b)) + B(a, k-1) +
                     B(k, b) for EVERY split a < k <= b; then, by induction over the last merge, every merge tree of the
                     row a..b costs at least B(a, b). If the bounds meet, the output must equal them. A valid
                     certificate is an instance-wise check of the closed form, not an assumption of it.
  larger n           None.
The oracle is valid for any real sizes (for negative sizes the table B may fail its inequalities; then the
certificate is invalid and check returns None above BRUTE_MAX_N).

V2 (measure "reported"): generate_scaling draws a family (every integer family) and builds the instance from
CountingInt, a number type that counts every COMPARISON of two size-derived values (<, <=, >, >=) made by the
unchanged implementations, and separately every addition and subtraction; reported_cost returns the comparison
count. Both counts depend on n only.
"""
from fractions import Fraction

# --------------------------------------------------------------------------------------------------
# The objective
# --------------------------------------------------------------------------------------------------

MAXIMISE = False


def cost(left, right):
    return min(left, right)


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
    """Return {'lower', 'upper', 'valid', 'tree'} for the minimum (see the module docstring)."""
    m = len(sizes)
    pre = [0]
    for x in sizes:
        pre.append(pre[-1] + x)

    def S(a, b):
        return pre[b + 1] - pre[a]

    B = [[None] * m for _ in range(m)]  # the closed form S(a, b) - max(s_a..s_b) of the row a..b
    for a in range(m):
        top = sizes[a]
        for b in range(a, m):
            top = max(top, sizes[b])
            B[a][b] = S(a, b) - top
    # upper bound: the explicit caterpillar from a largest pile, costed from direct sums
    start = max(range(m), key=lambda t: sizes[t])
    tree, lo, hi = [], start, start
    while lo > 0:  # add the left neighbour: the merge joins pile lo-1 and the block lo..hi
        tree.append((lo - 1, lo, hi))
        lo -= 1
    while hi < m - 1:  # add the right neighbour: the merge joins the block lo..hi and pile hi+1
        tree.append((lo, hi + 1, hi + 1))
        hi += 1
    upper = sum(cost(sum(sizes[x:k]), sum(sizes[k:y + 1])) for x, k, y in tree)
    # lower bound: the dual inequalities for every row and every split
    valid = all(B[a][a] == 0 for a in range(m))
    for a in range(m):
        if not valid:
            break
        for b in range(a + 1, m):
            for k in range(a + 1, b + 1):
                if B[a][b] > cost(S(a, k - 1), S(k, b)) + B[a][k - 1] + B[k][b]:
                    valid = False
                    break
            if not valid:
                break
    return {"lower": B[0][m - 1] if valid else None, "upper": upper, "valid": valid, "tree": tuple(tree)}


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
# Every comparison of two size-derived values is counted: in the DP the one inside each merge cost and the one between
# a new candidate value and the running minimum; in the closed form the comparisons of the running maximum. Additions
# and subtractions are counted separately (caveats; tests).

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
