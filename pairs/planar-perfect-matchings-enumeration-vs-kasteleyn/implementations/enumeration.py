"""Weighted perfect matchings of an a x b grid graph by backtracking enumeration.

Instance (a, b, W): vertex u = r*b + c for 0 <= r < a, 0 <= c < b; W is the N x N symmetric weight matrix
(N = a*b), non-zero only on grid edges, weight 0 meaning "edge absent". The answer is the sum, over all
perfect matchings M (every vertex covered exactly once), of the product of the weights of M's edges.

Backtracking: take the first unmatched vertex u in index order. Every vertex before u is already matched,
so u can only be matched to its right neighbour u + 1 or its lower neighbour u + b. Try each of them that is
unmatched and has non-zero weight, recurse, and add up weight * (sum over completions). Each perfect
matching is reached along exactly one path (the partner of the first unmatched vertex is decided at each
step), so every matching is counted once. N = 0 gives the empty matching (answer 1); odd N gives 0.

Cost: every node of the search tree except the root costs one multiplication weight * subtotal. The tree
has branching factor <= 2 and depth <= N/2, so O(2^(N/2)) nodes and O(N 2^(N/2)) time (the scan for the
next unmatched vertex moves forward only along a root-to-leaf path). Every perfect matching is a leaf, so
the time is also at least the number of perfect matchings, which is exponential in N on full grids.
"""


def count_perfect_matchings_enumeration(instance):
    a, b, W = instance
    N = a * b
    matched = [False] * N

    def extend(start):
        u = start
        while u < N and matched[u]:
            u += 1
        if u == N:
            return 1  # every vertex is matched: one complete matching (empty product)
        r, c = divmod(u, b)
        partners = []
        if c + 1 < b:
            partners.append(u + 1)  # right neighbour
        if r + 1 < a:
            partners.append(u + b)  # lower neighbour
        total = 0
        matched[u] = True
        for v in partners:
            if not matched[v] and W[u][v]:
                matched[v] = True
                total = total + W[u][v] * extend(u + 1)
                matched[v] = False
        matched[u] = False
        return total

    return extend(0)
