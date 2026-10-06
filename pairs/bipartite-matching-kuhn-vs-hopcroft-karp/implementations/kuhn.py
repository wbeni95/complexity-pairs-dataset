"""Maximum bipartite matching by Kuhn's augmenting-path method: one depth-first search per left vertex.

For each left vertex in index order, search for an augmenting path by DFS over alternating paths (left
vertex -> unmatched edge -> right vertex -> its matched edge -> left vertex ...), marking right vertices as
seen; if a free right vertex is reached, flip the path. Each search scans every adjacency list at most once
(a left vertex is entered only through its matched right vertex, which is marked seen), so it costs
O(V + E), and the n_left searches cost O(V (V + E)) = O(V E) when E = Omega(V).

The DFS is iterative (augmenting paths can be longer than Python's recursion limit).

Graph: (n_left, n_right, adj) with adj[u] = tuple of the right neighbours of left vertex u, scanned in that
order. Returns the size of a maximum matching.
"""


def matching_kuhn(graph) -> int:
    n_left, n_right, adj = graph
    match_l = [-1] * n_left
    match_r = [-1] * n_right
    size = 0
    for root in range(n_left):
        seen = [False] * n_right
        ptr = [0] * n_left
        stack = [root]
        free_right = -1
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            if ptr[u] < len(nbrs):
                v = nbrs[ptr[u]]
                ptr[u] += 1
                if seen[v]:
                    continue
                seen[v] = True
                w = match_r[v]
                if w == -1:
                    free_right = v
                    break
                stack.append(w)            # continue from v's partner
            else:
                stack.pop()                # dead end: back up
        if free_right != -1:
            v = free_right                 # flip: each stack vertex takes the next right vertex on the path
            for u in reversed(stack):
                old = match_l[u]
                match_l[u] = v
                match_r[v] = u
                v = old
            size += 1
    return size
