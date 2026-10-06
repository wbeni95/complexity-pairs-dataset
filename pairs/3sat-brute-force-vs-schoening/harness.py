"""Instances: CNF formulas (n, clauses) over variables 1..n with clauses of 1 to 3 literals (DIMACS style).

generate() mixes: random 3-CNF with m = round(c n) clauses for c in {2, 4.26, 6} (both answers occur);
planted satisfiable 3-CNF (a hidden assignment a*; clauses drawn uniformly among those a* satisfies,
m = round(5 n)); unsatisfiable formulas (random 3-CNF with m = round(3 n) plus all 8 sign patterns on one
random variable triple, shuffled); and mixed-width formulas with 1-, 2- and 3-literal clauses. Very small
n give the edge cases (n = 0: no clauses or one empty clause).

generate_scaling() returns unsatisfiable formulas: random 3-CNF with m = round(5 n) clauses plus the 8
clauses on variables (1, 2, 3), shuffled. Every assignment falsifies exactly one of those 8 clauses, so the
formula is unsatisfiable by construction (no solver is needed to know it). Brute force must then examine
all 2^n assignments and Schöning's walk uses its whole restart budget.

The oracle is a small DPLL solver (unit propagation + branching): a third, independent algorithm.
"""


def _random_clause(n, rng, width=3):
    vs = rng.sample(range(1, n + 1), width)
    return tuple(v if rng.random() < 0.5 else -v for v in vs)


def _forcing_triple(vs):
    a, b, c = vs
    return [(sa * a, sb * b, sc * c) for sa in (1, -1) for sb in (1, -1) for sc in (1, -1)]


def generate(n, rng):
    if n == 0:
        return (0, ()) if rng.random() < 0.5 else (0, ((),))
    if n < 3:
        width = n
        m = rng.randint(1, 4 * n)
        return n, tuple(_random_clause(n, rng, rng.randint(1, width)) for _ in range(m))
    kind = rng.randrange(5)
    if kind == 0:
        c = rng.choice((2, 4.26, 6))
        return n, tuple(_random_clause(n, rng) for _ in range(round(c * n)))
    if kind == 1:
        star = {v: rng.random() < 0.5 for v in range(1, n + 1)}
        clauses = []
        while len(clauses) < round(5 * n):
            cl = _random_clause(n, rng)
            if any(star[abs(l)] == (l > 0) for l in cl):
                clauses.append(cl)
        return n, tuple(clauses)
    if kind == 2:
        clauses = [_random_clause(n, rng) for _ in range(round(3 * n))] + _forcing_triple(rng.sample(range(1, n + 1), 3))
        rng.shuffle(clauses)
        return n, tuple(clauses)
    if kind == 3:
        return n, tuple(_random_clause(n, rng, rng.choice((1, 2, 3, 3))) for _ in range(round(3 * n)))
    return n, tuple(_random_clause(n, rng) for _ in range(round(4.26 * n)))


def generate_scaling(n, rng):
    clauses = [_random_clause(n, rng) for _ in range(round(5 * n))] + _forcing_triple((1, 2, 3))
    rng.shuffle(clauses)
    return n, tuple(clauses)


def _dpll(clauses, assignment):
    clauses = list(clauses)
    while True:                                   # unit propagation
        simplified = []
        unit = None
        for cl in clauses:
            if any(assignment.get(abs(l)) == (l > 0) for l in cl):
                continue                          # satisfied
            rest = tuple(l for l in cl if abs(l) not in assignment)
            if not rest:
                return False                      # falsified
            if len(rest) == 1 and unit is None:
                unit = rest[0]
            simplified.append(rest)
        if unit is None:
            break
        assignment = {**assignment, abs(unit): unit > 0}
        clauses = simplified
    if not simplified:
        return True
    v = abs(simplified[0][0])
    return (_dpll(simplified, {**assignment, v: True})
            or _dpll(simplified, {**assignment, v: False}))


def check(formula, output):
    n, clauses = formula
    return output == _dpll(clauses, {})
