"""Instances: simple undirected graphs (n, edges), vertices 0..n-1, edges a sorted tuple of pairs (u, v), u < v.

generate() mixes: G(n, p) random graphs with p in {0.2, 0.5, 0.8}; the empty graph (chi = 1 for n >= 1);
the complete graph (chi = n); the cycle C_n (chi = 3 for odd n >= 3, 2 for even n); a random bipartite
graph (chi <= 2); and a disjoint union of triangles plus leftover vertices.

generate_scaling() returns G(n, 0.8) random graphs. Their complements are sparse, so independent sets are
small; on the seeded instances chi/n lies between 0.50 and 5/7 for n = 6..18 (computed;
experiments/2026-10-07_chromatic_probe.py prints the values), so the inclusion-exclusion algorithm runs a number of
rounds proportional to n on them. The subset DP does
exactly 3^n - 2^n inner iterations on every graph.

The oracle is an exact backtracking k-colouring search, independent of both implementations: it checks
that the claimed chi colours suffice and that chi - 1 do not (n <= 14; larger instances return None).
"""
import itertools


def _random_graph(n, rng, p):
    return n, tuple((u, v) for u, v in itertools.combinations(range(n), 2) if rng.random() < p)


def generate(n, rng):
    kind = rng.randrange(8)
    if kind <= 2:
        return _random_graph(n, rng, (0.2, 0.5, 0.8)[kind])
    if kind == 3:
        return n, ()
    if kind == 4:
        return n, tuple(itertools.combinations(range(n), 2))
    if kind == 5:
        if n < 3:
            return _random_graph(n, rng, 0.5)
        return n, tuple(sorted((min(i, (i + 1) % n), max(i, (i + 1) % n)) for i in range(n)))
    if kind == 6:
        side = [rng.random() < 0.5 for _ in range(n)]
        return n, tuple((u, v) for u, v in itertools.combinations(range(n), 2)
                        if side[u] != side[v] and rng.random() < 0.6)
    perm = list(range(n))
    rng.shuffle(perm)
    edges = set()
    for t in range(n // 3):
        a, b, c = perm[3 * t:3 * t + 3]
        edges.update(tuple(sorted(e)) for e in ((a, b), (b, c), (a, c)))
    return n, tuple(sorted(edges))


def generate_scaling(n, rng):
    return _random_graph(n, rng, 0.8)


def _colourable(n, edges, k):
    """Backtracking: assign colours to vertices in order of decreasing degree; a vertex may only open
    the next unused colour (symmetry breaking)."""
    nbrs = [set() for _ in range(n)]
    for u, v in edges:
        nbrs[u].add(v)
        nbrs[v].add(u)
    order = sorted(range(n), key=lambda v: -len(nbrs[v]))
    colour = [-1] * n

    def place(i, used):
        if i == n:
            return True
        v = order[i]
        taken = {colour[w] for w in nbrs[v]}
        for c in range(min(k, used + 1)):
            if c not in taken:
                colour[v] = c
                if place(i + 1, max(used, c + 1)):
                    return True
                colour[v] = -1
        return False

    return place(0, 0)


def check(graph, output):
    n, edges = graph
    if n == 0:
        return output == 0
    if n > 14:
        return None
    if not 1 <= output <= n:
        return False
    return _colourable(n, edges, output) and not _colourable(n, edges, output - 1)
