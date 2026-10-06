"""Schoolbook matrix multiplication: Theta(n^3) scalar multiplications."""


def matmul_naive(instance):
    A, B = instance
    n = len(A)
    Bt = list(zip(*B))  # columns of B
    return [[sum(A[i][k] * Bt[j][k] for k in range(n)) for j in range(n)] for i in range(n)]
