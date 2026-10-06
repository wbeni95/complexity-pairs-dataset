"""Expand around each of the 2n - 1 centers (n characters and n - 1 gaps between them).

From each center, extend while the characters on both sides are equal. The cost is Theta(n + R), where R is
the sum of the maximal palindrome radii over all centers: Theta(n^2) in the worst case (n equal characters,
R ~ n^2/2), but Theta(n) in expectation on random strings over two or more letters.

Returns (length, start) of the leftmost longest palindromic substring; (0, 0) for the empty string.
"""


def lps_expand(s):
    n = len(s)
    best_len, best_start = 0, 0
    for c in range(2 * n - 1):
        lo = c // 2
        hi = lo + (c % 2)               # even c: center at character lo; odd c: center in the gap lo|lo+1
        while lo >= 0 and hi < n and s[lo] == s[hi]:
            lo -= 1
            hi += 1
        length = hi - lo - 1
        # For a fixed length the start (c - length + 1) / 2 grows with c, so "strictly longer"
        # keeps the leftmost palindrome among those of maximum length.
        if length > best_len:
            best_len, best_start = length, lo + 1
    return best_len, best_start
