"""Quadratic dynamic programming.

L[i] = length of the longest strictly increasing subsequence that ends at position i
     = 1 + max(L[j] : j < i, a[j] < a[i])   (1 if there is no such j).
The answer is max(L). Every pair j < i is examined once: n(n-1)/2 comparisons, Theta(n^2).
"""


def lis_quadratic(a) -> int:
    n = len(a)
    L = [1] * n
    best = 0
    for i in range(n):
        ai = a[i]
        li = 1
        for j in range(i):
            if a[j] < ai and L[j] + 1 > li:
                li = L[j] + 1
        L[i] = li
        if li > best:
            best = li
    return best
