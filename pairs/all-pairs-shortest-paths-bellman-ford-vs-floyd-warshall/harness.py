"""Instances: n x n weight matrices (tuples of tuples) of a digraph with non-negative integer weights.

W[i][j] is the weight of the edge i -> j or None if absent; the diagonal is 0. generate() varies the edge
density (0.1, 0.3, 0.6 or 1.0) and draws weights from [0, 20], so instances contain zero-weight edges,
ties between paths and unreachable pairs. generate_scaling() returns complete digraphs (m = n(n-1)) with
weights in [1, 1000], where Bellman-Ford's n(n-1) passes over m edges cost n^2 (n-1)^2 relaxations.

The oracle runs Dijkstra's algorithm with a binary heap from every source: a different algorithm from
both implementations under test (valid because weights are non-negative).

V2 counts relaxation steps (measure: "reported"; RESEARCH_LOG RL-047/RL-048): generate_scaling() wraps every
off-diagonal weight in CountingWeight, which counts each addition in which it (or a sum derived from it)
takes part; reported_cost() returns the number of such additions since the instance was generated. Each
relaxation step of the UNCHANGED implementations performs one addition (Bellman-Ford: dist[u] + w;
Floyd-Warshall: D[i][k] + D[k][j]). Every Bellman-Ford addition involves an input weight w, so all
n^2 (n-1)^2 are counted. Floyd-Warshall's n steps with i = j = k add the implementation's own diagonal
zeros (0 + 0, no input weight) and are not seen, so it reports n^3 - n.
"""
import heapq


def _matrix(n, rng, density, wmax):
    return tuple(
        tuple(0 if i == j else (rng.randint(0, wmax) if rng.random() < density else None) for j in range(n))
        for i in range(n)
    )


def generate(n, rng):
    density = rng.choice((0.1, 0.3, 0.6, 1.0))
    return _matrix(n, rng, density, 20)


# --- Exact relaxation counting for V2 (measure: "reported") -----------------------------------------

_additions = 0


def _val(x):
    return x.v if isinstance(x, CountingWeight) else x


class CountingWeight:
    """A weight (or path length) that counts every addition it takes part in; sums stay CountingWeight."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    def __add__(self, other):
        global _additions
        _additions += 1
        return CountingWeight(self.v + _val(other))

    def __radd__(self, other):
        global _additions
        _additions += 1
        return CountingWeight(_val(other) + self.v)

    def __lt__(self, other):
        return self.v < _val(other)

    def __le__(self, other):
        return self.v <= _val(other)

    def __gt__(self, other):
        return self.v > _val(other)

    def __ge__(self, other):
        return self.v >= _val(other)

    def __eq__(self, other):
        return self.v == _val(other)

    def __ne__(self, other):
        return self.v != _val(other)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f"CountingWeight({self.v!r})"


def generate_scaling(n, rng):
    """Complete digraph, weights in [1, 1000] wrapped in CountingWeight; resets the addition counter."""
    global _additions
    inst = tuple(tuple(0 if i == j else CountingWeight(rng.randint(1, 1000)) for j in range(n)) for i in range(n))
    _additions = 0
    return inst


def reported_cost(output):
    """Number of additions involving an input weight since the instance was generated."""
    return _additions


def _dijkstra_all(W):
    n = len(W)
    adj = [[(v, W[u][v]) for v in range(n) if v != u and W[u][v] is not None] for u in range(n)]
    out = []
    for s in range(n):
        dist = [None] * n
        heap = [(0, s)]
        while heap:
            d, u = heapq.heappop(heap)
            if dist[u] is not None:
                continue
            dist[u] = d
            for v, w in adj[u]:
                if dist[v] is None:
                    heapq.heappush(heap, (d + w, v))
        out.append(tuple(dist))
    return tuple(out)


def check(W, output):
    return output == _dijkstra_all(W)
