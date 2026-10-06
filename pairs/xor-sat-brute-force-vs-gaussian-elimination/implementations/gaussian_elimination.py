"""Count the solutions of a linear system over GF(2) (XOR-SAT / #XOR-SAT) by Gaussian elimination.

System: (n, rows), each row a tuple of n + 1 bits (a_1, ..., a_n, b), the augmented matrix [A | b] of A x = b over
GF(2), given densely.

1. Forward elimination on a copy of [A | b]: for each column c in order, the first row at or below the current row
   with a 1 in column c becomes the pivot row (swapped up); it is XORed into every row below that has a 1 in
   column c (entries c..n only, the ones to the left are already 0). The number of pivots is r = rank(A).
2. The system is inconsistent iff some row below the pivot rows (all-zero in the A part) has b = 1: then there are
   0 solutions. Otherwise the solution set is a coset of the null space of A, which has dimension n - r, so there
   are exactly 2^(n - r) solutions.
3. One solution by back substitution, with every free (non-pivot) variable set to 0.

Cost: at most min(m, n) pivot steps, each XORing at most m rows of at most n + 1 entries: O(m n min(m, n)) bit
operations, Theta(n^3) for square systems in the worst case. On the V2 family (see harness.py) exactly
n (n^2 + 6n - 4) / 3 operations.

Returns (number of solutions, one solution as a tuple of n bits, or None if there is none).
"""


def xor_sat_gauss(system):
    n, rows = system
    M = [list(row) for row in rows]                     # working copy; the input is not modified
    m = len(M)
    pivots = []                                         # pivot column of each pivot row, in row order
    r = 0
    for c in range(n):
        if r == m:
            break
        p = None
        for i in range(r, m):
            if M[i][c]:
                p = i
                break
        if p is None:
            continue                                    # no pivot in this column: x_{c+1} is free
        M[r], M[p] = M[p], M[r]
        top = M[r]
        for i in range(r + 1, m):
            if M[i][c]:
                row = M[i]
                for j in range(c, n + 1):
                    row[j] = row[j] ^ top[j]
        pivots.append(c)
        r += 1
    for i in range(r, m):                               # rows r..m-1 are zero in the A part
        if M[i][n]:
            return 0, None                              # 0 = 1: inconsistent
    x = [0] * n                                         # free variables stay 0
    for k in range(r - 1, -1, -1):
        c = pivots[k]
        row = M[k]
        s = row[n]
        for j in range(c + 1, n):
            s = s ^ (row[j] & x[j])
        x[c] = s
    return 2 ** (n - r), tuple(x)
