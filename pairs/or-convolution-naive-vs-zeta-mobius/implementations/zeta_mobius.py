"""OR convolution (covering product) by the zeta and Moebius transforms over the subset lattice.

zeta[S] = sum of f[T] over T subset of S. For h = f (OR-conv) g:
    zeta_h[S] = sum over T subset of S of sum over A | B = T of f[A] g[B]
              = sum over A subset of S and B subset of S of f[A] g[B]  = zeta_f[S] * zeta_g[S],
because A | B is a subset of S iff both A and B are. The Moebius transform (sums with signs (-1)^(|S| - |T|) over T subset of S) inverts
zeta, so h = moebius(zeta_f . zeta_g) (Bjorklund, Husfeldt, Kaski & Koivisto 2007, 'covering product').

Both transforms use Yates' method: one pass per element i, updating every set S that contains i from S without i
(n * 2^(n-1) additions for zeta, the same number of subtractions for Moebius). In total: two zeta transforms, 2^n
pointwise multiplications and one Moebius transform, i.e. 3 n 2^(n-1) + 2^n = (3n + 2) 2^(n-1) ring operations.
"""


def _zeta(values):
    g = list(values)
    size = len(g)
    bit = 1
    while bit < size:
        for s in range(size):
            if s & bit:
                g[s] = g[s] + g[s ^ bit]
        bit <<= 1
    return g


def _moebius(values):
    g = list(values)
    size = len(g)
    bit = 1
    while bit < size:
        for s in range(size):
            if s & bit:
                g[s] = g[s] - g[s ^ bit]
        bit <<= 1
    return g


def or_convolution_zeta_mobius(instance):
    f, g = instance
    zf = _zeta(f)
    zg = _zeta(g)
    return _moebius([x * y for x, y in zip(zf, zg)])
