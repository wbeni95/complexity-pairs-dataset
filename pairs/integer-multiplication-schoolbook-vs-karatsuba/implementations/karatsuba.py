"""Karatsuba multiplication of digit lists: Theta(n^log2(3)) ~ Theta(n^1.585) digit operations.

Numbers are little-endian lists of base-2^15 digits. Split x = x0 + x1*B^m and y = y0 + y1*B^m.
Then
    x*y = z0 + (x0*y1 + x1*y0)*B^m + z2*B^(2m),  z0 = x0*y0,  z2 = x1*y1,
    x0*y1 + x1*y0 = z0 + z2 - (x1 - x0)*(y1 - y0),
so three half-size products replace four. This is the "subtractive" form of Karatsuba's identity
(Knuth, TAOCP Vol. 2, 4.3.3): |x1 - x0| has no carry digit, so all three sub-products have the same
size and T(n) = 3 T(n/2) + Theta(n).

Below CUTOFF digits the recursion switches to schoolbook multiplication; the cutoff changes constant
factors only, not the exponent.
"""

BITS = 15
BASE = 1 << BITS
MASK = BASE - 1
CUTOFF = 32


def multiply_karatsuba(instance):
    """Return the product of two equal-length digit lists as a list of 2n digits (high digits may be 0)."""
    a, b = instance
    if len(a) != len(b):
        raise ValueError("both factors must have the same number of digits")
    if not a:
        return []
    return _karatsuba(list(a), list(b))


def _karatsuba(x, y):
    """x, y: digit lists of equal length L. Returns x*y as a list of exactly 2L digits."""
    L = len(x)
    if L <= CUTOFF:
        return _schoolbook(x, y)
    m = L // 2          # low halves have m digits
    h = L - m           # high halves have h digits (h = m or m + 1)
    x0, x1 = x[:m] + [0] * (h - m), x[m:]
    y0, y1 = y[:m] + [0] * (h - m), y[m:]

    z0 = _karatsuba(x0, y0)              # 2h digits
    z2 = _karatsuba(x1, y1)              # 2h digits
    dx, sx = _abs_diff(x1, x0)           # |x1 - x0|, sign
    dy, sy = _abs_diff(y1, y0)
    z1 = _karatsuba(dx, dy)              # |(x1 - x0)(y1 - y0)|

    mid = [0] * (2 * h + 1)              # mid = z0 + z2 - (x1 - x0)(y1 - y0) = x0*y1 + x1*y0 >= 0
    _add_at(mid, z0, 0)
    _add_at(mid, z2, 0)
    if sx * sy > 0:
        _sub_at(mid, z1, 0)
    else:
        _add_at(mid, z1, 0)

    res = [0] * (2 * L)                  # all three parts are >= 0, so partial sums never exceed x*y
    _add_at(res, z0, 0)
    _add_at(res, z2, 2 * m)
    _add_at(res, mid, m)
    return res


def _schoolbook(x, y):
    res = [0] * (len(x) + len(y))
    for i, xi in enumerate(x):
        carry = 0
        k = i
        for yj in y:
            t = res[k] + xi * yj + carry
            res[k] = t & MASK
            carry = t >> BITS
            k += 1
        res[k] = carry
    return res


def _abs_diff(a, b):
    """For equal-length digit lists, return (|a - b| as a digit list, sign of a - b)."""
    for i in range(len(a) - 1, -1, -1):
        if a[i] != b[i]:
            break
    else:
        return [0] * len(a), 0
    if a[i] < b[i]:
        a, b, sign = b, a, -1
    else:
        sign = 1
    out = list(a)
    _sub_at(out, b, 0)
    return out, sign


def _add_at(res, src, off):
    """res += src * BASE^off, in place (the caller guarantees the sum fits in len(res) digits)."""
    carry = 0
    k = off
    for d in src:
        t = res[k] + d + carry
        res[k] = t & MASK
        carry = t >> BITS
        k += 1
    while carry:
        t = res[k] + carry
        res[k] = t & MASK
        carry = t >> BITS
        k += 1


def _sub_at(res, src, off):
    """res -= src * BASE^off, in place; requires the result to be non-negative."""
    borrow = 0
    k = off
    for d in src:
        t = res[k] - d - borrow
        res[k] = t & MASK
        borrow = -(t >> BITS)  # t >= -BASE, so t >> BITS is 0 or -1
        k += 1
    while borrow:
        t = res[k] - borrow
        res[k] = t & MASK
        borrow = -(t >> BITS)
        k += 1
