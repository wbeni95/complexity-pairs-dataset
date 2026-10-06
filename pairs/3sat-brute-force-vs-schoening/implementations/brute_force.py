"""Decide 3-SAT by trying all 2^n assignments.

Each assignment is evaluated clause by clause and abandoned at the first falsified clause, so one
evaluation costs O(m) clause checks (O(3m) literal checks) in the worst case. On an unsatisfiable formula
all 2^n assignments are examined: O(2^n m) time, Theta(2^n) assignments. On a satisfiable formula the search
stops at the first satisfying assignment in the enumeration order.

Formula: (n, clauses), variables 1..n, each clause a tuple of 1 to 3 non-zero integers (DIMACS literals:
v means x_v, -v means NOT x_v). An empty clause makes the formula unsatisfiable. Returns True iff the
formula is satisfiable.
"""


def sat_brute_force(formula) -> bool:
    n, clauses = formula
    for mask in range(1 << n):                 # bit v-1 of mask is the value of x_v
        for clause in clauses:
            for lit in clause:
                if ((mask >> (abs(lit) - 1)) & 1) == (lit > 0):
                    break                      # literal true: clause satisfied
            else:
                break                          # no true literal: clause falsified, next assignment
        else:
            return True                        # every clause satisfied
    return False
