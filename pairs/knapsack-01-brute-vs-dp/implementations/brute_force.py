"""Try all 2^n subsets of items: Theta(2^n n) time."""


def knapsack_brute(instance) -> int:
    weights, values, capacity = instance
    n = len(weights)
    best = 0
    for mask in range(1 << n):
        w = v = 0
        for i in range(n):
            if mask >> i & 1:
                w += weights[i]
                v += values[i]
        if w <= capacity:
            best = max(best, v)
    return best
