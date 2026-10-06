"""Subset enumeration: test every one of the 2^n index subsets for being strictly increasing.

Every subset is scanned over all n positions (no early exit), so the cost is exactly 2^n * n
inner steps on every input: Theta(2^n n).
"""


def lis_subsets(a) -> int:
    n = len(a)
    best = 0
    for mask in range(1 << n):
        size = 0
        last = None
        increasing = True
        for i in range(n):
            if mask >> i & 1:
                if last is not None and a[i] <= last:
                    increasing = False
                last = a[i]
                size += 1
        if increasing and size > best:
            best = size
    return best
