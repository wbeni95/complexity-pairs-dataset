"""Instances: a list of n integers drawn uniformly from [-n, n] (so duplicates and negatives occur).

Uniformly random input is the average case for insertion sort; V2 is measured on it too (no
generate_scaling), which is honest because insertion sort is Theta(n^2) on average as well as in
the worst case, and merge sort is Theta(n log n) on every input.

The oracle is Python's built-in sorted(), used here only as a reference, never as an implementation.
"""


def generate(n, rng):
    return [rng.randint(-n, n) for _ in range(n)]


def check(instance, output):
    return isinstance(output, list) and output == sorted(instance)
