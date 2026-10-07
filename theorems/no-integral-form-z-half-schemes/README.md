# No integer equivalent form for two ℤ[1/2] matrix multiplication schemes

> **Provenance: literature.** In §3.2 of *Complex to Rational Fast Matrix Multiplication* (arXiv:2602.13171),
> Moran, Schwartz and Yuan (2026) state, with their Proposition 3 as the tool, that the ⟨3,3,6,40⟩ ℤ[1/2] algorithm
> of Smirnov cannot be transformed into an integer algorithm, and that the same holds for a ⟨2,4,5,32⟩ algorithm
> over ℤ[1/2] which they attribute to Hopcroft and Kerr (1971). They print neither scheme, name no certificate terms
> for either, and do not identify the files they used, so it is not established that their statements concern the
> schemes S₁ and S₂ below or schemes equivalent to them (see [Relation to the source](#relation-to-the-source)).
> This note proves the statement directly for the two pinned files: the proof below is written out in full, and
> [verify.py](verify.py) is independent code (its own parser, exact Brent check and trace computation, Python
> standard library only). Both certificates are of the type used by their Proposition 3: the trace of a product of
> term matrices.

## Statement

**Schemes.** For a format ⟨n,m,p⟩ and a field K, a *scheme of rank R* is a list of R terms (a_r, b_r, c_r) with
a_r ∈ K^(n×m), b_r ∈ K^(m×p) and c_r ∈ K^(p×n) such that

    Σ_r ⟨a_r, X⟩ ⟨b_r, Y⟩ ⟨c_r, Z⟩ = tr(XYZ)   for all X ∈ K^(n×m), Y ∈ K^(m×p), Z ∈ K^(p×n),      (B)

where ⟨u, X⟩ = Σ_{i,j} u_ij X_ij. Comparing coefficients, (B) is the system of Brent equations
Σ_r a_r[i][j] · b_r[j′][k] · c_r[k′][i′] = [j = j′]·[k = k′]·[i = i′]. Taking for Z the matrix with a single 1 in
position (k, i) gives AB = Σ_r ⟨a_r, A⟩ ⟨b_r, B⟩ c_rᵀ, so a scheme multiplies an n×m matrix by an m×p matrix with R
multiplications.

**Equivalence.** Let K be a field of characteristic 0 (for example ℚ, ℝ or ℂ). For U ∈ GL_n(K), V ∈ GL_m(K),
W ∈ GL_p(K) and scalars λ_r, μ_r ∈ K^× put

    a′_r = λ_r U a_r V⁻¹,   b′_r = μ_r V b_r W⁻¹,   c′_r = (λ_r μ_r)⁻¹ W c_r U⁻¹   (r = 1, …, R).        (E)

This is the sandwich action together with term scalings. By Lemma 1 below it maps schemes to schemes. A scheme is
*equivalent* to (a_r, b_r, c_r) if it arises from it by (E), possibly followed by a reordering of the terms. It has
*integer coefficients* if every entry of every a′_r, b′_r, c′_r lies in ℤ ⊂ K.

**The two schemes.** Both are read from pinned files of the collection of known schemes in the GitHub repository
`dronperminov/FastMatrixMultiplication` (commit `64f58a5e40806bc47847b11dd8aceec043fa895d`):

| | Scheme | File (under `schemes/known/`) | SHA-256 | Denominators |
|---|---|---|---|---|
| S₁ | ⟨2,4,5;32⟩ of AlphaEvolve (Novikov et al. 2025) | [`tensor/2x4x5_tensor.mpl`](https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/known/tensor/2x4x5_tensor.mpl) | `e03c7743a60f53ae21a3413af4a5f019600a12befc8ed22ffdf2baa8b0f7dd4b` | 1, 2 |
| S₂ | ⟨3,3,6;40⟩, attributed to Smirnov (2013) | [`tensor/3x3x6_tensor.mpl`](https://raw.githubusercontent.com/dronperminov/FastMatrixMultiplication/64f58a5e40806bc47847b11dd8aceec043fa895d/schemes/known/tensor/3x3x6_tensor.mpl) | `3e79357c5d2540e5c54c2a5f484f17009f70799b10bd45ed8e4bf893b5e223ab` | 1, 8 |

In each file the r-th `Triad` is the term (a_r, b_r, c_r), with matrices of sizes n×m, m×p and p×n in this order.
Terms are numbered r = 1, …, R in file order. The Maple check line at the end of each file subtracts from A.B the
sum over r of Trace(Transpose(a_r).A) · Trace(Transpose(b_r).B) · Transpose(c_r), which is the identity
AB = Σ_r ⟨a_r, A⟩⟨b_r, B⟩ c_rᵀ above. All coefficients lie in ℤ[1/2], and some are not integers. The file for S₁
agrees term by term, in the same order, with the decomposition `decomposition_245` in the notebook
`mathematical_results.ipynb` of the repository `google-deepmind/alphaevolve_results` (commit
`4226acbf237ff9ad10ba7673a2af127a2d8a5971`). This identity was checked once; `verify.py` does not re-check it,
because it downloads only the two scheme files. The file for S₂ is not compared with Smirnov (2013), here or
in `verify.py`; the attribution is not checked in this note.

**Theorem.** Let K be a field of characteristic 0.

1. There are no U ∈ GL_2(K), V ∈ GL_4(K), W ∈ GL_5(K) and λ_r, μ_r ∈ K^× (r = 1, …, 32) such that (E) applied to
   S₁ has integer coefficients.
2. There are no U ∈ GL_3(K), V ∈ GL_3(K), W ∈ GL_6(K) and λ_r, μ_r ∈ K^× (r = 1, …, 40) such that (E) applied to
   S₂ has integer coefficients.

In words: neither S₁ nor S₂ has an equivalent form with integer coefficients. Reordering the terms does not change
the set of coefficients, so it plays no role.

## Proof

**Lemma 1 (the action maps schemes to schemes).** If (a_r, b_r, c_r) satisfies (B), so does (a′_r, b′_r, c′_r).

*Proof.* With ⟨M, X⟩ = tr(MᵀX): ⟨U a V⁻¹, X⟩ = ⟨a, UᵀX V⁻ᵀ⟩, ⟨V b W⁻¹, Y⟩ = ⟨b, VᵀY W⁻ᵀ⟩ and
⟨W c U⁻¹, Z⟩ = ⟨c, WᵀZ U⁻ᵀ⟩. The scalars of each term multiply to λ_r μ_r (λ_r μ_r)⁻¹ = 1. So the left side of (B)
for the new terms equals the left side for the old terms at X̃ = UᵀXV⁻ᵀ, Ỹ = VᵀYW⁻ᵀ, Z̃ = WᵀZU⁻ᵀ, which is
tr(X̃ỸZ̃) = tr(Uᵀ XYZ U⁻ᵀ) = tr(XYZ). ∎

Lemma 1 is not used in the argument below. It only shows that an "equivalent form" is again a scheme.

**Term matrices.** For each term put M_r = a_r b_r c_r, an n×n matrix, and M′_r = a′_r b′_r c′_r.

**Lemma 2 (conjugation).** M′_r = U M_r U⁻¹ for every r.

*Proof.* M′_r = λ_r μ_r (λ_r μ_r)⁻¹ · U a_r V⁻¹ V b_r W⁻¹ W c_r U⁻¹ = U M_r U⁻¹: the term scalings cancel, and so do
the inner factors V⁻¹V and W⁻¹W. ∎

**Lemma 3 (Moran–Schwartz–Yuan, Proposition 3).** For all term numbers j_1, …, j_k,
tr(M′_{j_1} ⋯ M′_{j_k}) = tr(M_{j_1} ⋯ M_{j_k}). If (a′_r, b′_r, c′_r) has integer coefficients, this trace is an
integer.

*Proof.* By Lemma 2, M′_{j_1} ⋯ M′_{j_k} = U (M_{j_1} ⋯ M_{j_k}) U⁻¹, and the trace is invariant under conjugation. If
all a′_r, b′_r, c′_r have integer entries, so do all M′_r and their products, and so does the trace. ∎

**Proof of the Theorem.** Since K has characteristic 0, ℤ embeds in K and a rational number u/v in lowest terms
with v > 1 is not in ℤ: if u/v = z ∈ ℤ, then u = vz in ℤ, which is impossible since v > 1 and gcd(u, v) = 1.

*Part 2 (S₂, one factor).* Term 1 of S₂ is

    a_1 = [ 1  0 -1 ;  0  1 -1 ; -1  1  0 ]
    b_1 = [ 0  0 -1/8 -1/8 -1  0 ;  0  1/8  0  0  1 -1/8 ; -1 -1/8  0  1/8  0  0 ]
    c_1 = [ 1/8 1/8 0 ;  0 1 0 ;  -1 0 1 ;  -1 0 0 ;  0 0 1/8 ;  0 -1 -1 ]

(rows separated by semicolons), and

    M_1 = a_1 b_1 c_1 = [ 1/2 1/4 -1/4 ;  1/4 1/2 1/4 ;  -1/4 1/4 1/2 ],   tr(M_1) = 3/2.

If some (E) gave S₂ integer coefficients, Lemma 3 with k = 1 would give 3/2 = tr(M′_1) ∈ ℤ, a contradiction.

*Part 1 (S₁, two factors).* For S₁ every single trace tr(M_r) is 1 or 2, so one factor does not suffice. Terms 2
and 5 of S₁ are

    a_2 = [ 1/2 -1/2 0 0 ;  1/2 -1/2 0 0 ]
    b_2 = the 4×5 matrix with a single nonzero entry, -2, in row 2 and column 1
    c_2 = [ 1/2 1/2 ;  1/2 1/2 ;  0 0 ;  0 0 ;  0 0 ]
    a_5 = [ 0 0 1/2 1/2 ;  0 0 0 0 ]
    b_5 = the 4×5 matrix with a single nonzero entry, 2, in row 3 and column 2
    c_5 = [ 0 0 ;  1 0 ;  1 0 ;  0 0 ;  0 0 ]

and

    M_2 = [ 1/2 1/2 ;  1/2 1/2 ],   M_5 = [ 1 0 ;  0 0 ],   M_2 M_5 = [ 1/2 0 ;  1/2 0 ],   tr(M_2 M_5) = 1/2.

If some (E) gave S₁ integer coefficients, Lemma 3 with k = 2 would give 1/2 = tr(M′_2 M′_5) ∈ ℤ, a
contradiction. ∎

## Relation to the source

- **Proposition 3** of Moran, Schwartz and Yuan: for A_1, …, A_m ∈ M_n(ℂ), if the trace of some product
  A_{j_1} ⋯ A_{j_k} is not an integer, then there is no invertible X with X A_j X⁻¹ ∈ M_n(ℤ) for every j. Their §3.2
  applies it to the matrices O_j P_j Q_j of a scheme (M_j = a_j b_j c_j in the notation used here), which the
  sandwich action conjugates while the term scalings cancel. Lemmas 2 and 3 above are this argument, and both
  certificates are of the type their Proposition 3 uses.
- **S₂.** §3.2 states that the ⟨3,3,6,40⟩ ℤ[1/2] algorithm of Smirnov cannot be transformed into an integer
  algorithm, because Trace(O_j P_j Q_j) ∉ ℤ for some j; it does not say which j. Part 2 above gives such a j
  explicitly for the pinned file S₂.
- **S₁.** §3.2 states that a ⟨2,4,5,32⟩ algorithm over ℤ[1/2], the one they attribute to Hopcroft and Kerr (see
  below), has no ℤ equivalent form "for the same reason" as the ⟨4,4,4,48⟩ scheme over ℚ[i] treated just before it:
  all single traces are integers, and the trace of a product of two term matrices,
  Trace(O_{j_1}P_{j_1}Q_{j_1} · O_{j_2}P_{j_2}Q_{j_2}), is not. It does not say which pair. Part 1 above gives such a
  pair explicitly for the pinned file S₁.
- **Attribution of the ⟨2,4,5⟩ scheme.** Moran, Schwartz and Yuan attribute the ⟨2,4,5,32⟩ algorithm over ℤ[1/2]
  to Hopcroft and Kerr (1971), their reference [24]. By its abstract, that paper multiplies a p×2 by a 2×n matrix
  with ⌈(3pn + max(n, p))/2⌉ multiplications. For {p, n} = {4, 5}, which corresponds to the format ⟨2,4,5⟩ under the
  usual permutation symmetry of formats, this is 33. Their text does not identify the file they used. The proof
  above does not depend on this question, because it proves the statement directly for the AlphaEvolve scheme S₁.

## Scope

- "Equivalent" means (E) followed by reordering of terms, over any field of characteristic 0. "Integer
  coefficients" means that every coefficient lies in ℤ.
- The theorem concerns S₁ and S₂ and every scheme equivalent to them. It says nothing about other schemes of the
  same format and rank that are not equivalent to S₁ or S₂.
- `verify.py` checks the two pinned files. The theorem applies to any other copy only if that copy is equivalent to
  them.

## Verification

```bash
python theorems/no-integral-form-z-half-schemes/verify.py              # downloads the two files
python theorems/no-integral-form-z-half-schemes/verify.py --cache DIR  # reads local copies, no network
```

The script obtains the two files, either by two HTTPS downloads from the pinned URLs above (with a generic
User-Agent and nothing else sent) or, with `--cache DIR`, from `DIR/<sha1 of the URL>` or `DIR/<file name>`. It then
checks:

1. the SHA-256 of each file;
2. the number of terms, the factor shapes, and that all coefficients lie in ℤ[1/2], not all in ℤ;
3. validity over ℚ: all n²m²p² Brent equations, in exact rational arithmetic (1 600 for S₁, 2 916 for S₂);
4. the certificates with `fractions.Fraction`, from the term matrices M_j = a_j b_j c_j: tr(M_1) = 3/2 for S₂, and
   tr(M_2 M_5) = 1/2 for S₁; for S₁ also that every single trace tr(M_j) is an integer;
5. as an illustration of Lemmas 2 and 3 (not part of the proof): after a seeded random rational sandwich with random
   term scalings, the scheme still satisfies the Brent equations and the certificate value is unchanged.

It exits with code 0 only if every check passes. Without network delays it runs in under a second.

## Sources

- Y. Moran, O. Schwartz, S. Yuan (2026). *Complex to Rational Fast Matrix Multiplication*. arXiv:2602.13171
  (v1, 13 February 2026). Proposition 3 and §3.2 "Integer algorithms". <https://arxiv.org/abs/2602.13171>
- A. Novikov, N. Vũ, M. Eisenberger, E. Dupont, P.-S. Huang, A. Z. Wagner, S. Shirobokov, B. Kozlovskii,
  F. J. R. Ruiz, A. Mehrabian, M. P. Kumar, A. See, S. Chaudhuri, G. Holland, A. Davies, S. Nowozin, P. Kohli,
  M. Balog (2025). *AlphaEvolve: A coding agent for scientific and algorithmic discovery*. arXiv:2506.13131.
  <https://arxiv.org/abs/2506.13131>. Published decomposition: <https://github.com/google-deepmind/alphaevolve_results>
  (commit `4226acbf237ff9ad10ba7673a2af127a2d8a5971`, `mathematical_results.ipynb`, `decomposition_245`).
- A. V. Smirnov (2013). *The bilinear complexity and practical algorithms for matrix multiplication*. Computational
  Mathematics and Mathematical Physics 53(12), 1781–1795.
  [doi:10.1134/S0965542513120129](https://doi.org/10.1134/S0965542513120129)
- J. E. Hopcroft, L. R. Kerr (1971). *On minimizing the number of multiplications necessary for matrix
  multiplication*. SIAM Journal on Applied Mathematics 20(1), 30–36.
  [doi:10.1137/0120004](https://doi.org/10.1137/0120004). Cited here only for the attribution remark above.
- Scheme files: <https://github.com/dronperminov/FastMatrixMultiplication> at commit
  `64f58a5e40806bc47847b11dd8aceec043fa895d`, `schemes/known/tensor/2x4x5_tensor.mpl` and
  `schemes/known/tensor/3x3x6_tensor.mpl`.
