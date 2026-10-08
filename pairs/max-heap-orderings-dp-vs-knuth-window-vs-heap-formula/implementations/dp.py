"""Dynamic program over the root split: Theta(N^2) on every input.

Instance (N, one): N >= 0 nodes; one = the number 1 (the hook product of the empty tree) in the integer type used
for the computation. Output: H(N) = min over binary trees T with N nodes of prod_v |T_v|.

A binary tree with d >= 1 nodes is a root with a left subtree of t nodes and a right subtree of d - 1 - t nodes, and
its hook product is d * (left product) * (right product). All factors are positive, so

    H(0) = 1,   H(d) = d * min_{0 <= t <= d-1} H(t) * H(d - 1 - t).

Work: for each d, d candidate products, d - 1 comparisons and one more multiplication, i.e. exactly
N(N+3)/2 multiplications and N(N-1)/2 comparisons of hook-product values on every input (N(N+1) in total).
"""


def min_hook_product_dp(instance):
    n, one = instance
    h = [one] * (n + 1)
    for d in range(1, n + 1):
        best = None
        for t in range(d):
            v = h[t] * h[d - 1 - t]
            if best is None or v < best:
                best = v
        h[d] = d * best
    return h[n]
