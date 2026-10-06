"""Instances: bipartite graphs (n_left, n_right, adj), adj[u] = tuple of right neighbours of left vertex u.
The size parameter n is the total number of vertices V = n_left + n_right.

generate() mixes: random bipartite graphs with several densities and unbalanced sides; complete bipartite
graphs K_{s,t}; a random perfect matching plus noise edges; graphs with isolated vertices; and members of
the adversarial family below (when n has the form 4k^2 + k).

generate_scaling() returns the adversarial family G_k, with n = V = 4k^2 + k (n must have this form):
  * a dense gadget K_{2a,a}, a = k^2: left vertices 0..2a-1, right vertices 0..a-1, every adjacency list in
    the order 0..a-1. Only a of the 2a left vertices can be matched, so each of the a failing Kuhn searches
    explores the whole gadget, Theta(a^2) edges each: Theta(a^3) = Theta(V E) in total. Hopcroft-Karp's BFS and
    DFS also scan the whole gadget in every phase, because its a free left vertices are roots of every phase.
  * paths P_2, P_4, ..., P_2k: path j has left vertices L_1..L_j and right vertices R_1..R_j, edges L_i-R_i and
    L_(i+1)-R_i. The left vertices are numbered L_2, ..., L_j, L_1 and adj[L_i] = (R_(i-1), R_i), so the first
    Hopcroft-Karp phase (which matches free left vertices to the first free neighbour, in index order) picks
    L_(i+1)-R_i and leaves L_1 and R_j free. Path j then needs one augmenting path of length 2j - 1, and phase j
    repairs only path j: k + 1 phases in all, each scanning the gadget's Theta(a^2) = Theta(E) edges, for
    Theta(k E) = Theta(E sqrt(V)) time.
experiments/2026-10-07_bipartite_matching_counts.py verifies the phase count and edge-scan counts.

The oracle is algebraic and independent of augmenting paths: the rank, over GF(p) with p = 2^61 - 1, of the
n_left x n_right Edmonds matrix with an independent uniformly random entry for each edge (0 elsewhere). The
rank of the matrix of indeterminates equals the maximum matching size (a k x k minor is a non-zero
polynomial iff the corresponding vertex sets have a perfect matching), and by the Schwartz-Zippel lemma a
random substitution lowers the rank with probability at most k / p < 10^-15 here. The oracle's random
generator is seeded from the instance, so it is deterministic. It returns None above 160 vertices per side.
"""
import math
import random

P = (1 << 61) - 1


def adversarial_k(n):
    k = (math.isqrt(1 + 16 * n) - 1) // 8
    return k if k >= 1 and 4 * k * k + k == n else None


def adversarial(k):
    a = k * k
    adj = [tuple(range(a)) for _ in range(2 * a)]
    n_right = a
    for j in range(1, k + 1):
        R = list(range(n_right, n_right + j))       # R_1..R_j
        n_right += j
        for i in range(2, j + 1):                   # L_2..L_j first
            adj.append((R[i - 2], R[i - 1]))
        adj.append((R[0],))                         # then L_1
    return len(adj), n_right, tuple(adj)


def _random_bipartite(n_left, n_right, p, rng):
    return n_left, n_right, tuple(
        tuple(v for v in range(n_right) if rng.random() < p) for _ in range(n_left))


def generate(n, rng):
    kind = rng.randrange(6)
    k = adversarial_k(n)
    if kind == 5 and k is not None:
        return adversarial(k)
    n_left = rng.randint(0, n) if kind == 1 else n // 2
    n_right = n - n_left
    if kind in (0, 1, 5):
        p = rng.choice((0.05, 0.15, 0.4, 0.8))
        return _random_bipartite(n_left, n_right, p, rng)
    if kind == 2:
        return n_left, n_right, tuple(tuple(range(n_right)) for _ in range(n_left))
    if kind == 3:
        perm = list(range(n_right))
        rng.shuffle(perm)
        adj = []
        for u in range(n_left):
            nb = {v for v in range(n_right) if rng.random() < 0.05}
            if u < n_right:
                nb.add(perm[u])
            nb = list(nb)
            rng.shuffle(nb)
            adj.append(tuple(nb))
        return n_left, n_right, tuple(adj)
    # kind 4: a third of the left vertices isolated, the rest sparse
    return n_left, n_right, tuple(
        () if rng.random() < 1 / 3 else tuple(v for v in range(n_right) if rng.random() < 0.1)
        for _ in range(n_left))


def generate_scaling(n, rng):
    k = adversarial_k(n)
    if k is None:
        raise ValueError(f"n = {n} is not of the form 4k^2 + k")
    return adversarial(k)


def _edmonds_rank(n_left, n_right, adj, rng):
    M = [[0] * n_right for _ in range(n_left)]
    for u in range(n_left):
        for v in adj[u]:
            M[u][v] = rng.randrange(1, P)
    rank = 0
    for col in range(n_right):
        pivot = next((r for r in range(rank, n_left) if M[r][col]), None)
        if pivot is None:
            continue
        M[rank], M[pivot] = M[pivot], M[rank]
        inv = pow(M[rank][col], P - 2, P)
        prow = M[rank]
        for r in range(rank + 1, n_left):
            f = M[r][col]
            if f:
                f = f * inv % P
                row = M[r]
                for c in range(col, n_right):
                    if prow[c]:
                        row[c] = (row[c] - f * prow[c]) % P
        rank += 1
    return rank


def check(graph, output):
    n_left, n_right, adj = graph
    if max(n_left, n_right) > 160:
        return None
    rng = random.Random(repr(graph))
    return output == _edmonds_rank(n_left, n_right, adj, rng)
