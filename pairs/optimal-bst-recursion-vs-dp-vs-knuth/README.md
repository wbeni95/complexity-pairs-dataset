# Optimal binary search tree: plain recursion vs cubic DP vs Knuth

**Type:** T2 (naive-exp → poly), secondary T3 · **Verification:** V2 (exact comparison counts)

**Problem (Knuth 1971).** Keys k₁ < … < kₙ have access frequencies p₁..pₙ and the gaps between them have
frequencies q₀..qₙ (all non-negative integers). Find the minimum over all BSTs of
Σ pₘ (level(kₘ) + 1) + Σ qⱼ level(gap j), with the root at level 0. The output is that exact integer.

| Algorithm | Time (n keys) | Exact cost comparisons | Implementation |
|---|---|---|---|
| Plain recursion over the root | Θ(3ⁿ) | (3ⁿ⁻¹ − 1)/2, with exactly 3ⁿ calls | [recursion.py](implementations/recursion.py) |
| Interval DP, every root | Θ(n³) | (n+1)n(n−1)/6 | [cubic_dp.py](implementations/cubic_dp.py) |
| Knuth: root of [i..j] in r[i][j−1]..r[i+1][j] | Θ(n²) on every input | Σ_{L=2..n} (r[n−L+1][n] − r[0][L−1]) ≤ (n−1)² | [knuth.py](implementations/knuth.py) |

**Why it's here.** The recursion recomputes the Θ(n²) intervals, and memoising them gives Θ(n³) (T2). With
non-negative weights, w(i, j) satisfies the quadrangle inequality, so the optimal roots can be chosen monotone. The
root searches then telescope: for each length L the ranges sum to (n − L + 1) + r[n−L+1][n] − r[0][L−1] ≤ 2n, so
the total is O(n²). It is also Ω(n²), since there are n(n+1)/2 intervals (T3). This is the first entry in the
dataset from the Knuth–Yao "monotone roots / quadrangle inequality" family.

**The 3ⁿ estimate, checked.** The pattern report estimated Θ(3ⁿ) for the recursion by analogy with matrix chain.
Call counting confirms it exactly: K(m) = 1 + 2 Σ_{t<m} K(t) = 3ᵐ (empty intervals are calls too), measured for
n = 0..11.

**Ties.** Tie-heavy inputs (frequencies in {0, 1}, all zero, all equal) do not break the restricted search,
whatever minimiser in the range is kept (largest, smallest, random, or deliberately inconsistent): 0 wrong values on
6006 instances. This was tested and refuted after an earlier draft of this entry claimed otherwise. The reason is
that chosen roots stay inside their ranges, so r[i][j−1] ≤ r[i+1][j−1] ≤ r[i+1][j]. Monotonicity is *not* a
property of arbitrary optimal roots, though: mixing "largest" and "smallest" over the full optimal sets gives
non-monotone tables (3417 of the 6006).

**Verification.**
- **V1.** The three implementations agree with each other and with an independent oracle on n = 0..100, using ten
  families of instances, most of them full of ties. For n ≤ 10 the oracle enumerates every tree shape explicitly
  and computes the cost from the levels. For n ≤ 60 it uses a separately written memoised recursion.
- **V2.** Exact counts of cost comparisons on Knuth's worst-case family: p₁ = pₙ heavy, so every prefix interval
  has root 1, every suffix interval has root n, and the count is (n−1)². The fits use tolerance 0.04 and give
  α = 1.002 (3ⁿ), 1.001 (n³) and 1.010 (n²).
- **Rivals rejected.** 2ⁿ, 4ⁿ and 4ⁿ/n^1.5 for the recursion (α = 1.587, 0.794, 0.923); n² and n⁴ for the cubic DP
  (1.501, 0.750); n³, n, n log n and n² log n for Knuth (0.674, 2.021, 1.668, 0.914).
- **Other families.** On seven other families Knuth's count is 0.39n²–0.61n² and α against n² is 0.993–1.013, for
  n = 32..512.

Scripts: [counts](../../experiments/2026-10-07b_optimal_bst_counts.py), [ties](../../experiments/2026-10-07b_optimal_bst_ties.py).

**Sources.** Knuth 1971, *Optimum binary search trees*, Acta Informatica 1(1), 14–25. Yao 1980, *Efficient dynamic
programming using quadrangle inequalities*, STOC 1980, 429–435. CLRS (3rd ed.), §15.5 (its cost adds Σqⱼ).
