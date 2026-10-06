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
sorting: runtimes fit 2ⁿn, n² and n log n. A plain-n fit would also pass for patience sorting at the default
tolerance, so the log factor itself is not isolated.

**Sources.** Schensted 1961 (Canad. J. Math. 13). Fredman 1975 (Discrete Math. 11). CLRS (3rd ed.),
Exercises 15.4-5 and 15.4-6.
