# Closed-form left powers in para-Cayley–Dickson algebras

> **Provenance: literature.** For dimension ≤ 8 the Theorem is the case y = x of the identity
> (x ∗ y) ∗ x = n(x) y of symmetric composition algebras, which is published (credit below). For dimension ≥ 16 it
> follows in a few lines from identities published for the Cayley–Dickson algebras of every dimension; the closed
> form itself was not found stated in the sources consulted. The proofs below are complete and self-contained and
> do not use the cited results; `verify.py` checks every statement on a stated finite range. See [Credit](#credit).
>
> **What this note adds.** Remark 2 (binary powering is right at every e = 2^j − 1 and 2^j − 2, and first wrong at
> e = 4 exactly when x⁴ ≠ n(x) x̄²) and the explicit counterexample of Remark 3 are additions of this note, with
> their proofs; they were not found in the sources consulted. That the identities (x ∗ y) ∗ x = x ∗ (y ∗ x) = n(x) y
> cannot both hold for all x, y in dimension ≥ 16 already follows from Elduque's Remark 3.3 and Theorem 3.2 (see
> [Credit](#credit)); only the explicit witness, for the first identity, is new.

## Setting

**Cayley–Dickson algebras.** A_0 = ℝ, with the identity as conjugation. For m ≥ 1, A_m = A_{m−1} × A_{m−1} with

    (a, b)(c, d) = (ac − d̄ b,  d a + b c̄),        conj(a, b) = (ā, −b).

A_m has dimension 2^m. Elements are written in the standard basis e_0 = 1, e_1, …, e_{2^m − 1} (the basis of
A_{m−1} × 0 followed by that of 0 × A_{m−1}, so e_{2^{m−1}+i} = (0, e_i)); x_i is the i-th coordinate.
A_{m−1} × 0 is a subalgebra on which the product and conjugation are those of A_{m−1}, since
(a, 0)(c, 0) = (ac − 0̄·0, 0·a + 0·c̄) = (ac, 0) and conj(a, 0) = (ā, 0); the coordinates keep their indices, so
n(x) and t(x) (below) are also those of A_{m−1}. A_1 multiplies like the complex numbers:
(a, b)(c, d) = (ac − bd, ad + bc) for real a, b, c, d, since conjugation on A_0 = ℝ is the identity. (A_2 and A_3
are isomorphic to the quaternions and the octonions; Biss, Dugger and Isaksen 2008, Examples 2.3 and 2.4. This is
cited and not used below.) A_m is not associative for m ≥ 3. By the doubling formula, (u, 0)(0, 1) = (0, u),
(u, 0)(0, v) = (0, v u) and (0, 1)(u, 0) = (0, ū) for u, v ∈ A_{m−1}. Hence e_1 e_2 = e_3 and e_2 e_1 = (0, ē_1) = −e_3
in A_2, and e_3 e_4 = e_7, e_2 e_4 = e_6 and e_1 e_6 = (0, e_2 e_1) = −e_7 in A_3. So (e_1 e_2) e_4 = e_7 while
e_1 (e_2 e_4) = −e_7, and A_3 embeds in every A_m with m ≥ 3 as above.

For x ∈ A_m write x̄ = conj(x), t(x) = 2x_0 and n(x) = Σ_i x_i².

**The para-product.** On the same space define

    x ∗ y = x̄ ȳ.

For m ≤ 3 this is the *para-Hurwitz algebra* of ℝ, ℂ, ℍ or 𝕆 in the terminology of Elduque (Examples 3.4), via
the isomorphisms just cited. For m ≥ 4 we call it the *para-Cayley–Dickson algebra* of dimension 2^m. The *left
powers* of x are

    p_1 = x,   p_{k+1} = p_k ∗ x   (k ≥ 1).

## Statement

**Theorem.** Let m ≥ 0, x ∈ A_m and n = n(x). Then for every j ≥ 0

    p_{2j+1} = n^j · x,        p_{2j+2} = n^j · x̄².

Equivalently, (x ∗ x) ∗ x = n(x) · x.

Here x̄² = x̄ x̄ is the square in A_m.

## Proof

**Lemma 1.** In A_m: the product is ℝ-bilinear, 1 = (1, 0) is a two-sided unit, and conjugation is ℝ-linear and
involutive with conj(1) = 1. Moreover, for every x,

    x + x̄ = t(x) · 1,        x x̄ = x̄ x = n(x) · 1.

*Proof.* Induction on m; for m = 0 everything is immediate (x̄ = x, t(x) = 2x, n(x) = x²). Let x = (a, b).
Bilinearity, linearity and the involution property follow from the defining formulas. The unit:
(1, 0)(c, d) = (c − d̄·0, d·1 + 0·c̄) = (c, d), and (c, d)(1, 0) = (c·1 − 0·d, 0·c + d·1̄) = (c, d). Next,
x + x̄ = (a + ā, 0) = (t(a)·1, 0) = t(x)·1. With conj(−b) = −b̄ and the induction hypothesis,

    x x̄ = (a, b)(ā, −b) = (a ā + b̄ b,  −b a + b a) = ((n(a) + n(b))·1, 0),
    x̄ x = (ā, −b)(a, b) = (ā a + b̄ b,  b ā − b ā) = ((n(a) + n(b))·1, 0),

and n(a) + n(b) = n(x). ∎

**Lemma 2.** Fix x ∈ A_m, put t = t(x), n = n(x), let R = ℝ[X]/(X² − tX + n) and let φ: R → A_m map the class of
α + βX to α·1 + βx. Then:

1. φ is an algebra homomorphism. Hence A_x = span{1, x}, its image, is a subalgebra, and it is commutative and
   associative.
2. The map σ: X ↦ t − X is an algebra automorphism of R, and conj(φ(r)) = φ(σ(r)) for every r ∈ R. Hence x̄ ∈ A_x,
   and conjugation is multiplicative on A_x: conj(uv) = conj(u) conj(v) for u, v ∈ A_x.

*Proof.* By Lemma 1, x² = x(t·1 − x̄) = t x − n·1. Every class of R has a unique representative α + βX. For
r = α + βX and s = γ + δX, rs = (αγ − βδn) + (αδ + βγ + βδt)X in R. By bilinearity and the unit,
φ(r)φ(s) = αγ·1 + (αδ + βγ)x + βδx² = (αγ − βδn)·1 + (αδ + βγ + βδt)x = φ(rs). So φ is a homomorphism. Every
product of two elements of A_x is the image of a product in R, which is commutative and associative, so A_x is a
commutative, associative subalgebra. (If x is real, φ is not injective; the argument does not need injectivity.)
For σ: (t − X)² − t(t − X) + n = X² − tX + n, so X ↦ t − X respects the defining relation and defines an algebra
endomorphism of R, and σ∘σ = id. By linearity of conjugation, conj(1) = 1 and x̄ = t·1 − x,
conj(φ(α + βX)) = α·1 + β(t·1 − x) = φ(σ(α + βX)). For u = φ(r), v = φ(s):
conj(uv) = conj(φ(rs)) = φ(σ(rs)) = φ(σ(r))φ(σ(s)) = conj(u) conj(v). ∎

**Proof of the Theorem.** Every left power lies in A_x: p_1 = x, and p_{k+1} = conj(p_k) x̄ ∈ A_x by Lemma 2.
Then p_2 = x ∗ x = x̄ x̄ = x̄², and, computing in the commutative associative algebra A_x with conj multiplicative
there,

    p_3 = conj(x̄²) x̄ = x² x̄ = x (x x̄) = n · x.

Now suppose p_{k+2} = n·p_k for some k ≥ 1. Since conjugation is linear and the product bilinear,
p_{k+3} = conj(n p_k) x̄ = n · conj(p_k) x̄ = n · p_{k+1}. With p_3 = n·p_1 this gives p_{k+2} = n·p_k for all
k ≥ 1, hence p_{2j+1} = n^j p_1 and p_{2j+2} = n^j p_2. The identity (x ∗ x) ∗ x = n(x) x is p_3 = n p_1, and the
same induction derives the closed form from it. ∎

The proof uses only Lemma 1 and the two-dimensional subalgebra span{1, x}. It does not use the identity
(x ∗ y) ∗ x = n(x) y for general y, which is false for m ≥ 4 (Remark 3).

## Remarks

**1. Computing p_e.** By definition p_e costs e − 1 para-products. By the Theorem, with e = 2j + 1 or e = 2j + 2,
it can instead be computed from: n(x), with 2^m multiplications and 2^m − 1 additions; the real number n^j, with
⌊log₂ j⌋ + popcount(j) − 1 ≤ 2⌊log₂ j⌋ multiplications for j ≥ 1 by left-to-right binary powering in ℝ (one squaring
per binary digit of j after the leading one and one multiplication per further digit 1; ℝ is associative), and none
for j = 0; for even e, the conjugate x̄, which by Lemma 1 (x̄ = t(x)·1 − x) changes the sign of the 2^m − 1
coordinates x_1, …, x_{2^m−1}, and one algebra product x̄ x̄; and finally 2^m multiplications of coordinates by n^j.
Real arithmetic operations are counted as unit cost.

**2. Binary powering.** Left-to-right binary powering with the para-product computes

    B(1) = x,   B(2a) = B(a) ∗ B(a),   B(2a + 1) = B(2a) ∗ x,

that is, square-and-multiply over the binary digits of e. Here:

- (a) For every x: B(e) = p_e for every e = 2^j − 1 (j ≥ 1) and every e = 2^j − 2 (j ≥ 2). In particular B(e) = p_e
  for e = 1, 2, 3, 6, 7, 14, 15, 30, 31, ….
- (b) B(4) = p_4 if and only if x⁴ = n(x) x̄², where x⁴ = x² x² is computed in A_m. For x = 1 + e_1 (any m ≥ 1),
  B(4) = −4·1 while p_4 = −4e_1.

So binary powering is first wrong at e = 4 for every x with x⁴ ≠ n(x) x̄², for example x = 1 + e_1. It is **not**
wrong at every e ≥ 4: by (a) it is right at every e = 2^j − 1 and 2^j − 2.

*Proof of (a).* For odd a = 2j + 1 the Theorem gives p_a ∗ p_a = conj(n^j x) conj(n^j x) = n^{2j} x̄² = p_{4j+2}
= p_{2a}. Also B(2a + 1) = B(2a) ∗ x and p_{2a+1} = p_{2a} ∗ x. So if B(a) = p_a for an odd a, then
B(2a) = p_{2a} and B(2a + 1) = p_{2a+1}. Starting from B(1) = p_1, the binary prefixes 1, 3, 7, …, 2^j − 1 of
e = 2^j − 1 are odd and each is twice the previous one plus 1; e = 2^j − 2 is twice the odd number 2^{j−1} − 1. ∎

*Proof of (b).* B(2) = p_2 = x̄², so B(4) = p_2 ∗ p_2 = conj(x̄²) conj(x̄²) = x² x², computed in A_x (Lemma 2),
while p_4 = n x̄². For x = 1 + e_1, which lies in the subalgebra A_1 (the complex number 1 + i): t = n = 2,
x² = t x − n = 2e_1, x² x² = (2e_1)² = −4, and x̄² = t x̄ − n = −2e_1, so p_4 = −4e_1. ∎

**3. The identity (x ∗ y) ∗ x = n(x) y fails for every m ≥ 4.** In A_4, take x = e_1 + e_10 and y = 1 + e_4. Then
n(x) = 2 and (x ∗ y) ∗ x = 2 + 2e_4 + 2e_15, while n(x) y = 2 + 2e_4. In detail: the doubling formula gives
(u, 0)(0, v) = (0, v u), (0, u)(v, 0) = (0, u v̄) and (0, u)(0, v) = (−v̄ u, 0) for u, v ∈ A_{m−1}, and e_i e_i = −1 for
i ≥ 1 (Lemma 1, since ē_i = −e_i). In A_3 (e_4 = (0, 1), e_5 = (0, e_1), e_6 = (0, e_2)) this gives e_1 e_4 = e_5,
e_5 e_1 = (0, e_1 ē_1) = e_4, e_2 e_5 = (0, e_1 e_2) = e_7, e_6 e_1 = (0, e_2 ē_1) = e_7 and e_2 e_6 = (0, e_2 e_2) = −e_4.
In A_4 (e_10 = (0, e_2), e_14 = (0, e_6)) it gives e_10 e_4 = (0, e_2 ē_4) = −e_14, e_1 e_10 = (0, e_2 e_1) = −e_11,
e_10 e_1 = (0, e_2 ē_1) = e_11, e_5 e_10 = (0, e_2 e_5) = e_15, e_14 e_1 = (0, e_6 ē_1) = −e_15 and
e_14 e_10 = (−ē_2 e_6, 0) = (e_2 e_6, 0) = −e_4. An element z with z_0 = 0 has z̄ = −z (Lemma 1),
so x̄ = −x, ȳ = 1 − e_4, and x ∗ y = x̄ ȳ = −(e_1 + e_10)(1 − e_4) = −e_1 + e_5 − e_10 − e_14 =: z. Then
(x ∗ y) ∗ x = z̄ x̄ = −(e_1 − e_5 + e_10 + e_14)(e_1 + e_10) = −(−1 − e_11 − e_4 − e_15 + e_11 − 1 − e_15 − e_4)
= 2 + 2e_4 + 2e_15. Since A_4 × 0 × … is a subalgebra of every
A_m (m ≥ 4) on which product and conjugation, hence the para-product, are those of A_4, the same x and y give a
counterexample in every A_m with m ≥ 4. The case y = x still holds in every dimension (the Theorem), and by
bilinearity so does every y ∈ span{1, x}: (x ∗ y) ∗ x is linear in y, and for y = 1,
(x ∗ 1) ∗ x = conj(x̄) x̄ = x x̄ = n(x)·1 (Lemma 1).

## Credit

The citations below are credit; none of them is used in the proofs above.

- **Dimension ≤ 8.** A. Elduque's survey *Composition algebras* (arXiv:1810.09979) states, as Theorem 3.2, that a
  composition algebra is symmetric if and only if (x ∗ y) ∗ x = x ∗ (y ∗ x) = n(x) y for all x, y, and, in
  Examples 3.4, that para-Hurwitz algebras (x • y = x̄ · ȳ on a Hurwitz algebra) are symmetric composition algebras,
  crediting these examples to Okubo (1978). His doubling formula (§2, formula (7)) with the scalar −1 is the one used
  here, and his Remark 2.7 identifies the resulting algebras over ℝ with ℂ, ℍ and 𝕆. The Theorem of this note, for
  m ≤ 3, is the case y = x of that identity together with the bilinearity step of the proof above.
- **Every dimension.** The identities of Lemma 1, for the real Cayley–Dickson algebras of every dimension with
  exactly this doubling and conjugation, are published by Biss, Dugger and Isaksen (2008): Definition 2.1, Section 2
  (2Re(x) = x + x*, left there to the reader) and Lemma 3.6 (x x* = x* x = ‖x‖²). Together they give
  x² = t(x) x − n(x)·1, the relation on which Lemma 2 rests. They do not consider the para-product or powers. The
  closed form for dimension ≥ 16 was not found stated in the sources consulted; it is classified here as literature
  because it follows from these identities in a few lines.
- **Failure in dimension ≥ 16.** That the identity (x ∗ y) ∗ x = x ∗ (y ∗ x) = n(x) y cannot hold for all x, y in
  dimension ≥ 16 already follows from Elduque's results: by his Remark 3.3 the identity forces the norm to be
  multiplicative, so the algebra with the nondegenerate norm n would be a composition algebra and, by Theorem 3.2, a
  symmetric one, whose dimension is 1, 2, 4 or 8. The explicit witness of Remark 3 is the note's.
- **Cayley–Dickson algebras in general.** R. Schafer (1954) is cited by Biss, Dugger and Isaksen for basic
  statements of alternativity (their Section 4); only its bibliographic data were seen here.

## Scope

- The real Cayley–Dickson algebras A_m of this note (doubling with α = −1 at every step), every m ≥ 0. Elements with
  integer or rational coordinates, which `verify.py` uses, are included. Other doubling parameters, other
  conventions for the doubling formula and other base rings are not claimed here.
- The statement is about left powers p_{k+1} = p_k ∗ x of the para-product. Other bracketings of the para-product
  and right-to-left binary powering are not discussed.
- Remark 2 claims (a) and (b) only; nothing is claimed about the set of all exponents at which binary powering is
  right.
- Remark 1 counts real arithmetic operations as unit cost. With integer coordinates, n ≥ 2 and j ≥ 1, the integer
  n^j has Θ(j log n) bits: with k = ⌊log₂ n⌋ ≥ 1, 2^(jk) ≤ n^j < 2^(j(k+1)), so it has between jk + 1 and j(k + 1)
  bits, and k ≤ log₂ n < 2k.

## Verification

```bash
python theorems/para-cayley-dickson-closed-form-powers/verify.py
```

The script is deterministic (fixed seed), uses the Python standard library only, computes with exact integers and
fractions, needs no network, and runs in a few seconds. It exits with code 0 only if every check passes. It checks:

- Lemma 1 (120 random integer elements, m = 0..5) and Lemma 2 (closure, commutativity, associativity of span{1, x}
  and multiplicativity of conjugation on it; 72 elements, m = 0..5);
- the Theorem by computing the left powers from the definition: exponents up to 200 for m ≤ 4 and up to 96 for
  m = 5, on 12 (m ≤ 4) or 6 (m = 5) random integer elements per dimension and on special elements (0, real
  elements, 1 + e_1, a purely imaginary element); 18 elements with fraction coordinates (e ≤ 40); the identity
  (x ∗ x) ∗ x = n(x) x on 180 further elements;
- the setting: A_{m−1} × 0 is a subalgebra closed under conjugation (m = 1..6, 60 random pairs), the five doubling
  rules (m = 1..6, 60 random pairs), A_1 multiplies like ℂ (200 random pairs), and the non-associativity witness
  with each basis product written above (m = 3..6);
- Remark 2: (a) on 33 random elements for all e = 2^j − 1, 2^j − 2 up to 255 (m = 0..5); (b) the criterion for B(4)
  on 120 random elements, and the witness x = 1 + e_1 for m = 1..5;
- Remark 3: the counterexample with every basis product and intermediate value written above, for m = 4, 5, 6, and
  the identity for y ∈ span{1, x} (m = 0..6, 70 random pairs x, y);
- Remark 1 and Scope: the closed-form evaluation equals p_e for e ≤ 150 (m = 0..5, 24 elements); the operation counts
  of Remark 1 by a counted evaluation (n(x): 2^m multiplications and 2^m − 1 additions; 2^m final multiplications;
  m = 0..6, odd and even e); conjugation negates exactly x_1, …, x_{2^m−1} (m = 0..6); the multiplication count of
  scalar binary powering (j ≤ 2048); the bit-length bounds for n^j (n = 2..64, j = 1..100).

## Sources

- A. Elduque (2018). *Composition algebras*. arXiv:1810.09979 (survey). Section 2, formula (7), Remark 2.7;
  Theorem 3.2, Remark 3.3, Examples 3.4.
- D. K. Biss, D. Dugger, D. C. Isaksen (2008). *Large annihilators in Cayley–Dickson algebras*. Communications in
  Algebra 36(2), 632–664. [doi:10.1080/00927870701724094](https://doi.org/10.1080/00927870701724094);
  arXiv:math/0511691. Definition 2.1, Examples 2.3 and 2.4, Section 2, Lemma 3.6, Section 4.
- R. Schafer (1954). *On the algebras formed by the Cayley–Dickson process*. American Journal of Mathematics 76,
  435–446. [doi:10.2307/2372583](https://doi.org/10.2307/2372583).
