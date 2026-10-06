"""Harness for counting directed Hamiltonian cycles: enumeration vs inclusion-exclusion vs Held-Karp counting DP.

Instances: an n x n adjacency matrix as a tuple of n tuples with entries 0 or 1; adj[u][v] = 1 is an arc u -> v.
The diagonal is ignored by every algorithm (some instances carry random diagonal bits to test this). Symmetric
matrices are undirected graphs. Output: the number of directed Hamiltonian cycles, each counted once; n <= 1
gives 0 and n = 2 gives adj[0][1] * adj[1][0]. For a symmetric matrix with n >= 3 the answer is twice the number
of undirected Hamiltonian cycles.

generate(n, rng), for n >= 3, mixes 8 kinds, each under a random relabelling of the vertices:
  0  random digraph G(n, p), p in {0.3, 0.5, 0.7, 0.9};
  1  random undirected graph G(n, p), p in {0.3, 0.5, 0.7, 0.9};
  2  the complete digraph, or the complete digraph minus one arc;
  3  an undirected cycle C_n or a directed cycle;
  4  a complete bipartite graph K_{a,b}: a = b = n/2 for even n (half the time), otherwise a != b (answer 0);
  5  a random digraph (p = 0.7) in which one vertex loses all out-arcs or all in-arcs (answer 0);
  6  a planted directed Hamiltonian cycle plus random arcs (p in {0.1, 0.25}); for n = 10 half of these are the
     Petersen graph instead;
  7  a planted undirected Hamiltonian cycle plus random edges (p in {0.1, 0.25}).
About 30% of all instances get random bits on the diagonal. For n <= 2 the diagonal bits are random
(probability 1/2) and for n = 2 both arcs are present with probability 1/2, otherwise one or none.

check(instance, output) is independent of the implementations. It returns the exact verdict when it can:
  - n <= 2 by the conventions above;
  - closed forms valid for every n: complete digraph (n-1)!; complete digraph minus one arc (n-1)! - (n-2)!
    (the cycles of the complete digraph through a fixed arc are (n-2)!); not strongly connected, which includes a
    vertex without out-arcs or in-arcs: 0; strongly connected with every out-degree 1 or every in-degree 1 (a
    single directed n-cycle): 1; undirected n-cycle: 2; undirected bipartite with sides of different sizes: 0;
    complete bipartite K_{m,m}: m!(m-1)!;
  - otherwise a depth-first backtracking count that extends paths from vertex 0 along existing arcs only. For
    n <= 10 it always runs to completion (at most 986 410 search nodes); for n > 10 it gives up after 200 000
    nodes.
  If no exact verdict is available it still rejects outputs that violate necessary conditions (a negative or
  non-integer count, more cycles than the product of the out-degrees or of the in-degrees, an odd count for an
  undirected graph with n >= 3), and otherwise returns None.

V2 (measure "reported"): generate_scaling(n, rng) is the complete digraph K_n (deterministic; rng unused) whose
entries are CountingInt values (1 off the diagonal, 0 on it), and it resets the counter. CountingInt counts every
truth test, comparison and arithmetic operation (+, -, *, unary -) applied to an entry or to a value computed from
one; arithmetic results are CountingInt again. The implementations are unchanged. On K_n the enumeration finds no
missing arc, so it never stops early. Exact counts (derived in entry.json, checked in
experiments/2026-10-06f_entries_hamiltonian.py):
  enumeration          n!                                         truth tests
  inclusion-exclusion  n(n-1)(n+2)2^(n-2) + 2^(n-1) - 1            multiplications + additions/subtractions
  Held-Karp counting   (n-1)(n-2)2^(n-2) + 2(n-1)                  multiplications + additions
No counted operation happens inside a CPython built-in such as sorted, min or max.
"""
import math

DFS_FULL_UP_TO = 10
DFS_BUDGET = 200_000


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _empty(n):
    return [[0] * n for _ in range(n)]


def _relabel(a, rng):
    n = len(a)
    p = list(range(n))
    rng.shuffle(p)
    b = _empty(n)
    for u in range(n):
        for v in range(n):
            b[p[u]][p[v]] = a[u][v]
    return b


def _random_digraph(n, p, rng):
    a = _empty(n)
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < p:
                a[u][v] = 1
    return a


def _random_graph(n, p, rng):
    a = _empty(n)
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                a[u][v] = a[v][u] = 1
    return a


def complete_digraph(n):
    return [[1 if u != v else 0 for v in range(n)] for u in range(n)]


def petersen():
    a = _empty(10)
    edges = [(i, (i + 1) % 5) for i in range(5)]                 # outer 5-cycle
    edges += [(i, i + 5) for i in range(5)]                      # spokes
    edges += [(5 + i, 5 + (i + 2) % 5) for i in range(5)]        # inner pentagram
    for u, v in edges:
        a[u][v] = a[v][u] = 1
    return a


def complete_bipartite(a_size, b_size):
    n = a_size + b_size
    a = _empty(n)
    for u in range(a_size):
        for v in range(a_size, n):
            a[u][v] = a[v][u] = 1
    return a


def generate(n, rng):
    if n == 0:
        return ()
    if n <= 2:
        arcs = (1, 1) if rng.random() < 0.5 else rng.choice(((0, 0), (1, 0), (0, 1)))   # used for n = 2
        a = [[1 if u == v and rng.random() < 0.5 else 0 for v in range(n)] for u in range(n)]
        if n == 2:
            a[0][1], a[1][0] = arcs
        return tuple(tuple(row) for row in a)
    kind = rng.randrange(8)
    if kind == 0:
        a = _random_digraph(n, rng.choice((0.3, 0.5, 0.7, 0.9)), rng)
    elif kind == 1:
        a = _random_graph(n, rng.choice((0.3, 0.5, 0.7, 0.9)), rng)
    elif kind == 2:
        a = complete_digraph(n)
        if rng.random() < 0.5:
            u, v = rng.sample(range(n), 2)
            a[u][v] = 0
    elif kind == 3:
        a = _empty(n)
        directed = rng.random() < 0.5
        for i in range(n):
            a[i][(i + 1) % n] = 1
            if not directed:
                a[(i + 1) % n][i] = 1
    elif kind == 4:
        if n % 2 == 0 and rng.random() < 0.5:
            a = complete_bipartite(n // 2, n // 2)
        else:
            sizes = [s for s in range(1, n) if 2 * s != n]
            s = rng.choice(sizes)
            a = complete_bipartite(s, n - s)
    elif kind == 5:
        a = _random_digraph(n, 0.7, rng)
        v = rng.randrange(n)
        sink = rng.random() < 0.5
        for w in range(n):
            if w != v:
                if sink:
                    a[v][w] = 0                  # v has no out-arcs
                else:
                    a[w][v] = 0                  # v has no in-arcs
    elif kind == 6:
        if n == 10 and rng.random() < 0.5:
            a = petersen()
        else:
            a = _random_digraph(n, rng.choice((0.1, 0.25)), rng)
            order = rng.sample(range(n), n)
            for i in range(n):
                a[order[i]][order[(i + 1) % n]] = 1
    else:
        a = _random_graph(n, rng.choice((0.1, 0.25)), rng)
        order = rng.sample(range(n), n)
        for i in range(n):
            u, v = order[i], order[(i + 1) % n]
            a[u][v] = a[v][u] = 1
    a = _relabel(a, rng)
    if rng.random() < 0.3:
        for v in range(n):
            a[v][v] = 1 if rng.random() < 0.5 else 0
    return tuple(tuple(row) for row in a)


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _arc_lists(adj):
    n = len(adj)
    succ = [[v for v in range(n) if v != u and adj[u][v]] for u in range(n)]
    pred = [[u for u in range(n) if u != v and adj[u][v]] for v in range(n)]
    return succ, pred


def _reach_all(n, nbrs):
    seen = [False] * n
    seen[0] = True
    todo = [0]
    while todo:
        v = todo.pop()
        for w in nbrs[v]:
            if not seen[w]:
                seen[w] = True
                todo.append(w)
    return all(seen)


def _symmetric(adj):
    n = len(adj)
    return all(bool(adj[u][v]) == bool(adj[v][u]) for u in range(n) for v in range(u + 1, n))


def _two_colouring(n, succ):
    """Colours 0/1 of a connected undirected graph, or None if it has an odd cycle."""
    colour = [-1] * n
    colour[0] = 0
    todo = [0]
    while todo:
        v = todo.pop()
        for w in succ[v]:
            if colour[w] == -1:
                colour[w] = 1 - colour[v]
                todo.append(w)
            elif colour[w] == colour[v]:
                return None
    return colour


def closed_form(adj):
    """Exact count for the recognised graph families, or None. Returns (count, rule name)."""
    n = len(adj)
    if n <= 1:
        return 0, "n <= 1"
    if n == 2:
        return (1 if adj[0][1] and adj[1][0] else 0), "n = 2"
    succ, pred = _arc_lists(adj)
    missing = n * (n - 1) - sum(len(s) for s in succ)
    if missing == 0:
        return math.factorial(n - 1), "complete digraph"
    if missing == 1:
        return math.factorial(n - 1) - math.factorial(n - 2), "complete digraph minus one arc"
    if not (_reach_all(n, succ) and _reach_all(n, pred)):
        return 0, "not strongly connected"
    if all(len(s) == 1 for s in succ) or all(len(p) == 1 for p in pred):
        return 1, "single directed cycle"
    if _symmetric(adj):
        if all(len(s) == 2 for s in succ):
            return 2, "undirected cycle"
        colour = _two_colouring(n, succ)
        if colour is not None:
            side = sum(colour)
            if 2 * side != n:
                return 0, "bipartite, unequal sides"
            m = n // 2
            if sum(len(s) for s in succ) == 2 * m * m:
                return math.factorial(m) * math.factorial(m - 1), "complete bipartite K_{m,m}"
    return None


def dfs_count(adj, budget=None):
    """Hamiltonian cycles by backtracking from vertex 0 along existing arcs; None if `budget` nodes are exceeded."""
    n = len(adj)
    succ, _ = _arc_lists(adj)
    closes = [bool(adj[v][0]) and v != 0 for v in range(n)]
    full = (1 << n) - 1
    count = 0
    nodes = 0
    stack = [(0, 1)]
    while stack:
        v, visited = stack.pop()
        nodes += 1
        if budget is not None and nodes > budget:
            return None
        if visited == full:
            if closes[v]:
                count += 1
            continue
        for w in succ[v]:
            if not (visited >> w) & 1:
                stack.append((w, visited | (1 << w)))
    return count


def exact_count(adj):
    """(count, rule) from a closed form or the depth-first count, or (None, reason)."""
    cf = closed_form(adj)
    if cf is not None:
        return cf
    n = len(adj)
    budget = None if n <= DFS_FULL_UP_TO else DFS_BUDGET
    c = dfs_count(adj, budget)
    if c is not None:
        return c, "depth-first count"
    return None, "no exact rule"


def check(instance, output):
    if isinstance(output, bool) or not isinstance(output, int) or output < 0:
        return False
    expected, _ = exact_count(instance)
    if expected is not None:
        return output == expected
    succ, pred = _arc_lists(instance)
    if output > math.prod(len(s) for s in succ) or output > math.prod(len(p) for p in pred):
        return False
    if len(instance) >= 3 and _symmetric(instance) and output % 2 == 1:
        return False
    return None


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = {"truth": 0, "compare": 0, "mul": 0, "add": 0}


class CountingInt:
    """An integer that counts every truth test, comparison and +, -, * it takes part in."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingInt) else x

    def _arith(self, kind, value):
        _ops[kind] += 1
        return CountingInt(value)

    def __add__(self, o):
        return self._arith("add", self.v + self._val(o))

    def __radd__(self, o):
        return self._arith("add", self._val(o) + self.v)

    def __sub__(self, o):
        return self._arith("add", self.v - self._val(o))

    def __rsub__(self, o):
        return self._arith("add", self._val(o) - self.v)

    def __neg__(self):
        return self._arith("add", -self.v)

    def __mul__(self, o):
        return self._arith("mul", self.v * self._val(o))

    def __rmul__(self, o):
        return self._arith("mul", self._val(o) * self.v)

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

    def __bool__(self):
        _ops["truth"] += 1
        return self.v != 0

    def __int__(self):
        return self.v

    def __repr__(self):
        return f"CountingInt({self.v})"


def reset_counter():
    for key in _ops:
        _ops[key] = 0


def counted_complete_digraph(n):
    return tuple(tuple(CountingInt(1 if u != v else 0) for v in range(n)) for u in range(n))


def generate_scaling(n, rng):
    """Complete digraph K_n with CountingInt entries (deterministic; rng unused); resets the counter."""
    inst = counted_complete_digraph(n)
    reset_counter()
    return inst


def reported_cost(output):
    """Counted operations on entry-derived values since the scaling instance was generated."""
    return sum(_ops.values())
