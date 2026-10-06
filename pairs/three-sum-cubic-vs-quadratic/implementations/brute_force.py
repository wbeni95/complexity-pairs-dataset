"""Check every triple i < j < k: Theta(n^3) in the worst case (no solution, so no early exit)."""


def three_sum_brute(values) -> bool:
    n = len(values)
    for i in range(n):
        for j in range(i + 1, n):
            target = -(values[i] + values[j])
            for k in range(j + 1, n):
                if values[k] == target:
                    return True
    return False
