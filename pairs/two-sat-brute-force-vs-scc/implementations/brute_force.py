"""Decide 2-SAT by trying all 2^n assignments (and return the first satisfying one).

Formula: (n, clauses), variables 1..n, each clause a tuple of 0, 1 or 2 non-zero integers (DIMACS literals:
v means x_v, -v means NOT x_v). An empty clause is unsatisfiable.

Assignments are enumerated as integers mask = 0, 1, ..., 2^n - 1 (bit v-1 of mask is the value of x_v). Each one is
checked clause by clause, literal by literal, and abandoned at the first falsified clause. One check costs at most 2m
literal evaluations and O(m + 1) steps, so the total is O(2^n * (m + 1)). On an unsatisfiable formula all 2^n
assignments are examined.

Returns a tuple of n booleans (x_1, ..., x_n) satisfying every clause, or None if there is none.
"""


def two_sat_brute_force(formula):
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
