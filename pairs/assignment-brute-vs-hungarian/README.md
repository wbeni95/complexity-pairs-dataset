# Assignment problem: enumeration vs the Hungarian method

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given an n × n integer cost matrix, find the minimum cost of assigning each row to a distinct
column (minimum-cost perfect matching in K_{n,n}).

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Permutation enumeration | Θ(n · n!) | [brute_force.py](implementations/brute_force.py) |
| Hungarian method, shortest augmenting paths with potentials | O(n³) | [hungarian.py](implementations/hungarian.py) |

**Why it's a pair.** Enumeration ignores the linear-programming structure of the problem. Dual potentials
certify optimality, and each new row needs only one Dijkstra-like search on non-negative reduced costs.

**Worst case for timing.** On uniformly random matrices the search usually stops early, so the timing
uses C[i][j] = 1000·j + noise. Every row then ranks the columns the same way. On this family the runtimes grow
like n³ (V2 timing fit); no proof is given here that each search visits every matched column, or of a Θ(n³) lower
bound.

**Verification.** V1: both agree, and for n ≤ 12 they also match an independent O(n·2ⁿ) subset DP.
V2: runtimes fit n·n! and n³.

**Sources.** Kuhn 1955. Munkres 1957. Edmonds & Karp 1972 and Tomizawa 1971 (O(n³) with potentials).
Jonker & Volgenant 1987. Gabow & Tarjan 1989.
