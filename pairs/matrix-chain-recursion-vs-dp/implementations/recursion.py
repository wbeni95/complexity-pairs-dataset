"""Plain recursion over the split point, no memoisation.

T(n) = sum_{k=1}^{n-1} (T(k) + T(n-k)) + Theta(n) gives T(n) = 3 T(n-1) + Theta(1) = Theta(3^n).
"""


def matrix_chain_recursive(dims) -> int:
    def cost(i, j):  # matrices i..j inclusive; matrix k has shape dims[k] x dims[k+1]
        if i == j:
            return 0
        return min(cost(i, k) + cost(k + 1, j) + dims[i] * dims[k + 1] * dims[j + 1]
                   for k in range(i, j))

    n = len(dims) - 1
    return cost(0, n - 1) if n >= 1 else 0
