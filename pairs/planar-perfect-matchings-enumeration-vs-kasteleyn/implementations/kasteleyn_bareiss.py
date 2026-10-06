"""Weighted perfect matchings of an a x b grid graph via a Kasteleyn matrix and Bareiss's determinant.

Instance (a, b, W): vertex u = r*b + c; W is the N x N symmetric weight matrix (N = a*b), non-zero only on
grid edges. The answer is the sum over perfect matchings of the product of their edge weights.

Kasteleyn matrix. Colour vertex (r, c) black if r + c is even, white otherwise; every grid edge joins a black
and a white vertex. If N is odd the colour classes differ in size (black has one more vertex) and there is
no perfect matching: the answer is 0. Otherwise both classes have N/2 vertices, listed in index order, and
    K[i][j] = -W[x][y]  if black x and white y are vertically adjacent in an odd column c,
    K[i][j] =  W[x][y]  otherwise                         (x = i-th black, y = j-th white),
i.e. horizontal edges carry sign +1 and the vertical edge (r, c)-(r+1, c) carries sign (-1)^c. Every unit
square then has two horizontal edges (+1, +1) and vertical edges in columns c and c+1 (signs (-1)^c and
(-1)^(c+1)), so its sign product is -1. This makes every term of det K that belongs to a perfect matching
carry the same sign (Kasteleyn's theorem for planar bipartite graphs; proof sketch in entry.json), and with
non-negative weights |det K| is the weighted number of perfect matchings. Zero weights only remove terms,
so every spanning subgraph of the grid is handled with the signs of the full rectangle. All entries of K
come from W (non-neighbours give W[x][y] = 0), so K is built without arithmetic beyond negation.

Determinant: Bareiss (1968) fraction-free elimination; for k = 0..m-2 every entry below and right of the
pivot becomes (M[i][j] * M[k][k] - M[i][k] * M[k][j]) // prev with prev the previous pivot (1 at k = 0).
By Sylvester's identity each value is a minor of the (row-permuted) matrix, so the division is exact. A zero
pivot is replaced by a lower row with a non-zero entry in that column (one sign change, which the absolute
value discards anyway); if there is none, det = 0.

Cost: exactly 3 * sum_{t=1}^{m-1} t^2 = (m-1) m (2m-1) / 2 multiplications and exact divisions when the
determinant is non-zero (m = N/2), whatever pivots are swapped; i.e. Theta(N^3) arithmetic operations.
"""


def _bareiss_det(M):
    """Determinant of a square integer matrix (list of lists, modified in place)."""
    m = len(M)
    if m == 0:
        return 1
    sign = 1
    prev = 1
    for k in range(m - 1):
        if M[k][k] == 0:
            swap = next((r for r in range(k + 1, m) if M[r][k] != 0), None)
            if swap is None:
                return 0
            M[k], M[swap] = M[swap], M[k]
            sign = -sign
        pivot = M[k][k]
        row_k = M[k]
        for i in range(k + 1, m):
            row_i = M[i]
            f = row_i[k]
            for j in range(k + 1, m):
                row_i[j] = (row_i[j] * pivot - f * row_k[j]) // prev
        prev = pivot
    det = M[m - 1][m - 1]
    return det if sign > 0 else -det


def count_perfect_matchings_kasteleyn(instance):
    a, b, W = instance
    N = a * b
    if N == 0:
        return 1  # the empty matching
    if N % 2 == 1:
        return 0  # colour classes of different sizes
    black = [u for u in range(N) if (u // b + u % b) % 2 == 0]
    white = [u for u in range(N) if (u // b + u % b) % 2 == 1]
    K = []
    for x in black:
        rx, cx = divmod(x, b)
        row = []
        for y in white:
            ry, cy = divmod(y, b)
            if cx == cy and abs(rx - ry) == 1 and cx % 2 == 1:
                row.append(-W[x][y])  # vertical edge in an odd column: sign -1
            else:
                row.append(W[x][y])
        K.append(row)
    return abs(_bareiss_det(K))
