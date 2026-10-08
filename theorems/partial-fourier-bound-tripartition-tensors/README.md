# A partial Fourier bound for the rank of tripartitioning tensors

> **Provenance: own extension.** Base: C. Flavi, J. Jelisiejew and M. Michałek, *Symmetric powers: structure,
> smoothability, and applications*, arXiv:2408.02754v2, Proposition 6.18 (Proposition 6.17 in v1; IMRN 2025). They
> prove R(P_k) ≤ ½ 8^k − Σ_{i=k+1}^{⌊3k/2⌋} C(3k, 2i) = Σ_{j=0}^{k} C(3k, 2j) over algebraically closed fields of
> characteristic 0, by bounding the rank by the number of symmetric differences of two k-subsets of a 3k-set,
> starting from the group tensor of Z₂^{3k} with a substitution in the third factor. This is Corollary 1 below. The
> note goes beyond it as follows: the bound for every T_{a,b,c} (Theorem 1); every field of characteristic ≠ 2,
> with an explicit integer identity when |a − b| ≤ 1 (Theorem 2); the bound R(T_{1,1,c}) ≤ C(c+2, 2) + 1
> (Corollary 2); exactness of the bound within the family of decompositions of this form (Theorem 3, Corollary 3);
> and the statement that the gain over 8^d/2 is of lower order (Proposition 4). The literature checked (see
> [Literature checked](#literature-checked)) contains none of these; this is a statement about that search, not a
> claim of priority.

The construction keeps characters of the group {±1}^n in the first two factors and leaves the third factor free.
For P_d it gives the bound Σ_{k=0}^{d} C(3d, 2k) (4, 31, 247, 1981, …) of Flavi, Jelisiejew and Michałek, against
8^d/2 (4, 32, 256, 2048, …). For P_d, and whenever the first two sizes differ by at most 1, the bound is exact
within the family of decompositions of this form; for P_d it improves 8^d/2 only by a factor 1 − O((27/32)^d).

## Definitions

- **Tensors.** For integers a, b, c ≥ 0 with n = a + b + c ≥ 1, T_{a,b,c} = Σ x_A y_B z_C, the sum over all
  ordered partitions (A, B, C) of [n] = {1, …, n} with |A| = a, |B| = b, |C| = c; a tensor in
  F^(n choose a) ⊗ F^(n choose b) ⊗ F^(n choose c) whose coefficient at (S, T, U) is 1 if (S, T, U) is such a
  partition and 0 otherwise. P_d = T_{d,d,d} is the balanced tripartitioning tensor (Pratt's T_d,
  arXiv:2311.02774v1, Definition 1.4; the P_d of Björklund, Kaski, Koana and Nederlof, ICALP 2026). R_F denotes
  tensor rank over a field F.
- **Symmetric difference.** S ⊕ T = (S ∖ T) ∪ (T ∖ S). D_{a,b} = {S ⊕ T : S, T ⊆ [n], |S| = a, |T| = b}.
- **Sign vectors and characters.** For t ∈ {±1}^n (entries in F) and v ⊆ [n], χ_v(t) = Π_{i ∈ v} t_i, and
  u_t^{(m)} ∈ F^(n choose m) is the vector with entries u_t^{(m)}(S) = χ_S(t) (|S| = m). Write u_t for u_t^{(a)} in the
  first factor and for u_t^{(b)} in the second.
- **The family.** A decomposition *of character type* (in the first two factors) is an identity
  T_{a,b,c} = Σ_{l=1}^{m} u_{t_l} ⊗ u_{t_l} ⊗ W_l with sign vectors t_1, …, t_m ∈ {±1}^n (repetitions allowed) and
  arbitrary vectors W_l ∈ F^(n choose c). Scalar factors are absorbed into W_l. Its *length* is m.
- **Targets.** For v ∈ D_{a,b}, τ_v ∈ F^(n choose c) is the unit vector e_{[n]∖v} if |v| = a + b, and 0 otherwise.

## Statement

**Theorem 1.** For every field F of characteristic ≠ 2 and all a, b, c ≥ 0 with n ≥ 1, T_{a,b,c} has a
decomposition of character type of length |D_{a,b}|. Hence R_F(T_{a,b,c}) ≤ |D_{a,b}|, where

    |D_{a,b}| = Σ_{j=0}^{min(a,b)} C(n, a + b − 2j).

**Theorem 2 (explicit form for |a − b| ≤ 1).** Let |a − b| ≤ 1, r = min(a + b, n − 1), and Γ₀ the set of sign
vectors t with t_n = +1 and at most r entries −1. Then |Γ₀| = |D_{a,b}|, and there are integer vectors W̃_t
(t ∈ Γ₀), given by the formula in the proof, with

    2^r · T_{a,b,c} = Σ_{t ∈ Γ₀} u_t ⊗ u_t ⊗ W̃_t      over ℤ.

So the decomposition of Theorem 1 holds with W_t = 2^{−r} W̃_t over every commutative ring in which 2 is invertible.

**Corollary 1 (Flavi–Jelisiejew–Michałek, Proposition 6.18, over algebraically closed fields of characteristic 0).**
R_F(P_d) ≤ Σ_{k=0}^{d} C(3d, 2k) = Σ_{i=0}^{2d} C(3d−1, i) for every d ≥ 1 and every field F of characteristic ≠ 2.
The values for d = 1, …, 6 are 4, 31, 247, 1981, 15914, 127858.

**Corollary 2.** R_F(T_{1,1,c}) ≤ C(c+2, 2) + 1 for every c ≥ 0 and every field F of characteristic ≠ 2.

**Remark 1 (another description of T_{1,1,c}).** With n = c + 2, renaming each coordinate C of the third factor by
its complement [n] ∖ C turns T_{1,1,c} into Σ_{i ≠ j} x_i y_j z_{{i,j}} = Σ_{i<j} z_{ij} (x_i y_j + x_j y_i), the
trilinear form xᵀ Z y of the product of a symmetric n × n matrix Z = (z_{ij}) with zero diagonal and a vector y.
*Proof.* ({i}, {j}, C) is an ordered partition of [n] exactly when i ≠ j and C = [n] ∖ {i, j}. ∎

**Theorem 3 (exact within the family).** Let |a − b| ≤ 1 and F any field. Every decomposition of character type
of T_{a,b,c} has length at least |D_{a,b}|. With Theorem 1: if char F ≠ 2, the shortest decomposition of
character type has length exactly |D_{a,b}|.

**Corollary 3 (other pairs of factors).** Let i ≠ j be two of the three factors, with sizes a_i, a_j, and call a
decomposition of character type in factors i, j one in which factors i and j carry u_t^{(a_i)} and u_t^{(a_j)} for
the same sign vector t and the remaining factor is arbitrary. If char F ≠ 2, T_{a,b,c} has one of length
|D_{a_i,a_j}|; if |a_i − a_j| ≤ 1, none is shorter (any F). For P_d every pair gives Σ_{k=0}^{d} C(3d, 2k).

**Proposition 4 (the gain over 8^d/2 is of lower order).** Let D_d = |D_{d,d}|. For every d ≥ 1,

    8^d/2 − (27/4)^d  ≤  D_d  ≤  8^d/2,

with equality on the right only for d = 1. Consequently D_d / (8^d/2) → 1 (the relative gain is at most
2 · (27/32)^d), lim D_d^{1/d} = 8, D_d > Λ^d for every Λ < 8 and all sufficiently large d, and

    lim_{d→∞} log D_d / log C(3d, d) = log 8 / log(27/4) = 1/H(1/3),   H(1/3) = log₂ 3 − 2/3,

the same limit as for 8^d/2. By Theorem 3 this holds for every decomposition of P_d of character type (in any two
factors): such decompositions have length at least D_d, so they never give R(P_d) ≤ Λ^d with Λ < 8 for all
large d. In the notation of Björklund, Kaski, Koana and Nederlof (see [Background](#background)), the bounds
R(P_d) ≤ D_d give σ(P_ℕ) ≤ H(1/3)^{−1}, and every sequence of decompositions of P_d of character type (in any
two factors), of lengths L_d, satisfies lim inf_{d→∞} log L_d / log C(3d, d) ≥ H(1/3)^{−1}.

## Proof

**Lemma 1 (D_{a,b}).** v ∈ D_{a,b} if and only if |v| ≡ a + b (mod 2) and |a − b| ≤ |v| ≤ a + b. Hence |D_{a,b}| is
the sum above. Moreover |S ⊕ T| = a + b if and only if S ∩ T = ∅.

*Proof.* |S ⊕ T| = a + b − 2|S ∩ T| with 0 ≤ |S ∩ T| ≤ min(a, b): this gives the parity, the two bounds and the last
sentence. Conversely let |v| = a + b − 2j with 0 ≤ j ≤ min(a, b). Since n − |v| = c + 2j ≥ j, there is a j-set
I ⊆ [n] ∖ v; split v into V₁ and V₂ with |V₁| = a − j and |V₂| = b − j, and put S = V₁ ∪ I, T = V₂ ∪ I. Then
|S| = a, |T| = b and S ⊕ T = v. The sizes a + b − 2j are distinct for different j, so |D_{a,b}| = Σ_j C(n, a+b−2j). ∎

**Lemma 2 (characters).** (i) u_t(S) u_t(T) = χ_{S⊕T}(t). (ii) Σ_{t ∈ {±1}^n} χ_v(t) χ_w(t) = 2^n [v = w].

*Proof.* (i) χ_S(t) χ_T(t) = Π_{i ∈ S∩T} t_i² Π_{i ∈ S⊕T} t_i and t_i² = 1. (ii) χ_v χ_w = χ_{v⊕w} by (i). If
v ⊕ w ≠ ∅, pick i in it; flipping t_i is a bijection of {±1}^n that changes the sign of χ_{v⊕w}(t), so the sum is
0. If v = w every term is 1. ∎

**Lemma 3 (reduction).** For sign vectors t_1, …, t_m and vectors W_1, …, W_m,

    T_{a,b,c} = Σ_l u_{t_l} ⊗ u_{t_l} ⊗ W_l   ⟺   Σ_l χ_v(t_l) W_l = τ_v for every v ∈ D_{a,b}.

*Proof.* By Lemma 2(i), the (S, T)-slice of the right-hand sum, a vector in F^(n choose c), is
Σ_l χ_{S⊕T}(t_l) W_l. The (S, T)-slice of T_{a,b,c} is τ_{S⊕T}: if S ∩ T ≠ ∅, both are 0 (Lemma 1: |S ⊕ T| < a + b);
if S ∩ T = ∅, S ⊕ T = S ∪ T, and the slice is the unit vector at the only U with (S, T, U) a partition,
U = [n] ∖ (S ∪ T). Every v ∈ D_{a,b} is some S ⊕ T, so the slices agree for all (S, T) exactly when the right-hand
condition holds. ∎

**Proof of Theorem 1.** Let H be the matrix (χ_v(t)) with rows v ⊆ [n] and columns t ∈ {±1}^n. By Lemma 2(ii),
H Hᵀ = 2^n I, which is invertible when char F ≠ 2, so the rows of H are linearly independent over F. The rows with
v ∈ D_{a,b} have rank |D_{a,b}|, so some |D_{a,b}| columns t_1, …, t_m form an invertible matrix
X = (χ_v(t_l))_{v ∈ D_{a,b}, l}. Let W_l be the solution of the linear system Σ_l χ_v(t_l) W_l = τ_v (v ∈ D_{a,b}),
coordinate by coordinate. Lemma 3 gives the decomposition, of length m = |D_{a,b}|. ∎

(This is the argument of Flavi, Jelisiejew and Michałek for P_k, the group tensor of Z₂^n kept in two factors with
a substitution in the third, written out for all (a, b, c) and every characteristic ≠ 2.)

**Lemma 4.** Let |a − b| ≤ 1 and r = min(a + b, n − 1). Then v ↦ v′ = v ∖ {n} is a bijection from D_{a,b} onto
F_r = {w ⊆ [n−1] : |w| ≤ r}.

*Proof.* All v ∈ D_{a,b} have |v| ≡ a + b, so two of them that differ only in n cannot both lie in D_{a,b}: the
map is injective. Its values lie in F_r (|v′| ≤ |v| ≤ a + b and v′ ⊆ [n−1]). Given w ∈ F_r, put v = w if
|w| ≡ a + b and v = w ∪ {n} otherwise; in the second case |w| ≤ a + b − 1, so |v| ≤ a + b. Then |v| ≡ a + b,
|v| ≤ a + b, and |v| ≥ |a − b| holds trivially when a = b, and because |v| is odd when |a − b| = 1. By Lemma 1,
v ∈ D_{a,b}, and v′ = w. ∎

**Proof of Theorem 2.** Encode t ∈ Γ₀ by y = {i : t_i = −1} ∈ F_r. For v ∈ D_{a,b}, χ_v(t) = (−1)^{|v′ ∩ y|} because
t_n = +1, so |Γ₀| = |F_r| = |D_{a,b}| by Lemma 4, and the system of Lemma 3 is Σ_{y ∈ F_r} Y_{w,y} W_y = τ′_w
(w ∈ F_r), with Y_{w,y} = (−1)^{|w ∩ y|} and τ′_w = τ_v for the v with v′ = w. Expanding
(−1)^{|w∩y|} = Π_{i ∈ w∩y} (1 − 2) = Σ_{z ⊆ w∩y} (−2)^{|z|} gives Y = Z Δ Zᵀ with Z_{w,z} = [z ⊆ w] and
Δ = diag((−2)^{|z|}), all indexed by F_r (z ⊆ w ∈ F_r implies z ∈ F_r). Z is unitriangular for any order by size,
and by Möbius inversion on subsets (the interval between z ⊆ w lies in F_r) Z⁻¹_{z,w} = (−1)^{|z|−|w|} [w ⊆ z].
Hence the unique solution is

    W_y = Σ_{z ∈ F_r, z ⊇ y} (−1)^{|z|−|y|} (−2)^{−|z|} Σ_{w ⊆ z} (−1)^{|z|−|w|} τ′_w .

Every |z| ≤ r, so W̃_y = 2^r W_y has integer entries. With these W_y, Lemma 3 holds over ℚ, and multiplying by 2^r
gives the identity over ℤ (all entries are integers; an identity of integer tensors holds over ℤ if it holds
over ℚ). Its image in a commutative ring with 2 invertible, divided by 2^r, is the decomposition. ∎

**Proof of Corollaries 1 and 2.** For a = b = d, n = 3d, Lemma 1 gives
Σ_{j=0}^{d} C(3d, 2d − 2j) = Σ_{k=0}^{d} C(3d, 2k), and Lemma 4 (r = 2d) gives Σ_{i=0}^{2d} C(3d−1, i). For
a = b = 1, n = c + 2: C(c+2, 2) + C(c+2, 0). ∎

**Proof of Theorem 3.** Let T_{a,b,c} = Σ_{l=1}^{m} u_{t_l} ⊗ u_{t_l} ⊗ W_l. For v ∈ D_{a,b} let
x_v = (χ_v(t_1), …, χ_v(t_m)) ∈ F^m. It suffices to show that the x_v (v ∈ D_{a,b}) are linearly independent,
since then |D_{a,b}| ≤ m. Suppose Σ_{v ∈ D_{a,b}} α_v x_v = 0.

(1) *Top coefficients vanish.* Multiply the l-th coordinate by W_l and sum over l: by Lemma 3,
0 = Σ_v α_v Σ_l χ_v(t_l) W_l = Σ_v α_v τ_v = Σ_{|v| = a+b} α_v e_{[n]∖v}. The vectors e_{[n]∖v} are distinct unit
vectors, so α_v = 0 whenever |v| = a + b. This holds for every relation among the x_v.

(2) *All coefficients vanish.* Suppose not, and pick v* with α_{v*} ≠ 0 and |v*| largest; by (1), s = a + b − |v*|
is positive, and it is even. As n − |v*| ≥ s, there is an s-set w ⊆ [n] ∖ v*. Multiplying the relation coordinatewise
by (χ_w(t_l))_l gives Σ_v α_v x_{v⊕w} = 0 (Lemma 2(i)). Each v ⊕ w with α_v ≠ 0 lies in D_{a,b}: |v ⊕ w| ≡ a + b,
|v ⊕ w| ≤ |v| + s ≤ a + b, and |v ⊕ w| ≥ |a − b| is automatic when a = b and follows from oddness when
|a − b| = 1 (Lemma 1). The map v ↦ v ⊕ w is injective, so this is a relation among the x_v with the coefficient
α_{v*} ≠ 0 at v* ⊕ w = v* ∪ w, which has size a + b. This contradicts (1). ∎

**Proof of Corollary 3.** The definition of T_{a,b,c} is symmetric under permuting the three factors together with
the three sizes, so the statement for factors i, j is Theorem 1 and Theorem 3 for the permuted tensor. For P_d all
sizes equal d. ∎

**Proof of Proposition 4.** The even-size subsets of a nonempty set are half of all subsets, so
Σ_{k ≥ 0} C(3d, 2k) = 2^{3d−1} = 8^d/2, and

    8^d/2 − D_d = Σ_{2d < 2k ≤ 3d} C(3d, 2k) ≤ Σ_{i > 2d} C(3d, i) = Σ_{i < d} C(3d, i).

The first sum is empty for d = 1 and positive for d ≥ 2, since then 2d + 2 ≤ 3d.
For the upper bound use the standard estimate Σ_{i ≤ m/3} C(m, i) ≤ 2^{m H(1/3)}: with p = 1/3,
1 = Σ_i C(m, i) p^i (1−p)^{m−i} ≥ Σ_{i ≤ pm} C(m, i) (1−p)^m (p/(1−p))^{pm} because p/(1−p) ≤ 1; for m = 3d,
(1−p)^m (p/(1−p))^{pm} = (2/3)^{2d} (1/3)^d = 4^d/27^d. So Σ_{i ≤ d} C(3d, i) ≤ (27/4)^d, which proves the
displayed inequality. Dividing by 8^d/2 gives 1 − 2(27/32)^d ≤ D_d/(8^d/2) ≤ 1, hence the limit 1 and
D_d^{1/d} → 8. For Λ < 8, D_d / Λ^d ≥ (8/Λ)^d (1/2 − (27/32)^d) → ∞.

For the last limit: C(3d, d) ≤ Σ_{i≤d} C(3d, i) ≤ (27/4)^d, and C(3d, d) 4^d/27^d is the largest term of
Σ_i C(3d, i) (1/3)^i (2/3)^{3d−i} = 1 (the ratio of consecutive terms, (3d − i)/(2(i + 1)), is ≥ 1 exactly for
i ≤ d − 1), so C(3d, d) ≥ (27/4)^d/(3d + 1). Hence log C(3d, d) = d log(27/4) + O(log d), while
log D_d = d log 8 + O(1) by the first part, and the ratio tends to log 8/log(27/4). Finally
log₂(27/4) = 3 log₂ 3 − 2 = 3 H(1/3) and log₂ 8 = 3.

The sentence on decompositions of character type follows from Theorem 3 and Corollary 3: their lengths are at
least D_d, and D_d > Λ^d for all large d. For the last sentence write s_d = C(3d, d) and
e_d = log D_d / log s_d, so that D_d = s_d^{e_d} and e_d → H(1/3)^{−1}. Then R(P_d) ≤ s_d^{H(1/3)^{−1} + o(1)},
which gives σ(P_ℕ) ≤ H(1/3)^{−1} by the definition of σ. And L_d ≥ D_d (Theorem 3, Corollary 3) gives
log L_d / log s_d ≥ e_d → H(1/3)^{−1}. ∎

## Background

These statements are cited, not proved here.

- Flavi, Jelisiejew and Michałek (arXiv:2408.02754v2, Proposition 6.18, p. 31; Proposition 6.17 in v1; IMRN 2025,
  rnaf277): "The rank of the tensor T_N is at most ½ 8^k − Σ_{i=k+1}^{⌊N/2⌋} C(N, 2i)", with N = 3k and T_N Pratt's
  tensor T_k (§6, p. 31). Proof (p. 32): T_N is a subtensor of a power of the group tensor of Z₂, and "by the
  substitution method the rank of T_N is bounded by the number of sets obtained as the symmetric difference of two
  subsets of cardinality k of a set of cardinality N". Standing assumption (§2, p. 7): an algebraically closed field of
  characteristic zero. Since Σ_{i ≥ 0} C(3k, 2i) = 2^{3k−1}, their bound equals Σ_{j=0}^{k} C(3k, 2j).
- Pratt (arXiv:2311.02774v1, §1.2, p. 4, item 4 of the numbered comments after Corollary 1.12) states the upper bound
  R(T_k) ≤ 8^k/2 for every field with char(F) ≠ 2, with a construction through a function from k-sets into an
  abelian group (see the note [pratt-remark-4-construction-even-k](../pratt-remark-4-construction-even-k/), which
  proves the bound).
- For c = 1, T_{1,1,1} = P₁ = Σ_{σ ∈ S₃} x_{σ(1)} y_{σ(2)} z_{σ(3)} is the 3 × 3 permanent, read as a trilinear form in
  the three rows. Its tensor rank is 4 over fields of characteristic 0 (Ilten and Teitler, arXiv:1503.00822v2,
  Remark 2.2, p. 4; Canad. Math. Bull. 59 (2016)), and its border rank is 4 over fields of characteristic 0 (lower
  bound ≥ 4 by Derksen and Makam 2019; the value then follows with Fischer's formula; as reported by Han and Song,
  arXiv:2608.09708v2, pp. 2–3). In the literature checked this is the only previously known value of the rank of
  T_{1,1,c} with c ≥ 1.
- Ye and Lim (arXiv:1601.00292v2, Theorem 14.1, p. 27; Found. Comput. Math. 18 (2018)) prove that over ℂ the
  bilinear map (S, v) ↦ Sv on symmetric n × n matrices S, diagonal included, has rank n(n + 1)/2. They do not
  treat the case of zero diagonal, which is T_{1,1,c} with n = c + 2 (Remark 1). Their theorem is cited for context
  only.
- Björklund, Kaski, Koana and Nederlof (ICALP 2026, §1.1, pp. 36:3–36:4) define the exponent σ(P_ℕ) = inf{σ > 0 :
  R(P_n) ≤ s_n^{σ + o(1)}} with s_n = C(3n, n), state 1 ≤ σ(P_ℕ) ≤ H(1/3)^{−1} ≤ 1.0891, and ask whether
  σ(P_ℕ) < H(1/3)^{−1}. Their main application (Theorem 1.3, p. 36:4) gives arithmetic circuits for the permanent
  that are exponentially smaller than 2^n under the assumption σ(P_ℕ) < H(1/3)^{−1}.

## Scope

- Theorems 1 and 2 and Corollaries 1 and 2: every field of characteristic ≠ 2 (Theorem 2: every commutative ring
  with 2 invertible). No claim in characteristic 2.
- Theorem 3 and Corollary 3 concern only decompositions of character type as defined above (the same sign vector
  t in two factors, characters u_t^{(m)}(S) = Π_{i ∈ S} t_i). For |a − b| ≥ 2 the note claims no lower bound on
  their length. Nothing is claimed about the rank of T_{a,b,c} beyond the upper bounds; in particular the bounds
  are not claimed to equal the rank.
- Proposition 4 is a statement about the numbers D_d.

## Verification

```bash
python theorems/partial-fourier-bound-tripartition-tensors/verify.py
```

Offline, standard library only, about ten seconds. In order, the script checks:

1. Lemma 1 (D_{a,b} computed by brute force equals the description, and its size) for all 285 triples
   (a, b, c) ≥ 0 with 1 ≤ n ≤ 10, and Lemma 4 for those with |a − b| ≤ 1;
2. the values of Corollaries 1 and 2: Σ_k C(3d, 2k) = Σ_{i≤2d} C(3d−1, i) for d ≤ 12, the brute-force sizes 4, 31,
   247, 1981 for d ≤ 4, and |D_{1,1}| = 1 + C(c+2, 2) for c ≤ 20;
3. Theorem 1, constructively, for all 119 triples (a, b, c) ≥ 0 with 1 ≤ n ≤ 7, for (3, 3, 3) and for (1, 1, c),
   6 ≤ c ≤ 10 (125 tensors): it builds a decomposition of length |D_{a,b}| and checks it exactly. For |a − b| ≤ 1
   this is the explicit decomposition of Theorem 2, with the formula above, and the check is the integer identity
   (the W̃_t must be integers). For |a − b| ≥ 2 it takes the first |D_{a,b}| sign vectors with t_n = +1, in order of
   the number of entries −1, that are independent (as in the proof of Theorem 1), solves the system over ℚ, and
   checks the identity over ℚ. Every tensor except (3, 3, 3) is checked entry by entry (163 811 entries in all);
   every tensor, (3, 3, 3) included, is also checked through the three facts of the proof: Lemma 2(i) for all
   S, T, t used, the system of Lemma 3 for every v ∈ D_{a,b}, and that τ_{S⊕T} is the (S, T)-slice of T_{a,b,c};
4. Theorem 3 on six small tensors, (1,1,1), (1,1,2), (2,1,1), (1,1,3), (2,1,2) and (2,2,2), exhaustively: no set
   of |D_{a,b}| − 1 sign vectors with t_n = +1 admits weights, over 𝔽₃ and over 𝔽_{2³¹−1}. (A term with −t equals a
   term with t up to sign, repeated sign vectors can be merged, and a set that admits weights keeps admitting them
   when it grows, so this covers every shorter decomposition of character type over these fields.) The selected
   |D_{a,b}| vectors do admit weights;
5. Proposition 4 in exact integer arithmetic for 1 ≤ d ≤ 200: both bounds on D_d (strict on the right for
   d ≥ 2), the tail identity, Σ_{i≤d} C(3d, i) ≤ (27/4)^d, and (27/4)^d/(3d+1) ≤ C(3d, d).

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time
on the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 8 October 2026: the papers below; the works citing Pratt (2023) or Björklund, Kaski, Koana and Nederlof
(2026) found through Semantic Scholar, OpenAlex and OpenCitations (read at least by keyword search of the full
text); keyword searches on arXiv and the web for tripartitioning tensors.

- C. Flavi, J. Jelisiejew, M. Michałek, arXiv:2408.02754v2 (§6 read): the balanced case, Corollary 1, over
  algebraically closed fields of characteristic 0 (see Background). No unbalanced case, no bound for T_{1,1,c}, no
  optimality statement.
- For T_{1,1,c}, also searched under the descriptions of Remark 1 and as the degree-1 × degree-1 → degree-2
  multiplication in K[x_1, …, x_n]/(x_1², …, x_n²): K. Ye and L.-H. Lim (2018), §§14–16 (see Background), and the
  works citing it. No source states the value of R(T_{1,1,c}) for any c ≥ 2, or a bound stated for T_{1,1,c}
  itself; the value for c = 1 is in Background.
- K. Pratt, arXiv:2311.02774v1 (full text): the bound 8^k/2 and its construction through a group (§1.2, item 4).
- A. Björklund, P. Kaski, T. Koana, J. Nederlof, ICALP 2026 (full text): §1.1 (the exponent σ and its bounds), §1.5
  (Pratt's bound 2^{3n−1}).

## Sources

- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754 (v1 5 August 2024, v2
  29 August 2025; read: v2). Base of this note: Proposition 6.18.
- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1. <https://arxiv.org/abs/2311.02774v1>
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36). Full version: arXiv:2504.05772.
- K. Ye, L.-H. Lim (2018). *Fast Structured Matrix Computations: Tensor Rank and Cohn–Umans Method*. Foundations of
  Computational Mathematics 18(1), 45–95. [doi:10.1007/s10208-016-9332-x](https://doi.org/10.1007/s10208-016-9332-x);
  arXiv:1601.00292 (read: v2). Theorem 14.1 (v2, p. 27), cited for context.
- N. Ilten, Z. Teitler (2016). *Product Ranks of the 3 × 3 Determinant and Permanent*. Canadian Mathematical
  Bulletin 59(2), 311–319. [doi:10.4153/CMB-2015-076-1](https://doi.org/10.4153/CMB-2015-076-1); arXiv:1503.00822
  (read: v2). Remark 2.2 (v2, p. 4).
- J. I. Han, J. Song (2026). *The rank of the 5×5 permanent tensor is sixteen*. arXiv:2608.09708v2, pp. 2–3 (report
  of the rank and border rank of the 3 × 3 permanent over fields of characteristic 0, citing Derksen and Makam
  2019).

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
