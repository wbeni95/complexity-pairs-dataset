"""Test harness: the instance is just n."""

# OEIS A000045, independent of all three implementations.
KNOWN = [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987,
         1597, 2584, 4181, 6765, 10946, 17711, 28657, 46368, 75025]


def generate(n, rng):
    return n


def check(instance, output):
    if instance < len(KNOWN):
        return output == KNOWN[instance]
    return None
