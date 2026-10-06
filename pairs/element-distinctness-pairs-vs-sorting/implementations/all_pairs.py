"""Compare every pair of positions: n(n-1)/2 equality tests when the values are distinct.

The scan stops at the first equal pair, so the worst case (Theta(n^2)) is exactly the "all distinct"
answer: every pair must be compared before the algorithm can say yes.
"""


def distinct_all_pairs(values) -> bool:
    n = len(values)
    for i in range(n):
        x = values[i]
        for j in range(i + 1, n):
            if values[j] == x:
                return False
    return True
