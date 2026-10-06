"""Naive recursion straight from the definition: Theta(phi^n) calls."""

MASK = (1 << 64) - 1  # results are taken mod 2^64 (one machine word)


def fib_naive(n: int) -> int:
    if n < 2:
        return n
    return (fib_naive(n - 1) + fib_naive(n - 2)) & MASK
