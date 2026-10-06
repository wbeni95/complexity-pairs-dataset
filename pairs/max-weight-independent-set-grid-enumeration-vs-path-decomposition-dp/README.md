# Maximum-weight independent set on k × n grids with diagonals: exhaustive search vs path-decomposition DP

**Type:** T2 (naive-exp → poly, for every fixed number of rows k) · **Verification:** V2 (exact addition counts,
with rivals)

**Problem.** The input is a grid of k rows and n columns with non-negative integer vertex weights. Horizontal and
vertical neighbours are always adjacent. Each unit square may also carry the diagonal ╲, the diagonal ╱, both, or
neither; with both diagonals everywhere the graph is the king's graph. Output: the maximum total weight of an
independent set, together with one optimal set. A square with a diagonal contains a triangle, so these graphs are
in general not bipartite.

| Algorithm | Cost (N = k·n vertices) | Implementation |
|---|---|---|
| Exhaustive search over all 2ᴺ subsets (weight and independence of every subset, no early exit) | Θ(N·2ᴺ) on every input; exactly N·2ᴺ⁻¹ weight additions | [brute_force.py](implementations/brute_force.py) |
| DP over the columns (bags = two adjacent columns, width 2k − 1; states = column subsets independent inside the column) | Θ(F_{k+2}²·n) = Θ(φ^(2k)·n); exactly n·P_k + (n − 1)·F_{k+2} additions with positive weights (10n − 5 for k = 3) | [column_dp.py](implementations/column_dp.py) |

F_{k+2} (2, 3, 5, 8, 13, 21 for k = 1..6) is the number of k-bit column masks without two adjacent ones. P_k is
the total number of rows chosen over those masks (1, 2, 5, 10, 20, 38).

**Why it is here.** Every edge stays inside one column or joins two adjacent columns. So column c separates the
grid left of it from the grid right of it, and an optimal solution only needs to know which vertices of column c it
uses. That turns 2^(kn) subsets into n·F_{k+2}² state pairs: exponential → linear in n for every fixed k. The
dependence on k remains exponential (φ^(2k) ≈ 2.618^k). For square grids (k = n) the DP is exponential in n,
but not in N = n². This is the simplest case of dynamic programming over a path or tree decomposition of bounded
width (Arnborg & Proskurowski 1989; path-width: Robertson & Seymour 1983). On general graphs the problem is
NP-hard: independent sets of G are the cliques of its complement, and CLIQUE is NP-complete (Karp 1972).

**Why the diagonals.** Without diagonals a grid is bipartite (colour (r, c) by the parity of r + c). On bipartite
graphs this problem reduces to a minimum s–t cut: an arc source → u of capacity w(u) for every u on one side, an
arc v → sink of capacity w(v) for every v on the other side, and infinite capacity on every edge from the first
side to the second. The finite cuts are exactly the vertex covers, each with capacity equal to its weight, and a
maximum independent set is the complement of a minimum vertex cover. So a polynomial max-flow algorithm (see
[max-flow-edmonds-karp-vs-dinic](../max-flow-edmonds-karp-vs-dinic/)) already solves plain grids. With diagonals
that reduction no longer applies, and the column DP is what makes the problem easy. The DP handles both cases. The
flow method is not implemented here.

**Verification.**
- *V1:* the validator runs n = 0..6, 8, 12, 20, 50, 8 instances per size (88 instances, 136 implementation runs).
  Exhaustive search runs up to n = 5 (at most 15 vertices), so the two algorithms are compared on 48 instances.
  The row count is k = 1..5 for n ≤ 3, 1..3 for n = 4, 5 and 1..6 for n ≥ 6. The diagonal patterns are random,
  king's graph, none, all ╲, all ╱ and sparse. The weights are uniform 0..9 or 0..1000, all equal (ties), half
  zeros, or one heavy vertex.
- *Oracle:* `check` is independent and always gives a verdict. The returned set must consist of distinct grid
  vertices, be independent (edges rebuilt from the instance), and weigh exactly the returned value. The value
  must equal the optimum of a vertex-by-vertex DP written in the harness. That DP works in column-major order
  over the last k + 1 vertices, which contain every earlier neighbour of the next vertex: a different
  decomposition (width k + 1) and different code.
- *Experiment* ([script](../../experiments/2026-10-06f_entries_mis_pathwidth.py)):
  - 600 more instances: n = 0..5 with both algorithms, n = 6..60 with the DP; 0 failures.
  - **oracle control:** 3393 deliberately wrong outputs on 330 instances; **all rejected**, 0 undecided,
    0 accepted. Of the 510 correct outputs, all were accepted. The wrong outputs were:
    - the value ± 1 with the same set;
    - a suboptimal independent set with its honest weight (one vertex dropped, or the greedy-by-weight set);
    - a non-independent set with its honest weight (a neighbour added, or the optimum computed as if the diagonals
      were absent);
    - duplicate or out-of-grid vertices, the empty set, and wrong types.
- *V2:* the scaling instance is the 3 × n king's graph with seeded weights 1..9. The weights use an instrumented
  integer type that counts additions on weight-derived values; comparisons are tallied separately and not
  included. The implementations are unchanged. The counts are exactly 3n·2^(3n−1) for exhaustive search (n = 1..6;
  the same formula N·2ᴺ⁻¹ holds on 77 random instances with any k, any diagonals and zero weights) and 10n − 5 for
  the DP. The DP form n·P_k + (n − 1)·F_{k+2} holds on 420 random instances with n = 1..40, k = 1..6, every
  diagonal pattern and positive weights.

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| exhaustive search vs n·8ⁿ (= (2/3)·3n·2^(3n−1)), n = 2..6 | 1.000 | 8ⁿ: 1.130, n²·8ⁿ: 0.896, 4ⁿ: 1.695 |
| column DP vs 10n − 5, n = 100..3200 | 1.000 | n²: 0.501, n log n: 0.862 |

Both fits resolve the log factor.

*k-dependence* (information, n = 20, king's graph), with the DP's additions measured and equal to the formula:

| k | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|
| additions | 58 | 97 | 195 | 352 | 647 | 1159 | 2066 | 3645 |
| compatibility tests | 76 | 171 | 475 | 1216 | 3211 | 8379 | 21964 | 57475 |

Exhaustive search would need N·2ᴺ⁻¹ ≈ 3.5·10¹⁹ additions at k = 3.

**Caveats.**
- The V2 family fixes k = 3, so n·8ⁿ is the k = 3 instance of N·2ᴺ.
- Only additions are counted. The DP's (n − 1)·F_{k+2}² compatibility tests (25 per column for k = 3) and the
  exhaustive search's independence tests use plain integers and are not counted; for fixed k they are linear in n
  and Θ(N·2ᴺ) respectively, the same order as the counted additions.
- The DP count needs positive weights. With weights in {0, 1}, up to 6 additions (in 59 of 420 instances) involve
  two plain zeros and go uncounted.
- In all batteries both algorithms returned the same optimal set (0 differences in 348 compared instances), so
  the value-only `equal` was never needed to absorb a tie.

**Sources.** Arnborg & Proskurowski, Discrete Appl. Math. 1989. Bodlaender, SIAM J. Comput. 1996 (tree
decompositions of small width can be found in linear time; here the columns give one directly). Robertson &
Seymour, J. Combin. Theory B 1983 (path-width). Karp 1972 (CLIQUE).
