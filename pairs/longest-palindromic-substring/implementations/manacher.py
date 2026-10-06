"""Manacher's algorithm: the maximal palindrome radius at every center in Theta(n) time.

d1[i] = number of odd-length palindromes centered at character i (the longest has length 2 d1[i] - 1);
d2[i] = number of even-length palindromes centered in the gap before character i (longest: 2 d2[i]).
The scan keeps the rightmost palindrome found so far, s[l..r]. For a center i inside it, the mirror center
l + r - i already gives a lower bound on the radius at i (capped at the right end r), so character
comparisons start from there. In each of the two scans, every comparison that succeeds moves r to the
right, so there are at most n successful comparisons, plus at most one failed comparison per center:
Theta(n) in total, on every input.

Returns (length, start) of the leftmost longest palindromic substring; (0, 0) for the empty string.
"""


def lps_manacher(s):
    n = len(s)
    if n == 0:
        return 0, 0
    d1 = [0] * n
    l, r = 0, -1
    for i in range(n):
        k = 1 if i > r else min(d1[l + r - i], r - i + 1)
        while i - k >= 0 and i + k < n and s[i - k] == s[i + k]:
            k += 1
        d1[i] = k
        if i + k - 1 > r:
            l, r = i - k + 1, i + k - 1
    d2 = [0] * n
    l, r = 0, -1
    for i in range(n):
        k = 0 if i > r else min(d2[l + r - i + 1], r - i + 1)
        while i - k - 1 >= 0 and i + k < n and s[i - k - 1] == s[i + k]:
            k += 1
        d2[i] = k
        if i + k - 1 > r:
            l, r = i - k, i + k - 1
    best_len, best_start = 0, 0
    for i in range(n):
        for length, start in ((2 * d1[i] - 1, i - d1[i] + 1), (2 * d2[i], i - d2[i])):
            if length > best_len or (length == best_len and start < best_start):
                best_len, best_start = length, start
    return best_len, best_start
