"""Sorting networks: an exact verifier (0-1 principle) and a small randomized search, as a second, cheap
validation target for the search pipeline. Fixed-size results only (START_HERE section 1; notes/constant-factor-
alphadev.md): a network for a fixed n is O(1), so nothing found here is a dataset pair.

A network is a list of comparators (i, j), i < j; a comparator puts the minimum on wire i and the maximum on j.

Verifier. By the 0-1 principle (Knuth, TAOCP Vol. 3, Section 5.3.4), a comparator network sorts every input iff
it sorts every 0-1 input. All 2^n 0-1 inputs are processed at once: wire w holds an int whose bit t is the
value of wire w on input t; a comparator is (w_i, w_j) <- (w_i AND w_j, w_i OR w_j). The output is sorted iff no
input has a 1 on wire i and a 0 on wire i+1, i.e. w_i AND NOT w_{i+1} == 0 for all i.
`sorts_permutations` is an independent check on all n! permutations (feasible for n <= 8).

Search. Repeated randomized greedy construction followed by pruning:
  * construct: while the network does not sort, append a comparator chosen to minimise the number of distinct
    0-1 output vectors (random tie-breaking; with probability `explore` a random useful comparator instead);
  * prune: try deleting each comparator (random order); keep the deletion if the network still sorts;
  * keep the smallest network over `tries` constructions.
"""
from __future__ import annotations

import random
from itertools import permutations


def initial_wires(n: int) -> list[int]:
    N = 1 << n
    wires = []
    for w in range(n):
        x = 0
        for t in range(N):
            if (t >> w) & 1:
                x |= 1 << t
        wires.append(x)
    return wires


def apply(wires: list[int], network) -> list[int]:
    w = list(wires)
    for i, j in network:
        a, b = w[i], w[j]
        w[i], w[j] = a & b, a | b
    return w


def is_sorted_wires(w: list[int]) -> bool:
    return all(w[i] & ~w[i + 1] == 0 for i in range(len(w) - 1))


def check_network(n: int, network) -> None:
    for c in network:
        if len(c) != 2 or not (0 <= c[0] < c[1] < n):
            raise ValueError(f"bad comparator {c!r} for n = {n}")


def sorts(n: int, network) -> bool:
    """Exact verifier via the 0-1 principle."""
    check_network(n, network)
    return is_sorted_wires(apply(initial_wires(n), network))


def sorts_permutations(n: int, network) -> bool:
    """Independent exact check on all n! permutations of 0..n-1."""
    check_network(n, network)
    target = list(range(n))
    for perm in permutations(range(n)):
        v = list(perm)
        for i, j in network:
            if v[i] > v[j]:
                v[i], v[j] = v[j], v[i]
        if v != target:
            return False
    return True


def distinct_outputs(w: list[int], n: int) -> int:
    N = 1 << n
    seen = set()
    for t in range(N):
        key = 0
        for idx in range(n):
            key = (key << 1) | ((w[idx] >> t) & 1)
        seen.add(key)
    return len(seen)


def prune(n: int, network, rng: random.Random):
    net = list(network)
    order = list(range(len(net)))
    rng.shuffle(order)
    removed = set()
    for idx in order:
        trial = [c for k, c in enumerate(net) if k not in removed and k != idx]
        if sorts(n, trial):
            removed.add(idx)
    return [c for k, c in enumerate(net) if k not in removed]


def construct(n: int, rng: random.Random, explore: float = 0.1):
    comps = [(i, j) for i in range(n) for j in range(i + 1, n)]
    w = initial_wires(n)
    net = []
    while not is_sorted_wires(w):
        useful = [(i, j) for i, j in comps if w[i] & ~w[j]]   # some input has 1 on i and 0 on j
        if rng.random() < explore:
            c = useful[rng.randrange(len(useful))]
        else:
            best, cands = None, []
            for i, j in useful:
                w2 = list(w)
                w2[i], w2[j] = w[i] & w[j], w[i] | w[j]
                d = distinct_outputs(w2, n)
                if best is None or d < best:
                    best, cands = d, [(i, j)]
                elif d == best:
                    cands.append((i, j))
            c = cands[rng.randrange(len(cands))]
        i, j = c
        w[i], w[j] = w[i] & w[j], w[i] | w[j]
        net.append(c)
    return net


def search(n: int, seed: int, tries: int, explore: float = 0.1):
    """Return (smallest network found, stats)."""
    rng = random.Random(seed)
    best = None
    sizes = []
    first_best_try = None
    for k in range(tries):
        net = prune(n, construct(n, rng, explore), rng)
        sizes.append(len(net))
        if best is None or len(net) < len(best):
            best = net
            first_best_try = k + 1
    if best is None:
        best = []
    return best, {"tries": tries, "best_size": len(best), "first_reached_at_try": first_best_try,
                  "min": min(sizes) if sizes else 0, "max": max(sizes) if sizes else 0}
