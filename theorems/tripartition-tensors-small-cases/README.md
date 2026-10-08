# Rank and border rank of three small tripartitioning tensors

> **Provenance: own result.** The literature checked for this note (see [Literature checked](#literature-checked))
> states no value or bound for these three tensors. This is a statement about that search, not a claim of
> priority.

| Tensor | Size | Lower bound | Upper bound | Consequence |
|---|---|---|---|---|
| T_{1,1,2} | 4 × 4 × 6 | border rank ≥ 7 | rank ≤ 7 | rank = border rank = 7 |
| T_{1,1,3} | 5 × 5 × 10 | border rank ≥ 10 | rank ≤ 11 | 10 ≤ border rank ≤ rank ≤ 11 |
| T_{1,2,2} | 5 × 10 × 10 | border rank ≥ 13 | rank ≤ 14 | 13 ≤ border rank ≤ rank ≤ 14 |

The fields for which each entry is proved are stated in the Theorem below.

## Definitions

- **Tensors.** For a, b, c ≥ 0 and n = a + b + c, T_{a,b,c} = Σ x_A y_B z_C over all ordered partitions (A, B, C) of
  [n] = {1, …, n} with |A| = a, |B| = b, |C| = c, as in
  [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/). The coordinates of
  each factor are the subsets of the corresponding size of [n], in increasing order of Σ_{e ∈ S} 2^(e−1)
  (colexicographic order), numbered from 0. For example, for T_{1,1,2} the first two factors have coordinates
  {1}, {2}, {3}, {4} and the third has {1,2}, {1,3}, {2,3}, {1,4}, {2,4}, {3,4}.
- **Rank and border rank** as in
  [tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/): R_F is the
  tensor rank over F; R̲_ℂ the border rank over ℂ (Euclidean limits); R̲_F, for any field F, the algebraic border
  rank (Σ_{i ≤ r} u_i(ε) ⊗ v_i(ε) ⊗ w_i(ε) = ε^h T + ε^{h+1} T₁(ε) with polynomial entries). R̲ ≤ R always.
- **Koszul–Young flattening** K_p(T′) of a tensor whose first factor has dimension 2p + 1, as defined in that note,
  applied to the tensor with its factors in a stated order.
- **Data.** [data/](data/) holds the three files `T112_rank7.json`, `T113_rank11.json` and `T122_rank14.json`
  (SHA-256 in [data/README.md](data/README.md)). Each holds integer matrices A, B, C with one row per coordinate of
  the first, second and third factor and one column per term, with the fields `"tensor"`, `"scale": "1/4"` and
  `"rank"`; column r gives the term a_r ⊗ b_r ⊗ c_r.

## Statement

**Theorem.**

1. *Upper bounds.* The entries of the three data files lie in {−1, 0, 1}, and over ℤ
   4 T_{1,1,2} = Σ_{r=1}^{7} a_r ⊗ b_r ⊗ c_r, 4 T_{1,1,3} = Σ_{r=1}^{11} a_r ⊗ b_r ⊗ c_r and
   4 T_{1,2,2} = Σ_{r=1}^{14} a_r ⊗ b_r ⊗ c_r. Hence, for every field F of characteristic ≠ 2,
   R_F(T_{1,1,2}) ≤ 7, R_F(T_{1,1,3}) ≤ 11 and R_F(T_{1,2,2}) ≤ 14.
2. *Lower bounds.* R̲(T_{1,1,2}) ≥ 7 and R̲(T_{1,2,2}) ≥ 13 over ℂ and over every field of characteristic 0 or of
   prime characteristic q ≤ 31. R̲_F(T_{1,1,3}) ≥ 10 over ℂ and over every field F.
3. *Consequences.* R(T_{1,1,2}) = R̲(T_{1,1,2}) = 7 over ℂ and over every field of characteristic 0 or of prime
   characteristic 3 ≤ q ≤ 31. Over every field of characteristic ≠ 2, 10 ≤ R̲(T_{1,1,3}) ≤ R(T_{1,1,3}) ≤ 11; over
   ℂ and every field of characteristic 0 or 3 ≤ q ≤ 31, 13 ≤ R̲(T_{1,2,2}) ≤ R(T_{1,2,2}) ≤ 14.

The proof uses three computed facts: the ranks of the two flattening matrices below modulo every prime q ≤ 31, and
the 846 integer equations of the three identities.

## Proof

**Upper bounds.** As in the companion note on P₂: each identity is the system of its integer coefficient
equations (4 · 4 · 6 = 96, 5 · 5 · 10 = 250 and 5 · 10 · 10 = 500 equations), which `verify.py` evaluates exactly,
together with the range of the entries. In a field of characteristic ≠ 2, 4 is invertible, so each tensor is the
sum of the stated number of rank-one tensors (4⁻¹ a_r) ⊗ b_r ⊗ c_r. The bounds 7 and 11 also follow from
Corollary 2 of [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/):
1 + C(4, 2) = 7 and 1 + C(5, 2) = 11.

**Two facts used for the lower bounds.**

- *Permuting factors.* If T^σ is T with its three factors permuted, then R(T^σ) = R(T) and R̲(T^σ) = R̲(T), in both
  definitions: permuting the factors of a rank-one tensor gives a rank-one tensor, and the permutation is linear,
  hence continuous, and can be applied coefficientwise in ε.
- *Lemma 3 of the border-rank note* (proved there for the algebraic definition over every field and for the
  topological one over ℂ): R̲(T) ≥ rank K_p((Φ ⊗ 1 ⊗ 1)T) / C(2p, p), and *Lemma 4* there: for an integer matrix
  M, rank over a field of characteristic q equals rank_{𝔽_q}(M mod q), and over a field of characteristic 0 it is
  rank_ℚ(M) ≥ rank_{𝔽_q}(M mod q).

**Lemma (flattening bound for border rank).** For T ∈ F^{n₁} ⊗ F^{n₂} ⊗ F^{n₃}, let M₃(T) be the n₃ × (n₁ n₂) matrix
with entries M₃(T)[k, (i, j)] = T[i][j][k]. Then R̲_F(T) ≥ rank_F M₃(T) (algebraic definition, every field F) and
R̲_ℂ(T) ≥ rank M₃(T) (topological definition).

*Proof.* T ↦ M₃(T) is linear, and M₃(u ⊗ v ⊗ w) = w (u ⊗ v)ᵀ has rank at most 1. The rest is the proof of Lemma 3
in the border-rank note, parts (b), (c) and (d), with K_p replaced by M₃ and C(2p, p) by 1: a sum of r rank-one
tensors has a flattening of rank at most r; over ℂ, the minors of size r + 1 are continuous and vanish along the
sequence; over F, a nonzero s × s minor of M₃(T) is the value at ε = 0 of the same minor of M₃(T) + ε N(ε), which
is therefore nonzero in F(ε), so s ≤ r. ∎

**T_{1,1,2} ≥ 7.** Order the factors as (third, first, second), so that the first factor, of dimension
C(4, 2) = 6, is projected by

    Φ = [ I₅ | 1 ] = [ 1 0 0 0 0 1 ; 0 1 0 0 0 1 ; 0 0 1 0 0 1 ; 0 0 0 1 0 1 ; 0 0 0 0 1 1 ]

(5 × 6; column a belongs to coordinate a of the third factor of T_{1,1,2}), and take p = 2. The matrix
K₂((Φ ⊗ 1 ⊗ 1)T^σ) is 40 × 40 (C(5,2) · 4 columns, C(5,3) · 4 rows) with integer entries. `verify.py` computes its
rank modulo every prime q ≤ 31: 40, except 39 for q = 5. Each value exceeds 36 = 6 · C(4, 2). By Lemma 4, the rank
over a field of characteristic q ≤ 31 is the value for q, and over a field of characteristic 0 (in particular ℂ) it
is at least 40. By Lemma 3, R̲ ≥ 39/6 > 6, so R̲(T_{1,1,2}) ≥ 7 for these fields.

**T_{1,2,2} ≥ 13.** Keep the order of the factors; the first has dimension 5 = 2p + 1 for p = 2, and Φ = I₅. The
matrix K₂(T_{1,2,2}) is 100 × 100 (C(5,2) · 10 columns, C(5,3) · 10 rows) with integer entries, and `verify.py`
finds rank 76 modulo every prime q ≤ 31. As 76 > 72 = 12 · 6, Lemmas 3 and 4 give R̲(T_{1,2,2}) ≥ 76/6 > 12, that
is R̲ ≥ 13, over ℂ and over every field of characteristic 0 or q ≤ 31.

**T_{1,1,3} ≥ 10.** Row U of M₃(T_{1,1,3}) (U a 3-subset of [5]) has entry 1 in the columns (A, B) with (A, B, U)
a partition of [5], and 0 elsewhere. Each row is nonzero, and different rows have disjoint supports because (A, B)
determines U = [5] ∖ (A ∪ B). So the 10 rows are linearly independent over every field, rank M₃ = 10, and the
Lemma gives R̲_F(T_{1,1,3}) ≥ 10 for every field F and over ℂ. ∎

**Consequences.** Combine the bounds, using R̲ ≤ R; for T_{1,1,2} and T_{1,2,2} the upper bound needs
characteristic ≠ 2 and the lower bound characteristic 0 or q ≤ 31. ∎

## Background

These statements are cited, not proved here.

- The smallest member of the family T_{1,1,c} with c ≥ 1, T_{1,1,1} = P₁ = Σ_{σ ∈ S₃} x_{σ(1)} y_{σ(2)} z_{σ(3)}, is
  the 3 × 3 permanent, read as a trilinear form in the three rows. Its tensor rank is 4 over fields of
  characteristic 0 (Ilten and Teitler, arXiv:1503.00822v2, Remark 2.2, p. 4; Canad. Math. Bull. 59 (2016)), and its
  border rank is 4 over fields of characteristic 0 (lower bound ≥ 4 by Derksen and Makam 2019; the value then
  follows with Fischer's formula; as reported by Han and Song, arXiv:2608.09708v2, pp. 2–3). In the literature
  checked this is the only previously known value of the rank of T_{1,1,c} with c ≥ 1.
- Ye and Lim (arXiv:1601.00292v2, §14, Theorem 14.1, p. 27; Found. Comput. Math. 18 (2018)) prove that over ℂ the
  bilinear map (S, v) ↦ Sv on symmetric n × n matrices S, diagonal included, has rank n(n + 1)/2. They do not
  treat the case of zero diagonal, which is T_{1,1,c} with n = c + 2 (Remark 1 of the note
  [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/)). Their theorem is
  cited for context only.

## Scope

- The note claims exactly the bounds of the Theorem, over the fields stated there. It claims neither the rank nor
  the border rank of T_{1,1,3} or T_{1,2,2}.
- The computed ranks are for the stated matrices only; no claim is made about other projections or other p.

## Verification

```bash
python theorems/tripartition-tensors-small-cases/verify.py
```

Offline, standard library only, well under a second. In order, the script checks:

1. the SHA-256 of the three data files, before reading anything else from them;
2. for each file, the keys, the tensor name, `"scale": "1/4"`, the number of terms, the matrix shapes and that every
   entry is −1, 0 or 1; and the identity at all 96, 250 and 500 coefficients, in integer arithmetic;
3. its flattening and rank code on cases proved in the border-rank note: rank-one tensors give C(4, 2) = 6 and the
   unit tensor ⟨5⟩ gives 30 (p = 2), modulo every prime q ≤ 31;
4. T_{1,1,2}: the 40 × 40 matrix above has rank 40 modulo every prime q ≤ 31 except 39 modulo 5;
5. T_{1,2,2}: the 100 × 100 matrix above has rank 76 modulo every prime q ≤ 31;
6. T_{1,1,3}: the 10 rows of M₃ are nonzero with pairwise disjoint supports, and the rank is 10 modulo every
   prime q ≤ 31;
7. that 7 and 11 equal 1 + C(c+2, 2) for c = 2, 3.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time
on the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 8 October 2026: Pratt (arXiv:2311.02774v1), Björklund, Kaski, Koana and Nederlof (ICALP 2026), Flavi,
Jelisiejew and Michałek (arXiv:2408.02754v2, §6), the works citing Pratt or Björklund–Kaski–Koana–Nederlof found
through Semantic Scholar, OpenAlex and OpenCitations, and keyword searches on arXiv and the web for tripartitioning
tensors; for T_{1,1,c} also the descriptions of Remark 1 of the partial-Fourier note and the degree-1 × degree-1 →
degree-2 multiplication in K[x_1, …, x_n]/(x_1², …, x_n²), with Ye and Lim (2018) and the works citing it. None
states a value or bound for T_{1,1,2}, T_{1,1,3} or T_{1,2,2}.

## Sources

- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36).
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754.
- J. M. Landsberg, G. Ottaviani (2015). *New lower bounds for the border rank of matrix multiplication*. Theory of
  Computing 11(1), 285–298. [doi:10.4086/toc.2015.v011a011](https://doi.org/10.4086/toc.2015.v011a011). Credit for
  the Koszul flattening bound (Theorem 2.1 of arXiv:1112.6007v3), proved in the border-rank note.
- K. Ye, L.-H. Lim (2018). *Fast Structured Matrix Computations: Tensor Rank and Cohn–Umans Method*. Foundations of
  Computational Mathematics 18(1), 45–95. [doi:10.1007/s10208-016-9332-x](https://doi.org/10.1007/s10208-016-9332-x);
  arXiv:1601.00292 (read: v2). Theorem 14.1 (v2, p. 27), cited for context.
- N. Ilten, Z. Teitler (2016). *Product Ranks of the 3 × 3 Determinant and Permanent*. Canadian Mathematical
  Bulletin 59(2), 311–319. [doi:10.4153/CMB-2015-076-1](https://doi.org/10.4153/CMB-2015-076-1); arXiv:1503.00822
  (read: v2). Remark 2.2 (v2, p. 4).
- J. I. Han, J. Song (2026). *The rank of the 5×5 permanent tensor is sixteen*. arXiv:2608.09708v2, pp. 2–3.

## Licence

The data files and this text are under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the
Apache License 2.0 ([LICENSE](../../LICENSE)).
