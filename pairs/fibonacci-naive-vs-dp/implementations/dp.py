"""Bottom-up dynamic programming: keep the last two values, Theta(n) steps."""

MASK = (1 << 64) - 1


def fib_dp(n: int) -> int:
    a, b = 0, 1
    for _ in range(n):
        a, b = b, (a + b) & MASK
    return a
