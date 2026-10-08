# Merging adjacent piles at the cost of the smaller part: cubic interval DP vs the closed form S − max s

> **Provenance: own result (elementary).** No statement of the closed form was found in the literature checked (see
> [Literature checked](#literature-checked)). This is a statement about that search, not a claim of priority.

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact comparison counts) · **Proofs:**
[PROOFS.md](PROOFS.md) (every claim of this entry, with the proofs below).

**Problem.** A row of n + 1 piles has sizes s₀, …, sₙ ≥ 0 (n ≥ 0). A merge joins two adjacent piles of sizes L (left)
and R (right) into one pile of size L + R and costs min(L, R), the size of the smaller part. After n merges one pile
is left. Compute the smallest possible total cost over all merge orders.

The total depends only on the merge tree (the full binary tree whose leaves are s₀, …, sₙ in order). With
S(x, y) = s_x + … + s_y, the row of piles i..j has the interval recurrence

  c(i, i) = 0,  c(i, j) = min_{i<k≤j} [ min(S(i, k−1), S(k, j)) + c(i, k−1) + c(k, j) ],

where the split k means that the last merge of the row joins the blocks i..k−1 and k..j. The answer is c(0, n).

| Algorithm | Time (n merges) | Exact comparisons (every input) | Implementation |
|---|---|---|---|
| Interval DP, every split | Θ(n³) | n(n+1)(2n+1)/6, of which (n+1)n(n−1)/6 between candidate values | [cubic_dp.py](implementations/cubic_dp.py) |
| Closed form S(0, n) − max sₗ | Θ(n) | n | [closed_form.py](implementations/closed_form.py) |

**What is counted.** Every comparison of two size-derived values. In the DP, each merge cost min(L, R) is one
comparison, made once per candidate split (n(n+1)(n+2)/6 times); the remaining comparisons are between candidate
values. The closed form makes the n comparisons of a running maximum.

**Why it's here.** The cubic DP is correct for every merge cost. For the cost min(L, R) the optimum has a closed
form, so a single pass suffices. Every row also has a minimising split at one of its ends. The rotation conditions
under which the note
[endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/) proves such an endpoint
law fail for this merge cost on some non-negative sizes (section [The endpoint law](#the-endpoint-law)), so here the
law is derived from the closed form.

**The cubic DP** is correct for any sizes (and any merge cost): the merge trees of the row i..j whose last merge joins
i..k−1 and k..j are the pairs (merge tree of i..k−1, merge tree of k..j), and such a tree costs
min(S(i, k−1), S(k, j)) plus the costs of its two parts; induction on j − i ([PROOFS.md](PROOFS.md), section 3).

## The closed form

**Proposition.** Let s₀, …, sₙ ≥ 0, and write M(i, j) = max(sᵢ, …, sⱼ). Then for every row i..j,

  c(i, j) = S(i, j) − M(i, j),

and a caterpillar that starts at a pile of size M(i, j) and adds the neighbouring piles one at a time attains it.

*Proof.* **Lower bound:** every merge tree of the row i..j costs at least S(i, j) − M(i, j). Induction on the number
of piles. A single pile costs 0 = s − s. Otherwise let the last merge join blocks of sizes L and R whose largest piles
are m_L and m_R, and assume m_L ≥ m_R (the other case is the mirror image). By the induction hypothesis the two
subtrees cost at least L − m_L and R − m_R. The largest pile of a block of non-negative sizes is at most the block's
sum, so m_R ≤ R; and m_R ≤ m_L ≤ L. Hence m_R ≤ min(L, R), and the tree costs at least
min(L, R) + (L − m_L) + (R − m_R) ≥ L + R − m_L = S(i, j) − M(i, j), since M(i, j) = m_L.

**Upper bound:** start with a pile of size M = M(i, j) and add the neighbouring piles one at a time, in any order that
keeps the block contiguous. When a pile of size s is added, the block contains the pile of size M, so its size is at
least M ≥ s (sizes are non-negative), and the merge costs min(block, s) = s. Every pile except the first is added
once, so the total is S(i, j) − M. ∎

So c(0, n) = S(0, n) − max sₗ, which the closed form computes with n comparisons, n additions and one subtraction.

## The counts

The loops and the comparisons they execute do not depend on the sizes, so the counts hold on every input. A row of
length L = j − i tries L splits in the cubic DP: L merge-cost comparisons and L − 1 comparisons between candidates.
There are n − L + 1 rows of length L, and Σ_{L=1..n} L(n + 1 − L) = (n+1)·n(n+1)/2 − n(n+1)(2n+1)/6 = n(n+1)(n+2)/6
candidate splits. So the cubic DP makes n(n+1)(n+2)/6 merge-cost comparisons and
Σ_{L=1..n} (n + 1 − L)(L − 1) = n(n+1)(n+2)/6 − n(n+1)/2 = (n+1)n(n−1)/6 candidate comparisons,
n(n+1)(2n+1)/6 in all. The closed form compares each of s₁, …, sₙ once with the running maximum: n comparisons.

## The endpoint law

**Corollary (endpoint law).** For s ≥ 0, every row i..j with j > i has a minimising split k ∈ {i+1, j}.

*Proof.* Write M = M(i, j).
- If some pile of size M lies in i+1..j, take k = i+1: the last merge joins the pile sᵢ to the block i+1..j. That
  block contains a pile of size M, so its size S(i+1, j) is at least M ≥ sᵢ, and the merge costs sᵢ. By the
  Proposition, c(i+1, j) = S(i+1, j) − M(i+1, j) = S(i+1, j) − M, so the split costs sᵢ + S(i+1, j) − M =
  S(i, j) − M = c(i, j).
- Otherwise sᵢ = M is the only largest pile, and we take k = j: the block i..j−1 contains sᵢ, so its size is at
  least M ≥ sⱼ, and the merge costs sⱼ. Since M(i, j−1) = sᵢ = M, the split costs sⱼ + S(i, j−1) − M = c(i, j). ∎

So restricting the minimum to the two end splits does not change any c(i, j): the endpoint DP (Θ(n²)) is also exact
here. This entry does not list it as a separate algorithm. The rotation theorems of the note
[endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/) do *not* give this law
for all non-negative sizes. Their min forms need, for w(i, k, j) = min(S(i, k−1), S(k, j)), the condition RS3 or
RS3w for −w. For four piles s₀, …, s₃ the only index tuple is (i, a, k, b, j) = (0, 1, 2, 3, 3), with L = s₀ + s₁,
R = s₂ + s₃ and the rotation changes Δ_R = min(s₀, s₁ + R) + min(s₁, R) − min(L, R) − min(s₀, s₁) and
Δ_L = min(L + s₂, s₃) + min(L, s₂) − min(L, R) − min(s₂, s₃) of w:
- **RS3 for −w** asks Δ_R + Δ_L ≤ 0. For the piles (0, 1, 1, 2): L = 1, R = 3, Δ_R = 0 + 1 − 1 − 0 = 0 and
  Δ_L = 2 + 1 − 1 − 1 = 1, so the sum is 1 > 0. With positive piles, (1, 1, 2, 4): L = 2, R = 6,
  Δ_R = 1 + 1 − 2 − 1 = −1 and Δ_L = 4 + 2 − 2 − 2 = 2.
- **RS3w for −w** asks that Δ_R ≥ 0 and Δ_L ≥ 0 imply Δ_R = 0. For the piles (2, 1, 0, 1): L = 3, R = 1,
  Δ_R = 2 + 1 − 1 − 1 = 1 and Δ_L = 1 + 0 − 1 − 0 = 0.

The endpoint law holds on these rows as on all others (Corollary; checked by the tests).

## Limits

- **Non-negative sizes are needed.** With a negative size the closed form can fail. Sizes (−1, 0, 0) have two merge
  trees: ((s₀s₁)s₂) costs min(−1, 0) + min(−1, 0) = −2 and (s₀(s₁s₂)) costs min(0, 0) + min(−1, 0) = −1. The minimum
  is −2; the formula gives −1 − 0 = −1.
- **The direction matters.** Maximising the same total (max Σ min(L, R)) is a different problem. Neither the closed
  form nor the endpoint rule applies there. For sizes (1, 1, 1, 1) the tree ((s₀s₁)(s₂s₃)) costs 1 + 1 + 2 = 4, and
  each of the four caterpillars costs 1 + 1 + 1 = 3.
- **No lower bound** is claimed for the problem.
- **Exact arithmetic** is assumed. For sizes ≥ 0 every number the cubic DP computes lies between 0 and n times the
  total size ([PROOFS.md](PROOFS.md), section 6).

## Verification

- **V1.** The validator runs n = 0..10, 12, 16, 25, 40 and 70, with 12 instances per n from 12 families of
  non-negative sizes: bits, small values with many ties, all zero, constant, wide values up to 10⁶, one heavy pile,
  geometric, ramps, sparse, valley, peak, and exact rationals. `harness.check` is an oracle written separately from
  the implementations:
  - **n ≤ 9:** every merge tree is enumerated (Catalan(n) trees) and costed from direct sums, with no recurrence.
  - **10 ≤ n ≤ 150:** an exact certificate. The upper bound is an explicit caterpillar from a largest pile, costed
    from direct sums. The lower bound is the table B(a, b) = S(a, b) − M(a, b), accepted only if
    B(a, b) ≤ min(S(a, k−1), S(k, b)) + B(a, k−1) + B(k, b) for *every* split; by induction over the last merge, every
    merge tree of the row a..b then costs at least B(a, b). So a valid certificate checks the closed form on that
    instance instead of assuming it ([PROOFS.md](PROOFS.md), section 7).
- **Tests** ([tests/test_entry_merge_smaller.py](../../tests/test_entry_merge_smaller.py), under a minute):
  - the cubic DP, the closed form and the tree enumeration agree on every size vector with n ≤ 4 and sizes 0..4,
    n = 5 and sizes 0..3, and n = 6 and sizes 0..2 (10 188 vectors); in every row of every such vector the DP value
    equals S − max and some minimising split is an end; for n ≤ 5, every caterpillar whose first merge involves a
    largest pile costs exactly S − max (the upper bound of the Proposition, for every admissible order);
  - `check` accepts the true value and rejects the value ± 1 on seeded instances, and the certificate equals the
    enumeration on 60 seeded instances with n ≤ 8;
  - `check` returns True for both outputs on every instance of the validator's V1 battery (its seeds, 16 sizes × 12
    trials);
  - the comparison counts equal n(n+1)(2n+1)/6 for n = 0..40 and n for n = 0..199, 1000 and 4096, and the additions
    and subtractions equal (n + 1) + 2n(n+1)(n+2)/3 and n + 1, each for all 11 integer families at every n; on one
    seeded family per n (n = 0..30), the candidate-only count of the DP is (n+1)n(n−1)/6;
  - the DP table has n + 1 rows of length n + 1 and the prefix list n + 2 entries (n = 0..40), every table entry lies
    between 0 and (j − i)·S(i, j) (120 seeded instances, n ≤ 40), and the closed form keeps only its three variables
    and the loop variable (named variables; the slice sizes[1:] is a temporary) (n = 0..49);
  - the endpoint DP (two end splits per row) equals the cubic DP on the 10 188 vectors above;
  - the rotation-condition failures, the split dependence on (1, 1, 0) and the counterexamples above, value by
    value.
- **V2 (exact counts, `measure: "reported"`).** The harness's CountingInt counts comparisons of two size-derived values
  made by the unchanged implementations; `generate_scaling` draws one of the 11 integer families, and the counts depend
  on n only. Fits with tolerance 0.02. Every claimed count fits with α = 1.000 and every rival is rejected (the α
  values below are printed by `python tools/validate.py pairs/min-merge-cost-smaller-part-cubic-dp-vs-closed-form
  --scaling -v`):

  | Algorithm (n values) | Claimed count | Rivals (α) |
  |---|---|---|
  | cubic DP (16..128) | n(n+1)(2n+1)/6 | n² 1.481, n² log n 1.306, n³/log n 1.084, n³ log n 0.906, n⁴ 0.741 |
  | closed form (16..4096) | n | √n 2.000, log n 4.988, n log n 0.836, n² 0.500 |

  No counted comparison happens inside a CPython built-in.
- **Level.** V2. The Proposition, its corollary and the counts have written proofs (above and in
  [PROOFS.md](PROOFS.md)); they are not machine-checked.

## Literature checked

This is a statement about a search, not a priority claim. Bibliographic databases (Crossref, OpenAlex, arXiv; titles
and abstracts) were searched for stone merging and merging adjacent piles (minimum and maximum total cost),
small-to-large merging, and alphabetic trees, without a relevant hit. No source found states the closed form
S − max s for merging adjacent piles at the cost of the smaller part.

## Credit

- J. Qian, C. A. Wang (2004). *Maximum weight triangulation of a special convex polygon*. 20th European Workshop on
  Computational Geometry (EWCG 2004), Seville. [hdl:11441/55702](http://hdl.handle.net/11441/55702). Lemma 1 (background,
  cited): in a semi-circled convex polygon, one of the two extreme edges belongs to a maximum weight triangulation, an
  endpoint law for Euclidean chord weights; the entry
  [max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/) writes
  their exchange argument out for inclusion-monotone interval weights (Theorem E′). This entry's merge cost depends on
  the split: for sizes (1, 1, 0) the row 0..2 costs min(1, 1) = 1 at the split k = 1 and min(2, 0) = 0 at k = 2.

Related: [max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp](../max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp/)
(merge cost max(L, R), maximised),
[max-merge-imbalance-cubic-dp-vs-endpoint-dp](../max-merge-imbalance-cubic-dp-vs-endpoint-dp/)
(merge cost |L − R|, maximised),
[theorems/endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/).
