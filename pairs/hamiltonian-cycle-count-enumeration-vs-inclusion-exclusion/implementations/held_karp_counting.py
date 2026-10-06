"""Count directed Hamiltonian cycles with the Bellman / Held-Karp dynamic programme over (subset, end vertex).

Input: an n x n 0/1 adjacency matrix (tuple of tuples); adj[u][v] = 1 means there is an arc u -> v. The diagonal
is ignored. Output: the number of directed Hamiltonian cycles, each counted once. n <= 1 gives 0; n = 2 gives
adj[0][1] * adj[1][0].

paths[S][v] (S a non-empty set of vertices from 1..n-1, v in S) is the number of directed paths that start at
vertex 0, visit exactly the vertices {0} plus S, and end at v:
    paths[{v}][v] = adj[0][v]
    paths[S][v]   = sum over u in S - {v} of paths[S - {v}][u] * adj[u][v]      (|S| >= 2)
    answer        = sum over v of paths[{1..n-1}][v] * adj[v][0]
This is the TSP recurrence of Bellman (1962) and Held & Karp (1962) with (min, +) replaced by (+, *).

Operation count: a set S of size s >= 2 costs s(s-1) multiplications and s(s-1) additions, so with m = n-1 the
total is m(m-1)2^(m-2) + m multiplications and as many additions, i.e. (n-1)(n-2)2^(n-2) + 2(n-1) arithmetic
operations: Theta(n^2 2^n) time. Nothing branches on the matrix entries. Space Theta(n 2^n) numbers: the table
is exponential, which is the price for being a factor Theta(n) faster than the inclusion-exclusion count.
"""


def count_hamiltonian_cycles_held_karp(adj):
    n = len(adj)
    if n <= 1:
        return 0
    m = n - 1                                  # vertex v >= 1 is bit v-1
    full = (1 << m) - 1
    paths = [[0] * m for _ in range(1 << m)]
    for b in range(m):
        paths[1 << b][b] = adj[0][b + 1]
    for mask in range(1, 1 << m):              # increasing order: every subset comes before its supersets
        if mask & (mask - 1) == 0:
            continue                           # singletons: base case above
        for b in range(m):
            if not (mask >> b) & 1:
                continue
            prev = mask ^ (1 << b)
            acc = 0
            for a in range(m):
                if (prev >> a) & 1:
                    acc = acc + paths[prev][a] * adj[a + 1][b + 1]
            paths[mask][b] = acc
    total = 0
    for b in range(m):
        total = total + paths[full][b] * adj[b + 1][0]
    return total
