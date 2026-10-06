"""Try every set of n-1 edges: C(n(n-1)/2, n-1) subsets, Theta(n) each to test and weigh.

An (n-1)-edge subgraph of an n-vertex graph is a spanning tree iff it is connected, which one
depth-first search from vertex 0 decides in Theta(n) time. Total: Theta(n * C(n(n-1)/2, n-1)).
"""
from itertools import combinations


def mst_brute(W) -> int:
    n = len(W)
    if n <= 1:
        return 0
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
    best = None
    for subset in combinations(edges, n - 1):
        adj = [[] for _ in range(n)]
        total = 0
        for u, v in subset:
            adj[u].append(v)
            adj[v].append(u)
            total += W[u][v]
        seen = [False] * n
        seen[0] = True
        stack = [0]
        reached = 1
        while stack:
            x = stack.pop()
            for y in adj[x]:
                if not seen[y]:
                    seen[y] = True
                    reached += 1
                    stack.append(y)
        if reached == n and (best is None or total < best):
            best = total
    return best
