"""Experiment: would the common early-exit optimisation of Bellman-Ford ("stop when a pass changes
nothing") still give Theta(n^4) for all-pairs shortest paths on the instances used for timing?

The entry's implementation makes exactly n - 1 passes per source. This script counts, for the
early-exit variant (same edge order: u ascending, then v ascending), the number of passes per source
(including the final pass that changes nothing) on
  (a) random complete digraphs with weights in [1, 1000]  (the entry's generate_scaling family), and
  (b) a "descending path" family: edges i -> i-1 of weight 1, every other edge of weight 10^6.
      From source s the shortest path to s-k uses k edges, and with u-ascending edge order each pass
      extends the settled prefix by only one edge, so early exit saves nothing.
Pass counts are deterministic (no timing).

Outcome (2026-10-07 run, output reproduced exactly on rerun):
  (a) mean passes per source 3.25 / 3.44 / 4.53 / 5.22 for n = 8 / 16 / 32 / 64 (max 4 / 4 / 6 / 7), against
      n - 1 = 7 / 15 / 31 / 63 for the plain variant. The pass count grows only slowly (roughly like log n),
      so early-exit Bellman-Ford on random complete digraphs is far below Theta(n^4).
  (b) mean passes per source 4.50 / 8.50 / 16.50 / 32.50 = (n + 1)/2, max n - 1, min 2: from source s the
      variant needs about s + 1 passes, n^2/2 passes in total, so Theta(n^4) is attained.
(An earlier draft of this docstring predicted "3 to 4 passes, not growing with n" for (a) before the script
had been run; the run showed slow growth instead, and the text was corrected.)
Decision: the entry implements the plain n - 1 passes (Theta(n^2 m) on every input) and mentions the
early-exit variant in its caveats.

Run from the repository root:  python experiments/2026-10-07_apsp_bellman_ford_early_exit.py
"""
import random


def passes_early_exit(W, s):
    n = len(W)
    edges = [(u, v, W[u][v]) for u in range(n) for v in range(n) if u != v and W[u][v] is not None]
    dist = [float("inf")] * n
    dist[s] = 0
    passes = 0
    for _ in range(n - 1):
        passes += 1
        changed = False
        for u, v, w in edges:
            d = dist[u] + w
            if d < dist[v]:
                dist[v] = d
                changed = True
        if not changed:
            break
    return passes


def random_complete(n, rng):
    return tuple(tuple(0 if i == j else rng.randint(1, 1000) for j in range(n)) for i in range(n))


def descending_path(n):
    return tuple(tuple(0 if i == j else (1 if j == i - 1 else 10 ** 6) for j in range(n)) for i in range(n))


print("(a) random complete digraphs, weights 1..1000: passes per source (early exit)")
for n in (8, 16, 32, 64):
    rng = random.Random(f"bf-early-exit|{n}")
    W = random_complete(n, rng)
    p = [passes_early_exit(W, s) for s in range(n)]
    print(f"  n={n}: mean {sum(p) / n:.2f}, max {max(p)}, plain variant would make {n - 1}")

print("(b) descending path family: passes per source (early exit)")
for n in (8, 16, 32, 64):
    W = descending_path(n)
    p = [passes_early_exit(W, s) for s in range(n)]
    print(f"  n={n}: mean {sum(p) / n:.2f}, max {max(p)}, min {min(p)}, plain variant would make {n - 1}")
