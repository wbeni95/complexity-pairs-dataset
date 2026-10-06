# Global minimum cut: all bipartitions vs Stoer–Wagner

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (exact operation counts with rivals)

Input: an undirected graph on n vertices, given as an n × n symmetric matrix of non-negative integer weights with
zero diagonal (0 = no edge). Output: the smallest total weight of the edges crossing a partition of the vertices into
two non-empty sides. Disconnected graphs have answer 0. For n < 2 no such partition exists, and the answer is `None`.

| Algorithm | Weight operations (n ≥ 2, exact) | Time | Implementation |
|---|---|---|---|
| All 2ⁿ⁻¹ − 1 bipartitions (vertex 0 fixed) | n(n−1)2ⁿ⁻³ additions + 2ⁿ⁻¹ − 2 comparisons | Θ(n²·2ⁿ) | [brute_force.py](implementations/brute_force.py) |
| Stoer–Wagner, array version (1997) | (n−1)(n−2)(n+3)/6 additions + n(n−1)(n−2)/6 + n − 2 comparisons | Θ(n³) | [stoer_wagner.py](implementations/stoer_wagner.py) |

**Why it's here.** The brute force ignores the structure of minimum cuts. In a maximum-adjacency ordering that ends
in s, t, the cut separating t from everything else is a minimum s–t cut (the "cut of the phase"). So after each
phase either the global minimum separates s and t, and it has just been seen, or s and t can be merged. Then n − 1
phases suffice. Stoer and Wagner found this simple proof for the earlier Nagamochi–Ibaraki algorithm. Their
Fibonacci-heap bound O(nm + n² log n) is Θ(n³) on dense matrix input, so the array version is the natural one here.
Karger–Stein (randomized) is faster but is not implemented (see `notes` in entry.json).

**Where the closed forms come from.** Brute force: summed over all S ⊆ {1..n−1}, the number of S × T pairs is
Σₖ C(n−1,k)·k(n−k) = n(n−1)2ⁿ⁻³. Each pair is one addition, and each bipartition after the first costs one
comparison. Stoer–Wagner, phase on k vertices: (k−1)(k−2)/2 key additions, k − 2 merge additions, (k−1)(k−2)/2
selection comparisons, and one comparison with the best cut so far (in every phase but the first). Summing over
k = n..2 gives the table. The experiment script checks every formula against the instrumented counts (brute force at
n = 2..14, Stoer–Wagner at n = 2..40 and 48..256). The counts do not depend on the weights.

**Verification.**
- **V1:** 96 instances from six families: dense, sparse, two components, a planted light cut, a weakly attached
  vertex, and all-zero. Among the instances with n ≥ 2, the minimum cut is 0 in 47 of 84. The independent `check`
  takes the minimum over t of the maximum 0–t flow, using Edmonds–Karp written in the harness. For n ≤ 10 it also
  enumerates all subsets with a different cut formula. As negative controls, `check` rejects answer + 1 on 84/84
  instances, the minimum weighted degree on 28/84, and Stoer–Wagner's first phase alone on 34/84.
- **V2:** the harness's `CountingWeight` counts the weight additions and comparisons made by the unchanged
  implementations. The tolerance is 0.03.
  - Brute force (n = 6..14): α = 1.002 against n²·2ⁿ. The rivals n³ (2.838), 2ⁿ (1.305), n·2ⁿ (1.134) and n³·2ⁿ
    (0.897) are rejected.
  - Stoer–Wagner (n = 32..256): α = 1.007 against n³. The rivals n²·2ⁿ (0.037), n⁴ (0.755), n² (1.510) and
    n² log³ n (1.128) are rejected.

  Timing at tolerance 0.25 could not separate n³ from n² log³ n (ρ = 1.050, pattern report). Exact counts can.

**Caveats.** Additions and comparisons are unit cost. With b-bit weights, each costs O(b + log n) bit operations. In
the input size N = n² the brute force is 2^Θ(√N), not 2^Θ(N).

**Sources.** Stoer & Wagner, J. ACM 44(4) 1997. Nagamochi & Ibaraki, SIAM J. Discrete Math. 5(1) 1992. Karger &
Stein, J. ACM 43(4) 1996 (context only). Edmonds & Karp, J. ACM 19(2) 1972 (the oracle's max flow). Experiment:
[experiments/2026-10-07b_global_min_cut_counts.py](../../experiments/2026-10-07b_global_min_cut_counts.py).
