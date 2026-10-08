# Powering in non-associative Cayley-Dickson algebras (octonions, sedenions, dimension 32): repeated multiplication vs square-and-multiply

**Type:** T2 (naive-exp → poly, in the bit length of e) · **Verification:** V2 (exact operation counts) ·
**Provenance:** literature (see [Credit](#credit)). Every claim below is proved in [PROOFS.md](PROOFS.md) and checked
by the scripts listed under [Verification](#verification).

**Problem.** Fix the odd modulus p = 2^61 − 1. Let A_0 = ℤ/pℤ with the identity conjugation, and A_m = A_{m−1} × A_{m−1}
with

    (a, b)(c, d) = (ac − d̄ b,  d a + b c̄),        conj(a, b) = (ā, −b).

Elements of A_m are tuples of 2^m residues (index 0 is the unit 1 = (1, 0)). Given m ∈ {3, 4, 5} (the octonions,
the sedenions and the 32-dimensional algebra over ℤ/pℤ), x ∈ A_m and e ≥ 1, compute x^e, defined as the left power
p_1 = x, p_{k+1} = p_k x. The size parameter is n, the bit length of e. A_m is not associative for m ≥ 3 (Lemma 4),
so it is not obvious that the binary method may regroup the factors; it may, because A_m is power-associative
(Lemma 2).

| Algorithm | Algebra products (exact) | Implementation |
|---|---|---|
| Repeated multiplication | e − 1 = Θ(2^n) | [repeated.py](implementations/repeated.py) |
| Left-to-right square-and-multiply | ⌊log₂ e⌋ + popcount(e) − 1 ≤ 2(n − 1), so Θ(n) | [square_multiply.py](implementations/square_multiply.py) |

One algebra product in dimension 2^m makes exactly 4^m multiplications of residues (Lemma 3), so for fixed m each
product costs O(1) word operations.

**Why it's here.** The pair is the classical one of
[modular-exponentiation-repeated-vs-square-multiply](../modular-exponentiation-repeated-vs-square-multiply), in a
setting where the textbook correctness argument (associativity) is not available. The binary method is correct
here because every power of x lives in a commutative, associative two-dimensional subalgebra. That this is a real
condition is shown by the closely related para-product x ∗ y = x̄ ȳ on the same space, for which binary powering
returns a wrong value already at e = 4 (PROOFS.md §8; over ℝ this is Remark 2(b) of the repository note
[para-cayley-dickson-closed-form-powers](../../theorems/para-cayley-dickson-closed-form-powers/)).

## Results

Every statement here is proved in [PROOFS.md](PROOFS.md) (section numbers in brackets) for every m ≥ 0 and every
commutative ring of coordinates where it says so.

- **Lemma 1** [§4]. Over any commutative ring, the product of A_m is bilinear with unit 1 = (1, 0), conjugation is
  linear and involutive, and x + x̄ = t(x)·1, x x̄ = x̄ x = n(x)·1, with t(x) = 2x_0 and n(x) = Σ_i x_i².
- **Lemma 2 (power-associativity)** [§5]. x² = t(x) x − n(x)·1, and span{1, x} is a commutative, associative
  subalgebra containing every power of x. Hence x^i x^j = x^(i+j), every bracketing of a product of e copies of x
  equals x^e, and x^e = α_e·1 + β_e·x, where α_e + β_e X is the remainder of X^e modulo X² − t(x)X + n(x).
- **Proposition S** [§3]. Square-and-multiply returns x^e with exactly ⌊log₂ e⌋ + popcount(e) − 1 algebra
  products, at most 2(n − 1), and exactly 2(n − 1) when e = 2^n − 1.
- **Repeated multiplication** [§2] returns x^e with exactly e − 1 ≥ 2^(n−1) − 1 algebra products.
- **Lemma 3** [§1]. One product in dimension 2^m makes exactly 4^m multiplications of residues, besides
  4^m − 2^m additions and subtractions, (4^m − 3·2^m + 2)/3 negations and one reduction mod p after each operation.
- **Lemma 4** [§7]. For odd p ≥ 3: (e_1 e_2) e_4 = e_7 while e_1 (e_2 e_4) = −e_7 in every A_m with m ≥ 3, so A_m is not
  associative; for x = e_1 + e_10 and y = e_4, (x x) y = −2e_4 while x (x y) = −2e_4 − 2e_15 in every A_m with
  m ≥ 4, so A_m is not even alternative. PROOFS.md writes out every basis product used.
- **The para-product** [§8]. With x ∗ y = x̄ ȳ on the same space, binary powering of x = 1 + e_1 gives −4 at e = 4
  while the left power is −4e_1 (m ≥ 1, mod p).

**Why residues mod p** [§9]. Over the integers the coordinates of x^e grow: for x = 1 + e_1, which lies in the
subalgebra A_1 × 0 × … (multiplied like the complex numbers, (a, b)(c, d) = (ac − bd, ad + bc)), x^e = (1 + i)^e,
whose two coordinates satisfy α² + β² = 2^e (|1 + i|^(2e) = 2^e), so max(|α|, |β|) lies between 2^((e−1)/2) and
2^(e/2), and the integer output has Θ(e) bits, exponential in n; reducing mod p keeps every residue multiplication
O(1).

## Limits

- **Bit-size view.** n is the bit length of e. In the VALUE e, repeated multiplication is linear.
- **Fixed dimension.** m ≤ 5. For general m both counts are multiplied by 4^m (Lemma 3).
- **What is counted.** Multiplications of residues. Additions, subtractions, negations and reductions mod p
  (Θ(4^m) per product, Lemma 3), the loop control and reading the bits of e are not counted.
- **Reading the bits.** Square-and-multiply reads e through `bin(e)`; that this takes time linear in n is a
  machine-model assumption about the interpreter (see Background), not proved here.
- **No lower bound** for the problem is claimed.

## Verification

The [checks script](../../experiments/2026-10-07_cayley_dickson_powering_checks.py) is deterministic and runs in
under a minute; the [entry's tests](../../tests/test_entry_cayley_dickson_powering.py) repeat the essential checks
in a few seconds. The proofs in [PROOFS.md](PROOFS.md) cover all inputs; the scripts check the statements on the
ranges given. Every check line starts with `[PASS]` or `[FAIL]`, and the script ends with `ALL CHECKS PASSED`.

- **V1.** Both implementations agree with each other and with an oracle (`harness.check`) on bit lengths
  n = 1..16, 24, 32, 64, 128 and 256, three instances per n (repeated multiplication up to n = 9). Instances: m drawn
  from {3, 4, 5}; x with uniformly random residues, small coordinates in −3..3, real, purely imaginary, purely
  imaginary of norm 0 mod p (so x² = 0), x = 1 + e_1, and sparse elements with coordinates in {0, 1, p − 1}; e random
  of exactly n bits, all ones, or a power of two. The oracle has two tiers:
  - every e: x^e must equal α_e·1 + β_e·x with α_e + β_e X = X^e mod (X² − tX + n) over ℤ/pℤ (Lemma 2), computed with
    polynomials of degree < 2 only, no Cayley–Dickson product;
  - e ≤ 40: the left powers are also recomputed from the definition with a product built from a table of basis
    products e_i e_j = s(i, j) e_{i xor j}, the signs s derived from the doubling rules, written independently of the
    recursive product of the implementations.
- **Checks script.**
  - (1) The table product equals the recursive product on 240 random pairs, m = 0..5.
  - (2) Lemma 1 and Lemma 2 mod p (x + x̄ = t·1, x x̄ = x̄ x = n·1; x² = t x − n·1; span{1, x} closed, commutative and
    associative), 90 random elements, m = 0..5.
  - (3) Lemma 4, every product written in its proof: the non-associativity witness for m = 3, 4, 5 and the
    non-alternativity witness for m = 4, 5.
  - (4) Lemma 2: 432 random bracketings of products of e copies of x equal x^e, for e ≤ 12 and m = 3..5.
  - (5) Proposition S and the oracle: both algorithms = left power = the remainder formula on 768 extra instances
    (e ≤ 64), and square-and-multiply = the remainder formula for 15 random 200-bit exponents.
  - (6) The exact counts: e − 1 and ⌊log₂ e⌋ + popcount(e) − 1 algebra products, each of 4^m residue
    multiplications, for e = 1..300 (m = 3) and e = 1..100 (m = 4, 5), and square-and-multiply also at
    e = 2^n − 1 and random n-bit e for n = 16..1024.
  - (7) The integer growth example: for x = 1 + e_1 over ℤ, α² + β² = 2^e and 2^((e−1)/2) ≤ max(|α|, |β|) ≤ 2^(e/2)
    for e ≤ 200.
  - (8) Oracle control: 247 deliberately wrong outputs rejected, 32 true outputs accepted.
  - (9) The remaining facts of PROOFS.md: the numbers of multiplications, additions and subtractions, negations and
    reductions in one product (m = 0..6); the four doubling rules (40 random pairs, m = 1..5); the digits read from
    `bin(e)` (e = 1..4096); the para-product witness mod p (m = 1..5); the recursion depth of the product (m = 0..5);
    the working memory of square-and-multiply (n = 64..8192); x² = 0 for 20 isotropic elements of the generator.
- **V2 (exact counts, `measure: "reported"`).** `generate_scaling` gives octonions (m = 3) with CountingInt
  coordinates, which count every multiplication of two residues, and e = 2^n − 1; the implementations are unchanged.
  Both fits give α = 1.000 at tolerance 0.02.

  | Algorithm (n values) | Claimed count | Rivals (α), all rejected |
  |---|---|---|
  | repeated multiplication (6..11) | 64 (2^n − 2) | n³ 1.918, 1.5ⁿ 1.724, n·2ⁿ 0.859, 2ⁿ/n 1.220, 3ⁿ 0.636 |
  | square-and-multiply (16..512) | 128 (n − 1) | √n 2.033, log n 4.333, n log n 0.825, n² 0.508 |

- **Shape diagnostic:** MATCH for both: base 2 with n⁰ (n = 2..14) and n¹ (n = 2..40).

## Background

Cited, not claims of this entry (the entry's `background` field lists them with their sources):

- **Machine-model assumption.** Python's `bin(e)` runs in time linear in the bit length of e (the slice `bin(e)[3:]`
  then copies n − 1 characters). PROOFS.md §10 uses it for the cost of reading the bits; it is not proved here.
- The identities of Lemma 1 are stated for the real Cayley–Dickson algebras of every dimension, with exactly this
  doubling and conjugation, by Biss, Dugger and Isaksen (2008): Definition 2.1, Section 2 (2Re(x) = x + x*) and
  Lemma 3.6 (x x* = x* x = ‖x‖²).
- In a non-associative linear algebra in which every element satisfies a quadratic equation, multiplication is
  associative for powers: stated without proof by Etherington (1941, J. London Math. Soc. 16, pp. 50–51), who cites
  Dickson (1912, Trans. Amer. Math. Soc. 13, §5).
- The algebras of dimension 2^t built by the Cayley–Dickson process are quadratic algebras,
  x² − t(x)x + n(x)1 = 0: Schafer's 1961 lecture notes *An Introduction to Nonassociative Algebras*, Chapter III,
  equations (25)–(31), with a different doubling convention (below).
- The binary method is described in Knuth, *The Art of Computer Programming*, Vol. 2, Section 4.6.3 (Evaluation of
  Powers).

## Credit

- **Power-associativity.** I. M. H. Etherington (1941, *Some non-associative algebras in which the multiplication
  of indices is commutative*, J. London Math. Soc. 16, pp. 50–51) states, without proof and citing Dickson (1912,
  §5), that "in a non-associative linear algebra where every element satisfies a quadratic equation … multiplication
  is associative for powers". R. D. Schafer's 1961 lecture notes *An Introduction to Nonassociative Algebras*
  (Chapter III, equations (25)–(31)) show that the Cayley–Dickson process produces such algebras: an algebra 𝔄 with 1
  is called quadratic if 𝔄 ≠ F1 and x² − t(x)x + n(x)1 = 0 for every x; the doubling there, (b_1, b_2)(b_3, b_4) =
  (b_1 b_3 + μ b_4 b̄_2, b̄_1 b_4 + b_3 b_2) over a field of characteristic ≠ 2, carries an involution with
  x + x̄ = t(x)1 and x x̄ = x̄ x = n(x)1, which gives the quadratic equation, and iterating it from F1 gives algebras of
  dimension 2^t. That doubling differs from the one used here in the order of the factors and in the free scalar μ,
  and the notes do not state power-associativity for these algebras. The proof here (Lemma 2) is our own: it uses
  only the identities of Lemma 1, which Biss, Dugger and Isaksen (2008) publish over ℝ for exactly this doubling
  (see Background), and Lemma 1 is proved here over every commutative ring. R. Schafer (1954), a paper on the
  algebras formed by the Cayley–Dickson process, is cited by Biss, Dugger and Isaksen for basic statements of
  alternativity; only its bibliographic data were seen. Power-associativity is not claimed as new here.
- **The binary method** is described in Knuth, TAOCP Vol. 2, Section 4.6.3; the modular-exponentiation entry of this
  repository cites the same book. It is not claimed as new here.

## Sources

- D. K. Biss, D. Dugger, D. C. Isaksen (2008). *Large annihilators in Cayley–Dickson algebras*. Communications in
  Algebra 36(2), 632–664. [doi:10.1080/00927870701724094](https://doi.org/10.1080/00927870701724094);
  arXiv:math/0511691.
- I. M. H. Etherington (1941). *Some non-associative algebras in which the multiplication of indices is
  commutative*. Journal of the London Mathematical Society 16, 48–55.
  [doi:10.1112/jlms/s1-16.1.48](https://doi.org/10.1112/jlms/s1-16.1.48). Pages 50–51.
- R. D. Schafer (1961). *An Introduction to Nonassociative Algebras* (lecture notes, Department of Mathematics,
  Oklahoma State University). Project Gutenberg eBook #25156, <https://www.gutenberg.org/ebooks/25156>. Chapter III,
  equations (25)–(31).
- R. Schafer (1954). *On the algebras formed by the Cayley–Dickson process*. American Journal of Mathematics 76,
  435–446. [doi:10.2307/2372583](https://doi.org/10.2307/2372583).
- D. E. Knuth (1997). *The Art of Computer Programming, Vol. 2: Seminumerical Algorithms* (3rd ed.). Addison-Wesley.
  ISBN 978-0-201-89684-8. Section 4.6.3.
