"""DP over remaining capacity (Bellman): O(n (W + 1)) time, Theta(n W) in the worst case; Theta(W) space.

Pseudo-polynomial. Proofs: PROOFS.md."""


def knapsack_dp(instance) -> int:
    weights, values, capacity = instance
    best = [0] * (capacity + 1)  # best[c] = max value with total weight <= c
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):  # descending: each item used at most once
            if best[c - w] + v > best[c]:
                best[c] = best[c - w] + v
    return best[capacity]
