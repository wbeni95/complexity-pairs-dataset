"""Instances: n integers in [-R, R] with R = n^2, which gives a mix of yes and no answers."""
from collections import Counter


def generate(n, rng):
    r = max(1, n * n)
    return tuple(rng.randint(-r, r) for _ in range(n))


def generate_scaling(n, rng):
    """Worst case for both algorithms: no solution exists (all values positive), so neither exits early."""
    return tuple(rng.randint(1, 10 * n * n) for _ in range(n))


def check(values, output):
    """Independent oracle: hash lookup over pairs, Theta(n^2), respecting index multiplicity."""
    count = Counter(values)
    n = len(values)
    found = False
    for i in range(n):
        for j in range(i + 1, n):
            t = -(values[i] + values[j])
            need = 1 + (t == values[i]) + (t == values[j])
            if count[t] >= need:
                found = True
                break
        if found:
            break
    return output == found
