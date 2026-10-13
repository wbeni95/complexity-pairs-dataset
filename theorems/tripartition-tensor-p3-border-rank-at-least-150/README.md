# The balanced tripartitioning tensor P₃ has border rank at least 150

> **Provenance: own result.** The bound is obtained with a Koszul–Young flattening, the method of Landsberg and
> Ottaviani; the method is credited, and its proof is written out in the public note
> [tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/) (Lemmas 1–4),
> which this note uses. The literature checked for this note (see [Literature checked](#literature-checked)) states no
> lower bound on the rank or border rank of P₃ above the flattening bound 84. This is a statement about that search,
> not a claim of priority.

## Definitions

**The tensor.** P₃ = T_{3,3,3} = Σ x_A y_B z_C, the sum over all ordered partitions (A, B, C) of [9] = {1, …, 9} into
three 3-sets (Pratt's T₃, Björklund–Kaski–Koana–Nederlof's P₃). Its three factors are F^84, with coordinate a
(a = 0, …, 83) the a-th 3-subset S_a of [9] in increasing order of Σ_{e ∈ S} 2^(e−1), as in the note
[tripartition-tensors-small-cases](../tripartition-tensors-small-cases/). Its coefficients are P₃[a][b][c] = 1 if
S_a, S_b, S_c are pairwise disjoint and 0 otherwise; 1 680 of them are 1.

**Rank, border rank, Koszul–Young flattening.** As in
[tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/): R_F is the
tensor rank over F; R̲_ℂ the border rank over ℂ (Euclidean limits); R̲_F, for any field F, the algebraic border rank
(Σ_{i ≤ r} u_i(ε) ⊗ v_i(ε) ⊗ w_i(ε) = ε^h T + ε^{h+1} T₁(ε) with polynomial entries); R̲ ≤ R. For a tensor T′ whose
first factor is F^{2p+1}, K_p(T′) is the matrix with rows (U, k) (|U| = p + 1) and columns (S, j) (|S| = p),

    K_p(T′)[(U, k), (S, j)] = sgn(i, S) · T′[i][j][k]   if U = S ∪ {i} with i ∉ S,   and 0 otherwise,

sgn(i, S) = (−1)^{|{s ∈ S : s < i}|}, and (Φ ⊗ 1 ⊗ 1)T has coefficients Σ_a Φ[i][a] T[a][j][k].

**The projection.** p = 4, so 2p + 1 = 9 and C(2p, p) = 70, and Φ is the following 9 × 84 integer matrix with entries
−1, 0, 1. It is printed by columns: the line for coordinate a gives the column Φ[·][a] = (Φ[0][a], …, Φ[8][a]).

<!-- PHI -->
```
 0  {1,2,3}   [ -1,  1,  1, -1,  0,  1, -1,  1,  1 ]
 1  {1,2,4}   [  0,  0, -1,  1, -1, -1,  0,  1,  1 ]
 2  {1,3,4}   [  1,  1,  0,  1, -1,  1, -1, -1, -1 ]
 3  {2,3,4}   [  0,  0,  0, -1, -1, -1,  0,  1, -1 ]
 4  {1,2,5}   [  0,  0, -1,  0,  1, -1,  0, -1,  1 ]
 5  {1,3,5}   [  0,  1,  0,  1,  1,  0, -1,  1,  0 ]
 6  {2,3,5}   [  0, -1,  0, -1,  1,  0,  1,  0,  0 ]
 7  {1,4,5}   [  1, -1,  1,  1, -1,  0, -1,  0,  1 ]
 8  {2,4,5}   [  1,  1,  0,  1,  1,  1,  0, -1,  1 ]
 9  {3,4,5}   [  0,  1,  1,  0,  1, -1, -1, -1,  1 ]
10  {1,2,6}   [  0,  1,  0,  1,  1, -1,  0, -1,  0 ]
11  {1,3,6}   [ -1,  1, -1,  1, -1,  0, -1,  1,  0 ]
12  {2,3,6}   [  1, -1,  0, -1, -1, -1,  1,  0,  0 ]
13  {1,4,6}   [ -1, -1,  0,  1, -1,  1,  1, -1,  1 ]
14  {2,4,6}   [ -1,  0,  1,  0,  0, -1, -1,  0,  0 ]
15  {3,4,6}   [  1,  0,  1,  1,  0,  0,  1,  0,  1 ]
16  {1,5,6}   [  1, -1,  1, -1, -1, -1,  0,  0,  0 ]
17  {2,5,6}   [  0, -1, -1,  0,  1,  1,  0, -1, -1 ]
18  {3,5,6}   [  1,  1,  1, -1, -1, -1,  1,  0,  0 ]
19  {4,5,6}   [ -1, -1,  0, -1,  0, -1, -1,  1,  1 ]
20  {1,2,7}   [ -1,  0, -1,  1,  1,  1,  0,  0,  1 ]
21  {1,3,7}   [  0, -1, -1,  1,  1,  1, -1,  1,  0 ]
22  {2,3,7}   [  1, -1,  0, -1, -1,  1, -1,  1, -1 ]
23  {1,4,7}   [  1,  1,  1,  1,  0,  0,  1,  0, -1 ]
24  {2,4,7}   [ -1, -1, -1, -1,  0,  1,  0, -1,  1 ]
25  {3,4,7}   [  0, -1,  1,  0, -1, -1,  0,  1,  0 ]
26  {1,5,7}   [  1,  1,  0,  0,  1, -1,  1, -1, -1 ]
27  {2,5,7}   [  1, -1,  0, -1,  1,  1,  1,  1,  1 ]
28  {3,5,7}   [  1,  1, -1,  0,  1, -1,  0,  1, -1 ]
29  {4,5,7}   [ -1, -1,  1,  0,  1,  1,  1,  1, -1 ]
30  {1,6,7}   [ -1, -1, -1,  0,  1,  0,  0,  0,  1 ]
31  {2,6,7}   [ -1,  1, -1,  0,  0, -1, -1,  1,  1 ]
32  {3,6,7}   [  1,  1, -1,  0,  1,  0,  1, -1,  1 ]
33  {4,6,7}   [  0,  0,  0,  1,  0,  0,  0, -1,  1 ]
34  {5,6,7}   [  0, -1, -1,  0, -1, -1,  0,  1,  1 ]
35  {1,2,8}   [  1,  0,  1, -1, -1,  0, -1,  0,  1 ]
36  {1,3,8}   [  0,  0,  1, -1,  1, -1, -1,  1, -1 ]
37  {2,3,8}   [ -1,  1, -1,  0,  0,  0,  1, -1, -1 ]
38  {1,4,8}   [  1,  1,  0,  0, -1,  1,  1,  0, -1 ]
39  {2,4,8}   [  1,  1,  1,  1,  1,  0,  1,  1,  1 ]
40  {3,4,8}   [  0, -1, -1, -1,  1,  0,  0,  1,  0 ]
41  {1,5,8}   [  1,  1,  1, -1,  0, -1,  0,  0, -1 ]
42  {2,5,8}   [  1,  1,  0, -1,  1, -1,  1, -1,  1 ]
43  {3,5,8}   [  1,  0,  0,  0, -1,  1,  1,  0,  0 ]
44  {4,5,8}   [  0,  1,  0,  0, -1, -1, -1, -1, -1 ]
45  {1,6,8}   [ -1,  1, -1, -1,  1,  1, -1,  0, -1 ]
46  {2,6,8}   [  1,  0,  1,  0,  0, -1,  0,  0,  0 ]
47  {3,6,8}   [  0, -1, -1,  0,  1, -1,  1,  0, -1 ]
48  {4,6,8}   [  1, -1,  1,  0,  1,  1,  1, -1, -1 ]
49  {5,6,8}   [  1, -1,  0,  1, -1, -1, -1, -1, -1 ]
50  {1,7,8}   [  0,  0, -1, -1,  1,  0,  1, -1, -1 ]
51  {2,7,8}   [  1,  1, -1,  0,  0,  1,  1,  0, -1 ]
52  {3,7,8}   [  1,  0,  1,  1,  1, -1, -1,  0, -1 ]
53  {4,7,8}   [  1,  1,  0,  1,  1,  1,  1,  1,  0 ]
54  {5,7,8}   [ -1,  0,  1,  1,  1,  1, -1,  0,  0 ]
55  {6,7,8}   [  1, -1,  0,  1,  1, -1, -1,  1, -1 ]
56  {1,2,9}   [  1, -1,  1, -1,  0, -1,  1,  1, -1 ]
57  {1,3,9}   [  0, -1,  0, -1,  0, -1, -1,  0, -1 ]
58  {2,3,9}   [  0,  0,  1, -1,  1, -1,  1,  0,  1 ]
59  {1,4,9}   [  1,  0, -1,  1,  0,  0, -1,  1,  0 ]
60  {2,4,9}   [ -1,  0,  1, -1, -1,  0,  1,  0, -1 ]
61  {3,4,9}   [  1,  1,  0, -1, -1,  0,  1,  0, -1 ]
62  {1,5,9}   [  0,  0, -1, -1, -1, -1, -1,  0,  1 ]
63  {2,5,9}   [  1,  0, -1,  1,  1,  0, -1, -1,  1 ]
64  {3,5,9}   [  0,  1,  1, -1,  1, -1,  1, -1,  1 ]
65  {4,5,9}   [  1,  1,  0, -1,  1,  0, -1, -1,  1 ]
66  {1,6,9}   [  1, -1,  1,  0,  0,  0,  0, -1,  0 ]
67  {2,6,9}   [ -1,  1,  0,  0,  1,  0, -1,  0,  1 ]
68  {3,6,9}   [  1, -1,  0,  1,  0, -1,  0,  0, -1 ]
69  {4,6,9}   [  1,  0,  0, -1, -1, -1, -1, -1,  1 ]
70  {5,6,9}   [  0, -1, -1,  1,  0, -1, -1,  0,  1 ]
71  {1,7,9}   [  1,  0, -1,  1, -1,  1,  0,  0,  1 ]
72  {2,7,9}   [ -1,  1, -1,  1,  0,  1, -1,  0,  1 ]
73  {3,7,9}   [ -1, -1,  1, -1,  1,  1,  0, -1, -1 ]
74  {4,7,9}   [  0, -1,  0,  1,  0,  1,  1,  1, -1 ]
75  {5,7,9}   [ -1, -1, -1,  0,  0,  0, -1,  1,  0 ]
76  {6,7,9}   [  1, -1, -1,  0, -1,  1, -1,  0,  0 ]
77  {1,8,9}   [  0,  1, -1,  0, -1,  1,  0, -1,  1 ]
78  {2,8,9}   [  0,  1,  0,  0,  1, -1,  1, -1,  0 ]
79  {3,8,9}   [ -1, -1,  1,  1,  1,  1,  0,  0,  1 ]
80  {4,8,9}   [ -1, -1,  1,  1,  0,  1,  1,  1, -1 ]
81  {5,8,9}   [ -1, -1, -1,  0, -1, -1,  0,  1, -1 ]
82  {6,8,9}   [ -1,  1, -1,  0, -1,  0,  0,  0,  0 ]
83  {7,8,9}   [  0,  1,  1, -1,  1, -1, -1,  0,  0 ]
```
<!-- PHI -->

Let M = K₄((Φ ⊗ 1 ⊗ 1)P₃), a 10 584 × 10 584 matrix with integer entries (C(9, 5) · 84 = C(9, 4) · 84 = 126 · 84 rows
and columns).

## Statement

**Theorem.**

1. R̲_ℂ(P₃) ≥ 150.
2. For every field F of characteristic 0, and for every field F whose characteristic is a prime q ≤ 31,
   R̲_F(P₃) ≥ 150 (algebraic definition), and hence R_F(P₃) ≥ 150.

The proof uses one computed fact: the rank of M modulo q is 10 498 for q = 2 and 10 500 for every
other prime q ≤ 31.

**Corollary (with the partial-Fourier note).** Over ℂ, and over every field of characteristic 0 or of prime
characteristic 3 ≤ q ≤ 31:  150 ≤ R̲(P₃) ≤ R(P₃) ≤ 247.

## Proof

The proof uses two lemmas of the public note
[tripartition-tensor-p2-border-rank-at-least-26](../tripartition-tensor-p2-border-rank-at-least-26/), both proved
there for every p ≥ 1, every tensor T ∈ F^{n₁} ⊗ F^{n₂} ⊗ F^{n₃} and every (2p+1) × n₁ matrix Φ:

- *Lemma 3 there (Koszul–Young bound; Landsberg–Ottaviani, arXiv:1112.6007v3, Theorem 2.1):*
  R̲_F(T) ≥ rank_F K_p((Φ ⊗ 1 ⊗ 1)T) / C(2p, p), for the algebraic definition over every field F and for the
  topological definition over F = ℂ.
- *Lemma 4 there:* for an integer matrix M and a prime q, rank_F(M) = rank_{𝔽_q}(M mod q) if F has characteristic q,
  and rank_F(M) = rank_ℚ(M) ≥ rank_{𝔽_q}(M mod q) if F has characteristic 0.

**Proof of the Theorem.** Apply Lemma 3 with T = P₃, p = 4 and the projection Φ above. Φ and P₃ have integer entries,
so the flattening K₄((Φ ⊗ 1 ⊗ 1)P₃) over any field F is the image of the integer matrix M under ℤ → F. `verify.py`
computes the rank of M modulo q by exact elimination over 𝔽_q: 10 498 for q = 2 and 10 500 for the
other primes q ≤ 31.

- Part 2, characteristic q ≤ 31: rank_F(M) = rank_{𝔽_q}(M mod q) ≥ 10 498 by Lemma 4.
- Part 2, characteristic 0, and Part 1 (ℂ has characteristic 0): rank_F(M) = rank_ℚ(M) ≥ rank_{𝔽_3}(M mod 3) = 10 500
  by Lemma 4.

In all cases rank(M) ≥ 10 498 > 10 430 = 149 · 70, so Lemma 3 gives R̲(P₃) ≥ 10 498/70 > 149, that is
R̲(P₃) ≥ 150. Finally R_F ≥ R̲_F. ∎

**Proof of the Corollary.** Corollary 1 of the public note
[partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/) gives
R_F(P₃) ≤ Σ_{k=0}^{3} C(9, 2k) = 1 + 36 + 126 + 84 = 247 for every field of characteristic ≠ 2 (Flavi, Jelisiejew and
Michałek, Proposition 6.18, over algebraically closed fields of characteristic 0), and R̲ ≤ R always. ∎

**Example (used as a self-test).** For the unit tensor ⟨84⟩ = Σ_{a} e_a ⊗ e_a ⊗ e_a and the projection Φ above, whose
columns are all nonzero modulo every prime (each has an entry ±1), rank K₄((Φ ⊗ 1 ⊗ 1)⟨84⟩) = 84 · 70 = 5 880 over every
field, by the Example of the P₂ note (the 84 blocks are disjoint, and each has rank 70 by Lemma 2 there). Lemma 3 then
gives exactly R̲(⟨84⟩) ≥ 84.

## Background

These statements are cited, not proved here.

- The only unconditional published lower bound on the rank of P_d found is the flattening bound R(P_d) ≥ C(3d, d),
  84 for d = 3 (Björklund, Kaski, Koana, Nederlof, arXiv:2504.05772v1, §1.1, footnote 3 and proof of Theorem 1.2,
  p. 13: "By flattening P_d into a matrix and observing a large identity submatrix, we have that R(P_d) ≥ C(3d, d)";
  Pratt, arXiv:2311.02774v1, §1.1: "if T is concise, then R(T) ≥ n", and Proposition 2.1: T_k is concise). The same
  flattening argument gives R̲(P₃) ≥ 84 (Lemma of the note [tripartition-tensors-small-cases](../tripartition-tensors-small-cases/)).
- Upper bounds: R(P₃) ≤ 256 = 8³/2 (Pratt, arXiv:2311.02774v1, §1.2, item 4; proved for every k in the note
  [pratt-remark-4-construction-even-k](../pratt-remark-4-construction-even-k/)) and R(P₃) ≤ 247 (Flavi, Jelisiejew,
  Michałek, Proposition 6.18, stated over algebraically closed fields of characteristic 0; over every field of
  characteristic ≠ 2 by Corollary 1 of the note
  [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/); see the Corollary).
- Lovitz (arXiv:2610.08504v1, Corollary 1.3) proves that for n × n × n tensors over ℂ the linear flattening method can
  give a nontrivial equation for border rank r (which certifies R̲ > r) only if r ≤ 2n − 2. For n = 84 this means that
  the linear flattening method in Lovitz's sense (the rank of L(T) divided by the largest rank of L on rank-one
  tensors), with Koszul or other linear maps L, cannot certify a lower bound on R̲_ℂ(P₃) above 2n − 1 = 167.

## Scope

- The note claims R̲(P₃) ≥ 150 over ℂ (topological definition) and over every field of characteristic 0 or of prime
  characteristic q ≤ 31 (algebraic definition). It makes no claim for other characteristics.
- It claims no value of the border rank or of the rank of P₃, and nothing about P_d for d ≥ 4.
- The computed ranks are the ranks of M for the projection Φ above; nothing is claimed about other projections or
  other values of p.

## Verification

```bash
python theorems/tripartition-tensor-p3-border-rank-at-least-150/verify.py            # about 15 minutes
python theorems/tripartition-tensor-p3-border-rank-at-least-150/verify.py --quick    # under a minute
```

Offline, standard library only, about 1 GB of memory. The full run checks every claim; `--quick` checks the
characteristic-0 claim (through the rank modulo 2, Lemma 4) and the characteristic-2 claim, and skips the odd primes
for the large matrices. In order, the script checks:

1. that the matrix Φ printed above (84 labelled columns) equals the one it uses, with entries −1, 0, 1 and an entry
   ±1 in every column;
2. its two rank routines (an exclusive-or basis over 𝔽₂, and an elimination over 𝔽_q on rows packed into integers):
   on 45 fixed integer matrices with planted ranks 0–8 both agree with Gaussian elimination modulo every prime
   q ≤ 31, and elimination modulo 2³¹ − 1 agrees with the exact rank over ℚ; diag(q, 1) has rank 2 over ℚ and 1
   modulo q;
3. its flattening code against the public P₂ note: with that note's projection, the 525 × 525 flattening of P₂ has rank
   502 modulo 2 and 504 modulo 3;
4. Lemma 2 of the P₂ note: a rank-one tensor gives rank exactly 70, modulo every prime q ≤ 31;
5. the Example: ⟨84⟩ gives 5 880, modulo every prime q ≤ 31;
6. two controls at the threshold: a fixed sum of 149 rank-one tensors with entries −1, 0, 1 gives rank 10 430 = 149 · 70
   (so the method does not certify 150 for it), and a fixed sum of 150 gives 10 500 = 150 · 70, modulo 2 and 3;
7. that P₃ has 1 680 nonzero coefficients and M is 10 584 × 10 584, and the rank of M: 10 498 modulo 2 (with both
   routines) and 10 500 modulo every odd prime q ≤ 31; each exceeds 10 430, so ⌈rank/70⌉ = 150.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count (row eliminations, entries
built), and its wall-clock time on the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits
with code 1.

## Literature checked

Search of 12 October 2026, in addition to the search of 8 October 2026 recorded in the P₂ note: the works citing Pratt
(2023/2024), Björklund–Kaski–Koana–Nederlof (2026) or Flavi–Jelisiejew–Michałek (2025) listed by Semantic Scholar and
OpenAlex; keyword searches on arXiv and the web for tripartitioning, partition and matching tensors, the asymptotic
rank conjecture together with set cover, and Koszul flattenings together with border rank. Read in full text (keyword
search of the whole text and reading of every passage on tensors): arXiv:2608.08328, 2607.25973v2, 2608.12224,
2601.05044, 2602.12762, 2605.21738v2, 2609.39062, 2602.11975, 2610.08504. No lower bound on the rank or border rank of
P₃ above 84 was found.
The other citing works listed there (arXiv:2404.06427, 2411.15789, 2411.02936v3, 2505.22410, 2507.11098v2,
2510.08185, 2510.08336), Björklund–Kaski (arXiv:2310.11926) and Björklund–Curticapean–Husfeldt–Kaski–Pratt
(arXiv:2404.04987) were checked by keyword search of the full text; they cite these papers for conditional or
algorithmic results and state no rank or border rank bound for the tensors of this note.

- Doležálek and Michałek (arXiv:2602.12762v1) introduce Kronecker–Koszul flattenings; in §6.3 they list matching
  tensors among the special tensors of interest and write "We did not extensively check all our equations on these
  examples". No statement about P₃.
- Alman and Li (arXiv:2605.21738v2, Remark 6.1) cite the upper bound of Flavi–Jelisiejew–Michałek for Pratt's balanced
  partition tensor; no lower bound.
- Lovitz (arXiv:2610.08504v1): the barrier quoted in Background; no statement about partition tensors.
- Alman–Li–Pratt (arXiv:2608.08328v1), Zamir (arXiv:2607.25973v2), Dhar et al. (arXiv:2608.12224v1), Nederlof
  (arXiv:2601.05044v1, §4.6), Koana–Kumabe (arXiv:2609.39062v1) and Brand et al. (arXiv:2602.11975v1) cite Pratt or
  Björklund–Kaski–Koana–Nederlof for the algorithmic consequences of the asymptotic rank conjecture; none states a
  rank or border rank bound for P₃.

## Sources

- J. M. Landsberg, G. Ottaviani (2015). *New lower bounds for the border rank of matrix multiplication*. Theory of
  Computing 11(1), 285–298. [doi:10.4086/toc.2015.v011a011](https://doi.org/10.4086/toc.2015.v011a011);
  arXiv:1112.6007. Credit for the Koszul flattening bound (Lemma 3 of the P₂ note).
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754 (read: v2, §6). Proposition 6.18:
  the upper bound 247.
- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36). Full version: arXiv:2504.05772.
- B. Lovitz (2026). *Explicit tensors beyond the linear flattening barrier*. arXiv:2610.08504v1.
- M. Doležálek, M. Michałek (2026). *Nonlinear methods for tensors: determinantal equations for secant varieties
  beyond cactus*. arXiv:2602.12762v1.
- J. Alman, B. Li (2026). *Asymptotic Rank Speedup Theorems, Revisited*. arXiv:2605.21738v2.

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
