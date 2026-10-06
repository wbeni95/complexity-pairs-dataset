"""Optimal binary search tree cost with Knuth's speed-up: Theta(n^2) on every input.

Instance (p, q) as in recursion.py: p = (p_1..p_n), q = (q_0..q_n), non-negative.
Same recurrence as the cubic DP, but the root of (i, j) is searched only in r[i][j-1] .. r[i+1][j], the roots
chosen for the two intervals one shorter. With non-negative weights, w(i, j) satisfies the quadrangle inequality
(with equality) and is monotone under interval inclusion, so c does too and the range always contains an
optimal root of (i, j) (Knuth 1971; in the quadrangle-inequality form, Yao 1980).
Ties: '<=' moves to the later root, so r[i][j] is the largest optimal root in the range. (Any choice among the
minimisers in the range would also be correct: see experiments/2026-10-07b_optimal_bst_ties.py.)

Work: for a fixed length L >= 2 the range widths telescope,
    sum_i (r[i+1][i+L] - r[i][i+L-1] + 1) = (n - L + 1) + r[n-L+1][n] - r[0][L-1] <= 2n,
so the total is O(n^2); and there are n(n+1)/2 intervals, so it is also Omega(n^2).
"""


def obst_knuth(instance):
    p, q = instance
    n = len(p)
    w = [[None] * (n + 1) for _ in range(n + 1)]
    c = [[None] * (n + 1) for _ in range(n + 1)]
    r = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
        c[i][i] = 0
    for i in range(n):  # one key: the root is forced
        w[i][i + 1] = w[i][i] + p[i] + q[i + 1]  # p[i] is p_(i+1)
        c[i][i + 1] = w[i][i + 1]
        r[i][i + 1] = i + 1
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
            best, best_k = None, None
            for k in range(r[i][j - 1], r[i + 1][j] + 1):  # Knuth's root range
                cand = c[i][k - 1] + c[k][j]
                if best is None or cand <= best:  # '<=': keep the largest optimal root
                    best, best_k = cand, k
            c[i][j] = w[i][j] + best
            r[i][j] = best_k
    return c[0][n]
