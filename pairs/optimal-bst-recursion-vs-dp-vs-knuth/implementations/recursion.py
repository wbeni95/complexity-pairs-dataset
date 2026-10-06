"""Optimal binary search tree cost by plain recursion over the root (no memoisation).

Instance (p, q): p = (p_1, ..., p_n) access frequencies of the keys k_1 < ... < k_n, q = (q_0, ..., q_n)
frequencies of the gaps (q_j: searches for values strictly between k_j and k_(j+1)). Both non-negative.
The subproblem (i, j), 0 <= i <= j <= n, holds keys k_(i+1)..k_j and gaps q_i..q_j (Knuth 1971):

    c(i, i) = 0
    c(i, j) = w(i, j) + min over i < k <= j of ( c(i, k-1) + c(k, j) ),
    w(i, j) = q_i + sum_{m=i+1..j} (p_m + q_m).

c(0, n) is the minimum of sum_m p_m (level(k_m) + 1) + sum_j q_j level(gap j), levels counted from the root (0).
Without memoisation the same subproblems are solved again and again: 3^n calls in total (counted in the
experiments), i.e. Theta(3^n).
"""


def obst_recursive(instance):
    p, q = instance
    n = len(p)

    def weight(i, j):
        # p[m - 1] is p_m
        return q[i] + sum(p[m - 1] + q[m] for m in range(i + 1, j + 1))

    def cost(i, j):
        if i == j:
            return 0
        best = None
        for k in range(i + 1, j + 1):  # key k_k is the root
            cand = cost(i, k - 1) + cost(k, j)
            if best is None or cand < best:
                best = cand
        return weight(i, j) + best

    return cost(0, n)
