# Shortest path: simple-path enumeration vs Dijkstra

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (complete digraph, n vertices) | Implementation |
|---|---|---|
| Enumerate all simple s–t paths | Θ(n·(n−2)!) | [enumeration.py](implementations/enumeration.py) |
| Dijkstra, array version | Θ(n²) | [dijkstra.py](implementations/dijkstra.py) |

**Why it's a pair.** There are factorially many paths, but with non-negative weights a greedy settling
order is enough to find the shortest one.

**Θ(n²) is optimal for matrix input.** For n ≥ 4, split the vertices other than s and t into U (⌊(n−2)/2⌋ of
them) and W. Give every arc s→u and x→t weight 1 and every arc u→x weight 2 (u ∈ U, x ∈ W), and every other arc
weight 100. The distance is 4, and lowering any single u→x weight to 1 makes it 3, so every correct deterministic
algorithm must read all ⌊(n−2)²/4⌋ of these weights. The array version reads exactly n(n−1)/2 distinct weights (for each
pair of vertices, the one leaving the vertex settled first).

**Further T3 steps.** Fibonacci heaps give O(m + n log n) (Fredman–Tarjan 1987). Duan et al. 2025 give
O(m log^(2/3) n) on sparse graphs.

**Sources.** Dijkstra 1959. Fredman & Tarjan 1987. arXiv:2504.17033.
