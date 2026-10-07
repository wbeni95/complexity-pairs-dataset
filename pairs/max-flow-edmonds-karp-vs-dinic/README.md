# Maximum flow: Edmonds–Karp vs Dinic

**Type:** T3 (poly → faster poly) · **Verification:** V1

**Problem.** Compute the value of a maximum s–t flow in a directed network with integer capacities.

| Algorithm | Time (V vertices, E edges) | Implementation |
|---|---|---|
| Edmonds–Karp: shortest augmenting paths (BFS) | O(V·E²) | [edmonds_karp.py](implementations/edmonds_karp.py) |
| Dinic: blocking flows in level graphs | O(V²·E) | [dinic.py](implementations/dinic.py) |

**Why it's a pair.** Edmonds–Karp runs one BFS per augmenting path. Dinic augments along shortest
paths until none of the current length is left, in one blocking-flow phase. At most V − 1 phases are needed,
because the s–t distance grows every phase.

**Why only V1.** Both bounds are worst-case bounds, and no family attaining them was built here. On random
dense networks the [probe](../../experiments/2026-10-07_max_flow_probe.py) found Edmonds–Karp making only
about n augmentations (176 at n = 160, against V·E ≈ 2·10⁶) and Dinic needing 2–4 phases. The fits against
the claimed bounds fail (α = 0.558 against n⁵, α = 0.479 against n⁴). The timings say nothing about the
worst case, so the entry stays at V1 (INCONCLUSIVE). Zadeh (1972) studies the efficiency of Edmonds–Karp (per its
title; the paper was not read here); no worst-case construction is claimed or implemented in this entry.

**Upper bounds only.** Both time bounds are upper bounds, proved for these two implementations in
[PROOFS.md](PROOFS.md) (with their correctness). No lower bound for Edmonds–Karp is proved here, so this entry does
not show that Dinic is asymptotically faster. The T3 tag is a classification by the published worst-case upper
bounds of the two algorithms (Edmonds & Karp 1972; Dinic 1970), listed as background in `entry.json`; no lower bound
for Edmonds–Karp and no separation is shown here.

**No such family exists with small capacities and no parallel edges out of s.** With integer capacities both implementations run in
O((F + 1)·(V + E)) time for maximum flow value F: every augmentation adds at least 1 to the flow, every BFS reads
each adjacency list at most once, and every Dinic phase except the last augments. With capacities ≤ 100 and no
parallel edges out of s, F ≤ 100·min(V − 1, E), so both are O(V·E) there (E ≥ 1), including the harness's
random networks (O(n³)). So in that range Dinic's O(V²·E) is not attained as V → ∞, and Edmonds–Karp's O(V·E²) is
not attained as E → ∞ (PROOFS.md, section 6).

**Verification.** V1: both agree with each other and, for n ≤ 14, with an independent oracle that
enumerates every s–t cut (max-flow min-cut theorem). The instances are random networks with mixed
capacities, zero-capacity, parallel and antiparallel edges, layered networks and networks with t
unreachable. [tests/test_proofs_maxflow.py](../../tests/test_proofs_maxflow.py) checks the computable parts of
the proofs: cut enumeration, the augmentation and phase counts against their bounds, memory peaks, and the
bipartite-matching reduction.

**Proofs.** [PROOFS.md](PROOFS.md): correctness of both implementations (max-flow min-cut from the residual graph),
the bounds O(V·E²) and O(V²·E), space O(V + E), the bounds in terms of F above, and the reduction of maximum
bipartite matching to unit-capacity flow.

**Sources.** Edmonds & Karp, J. ACM 19(2), 1972. Dinic, Soviet Math. Doklady 11, 1970 (no DOI). Ford &
Fulkerson, Canad. J. Math. 8, 1956. Zadeh, J. ACM 19(1), 1972.
