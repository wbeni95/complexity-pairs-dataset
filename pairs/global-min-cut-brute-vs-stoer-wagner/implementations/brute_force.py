"""Global minimum cut by exhaustive enumeration of all bipartitions.

Input: an n x n symmetric matrix W of non-negative weights with zero diagonal (W[u][v] = weight of edge uv,
0 = no edge). Output: the minimum, over all partitions of the vertices into two non-empty sides, of the total
weight of the edges between the sides. For n < 2 no such partition exists and the function returns None.

Vertex 0 is fixed on side T, so each bipartition {S, T} is enumerated exactly once: S ranges over the
2^(n-1) - 1 non-empty subsets of {1, ..., n-1}. The cut weight of each S is summed edge by edge over S x T.
"""


def min_cut_brute_force(W):
    n = len(W)
    if n < 2:
        return None
    best = None
    for mask in range(1, 1 << (n - 1)):          # bit i set  <=>  vertex i + 1 is in S
        S = [v for v in range(1, n) if (mask >> (v - 1)) & 1]
        T = [0] + [v for v in range(1, n) if not (mask >> (v - 1)) & 1]
        w = 0
        for u in S:
            row = W[u]
            for v in T:
                w = w + row[v]
        if best is None or w < best:
            best = w
    return best
