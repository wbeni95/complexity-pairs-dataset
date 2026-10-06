"""Generic brute-force oracles over an arbitrary structure S (they use only S.add, S.mul, S.zero, S.one).

They define the semantics of a mutated problem by exhaustive enumeration: the "brute side evaluates any algebra".
"""
from __future__ import annotations

from itertools import combinations


def simple_paths_all_pairs(W, S):
    """D[i][j] = ⊕ over simple directed paths i -> j of the ⊗-product of their edge weights; D[i][i] = 1 (empty path).
    W[i][j] is a weight or None (no edge); the diagonal is ignored. Entries equal to S.zero are reported as None."""
    n = len(W)
    D = [[S.zero] * n for _ in range(n)]

    def dfs(s, u, acc, visited):
        D[s][u] = S.add(D[s][u], acc) if u != s else D[s][u]
        for v in range(n):
            if v != u and not visited[v] and W[u][v] is not None:
                visited[v] = True
                dfs(s, v, S.mul(acc, W[u][v]), visited)
                visited[v] = False

    for s in range(n):
        visited = [False] * n
        visited[s] = True
        dfs(s, s, S.one, visited)
        D[s][s] = S.one
    return tuple(tuple(None if S.eq(d, S.zero) else d for d in row) for row in D)


def spanning_trees(W, S):
    """⊕ over all spanning trees T of K_n of ⊗_{e in T} W[u][v] (n <= 1: the empty tree, value 1)."""
    n = len(W)
    if n <= 1:
        return S.one
    edges = [(u, v) for u in range(n) for v in range(u + 1, n)]
    total = S.zero
    for subset in combinations(edges, n - 1):
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        ok = True
        prod = S.one
        for u, v in subset:
            ru, rv = find(u), find(v)
            if ru == rv:
                ok = False
                break
            parent[ru] = rv
            prod = S.mul(prod, W[u][v])
        if ok:
            total = S.add(total, prod)
    return total


def max_cut_brute(W):
    """Maximum cut weight of a symmetric weight matrix (plain ints), for the min-cut -> max-cut mirror."""
    n = len(W)
    if n < 2:
        return None
    best = None
    for mask in range((1 << (n - 1)) - 1):      # vertex 0 and the vertices in mask on one side; T must be non-empty
        S_ = [0] + [v for v in range(1, n) if (mask >> (v - 1)) & 1]
        T = [v for v in range(1, n) if not (mask >> (v - 1)) & 1]
        w = sum(W[u][v] for u in S_ for v in T)
        best = w if best is None or w > best else best
    return best


def subarray_sum_product(a, S):
    """⊕ over non-empty contiguous subarrays a[i..j] of a[i] ⊗ ... ⊗ a[j] (left to right)."""
    total = None
    for i in range(len(a)):
        prod = None
        for j in range(i, len(a)):
            prod = a[j] if prod is None else S.mul(prod, a[j])
            total = prod if total is None else S.add(total, prod)
    return total


def longest_simple_path(W):
    """Largest total weight of a simple 0 -> n-1 path (plain numbers), by depth-first enumeration."""
    n = len(W)
    if n == 1:
        return 0
    best = None
    visited = [False] * n
    visited[0] = True

    def dfs(u, cost):
        nonlocal best
        if u == n - 1:
            best = cost if best is None or cost > best else best
            return
        for v in range(n):
            if not visited[v]:
                visited[v] = True
                dfs(v, cost + W[u][v])
                visited[v] = False
    dfs(0, 0)
    return best
