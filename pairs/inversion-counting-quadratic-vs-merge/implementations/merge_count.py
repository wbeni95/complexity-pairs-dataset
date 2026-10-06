"""Count inversions during merge sort: Theta(n log n).

When an element of the right half is merged before the remaining elements of the left half, it forms an
inversion with each of them, so all cross inversions are counted in the linear-time merge.
"""


def inversions_merge(values) -> int:
    _, count = _sort_count(list(values))
    return count


def _sort_count(a):
    if len(a) <= 1:
        return a, 0
    mid = len(a) // 2
    left, cl = _sort_count(a[:mid])
    right, cr = _sort_count(a[mid:])
    merged, cross = [], 0
    i = j = 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:
            merged.append(right[j])
            cross += len(left) - i
            j += 1
        else:
            merged.append(left[i])
            i += 1
    merged.extend(left[i:])
    merged.extend(right[j:])
    return merged, cl + cr + cross
