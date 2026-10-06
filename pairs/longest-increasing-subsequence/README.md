# Longest increasing subsequence: enumeration vs quadratic DP vs patience sorting

**Type:** T2 (naive-exp → poly), secondary T3 · **Verification:** V2

**Problem.** Given n integers, find the length of the longest strictly increasing subsequence.

| Algorithm | Time | Implementation |
|---|---|---|
| Subset enumeration | Θ(2ⁿ n) | [subset_enumeration.py](implementations/subset_enumeration.py) |
| Quadratic DP | Θ(n²) | [quadratic_dp.py](implementations/quadratic_dp.py) |
| Patience sorting + binary search | O(n log L) ≤ O(n log n), L = answer | [patience.py](implementations/patience.py) |

**Why it's a pair.** Trying all 2ⁿ subsequences is wasteful. The best subsequence ending at position i depends
only on the best ones ending earlier, which gives Θ(n²) (T2). Keeping just the smallest possible tail for each
length gives a sorted array, so the inner scan becomes a binary search: O(n log n) (T3). Its length matches the
first row of Schensted's tableau.

**Verification.** V1: the three agree with each other and with an independent oracle, LIS(a) = LCS(a,
sorted(set(a))), on inputs with many ties. V2 uses strictly increasing input, the worst case for patience
sorting, and counts **element comparisons exactly** with an instrumented element type (`CountingKey`); the
implementations are unchanged. Every count equals a closed form: n·2ⁿ⁻¹ − 2ⁿ + 1 for the enumeration (α = 1.014
against 2ⁿn, n = 12..18), n(n−1)/2 for the DP (α = 1.002 against n², n = 100..1600), and Σ_{j=2..n} ⌊log₂ j⌋ =
n log₂ n − c·n with c = 1.92–1.96 for patience sorting (α = 1.012 against n log n, n = 10⁴..3·10⁵). With
tolerance 0.03, every declared rival is rejected: 2ⁿ (α = 1.113) and 2ⁿn² (0.931); n log n (1.713) and n² log n
(0.923); n (1.105), n log² n (0.933) and n² (0.553). So the log factor of patience sorting is resolved. The
enumeration's count is of comparisons, not of its 2ⁿn loop steps. Details:
`experiments/2026-10-07b_count_v2_inversions_lis.py` and `research/2026-10-07b_count_based_v2.md`.

**Sources.** Schensted 1961 (Canad. J. Math. 13). Fredman 1975 (Discrete Math. 11). CLRS (3rd ed.),
Exercises 15.4-5 and 15.4-6.
