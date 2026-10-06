"""Instances: two random n x n integer matrices with entries in [-9, 9]."""


def generate(n, rng):
    def mat():
        return tuple(tuple(rng.randint(-9, 9) for _ in range(n)) for _ in range(n))
    return mat(), mat()


def check(instance, output):
    """Freivalds-style spot check: A(Bx) == Cx for a random 0/1 vector x (independent of both algorithms)."""
    import random
    A, B = instance
    n = len(A)
    if n == 0:
        return output == []
    x = [random.Random(n).randint(0, 1) for _ in range(n)]
    Bx = [sum(B[i][j] * x[j] for j in range(n)) for i in range(n)]
    ABx = [sum(A[i][j] * Bx[j] for j in range(n)) for i in range(n)]
    Cx = [sum(output[i][j] * x[j] for j in range(n)) for i in range(n)]
    return ABx == Cx
