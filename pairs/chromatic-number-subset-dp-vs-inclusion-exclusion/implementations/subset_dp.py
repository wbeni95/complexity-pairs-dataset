"""Chromatic number by dynamic programming over vertex subsets, removing one independent set at a time.

chi(S) = min over non-empty independent sets T contained in S of chi(S \\ T) + 1, with chi(empty) = 0.
This is the plain variant: T ranges over ALL non-empty independent subsets of S (Lawler 1976 restricts T
to the maximal independent sets of G[S], which is what gives his O(2.4423^n) bound; that refinement is
not implemented here).

Cost: the submask loop visits every pair (S, T) with T a non-empty subset of S, i.e.
sum_S (2^|S| - 1) = 3^n - 2^n iterations on every input, each O(1) on n-bit masks; tabulating which
subsets are independent takes Theta(2^n). Total Theta(3^n) time, Theta(2^n) space.

The graph is (n, edges) with vertices 0..n-1 and edges a tuple of pairs (u, v), u < v.
"""


def chromatic_subset_dp(graph) -> int:
    n, edges = graph
    adj = [0] * n
    for u, v in edges:
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    size = 1 << n
    independent = [False] * size
    independent[0] = True
    for S in range(1, size):
        low = S & -S
        v = low.bit_length() - 1
        rest = S ^ low
        independent[S] = independent[rest] and not (adj[v] & rest)
    chi = [0] * size
    for S in range(1, size):
        best = n
        T = S
        while T:                      # every non-empty submask T of S
            if independent[T]:
                c = chi[S ^ T] + 1
                if c < best:
                    best = c
            T = (T - 1) & S
        chi[S] = best
    return chi[size - 1]
