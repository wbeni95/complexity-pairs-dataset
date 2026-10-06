"""Enumerate every simple path from vertex 0 to vertex n-1 by depth-first search; keep the cheapest.

On the complete digraph there are sum_k (n-2)!/(n-2-k)! ~ e (n-2)! simple 0 -> n-1 paths, and each
search node scans n neighbours: Theta(n (n-2)!) time.
"""
import math


def shortest_path_enumerate(W) -> int:
    n = len(W)
    target = n - 1
    best = math.inf
    visited = [False] * n
    visited[0] = True

    def dfs(u, cost):
        nonlocal best
        if u == target:
            best = min(best, cost)
            return
        for v in range(n):
            if not visited[v]:
                visited[v] = True
                dfs(v, cost + W[u][v])
                visited[v] = False

    dfs(0, 0)
    return best
