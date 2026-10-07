"""Trial divisors: try d = min(a, b), min(a, b) - 1, ... until d divides both.

For a, b >= 1 it runs min(a, b) - gcd(a, b) + 1 iterations, so min(a, b) of them on coprime inputs: Theta(2^n)
in the worst case for n-bit inputs; none if a = 0 or b = 0. Proofs: ../PROOFS.md.
"""


def gcd_trial(instance) -> int:
    a, b = instance
    if a == 0 or b == 0:
        return a + b              # gcd(a, 0) = a, and gcd(0, 0) = 0 by convention
    d = min(a, b)
    while a % d or b % d:         # d = 1 always succeeds, so the loop terminates
        d -= 1
    return d
