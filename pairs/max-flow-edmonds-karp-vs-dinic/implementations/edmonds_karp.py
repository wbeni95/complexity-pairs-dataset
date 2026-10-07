"""Maximum flow by Edmonds-Karp: Ford-Fulkerson with shortest (fewest-edge) augmenting paths found by BFS.

Each augmentation is one BFS over the residual graph, O(V + E). The residual distance from s to every
vertex never decreases, and each arc can be the bottleneck of an augmenting path at most O(V) times, so there
are O(V E) augmentations: O(V E^2) time in total (independent of the capacity values; proofs in PROOFS.md,
section 3; the algorithm is due to Edmonds & Karp 1972).

Network: (n, s, t, edges) with vertices 0..n-1, s != t, and edges a tuple of (u, v, c), c >= 0 an integer
capacity (parallel and antiparallel edges allowed). Returns the value of a maximum s-t flow.
"""
from collections import deque


def max_flow_edmonds_karp(network) -> int:
    n, s, t, edges = network
    to, cap, adj = [], [], [[] for _ in range(n)]
    for u, v, c in edges:              # edge 2i: u -> v with capacity c; edge 2i + 1: its residual reverse
        adj[u].append(len(to))
        to.append(v)
        cap.append(c)
        adj[v].append(len(to))
        to.append(u)
        cap.append(0)
    flow = 0
    while True:
        parent_edge = [-1] * n
        parent_edge[s] = -2
        queue = deque([s])
        while queue and parent_edge[t] == -1:
            u = queue.popleft()
            for e in adj[u]:
                v = to[e]
                if cap[e] > 0 and parent_edge[v] == -1:
                    parent_edge[v] = e
                    queue.append(v)
        if parent_edge[t] == -1:
            return flow
        bottleneck = None
        v = t
        while v != s:                  # walk the path back from t
            e = parent_edge[v]
            if bottleneck is None or cap[e] < bottleneck:
                bottleneck = cap[e]
            v = to[e ^ 1]
        v = t
        while v != s:
            e = parent_edge[v]
            cap[e] -= bottleneck
            cap[e ^ 1] += bottleneck
            v = to[e ^ 1]
        flow += bottleneck
