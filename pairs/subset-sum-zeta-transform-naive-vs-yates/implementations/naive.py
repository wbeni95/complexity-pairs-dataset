"""Zeta transform (sums over subsets) by enumerating the submasks of every set.

zeta[S] = sum of f[T] over all T subset of S. Set S has 2^|S| subsets, and sum over S of 2^|S| = 3^n,
so this performs exactly 3^n additions (the running sum starts at 0).
"""


def zeta_naive(f):
    size = len(f)
    out = [0] * size
    for s in range(size):
        acc = 0
        t = s
        while True:            # enumerate all submasks t of s, from s down to 0
            acc = acc + f[t]
            if t == 0:
                break
            t = (t - 1) & s
        out[s] = acc
    return out
