"""Count directed Hamiltonian cycles by inclusion-exclusion over vertex subsets (polynomial space).

Input: an n x n 0/1 adjacency matrix (tuple of tuples); adj[u][v] = 1 means there is an arc u -> v. The diagonal
is ignored. Output: the number of directed Hamiltonian cycles, each counted once. n <= 1 gives 0; n = 2 gives
adj[0][1] * adj[1][0].

Idea. A closed walk of length n from vertex 0 is a sequence 0 = w_0, w_1, ..., w_{n-1}, w_n = 0 in which every
step w_i -> w_{i+1} is an arc between two different vertices. Such a walk is a Hamiltonian cycle (written from 0)
exactly when w_0, ..., w_{n-1} cover all n vertices, i.e. are pairwise distinct. For a set T containing 0 let W(T)
be the number of closed walks of length n from 0 that stay inside T. By inclusion-exclusion over the vertices
missed by a walk,
    #Hamiltonian cycles = sum over T with 0 in T of (-1)^(n - |T|) * W(T).
Each W(T) is computed by a dynamic programme over the walk length that keeps one number per vertex of T
("walks of the current length from 0 ending here"), so the memory is Theta(n) numbers, not Theta(2^n).

Operation count (unit-cost integers): for |T| = t the walk DP makes n steps of t(t-1) multiplications and t(t-1)
additions. Summed over the 2^(n-1) sets T, that is exactly n(n-1)(n+2)2^(n-3) multiplications and as many
additions, plus one signed accumulation per set: Theta(n^3 2^n) time. Nothing branches on the matrix entries,
so the count is the same on every input with n vertices.
"""


def count_hamiltonian_cycles_inclusion_exclusion(adj):
    n = len(adj)
    if n <= 1:
        return 0
    total = 0
    for mask in range(1 << (n - 1)):          # T = {0} plus the vertices v >= 1 with bit v-1 set
        allowed = [0] + [v for v in range(1, n) if (mask >> (v - 1)) & 1]
        t = len(allowed)
        walks = [0] * t                        # walks[i]: walks of the current length from 0 to allowed[i]
        walks[0] = 1
        for _ in range(n):
            nxt = []
            for j in range(t):
                acc = 0
                for i in range(t):
                    if i != j:                 # self-loops are never used
                        acc = acc + walks[i] * adj[allowed[i]][allowed[j]]
                nxt.append(acc)
            walks = nxt
        if (n - t) % 2 == 0:
            total = total + walks[0]
        else:
            total = total - walks[0]
    return total
