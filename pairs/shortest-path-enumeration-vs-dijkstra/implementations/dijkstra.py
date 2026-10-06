"""Dijkstra's algorithm, array version as in Dijkstra (1959): Theta(n^2) on an n x n weight matrix.

Settles all n vertices (no early exit at the target), so the running time does not depend on
where the target happens to fall in the settling order.
"""
import math


def shortest_path_dijkstra(W) -> int:
    n = len(W)
    dist = [math.inf] * n
    dist[0] = 0
    done = [False] * n
    for _ in range(n):
        u = min((d, v) for v, d in enumerate(dist) if not done[v])[1]
        done[u] = True
        row = W[u]
        for v in range(n):
            if not done[v] and dist[u] + row[v] < dist[v]:
                dist[v] = dist[u] + row[v]
    return dist[n - 1]
