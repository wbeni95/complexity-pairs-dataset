"""Interval DP over binary trees by plain recursion over the root (no memoisation): Theta(3^n).

Instance, in one of two forms:
  (sense, w)   sense is "max" or "min"; w[i][j] is the weight of the interval (i, j), 0 <= i < j <= n
               (n = len(w) - 1; entries with j <= i are unused). Precondition of the problem: w is monotone
               under inclusion for "max" (w(b, c) <= w(a, d) whenever a <= b < c <= d) and anti-monotone for
               "min". This implementation does not use the precondition.
  (p, q)       the maximum-cost BST: key frequencies p = (p_1..p_n), gap frequencies q = (q_0..q_n); it stands
               for sense "max" and w(i, j) = q_i + sum_{l=i+1..j} (p_l + q_l).

The subproblem (i, j) holds the nodes i+1..j:

    c(i, i) = 0,   c(i, j) = w(i, j) + opt over i < k <= j of ( c(i, k-1) + c(k, j) ),   opt = max or min.

c(0, n) is the max (min) over all binary trees with in-order nodes 1..n of the sum, over the nodes v, of the weight
of the interval spanned by v's subtree; for the BST form this is Knuth's cost sum_m p_m (level(k_m) + 1) +
sum_j q_j level(gap j), maximised. Without memoisation the same subproblems are solved again and again: exactly
3^n calls of cost() and (3^(n-1) - 1)/2 comparisons of two cost values for n >= 1, i.e. Theta(3^n).
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


def maxbst_recursive(instance):
    maximise, n, w = _interval_weights(instance)

    def cost(i, j):
        if i == j:
            return 0
        best = None
        for k in range(i + 1, j + 1):  # node k is the root
            cand = cost(i, k - 1) + cost(k, j)
            if best is None or (cand > best if maximise else cand < best):
                best = cand
        return w[i][j] + best

    return cost(0, n)
