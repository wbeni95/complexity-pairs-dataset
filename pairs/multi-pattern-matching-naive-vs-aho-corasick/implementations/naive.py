"""Naive multi-pattern matching: run the naive matcher once for every pattern.

For each pattern p of length m, try every alignment i of p against the text and compare characters left to right
until a mismatch or a full match. At most (N - m + 1) m comparisons per pattern, so O(N L) for total pattern length
L; Theta(sum over patterns of (N - m_p + 1) m_p) in the worst case (e.g. text a^N, patterns a^(m-1) b).
"""


def count_occurrences_naive(instance):
    text, patterns = instance
    n = len(text)
    counts = []
    for pattern in patterns:
        m = len(pattern)
        count = 0
        for i in range(n - m + 1):
            j = 0
            while j < m and text[i + j] == pattern[j]:
                j += 1
            if j == m:
                count += 1
        counts.append(count)
    return tuple(counts)
