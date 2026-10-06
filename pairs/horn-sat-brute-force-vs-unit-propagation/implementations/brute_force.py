"""Decide Horn-SAT by trying all 2^n assignments; return the first satisfying one.

Formula: (n, clauses), variables 1..n, each clause a tuple of non-zero integers (DIMACS literals: v means x_v,
-v means NOT x_v). This code works for any CNF formula; for a Horn formula (at most one positive literal per
clause) its answer is the formula's least model, see below. An empty clause is unsatisfiable.

Assignments are enumerated as integers mask = 0, 1, ..., 2^n - 1 (bit v-1 of mask is the value of x_v). Each one is
checked clause by clause, literal by literal, and abandoned at the first falsified clause. The search STOPS at the
first satisfying assignment. One check costs O(L) literal evaluations (L = total clause length), so the total is
O(2^n * L); on an unsatisfiable formula all 2^n assignments are examined.

Why the first satisfying mask is the least model: the models of a Horn formula are closed under intersection, so
a satisfiable Horn formula has a least model M (its set of true variables is contained in that of every model).
Every model M' contains M bit by bit, hence mask(M') >= mask(M), with equality only for M' = M.

Returns a tuple of n booleans (x_1, ..., x_n), or None if the formula is unsatisfiable.
"""


def horn_sat_brute_force(formula):
    n, clauses = formula
    for mask in range(1 << n):
        for clause in clauses:
            for lit in clause:
                if ((mask >> (abs(lit) - 1)) & 1) == (lit > 0):
                    break                      # literal true: clause satisfied
            else:
                break                          # no true literal: clause falsified, next assignment
        else:
            return tuple(bool((mask >> v) & 1) for v in range(n))
    return None
