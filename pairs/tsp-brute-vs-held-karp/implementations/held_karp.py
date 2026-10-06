"""Held-Karp / Bellman dynamic programming over subsets: Theta(n^2 2^n) time, Theta(n 2^n) space.

best[S][j] = cheapest path that starts at city 0, visits exactly the cities in S (a subset of
{1..n-1}, encoded as a bitmask over cities 1..n-1), and ends at city j in S.
"""
import math


def tsp_held_karp(W) -> int:
    n = len(W)
    if n <= 1:
        return 0
    m = n - 1  # cities 1..n-1 are bits 0..m-1
    full = (1 << m) - 1
    best = [[math.inf] * m for _ in range(1 << m)]
    for j in range(m):
        best[1 << j][j] = W[0][j + 1]
    for S in range(1, 1 << m):
        row = best[S]
        for j in range(m):
            if not (S >> j & 1) or row[j] == math.inf:
                continue
            base = row[j]
            wj = W[j + 1]
            for k in range(m):
                if S >> k & 1:
                    continue
                T = S | (1 << k)
                c = base + wj[k + 1]
                if c < best[T][k]:
                    best[T][k] = c
    return min(best[full][j] + W[j + 1][0] for j in range(m))
