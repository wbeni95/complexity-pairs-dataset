"""XOR convolution by the fast Walsh-Hadamard transform (FWHT), exactly over the integers.

W is the 2^n x 2^n matrix W[x][y] = (-1)^popcount(x & y). The convolution theorem for the group (Z_2)^n says
W(a * b) = (W a) . (W b) pointwise, and W W = N I with N = 2^n. Hence h = W((W a) . (W b)) / N.

The FWHT applies W in n stages; stage s combines the entries whose indices differ only in bit s with one
butterfly (u, v) -> (u + v, u - v). Per transform: n * 2^(n-1) butterflies = n * 2^n additions/subtractions.
In total: three transforms (3 n 2^n additions/subtractions), 2^n pointwise multiplications and 2^n exact
divisions by N, i.e. (3n + 2) 2^n ring operations.
"""


def _fwht(values):
    """Return W @ values (unnormalised Walsh-Hadamard transform) as a new list."""
    a = list(values)
    size = len(a)
    half = 1
    while half < size:
        for start in range(0, size, 2 * half):
            for i in range(start, start + half):
                u, v = a[i], a[i + half]
                a[i] = u + v
                a[i + half] = u - v
        half *= 2
    return a


def xor_convolution_fwht(instance):
    a, b = instance
    size = len(a)
    fa = _fwht(a)
    fb = _fwht(b)
    prod = [x * y for x, y in zip(fa, fb)]
    h = _fwht(prod)
    # W W = N I, so every entry of h is divisible by N: the division is exact.
    return [x // size for x in h]
