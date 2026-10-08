# Term by term: how much of the ⟨2,4,5;32⟩ and ⟨3,3,6;40⟩ ℤ[1/2] schemes can be made 2-integral

> **Provenance: own extension.** Base: Moran, Schwartz and Yuan (2026), *Complex to Rational Fast Matrix
> Multiplication*, arXiv:2602.13171 (v1), Proposition 3 and §3.2. With their Proposition 3 as the tool, they state
> that the ⟨3,3,6,40⟩ ℤ[1/2] algorithm of Smirnov, and a ⟨2,4,5,32⟩ algorithm over ℤ[1/2] that they attribute to
> Hopcroft and Kerr, cannot be transformed into algorithms with integer coefficients. The note
> [no-integral-form-z-half-schemes](../no-integral-form-z-half-schemes/) proves this statement for the two pinned
> scheme files used here, and explains why it is not established that the base concerns these files (that note is
> labelled pending for this reason). This note goes further: it asks *which terms* can be made integral, over a
> wider class of rings. [What is new here](#what-is-new-relative-to-the-base) lists exactly what is the base's and
> what is not. The extensions go beyond the base whichever schemes the base concerns.

## Setting

Schemes, the equivalence (E) (sandwich action with term scalings), the two pinned scheme files and the numbering of
the terms are as in [no-integral-form-z-half-schemes](../no-integral-form-z-half-schemes/), and the files are read
from the `data/` folder of that note. S₁ is the ⟨2,4,5;32⟩ scheme of AlphaEvolve (that note checks that the file
agrees term by term with AlphaEvolve's published decomposition) and S₂ is the ⟨3,3,6;40⟩ scheme attributed to
Smirnov (2013) (that note does not check the attribution). Both have coefficients in ℤ[1/2], and the terms
(a_r, b_r, c_r) are numbered r = 1, …, R in file order. With the term matrices M_r = a_r b_r c_r of that note,
t(r, r, r) below is tr(M_r). K is a field of characteristic 0, so ℚ ⊆ K, and an equivalent form over K is

    a′_r = λ_r U a_r V⁻¹,   b′_r = μ_r V b_r W⁻¹,   c′_r = (λ_r μ_r)⁻¹ W c_r U⁻¹      (r = 1, …, R)      (E)

with U, V, W invertible over K and λ_r, μ_r ∈ K^×. Reordering the terms changes nothing below, since every
statement follows the terms by their original numbers.

**Definitions.**
- A subring A ⊆ K (with 1) is **2-admissible** if there is a ring homomorphism from A to some field of
  characteristic 2. Ring homomorphisms map 1 to 1. Examples: ℤ and the localisation ℤ_(2) (rationals with odd
  denominator), both by reduction modulo 2 (u/v ↦ (u mod 2)·(v mod 2)⁻¹ in 𝔽₂, well defined because v is odd); the
  2-adic integers ℤ₂ when ℚ₂ ⊆ K, by reduction modulo 2; every valuation ring of K whose maximal ideal contains 2,
  by the map to its residue field, which has characteristic 2.
- Term r of an equivalent form is **A-integral** if every coefficient of a′_r, b′_r and c′_r lies in A.
- **Mixed traces** of the original scheme: t(r, s, u) = tr(a_r b_s c_u) for term numbers r, s, u. The product
  a_r b_s c_u is an n×n matrix.
- A **balanced product** is a product t(r₁, s₁, u₁) ⋯ t(r_L, s_L, u_L) whose three index multisets
  {r₁, …, r_L}, {s₁, …, s_L} and {u₁, …, u_L} coincide. Its **support** is the set of term numbers that occur.
  This note uses five types (r, s, q distinct term numbers where they differ). In each factor of an a-, b- or
  c-pair, the term number at the position of a, of b or of c, respectively, differs from the other two:

  | type | product | support |
  |---|---|---|
  | single | t(r, r, r) | {r} |
  | a-pair | t(r, q, q) · t(q, r, r) | {r, q} |
  | b-pair | t(q, r, q) · t(r, q, r) | {r, q} |
  | c-pair | t(r, r, q) · t(q, q, r) | {r, q} |
  | 3-cycle | t(r, s, q) · t(q, r, s) · t(s, q, r) | {r, s, q} |

  For example, for the c-pair the first indices are {r, q}, the second {r, q} and the third {q, r}.
- A set of terms is **obstructed** if it is the support of a balanced product that is a rational number of negative
  2-adic valuation (an odd numerator over an even denominator, in lowest terms).

## Statement

**Theorem A (obstructed sets are never integral together).** Let S be an obstructed set of terms of a scheme with
rational coefficients. Then for every field K of characteristic 0, every equivalent form over K and every
2-admissible subring A ⊆ K, the terms of S are not all A-integral.

**Theorem B (⟨3,3,6;40⟩: no term at all).** Every single trace of S₂ has negative 2-adic valuation:
t(r, r, r) = 3/2 for 16 terms and 5/4 for the other 24. Hence, for every K, every equivalent form over K and every
2-admissible A ⊆ K, **no term** of S₂ is A-integral.

**Theorem C (⟨2,4,5;32⟩: at least 20 terms, and 20 is attained).** For every K, every equivalent form over K and
every 2-admissible A ⊆ K, **at least 20 of the 32 terms** of S₁ are not A-integral. Conversely, there is an
equivalent form over ℚ (given below) in which exactly 20 terms are not ℤ_(2)-integral. So for A = ℤ_(2), and for
every valuation ring A of K whose maximal ideal contains 2, the smallest number of non-A-integral terms over all
equivalent forms is **exactly 20**.

**Corollary 1 (exactly 20 over ℤ and over every 2-admissible ring).** In the equivalent form of Theorem C the 12
integral terms have all their coefficients in ℤ. Hence, for every field K of characteristic 0 and every
2-admissible subring A ⊆ K, in particular for A = ℤ, the smallest number of terms of S₁ that are not A-integral,
over all equivalent forms over K, is **exactly 20**.

**Corollary 2 (no reduction to characteristic 2).** No equivalent form of S₁ or S₂ over a field K of
characteristic 0 has all its coefficients in a 2-admissible subring of K. In particular, no equivalent form can be
reduced term by term to a scheme over a field of characteristic 2.

## Proof

**Lemma 1.** For all term numbers r, s, u,

    tr(a′_r b′_s c′_u) = (λ_r μ_s / (λ_u μ_u)) · t(r, s, u).

If the three terms r, s and u are A-integral, the left side lies in A.

*Proof.* a′_r b′_s c′_u = λ_r μ_s (λ_u μ_u)⁻¹ · U a_r V⁻¹ V b_s W⁻¹ W c_u U⁻¹ = λ_r μ_s (λ_u μ_u)⁻¹ · U (a_r b_s c_u)
U⁻¹, and the trace is invariant under conjugation. If a′_r, b′_s and c′_u have entries in A, so do their product and
its trace. ∎

**Lemma 2.** A balanced product has the same value for every equivalent form: Π_i tr(a′_{r_i} b′_{s_i} c′_{u_i}) =
Π_i t(r_i, s_i, u_i).

*Proof.* By Lemma 1 the product of the scalars is Π_i λ_{r_i} μ_{s_i} / (λ_{u_i} μ_{u_i}). The λ's in the numerator
run over the multiset {r_i} and those in the denominator over {u_i}; the μ's run over {s_i} and {u_i}. The three
multisets coincide, so the scalar is 1. ∎

**Lemma 3.** Let A be a commutative ring with a ring homomorphism φ: A → F to a field F of characteristic 2. If a
rational number x lies in A (as an element of K), then its 2-adic valuation is ≥ 0.

*Proof.* Otherwise x = u/(2^k v) with u, v odd integers and k ≥ 1, and 2^k v x = u holds in A. Applying φ gives
φ(2)^k φ(v) φ(x) = φ(u). The left side is 0, since φ(2) = 2·1_F = 0. The right side is 1, since u is odd. ∎

*Proof of Theorem A.* Suppose all terms of S were A-integral. Every factor tr(a′_{r_i} b′_{s_i} c′_{u_i}) of the
balanced product has its indices in S, so it lies in A by Lemma 1, and so does the product. By Lemma 2 the
product equals the original rational value, whose 2-adic valuation is negative. This contradicts Lemma 3. ∎

*Proof of Theorem B.* Each single {r} is obstructed by the value of t(r, r, r), computed exactly by verify.py
(3/2 for 16 terms, 5/4 for 24). Apply Theorem A to S = {r} for each r. ∎

*Proof of Theorem C, lower bound.* Let I be the set of A-integral terms of an equivalent form. By Theorem A, I
contains no obstructed set, so its complement meets every obstructed set: it is a **hitting set** of the
hypergraph whose edges are the obstructed sets. For S₁ (exact values computed by verify.py):

| edges of type | count |
|---|---|
| single | 0 (t(r, r, r) = 1 for 24 terms and 2 for 8) |
| a-pair | 76 |
| b-pair | 0 |
| c-pair | 54 (32 of them are also a-pairs; 22 are new) |
| 3-cycle | 384 ordered triples (r, s, t), all with distinct indices, forming 120 three-element sets |

Let H₁ be the hypergraph of the obstructed singles, a- and b-pairs and 3-cycles (196 edges), and H₂ the hypergraph
with the c-pairs added (218 edges). The smallest hitting set of H₁ has **18** elements, and the smallest hitting
set of H₂ has **20**. Both minima are computed exactly by verify.py, with two different exact algorithms (a branch
and bound for the largest edge-free set, and a search that branches on the vertices of an unhit edge), and both
are attained by explicit sets. So the complement of I has at least 20 elements. ∎

The c-pairs are needed for the bound 20: without them the same argument gives only 18. Example certificates (term
numbers as in the file):
- a-pair {1, 3}: t(1, 3, 3) · t(3, 1, 1) = (−1) · (−1/2) = 1/2;
- c-pair {3, 10}, not an a- or b-pair: t(3, 3, 10) · t(10, 10, 3) = (−1) · (−1/2) = 1/2;
- 3-cycle {1, 3, 17}: t(1, 3, 17) · t(17, 1, 3) · t(3, 17, 1) = 1 · (−1/4) · (−1/2) = 1/8.

*Proof of Theorem C, attainment.* Take U = I₂ and

    V = [ 0 0 0  2 ;  1 0 0 −1 ;  0 1 0 −1 ;  0 0 1 −1 ],
    W = [ 2 −2 −2 −2 0 ;  0 2 0 0 0 ;  0 0 2 0 0 ;  0 0 0 2 0 ;  −1 1 1 1 2 ]

(rows separated by semicolons; det V = −2 and det W = 32, so both are invertible over ℚ). For each term let ν(X)
be the smallest 2-adic valuation of a nonzero entry of X, and put λ_r = 2^(−ν(a_r V⁻¹)) and
μ_r = 2^(−ν(V b_r W⁻¹)). verify.py computes the form (E) with these choices exactly from the pinned file and checks
that it satisfies all 1 600 Brent equations (so it is a scheme) and that:
- every a′_r and every b′_r has all coefficients in ℤ_(2);
- c′_r has all coefficients in ℤ_(2) exactly for the 12 terms r = 5, 6, 8, 9, 10, 11, 13, 21, 28, 29, 30, 31;
- in these 12 terms every coefficient of a′_r, b′_r and c′_r is an integer;
- for each of the other 20 terms, c′_r has a coefficient of 2-adic valuation −1 (16 terms) or −2 (4 terms).

So exactly 12 terms are ℤ_(2)-integral and 20 are not. Let A be a valuation ring of K whose maximal ideal 𝔪
contains 2. Every odd integer v is a unit of A: otherwise v ∈ 𝔪, and then 1 = xv + 2y ∈ 𝔪 for integers x, y with
xv + 2y = 1, which is impossible. So ℤ_(2) ⊆ A, and the same 12 terms are A-integral. Together with the lower bound
this gives exactly 20. As a consistency check, verify.py confirms that the 12 integral terms contain no edge of H₂,
as Theorem A requires. ∎

*Proof of Corollary 1.* The integrality of the 12 terms is the third item checked above. It also follows from the
first two items: all coefficients of the form lie in ℤ[1/2] (those of the file do; V⁻¹ = adj(V)/det V and
W⁻¹ = adj(W)/det W have entries in ℤ[1/2] because V and W have integer entries and det V = −2, det W = 32; U = I₂;
the scalings are powers of 2), and an element u/2^k of ℤ[1/2] (u odd or k = 0) with nonnegative 2-adic valuation
has k = 0, so it is an integer. Let A ⊆ K be a 2-admissible subring. Lower bound: by Theorem C, every equivalent
form over K has at least 20 terms that are not A-integral. Attainment: the form above has coefficients in ℚ ⊆ K
and U, V, W, λ_r, μ_r over ℚ, so it is an equivalent form over K. A contains 1, hence the image of ℤ, which is a
copy of ℤ because K has characteristic 0; so every integer lies in A, and the 12 terms with integer coefficients
are A-integral. So at most 20 terms of this form are not A-integral, and the minimum is exactly 20. ℤ is
2-admissible (reduction modulo 2). ∎

Here "over ℤ" refers to the coefficients of the form. The transformation is over ℚ: V and W have integer entries
but are not invertible over ℤ (det V = −2, det W = 32), and the scalings are powers of 2.

*Proof of Corollary 2.* If all coefficients were in a 2-admissible A, every term would be A-integral, against
Theorems B and C. A term-by-term reduction to a field F of characteristic 2 means applying a ring homomorphism
A → F to all coefficients, where A ⊆ K is a subring that contains them (for example the subring they generate);
such an A is 2-admissible, so by the first sentence no such homomorphism exists. ∎

## What is new relative to the base

**In Moran, Schwartz and Yuan (2026)** (full text of v1 read, in particular §3.2 "Integer algorithms",
§4 "Applications", §5 "Open problems" and the references):
- **Proposition 3:** for matrices A_1, …, A_m ∈ M_n(ℂ), if the trace of some product A_{j_1} ⋯ A_{j_k} is not an
  integer, there is no invertible X with X A_j X⁻¹ ∈ M_n(ℤ) for every j.
- **§3.2** applies it to the products O_j P_j Q_j of the three factor matrices of each term (a_j b_j c_j here):
  the ⟨3,3,6,40⟩ ℤ[1/2] algorithm found by Smirnov cannot be transformed into an integer algorithm, because
  Trace(O_j P_j Q_j) ∉ ℤ for some j; a ⟨2,4,5,32⟩ algorithm over ℤ[1/2] (attributed there to Hopcroft and Kerr) has
  no ℤ equivalent form "for the same reason" as their ⟨4,4,4,48⟩ example, where all single traces are integers and
  the trace of a product of two such matrices is 1/2; a ⟨2,4,4,26⟩ algorithm has none, through a product of
  three. They print neither the ⟨3,3,6,40⟩ nor the ⟨2,4,5,32⟩ scheme, name no certificate terms and do not identify
  the files they used; [Relation to the source](../no-integral-form-z-half-schemes/#relation-to-the-source) in the
  published note says what follows from this for S₁ and S₂.
- Their non-existence statements for integer forms concern the ring ℤ and the existence of a form in which **all**
  terms are integral at once. (Their other non-existence results concern rational or real equivalent forms of schemes
  with irrational or complex coefficients.) §5 (open problem 1) asks for a necessary and sufficient condition for an
  integer equivalent form.

**Beyond the base, in this note:**
1. **Per-term statements.** For ⟨3,3,6;40⟩, *every* single trace is non-integral, so *no single term* can be made
   integral (the base needs one such term). For ⟨2,4,5;32⟩, *at least 20 of the 32 terms* are non-integral in
   every equivalent form, and 20 is attained, with the 12 integral terms having integer coefficients, so the minimum
   is exactly 20 over ℤ and over every 2-admissible ring (Corollary 1). This is a term-level, exact quantity; the
   base states only that not all terms can be integral. (The note does not answer the base's open problem 1.)
2. **The ring generalisation.** From ℤ to every 2-admissible subring, through Lemma 3; this includes ℤ_(2), ℤ₂,
   valuation rings with 2 in the maximal ideal, and every ring that allows a reduction to a field of characteristic
   2.
3. **A different family of invariants.** Mixed traces tr(a_r b_s c_u) combined into balanced products (the a-, b- and
   c-pairs and the 3-cycles), where the base uses traces of products of whole-term matrices a_j b_j c_j. The single
   traces t(r, r, r) = tr(a_r b_r c_r) are common to both. The exact minimum 20 does not depend on the choice of
   invariants, since it is attained.

What is the base's and is used here: the idea that a trace invariant under the action, if it is not integral, rules
out an integral form (their Proposition 3 and its application to term matrices in §3.2). Lemmas 1 and 2 are this
idea for mixed traces.

## Scope

- "Equivalent" means (E), possibly followed by a reordering of the terms, over a field of characteristic 0. No
  other symmetries of the matrix multiplication tensor are considered.
- The theorems concern S₁ and S₂ and every scheme equivalent to them, as pinned files. They say nothing about other
  schemes of the same format and rank that are not equivalent to S₁ or S₂.
- The minimum 20 is exact for every 2-admissible ring, ℤ included (Corollary 1). It is a minimum over equivalent
  forms over a field K, that is, over transformations U, V, W, λ_r, μ_r with entries in K. The note says nothing
  about forms obtained only by transformations invertible over ℤ.
- The minimum hitting sets are exact computations on finite hypergraphs that verify.py builds from the pinned file
  of S₁ (their edges are counted by type in the table above). Theorem C rests on them (computer-assisted), and
  verify.py recomputes both minima with two different exact algorithms.

## Literature search

The class `own-extension` rests on the base above (full text of v1 read) and on a search for further sources: two
arXiv queries, one combining matrix multiplication with 2-adic, Hensel, integer coefficients, non-integral or
rational coefficients, and one combining it with invariant, scheme and equivalent; the abstracts returned were read.
No passage or abstract read counts the non-integral terms of a scheme, or treats forms with coefficients in a ring
other than ℤ that has a homomorphism to a field of characteristic 2 (such as ℤ_(2)). The other coefficient rings in
the base (ℤ[1/2], ℤ[1/8], ℚ[i], ℚ[√161], ℚ, ℝ, ℂ, and the extensions F[√d] of fields F of characteristic 0) have no
such homomorphism, because 2 is invertible in each of them. This is a statement about that search. The base is cited
as credit for the idea and for the statement over ℤ (proved for the pinned files in
[no-integral-form-z-half-schemes](../no-integral-form-z-half-schemes/)); no step of the proofs above relies on it.

## Verification

```bash
python theorems/per-term-2-integrality-z-half-schemes/verify.py              # offline: the copies in ../no-integral-form-z-half-schemes/data/
python theorems/per-term-2-integrality-z-half-schemes/verify.py --download   # fetches the two pinned URLs instead
python theorems/per-term-2-integrality-z-half-schemes/verify.py --cache DIR  # reads other local copies, no network
```

The two scheme files and their SHA-256 are those of
[no-integral-form-z-half-schemes](../no-integral-form-z-half-schemes/). By default the script reads the unmodified
copies kept in that note's [data/](../no-integral-form-z-half-schemes/data/) folder under their licence (MIT; see
[data/README.md](../no-integral-form-z-half-schemes/data/README.md)), so it runs offline and nothing is copied
into this folder. With `--download` it fetches the same two files by HTTPS from the pinned URLs (with a fixed
User-Agent that names this project, and nothing else sent); with `--cache DIR` it reads `DIR/<sha1 of the URL>` or
`DIR/<file name>`. In every case it checks the SHA-256 first. It uses the Python standard library only, is
deterministic, and runs in a few seconds. It checks:
1. the SHA-256, the shapes, the ℤ[1/2] coefficients and all Brent equations of both files (1 600 for S₁, 2 916 for
   S₂);
2. Theorem B: the 40 single traces of S₂, and that t(1, 1, 1) = 3/2 is the certificate tr(M_1) of the published
   note;
3. for S₁: the table of all 32³ mixed traces, the obstructed sets of the five types and their counts, the three
   certificates above, and that the five product types are balanced;
4. the edge counts 196 (H₁) and 218 (H₂), and the minimum hitting sets 18 (H₁) and 20 (H₂), each by two exact
   algorithms, with witness sets;
5. the explicit form: that it is (E) applied to S₁ with the stated U, V, W (checked through the relations
   a′_r V = λ_r a_r, b′_r W = μ_r V b_r and λ_r μ_r c′_r = W c_r, without inverses) and with scalings λ_r, μ_r that
   are powers of 2; that it satisfies all Brent equations; which terms are ℤ_(2)-integral; that every coefficient of
   these 12 terms is an integer; the valuations of the other 20; and that its integral terms contain no obstructed
   set;
6. as an illustration of Lemmas 1 and 2 (not part of the proof): after a seeded random rational sandwich with
   random term scalings, every mixed trace changes by exactly the factor of Lemma 1, and every balanced product of
   the five types is unchanged;
7. a negative control: the standard ⟨2,4,5⟩ algorithm, disguised by a seeded random rational sandwich with term
   scalings, has no obstructed set of these types (as Theorem A predicts for a scheme with an integral form).

It exits with code 0 only if every check passes.

## Sources

- Y. Moran, O. Schwartz, S. Yuan (2026). *Complex to Rational Fast Matrix Multiplication*. arXiv:2602.13171
  (v1, 13 February 2026). Proposition 3, §3.2, §4 and §5. <https://arxiv.org/abs/2602.13171>. The base.
- The scheme sources and the pinned files are listed in
  [no-integral-form-z-half-schemes](../no-integral-form-z-half-schemes/#sources): AlphaEvolve (Novikov et al.
  2025, arXiv:2506.13131) for S₁; Smirnov (2013, doi:10.1134/S0965542513120129), to whom S₂ is attributed (the
  attribution is not checked); and `dronperminov/FastMatrixMultiplication` at commit
  `64f58a5e40806bc47847b11dd8aceec043fa895d`, whose two files are vendored in that note's `data/` folder.
