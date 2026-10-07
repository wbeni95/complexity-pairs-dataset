# Maximum flow: Edmonds–Karp vs Dinic

**Type:** T3 (poly → faster poly) · **Verification:** V1

**Problem.** Compute the value of a maximum s–t flow in a directed network with integer capacities.

| Algorithm | Time (V vertices, E edges) | Implementation |
|---|---|---|
| Edmonds–Karp: shortest augmenting paths (BFS) | O(V·E²) | [edmonds_karp.py](implementations/edmonds_karp.py) |
| Dinic: blocking flows in level graphs | O(V²·E) | [dinic.py](implementations/dinic.py) |

**Why it's a pair.** Edmonds–Karp spends a full BFS on every augmenting path. Dinic augments along *all*
current shortest paths in one blocking-flow phase. At most V − 1 phases are needed, because the s–t
distance grows every phase.

**Why only V1.** Both bounds are worst-case bounds, and no family attaining them was built here. On random
dense networks the [probe](../../experiments/2026-10-07_max_flow_probe.py) found Edmonds–Karp making only
about n augmentations (176 at n = 160, against V·E ≈ 2·10⁶) and Dinic needing 2–4 phases. The fits against
the claimed bounds fail (α = 0.558 against n⁵, α = 0.479 against n⁴). The timings say nothing about the
worst case, so the entry stays at V1 (INCONCLUSIVE). Zadeh (1972) studies the efficiency of Edmonds–Karp (per its
title; the paper was not read here); no worst-case construction is claimed or implemented in this entry.

**Upper bounds only.** Both time bounds are cited upper bounds, and no lower bound for Edmonds–Karp is shown here,
so this entry does not show that Dinic is asymptotically faster.

**No such family exists with small capacities.** With integer capacities both implementations run in
O((F + 1)·(V + E)) time for maximum flow value F: every augmentation adds at least 1 to the flow, every BFS reads
each adjacency list at most once, and every Dinic phase except the last augments. With capacities ≤ 100 and no
parallel edges out of s, F ≤ 100·(V − 1), so both are O(V·(V + E)) there, including the harness's random
networks (O(n³)). So in that range Dinic's O(V²·E) is not attained as V → ∞, and Edmonds–Karp's O(V·E²) is not
attained as E → ∞.

**Verification.** V1: both agree with each other and, for n ≤ 14, with an independent oracle that
enumerates every s–t cut (max-flow min-cut theorem). The instances are random networks with mixed
capacities, zero-capacity, parallel and antiparallel edges, layered networks and networks with t
unreachable.

**Sources.** Edmonds & Karp, J. ACM 19(2), 1972. Dinic, Soviet Math. Doklady 11, 1970 (no DOI). Ford &
Fulkerson, Canad. J. Math. 8, 1956. Zadeh, J. ACM 19(1), 1972.
