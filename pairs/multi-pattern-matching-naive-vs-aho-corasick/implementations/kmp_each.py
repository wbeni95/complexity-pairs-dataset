"""Knuth-Morris-Pratt once for every pattern.

Each run is Theta(N + m) (failure table in at most 3(m - 1) comparisons, scan in at most 3N, because the current
character is compared again after the while loop), so P patterns of total
length L cost Theta(P N + L): linear in the text for each pattern, but the text is read P times.
"""


def _failure(pattern):
    fail = [0] * len(pattern)
    k = 0
    for q in range(1, len(pattern)):
        while k > 0 and pattern[q] != pattern[k]:
            k = fail[k - 1]
        if pattern[q] == pattern[k]:
            k += 1
        fail[q] = k
    return fail


def count_occurrences_kmp_each(instance):
    text, patterns = instance
    counts = []
    for pattern in patterns:
        m = len(pattern)
        fail = _failure(pattern)
        count = 0
        q = 0
        for c in text:
            while q > 0 and c != pattern[q]:
                q = fail[q - 1]
            if c == pattern[q]:
                q += 1
            if q == m:                      # full match ending here; keep the longest border for overlaps
                count += 1
                q = fail[q - 1]
        counts.append(count)
    return tuple(counts)
