# Proofs: primality testing, Miller–Rabin vs AKS

This file proves the claims of this entry about Miller–Rabin (sections M.1–M.7) and the comparison in its
`relationship` (M.8). The claims about AKS (correctness of the shared implementation, its polynomial bounds, its
space, and the lower bound on primes) are proved in
[`../primality-trial-vs-aks/PROOFS.md`](../primality-trial-vs-aks/PROOFS.md), Part A, and are only referred to here.
Statements about the literature are in the entry's `background` field. Each section ends with the deterministic
checks that re-run its computable facts and their ranges.

## Conventions

N ≥ 0 is the input and n its bit length. For odd N ≥ 3 write N − 1 = 2^s d with d odd (s ≥ 1). A base
a ∈ {1, …, N − 1} is a **non-witness** if a^d ≡ 1 (mod N) or a^(2^j d) ≡ −1 (mod N) for some 0 ≤ j ≤ s − 1, and a
**witness** otherwise; S(N) is the set of non-witnesses. φ is Euler's function. The cost models (schoolbook and
fast arithmetic) are those of `../primality-trial-vs-aks/PROOFS.md`, Conventions.

## M.1 What one round of the code does

**Statement.** `is_prime_miller_rabin(N, rounds)` returns N ∈ {2, 3} for N < 4 and False for even N ≥ 4, both
correct. For odd N ≥ 5 it computes s and d with N − 1 = 2^s d, d odd, and each round draws a base a from
{2, …, N − 2} and passes iff a ∈ S(N); the function returns True iff all rounds pass.

**Proof.** The `while` loop divides N − 1 by 2 until it is odd, counting s. `random.randrange(2, N - 1)` returns an
integer in [2, N − 2] (non-empty for N ≥ 5). Then y = a^d mod N; if y ∈ {1, N − 1} the round passes (the cases
a^d ≡ 1 and j = 0). Otherwise the inner loop squares y up to s − 1 times, so y takes the values a^(2^j d) mod N for
j = 1, …, s − 1, and the round passes as soon as one of them is N − 1. If none is, the `for … else` returns False.
So a round passes iff a ∈ S(N). ∎

**Check.** `tests/test_proofs_primality.py`, `MillerRabinTests.test_round_matches_definition`: with
`random.randrange` replaced by a function returning a fixed base, `is_prime_miller_rabin(N, 1)` equals
"a ∈ S(N)" (computed from the definition) for every odd N in [5, 400] and every a in [2, N − 2]; and N < 4 and even
N < 400 give the correct answer.

## M.2 Primes always pass

**Statement.** If N ≥ 3 is prime, every base a with N ∤ a is a non-witness. So the code never rejects a prime.

**Proof.** By Fermat's little theorem a^(N−1) = a^(2^s d) ≡ 1. Let j be the least index in [0, s] with
a^(2^j d) ≡ 1. If j = 0, a^d ≡ 1. Otherwise y = a^(2^(j−1) d) satisfies y² ≡ 1 and y ≢ 1; modulo a prime,
y² − 1 = (y − 1)(y + 1) ≡ 0 forces y ≡ −1, so a^(2^(j−1) d) ≡ −1 with 0 ≤ j − 1 ≤ s − 1. ∎

**Check.** `tests/test_proofs_primality.py`, `MillerRabinTests.test_primes_pass_every_base`: every base
1 ≤ a ≤ N − 1 is a non-witness for every odd prime N < 2000.

## M.3 At least 3/4 of the bases are witnesses

**Theorem M.3.** Let N be an odd composite. If N ≠ 9, then |S(N)| ≤ φ(N)/4; and S(9) = {1, 8}. Hence at least
3/4 of the bases in {1, …, N − 1} are witnesses (exactly 3/4 for N = 9).

**Proof.** *Non-witnesses are units:* if a ∈ S(N), then a^(N−1) ≡ 1 (square a^d ≡ 1, or a^(2^j d) ≡ −1, enough
times), so gcd(a, N) = 1. Let U = (Z/NZ)^×, of order φ(N).

*A subgroup containing S(N).* Let j_0 be the largest j ∈ [0, s − 1] for which some unit b has b^(2^j d) ≡ −1; it
exists because (−1)^d = −1 (d is odd). Put m = 2^(j_0) d; then 2m divides 2^s d = N − 1. Let
G_1 = {a ∈ U : a^m ≡ ±1 (mod N)}. If a ∈ S(N) and a^d ≡ 1, then a^m ≡ 1. If a^(2^j d) ≡ −1, then j ≤ j_0 by the
choice of j_0, and a^m = (a^(2^j d))^(2^(j_0 − j)) ≡ ±1. So S(N) ⊆ G_1, a subgroup of U.

Let N = Π_(i=1..k) p_i^(e_i) with distinct odd primes p_i, and G_2 = {a ∈ U : a^m ≡ ±1 (mod p_i^(e_i)) for each i}
(the signs may differ between the i), a subgroup with G_1 ⊆ G_2 ⊆ U.

*(a) [G_2 : G_1] = 2^(k−1).* The map ψ : G_2 → {±1}^k, a ↦ (a^m mod p_i^(e_i))_i, is a homomorphism (+1 ≢ −1 modulo
an odd prime power). It is onto: take b with b^m ≡ −1 (mod N); for a sign vector σ, the Chinese remainder theorem
gives a unit a with a ≡ b (mod p_i^(e_i)) where σ_i = −1 and a ≡ 1 where σ_i = +1, and ψ(a) = σ. G_1 is the preimage
of {(1, …, 1), (−1, …, −1)}, so its index in G_2 is 2^k/2.

*(b) If some e_i ≥ 2 (p = p_i, e = e_i), then [U : G_2] ≥ p^(e−1).* Let T = {x ∈ (Z/p^e Z)^× : x^(2m) = 1}. Since
p | N, p ∤ N − 1, and 2m | N − 1, p does not divide 2m. The subgroup V = {x ≡ 1 (mod p)} of (Z/p^e Z)^× has order
p^(e−1), so the order of each of its elements is a power of p; the order of each element of T divides 2m. So
T ∩ V = {1}, T maps injectively into (Z/p^e Z)^×/V, which has order p − 1, and |T| ≤ p − 1. Every a ∈ G_2 has
a^(2m) ≡ 1 (mod p^e), so G_2 lies in the preimage of T under the reduction U → (Z/p^e Z)^×, which is onto (Chinese
remainder theorem); that preimage has index [(Z/p^e Z)^× : T] ≥ p^(e−1)(p − 1)/(p − 1) = p^(e−1) in U.

*(c) Cases.* If k ≥ 3, [U : G_1] ≥ [G_2 : G_1] ≥ 4. If k = 2 and some e_i ≥ 2, [U : G_1] ≥ 3 · 2 = 6. If k = 1, then
N = p^e with e ≥ 2 and [U : G_1] ≥ p^(e−1), which is ≥ 4 unless p^(e−1) = 3, i.e. N = 9. If N = pq with distinct
primes, [G_2 : G_1] = 2, and [U : G_2] ≥ 2: otherwise every x ∈ (Z/pZ)^× would satisfy x^(2m) = 1 (take a ≡ x mod p,
a ≡ 1 mod q), and then x^g = 1 for g = gcd(2m, p − 1) (Bézout, with x^(p−1) = 1); a nonzero polynomial over the field
Z/pZ has at most g roots, so p − 1 ≤ g and p − 1 divides 2m, hence N − 1. As N − 1 = pq − 1 ≡ q − 1 (mod p − 1),
p − 1 | q − 1; by symmetry q − 1 | p − 1, so p = q, a contradiction. In every case except N = 9, [U : G_1] ≥ 4 and
|S(N)| ≤ |G_1| ≤ φ(N)/4. For N = 9: N − 1 = 8 = 2³ · 1; the squares mod 9 are 0, 1, 4, 7, so no a has a² ≡ −1 or
a⁴ ≡ −1, and S(9) = {1, 8}. Finally φ(N)/4 ≤ (N − 1)/4, and 2 = (9 − 1)/4. ∎

**Check.** `tests/test_proofs_primality.py`, `MillerRabinTests.test_three_quarters_bound`: |S(N)| ≤ φ(N)/4 for every
odd composite N < 2000 except N = 9, S(9) = {1, 8}, and for the Carmichael numbers 561, 1105, 1729, 2465, 2821,
6601, 8911, 10585, 15841, 29341. `experiments/2026-10-07_primality_proof_checks.py` (part 2): every odd composite
N < 2^14.

## M.4 The error bound of the implementation

**Statement.** For an odd composite N and a base drawn uniformly from {2, …, N − 2}, one round passes with
probability (|S(N)| − 2)/(N − 3) < 1/4. With k ≥ 1 rounds whose bases are independent and uniform, a composite is
accepted with probability < 4^(−k), and a prime is always accepted (one-sided error). (For k = 0 the function
accepts every odd N ≥ 5.)

**Proof.** 1 and N − 1 are always non-witnesses (1^d = 1, (−1)^d = −1), so |S(N) ∩ {2, …, N − 2}| = |S(N)| − 2. For
N = 9 this is 0. For N ≠ 9, Theorem M.3 gives (|S(N)| − 2)/(N − 3) ≤ (φ(N)/4 − 2)/(N − 3) < 1/4, because
φ(N) − 8 < N − 3. Independence multiplies the k probabilities. Even composites and N < 4 are answered correctly
without randomness (M.1), and primes pass every round (M.2). ∎

The code draws its bases from Python's `random` module, a deterministic pseudo-random generator that the validator
re-seeds before every call; the probability statements are about independent uniform bases, and the recorded V1 run
is a fixed, reproducible computation.

**Check.** `MillerRabinTests.test_three_quarters_bound` and part 2 of the experiment also check
(|S(N)| − 2)/(N − 3) < 1/4 on the same N.

## M.5 Running time

**Statement.** k rounds take O(n² + k n³) bit operations in the schoolbook model: O(n) multiplications mod N per
round. In the fast-arithmetic model this is Õ(k n²).

**Proof.** Computing s and d takes at most n halvings of n-bit numbers: O(n²). Per round: drawing a takes O(n);
`pow(a, d, N)` makes O(bitlen(d)) = O(n) multiplications mod N. This is an assumption of the machine model (stated
in the entry's `background`) about
the interpreter's three-argument `pow`, not proved here; the left-to-right binary method, for example, makes at
most 2·bitlen(d) (`../modular-exponentiation-repeated-vs-square-multiply/PROOFS.md`, section 3). Then at most
s − 1 ≤ n − 1 squarings mod N. Each multiplication mod N multiplies numbers below N and
divides by N: O(n²) schoolbook, Õ(n) fast. ∎

## M.6 Space

The code holds N, d, a, y (all below N), s ≤ n and loop counters bounded by `rounds` and s: O(n) bits for a fixed
number of rounds. **Check.** `MillerRabinTests.test_locals_have_O_n_bits`: every integer local has at most
max(n, 6) bits (6 for `rounds` = 32), traced with `sys.settrace`, on 200 seeded N with n ≤ 64.

## M.7 PRIMES is in coRP

**Statement.** There is a randomized algorithm that runs in polynomial time on uniform random bits, always accepts
primes, and rejects every composite with probability greater than 1/2.

**Proof.** Answer N < 4 and even N exactly. For odd N ≥ 5, repeat three times independently: draw n random bits,
giving c ∈ [0, 2^n); if 2 ≤ c ≤ N − 2 and c is a witness, reject. If no repetition rejects, accept. Primes are never
rejected (M.2). An odd composite N has N ≥ 9, so n ≥ 4 and P(2 ≤ c ≤ N − 2) = (N − 3)/2^n ≥ 1/2 − 3/2^n ≥ 5/16;
given that event, c is uniform on [2, N − 2] and is a witness with probability > 3/4 (M.4). So one repetition rejects
with probability > 15/64, and three reject with probability > 1 − (49/64)³ > 0.55. The time is polynomial by M.5. So
the complement of PRIMES is in RP, i.e. PRIMES is in coRP. ∎

**Check.** `MillerRabinTests.test_corp_constants`: 1/2 − 3/2^n ≥ 5/16 for 4 ≤ n < 200, and 1 − (49/64)³ > 0.55.

## M.8 The comparison with AKS

**Statement.** For a fixed number of rounds k, Miller–Rabin takes O(n³) bit operations (M.5), while the AKS
implementation performs at least (n − 1)^4 n operations on every n-bit prime with n ≥ 24
(`../primality-trial-vs-aks/PROOFS.md`, A.11), and at most O(n^(33/2)) (schoolbook) or Õ(n^(21/2)) (fast arithmetic)
on every n-bit input (A.9). So on primes Miller–Rabin is asymptotically faster, and the proved upper bound of AKS has
a much larger degree; AKS is deterministic and correct on every input without any assumption (A.8).

**Proof.** Combine M.5 with A.8, A.9 and A.11; each coefficient operation counted in A.11 costs at least one bit
operation, and k n³ = o((n − 1)^4 n). ∎
