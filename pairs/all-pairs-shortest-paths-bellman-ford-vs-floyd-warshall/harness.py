"""Instances: n x n weight matrices (tuples of tuples) of a digraph with non-negative integer weights.

W[i][j] is the weight of the edge i -> j or None if absent; the diagonal is 0. generate() varies the edge
density (0.1, 0.3, 0.6 or 1.0) and draws weights from [0, 20], so instances contain zero-weight edges,
ties between paths and unreachable pairs. generate_scaling() returns complete digraphs (m = n(n-1)) with
weights in [1, 1000], where Bellman-Ford's n(n-1) passes over m edges cost n^2 (n-1)^2 relaxations.

The oracle runs Dijkstra's algorithm with a binary heap from every source: a different algorithm from
both implementations under test (valid because weights are non-negative).
"""
import heapq


def _matrix(n, rng, density, wmax):
    return tuple(
        tuple(0 if i == j else (rng.randint(0, wmax) if rng.random() < density else None) for j in range(n))
        for i in range(n)
    )


def generate(n, rng):
    density = rng.choice((0.1, 0.3, 0.6, 1.0))
    return _matrix(n, rng, density, 20)


def generate_scaling(n, rng):
    return tuple(tuple(0 if i == j else rng.randint(1, 1000) for j in range(n)) for i in range(n))


def _dijkstra_all(W):
    n = len(W)
    adj = [[(v, W[u][v]) for v in range(n) if v != u and W[u][v] is not None] for u in range(n)]
    out = []
    for s in range(n):
        dist = [None] * n
        heap = [(0, s)]
        while heap:
            d, u = heapq.heappop(heap)
            if dist[u] is not None:
                continue
            dist[u] = d
            for v, w in adj[u]:
                if dist[v] is None:
                    heapq.heappush(heap, (d + w, v))
        out.append(tuple(dist))
    return tuple(out)


def check(W, output):
    return output == _dijkstra_all(W)
