"""DP over remaining capacity (Bellman): Theta(n W) time, Theta(W) space. Pseudo-polynomial."""


def knapsack_dp(instance) -> int:
    weights, values, capacity = instance
    best = [0] * (capacity + 1)  # best[c] = max value with total weight <= c
    for w, v in zip(weights, values):
        for c in range(capacity, w - 1, -1):  # descending: each item used at most once
            if best[c - w] + v > best[c]:
                best[c] = best[c - w] + v
    return best[capacity]
