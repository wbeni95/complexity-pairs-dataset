"""Harness for Horn-SAT: brute force over 2^n assignments vs unit propagation (Dowling & Gallier 1984).

Instances: (n, clauses), variables 1..n, each clause a tuple of non-zero integers (DIMACS literals) with at most one
positive literal. Outputs: the least model as a tuple of n booleans, or None (unsatisfiable). Both algorithms return
the least model (brute force because it scans masks in increasing order, see implementations/brute_force.py), so
outputs are compared with plain ==.

generate(n, rng) mixes, for n >= 3:
  0  random Horn CNF: m = round(c n), c in {0.5, 1, 2, 3, 4}, widths 1..4, a positive literal with probability 0.7;
  1  planted derivation: a random chain of implications from a fact derives k < n variables (each implication
     may carry extra negative literals on already derived variables); goal clauses each mention a variable that
     is not derived, plus noise implications whose head is derived; satisfiable, least model = the derived set;
  2  the same derivation plus one goal clause on derived variables: unsatisfiable, refutation needs the chain;
  3  edge cases: repeated literals, tautologies (NOT x OR x), unit goals, unit facts, and an empty clause in about
     1 formula in 8;
  4  the V2 family H_n below under a random renaming of the variables (unsatisfiable);
  5  definite clauses only (every clause has a head): always satisfiable, often with a large least model.
For n = 0, 1, 2 it returns small random formulas including the empty formula and the empty clause.

check(instance, output) is independent of both implementations. It computes the derived set D by NAIVE forward
chaining (repeated full passes over the clause list until nothing changes: no counters, no occurrence lists, a
different algorithm from the propagation under test: at most n + 1 passes of O(m + L + 1) steps each, and exactly
n passes on the V2 family H_n) and returns
  - for an assignment: True iff no clause is violated by D, the assignment equals the indicator of D, and it
    satisfies every clause. Every variable of D is true in every model (induction over the passes), so a
    satisfying assignment equal to D is the least model;
  - for None: True iff some clause is violated by D (an empty clause, or a goal clause whose variables all lie in
    D). Every model contains D, so that clause is false in every model: a proof of unsatisfiability.
For n <= 10 it also runs an exhaustive search over itertools.product and rejects any verdict that contradicts it.

V2 (measure "reported"): generate_scaling(n, rng) builds the deterministic unsatisfiable family H_n (n >= 3; rng is
not used) from CountingLit literals and resets the counter:
    S_j = (NOT x1 OR NOT x_j OR x_{j+1})   for j = n-1, n-2, ..., 2   (n - 2 clauses, listed in DECREASING j)
    F1 = (x1),  F2 = (NOT x1 OR x2),  G = (NOT x_n)
so m = n + 1 clauses and L = 3n - 2 literals. Unsatisfiable: x1 (F1), x2 (F2), then x3, ..., x_n by S_2, ..., S_{n-1},
contradicting G.
  * Brute force: the 2^(n-1) assignments with x1 false pass all n - 2 clauses S_j with one literal evaluation each
    and fail at F1, so half of the assignments do Theta(n) work: exactly (2n + 13) 2^(n-2) - 2n - 4 literal
    evaluations in total (derivation in entry.json), 6 counted operations each.
  * Unit propagation: the chain is followed through n - 1 firings. Because the S_j are listed in decreasing j,
    naive forward chaining (the oracle's method) needs n full passes on this family, Theta(n^2), while the
    counter-based propagation stays linear.
CountingLit counts every primitive operation applied to an input literal or to a value computed from one
(arithmetic, comparisons, hashing, truth tests, and use as a list index via __index__). The implementations are
unchanged and count nothing themselves.
"""
import itertools


# --------------------------------------------------------------------------
# Instances for V1
# --------------------------------------------------------------------------

def _horn_clause(n, rng, width, p_head=0.7):
    lits = [-rng.randint(1, n) for _ in range(width)]
    if lits and rng.random() < p_head:
        lits[rng.randrange(len(lits))] *= -1
    return tuple(lits)


def _family(n):
    """The V2 family H_n as plain-integer clauses (n >= 3)."""
    star = [(-1, -j, j + 1) for j in range(n - 1, 1, -1)]
    return star + [(1,), (-1, 2), (-n,)]


def _derivation(n, rng):
    """A random derivation chain from one fact: returns (clauses, derived variables, underived variables)."""
    order = rng.sample(range(1, n + 1), n)
    k = rng.randint(1, n - 1)
    derived, rest = order[:k], order[k:]
    clauses = [(derived[0],)]
    for i in range(1, k):
        extra = [-v for v in rng.sample(derived[:i], min(i, rng.randint(0, 2)))]
        cl = [-derived[i - 1]] + extra + [derived[i]]
        rng.shuffle(cl)
        clauses.append(tuple(cl))
    return clauses, derived, rest


def _small(n, rng):
    if n == 0:
        return (0, ()) if rng.random() < 0.5 else (0, ((),))
    clauses = []
    for _ in range(rng.randint(1, 3 * n + 1)):
        width = rng.choice((0, 1, 1, 2, 2, 3)) if rng.random() < 0.25 else rng.choice((1, 2))
        clauses.append(_horn_clause(n, rng, width))
    return n, tuple(clauses)


def generate(n, rng):
    if n < 3:
        return _small(n, rng)
    kind = rng.randrange(6)
    if kind == 0:
        c = rng.choice((0.5, 1.0, 2.0, 3.0, 4.0))
        return n, tuple(_horn_clause(n, rng, rng.randint(1, 4)) for _ in range(round(c * n)))
    if kind in (1, 2):
        clauses, derived, rest = _derivation(n, rng)
        for _ in range(n):                              # goals that mention an underived variable (stay satisfied)
            vs = rng.sample(derived, min(len(derived), rng.randint(0, 2))) + [rng.choice(rest)]
            clauses.append(tuple(-v for v in vs))
        for _ in range(n):                              # noise implications whose head is already derived
            body = rng.sample(range(1, n + 1), rng.randint(1, 3))
            clauses.append(tuple([-v for v in body] + [rng.choice(derived)]))
        if kind == 2:                                   # a goal on derived variables: unsatisfiable
            clauses.append(tuple(-v for v in rng.sample(derived, rng.randint(1, min(3, len(derived))))))
        rng.shuffle(clauses)
        return n, tuple(clauses)
    if kind == 3:
        clauses = []
        for _ in range(2 * n):
            r = rng.random()
            v = rng.randint(1, n)
            if r < 0.15:
                clauses.append((-v,))
            elif r < 0.25:
                clauses.append((-v, -v, rng.randint(1, n)))
            elif r < 0.35:
                clauses.append((-v, v) if rng.random() < 0.5 else (v, -v))
            elif r < 0.45:
                clauses.append((v,))
            else:
                clauses.append(_horn_clause(n, rng, rng.randint(1, 3)))
        if rng.random() < 0.125:
            clauses.insert(rng.randrange(len(clauses) + 1), ())
        return n, tuple(clauses)
    if kind == 4:
        perm = rng.sample(range(1, n + 1), n)
        return n, tuple(tuple((1 if l > 0 else -1) * perm[abs(l) - 1] for l in cl) for cl in _family(n))
    # kind == 5: definite clauses only
    clauses = [(rng.randint(1, n),) for _ in range(rng.randint(1, 2))]
    clauses += [_horn_clause(n, rng, rng.randint(1, 4), p_head=1.0) for _ in range(2 * n)]
    rng.shuffle(clauses)
    return n, tuple(clauses)


# --------------------------------------------------------------------------
# Independent oracle
# --------------------------------------------------------------------------

def _naive_chaining(n, clauses):
    """Derived set by repeated full passes over the clause list (no counters, no occurrence lists)."""
    true = [False] * (n + 1)
    changed = True
    while changed:
        changed = False
        for cl in clauses:
            heads = [l for l in cl if l > 0]
            if heads and all(true[-l] for l in cl if l < 0) and not true[heads[0]]:
                true[heads[0]] = True
                changed = True
    return true


def _satisfies(clauses, values):
    return all(any(values[abs(l)] == (l > 0) for l in cl) for cl in clauses)


def check(instance, output):
    n, clauses = instance
    true = _naive_chaining(n, clauses)
    refuted = any(not any(l > 0 for l in cl) and all(true[-l] for l in cl) for cl in clauses)
    if output is None:
        verdict = refuted
    else:
        if not isinstance(output, tuple) or len(output) != n or not all(isinstance(x, bool) for x in output):
            return False
        verdict = (not refuted) and output == tuple(true[1:]) and _satisfies(clauses, (None,) + output)
    if verdict and n <= 10:                     # exhaustive cross-check of the satisfiability verdict
        sat = any(_satisfies(clauses, (None,) + vals) for vals in itertools.product((False, True), repeat=n))
        if sat == (output is None):
            return False
    return verdict


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
    """The family H_n (deterministic; rng unused) with counting literals; resets the operation counter."""
    global _ops
    if n < 3:
        raise ValueError("the V2 family needs n >= 3")
    clauses = tuple(tuple(CountingLit(l) for l in cl) for cl in _family(n))
    _ops = 0
    return n, clauses


def reported_cost(output):
    """Operations on input-derived values performed since the instance was generated."""
    return _ops
