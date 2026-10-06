"""Meet in the middle (Horowitz-Sahni): Theta(2^(n/2) n) time, Theta(2^(n/2)) space.

Enumerate the 2^(n/2) subsets of each half. Sort the right half by weight with a running maximum of
value. Then, for each left subset, binary-search the heaviest right subset that still fits.
"""
from bisect import bisect_right


def knapsack_mitm(instance) -> int:
    weights, values, capacity = instance
    h = len(weights) // 2
    left = _subset_sums(weights[:h], values[:h])
    right = sorted(_subset_sums(weights[h:], values[h:]))

    right_weights, best_value_up_to = [], []
    running = 0
    for w, v in right:
        running = max(running, v)
        right_weights.append(w)
        best_value_up_to.append(running)

    best = 0
    for w, v in left:
        if w <= capacity:
            i = bisect_right(right_weights, capacity - w) - 1  # i >= 0: the empty subset has weight 0
            best = max(best, v + best_value_up_to[i])
    return best


def _subset_sums(ws, vs):
    """All 2^k (total weight, total value) pairs of the k given items."""
    sums = [(0, 0)]
    for w, v in zip(ws, vs):
        sums += [(sw + w, sv + v) for sw, sv in sums]
    return sums
