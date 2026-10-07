"""Straight insertion sort (Knuth, TAOCP Vol. 3) on a copy of the input.

Each element is shifted left past every larger element before it, so for n >= 1 the work is n - 1 plus the
number of inversions: Theta(n^2) in the worst case (reversed input) and on average (n(n-1)/4 expected inversions for a
uniformly random order of distinct elements).
"""


def insertion_sort(xs) -> list:
    a = list(xs)                  # never touch the caller's list
    for i in range(1, len(a)):
        key = a[i]
        j = i - 1
        while j >= 0 and a[j] > key:
            a[j + 1] = a[j]
            j -= 1
        a[j + 1] = key
    return a
