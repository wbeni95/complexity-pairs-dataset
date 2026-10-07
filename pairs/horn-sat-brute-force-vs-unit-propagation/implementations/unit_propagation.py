"""Decide Horn-SAT in linear time by unit propagation with clause counters (Dowling & Gallier 1984).

Formula: (n, clauses), variables 1..n, each clause a tuple of non-zero integers (DIMACS literals) with at most one
positive literal (a Horn clause). Repeated literals and tautologies (NOT x OR x) are allowed; an empty clause is
unsatisfiable. A clause with a positive literal h and negative literals NOT y_1 .. NOT y_k is the implication
y_1 AND ... AND y_k -> h; a clause without a positive literal is a goal (NOT all of y_1 .. y_k).

Algorithm (one pass to build, one propagation):
  1. For every clause record its head h (the positive literal's variable, 0 if none) and a counter = number of
     negative literal occurrences; for every variable the list of clauses in which it occurs negatively.
     Clauses with counter 0 are facts: an empty clause means UNSAT, otherwise its head goes on the queue.
  2. Pop a variable v from the queue; if it is not yet true, set it true and decrement the counter of every clause
     in which NOT v occurs. A counter that reaches 0 fires its clause: a goal clause means UNSAT, otherwise its head
     goes on the queue.
Every variable is set true at most once, so every negative literal occurrence is decremented at most once, and
every clause fires at most once: O(n + L + 1) time, L = total clause length (Theta(n + L) when no clause is empty;
an empty clause stops the build pass at once).

Correctness (Dowling & Gallier 1984): every variable set true is true in every model (induction on the order in
which variables are set), so a fired goal clause proves unsatisfiability; if propagation ends without that, the
assignment "exactly the derived variables are true" satisfies every clause (a clause with all its negative
variables true has fired and made its head true), and it is the least model.

Returns the least model as a tuple of n booleans, or None if the formula is unsatisfiable.
"""


def horn_sat_unit_propagation(formula):
    n, clauses = formula
    value = [False] * (n + 1)                  # value[v] for v = 1..n (index 0 unused)
    occurs = [[] for _ in range(n + 1)]        # occurs[v] = indices of clauses containing NOT x_v (with multiplicity)
    head = []                                  # head[c] = variable of the positive literal of clause c, or 0
    counter = []                               # counter[c] = negative literal occurrences whose variable is not true
    queue = []
    for c, clause in enumerate(clauses):
        h = 0
        k = 0
        for lit in clause:
            if lit > 0:
                if h != 0 and h != lit:
                    raise ValueError(f"clause {c} has two positive literals: not a Horn formula")
                h = lit
            else:
                occurs[-lit].append(c)
                k += 1
        head.append(h)
        counter.append(k)
        if k == 0:
            if h == 0:
                return None                    # empty clause
            queue.append(h)                    # fact
    while queue:
        v = queue.pop()
        if value[v]:
            continue
        value[v] = True
        for c in occurs[v]:
            counter[c] -= 1
            if counter[c] == 0:
                h = head[c]
                if h == 0:
                    return None                # goal clause with all its variables true
                if not value[h]:
                    queue.append(h)
    return tuple(value[1:])
