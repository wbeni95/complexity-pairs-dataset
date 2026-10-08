# The balanced tripartitioning tensor P₂ has tensor rank at most 29

> **Provenance: own result.** The literature checked for this note (see [Literature checked](#literature-checked))
> states no upper bound on the rank of P₂ below 31. This is a statement about that search, not a claim of
> priority.

The theorem is an explicit identity with 29 terms whose coefficients lie in {−1, 0, 1}. It is stored in
[data/P2_rank29.json](data/P2_rank29.json) and checked entry by entry by [verify.py](verify.py).

## Definitions

**Tripartitioning tensors.** For integers a, b, c ≥ 0 with n = a + b + c ≥ 1, let

    T_{a,b,c} = Σ x_A y_B z_C,

the sum over all ordered partitions (A, B, C) of [n] = {1, …, n} into sets with |A| = a, |B| = b, |C| = c. It is a
trilinear form in the variables x_A (|A| = a), y_B (|B| = b) and z_C (|C| = c), that is, a tensor in
F^(n choose a) ⊗ F^(n choose b) ⊗ F^(n choose c) for any field F, with all coefficients 0 or 1. The *balanced*
tensor is P_d = T_{d,d,d} (d ≥ 1), of size N × N × N with N = N_d = C(3d, d). Three d-subsets of [3d] with union
[3d] are pairwise disjoint, so P_d is the sum of x_A y_B z_C over all A, B, C ∈ C([3d], d) with A ∪ B ∪ C = [3d].

**Notation in the literature.** P_d is the tensor T_k of Pratt (arXiv:2311.02774v1, Definition 1.4), with k = d,
and the tensor P_d of Björklund, Kaski, Koana and Nederlof (ICALP 2026; abstract, and equation (3) with index n).
This note writes P_d throughout. The symbol T_{a,b,c} with three indices is this note's own and is not Pratt's T_k.

**Rank.** The rank R_F(T) of a tensor T over a field F is the least r such that T = Σ_{i=1}^{r} u_i ⊗ v_i ⊗ w_i with
vectors over F.

**Coordinates of P₂.** N₂ = 15. Coordinate i (counting from 0) of each of the three factors is the i-th 2-subset
S_i of {1, …, 6} in increasing order of the number Σ_{e ∈ S} 2^(e−1) (colexicographic order):

| 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| {1,2} | {1,3} | {2,3} | {1,4} | {2,4} | {3,4} | {1,5} | {2,5} | {3,5} | {4,5} | {1,6} | {2,6} | {3,6} | {4,6} | {5,6} |

So P₂ = Σ_{i,j,k} [S_i, S_j, S_k pairwise disjoint] x_{S_i} y_{S_j} z_{S_k}; it has 6!/(2!)³ = 90 nonzero
coefficients.

**The data.** [data/P2_rank29.json](data/P2_rank29.json) (SHA-256
`3a46395da0783d3b315509261ea69fb4bb511ce2418a05b432e4bd0bfea32351`) holds three 15 × 29 integer matrices A, B, C
(keys `"A"`, `"B"`, `"C"`; row i is coordinate i above, column r is term r) and the fields `"tensor": "T_2,2,2"`,
`"scale": "1/4"` and `"rank": 29`. Let a_r, b_r, c_r ∈ ℤ^15 be the r-th columns of A, B, C (r = 1, …, 29).

## Statement

**Theorem.** Every entry of A, B and C is −1, 0 or 1, and

    4 · P₂ = Σ_{r=1}^{29} a_r ⊗ b_r ⊗ c_r      over ℤ,

that is, Σ_{r=1}^{29} A[i][r] B[j][r] C[k][r] = 4 · [S_i, S_j, S_k pairwise disjoint] for all
i, j, k ∈ {0, …, 14}. Consequently R_F(P₂) ≤ 29 for every field F of characteristic ≠ 2.

**Remark (Pratt's finite criterion).** Pratt's Corollary 1.12 (see [Background](#background)) gives the
inequality R(P_k) ≥ θ_k = 8^k · C(3k,k) · C(2k,k) / 27^k for every k, under the set cover conjecture.

**Proposition.** For every field F and every k ≥ 1, R_F(P_k) ≥ N_k = C(3k, k). Moreover θ_k < N_k for
1 ≤ k ≤ 10 and θ_k > N_k for every k ≥ 11. Hence, for 1 ≤ k ≤ 10 and every field F, R_F(P_k) > θ_k holds
without any hypothesis.

So for k ≤ 10 no upper bound on R(P_k), in particular not the Theorem (k = 2, where θ₂ = 640/81 < 8 and
N₂ = 15), can contradict the inequality of Corollary 1.12. In particular, the Theorem is consistent with the
inequality of Corollary 1.12.

**Comparison with published bounds** (see [Background](#background)). The smallest published upper bounds on
R(P₂) found are 31, from the bound of Flavi, Jelisiejew and Michałek (Proposition 6.18), stated over algebraically
closed fields of characteristic 0, and 32 = 8²/2, stated by Pratt (arXiv:2311.02774v1) for every field of
characteristic ≠ 2. The Theorem gives 29 over every field of characteristic ≠ 2: over algebraically closed fields of
characteristic 0 this improves 31 to 29; for the other fields of characteristic ≠ 2 (to which the standing
assumption of Flavi et al. does not apply) the published bound found is 32, and the Theorem gives 29. (The
companion note [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/) proves
the bound 31 over every field of characteristic ≠ 2.)

## Proof

**Theorem.** Two tensors over ℤ are equal if and only if all their coefficients are equal, so the identity is the
system of 15³ = 3375 integer equations written above. `verify.py` checks that every entry of A, B and C lies in
{−1, 0, 1} and evaluates every one of the 3375 equations in exact integer arithmetic (checks 2 and 4). Let F be a
field of characteristic ≠ 2. The ring map ℤ → F sends the identity to 4 · P₂ = Σ_r a_r ⊗ b_r ⊗ c_r over F, and 4 is
invertible in F, so P₂ = Σ_{r=1}^{29} (4⁻¹ a_r) ⊗ b_r ⊗ c_r is a sum of 29 rank-one tensors over F. ∎

**Lemma 1 (flattening).** For a tensor T ∈ F^{n₁} ⊗ F^{n₂} ⊗ F^{n₃}, let M_T be the n₁ × (n₂ n₃) matrix with
entries M_T[i, (j, k)] = T_{ijk}. Then R_F(T) ≥ rank_F(M_T).

*Proof.* T ↦ M_T is linear, and M_{u⊗v⊗w} = u (v ⊗ w)ᵀ has rank at most 1. If T = Σ_{i=1}^{r} u_i ⊗ v_i ⊗ w_i,
then M_T is a sum of r matrices of rank at most 1, and the rank of a sum is at most the sum of the ranks. ∎

**Lemma 2 (P_k is concise in the first factor).** For every field F and k ≥ 1, rank_F(M_{P_k}) = N_k.

*Proof.* Row S of M_{P_k} (S ∈ C([3k], k)) has entry 1 in column (T, U) when (S, T, U) is an ordered partition of
[3k], and 0 elsewhere. It is nonzero: split [3k] ∖ S into two k-sets T, U. Two different rows have disjoint
supports, because the column (T, U) determines S = [3k] ∖ (T ∪ U). Nonzero rows with pairwise disjoint supports
are linearly independent over every field, so the N_k rows have rank N_k. ∎

**Lemma 3 (θ_k against N_k).** Put ρ_k = θ_k / N_k = 8^k C(2k,k) / 27^k. Then ρ_k < 1 for 1 ≤ k ≤ 10 and
ρ_k > 1 for k ≥ 11.

*Proof.* ρ_{k+1}/ρ_k = (8/27) · C(2k+2, k+1)/C(2k, k) = (8/27) · (2k+1)(2k+2)/(k+1)² = 16(2k+1) / (27(k+1)). This
is > 1 if and only if 16(2k+1) > 27(k+1), that is 5k > 11, that is k ≥ 3. So ρ₃ < ρ₄ < ρ₅ < ⋯. The exact integer
comparisons 8^k C(2k,k) < 27^k for k = 1, …, 10 and 8^11 C(22,11) > 27^11 (check 6) give ρ₁, ρ₂, ρ₁₀ < 1 < ρ₁₁. By
monotonicity ρ_k ≤ ρ₁₀ < 1 for 3 ≤ k ≤ 10 and ρ_k ≥ ρ₁₁ > 1 for k ≥ 11. ∎

**Proposition.** Lemmas 1 and 2 give R_F(P_k) ≥ N_k, and Lemma 3 gives N_k > θ_k for k ≤ 10 and N_k < θ_k for
k ≥ 11. For k = 2: θ₂ = 64 · 15 · 6 / 729 = 640/81. ∎

## Background

These statements are cited, not proved here.

- Pratt (arXiv:2311.02774v1, §1.2, item 4 of the numbered comments after Corollary 1.12, p. 4) states the upper
  bound R(T_k) ≤ 8^k/2 for every field with char(F) ≠ 2. For k = 2 this is 32. The version published in the
  STOC 2024 proceedings (doi:10.1145/3618260.3649620) does not contain that item, and its abstract refers to "a
  known upper bound of 8^n on the tensor rank of T_n".
- Flavi, Jelisiejew and Michałek (arXiv:2408.02754v2, Proposition 6.18, p. 31; Proposition 6.17 in v1; published in
  IMRN 2025): "The rank of the tensor T_N is at most ½ 8^k − Σ_{i=k+1}^{⌊N/2⌋} C(N, 2i)", where N = 3k and T_N is
  Pratt's tensor T_k (§6, p. 31). Their standing assumption (§2, p. 7): "In this article we work over an
  algebraically closed field K of characteristic zero." For k = 2 the bound is 32 − C(6, 6) = 31.
- Corollary 1.12 states: if the set cover conjecture is true, then for every k,
  R(T_k) ≥ 8^k · C(3k,k) · C(2k,k) / 27^k ≥ (2/9) · 8^k · k^(−1). (Pratt, arXiv:2311.02774v1, §1.2, p. 4.)
- "Pratt also observes the upper bound R(P_n) ≤ 2^{3n−1} over any field F with char F ≠ 2." (Björklund, Kaski,
  Koana, Nederlof, ICALP 2026, §1.5 "Related work", p. 36:8.)
- Pratt (arXiv:2311.02774v1, §1.1, p. 2) notes that a concise tensor of dimension n has rank at least n, and his
  Proposition 2.1 (p. 4) states that T_k is concise; Lemmas 1 and 2 above prove this for every field. Comment 1
  after Corollary 1.12 (p. 4) states that, assuming the asymptotic rank conjecture, k = 11 is the smallest value
  for which his Theorem 1.9 would beat the 8^n · poly(n)-time algorithm; this is the comparison
  8^k C(2k, k) > 27^k of Lemma 3.

## Scope

- The note claims R_F(P₂) ≤ 29 for every field F of characteristic ≠ 2, and the Proposition for every field. It
  claims nothing about the exact rank or the border rank of P₂ (a lower bound on the border rank is the subject of
  [tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/)).
- In characteristic 2 the identity reads 0 = Σ_r a_r ⊗ b_r ⊗ c_r and gives no bound; the note claims nothing there.
- Nothing is claimed about P_d for d ≥ 3, about asymptotic rank, or about the set cover conjecture beyond the
  Proposition.

## Verification

```bash
python theorems/tripartition-tensor-p2-rank-at-most-29/verify.py
```

Offline, standard library only, well under a second. The script checks, in order:

1. the SHA-256 of `data/P2_rank29.json`, before reading anything else from it;
2. the format: the keys, `"tensor": "T_2,2,2"`, `"scale": "1/4"`, `"rank": 29`, three 15 × 29 matrices, every
   entry in {−1, 0, 1};
3. the coordinate convention: the 2-subsets of {1, …, 6} in increasing bitmask order equal the table above, which
   it also finds in this README;
4. the identity of the Theorem at all 3375 index triples, in integer arithmetic (90 entries equal 4, the others 0);
5. Lemma 2 for k = 1, 2, 3: the rows of M_{P_k} are nonzero with pairwise disjoint supports;
6. Lemma 3: the exact comparisons for k = 1, …, 11, and 16(2k+1) > 27(k+1) for 3 ≤ k ≤ 1000 (proved above for all
   k ≥ 3).

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time on
the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 8 October 2026: the three papers below; the works citing Pratt (2023) or Björklund, Kaski, Koana and
Nederlof (2026) found through Semantic Scholar, OpenAlex and OpenCitations (read at least by keyword search of the
full text); and keyword searches on arXiv and the web for tripartitioning tensors and for P₂ described through the
perfect matchings of K₆. The smallest upper bound on R(P₂) found is 31.

- K. Pratt, arXiv:2311.02774v1: full text read. §1.2, item 4, states the bound 8^k/2 (see Background). No smaller
  value for any k is given.
- C. Flavi, J. Jelisiejew, M. Michałek, arXiv:2408.02754v2: §6 read. Proposition 6.18 gives Σ_{j=0}^{k} C(3k, 2j)
  (31 for k = 2) over algebraically closed fields of characteristic 0 (see Background).
- A. Björklund, P. Kaski, T. Koana, J. Nederlof, ICALP 2026: full text read. §1.5 cites the bound 2^{3n−1} (see
  Background). No value for a fixed n is given.

## Sources

- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1 (5 November 2023). <https://arxiv.org/abs/2311.02774v1>
- K. Pratt (2024). Same title. Proceedings of the 56th Annual ACM Symposium on Theory of Computing (STOC 2024),
  871–874. [doi:10.1145/3618260.3649620](https://doi.org/10.1145/3618260.3649620). Read: abstract and the comments
  after Corollary 1.12 (pp. 872–873).
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754 (v1 5 August 2024, v2
  29 August 2025; read: v2).
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. 53rd International Colloquium on Automata, Languages, and Programming
  (ICALP 2026), LIPIcs, paper 36. [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36).
  Full version: arXiv:2504.05772.

## Licence

The data file and this text are under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the
Apache License 2.0 ([LICENSE](../../LICENSE)).
