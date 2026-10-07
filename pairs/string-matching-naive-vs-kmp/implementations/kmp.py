"""Knuth-Morris-Pratt: Theta(n + m) for every text and pattern.

fail[q] = length of the longest proper border (prefix that is also a suffix) of pattern[:q + 1].
On a mismatch after q matched characters, the next alignment worth trying keeps fail[q - 1] of them,
so no text character is ever re-read. Per text character the scan makes one comparison in the if test
after the while loop and at most one failing while test; every succeeding while test strictly shrinks q,
which grows by at most 1 per character. This bounds the comparisons by 3n (scan) + 3(m - 1) (failure
table, by the same argument); T = a^n, P = a^(m-1) b (m >= 3, n >= m - 1) attains 3n - m and 3m - 6.
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
