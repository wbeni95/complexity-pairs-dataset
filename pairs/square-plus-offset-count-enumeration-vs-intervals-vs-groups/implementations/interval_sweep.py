"""Counting the n-bit integers with a cheap representation k = X^2 + C, by a sweep over one interval per root
(algorithm A2).

Definitions as in entry.json: L(v) = binary digits of |v| (L(0) = 1), f_k(X) = L(X) + L(C) + [C < 0] with C = k - X^2,
S_n = {0 <= k < 2^n : min over X of f_k(X) <= n - 4}. Output: (|S_n|, number of roots examined).

Lemma B of the entry. Let B = 2^n - 1, v = n - 4 and T = isqrt(B) + 1. For a root X let w = v - L(X). If w >= 1, the
k >= 0 with f_k(X) <= v form the interval I_X = [max(0, X^2 - m), X^2 + 2^w - 1], with m = 2^(w-1) - 1 for w >= 2 and
m = 0 for w = 1; if w <= 0 there are none. S_n is the union of the clipped intervals I_X intersected with [0, B] over
X = 0, ..., T.

The left ends X^2 - m are strictly increasing in X (m does not grow when L(X) grows), so the clipped left ends are
non-decreasing and one merge pass in X order computes the size of the union. Clipping can leave an interval empty
(for example n = 13, X = 91: X^2 - m = 8280 > B = 8191); such an interval contributes nothing and is skipped.
The run examines exactly T + 1 = isqrt(2^n - 1) + 2 roots (2^(n/2) + 1 for even n), each with O(1) word operations.
"""
from math import isqrt


def bit_length(v):
    """L(v): number of binary digits of |v|, with L(0) = 1."""
    v = -v if v < 0 else v
    return v.bit_length() if v else 1


def count_by_interval_sweep(n):
    B = (1 << n) - 1
    v = n - 4
    T = isqrt(B) + 1
    total = 0
    start = end = None                     # current merged component [start, end]
    examined = 0
    for x in range(T + 1):
        examined += 1
        w = v - bit_length(x)
        if w < 1:
            continue                       # no k has f_k(x) <= v
        m = (1 << (w - 1)) - 1 if w >= 2 else 0
        lo = max(0, x * x - m)
        hi = min(x * x + (1 << w) - 1, B)
        if lo > hi:
            continue                       # empty after clipping to [0, B]
        if start is None:
            start, end = lo, hi
        elif lo <= end + 1:                # left ends are non-decreasing: overlap or touch
            if hi > end:
                end = hi
        else:
            total += end - start + 1
            start, end = lo, hi
    if start is not None:
        total += end - start + 1
    return total, examined
