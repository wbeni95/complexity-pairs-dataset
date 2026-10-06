"""A mechanical tractability predictor for Boolean constraint languages (Schaefer's dichotomy via polymorphisms).

Schaefer (1978), The complexity of satisfiability problems, STOC, doi:10.1145/800133.804350: for a finite set Gamma
of Boolean relations, CSP(Gamma) is in P if every relation in Gamma is 0-valid, or every one is 1-valid, Horn,
dual-Horn, bijunctive or affine; otherwise CSP(Gamma) is NP-complete. In the algebraic formulation (Jeavons,
Cohen, Gyssens 1997, Closure properties of constraints, J. ACM 44, doi:10.1145/263867.263489; Jeavons 1998,
doi:10.1016/S0304-3975(97)00230-2) the six cases are the polymorphisms: constant 0, constant 1, AND (binary min),
OR (binary max), majority (ternary), minority x XOR y XOR z (ternary). This module

  * classifies a relation (set of 0/1 tuples) by these six polymorphisms (`polymorphism_classes`);
  * cross-checks the classification against the syntactic definitions (Horn / dual-Horn / 2-CNF clause sets,
    GF(2) cosets) by an independent brute-force construction (`syntactic_classes`);
  * solves CSP instances with the polynomial algorithm the predicted class provides (trivial assignment, unit
    propagation, 2-SAT by strongly connected components, Gaussian elimination over GF(2)), and by brute force.
  * counts solutions for affine languages (2^(n - rank)); Creignou & Hermann 1996, doi:10.1006/inco.1996.0016,
    prove that #CSP(Gamma) is in FP iff Gamma is affine, and #P-complete otherwise.

A relation of arity k is a frozenset of k-tuples of 0/1. A constraint is (relation, variables) with distinct
variables. An instance is (n, [constraints]).
"""
from __future__ import annotations

from itertools import combinations, product

CLASSES = ("0-valid", "1-valid", "Horn", "dual-Horn", "bijunctive", "affine")


# --------------------------------------------------------------------------------------------------------------
# Polymorphism tests
# --------------------------------------------------------------------------------------------------------------


def polymorphism_classes(R: frozenset) -> set[str]:
    """Which of Schaefer's six classes contain R, decided by closure under the corresponding polymorphism."""
    if not R:
        return set(CLASSES)  # the empty relation is preserved by every operation
    k = len(next(iter(R)))
    out = set()
    if tuple([0] * k) in R:
        out.add("0-valid")
    if tuple([1] * k) in R:
        out.add("1-valid")
    T = list(R)
    if all(tuple(a & b for a, b in zip(s, t)) in R for s in T for t in T):
        out.add("Horn")
    if all(tuple(a | b for a, b in zip(s, t)) in R for s in T for t in T):
        out.add("dual-Horn")
    if all(tuple((a & b) | (a & c) | (b & c) for a, b, c in zip(s, t, u)) in R for s in T for t in T for u in T):
        out.add("bijunctive")
    if all(tuple(a ^ b ^ c for a, b, c in zip(s, t, u)) in R for s in T for t in T for u in T):
        out.add("affine")
    return out


def language_classes(gamma: list[frozenset]) -> set[str]:
    out = set(CLASSES)
    for R in gamma:
        out &= polymorphism_classes(R)
    return out


def predict(gamma: list[frozenset]) -> str:
    """'P (<classes>)' or 'NP-complete' by Schaefer's theorem."""
    cls = language_classes(gamma)
    return f"P ({', '.join(c for c in CLASSES if c in cls)})" if cls else "NP-complete"


# --------------------------------------------------------------------------------------------------------------
# Syntactic definitions (independent cross-check)
# --------------------------------------------------------------------------------------------------------------


def _clauses(k: int, max_width: int):
    """All clauses over variables 0..k-1 with <= max_width literals: tuples of (var, sign) with sign 1 = positive."""
    for w in range(1, max_width + 1):
        for vs in combinations(range(k), w):
            for signs in product((0, 1), repeat=w):
                yield tuple(zip(vs, signs))


def _sat(clause, t) -> bool:
    return any(t[v] == s for v, s in clause)


def implied_clauses(R: frozenset, k: int, kind: str) -> list[tuple]:
    """All clauses of the given kind satisfied by every tuple of R. kind: 'horn' (<= 1 positive literal),
    'dual-horn' (<= 1 negative literal), '2cnf' (width <= 2)."""
    width = 2 if kind == "2cnf" else k
    out = []
    for cl in _clauses(k, width):
        pos = sum(s for _, s in cl)
        neg = len(cl) - pos
        if kind == "horn" and pos > 1 or kind == "dual-horn" and neg > 1:
            continue
        if all(_sat(cl, t) for t in R):
            out.append(cl)
    return out


def _solutions(clauses, k) -> frozenset:
    return frozenset(t for t in product((0, 1), repeat=k) if all(_sat(c, t) for c in clauses))


def is_coset(R: frozenset) -> bool:
    if not R:
        return True
    r0 = next(iter(R))
    S = {tuple(a ^ b for a, b in zip(r, r0)) for r in R}
    return all(tuple(a ^ b for a, b in zip(s, t)) in S for s in S for t in S)


def syntactic_classes(R: frozenset, k: int) -> set[str]:
    out = set()
    if not R:
        return set(CLASSES)
    if tuple([0] * k) in R:
        out.add("0-valid")
    if tuple([1] * k) in R:
        out.add("1-valid")
    if _solutions(implied_clauses(R, k, "horn"), k) == R:
        out.add("Horn")
    if _solutions(implied_clauses(R, k, "dual-horn"), k) == R:
        out.add("dual-Horn")
    if _solutions(implied_clauses(R, k, "2cnf"), k) == R:
        out.add("bijunctive")
    if is_coset(R):
        out.add("affine")
    return out


def all_relations(k: int) -> list[frozenset]:
    tuples = list(product((0, 1), repeat=k))
    return [frozenset(t for i, t in enumerate(tuples) if code >> i & 1) for code in range(1 << len(tuples))]


# --------------------------------------------------------------------------------------------------------------
# Solvers
# --------------------------------------------------------------------------------------------------------------


def satisfies(inst, assign) -> bool:
    n, cons = inst
    return all(tuple(assign[v] for v in vs) in R for R, vs in cons)


def brute_force(inst):
    """(satisfiable?, a witness or None, number of solutions)."""
    n, cons = inst
    count, wit = 0, None
    for code in range(1 << n):
        a = [(code >> i) & 1 for i in range(n)]
        if satisfies(inst, a):
            count += 1
            if wit is None:
                wit = a
    return wit is not None, wit, count


def _to_global_clauses(inst, kind):
    n, cons = inst
    out = []
    for R, vs in cons:
        k = len(vs)
        if not R:
            return None  # unsatisfiable constraint
        for cl in implied_clauses(R, k, kind):
            out.append(tuple((vs[v], s) for v, s in cl))
    return out


def solve_horn(inst, dual: bool = False):
    """Unit propagation to the minimal model (Dowling & Gallier 1984, doi:10.1016/0743-1066(84)90014-1)."""
    n, cons = inst
    clauses = _to_global_clauses(inst, "dual-horn" if dual else "horn")
    if clauses is None:
        return False, None
    if dual:  # flip all literals: dual-Horn becomes Horn
        clauses = [tuple((v, 1 - s) for v, s in cl) for cl in clauses]
    val = [0] * n
    changed = True
    while changed:
        changed = False
        for cl in clauses:
            if _sat(cl, val):
                continue
            heads = [v for v, s in cl if s == 1]
            if not heads:
                return False, None
            val[heads[0]] = 1  # the body (negative literals) is all true, so the head is forced
            changed = True
    if dual:
        val = [1 - x for x in val]
    return True, val


def solve_2sat(inst):
    """Implication graph + Kosaraju SCC (Aspvall, Plass, Tarjan 1979, doi:10.1016/0020-0190(79)90002-4)."""
    n, cons = inst
    clauses = _to_global_clauses(inst, "2cnf")
    if clauses is None:
        return False, None
    lit = lambda v, s: 2 * v + (1 - s)  # node 2v = x_v true, 2v+1 = x_v false  # noqa: E731
    g = [[] for _ in range(2 * n)]
    for cl in clauses:
        if len(cl) == 1:
            (v, s), = cl
            g[lit(v, 1 - s)].append(lit(v, s))
        else:
            (a, sa), (b, sb) = cl
            g[lit(a, 1 - sa)].append(lit(b, sb))
            g[lit(b, 1 - sb)].append(lit(a, sa))
    order, seen = [], [False] * (2 * n)
    for s in range(2 * n):
        if seen[s]:
            continue
        stack = [(s, 0)]
        seen[s] = True
        while stack:
            u, i = stack.pop()
            if i < len(g[u]):
                stack.append((u, i + 1))
                w = g[u][i]
                if not seen[w]:
                    seen[w] = True
                    stack.append((w, 0))
            else:
                order.append(u)
    rg = [[] for _ in range(2 * n)]
    for u in range(2 * n):
        for w in g[u]:
            rg[w].append(u)
    comp, c = [-1] * (2 * n), 0
    for s in reversed(order):
        if comp[s] != -1:
            continue
        stack = [s]
        comp[s] = c
        while stack:
            u = stack.pop()
            for w in rg[u]:
                if comp[w] == -1:
                    comp[w] = c
                    stack.append(w)
        c += 1
    if any(comp[2 * v] == comp[2 * v + 1] for v in range(n)):
        return False, None
    # Kosaraju numbers components in topological order of the condensation; pick the later one as true
    return True, [1 if comp[2 * v] > comp[2 * v + 1] else 0 for v in range(n)]


def affine_equations(R: frozenset, k: int):
    """R (a nonempty coset) as GF(2) equations: list of (mask, rhs) with parity(mask & x) == rhs."""
    r0 = next(iter(R))
    eqs = []
    for mask in range(1, 1 << k):
        par = {sum((t[i] for i in range(k) if mask >> i & 1)) % 2 for t in R}
        if len(par) == 1:
            eqs.append((mask, par.pop()))
    return eqs


def solve_affine(inst):
    """Gaussian elimination over GF(2): (satisfiable?, witness, number of solutions = 2^(n - rank))."""
    n, cons = inst
    rows = []
    for R, vs in cons:
        if not R:
            return False, None, 0
        for mask, rhs in affine_equations(R, len(vs)):
            gm = 0
            for i, v in enumerate(vs):
                if mask >> i & 1:
                    gm ^= 1 << v
            rows.append([gm, rhs])
    piv_rows, rank = [], 0
    for r in rows:
        m, b = r
        for pm, pb, pc in piv_rows:
            if m >> pc & 1:
                m ^= pm
                b ^= pb
        if m == 0:
            if b:
                return False, None, 0
            continue
        pc = m.bit_length() - 1
        new = []
        for pm, pb, c in piv_rows:  # keep rows reduced in the new pivot column
            if pm >> pc & 1:
                pm ^= m
                pb ^= b
            new.append((pm, pb, c))
        piv_rows = new + [(m, b, pc)]
        rank += 1
    x = [0] * n
    for pm, pb, pc in piv_rows:  # free variables = 0; each pivot row has exactly its pivot among pivot columns
        x[pc] = pb
    return True, x, 2 ** (n - rank)


def solve_by_class(inst, cls: str):
    n, cons = inst
    if cls == "0-valid":
        a = [0] * n
        return satisfies(inst, a), a
    if cls == "1-valid":
        a = [1] * n
        return satisfies(inst, a), a
    if cls == "Horn":
        return solve_horn(inst)
    if cls == "dual-Horn":
        return solve_horn(inst, dual=True)
    if cls == "bijunctive":
        return solve_2sat(inst)
    if cls == "affine":
        s, w, _ = solve_affine(inst)
        return s, w
    raise ValueError(cls)


def random_instance(gamma: list[frozenset], n: int, m: int, rng):
    cons = []
    for _ in range(m):
        R = rng.choice(gamma)
        k = len(next(iter(R))) if R else 2
        cons.append((R, tuple(rng.sample(range(n), k))))
    return n, cons
