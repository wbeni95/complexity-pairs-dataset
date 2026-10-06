"""Instances: n x n matrices over GF(P), P = 2^31 - 1, as tuples of tuples of residues in [0, P).

generate builds A = (row permutation of) L * U mod P, where L is unit lower triangular and U is upper
triangular. Its determinant is therefore known in advance: sign(permutation) * prod(diag U). Entries of
L and U are 0 with probability 1/3 (so zero pivots and row swaps occur), and in about a quarter of the
instances one diagonal entry of U is 0 (singular matrix, determinant 0). The known determinant is
recorded per instance, which gives check an exact oracle independent of both implementations.

generate_scaling draws every entry uniformly from [0, P); such a matrix is non-singular with
probability ~1 - 1/P, so Gaussian elimination does its full Theta(n^3) work.
"""

P = 2 ** 31 - 1
_KNOWN = {}  # instance -> determinant mod P, filled by generate


def generate(n, rng):
    def entry():
        return 0 if rng.random() < 1 / 3 else rng.randrange(1, P)

    L = [[1 if i == j else (entry() if j < i else 0) for j in range(n)] for i in range(n)]
    U = [[(entry() if j > i else 0) for j in range(n)] for i in range(n)]
    for i in range(n):
        U[i][i] = rng.randrange(1, P)
    if n and rng.random() < 0.25:
        k = rng.randrange(n)
        U[k][k] = 0  # singular instance
    LU =[[sum(L[i][k] * U[k][j] for k in range(n)) % P for j in range(n)] for i in range(n)]
    perm = list(range(n))
    rng.shuffle(perm)
    A = tuple(tuple(LU[perm[i]]) for i in range(n))

    det = _sign(perm)
    for i in range(n):
        det = det * U[i][i] % P
    _KNOWN[A] = det % P
    return A


def generate_scaling(n, rng):
    return tuple(tuple(rng.randrange(P) for _ in range(n)) for _ in range(n))


def _sign(perm):
    """Sign of a permutation from its cycle decomposition."""
    seen = [False] * len(perm)
    sign = 1
    for i in range(len(perm)):
        if not seen[i]:
            j, length = i, 0
            while not seen[j]:
                seen[j] = True
                j = perm[j]
                length += 1
            if length % 2 == 0:
                sign = -sign
    return sign


def check(A, output):
    if A in _KNOWN:
        return output == _KNOWN[A]
    return None
