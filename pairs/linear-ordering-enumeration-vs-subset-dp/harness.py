"""Harness for the linear ordering problem: enumeration of all n! orders vs dynamic programming over subsets.

Instance: an n x n integer matrix W as a tuple of tuples; the diagonal holds random integers that every algorithm
must ignore. The value of an order is the sum of W[a][b] over all pairs with a before b. Output: (maximum value, an
order attaining it). Several orders can be optimal, so `equal` compares the values only and `check` verifies the
returned order.

generate(n, rng) mixes five kinds: random entries in -9..9; random entries in 0..9; a tournament (W[a][b] + W[b][a]
= 1 for a != b); a hidden acyclic instance (W[a][b] > 0 only if a precedes b in a hidden random order, so the
optimum takes every positive entry); zero matrices and large entries (up to 10^6) for ties and range.

check(instance, output) is independent of both implementations: the order must be a permutation of range(n); its
value is recomputed from positions and must equal the claim; the claim must not exceed the upper bound
sum over a < b of max(W[a][b], W[b][a]) and is certified when it equals it; otherwise a depth-first branch and
bound over order prefixes (bound: value so far plus that upper bound for the pairs not yet decided) computes the
optimum exactly for n <= 8, and with a budget of BB_BUDGET nodes above; if it gives up, an improving move of one
element proves non-optimality, and anything else is undecided (None).

V2 (measure "reported"): generate_scaling(n, rng) is an n x n matrix of CountingInt entries drawn from rng in
0..9, which count every comparison and +, -; it resets the counter. Exact counts for n >= 2 (derived in entry.json,
checked in experiments/2026-10-06i_linear_ordering.py; they do not depend on the entries):
  enumeration   n! (n(n-1)/2 + 1) - 1
  subset DP     2^(n-2) (n+4)(n-1) + 1
No counted operation happens inside a CPython built-in.
"""
BB_EXACT_UP_TO = 8
BB_BUDGET = 300_000


def generate(n, rng):
    kind = rng.randrange(5)
    w = [[0] * n for _ in range(n)]
    if kind == 0:
        w = [[rng.randint(-9, 9) for _ in range(n)] for _ in range(n)]
    elif kind == 1:
        w = [[rng.randint(0, 9) for _ in range(n)] for _ in range(n)]
    elif kind == 2:
        for a in range(n):
            for b in range(a + 1, n):
                if rng.random() < 0.5:
                    w[a][b] = 1
                else:
                    w[b][a] = 1
    elif kind == 3:
        hidden = rng.sample(range(n), n)
        for p in range(n):
            for q in range(p + 1, n):
                w[hidden[p]][hidden[q]] = rng.randint(0, 9)
    else:
        if rng.random() < 0.5:
            w = [[rng.randint(0, 10 ** 6) for _ in range(n)] for _ in range(n)]
    for a in range(n):
        w[a][a] = rng.randint(-50, 50)
    return tuple(tuple(row) for row in w)


def order_value(w, order):
    n = len(w)
    pos = [0] * n
    for p, a in enumerate(order):
        pos[a] = p
    return sum(w[a][b] for a in range(n) for b in range(n) if a != b and pos[a] < pos[b])


def upper_bound(w):
    n = len(w)
    return sum(max(w[a][b], w[b][a]) for a in range(n) for b in range(a + 1, n))


def branch_and_bound(w, budget=None):
    n = len(w)
    best = [None]
    nodes = [0]

    def dfs(placed, so_far, remaining_ub):
        nodes[0] += 1
        if budget is not None and nodes[0] > budget:
            raise TimeoutError
        if best[0] is not None and so_far + remaining_ub <= best[0]:
            return
        if placed == (1 << n) - 1:
            best[0] = so_far
            return
        rest = [u for u in range(n) if not placed >> u & 1]
        for v in rest:
            add = sum(w[v][u] for u in rest if u != v)
            drop = sum(max(w[v][u], w[u][v]) for u in rest if u != v)
            dfs(placed | (1 << v), so_far + add, remaining_ub - drop)

    try:
        dfs(0, 0, upper_bound(w))
    except TimeoutError:
        return None
    return best[0]


def improving_move(w, order):
    base = order_value(w, order)
    n = len(order)
    for a in range(n):
        rest = order[:a] + order[a + 1:]
        for b in range(n):
            if b != a and order_value(w, rest[:b] + (order[a],) + rest[b:]) > base:
                return True
    return False


def check(w, output):
    n = len(w)
    if not (isinstance(output, tuple) and len(output) == 2):
        return False
    claimed, order = output
    if isinstance(claimed, bool) or not isinstance(claimed, int):
        return False
    if not isinstance(order, tuple) or sorted(order) != list(range(n)) or not all(type(a) is int for a in order):
        return False
    if order_value(w, order) != claimed:
        return False
    ub = upper_bound(w)
    if claimed > ub:
        return False
    if claimed == ub:
        return True
    opt = branch_and_bound(w, None if n <= BB_EXACT_UP_TO else BB_BUDGET)
    if opt is not None:
        return claimed == opt
    if improving_move(w, order):
        return False
    return None


def equal(a, b):
    return a[0] == b[0]


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = {"compare": 0, "add": 0}


class CountingInt:
    """An integer that counts every comparison and +, - it takes part in."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def _add(self, value):
        _ops["add"] += 1
        return CountingInt(value)

    def __add__(self, o):
        return self._add(self.v + self._val(o))

    def __radd__(self, o):
        return self._add(self._val(o) + self.v)

    def __sub__(self, o):
        return self._add(self.v - self._val(o))

    def __rsub__(self, o):
        return self._add(self._val(o) - self.v)

    def _cmp(self, result):
        _ops["compare"] += 1
        return result

    def __eq__(self, o):
        return self._cmp(self.v == self._val(o))

    def __ne__(self, o):
        return self._cmp(self.v != self._val(o))

    def __lt__(self, o):
        return self._cmp(self.v < self._val(o))

    def __le__(self, o):
        return self._cmp(self.v <= self._val(o))

    def __gt__(self, o):
        return self._cmp(self.v > self._val(o))

    def __ge__(self, o):
        return self._cmp(self.v >= self._val(o))

    __hash__ = None

    def __int__(self):
        return self.v

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counter():
    for key in _ops:
        _ops[key] = 0


def generate_scaling(n, rng):
    """n x n matrix of CountingInt entries in 0..9 drawn from rng; resets the counter."""
    inst = tuple(tuple(CountingInt(rng.randint(0, 9)) for _ in range(n)) for _ in range(n))
    reset_counter()
    return inst


def reported_cost(output):
    """Counted operations on entry-derived values since the scaling instance was generated."""
    return sum(_ops.values())


def counts_by_kind():
    return dict(_ops)
