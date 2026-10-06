# Shortest path: simple-path enumeration vs Dijkstra

**Type:** T2 (naive-exp → poly) · **Verification:** V2

| Algorithm | Time (complete digraph, n vertices) | Implementation |
|---|---|---|
| Enumerate all simple s–t paths | Θ(n·(n−2)!) | [enumeration.py](implementations/enumeration.py) |
| Dijkstra, array version | Θ(n²) | [dijkstra.py](implementations/dijkstra.py) |

**Why it's a pair.** There are factorially many paths, but with non-negative weights a greedy settling
order is enough to find the shortest one.

**Further T3 steps.** Fibonacci heaps give O(m + n log n) (Fredman–Tarjan 1987). Duan et al. 2025 give
O(m log^(2/3) n) on sparse graphs.

**Sources.** Dijkstra 1959. Fredman & Tarjan 1987. arXiv:2504.17033.
