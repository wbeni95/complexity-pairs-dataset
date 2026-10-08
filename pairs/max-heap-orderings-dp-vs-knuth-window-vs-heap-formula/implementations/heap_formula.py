"""Hook product of the heap-shaped tree, by memoised recursion: O(log N) multiplications.

Instance (N, one) as in dp.py. The heap-shaped tree with d nodes has the nodes 1..d, node v having the children
2v and 2v + 1 when these are <= d (levels filled from the left). Its root subtrees are again heap-shaped, with
L(d) and d - 1 - L(d) nodes, where for d + 1 = 2^H + e, 0 <= e < 2^H:

    L(d) = 2^(H-1) - 1 + min(e, 2^(H-1)).

So its hook product is P(0) = P(1) = 1, P(d) = d * P(L(d)) * P(d - 1 - L(d)). By Theorem H (PROOFS.md) the heap shape
attains the minimum, so P(N) = H(N).

Work: two multiplications for every distinct argument d >= 2 that the recursion reaches. One of the two root
subtrees is always perfect, so at most 2H - 1 such arguments occur, H = floor(log2(N + 1)): at most 4H - 2
multiplications (PROOFS.md, Lemma C); exactly 4k - 4 for N = 2^k, k >= 2. No comparisons of hook-product values.
"""


def heap_left(d):
    """Number of nodes in the left subtree of the heap-shaped tree with d >= 1 nodes."""
    big_h = (d + 1).bit_length() - 1          # d + 1 = 2^H + e with 0 <= e < 2^H
    e = d + 1 - (1 << big_h)
    half = 1 << (big_h - 1)
    return half - 1 + min(e, half)


def min_hook_product_heap(instance):
    n, one = instance
    memo = {}

    def hook(d):
        if d <= 1:
            return one
        if d not in memo:
            left = heap_left(d)
            memo[d] = d * hook(left) * hook(d - 1 - left)
        return memo[d]

    return hook(n)
