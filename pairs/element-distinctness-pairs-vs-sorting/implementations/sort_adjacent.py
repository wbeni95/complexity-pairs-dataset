"""Sort a copy with a bottom-up merge sort, then compare neighbours: Theta(n log n) on every input.

Equal values end up adjacent after sorting, so the values are pairwise distinct iff no two neighbours
in sorted order are equal. Merge sort makes ceil(log2 n) passes of Theta(n) work each, regardless of the
input order; the final scan is O(n) (n - 1 tests when the values are distinct). Only comparisons between
input values are used.
"""


def _merge_sort(values):
    a = list(values)
    n = len(a)
    buf = [None] * n
    width = 1
    while width < n:
        for lo in range(0, n, 2 * width):
            mid = min(lo + width, n)
            hi = min(lo + 2 * width, n)
            i, j, k = lo, mid, lo
            while i < mid and j < hi:
                if a[i] <= a[j]:
                    buf[k] = a[i]
                    i += 1
                else:
                    buf[k] = a[j]
                    j += 1
                k += 1
            while i < mid:
                buf[k] = a[i]
                i += 1
                k += 1
            while j < hi:
                buf[k] = a[j]
                j += 1
                k += 1
        a, buf = buf, a
        width *= 2
    return a


def distinct_by_sorting(values) -> bool:
    a = _merge_sort(values)
    for k in range(1, len(a)):
        if a[k - 1] == a[k]:
            return False
    return True
