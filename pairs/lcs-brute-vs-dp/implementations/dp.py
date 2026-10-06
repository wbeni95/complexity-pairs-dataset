"""Classic LCS dynamic programming, two rows: Theta(n m) time, O(m) space."""


def lcs_dp(instance) -> int:
    a, b = instance
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]
