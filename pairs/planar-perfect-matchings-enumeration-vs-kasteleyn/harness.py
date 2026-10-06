"""Harness: weighted perfect matchings (dimer partition function) of a x b grid graphs.

Instances: (a, b, W). The grid has N = a*b vertices, vertex u = r*b + c (0 <= r < a, 0 <= c < b), and W is an
N x N symmetric matrix of non-negative integers (tuple of tuples) that is non-zero only for grid neighbours
(|r - r'| + |c - c'| = 1); weight 0 means the edge is absent. The answer is the sum over perfect matchings of
the product of their edge weights: an exact non-negative integer, 1 for N = 0 (the empty matching), 0 for odd N.

The size parameter n is the number of vertices N. generate(n, rng) picks a shape a x b with a*b = n (for
n = 0: a = 0 or b = 0 with the other side in 0..3, W = ()) and one of these weight patterns:
  unit    every grid edge weight 1 (the answer is the number of domino tilings of the rectangle);
  subset  every grid edge present (weight 1) with probability p in {0.5, 0.75, 0.9}, absent (0) otherwise;
  small   every grid edge weight uniform in 0..3;
  large   every grid edge weight 0 with probability 0.2, otherwise uniform in 1..10^9;
  ladder  unit weights on the 2 x (n/2) or (n/2) x 2 ladder (odd n: falls back to a random shape);
  path    unit weights on the 1 x n or n x 1 path.
Shapes with both sides >= 2 are preferred whenever n has one (except for ladder and path).

check(instance, output) is independent of both implementations: a transfer-matrix ("broken profile")
dynamic programme over the cells in row-major order, after transposing so that the row width is min(a, b).
The state is the set of the next `width` cells that are already covered (bitmask); a free cell is covered
by a horizontal edge to its right neighbour or a vertical edge to the cell below, and each choice multiplies
the weight of the state by that edge's weight. It is exact for any weights and costs O(N 2^width) dictionary
operations. check also requires a non-negative int (bool rejected).

V2 (measure "reported"): generate_scaling(n, rng) returns the (n/2) x 2 ladder (n even; rng is not used) with
unit weights, every entry of W (zeros included) being a CountingInt, and resets the counter. CountingInt counts
multiplications and floor divisions performed on it; additions, subtractions, negations, comparisons, truth
tests and abs() are not counted. The implementations are unchanged: the Kasteleyn implementation builds its
matrix from the entries of W, so every multiplication and exact division of Bareiss's elimination is counted;
the enumeration multiplies a weight from W by a subtotal once per search-tree edge. reported_cost returns the
count. No comparison-based CPython built-in (sorted, min, max) sees a counting value; the only built-in applied
to one is abs() on the Kasteleyn result, which counts nothing. So the counts do not depend on the Python version
through such calls.
"""

# --------------------------------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------------------------------

KINDS = ("unit", "unit", "subset", "subset", "small", "small", "large", "ladder", "path")


def _grid_edges(a, b):
    """Edges (u, v), u < v, of the a x b grid: horizontal (u, u+1) and vertical (u, u+b)."""
    edges = []
    for r in range(a):
        for c in range(b):
            u = r * b + c
            if c + 1 < b:
                edges.append((u, u + 1))
            if r + 1 < a:
                edges.append((u, u + b))
    return edges


def _matrix(a, b, weight_of_edge):
    N = a * b
    W = [[0] * N for _ in range(N)]
    for u, v in _grid_edges(a, b):
        W[u][v] = W[v][u] = weight_of_edge()
    return tuple(tuple(row) for row in W)


def generate(n, rng):
    if n == 0:
        k = rng.randint(0, 3)
        a, b = (0, k) if rng.random() < 0.5 else (k, 0)
        return (a, b, ())
    kind = rng.choice(KINDS)
    shapes = [(d, n // d) for d in range(1, n + 1) if n % d == 0]
    proper = [s for s in shapes if min(s) >= 2]
    if kind == "ladder" and n % 2 == 0 and n >= 4:
        a, b = rng.choice([(2, n // 2), (n // 2, 2)])
    elif kind == "path":
        a, b = rng.choice([(1, n), (n, 1)])
    else:
        a, b = rng.choice(proper or shapes)
    if kind == "subset":
        p = rng.choice([0.5, 0.75, 0.9])
        weight = lambda: 1 if rng.random() < p else 0  # noqa: E731
    elif kind == "small":
        weight = lambda: rng.randint(0, 3)  # noqa: E731
    elif kind == "large":
        weight = lambda: 0 if rng.random() < 0.2 else rng.randint(1, 10 ** 9)  # noqa: E731
    else:  # unit, ladder, path
        weight = lambda: 1  # noqa: E731
    return (a, b, _matrix(a, b, weight))


# --------------------------------------------------------------------------------------------------
# Independent oracle: transfer-matrix (broken-profile) dynamic programme
# --------------------------------------------------------------------------------------------------

def transfer_matrix_count(a, b, W):
    """Sum over perfect matchings of the product of edge weights, by a row-major profile DP.

    The grid is traversed as `rows` x `width` with width = min(a, b) (transposed if b > a). mask bit k
    says that the k-th cell from the current one (in traversal order) is already covered."""
    if a * b == 0:
        return 1
    if b > a:
        rows, width = b, a
        def vertex(r, c):  # cell (r, c) of the transposed grid is vertex (c, r) of the input
            return c * b + r
    else:
        rows, width = a, b
        def vertex(r, c):
            return r * b + c
    top = 1 << (width - 1)
    states = {0: 1}
    for r in range(rows):
        for c in range(width):
            u = vertex(r, c)
            nxt = {}
            for mask, val in states.items():
                if mask & 1:  # this cell is already covered
                    key = mask >> 1
                    nxt[key] = nxt.get(key, 0) + val
                    continue
                if c + 1 < width and not mask & 2:  # edge to the next cell in this row
                    w = W[u][vertex(r, c + 1)]
                    if w:
                        key = (mask >> 1) | 1
                        nxt[key] = nxt.get(key, 0) + val * w
                if r + 1 < rows:  # edge to the cell below
                    w = W[u][vertex(r + 1, c)]
                    if w:
                        key = (mask >> 1) | top
                        nxt[key] = nxt.get(key, 0) + val * w
            states = nxt
    return states.get(0, 0)


def check(instance, output):
    a, b, W = instance
    if isinstance(output, bool) or not isinstance(output, int) or output < 0:
        return False
    if (a * b) % 2 == 1 and output != 0:
        return False
    return output == transfer_matrix_count(a, b, W)


# --------------------------------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------------------------------

_ops = 0


class CountingInt:
    """An integer that counts multiplications and floor divisions performed on it. Additions, subtractions,
    negations, comparisons, truth tests and abs() are not counted."""
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

    def __abs__(self):
        return CountingInt(abs(self.v))

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

    def __repr__(self):
        return f"CountingInt({self.v})"


def ladder(rows, weight=1):
    """(rows x 2) ladder with every grid edge of the given weight, plain ints."""
    return (rows, 2, _matrix(rows, 2, lambda: weight))


def generate_scaling(n, rng):
    """The (n/2) x 2 ladder (n even) with unit weights, every entry of W a CountingInt; resets the counter."""
    global _ops
    if n % 2 or n < 2:
        raise ValueError("generate_scaling needs an even n >= 2")
    a, b, W = ladder(n // 2)
    _ops = 0
    return (a, b, tuple(tuple(CountingInt(x) for x in row) for row in W))


def reported_cost(output):
    """Multiplications plus floor divisions performed on counting values since generate_scaling."""
    return _ops
