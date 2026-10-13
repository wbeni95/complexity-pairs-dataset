# Rank and border rank of the remaining small tripartitioning tensors

Extension of the note [tripartition-tensors-small-cases](../tripartition-tensors-small-cases/).

> **Provenance: own result.** The lower bounds use the Koszul–Young flattening of Landsberg and Ottaviani and the
> ordinary flattening bound, both proved in the public notes cited below, and the rank bound R ≥ C(n, c) + 1 uses a
> standard lemma on tensors whose rank equals a factor dimension (proof included); the upper bounds are Theorem 1 and
> Corollaries 2–3 of the public note
> [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/). The literature
> checked (see [Literature checked](#literature-checked)) states no value or bound for these tensors. This is a
> statement about that search, not a claim of priority.

| Tensor | Size | Lower bound | Upper bound | Consequence |
|---|---|---|---|---|
| T_{1,2,3} | 6 × 15 × 20 | border rank ≥ 21 | rank ≤ 26 | 21 ≤ R̲ ≤ R ≤ 26 |
| T_{1,2,4} | 7 × 21 × 35 | border rank ≥ 35; rank ≥ 36 | rank ≤ 42 | 35 ≤ R̲; 36 ≤ R ≤ 42 |
| T_{1,3,3} | 7 × 35 × 35 | border rank ≥ 42 | rank ≤ 56 | 42 ≤ R̲ ≤ R ≤ 56 |
| T_{2,2,3} | 21 × 21 × 35 | border rank ≥ 39 | rank ≤ 57 | 39 ≤ R̲ ≤ R ≤ 57 |
| T_{1,1,c}, c ≥ 1 | (c+2) × (c+2) × C(c+2, 2) | border rank ≥ C(c+2, 2); rank ≥ C(c+2, 2) + 1 | rank ≤ C(c+2, 2) + 1 | R = C(c+2,2)+1; R̲ ∈ {C(c+2,2), C(c+2,2)+1} |

For c = 3, 4 and 5 the last row reads R = 11, R = 16 and R = 22, with 10 ≤ R̲ ≤ 11, 15 ≤ R̲ ≤ 16 and 21 ≤ R̲ ≤ 22;
for c = 3 this settles the interval 10 ≤ R ≤ 11 of the public note. With the public note, this completes the table of
all T_{a,b,c} with a ≤ b ≤ c, a ≥ 1 and a + b + c ≤ 7 other than P₂ = T_{2,2,2} (treated in its own notes). The fields
for which each entry is proved are stated in the Theorem.

## Definitions

- **Tensors, coordinates, rank, border rank, flattenings** as in the public note
  [tripartition-tensors-small-cases](../tripartition-tensors-small-cases/): T_{a,b,c} = Σ x_A y_B z_C over the ordered
  partitions (A, B, C) of [n], n = a + b + c, with |A| = a, |B| = b, |C| = c; the coordinates of each factor are the
  subsets of the right size in increasing order of Σ_{e ∈ S} 2^(e−1), numbered from 0; R_F is the rank, R̲_ℂ the
  border rank over ℂ and R̲_F the algebraic border rank over F; K_p(T′) is the Koszul–Young flattening of the note
  [tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/), and M₃(T) the
  flattening along the third factor, M₃(T)[k, (i, j)] = T[i][j][k].
- **The projections.** For T_{1,2,3} (first factor of dimension 6, p = 2) Φ₁₂₃ = [I₅ | 1], the 5 × 6 matrix

<!-- PHI -->
```
[ 1, 0, 0, 0, 0, 1 ]
[ 0, 1, 0, 0, 0, 1 ]
[ 0, 0, 1, 0, 0, 1 ]
[ 0, 0, 0, 1, 0, 1 ]
[ 0, 0, 0, 0, 1, 1 ]
```
<!-- PHI -->

  For T_{1,3,3} (first factor of dimension 7, p = 2) Φ₁₃₃ is the 5 × 7 matrix

<!-- PHI -->
```
[ 1, 0, 0, 0, 0, 1,  1 ]
[ 0, 1, 0, 0, 0, 1, -1 ]
[ 0, 0, 1, 0, 0, 1,  1 ]
[ 0, 0, 0, 1, 0, 1, -1 ]
[ 0, 0, 0, 0, 1, 1,  1 ]
```
<!-- PHI -->

  For T_{2,2,3} the factors are taken in the order (third, first, second), so that the projected factor is the one of
  dimension C(7, 3) = 35, and p = 5. Φ₂₂₃ is the following 11 × 35 matrix with entries −1, 0, 1, printed by columns:
  the line for coordinate a (the a-th 3-subset of [7]) gives the column (Φ₂₂₃[0][a], …, Φ₂₂₃[10][a]).

<!-- PHI -->
```
 0  {1,2,3}  [  1,  1, -1, -1,  0,  0,  1,  1, -1,  0, -1 ]
 1  {1,2,4}  [  0,  0,  1,  0,  1,  0,  1, -1, -1,  1, -1 ]
 2  {1,3,4}  [  1,  1,  0,  1,  1,  1,  0,  0,  1,  0,  1 ]
 3  {2,3,4}  [ -1,  0,  0,  1,  1, -1, -1, -1, -1, -1,  1 ]
 4  {1,2,5}  [ -1,  1,  1,  0,  0,  0,  1,  1,  0, -1,  1 ]
 5  {1,3,5}  [  0,  1,  0,  0, -1,  0, -1, -1,  1,  0,  1 ]
 6  {2,3,5}  [  0,  0,  0,  0, -1, -1, -1,  1,  1,  0, -1 ]
 7  {1,4,5}  [ -1, -1, -1, -1, -1, -1,  0,  0, -1,  0,  0 ]
 8  {2,4,5}  [  1,  0,  0,  0,  0,  0,  0, -1, -1,  0,  1 ]
 9  {3,4,5}  [  1,  1,  0,  1,  1,  1,  1,  0, -1,  0, -1 ]
10  {1,2,6}  [ -1,  0,  0,  0, -1,  1,  0,  0,  0,  0,  1 ]
11  {1,3,6}  [  1,  0,  1,  1,  1,  0,  0,  1,  0,  1, -1 ]
12  {2,3,6}  [ -1,  0,  1, -1, -1,  1,  1, -1,  1,  0,  0 ]
13  {1,4,6}  [  0,  0,  1, -1, -1,  0,  0,  1,  1,  1,  1 ]
14  {2,4,6}  [  0,  1,  1,  0, -1, -1,  0, -1,  1,  0,  1 ]
15  {3,4,6}  [  1,  1, -1, -1, -1,  0, -1,  0,  0, -1,  1 ]
16  {1,5,6}  [  0,  0,  1, -1,  0, -1, -1,  1, -1,  1, -1 ]
17  {2,5,6}  [  0,  1, -1,  1, -1,  0,  0,  0,  1,  0,  0 ]
18  {3,5,6}  [ -1,  1,  1,  1,  0,  0,  1,  0,  0,  0,  0 ]
19  {4,5,6}  [ -1, -1,  0, -1, -1,  1,  1,  0,  0,  0,  1 ]
20  {1,2,7}  [  1,  1,  1,  0,  0,  1,  0,  1,  1,  1,  0 ]
21  {1,3,7}  [  1,  1,  0, -1, -1, -1, -1,  1, -1, -1,  0 ]
22  {2,3,7}  [ -1,  1, -1,  1,  1,  1,  0,  0,  0,  0,  1 ]
23  {1,4,7}  [ -1,  0,  1,  0,  0,  1,  0,  1,  0,  1, -1 ]
24  {2,4,7}  [ -1,  0, -1,  0, -1,  0,  0,  1,  1,  1, -1 ]
25  {3,4,7}  [  1,  1,  1,  0,  1,  1,  1, -1, -1,  0,  0 ]
26  {1,5,7}  [ -1,  1,  1,  0, -1,  0, -1,  1, -1,  0, -1 ]
27  {2,5,7}  [  0, -1,  1,  0,  0,  1,  0,  1,  0, -1,  0 ]
28  {3,5,7}  [ -1, -1,  1,  1,  1,  0,  1,  1, -1, -1, -1 ]
29  {4,5,7}  [  0, -1,  1, -1,  0, -1,  1, -1, -1, -1, -1 ]
30  {1,6,7}  [  0, -1, -1,  1,  0,  0,  0,  0,  1, -1, -1 ]
31  {2,6,7}  [ -1,  1,  0,  1,  1,  1,  0,  1, -1,  0,  1 ]
32  {3,6,7}  [  1,  0, -1,  1,  1,  0,  1,  1, -1,  0, -1 ]
33  {4,6,7}  [  0,  1, -1,  1,  1,  0,  1, -1,  0,  1,  1 ]
34  {5,6,7}  [  0, -1,  1,  0,  0,  1,  1, -1,  0, -1, -1 ]
```
<!-- PHI -->

- **The three matrices.** M₁₂₃ = K₂((Φ₁₂₃ ⊗ 1 ⊗ 1)T_{1,2,3}) is 200 × 150 (C(5,3) · 20 rows, C(5,2) · 15 columns);
  M₁₃₃ = K₂((Φ₁₃₃ ⊗ 1 ⊗ 1)T_{1,3,3}) is 350 × 350; M₂₂₃ = K₅((Φ₂₂₃ ⊗ 1 ⊗ 1)T^σ_{2,2,3}), with T^σ_{2,2,3} the tensor with
  its factors in the order (third, first, second), is 9 702 × 9 702 (C(11, 6) · 21 = C(11, 5) · 21). All three have
  integer entries.

## Statement

**Theorem.**

1. *Upper bounds.* For every field F of characteristic ≠ 2: R_F(T_{1,2,3}) ≤ 26, R_F(T_{1,2,4}) ≤ 42,
   R_F(T_{1,3,3}) ≤ 56, R_F(T_{2,2,3}) ≤ 57, and R_F(T_{1,1,c}) ≤ C(c+2, 2) + 1 for every c ≥ 1.
2. *Lower bounds.*
   - R̲(T_{1,2,3}) ≥ 21 and R̲(T_{2,2,3}) ≥ 39 over ℂ and over every field of characteristic 0 or of prime
     characteristic q ≤ 31.
   - R̲(T_{1,3,3}) ≥ 42 over ℂ and over every field of characteristic 0 or of prime characteristic 3 ≤ q ≤ 31.
   - R̲_F(T_{1,2,4}) ≥ 35 and R̲_F(T_{1,1,c}) ≥ C(c+2, 2) (every c ≥ 1) over ℂ and over every field F.
3. *Rank one above the dimension.* For all a, b, c ≥ 1, n = a + b + c, and every field F:
   R_F(T_{a,b,c}) ≥ C(n, c) + 1. In particular R_F(T_{1,2,4}) ≥ 36 and R_F(T_{1,1,c}) ≥ C(c+2, 2) + 1 for every c ≥ 1.
4. *Consequences.* Over ℂ and over every field of characteristic 0 or of prime characteristic 3 ≤ q ≤ 31:
   21 ≤ R̲(T_{1,2,3}) ≤ R(T_{1,2,3}) ≤ 26, 42 ≤ R̲(T_{1,3,3}) ≤ R(T_{1,3,3}) ≤ 56 and
   39 ≤ R̲(T_{2,2,3}) ≤ R(T_{2,2,3}) ≤ 57. Over every field of characteristic ≠ 2: 35 ≤ R̲(T_{1,2,4}),
   36 ≤ R(T_{1,2,4}) ≤ 42, **R(T_{1,1,c}) = C(c+2, 2) + 1** and C(c+2, 2) ≤ R̲(T_{1,1,c}) ≤ C(c+2, 2) + 1 for every
   c ≥ 1.

The proof uses the following computed facts: rank_{𝔽_q}(M₁₂₃ mod q) = 121 for every prime q ≤ 31;
rank_{𝔽_q}(M₁₃₃ mod q) = 248 for every prime 3 ≤ q ≤ 31 (and 242 for q = 2); rank_{𝔽_q}(M₂₂₃ mod q) = 9 646 for q = 2,
9 700 for q = 11, and 9 702 for every other prime q ≤ 31.

**Open question (not claimed).** Is R̲(T_{1,1,c}) = C(c+2, 2) + 1 for every c ≥ 3? By the Theorem the border rank
is C(c+2, 2) or C(c+2, 2) + 1. The value C(c+2, 2) + 1 is known for c = 1 (border rank 4 over fields of
characteristic 0; see Background) and for c = 2 (border rank 7 over ℂ and over every field of characteristic 0 or
3 ≤ q ≤ 31; the public note).

## Proof

**Facts used** (proved in the public notes, cited by name):

- *Lemma 3* of [tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/):
  R̲(T) ≥ rank K_p((Φ ⊗ 1 ⊗ 1)T)/C(2p, p) (algebraic definition over every field, topological over ℂ); *Lemma 4*
  there: for an integer matrix M, the rank over a field of characteristic q is rank_{𝔽_q}(M mod q), and over a field
  of characteristic 0 it is rank_ℚ(M) ≥ rank_{𝔽_q}(M mod q).
- *Permuting factors* and the *flattening Lemma* of [tripartition-tensors-small-cases](../tripartition-tensors-small-cases/):
  R and R̲ do not change when the factors are permuted; R̲_F(T) ≥ rank_F M₃(T) over every field (and over ℂ).
- *Theorem 1, Corollary 2 and Corollary 3* of
  [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/): for every field of
  characteristic ≠ 2, R(T_{a,b,c}) ≤ |D_{a_i, a_j}| for every pair i ≠ j of the three sizes, where
  |D_{a,b}| = Σ_{j=0}^{min(a,b)} C(n, a + b − 2j); and R(T_{1,1,c}) ≤ C(c+2, 2) + 1.

**Upper bounds.** With n = a + b + c, the formula gives:

| Tensor | n | |D| for the pairs of sizes | minimum |
|---|---|---|---|
| T_{1,2,3} | 6 | (1,2): 20 + 6 = 26; (1,3): 15 + 15 = 30; (2,3): 6 + 20 + 6 = 32 | 26 |
| T_{1,2,4} | 7 | (1,2): 35 + 7 = 42; (1,4): 21 + 35 = 56; (2,4): 7 + 35 + 21 = 63 | 42 |
| T_{1,3,3} | 7 | (1,3): 35 + 21 = 56; (3,3): 7 + 35 + 21 + 1 = 64 | 56 |
| T_{2,2,3} | 7 | (2,2): 35 + 21 + 1 = 57; (2,3): 21 + 35 + 7 = 63 | 57 |

and Corollary 2 gives C(c+2, 2) + 1 for T_{1,1,c}. ∎

**T_{1,2,3} ≥ 21.** The first factor has dimension 6; project it by Φ₁₂₃ and take p = 2. `verify.py` finds
rank_{𝔽_q}(M₁₂₃ mod q) = 121 for every prime q ≤ 31. As 121 > 120 = 20 · C(4, 2), Lemmas 3 and 4 give
R̲(T_{1,2,3}) ≥ 121/6 > 20 over every field of characteristic q ≤ 31 and, through rank_ℚ ≥ 121, of characteristic 0
(in particular ℂ). ∎

**T_{1,3,3} ≥ 42.** Project the first factor (dimension 7) by Φ₁₃₃, p = 2. rank_{𝔽_q}(M₁₃₃ mod q) = 248 for every prime
3 ≤ q ≤ 31; 248 > 246 = 41 · 6, so R̲ ≥ 248/6 > 41 for characteristic 3 ≤ q ≤ 31 and, through rank_ℚ ≥ 248, for
characteristic 0. Modulo 2 the rank is 242 ≤ 246, which gives nothing; the note makes no claim in characteristic 2. ∎

**T_{2,2,3} ≥ 39.** Permute the factors to (third, first, second) and project the factor of dimension 35 by Φ₂₂₃,
p = 5, C(10, 5) = 252. rank_{𝔽_q}(M₂₂₃ mod q) ≥ 9 646 for every prime q ≤ 31, and 9 646 > 9 576 = 38 · 252. Lemmas 3
and 4 (with rank_ℚ(M₂₂₃) ≥ 9 702 from q = 5 for characteristic 0) give R̲(T^σ_{2,2,3}) ≥ 39, and permuting the factors
back does not change the border rank. ∎

**T_{1,2,4} ≥ 35 and T_{1,1,c} ≥ C(c+2, 2).** Let (a, b, c) be (1, 2, 4) or (1, 1, c) and n = a + b + c. Row U of
M₃(T_{a,b,c}) (U a c-subset of [n]) has entry 1 in the columns (A, B) with (A, B, U) an ordered partition of [n], and 0
elsewhere. It is nonzero, because [n] ∖ U has a + b elements and can be split into an a-set and a b-set; and
different rows have disjoint supports, because (A, B) determines U = [n] ∖ (A ∪ B). So the C(n, c) rows are linearly
independent over every field, rank M₃ = C(n, c), and the flattening Lemma gives R̲_F ≥ C(n, c): C(7, 4) = 35 for
T_{1,2,4} and C(c+2, c) = C(c+2, 2) for T_{1,1,c}, over every field F and over ℂ. ∎

**Rank one above the dimension.** Write T = T_{a,b,c} ∈ A ⊗ B ⊗ C with dim C = C(n, c), and for γ ∈ C* let T(γ) be
the matrix in A ⊗ B obtained by contracting the third factor with γ.

*Lemma (standard).* Let T ∈ A ⊗ B ⊗ C be such that γ ↦ T(γ) is injective on C*, and let r = dim C. If R_F(T) = r,
then {T(γ) : γ ∈ C*} contains a nonzero matrix of rank one.

*Proof.* Write T = Σ_{l=1}^{r} a_l ⊗ b_l ⊗ c_l. If the c_l did not span C, some γ ≠ 0 would vanish on all of them and
T(γ) = 0, against injectivity; so c_1, …, c_r is a basis of C. For the dual basis γ_1, …, γ_r, T(γ_l) = a_l ⊗ b_l,
which is nonzero by injectivity and has rank one. ∎

*Application.* The argument for M₃ above, which works for every (a, b, c) with a, b ≥ 1, shows that the C(n, c) rows
of M₃(T_{a,b,c}) are linearly independent over every field, that is, γ ↦ T(γ) is injective; so R_F(T_{a,b,c}) ≥ C(n, c).
For γ ∈ C*, T(γ) is the matrix with entry γ([n] ∖ (S ∪ W)) in row S (an a-subset) and column W (a b-subset) when
S ∩ W = ∅, and 0 when S ∩ W ≠ ∅. Suppose T(γ) = u vᵀ with u ≠ 0, and pick S₀ with u_{S₀} ≠ 0. Let W be any b-subset.
- If W ∩ S₀ ≠ ∅, the entry (S₀, W) is 0, so u_{S₀} v_W = 0 and v_W = 0.
- If W ∩ S₀ = ∅, pick s ∈ S₀ and t ∈ W (possible since a, b ≥ 1) and put S′ = (S₀ ∖ {s}) ∪ {t} and
  W′ = (W ∖ {t}) ∪ {s}. Then |S′| = a, |W′| = b, S′ ∩ W′ = ∅ and S′ ∪ W′ = S₀ ∪ W, so the entries (S₀, W) and (S′, W′)
  are equal. Since s ∈ W′ ∩ S₀, the first case gives v_{W′} = 0, so u_{S₀} v_W = u_{S′} v_{W′} = 0 and v_W = 0.

So v = 0 and u vᵀ = 0, a contradiction: the slice space contains no nonzero rank-one matrix, the Lemma excludes
R_F = C(n, c), and R_F(T_{a,b,c}) ≥ C(n, c) + 1 over every field F. For (1, 2, 4) this is 36 and for (1, 1, c) it is
C(c+2, 2) + 1. ∎

**Consequences.** Combine the bounds with R̲ ≤ R; the upper bounds need characteristic ≠ 2. For T_{1,1,c} the lower
bound C(c+2, 2) + 1 meets the upper bound of Corollary 2 of the partial-Fourier note. ∎

## Background

These statements are cited, not proved here.

- T_{1,1,1} = P₁ is the 3 × 3 permanent read as a trilinear form in the three rows; its rank is 4 over fields of
  characteristic 0 (Ilten and Teitler, arXiv:1503.00822v2, Remark 2.2; Canad. Math. Bull. 59 (2016)), and its border
  rank is 4 over fields of characteristic 0 (as reported by Han and Song, arXiv:2608.09708v2, pp. 2–3, citing Derksen
  and Makam 2019 for the lower bound). See the public note for both.
- By Remark 1 of the partial-Fourier note, T_{1,1,c} is the trilinear form xᵀ Z y of the product of a symmetric
  (c+2) × (c+2) matrix Z with zero diagonal and a vector. Ye and Lim (arXiv:1601.00292v2, Theorem 14.1; Found.
  Comput. Math. 18 (2018)) prove that over ℂ the same map for symmetric matrices with the diagonal included has rank
  n(n + 1)/2, n the matrix size; they do not treat the zero-diagonal case. Cited for context only.

## Scope

- The note claims exactly the bounds of the Theorem, over the fields stated there; in particular nothing for
  T_{1,3,3} in characteristic 2, and no lower bound in characteristic > 31 except those stated for every field.
- The only exact value it claims is R(T_{1,1,c}) = C(c+2, 2) + 1, over every field of characteristic ≠ 2. It claims
  no other value of a rank or border rank; the border rank of T_{1,1,c} for c ≥ 3 is an open question.
- The computed ranks are for the stated matrices only; nothing is claimed about other projections or other p.

## Verification

```bash
python theorems/tripartition-tensors-small-cases-extension/verify.py            # about 5 minutes
python theorems/tripartition-tensors-small-cases-extension/verify.py --quick    # about a minute
```

Offline, standard library only, about 0.5 GB of memory. `--quick` checks M₂₂₃ modulo 2 and 3 only (which suffices for characteristic 0, 2
and 3). In order, the script checks:

1. that the three projections printed above equal the ones it uses;
2. its two rank routines (exclusive-or basis over 𝔽₂; elimination over 𝔽_q on rows packed into integers) against
   dense Gaussian elimination modulo every prime q ≤ 31 on 45 fixed planted-rank matrices, dense elimination modulo
   2³¹ − 1 against the exact rank over ℚ, and diag(q, 1);
3. its flattening code on the values of the public note (T_{1,1,2}: 40, 39 modulo 5; T_{1,2,2}: 76), and on rank-one
   and diagonal unit tensors with the three projections (C(2p, p) and size · C(2p, p));
4. the upper bounds constructively: decompositions of character type with 26, 42, 56, 57 and C(c+2, 2) + 1
   (1 ≤ c ≤ 12) terms, solved over ℚ and checked entry by entry; every coefficient has a power of 2 as denominator,
   so each identity holds over ℤ[1/2] and hence over every field of characteristic ≠ 2 (this re-checks, for these
   tensors, Theorem 1 of the partial-Fourier note);
5. T_{1,2,3}: rank 121 modulo every prime q ≤ 31;
6. T_{1,3,3}: rank 248 modulo every odd prime q ≤ 31 and 242 modulo 2;
7. T_{2,2,3}: rank 9 646, 9 700, 9 702 as stated, modulo every prime q ≤ 31; and a control: a fixed sum of 38 rank-one
   tensors of format 35 × 21 × 21 gives rank 9 552 modulo 2 and 9 576 = 38 · 252 modulo 3, so the method does not
   certify 39 for it;
8. T_{1,2,4} and T_{1,1,c} (1 ≤ c ≤ 20): the rows of M₃ are nonzero with pairwise disjoint supports, and the rank modulo
   every prime q ≤ 31 equals the number of rows;
9. the rank bound C(n, c) + 1: the exchange step of its proof for every disjoint pair in (1,2,3), (1,2,4), (1,3,3),
   (2,2,3) and (1,1,c), c ≤ 8; and, as a sanity check of the conclusion, that no nonzero slice of T_{1,1,c} has rank
   one, exhaustively over 𝔽₂ for c ≤ 4 and over 𝔽₃ for c ≤ 2. The theorem itself rests on the written proof, which
   holds for every c and every field.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time on
the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 12 October 2026, in addition to the search of 8 October 2026 recorded in the public note: the works citing
Pratt (2023/2024), Björklund–Kaski–Koana–Nederlof (2026) or Flavi–Jelisiejew–Michałek (2025) listed by Semantic
Scholar and OpenAlex, read in full text (keyword search of the whole text and reading of every passage on tensors):
arXiv:2608.08328, 2607.25973v2, 2608.12224, 2601.05044, 2602.12762, 2605.21738v2, 2609.39062, 2602.11975; and keyword
searches on arXiv and the web for tripartitioning, partition and matching tensors. None states a value or bound for
T_{1,2,3}, T_{1,2,4}, T_{1,3,3}, T_{2,2,3} or T_{1,1,c} with c ≥ 2. For the rank of T_{1,1,c} we also read Ye and Lim (arXiv:1601.00292v2,
§§14–15): they treat the symmetric matrix–vector product with the diagonal included (rank n(n + 1)/2, Theorem 14.1) and
the skew-symmetric one (bounds only), not the zero-diagonal symmetric case, and they state no bound of the form
dimension + 1 for it. Doležálek and Michałek (arXiv:2602.12762v1, §6.3)
mention matching tensors among special tensors on which their new equations were not checked.
The other citing works listed there (arXiv:2404.06427, 2411.15789, 2411.02936v3, 2505.22410, 2507.11098v2,
2510.08185, 2510.08336), Björklund–Kaski (arXiv:2310.11926) and Björklund–Curticapean–Husfeldt–Kaski–Pratt
(arXiv:2404.04987) were checked by keyword search of the full text; they cite these papers for conditional or
algorithmic results and state no rank or border rank bound for the tensors of this note.

## Sources

- J. M. Landsberg, G. Ottaviani (2015). *New lower bounds for the border rank of matrix multiplication*. Theory of
  Computing 11(1), 285–298. [doi:10.4086/toc.2015.v011a011](https://doi.org/10.4086/toc.2015.v011a011). Credit for
  the Koszul flattening bound, proved in the P₂ border-rank note.
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754. Base of the partial-Fourier note.
- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36).
- N. Ilten, Z. Teitler (2016). *Product Ranks of the 3 × 3 Determinant and Permanent*. Canadian Mathematical
  Bulletin 59(2), 311–319. [doi:10.4153/CMB-2015-076-1](https://doi.org/10.4153/CMB-2015-076-1).
- K. Ye, L.-H. Lim (2018). *Fast Structured Matrix Computations: Tensor Rank and Cohn–Umans Method*. Foundations of
  Computational Mathematics 18(1), 45–95. [doi:10.1007/s10208-016-9332-x](https://doi.org/10.1007/s10208-016-9332-x).
- J. I. Han, J. Song (2026). *The rank of the 5×5 permanent tensor is sixteen*. arXiv:2608.09708v2.
- M. Doležálek, M. Michałek (2026). *Nonlinear methods for tensors: determinantal equations for secant varieties
  beyond cactus*. arXiv:2602.12762v1.

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
