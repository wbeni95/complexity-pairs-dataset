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
the claimed bounds fail (α = 0.558 against n⁵, α = 0.479 against n⁴). These are measurements; they say nothing about
the worst case, so the entry stays at V1 (INCONCLUSIVE). No worst-case construction is claimed or implemented in this
entry (a paper on the efficiency of Edmonds–Karp, Zadeh 1972, is listed as background by its title).

**What is proved about "faster".** Both time bounds are upper bounds, proved for these two implementations in
[PROOFS.md](PROOFS.md) (with their correctness). On the harness's own random family (`generate_scaling`: G(n, ½) with
capacities uniform on 1..100, under an ideal-random-bits assumption), PROOFS.md, section 10, with three theorem notes
([trivial minimum cut](../../theorems/max-flow-random-dense-trivial-min-cut/),
[Dinic](../../theorems/max-flow-random-dense-dinic-short-residual-paths/),
[Edmonds–Karp](../../theorems/max-flow-random-dense-edmonds-karp-cubic-reads/)), proves a separation: for every
n ≥ 21 793, with probability at least 1 − 5/n, Edmonds–Karp makes at least 0.011·n³ reads while Dinic makes at most
26·n(n − 1) + 600(n − 1) reads and runs in O(n²) time. No worst-case separation is proved: Edmonds–Karp's worst case is
shown to be Θ(n³) on networks with capacities ≤ 100 and no parallel edges (n ≥ 1000), which does not exceed Dinic's
proved worst-case bound O(V²·E). The T3 tag rests on the two worst-case upper bounds proved in PROOFS.md (the
published bounds, Edmonds & Karp 1972; Dinic 1970, listed as background in `entry.json`) and on this family
separation. The separation says nothing about the sizes the tests and the probe use (n ≤ 160).

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
the proofs: cut enumeration, the augmentation and phase counts against their bounds, memory peaks, the
bipartite-matching reduction, the random calls of `generate_scaling`, and the measured counts quoted above. The
`verify.py` scripts of the three theorem notes check the probability bounds of the separation (certified rounding) and
its deterministic steps on seeded instances.

**Proofs.** [PROOFS.md](PROOFS.md): correctness of both implementations (max-flow min-cut from the residual graph),
the bounds O(V·E²) and O(V²·E), space O(V + E), the bounds in terms of F above, the reduction of maximum
bipartite matching to unit-capacity flow, the random model of `generate_scaling`, and the separation on it (with the
theorem notes).

**Sources.** Edmonds & Karp, J. ACM 19(2), 1972. Dinic, Soviet Math. Doklady 11, 1970 (no DOI). Ford &
Fulkerson, Canad. J. Math. 8, 1956. Zadeh, J. ACM 19(1), 1972 (background, title only).
