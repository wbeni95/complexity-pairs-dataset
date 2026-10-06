"""Naive XOR convolution: h[k] = sum over all pairs (i, j) with i XOR j = k of a[i] * b[j].

Every one of the N^2 = 4^n index pairs contributes once: exactly 4^n multiplications and 4^n additions.
"""


def xor_convolution_naive(instance):
    a, b = instance
    size = len(a)
    h = [0] * size
    for i in range(size):
        ai = a[i]
        for j in range(size):
            h[i ^ j] += ai * b[j]
    return h
