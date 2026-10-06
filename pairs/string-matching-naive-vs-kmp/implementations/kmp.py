"""Knuth-Morris-Pratt: Theta(n + m) for every text and pattern.

fail[q] = length of the longest proper border (prefix that is also a suffix) of pattern[:q + 1].
On a mismatch after q matched characters, the next alignment worth trying keeps fail[q - 1] of them,
so no text character is ever re-read. Each step either advances the text position or strictly
shrinks q, which bounds the total work by 2n (scan) + 2m (failure table).
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


def count_kmp(instance) -> int:
    text, pattern = instance
    m = len(pattern)
    fail = _failure(pattern)
    count = 0
    q = 0                                   # number of pattern characters currently matched
    for c in text:
        while q > 0 and c != pattern[q]:
            q = fail[q - 1]
        if c == pattern[q]:
            q += 1
        if q == m:                          # full match ending here; keep the longest border to allow overlaps
            count += 1
            q = fail[q - 1]
    return count
