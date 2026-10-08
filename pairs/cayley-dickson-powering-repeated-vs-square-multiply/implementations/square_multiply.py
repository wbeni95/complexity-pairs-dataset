"""Left-to-right square-and-multiply in a Cayley-Dickson algebra over Z/pZ: floor(log2 e) + popcount(e) - 1
algebra products.

Instance (x, e, p) as in repeated.py. Starting from r = x for the leading bit of e, each further bit squares r and,
if the bit is 1, multiplies r by x.

Correctness rests on power-associativity (PROOFS.md, sections 3 and 5): every element computed lies in the
commutative, associative subalgebra span{1, x}, where r = x^k after the bits of value k have been read, r r = x^(2k)
and x^(2k) x = x^(2k+1). The algebra itself is not associative for dimension >= 8 (PROOFS.md, section 7), so this
needs a proof; it is not the textbook argument.
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


def cd_power_square_multiply(instance):
    x, e, p = instance
    x = tuple(v % p for v in x)
    r = x
    for bit in bin(e)[3:]:          # the bits of e after the leading 1, most significant first
        r = cd_mul(r, r, p)
        if bit == "1":
            r = cd_mul(r, x, p)
    return r
