"""Harness for 2-SAT: brute force over 2^n assignments vs Aspvall-Plass-Tarjan (implication graph + SCC).

Instances: (n, clauses), variables 1..n, each clause a tuple of 0, 1 or 2 non-zero integers (DIMACS literals).
Outputs: a tuple of n booleans (a satisfying assignment) or None (unsatisfiable). The two algorithms may return
different satisfying assignments, so `equal` compares satisfiability only and `check` verifies every returned
assignment against all clauses.

generate(n, rng) mixes, for n >= 3:
  0  random 2-CNF (two distinct variables per clause), m = round(c n), c in {0.5, 1, 1.5, 2, 3} (both answers occur);
  1  planted satisfiable 2-CNF: m = 2n random clauses, each satisfied by a hidden assignment;
  2  forced unsatisfiable: implication paths x -> ... -> NOT x and NOT x -> ... -> x through random literals
     (long paths for large n), plus n random clauses, shuffled;
  3  mixed widths: clauses of width 1 or 2, repeated literals (v, v) and tautologies (v, -v) allowed, and an
     empty clause in about 1 formula in 8;
  4  the V2 family W_n below, with a random renaming and sign flip of the variables (unsatisfiable);
  5  planted satisfiable with a long implication chain l_1 -> l_2 -> ... (all l_i true in the hidden assignment)
     plus n random clauses the hidden assignment satisfies (deep DFS in the satisfiable case).
For n = 0, 1, 2 it returns the edge cases (no clauses, an empty clause, unit clauses, (v, v), (v, -v)).

check(instance, output) is independent of both implementations:
  - an assignment is verified against every clause (a certificate of satisfiability);
  - None is accepted only with a proof of unsatisfiability: an empty clause; for n <= 12 an exhaustive search
    over all assignments written here; for larger n an explicit pair of implication paths x ~> NOT x and
    NOT x ~> x found by breadth-first search (every edge comes from a clause, so the paths force both x = false
    and x = true). The variable x is located with Kosaraju's two-pass SCC algorithm (a different SCC algorithm
    from the Tarjan code under test). If no such x exists, the harness builds an assignment from Kosaraju's
    order and verifies it clause by clause; None is then rejected with that assignment as the certificate.
    Every verdict is backed by a certificate checked here; only if neither certificate is found (impossible by
    Aspvall-Plass-Tarjan) does check return None.

V2 (measure "reported"): exact operation counts. generate_scaling(n, rng) builds the deterministic family W_n
(n >= 3; rng is not used) from CountingLit literals and resets the counter:
    (x1 OR x_j) for j = 2..n                                (n - 1 clauses, x1 written first)
    (x2 OR x3), (x2 OR NOT x3), (NOT x2 OR x3), (NOT x2 OR NOT x3)   (an unsatisfiable core: 4 clauses)
    (NOT x_j OR x_{j+1}) for j = 1..n-1                     (an implication chain: n - 1 clauses)
so m = 2n + 2. The core alone is unsatisfiable, so W_n is unsatisfiable: brute force examines all 2^n
assignments and never reaches the chain clauses (every assignment falsifies a core clause first). Half of the
assignments (x1 true) pass all n - 1 star clauses with one literal evaluation each, which gives the Theta(n 2^n)
= Theta(m 2^n) worst case. The chain makes the depth-first search in the SCC algorithm Theta(n) deep.

CountingLit counts every primitive operation applied to an input literal or to a value computed from one
(arithmetic, comparisons, hashing, and use as a list index via __index__); arithmetic results are CountingLit
again, so in the SCC implementation every node id is derived from the input and every list access at a node
reached through an edge is counted. The implementations are unchanged and count nothing themselves.
"""
import itertools
from collections import deque


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _lit(v, rng):
    return v if rng.random() < 0.5 else -v


def _random_clause(n, rng):
    a, b = rng.sample(range(1, n + 1), 2)
    return (_lit(a, rng), _lit(b, rng))


def _family(n):
    """The V2 family W_n as plain-integer clauses (n >= 3)."""
    star = [(1, j) for j in range(2, n + 1)]
    core = [(2, 3), (2, -3), (-2, 3), (-2, -3)]
    chain = [(-j, j + 1) for j in range(1, n)]
    return star + core + chain


def _small(n, rng):
    if n == 0:
        return (0, ()) if rng.random() < 0.5 else (0, ((),))
    clauses = []
    for _ in range(rng.randint(1, 3 * n + 1)):
        width = rng.choice((0, 1, 1, 2, 2, 2, 2, 2, 2, 2)) if rng.random() < 0.3 else rng.choice((1, 2))
        clauses.append(tuple(_lit(rng.randint(1, n), rng) for _ in range(width)))
    return n, tuple(clauses)


def generate(n, rng):
    if n < 3:
        return _small(n, rng)
    kind = rng.randrange(6)
    if kind == 0:
        c = rng.choice((0.5, 1.0, 1.5, 2.0, 3.0))
        return n, tuple(_random_clause(n, rng) for _ in range(round(c * n)))
    if kind in (1, 5):
        star = {v: rng.random() < 0.5 for v in range(1, n + 1)}

        def true_lit(v):
            return v if star[v] else -v
        clauses = []
        if kind == 5:
            order = rng.sample(range(1, n + 1), n)
            clauses += [(-true_lit(order[i]), true_lit(order[i + 1])) for i in range(n - 1)]
        target = len(clauses) + (2 * n if kind == 1 else n)
        while len(clauses) < target:
            cl = _random_clause(n, rng)
            if any(star[abs(l)] == (l > 0) for l in cl):
                clauses.append(cl)
        rng.shuffle(clauses)
        return n, tuple(clauses)
    if kind == 2:
        k = max(1, (n - 1) // 2)
        x, *rest = rng.sample(range(1, n + 1), min(n, 2 * k + 1))
        path1 = [_lit(v, rng) for v in rest[:k]]          # x -> path1 -> NOT x
        path2 = [_lit(v, rng) for v in rest[k:2 * k]]     # NOT x -> path2 -> x
        clauses = []
        for start, mids, end in ((x, path1, -x), (-x, path2, x)):
            seq = [start] + mids + [end]
            clauses += [(-seq[i], seq[i + 1]) for i in range(len(seq) - 1)]   # seq[i] -> seq[i+1]
        clauses += [_random_clause(n, rng) for _ in range(n)]
        rng.shuffle(clauses)
        return n, tuple(clauses)
    if kind == 3:
        clauses = []
        for _ in range(round(2 * n)):
            r = rng.random()
            v = rng.randint(1, n)
            if r < 0.15:
                clauses.append((_lit(v, rng),))
            elif r < 0.25:
                l = _lit(v, rng)
                clauses.append((l, l))
            elif r < 0.32:
                clauses.append((v, -v) if rng.random() < 0.5 else (-v, v))
            else:
                clauses.append(_random_clause(n, rng))
        if rng.random() < 0.125:
            clauses.insert(rng.randrange(len(clauses) + 1), ())
        return n, tuple(clauses)
    # kind == 4: W_n under a random renaming and sign flip of the variables
    perm = rng.sample(range(1, n + 1), n)
    sign = [1 if rng.random() < 0.5 else -1 for _ in range(n)]

    def ren(l):
        v = abs(l)
        return (1 if l > 0 else -1) * sign[v - 1] * perm[v - 1]
    return n, tuple(tuple(ren(l) for l in cl) for cl in _family(n))


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _satisfies(clauses, values):
    """values[v] is the truth value of x_v (index 0 unused)."""
    return all(any(values[abs(l)] == (l > 0) for l in cl) for cl in clauses)


def _lit_id(l, n):
    return l + n                              # literal l in -n..n (l != 0) -> 0..2n


def _implication_graph(n, clauses):
    succ = [[] for _ in range(2 * n + 1)]
    pred = [[] for _ in range(2 * n + 1)]
    for cl in clauses:
        a, b = (cl[0], cl[0]) if len(cl) == 1 else cl
        for u, w in ((-a, b), (-b, a)):        # (a OR b): NOT a -> b, NOT b -> a
            succ[_lit_id(u, n)].append(_lit_id(w, n))
            pred[_lit_id(w, n)].append(_lit_id(u, n))
    return succ, pred


def _kosaraju(n, succ, pred):
    """Component labels over literal ids; labels increase along a topological order of the condensation."""
    nodes = [i for i in range(2 * n + 1) if i != n]
    seen = [False] * (2 * n + 1)
    finish = []
    for s in nodes:                            # pass 1: finishing order on the graph (iterative DFS)
        if seen[s]:
            continue
        seen[s] = True
        it = [(s, iter(succ[s]))]
        while it:
            v, children = it[-1]
            for w in children:
                if not seen[w]:
                    seen[w] = True
                    it.append((w, iter(succ[w])))
                    break
            else:
                it.pop()
                finish.append(v)
    label = [-1] * (2 * n + 1)
    c = 0
    for s in reversed(finish):                 # pass 2: on the transpose, in decreasing finishing time
        if label[s] != -1:
            continue
        label[s] = c
        todo = [s]
        while todo:
            v = todo.pop()
            for w in pred[v]:
                if label[w] == -1:
                    label[w] = c
                    todo.append(w)
        c += 1
    return label


def _reaches(succ, s, t):
    """Breadth-first search; returns the path s ~> t as a list of literal ids, or None."""
    parent = {s: None}
    q = deque([s])
    while q and t not in parent:
        v = q.popleft()
        for w in succ[v]:
            if w not in parent:
                parent[w] = v
                q.append(w)
    if t not in parent:
        return None
    path = [t]
    while path[-1] != s:
        path.append(parent[path[-1]])
    return path[::-1]


def _edge_from_clause(n, clauses_set, u, w):
    a, b = -(u - n), w - n                     # edge NOT a -> b must come from clause (a OR b) or (b OR a)
    return (a, b) in clauses_set or (b, a) in clauses_set or (a == b and (a,) in clauses_set)


def check(instance, output):
    n, clauses = instance
    if output is not None:
        if not isinstance(output, tuple) or len(output) != n or not all(isinstance(x, bool) for x in output):
            return False
        return _satisfies(clauses, (None,) + output)
    # output is None: accept only with a proof of unsatisfiability
    if any(len(cl) == 0 for cl in clauses):
        return True
    if n <= 12:
        return not any(_satisfies(clauses, (None,) + vals)
                       for vals in itertools.product((False, True), repeat=n))
    succ, pred = _implication_graph(n, clauses)
    label = _kosaraju(n, succ, pred)
    clauses_set = set(clauses)
    for v in range(1, n + 1):
        if label[_lit_id(v, n)] == label[_lit_id(-v, n)]:
            p = _reaches(succ, _lit_id(v, n), _lit_id(-v, n))
            q = _reaches(succ, _lit_id(-v, n), _lit_id(v, n))
            if p and q and all(_edge_from_clause(n, clauses_set, path[i], path[i + 1])
                               for path in (p, q) for i in range(len(path) - 1)):
                return True                    # x -> ... -> NOT x and NOT x -> ... -> x: no value of x works
            return None
    # no contradictory component: x_v true iff its component comes later in topological order
    values = (None,) + tuple(label[_lit_id(v, n)] > label[_lit_id(-v, n)] for v in range(1, n + 1))
    if _satisfies(clauses, values):
        return False                           # satisfiable (certificate found): None was wrong
    return None


def equal(a, b):
    return (a is None) == (b is None)


# --------------------------------------------------------------------------
# Exact operation counting for V2 (measure: "reported")
# --------------------------------------------------------------------------

_ops = 0


class CountingLit:
    """An integer that counts every primitive operation applied to it (results of arithmetic stay counting)."""
    __slots__ = ("v",)

    def __init__(self, v):
        self.v = v

    @staticmethod
    def _val(x):
        return x.v if isinstance(x, CountingLit) else x

    def _arith(self, f, other=None):
        global _ops
        _ops += 1
        return CountingLit(f(self.v) if other is None else f(self.v, self._val(other)))

    def _cmp(self, f, other):
        global _ops
        _ops += 1
        return f(self.v, self._val(other))

    def __abs__(self):
        return self._arith(abs)

    def __neg__(self):
        return self._arith(lambda a: -a)

    def __add__(self, o):
        return self._arith(lambda a, b: a + b, o)

    def __radd__(self, o):
        return self._arith(lambda a, b: b + a, o)

    def __sub__(self, o):
        return self._arith(lambda a, b: a - b, o)

    def __rsub__(self, o):
        return self._arith(lambda a, b: b - a, o)

    def __mul__(self, o):
        return self._arith(lambda a, b: a * b, o)

    def __rmul__(self, o):
        return self._arith(lambda a, b: b * a, o)

    def __xor__(self, o):
        return self._arith(lambda a, b: a ^ b, o)

    def __rxor__(self, o):
        return self._arith(lambda a, b: b ^ a, o)

    def __and__(self, o):
        return self._arith(lambda a, b: a & b, o)

    def __rand__(self, o):
        return self._arith(lambda a, b: b & a, o)

    def __rshift__(self, o):
        return self._arith(lambda a, b: a >> b, o)

    def __rrshift__(self, o):
        return self._arith(lambda a, b: b >> a, o)

    def __lt__(self, o):
        return self._cmp(lambda a, b: a < b, o)

    def __le__(self, o):
        return self._cmp(lambda a, b: a <= b, o)

    def __gt__(self, o):
        return self._cmp(lambda a, b: a > b, o)

    def __ge__(self, o):
        return self._cmp(lambda a, b: a >= b, o)

    def __eq__(self, o):
        return self._cmp(lambda a, b: a == b, o)

    def __ne__(self, o):
        return self._cmp(lambda a, b: a != b, o)

    def __index__(self):
        global _ops
        _ops += 1
        return self.v

    __int__ = __index__

    def __hash__(self):
        global _ops
        _ops += 1
        return hash(self.v)

    def __bool__(self):
        global _ops
        _ops += 1
        return self.v != 0

    def __repr__(self):
        return f"CountingLit({self.v})"


def generate_scaling(n, rng):
    """The family W_n (deterministic; rng unused) with counting literals; resets the operation counter."""
    global _ops
    if n < 3:
        raise ValueError("the V2 family needs n >= 3")
    clauses = tuple(tuple(CountingLit(l) for l in cl) for cl in _family(n))
    _ops = 0
    return n, clauses


def reported_cost(output):
    """Operations on input-derived values performed since the instance was generated."""
    return _ops
