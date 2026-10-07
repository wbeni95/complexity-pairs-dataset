"""Interval DP over binary trees that tries every root: Theta(n^3).

Instance (sense, w) or (p, q) as in recursion.py. c[i][j] (nodes i+1..j) is filled for increasing length
L = j - i:

    c[i][i] = 0,   c[i][j] = w[i][j] + opt over i < k <= j of ( c[i][k-1] + c[k][j] ),   opt = max or min.

Correct for any weights (the precondition of the problem is not used). An interval of length L tries all L roots
and makes L - 1 comparisons of two cost values, so the total is sum_{L=1..n} (n - L + 1)(L - 1) = (n+1) n (n-1) / 6
comparisons on every input.
"""


def _interval_weights(instance):
    """(maximise, n, w) with w[i][j] the weight of the interval (i, j), 0 <= i < j <= n."""
    first, second = instance
    if isinstance(first, str):  # explicit form (sense, w)
        return first == "max", len(second) - 1, second
    p, q = first, second  # BST form; p[l - 1] is p_l
    n = len(p)
    w = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        acc = q[i]
        for j in range(i + 1, n + 1):
            acc = acc + p[j - 1] + q[j]
            w[i][j] = acc
    return True, n, w


def maxbst_cubic(instance):
    maximise, n, w = _interval_weights(instance)
    c = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        c[i][i] = 0
    for length in range(1, n + 1):
        for i in range(0, n - length + 1):
            j = i + length
            best = None
            for k in range(i + 1, j + 1):  # every root i+1..j
                cand = c[i][k - 1] + c[k][j]
                if best is None or (cand > best if maximise else cand < best):
                    best = cand
            c[i][j] = w[i][j] + best
    return c[0][n]
