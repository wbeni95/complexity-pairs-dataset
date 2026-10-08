# Worst-case total imbalance of merging adjacent piles: cubic interval DP vs endpoint DP

> **Provenance: own result.** No statement of the endpoint law for this merge cost, or of the endpoint DP for this
> problem, was found in the literature checked (see [Literature checked](#literature-checked)). This is a statement
> about that search, not a claim of priority. The proof rests on the note
> [endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/) (own result).

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact comparison counts) · **Proofs:**
[PROOFS.md](PROOFS.md) (every claim of this entry) and the note above.

**Problem.** A row of n + 1 piles has sizes s₀, …, sₙ ≥ 0 (n ≥ 0). A merge joins two adjacent piles of sizes L (left)
and R (right) into one pile of size L + R and costs its imbalance |L − R|. After n merges one pile is left. Compute
the largest possible total imbalance over all merge orders.

The total depends only on the merge tree (the full binary tree whose leaves are s₀, …, sₙ in order). With
S(x, y) = s_x + … + s_y, the row of piles i..j has the interval recurrence

  c(i, i) = 0,  c(i, j) = max_{i<k≤j} [ |S(i, k−1) − S(k, j)| + c(i, k−1) + c(k, j) ],

where the split k means that the last merge of the row joins the blocks i..k−1 and k..j. The answer is c(0, n).

| Algorithm | Time (n merges) | Exact comparisons (every input) | Of these, between candidate values | Implementation |
|---|---|---|---|---|
| Interval DP, every split | Θ(n³) | n(n+1)(2n+1)/6 | (n+1)n(n−1)/6 | [cubic_dp.py](implementations/cubic_dp.py) |
| Endpoint DP: splits i+1 and j only | Θ(n²) | n(3n−1)/2 | n(n−1)/2 | [endpoint_dp.py](implementations/endpoint_dp.py) |

**What is counted.** Every comparison of two size-derived values. Each merge cost |L − R| is computed with one
comparison (as L − R or R − L), once per candidate split: n(n+1)(n+2)/6 times in the cubic DP and n² times in the
endpoint DP. The remaining comparisons are between candidate values.

**Why it's here.** The imbalance depends on where the row is split: for sizes (1, 1, 0) the row 0..2 has the split
costs |1 − 1| = 0 at k = 1 and |2 − 0| = 2 at k = 2. The endpoint law of the interval-weight entry
[max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/)
(Theorem E′) is stated for weights that depend on the row only. The split-dependent rotation condition RS3 of the
note's Corollary 2 fails for this weight (below). The weaker condition RS3w holds for non-negative sizes, and the
note's Theorem 1 gives the endpoint law from it. So two candidates per row suffice, and an optimal merge order
can be taken to be a caterpillar (every merge joins a single original pile to a block).

## Correctness of the endpoint DP

**Corollary.** Let s₀, …, sₙ ≥ 0. Then for every row i..j with j > i:
- (a) k = i+1 or k = j attains the maximum in the recurrence;
- (b) for j − i ≥ 2, c(i, j) = max( |sᵢ − S(i+1, j)| + c(i+1, j), |S(i, j−1) − sⱼ| + c(i, j−1) );
- (c) some maximum-imbalance merge tree of the row is a caterpillar.

*Proof.* The recurrence is the max-recurrence with the split-dependent weights w(i, k, j) = |S(i, k−1) − S(k, j)|.
Lemma 11 of the note [endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/)
proves for these weights, when all sizes are ≥ 0, that the two rotation changes Δ_R and Δ_L of every rotation at a
root can be ≤ 0 together only if both are 0. That implies the condition RS3w, and Theorem 1 of the same note gives
(a), (b) and (c) (its path trees are the caterpillars, by the correspondence in the note's Setting). ∎

RS3 itself fails. For sizes (1, 0, 1, 2) the only index tuple is (i, a, k, b, j) = (0, 1, 2, 3, 3), with block sums
X, Y, Z, U = 1, 0, 1, 2, L = 1 and R = 3. With the note's formulas,
Δ_R = |X − (Y + R)| + |Y − R| − |L − R| − |X − Y| = 2 + 3 − 2 − 1 = 2 and
Δ_L = |L + Z − U| + |L − Z| − |L − R| − |Z − U| = 0 + 0 − 2 − 1 = −3, so Δ_R + Δ_L < 0. The endpoint DP is still
exact there, as Theorem 1 says.

The cubic DP is correct for any sizes: the merge trees of the row i..j whose last merge joins i..k−1 and k..j are the
pairs (merge tree of i..k−1, merge tree of k..j), and such a tree costs |S(i, k−1) − S(k, j)| plus the costs of its
two parts ([PROOFS.md](PROOFS.md), section 3).

**The counts.** The loops and the comparisons they execute do not depend on the sizes, so every count below holds
on every input. A row of length L = j − i tries L splits in the cubic DP: L merge-cost comparisons and L − 1
comparisons between candidates. There are n − L + 1 rows of length L, and
Σ_{L=1..n} L(n + 1 − L) = (n+1)·n(n+1)/2 − n(n+1)(2n+1)/6 = n(n+1)(n+2)/6 candidate splits. So the cubic DP makes
n(n+1)(n+2)/6 merge-cost comparisons and Σ_{L=1..n} (n + 1 − L)(L − 1) = n(n+1)(n+2)/6 − n(n+1)/2 = (n+1)n(n−1)/6
candidate comparisons, n(n+1)(n+2)/6 + (n+1)n(n−1)/6 = n(n+1)(2n+1)/6 in all. The endpoint DP makes one merge-cost
comparison for each of the n rows of length 1, and two merge-cost comparisons and one candidate comparison for each
of the n(n−1)/2 rows of length ≥ 2: n² merge-cost and n(n−1)/2 candidate comparisons, n + 3n(n−1)/2 = n(3n−1)/2 in
all. [PROOFS.md](PROOFS.md), sections 1 and 2, reads these counts off the code.

## Limits

The five merge trees of four piles are ((s₀s₁)(s₂s₃)) and the four caterpillars (((s₀s₁)s₂)s₃), ((s₀(s₁s₂))s₃),
(s₀((s₁s₂)s₃)) and (s₀(s₁(s₂s₃))); the costs below are listed merge by merge in this order.
- **Non-negative sizes are needed.** With a negative size the endpoint law can fail. For sizes (0, −1, 1, 0) the five
  trees cost 1 + 1 + 2 = 4, then 1 + 2 + 0 = 3, 2 + 0 + 0 = 2, 2 + 0 + 0 = 2 and 1 + 2 + 0 = 3. The maximum 4 needs
  the middle split; the endpoint DP returns 3.
- **The direction matters.** The same merge cost under *min* (minimise Σ |L − R|) is not covered, and the endpoint
  rule is wrong there. For sizes (0, 1, 1, 0) the five trees cost 1 + 1 + 0 = 2, then 1 + 0 + 2 = 3, 0 + 2 + 2 = 4,
  0 + 2 + 2 = 4 and 1 + 0 + 2 = 3: the minimum is 2, and the best caterpillar costs 3.
- **No lower bound.** Θ(n²) is the cost of the endpoint DP, not a lower bound for the problem; no lower bound is
  claimed.
- **Exact arithmetic** is assumed: ties are decided by exact equality. For sizes ≥ 0 every number the DPs compute lies
  between 0 and n times the total size ([PROOFS.md](PROOFS.md), section 6).

## Verification

- **V1.** As in the entry for the merge cost max(L, R): n = 0..10, 12, 16, 25, 40 and 70, with 12 instances per n
  from 12 families of non-negative sizes. `harness.check` enumerates every merge tree for n ≤ 9 (costed from direct
  sums) and checks an exact certificate for 10 ≤ n ≤ 150: an explicit caterpillar as the lower bound, and a table U
  of best caterpillar values accepted only if U(a, b) ≥ |S(a, k−1) − S(k, b)| + U(a, k−1) + U(k, b) for every split,
  which bounds every merge tree by induction ([PROOFS.md](PROOFS.md), section 7).
- **Tests** ([tests/test_entry_merge_imbalance.py](../../tests/test_entry_merge_imbalance.py), under a minute):
  - the two DPs agree with each other and with the tree enumeration on every size vector with n ≤ 4 and sizes 0..4,
    n = 5 and sizes 0..3, and n = 6 and sizes 0..2 (10 188 vectors; every contiguous sub-row is itself in the set);
  - `check` accepts the true value and rejects the value ± 1 on seeded instances, and the certificate equals the
    enumeration on 60 seeded instances with n ≤ 8;
  - `check` returns True for both outputs on every instance of the validator's V1 battery (its seeds, 16 sizes × 12
    trials);
  - the comparison counts equal n(n+1)(2n+1)/6 for n = 0..40 and n(3n−1)/2 for n = 0..80, and the additions and
    subtractions equal (n + 1) + 5n(n+1)(n+2)/6 and (n + 1) + 5n², each for all 11 integer families at every n;
  - on one seeded family per n (n = 0..30), the candidate-only counts are (n+1)n(n−1)/6 and n(n−1)/2;
  - the table has n + 1 rows of length n + 1 and the prefix list n + 2 entries (n = 0..40 and 0..80), and every
    table entry lies between 0 and (j − i)·S(i, j) (120 seeded instances, n ≤ 40);
  - the RS3 failure on (1, 0, 1, 2) with the endpoint DP exact, the split dependence on (1, 1, 0), and the two
    counterexamples of the Limits section, merge by merge.
- **Theorem 1 and Lemma 11** are checked separately by the note's
  [verify.py](../../theorems/endpoint-law-split-dependent-weights/verify.py).
- **V2 (exact counts, `measure: "reported"`).** The harness's CountingInt counts comparisons of two size-derived values
  made by the unchanged implementations; `generate_scaling` draws one of the 11 integer families, and the counts depend
  on n only. Fits with tolerance 0.02. Every claimed count fits with α = 1.000 and every rival is rejected (the α
  values below are printed by `python tools/validate.py pairs/max-merge-imbalance-cubic-dp-vs-endpoint-dp --scaling
  -v`):

  | Algorithm (n values) | Claimed count | Rivals (α) |
  |---|---|---|
  | cubic DP (16..128) | n(n+1)(2n+1)/6 | n² 1.481, n² log n 1.306, n³/log n 1.084, n³ log n 0.906, n⁴ 0.741 |
  | endpoint DP (32..512) | n(3n−1)/2 | n 2.003, n log n 1.654, n^1.5 1.336, n²/log n 1.120, n² log n 0.906, n³ 0.668 |

  No counted comparison happens inside a CPython built-in.
- **Level.** V2. The written proofs are in [PROOFS.md](PROOFS.md) and the note; they are not machine-checked.

## Literature checked

This is a statement about a search, not a priority claim.
- **Credit for the interval-weight case** (background, cited). Qian & Wang (2004, Lemma 1): in a semi-circled convex
  polygon, one of the two extreme edges belongs to a maximum weight triangulation. The entry
  [max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/) writes
  their exchange argument out for inclusion-monotone interval weights (Theorem E′). The merge cost of this entry
  depends on the split.
- **Credit for a merge special case** (background, cited). For the merge cost L + R, a 2020 article on interval
  dynamic programming in the Tencent Cloud developer community (https://cloud.tencent.com/developer/article/1697989)
  gives code for the maximum total cost that tries only the two end splits of every row, without a proof.
- **Searched, with no relevant hit beyond the credits above:** bibliographic databases (Crossref, OpenAlex, arXiv;
  titles and abstracts) for stone merging and merging adjacent piles (maximum and minimum total cost), small-to-large
  merging, alphabetic trees, maximum weight triangulations, worst-case and maximum-cost binary search trees, interval
  dynamic programming with maximisation and endpoint splits, and the quadrangle inequality under maximisation.
  Wang, Chin & Yang (1999), an O(n²) algorithm for maximum weight triangulations of inscribed polygons, was seen only
  as a title and summary.

No source found states an endpoint law for the merge cost |L − R|.

## Credit

- J. Qian, C. A. Wang (2004). *Maximum weight triangulation of a special convex polygon*. 20th European Workshop on
  Computational Geometry (EWCG 2004), Seville. [hdl:11441/55702](http://hdl.handle.net/11441/55702). Lemma 1: an
  endpoint law for the Euclidean chord weights of semi-circled convex polygons (maximum weight triangulations).
- Tencent Cloud developer community (2020). *Dynamic programming: interval DP* (title translated).
  https://cloud.tencent.com/developer/article/1697989. Endpoint-only code for the merge cost L + R, without a proof.

Related: [theorems/endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/) (the
proof), [max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp](../max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp/)
(merge cost max(L, R)),
[min-merge-cost-smaller-part-cubic-dp-vs-closed-form](../min-merge-cost-smaller-part-cubic-dp-vs-closed-form/)
(merge cost min(L, R), minimised).
