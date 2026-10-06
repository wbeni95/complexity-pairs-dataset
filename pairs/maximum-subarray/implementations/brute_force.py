"""Brute force: sum every contiguous subarray from scratch.

The innermost loop runs sum over i <= j of (j - i + 1) = n(n+1)(n+2)/6 times: Theta(n^3) on every input.
"""


def max_subarray_brute(a) -> int:
    n = len(a)
    best = a[0]
    for i in range(n):
        for j in range(i, n):
            s = 0
            for k in range(i, j + 1):
                s += a[k]
            if s > best:
                best = s
    return best
