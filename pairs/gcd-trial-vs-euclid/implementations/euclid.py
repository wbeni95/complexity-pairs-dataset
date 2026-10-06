"""Euclid's algorithm: gcd(a, b) = gcd(b, a mod b), gcd(a, 0) = a.

At most about log_phi(min(a, b)) + 2 ~ 1.44 n + 2 division steps (Lame 1844); consecutive Fibonacci
numbers are the worst case.
"""


def gcd_euclid(instance) -> int:
    a, b = instance
    while b:
        a, b = b, a % b
    return a
