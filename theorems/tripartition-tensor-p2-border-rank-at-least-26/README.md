# The balanced tripartitioning tensor P₂ has border rank at least 26

> **Provenance: own result.** The bound is obtained with a Koszul–Young flattening, the method of Landsberg and
> Ottaviani (see [Credit](#credit)); the method is credited, and its proof is written out below. The literature
> checked for this note (see [Literature checked](#literature-checked)) states no unconditional lower bound on the
> border rank of P₂, and no lower bound on its rank or border rank above 15. This is a statement about that search,
> not a claim of priority.

## Definitions

**The tensor.** P₂ = Σ x_A y_B z_C, the sum over all ordered partitions (A, B, C) of {1, …, 6} into three 2-sets,
as in the companion note [tripartition-tensor-p2-rank-at-most-29](../tripartition-tensor-p2-rank-at-most-29/)
(Pratt's T₂, Björklund–Kaski–Koana–Nederlof's P₂). Its three factors are A = B = C = F^15, with coordinate i
(i = 0, …, 14) the i-th 2-subset S_i of {1, …, 6} in increasing order of Σ_{e ∈ S} 2^(e−1), exactly as in the
companion note. Its coefficients are P₂[i][j][k] = 1 if S_i, S_j, S_k are pairwise disjoint and 0 otherwise.

**Rank and border rank.** R_F(T) is the least r with T = Σ_{i=1}^{r} u_i ⊗ v_i ⊗ w_i over the field F.

- *Over ℂ* (topological definition): R̲_ℂ(T) is the least r such that T is a limit, in the Euclidean topology of
  the finite-dimensional space ℂ^{n₁} ⊗ ℂ^{n₂} ⊗ ℂ^{n₃}, of tensors of rank at most r.
- *Over any field F* (algebraic definition): R̲_F(T) is the least r for which there are h ≥ 0 and vectors
  u_i(ε), v_i(ε), w_i(ε) whose entries are polynomials in ε over F (i = 1, …, r) such that
  Σ_{i=1}^{r} u_i(ε) ⊗ v_i(ε) ⊗ w_i(ε) = ε^h T + ε^{h+1} T₁(ε) for some tensor T₁(ε) with entries in F[ε].

Both are at most R_F(T) (constant sequence; h = 0).

**Exterior powers.** For V = F^{2p+1} with basis e_1, …, e_{2p+1} and a set S = {s_1 < ⋯ < s_p}, write
e_S = e_{s_1} ∧ ⋯ ∧ e_{s_p}; these form a basis of Λ^p V. For i ∉ S, e_i ∧ e_S = sgn(i, S) e_{S ∪ {i}} with
sgn(i, S) = (−1)^{|{s ∈ S : s < i}|}, and e_i ∧ e_S = 0 for i ∈ S.

**Koszul–Young flattening.** Let T′ ∈ F^{2p+1} ⊗ F^{n₂} ⊗ F^{n₃} have coefficients T′[i][j][k]. Its flattening
K_p(T′) is the linear map Λ^p F^{2p+1} ⊗ (F^{n₂})* → Λ^{p+1} F^{2p+1} ⊗ F^{n₃},
e_S ⊗ y_j* ↦ Σ_{i,k} T′[i][j][k] (e_i ∧ e_S) ⊗ z_k. As a matrix, with columns indexed by (S, j) (|S| = p) and
rows by (U, k) (|U| = p + 1),

    K_p(T′)[(U, k), (S, j)] = sgn(i, S) · T′[i][j][k]   if U = S ∪ {i} with i ∉ S,   and 0 otherwise.

It has C(2p+1, p) n₂ columns and C(2p+1, p+1) n₃ rows, and T′ ↦ K_p(T′) is linear. For an m × n₁ matrix Φ
(m = 2p + 1) and T ∈ F^{n₁} ⊗ F^{n₂} ⊗ F^{n₃}, (Φ ⊗ 1 ⊗ 1)T is the tensor with coefficients
Σ_a Φ[i][a] T[a][j][k].

**The projection.** p = 3, so m = 7 and C(2p, p) = 20, and Φ is the following 7 × 15 integer matrix (column a
belongs to coordinate a of the first factor):

<!-- PHI -->
```
[  0,  1,  0, -1,  0, -1,  1,  1,  1,  0,  1,  0,  0, -1,  1 ]
[ -1,  0, -1, -1,  0, -1,  0, -1,  0, -1,  1,  1,  1,  0, -1 ]
[  0,  0, -1,  0, -1,  0,  1,  0, -1,  0, -1,  1,  1,  1,  1 ]
[ -1, -1, -1, -1, -1,  0, -1,  0,  1, -1,  1, -1, -1,  1, -1 ]
[  0,  0,  0,  0, -1, -1,  1,  0, -1,  1,  1, -1, -1, -1, -1 ]
[  0,  0, -1,  1,  1,  1,  0, -1, -1, -1,  1,  1, -1,  0,  1 ]
[  1,  1,  1,  1, -1, -1,  0,  0,  1, -1, -1,  1,  1, -1,  0 ]
```
<!-- PHI -->

Let M = K₃((Φ ⊗ 1 ⊗ 1)P₂), a 525 × 525 matrix with integer entries (35 · 15 rows and columns).

## Statement

**Theorem.**

1. R̲_ℂ(P₂) ≥ 26.
2. For every field F of characteristic 0, and for every field F whose characteristic is a prime q ≤ 31,
   R̲_F(P₂) ≥ 26 (algebraic definition), and hence R_F(P₂) ≥ 26.

The proof uses one computed fact: the rank of M modulo q is 502 for q = 2 and 504 for every prime 3 ≤ q ≤ 31.

**Corollary (with the companion note).** Over ℂ, and over every field of characteristic 0 or of prime
characteristic 3 ≤ q ≤ 31:  26 ≤ R̲(P₂) ≤ R(P₂) ≤ 29.

## Proof

**Lemma 1 (wedge with a vector).** Let K be a field, V = K^{2p+1} and α ∈ V, α ≠ 0. The map Λ^p V → Λ^{p+1} V,
ω ↦ α ∧ ω, has rank C(2p, p).

*Proof.* The rank of a linear map does not depend on the basis used to write it. Choose a basis f_1 = α,
f_2, …, f_{2p+1} of V; the f_S (|S| = p) form a basis of Λ^p V and the f_U (|U| = p + 1) one of Λ^{p+1} V. Then
α ∧ f_S = 0 if 1 ∈ S, and α ∧ f_S = f_{{1} ∪ S} if 1 ∉ S (1 is the smallest index, so the sign is +). The image is
spanned by the C(2p, p) distinct basis vectors f_{{1} ∪ S}, S ⊆ {2, …, 2p+1}, |S| = p. ∎

**Lemma 2 (rank-one tensors).** Over any field K, if α ∈ K^{2p+1}, β ∈ K^{n₂}, γ ∈ K^{n₃} are all nonzero, then
rank K_p(α ⊗ β ⊗ γ) = C(2p, p). If one of them is zero, the rank is 0.

*Proof.* By the definition, K_p(α ⊗ β ⊗ γ)[(U, k), (S, j)] = W_α[U, S] · γ_k β_j, where W_α is the matrix of
ω ↦ α ∧ ω in the bases e_S, e_U. So K_p(α ⊗ β ⊗ γ) is the Kronecker product W_α ⊗ (γ βᵀ), whose rank is
rank(W_α) · rank(γ βᵀ) = C(2p, p) · 1 by Lemma 1. If α, β or γ is zero, the matrix is zero. ∎

**Lemma 3 (Koszul–Young bound; Landsberg–Ottaviani, arXiv:1112.6007v3, Theorem 2.1).** Let T ∈ F^{n₁} ⊗ F^{n₂} ⊗ F^{n₃},
p ≥ 1, and let Φ be a (2p+1) × n₁ matrix over F. Then

    R̲_F(T) ≥ rank_F K_p((Φ ⊗ 1 ⊗ 1)T) / C(2p, p),

for the algebraic definition over every field F, and for the topological definition over F = ℂ.

*Proof.* Write T′ = (Φ ⊗ 1 ⊗ 1)T and c = C(2p, p).

(a) *Projection does not raise rank.* (Φ ⊗ 1 ⊗ 1)(u ⊗ v ⊗ w) = (Φu) ⊗ v ⊗ w, so applying Φ ⊗ 1 ⊗ 1 to a sum of r
rank-one tensors gives a sum of r rank-one tensors (some possibly zero).

(b) *Rank.* If T = Σ_{i=1}^{r} u_i ⊗ v_i ⊗ w_i, then by (a), linearity and Lemma 2, K_p(T′) is a sum of r matrices
of rank at most c, so rank K_p(T′) ≤ r c.

(c) *Topological border rank over ℂ.* Let T = lim T_m with R_ℂ(T_m) ≤ r. The maps T ↦ T′ and T′ ↦ K_p(T′) are
linear, hence continuous, so K_p(T′_m) → K_p(T′). By (b), every (rc + 1) × (rc + 1) minor of K_p(T′_m) is 0;
minors are polynomials in the entries, hence continuous, so every such minor of K_p(T′) is 0, and
rank K_p(T′) ≤ rc.

(d) *Algebraic border rank over F.* Let Σ_{i=1}^{r} u_i(ε) ⊗ v_i(ε) ⊗ w_i(ε) = ε^h T + ε^{h+1} T₁(ε). Apply
Φ ⊗ 1 ⊗ 1 and then K_p, both F[ε]-linear when applied coefficientwise: the left side becomes a sum of r matrices
over the field F(ε) of rank at most c (Lemma 2 over K = F(ε)), so its rank over F(ε) is at most rc. The right side
becomes ε^h (K_p(T′) + ε N(ε)) for a matrix N(ε) over F[ε]. Let s = rank_F K_p(T′) and pick a nonzero s × s minor of
K_p(T′). The same minor of K_p(T′) + ε N(ε) is a polynomial in ε whose value at ε = 0 is that nonzero minor, so it
is a nonzero element of F(ε). Hence s ≤ rank_{F(ε)}(K_p(T′) + εN(ε)) = rank_{F(ε)}(ε^{−h} · left side) ≤ rc. ∎

**Lemma 4 (ranks of integer matrices in different fields).** Let M be a matrix with integer entries and q a prime.

1. If F has characteristic q, then rank_F(M) = rank_{𝔽_q}(M mod q).
2. If F has characteristic 0, then rank_F(M) = rank_ℚ(M) ≥ rank_{𝔽_q}(M mod q).

*Proof.* The rank over a field is the largest size of a nonzero minor. A minor of M is an integer, mapped into the
prime field 𝔽_q or ℚ of F; whether it is zero does not depend on the field containing the prime field. This gives
both equalities. A minor that is nonzero modulo q is a nonzero integer, hence nonzero in ℚ; this gives the
inequality. ∎

**Proof of the Theorem.** Apply Lemma 3 with T = P₂, p = 3 and the projection Φ above, an integer matrix, so the
flattening K₃((Φ ⊗ 1 ⊗ 1)P₂) over any field is the image of the integer matrix M. `verify.py` computes the rank of
M modulo q by Gaussian elimination in 𝔽_q: 502 for q = 2 and 504 for every prime 3 ≤ q ≤ 31.

- Part 2, characteristic q ≤ 31: rank_F(M) = rank_{𝔽_q}(M mod q) ≥ 502 by Lemma 4.1.
- Part 2, characteristic 0, and Part 1 (ℂ has characteristic 0): rank(M) = rank_ℚ(M) ≥ rank_{𝔽_3}(M mod 3) = 504
  by Lemma 4.2.

In all cases rank(M) ≥ 502 > 500 = 25 · 20, so Lemma 3 gives R̲(P₂) ≥ 502/20 > 25, that is R̲(P₂) ≥ 26. The rank
satisfies R_F ≥ R̲_F. ∎

**Proof of the Corollary.** The companion note proves R_F(P₂) ≤ 29 for every field of characteristic ≠ 2, and
R̲ ≤ R always. ∎

**Example (used as a self-test).** For the unit tensor ⟨m⟩ = Σ_{j=1}^{m} e_j ⊗ e_j ⊗ e_j and any (2p+1) × m
matrix Φ with no zero column, rank K_p((Φ ⊗ 1 ⊗ 1)⟨m⟩) = m · C(2p, p). Indeed, the j-th term contributes the matrix
of Lemma 2 for (Φe_j) ⊗ e_j ⊗ e_j, which is supported on the columns (S, j) and the rows (U, j); these blocks are
disjoint for different j, so their ranks add. Lemma 3 then gives exactly R̲(⟨m⟩) ≥ m, and ⟨m⟩ has rank at most m.

## Credit

The bound of Lemma 3 is Theorem 2.1 of J. M. Landsberg and G. Ottaviani, *New lower bounds for the border rank of
matrix multiplication* (arXiv:1112.6007v3, p. 3; published in Theory of Computing 11, 2015): for T ∈ A ⊗ B ⊗ C with
dim A = a, the border rank is at least rank T_A^{∧p} / C(a − 1, p). Lemma 3 is the case a = 2p + 1, applied after
the projection Φ. Young flattenings in general are from their paper *Equations for secant varieties of Veronese
and other varieties* (2013). The proof above is written out for this note; the citations are credit.

## Background

These statements are cited, not proved here (Lemmas 1 and 2 of the companion note prove the flattening bound for every field).

- The only unconditional published lower bound on the rank of P_d found is the flattening bound
  R(P_d) ≥ C(3d, d), 15 for d = 2: "By flattening P_d into a matrix and observing a large identity submatrix, we
  have that R(P_d) ≥ C(3d, d)" (Björklund, Kaski, Koana, Nederlof, proof of Theorem 1.2: arXiv:2504.05772v1,
  p. 13; ICALP 2026, p. 36:16). Pratt's Corollary 1.12 (arXiv:2311.02774v1, p. 4) gives a lower bound conditional
  on the set cover conjecture; for d = 2 it is 640/81.

## Scope

- The note claims R̲(P₂) ≥ 26 over ℂ (topological definition), and over every field of characteristic 0 or of
  prime characteristic q ≤ 31 (algebraic definition). It makes no claim for other characteristics.
- It claims no value of the border rank or of the rank of P₂, and no statement about P_d for d ≥ 3.
- The computed ranks are the ranks of M for the projection Φ above; nothing is claimed about other projections or
  other values of p.

## Verification

```bash
python theorems/tripartition-tensor-p2-border-rank-at-least-26/verify.py
```

Offline, standard library only, a few seconds. In order, the script checks:

1. that the matrix Φ printed above equals the one it uses, and that Φ has no zero column;
2. its two rank routines: on 45 fixed integer matrices with planted ranks 0–8 the rank modulo 2³¹ − 1 equals the
   exact rank over ℚ (computed with fractions), and the rank modulo every prime q ≤ 31 is at most it; and
   diag(q, 1) has rank 2 over ℚ and 1 modulo q (Lemma 4 can be strict);
3. Lemma 2: rank-one tensors give rank exactly C(2p, p) for p = 1, 2, 3, modulo every prime q ≤ 31;
4. the Example: ⟨2p+1⟩ with the identity projection (p = 1, 2, 3) and ⟨15⟩ with Φ (p = 3) give m · C(2p, p);
5. linearity on real data: with the 29-term identity of the companion note (its data file, SHA-256 checked),
   K₃((Φ ⊗ 1 ⊗ 1)(4P₂)) equals the sum of the 29 term flattenings entry by entry, and the partial sums of the first
   1, 3 and 10 terms have rank at most 20, 60 and 200 modulo 3 (Lemma 3(b));
6. that P₂ has 90 nonzero coefficients and M is 525 × 525, and the rank of M modulo every prime q ≤ 31: 502 for
   q = 2, 504 otherwise; each exceeds 500, so ⌈rank/20⌉ = 26.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count (field operations of the
eliminations, entries built), and its wall-clock time on the next line. The script ends with `ALL CHECKS PASSED` and
exit code 0, or exits with code 1.

## Literature checked

Search of 8 October 2026: the papers below; the works citing Pratt (2023) or Björklund, Kaski, Koana and Nederlof
(2026) found through Semantic Scholar, OpenAlex and OpenCitations (read at least by keyword search of the full
text); keyword searches on arXiv and the web for tripartitioning tensors and for P₂ described through the perfect
matchings of K₆. No lower bound on the rank or border rank of P₂ above 15 was found.

- K. Pratt, arXiv:2311.02774v1, and A. Björklund, P. Kaski, T. Koana, J. Nederlof, ICALP 2026: full texts read.
  Neither gives a lower bound on the rank or border rank of P₂ beyond the flattening bound N = 15 (Pratt: "if T is
  concise, then R(T) ≥ n", §1.1; Björklund et al.: the flattening argument in §1.1, footnote 2, and in the proof of
  Theorem 1.2 in §4.2).
- C. Flavi, J. Jelisiejew, M. Michałek, arXiv:2408.02754v2 (§6 read): upper bounds only.

## Sources

- J. M. Landsberg, G. Ottaviani (2013). *Equations for secant varieties of Veronese and other varieties*. Annali di
  Matematica Pura ed Applicata 192(4), 569–606.
  [doi:10.1007/s10231-011-0238-6](https://doi.org/10.1007/s10231-011-0238-6). Credit for Young flattenings.
- J. M. Landsberg, G. Ottaviani (2015). *New lower bounds for the border rank of matrix multiplication*. Theory of
  Computing 11(1), 285–298. [doi:10.4086/toc.2015.v011a011](https://doi.org/10.4086/toc.2015.v011a011);
  arXiv:1112.6007. Credit for the Koszul flattening bound.
- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754.
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36). Full version: arXiv:2504.05772.

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
