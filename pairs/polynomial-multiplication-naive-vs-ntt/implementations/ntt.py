"""Polynomial multiplication via the number-theoretic transform (an FFT over Z_p): Theta(n log n).

p = 998244353 = 119 * 2^23 + 1 has a primitive root 3, so Z_p contains 2^k-th roots of unity for every
k <= 23. Evaluate both polynomials at the 2^k-th roots of unity (iterative radix-2 Cooley-Tukey),
multiply pointwise, and interpolate with the inverse transform.
"""

P = 998244353
G = 3


def polymul_ntt(instance):
    A, B = instance
    if not A or not B:
        return []
    out_len = len(A) + len(B) - 1
    size = 1
    while size < out_len:
        size *= 2
    fa = list(A) + [0] * (size - len(A))
    fb = list(B) + [0] * (size - len(B))
    _ntt(fa, invert=False)
    _ntt(fb, invert=False)
    fc = [x * y % P for x, y in zip(fa, fb)]
    _ntt(fc, invert=True)
    return fc[:out_len]


def _ntt(a, invert):
    n = len(a)
    # bit-reversal permutation
    j = 0
    for i in range(1, n):
        bit = n >> 1
        while j & bit:
            j ^= bit
            bit >>= 1
        j |= bit
        if i < j:
            a[i], a[j] = a[j], a[i]
    length = 2
    while length <= n:
        w_len = pow(G, (P - 1) // length, P)
        if invert:
            w_len = pow(w_len, P - 2, P)
        half = length // 2
        for start in range(0, n, length):
            w = 1
            for k in range(start, start + half):
                u = a[k]
                v = a[k + half] * w % P
                a[k] = (u + v) % P
                a[k + half] = (u - v) % P
                w = w * w_len % P
        length *= 2
    if invert:
        n_inv = pow(n, P - 2, P)
        for i in range(n):
            a[i] = a[i] * n_inv % P
