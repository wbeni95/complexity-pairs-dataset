"""Experiment: does the adversarial family G_k of pairs/bipartite-matching-kuhn-vs-hopcroft-karp (harness.py,
generate_scaling) really force Theta(V E) work for Kuhn and Theta(E sqrt V) work, with k + 1 phases, for
Hopcroft-Karp? And how do both behave on random bipartite graphs, where worst cases are not expected?

Method: instrumented copies of the two implementations (same logic, plus counters) count adjacency-list
entries scanned ("edge scans", BFS and DFS together for Hopcroft-Karp) and Hopcroft-Karp phases (BFS
passes, including the final one that finds no augmenting path). Counts are deterministic.
For G_k: V = 4k^2 + k, E = 2k^4 + k^2. Printed ratios: Kuhn scans / (V E) and HK scans / (E sqrt V),
which should level off to constants if the claims hold; and HK phases vs k + 1.

Run from the repository root:  python experiments/2026-10-07_bipartite_matching_counts.py

Outcome (2026-10-07, deterministic, reproduced on rerun): on G_k, Hopcroft-Karp ran exactly k + 1 phases for
every k = 2, 4, ..., 16. Kuhn scans / (V E) = 0.1620, 0.1446, 0.1432, 0.1432, 0.1434, 0.1436, 0.1439, 0.1440 and
HK scans / (E sqrt V) = 1.0934, 1.0501, 1.0350, 1.0271, 1.0222, 1.0188, 1.0163, 1.0144 for k = 2..16, i.e. both
ratios level off as claimed. The matching sizes equal the analytic maximum k^2 + k(k+1)/2 (e.g. 26 at k = 4,
392 at k = 16). On random graphs (V = 100..800): Hopcroft-Karp 2-5 phases and 1.5-4.7 E scans; Kuhn
0.025-0.047 V E scans at p = 0.05 and 0.079-0.082 V E at p = 0.5 (so Kuhn is near its worst case on dense
random graphs, while Hopcroft-Karp is far from its sqrt(V) phase bound there).
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("bm_harness", ROOT / "pairs" / "bipartite-matching-kuhn-vs-hopcroft-karp" / "harness.py")
H = importlib.util.module_from_spec(spec)
spec.loader.exec_module(H)


def kuhn_counts(graph):
    n_left, n_right, adj = graph
    match_l, match_r = [-1] * n_left, [-1] * n_right
    size = scans = 0
    for root in range(n_left):
        seen, ptr, stack, free_right = [False] * n_right, [0] * n_left, [root], -1
        while stack:
            u = stack[-1]
            nbrs = adj[u]
            if ptr[u] < len(nbrs):
                v = nbrs[ptr[u]]
                ptr[u] += 1
                scans += 1
                if seen[v]:
                    continue
                seen[v] = True
                w = match_r[v]
                if w == -1:
                    free_right = v
                    break
                stack.append(w)
            else:
                stack.pop()
        if free_right != -1:
            v = free_right
            for u in reversed(stack):
                old = match_l[u]
                match_l[u], match_r[v] = v, u
                v = old
            size += 1
    return size, scans


def hk_counts(graph):
    n_left, n_right, adj = graph
    INF = n_left + n_right + 1
    match_l, match_r = [-1] * n_left, [-1] * n_right
    size = scans = phases = 0
    while True:
        phases += 1
        dist = [INF] * n_left
        queue = [u for u in range(n_left) if match_l[u] == -1]
        for u in queue:
            dist[u] = 0
        target, head = INF, 0
        while head < len(queue):
            u = queue[head]
            head += 1
            du = dist[u]
            if du + 1 > target:
                continue
            for v in adj[u]:
                scans += 1
                w = match_r[v]
                if w == -1:
                    if target == INF:
                        target = du + 1
                elif dist[w] == INF:
                    dist[w] = du + 1
                    queue.append(w)
        if target == INF:
            return size, scans, phases
        ptr = [0] * n_left
        for root in range(n_left):
            if match_l[root] != -1 or dist[root] != 0:
                continue
            stack = [root]
            while stack:
                u = stack[-1]
                nbrs, du, pushed = adj[u], dist[u], False
                while ptr[u] < len(nbrs):
                    v = nbrs[ptr[u]]
                    ptr[u] += 1
                    scans += 1
                    w = match_r[v]
                    if w == -1:
                        if du + 1 == target:
                            for x in stack:
                                dist[x] = INF
                            for x in reversed(stack):
                                old = match_l[x]
                                match_l[x], match_r[v] = v, x
                                v = old
                            size += 1
                            stack = []
                            break
                    elif dist[w] == du + 1:
                        stack.append(w)
                        pushed = True
                        break
                if stack and not pushed:
                    dist[u] = INF
                    stack.pop()


print("Adversarial family G_k (V = 4k^2 + k, E = 2k^4 + k^2)")
for k in range(2, 17, 2):
    g = H.adversarial(k)
    V = g[0] + g[1]
    E = sum(len(a) for a in g[2])
    sk, ks = kuhn_counts(g)
    sh, hs, ph = hk_counts(g)
    assert sk == sh
    print(f"  k={k:2d}: V={V}, E={E}, matching={sk}; Kuhn scans {ks} = {ks / (V * E):.4f} V E; "
          f"HK scans {hs} = {hs / (E * math.sqrt(V)):.4f} E sqrt(V), phases {ph} (k + 1 = {k + 1})", flush=True)

print("Random bipartite graphs, n_left = n_right = V/2, edge probability p (one instance each)")
for p in (0.05, 0.5):
    for half in (50, 100, 200, 400):
        rng = random.Random(f"bm-random|{p}|{half}")
        g = H._random_bipartite(half, half, p, rng)
        V = 2 * half
        E = sum(len(a) for a in g[2])
        sk, ks = kuhn_counts(g)
        sh, hs, ph = hk_counts(g)
        assert sk == sh
        print(f"  p={p}, V={V}, E={E}, matching={sk}: Kuhn scans {ks} = {ks / (V * E):.4f} V E "
              f"= {ks / E:.2f} E; HK scans {hs} = {hs / E:.2f} E, phases {ph}", flush=True)

# How many members of the adversarial family does the validator's V1 battery contain? (Run inline first,
# kept here.) Outcome 2026-10-07: 2, 0, 1, 2 of 6 instances for n = 5, 18, 39, 68 (k = 1, 2, 3, 4).
E = "bipartite-matching-kuhn-vs-hopcroft-karp"
print("Adversarial instances in the V1 battery (seeded as tools/validate.py seeds them)")
for n in [5, 18, 39, 68]:
    hits = sum(H.generate(n, random.Random(f"{E}|v1|{n}|{trial}")) == H.adversarial(H.adversarial_k(n))
               for trial in range(6))
    print(f"  n={n}: {hits} of 6")
