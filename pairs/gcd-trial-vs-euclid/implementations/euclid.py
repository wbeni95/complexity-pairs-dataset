"""Euclid's algorithm: gcd(a, b) = gcd(b, a mod b), gcd(a, 0) = a.

At most log_phi(min(a, b)) + 2 < 1.4405 n + 2 division steps if min(a, b) >= 1 (after Lame 1844); consecutive
Fibonacci numbers are the worst case. Proofs: ../PROOFS.md, section 5.
"""


def gcd_euclid(instance) -> int:
    a, b = instance
    while b:
        a, b = b, a % b
    return a
