# Proofs: powering in Cayley–Dickson algebras, repeated multiplication vs square-and-multiply

This file proves every claim that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the algebraic facts (Lemmas 1 to 4), the correctness of both
implementations, the exact operation counts and the V2 closed forms, the uncounted work, the space bounds, the
facts used by the V1 oracle, and the factual remarks (integer growth, the para-product). Statements about the
literature, and one machine-model assumption about the interpreter, are listed under `background` in `entry.json`
and are not proved here. Each section ends with the deterministic checks that re-run its computable facts and the
ranges they cover. A check covers only its range; the proofs cover the general statements.

## Conventions and cost model

R is a commutative ring with 1. A_0 = R with the identity as conjugation, and for m ≥ 1, A_m = A_{m−1} × A_{m−1}
with

    (a, b)(c, d) = (ac − d̄ b,  d a + b c̄),        conj(a, b) = (ā, −b).

Elements of A_m are tuples of 2^m elements of R in the standard basis e_0 = 1, e_1, …, e_{2^m−1}: the basis of
A_{m−1} × 0 followed by that of 0 × A_{m−1}, so e_{2^{m−1}+i} = (0, e_i). For x ∈ A_m, x̄ = conj(x), t(x) = 2x_0
and n(x) = Σ_i x_i² (elements of R). The power x^e (e ≥ 1) is the left power: x^1 = x, x^{k+1} = x^k x; x^0 = 1.

The entry uses R = ℤ/pℤ with the fixed odd modulus p = 2^61 − 1; residues are represented by integers in [0, p).
n is the bit length of e ≥ 1, so 2^{n−1} ≤ e < 2^n, and popcount(e) is the number of 1-digits of e.

**Cost model.** An *algebra product* is one top-level call `cd_mul(x, y, p)` on two elements of A_m. A *residue
multiplication* is one evaluation of `x[0] * y[0]` in the base case of `cd_mul`. Residues are below 2^61, so a
product of two residues is below 2^122 and a residue multiplication with its reduction mod p takes O(1) word
operations; so do additions, subtractions, negations and reductions of residues. Tuple slicing and concatenation
on tuples of length 2^k cost O(2^k). Reading the bits of e uses `bin(e)`, whose cost is a machine-model assumption
(section 10).

**Counting convention (V2).** `harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`) adds 1 to the
module tally `_ops["mul"]` and returns a new `CountingInt`; `__add__`, `__radd__`, `__sub__`, `__rsub__`,
`__neg__` and `__mod__` return a new `CountingInt` and count nothing; `__int__` and `__repr__` count nothing.
`generate_scaling(n, rng)` resets the tally and returns (x, 2^n − 1, p) with m = 3 and eight `CountingInt`
coordinates drawn from `rng`; `reported_cost(output)` returns the tally. A product `x[0] * y[0]` of two `CountingInt`
values counts exactly 1. Every coordinate the implementations handle on such an instance is a `CountingInt`: the
input coordinates, and every result of `%`, `-`, `+` and `*` on them.

## 1. One algebra product: exactly 4^m residue multiplications (Lemma 3), and the uncounted work

**Statement.** For every m ≥ 0, one call `cd_mul(x, y, p)` on elements of A_m makes exactly 4^m residue
multiplications, 4^m − 2^m additions and subtractions of residues, (4^m − 3·2^m + 2)/3 negations of residues, and
one reduction mod p after each of these operations. All four numbers are O(4^m), and the first three are Θ(4^m).

**Proof.** Let M(m), A(m) and N(m) be the three numbers, and G(k) the number of negations of `cd_conj` in dimension
2^k. Dimension 1: one multiplication `x[0] * y[0]`, reduced once; no addition, no negation: M(0) = 1,
A(0) = N(0) = 0. `cd_conj` in dimension 2^k ≥ 2 negates and reduces the 2^{k−1} coordinates of the second half and
recurses on the first half, and in dimension 1 returns its argument: G(0) = 0, G(k) = G(k−1) + 2^{k−1}, so
G(k) = 2^k − 1; it makes no multiplication and no addition. In dimension 2^m ≥ 2, `cd_mul` makes four calls of
dimension 2^{m−1} (ac, d̄ b, d a, b c̄), two conjugations of dimension 2^{m−1}, and then 2^{m−1} subtractions and
2^{m−1} additions, each reduced once. So M(m) = 4M(m−1), A(m) = 4A(m−1) + 2^m and
N(m) = 4N(m−1) + 2G(m−1) = 4N(m−1) + 2^m − 2. The closed forms satisfy these recurrences and the initial values:
4·4^{m−1} = 4^m; 4(4^{m−1} − 2^{m−1}) + 2^m = 4^m − 2^m; 4(4^{m−1} − 3·2^{m−1} + 2)/3 + 2^m − 2 =
(4^m − 6·2^m + 8 + 3·2^m − 6)/3 = (4^m − 3·2^m + 2)/3. For m ≥ 1, 4^m − 2^m ≥ 4^m/2. ∎

So for fixed m every algebra product costs O(1) word operations, and the counted residue multiplications are a
constant fraction of the arithmetic on residues. The power functions also reduce the 2^m input coordinates once
(`x = tuple(v % p for v in x)`), and the loops cost O(1) per iteration besides the products.

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 6: one product makes 4^m counted
multiplications (m = 0..5); section 9: an operation-recording number type counts multiplications, additions and
subtractions, negations and reductions in one product for m = 0..6 and compares them with the four closed forms.

## 2. Repeated multiplication: exactly e − 1 algebra products

**Statement.** For every m ≥ 0, every x and every e ≥ 1, `cd_power_repeated((x, e, p))` makes exactly e − 1 algebra
products, that is 4^m (e − 1) residue multiplications, and returns x^e. With 2^{n−1} ≤ e, this is at least
2^{n−1} − 1 products. On the V2 family (m = 3, e = 2^n − 1) the count is 64(2^n − 2).

**Proof.** The loop `for _ in range(e - 1)` runs e − 1 times with one call `cd_mul(r, x, p)` each, and nothing else
multiplies residues; section 1 gives 4^m per product. Invariant: after k iterations r is the left power x^{k+1}
(k = 0: r = x; an iteration replaces x^{k+1} by x^{k+1} x = x^{k+2}); the product is the one of A_m over ℤ/pℤ by
section 6. So the result is x^e. For the V2 family, 4^3 (2^n − 1 − 1) = 64(2^n − 2). ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 6: 4^m (e − 1) counted multiplications
for e = 1..300 (m = 3) and e = 1..100 (m = 4, 5), and the V2 points n = 6..11; section 5: the result equals the left
power computed with an independent product (e ≤ 64). `tests/test_entry_cayley_dickson_powering.py`,
`test_closed_form_counts` (n = 2..9).

## 3. Square-and-multiply: Proposition S

**Statement.** For every m ≥ 0, every x and every e ≥ 1 with binary digits 1 b_2 … b_n,
`cd_power_square_multiply((x, e, p))` returns x^e and makes exactly (n − 1) + (popcount(e) − 1) =
⌊log₂ e⌋ + popcount(e) − 1 algebra products, at most 2(n − 1), with equality exactly when e = 2^n − 1. On the V2
family (m = 3, e = 2^n − 1) it makes 2(n − 1) products, 128(n − 1) residue multiplications.

**Proof.** For e ≥ 1, `bin(e)` is "0b" followed by the binary digits of e, the first of which is 1, so `bin(e)[3:]`
is the string b_2 … b_n of the n − 1 digits after the leading one. The function starts with r = x and, for each
digit, replaces r by `cd_mul(r, r, p)` and then, if the digit is "1", by `cd_mul(r, x, p)`. Invariant: after the
digits 1 b_2 … b_i, whose value is k, r = x^k. It holds at the start (k = 1). A digit b turns k into 2k + b, and by
Lemma 2 (section 5), r r = x^k x^k = x^{2k} and, for b = 1, x^{2k} x = x^{2k+1}. So the result is x^e. The loop
makes one squaring per digit after the leading one, n − 1 = ⌊log₂ e⌋ of them, and one further product per further
digit 1, popcount(e) − 1 of them. Both counts are at most n − 1, and the second equals n − 1 exactly when every
digit is 1, that is e = 2^n − 1. Section 1 gives 4^m residue multiplications per product; for the V2 family
64 · 2(n − 1) = 128(n − 1). ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 6: 4^m (⌊log₂ e⌋ + popcount(e) − 1)
counted multiplications for e = 1..300 (m = 3) and e = 1..100 (m = 4, 5), at e = 2^n − 1 and at random n-bit e for
n = 16..1024, and the V2 points n = 16..512; section 5: the result equals the left power (e ≤ 64) and the remainder
formula (random 200-bit e); section 9: `bin(e)[3:]` lists the n − 1 digits after the leading one, e = 1..4096.
`tests/test_entry_cayley_dickson_powering.py`, `test_closed_form_counts`.

## 4. Lemma 1 (over any commutative ring)

**Statement.** In A_m over a commutative ring R: the product is R-bilinear, 1 = (1, 0) is a two-sided unit,
conjugation is R-linear and involutive with conj(1) = 1, and for every x

    x + x̄ = t(x) · 1,        x x̄ = x̄ x = n(x) · 1.

**Proof.** Induction on m; for m = 0 everything is immediate (x̄ = x, t(x) = 2x, n(x) = x²). Let x = (a, b) with
a, b ∈ A_{m−1}. Bilinearity, linearity and the involution property conj(conj(a, b)) = (conj(ā), b) = (a, b) follow
from the defining formulas and the induction hypothesis. The unit: (1, 0)(c, d) = (1·c − d̄·0, d·1 + 0·c̄) = (c, d)
and (c, d)(1, 0) = (c·1 − 0̄·d, 0·c + d·1̄) = (c, d), using conj(1) = 1 in A_{m−1}; and conj(1, 0) = (1̄, 0) = (1, 0).
Next, x + x̄ = (a + ā, b − b) = (t(a)·1, 0) = t(x)·1, since t(x) = 2x_0 = 2a_0 = t(a). With conj(−b) = −b̄,
conj(ā) = a and the induction hypothesis,

    x x̄ = (a, b)(ā, −b) = (a ā + b̄ b,  −b a + b a) = ((n(a) + n(b))·1, 0),
    x̄ x = (ā, −b)(a, b) = (ā a + b̄ b,  b ā − b ā) = ((n(a) + n(b))·1, 0),

and n(a) + n(b) = n(x). Only the ring axioms of R are used. ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 2 (mod p, m = 0..5, 90 random
elements).

## 5. Lemma 2 (power-associativity)

**Statement.** Fix x ∈ A_m, put t = t(x) and n = n(x), and let φ: R[X] → A_m map f = Σ c_i X^i to Σ c_i x^i
(x^0 = 1, x^i the left power). Then x² = t x − n·1; φ(fg) = φ(f)φ(g) for all f, g ∈ R[X]; φ(X² − tX + n) = 0; and
A_x = {α·1 + βx : α, β ∈ R} is a commutative, associative subalgebra that contains every power of x. In particular
x^i x^j = x^{i+j} for all i, j ≥ 0, and every bracketing of a product of e copies of x equals x^e. Moreover
x^e = α_e·1 + β_e·x, where α_e + β_e X is the remainder of X^e modulo X² − tX + n.

**Proof.** By Lemma 1, x̄ = t·1 − x, so x² = x(t·1 − x̄) = t x − x x̄ = t x − n·1. Since X² − tX + n is monic, every
class of S = R[X]/(X² − tX + n) has a unique representative α + βX. Let ψ: S → A_m send that class to α·1 + βx;
ψ is R-linear. For r = α + βX and s = γ + δX, rs = (αγ − βδn) + (αδ + βγ + βδt)X in S, and by bilinearity and the
unit ψ(r)ψ(s) = αγ·1 + (αδ + βγ)x + βδ x² = (αγ − βδn)·1 + (αδ + βγ + βδt)x = ψ(rs). So ψ is a homomorphism of
R-algebras with ψ(1) = 1, and its image A_x is the image of a commutative, associative ring under a homomorphism, so
it is a commutative, associative subalgebra. By induction on i, x^i = ψ(X^i mod (X² − tX + n)): this holds for i = 0
and i = 1, and x^{i+1} = x^i x = ψ(X^i)ψ(X) = ψ(X^{i+1}). Hence φ(f) = ψ(f mod (X² − tX + n)) for every f, φ is
multiplicative and vanishes on X² − tX + n, every power of x lies in A_x, and x^i x^j = ψ(X^i)ψ(X^j) = ψ(X^{i+j})
= x^{i+j}. A bracketed product of e ≥ 2 copies of x is a product u v of bracketed products of i and e − i copies
(1 ≤ i < e); by induction on e these equal x^i and x^{e−i}, so u v = x^e. The last sentence is
x^e = ψ(X^e mod (X² − tX + n)). ∎

The proof never uses associativity of A_m, which fails for m ≥ 3 (section 7).

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 2 (x² = t x − n·1 and span{1, x}
closed, commutative and associative, mod p, m = 0..5), section 4 (random bracketings of e ≤ 12 copies of x, m = 3, 4,
5, 432 comparisons), section 5 (the remainder formula against the left power and both algorithms).
`tests/test_entry_cayley_dickson_powering.py`, `test_power_associative`.

## 6. The implementations compute in A_m over ℤ/pℤ

**Statement.** For integer tuples x, y of length 2^m, `cd_mul(x, y, p)` returns the residues in [0, p) of the
product in A_m over ℤ/pℤ of the classes of x and y, and `cd_conj(x, p)` returns integers whose classes are the
conjugate of the class of x. Both power functions return residues in [0, p).

**Proof.** Reduction ℤ → ℤ/pℤ is a ring homomorphism, so it commutes with the doubling formulas. Induction on m:
in dimension 1, `x[0] * y[0] % p` is the residue of the product, and `cd_conj` returns its argument (the
conjugation of A_0 is the identity). In dimension 2^m ≥ 2, `cd_conj` returns conj of the first half (induction) and
`(-v) % p` for the second half; `cd_mul` combines the four half-size products (residues by induction) by `(u − v) % p`
and `(u + v) % p`, which are the residues of the two halves of (ac − d̄ b, d a + b c̄). Both power functions reduce
the input coordinates first (`v % p`) and return either this reduced tuple (e = 1) or a result of `cd_mul`. ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 1 (the recursive product of both
implementations equals the independent table product, m = 0..5, 240 random pairs).

## 7. Lemma 4: A_m is not associative (m ≥ 3) and not alternative (m ≥ 4)

**Statement.** Let p be odd, p ≥ 3. For m ≥ 3, (e_1 e_2) e_4 = e_7 and e_1 (e_2 e_4) = −e_7 in A_m. For m ≥ 4, with
x = e_1 + e_10 and y = e_4, (x x) y = −2e_4 and x (x y) = −2e_4 − 2e_15. Since 2 ≢ 0 mod p, e_7 ≠ −e_7 and
−2e_15 ≠ 0, so A_m is not associative for m ≥ 3 and not alternative for m ≥ 4.

**Proof.** With h = 2^{m−1} and u, v ∈ A_{m−1}, the doubling formula gives

    (u, 0)(v, 0) = (uv, 0),   (u, 0)(0, v) = (0, v u),   (0, u)(v, 0) = (0, u v̄),   (0, u)(0, v) = (−v̄ u, 0).

Every e_i with i ≥ 1 satisfies ē_i = −e_i (Lemma 1, t(e_i) = 0) and e_i e_i = −e_i ē_i = −1. Basis products used
(each from one of the four rules and products already listed; e_4 = (0, 1) in A_3, e_10 = (0, e_2) and
e_14 = (0, e_6) in A_4):

- A_2: e_1 e_2 = (e_1, 0)(0, 1) = (0, e_1) = e_3; e_2 e_1 = (0, 1)(e_1, 0) = (0, ē_1) = −e_3.
- A_3: e_3 e_4 = (0, e_3) = e_7; e_2 e_4 = (0, e_2) = e_6; e_1 e_4 = (0, e_1) = e_5; e_1 e_6 = (e_1, 0)(0, e_2) =
  (0, e_2 e_1) = −e_7; e_1 e_5 = (e_1, 0)(0, e_1) = (0, e_1 e_1) = −e_4; e_2 e_5 = (e_2, 0)(0, e_1) = (0, e_1 e_2) = e_7;
  e_6 e_1 = (0, e_2)(e_1, 0) = (0, e_2 ē_1) = (0, e_3) = e_7; e_6 e_2 = (0, e_2)(e_2, 0) = (0, e_2 ē_2) = (0, 1) = e_4.
- A_4: e_10 e_4 = (0, e_2)(e_4, 0) = (0, e_2 ē_4) = −e_14; e_1 e_14 = (e_1, 0)(0, e_6) = (0, e_6 e_1) = e_15;
  e_10 e_5 = (0, e_2)(e_5, 0) = (0, e_2 ē_5) = (0, −e_7) = −e_15; e_10 e_14 = (0, e_2)(0, e_6) = (−ē_6 e_2, 0) =
  (e_6 e_2, 0) = e_4.

(a) (e_1 e_2) e_4 = e_3 e_4 = e_7 and e_1 (e_2 e_4) = e_1 e_6 = −e_7.
(b) x is imaginary with n(x) = 2, so x x = −x x̄ = −2·1 (Lemma 1) and (x x) y = −2e_4. Next
x y = e_1 e_4 + e_10 e_4 = e_5 − e_14, and x (x y) = e_1 e_5 − e_1 e_14 + e_10 e_5 − e_10 e_14 =
−e_4 − e_15 − e_15 − e_4 = −2e_4 − 2e_15.
A_{m−1} × 0 is a subalgebra on which the product is that of A_{m−1} ((a, 0)(c, 0) = (ac, 0)) and the coordinates
keep their indices, so the witnesses in A_3 and A_4 are witnesses in every larger A_m. ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 3 (every product above, with the
independent table product, m = 3, 4, 5); section 9 (the four doubling rules on random pairs, m = 1..5).
`tests/test_entry_cayley_dickson_powering.py`, `test_not_associative_not_alternative`.

## 8. Binary powering fails for the para-product (the remark in README and `relationship`)

**Statement.** On the same space A_m (m ≥ 1) over ℤ/pℤ with p odd, p ≥ 3, define the para-product x ∗ y = x̄ ȳ, its left
powers P_1 = x, P_{k+1} = P_k ∗ x, and left-to-right binary powering B(1) = x, B(2a) = B(a) ∗ B(a),
B(2a+1) = B(2a) ∗ x. For x = 1 + e_1, B(4) = −4·1 while P_4 = −4e_1, and these differ.

**Proof.** x lies in A_1 × 0 × …, a subalgebra closed under conjugation on which the product is that of A_1, the
complex numbers over ℤ/pℤ: (a, b)(c, d) = (ac − bd, ad + bc); write i = e_1, so x = 1 + i and x̄ = 1 − i. Then
P_2 = B(2) = x̄ x̄ = (1 − i)² = −2i; B(4) = B(2) ∗ B(2) = conj(−2i) conj(−2i) = (2i)(2i) = −4;
P_3 = P_2 ∗ x = (2i)(1 − i) = 2 + 2i; P_4 = P_3 ∗ x = (2 − 2i)(1 − i) = −4i. The coordinate 0 of −4·1 is −4 ≢ 0 mod p,
while that of −4i is 0. ∎ (Over ℝ this is Remark 2(b) of the repository note
`theorems/para-cayley-dickson-closed-form-powers`.)

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 9 (m = 1..5, mod p).

## 9. Integer growth (the remark "why residues mod p" and the caveat)

**Statement.** Over R = ℤ, for x = 1 + e_1 ∈ A_m (m ≥ 1) and e ≥ 1, x^e = α_e + β_e e_1 with (α_e + β_e i) = (1 + i)^e,
α_e² + β_e² = 2^e and 2^{(e−1)/2} ≤ max(|α_e|, |β_e|) ≤ 2^{e/2}. So the coordinates of x^e have Θ(e) bits.

**Proof.** x lies in the subalgebra A_1 × 0 × …, on which the product is that of A_1 = ℤ[i] (section 8), which is
associative, so the left power is (1 + i)^e. The norm |·|² is multiplicative on ℤ[i] and |1 + i|² = 2, so
α_e² + β_e² = 2^e. The larger of α_e², β_e² is at least half of the sum and at most the sum:
2^{e−1} ≤ max² ≤ 2^e. Hence the larger coordinate M satisfies (e − 1)/2 ≤ log₂ M ≤ e/2, and its bit length
⌊log₂ M⌋ + 1 lies between (e − 1)/2 and e/2 + 1. ∎

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 7 (e ≤ 200, m = 1, 3, 5).

## 10. Time on every input, reading the bits, space

**Time.** Repeated multiplication makes e − 1 algebra products (section 2), each O(4^m) word operations
(section 1), and the loop control besides: Θ(e) = Θ(2^n) products for n ≥ 2. Square-and-multiply makes
⌊log₂ e⌋ + popcount(e) − 1 products, between n − 1 and 2(n − 1) (section 3): Θ(n) products for n ≥ 2. It also
builds `bin(e)` and its slice and reads n − 1 characters. *Machine-model assumption* (listed in `background`): `bin(e)`
runs in time linear in n; the slice copies n − 1 characters. Under this assumption reading the bits costs Θ(n), so
square-and-multiply takes Θ(n) time for fixed m. This is an assumption about the interpreter, not proved here.

**Space.** `cd_mul` in dimension 2^k holds the halves a, b, c, d, the four partial products and two conjugates, all
of length 2^{k−1}, and recurses with depth k, so a product needs O(2^m) residues of working memory
(Σ_k O(2^k) = O(2^m)). Repeated multiplication keeps x and r besides (O(2^m) residues) and the loop counter of
`range(e - 1)`, below e, so at most n bits. Square-and-multiply keeps x and r, the string `bin(e)` (n + 2
characters) and its slice (n − 1 characters): O(2^m) residues plus O(n) characters.

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 9: the recursion depth of `cd_mul` is
m + 1 calls for m = 0..5 (counted by a profiler hook), and the peak memory allocated during
`cd_power_square_multiply` (tracemalloc) stays within 4096 + 4n bytes above that of the n = 64 run, for
n = 64..8192 (octonions).

## 11. Facts used by the V1 oracle (`harness.py`)

- *Tier 1, every e.* By Lemma 2 (section 5) over R = ℤ/pℤ, x^e = α·1 + βx with α + βX = X^e mod (X² − tX + n),
  t = 2x_0 and n = Σ x_i² mod p. `quadratic_power` computes X^e in the commutative, associative ring
  S = (ℤ/pℤ)[X]/(X² − tX + n) by right-to-left binary powering (`mul` multiplies two representatives using
  X² = tX − n), which is correct in any associative ring, and returns the coordinates of α·1 + βx. It makes no
  Cayley–Dickson product.
- *Tier 2, e ≤ 40.* `_basis_sign_table(m)` gives signs s(i, j) with e_i e_j = s(i, j) e_{i xor j}. By induction on
  the level, with h = 2^{level−1} and the four rules of section 7: for i, j < h, (e_i, 0)(e_j, 0) = (e_i e_j, 0),
  sign s(i, j), index i xor j; (e_i, 0)(0, e_j) = (0, e_j e_i), sign s(j, i), index h + (j xor i) = i xor (h + j);
  (0, e_i)(e_j, 0) = (0, e_i ē_j), sign s(i, j)·c(j) with c(0) = 1 and c(j) = −1 for j ≥ 1 (ē_j = c(j) e_j by
  Lemma 1), index (h + i) xor j; (0, e_i)(0, e_j) = (−ē_j e_i, 0), sign −c(j) s(j, i), index (h + i) xor (h + j).
  These are the four assignments of the code. `table_mul` expands the product bilinearly over the basis and reduces
  mod p, so it computes the same product as `cd_mul` by a different route.
- *Rejections.* Outputs that are not tuples of the right length of integers in [0, p) are rejected, since the
  implementations return such tuples (section 6).

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 1 (table product = recursive product,
m = 0..5), section 5 (remainder formula = left power), section 8 (oracle control: 247 deliberately wrong outputs
rejected, 32 true outputs accepted). `tests/test_entry_cayley_dickson_powering.py`,
`test_table_product_equals_recursive_product`, `test_agree_and_check`.

## 12. Generator facts (V1 instances)

`harness._isotropic_imaginary` returns x = a e_1 + b e_2 + c e_3 with c² ≡ −(a² + b²) mod p, which it verifies
before returning; then x is imaginary with n(x) ≡ 0, so x² = t x − n·1 = 0 by Lemma 2. (The candidate square root
q^{(p+1)/4} is used because p ≡ 3 mod 4; the code accepts it only after the check c·c ≡ q, so the instance is correct
whatever the candidate.)

**Check.** `experiments/2026-10-07_cayley_dickson_powering_checks.py`, section 9 (x² = 0 for 20 generated isotropic
elements, m = 3, 4, 5).

## 13. Relationship and tag

Repeated multiplication makes e − 1 products, linear in the value of e and Θ(2^n) in its bit length (section 2);
square-and-multiply makes Θ(n) (section 3). The input is the n-bit exponent and a bounded number of residues, so
this is an exponential-to-polynomial improvement in the input length, with the naive method on the exponential side
(tag T2), as for `modular-exponentiation-repeated-vs-square-multiply`. The V2 fits are measurements of the exact
counts of sections 2 and 3; they prove nothing beyond those counts.
