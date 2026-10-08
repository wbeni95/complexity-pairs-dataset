"""Harness for the entry "maximum number of heap orderings of a binary tree".

Instance: (N, one) with N >= 0 the number of nodes and one the number 1 (the hook product of the empty tree) in the
integer type the implementations compute with: a Python int in V1, the counting integer below in V2.
Output: H(N) = min over binary trees T with N nodes of prod_v |T_v| (|T_v| = nodes in the subtree of v). The maximum
number of heap orderings over binary trees with N nodes is N! / H(N) (hook length formula, PROOFS.md section 1).

check(): an oracle written separately from the implementations, with two tiers.
  N <= BRUTE_MAX_N    the set of hook products of ALL binary trees with N nodes is enumerated (a tree with d nodes
                      is a root with subtrees of t and d - 1 - t nodes, so its hook product is d * a * b for a, b
                      in the sets of the two sizes; every value of every tree is kept, no minimisation is used
                      before the end). The output must equal the minimum of that set.
  N <= FORMULA_MAX_N  consistency check: the output must equal the explicit formula of Cleary, Fischer and St. John
                      (2025), Corollary 18 with c = -1 and Theorem 17: prod_{i=2}^{n} (i - 1)^{a_n(i)} with n = N + 1
                      leaves, where a_n(i) is the number of subtrees with i leaves of the GFB (complete) tree; the
                      counts a_n(i) are computed from the case formula of Theorem 17, not from a tree.
  larger N            None.

V2 (measure "reported"): generate_scaling(n) returns (n, CountingInt(1)) and resets the counter. CountingInt counts
every multiplication and every comparison (<, <=, >, >=, ==) in which a hook-product value takes part; the
implementations are unchanged. reported_cost returns the total. The counts depend on n only.
"""

BRUTE_MAX_N = 20
FORMULA_MAX_N = 5000

_sets = {0: frozenset([1])}


def _all_hook_products(n):
    """Set of hook products of all binary trees with n nodes (cached, built bottom-up)."""
    for d in range(len(_sets), n + 1):
        s = set()
        for t in range(d):
            for a in _sets[t]:
                for b in _sets[d - 1 - t]:
                    s.add(d * a * b)
        _sets[d] = frozenset(s)
    return _sets[n]


def _ceil_log2(i):
    return (i - 1).bit_length()          # ceil(log2(i)) for i >= 1


def _subtree_count(n, i):
    """Theorem 17 of Cleary, Fischer, St. John (2025): number of subtrees with i >= 2 leaves of the GFB tree with
    n leaves. k_i = ceil(log2 i)."""
    k = _ceil_log2(i)
    if i == 1 << k:                       # i is a power of two
        r = n % i
        if r == 0 or r >= (1 << (k - 1)):
            return n // i
        return n // i - 1
    return 1 if (n - i) % (1 << (k - 1)) == 0 else 0


def cfs_formula(n_nodes):
    """Hook product of the complete tree by Corollary 18 (c = -1) with Theorem 17 of Cleary, Fischer, St. John (2025);
    used only as a consistency check."""
    n = n_nodes + 1
    prod = 1
    for i in range(2, n + 1):
        a = _subtree_count(n, i)
        if a:
            prod *= (i - 1) ** a
    return prod


def generate(n, rng):
    return (n, 1)


def check(instance, output):
    n, _ = instance
    if isinstance(output, CountingInt):
        output = output.v
    if isinstance(output, bool) or not isinstance(output, int):
        return False
    value = output
    if n <= BRUTE_MAX_N:
        return value == min(_all_hook_products(n))
    if n <= FORMULA_MAX_N:
        return value == cfs_formula(n)
    return None


def equal(a, b):
    a = a.v if isinstance(a, CountingInt) else a
    b = b.v if isinstance(b, CountingInt) else b
    return a == b


# --------------------------------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------------------------------

_ops = {"mul": 0, "cmp": 0}


class CountingInt:
    """An integer that counts every multiplication and comparison it takes part in."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __mul__(self, other):
        _ops["mul"] += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def _cmp(self, other, op):
        _ops["cmp"] += 1
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
        return self._cmp(other, lambda a, b: a == b)

    def __hash__(self):
        return hash(self.v)

    def __int__(self):
        return int(self.v)

    def __index__(self):
        return int(self.v)

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counts():
    _ops["mul"] = 0
    _ops["cmp"] = 0


def generate_scaling(n, rng):
    """(n, CountingInt(1)); resets the counter. The counts depend on n only."""
    reset_counts()
    return (n, CountingInt(1))


def reported_cost(output):
    """Multiplications plus comparisons of hook-product values since the scaling instance was generated."""
    return _ops["mul"] + _ops["cmp"]


def counts_by_kind():
    return dict(_ops)
