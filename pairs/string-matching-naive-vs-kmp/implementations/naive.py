"""Naive matching: compare P against every alignment of T, character by character.

At most (n - m + 1) * m character comparisons: Theta(n m) in the worst case (e.g. T = a^n, P = a^(m-1) b).
"""


def count_naive(instance) -> int:
    text, pattern = instance
    n, m = len(text), len(pattern)
    count = 0
    for i in range(n - m + 1):
        j = 0
        while j < m and text[i + j] == pattern[j]:
            j += 1
        if j == m:
            count += 1
    return count
