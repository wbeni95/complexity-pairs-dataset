"""Brute force: test every substring s[i..j] for being a palindrome.

There are n(n+1)/2 substrings; each test compares characters from both ends inward and stops at the first
mismatch. On a string of n equal characters every substring is a palindrome and its test makes
floor(len/2) comparisons, sum_{L=1..n} (n - L + 1) floor(L/2) ~ n^3/12 in total: Theta(n^3) worst case.
(On random strings over two or more letters most tests stop after O(1) comparisons, so the cost there is
Theta(n^2).)

Returns (length, start) of the longest palindromic substring, the leftmost one among those of maximum
length; (0, 0) for the empty string.
"""


def lps_brute(s):
    n = len(s)
    best_len, best_start = 0, 0
    for i in range(n):
        for j in range(i, n):
            lo, hi = i, j
            while lo < hi and s[lo] == s[hi]:
                lo += 1
                hi -= 1
            if lo >= hi and j - i + 1 > best_len:     # strictly longer: keeps the leftmost on ties
                best_len, best_start = j - i + 1, i
    return best_len, best_start
