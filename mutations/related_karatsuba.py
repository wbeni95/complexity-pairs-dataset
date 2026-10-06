"""Polynomial Karatsuba multiplication, written for the mutation pilot (a closely related problem: the repository's
Karatsuba entry multiplies integers with carries, which has no semiring reading). Coefficients are used only
through +, - and *, so injected element types decide the algebra. Base case: length 1 (no schoolbook cutoff), so
for n a power of two exactly 3^log2(n) = n^log2(3) coefficient multiplications are made.
"""


def polymul_karatsuba(instance):
    A, B = instance
    if not A or not B:
        return []
    n = 1
    while n < max(len(A), len(B)):
        n *= 2
    a = list(A) + [0] * (n - len(A))
    b = list(B) + [0] * (n - len(B))
    c = _kara(a, b)
    return c[:len(A) + len(B) - 1]


def _kara(a, b):
    n = len(a)
    if n == 1:
        return [a[0] * b[0]]
    h = n // 2
    a0, a1, b0, b1 = a[:h], a[h:], b[:h], b[h:]
    z0 = _kara(a0, b0)
    z2 = _kara(a1, b1)
    z1 = _kara([x + y for x, y in zip(a0, a1)], [x + y for x, y in zip(b0, b1)])
    mid = [z1[i] - z0[i] - z2[i] for i in range(len(z1))]
    out = [0] * (2 * n - 1)
    for i, v in enumerate(z0):
        out[i] = out[i] + v
    for i, v in enumerate(mid):
        out[i + h] = out[i + h] + v
    for i, v in enumerate(z2):
        out[i + 2 * h] = out[i + 2 * h] + v
    return out
