# Pratt's group construction for T_k: affine maps over ℤ₂ need a group of order at least 2^{3k−1}

> **Provenance: own extension.** Base: K. Pratt, *A stronger connection between the asymptotic rank conjecture and
> the set cover conjecture*, arXiv:2311.02774v1, §1.2, item 4 of the comments after Corollary 1.12, and the public
> note [pratt-remark-4-construction-even-k](../pratt-remark-4-construction-even-k/), which proves the principle
> (its Theorem 1) and the bound R(T_k) ≤ 2^{3k−1} with the deletion map (its Theorem 3). Pratt's item instantiates
> the principle with G = ℤ₂^{3k} and then with G = ℤ₂^{3k−1} ("we can do a little better"). This note proves that no
> instantiation by affine maps over ℤ₂, with one map or with three different maps, uses a group of order below
> 2^{3k−1}, and characterises the instantiations that reach 2^{3k−1}. For arbitrary (non-linear) maps into any finite
> abelian group it proves the weaker bound |G| ≥ 2 C(3k, k) − C(2k, k), which gives 2^{3k−1} for G = ℤ₂^m when
> k ≤ 3. The literature checked (see [Literature checked](#literature-checked)) contains none of these statements;
> this is a statement about that search, not a claim of priority.

## Definitions

- **Tensor and triples.** k ≥ 1. S, T, U range over the k-subsets of [3k] = {1, …, 3k}. T_k = Σ x_S y_T z_U over
  the ordered partitions (S, T, U) of [3k] (Pratt's T_k, Definition 1.4; the P_k of Björklund, Kaski, Koana and
  Nederlof). Three k-subsets form an ordered partition exactly when they are pairwise disjoint.
- **Valid maps.** Let G be a finite abelian group, f₁, f₂, f₃ maps from the k-subsets of [3k] to G, and x ∈ G. The
  quadruple (f₁, f₂, f₃, x) is *valid* if, for all k-subsets S, T, U,
  f₁(S) + f₂(T) + f₃(U) = x  ⟺  (S, T, U) is an ordered partition of [3k].
  Pratt's item 4 is the case f₁ = f₂ = f₃ = f ("(f, x) is valid").
- **Vectors.** 1_X ∈ 𝔽₂^{3k} is the indicator vector of X ⊆ [3k], **1** = 1_{[3k]}, e_s = 1_{{s}}, |w| is the
  number of entries 1 of w, and E = {w ∈ 𝔽₂^{3k} : |w| even}, a subspace of dimension 3k − 1 spanned by the vectors
  e_s + e_t (s ≠ t). We identify ℤ₂^m with 𝔽₂^m.
- **Affine maps.** An *affine quadruple* is a quadruple (f₁, f₂, f₃, x) with G = 𝔽₂^m and f_i(S) = L_i(1_S) + b_i
  (i = 1, 2, 3), where L_i : 𝔽₂^{3k} → 𝔽₂^m are 𝔽₂-linear and b_i, x ∈ 𝔽₂^m. An *affine construction* is a valid
  affine quadruple. (Linear maps are the case b_i = 0.)

## Statement

**Theorem 1 (the principle for three maps).** Let G = 𝔽₂^m, f₁, f₂, f₃ any maps from k-subsets to G and x ∈ G. Over
any field, with u^i_y(S) = (−1)^{y·f_i(S)} for y ∈ 𝔽₂^m,

    Σ_{y ∈ 𝔽₂^m} (−1)^{y·x} u¹_y ⊗ u²_y ⊗ u³_y = 2^m · H,   H[S, T, U] = [f₁(S) + f₂(T) + f₃(U) = x].

If (f₁, f₂, f₃, x) is valid, H = T_k, so R_F(T_k) ≤ 2^m for every field F of characteristic ≠ 2.

**Theorem 2 (sums of three k-sets).** For every k ≥ 1,

    { **1** + 1_S + 1_T + 1_U : S, T, U k-subsets of [3k] } = E,

and **1** + 1_S + 1_T + 1_U = 0 exactly when (S, T, U) is an ordered partition.

**Theorem 3 (affine constructions).** Let k ≥ 1, m ≥ 1, L₁, L₂, L₃ : 𝔽₂^{3k} → 𝔽₂^m linear, b₁, b₂, b₃, x ∈ 𝔽₂^m,
f_i(S) = L_i(1_S) + b_i, and fix one ordered partition (S₀, T₀, U₀). Then (f₁, f₂, f₃, x) is valid if and only if

1. L₁, L₂ and L₃ agree on E;
2. L₁ is injective on E; and
3. x = f₁(S₀) + f₂(T₀) + f₃(U₀).

Consequently every affine construction has m ≥ 3k − 1, so the bound R(T_k) ≤ 2^m of Theorem 1 obtained from it is
never below 2^{3k−1}. For m = 3k − 1, the quadruple is valid if and only if conditions 1 and 3 hold and the kernel of
L₁ is spanned by a single vector of odd weight; the deletion map f(S) = 1_{S∖{1}} of the companion note (Theorem 3
there) is such a construction.

**Corollary 4 (one map).** For a single affine map f(S) = L(1_S) + b, (f, x) is valid if and only if
ker L ∩ E = {0} and x = L(**1**) + b. In particular ker L has dimension at most 1, and if it is 1, its nonzero
vector has odd weight.

**Remark (consistency with the companion note).** Write **1**′ for the all-ones vector of the target 𝔽₂^{3k−1} and
π_j for the deletion of coordinate j. Reading R1 of the printed map in the companion note is affine:
f(S) = π₁(1_S) + [1 ∉ S]·**1**′ = L(1_S) + **1**′ with L(v) = π₁(v) + v₁·**1**′, whose kernel is {0, **1**}; |**1**| = 3k is
odd exactly for odd k, and Corollary 4 recovers Theorem 4.1 there (R1 valid exactly for odd k). Reading R2,
f(S) = π_{3k}(1_S) + [1 ∉ S]·**1**′, has the 2-dimensional kernel {0, e_{3k}, **1**, **1** + e_{3k}} and is valid for no k
(Theorem 4.2 there).

**Proposition 5 (arbitrary maps).** Let G be any finite abelian group and f₁, f₂, f₃ arbitrary maps from k-subsets to
G with (f₁, f₂, f₃, x) valid. Then each f_i is injective and

    |G| ≥ 2 C(3k, k) − C(2k, k).

For G = ℤ₂^m this gives m ≥ 3k − 1 for k = 1, 2, 3 (the right side is 4, 24, 148). For every k ≥ 4,
2 C(3k, k) − C(2k, k) < 2^{3k−2}, so for k ≥ 4 the proposition does not give m ≥ 3k − 1.

## Proof

**Lemma 1.** For z ∈ 𝔽₂^m, Σ_{y ∈ 𝔽₂^m} (−1)^{y·z} = 2^m [z = 0]. (Lemma 1 of the companion note.)

**Proof of Theorem 1.** The (S, T, U) coefficient of the left side is
Σ_y (−1)^{y·(x + f₁(S) + f₂(T) + f₃(U))} = 2^m [f₁(S) + f₂(T) + f₃(U) = x] by Lemma 1 (signs: −x = x in 𝔽₂^m). If the
quadruple is valid, H[S, T, U] = 1 exactly at the ordered partitions, so H = T_k; in characteristic ≠ 2, 2^m is
invertible and T_k is a sum of 2^m rank-one tensors. ∎

**Lemma 2.1 (parity; the companion note's Lemma 2).** |1_S + 1_T + 1_U| ≡ k (mod 2), and 1_S + 1_T + 1_U = **1** if and
only if (S, T, U) is an ordered partition.

*Proof.* The weight of a sum in 𝔽₂^{3k} is ≡ the sum of the weights, 3k ≡ k. If the sum is **1**, every element lies
in one or three of the sets; with n₁ and n₃ elements of each kind, n₁ + n₃ = 3k and n₁ + 3n₃ = |S| + |T| + |U| = 3k,
so n₃ = 0 and the sets are pairwise disjoint. The converse is clear. ∎

**Lemma 2.2 (every even vector occurs).** For every w ∈ E there are k-subsets S, T, U with 1_S + 1_T + 1_U = **1** + w.

*Proof.* Let |w| = 2t; then 0 ≤ t ≤ ⌊3k/2⌋. Split the support of w into two sets Y₂ and Y₀ of t elements each, and
let Z be the 3k − 2t elements outside the support. We put every element of Y₂ into exactly two of the sets, no element
of Y₀ into any set, and every element of Z into exactly one set; then an element of the support of w lies in an even
number of sets and every other element in exactly one, so 1_S + 1_T + 1_U = **1** + w. It remains to choose the sizes.
Write t = 3a + r with r ∈ {0, 1, 2} and send d₁, d₂, d₃ elements of Y₂ to the pairs {S, T}, {S, U}, {T, U}, where
(d₁, d₂, d₃) = (a, a, a), (a+1, a, a) or (a+1, a+1, a) for r = 0, 1, 2. The largest number of elements of Y₂ in one
set is 2a, 2a + 1 or 2a + 2. From 3a + r = t ≤ 3k/2 we get 2a ≤ k (r = 0), 2a + 1 ≤ k + 1/3 (r = 1) and
2a + 2 ≤ k + 2/3 (r = 2); these numbers are integers, so each set receives at most k elements of Y₂. Fill each set up
to k elements with elements of Z; this uses 3k − (d₁ + d₂) − (d₁ + d₃) − (d₂ + d₃) = 3k − 2t elements, which is
exactly |Z|. ∎

**Proof of Theorem 2.** By Lemma 2.1, **1** + 1_S + 1_T + 1_U has weight ≡ 3k − k ≡ 0, so it lies in E, and it is 0
exactly for the ordered partitions. Lemma 2.2 gives every element of E. ∎

**Lemma 3.1 (three affine maps agree on E).** If (f₁, f₂, f₃, x) is a valid affine construction, then L₁, L₂ and L₃
agree on E.

*Proof.* Let s ≠ t be elements of [3k]. As k ≥ 1, there is an ordered partition (S, T, U) with s ∈ S and t ∈ T. Then
(S′, T′, U) with S′ = (S ∖ {s}) ∪ {t} and T′ = (T ∖ {t}) ∪ {s} is also an ordered partition, so both are hits:
L₁(1_S) + L₂(1_T) + L₃(1_U) + b = x = L₁(1_{S′}) + L₂(1_{T′}) + L₃(1_U) + b with b = b₁ + b₂ + b₃. Adding the two
equations and using 1_S + 1_{S′} = e_s + e_t = 1_T + 1_{T′} gives (L₁ + L₂)(e_s + e_t) = 0. The e_s + e_t span E, so
L₁ = L₂ on E. The same argument with s ∈ S, t ∈ U (exchanging s and t between S and U) gives L₁ = L₃ on E. ∎

**Proof of Theorem 3.** Write L = L₁.

(⟹) By Lemma 3.1, L_i − L vanishes on E (i = 2, 3). For two k-subsets X, Y, 1_X + 1_Y ∈ E, so (L_i − L)(1_X) =
(L_i − L)(1_Y): the value c_i = (L_i − L)(1_X) does not depend on X. Hence f_i(S) = L(1_S) + b′_i with b′₁ = b₁ and
b′_i = b_i + c_i, and for all S, T, U

    f₁(S) + f₂(T) + f₃(U) = L(1_S + 1_T + 1_U) + b′,   b′ = b′₁ + b′₂ + b′₃.          (∗)

Condition 3 holds because (S₀, T₀, U₀) is a partition and the quadruple is valid. By (∗) and Lemma 2.1,
x = L(**1**) + b′. Let w ∈ E, w ≠ 0. By Lemma 2.2 there are S, T, U with 1_S + 1_T + 1_U = **1** + w, and by Lemma 2.1
they do not form a partition (w ≠ 0). By (∗) their sum is L(**1**) + L(w) + b′ = x + L(w); validity requires it to differ
from x, so L(w) ≠ 0. Hence L is injective on E: condition 2.

(⟸) Assume 1–3. As in the first part, condition 1 gives (∗), and condition 3 with Lemma 2.1 gives
x = L(**1**) + b′. For any S, T, U let w = **1** + 1_S + 1_T + 1_U, which lies in E (Theorem 2). By (∗) the sum is
x + L(w), which equals x iff L(w) = 0, iff w = 0 (condition 2), iff (S, T, U) is an ordered partition (Lemma 2.1).

*Consequences.* L restricted to E is an injective linear map from a space of dimension 3k − 1 into 𝔽₂^m, so
m ≥ 3k − 1. The deletion map is the case L₁ = L₂ = L₃ = π₁ (delete coordinate 1), b_i = 0 and x = π₁(**1**), the
all-ones vector of 𝔽₂^{3k−1}, with m = 3k − 1: condition 1 is automatic, condition 2 holds because
ker π₁ = {0, e₁} meets E only in 0, and condition 3 holds because f(S₀) + f(T₀) + f(U₀) = π₁(**1**). If m = 3k − 1 and
the construction is valid, L maps E bijectively onto 𝔽₂^m, so L has rank 3k − 1 and a kernel of dimension 1, which
meets E only in 0: it is spanned by an odd-weight vector. Conversely, if m = 3k − 1, conditions 1 and 3 hold and ker L = {0, a} with
|a| odd, then ker L ∩ E = {0}, so condition 2 holds and the construction is valid. ∎

**Proof of Corollary 4.** With L₁ = L₂ = L₃ = L and b_i = b, condition 1 is automatic, condition 2 says ker L ∩ E =
{0}, and condition 3 reads x = L(1_{S₀} + 1_{T₀} + 1_{U₀}) + 3b = L(**1**) + b. A subspace of dimension ≥ 2 meets the
hyperplane E in a subspace of dimension ≥ 1, so dim ker L ≤ 1, and a nonzero kernel vector is not in E. ∎

**Proof of the Remark.** For R1, f(S) = π₁(1_S) + [1 ∉ S]·**1**′, and [1 ∉ S] = 1 + (1_S)₁, so f(S) = L(1_S) + **1**′ with
L(v) = π₁(v) + v₁·**1**′. If L(v) = 0 and v₁ = 0, then π₁(v) = 0 and v = 0; if v₁ = 1, then π₁(v) = **1**′ and v = **1**.
So ker L = {0, **1**}. For R2, in the same way L(v) = π_{3k}(v) + v₁·**1**′: v₁ = 0 forces π_{3k}(v) = 0, so
v ∈ {0, e_{3k}}; v₁ = 1 forces π_{3k}(v) = **1**′, so v ∈ {**1**, **1** + e_{3k}}. Corollary 4 then gives the stated
verdicts: for R1 the kernel meets E only in 0 exactly when 3k is odd; for R2 the kernel has dimension 2. ∎

**Proof of Proposition 5.** Write N = C(3k, k), D = C(2k, k), and 𝒦 for the set of k-subsets.

*Injectivity.* Suppose f₃(U) = f₃(U′) with U ≠ U′. Split [3k] ∖ U into two k-sets S, T. (S, T, U) is an ordered
partition, hence a hit; (S, T, U′) has the same sum, so it is a hit, hence a partition, so U′ = [3k] ∖ (S ∪ T) = U,
a contradiction. The same argument applies to f₁ and f₂.

*Counting.* Consider the N² ordered pairs (S, T) and the sums σ(S, T) = f₁(S) + f₂(T). Exactly N·D pairs are disjoint
(choose S, then T among the k-subsets of the 2k-set [3k] ∖ S). If S ∩ T ≠ ∅, then σ(S, T) ∉ X = {x − f₃(U) : U ∈ 𝒦}:
otherwise (S, T, U) would be a hit that is not a partition. By injectivity of f₃, |X| = N, so the N² − N·D sums of
non-disjoint pairs lie in G ∖ X, a set of |G| − N elements. For a fixed g ∈ G and a fixed S there is at most one T
with σ(S, T) = g (f₂ is injective), so each g is the sum of at most N ordered pairs. Hence N² − N·D ≤ N(|G| − N),
that is |G| ≥ 2N − D.

*Values.* For k = 1, 2, 3: 2N − D = 6 − 2 = 4, 30 − 6 = 24 and 168 − 20 = 148, and the least m with 2^m ≥ 2N − D is
2, 5 and 8 = 3k − 1. For k ≥ 4: C(12, 4) = 495 ≤ 2⁹, and C(3k+3, k+1)/C(3k, k) =
3(3k+2)(3k+1)/((2k+2)(2k+1)) < 27/4 < 8 (since 4(3k+2)(3k+1) < 9(2k+2)(2k+1) ⟺ 0 < 18k + 10), so by induction
C(3k, k) ≤ 2^{3k−3} for all k ≥ 4, and 2N − D < 2N ≤ 2^{3k−2}. ∎

## Background

These statements are cited, not proved here.

- Pratt (arXiv:2311.02774v1, §1.2, item 4, p. 4) states R(T_k) ≤ 8^k/2 for char(F) ≠ 2, describes the principle
  (a function f into an abelian group G and x ∈ G with f(S) + f(T) + f(U) = x iff S, T, U are disjoint give
  R(T_k) ≤ |G| "by zeroing-out and relabeling variables in the tensor Σ_{a+b+c=x} X_a Y_b Z_c"), calls G = ℤ₂^{3k}
  with indicator vectors "the most obvious way to instantiate this idea", and continues "But we can do a little
  better by taking G = ℤ₂^{3k−1} …". The text makes no statement about smaller groups.
- Flavi, Jelisiejew and Michałek (arXiv:2408.02754v2, Proposition 6.18; IMRN 2025) prove the smaller bound
  R(T_k) ≤ Σ_{j=0}^{k} C(3k, 2j) (31 < 32 for k = 2, 247 < 256 for k = 3) over algebraically closed fields of
  characteristic 0, by a construction that keeps the group tensor in two factors and substitutes in the third; the
  public note [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/) proves it
  over every field of characteristic ≠ 2. By Theorem 3, that improvement cannot come from an affine construction in
  Theorem 1.

## Scope

- Theorem 3 and Corollary 4 concern affine maps over ℤ₂ (one map, or three maps with the same group and target x),
  as defined above. Proposition 5 concerns arbitrary maps into any finite abelian group. Nothing is claimed about
  other constructions, about R(T_k) itself, or about non-abelian groups.
- *Open, not claimed:* whether every valid quadruple of arbitrary maps into ℤ₂^m has m ≥ 3k − 1 when k ≥ 4.
  Proposition 5 gives only m ≥ 10 for k = 4 (2N − D = 920).

## Verification

```bash
python theorems/pratt-group-method-affine-maps-lower-bound/verify.py
```

Offline, standard library only, under a second. In order, the script checks:

1. Theorem 2 for k = 1, 2, 3 over all ordered triples (596 106 triples), and the explicit triple of Lemma 2.2 for every
   even weight and k = 1, …, 8;
2. Corollary 4 by brute force for k = 1, 2: all 7 + 63 kernels of dimension 1 (valid exactly for odd weight) and all
   7 + 651 kernels of dimension 2 (none valid), plus four kernels against the definition directly;
3. Theorem 3 for three affine maps, k = 1, 2, m = 3k − 1 and 3k: on 48 fixed triples of maps (agreeing on E or not,
   correct or wrong x, injective on E or not; 17 of them valid), brute-force validity equals conditions 1–3;
4. controls for k = 1, …, 4: the deletion map is valid; the kernel {0, e₁ + e₂} is not, with the false positive of
   Lemma 2.2; the kernel {0, **1**} (reading R1) is valid exactly for odd k;
5. Proposition 5: exhaustively for k = 1, no valid quadruple of arbitrary maps into ℤ₂ or ℤ₃ (both of order < 4); the
   ingredients of the proof on the deletion map for k = 1, 2, 3; the least m with 2^m ≥ 2C(3k,k) − C(2k,k) equals
   3k − 1 for k ≤ 3 and is at most 3k − 2 for 4 ≤ k ≤ 60, with C(3k, k) ≤ 2^{3k−3}.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time on
the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 12 October 2026, in addition to the search of 8 October 2026 recorded in the companion note:
arXiv:2311.02774v1 (item 4 read again in full); the works citing Pratt (2023/2024), Björklund–Kaski–Koana–Nederlof
(2026) or Flavi–Jelisiejew–Michałek (2025) listed by Semantic Scholar and OpenAlex on 12 October 2026, of which the
following were read in full text (keyword search of the whole text and reading of every passage on tensors):
arXiv:2608.08328, 2607.25973v2, 2608.12224, 2601.05044, 2602.12762, 2605.21738v2, 2609.39062, 2602.11975. None of
them discusses the group construction of item 4 or a lower bound on the size of the group it uses; Alman–Li
(arXiv:2605.21738v2, Remark 6.1) cites the upper bound of Flavi–Jelisiejew–Michałek for T_n.
The other citing works listed there (arXiv:2404.06427, 2411.15789, 2411.02936v3, 2505.22410, 2507.11098v2,
2510.08185, 2510.08336), Björklund–Kaski (arXiv:2310.11926) and Björklund–Curticapean–Husfeldt–Kaski–Pratt
(arXiv:2404.04987) were checked by keyword search of the full text; they cite these papers for conditional or
algorithmic results and state no rank or border rank bound for the tensors of this note.

## Sources

- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>. Base: §1.2, item 4.
- K. Pratt (2024). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  STOC 2024, 871–874. [doi:10.1145/3618260.3649620](https://doi.org/10.1145/3618260.3649620).
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754 (read: v2, §6).
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36).
- J. Alman, B. Li (2026). *Asymptotic Rank Speedup Theorems, Revisited*. arXiv:2605.21738v2.

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
