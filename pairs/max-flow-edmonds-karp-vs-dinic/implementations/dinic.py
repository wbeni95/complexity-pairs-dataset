"""Maximum flow by Dinic's algorithm: blocking flows in BFS level graphs.

Each phase computes BFS levels from s in the residual graph and then a blocking flow in the level graph
(edges from level i to level i + 1 with positive residual capacity), by repeated depth-first searches that
use a current-arc pointer per vertex: an edge that leads nowhere or is saturated is never tried again in
the phase. A blocking flow costs O(V E) (at most E augmenting paths of at most V edges, plus O(E) pointer
advances), and the s-t distance strictly increases from phase to phase, so there are at most V - 1 phases:
O(V^2 E) time in total.

The DFS is iterative (paths can be longer than Python's recursion limit).

Network: (n, s, t, edges) as in the Edmonds-Karp implementation. Returns the value of a maximum s-t flow.
"""
from collections import deque


def max_flow_dinic(network) -> int:
    n, s, t, edges = network
    to, cap, adj = [], [], [[] for _ in range(n)]
    for u, v, c in edges:
        adj[u].append(len(to))
        to.append(v)
        cap.append(c)
        adj[v].append(len(to))
        to.append(u)
        cap.append(0)
    flow = 0
    while True:
        level = [-1] * n
        level[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for e in adj[u]:
                v = to[e]
                if cap[e] > 0 and level[v] == -1:
                    level[v] = level[u] + 1
                    queue.append(v)
        if level[t] == -1:
            return flow
        it = [0] * n                       # current-arc pointers
        path = []                          # edge ids of the current partial path from s
        u = s
        while True:
            if u == t:                     # augment along the path, then restart from s
                f = min(cap[e] for e in path)
                for e in path:
                    cap[e] -= f
                    cap[e ^ 1] += f
                flow += f
                path = []
                u = s
                continue
            arcs = adj[u]
            while it[u] < len(arcs):
                e = arcs[it[u]]
                if cap[e] > 0 and level[to[e]] == level[u] + 1:
                    break
                it[u] += 1
            if it[u] < len(arcs):          # advance
                e = arcs[it[u]]
                path.append(e)
                u = to[e]
            else:                          # retreat: u is a dead end for this phase
                if not path:
                    break                  # s is exhausted: the flow is blocking
                e = path.pop()
                u = to[e ^ 1]
                it[u] += 1
