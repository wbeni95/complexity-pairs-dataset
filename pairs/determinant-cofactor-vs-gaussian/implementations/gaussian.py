"""Gaussian elimination over GF(P): Theta(n^3) field operations on non-singular input.

Reduce to upper-triangular form with row swaps (each flips the sign) and row operations
row_r -= f * row_c (which leave the determinant unchanged); the determinant is then the signed product
of the pivots. Pivots are inverted with Fermat's little theorem, pow(x, P - 2, P): O(log P) = O(1)
multiplications for the fixed prime P, done n times.
"""

P = 2 ** 31 - 1


def det_gaussian(A) -> int:
    n = len(A)
    M = [[x % P for x in row] for row in A]  # work on a copy
    det = 1
    for c in range(n):
        piv = next((r for r in range(c, n) if M[r][c]), None)
        if piv is None:
            return 0  # no pivot in this column: the matrix is singular
        if piv != c:
            M[c], M[piv] = M[piv], M[c]
            det = -det
        prow = M[c]
        det = det * prow[c] % P
        inv = pow(prow[c], P - 2, P)
        tail = prow[c:]
        for r in range(c + 1, n):
            row = M[r]
            f = row[c] * inv % P
            M[r] = row[:c] + [(x - f * y) % P for x, y in zip(row[c:], tail)]
    return det % P
