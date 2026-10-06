"""Instances: n items, weights in [1, 20], values in [1, 30], capacity = half the total weight."""


def generate(n, rng):
    weights = tuple(rng.randint(1, 20) for _ in range(n))
    values = tuple(rng.randint(1, 30) for _ in range(n))
    return weights, values, sum(weights) // 2


def check(instance, output):
    weights, values, capacity = instance
    # Greedy-by-ratio packing is feasible, so it bounds the optimum from below.
    greedy = w = 0
    for i in sorted(range(len(weights)), key=lambda i: values[i] / weights[i], reverse=True):
        if w + weights[i] <= capacity:
            w += weights[i]
            greedy += values[i]
    return greedy <= output <= sum(values)
