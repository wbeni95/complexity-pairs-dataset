"""Bottom-up DP over chain length: Theta(n^3) time, Theta(n^2) space."""


def matrix_chain_dp(dims) -> int:
    n = len(dims) - 1
    if n < 1:
        return 0
    m = [[0] * n for _ in range(n)]
    for length in range(2, n + 1):
        for i in range(n - length + 1):
            j = i + length - 1
            m[i][j] = min(m[i][k] + m[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]
                          for k in range(i, j))
    return m[0][n - 1]
