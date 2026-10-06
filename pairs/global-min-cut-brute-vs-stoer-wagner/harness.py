"""Harness for global minimum cut (n x n symmetric non-negative integer weight matrix, zero diagonal).

Instances are tuples of tuples (immutable). Convention: for n < 2 there is no partition into two non-empty sides,
and the answer is None.

generate(n, rng) mixes six families so that the battery contains zero-weight entries, disconnected graphs
(minimum cut 0), planted sparse cuts between two dense halves, trivial (single-vertex) minimum cuts and all-zero
matrices. check(instance, output) is independent of both implementations: it computes the answer as the minimum,
over t = 1..n-1, of a maximum 0-t flow (Edmonds-Karp, max-flow = min-cut), and for n <= 10 it also enumerates all
vertex subsets with a different cut formula (sum of degrees in S minus twice the weight inside S). Every global cut
separates vertex 0 from some t, so min over t of the minimum 0-t cut is the global minimum cut.

V2 uses exact operation counts (measure "reported"): generate_scaling builds the matrix from CountingWeight objects,
which count every addition and every order comparison performed on weights by the UNCHANGED implementations;
reported_cost returns additions + comparisons since the instance was generated.
"""
from collections import deque
from itertools import combinations


# ---------------------------------------------------------------------------------------------- instances

def _family_matrix(n, rng):
    W = [[0] * n for _ in range(n)]

    def put(u, v, w):
        W[u][v] = W[v][u] = w

    fam = rng.randrange(6)
    if fam == 0:                                  # dense, weights 0..9 (zeros are zero-weight / absent edges)
        for u, v in combinations(range(n), 2):
            put(u, v, rng.randint(0, 9))
    elif fam == 1:                                # sparse, often disconnected (min cut 0)
        for u, v in combinations(range(n), 2):
            if rng.random() < 0.25:
                put(u, v, rng.randint(1, 9))
    elif fam == 2:                                # two components by construction (min cut 0 for n >= 2)
        side = [rng.random() < 0.5 for _ in range(n)]
        if n >= 2:
            side[0], side[1] = True, False
        for u, v in combinations(range(n), 2):
            if side[u] == side[v]:
                put(u, v, rng.randint(0, 9))
    elif fam == 3:                                # planted light cut between two dense halves
        side = [rng.random() < 0.5 for _ in range(n)]
        if n >= 2:
            side[0], side[1] = True, False
        for u, v in combinations(range(n), 2):
            if side[u] == side[v]:
                put(u, v, rng.randint(5, 9))
            elif rng.random() < 0.15:
                put(u, v, rng.randint(1, 2))
    elif fam == 4:                                # dense graph plus one weakly attached vertex
        for u, v in combinations(range(n), 2):
            put(u, v, rng.randint(3, 9))
        if n >= 2:
            x = rng.randrange(n)
            for v in range(n):
                if v != x:
                    put(x, v, 1 if rng.random() < 0.3 else 0)
    # fam == 5: all-zero matrix (every cut has weight 0)
    return W


def generate(n, rng):
    """One instance: an n x n symmetric matrix of non-negative integers with zero diagonal."""
    return tuple(tuple(row) for row in _family_matrix(n, rng))


# ---------------------------------------------------------------------------------------------- oracle

def _max_flow(cap, s, t):
    """Edmonds-Karp (BFS augmenting paths) on a dense capacity matrix; returns the max s-t flow value."""
    n = len(cap)
    res = [list(r) for r in cap]
    flow = 0
    while True:
        parent = [-1] * n
        parent[s] = s
        q = deque([s])
        while q and parent[t] < 0:
            u = q.popleft()
            ru = res[u]
            for v in range(n):
                if parent[v] < 0 and ru[v] > 0:
                    parent[v] = u
                    q.append(v)
        if parent[t] < 0:
            return flow
        b, v = None, t
        while v != s:
            u = parent[v]
            b = res[u][v] if b is None else min(b, res[u][v])
            v = u
        v = t
        while v != s:
            u = parent[v]
            res[u][v] -= b
            res[v][u] += b
            v = u
        flow += b


def _min_cut_by_flows(W):
    return min(_max_flow(W, 0, t) for t in range(1, len(W)))


def _min_cut_by_subsets(W):
    n = len(W)
    deg = [sum(r) for r in W]
    best = None
    for k in range(1, n):
        for S in combinations(range(n), k):
            inside = sum(W[u][v] for u, v in combinations(S, 2))
            c = sum(deg[u] for u in S) - 2 * inside
            best = c if best is None else min(best, c)
    return best


def check(instance, output):
    n = len(instance)
    if n < 2:
        return output is None
    W = [[int(x) for x in r] for r in instance]
    ref = _min_cut_by_flows(W)
    if n <= 10 and _min_cut_by_subsets(W) != ref:
        return False                              # the two oracle methods disagree: cannot be a valid answer
    return output == ref


# ---------------------------------------------------------------------------------------------- exact counts (V2)

_adds = 0
_cmps = 0


class CountingWeight:
    """Integer weight that counts additions and comparisons performed on it (harness instrumentation)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingWeight) else x

    def __add__(self, other):
        global _adds
        _adds += 1
        return CountingWeight(self.v + self._val(other))

    __radd__ = __add__

    def _cmp(self, other, op):
        global _cmps
        _cmps += 1
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

    def __ne__(self, other):
        return self._cmp(other, lambda a, b: a != b)

    def __hash__(self):
        return hash(self.v)

    def __int__(self):
        return int(self.v)

    def __repr__(self):
        return f"CountingWeight({self.v})"


def generate_scaling(n, rng):
    """Dense random weights 1..9 (every pair is an edge), as CountingWeight objects; resets both counters.

    The operation counts of both implementations depend only on n, not on the weights (no data-dependent
    early exits), so the family does not matter for the count; dense positive weights are used for definiteness.
    """
    global _adds, _cmps
    W = [[0] * n for _ in range(n)]
    for u, v in combinations(range(n), 2):
        W[u][v] = W[v][u] = rng.randint(1, 9)
    inst = tuple(tuple(CountingWeight(x) for x in row) for row in W)
    _adds = 0
    _cmps = 0
    return inst


def reported_cost(output):
    """Weight additions + weight comparisons performed since the instance was generated."""
    return _adds + _cmps


def counters():
    """(additions, comparisons) since the last generate_scaling (used by the experiment script)."""
    return _adds, _cmps
