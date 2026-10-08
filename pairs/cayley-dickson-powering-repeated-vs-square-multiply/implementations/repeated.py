"""Repeated multiplication in a Cayley-Dickson algebra over Z/pZ: exactly e - 1 algebra products.

Instance (x, e, p): x = tuple of 2^m residues mod the odd modulus p (coordinates in the standard basis, x[0] the real
part), e >= 1. Output: the left power x^e = (...((x x) x)...) x, as a tuple of residues.

The Cayley-Dickson product is defined recursively on pairs of halves:
    (a, b)(c, d) = (ac - conj(d) b,  d a + b conj(c)),   conj(a, b) = (conj(a), -b),
with the product of residues at the bottom. One product in dimension 2^m makes exactly 4^m multiplications of
residues (four half-size products per level).
"""


def cd_conj(x, p):
    if len(x) == 1:
        return x
    h = len(x) // 2
    return cd_conj(x[:h], p) + tuple((-v) % p for v in x[h:])


def cd_mul(x, y, p):
    if len(x) == 1:
        return (x[0] * y[0] % p,)
    h = len(x) // 2
    a, b, c, d = x[:h], x[h:], y[:h], y[h:]
    ac = cd_mul(a, c, p)
    db = cd_mul(cd_conj(d, p), b, p)
    da = cd_mul(d, a, p)
    bc = cd_mul(b, cd_conj(c, p), p)
    return tuple((u - v) % p for u, v in zip(ac, db)) + tuple((u + v) % p for u, v in zip(da, bc))


def cd_power_repeated(instance):
    x, e, p = instance
    x = tuple(v % p for v in x)
    r = x
    for _ in range(e - 1):
        r = cd_mul(r, x, p)
    return r
