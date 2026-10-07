"""Classic LCS dynamic programming, two rows: O(m) space and Theta((n + 1)(m + 1)) time,
i.e. Theta(n m) for non-empty strings (proofs: PROOFS.md)."""


def lcs_dp(instance) -> int:
    a, b = instance
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]
