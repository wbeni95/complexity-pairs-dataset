# Proofs: primality testing, trial division vs AKS

This file proves every claim of this entry (in `entry.json`, `README.md` and the docstrings of the code) from the
code in this folder:

- Part T: trial division (correctness, exact division counts, the Θ(2^(n/2)) worst case, space);
- Part A: the AKS implementation in `implementations/aks.py` (it returns True iff N is prime, for every N; its
  parameter r is O(n^5); polynomial running time and space; a lower bound on primes, used by
  `primality-miller-rabin-vs-aks`);
- Part H: the facts about the harness that the verification relies on;
- Part B: Bertrand's postulate, used in Part T.

The proof of Part A follows the structure of the argument of Agrawal, Kayal and Saxena (2004); the written
argument below is complete and is checked against the code as it stands. Faster analyses and variants, and
statements about the literature, are in the entry's `background` field and are not claimed. Each section ends with
the deterministic checks that re-run its computable facts and their ranges; a check covers only its range.

## Conventions

N ≥ 0 is the input, n = bitlen(N) its bit length, so 2^(n−1) ≤ N < 2^n for N ≥ 1, and L = log₂ N for N ≥ 1, so
n − 1 ≤ L < n. φ is Euler's function. ord_r(N) is the multiplicative order of N modulo r, for gcd(r, N) = 1.

**Cost models.** *Schoolbook:* adding x-bit and y-bit integers costs O(x + y) bit operations; multiplying them
O(xy); dividing an x-bit number by a y-bit number with remainder O(xy); a gcd of two numbers below 2^n is charged
O(n²), the bound proved for Euclid's algorithm in `gcd-trial-vs-euclid/PROOFS.md`, section 6; conversions between
integers and byte strings, slicing and list operations cost time linear in their size. *Fast arithmetic:* the same,
except that multiplication and division with remainder of m-bit integers cost Õ(m), where Õ hides factors
polylogarithmic in m. Both are cost models for the operations the code performs; the cost of the interpreter's own
integer routines is not analysed here.

## Part T: trial division

### T.1 Correctness

**Statement.** `is_prime_trial(N)` returns True iff N is prime, for every N ≥ 0.

**Proof.** N < 2 is not prime and gives False. For even N the function returns N == 2, which is correct. Let N ≥ 3
be odd. If N is composite, its smallest prime factor p satisfies p² ≤ N (N = p·m with m ≥ p) and p is odd, so the
loop reaches d = p (it runs over the odd d ≥ 3 with d² ≤ N) unless it returned False earlier, and N % p == 0 gives
False. If N is prime, no d with 3 ≤ d ≤ √N < N divides N, so the loop ends and the function returns True. ∎

### T.2 Exact division counts

Count the evaluations of `N % 2` and `N % d`.

**Statement.** On an odd prime N the function makes exactly D(N) = 1 + ⌊(⌊√N⌋ − 1)/2⌋ divisions. On every other
N ≥ 2 it makes at most D(N) divisions: 1 for even N, and 1 + (p − 1)/2 ≤ D(N) for odd composite N with smallest
prime factor p. For every n-bit N, D(N) < 1 + 2^(n/2 − 1); for every n-bit prime N ≥ 3,
D(N) ≥ ⌊√N⌋/2 ≥ (2^((n−1)/2) − 1)/2.

**Proof.** The loop tests d = 3, 5, …, while d² ≤ N, one division each, and stops early only at a divisor. On an
odd prime it runs over all odd d with 3 ≤ d ≤ ⌊√N⌋, of which there are ⌊(⌊√N⌋ − 1)/2⌋; add the test `N % 2`. On an
odd composite it stops at d = p, after (p − 1)/2 loop divisions, and p ≤ ⌊√N⌋. Bounds:
D(N) ≤ 1 + (√N − 1)/2 < 1 + 2^(n/2)/2. For a prime N ≥ 3, D(N) ≥ 1 + (⌊√N⌋ − 2)/2 = ⌊√N⌋/2, and
⌊√N⌋ > √N − 1 ≥ 2^((n−1)/2) − 1. ∎

### T.3 The worst case is Θ(2^(n/2))

**Statement.** For every n ≥ 2, the maximum number of divisions over n-bit inputs lies between
(2^((n−1)/2) − 1)/2 and 1 + 2^(n/2 − 1), and every n-bit prime needs at least the lower bound. So the worst case is
Θ(√N) = Θ(2^(n/2)), reached up to a constant factor on every prime.

**Proof.** The upper bound holds for every n-bit N by T.2. By Bertrand's postulate (Part B) with m = 2^(n−1) there
is a prime p with 2^(n−1) < p ≤ 2^n; p ≠ 2^n because n ≥ 2, so p has n bits, and T.2 gives the lower bound for it
and for every other n-bit prime. ∎

### T.4 Polynomial in the value N; space

Trial division makes at most 1 + √N/2 divisions of numbers at most N, so it is polynomial in the value N
(O(√N log² N) bit operations in the schoolbook model), while N is exponential in the input length n. It stores N, d
(at most √N + 2, since (d − 2)² ≤ N, so at most n/2 + 2 bits) and d·d: O(n) bits.

**Check (Part T).** `tests/test_proofs_primality.py`, class `TrialDivisionTests`: correctness for every N < 2^16
against an independent sieve; divisions counted with an integer subclass equal D(N) on every odd prime below 2^14
and are at most D(N) on every N in [2, 2^14); the bounds of T.2 for every prime below 2^16; the lower bound on the
seeded V2 instances (n = 26..40, all prime, see H.3); and `test_locals_have_O_n_bits` (every integer local has at
most n + 2 bits, traced with `sys.settrace`, on 200 seeded N with n ≤ 24). Timing data (V2-style fit of 2^(n/2))
are measurements.

## Part A: the AKS implementation

### A.0 What the code does

`is_prime_aks(N)`:

0. N < 2: return False.
1. If `_is_perfect_power(N)` (N = a^b with a ≥ 2, b ≥ 2): return False.
2. (A, J) = `_log2_upper(N)` with J = 64, and λ = A/2^J. K = `(A*A) >> (2*J)` = ⌊A²/4^J⌋ = ⌊λ²⌋. Find the least
   r ≥ 2 with gcd(r, N) = 1 and `_order_exceeds(N, r, K)`.
3. For a = 2, …, min(r, N − 1): if 1 < gcd(a, N) < N, return False.
4. If N ≤ r: return True.
5. ℓ = `isqrt(phi(r) * A * A) >> J`. For a = 1, …, ℓ: if `_pow_x_plus_a(a, N, r)` differs from the coefficient
   list of X^N + a, return False.
6. Return True.

Since ⌊⌊y⌋/q⌋ = ⌊y/q⌋ for real y ≥ 0 and integers q ≥ 1, ℓ = ⌊⌊√(φ(r)A²)⌋/2^J⌋ = ⌊√φ(r) · λ⌋. With log₂ N in
place of λ the bounds would be ⌊log₂² N⌋ and ⌊√φ(r) log₂ N⌋. Lemma A1 shows log₂ N ≤ λ ≤ n, and the proof below
works for any such λ. So the code computes the floors of λ² and √φ(r)·λ exactly; since λ may exceed log₂ N, K and
ℓ can exceed ⌊log₂² N⌋ and ⌊√φ(r) log₂ N⌋, which the proof allows. For example N = 229533671885360152 (58 bits)
has log₂² N = 3325.99999999999999999779… and K = 3326. On every N < 2^16 the code's K, r and ℓ equal those computed
with the exact log₂ N, and K does for every N < 2^20 (see the check of A1). A floating-point log₂ could instead
give values *below* those with log₂ N, which the proof does not allow; this is why the code uses λ.

### A.1 The upper bound λ

**Lemma A1.** For every N ≥ 1 and J ≥ 1, `_log2_upper(N, J)` returns (A, J) with log₂ N ≤ A/2^J ≤ n.

**Proof.** Let e = n − 1 and y = N/2^e ∈ [1, 2), and P = J + 64. Write ⌈·⌉ for the ceiling; the code computes
ceilings exactly, since −((−x) >> k) = ⌈x/2^k⌉ for integers x. Put u_0 = Y_0/2^P with Y_0 = ⌈y · 2^P⌉, and let
u_i = Y_i/2^P be the value after step i. In step i the code computes Y′ = ⌈Y_(i−1)²/2^P⌉, so v = Y′/2^P ≥ u_(i−1)²;
if Y′ ≥ 2^(P+1) (v ≥ 2) it records digit b_i = 1 and sets Y_i = ⌈Y′/2⌉, so u_i ≥ v/2; otherwise b_i = 0 and
u_i = v. In both cases u_i ≥ u_(i−1)²/2^(b_i), i.e. log₂ u_(i−1) ≤ (b_i + log₂ u_i)/2. All u_i are ≥ 1: u_0 ≥ y ≥ 1,
and u_i ≥ v ≥ u_(i−1)² ≥ 1 if b_i = 0, u_i ≥ v/2 ≥ 1 if b_i = 1. Also u_i ≤ 2 for all i: Y_0 ≤ 2^(P+1) since y < 2; if
Y_(i−1) ≤ 2^(P+1), then Y′ ≤ 2^(P+2), and either Y_i = ⌈Y′/2⌉ ≤ 2^(P+1) or Y_i = Y′ < 2^(P+1). Iterating the
inequality J times, log₂ y ≤ log₂ u_0 ≤ Σ_(i=1..J) b_i 2^(−i) + 2^(−J) log₂ u_J ≤ bits/2^J + 2^(−J), where bits is the
integer with binary digits b_1 … b_J. So log₂ N = e + log₂ y ≤ (e·2^J + bits + 1)/2^J = A/2^J. Finally
bits ≤ 2^J − 1 gives A ≤ (e + 1) 2^J = n 2^J. ∎

**Check.** `tests/test_proofs_primality.py`, `AKSParameterTests.test_log2_upper`: 2^A ≥ N^(2^J) and A ≤ n 2^J exactly
for J = 1, 2, 3, 5, 8 and every N < 4096 plus 200 seeded N of 13 to 400 bits; for J = 64, A ≤ n 2^64 and
A/2^64 − log₂ N ≥ 0 by 80-digit decimal arithmetic on the same N. `experiments/2026-10-07_primality_proof_checks.py`
(part 1): the code's K equals ⌊log₂² N⌋ for every N in [2, 2^20), and its r and ℓ equal the values from the exact
log₂ N for every N in [2, 2^16) (exact decimal arithmetic with a certified margin); and K = ⌊log₂² N⌋ + 1 for
N = 229533671885360152.

### A.2 A lower bound on lcm(1, …, m)

**Lemma A2 (credit: Nair 1982).** For every integer m ≥ 7, d_m := lcm(1, …, m) ≥ 2^m.

**Proof.** For integers 1 ≤ k ≤ m let I(k, m) = ∫₀¹ x^(k−1)(1 − x)^(m−k) dx. Expanding (1 − x)^(m−k) binomially,
I(k, m) = Σ_(j=0..m−k) (−1)^j C(m−k, j)/(k + j), and every k + j lies in [1, m], so d_m · I(k, m) is an integer.
On the other hand, for a real y, Σ_(k=1..m) C(m−1, k−1) y^(k−1) I(k, m) = ∫₀¹ (1 − x + xy)^(m−1) dx
= (y^m − 1)/(m(y − 1)) = (1 + y + … + y^(m−1))/m, and comparing coefficients of y^(k−1) gives
I(k, m) = 1/(m C(m−1, k−1)) = 1/(k C(m, k)). Hence k C(m, k) divides d_m for all 1 ≤ k ≤ m. With m = 2s and k = s,
s C(2s, s) | d_(2s), which divides d_(2s+1); with m = 2s + 1 and k = s + 1, (s + 1) C(2s+1, s+1) = (2s + 1) C(2s, s)
divides d_(2s+1). As gcd(s, 2s + 1) = 1, s(2s + 1) C(2s, s) divides d_(2s+1). Since C(2s, s) is the largest of the
2s + 1 binomial coefficients C(2s, j), which sum to 4^s, (2s + 1) C(2s, s) ≥ 4^s and d_(2s+1) ≥ s 4^s. For s ≥ 2,
s 4^s ≥ 2^(2s+1), which covers odd m ≥ 5; for s ≥ 4, d_(2s+2) ≥ d_(2s+1) ≥ s 4^s ≥ 2^(2s+2), which covers even
m ≥ 10; and d_8 = 840 ≥ 2^8. ∎

**Check.** `AKSLemmaTests.test_nair`: k C(m, k) | d_m for all 1 ≤ k ≤ m ≤ 300, and d_m ≥ 2^m for 7 ≤ m ≤ 2000.

### A.3 Step 2 terminates, with r = O(n^5)

**Lemma A3.** Let N ≥ 2, λ ≥ log₂ N with λ ≥ 1, K = ⌊λ²⌋ and B = max(16, ⌈λ(K + 1)²⌉). Some r with 2 ≤ r ≤ B has
gcd(r, N) = 1 and ord_r(N) > K. Consequently step 2 stops with r ≤ B ≤ R(n) := max(16, n(n² + 1)²).

**Proof.** *Two inequalities.* Since K + 1 > λ², B ≥ λ(K + 1)² > λ⁵, so λ < B^(1/5). For B ≥ 16,
log₂ B ≤ B^(4/5)/2 (at B = 16: 4 < 4.59; and B^(4/5)/2 − log₂ B is increasing for B ≥ 5 because its derivative
0.4 B^(−1/5) − 1/(B ln 2) is positive there), so λ⌊log₂ B⌋ ≤ B^(1/5) log₂ B ≤ B/2. Also
λ K(K + 1)/2 ≤ λ(K + 1)²/2 ≤ B/2. So λ(⌊log₂ B⌋ + K(K + 1)/2) ≤ B.

*Existence.* Suppose that every r in [2, B] with gcd(r, N) = 1 has ord_r(N) ≤ K. Let Π = Π_(i=1..K) (N^i − 1),
a positive integer (N ≥ 2, and K ≥ 1 since λ ≥ 1). Let q^e ≤ B be a prime power. If q ∤ N, then q^e ∈ [2, B] is
coprime to N, so o = ord_(q^e)(N) ≤ K and q^e | N^o − 1 | Π. If q | N, then q^e | N^e, and 2^e ≤ q^e ≤ B gives
e ≤ ⌊log₂ B⌋, so q^e | N^⌊log₂ B⌋. Either way q^e | N^⌊log₂ B⌋ Π. Now d_B = Π_q q^(e_q), with q^(e_q) the largest power
of q not above B, is a product of pairwise coprime divisors of N^⌊log₂ B⌋ Π, hence divides it. By Lemma A2 (B ≥ 16),
2^B ≤ d_B ≤ N^⌊log₂ B⌋ Π < N^(⌊log₂ B⌋ + K(K+1)/2) ≤ 2^(λ(⌊log₂ B⌋ + K(K+1)/2)) ≤ 2^B, a contradiction.

*The code.* With x = N^k mod r after k iterations, `_order_exceeds(N, r, K)` returns False iff N^k ≡ 1 (mod r)
for some 1 ≤ k ≤ K, i.e. (when gcd(r, N) = 1) iff ord_r(N) ≤ K. Step 2 tries r = 2, 3, … in turn and stops at the
first r with gcd(r, N) = 1 and ord_r(N) > K, so at some r ≤ B. With λ ≤ n (Lemma A1), K + 1 ≤ n² + 1 and
B ≤ max(16, n(n² + 1)²) = R(n). ∎

**Check.** `AKSLemmaTests.test_order_lemma`: for every N in [2, 2^12) and 300 seeded N of 15 to 20 bits, the r of
step 2 has gcd(r, N) = 1, ord_r(N) > K, and r ≤ max(16, ⌈λ(K + 1)²⌉) ≤ R(n); and B^(1/5) log₂ B ≤ B/2 for
B = 16, 1013, 2010, … (step 997) below 10^6. (The r of the test's re-computation of step 2 equals the code's r on
every N < 600 that reaches step 2: `AKSCorrectnessTests.test_small_N`.)
`experiments/2026-10-07_primality_proof_checks.py` (part 1): the largest r over N < 2^16 is 557.

### A.4 Steps 1, 3 and 4

**Lemma A4.** (a) `_iroot(N, b)` returns ⌊N^(1/b)⌋ for N ≥ 1, b ≥ 1. (b) `_is_perfect_power(N)` is True iff N = a^b
for some integers a ≥ 2, b ≥ 2. (c) If step 3 returns False, N is composite; if N is prime, step 3 does not return.
(d) If step 4 returns True, N is prime. (e) `_totient(r)` returns φ(r) for every r ≥ 1.

**Proof.** (a) Binary search with the invariant lo ≤ ⌊N^(1/b)⌋ ≤ hi: initially lo = 1 ≤ N^(1/b), and
N < 2^n ≤ 2^(b(⌊n/b⌋+1)) = hi^b gives ⌊N^(1/b)⌋ < hi. With mid = ⌈(lo + hi)/2⌉ > lo: if mid^b ≤ N then
mid ≤ ⌊N^(1/b)⌋ and lo becomes mid; otherwise ⌊N^(1/b)⌋ ≤ mid − 1, which becomes hi. hi − lo decreases, and at the
end lo = hi = ⌊N^(1/b)⌋. (b) If N = a^b with a, b ≥ 2, then 2^b ≤ N < 2^n gives b < n, so b is tried, and
`_iroot(N, b)` = a with a^b = N. Conversely True is returned only when a > 1 and a^b = N with b ≥ 2. (c) A value
1 < gcd(a, N) < N is a proper divisor of N. For a prime N, gcd(a, N) ∈ {1, N} for every a. (d) Suppose N ≤ r and
N is composite. Its smallest prime factor p satisfies 2 ≤ p ≤ N − 1 and p ≤ r, so a = p is tried in step 3
(a ranges up to min(r, N − 1)), and gcd(p, N) = p ∈ (1, N): step 3 returns False before step 4. (e) Invariant when p
is tested: m is r with all prime factors below p divided out, and `result` = r Π (1 − 1/q) over the primes q < p
dividing r. If p divides m, p is prime (m has no smaller prime factor) and divides r/Π q, which divides `result`,
so `result -= result // p` multiplies `result` by exactly 1 − 1/p; then all factors p are removed from m. The loop
stops when p² > m, so the remaining m is 1 or a single prime q (two prime factors, both ≥ p, would give p² ≤ m),
not yet used, and the last line applies 1 − 1/q in the same way. So `result` = r Π_(q | r) (1 − 1/q) = φ(r), by
inclusion–exclusion over the prime divisors of r. ∎

**Check.** `AKSLemmaTests.test_totient`: `_totient(r)` equals φ(r) from an independent sieve for every r < 20000, and
the count of k ≤ r with gcd(k, r) = 1 for every r < 1000.

### A.5 The polynomial arithmetic of the code

Elements of Z_N[X]/(X^r − 1) are represented by lists of r coefficients in [0, N − 1] (coefficient i of X^i); this
representation is unique.

**Lemma A5.** Let N ≥ 2 and r ≥ 1. (a) For a list P of r integers in [0, N − 1], `_square_mod(P, r, N)` returns the
representation of P(X)² mod (X^r − 1, N). (b) The list comprehension in `_pow_x_plus_a` returns the representation
of (X + a) · P(X). (c) `_pow_x_plus_a(a, N, r)` returns the representation of (X + a)^N mod (X^r − 1, N). (d) In
step 5 (where gcd(r, N) = 1, r ≥ 2 and 1 ≤ a ≤ ℓ < r < N; ℓ ≤ √φ(r) λ < φ(r) < r because
φ(r) ≥ ord_r(N) > λ², and r < N after step 4), `rhs` is the representation of X^N + a. So step 5 returns
False iff (X + a)^N ≢ X^N + a (mod X^r − 1, N) for some 1 ≤ a ≤ ℓ.

**Proof.** (a) Let wb be the computed number of bytes and w = 8·wb, so r(N − 1)² < 2^w. The packed integer is
Σ_i P_i 2^(wi), each P_i < N ≤ 2^w. Its square is Σ_k s_k 2^(wk) with s_k = Σ_(i+j=k) P_i P_j for 0 ≤ k ≤ 2r − 2;
there are at most r pairs (i, j) with i + j = k, so 0 ≤ s_k ≤ r(N − 1)² < 2^w, and s_k is exactly the k-th base-2^w
digit of the square. The square is below 2^(w(2r−1)), so it fits in the 2r·wb bytes, and the code reads
c_k = s_k (c_(2r−1) = 0). Since X^(i+r) ≡ X^i, the reduced coefficients are (c_i + c_(i+r)) mod N. (b) (X + a)P(X) =
Σ_i (a P_i + P_(i−1)) X^i + P_(r−1) X^r with X^r ≡ 1; Python's P[−1] is P[r − 1], so coefficient i is
(a P_i + P_(i−1)) mod N. (c) Let b_1 … b_n be the bits of N (most significant first) and k_j the value of the first
j bits. Invariant: after j bits P represents (X + a)^(k_j); it holds for j = 0 (P = 1), and a bit replaces P by P²
and then, if the bit is 1, by (X + a)P², which represents (X + a)^(2k_j + b_(j+1)) by (a), (b). After n bits,
k_n = N. (d) X^N ≡ X^(N mod r) mod X^r − 1, and N mod r ≠ 0 because gcd(r, N) = 1 and r ≥ 2; so the code's list has
1 at position N mod r and (0 + a) mod N = a at position 0, which is the representation of X^N + a. ∎

**Check.** `AKSArithmeticTests`: `_square_mod` equals a direct cyclic convolution mod N on 2000 seeded lists with
r = 1..40 and N in {2, 3, 7, 255, 65537, 2^61 − 1, 10^30 + 57}; `_pow_x_plus_a` equals repeated multiplication by
X + a for every N in [2, 40], r in [1, 10] and a in [0, 3].

### A.6 Primes pass step 5

**Lemma A6.** If N is prime, (X + a)^N ≡ X^N + a (mod X^r − 1, N) for every integer a and r ≥ 1.

**Proof.** In Z_N[X], (X + a)^N = Σ_i C(N, i) a^(N−i) X^i, and N divides C(N, i) = N!/(i!(N − i)!) for 0 < i < N
(N divides the numerator but not the denominator). So (X + a)^N ≡ X^N + a^N, and a^N ≡ a (mod N) by Fermat's little
theorem (for a coprime to N, multiplication by a permutes the nonzero residues, so a^(N−1) Π x ≡ Π x; for N | a both
sides are 0). Reducing mod X^r − 1 preserves the congruence. ∎

### A.7 The main theorem

**Theorem A7.** Let N ≥ 2 pass steps 1, 3 and 5 of the code with N > r. Then N is prime.

**Proof.** Write t, ℓ, λ, K as above.

*(i) Every prime factor p of N exceeds r.* If p ≤ r, then a = p is tried in step 3 (N > r gives min(r, N − 1) = r)
and gcd(p, N) = p with 1 < p < N (p = N would give N ≤ r): step 3 would have returned False. Fix a prime p | N.
Then p ∤ r.

*(ii) The congruences in characteristic p.* Let R_p = F_p[X]/(X^r − 1). Reducing step 5 mod p:
(X + a)^N = X^N + a in R_p for 0 ≤ a ≤ ℓ (a = 0 is trivial). For every f ∈ F_p[X], f(X)^p = f(X^p) in F_p[X]: the
p-th power map is additive in characteristic p (p | C(p, i) for 0 < i < p) and c^p = c for c ∈ F_p (Fermat).

*(iii) R_p is reduced, so the p-th power map is injective on it.* X^r − 1 is squarefree in F_p[X]: if h² divides
it, h divides the derivative r X^(r−1), and r is invertible mod p, so h divides X^(r−1); but X does not divide
X^r − 1, so h is constant. If g^p ≡ 0 mod X^r − 1, every irreducible factor of X^r − 1 divides g^p and hence g;
these factors are distinct, so their product X^r − 1 divides g. So g^p = 0 implies g = 0 in R_p, and g^p = h^p
implies (g − h)^p = 0, so g = h.

*(iv) Introspective numbers.* Call an integer m ≥ 1 introspective for f ∈ F_p[X] if f(X)^m = f(X^m) in R_p.
- If m and m′ are introspective for f, so is m m′: f(X)^(mm′) = (f(X^m))^(m′) in R_p; and f(Y)^(m′) ≡ f(Y^(m′))
  mod Y^r − 1, with Y = X^m, gives f(X^m)^(m′) ≡ f(X^(mm′)) mod X^(mr) − 1, which X^r − 1 divides.
- If m is introspective for f and g, it is for f g.
- p is introspective for every f ∈ F_p[X], by (ii).
- N is introspective for X + a, 0 ≤ a ≤ ℓ, by (ii).
- m = N/p is introspective for X + a, 0 ≤ a ≤ ℓ: in R_p, ((X + a)^m)^p = (X + a)^N = X^N + a, and
  (X^m + a)^p = X^(mp) + a = X^N + a by (ii); so ((X + a)^m)^p = (X^m + a)^p and (iii) gives (X + a)^m = X^m + a.

Let I = {(N/p)^i p^j : i, j ≥ 0} and P = {Π_(a=0..ℓ) (X + a)^(e_a) : e_a ≥ 0} ⊆ F_p[X]. By the rules above, every
m ∈ I is introspective for every f ∈ P.

*(v) The group G.* Both N/p and p are coprime to r (gcd(r, N) = 1), so G = {m mod r : m ∈ I} is a subset of the
unit group (Z/rZ)^×, closed under multiplication and containing 1, hence a subgroup. Let t = |G|. N = (N/p)·p ∈ I,
so G contains the powers of N mod r and t ≥ ord_r(N) ≥ K + 1 > λ². Also t ≤ φ(r).

*(vi) A field in which X has order r.* Write X^r − 1 = h_1 ⋯ h_s with distinct monic irreducible h_i (by (iii)).
For a divisor d of r, X^d − 1 divides X^r − 1, so it is the product of the h_i that divide it, and the degrees of
those h_i sum to d. In the field F_i = F_p[X]/(h_i) let x_i be the class of X; x_i^r = 1, so its order o_i divides r,
and x_i^d = 1 iff h_i | X^d − 1. For a set Q of primes dividing r put d_Q = r/Π_(q∈Q) q; then x_i^(r/q) = 1 for all
q ∈ Q iff o_i divides every r/q (q ∈ Q) iff o_i | d_Q (the gcd of these r/q is d_Q). Let T_i = {q prime, q | r :
x_i^(r/q) = 1}; o_i = r iff T_i is empty, and Σ_(Q⊆T_i) (−1)^|Q| is 1 if T_i is empty and 0 otherwise. Hence
Σ_(i: o_i = r) deg h_i = Σ_Q (−1)^|Q| Σ_(i: Q⊆T_i) deg h_i = Σ_Q (−1)^|Q| d_Q = r Π_(q|r) (1 − 1/q) > 0, the sum over
all sets Q of primes dividing r. So some h = h_i has o_i = r. Let F = F_p[X]/(h) and let x be the class of X, of
order r. Since h | X^r − 1, every equality in R_p gives an equality in F. Let 𝒢 be the set of values f(x), f ∈ P.

*(vii) ℓ < p, and two counting inequalities for B = ⌊√t λ⌋.* Since t > λ², √t > λ, so √t λ < t and B ≤ t − 1.
As t ≤ φ(r), ℓ = ⌊√φ(r) λ⌋ ≥ B. Moreover ℓ ≤ √φ(r) λ < √φ(r) √t ≤ φ(r) ≤ r − 1 < p by (i). And N > r ≥ 2 gives
N ≥ 3, so √t λ > λ² ≥ (log₂ 3)² > 2.5 and B ≥ 2.

*(viii) Lower bound: |𝒢| ≥ C(t + ℓ, t − 1).* Since ℓ < p, the linear polynomials X + a (0 ≤ a ≤ ℓ) are distinct and
irreducible in F_p[X], so distinct exponent vectors (e_0, …, e_ℓ) give distinct polynomials in P (unique
factorization). Let f ≠ g in P have degree < t, and suppose f(x) = g(x). For m ∈ I, f(x)^m = g(x)^m, and
introspection gives f(x^m) = f(x)^m = g(x)^m = g(x^m). So the nonzero polynomial f(Y) − g(Y) ∈ F[Y] of degree < t
vanishes at x^m for all m ∈ I; as x has order r, these are t distinct elements (one for each residue in G), more
than its degree allows. So the polynomials of P of degree < t have distinct values, and there are
C(t − 1 + ℓ + 1, ℓ + 1) = C(t + ℓ, t − 1) of them (exponent vectors with Σ e_a ≤ t − 1).

*(ix) Upper bound: if N is not a power of p, |𝒢| ≤ N^√t.* Then N/p = p^c M with M > 1 and p ∤ M, so the numbers
(N/p)^i p^j = p^(ci+j) M^i with 0 ≤ i, j ≤ ⌊√t⌋ are pairwise distinct ((i, j) is recovered from M^i and the power of
p); there are (⌊√t⌋ + 1)² > t of them, so two of them, m_1 > m_2, are congruent mod r. Then x^(m_1) = x^(m_2), and for
f ∈ P, f(x)^(m_1) = f(x^(m_1)) = f(x^(m_2)) = f(x)^(m_2). So every element of 𝒢 is a root of the nonzero polynomial
Y^(m_1) − Y^(m_2) ∈ F[Y], and |𝒢| ≤ m_1 ≤ (N/p)^⌊√t⌋ p^⌊√t⌋ = N^⌊√t⌋ ≤ N^√t.

*(x) Conclusion.* The map s ↦ C(c + s, s) is nondecreasing in s for c ≥ 0 (the ratio of consecutive values is
(c + s + 1)/(s + 1)), and C(c + B, B) is nondecreasing in c. Using B ≤ t − 1 and B ≤ ℓ from (vii):
|𝒢| ≥ C((ℓ + 1) + (t − 1), t − 1) ≥ C(ℓ + 1 + B, B) ≥ C(2B + 1, B). For B ≥ 2, C(2B + 1, B) > 2^(B+1): C(5, 2) = 10 > 8,
and C(2B + 3, B + 1)/C(2B + 1, B) = 2(2B + 3)/(B + 2) ≥ 2. Finally 2^(B+1) > 2^(√t λ) ≥ 2^(√t log₂ N) = N^√t. So
|𝒢| > N^√t, and by (ix) N is a power of p. Step 1 passed, so N is not a power with exponent ≥ 2, and N = p. ∎

**Check.** `AKSLemmaTests.test_counting_chain`: C(2B + 1, B) > 2^(B+1) for 2 ≤ B ≤ 2000; and for every prime
N < 2^14 with N > r (where p = N, G = ⟨N⟩ and t = ord_r(N)): t > λ², B ≤ t − 1, B ≤ ℓ < r, B ≥ 2, and
C(t + ℓ, t − 1) ≥ C(2B + 1, B) > 2^(B+1), in exact integer arithmetic. `AKSFieldTests.test_order_r_factor`: for
every prime p < 30 and every 2 ≤ r < 40 with p ∤ r, X^r − 1 is squarefree over F_p, and the product of its
irreducible factors in which X has order r, computed as (X^r − 1)/lcm_(q | r) (X^(r/q) − 1), has degree φ(r).

### A.8 Correctness of the implementation

**Theorem A8.** For every integer N ≥ 0, `is_prime_aks(N)` terminates and returns True iff N is prime.

**Proof.** Step 0 is correct for N < 2. Let N ≥ 2. Step 1 returns False exactly for perfect powers (Lemma A4(b)),
which are composite; primes pass it. Step 2 terminates (Lemma A3). Step 3 returns False only for composite N and
never for prime N (A4(c)). Step 4 returns True only for primes (A4(d)). Step 5 returns False only if the congruence
fails for some a (A5(d)), which never happens for primes (A6). Step 6 is reached only with N > r after steps 1, 3
and 5 passed, so N is prime (Theorem A7). A prime N passes steps 1 and 3 and then returns True in step 4 or, after
passing step 5, in step 6. ∎

**Check.** V1 (`python tools/validate.py pairs/primality-trial-vs-aks`): random n-bit N, n = 0..16, sieve oracle.
`AKSCorrectnessTests`: every N < 600 against the sieve (`test_small_N`, which also checks that the K, r and ℓ read
from the code's local variables equal the test's re-computation); 8 semiprimes p·q whose prime factors both exceed
r, so that only step 5 can reject them (checked: N > r, not a perfect power, no factor ≤ r), are reported
composite. `experiments/2026-10-07_primality_proof_checks.py` (part 3): every N < 2^12, and at least 30 such semiprimes
(31 in the recorded run).
`experiments/2026-10-06_aks_step5_composites.py`: every N < 3000 (against trial division and Miller–Rabin), and 13
such semiprimes.

### A.9 Running time

**Theorem A9.** For n-bit N, `is_prime_aks(N)` takes O(n^(33/2)) bit operations in the schoolbook model and
Õ(n^(21/2)) in the fast-arithmetic model.

**Proof.** Let R = R(n) = O(n^5), so r ≤ R (Lemma A3), K ≤ λ² ≤ n², ℓ ≤ √φ(r) λ ≤ √R n, and let
w = 8·wb ≤ bitlen(r(N − 1)²) + 7 ≤ 2n + log₂ R + 8 = O(n).
- `_log2_upper`: two shifts of N (O(n)) and 64 squarings of numbers of at most 2P + 2 = 258 bits: O(n).
- Step 1: for each b ≤ n, `_iroot` makes at most n/b + 2 iterations, each computing mid^b < 2^(n+b) with O(log b)
  multiplications of numbers below 2^(2n): O(n² log n) per iteration, O(n³ log² n) in total (Õ(n²) fast).
- Step 2: at most R values of r; each costs one gcd (O(n²)) and at most K iterations of `x * N % r` with x < r
  (O(n log R) each): O(R(n² + n³ log n)) = O(n^8 log n) (Õ(n^8) fast).
- Step 3: at most r gcds: O(R n²) = O(n^7). `_totient(r)`: O(√r) divisions of O(log r)-bit numbers. ℓ: one `isqrt`
  of φ(r)A² < R n² 4^J, a number of O(log n) bits (J = 64 is fixed).
- Step 5: ℓ calls of `_pow_x_plus_a`, each with n squarings, at most n multiplications by X + a, and an O(rn)
  comparison. One squaring packs r coefficients (O(rw)), squares an rw-bit integer (O(r²w²) schoolbook, Õ(rw)
  fast), unpacks (O(rw)) and reduces r numbers of at most w + 1 bits mod N (O(r n w) schoolbook, r·Õ(n) fast). One
  multiplication by X + a costs r products a·P_i with a < r (O(n log r) each) and r reductions of
  (n + log₂ r + 1)-bit numbers mod N: O(r n²) schoolbook in the stated division model, r·Õ(n) fast. Per call:
  n · O(r² w²) + n · O(r n²) = O(r² n³) schoolbook, Õ(r n²) fast.
  Total: ℓ · O(r² n³) ≤ √R n · O(R² n³) = O(R^(5/2) n⁴) = O(n^(33/2)) schoolbook, and
  ℓ · Õ(r n²) ≤ √R n · Õ(R n²) = Õ(R^(3/2) n³) = Õ(n^(21/2)) fast.
Step 5 dominates in both models. ∎

### A.10 Space

**Statement.** `is_prime_aks` uses O(rn) = O(n^6) bits.

**Proof.** The largest objects are the coefficient lists (r integers below N: rn bits) and, inside `_square_mod`, the
packed integer (rw bits), its square and its byte string (at most 2rw bits each) and the list c (2r integers below
2^w). At any moment a bounded number of these is alive (in `_square_mod` its input and these four objects; in the
callers the current P, the previous `lhs` and `rhs`). With w = O(n) and r ≤ R(n) = O(n^5) this is O(rn) = O(n^6)
bits; steps 1–3 hold O(n) bits. ∎

**Check.** `AKSSpaceTests.test_live_size`: at every return of `_square_mod` (traced with `sys.setprofile`), the total
size of the integers, byte strings and integer lists held in the local variables of all active frames of `aks.py`
is at most r(14n + 5 log₂ r + 48) + 4096 bits, for 6 seeded primes of 8 to 13 bits and 2 composites rejected in
step 5.

### A.11 A lower bound on primes

**Statement.** If N is prime and N > r (in particular for every prime N with n ≥ 24), the code performs exactly
ℓ·n polynomial squarings, each computing r reduced coefficients, and ℓ·n·r ≥ (n − 1)^4 n. So it takes Ω(n^5)
operations on every n-bit prime with n ≥ 24.

**Proof.** A prime passes steps 1 and 3; with N > r, step 5 runs for a = 1, …, ℓ and never returns False (A6), and
each call of `_pow_x_plus_a` makes one squaring per bit of N. Next, φ(r) ≥ ord_r(N) ≥ K + 1 > λ², so
√φ(r) λ > λ² ≥ (log₂ N)² ≥ (n − 1)², and ℓ = ⌊√φ(r) λ⌋ ≥ (n − 1)². Also r ≥ ord_r(N) + 1 > λ² + 1 > (n − 1)². So
ℓ n r ≥ (n − 1)^4 n. For n ≥ 24, N ≥ 2^(n−1) > R(n) ≥ r: R(24) = 24 · 577² = 7990296 < 2^23 = 8388608, and for
n ≥ 24, R(n + 1)/R(n) = ((n + 1)/n) · (((n + 1)² + 1)/(n² + 1))² ≤ (25/24)(626/577)² < 1.23 < 2 (both factors
decrease in n). ∎

**Check.** `AKSLemmaTests.test_lower_bound`: R(n) < 2^(n−1) for 24 ≤ n ≤ 5000 (and R(23) > 2^22).
`AKSCorrectnessTests.test_small_N`: for every prime N < 600 with N > r, the number of squarings, counted by wrapping
`_square_mod`, equals ℓ·n, and ℓ ≥ (n − 1)², r > (n − 1)².

## Part H: the harness

**H.1 The oracle.** `harness._build` is the sieve of Eratosthenes on [0, 2^20): for each p ≤ 2^10 still marked, it
unmarks p², p² + p, …. A marked p at that time is prime (every smaller prime has unmarked its multiples), only
multiples k·p with k ≥ p ≥ 2 are unmarked, and every composite x < 2^20 has a prime factor p ≤ √x < 2^10 with x ≥ p²
a multiple of p. So `check` compares with the exact primality of x < 2^20. *Check:* `HarnessTests.test_sieve`
(equal to trial division for every x < 2^20).

**H.2 The V1 generator.** For n ≥ 2, `generate(n, rng)` returns, with probability 1/2 each, a uniformly chosen
n-bit prime (from the sieve) or a uniform n-bit integer; for n ≤ 1 it returns n.

**H.3 The V2 generator.** `generate_scaling(n, rng)` returns a random odd n-bit integer accepted by `_is_prime_det`,
Miller–Rabin with the twelve prime bases 2, …, 37. Every prime passes it (see
`primality-miller-rabin-vs-aks/PROOFS.md`, M.2, which holds for every base). That no composite below its guard
passes all twelve bases is a published bound (Sorenson & Webster, arXiv:1509.00864, Theorem 1.1;
background); the guard value itself is a composite that passes all
twelve bases (`HarnessTests.test_psi12_passes_twelve_bases`). The V2 instances themselves are checked prime
independently: *Check:* `TrialDivisionTests.test_v2_instances` (the instances drawn with the validator's seeds
for n = 26, 28, …, 40 are n-bit primes, by trial division), and `tests/test_errata_2026_10_07.py` (the guard, and
agreement with trial division below 20000).

**H.4 "AKS up to 16 bits, where step 5 is genuinely exercised: N > r".** The largest r over the n-bit N is 199, 251,
307, 347, 419, 467, 557 for n = 10, 11, …, 16, each below 2^(n−1). So N > r for every N in [512, 2^16), and on every
input of 10 to 16 bits that passes steps 1 and 3, step 5 runs. *Check:*
`experiments/2026-10-07_primality_proof_checks.py`, part 1 (asserts N > r on [512, 2^16) and prints the largest r per
bit length).

## Part B: Bertrand's postulate

**Theorem B.** For every integer m ≥ 1 there is a prime p with m < p ≤ 2m.

**Proof.** *(B1)* Π_(p≤x) p ≤ 4^(x−1) for every integer x ≥ 1. True for x = 1, 2. For even x ≥ 4 the product equals
that for x − 1. For x = 2k + 1 ≥ 3: every prime p with k + 2 ≤ p ≤ 2k + 1 divides C(2k + 1, k) =
(2k + 1)!/(k!(k + 1)!), and C(2k + 1, k) = C(2k + 1, k + 1) are two terms of the sum 2^(2k+1) of all C(2k + 1, j),
so C(2k + 1, k) ≤ 4^k; by induction Π_(p≤2k+1) p ≤ 4^k · 4^k = 4^(x−1).
*(B2)* C(2m, m) ≥ 4^m/(2m + 1), being the largest of 2m + 1 terms that sum to 4^m.
*(B3)* By Legendre's formula, the exponent of a prime p in C(2m, m) is R_p = Σ_(i≥1) (⌊2m/p^i⌋ − 2⌊m/p^i⌋), whose
terms are 0 or 1 and vanish for p^i > 2m. So p^(R_p) ≤ 2m; R_p ≤ 1 if p > √(2m); and R_p = 0 if m ≥ 3 and
2m/3 < p ≤ m (then ⌊2m/p⌋ = 2, ⌊m/p⌋ = 1, and p² > 2m: for m ≥ 5 since p² > 4m²/9 ≥ 2m, and for m = 3, 4 since
p = 3).
*(B4)* Suppose m ≥ 512 and no prime lies in (m, 2m]. The prime factors of C(2m, m) divide (2m)!, so they are at most
m, hence at most 2m/3 by (B3). With (B3) and (B1), C(2m, m) ≤ (2m)^√(2m) · Π_(p≤2m/3) p ≤ (2m)^√(2m) 4^(2m/3) (at most
√(2m) primes are ≤ √(2m)). With (B2), 4^(m/3) ≤ (2m + 1)(2m)^√(2m) < (2m + 1)^(√(2m)+1), i.e. with x = 2m ≥ 1024,
x/3 < (√x + 1) log₂(x + 1). Put y = √x ≥ 32. Then log₂(x + 1) ≤ 2 log₂ y + 1/(y² ln 2) ≤ 2 log₂ y + 0.002, and
g(y) = y²/3 − (y + 1)(2 log₂ y + 0.002) satisfies g(32) = 341.33 − 33 · 10.002 > 11, g′(32) =
64/3 − 10.002 − 66/(32 ln 2) > 8, and g″(y) = 2/3 − 2/(y ln 2) + 2/(y² ln 2) > 0.57 for y ≥ 32. So g > 0 on
[32, ∞), i.e. x/3 > (√x + 1) log₂(x + 1), a contradiction.
*(B5)* For 1 ≤ m ≤ 511 use the primes 2, 3, 5, 7, 13, 23, 43, 83, 163, 317, 631, each less than twice the previous
one: the least of them above m is at most 2m (it is 2 for m = 1, and otherwise less than twice its predecessor,
which is at most m). ∎

**Check.** `BertrandTests`: the listed chain consists of primes, each less than twice its predecessor; a prime
lies in (m, 2m] for every m ≤ 10^5 (sieve); g(32) > 11, g′(32) > 8, and the bound on g″, evaluated numerically.
