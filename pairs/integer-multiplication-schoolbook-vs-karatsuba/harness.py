"""Instances: two n-digit non-negative integers as little-endian tuples of base-2^15 digits.

The top digit of each factor is non-zero (so both really have n digits). Besides uniform digits, some
V1 factors are BASE^n - 1 (all digits BASE-1) or random mixes of 0 and BASE-1 digits, to exercise
carries and borrows.
"""

BITS = 15
BASE = 1 << BITS


def generate(n, rng):
    def number():
        r = rng.random()
        if r < 0.1:             # BASE^n - 1: the maximal n-digit number, carries everywhere
            digits = [BASE - 1] * n
        elif r < 0.4:           # carry / borrow stress: long runs of 0 and BASE-1
            digits = [rng.choice((0, BASE - 1)) for _ in range(n)]
        else:
            digits = [rng.randrange(BASE) for _ in range(n)]
        if n:
            digits[-1] = digits[-1] or 1 + rng.randrange(BASE - 1)
        return tuple(digits)
    return number(), number()


def generate_scaling(n, rng):
    return (tuple(rng.randrange(1, BASE) for _ in range(n)),
            tuple(rng.randrange(1, BASE) for _ in range(n)))


def _value(digits):
    v = 0
    for d in reversed(digits):
        v = (v << BITS) | d
    return v


def check(instance, output):
    """Oracle: Python's built-in big-integer product (used here only, never in the implementations)."""
    a, b = instance
    if len(output) != len(a) + len(b) or not all(0 <= d < BASE for d in output):
        return False
    return _value(output) == _value(a) * _value(b)
