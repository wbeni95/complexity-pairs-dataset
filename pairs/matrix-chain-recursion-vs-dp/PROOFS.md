# Proofs: matrix-chain ordering, plain recursion vs dynamic programming

This file proves every claim that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): correctness, the exact call and split counts of the recursion and its
Θ(3ⁿ) time, the DP's exact split count and Θ(n³) time, space, the count of parenthesisations, and the unit-cost
caveat. The statements in the entry's `background` field (the published O(n log n) algorithm and the report on its
proof) are cited from the literature and are not proved here. Each section ends with the
deterministic checks of its computable facts; a check covers only the inputs it states.

**Notation and cost model.** Matrix k (0-based, as in the code) has shape dims[k] × dims[k + 1]; multiplying a p × q
matrix by a q × r matrix with the schoolbook method costs pqr scalar multiplications. Machine-model assumptions
(not proved here): arithmetic on the cost values and indexing cost O(1) (see §5 for why the values stay small in the
harness), `min` over a generator of t values costs Θ(t) plus the generator's work, a Python call costs O(1), and
allocating a list of length t costs Θ(t + 1). A *split evaluation* is one evaluation of
`cost(i, k) + cost(k + 1, j) + dims[i] * dims[k + 1] * dims[j + 1]` (recursion) or of
`m[i][k] + m[k + 1][j] + dims[i] * dims[k + 1] * dims[j + 1]` (DP); each makes 2 multiplications and 2 additions.

## 1. Correctness

A *parenthesisation* of the matrices i..j is a full binary tree whose leaves are i..j in order; an internal node
whose left subtree holds i′..k and right subtree k + 1..j′ multiplies a dims[i′] × dims[k + 1] matrix by a
dims[k + 1] × dims[j′ + 1] matrix, at cost dims[i′]·dims[k + 1]·dims[j′ + 1]. The cost of the tree is the sum over
its internal nodes. Let M(i, j) be the least cost over the parenthesisations of i..j.

**Lemma 1.** M(i, i) = 0 and M(i, j) = min_{i≤k<j} [M(i, k) + M(k + 1, j) + dims[i]·dims[k + 1]·dims[j + 1]].

*Proof.* A single matrix needs no multiplication. For i < j, the root of a tree on i..j splits it at some k into a
tree on i..k and a tree on k + 1..j, which can be chosen independently; the root's product costs
dims[i]·dims[k + 1]·dims[j + 1] and the rest is the sum of the two subtree costs. Minimising over k and over the two
subtrees gives the recurrence. ∎

**Theorem 1.** `matrix_chain_recursive` and `matrix_chain_dp` both return M(0, n − 1) for n ≥ 1, and 0 for n = 0.

*Proof.* The recursion evaluates the recurrence of Lemma 1 top-down (induction on j − i). The DP fills `m[i][j]` for
increasing length j − i + 1; every split reads `m[i][k]` and `m[k + 1][j]`, which are shorter and already final (the
diagonal is initialised to 0), so by induction on the length `m[i][j]` = M(i, j). For n = 0 both return 0, and for
n = 1 the recursion returns cost(0, 0) = 0 and the DP `m[0][0]` = 0. ∎

**Check.** `tests/test_proofs_matchain.py`, `test_correct_against_tree_enumeration`: both outputs equal the minimum
over all parenthesisations, enumerated explicitly as trees and costed by multiplying out the shapes (no
recurrence), on 30 random chains for each n = 0..9 (dimensions 1..50, seed 1); the number of trees is the Catalan
number of §4. The harness check is exact only for n ≤ 2; this oracle covers n ≤ 9.

## 2. The plain recursion: 3^(n−1) calls, Θ(3ⁿ) time, Θ(n) depth

**Theorem 2.** For n ≥ 1, on every input, `matrix_chain_recursive` calls `cost` exactly 3^(n−1) times and makes
exactly (3^(n−1) − 1)/2 split evaluations (3^(n−1) − 1 multiplications). Its time is Θ(3ⁿ), and the nesting depth of
`cost` is n, so its space is Θ(n).

*Proof.* Let K(L) and S(L) be the calls and split evaluations of a call on L matrices. A call with L = 1 returns at
once: K(1) = 1, S(1) = 0. A call with L ≥ 2 makes L − 1 split evaluations, each calling `cost` on lengths k and
L − k for k = 1..L − 1 (no short-circuit; `min` consumes the whole generator), so
K(L) = 1 + Σ_{k=1}^{L−1} (K(k) + K(L − k)) = 1 + 2 Σ_{t=1}^{L−1} K(t) and S(L) = (L − 1) + 2 Σ_{t=1}^{L−1} S(t).
Then K(2) = 3, S(2) = 1, and subtracting the identities for L − 1 (L ≥ 3) gives K(L) = 3K(L − 1) and
S(L) = 3S(L − 1) + 1; hence K(L) = 3^(L−1) and S(L) = (3^(L−1) − 1)/2 for L ≥ 1. The work of a call is O(1) plus
O(1) per split evaluation, so the time is Θ(K(n) + S(n)) = Θ(3ⁿ). (The entry's sketch T(n) = Σ_k (T(k) + T(n − k))
+ Θ(n), so T(n) − T(n − 1) = 2T(n − 1) + Θ(1), is this computation with the counts left implicit.) Depth: the
length decreases by at least 1 from a call to its callee, so at most n calls of `cost` are nested, and the first
split of each call, k = i, calls `cost(i + 1, j)` after the leaf `cost(i, i)`: the chain
cost(0, n − 1) → cost(1, n − 1) → … → cost(n − 1, n − 1) has n calls. Each call adds O(1) frames (its own and
the generator of `min`). ∎

**Check.** `tests/test_proofs_matchain.py`, `test_recursion_counts`: calls of `cost` (profiler hook) = 3^(n−1),
multiplications (an instrumented number type wrapped around the dimensions) = 3^(n−1) − 1, nesting depth of `cost`
= n, for n = 1..10, two chains each (seed 2); n = 0 makes no call. The V2 measurement times the recursion against
3ⁿ (n = 7..12); a measurement, not part of the proof.

## 3. The DP: (n³ − n)/6 split evaluations, Θ(n³) time, Θ(n²) space

**Theorem 3.** For every n ≥ 0 and every input, `matrix_chain_dp` makes exactly
Σ_{L=2}^{n} (n − L + 1)(L − 1) = (n + 1)n(n − 1)/6 = (n³ − n)/6 split evaluations ((n³ − n)/3 multiplications) and
allocates an n × n table, so it takes Θ(n³) time (n ≥ 2) and Θ(n²) space.

*Proof.* For each length L = 2..n there are n − L + 1 intervals, each with L − 1 splits. With t = L − 1:
Σ_{t=1}^{n−1} (n − t)t = n·n(n − 1)/2 − (n − 1)n(2n − 1)/6 = (n + 1)n(n − 1)/6. The table has n² entries, built in
Θ(n²). For n ≥ 2 the split count is ≥ n³/8 (n³ − n ≥ 3n³/4 for n ≥ 2), so the time is Θ(n³). ∎

**Check.** `tests/test_proofs_matchain.py`, `test_dp_counts`: multiplications = (n³ − n)/3 and the table at return
has n rows of length n, for n = 0..60 (seed 3). The V2 measurement times the DP against n³ (n = 25..150); a
measurement.

## 4. The number of parenthesisations (`relationship`)

**Theorem 4.** The number P(n) of parenthesisations of n ≥ 1 matrices is the Catalan number
C_{n−1} = C(2n − 2, n − 1)/n, and 4^(n−1)/(2n√(n − 1)) ≤ P(n) ≤ 4^(n−1)/(n√(3n − 2)) for n ≥ 2; so
P(n) = Θ(4ⁿ/n^(3/2)), which exceeds the recursion's 3^(n−1) calls exactly for n ≥ 18 (§6).

*Proof.* P(1) = 1 and P(n) = Σ_{k=1}^{n−1} P(k)P(n − k) (split at the root). The series B(x) = Σ_{n≥1} P(n)xⁿ
therefore satisfies B = x + B², and since B(0) = 0, B(x) = (1 − √(1 − 4x))/2. By the binomial series,
√(1 − 4x) = Σ_n C(1/2, n)(−4x)ⁿ, so P(n) = −(1/2) C(1/2, n)(−4)ⁿ for n ≥ 1. Writing out the generalised binomial
coefficient, C(1/2, n) = (1/2)(1/2 − 1)…(1/2 − n + 1)/n! = (−1)^(n−1) · 1·3·5…(2n − 3)/(2ⁿ n!), and
1·3·5…(2n − 3) = (2n − 2)!/(2^(n−1) (n − 1)!) (the empty product 1 for n = 1). Hence
P(n) = (1/2) · 4ⁿ · (2n − 2)!/(2ⁿ · 2^(n−1) · n! (n − 1)!) = (2n − 2)!/(n! (n − 1)!) = C(2n − 2, n − 1)/n. For the
bounds, write k = n − 1 ≥ 1 and use
4^k/√(4k) ≤ C(2k, k) ≤ 4^k/√(3k + 1), proved by induction from C(2k + 2, k + 1) = C(2k, k)·4(2k + 1)/(2k + 2): both
hold with equality at k = 1 (C(2, 1) = 2), the lower step reduces to (2k + 1)² ≥ 4k(k + 1), and the upper step to
(2k + 1)²(3k + 4) ≤ (2k + 2)²(3k + 1), i.e. 12k³ + 28k² + 19k + 4 ≤ 12k³ + 28k² + 20k + 4. ∎

The entry's former "~4^n / n^1.5" (asymptotic equality) was wrong: by Theorem 4, for n ≥ 2 the ratio
P(n)·n^(3/2)/4ⁿ lies between √n/(8√(n − 1)) ≥ 1/8 and √n/(4√(3n − 2)) ≤ 0.18, so it stays below 1; Θ is what is
meant.

**Check.** `tests/test_proofs_matchain.py`, `test_catalan`: the recurrence equals C(2n − 2, n − 1)/n for n = 1..60,
the explicit tree enumeration finds that many trees for n = 1..9, and the two bounds on C(2k, k) hold for
k = 1..2000 (exact integer arithmetic); the ratio P(n)·n^(3/2)/4ⁿ lies in [1/8, 0.18] for n = 2..400;
`test_recursion_vs_enumeration`: 3^(n−1) < P(n) exactly for n ≥ 18 within n = 1..60 (equal at n = 1), g(20) > 1.35
and g(n + 1)/g(n) > 1 for n = 6..400.

## 5. Unit-cost arithmetic (`caveats`)

The harness draws dimensions from 1..50, so every product dims[i]·dims[k + 1]·dims[j + 1] is at most 50³ = 125000
and every cost value (of a parenthesisation of at most n matrices, n − 1 products) is at most (n − 1)·125000; for the
largest V2 size, n = 150, this is below 2^25. So all arithmetic is on small integers, as the caveat says.

## 6. The separation (T2)

Both algorithms return M(0, n − 1) (Theorem 1); the recursion takes Θ(3ⁿ) (Theorem 2), the DP Θ(n³) (Theorem 3). The
recursion re-solves the n(n + 1)/2 subchains i..j many times; the DP solves each once.

*Recursion against full enumeration.* The recursion's 3^(n−1) calls are fewer than the P(n) parenthesisations
exactly for n ≥ 18: P(1) = 1 = 3⁰, and 3^(n−1) > P(n) for 2 ≤ n ≤ 17 (direct computation; e.g. P(17) = 35 357 670 <
3^16 = 43 046 721 and P(18) = 129 644 790 > 3^17 = 129 140 163; see the check). For n ≥ 20, Theorem 4 gives
P(n)/3^(n−1) ≥ g(n) = (4/3)^(n−1)/(2n√(n − 1)); g(20) > 1.35, and g(n + 1)/g(n) = (4/3)·(n/(n + 1))·√((n − 1)/n) is
increasing in n and exceeds 1 from n = 6 on (it is about 1.043 at n = 6), so g(n) > 1 for all n ≥ 20; n = 18, 19
are covered by the direct computation. So for large n plain recursion is already better than full enumeration;
both are exponential.

## Claim map

| Claim (location) | Proof |
|---|---|
| recursion and DP correct (`algorithms[*].correctness`) | Lemma 1, Theorem 1 |
| recursion Θ(3ⁿ), the recurrence in its correctness field and docstring, Θ(n) space | Theorem 2 |
| DP Θ(n³), Θ(n²) cells × O(n) splits, Θ(n²) space | Theorem 3 |
| Θ(n²) distinct subchains (README) | §6 (n(n + 1)/2) |
| parenthesisations: Catalan, Θ(4ⁿ/n^1.5) (`relationship`) | Theorem 4 |
| dimensions are small, arithmetic is unit cost (`caveats`) | §5 |
| T2 | §6 |
