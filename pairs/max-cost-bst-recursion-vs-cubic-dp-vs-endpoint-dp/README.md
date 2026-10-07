# Interval DP with inclusion-monotone weights (endpoint law; maximum-cost BST): plain recursion vs cubic DP vs endpoint DP

**Type:** T2 (naive-exp → poly), secondary T3 · **Verification:** V2 (exact comparison counts) · **Theorem E′:**
literature-based (the exchange argument of Qian & Wang 2004, Lemma 1; the proof is written out below)

**Problem.** Weights w(i, j) are given for the intervals 0 ≤ i < j ≤ n. They are *monotone under inclusion*:
w(b, c) ≤ w(a, d) whenever a ≤ b < c ≤ d. Compute c(0, n) for the max-recurrence

  c(i, i) = 0,  c(i, j) = w(i, j) + max_{i<k≤j} [c(i, k−1) + c(k, j)].

Equivalently, c(0, n) is the maximum, over all binary trees with in-order nodes 1..n, of Σ_v w(I_v), where I_v is the
interval spanned by v's subtree. The *equivalent form* is the min-recurrence with *anti-monotone* weights
(w(b, c) ≥ w(a, d)); an instance carries its direction, ("max", w) or ("min", w).

**Main instance: the maximum-cost binary search tree.** Keys k₁ < … < kₙ have access frequencies p₁..pₙ, and the
gaps between them have frequencies q₀..qₙ, all non-negative. Maximise Σ pₘ (level(kₘ) + 1) + Σ qⱼ level(gap j) over
all BSTs, with the root at level 0. This is the cost of the optimal-BST problem (Knuth 1971; entry
[optimal-bst-recursion-vs-dp-vs-knuth](../optimal-bst-recursion-vs-dp-vs-knuth)), maximised instead of minimised:
the largest weighted number of comparisons that any BST can force (a search compares with every key on its path:
level + 1 comparisons for a key, level comparisons for a gap; see the optimal-BST entry's PROOFS.md, section 6). It
is the instance with direction max and
w(i, j) = qᵢ + Σ_{l=i+1..j} (p_l + q_l); the implementations also accept it in the form (p, q).

| Algorithm | Time (n nodes) | Exact cost comparisons (every input) | Implementation |
|---|---|---|---|
| Plain recursion over the root | Θ(3ⁿ) | (3ⁿ⁻¹ − 1)/2 (n ≥ 1), with exactly 3ⁿ calls | [recursion.py](implementations/recursion.py) |
| Interval DP, every root | Θ(n³) | (n+1)n(n−1)/6 | [cubic_dp.py](implementations/cubic_dp.py) |
| Endpoint DP: roots i+1 and j only | Θ(n²) | n(n−1)/2 | [endpoint_dp.py](implementations/endpoint_dp.py) |

**Why it's here.** The recursion recomputes the Θ(n²) intervals, and tabulating them gives Θ(n³) (T2). With
monotone weights, every interval has an optimal root at one of its two ends (Theorem E′ below). So each interval
needs only two candidates, which gives Θ(n²) (T3). The plain recursion and the cubic DP are correct for any weights;
only the endpoint DP needs the monotonicity. Studied in the course of this project; the endpoint law is
literature-based (see Sources).

## Theorem E′ and its proof

**Source (credit).** Theorem E′ follows the exchange argument of Qian & Wang (2004, Lemma 1), whose setting is the maximum
weight triangulation of convex polygons. Under the standard correspondence between binary trees with in-order nodes
1..n and triangulations of a convex polygon with vertices v₀, …, v_{n+1}, the interval (i, j) is the chord
v_i v_{j+1}, the root k is the apex v_k of the triangle on that chord, and a tree rotation is a diagonal flip. The
proof below writes the argument out for interval weights that are monotone under inclusion.

**Setting.** The interval (i, j), 0 ≤ i ≤ j ≤ n, holds the nodes i+1..j; it is empty if i = j. A tree on (i, j) is
empty if i = j. Otherwise it is a root k (i < k ≤ j) with a left subtree on (i, k−1) and a right subtree on (k, j).
I_v denotes the interval of the subtree of node v. A *path tree* is a tree in which every node has at most one
non-empty subtree. The value of a tree T is val(T) = Σ_v w(I_v).

**Lemma A (the recurrence optimises over trees).** For any real weights, c(i, j) = max val(T) over the trees T on
(i, j). Also, k attains the maximum in the recurrence exactly when some optimal tree on (i, j) has root k. The
subtrees of an optimal tree are optimal for their intervals.

*Proof.* Induction on j − i. A tree with root k has value w(i, j) + val(L) + val(R), and L and R range independently
over the trees on (i, k−1) and (k, j). ∎

**Lemma B (rotations at the root).** Let T on (i, j) have root k, with non-empty subtrees whose roots are k_L (left)
and k_R (right). The right rotation at the root makes k_L the root, with k as its right child. It changes the value
by Δ_R = w(k_L, j) − w(i, k−1). The left rotation makes k_R the root and changes the value by
Δ_L = w(i, k_R − 1) − w(k, j).

*Proof.* A rotation keeps the in-order sequence, so the result is a tree on (i, j). Only the subtree intervals of the
two rotated nodes change. Before the right rotation, k spans (i, j) and k_L spans (i, k−1). After it, k_L spans
(i, j) and k spans (k_L, j). The left rotation is the mirror image. ∎

**Lemma C (monotonicity makes the two changes sum to at least 0).** In Lemma B, if w is monotone under inclusion,
then Δ_R + Δ_L ≥ 0.

*Proof.* Δ_R + Δ_L = [w(k_L, j) − w(k, j)] + [w(i, k_R − 1) − w(i, k−1)]. Since k_L < k, the interval (k, j) lies
inside (k_L, j), and both are non-empty. Since k_R − 1 ≥ k > k − 1, the interval (i, k−1) lies inside (i, k_R − 1).
Each bracket is therefore ≥ 0. ∎

**Theorem E′.** Let w be real weights that are monotone under inclusion. Then for every interval (i, j) with j > i:
- (a) some optimal (maximum-value) tree on (i, j) is a path tree;
- (b) k = i+1 or k = j attains the maximum in the recurrence;
- (c) c(i, j) = w(i, j) + max(c(i+1, j), c(i, j−1)).

*Proof.* (a) implies (b): the root of a path tree has an empty subtree, so it is i+1 or j, and Lemma A applies.
(b) implies (c): restricting the maximum to a set that contains a maximiser does not change it, and the two
candidates are c(i, i) + c(i+1, j) = c(i+1, j) and c(i, j−1) + c(j, j) = c(i, j−1).

We prove (a) by induction on j − i. For j − i ≤ 2, every tree is a path tree. Let j − i ≥ 3 and assume (a) for all
shorter intervals. Take an optimal tree on (i, j) with root k, and replace its subtrees by optimal path trees (the
induction hypothesis). The result T₀ is optimal by Lemma A. If k is an endpoint, T₀ is a path tree. Otherwise
i+1 < k < j, and we use the following claim.

*Claim.* Let T be an optimal tree on (i, j) whose root k is interior (i+1 < k < j), and whose two subtrees are path
trees with roots k_L and k_R. Then the right rotation at the root gives an optimal tree T′ with root k_L. Moreover,
either k_L = i+1, or k_L = k−1 > i+1 and both subtrees of T′ are path trees.

*Proof of the claim.* Both rotations give trees on (i, j). T is optimal, so Δ_R ≤ 0 and Δ_L ≤ 0. By Lemma C,
Δ_R + Δ_L ≥ 0. Hence Δ_R = Δ_L = 0, and T′ is optimal. The root k_L of the path tree on (i, k−1) is an end of that
interval, so k_L = i+1 or k_L = k−1. Suppose k_L ≠ i+1, so k_L = k−1 > i+1. As the right end of (i, k−1), the node
k−1 has an empty right subtree, and its left subtree A is a path tree on (i, k−2). After the rotation, the root k−1
has left subtree A. Its right subtree is k, with an empty left subtree and the old right path tree below it, which
is again a path tree. ∎

Apply the claim repeatedly, starting from T₀. While the second case occurs, the root moves one node to the left and
stays interior. So after at most k − i − 1 rotations, an optimal tree with root i+1 is reached. Its left subtree is
empty, and its right subtree is optimal on (i+1, j) (Lemma A). Replacing it by an optimal path tree (the induction
hypothesis) gives an optimal path tree on (i, j). ∎

**Corollary 1 (the equivalent min form).** If w is anti-monotone, every interval has a minimising split in
{i+1, j}, and c(i, j) = w(i, j) + min(c(i+1, j), c(i, j−1)). *Proof:* the min-recurrence with w equals −c for the
max-recurrence with −w (induction), its minimisers are the maximisers there, and −w is monotone. ∎

**Corollary 2 (strict monotonicity).** If w(i, j) > w(i+1, j) and w(i, j) > w(i, j−1) whenever j − i ≥ 2, then
every maximising split is an endpoint and *every* optimal tree is a path tree. *Proof:* strict local inequalities
make both brackets in Lemma C positive. An optimal tree with an interior root would give, after its subtrees are
replaced by optimal path trees, Δ_R + Δ_L > 0, contradicting Δ_R, Δ_L ≤ 0. The non-empty subtree of the endpoint
root is optimal on a shorter interval, so induction gives a path tree. ∎ Without strictness, non-path optimal trees
exist (all-zero weights make every tree optimal), which is why (a) says *some*.

**Remark (a local test of the hypothesis).** w is monotone under inclusion exactly when w(i, j) ≥ w(i+1, j) and
w(i, j) ≥ w(i, j−1) for all j − i ≥ 2. A nested pair (b, c) ⊆ (a, d) is reached from (a, d) by one-step shrinks
that keep the interval non-empty. The harness checks the precondition this way, in O(n²).

**Where monotonicity is used:** only in Lemma C, for the two nested pairs (k, j) ⊆ (k_L, j) and
(i, k−1) ⊆ (i, k_R − 1). There is no modularity and no quadrangle inequality.

**Extension to −∞ entries.** Let w take values in ℝ ∪ {−∞} and be monotone in the extended order, so an interval of
weight −∞ has only sub-intervals of weight −∞. Evaluate the recurrences in (max, +), where −∞ absorbs addition.
Then the endpoint recurrence of (c) gives c(i, j) on every interval.

*Proof.* Lemma A holds in (max, +), and the endpoint recurrence computes the maximum over *path* trees. Fix (i, j).
For a tree τ on (i, j), let t(τ) be its number of nodes with weight −∞ and f(τ) the sum of its finite node weights.
Let F = max_τ |f(τ)| and B = max |w| over the finite entries, and choose a real M > max(2F, B). Replacing −∞ by −M
gives a real table w_M, which is monotone: an interval of weight −∞ inside a finite one gets −M < −B ≤ the finite
weight. The value of τ under w_M is f(τ) − M·t(τ). If t(τ) < t(σ), then τ is worth more than σ, because
−F − M t(τ) > F − M − M t(τ). So the w_M-optimal trees minimise t, and among those they maximise f. By Theorem E′
one of them is a path tree π. If the minimum of t is 0, π attains the extended optimum, which is the largest f over
the trees with t = 0. Otherwise every tree, π included, is worth −∞. ∎

The mirror image holds for anti-monotone weights with +∞ entries under min (negate, as in Corollary 1: −w is
monotone with −∞ entries, and the min-recurrence with w is the negated max-recurrence with −w). +∞ under max is not
covered, since it
would create +∞ + (−∞).

**Checked step by step** ([checks script](../../experiments/2026-10-07_max_cost_bst_checks.py); its DP code is
independent of the implementations):
- **The proof run as an algorithm (section E3).** Over every monotone table of seven scopes (n = 3..7), every
  interval with an interior maximiser was taken as a starting point: 108 349 cases. In every case:
  - Δ_R and Δ_L equalled the change of the explicitly computed tree values;
  - both were ≤ 0, their sum was ≥ 0, so both were 0;
  - each rotated tree was optimal, with path subtrees whenever its root was still interior, and the procedure ended
    in an optimal path tree.

  The cases needed 1 to 5 rotations (97 959, 7360, 2301, 673 and 56 cases).
- **Corollary 2 (section E2).** Every strictly monotone table with values 0..6 for n = 4 and n = 5: 9438 tables, none
  with an interior optimum, under max with w and under min with −w.
- **The local test (sections E5 and B).** The harness's O(n²) test agreed with the O(n⁴) definition of monotonicity
  on 3000 random tables (1347 of them monotone). For BST weights, the adjacent-sum condition (next section) agreed
  with the definition on all 100 933 instances of section B.

## The maximum-cost BST

**Lemma (cost as a sum over nodes).** For BST weights w(i, j) = qᵢ + Σ_{l=i+1..j} (p_l + q_l), the cost of a BST T
equals Σ_v w(I_v). *Proof:* a frequency is counted in w(I_v) once for every key v whose subtree contains it. For a
key kₘ these are its ancestors and kₘ itself, level(kₘ) + 1 of them; for a gap, they are its ancestors, level(gap) of
them. ∎ So the maximum-cost BST is the instance ("max", w) of the problem.

**When BST weights are monotone.** w(i, j) − w(i+1, j) = qᵢ + p_{i+1} and w(i, j) − w(i, j−1) = p_j + q_j. By the
local test, the BST weights are monotone under inclusion exactly when

  q_{l−1} + p_l ≥ 0 (l = 1..n−1)  and  p_l + q_l ≥ 0 (l = 2..n).

In particular they are monotone when p, q ≥ 0.

**Corollary (Theorem E).** Let p₁, …, pₙ ≥ 0 and q₀, …, qₙ ≥ 0. Then for every interval (i, j) with j > i:
- (a) some maximum-cost BST on (i, j) is a path;
- (b) k = i+1 or k = j is a maximising root;
- (c) for j − i ≥ 2, c(i, j) = w(i, j) + max(c(i+1, j), c(i, j−1)).

*Proof:* Theorem E′ with the monotone BST weights. ∎

**Corollary (positive key frequencies).** If in addition every pₘ > 0, the strict local inequalities hold
(q_{l−1} + p_l > 0 and p_l + q_l > 0). By Corollary 2, every maximising root is then an endpoint and *every*
maximum-cost tree is a path. More generally, the strict adjacent sums suffice, e.g. p = 0 with all q > 0. Section B
of the checks script and the entry's tests check both cases exhaustively for small n (p = 0 with q ∈ {1, 2},
n = 3..6; p ∈ {1, 2} with q ∈ {0, 1}, n = 3, 4): 880 instances, none with an interior maximiser.

**Signed frequencies.** The adjacent-sum condition allows some negative frequencies. Example:
p = (1, −1, 1), q = (0, 1, 1, 0), where the endpoint DP gives the true maximum 7.

Exhaustive checks (section B): n = 2 and 3 with values −2..2, and n = 4 with values −1..1, 100 933 instances in all.
- 16 020 instances satisfy the condition, 13 078 of them with a negative frequency.
- The endpoint DP is exact on every interval of all 16 020.

**Negative-frequency counterexamples (section C).** Theorem E fails without its hypothesis; every failure violates
the adjacent-sum condition, as E′ predicts. It cannot fail for n ≤ 2, where every root is an endpoint.
- **Smallest counterexample:** n = 3, p = (0, −1, 0), q = (0, 0, 0, 0), where q₁ + p₂ = −1. The maximum, −1, needs
  the middle key at the root; the endpoint DP returns −2. It is the only failure at n = 3 with total absolute
  frequency 1.
- **Exhaustive, n = 3, values −2..2:**
  - 8831 of the 78 125 instances fail;
  - all 8831 lie outside the precondition;
  - 383 failures have negative frequencies only in q (e.g. p = 0, q = (0, −1, −1, 0): −4 vs −5), and 383 only in p.
- **A larger counterexample:** p = (−11, −3, 11), q = (18, −8, −12, −7), maximum −21 (unique maximising root 2),
  endpoint DP −29.
- **Random instances** with frequencies −20..20, n = 1..14: the endpoint DP is right on 1759 of 3000.

## Limits

- **Real weights.** Theorem E′ is proved for real weights. Entries −∞ are covered by the extension above, which was
  also tested exhaustively (section E4) on n = 1..4 with values {−∞, 0, 1, 2}: 5083 tables, 4388 with a −∞ entry,
  the endpoint DP exact on every interval of every table; the same holds for the mirrored +∞ tables under min. +∞
  under max is not covered.
- **Controls: the precondition matters** (section C). Without it, the endpoint DP fails on many inputs.
  - *Monotone weights under MIN.* This includes the optimal-BST recurrence, where Knuth's speed-up is exact
    (proved in that entry's PROOFS.md, section 7), and the endpoint DP fails there. The
    classical optimal BST with p = (1, 1, 1), q = 0 has w(i, j) = j − i, minimum 5 (root k₂, the balanced tree) and
    endpoint DP 6. The smallest failure among n = 3 tables with values 0..2 (smallest sum of the entries) is w(0, 2) = w(0, 3) = w(1, 3) = 1,
    other weights 0 (minimum 1, endpoint DP 2). Random instances of the 11 general families: exact on 523 of 3300.
  - *Arbitrary weights under max.* The smallest failure among n = 3 tables with values 0..2 (smallest sum of the
    entries) is w(0, 1) = w(2, 3) = 1, all other weights 0
    (maximum 2 from root 2; endpoint DP 1). iid random tables, values 0..20, n = 3..12: exact on 798 of 3000, and on
    816 of 3000 under min.
  - *Anti-monotone weights under max:* exact on 340 of 2100 (the 7 anti-monotone families).
- **Sufficient, not necessary.** Some non-monotone inputs are exact. Of the BST instances in section B that violate
  the condition, the endpoint DP is right at the root on 2000 of 2000 (n = 2), 56 919 of 65 750 (n = 3) and 13 341
  of 17 163 (n = 4). The exact set is not characterised.
- **No lower bound.** Θ(n²) is the cost of the endpoint DP. It is not a lower bound for the problem, and no lower
  bound is claimed. In the table form, Θ(n²) is linear in the input size. In the BST form the input has 2n + 1
  numbers, and whether the separable weights allow a faster algorithm was not examined.

## Verification

Every number below is printed by the [checks script](../../experiments/2026-10-07_max_cost_bst_checks.py)
(deterministic, about two minutes); the [entry's tests](../../tests/test_entry_max_cost_bst.py) repeat the essential
checks in a few seconds.

- **V1.** The three implementations agree with each other and with an independent oracle (`harness.check`). The
  battery covers n = 0..10, 12, 16, 25, 40, 70 and 100, with 24 instances per n (408 in all); the plain recursion
  runs up to n = 10.
  - **Families.** Each instance draws one of three categories with equal probability, then a family:
    - **14 BST families**, form (p, q): many full of ties, plus p = 0 with a single non-zero end gap frequency (q₀ or
      qₙ).
    - **11 general monotone families**, form ("max", w): maxima of random values over sub-intervals; sums of sparse
      non-negative values over sub-intervals; non-decreasing functions of the length; capped and squared frequency
      sums; range maxima; random tables built upwards; "tight" tables with many equalities; all-negative tables;
      exact rationals; products.
    - **7 anti-monotone MIN families**, form ("min", w): a constant minus a monotone table, non-increasing length
      functions, reciprocals R/(1 + S) of frequency sums, and negated BST weights.
  - **Composition** (section O). 151 BST, 130 general-max and 127 anti-min battery instances, from all 32 families.
  - **Not BST weights.** By design, most general and anti-monotone instances are not BST weights of any (signed)
    frequencies. BST weights are exactly the separable tables F(j) − G(i). In section E5, 3271 of 3719 general-max
    and 1883 of 2426 anti-min instances with n ≥ 3 are not separable. The negated-BST family is separable by
    construction.
  - **The oracle has two tiers:**
    - **n ≤ 10** (264 battery instances): every tree shape is enumerated (Catalan(n) shapes). A BST instance is
      costed from the levels of its keys and gaps; a table instance by summing the weights of its node intervals.
      There is no recurrence.
    - **10 < n ≤ 200** (144 battery instances): a checked exact certificate. One bound is an explicit path tree,
      valued from its levels or node intervals. The other is a table U, checked against
      U(a, b) ≥ W(a, b) + U(a, k−1) + U(k, b) for every interval and *every* root (≤ for min). W is summed directly
      from p and q, or read from the input. By induction on the root, U bounds every tree, whatever produced U.
      Since U is the best-path table, a valid certificate checks Theorem E′ on that instance instead of assuming it.

    All 408 outputs of each DP, and all 264 of the recursion, were accepted.
- **Oracle control** (section O). It ran on 2528 instances: the battery plus 40 extra seeds per size (1088), and
  every family at 15 sizes with 3 seeds each (1440).
  - **Wrong values presented and rejected:** 18 420 of 18 420 (0 accepted, 0 undecided); by category, 7152 BST,
    6338 general-max and 4930 anti-min.
    - The kinds: the reference ± 1, the optimum in the opposite direction, Knuth's root-range restriction, the left
      path, the right path, the median-root tree, a random tree, the path through the worse endpoint, and a greedy
      path.
    - 6860 such values happened to equal the reference and were not presented.
  - **The true value** was accepted on 2528 of 2528 instances.
  - **Certificate:** valid and tight on 352 of 352 instances with n ≤ 10 (every family at n = 0..10; equal to the
    enumeration) and on 135 of 135 with n = 11..195 (45 per category).
  - **Outside the precondition** (iid random tables under max and min, monotone tables under min, anti-monotone
    tables under max, BST frequencies −20..20; 750 instances with n = 3..30): the certificate never vouched for a
    wrong value.
    - All 500 wrong endpoint values with n > 10 were undecided. The true value was certified on 5 of the 545
      instances with n > 10.
    - All 138 wrong values with n ≤ 10 were rejected by the enumeration.
- **Theorem E′, tested** (checks script, DP code independent of the implementations):

  | Section | Scope | Result |
  |---|---|---|
  | E1 exhaustive, max with w and min with −w | every monotone table, values 0..V−1: n = 1..3 (0..3), n = 4 and 5 (0..2 and 0..3), n = 6 (0..2), n = 7 (0..2: 379 236 tables), n = 7..10 (0..1) | 594 200 / 594 200 tables: an endpoint optimum in every interval and the endpoint DP exact on every interval, in both forms; 375 632 tables have an interior maximiser somewhere; 591 401 are not BST weights |
  | E2 strict monotonicity | every strictly monotone table, values 0..6, n = 4 and 5 | 9438 / 9438 without an interior optimum, in both forms |
  | E3 proof as an algorithm | n = 3..7 | 108 349 / 108 349 |
  | E4 −∞ entries | n = 1..4, values {−∞, 0, 1, 2}, and the +∞ mirror | 5083 / 5083 each |
  | E5 random | 11 general families (max) and 7 anti-monotone families (min), 400 each with n = 1..14 and 40 each with n = 15..60 | 7200 / 7200 (full sets of optimal roots) and 720 / 720 (every interval) |
  | B BST precondition | n = 2, 3 (values −2..2), n = 4 (−1..1) | the adjacent-sum condition equals monotonicity on 100 933 / 100 933; the endpoint DP is exact on all 16 020 monotone instances |
  | C controls | see "Limits" | monotone under min 523/3300; anti-monotone under max 340/2100; iid random 798/3000 (max), 816/3000 (min) |

- **V2 (exact counts, `measure: "reported"`).** The harness's CountingInt counts comparisons of two cost values, with
  the implementations unchanged.
  - The counts do not depend on the weights, the instance form or the direction. `generate_scaling` draws the family
    at random from the 29 integer families of all three categories. The shape diagnostic's instance probe re-draws
    it at small n.
  - Each cost expression is the exact closed form read off the code (RL-062), and all three fits give α = 1.000 at
    tolerance 0.02 (section N runs the validator's own fit). Rivals, all rejected:

  | Algorithm (n values) | Claimed count | Rivals (α) |
  |---|---|---|
  | recursion (5..11) | (3ⁿ⁻¹ − 1)/2 | 2ⁿ 1.587, 2.5ⁿ 1.201, 3.5ⁿ 0.878, 4ⁿ 0.794, 4ⁿ/n^1.5 0.923, n·3ⁿ 0.895, 3ⁿ/n 1.136 |
  | cubic DP (16..128) | (n+1)n(n−1)/6 | n² 1.501, n² log n 1.323, n³/log n 1.099, n³ log n 0.918, n⁴ 0.750 |
  | endpoint DP (32..512) | n(n−1)/2 | n 2.010, n log n 1.660, n^1.5 1.340, n²/log n 1.124, n² log n 0.909, n³ 0.670 |

  - **Checked value by value** (section N): the recursion's call count (exactly 3ⁿ), all three comparison counts and
    the additions.
  - **Scope:** n = 0..9 (recursion), 0..40 (cubic DP) and 0..80 (endpoint DP) on all 32 families, and up to n = 12,
    60 and 512 on one family per category.
  - **Result:** 0 mismatches over 4311 runs. At every n, the comparison counts are identical across all families,
    both forms and both directions.
- **Shape diagnostic:** MATCH for all three: base 3 with n⁰ (n = 1..12), n³ (n = 1..20) and n² (n = 1..24).
- **Cross-version:** section N prints a SHA-256 digest of all count series; it is identical under CPython 3.12.10 and
  3.14.2. No CPython built-in takes part in a counted comparison.
- **Level.** V2. Theorem E′ is proved above (credit: it follows the exchange argument of Qian & Wang 2004, Lemma 1);
  the proof has not been machine-checked.

**Additions.** Counts cover comparisons of cost values. Additions are also Θ(3ⁿ), Θ(n³) and Θ(n²); their exact forms
are in `caveats` and are checked in section N.

**Proofs.** The theorems are proved above. [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry
for all sizes of their domains, from the code, and names the scripts and sizes that check each count; its section 5
indexes where every claim is proved and proves the rest (the correspondence with triangulations used in "Source",
BST weights = separable tables, the size of the numbers, time and space).
[tests/test_proofs_maxbst.py](../../tests/test_proofs_maxbst.py) checks section 5.

**Background (cited, not a claim of this entry).** Qian & Wang 2004, Lemma 1: in a semi-circled convex polygon one of
the two extreme edges belongs to a maximum weight triangulation; its exchange argument uses only that nested chords
are shorter.

**Sources.**
- Qian & Wang 2004, *Maximum weight triangulation of a special convex polygon*, 20th European Workshop on
  Computational Geometry (EWCG 2004), Seville, [hdl:11441/55702](http://hdl.handle.net/11441/55702): Lemma 1
  (semi-circled convex polygons), the exchange argument from which Theorem E′ follows.
- Wang, Chin & Yang 1999, *Maximum weight triangulation and graph drawing*, Information Processing Letters 70(1),
  17–22, doi:10.1016/S0020-0190(99)00037-X: related work on maximum weight triangulations.
- Knuth 1971, *Optimum binary search trees*, Acta Informatica 1(1), 14–25 (credit for the optimal-BST problem).
- Yao 1980, *Efficient dynamic programming using quadrangle inequalities*, STOC 1980, 429–435 (context; the endpoint
  DP does not use it).
- CLRS (3rd ed.) (textbook treatment of the min version).

Scripts: [checks](../../experiments/2026-10-07_max_cost_bst_checks.py), [tests](../../tests/test_entry_max_cost_bst.py).
