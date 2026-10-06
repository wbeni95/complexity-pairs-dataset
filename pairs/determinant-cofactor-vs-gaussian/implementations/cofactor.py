"""Laplace (cofactor) expansion along the first remaining row, without memoisation: Theta(n!) time.

det(rows r.., columns S) = sum over the k-th column c of S of (-1)^k * A[r][c] * det(rows r+1.., S - {c}).
A node with k remaining columns does Theta(k^2) work and there are n!/k! such nodes, so the total is
n! * sum_k k^2/k! = Theta(n!). All arithmetic is mod the prime P.
"""

P = 2 ** 31 - 1


def det_cofactor(A) -> int:
    return _expand(A, 0, list(range(len(A))))


def _expand(A, r, cols):
    if r == len(A):
        return 1  # determinant of the empty matrix
    row = A[r]
    total = 0
    for k, c in enumerate(cols):
        term = row[c] * _expand(A, r + 1, cols[:k] + cols[k + 1:]) % P
        total = total - term if k & 1 else total + term
    return total % P
