"""Instances: flow networks (n, s, t, edges), vertices 0..n-1 (n >= 2), s != t, edges a tuple of (u, v, c) with
u != v and integer capacity c >= 0.

generate() mixes: random digraphs of density 0.15, 0.4 or 1.0 with capacities from [1, 100], [1, 3] or
{1}; the same with some zero capacities and parallel / antiparallel edges added; layered networks
(s -> layer 1 -> ... -> layer L -> t, random edges between consecutive layers plus a few backward edges);
and networks in which t is unreachable (flow 0). s and t are random distinct vertices.

generate_scaling() returns random dense digraphs G(n, 0.5) with capacities from [1, 100], s = 0, t = n - 1.
Both implementations run in O(n^3) time on every instance (PROOFS.md, section 6(d)), so along its instances
Dinic's O(V^2 E) is not attained as V -> infinity and Edmonds-Karp's O(V E^2) not as E -> infinity (see
entry.json: the entry stays at V1). PROOFS.md,
section 10 proves a separation between the two on this family (with probability at least 1 - 5/n for every
n >= 21793, under an ideal-random-bits assumption).

The oracle is independent of both implementations: for n <= 14 it enumerates every s-t cut (all vertex
sets containing s and not t) and compares the output with the minimum cut capacity (max-flow min-cut
theorem). For larger n it can only reject outputs outside [0, min(capacity out of s, capacity into t)]
and returns None otherwise.
"""


def _random_network(n, rng, density, caps, extras=False):
    edges = []
    for u in range(n):
        for v in range(n):
            if u != v and rng.random() < density:
                edges.append((u, v, rng.choice(caps)))
    if extras:
        for _ in range(n):
            u, v = rng.sample(range(n), 2)
            edges.append((u, v, rng.choice((0, 0, 1, 5))))     # zero capacities and parallel edges
            edges.append((v, u, rng.randint(0, 3)))            # antiparallel edges
    return edges


def generate(n, rng):
    if n < 2:
        raise ValueError("a flow network needs n >= 2 (s != t)")
    s, t = rng.sample(range(n), 2)
    kind = rng.randrange(5)
    caps = rng.choice((tuple(range(1, 101)), (1, 2, 3), (1,)))
    if kind <= 1:
        edges = _random_network(n, rng, rng.choice((0.15, 0.4, 1.0)), caps, extras=(kind == 1))
    elif kind == 2:
        others = [v for v in range(n) if v not in (s, t)]
        rng.shuffle(others)
        L = max(1, min(len(others), rng.randint(1, 4)))
        layers = [[s]] + [others[i::L] for i in range(L)] + [[t]]
        layers = [layer for layer in layers if layer]
        edges = []
        for a, b in zip(layers, layers[1:]):
            for u in a:
                for v in b:
                    if rng.random() < 0.6:
                        edges.append((u, v, rng.choice(caps)))
        for _ in range(n // 2):
            u, v = rng.sample(range(n), 2)
            edges.append((u, v, rng.choice(caps)))
    elif kind == 3:
        edges = [e for e in _random_network(n, rng, 0.4, caps) if e[1] != t]   # t unreachable
    else:
        edges = _random_network(n, rng, 0.25, caps)
    return n, s, t, tuple(edges)


def generate_scaling(n, rng):
    edges = tuple((u, v, rng.randint(1, 100)) for u in range(n) for v in range(n)
                  if u != v and rng.random() < 0.5)
    return n, 0, n - 1, edges


def _min_cut_brute(n, s, t, edges):
    others = [v for v in range(n) if v not in (s, t)]
    best = None
    for mask in range(1 << len(others)):
        side = 1 << s
        for i, v in enumerate(others):
            if mask >> i & 1:
                side |= 1 << v
        cut = sum(c for u, v, c in edges if side >> u & 1 and not side >> v & 1)
        if best is None or cut < best:
            best = cut
    return best


def check(network, output):
    n, s, t, edges = network
    upper = min(sum(c for u, v, c in edges if u == s), sum(c for u, v, c in edges if v == t))
    if not 0 <= output <= upper:
        return False
    if n <= 14:
        return output == _min_cut_brute(n, s, t, edges)
    return None
