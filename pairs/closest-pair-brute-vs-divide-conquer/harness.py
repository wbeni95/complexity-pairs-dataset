"""Instances: n >= 2 points in the plane with integer coordinates, as a tuple of (x, y) tuples.

generate mixes three kinds: coordinates in [0, 10^6) (generic position), coordinates in [0, sqrt(n) + 2)
(many duplicate points, distance 0, collinear points), and all points on one vertical line (every point
falls in the dividing strip). generate_scaling uses coordinates in [0, 10^9).

V2 counts multiplications (measure: "reported"; RESEARCH_LOG RL-047/RL-048): generate_scaling() wraps every
coordinate in CountingInt, whose differences, products and sums stay CountingInt, and counts every
multiplication of such values, a squaring `** 2` counted as one. reported_cost() returns that count. The
UNCHANGED brute force squares dx and dy for every pair: exactly n(n-1). Divide and conquer multiplies in
its base cases (2 per pair), in the strip filter (one squaring per point per internal node) and in the strip
scan (dy*dy for every examined pair, plus dx*dx and a second dy*dy for each pair it does not stop at).
Comparisons are NOT part of the reported cost: the initial sorted() and the min() calls compare inside CPython's C code, and their
comparison counts differ between Python 3.12.10 and 3.14.2 (experiments/2026-10-07b_count_v2_cross_version.py);
multiplications all happen in the implementations' own Python code and are identical under both. They are tallied separately in _comparisons for experiments only.
"""


def generate(n, rng):
    kind = rng.randrange(3)
    if kind == 0:
        return tuple((rng.randrange(10 ** 6), rng.randrange(10 ** 6)) for _ in range(n))
    if kind == 1:
        r = int(n ** 0.5) + 2
        return tuple((rng.randrange(r), rng.randrange(r)) for _ in range(n))
    x = rng.randrange(1000)
    return tuple((x, rng.randrange(10 ** 6)) for _ in range(n))


# --- Exact multiplication counting for V2 (measure: "reported") -------------------------------------

_mults = 0
_comparisons = 0     # informational only (not reported; see the module docstring)


def _val(x):
    return x.v if isinstance(x, CountingInt) else x


class CountingInt:
    """An integer coordinate (or a value derived from coordinates) that counts multiplications."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __mul__(self, other):
        global _mults
        _mults += 1
        return CountingInt(self.v * _val(other))

    __rmul__ = __mul__

    def __pow__(self, exponent):
        global _mults
        if exponent != 2:
            raise ValueError("CountingInt only counts squarings")
        _mults += 1
        return CountingInt(self.v * self.v)

    def __add__(self, other):
        return CountingInt(self.v + _val(other))

    __radd__ = __add__

    def __sub__(self, other):
        return CountingInt(self.v - _val(other))

    def __rsub__(self, other):
        return CountingInt(_val(other) - self.v)

    def __lt__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v < _val(other)

    def __le__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v <= _val(other)

    def __gt__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v > _val(other)

    def __ge__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v >= _val(other)

    def __eq__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v == _val(other)

    def __ne__(self, other):
        global _comparisons
        _comparisons += 1
        return self.v != _val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingInt({self.v!r})"


def generate_scaling(n, rng):
    """Coordinates in [0, 10^9), wrapped in CountingInt; resets the counters."""
    global _mults, _comparisons
    inst = tuple((CountingInt(rng.randrange(10 ** 9)), CountingInt(rng.randrange(10 ** 9))) for _ in range(n))
    _mults = _comparisons = 0
    return inst


def reported_cost(output):
    """Number of multiplications (squarings included) performed since the instance was generated."""
    return _mults


def check(points, output):
    """Exact oracle independent of both implementations: a plane sweep with pruning along the coordinate
    of larger spread (O(n^2) in the worst case, fast on the harness instances)."""
    k = 0 if (max(p[0] for p in points) - min(p[0] for p in points)
              >= max(p[1] for p in points) - min(p[1] for p in points)) else 1
    pts = sorted(points, key=lambda p: p[k])
    best = None
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            gap = pts[j][k] - pts[i][k]
            if best is not None and gap * gap >= best:
                break
            d = (pts[i][0] - pts[j][0]) ** 2 + (pts[i][1] - pts[j][1]) ** 2
            if best is None or d < best:
                best = d
    return output == best
