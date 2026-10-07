"""Patience sorting with binary search: O(n log n).

tails[k] = the smallest possible last element of a strictly increasing subsequence of length k + 1
among the elements read so far. tails is strictly increasing, so each new element x replaces the first
entry >= x (found by binary search), or is appended if every entry is < x. The answer is len(tails).
Each step costs O(1 + log len(tails)) (at most floor(log2 len(tails)) + 1 comparisons), so the total is
O(n (1 + log L)) <= O(n log n) for n >= 2, L = the answer.
"""


def lis_patience(a) -> int:
    tails = []
    for x in a:
        lo, hi = 0, len(tails)               # find the first index with tails[index] >= x
        while lo < hi:
            mid = (lo + hi) // 2
            if tails[mid] < x:
                lo = mid + 1
            else:
                hi = mid
        if lo == len(tails):
            tails.append(x)
        else:
            tails[lo] = x
    return len(tails)
