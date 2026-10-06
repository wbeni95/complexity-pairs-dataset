"""Straight insertion sort (Knuth 5.2.1, Algorithm S) on a copy of the input.

Each element is shifted left past every larger element before it, so the work is n - 1 plus the number
of inversions: Theta(n^2) in the worst case (reversed input) and on average (n(n-1)/4 expected inversions).
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
