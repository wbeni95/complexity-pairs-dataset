"""Count the solutions of a linear system over GF(2) (XOR-SAT / #XOR-SAT) by trying all 2^n assignments.

System: (n, rows), each row a tuple of n + 1 bits (a_1, ..., a_n, b) meaning a_1 x_1 XOR ... XOR a_n x_n = b, i.e.
the augmented matrix [A | b] of A x = b over GF(2), given densely.

Every assignment mask = 0, 1, ..., 2^n - 1 is examined (bit j of mask is x_{j+1}); counting cannot stop at the first
solution. For each assignment the rows are checked in order, and the assignment is abandoned at the first violated
row; a row costs n AND and n XOR operations plus one test, whatever its number of non-zero coefficients.
Total O(2^n * m * n); on a system whose rows are linearly independent, an assignment reaches row i with
probability 2^-i, so the cost is (2n + 1)(2^(n+1) - 2) operations for an n x n system of full rank.

Returns (number of solutions, the solution with the smallest mask or None if there is none). The solution is a tuple
of n bits (0/1).
"""


def xor_sat_brute_force(system):
    n, rows = system
    count = 0
    first = None
    for mask in range(1 << n):
        for row in rows:
            s = row[n]                                  # s = b XOR (a . x); the row holds iff s == 0
            for j in range(n):
                s = s ^ (row[j] & ((mask >> j) & 1))
            if s:
                break                                   # row violated: next assignment
        else:
            count += 1
            if first is None:
                first = mask
    witness = None if first is None else tuple((first >> j) & 1 for j in range(n))
    return count, witness
