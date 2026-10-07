"""Interval DP over binary trees by the endpoint rule: Theta(n^2) on every input.

Instance (sense, w) or (p, q) as in recursion.py. REQUIRED precondition: w is monotone under inclusion for
sense "max" (w(b, c) <= w(a, d) whenever a <= b < c <= d), anti-monotone for "min"; for the BST form (p, q) this
holds in particular when p, q >= 0. Only the two endpoint roots k = i+1 and k = j are tried:

    c[i][i] = 0,   c[i][i+1] = w[i][i+1],
    c[i][j] = w[i][j] + opt( c[i][i] + c[i+1][j],  c[i][j-1] + c[j][j] )      (j - i >= 2),

i.e. c[i][j] = w[i][j] + opt(c[i+1][j], c[i][j-1]), opt = max or min.

Correctness (Theorem E' in this entry's README): under the precondition every interval has an optimal root at one
of its two ends, so restricting opt to {i+1, j} does not change its value; an optimal tree can be taken to be a
path. Without the precondition the restriction can be wrong (README: limits and controls).

Work: n(n+1)/2 non-empty intervals with O(1) work each; exactly one comparison of two cost values per interval of
length >= 2, i.e. n(n-1)/2 comparisons on every input.
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


def maxbst_endpoint(instance):
    maximise, n, w = _interval_weights(instance)
    c = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        c[i][i] = 0
    for i in range(n):  # one node: the root is forced
        c[i][i + 1] = w[i][i + 1]
    for length in range(2, n + 1):
        for i in range(0, n - length + 1):
            j = i + length
            best = None
            for k in (i + 1, j):  # only the two endpoint roots
                cand = c[i][k - 1] + c[k][j]
                if best is None or (cand > best if maximise else cand < best):
                    best = cand
            c[i][j] = w[i][j] + best
    return c[0][n]
