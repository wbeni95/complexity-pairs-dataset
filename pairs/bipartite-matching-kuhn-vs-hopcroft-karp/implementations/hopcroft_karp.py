"""Maximum bipartite matching by Hopcroft-Karp: phases of vertex-disjoint shortest augmenting paths.

Each phase (1) runs a BFS from all free left vertices over alternating paths, assigning layer numbers
dist[] to left vertices, and stops expanding at the layer where a free right vertex is first seen (the
length of a shortest augmenting path); (2) runs a DFS from every free left vertex that only follows edges
into the next layer and only accepts a free right vertex at the shortest-path layer. Per-vertex scan
pointers persist through the phase and dead-end vertices are removed (dist = infinity), so each adjacency
list is scanned at most once per DFS pass: O(V + E) per phase. After each augmentation the path's left
vertices are removed as well, so the paths found in one phase are vertex-disjoint; they form a maximal set
of vertex-disjoint shortest augmenting paths (PROOFS.md, Lemma HK3), as in Hopcroft & Karp 1973. Their
analysis bounds the number of phases by O(sqrt(V)), for O((V + E) sqrt(V)) time in total.

Graph: (n_left, n_right, adj) as in the Kuhn implementation. Returns the size of a maximum matching.
"""


def matching_hopcroft_karp(graph) -> int:
    n_left, n_right, adj = graph
    INF = n_left + n_right + 1
    match_l = [-1] * n_left
    match_r = [-1] * n_right
    size = 0
    while True:
        # Phase part 1: BFS layers from all free left vertices.
        dist = [INF] * n_left
        queue = [u for u in range(n_left) if match_l[u] == -1]
        for u in queue:
            dist[u] = 0
        target = INF                     # layer of the left end of a shortest augmenting path, plus 1
        head = 0
        while head < len(queue):
            u = queue[head]
            head += 1
            du = dist[u]
            if du + 1 > target:          # deeper than the shortest augmenting paths: not needed
                continue
            for v in adj[u]:
                w = match_r[v]
                if w == -1:
                    if target == INF:
                        target = du + 1
                elif dist[w] == INF:
                    dist[w] = du + 1
                    queue.append(w)
        if target == INF:
            return size
        # Phase part 2: DFS along the layers for vertex-disjoint shortest augmenting paths.
        ptr = [0] * n_left
        for root in range(n_left):
            if match_l[root] != -1 or dist[root] != 0:
                continue
            stack = [root]
            while stack:
                u = stack[-1]
                nbrs = adj[u]
                du = dist[u]
                pushed = False
                while ptr[u] < len(nbrs):
                    v = nbrs[ptr[u]]
                    ptr[u] += 1
                    w = match_r[v]
                    if w == -1:
                        if du + 1 == target:     # free right vertex at the shortest-path layer
                            for x in stack:      # remove the path's left vertices from this phase
                                dist[x] = INF
                            for x in reversed(stack):
                                old = match_l[x]
                                match_l[x] = v
                                match_r[v] = x
                                v = old
                            size += 1
                            stack = []
                            break
                    elif dist[w] == du + 1:
                        stack.append(w)
                        pushed = True
                        break
                if stack and not pushed:         # every edge of u tried: dead end
                    dist[u] = INF
                    stack.pop()
