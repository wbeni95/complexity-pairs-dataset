"""Boolean matrix multiplication via integer Strassen.

Read the 0/1 entries as integers and compute the integer product P = AB with Strassen's algorithm (1969). Then
P[i][j] = number of k with A[i][k] = B[k][j] = 1, so the Boolean product is C[i][j] = 1 iff P[i][j] > 0.
Strassen needs subtraction, which the Boolean semiring ({0,1}, OR, AND) does not have; embedding into the ring of
integers supplies it. All entries of P lie in [0, n]. Intermediate values are bounded in absolute value by a
polynomial in n (each of the log2(n/16) recursion levels at most doubles the entries of the operands passed down,
and the four-term combinations at most quadruple the results passed up), so all integers have O(log n) bits.

Matrices are zero-padded to a power of two. Below CUTOFF the recursion switches to the schoolbook method; the
cutoff changes constant factors only, not the exponent: Theta(n^(log2 7)) multiplications, exactly
7^(log2(n/16)) * 16^3 for n a power of two >= 16.
"""

CUTOFF = 16


def bmm_strassen(instance):
    A, B = instance
    n = len(A)
    if n == 0:
        return []
    size = 1
    while size < n:
        size *= 2
    P = _strassen(_pad(A, size), _pad(B, size))
    return [[1 if P[i][j] > 0 else 0 for j in range(n)] for i in range(n)]


def _pad(M, size):
    n = len(M)
    return [list(M[i]) + [0] * (size - n) for i in range(n)] + [[0] * size for _ in range(size - n)]


def _add(X, Y):
    return [[x + y for x, y in zip(rx, ry)] for rx, ry in zip(X, Y)]


def _sub(X, Y):
    return [[x - y for x, y in zip(rx, ry)] for rx, ry in zip(X, Y)]


def _naive(X, Y):
    Yt = list(zip(*Y))
    return [[sum(a * b for a, b in zip(row, col)) for col in Yt] for row in X]


def _strassen(X, Y):
    n = len(X)
    if n <= CUTOFF:
        return _naive(X, Y)
    h = n // 2
    A11 = [r[:h] for r in X[:h]]
    A12 = [r[h:] for r in X[:h]]
    A21 = [r[:h] for r in X[h:]]
    A22 = [r[h:] for r in X[h:]]
    B11 = [r[:h] for r in Y[:h]]
    B12 = [r[h:] for r in Y[:h]]
    B21 = [r[:h] for r in Y[h:]]
    B22 = [r[h:] for r in Y[h:]]

    M1 = _strassen(_add(A11, A22), _add(B11, B22))
    M2 = _strassen(_add(A21, A22), B11)
    M3 = _strassen(A11, _sub(B12, B22))
    M4 = _strassen(A22, _sub(B21, B11))
    M5 = _strassen(_add(A11, A12), B22)
    M6 = _strassen(_sub(A21, A11), _add(B11, B12))
    M7 = _strassen(_sub(A12, A22), _add(B21, B22))

    C11 = _add(_sub(_add(M1, M4), M5), M7)
    C12 = _add(M3, M5)
    C21 = _add(M2, M4)
    C22 = _add(_add(_sub(M1, M2), M3), M6)
    return [l + r for l, r in zip(C11, C12)] + [l + r for l, r in zip(C21, C22)]
