"""Instances: (values, queries) with n values and q = n queries (l, r), 0 <= l <= r < n.

generate() draws values from [-1000, 1000] or, half of the time, from [0, 4] (many ties), and mixes query
kinds: uniformly random endpoints, single positions (l = r), short ranges (length <= 4) and whole-array or
prefix/suffix ranges.

generate_scaling() returns random values with q = n long queries: l uniform in [0, n/4), r uniform in
[3n/4, n), so every range has length > n/2 and the naive scan costs Theta(n^2) in total.

The oracle answers the queries with an iterative segment tree, O((n + q) log n): a different data
structure from both implementations under test.
"""


def _queries(n, rng, long_only=False):
    qs = []
    for _ in range(n):
        if long_only:
            l = rng.randrange(0, max(1, n // 4))
            r = rng.randrange(3 * n // 4, n)
        else:
            kind = rng.randrange(4)
            if kind == 0:
                l, r = sorted((rng.randrange(n), rng.randrange(n)))
            elif kind == 1:
                l = r = rng.randrange(n)
            elif kind == 2:
                l = rng.randrange(n)
                r = min(n - 1, l + rng.randrange(4))
            else:
                l, r = rng.choice(((0, n - 1), (0, rng.randrange(n)), (rng.randrange(n), n - 1)))
        qs.append((l, r))
    return tuple(qs)


def generate(n, rng):
    lo, hi = (-1000, 1000) if rng.random() < 0.5 else (0, 4)
    values = tuple(rng.randint(lo, hi) for _ in range(n))
    return values, _queries(n, rng)


def generate_scaling(n, rng):
    values = tuple(rng.randint(-10 ** 6, 10 ** 6) for _ in range(n))
    return values, _queries(n, rng, long_only=True)


def _segment_tree_answers(values, queries):
    n = len(values)
    size = 1
    while size < n:
        size *= 2
    inf = float("inf")
    tree = [inf] * (2 * size)
    tree[size:size + n] = values
    for i in range(size - 1, 0, -1):
        tree[i] = min(tree[2 * i], tree[2 * i + 1])
    out = []
    for l, r in queries:
        res = inf
        lo, hi = l + size, r + size + 1      # half-open [lo, hi) at the leaf level
        while lo < hi:
            if lo & 1:
                res = min(res, tree[lo])
                lo += 1
            if hi & 1:
                hi -= 1
                res = min(res, tree[hi])
            lo //= 2
            hi //= 2
        out.append(res)
    return tuple(out)


def check(instance, output):
    values, queries = instance
    return output == _segment_tree_answers(values, queries)
