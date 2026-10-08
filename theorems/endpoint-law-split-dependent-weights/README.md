# Endpoint law for split-dependent interval weights

> **Provenance: own result.** No statement of Theorem 1, Corollary 2 or Corollary 5, of an endpoint law for interval
> recurrences whose weights depend on the split, or of Lemmas 10 and 11 was found in the literature checked (see
> [Literature checked](#literature-checked)). This is a statement about that search, not a claim of priority.
>
> **Credit for a special case.** For interval weights that are monotone under inclusion, the endpoint law follows the
> exchange argument of Qian & Wang (2004, Lemma 1), who proved that in a semi-circled convex polygon one of the two
> extreme edges belongs to a maximum weight triangulation. The pair entry
> [max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../../pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/)
> writes that argument out for inclusion-monotone interval weights (its Theorem E′); the credit for that case is
> theirs. In this note it is the case of Corollary 5 given by Proposition 6(a).

## Setting

Let n ≥ 0 and let w(i, k, j) be real weights for 0 ≤ i < k ≤ j ≤ n. Consider the recurrence

  c(i, i) = 0,  c(i, j) = max_{i<k≤j} [ w(i, k, j) + c(i, k−1) + c(k, j) ]      (0 ≤ i < j ≤ n).        (R3)

**Trees.** As in the pair entry
[max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../../pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/),
the interval (i, j) holds the nodes i+1..j, and a tree on (i, j) is empty if i = j and otherwise a root k
(i < k ≤ j) with a left subtree on (i, k−1) and a right subtree on (k, j). A node v with key k_v whose subtree spans
(i_v, j_v) has the weight w(i_v, k_v, j_v), and the value of a tree is val(T) = Σ_v w(i_v, k_v, j_v). So the weight
of a node depends on its interval *and on where the node splits it*. A *path tree* is a tree in which every node has
at most one non-empty subtree. The *endpoint DP* restricts (R3) to k ∈ {i+1, j}.

**Special cases.**
- *Interval weights* w(i, k, j) = w(i, j) are the setting of the pair entry above; the section
  [Interval weights](#interval-weights-the-rotation-sum-condition-rs) treats them.
- *Merging adjacent piles.* Piles s₀, …, sₙ lie in a row, and S(x, y) = s_x + … + s_y. A *merge tree* of the piles
  i..j is a full binary tree whose leaves are sᵢ, …, sⱼ in this order; each internal node is the merge of the two
  adjacent blocks formed by the leaves of its two subtrees. For j > i the leaves of the root's left subtree form a
  non-empty prefix i..k−1 of the row, so the root joins the blocks i..k−1 and k..j for exactly one k with i < k ≤ j,
  and its two subtrees are arbitrary merge trees of these blocks. By induction on j − i, mapping the root merge to
  the node k, with the trees of the two blocks as its subtrees, is a bijection between the merge trees of i..j and
  the trees on (i, j): the node k of a subtree on (i′, j′) is the merge that joins the blocks i′..k−1 and k..j′. If a
  merge of blocks of sizes L and R costs f(L, R), the total cost of a merge tree is therefore its value for
  w(i, k, j) = f(S(i, k−1), S(k, j)). A tree is a path tree exactly when its merge tree is a *caterpillar*, a merge
  tree in which every merge joins at least one single pile: the node k on (i′, j′) has an empty left subtree exactly
  when k − 1 = i′, that is, when the left block is the single pile i′, and an empty right subtree exactly when k = j′.

## Statement

**Definitions.** For 0 ≤ i < a < k < b ≤ j ≤ n put

  Δ_R(i, a, k, j) = w(i, a, j) + w(a, k, j) − w(i, k, j) − w(i, a, k−1),
  Δ_L(i, k, b, j) = w(i, b, j) + w(i, k, b−1) − w(i, k, j) − w(k, b, j).

All seven weights are defined (x < y ≤ z in each w(x, y, z), using a ≤ k−1 and k ≤ b−1). The table w satisfies
- **RS3** if Δ_R + Δ_L ≥ 0 for all such (i, a, k, b, j);
- **RS3w** if for all such (i, a, k, b, j), Δ_R ≤ 0 and Δ_L ≤ 0 imply Δ_R = 0;
- **two-sided RS3w** if for all such (i, a, k, b, j), Δ_R ≤ 0 and Δ_L ≤ 0 imply Δ_R = Δ_L = 0.

RS3 implies two-sided RS3w (if Δ_R, Δ_L ≤ 0 and Δ_R + Δ_L ≥ 0, then Δ_R ≥ −Δ_L ≥ 0, so Δ_R = 0, and likewise
Δ_L = 0), which implies RS3w.

**Theorem 1 (weak rotation condition).** If w satisfies RS3w, then for every interval (i, j) with j > i:
- (a) some optimal (maximum-value) tree on (i, j) is a path tree;
- (b) k = i+1 or k = j attains the maximum in (R3);
- (c) for j − i ≥ 2, c(i, j) = max( w(i, i+1, j) + c(i+1, j), w(i, j, j) + c(i, j−1) ).

**Corollary 2 (rotation-sum condition).** If w satisfies RS3, then (a)–(c) of Theorem 1 hold.

**Min form.** If −w satisfies RS3w (in particular, if −w satisfies RS3), then (a)–(c) hold for the min-recurrence
(R3 with min) and minimum-value trees, with min in place of max in (c).

**Remarks.**
- (i) For interval weights w(i, k, j) = w(i, j), Δ_R = w(a, j) − w(i, k−1) and Δ_L = w(i, b−1) − w(k, j), so RS3 is
  exactly the rotation-sum condition RS; see Corollary 5 in the section
  [Interval weights](#interval-weights-the-rotation-sum-condition-rs).
- (ii) RS3 is a system of linear inequalities in w, so non-negative combinations of tables that satisfy RS3 satisfy
  RS3.
- (iii) A root-only term w(i, k, j) = φ(k) gives Δ_R = φ(a) + φ(k) − φ(k) − φ(a) = 0 and Δ_L = 0. Since Δ_R and Δ_L
  are linear in w, adding such a term to any table changes neither, so it preserves RS3, RS3w and two-sided RS3w.

## Proof

**Lemma 3 (unfolding).** For any real weights, c(i, j) is the largest value of a tree on (i, j); k attains the
maximum in (R3) exactly when some optimal tree on (i, j) has root k; and the subtrees of an optimal tree are optimal
for their intervals.

*Proof.* Induction on j − i. The trees on (i, j) with root k are in bijection with the pairs (tree on (i, k−1), tree
on (k, j)), and such a tree has value w(i, k, j) + val(left) + val(right), since the root's weight depends only on
(i, k, j). The two subtrees range independently, so the best tree with root k has value
w(i, k, j) + c(i, k−1) + c(k, j) by the induction hypothesis, and a tree with root k one of whose subtrees is not
optimal has a smaller value. Taking the maximum over k gives the claims. ∎

**Lemma 4 (rotations at the root).** Let T be a tree on (i, j) whose root k is interior, i+1 < k < j. Then both
subtrees are non-empty; let a be the root of the left one and b the root of the right one, so
i < a ≤ k−1 < k < b ≤ j. The right rotation at the root (a becomes the root and k its right child) gives a tree on
(i, j) of value val(T) + Δ_R(i, a, k, j). The left rotation (b becomes the root and k its left child) gives a tree
on (i, j) of value val(T) + Δ_L(i, k, b, j).

*Proof.* A rotation keeps the in-order sequence of the nodes, so the result is a tree on (i, j). Before the right
rotation, k spans (i, j) and splits it at k, and a spans (i, k−1) and splits it at a. After it, a spans (i, j) and
splits it at a, with the parts (i, a−1) and (a, j); and k spans (a, j) and splits it at k, with the parts (a, k−1)
and (k, j). The three subtrees on (i, a−1), (a, k−1) and (k, j) keep their nodes, intervals and splits. So only two
weights change: a's from w(i, a, k−1) to w(i, a, j), and k's from w(i, k, j) to w(a, k, j). The left rotation is the
mirror image: b changes from w(k, b, j) to w(i, b, j), k from w(i, k, j) to w(i, k, b−1), and the subtrees on
(i, k−1), (k, b−1) and (b, j) are unchanged. ∎

*Proof of Theorem 1.* Fix (i, j) with j > i.

(b) There are finitely many trees on (i, j), so an optimal tree T₀ exists; let k₀ be its root. If k₀ ∈ {i+1, j}, (b)
holds by Lemma 3. Otherwise k₀ is interior, and we use the following claim.

*Claim.* Let T be an optimal tree on (i, j) whose root k is interior, and let a be the root of its left subtree.
Then the right-rotated tree T′ is optimal, and its root a satisfies i+1 ≤ a < k.

*Proof of the claim.* By Lemma 4 both rotated trees are trees on (i, j). Since T is optimal, Δ_R(i, a, k, j) ≤ 0
and Δ_L(i, k, b, j) ≤ 0, where b is the root of the right subtree. By RS3w at (i, a, k, b, j), Δ_R = 0, so T′ has
the value of T and is optimal. ∎

Apply the claim repeatedly, starting from T₀. The roots strictly decrease and stay in [i+1, k₀ − 1], so they never
reach j. A root in [i+1, j−1] that is not interior is i+1. So after at most k₀ − i − 1 rotations an optimal tree
with root i+1 is reached, and i+1 attains the maximum in (R3) by Lemma 3.

(c) The key i+1 leaves the parts (i, i) and (i+1, j), and the key j leaves (i, j−1) and (j, j); both empty parts have
c = 0. By (b), restricting the maximum in (R3) to {i+1, j} does not change it.

(a) Induction on j − i. Let k ∈ {i+1, j} attain the maximum (by (b)). One part of k is empty; the other, if
non-empty, has an optimal path tree by the induction hypothesis. The tree with root k, the empty part and that path
tree is a path tree, and it is optimal by Lemma 3.

*Min form.* By induction on j − i, the min-recurrence with w equals −c for the max-recurrence with −w, its minimising
splits are the maximising splits of the latter, and the minimum-value trees for w are the maximum-value trees for
−w. Apply the theorem to −w. ∎

*Proof of Corollary 2.* RS3 implies RS3w (see the definitions), so Theorem 1 applies. The same holds for −w in the
min form. ∎

## Interval weights: the rotation-sum condition RS

Let w(i, j), 0 ≤ i < j ≤ n, be *interval weights*, and consider

  c(i, i) = 0,  c(i, j) = w(i, j) + max_{i<k≤j} [ c(i, k−1) + c(k, j) ]      (0 ≤ i < j ≤ n).        (R)

A tree has the value Σ_v w(I_v), where I_v = (i_v, j_v) is the interval of the subtree of v. This is the setting of
the pair entry
[max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../../pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/).
For weights that are monotone under inclusion (w(b, c) ≤ w(a, d) whenever a ≤ b < c ≤ d), the endpoint law is
credited to Qian & Wang (2004, Lemma 1), as stated at the top. This section shows that a weaker condition suffices.

**Definition (RS).** The table w satisfies the *rotation-sum condition* RS if

  w(a, j) + w(i, b−1) ≥ w(k, j) + w(i, k−1)   for all 0 ≤ i < a < k < b ≤ j ≤ n.

The four intervals are non-empty, since a < k < j and i < k − 1 < b − 1 (using a ≥ i + 1 and b − 1 ≥ k). For
n ≤ 2 there is no such index tuple, so every table with n ≤ 2 satisfies RS.

**Corollary 5 (RS suffices).** If w satisfies RS, then for every interval (i, j) with j > i:
- (a) some optimal (maximum-value) tree on (i, j) is a path tree;
- (b) k = i+1 or k = j attains the maximum in (R);
- (c) c(i, j) = w(i, j) + max(c(i+1, j), c(i, j−1)).

If −w satisfies RS (w(a, j) + w(i, b−1) ≤ w(k, j) + w(i, k−1) for all such indices), the same holds for the
min-recurrence (R with min) and minimum-value trees, with min in (c).

*Proof: the case ŵ(i, k, j) = w(i, j) of Corollary 2.* Put ŵ(i, k, j) = w(i, j) for 0 ≤ i < k ≤ j ≤ n. We check
line by line that the objects of Corollary 2 for ŵ are those of this corollary for w.
1. *The recurrence.* Write ĉ for the solution of (R3) with ŵ: ĉ(i, j) = max_{i<k≤j} [w(i, j) + ĉ(i, k−1) + ĉ(k, j)].
   Adding the same w(i, j) to every candidate preserves their order, so ĉ(i, j) = w(i, j) +
   max_{i<k≤j} [ĉ(i, k−1) + ĉ(k, j)], with the same maximising k. By induction on j − i, ĉ = c, and the maximising k
   of (R3) for ŵ are those of (R).
2. *The trees.* A node v with key k_v spanning (i_v, j_v) has the weight ŵ(i_v, k_v, j_v) = w(i_v, j_v) = w(I_v). So
   every tree has the same value for ŵ as for w, and optimal trees and path trees are the same.
3. *The condition.* The seven weights of Δ_R and Δ_L become ŵ(i, a, j) = w(i, j), ŵ(a, k, j) = w(a, j),
   ŵ(i, k, j) = w(i, j), ŵ(i, a, k−1) = w(i, k−1), ŵ(i, b, j) = w(i, j), ŵ(i, k, b−1) = w(i, b−1) and
   ŵ(k, b, j) = w(k, j). Hence Δ_R = w(i, j) + w(a, j) − w(i, j) − w(i, k−1) = w(a, j) − w(i, k−1) and
   Δ_L = w(i, j) + w(i, b−1) − w(i, j) − w(k, j) = w(i, b−1) − w(k, j), so
   Δ_R + Δ_L = w(a, j) + w(i, b−1) − w(k, j) − w(i, k−1). Over the same index range i < a < k < b ≤ j, RS3 for ŵ is
   exactly RS for w.
4. *The endpoint recurrence.* Corollary 2(c) for ŵ reads
   c(i, j) = max(w(i, j) + c(i+1, j), w(i, j) + c(i, j−1)) = w(i, j) + max(c(i+1, j), c(i, j−1)) for j − i ≥ 2. For
   j − i = 1 the only split is k = j = i+1, and (R) gives c(i, i+1) = w(i, i+1) = w(i, i+1) + max(c(i+1, i+1),
   c(i, i)), since both of these are 0.
5. *The min form.* −ŵ is the table (i, k, j) ↦ −w(i, j), so by step 3 −ŵ satisfies RS3 exactly when −w satisfies RS;
   step 1 holds verbatim with min in place of max.

So Corollary 2 applied to ŵ gives (a), (b) and (c), and its min form gives the min statement. ∎

In the proof of Theorem 1 for ŵ, the rotation step is: at an optimal tree with interior root k and children a and
b, Δ_R = w(a, j) − w(i, k−1) ≤ 0, Δ_L = w(i, b−1) − w(k, j) ≤ 0 and, by RS, Δ_R + Δ_L ≥ 0, so Δ_R = Δ_L = 0. This is
the exchange step of the pair entry's proof of Theorem E′, with RS in place of monotonicity.

**Proposition 6 (RS and monotonicity).**
- (a) Every table that is monotone under inclusion satisfies RS.
- (b) RS does not imply monotonicity: for n = 3, the table with w(1, 3) = 1 and all other weights 0 satisfies RS and
  is not monotone.
- (c) RS is not necessary for the endpoint law: for n = 3, the table with w(2, 3) = 1 and all other weights 0
  violates RS, and (a)–(c) of Corollary 5 hold for it.

*Proof.* (a) Let i < a < k < b ≤ j. Since a < k, the interval (k, j) lies inside (a, j); since k − 1 < b − 1, the
interval (i, k−1) lies inside (i, b−1). Monotonicity gives w(a, j) ≥ w(k, j) and w(i, b−1) ≥ w(i, k−1); add the two
inequalities.

(b) For n = 3 the only index tuple is (i, a, k, b, j) = (0, 1, 2, 3, 3), and RS reads
w(1, 3) + w(0, 2) ≥ w(2, 3) + w(0, 1), here 1 + 0 ≥ 0 + 0. Monotonicity fails, because (1, 3) lies inside (0, 3) and
w(1, 3) = 1 > 0 = w(0, 3).

(c) RS reads 0 + 0 ≥ 1 + 0, which is false. Intervals with at most two nodes have only endpoint roots and only path
trees, so (a)–(c) hold for them. For (0, 3): c(1, 3) = w(1, 3) + max(c(2, 3), c(1, 2)) = 0 + max(1, 0) = 1,
c(0, 2) = 0 and c(0, 1) + c(2, 3) = 1, so the candidates of the splits k = 1, 2, 3 are 1, 1 and 0. The maximum 1 is
attained at the endpoint k = 1, the endpoint recurrence gives c(0, 3) = 0 + max(c(1, 3), c(0, 2)) = 1, and the root
1 with an optimal path tree on (1, 3) is an optimal path tree. ∎

**Proposition 7 (ordered groups).** Lemmas 3 and 4, Theorem 1, Corollary 2, their min forms, Corollary 5 and
Proposition 6(a) hold verbatim when the weights lie in a *totally ordered abelian group* G: an abelian group with a
total order ≤ such that x ≤ y implies x + z ≤ y + z for all x, y, z in G. (Then 0 is the neutral element of G, and
c(i, i) = 0.) Examples are ℝ, ℚ, ℤ, and ℤ² with componentwise addition and the lexicographic order: adding (e, f) to
two pairs keeps the comparison of their first coordinates and, when these are equal, of their second ones. ℤ² is not
archimedean, since m·(0, 1) = (0, m) < (1, 0) for every integer m.

*Proof.* Four facts follow from the axioms.
- (G1) x ≤ y if and only if x + z ≤ y + z, and x < y if and only if x + z < y + z. One direction is the axiom, the
  other is the axiom applied with −z; strictness follows by cancellation (x + z = y + z implies x = y).
- (G2) If x ≤ x′ and y ≤ y′, then x + y ≤ x′ + y ≤ x′ + y′, by (G1) twice; the sum is strict if one of the two
  inequalities is.
- (G3) x ≤ y if and only if −y ≤ −x (add −x − y). So negation reverses the order, and min X = −max(−X) for every
  finite non-empty X ⊆ G.
- (G4) Every finite non-empty subset of G has a maximum and a minimum, because the order is total.

The proofs above use the real numbers only through these facts:
- *Lemma 3.* The value of a tree is a finite sum in G. Every pair of subtrees gives at most
  w(i, k, j) + c(i, k−1) + c(k, j), optimal subtrees give it, and a non-optimal subtree gives strictly less, all by
  (G2); the maxima exist by (G4).
- *Lemma 4* is group arithmetic: two summands of the value are replaced.
- *Theorem 1.* An optimal tree exists by (G4). In the claim, val(T) + Δ_R = val(T′) ≤ val(T) gives Δ_R ≤ 0 by (G1)
  (add −val(T)), likewise Δ_L ≤ 0, and RS3w gives Δ_R = 0. The rest concerns indices and trees, and the empty parts
  in (c) have c = 0.
- *Corollary 2.* From Δ_R + Δ_L ≥ 0 and Δ_L ≤ 0, (G1) with −Δ_L gives Δ_R ≥ −Δ_L ≥ 0; with Δ_R ≤ 0 this forces
  Δ_R = 0, since the order is antisymmetric.
- *The min forms.* By (G3) and induction on j − i, the min-recurrence with w is −c for the max-recurrence with −w,
  with the same optimal splits and the same optimal trees.
- *Corollary 5.* Steps 1, 4 and 5 use (G1): adding w(i, j) to every candidate keeps their order, strict and
  non-strict, so it commutes with max and min. Step 3 uses (G1) once more: Δ_R + Δ_L ≥ 0 holds exactly when
  w(a, j) + w(i, b−1) ≥ w(k, j) + w(i, k−1) (add w(k, j) + w(i, k−1)). The rest of steps 2 to 5 is group arithmetic.
- *Proposition 6(a)* is (G2). ∎

Proposition 6(b) and (c) are statements about two integer tables and are not part of Proposition 7. The merge
lemmas 10 and 11 below are about real pile sizes and are not part of it either.

**Proposition 8 (+∞ entries).** Let G be a totally ordered abelian group, and let the interval weights w take values
in G ∪ {+∞}, where x < +∞ for all x in G, and x + (+∞) = (+∞) + x = +∞ for all x in G ∪ {+∞}. Let w be monotone
under inclusion in this extended order, and evaluate (R) in G ∪ {+∞}. Then for every interval (i, j) with j > i, some
optimal tree on (i, j) is a path tree, and c(i, j) = w(i, j) + max(c(i+1, j), c(i, j−1)).

*Proof.* First, c(i, j) is still the largest value of a tree on (i, j): for a in G ∪ {+∞} and a finite non-empty set
X ⊆ G ∪ {+∞}, a + max X = max (a + X), because for a = +∞ both sides are +∞, and otherwise x ↦ a + x preserves the
order and maps +∞ to +∞; so the induction of Lemma 3 (for ŵ(i, k, j) = w(i, j)) gives its first statement. The
other two statements of Lemma 3 can fail when w(i, j) = +∞, since then every tree on (i, j) is optimal, whatever its
subtrees. For example, n = 3 with w(0, 3) = +∞, w(1, 3) = 5, w(2, 3) = 1 and all other weights 0 is monotone; every
tree on (0, 3) is optimal, but the candidates of the splits k = 1, 2, 3 are 6, 1 and 0, so only k = 1 attains the
maximum in (R); and the tree with root 1 whose right subtree is the root 3 on (1, 3) is optimal although that subtree
has value 5 < c(1, 3) = 6. The proof below uses only the first statement. Now fix (i, j).
- If w(i, j) = +∞, every tree on (i, j) contains the root, of weight +∞, and no weight −∞, so every tree is worth
  +∞. Every tree is optimal, the path trees among them, and c(i, j) = +∞ = w(i, j) + max(c(i+1, j), c(i, j−1)).
- If w(i, j) ∈ G, every interval inside (i, j) has weight ≤ w(i, j) < +∞, so the weights of the sub-intervals of
  (i, j) form a G-valued table that is monotone under inclusion. The values c(x, y) and the trees on the intervals
  inside (i, j) depend only on these weights. By Proposition 6(a) this table satisfies RS, and Corollary 5 applied
  to it gives both claims for (i, j); both hold over G by Proposition 7. ∎

Tables with both +∞ and −∞ entries are not covered: they would need +∞ + (−∞). (The pair entry proves an extension
to −∞ entries for real monotone weights.)

**Proposition 9 (testing RS).** RS can be tested with O(n³) comparisons and additions: at most 3d − 7 comparisons
and 2(d − 2) additions for each interval (i, j) of length d = j − i ≥ 3, and none for shorter intervals.

*Proof.* Fix i < j with d = j − i ≥ 3 and a split k with i+1 < k < j. RS for all a with i < a < k and all b with
k < b ≤ j is equivalent to

  min_{i<a<k} w(a, j) + min_{k≤c≤j−1} w(i, c) ≥ w(k, j) + w(i, k−1)      (c = b − 1),

because the left side of RS is a term that depends only on a plus a term that depends only on b, so its minimum over
the pairs (a, b) is the sum of the two minima. The suffix minima of w(i, c) over c = j−1, j−2, …, i+1 cost one
comparison each after the first, d − 2 in all. The running minimum of w(a, j) over a = i+1, …, k−1, updated as k runs
through i+2, …, j−1, costs one comparison for every k after the first, d − 3 in all. Each of the d − 2 splits k then
costs two additions and one comparison. So (i, j) costs at most (d − 2) + (d − 3) + (d − 2) = 3d − 7 comparisons
(exactly that many if no violation is found) and 2(d − 2) additions. Intervals with d ≤ 2 have no index tuple. Over
the n − d + 1 intervals of each length d this is at most Σ_{d=3..n} (n − d + 1)(3d − 7) ≤ 3n³ comparisons, which is
O(n³), and likewise for the additions. ∎

## Two merge costs

Let s₀, …, sₙ ≥ 0, and w(i, k, j) = f(S(i, k−1), S(k, j)) for a merge cost f. At an index tuple
i < a < k < b ≤ j put

  X = S(i, a−1),  Y = S(a, k−1),  Z = S(k, b−1),  U = S(b, j),  L = X + Y = S(i, k−1),  R = Z + U = S(k, j).

Each of X, Y, Z, U is a sum over a non-empty range of piles, so all four are ≥ 0. The seven weights are
w(i, a, j) = f(X, Y + R), w(a, k, j) = f(Y, R), w(i, k, j) = f(L, R), w(i, a, k−1) = f(X, Y), w(i, b, j) = f(L + Z, U),
w(i, k, b−1) = f(L, Z) and w(k, b, j) = f(Z, U), so

  Δ_R = f(X, Y + R) + f(Y, R) − f(L, R) − f(X, Y),   Δ_L = f(L + Z, U) + f(L, Z) − f(L, R) − f(Z, U).

**Symmetry.** If f(x, y) = f(y, x), the substitution (X, Y, Z, U) ↦ (U, Z, Y, X) maps L to R and R to L, Δ_R to
f(U, Z + L) + f(Z, L) − f(R, L) − f(U, Z) = Δ_L, and Δ_L to Δ_R.

**Lemma 10 (merge cost = larger part).** For s ≥ 0, w(i, k, j) = max(S(i, k−1), S(k, j)) satisfies RS3.

*Proof.* The symmetry swaps Δ_R and Δ_L and leaves Δ_R + Δ_L unchanged, so we may assume L ≤ R. Then:
- X ≤ L (as Y ≥ 0), L ≤ R, and R ≤ Y + R (as Y ≥ 0), so max(X, Y + R) = Y + R; Y ≤ L ≤ R (as X ≥ 0), so
  max(Y, R) = R; and max(L, R) = R. Hence Δ_R = (Y + R) + R − R − max(X, Y) = Y + R − max(X, Y).
- max(L + Z, U) ≥ max(Z, U) (as L ≥ 0) and max(L, Z) ≥ L, so Δ_L ≥ L − R.

So Δ_R + Δ_L ≥ Y + L − max(X, Y) = X + 2Y − max(X, Y) = Y + min(X, Y) ≥ 0, using X, Y ≥ 0 once more. ∎

The non-negativity of the sizes is used at four places: Y ≥ 0 and X ≥ 0 in the first step, L ≥ 0 in the second, and
X, Y ≥ 0 in the last line.

**Lemma 11 (merge cost = imbalance).** For s ≥ 0, w(i, k, j) = |S(i, k−1) − S(k, j)| satisfies two-sided RS3w: at
every index tuple, Δ_R ≤ 0 and Δ_L ≤ 0 imply Δ_R = Δ_L = 0. In particular it satisfies RS3w.

*Proof.* The symmetry swaps Δ_R and Δ_L, and the claim is symmetric in them, so we may assume L ≤ R.

(1) Since X ≤ L ≤ R ≤ Y + R and Y ≤ L ≤ R: |X − (Y + R)| = Y + R − X, |Y − R| = R − Y and |L − R| = R − L. Hence
Δ_R = (Y + R − X) + (R − Y) − (R − L) − |X − Y| = R + L − X − |X − Y| = R + Y − |X − Y|. As R ≥ L = X + Y ≥ |X − Y|,
Δ_R ≥ Y ≥ 0, with equality only if Y = 0 and R = |X − Y| = X, that is, Y = 0 and X = L = R.

(2) So Δ_R ≤ 0 forces Δ_R = 0, Y = 0 and X = L = R = Z + U. Then |L + Z − U| = 2Z, |L − Z| = U and |L − R| = 0, so
Δ_L = 2Z + U − |Z − U| ≥ 2Z + U − (Z + U) = Z ≥ 0. Hence Δ_L ≤ 0 forces Z = 0, and then Δ_L = U − |−U| = 0. ∎

**Corollary 12 (two merge costs).** Let s₀, …, sₙ ≥ 0, and let a merge of blocks of sizes L and R cost max(L, R)
(Corollary 2 with Lemma 10) or |L − R| (Theorem 1 with Lemma 11). Then for every row i..j with j > i, the maximum
total cost of merging the row satisfies (a)–(c): some maximum-cost merge tree of the row is a caterpillar, some
maximising last merge joins a single end pile (sᵢ or sⱼ) to the rest, and the endpoint DP is exact. This follows from
the correspondence between merge trees and trees in the Setting, under which path trees are caterpillars. The pair
entries
[max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp](../../pairs/max-merge-cost-larger-part-cubic-dp-vs-endpoint-dp/)
and [max-merge-imbalance-cubic-dp-vs-endpoint-dp](../../pairs/max-merge-imbalance-cubic-dp-vs-endpoint-dp/) use
it: Θ(n²) instead of Θ(n³).

## Controls: where the hypotheses fail

Each value below is computed by hand here and again by verify.py. For four piles there is a single index tuple,
(i, a, k, b, j) = (0, 1, 2, 3, 3), with X = s₀, Y = s₁, Z = s₂, U = s₃. The five merge trees of four piles are
((s₀s₁)(s₂s₃)) (split k = 2 at the top) and the four caterpillars (((s₀s₁)s₂)s₃), ((s₀(s₁s₂))s₃), (s₀((s₁s₂)s₃)) and
(s₀(s₁(s₂s₃))).

- **|L − R| does not satisfy RS3.** Piles (1, 0, 1, 2): L = 1, R = 3, Δ_R = |1 − 3| + |0 − 3| − |1 − 3| − |1 − 0|
  = 2 + 3 − 2 − 1 = 2 and Δ_L = |2 − 2| + |1 − 1| − |1 − 3| − |1 − 2| = 0 + 0 − 2 − 1 = −3, so Δ_R + Δ_L = −1 < 0.
  So Corollary 2 does not apply to the imbalance, and Theorem 1 is used.
- **min(L, R) under min.** The min form needs RS3 or RS3w for −w: Δ_R + Δ_L ≤ 0, or (Δ_R ≥ 0 and Δ_L ≥ 0 imply
  Δ_R = 0), where Δ_R and Δ_L are the deltas of w = min(L, R).
  - RS3 for −w fails. Piles (0, 1, 1, 2): L = 1, R = 3, Δ_R = min(0, 4) + min(1, 3) − min(1, 3) − min(0, 1) = 0 and
    Δ_L = min(2, 2) + min(1, 1) − min(1, 3) − min(1, 2) = 2 + 1 − 1 − 1 = 1, so Δ_R + Δ_L = 1 > 0. With positive
    piles: (1, 1, 2, 4) gives L = 2, R = 6, Δ_R = 1 + 1 − 2 − 1 = −1 and Δ_L = 4 + 2 − 2 − 2 = 2.
  - RS3w for −w fails. Piles (2, 1, 0, 1): L = 3, R = 1, Δ_R = min(2, 2) + min(1, 1) − min(3, 1) − min(2, 1)
    = 2 + 1 − 1 − 1 = 1 and Δ_L = min(3, 1) + min(3, 0) − min(3, 1) − min(0, 1) = 1 + 0 − 1 − 0 = 0. Both are ≥ 0,
    and Δ_R ≠ 0.

  So neither min form applies to all non-negative sizes. The endpoint law nevertheless holds for this problem: it
  follows from a closed form, proved in the pair entry
  [min-merge-cost-smaller-part-cubic-dp-vs-closed-form](../../pairs/min-merge-cost-smaller-part-cubic-dp-vs-closed-form/).
- **Matrix chain under max.** The chain M₀, …, M₃ with dimensions p = (1, 1, 2, 1, 1) (M_t has p_t rows and p_{t+1}
  columns) has w(i, k, j) = p_i p_k p_{j+1}. Its five products cost: (M₀M₁)(M₂M₃): 2 + 2 + 2 = 6;
  ((M₀M₁)M₂)M₃: 2 + 2 + 1 = 5; (M₀(M₁M₂))M₃: 2 + 1 + 1 = 4; M₀((M₁M₂)M₃): 2 + 1 + 1 = 4; M₀(M₁(M₂M₃)): 2 + 2 + 1 = 5.
  The maximum 6 needs the split k = 2; the endpoint DP gives 5. At (0, 1, 2, 3, 3),
  Δ_R = w(0, 1, 3) + w(1, 2, 3) − w(0, 2, 3) − w(0, 1, 1) = 1 + 2 − 2 − 2 = −1 and
  Δ_L = w(0, 3, 3) + w(0, 2, 2) − w(0, 2, 3) − w(2, 3, 3) = 1 + 2 − 2 − 2 = −1, so RS3w fails. Split-dependent weights
  do not satisfy the endpoint law in general.
- **Negative sizes.** Lemmas 10 and 11 need s ≥ 0, and the endpoint law can fail without it.
  - max(L, R), piles (−2, −1, −2, 1): the five merge trees cost (−1) + 1 + (−1) = −1 for ((s₀s₁)(s₂s₃)), and
    −1 − 2 + 1, −1 − 2 + 1, −1 + 1 − 2 and 1 − 1 − 2, i.e. −2 each, for the four caterpillars. The maximum −1 needs the
    middle split; the endpoint DP gives −2.
  - |L − R|, piles (0, −1, 1, 0): the five merge trees cost 1 + 1 + 2 = 4 for ((s₀s₁)(s₂s₃)), and 1 + 2 + 0 = 3,
    2 + 0 + 0 = 2, 2 + 0 + 0 = 2 and 1 + 2 + 0 = 3 for the caterpillars. The maximum is 4; the endpoint DP gives 3.

## Scope

What this note does **not** claim:
- RS3, RS3w and RS are sufficient, not necessary (the min(L, R) control; Proposition 6(c)); no characterisation is
  claimed.
- Exact arithmetic is assumed: ties are decided by exact equality. Proposition 7 extends Lemmas 3 and 4, Theorem 1,
  Corollary 2, the min forms, Corollary 5 and Proposition 6(a) to totally ordered abelian groups, and nothing else.
  Infinite entries are treated only in Proposition 8 (interval weights, monotone, +∞ under max, no −∞); −∞ entries
  and the conditions RS3, RS3w or RS with infinite entries are not treated.
- The strict version of the pair entry (every optimal tree is a path tree) is not claimed under RS, RS3 or RS3w.
- Lemmas 10 and 11 are stated for non-negative real sizes only.
- No running-time bound other than Proposition 9, and no lower bound: the costs of the endpoint DP and of the cubic DP
  are stated and proved in the pair entries, and no lower bound for any of the problems is claimed.

## Verification

```bash
python theorems/endpoint-law-split-dependent-weights/verify.py
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and runs in well
under a minute. It exits with code 0 only if every check passes. Its code is its own. It checks:

- **Theorem 1 and Corollary 2, exhaustively** on every table with n = 3 and values 0..2 (59 049 tables: 33 858
  satisfy RS3, 33 408 of them depending on the split; 42 822 satisfy RS3w, 8 964 of them not RS3; 37 530 satisfy
  two-sided RS3w). RS3 implies two-sided RS3w, which implies RS3w, on every table. Every RS3w table has, in every
  interval, an optimal split in {i+1, j}, an exact endpoint DP and an optimal path tree (by enumeration of all trees),
  under max with w; and the endpoint law under min with −w. The endpoint law fails on 7 282 of the 59 049 tables,
  none of them RS3w (a control that the test can fail).
- **Random tables:** 40 000 seeded tables with n = 4 (9 102 RS3w, 6 287 of them not RS3) and 60 000 with n = 5
  (1 015 RS3w, 969 not RS3), values 0..2: the endpoint law under max and min on every RS3w table; Lemma 3 (the DP
  equals the maximum over all explicitly enumerated trees) on 200 of these tables of each size.
- **The proof as an algorithm:** on seeded RS3w tables with n = 3 and 4 and on merge tables, from every optimal tree
  with an interior root, the changes of the explicitly computed tree value under both rotations equal Δ_R and Δ_L
  (Lemma 4), Δ_R = 0 (and Δ_L = 0 for RS3 tables), and right rotations reach an optimal tree with root i+1 (6 759
  tables, 1 974 starting trees, 2 052 rotations).
- **Remarks:** RS3 equals RS for interval weights on every table with n = 4 and values 0..2; 200 seeded non-negative
  combinations of RS3 tables are RS3; adding φ(k) leaves Δ_R and Δ_L unchanged on 200 seeded tables.
- **Lemmas 10 and 11** on the grid X, Y, Z, U ∈ {0, …, 12} (28 561 quadruples) and on 5 000 seeded non-negative
  rationals, with the intermediate formulas of the proofs (for L ≤ R) and the symmetry. The merge tables of every size
  vector with n ≤ 4 and sizes 0..4, n = 5 and sizes 0..3, and n = 6 and sizes 0..2 (10 188 vectors): max(L, R)
  satisfies RS3 and |L − R| two-sided RS3w on all of them, and the endpoint law holds (with an optimal caterpillar,
  checked by enumeration, for n ≤ 5).
- **The Setting:** merge trees, enumerated as nested pairs of leaves and costed from leaf sums, against the trees on
  (0, n) with the merge weights: the same number Catalan(n), the same maximum and minimum (equal to the DP), and the
  same maximum and minimum over caterpillars as over path trees; for the merge costs max, |·| and min on every size
  vector with n ≤ 3 and sizes 0..3 and with n = 4 and sizes 0..2, and on 300 seeded vectors with signed sizes and
  n ≤ 5 (2 649 pairs of a vector and a merge cost).
- **The controls** of the previous section, and the endpoint law for min(L, R) under min on every size vector with
  n ≤ 4 and sizes 0..4 and n = 5 and sizes 0..3 (8 001 vectors).
- **Proposition 7 for split-dependent weights:** 20 000 seeded tables with n = 3 and values in
  {(0, 0), (0, 1), (1, −5), (1, 0)} ⊂ ℤ² ordered lexicographically (14 132 RS3w, 3 954 of them not RS3): the endpoint
  law and an optimal path tree under max, and the endpoint law under min for −w, on every RS3w table; Lemma 3 (the DP
  equals the maximum over all explicitly enumerated trees) on the first 200 of these tables; Lemma 4 (the explicit
  values of both rotated trees equal val(T) + Δ_R and val(T) + Δ_L) at the tree with an interior root of each of the
  20 000 tables.

Interval weights (section [Interval weights](#interval-weights-the-rotation-sum-condition-rs)), with interval tables
of their own:
- **Proposition 9:** the O(n³) test of RS agrees with the definition (all index tuples) on 3 000 seeded tables with
  n = 1..9 (1 267 of them RS); on every RS table its comparisons and additions number exactly
  Σ_{d=3..n} (n − d + 1)(3d − 7) and Σ_{d=3..n} (n − d + 1)·2(d − 2), and on every other table at most that.
- **Corollary 5, exhaustively:** every interval table with n = 3 and values 0..2 (729 tables), n = 4 and values 0..2
  (59 049) and n = 5 and values 0..1 (32 768). On every RS table (450, 8 430 and 1 008 tables, of which 366, 7 836 and
  876 are not monotone): every interval has an optimal split in {i+1, j}, the endpoint DP equals the full DP on every
  interval, and every interval has an optimal path tree (by enumeration of all trees), under max with w; and the
  endpoint law under min with −w.
- **Proposition 6:** all 84, 594 and 132 monotone tables of these scopes satisfy RS; the examples (b) and (c), with
  c(0, 3) = 1 and the optimal splits {1, 2} in (c); RS is vacuous for n ≤ 2.
- **Random tables:** 300 seeded interval tables with n = 5..9 that satisfy RS and are not monotone: the endpoint law
  under max and, for −w, under min.
- **Proposition 7 for Corollary 5:** every interval table with n = 3 and values in {(0, 0), (0, 1), (1, −5), (1, 0)}
  (4 096 tables, 2 272 of them RS, 1 942 of those not monotone): the endpoint law and optimal path trees under max,
  and the endpoint law under min for −w; Proposition 6(a): all 330 monotone tables among them satisfy RS.
- **Lemmas 3 and 4 for interval weights and the rotation step:** the recurrence equals the largest value over all
  explicitly enumerated trees on 300 seeded tables (n = 0..6, values −5..9); on RS tables that are not monotone (a
  seeded 15% sample of n = 4 with values 0..2, 1 180 tables, and 40 seeded tables with n = 5, 6): at every tree with
  an interior root the two rotations change the explicitly computed value by a total ≥ 0 (9 621 trees); from every
  optimal tree with an interior root, the changes equal w(a, j) − w(i, k−1) and w(i, b−1) − w(k, j), both are 0, and
  right rotations reach an optimal tree with root i+1 (267 starting trees, 279 rotations).
- **Proposition 8:** every interval table with n = 1..4 and values in {0, 1, 2, +∞} that is monotone in the extended
  order (5 083 tables, 4 388 with a +∞ entry): the endpoint recurrence gives c on every interval under max, and every
  interval has an optimal path tree; and the example in its proof (candidates 6, 1, 0; every tree on (0, 3) worth +∞;
  the subtree of value 5).

The written proofs cover the general statements; the script checks them on the finite scopes above. The proofs are
not machine-checked.

## Literature checked

This is a statement about a search, not a priority claim.
- **Credit for the monotone interval-weight case** (cited; not a claim of this note). Qian & Wang (2004, Lemma 1):
  in a semi-circled convex polygon, one of the two extreme edges belongs to a maximum weight triangulation; the
  exchange argument of their proof uses only that nested chords are shorter. The pair entry
  [max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp](../../pairs/max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp/)
  writes it out for inclusion-monotone interval weights (Theorem E′). Theorem 1 and Corollary 2 concern weights that
  depend on the split; for interval weights they give the weaker condition RS (Corollary 5).
- **Credit for a merge special case** (cited; not a claim of this note). For merging adjacent piles at the cost
  L + R, which is an interval weight, a 2020 article on interval dynamic programming in the Tencent Cloud developer
  community (https://cloud.tencent.com/developer/article/1697989) gives code for the maximum total cost that tries
  only the two end splits of every interval, without a proof.
- **Searched, with no relevant hit beyond the credits above:** bibliographic databases (Crossref, OpenAlex, arXiv;
  titles and abstracts) for stone merging and merging adjacent piles (maximum and minimum total cost), small-to-large
  merging, alphabetic trees, maximum weight triangulations, worst-case and maximum-cost binary search trees, interval
  dynamic programming with maximisation and endpoint splits, and the quadrangle inequality under maximisation.
  Wang, Chin & Yang (1999), an O(n²) algorithm for maximum weight triangulations of inscribed polygons, was seen only
  as a title and summary.

No source found states Theorem 1, Corollary 2, an endpoint law under the rotation-sum condition RS, or an endpoint
law for the merge costs max(L, R) or |L − R|.

## Credit

- J. Qian, C. A. Wang (2004). *Maximum weight triangulation of a special convex polygon*. 20th European Workshop on
  Computational Geometry (EWCG 2004), Seville. [hdl:11441/55702](http://hdl.handle.net/11441/55702). Lemma 1: in a
  semi-circled convex polygon, one of the two extreme edges belongs to a maximum weight triangulation. The case of
  inclusion-monotone interval weights is credited to them; this note's own results are listed at the top.
- Tencent Cloud developer community (2020). *Dynamic programming: interval DP* (title translated).
  https://cloud.tencent.com/developer/article/1697989. Code for the maximum total cost of merging adjacent piles at
  the cost L + R with two end splits per interval, without a proof.
