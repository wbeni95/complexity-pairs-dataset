"""Ryser's formula with Gray-code ordering: Theta(n 2^n) arithmetic operations.

    perm(A) = (-1)^n * sum over column subsets S of (-1)^|S| * prod_i (sum_{j in S} A[i][j])

by inclusion-exclusion over the columns each row is allowed to use. Visiting the subsets in Gray-code
order changes S by one column per step, so the n row sums are updated in Theta(n) instead of being
recomputed in Theta(n^2); the product of the row sums costs another Theta(n). 2^n - 1 non-empty subsets
(the empty one contributes 0 for n >= 1).
"""


def permanent_ryser(A) -> int:
    n = len(A)
    if n == 0:
        return 1  # the empty permutation
    cols = list(zip(*A))
    rowsum = [0] * n
    size = 0      # |S|
    gray = 0      # bitmask of S
    total = 0
    for k in range(1, 1 << n):
        j = (k & -k).bit_length() - 1  # Gray codes of k-1 and k differ exactly in bit j
        gray ^= 1 << j
        col = cols[j]
        if gray >> j & 1:
            size += 1
            for i in range(n):
                rowsum[i] += col[i]
        else:
            size -= 1
            for i in range(n):
                rowsum[i] -= col[i]
        prod = 1
        for s in rowsum:
            prod *= s
        total += -prod if size & 1 else prod
    return -total if n & 1 else total
