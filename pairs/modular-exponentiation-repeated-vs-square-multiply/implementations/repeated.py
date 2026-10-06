"""Repeated multiplication: multiply by a, e times. Theta(e) = Theta(2^n) modular multiplications."""


def modpow_repeated(instance) -> int:
    a, e, m = instance
    a %= m
    r = 1 % m
    for _ in range(e):
        r = r * a % m
    return r
