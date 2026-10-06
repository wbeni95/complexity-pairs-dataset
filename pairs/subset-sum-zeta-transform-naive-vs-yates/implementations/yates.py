"""Fast zeta transform (Yates' method): one pass per element, n * 2^(n-1) additions.

Invariant: after the passes for bits 0..i-1, g[S] = sum of f[T] over the subsets T of S that agree with S on
every bit >= i. The pass for bit i adds g[S without i] into g[S] for every S containing i, which extends the
invariant to bit i. After all n passes, g[S] = sum over all subsets T of S.
"""


def zeta_yates(f):
    g = list(f)
    size = len(g)
    bit = 1
    while bit < size:
        for s in range(size):
            if s & bit:
                g[s] = g[s] + g[s ^ bit]
        bit <<= 1
    return g
