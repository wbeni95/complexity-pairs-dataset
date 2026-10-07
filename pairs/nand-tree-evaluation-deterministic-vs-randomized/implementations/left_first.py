"""Deterministic left-first evaluation of a complete binary NAND tree with short-circuiting.

leaves is a sequence of N = 2^h bits; the tree's internal nodes compute NAND(x, y) = 1 - (x AND y). At each node
the left subtree is evaluated first; if it is 0, the node is 1 and the right subtree is skipped. Otherwise the
node is NAND(1, right) = 1 - right. On inputs where every node of value 1 has exactly one child of value 0, the right
one (the two right-zero reluctant inputs), all 2^h leaves are read, and no deterministic algorithm can do better in
the worst case (adversary argument, entry.json).
"""


def nand_tree_left_first(leaves):
    def evaluate(lo, size):
        if size == 1:
            return leaves[lo]
        half = size // 2
        if evaluate(lo, half) == 0:
            return 1
        return 1 - evaluate(lo + half, half)

    return evaluate(0, len(leaves))
