"""Running sums: for each start i, extend the subarray to the right one element at a time.

The sum of a[i..j] is obtained from the sum of a[i..j-1] in O(1), so there are n(n+1)/2 steps: Theta(n^2).
"""


def max_subarray_quadratic(a) -> int:
    n = len(a)
    best = a[0]
    for i in range(n):
        s = 0
        for j in range(i, n):
            s += a[j]                # s = a[i] + ... + a[j]
            if s > best:
                best = s
    return best
