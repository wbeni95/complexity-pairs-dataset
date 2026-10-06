"""Randomized evaluation of a complete binary NAND tree (Snir's directional algorithm, as analysed by Saks and
Wigderson 1986): at every node, evaluate the two subtrees in a uniformly random order and short-circuit.

The answer is always correct (zero error, Las Vegas); only the number of leaves read is random. On the worst-case
("reluctant") inputs its expected number of leaf reads satisfies R0(h) = 2 R1(h-1), R1(h) = R0(h-1) + R1(h-1)/2
with R0(0) = R1(0) = 1, which grows like ((1 + sqrt(33)) / 4)^h ~ 1.686^h = N^0.7537 for N = 2^h leaves.
Uses the global `random` module (the validator seeds it before every call).
"""
import random


def nand_tree_random_order(leaves):
    def evaluate(lo, size):
        if size == 1:
            return leaves[lo]
        half = size // 2
        first, second = (lo, lo + half) if random.getrandbits(1) else (lo + half, lo)
        if evaluate(first, half) == 0:
            return 1
        return 1 - evaluate(second, half)

    return evaluate(0, len(leaves))
