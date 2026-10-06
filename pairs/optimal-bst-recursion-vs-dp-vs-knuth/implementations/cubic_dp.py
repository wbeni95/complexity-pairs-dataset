"""Optimal binary search tree cost by the standard interval DP that tries every root: Theta(n^3).

Instance (p, q) as in recursion.py: p = (p_1..p_n), q = (q_0..q_n), non-negative.
c[i][j] (keys k_(i+1)..k_j, gaps q_i..q_j) is filled for increasing length L = j - i:

    c[i][i] = 0,   c[i][j] = w[i][j] + min over i < k <= j of ( c[i][k-1] + c[k][j] ).

Each of the n(n+1)/2 non-empty intervals of length L tries all L roots, so the number of candidate costs
evaluated is sum_L (n - L + 1) L = n(n+1)(n+2)/6 on every input.
"""


def obst_cubic(instance):
    p, q = instance
    n = len(p)
    w = [[None] * (n + 1) for _ in range(n + 1)]
    c = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
        c[i][i] = 0
    for length in range(1, n + 1):
        for i in range(0, n - length + 1):
            j = i + length
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]  # p[j - 1] is p_j
            best = None
            for k in range(i + 1, j + 1):  # every root k_(i+1)..k_j
                cand = c[i][k - 1] + c[k][j]
                if best is None or cand < best:
                    best = cand
            c[i][j] = w[i][j] + best
    return c[0][n]
