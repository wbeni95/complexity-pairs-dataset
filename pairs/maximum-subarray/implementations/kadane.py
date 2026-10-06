"""Kadane's algorithm: one left-to-right scan, Theta(n).

Invariant after reading a[0..j]: ending_here = the best sum of a non-empty subarray ending at j,
best = the best sum of any non-empty subarray of a[0..j]. A subarray ending at j is either a[j] alone
or extends the best one ending at j - 1.
"""


def max_subarray_kadane(a) -> int:
    best = ending_here = a[0]
    for j in range(1, len(a)):
        x = a[j]
        ending_here = x if ending_here < 0 else ending_here + x
        if ending_here > best:
            best = ending_here
    return best
