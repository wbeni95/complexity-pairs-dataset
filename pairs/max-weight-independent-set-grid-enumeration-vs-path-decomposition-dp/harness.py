"""Harness for maximum-weight independent set on k x n grids with diagonals: exhaustive search vs column DP.

Instances: (k, n, weights, diagonals). Vertices (r, c), r in 0..k-1 (rows), c in 0..n-1 (columns); weights is a
tuple of k rows of n non-negative integers; diagonals is a tuple of k-1 rows of n-1 codes for the unit squares:
0 none, 1 = (r, c)-(r+1, c+1), 2 = (r, c+1)-(r+1, c), 3 both. Horizontal and vertical neighbours are always
adjacent. All codes 3 give the king's graph. The size parameter is n (columns); k is part of the instance.
Outputs: (maximum weight, sorted tuple of chosen vertices). Optimal sets need not be unique, so `equal` compares
the values only.

generate(n, rng): k in 1..5 for n <= 3, 1..3 for n = 4, 5 (so exhaustive search sees at most 15 vertices), and
1..6 for n >= 6. Diagonal patterns: random codes, the king's graph, no diagonals (a bipartite grid), all code 1,
all code 2, sparse random codes. Weights: uniform 0..9, uniform 0..1000, all equal to 1 (many ties), half zeros
and half 1..20, or 0..3 with one heavy vertex.

check(instance, output) is independent of both implementations and returns True or False for every output whose
vertex pairs have integer coordinates (a non-integer coordinate makes it raise, which the validator reports as a
failure):
  1. the returned set must consist of distinct vertices of the grid, be independent (edges built here from the
     instance), and have exactly the returned weight;
  2. the returned value must equal the optimum of a vertex-by-vertex ("broken profile") DP written here: the
     vertices are processed in column-major order, and the state is the membership of the last k+1 processed
     vertices, which contain every earlier neighbour of the next vertex ((r-1, c), (r, c-1), (r-1, c-1) and
     (r+1, c-1)). This is a different decomposition (width at most k+1 instead of 2k-1) and different code.

V2 (measure "reported"): generate_scaling(n, rng) is the 3 x n king's graph (k = 3, every square has both
diagonals) with seeded weights 1..9 wrapped in CountingInt; it resets the counters. CountingInt counts additions
and subtractions on weight-derived values; comparisons are recorded in a separate counter that reported_cost does
not include. Exact addition counts (derived in entry.json, checked in experiments/2026-10-06f_entries_mis_pathwidth.py):
  exhaustive search  N 2^(N-1) with N = 3n, i.e. (3/2) n 8^n   (on every instance; zero weights included)
  column DP          10n - 5                                    (k = 3, n >= 1; any diagonals; all weights positive)
No counted value passes through a CPython built-in such as sorted, min or max.
"""


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _k_for(n, rng):
    if n <= 3:
        return rng.randint(1, 5)
    if n <= 5:
        return rng.randint(1, 3)
    return rng.randint(1, 6)


def _diagonals(k, n, rng):
    kind = rng.randrange(6)
    rows = []
    for _ in range(k - 1):
        row = []
        for _ in range(n - 1):
            if kind == 0:
                code = rng.randrange(4)
            elif kind == 1:
                code = 3
            elif kind == 2:
                code = 0
            elif kind == 3:
                code = 1
            elif kind == 4:
                code = 2
            else:
                code = rng.randrange(1, 4) if rng.random() < 0.2 else 0
            row.append(code)
        rows.append(tuple(row))
    return tuple(rows)


def _weights(k, n, rng):
    kind = rng.randrange(5)
    if kind == 0:
        w = [[rng.randint(0, 9) for _ in range(n)] for _ in range(k)]
    elif kind == 1:
        w = [[rng.randint(0, 1000) for _ in range(n)] for _ in range(k)]
    elif kind == 2:
        w = [[1] * n for _ in range(k)]
    elif kind == 3:
        w = [[0 if rng.random() < 0.5 else rng.randint(1, 20) for _ in range(n)] for _ in range(k)]
    else:
        w = [[rng.randint(0, 3) for _ in range(n)] for _ in range(k)]
        if n:
            w[rng.randrange(k)][rng.randrange(n)] = 50
    return tuple(tuple(row) for row in w)


def generate(n, rng):
    k = _k_for(n, rng)
    return k, n, _weights(k, n, rng), _diagonals(k, n, rng)


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def adjacent_pairs(k, n, diagonals):
    """Set of frozenset({u, v}) for every edge, built from the definition."""
    pairs = set()
    for r in range(k):
        for c in range(n):
            if c + 1 < n:
                pairs.add(frozenset(((r, c), (r, c + 1))))
            if r + 1 < k:
                pairs.add(frozenset(((r, c), (r + 1, c))))
    for r in range(k - 1):
        for c in range(n - 1):
            if diagonals[r][c] in (1, 3):
                pairs.add(frozenset(((r, c), (r + 1, c + 1))))
            if diagonals[r][c] in (2, 3):
                pairs.add(frozenset(((r, c + 1), (r + 1, c))))
    return pairs


def profile_dp_value(instance):
    """Optimum by a vertex-by-vertex DP over the last k+1 vertices in column-major order."""
    k, n, weights, diagonals = instance
    window = (1 << (k + 1)) - 1
    table = {0: 0}                             # bit j of a state: was the vertex processed j+1 steps ago chosen?
    for c in range(n):
        for r in range(k):
            w = weights[r][c]
            blocked = 0                        # bits of the window that must be 0 to take (r, c)
            if r >= 1:
                blocked |= 1                   # (r-1, c), one step back
            if c >= 1:
                blocked |= 1 << (k - 1)        # (r, c-1), k steps back
                if r >= 1 and diagonals[r - 1][c - 1] in (1, 3):
                    blocked |= 1 << k          # (r-1, c-1), k+1 steps back
                if r + 1 < k and diagonals[r][c - 1] in (2, 3):
                    blocked |= 1 << (k - 2)    # (r+1, c-1), k-1 steps back
            nxt = {}
            for state, value in table.items():
                skip = (state << 1) & window
                if nxt.get(skip, -1) < value:
                    nxt[skip] = value
                if not state & blocked:
                    take = ((state << 1) | 1) & window
                    if nxt.get(take, -1) < value + w:
                        nxt[take] = value + w
            table = nxt
    best = 0
    for value in table.values():
        if value > best:
            best = value
    return best


def check(instance, output):
    k, n, weights, diagonals = instance
    if not (isinstance(output, tuple) and len(output) == 2):
        return False
    value, chosen = output
    if isinstance(value, bool) or not isinstance(value, int) or not isinstance(chosen, tuple):
        return False
    for v in chosen:
        if not (isinstance(v, tuple) and len(v) == 2 and 0 <= v[0] < k and 0 <= v[1] < n):
            return False
    if len(set(chosen)) != len(chosen):
        return False
    pairs = adjacent_pairs(k, n, diagonals)
    for i in range(len(chosen)):
        for j in range(i + 1, len(chosen)):
            if frozenset((chosen[i], chosen[j])) in pairs:
                return False
    if sum(weights[r][c] for r, c in chosen) != value:
        return False
    return value == profile_dp_value(instance)


def equal(a, b):
    return a[0] == b[0]


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = {"add": 0, "compare": 0}


class CountingInt:
    """An integer that counts the additions/subtractions and (separately) the comparisons it takes part in."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __add__(self, o):
        _ops["add"] += 1
        return CountingInt(self.v + self._val(o))

    def __radd__(self, o):
        _ops["add"] += 1
        return CountingInt(self._val(o) + self.v)

    def __sub__(self, o):
        _ops["add"] += 1
        return CountingInt(self.v - self._val(o))

    def __rsub__(self, o):
        _ops["add"] += 1
        return CountingInt(self._val(o) - self.v)

    def _cmp(self, result):
        _ops["compare"] += 1
        return result

    def __lt__(self, o):
        return self._cmp(self.v < self._val(o))

    def __le__(self, o):
        return self._cmp(self.v <= self._val(o))

    def __gt__(self, o):
        return self._cmp(self.v > self._val(o))

    def __ge__(self, o):
        return self._cmp(self.v >= self._val(o))

    def __eq__(self, o):
        return self._cmp(self.v == self._val(o))

    def __ne__(self, o):
        return self._cmp(self.v != self._val(o))

    __hash__ = None

    def __int__(self):
        return self.v

    def __repr__(self):
        return f"CountingInt({self.v})"


SCALING_K = 3


def reset_counters():
    for key in _ops:
        _ops[key] = 0


def king_instance(k, n, rng, wrap=CountingInt):
    """k x n king's graph (both diagonals in every square) with seeded weights 1..9."""
    weights = tuple(tuple(wrap(rng.randint(1, 9)) for _ in range(n)) for _ in range(k))
    diagonals = tuple(tuple(3 for _ in range(n - 1)) for _ in range(k - 1))
    return k, n, weights, diagonals


def generate_scaling(n, rng):
    """3 x n king's graph with CountingInt weights 1..9; resets the counters."""
    inst = king_instance(SCALING_K, n, rng)
    reset_counters()
    return inst


def reported_cost(output):
    """Additions on weight-derived values since the scaling instance was generated (comparisons excluded)."""
    return _ops["add"]
