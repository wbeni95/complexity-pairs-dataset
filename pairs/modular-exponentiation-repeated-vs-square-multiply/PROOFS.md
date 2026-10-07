# Proofs: modular exponentiation, repeated multiplication vs square-and-multiply

This file proves every claim of this entry (in `entry.json`, `README.md` and the docstrings of the code) from the
code in this folder: the facts about the modulus, the correctness and exact multiplication counts of both
algorithms, the space bounds, the addition-chain lower bound and the factor-2 statement in the caveats. Statements
about the literature are in the entry's `background` field. Timing fits are measurements. Each section ends with
the deterministic checks that re-run its computable facts and their ranges.

## Conventions

m = 2^64 − 59. n is the bit length of e (n = 0 for e = 0), so 2^(n−1) ≤ e < 2^n for n ≥ 1. popcount(e) is the
number of 1-bits of e. A **multiplication** is one evaluation of `x * y` on residues in the loop of an
implementation (each is followed by one reduction `% m`). Both implementations first reduce the base once
(`a %= m`) and start from r = `1 % m` = 1; neither of these is a multiplication.

## 1. The modulus: m = 2^64 − 59 is the largest prime below 2^64

**Lemma 1.1 (Lucas).** Let M ≥ 2 and g be integers with g^(M−1) ≡ 1 (mod M) and g^((M−1)/q) ≢ 1 (mod M) for every
prime q dividing M − 1. Then M is prime.

*Proof.* g is a unit mod M, since g · g^(M−2) ≡ 1. Let t be its multiplicative order; t divides M − 1. If t < M − 1,
then (M − 1)/t > 1 has a prime factor q, which divides M − 1, and t divides (M − 1)/q, so g^((M−1)/q) ≡ 1, a
contradiction. So t = M − 1. The powers g, g², …, g^(M−1) are M − 1 distinct units mod M, so all of 1, …, M − 1 are
units, i.e. coprime to M, and M is prime. ∎

**Statement.** m is prime, and every integer x with m < x < 2^64 is composite.

**Proof.** m − 1 = 2² · 11 · 137 · 547 · 5594472617641. The factors 2, 11, 137, 547 are prime, and 5594472617641 is
prime because no odd d with 3 ≤ d ≤ 2365263 = ⌊√5594472617641⌋ divides it (it is odd). For g = 2,
2^(m−1) ≡ 1 (mod m) and 2^((m−1)/q) ≢ 1 (mod m) for q = 2, 11, 137, 547, 5594472617641 (computed exactly), so m is
prime by Lemma 1.1. Each of the 58 integers 2^64 − 58, …, 2^64 − 1 has a divisor strictly between 1 and itself:
2 for the even ones, and for the odd ones the divisors listed in the check (for example 3 | 2^64 − 1 and
139646831 | 2^64 − 39). ∎

**Check.** `tests/test_proofs_modexp.py`, `ModulusTests`: the factorization of m − 1, the trial-division primality
of its factors, the Lucas conditions for g = 2, and a listed divisor of each of 2^64 − 58, …, 2^64 − 1.

**Cost model.** Residues are below m < 2^64, so each product of two residues is below 2^128 and each multiplication
with its reduction mod m is O(1) word operations; this is why the entry counts multiplications mod m. The single
reduction of the input base costs time linear in the size of a.

## 2. Repeated multiplication: correctness and exactly e multiplications

**Statement.** `modpow_repeated((a, e, m))` returns a^e mod m (1 for e = 0), using exactly e multiplications.
For n ≥ 1 this is between 2^(n−1) and 2^n − 1, so Θ(2^n) on every input of bit length n.

**Proof.** After the reduction, a ≡ a_input (mod m). Invariant: after k iterations r = a^k mod m (k = 0: r = 1).
An iteration replaces r by r · a mod m = a^(k+1) mod m. The loop runs e times with one multiplication each. ∎

**Space.** Besides the input, the function holds r and the reduced a (one word each) and the loop counter of
`range(e)`, which is below e and so has at most n bits: O(n) bits, i.e. O(1) words plus a counter as long as e.

**Check.** `tests/test_proofs_modexp.py`, `CountTests.test_repeated`: multiplications counted with an integer
subclass for every e < 2^10 (seeded bases), equal to e, and the result equal to `pow(a, e, m)`; the V2 exponents
e = 2^n − 1 for n = 1..16 (2^n − 1 multiplications).

## 3. Square-and-multiply: correctness and exactly n + popcount(e) multiplications

**Statement.** `modpow_square_multiply((a, e, m))` returns a^e mod m. For e ≥ 1 it makes exactly n squarings and
popcount(e) multiplications by a, at most 2n in total, so Θ(n). For e = 0 it makes one squaring (of r = 1) and
returns 1. On the V2 exponents e = 2^n − 1 it makes n squarings and n multiplications.

**Proof.** For e ≥ 1, `bin(e)[2:]` is the binary expansion b_1 b_2 … b_n of e, most significant bit first, with
b_1 = 1. Let k_j = Σ_(i≤j) b_i 2^(j−i) be the value of the first j bits, so k_0 = 0, k_(j+1) = 2k_j + b_(j+1) and
k_n = e. Invariant: after j characters r = a^(k_j) mod m. It holds for j = 0 (r = 1), and the next character
replaces r by r² · a^(b_(j+1)) ≡ a^(2k_j + b_(j+1)) (mod m). Each of the n characters costs one squaring, and each
'1' one multiplication by a. For e = 0, `bin(0)[2:]` is "0": one squaring of 1 and the result 1 = a^0. ∎

**Reading the bits.** We assume, as part of the machine model, that converting e to its binary string with `bin`
takes time linear in n. This is an assumption about the interpreter, not proved here; the entry states it in its
`background`.

**Space.** Besides r and a (one word each) the function holds the binary string of e (n + 2 characters, and its
slice of n characters) and the current character: O(n) bits.

**Check.** `tests/test_proofs_modexp.py`: `CountTests.test_square_multiply` (squarings and multiplications counted
separately for every e < 2^12, equal to n and popcount(e), one squaring for e = 0, results equal to `pow`; the V2
exponents e = 2^n − 1 for n = 1..64 and n = 1000, 2000, 4000, 8000, 16000, 32000, 64000 give n and n);
`SpaceTests.test_peak_memory` (the peak memory allocated during a call, measured with `tracemalloc`, is at most
3n + 1024 bytes for n = 1000..64000).

## 4. Lower bound in the addition-chain model

**Statement.** In the model where every step multiplies two powers of a computed earlier (starting from a; the
value 1 may also be available), computing a^e for e ≥ 1 takes at least ⌈log₂ e⌉ ≥ n − 1 multiplications.

**Proof.** A product of a^x and a^y is a^(x+y). By induction on the number s of multiplications, every exponent
computed after s multiplications is at most 2^s: true for s = 0 (exponents 0 and 1), and x + y ≤ 2 · 2^s. So a
method that ends with a^e after s multiplications has e ≤ 2^s, i.e. s ≥ log₂ e, and s is an integer, so
s ≥ ⌈log₂ e⌉. Since e ≥ 2^(n−1), ⌈log₂ e⌉ ≥ n − 1. ∎

**Check.** `tests/test_proofs_modexp.py`, `AdditionChainTests.test_doubling_bound`: every addition sequence with
s ≤ 6 steps (each new element the sum of two earlier ones, starting from 1; 56700 sequences at s = 6) has all
elements at most 2^s, so no e ≤ 128 is reached in fewer than ⌈log₂ e⌉ steps.

## 5. Caveats: within a factor 2 of the lower bound, and the cost of a larger modulus

**Statement (a).** For e ≥ 1, leave out the two trivial products of square-and-multiply, the squaring 1 · 1 and the
multiplication 1 · a made for the leading bit. The remaining products form an addition chain for e of length
(n − 1) + (popcount(e) − 1) ≤ 2(n − 1) ≤ 2⌈log₂ e⌉. Counting every executed multiplication, n + popcount(e) can
exceed 2⌈log₂ e⌉: e = 2 takes 3 multiplications and ⌈log₂ 2⌉ = 1.

**Proof.** By section 3 the leading bit b_1 = 1 costs the squaring 1 · 1 = 1 and the product 1 · a = a, whose
exponents 0 and 1 are the starting values of a chain. Each later bit j ≥ 2 doubles the current exponent (a sum of
an exponent with itself) and, if b_j = 1, adds the exponent 1 of a: n − 1 doublings and popcount(e) − 1 additions,
ending at k_n = e. Both counts are at most n − 1, and n − 1 ≤ ⌈log₂ e⌉ because e ≥ 2^(n−1). For e = 2 = "10":
squaring, multiplication, squaring, 3 in total. ∎

**Statement (b).** For a modulus of k bits, each multiplication with its reduction costs M(k) instead of O(1), so
both counts are multiplied by M(k); the counts themselves do not depend on m.

**Proof.** Sections 2 and 3 count multiplications without using the value of m. ∎

**Check.** `tests/test_proofs_modexp.py`, `AdditionChainTests.test_square_multiply_chain`: for every e < 2^12 the
exponents produced by square-and-multiply, without the two trivial products, form a valid addition chain for e of
length (n − 1) + (popcount(e) − 1) ≤ 2⌈log₂ e⌉; and e = 2 gives 3 counted multiplications.

## 6. Relationship

Repeated multiplication makes e multiplications, linear in the value of e and Θ(2^n) in its bit length (section 2).
Square-and-multiply makes n + popcount(e) ≤ 2n for e ≥ 1, Θ(n) (section 3). The V2 fits are measurements.
