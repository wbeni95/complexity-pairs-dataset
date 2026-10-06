"""Prim, array version: Theta(n^2) on the complete graph, i.e. linear in the n^2 input entries.

Grow one tree from vertex 0. best[v] is the cheapest edge from v to the tree; each of the n-1 rounds
scans all vertices once to pick the closest one (cut property) and once to update best[].
"""


def mst_prim(W) -> int:
    n = len(W)
    if n <= 1:
        return 0
    best = list(W[0])
    in_tree = [False] * n
    in_tree[0] = True
    total = 0
    for _ in range(n - 1):
        u = -1
        for v in range(n):
            if not in_tree[v] and (u < 0 or best[v] < best[u]):
                u = v
        in_tree[u] = True
        total += best[u]
        row = W[u]
        for v in range(n):
            if not in_tree[v] and row[v] < best[v]:
                best[v] = row[v]
    return total
