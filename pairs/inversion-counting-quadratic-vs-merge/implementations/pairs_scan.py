"""Count inversions by checking every pair i < j: Theta(n^2)."""


def inversions_quadratic(values) -> int:
    n = len(values)
    count = 0
    for i in range(n):
        vi = values[i]
        for j in range(i + 1, n):
            if vi > values[j]:
                count += 1
    return count
