"""Enumerate all 2^n subsequences of a; keep the longest that is also a subsequence of b.

O(2^n (n + m)) time, Theta(2^n n) when m = n: each of the 2^n masks is checked with one greedy left-to-right
scan of b (proofs: PROOFS.md; the upper bound assumes that str.find scans forward to the first match).
"""


def lcs_brute(instance) -> int:
    a, b = instance
    n = len(a)
    best = 0
    for mask in range(1 << n):
        j = 0
        is_common = True
        for i in range(n):
            if mask >> i & 1:
                j = b.find(a[i], j)
                if j < 0:
                    is_common = False
                    break
                j += 1
        if is_common:
            best = max(best, mask.bit_count())
    return best
