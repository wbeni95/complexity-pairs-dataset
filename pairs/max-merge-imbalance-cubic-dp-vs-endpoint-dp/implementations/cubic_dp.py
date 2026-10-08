"""Worst-case total imbalance of merging adjacent piles (merge cost |L - R|): the interval DP over every split,
Theta(n^3).

Instance: a tuple of n + 1 non-negative numbers s_0..s_n, the pile sizes in their row order (n >= 0). A merge joins
two adjacent piles of sizes L (left) and R (right) into one pile of size L + R and costs |L - R|. The answer is the
largest total cost of the n merges over all merge orders.

With S(x, y) = s_x + ... + s_y, the subproblem (i, j) is the row of piles i..j, and a split k (i < k <= j) means
that its last merge joins the blocks i..k-1 and k..j:

    c(i, i) = 0,   c(i, j) = max over i < k <= j of ( |S(i, k-1) - S(k, j)| + c(i, k-1) + c(k, j) ).

Correct for any sizes. Work: the row (i, j) of length L = j - i tries L splits; each split costs one comparison
inside merge_cost and every split after the first one more comparison of two candidate values. Over all rows that is
n(n+1)(n+2)/6 merge-cost comparisons plus (n+1)n(n-1)/6 candidate comparisons, n(n+1)(2n+1)/6 comparisons in all,
on every input.
"""


def merge_cost(left, right):
    """Cost of merging two adjacent blocks of sizes left and right: |left - right| (one comparison)."""
    return left - right if left >= right else right - left


def merge_max_imbalance_cubic(sizes):
    n = len(sizes) - 1
    prefix = [0]  # prefix[t] = s_0 + ... + s_(t-1)
    for s in sizes:
        prefix.append(prefix[-1] + s)
    c = [[0] * (n + 1) for _ in range(n + 1)]
    for length in range(1, n + 1):
        for i in range(n - length + 1):
            j = i + length
            best = None
            for k in range(i + 1, j + 1):  # every split
                cand = merge_cost(prefix[k] - prefix[i], prefix[j + 1] - prefix[k]) + c[i][k - 1] + c[k][j]
                if best is None or cand > best:
                    best = cand
            c[i][j] = best
    return c[0][n]
