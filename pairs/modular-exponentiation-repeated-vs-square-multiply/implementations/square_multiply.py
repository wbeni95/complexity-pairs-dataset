"""Left-to-right binary exponentiation (square-and-multiply): Theta(n) modular multiplications.

Scans the bits of e from the most significant one. Invariant: after processing the top j bits of e
(value k), r = a^k mod m. Each further bit b turns k into 2k + b: square r, then multiply by a if b = 1.
"""


def modpow_square_multiply(instance) -> int:
    a, e, m = instance
    a %= m
    r = 1 % m
    for bit in bin(e)[2:]:          # bin() lists the bits of e, most significant first, in O(n)
        r = r * r % m
        if bit == "1":
            r = r * a % m
    return r
