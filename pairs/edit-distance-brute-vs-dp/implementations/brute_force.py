"""Plain recursion over the three edit operations, no memoisation.

The call tree for two length-n strings has Delannoy-number size D(n, n) ~ (3 + 2 sqrt 2)^n / sqrt(n).
"""


def edit_distance_brute(instance) -> int:
    a, b = instance

    def d(i, j):
        if i == len(a):
            return len(b) - j
        if j == len(b):
            return len(a) - i
        return min(d(i + 1, j) + 1,                        # delete a[i]
                   d(i, j + 1) + 1,                        # insert b[j]
                   d(i + 1, j + 1) + (a[i] != b[j]))       # substitute / match

    return d(0, 0)
