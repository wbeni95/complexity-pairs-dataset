"""All-pairs shortest paths by the Floyd-Warshall triple loop: Theta(n^3) on every input.

After the k-th outer iteration, D[i][j] is the length of a shortest path from i to j whose
intermediate vertices all lie in {0, ..., k}. The loops have no data-dependent skips, so exactly
n^3 relaxation steps are made on every input.

W is an n x n matrix: W[i][j] is the non-negative integer weight of the edge i -> j, or None if there
is no such edge (the diagonal is ignored). Returns D as in the Bellman-Ford implementation, with None
for unreachable pairs.
"""
INF = float("inf")


def apsp_floyd_warshall(W):
    n = len(W)
    D = [[0 if i == j else (INF if W[i][j] is None else W[i][j]) for j in range(n)] for i in range(n)]
    for k in range(n):
        Dk = D[k]
        for i in range(n):
            Di = D[i]
            dik = Di[k]
            for j in range(n):
                d = dik + Dk[j]
                if d < Di[j]:
                    Di[j] = d
    return tuple(tuple(None if d == INF else d for d in row) for row in D)
