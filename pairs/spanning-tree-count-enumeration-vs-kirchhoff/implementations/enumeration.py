"""Count spanning trees by trying every set of n-1 edges: C(m, n-1) subsets.

A set of n-1 edges on n vertices is a spanning tree iff it is acyclic (a forest with n vertices and
n-1 edges has exactly n - (n-1) = 1 component). Acyclicity is tested with a fresh union-find per
subset (union by size, path halving): an edge whose endpoints already have the same root closes a cycle,
and the subset is rejected at that edge.

Cost per subset: Theta(n) to reset the two arrays, plus at most n-1 unions (2(n-1) finds), O(n log n) because
union by size keeps every tree of height at most log2 n. With the Theta(n^2) scan of the matrix for the edge list,
the total is O(n^2 + n log n C(m, n-1)) and Omega(n^2 + n C(m, n-1)); on K_n, m = n(n-1)/2.
"""
from itertools import combinations


def _find(parent, x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]  # path halving
        x = parent[x]
    return x


def count_spanning_trees_enumeration(A) -> int:
    n = len(A)
    edges = [(u, v) for u in range(n) for v in range(u + 1, n) if A[u][v]]
    count = 0
    for subset in combinations(edges, n - 1):
        parent = list(range(n))
        size = [1] * n
        for u, v in subset:
            ru, rv = _find(parent, u), _find(parent, v)
            if ru == rv:
                break  # this edge closes a cycle
            if size[ru] < size[rv]:
                ru, rv = rv, ru
            parent[rv] = ru
            size[ru] += size[rv]
        else:
            count += 1  # n-1 edges and no cycle: a spanning tree
    return count
