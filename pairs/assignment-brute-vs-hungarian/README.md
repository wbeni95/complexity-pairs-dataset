# Assignment problem: enumeration vs the Hungarian method

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given an n × n integer cost matrix, find the minimum cost of assigning each row to a distinct
column (minimum-cost perfect matching in K_{n,n}).

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Permutation enumeration | Θ(n · n!) under the background assumption on `itertools.permutations`; Ω(n · n!) unconditionally | [brute_force.py](implementations/brute_force.py) |
| Hungarian method, shortest augmenting paths with potentials | O(n³) | [hungarian.py](implementations/hungarian.py) |

**Why it's a pair.** Enumeration ignores the linear-programming structure of the problem. Dual potentials
certify optimality (every assignment costs at least Σu + Σv, with equality for the final matching), and each new
row needs only one Dijkstra-like search on reduced costs: at most i iterations for the i-th row, so at most
n(n + 1)(2n + 1)/6 reduced-cost evaluations in all.

**Worst case for timing.** On uniformly random matrices the search usually stops early (measured: 8% to 28% of the
iteration bound on [0, 99] matrices, n = 30..200, [experiment](../../experiments/2026-10-07_assignment_random_matrix_counts.py)),
so the timing uses C[i][j] = 1000·j + noise. Every row then ranks the columns the same way. On this family the
runtimes grow like n³ (V2 timing fit); no proof is given here that each search visits every matched column, or of a
Θ(n³) lower bound.

**Verification.** V1: both agree, and for n ≤ 12 they also match an independent O(n·2ⁿ) subset DP.
V2: runtimes fit n·n! and n³.

**Background** (cited; not claims of this entry). Machine-model assumption: `itertools.permutations(range(n))`
behaves as the "roughly equivalent" code in its documentation, yielding every permutation once, with O(n·n!) work in
total (amortised O(n) per permutation) and O(n) state; PROOFS.md §1 proves these costs for the documented code, and
that the C implementation matches them is assumed. For integer costs of magnitude at most N, cost scaling solves the
assignment problem in O(√n·m·log(nN)) time, O(n^2.5 log(nN)) for an n × n matrix (Gabow & Tarjan 1989), which is
below O(n³) when log(nN) = o(√n). Jonker & Volgenant (1987) give a shortest augmenting path algorithm for dense and
sparse instances.

**Proofs.** [PROOFS.md](PROOFS.md) proves the correctness, the operation counts and bounds, and the space of both
implementations, and the maximisation remark; `tests/test_proofs_assignment.py` checks them on stated ranges. The
enumeration's upper time and space bounds hold under the background assumption on `itertools.permutations`; its
Ω(n · n!) holds unconditionally.

**Sources.** Kuhn 1955. Munkres 1957. Edmonds & Karp 1972. Tomizawa 1971. Jonker & Volgenant 1987. Gabow & Tarjan
1989. Python documentation, `itertools.permutations`.
