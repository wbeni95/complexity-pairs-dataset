"""Knuth's restricted root window (largest tie rule): Theta(N) on every input.

Instance (N, one) as in dp.py. The run keeps tau(d), the chosen number of nodes left of the root of an optimal tree
with d nodes, and for each d tries only the window

    W(d) = { t : max(tau(d-1), 0) <= t <= min(tau(d-1) + 1, d - 1) },   tau(0) = -1,

taking the LARGEST minimiser in the window as tau(d). For d >= 2 the window has exactly two elements.

Correctness (PROOFS.md, Proposition W): this is the one-dimensional restricted run of the repository note
theorems/knuth-window-concave-length-weights with h(s) = ln s; its Theorem 1 and Remark (i) give exact values and the
trajectory tau(d) = L(d), the left subtree size of the heap-shaped tree.

Work: one candidate for d = 1 and two for every d >= 2, so exactly 3N - 1 multiplications and N - 1 comparisons of
hook-product values for N >= 1 (4N - 2 in total; none for N = 0).
"""


def min_hook_product_window(instance):
    n, one = instance
    h = [one] * (n + 1)
    tau = -1
    for d in range(1, n + 1):
        lo, hi = max(tau, 0), min(tau + 1, d - 1)
        best, best_t = None, None
        for t in range(lo, hi + 1):
            v = h[t] * h[d - 1 - t]
            if best is None or v <= best:      # largest tie rule: a later (larger) t wins ties
                best, best_t = v, t
        h[d] = d * best
        tau = best_t
    return h[n]
