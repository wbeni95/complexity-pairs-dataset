"""Count spanning trees with Kirchhoff's matrix-tree theorem and Bareiss's fraction-free elimination.

tau(G) = det(L0), where L0 is the Laplacian L = D - A with the row and column of the last vertex deleted
(an (n-1) x (n-1) integer matrix; the 0 x 0 determinant, n = 1, is 1).

Bareiss (1968): for k = 0..N-2, every entry below and right of the pivot becomes
    M[i][j] = (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev,      prev = previous pivot (1 at k = 0).
By Sylvester's identity each new entry is a (k+2) x (k+2) minor of the (row-permuted) input, so the
division is exact and every value stays an integer. The determinant is the last diagonal entry, times -1
per row swap. A zero pivot is replaced by a lower row with a non-zero entry in that column; if there is
none, the column below the leading block is zero and det = 0.

Cost: exactly 3 * sum_{t=1}^{N-1} t^2 = (N-1)N(2N-1)/2 multiplications and exact divisions when no pivot
is zero (N = n-1), i.e. Theta(n^3) arithmetic operations on integers of O(n log n) bits.
"""


def _bareiss_det(M) -> int:
    """Determinant of a square integer matrix (list of lists, modified in place)."""
    N = len(M)
    if N == 0:
        return 1
    sign = 1
    prev = 1
    for k in range(N - 1):
        if M[k][k] == 0:
            swap = next((r for r in range(k + 1, N) if M[r][k] != 0), None)
            if swap is None:
                return 0
            M[k], M[swap] = M[swap], M[k]
            sign = -sign
        pivot = M[k][k]
        row_k = M[k]
        for i in range(k + 1, N):
            row_i = M[i]
            a = row_i[k]
            for j in range(k + 1, N):
                row_i[j] = (row_i[j] * pivot - a * row_k[j]) // prev
        prev = pivot
    det = M[N - 1][N - 1]
    return det if sign > 0 else -det


def count_spanning_trees_kirchhoff(A) -> int:
    n = len(A)
    N = n - 1  # delete the last vertex's row and column
    L0 = [[sum(A[i]) if i == j else -A[i][j] for j in range(N)] for i in range(N)]
    return _bareiss_det(L0)
