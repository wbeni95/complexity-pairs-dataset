"""Naive OR convolution (covering product): h[S] = sum over all pairs (A, B) with A | B = S of f[A] * g[B].

Every one of the N^2 = 4^n index pairs contributes once: exactly 4^n multiplications and 4^n additions.
"""


def or_convolution_naive(instance):
    f, g = instance
    size = len(f)
    h = [0] * size
    for a in range(size):
        fa = f[a]
        for b in range(size):
            s = a | b
            h[s] = h[s] + fa * g[b]
    return h
