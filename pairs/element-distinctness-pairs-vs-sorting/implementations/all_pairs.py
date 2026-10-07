"""Compare every pair of positions: n(n-1)/2 equality tests when the values are distinct.

The scan stops at the first equal pair, so every "all distinct" input costs the maximum n(n-1)/2 (Theta(n^2)):
every pair must be compared before the algorithm can say yes. A no-instance whose only equal pair is the last pair
scanned costs n(n-1)/2 as well.
"""


def distinct_all_pairs(values) -> bool:
    n = len(values)
    for i in range(n):
        x = values[i]
        for j in range(i + 1, n):
            if values[j] == x:
                return False
    return True
