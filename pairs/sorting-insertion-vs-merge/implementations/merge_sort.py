"""Top-down merge sort: sort each half recursively, then merge. Theta(n log n) on every input.

The recursion has ceil(log2 n) levels and the merges on each level touch every element once.
"""


def merge_sort(xs) -> list:
    if len(xs) <= 1:
        return list(xs)           # always return a new list
    mid = len(xs) // 2
    left = merge_sort(xs[:mid])
    right = merge_sort(xs[mid:])
    out = []
    i = j = 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:    # take from the left on ties: the sort is stable
            out.append(right[j])
            j += 1
        else:
            out.append(left[i])
            i += 1
    out.extend(left[i:])
    out.extend(right[j:])
    return out
