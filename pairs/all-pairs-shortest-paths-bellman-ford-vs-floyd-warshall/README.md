# All-pairs shortest paths: Bellman–Ford from every source vs Floyd–Warshall

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given an n × n matrix of non-negative integer edge weights (None = no edge), compute the
shortest-path distance between every ordered pair of vertices (None if unreachable).

| Algorithm | Time (n vertices, m edges) | Implementation |
|---|---|---|
| Bellman–Ford from every source (n − 1 passes, no early exit) | Θ(n²·m), Θ(n⁴) on dense graphs | [bellman_ford.py](implementations/bellman_ford.py) |
| Floyd–Warshall | Θ(n³) | [floyd_warshall.py](implementations/floyd_warshall.py) |

**Why it's a pair.** A single-source algorithm run n times recomputes, for every source, information
that Floyd–Warshall shares across all sources: its recursion over the set of allowed intermediate
vertices fills the whole matrix in n³ steps. The gain depends on density. With m = O(n) edges the two
bounds coincide, so the pair is about dense graphs.

**Early exit.** The usual "stop when a pass changes nothing" optimisation does not change Bellman–Ford's
worst case. It does make random complete digraphs easy: a mean of 3.25 to 5.22 passes per source for
n = 8 to 64 instead of n − 1 ([experiment](../../experiments/2026-10-07_apsp_bellman_ford_early_exit.py)).
The entry therefore times the plain version, which does the same work on every input.

**Verification.** V1: both implementations agree with each other and with an independent oracle
(heap-based Dijkstra from every source) on random digraphs of four densities, with zero-weight edges
and unreachable pairs. V2: on complete digraphs, the harness counts **relaxation steps exactly** (one weight
addition each) with an instrumented weight type (`CountingWeight`); the implementations are unchanged and
return the same distances. Bellman–Ford × n makes exactly n²(n − 1)² (n = 8..40) and Floyd–Warshall n³ − n
(n = 32..200; its n steps with i = j = k add the implementation's own diagonal zeros and are not seen). Both
fit their claims with α = 1.000 at tolerance 0.03, and each rejects the other's cost as a rival: Bellman–Ford
against n³ (α = 1.377), Floyd–Warshall against n²(n − 1)² (0.745). Details:
`experiments/2026-10-07b_count_v2_apsp_strings.py` and `research/2026-10-07b_count_based_v2.md`.

**Beyond.** Williams (2014) gave a randomized n³ / 2^Ω(√log n) algorithm. Vassilevska Williams and Williams
(2018) show that APSP, min-plus product and negative-triangle detection are subcubic-equivalent.

**Sources.** Floyd, CACM 5(6), 1962. Warshall, J. ACM 9(1), 1962. Bellman, Quart. Appl. Math. 16(1), 1958.
Johnson, J. ACM 24(1), 1977. Williams, SIAM J. Comput. 47(5), 2018. Vassilevska Williams & Williams,
J. ACM 65(5), 2018.
