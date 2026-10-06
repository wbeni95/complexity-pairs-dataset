"""Instances: tuples of n integers.

generate() mixes four kinds so that V1 sees both answers: n distinct values from a range of size 10 n^2 + 10;
the same with one planted duplicate (a copy of one value written over another position); n values drawn
from [0, n) (duplicates almost always, for n >= 2); and distinct values of magnitude up to 10^18 with both
signs.

generate_scaling() returns n distinct values from [-10^9, 10^9): the worst case for the all-pairs scan
(no early exit). The sorting algorithm does Theta(n log n) work on every input.

The oracle compares len(set(values)) with n (hashing): it shares no code or idea with the two
implementations under test.
"""


def generate(n, rng):
    kind = rng.randrange(4)
    if kind == 0:
        return tuple(rng.sample(range(10 * n * n + 10), n))
    if kind == 1:
        vals = rng.sample(range(10 * n * n + 10), n)
        if n >= 2:
            i, j = rng.sample(range(n), 2)
            vals[j] = vals[i]
        return tuple(vals)
    if kind == 2:
        return tuple(rng.randrange(max(n, 1)) for _ in range(n))
    return tuple(v - 10 ** 18 for v in rng.sample(range(2 * 10 ** 18), n))


def generate_scaling(n, rng):
    return tuple(rng.sample(range(-10 ** 9, 10 ** 9), n))


def check(values, output):
    return output == (len(set(values)) == len(values))
