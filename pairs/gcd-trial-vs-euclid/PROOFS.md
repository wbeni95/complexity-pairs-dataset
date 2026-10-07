# Proofs: greatest common divisor, trial divisors vs Euclid's algorithm

This file proves every claim of this entry (in `entry.json`, `README.md` and the docstrings of the code) from the
code in this folder: correctness, the exact iteration counts, the step and bit-operation bounds, the space bounds,
and the facts in the caveats. Statements about the literature are in the entry's `background` field and are not
claimed here; timing fits are measurements. Each section ends with the deterministic checks that re-run its
computable facts and the ranges they cover. A check covers only its range; the proofs cover every input.

## Conventions

- n is the bit length of max(a, b) (n = 0 only for a = b = 0). So a, b < 2^n, and max(a, b) ≥ 2^(n−1) for n ≥ 1.
- An **iteration** of trial divisors is one evaluation of the loop condition `a % d or b % d` in `gcd_trial`. A
  **division step** of Euclid is one execution of the loop body `a, b = b, a % b` in `gcd_euclid`.
- Fibonacci numbers: F_1 = F_2 = 1, F_(j+2) = F_(j+1) + F_j. φ = (1 + √5)/2, so φ² = φ + 1, and
  1/log₂ φ = 1.44042… < 1.4405.
- **Bit operations (schoolbook model).** Dividing x by y ≥ 1 with quotient q and remainder costs at least bitlen(x)
  bit operations (every bit of x is read) and at most c · (bitlen(q) + 2) · (bitlen(y) + 1) for a constant c: binary
  long division makes bitlen(x) − bitlen(y) + 1 ≤ bitlen(q) + 2 subtract-and-shift rounds on numbers of
  bitlen(y) + 1 bits (x < (q + 1) y gives bitlen(x) ≤ bitlen(q) + 1 + bitlen(y)). Tests, assignments and the
  `while` check cost O(n) per step. Here bitlen(0) = 0.

## 1. Trial divisors: correctness

**Statement.** For all integers a, b ≥ 0, `gcd_trial((a, b))` returns gcd(a, b), with gcd(a, 0) = a and
gcd(0, 0) = 0.

**Proof.** If a = 0 or b = 0 the function returns a + b. For a ≥ 1, gcd(a, 0) = a, since every integer divides 0
and the largest divisor of a positive integer is the integer itself; gcd(0, b) = b likewise, and gcd(0, 0) = 0 is
the convention of the problem statement. Otherwise a, b ≥ 1 and d starts at min(a, b). The loop condition
`a % d or b % d` is false exactly when d divides both a and b, so the loop stops at the first such d in the order
min(a, b), min(a, b) − 1, …. It stops at the latest at d = 1, which divides everything; so d ≥ 1 throughout and no
division by zero occurs. Every positive common divisor of a and b is at most min(a, b), since a positive divisor of
a positive integer is at most that integer. So the first common divisor met scanning downwards from min(a, b) is
the greatest one. ∎

**Check.** The V1 run (`python tools/validate.py pairs/gcd-trial-vs-euclid`): random pairs, n = 0..16, oracle
`math.gcd`. `tests/test_proofs_gcd.py`, `TrialDivisorTests.test_exact_iteration_count`: every pair
0 ≤ a, b ≤ 80, returned value equal to `math.gcd`.

## 2. Trial divisors: exact iteration count, maximum, the V2 Fibonacci pairs

**Statement.**
(a) For a, b ≥ 1 the loop condition is evaluated exactly min(a, b) − gcd(a, b) + 1 times, and the number of
divisions is that count plus the number of d in [gcd(a, b), min(a, b)] that divide a (each iteration computes
`a % d`, and `b % d` only when `a % d` is 0). For a = 0 or b = 0 there is no iteration.
(b) Over all inputs with max(a, b) of bit length n, the maximum number of iterations is 2^n − 2 for n ≥ 2, attained
by the coprime pair (2^n − 1, 2^n − 2) (in either order), and 1 for n = 1. So the worst case is Θ(2^n), and every
input needs at most min(a, b) iterations (linear in the value).
(c) For n ≥ 1, `harness.generate_scaling(n, rng)` returns (F_(k+1), F_k) with F_(k+1) < 2^n ≤ F_(k+2) and k ≥ 1;
F_(k+1) has bit length exactly n; gcd(F_(k+1), F_k) = 1; and trial divisors make exactly F_k iterations, with
F_k ≥ 2^n/3 > 2^(n−2).
(d) In bit operations trial divisors cost O(2^n · n²) on every input below 2^n: at most 2^n iterations, each with at
most two divisions of numbers below 2^n.

**Proof.** (a) By section 1 the condition is evaluated for d = min(a, b), …, g = gcd(a, b): min(a, b) − g + 1
values. Python evaluates `x or y` by computing x and, only if x is false (here: `a % d == 0`), also y.

(b) If a = 0 or b = 0 there are 0 iterations. If a = b ≥ 1, then g = a and there is 1 iteration. If a ≠ b, both
≥ 1, then min(a, b) ≤ max(a, b) − 1 ≤ 2^n − 2 and g ≥ 1, so at most 2^n − 2 iterations. Consecutive integers are
coprime (a common divisor divides their difference 1), so (2^n − 1, 2^n − 2) needs exactly 2^n − 2 iterations, and
2^n − 2 ≥ 2 > 1 for n ≥ 2. For n = 1 the inputs are (1, 0), (0, 1), (1, 1), with at most 1 iteration. In all cases
min(a, b) − g + 1 ≤ min(a, b).

(c) The generator starts with (a, b) = (1, 1) = (F_2, F_1) and replaces (F_(j+1), F_j) by (F_(j+2), F_(j+1)) while
F_(j+2) = a + b < 2^n. It stops at the first k ≥ 1 with F_(k+2) ≥ 2^n. Then F_(k+1) < 2^n: for k = 1 because
F_2 = 1 < 2^n, otherwise because the last replacement required F_(k+1) < 2^n. Since F_k ≤ F_(k+1),
F_(k+1) ≥ F_(k+2)/2 ≥ 2^(n−1), so its bit length is n. gcd(F_(j+1), F_j) = gcd(F_j, F_(j+1) − F_j) =
gcd(F_j, F_(j−1)) = … = gcd(F_2, F_1) = 1. Next, F_(k+1) ≤ 2F_k (for k ≥ 2, F_(k+1) = F_k + F_(k−1) and
F_(k−1) ≤ F_k; for k = 1, 1 ≤ 2), so F_(k+2) = F_(k+1) + F_k ≤ 3F_k and F_k ≥ F_(k+2)/3 ≥ 2^n/3 > 2^n/4. By (a),
the number of iterations is F_k − 1 + 1 = F_k.

(d) Each division has dividend a or b (< 2^n) and divisor d ≤ min(a, b) < 2^n, so its quotient is below 2^n and it
costs O(n²) in the schoolbook model; by (b) there are at most 2^n iterations with at most two divisions each. ∎

**Check.** `tests/test_proofs_gcd.py`, class `TrialDivisorTests`. `test_exact_iteration_count`: iterations and
divisions counted by integer subclasses that count every `%` on a and on b, compared with (a) for every pair
0 ≤ a, b ≤ 80 and 300 seeded random pairs below 2^12. `test_maximum_over_n_bit_inputs`: exhaustive maxima for
n = 1..7. `test_fibonacci_pairs`: the generator output and the inequalities of (c) for n = 1..300 (exact integer
arithmetic), and counted iterations equal to F_k for n = 1..16.

## 3. Trial divisors: space

**Statement.** `gcd_trial` uses O(n) bits.

**Proof.** Besides the input it holds d ≤ min(a, b) < 2^n and the remainders a % d, b % d < d: a constant number of
integers of at most n bits. ∎

**Check.** `tests/test_proofs_gcd.py`, `SpaceTests.test_locals_have_at_most_n_bits`: every integer local of
`gcd_trial`, at every executed line (traced with `sys.settrace`), has at most n bits, on 40 seeded pairs with
n ≤ 12.

## 4. Euclid's algorithm: correctness

**Statement.** For all a, b ≥ 0, `gcd_euclid((a, b))` returns gcd(a, b).

**Proof.** For b ≥ 1 write a mod b = a − qb with q = ⌊a/b⌋. A common divisor of a and b divides a − qb, and a
common divisor of b and a − qb divides a = (a − qb) + qb; so (a, b) and (b, a mod b) have the same common
divisors and the same gcd. Hence the gcd of the current pair never changes. Each step replaces b by a mod b < b,
so b strictly decreases and the loop ends, with b = 0. It then returns a = gcd(a, 0), which is the gcd of the input
pair. For the input (0, 0) the loop does not run and 0 is returned. ∎

**Check.** The V1 run: random pairs with n = 0..16, 32, 64, 256, 1024, 4096 (oracle `math.gcd`), including zeros
and large common factors. `tests/test_proofs_gcd.py`, `EuclidTests.test_step_bounds`: every pair 0 ≤ a, b < 2^8.

## 5. Euclid's algorithm: number of division steps (after Lamé 1844)

Write r_0 = a, r_1 = b and r_(i+1) = r_(i−1) mod r_i while r_i ≠ 0; the number of steps k is the least index with
r_(k+1) = 0 (k = 0 iff b = 0). Let q_i = ⌊r_(i−1)/r_i⌋, so r_(i−1) = q_i r_i + r_(i+1) with 0 ≤ r_(i+1) < r_i
(1 ≤ i ≤ k).

**Lemma 5.1.** If b ≥ 1, then r_i ≥ F_(k+2−i) for 1 ≤ i ≤ k; in particular b ≥ F_(k+1). If moreover a > b, then
a ≥ F_(k+2).

*Proof.* r_1 > r_2 > … > r_k ≥ 1 and r_(k+1) = 0. So r_k ≥ 1 = F_2. If k ≥ 2, then r_k divides r_(k−1)
(the remainder r_(k+1) is 0) and r_(k−1) > r_k, so r_(k−1) ≥ 2r_k ≥ 2 = F_3. For 2 ≤ i ≤ k − 1, r_(i−1) > r_i gives
q_i ≥ 1, so r_(i−1) ≥ r_i + r_(i+1) ≥ F_(k+2−i) + F_(k+1−i) = F_(k+3−i). Downward induction gives the claim for
i = k, k − 1, …, 1. If a > b, then q_1 ≥ 1 and a ≥ r_1 + r_2, which is ≥ F_(k+1) + F_k = F_(k+2) for k ≥ 2; for
k = 1, a > b ≥ 1 gives a ≥ 2 = F_3. ∎

**Theorem 5.2 (step bound).** If a ≥ b ≥ 1, then k ≤ log_φ b + 1. If 1 ≤ a < b, then k ≤ log_φ a + 2. If b = 0,
k = 0; if a = 0 < b, k = 1. Hence k ≤ log_φ(min(a, b)) + 2 whenever min(a, b) ≥ 1, and k ≤ log_φ(2^n) + 2
< 1.4405 n + 2 for every input with max(a, b) < 2^n.

*Proof.* F_j ≥ φ^(j−2) for j ≥ 1: F_1 = 1 ≥ φ^(−1), F_2 = 1 = φ^0, and F_(j+1) = F_j + F_(j−1) ≥
φ^(j−2) + φ^(j−3) = φ^(j−3)(φ + 1) = φ^(j−1). If a ≥ b ≥ 1, Lemma 5.1 gives b ≥ F_(k+1) ≥ φ^(k−1). If 1 ≤ a < b,
the first step gives r_2 = a mod b = a, so the remaining k − 1 ≥ 1 steps run on (b, a) with b > a ≥ 1, and Lemma
5.1 for that pair gives a ≥ F_k ≥ φ^(k−2). If a = 0 < b, one step gives (b, 0). For the last claim, min(a, b) < 2^n,
log_φ(2^n) = n/log₂ φ < 1.4405 n, and the cases with min(a, b) = 0 need at most one step. ∎

**Theorem 5.3 (consecutive Fibonacci numbers are the worst case).** For j ≥ 2 the pair (F_(j+1), F_j) needs
exactly j − 1 steps, with every quotient equal to 1 except the last, which is 2. By Lemma 5.1, among the pairs
a > b ≥ 1 that need k steps, (F_(k+2), F_(k+1)) has both the smallest a and the smallest b. For n ≥ 2 the V2 pair
(F_(k+1), F_k) of bit length n (section 2(c)) has k ≥ 3, and its number of steps k − 1 satisfies
n/log₂ φ − 2 ≤ k − 1 < n/log₂ φ, so it is 1.44 n + O(1). (For n = 1 the pair is (1, 1), one step.)

*Proof.* For j ≥ 3, F_(j+1) = 1 · F_j + F_(j−1) with 0 ≤ F_(j−1) < F_j, so one step with quotient 1 leads to
(F_j, F_(j−1)). For j = 2 the pair is (2, 1), and one step with quotient 2 leads to (1, 0). So there are j − 1 steps.
For n ≥ 2 the generator passes (2, 1) and (3, 2) = (F_4, F_3) because 2 + 1 < 2^n, so k ≥ 3 and the first claim
applies with j = k. F_j ≤ φ^(j−1) for j ≥ 1 (F_1 = 1, F_2 = 1 ≤ φ, F_(j+1) ≤ φ^(j−1) + φ^(j−2) = φ^j). From
2^n ≤ F_(k+2) ≤ φ^(k+1), k + 1 ≥ n/log₂ φ. From φ^(k−1) ≤ F_(k+1) < 2^n, k − 1 < n/log₂ φ. ∎

**Corollary 5.4 (decimal form).** If a ≥ b ≥ 1 and b has D decimal digits, then
k ≤ 5D.

*Proof.* F_(m+5) = 8F_m + 5F_(m−1) (expand the recurrence five times), and F_m ≤ 2F_(m−1) < 2.5F_(m−1) for m ≥ 2,
so F_(m+5) > 10F_m for m ≥ 2. By induction on D, F_(5D+2) > 10^D F_2 = 10^D. If k ≥ 5D + 1, Lemma 5.1 would give
b ≥ F_(k+1) ≥ F_(5D+2) > 10^D, contradicting b < 10^D. ∎

**Check.** `tests/test_proofs_gcd.py`, class `EuclidTests` (steps counted by an integer subclass that counts every
`%`). `test_step_bounds`: every pair 0 ≤ a, b < 2^8: the inequalities of Lemma 5.1, Theorem 5.2 (in the exact form
b ≥ F_(k+1), a ≥ F_k for a < b) and Corollary 5.4. `test_fibonacci_pairs`: steps and quotients on (F_(j+1), F_j)
for j = 2..400, the V2 pairs for n = 2..300 and n = 4000, 8000, 16000, 32000, 64000 (steps k − 1 and the bounds of
Theorem 5.3), and one step for n = 1.

## 6. Euclid's algorithm: bit operations

**Statement.** With schoolbook division Euclid costs O(n²) bit operations on every input with max(a, b) < 2^n, and
Θ(n²) on the V2 Fibonacci pairs.

**Proof.** Step i divides r_(i−1) by r_i, both below 2^n, with quotient q_i, at cost at most
c (bitlen(q_i) + 2)(n + 1), plus O(n) for the assignment and the test. Now bitlen(q) ≤ log₂ max(q, 1) + 1, and the
quotients that are ≥ 1 multiply to at most max(a, b): for i ≥ 2, q_i ≤ r_(i−1)/r_i, so q_2 ⋯ q_k ≤ r_1/r_k ≤ r_1;
if also q_1 ≥ 1, then q_1 ≤ r_0/r_1 and q_1 ⋯ q_k ≤ r_0. (Only q_1 can be 0, when a < b.) Hence
Σ_i log₂ max(q_i, 1) ≤ log₂ max(a, b) < n, and the total is at most c (n + 1)(3k + n) + O(nk) = O(n²), since
k = O(n) by Theorem 5.2.

On (F_(k+1), F_k), the step that divides F_(j+1) by F_j (j = k, …, 2) reads F_(j+1), which has at least
log₂ F_(j+1) ≥ (j − 1) log₂ φ bits. The total is at least log₂ φ · Σ_(j=2..k) (j − 1) = log₂ φ · k(k − 1)/2, and
k ≥ n/log₂ φ − 1 by Theorem 5.3, which is Ω(n²). ∎

**Check.** `tests/test_proofs_gcd.py`, `EuclidTests.test_quotient_product`: Π max(q_i, 1) ≤ max(a, b) and
Σ (bitlen(q_i) + 2) ≤ 3k + n on every pair below 2^8 and on 200 seeded random pairs of 64 to 4096 bits.

## 7. Euclid's algorithm: space

**Statement.** `gcd_euclid` uses O(n) bits.

**Proof.** It holds a, b and a % b, all below 2^n (after the first step the pair is (b, a mod b) with
a mod b < b). ∎

**Check.** `tests/test_proofs_gcd.py`, `SpaceTests.test_locals_have_at_most_n_bits`: every integer local of
`gcd_euclid` has at most n bits at every executed line, on 40 seeded pairs with n ≤ 4096.

## 8. Relationship and caveats

- *Trial divisors are linear in the value min(a, b) and Θ(2^n) in the bit length:* section 2(a), (b).
- *Euclid: O(n) division steps and O(n²) bit operations, polynomial in the input size:* sections 5 and 6.
- *Euclid's O(n²) bit cost assumes schoolbook division:* section 6 uses that model. Faster gcd algorithms are
  background (cited, not claimed).
- *V2:* the timing fits of both algorithms are measurements. The step count of section 5 is not timed; it is
  proved above and counted exactly by the tests.
