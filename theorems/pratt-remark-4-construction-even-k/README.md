# The group construction for R(T_k) ≤ 2^{3k−1} in Pratt's arXiv:2311.02774v1: the printed map and a corrected one

> **Provenance: own extension.** Base: K. Pratt, *A stronger connection between the asymptotic rank conjecture and
> the set cover conjecture*, arXiv:2311.02774v1 (the only arXiv version), §1.2, item 4 of the numbered comments
> after Corollary 1.12. That item states the bound R(T_k) ≤ 8^k/2 for fields of characteristic ≠ 2 and sketches a
> construction for it. The version of the paper in the STOC 2024 proceedings does not contain this item (see
> [Background](#background)). This note goes beyond the base as follows: it determines, for each of four readings
> of the printed map (R1–R4 below), for which k it has the required property (exactly the odd k under R1, where the
> element 1 has no coordinate and e_1 is read as 0; no k under R2–R4), describes and counts the false positives under
> R1 and exhibits false positives under R2, and proves that the map f(S) = 1_{S∖{1}} has the property for every k,
> so the stated bound holds for every k. None of the sources read discusses the printed construction.

## The printed text

From arXiv:2311.02774v1, §1.2, item 4 after Corollary 1.12 (p. 4), with the symbols retyped from the PDF text.
The item begins with the upper bound R(T_k) ≤ 8^k/2 for fields with char(F) ≠ 2 and continues:

> […] Let G be an abelian group. Suppose that there is a function f : ([3k] choose k) → G and x ∈ G such that
> f(S) + f(T) + f(U) = x if and only if S, T, U are disjoint. We could then obtain the upper bound R(T_k) ≤ |G| by
> zeroing-out and relabeling variables in the tensor Σ_{a,b,c ∈ G, a+b+c = x} X_a Y_b Z_c, which has rank |G| when
> char(F) ≠ 2. The most obvious way to instantiate this idea is to take G = Z_2^{3k}, let f be the indicator vector of S,
> and let x be the all-ones vector. But we can do a little better by taking G = Z_2^{3k−1}, letting f(S) be the the
> indicator vector Σ_{s∈S} e_s if 1 ∈ S, and otherwise f(S) = 1^{3k−1} + Σ_{s≠1∈S} e_i, and letting x be the
> all-ones vector.

Here T_k = Σ x_S y_T z_U over S, T, U ∈ ([3k] choose k) with S ∪ T ∪ U = [3k] (Definition 1.4). It is the tensor
P_k of Björklund, Kaski, Koana and Nederlof (ICALP 2026) and of the other notes in this folder; this note keeps
Pratt's name T_k.

## Definitions

- **Triples.** S, T, U range over the k-subsets of [3k] = {1, …, 3k}; "disjoint" means pairwise disjoint. Three
  pairwise disjoint k-subsets of [3k] form an ordered partition of [3k], and conversely.
- **Valid maps.** For G = Z_2^m, a map f from k-subsets to G and x ∈ G, a *hit* is an ordered triple (S, T, U)
  with f(S) + f(T) + f(U) = x. The pair (f, x) is *valid* if its hits are exactly the ordered partitions; a hit
  that is not a partition is a *false positive*.
- **Vectors.** 1_X ∈ Z_2^{3k} is the indicator vector of X ⊆ [3k], 1 = 1_{[3k]}, and for S, T, U we write
  v = 1_S + 1_T + 1_U. For an element m ∈ [3k], π_m : Z_2^{3k} → Z_2^{[3k]∖{m}} deletes coordinate m; the all-ones
  vector of Z_2^{[3k]∖{m}} (the 1^{3k−1} of the text) is also written 1.
- **Readings of the printed map.** G = Z_2^{3k−1} has one coordinate fewer than [3k] has elements, while the
  formula uses a symbol e_s for every s ∈ S, including s = 1 when 1 ∈ S. A reading must say which element m has no
  coordinate and what e_m stands for. The two values considered are e_m = 0 (the coordinate is dropped) and
  e_m = 1 (the image of e_m under Z_2^{3k} → Z_2^{3k}/⟨1⟩, identified with Z_2^{[3k]∖{m}} by the representatives with
  coordinate m equal to 0). For m ≠ 1 we take m = 3k; any other m ≠ 1 gives the same results after renaming the
  elements 2, …, 3k, because the formula singles out only the element 1. Renaming the coordinates of G (for example
  numbering them 1, …, 3k − 1) does not change validity. The subscript i in Σ_{s≠1∈S} e_i is read as s; in that
  case 1 ∉ S, so the sum is Σ_{s∈S} e_s. With w_S = Σ_{s∈S} e_s ∈ Z_2^{[3k]∖{m}}, the printed map is
  f(S) = w_S if 1 ∈ S and f(S) = 1 + w_S if 1 ∉ S, with x = 1:

  | Reading | element without a coordinate | e_m | f(S) for 1 ∈ S | f(S) for 1 ∉ S |
  |---|---|---|---|---|
  | R1 | m = 1 | 0 | π₁(1_S) | 1 + π₁(1_S) |
  | R2 | m = 3k | 0 | π_m(1_S) | 1 + π_m(1_S) |
  | R3 | m = 1 | 1 | 1 + π₁(1_S) | 1 + π₁(1_S) |
  | R4 | m = 3k | 1 | π_m(1_S) + [3k ∈ S]·1 | 1 + π_m(1_S) + [3k ∈ S]·1 |

  In R1 the element without a coordinate is the element 1, the one the formula singles out (it is excluded
  explicitly in the second case).
- **The deletion map.** f₀(S) = π₁(1_S) = 1_{S∖{1}} ∈ Z_2^{[3k]∖{1}}, with x = 1.

## Statement

**Theorem 1 (the principle, with an explicit decomposition).** Let G = Z_2^m, f any map from k-subsets to G and
x ∈ G. Over any field, with u_y(S) = (−1)^{y·f(S)} for y ∈ Z_2^m,

    Σ_{y ∈ Z_2^m} (−1)^{y·x} u_y ⊗ u_y ⊗ u_y = 2^m · H_f,   H_f[S, T, U] = [f(S) + f(T) + f(U) = x].

If (f, x) is valid, then H_f = T_k, so R_F(T_k) ≤ 2^m for every field F of characteristic ≠ 2.

**Theorem 2.** The first instantiation of the text (G = Z_2^{3k}, f(S) = 1_S, x = 1) is valid for every k ≥ 1.

**Theorem 3 (corrected map).** The deletion map (f₀, 1) on G = Z_2^{3k−1} is valid for every k ≥ 1. Hence
2^{3k−1} T_k = Σ_{y ∈ Z_2^{3k−1}} (−1)^{|y|} u_y ⊗ u_y ⊗ u_y with u_y(S) = (−1)^{|y ∩ (S∖{1})|}, and

    R_F(T_k) ≤ 2^{3k−1} = 8^k/2   for every k ≥ 1 and every field F of characteristic ≠ 2.

**Theorem 4 (the printed map).**

1. *R1* is valid exactly for odd k. For even k its false positives are exactly the ordered triples
   (A ∪ B, A ∪ C, B ∪ C) with A, B, C pairwise disjoint (k/2)-subsets of [3k]. There are
   (3k)! / ((k/2)!³ (3k/2)!) of them: 120 for k = 2 and 83 160 for k = 4. Each consists of three distinct sets, so
   as unordered triples {S, T, U} there are 20 and 13 860. For k = 2 an example is ({1,2}, {1,3}, {2,3}). For even
   k, the sum of Theorem 1 for R1 is therefore 2^{3k−1}(T_k + E_k), where E_k ≠ 0 is the 0/1 tensor of these
   triples, not 2^{3k−1} T_k.
2. *R2* is valid for no k ≥ 1. For even k every triple of item 1 is a false positive; for odd k every triple
   ({3k} ∪ A ∪ B, {3k} ∪ A ∪ C, {3k} ∪ B ∪ C) with A, B, C pairwise disjoint ((k−1)/2)-subsets of {2, …, 3k − 1}
   is a false positive.
3. *R3* and *R4* are valid for no k ≥ 1: no partition is a hit.

**Summary for arXiv:2311.02774v1, item 4.** The bound R(T_k) ≤ 8^k/2 for char(F) ≠ 2 (Theorem 3); the
principle that a valid map into G gives R(T_k) ≤ |G| (Theorem 1, in its explicit form for G = Z_2^m); and the
first instantiation with G = Z_2^{3k} (Theorem 2). The improved instantiation with G = Z_2^{3k−1}, as printed, is
valid for odd k under reading R1 and is not valid for even k under R1, nor for any k under R2, R3 and R4; the
deletion map f₀ has the stated property for every k.

## Background

These statements are cited, not proved here.

- The construction is printed in arXiv:2311.02774v1 (the only arXiv version), item 4 after Corollary 1.12. The
  version published in the STOC 2024 proceedings (doi:10.1145/3618260.3649620, pp. 871–874) does not contain this
  item: its comments after Corollary 1.12 are items (1)–(4) (pp. 872–873), of which (4) is item 5 of v1 (all
  results hold for any tensor with the same support as T_k). Its abstract speaks of "a known upper bound of 8^n on
  the tensor rank of T_n", where the abstract of v1 has ½ · 8^n.
- Björklund, Kaski, Koana and Nederlof (ICALP 2026, §1.5, p. 36:8) write: "Pratt also observes the upper bound
  R(P_n) ≤ 2^{3n−1} over any field F with char F ≠ 2." They cite the bound and do not reproduce the construction.
  The bound holds for every n ≥ 1 (Theorem 3).
- Flavi, Jelisiejew and Michałek (arXiv:2408.02754v2, Proposition 6.18, p. 31; Proposition 6.17 in v1; IMRN 2025)
  prove R(T_k) ≤ ½ 8^k − Σ_{i=k+1}^{⌊3k/2⌋} C(3k, 2i) under their standing assumption of an algebraically closed
  field of characteristic 0 (§2, p. 7), by a different construction. Over such fields the bound R(T_k) ≤ 2^{3k−1} also
  follows from theirs. They cite Pratt's bound (§6, p. 31) and do not discuss his construction. The note
  [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/) proves their bound
  over every field of characteristic ≠ 2.

## Proof

**Lemma 1.** For z ∈ Z_2^m, Σ_{y ∈ Z_2^m} (−1)^{y·z} = 2^m [z = 0].

*Proof.* If z = 0, every term is 1. Otherwise pick i with z_i = 1; adding e_i to y is a bijection of Z_2^m that
changes the sign of (−1)^{y·z}, so the terms cancel in pairs. ∎

**Proof of Theorem 1.** The (S, T, U) coefficient of the left side is
Σ_y (−1)^{y·x} (−1)^{y·f(S)} (−1)^{y·f(T)} (−1)^{y·f(U)} = Σ_y (−1)^{y·(x + f(S) + f(T) + f(U))}, which is
2^m [f(S) + f(T) + f(U) = x] by Lemma 1. If (f, x) is valid, H_f[S, T, U] = 1 exactly for the ordered partitions,
so H_f = T_k. In characteristic ≠ 2, 2^m is invertible and T_k is a sum of 2^m rank-one tensors. ∎

(This is the zeroing-out argument of the text written as a single identity; it does not need f to be injective,
and it uses only the upper bound on the rank of the group tensor.)

**Lemma 2 (parity and counting).** For k-subsets S, T, U of [3k] and v = 1_S + 1_T + 1_U:

1. |v| ≡ k (mod 2);
2. v = 1 if and only if (S, T, U) is an ordered partition;
3. v = 0 if and only if k is even and (S, T, U) = (A ∪ B, A ∪ C, B ∪ C) for pairwise disjoint (k/2)-sets A, B, C,
   namely A = S ∩ T, B = S ∩ U, C = T ∩ U.

*Proof.* (1) |v| ≡ |S| + |T| + |U| = 3k ≡ k. (2) If v = 1, every element lies in one or three of the sets; with
n₁ and n₃ elements of each kind, n₁ + n₃ = 3k and n₁ + 3n₃ = |S| + |T| + |U| = 3k, so n₃ = 0 and every element lies
in exactly one set. The converse is clear. (3) If v = 0, every element lies in zero or two of the sets, so
A = S ∩ T, B = S ∩ U, C = T ∩ U are pairwise disjoint and S = A ∪ B, T = A ∪ C, U = B ∪ C. Then
|A| + |B| = |A| + |C| = |B| + |C| = k, so |A| = |B| = |C| = k/2 and k is even. The converse is clear. ∎

**Proof of Theorem 2.** f(S) + f(T) + f(U) = v, and v = 1 exactly for the partitions (Lemma 2.2). ∎

**Proof of Theorem 3.** π₁ is a group homomorphism, so f₀(S) + f₀(T) + f₀(U) = π₁(v), and π₁(v) = π₁(1) if and only
if v ∈ {1, 1 + e₁}. The vector 1 + e₁ has weight 3k − 1 ≢ k (mod 2), so by Lemma 2.1 it is not of the form v.
Hence the hits are the triples with v = 1, which are the partitions by Lemma 2.2. The identity and the bound are
Theorem 1 with m = 3k − 1, x = 1 and y·x = |y|. ∎

**Proof of Theorem 4.** Let c be the number of the sets S, T, U that contain 1; then v₁ ≡ c (mod 2).

*R1.* f(S) = π₁(1_S) + [1 ∉ S]·1, so f(S) + f(T) + f(U) = π₁(v) + (3 − c)·1, and the equation
f(S) + f(T) + f(U) = 1 is π₁(v) = c·1 (coefficients mod 2). If c is odd, π₁(v) = 1 and v₁ = 1, so v = 1: a
partition (Lemma 2.2). If c is even, π₁(v) = 0 and v₁ = 0, so v = 0. Conversely, a partition has c = 1 and v = 1,
and v = 0 forces c even; both are hits. So the hits are the partitions together with the triples with v = 0. By
Lemma 2.3 there are no such triples for odd k, and for even k they are the triples (A ∪ B, A ∪ C, B ∪ C), which are
not partitions (S ∩ T = A ≠ ∅). The map (A, B, C) ↦ (A ∪ B, A ∪ C, B ∪ C) is injective (A = S ∩ T, B = S ∩ U,
C = T ∩ U), so their number is the number of ordered triples of pairwise disjoint (k/2)-subsets of [3k],
(3k)!/((k/2)!³ (3k/2)!); for k = 2 this is 720/6 = 120, for k = 4 it is 479 001 600/(8 · 720) = 83 160. The three
sets are distinct (S = T would give B = C, but B and C are disjoint and nonempty, and similarly for the other
pairs), and the six orderings of {S, T, U} correspond to the six orderings of (A, B, C), so the unordered count is
one sixth: 20 and 13 860. For k = 2, A = {1}, B = {2}, C = {3} give ({1,2}, {1,3}, {2,3}). The statement about the
sum of Theorem 1 is Theorem 1 itself.

*R2* (m = 3k, e_m = 0). f(S) = π_m(1_S) + [1 ∉ S]·1 and the sum is π_m(v) + (3 − c)·1. For even k, take a triple
of Lemma 2.3: v = 0, and c is even because every element lies in 0 or 2 of the sets, so the sum is 1 = x; it is
not a partition. For odd k, take the triples of item 2, which exist because 3(k − 1)/2 ≤ 3k − 2: the element 3k
lies in all three sets, every other element in 0 or 2, so v = e_m and π_m(v) = 0; the element 1 is in none (c = 0),
so the sum is 3·1 = 1 = x; it is not a partition.

*R3.* In both cases f(S) = 1 + π₁(1_S) (for 1 ∈ S, Σ_{s∈S} e_s = e₁ + π₁(1_S) = 1 + π₁(1_S)). For a partition the
sum is 3·1 + π₁(1) = 1 + 1 = 0 ≠ 1.

*R4.* Let q(w) = π_m(w) + w_m·1, a group homomorphism Z_2^{3k} → Z_2^{[3k]∖{m}}; then
f(S) = q(1_S) + [1 ∉ S]·1. For a partition c = 1 and v = 1, so the sum is q(1) + 2·1 = π_m(1) + 1 = 1 + 1 = 0 ≠ 1. ∎

## Scope

- The note concerns the construction as printed in arXiv:2311.02774v1, under the readings R1–R4 defined above,
  and makes no statement about other readings.
- The bound R(T_k) ≤ 2^{3k−1} is claimed for fields of characteristic ≠ 2. Nothing is claimed about the exact
  rank, and the note makes no claim about Björklund–Kaski–Koana–Nederlof beyond the quoted sentence and the truth
  of the bound it cites.
- The companion note [partial-fourier-bound-tripartition-tensors](../partial-fourier-bound-tripartition-tensors/)
  proves the smaller bound R(T_k) ≤ Σ_{j=0}^{k} C(3k, 2j) by a different construction; this note does not depend on
  it.

## Verification

```bash
python theorems/pratt-remark-4-construction-even-k/verify.py
```

Offline, standard library only, a few seconds. In order, the script checks:

1. for the first instantiation, the deletion map and R1–R4, and every 1 ≤ k ≤ 5, exhaustively: whether the map is
   injective, the number of hits (a set lookup for each of the C(3k,k)² ordered pairs (S, T), with multiplicities
   when the map is not injective), how many of the (3k)!/(k!)³ ordered partitions are hits, and the verdicts of
   Theorems 2–4 (first instantiation and deletion map valid; R1 valid exactly for odd k; R2 with false positives
   for every k; R3 and R4 with no partition among the hits);
2. for R1 and k = 2, 4: the false positives, listed by a loop over all ordered pairs with a dictionary lookup of
   the third set, are exactly the triples (A ∪ B, A ∪ C, B ∪ C); their numbers 120 and 83 160 (ordered) and 20 and
   13 860 (unordered, three distinct sets each); the example for k = 2;
3. for R2 and k = 1, …, 5: every witness triple of Theorem 4.2 is a false positive;
4. Lemma 1 for m = 2, 5, 8 (all z), and the identity of Theorem 1 entry by entry for all six maps and k = 1, 2;
   for the deletion map it is 2^{3k−1} T_k, for R1 and k = 2 the hits include the 120 false positives.

Each check prints one `[PASS]`/`[FAIL]` line with its coverage and an exact step count, and its wall-clock time
on the next line. The script ends with `ALL CHECKS PASSED` and exit code 0, or exits with code 1.

## Literature checked

Search of 8 October 2026: arXiv:2311.02774v1 and the STOC 2024 version (abstract and pp. 872–873); the works citing
Pratt (2023) or Björklund, Kaski, Koana and Nederlof (2026) found through Semantic Scholar, OpenAlex and
OpenCitations (read at least by keyword search of the full text), among them Flavi, Jelisiejew and Michałek
(arXiv:2408.02754v2) and Björklund, Kaski, Koana and Nederlof (ICALP 2026); and Crossref, OpenAlex and Semantic
Scholar for an erratum (none listed). None of them discusses the printed construction; Flavi, Jelisiejew and
Michałek and Björklund, Kaski, Koana and Nederlof cite the bound without the construction, and the other citing
works cite the paper for its algorithmic and conditional results.

## Sources

- K. Pratt (2023). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  arXiv:2311.02774v1 (5 November 2023). <https://arxiv.org/abs/2311.02774v1>. Base of this note: §1.2, item 4 of
  the comments after Corollary 1.12 (quoted above); Definition 1.4.
- K. Pratt (2024). *A stronger connection between the asymptotic rank conjecture and the set cover conjecture*.
  Proceedings of the 56th Annual ACM Symposium on Theory of Computing (STOC 2024), 871–874.
  [doi:10.1145/3618260.3649620](https://doi.org/10.1145/3618260.3649620). Read: abstract and pp. 872–873 (the
  comments after Corollary 1.12).
- A. Björklund, P. Kaski, T. Koana, J. Nederlof (2026). *Kronecker Scaling of Tensors with Applications to
  Arithmetic Circuits and Algorithms*. ICALP 2026, LIPIcs, paper 36.
  [doi:10.4230/LIPIcs.ICALP.2026.36](https://doi.org/10.4230/LIPIcs.ICALP.2026.36). §1.5 (quoted above).
- C. Flavi, J. Jelisiejew, M. Michałek (2025). *Symmetric powers: structure, smoothability, and applications*.
  International Mathematics Research Notices 2025, rnaf277.
  [doi:10.1093/imrn/rnaf277](https://doi.org/10.1093/imrn/rnaf277); arXiv:2408.02754 (read: v2, §6).

## Licence

This text is under CC BY 4.0 ([LICENSE-DATA](../../LICENSE-DATA)); `verify.py` is under the Apache License 2.0
([LICENSE](../../LICENSE)).
