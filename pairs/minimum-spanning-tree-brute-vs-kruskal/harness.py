"""Instances: complete undirected graph on n vertices as a symmetric n x n weight matrix (diagonal 0).

generate uses integer weights in [1, 100] (many ties) or, in some trials, in [1, 3] (massive ties).
generate_scaling uses weights in [1, 10^9] (distinct with high probability), so sorting the edges
really costs Theta(m log m) comparisons.
"""


def _matrix(n, rng, hi):
    W = [[0] * n for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            W[u][v] = W[v][u] = rng.randint(1, hi)
    return tuple(tuple(row) for row in W)


def generate(n, rng):
    return _matrix(n, rng, 3 if rng.random() < 0.3 else 100)


def generate_scaling(n, rng):
    return _matrix(n, rng, 10 ** 9)


_cache = {}


def _boruvka(W):
    """MST weight by Boruvka's algorithm, independent of the implementations under test.
    Ties are broken by the total order (w, u, v), which makes the cheapest-edge choices consistent."""
    n = len(W)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    total, components = 0, n
    while components > 1:
        cheapest = {}
        for u in range(n):
            for v in range(u + 1, n):
                ru, rv = find(u), find(v)
                if ru != rv:
                    key = (W[u][v], u, v)
                    for r in (ru, rv):
                        if r not in cheapest or key < cheapest[r]:
                            cheapest[r] = key
        for w, u, v in set(cheapest.values()):
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[ru] = rv
                total += w
                components -= 1
    return total


def check(W, output):
    n = len(W)
    if n <= 1:
        return output == 0
    if W not in _cache:
        _cache[W] = _boruvka(W)
    path = sum(W[i][i + 1] for i in range(n - 1))           # the path 0-1-...-(n-1) is a spanning tree
    lightest = sum(sorted(W[u][v] for u in range(n) for v in range(u + 1, n))[:n - 1])
    return output == _cache[W] and lightest <= output <= path
