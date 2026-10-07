"""Fast doubling: Theta(log n) word operations.

The bound assumes that bin(n) costs O(log n) (a machine-model assumption; see PROOFS.md).

Walks the bits of n from the top, maintaining (a, b) = (F(k), F(k+1)) and using
    F(2k)   = F(k) * (2 F(k+1) - F(k))
    F(2k+1) = F(k)^2 + F(k+1)^2
This is the matrix-power method [[1,1],[1,0]]^n with the redundant entries removed.
"""

MASK = (1 << 64) - 1


def fib_fast_doubling(n: int) -> int:
    a, b = 0, 1
    for bit in bin(n)[2:]:
        c = (a * ((2 * b - a) & MASK)) & MASK
        d = (a * a + b * b) & MASK
        if bit == "1":
            a, b = d, (c + d) & MASK
        else:
            a, b = c, d
    return a
