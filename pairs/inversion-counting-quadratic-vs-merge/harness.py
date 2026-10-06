"""Instances: n integers drawn from [0, n] (duplicates occur, and equal values are not inversions)."""


def generate(n, rng):
    return tuple(rng.randint(0, n) for _ in range(n))


def check(values, output):
    """Independent oracle: a Fenwick (binary indexed) tree over value ranks, Theta(n log n)."""
    ranks = {v: i + 1 for i, v in enumerate(sorted(set(values)))}
    tree = [0] * (len(ranks) + 1)
    count = 0
    for seen, v in enumerate(values):
        r = ranks[v]
        le, i = 0, r          # number of earlier elements <= v
        while i > 0:
            le += tree[i]
            i -= i & -i
        count += seen - le    # earlier elements > v
        i = r
        while i < len(tree):
            tree[i] += 1
            i += i & -i
    return output == count
