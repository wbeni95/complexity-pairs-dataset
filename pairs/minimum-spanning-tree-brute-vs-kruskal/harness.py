"""Instances: complete undirected graph on n vertices as a symmetric n x n weight matrix (diagonal 0).

generate uses integer weights in [1, 100] (many ties) or, in some trials, in [1, 3] (massive ties).
generate_scaling uses weights in [1, 10^9] (distinct with high probability); on these draws sorting the
edges took 1.095 to 1.179 m log2 m comparisons (measured for n = 50..800 under CPython 3.14.2).
"""


def _matrix(n, rng, hi):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = rng.randint(1, hi)
    return tuple(tuple(row) for row in W)


def generate(n, rng):
    return _matrix(n, rng, 3 if rng.random() < 0.3 else 100)


def _scaling_draws(n, rng):
    return _matrix(n, rng, 10 ** 9)


# --- Exact operation counting for V2 (measure: "reported"; RESEARCH_LOG RL-047/RL-048) ---------------
# Timing could not resolve Kruskal's log factor (log n varies ~1.7x over the timed range). generate_scaling()
# draws the same weights as before (same seeds) and wraps every off-diagonal weight in CountingWeight. It
# counts every comparison and every arithmetic operation (+, *, divmod) that has an input weight as an
# operand, in the UNCHANGED implementations. Kruskal packs each edge into the key w*n^2 + u*n + v: with
# a CountingWeight w that key is itself a CountingWeight, so the comparisons made inside sorted() call its
# __lt__ and are counted; divmod(key, n^2) returns plain ints. experiments/2026-10-06c_mst_counts.py gives
# the breakdown: Kruskal = 3m packing operations + sort comparisons + one divmod per scanned key (m = n(n-1)/2);
# Prim = (n-1)(n-2) comparisons + (n-1) additions = (n-1)^2; enumeration = (n-1) additions per subset +
# one comparison per spanning tree after the first = (n-1) C(m, n-1) + n^(n-2) - 1. The union-find work
# (on plain vertex ints) and the depth-first search of the enumeration are not counted.

_ops = 0


def _wv(x):
    return x.v if isinstance(x, CountingWeight) else x


class CountingWeight:
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __add__(self, o):
        global _ops
        _ops += 1
        return CountingWeight(self.v + _wv(o))

    __radd__ = __add__

    def __mul__(self, o):
        global _ops
        _ops += 1
        return CountingWeight(self.v * _wv(o))

    __rmul__ = __mul__

    def __divmod__(self, o):
        global _ops
        _ops += 1
        return divmod(self.v, _wv(o))      # plain ints: the implementation uses them as weight and indices

    def __lt__(self, o):
        global _ops
        _ops += 1
        return self.v < _wv(o)

    def __le__(self, o):
        global _ops
        _ops += 1
        return self.v <= _wv(o)

    def __gt__(self, o):
        global _ops
        _ops += 1
        return self.v > _wv(o)

    def __ge__(self, o):
        global _ops
        _ops += 1
        return self.v >= _wv(o)

    def __eq__(self, o):
        global _ops
        _ops += 1
        return self.v == _wv(o)

    def __ne__(self, o):
        global _ops
        _ops += 1
        return self.v != _wv(o)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingWeight({self.v!r})"


def generate_scaling(n, rng):
    """Weights in [1, 10^9] as before (same draws), off-diagonal entries wrapped in CountingWeight; resets the counter."""
    global _ops
    W = _scaling_draws(n, rng)
    _ops = 0
    return tuple(tuple(w if u == v else CountingWeight(w) for v, w in enumerate(row)) for u, row in enumerate(W))


def reported_cost(output):
    """Comparisons and arithmetic operations on input weights since the counting instance was generated."""
    return _ops


_cache = {}


def _boruvka(W):
    """MST weight by Boruvka's algorithm, independent of the implementations under test.
    Ties are broken by the total order (w, u, v), which makes the cheapest-edge choices consistent."""
    n = len(W)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, components = 0, n
    while components > 1:
        cheapest = {}
        for u in range(n):
            for v in range(u + 1, n):
                ru, rv = find(u), find(v)
                if ru != rv:
                    key = (W[u][v], u, v)
                    for r in (ru, rv):
                        if r not in cheapest or key < cheapest[r]:
                            cheapest[r] = key
        for w, u, v in set(cheapest.values()):
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
                total += w
                components -= 1
    return total


def check(W, output):
    n = len(W)
    if n <= 1:
        return output == 0
    if W not in _cache:
        _cache[W] = _boruvka(W)
    path = sum(W[i][i + 1] for i in range(n - 1))           # the path 0-1-...-(n-1) is a spanning tree
    lightest = sum(sorted(W[u][v] for u in range(n) for v in range(u + 1, n))[:n - 1])
    return output == _cache[W] and lightest <= output <= path
