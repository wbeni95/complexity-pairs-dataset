"""All-pairs shortest paths by running Bellman-Ford from every source.

W is an n x n matrix: W[i][j] is the non-negative integer weight of the edge i -> j, or None if there
is no such edge (the diagonal is ignored). The m edges are listed once (Theta(n^2)). Each of the n
single-source runs then makes exactly n - 1 passes over all m edges, with no early exit, so the
running time is Theta(n^2 m) on every input with m >= 1 edges: Theta(n^4) on dense digraphs
(m = n(n-1) on the complete digraphs used for timing).

Returns D with D[i][j] = length of a shortest directed path from i to j (D[i][i] = 0), or None if j is
unreachable from i.
"""
INF = float("inf")


def apsp_bellman_ford(W):
    n = len(W)
    edges = [(u, v, W[u][v]) for u in range(n) for v in range(n) if u != v and W[u][v] is not None]
    rows = []
    for s in range(n):
        dist = [INF] * n
        dist[s] = 0
        for _ in range(n - 1):              # n - 1 passes suffice: a shortest path has <= n - 1 edges
            for u, v, w in edges:
                d = dist[u] + w
                if d < dist[v]:
                    dist[v] = d
        rows.append(tuple(None if d == INF else d for d in dist))
    return tuple(rows)
