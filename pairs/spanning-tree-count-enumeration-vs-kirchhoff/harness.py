"""Instances: a simple undirected graph on n >= 1 vertices as a symmetric 0/1 adjacency matrix (tuple of
tuples, zero diagonal). The answer is the number of spanning trees tau(G), an exact integer.

generate mixes graph families so that every answer type occurs: random G(n, p) with p in {0.2, 0.5, 0.8}
(sparse ones are often disconnected), complete graphs K_n (Cayley), random trees (answer 1), trees plus a
few extra edges, cycles (answer n for n >= 3) and graphs built disconnected on purpose (answer 0). Vertices
are relabelled by a random permutation, so the vertex that the implementations delete is arbitrary.

generate_scaling returns K_n whose entries are CountingInt, a number type that counts every
multiplication and division performed on it. The Kirchhoff implementation builds its Laplacian from these
entries (degree = sum of a row, off-diagonal = -entry), so all of its elimination arithmetic is counted
without changing the implementation; reported_cost returns the count. The enumeration does no arithmetic
on the entries (it only tests them for truth), so its V2 is timed (see entry.json).
"""
from fractions import Fraction


def _empty(n):
    return [[0] * n for _ in range(n)]


def _add(W, u, v):
    W[u][v] = W[v][u] = 1


def _random_tree_edges(vertices, rng):
    """Random recursive tree on the given vertex list (each vertex attaches to an earlier one)."""
    return [(vertices[i], vertices[rng.randrange(i)]) for i in range(1, len(vertices))]


KINDS = ("gnp", "gnp", "complete", "tree", "tree_plus", "cycle", "disconnected")


def generate(n, rng):
    kind = rng.choice(KINDS)
    W = _empty(n)
    if kind == "gnp":
        p = rng.choice([0.2, 0.5, 0.8])
        for u in range(n):
            for v in range(u + 1, n):
                if rng.random() < p:
                    _add(W, u, v)
    elif kind == "complete":
        for u in range(n):
            for v in range(u + 1, n):
                _add(W, u, v)
    elif kind in ("tree", "tree_plus"):
        for u, v in _random_tree_edges(list(range(n)), rng):
            _add(W, u, v)
        if kind == "tree_plus" and n >= 3:
            for _ in range(rng.randint(1, n)):
                u, v = rng.sample(range(n), 2)
                _add(W, u, v)
    elif kind == "cycle":
        for u in range(n):
            if n >= 3 or (n == 2 and u == 0):
                _add(W, u, (u + 1) % n)
    elif kind == "disconnected" and n >= 2:
        k = rng.randint(1, n - 1)  # parts {0..k-1} and {k..n-1}, no edges between them
        for part in (list(range(k)), list(range(k, n))):
            for u, v in _random_tree_edges(part, rng):
                _add(W, u, v)
            for u in part:
                for v in part:
                    if u < v and rng.random() < 0.4:
                        _add(W, u, v)
    perm = list(range(n))
    rng.shuffle(perm)
    return tuple(tuple(W[perm[i]][perm[j]] for j in range(n)) for i in range(n))


# --------------------------------------------------------------------------------------------------
# Independent oracle (no code shared with the implementations)
# --------------------------------------------------------------------------------------------------

def _connected(A):
    n = len(A)
    seen = {0}
    stack = [0]
    while stack:
        u = stack.pop()
        for v in range(n):
            if A[u][v] and v not in seen:
                seen.add(v)
                stack.append(v)
    return len(seen) == n


_dc_memo = {}


def _deletion_contraction(vertices, edges):
    """tau of a multigraph: vertices a frozenset, edges a dict {(a, b): multiplicity} with a < b, no loops.

    tau(G) = tau(G minus all a-b edges) + k * tau(G with a and b merged), k = multiplicity of {a, b}:
    a spanning tree uses at most one of the k parallel a-b edges, and the trees that use a given one
    correspond to the spanning trees of the contracted multigraph (the other a-b edges become loops).
    """
    if len(vertices) == 1:
        return 1
    if not edges:
        return 0
    key = (vertices, frozenset(edges.items()))
    if key not in _dc_memo:
        _dc_memo[key] = _dc_step(vertices, edges)
    return _dc_memo[key]


def _dc_step(vertices, edges):
    # disconnected multigraphs have no spanning tree: prune early
    adj = {x: [] for x in vertices}
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    start = next(iter(vertices))
    seen, stack = {start}, [start]
    while stack:
        x = stack.pop()
        for y in adj[x]:
            if y not in seen:
                seen.add(y)
                stack.append(y)
    if len(seen) != len(vertices):
        return 0
    (a, b), k = max(edges.items(), key=lambda item: (item[1], item[0]))
    deleted = {e: c for e, c in edges.items() if e != (a, b)}
    contracted = {}
    for (x, y), c in deleted.items():
        x, y = (a if x == b else x), (a if y == b else y)  # merge b into a
        key = (min(x, y), max(x, y))
        contracted[key] = contracted.get(key, 0) + c
    return (_deletion_contraction(vertices, deleted)
            + k * _deletion_contraction(vertices - {b}, contracted))


def _cofactor_fractions(A):
    """det of the Laplacian with row and column 0 deleted (a different cofactor than the implementation
    uses), by Gaussian elimination over the rationals."""
    n = len(A)
    M = [[Fraction(sum(A[i]) if i == j else -A[i][j]) for j in range(1, n)] for i in range(1, n)]
    det = Fraction(1)
    size = n - 1
    for c in range(size):
        r = next((r for r in range(c, size) if M[r][c] != 0), None)
        if r is None:
            return 0
        if r != c:
            M[c], M[r] = M[r], M[c]
            det = -det
        det *= M[c][c]
        for r in range(c + 1, size):
            f = M[r][c] / M[c][c]
            if f:
                M[r] = [x - f * y for x, y in zip(M[r], M[c])]
    assert det.denominator == 1
    return int(det)


def expected(A):
    """tau(G) from the cheapest independent rule that applies."""
    n = len(A)
    m = sum(A[u][v] for u in range(n) for v in range(u + 1, n))
    if not _connected(A):
        return 0
    if m == n - 1:
        return 1  # a connected graph with n-1 edges is a tree
    if m == n * (n - 1) // 2:
        return n ** (n - 2)  # Cayley's formula for K_n
    if m <= 24:
        edges = {(u, v): 1 for u in range(n) for v in range(u + 1, n) if A[u][v]}
        return _deletion_contraction(frozenset(range(n)), edges)
    return _cofactor_fractions(A)


def check(A, output):
    n = len(A)
    if isinstance(output, bool) or not isinstance(output, int):
        return False
    if not 0 <= output <= n ** max(n - 2, 0):  # G is a subgraph of K_n
        return False
    return output == expected(A)


# --------------------------------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------------------------------

_ops = 0


class CountingInt:
    """An integer that counts multiplications and divisions (floor division) performed on it.
    Additions, subtractions, negations and comparisons are not counted."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def __mul__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v * self._val(other))

    __rmul__ = __mul__

    def __floordiv__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self.v // self._val(other))

    def __rfloordiv__(self, other):
        global _ops
        _ops += 1
        return CountingInt(self._val(other) // self.v)

    def __add__(self, other):
        return CountingInt(self.v + self._val(other))

    __radd__ = __add__

    def __sub__(self, other):
        return CountingInt(self.v - self._val(other))

    def __rsub__(self, other):
        return CountingInt(self._val(other) - self.v)

    def __neg__(self):
        return CountingInt(-self.v)

    def __eq__(self, other):
        return self.v == self._val(other)

    def __ne__(self, other):
        return self.v != self._val(other)

    def __bool__(self):
        return self.v != 0

    def __int__(self):
        return int(self.v)

    def __hash__(self):
        return hash(self.v)


def generate_scaling(n, rng):
    """K_n with counting entries (the worst case for the enumeration: m = n(n-1)/2); resets the counter.
    For the Kirchhoff implementation any connected graph gives the same count (no zero pivot occurs)."""
    global _ops
    _ops = 0
    return tuple(tuple(CountingInt(0 if i == j else 1) for j in range(n)) for i in range(n))


def reported_cost(output):
    """Multiplications plus exact divisions performed on counting entries since generate_scaling."""
    return _ops
