"""Wagner-Fischer dynamic programming, two rows: O(m) space and Theta((n + 1)(m + 1)) time,
i.e. Theta(n m) for non-empty strings (proofs: PROOFS.md)."""


def edit_distance_dp(instance) -> int:
    a, b = instance
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            cur[j] = min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb))
        prev = cur
    return prev[-1]
