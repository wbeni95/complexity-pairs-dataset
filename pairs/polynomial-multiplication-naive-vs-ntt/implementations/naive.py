"""Schoolbook polynomial multiplication over Z_p: Theta(n^2) coefficient multiplications."""

P = 998244353


def polymul_naive(instance):
    A, B = instance
    if not A or not B:
        return []
    C = [0] * (len(A) + len(B) - 1)
    for i, a in enumerate(A):
        if a:
            for j, b in enumerate(B):
                C[i + j] = (C[i + j] + a * b) % P
    return C
