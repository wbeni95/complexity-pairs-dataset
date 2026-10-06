"""Instances: two polynomials of n coefficients each, uniform in Z_p, p = 998244353."""

P = 998244353


def generate(n, rng):
    return (tuple(rng.randrange(P) for _ in range(n)), tuple(rng.randrange(P) for _ in range(n)))


def check(instance, output):
    """Independent spot check: A(x) * B(x) == C(x) mod p at a few fixed points (Horner evaluation)."""
    A, B = instance
    if not A or not B:
        return output == []
    if len(output) != len(A) + len(B) - 1:
        return False

    def ev(poly, x):
        acc = 0
        for c in reversed(poly):
            acc = (acc * x + c) % P
        return acc

    return all(ev(A, x) * ev(B, x) % P == ev(output, x) for x in (2, 12345, P - 7))
