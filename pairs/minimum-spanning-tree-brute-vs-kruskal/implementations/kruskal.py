"""Kruskal with union-find: sort the m = n(n-1)/2 edges of the complete graph; Omega(m log m) in the worst case if
sorted() is a deterministic comparison sort, and O(m log m) = O(n^2 log n) if it runs in O(m log m) time (both are
machine-model assumptions, see entry.json).

Scan edges by increasing weight and keep each edge that joins two different components (cut property).
Union by size keeps every tree of height at most log2 n (path halving only shortens paths), so the find
operations cost O(m log n) in total, which is O(m log m) on K_n (the sort cost: see entry.json).

Each edge (u, v) of weight w is packed into one integer key w*n^2 + u*n + v, so sorting the keys orders
the edges by (w, u, v). This is the same order as sorting (w, u, v) tuples, with one object per edge
instead of four (which matters for memory traffic in CPython, not for the asymptotics).
"""


def mst_kruskal(W) -> int:
    n = len(W)
    nn = n * n
    keys = sorted(W[u][v] * nn + u * n + v for u in range(n) for v in range(u + 1, n))
    parent = list(range(n))
    size = [1] * n

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path halving
            x = parent[x]
        return x

    total = 0
    taken = 0
    for key in keys:
        if taken == n - 1:
            break
        w, rest = divmod(key, nn)
        u, v = divmod(rest, n)
        ru, rv = find(u), find(v)
        if ru != rv:
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
            total += w
            taken += 1
    return total
