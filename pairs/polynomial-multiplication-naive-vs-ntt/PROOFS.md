# Proofs: polynomial multiplication, schoolbook vs NTT

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms (including the facts about the prime
p = 998244353 and its roots of unity, the iterative transform and its inverse), every stated time and space bound,
every exact operation count on its domain, and the unit-cost model. Sections 1 and 2 prove the exact counts;
sections 3 to 10 prove the rest. Statements about the literature are not claims of this entry: they are listed under
`background` in `entry.json`, with their sources, and are not proved here. Each proof is followed by the deterministic
scripts or tests that check its computable facts and the ranges they check. A check covers only those ranges; the
proofs cover the general statements.

## Counting convention

`harness.py`, class `CountingCoeff`: `__mul__` (also bound as `__rmul__`) adds 1 to the module counter `_mults`;
`__add__`, `__radd__`, `__sub__`, `__rsub__` and `__mod__` return a new `CountingCoeff` without counting, and
`__bool__` and `__eq__` do not count. `generate_scaling(n, rng)` draws the coefficients of `generate(n, rng)` (two
polynomials of n coefficients each, uniform in Z_p, p = 998244353), wraps each in `CountingCoeff` and sets
`_mults = 0`; `reported_cost(output)` returns `_mults`.

A product `x * y` counts exactly 1 if at least one operand is a `CountingCoeff` ("input-derived"; if only `y` is,
`int.__mul__` returns `NotImplemented` and Python calls `y.__rmul__`); a product of two plain ints does not count.
Any `+`, `-` or `%` with a `CountingCoeff` operand gives a `CountingCoeff`. Plain ints in `ntt.py`: the padding
zeros, the twiddle factors `w` and `w_len`, `n_inv` and everything computed by `pow`.

## 1. Schoolbook: n² when no coefficient of A is 0

**Statement.** On every input with len(A) = len(B) = n, `polymul_naive` makes exactly z · n counted
multiplications, where z is the number of non-zero coefficients of A; in particular exactly n² when no coefficient
of A is 0.

**Proof.** For each coefficient `a` of A the test `if a:` (`CountingCoeff.__bool__`, not counted) skips the row
when a = 0; otherwise the inner loop evaluates `a * b` for each of the n coefficients b of B, one counted product
each (both are input coefficients). Nothing else multiplies. (For n = 0 the function returns `[]`.)

**Check.** `experiments/2026-10-06c_ntt_counts.py` (the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "poly schoolbook n^2 (no zero coefficient drawn)": n = 0..29 and the V2 sizes n = 100, 200,
300, 400, 600, 800. `experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "poly schoolbook
nnz(A) * n with planted zero coefficients": n = 1..40, 3 seeded inputs per n.

## 2. NTT: 3n log₂n + 5n for n = 2^k, k ≥ 1 (and 2 at n = 1)

**Statement.** For every n = 2^k with k ≥ 1 and every input with len(A) = len(B) = n, `polymul_ntt` makes exactly
3n log₂n + 5n counted multiplications: n log₂n = (log₂(2n) − 1)n in each forward transform, 2n pointwise products,
and (log₂n + 1)n = log₂(2n)·n butterfly products plus 2n scalings in the inverse transform. Every counted butterfly
product has the plain twiddle factor `w` as its other operand, so only the 2n pointwise products have two
input-derived operands. Not counted: one twiddle update `w * w_len` per butterfly, the `pow` calls, and the
first-stage butterfly products, whose operand `a[k + half]` is a padding zero. At n = 1 the count is 2.

**Proof.** *Size.* out_len = 2n − 1, and for n = 2^k ≥ 2 the smallest power of two ≥ 2n − 1 is N = 2n. So
`fa = list(A) + [0] * n`: positions 0..n − 1 hold input coefficients, positions n..2n − 1 plain zeros (the same for
`fb`).

*Bit reversal.* The first loop of `_ntt` is the in-place bit-reversal permutation: it keeps j equal to the
log₂N-bit reversal rev(i) of i (the `while j & bit` loop clears the leading ones of j from the top and the next
line sets the first zero bit, which is adding 1 to the reversed number), and it swaps a[i] with a[rev(i)] once for
each pair i < rev(i). An index i < n = N/2 has top bit 0, so rev(i) is even. Hence after the permutation every even
position holds an input coefficient and every odd position a plain zero.

*Forward transforms.* Stage `length = 2` (half = 1) runs the butterflies (k, k + 1) for even k: `a[k + 1] * w` is
plain 0 times plain `w = 1`, not counted; `a[k] = (u + v) % P` and `a[k + 1] = (u - v) % P` are input-derived
because u = a[k] is. So after stage 2 every entry is input-derived. Each later stage, `length` = 4, 8, …, N, runs
N/2 = n butterflies, each with exactly one counted product `a[k + half] * w` (w is plain: it starts at 1 and is
updated by `w * w_len % P` on plain ints). There are log₂N − 1 = log₂n such stages, so each forward transform makes
n log₂n counted products.

*Pointwise.* `x * y % P` for each of the N = 2n pairs, both operands input-derived: 2n counted products, and every
entry of `fc` is input-derived.

*Inverse transform.* All entries are input-derived from the start (the permutation only moves them), so each of the
log₂N = log₂n + 1 stages makes n counted butterfly products; the final loop computes `a[i] * n_inv % P` for each of
the 2n entries with plain `n_inv`: 2n counted products.

Total: 2 · n log₂n + 2n + n(log₂n + 1) + 2n = 3n log₂n + 5n.

*n = 1.* out_len = 1, so N = 1: no stage runs (`length = 2 > 1`), the pointwise loop makes 1 counted product and the
scaling 1 (`n_inv = pow(1, P - 2, P) = 1` is plain, `a[0]` is input-derived): 2, while 3n log₂n + 5n = 5.

**Check.** `experiments/2026-10-06c_ntt_counts.py` (n = 2^3..2^15). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "NTT 3n log2 n + 5n (n=2^k)": n = 2, 4, 8, …, 16384 (n = 1 reported as outside the domain
with count 2, and n = 3, 5, 6, 7, 100 as non-powers of two); line "NTT n=1: 2": n = 1. `experiments/2026-10-07_count_proof_checks.py`, group
`algebra`, line "NTT split: forward n log2 n each, pointwise 2n, inverse (log2 n + 1) n + 2n; butterfly twiddles
plain": n = 2, 4, …, 4096.

## 3. Notation

p = 998244353 = `P`, Z_p the integers mod p. For a power of two N = 2^K and 0 ≤ i < N, rev_K(i) is the number whose
K-bit binary representation is that of i reversed. The DFT of x ∈ Z_p^N at an element ω is x̂[t] = Σ_u x_u ω^(ut).
For a polynomial A = Σ_j A_j X^j, A(y) is its value at y ∈ Z_p.

## 4. Correctness of the schoolbook method

**Statement.** For coefficient lists A, B with entries in [0, p), `polymul_naive((A, B))` returns the
len(A) + len(B) − 1 coefficients of A · B mod p, in [0, p) (and `[]` if A or B is empty).

**Proof.** C starts as zeros. For every i with A[i] ≠ 0 and every j the code sets
C[i + j] = (C[i + j] + A[i] B[j]) mod p; the skipped rows (A[i] = 0) would add 0. So C[k] = Σ_{i+j=k} A[i] B[j] mod p,
reduced into [0, p) by Python's `%`.

**Check.** `tests/test_proofs_ntt.py`, `CorrectnessTests`: n = 0..130, 255, 256, 257, 511, 512, 513 on seeded
uniform coefficients, and for n ≤ 130 also with planted zero coefficients and with all coefficients p − 1, against a
separate convolution loop. V1 (`harness.check`, evaluation at three points).

## 5. The prime and its roots of unity

**Statement** (`correctness`, `ntt.py` docstring, README). p is prime and p − 1 = 119 · 2²³ = 2²³ · 7 · 17; 3 is a
primitive root mod p; for every L = 2^s with 1 ≤ s ≤ 23 the code's root ω_L = 3^((p−1)/L) mod p has order exactly L,
ω_L^(L/2) = −1, and ω_(L/2) = ω_L². So Z_p contains primitive 2^s-th roots of unity for every s ≤ 23, and none of
order 2²⁴.

**Proof.** 119 = 7 · 17. *Lucas' test.* 3^(p−1) ≡ 1 and 3^((p−1)/q) ≢ 1 (mod p) for each prime q ∈ {2, 7, 17} dividing
p − 1 (computed). So the order of 3 in the multiplicative monoid of Z_p divides p − 1 but no (p − 1)/q, hence equals
p − 1: the powers 3, 3², …, 3^(p−1) are p − 1 distinct units, so every non-zero residue is a unit, p is prime, and 3
is a primitive root. *Roots.* ω_L^L = 3^(p−1) = 1, so the order of ω_L divides L = 2^s; it is L because
ω_L^(L/2) = 3^((p−1)/2) ≠ 1. Since (ω_L^(L/2))² = 1 and Z_p is a field, ω_L^(L/2) = −1. ω_L² = 3^((p−1)/(L/2)) =
ω_(L/2). The group Z_p^* is cyclic of order p − 1, which 2²⁴ does not divide, so no element has order 2²⁴.

**Check.** `tests/test_proofs_ntt.py`, `ModulusTests`: the factorisation, the four modular powers of Lucas' test,
trial division of p by every d ≤ √p (an independent primality check), and for every s = 1..23 the order, the value
−1 at L/2 and the squaring relation; 2²⁴ ∤ p − 1.

## 6. The iterative transform computes the DFT, and the inverse inverts it

**Statement.** Let a have length N = 2^K ≤ 2²³ and ω = ω_N. Then `_ntt(a, invert=False)` replaces a by its DFT at ω,
and `_ntt(a, invert=True)` replaces a by (1/N) Σ_t a[t] ω^(−ut) for every u, which inverts the DFT.

**Proof.** *(a) Bit reversal.* Claim: when iteration i (1 ≤ i < N) of the first loop starts, j = rev_K(i − 1), and it
ends with j = rev_K(i). Adding 1 to i − 1 (which is < N − 1, so it has a 0 bit) turns its trailing 1-bits into 0 and
the next 0-bit into 1; in the reversed representation these are the leading bits of j, which the `while j & bit`
loop clears from the top before `j |= bit` sets the next one. The swap `a[i], a[j]` runs only for i < j; rev_K is an
involution, so each pair {i, rev_K(i)} with i ≠ rev_K(i) is swapped exactly once and fixed points are left alone.
Afterwards a[i] = a₀[rev_K(i)], where a₀ is the input.

*(b) Stages.* Write ω_L for the root used by the stage with `length` L (for `invert`, its inverse
ω_L^(p−2) = ω_L^(−1), by Fermat, since p is prime; the inverses satisfy the same relations as in section 5). Claim:
after the stage with `length` L = 2^s, for every block start b (a multiple of L) and 0 ≤ t < L,

a[b + t] = Σ_{u=0..L−1} a₀[c + u · 2^(K−s)] ω_L^(ut),   with c = rev_(K−s)(b/L).

Before the first stage (s = 0) this is (a). For the step s − 1 → s, the block at b consists of the half-blocks at b
and b + L/2, whose block numbers (at length L/2) are 2q and 2q + 1 with q = b/L; rev_(K−s+1)(2q) = c and
rev_(K−s+1)(2q + 1) = c + 2^(K−s). By the claim for s − 1, for t < L/2,
E[t] = a[b + t] = Σ_{v<L/2} a₀[c + v · 2^(K−s+1)] ω_(L/2)^(vt) and
O[t] = a[b + L/2 + t] = Σ_{v<L/2} a₀[c + 2^(K−s) + v · 2^(K−s+1)] ω_(L/2)^(vt).
Split the target sum by the parity of u (u = 2v or 2v + 1) and use ω_(L/2) = ω_L²: it equals E[t mod L/2] +
ω_L^t O[t mod L/2]; for t < L/2 this is E[t] + ω_L^t O[t], and for t + L/2 it is E[t] − ω_L^t O[t], because
ω_L^(L/2) = −1. The code does exactly this: for k = b + t (t < L/2) the variable w equals ω_L^t mod p (it starts at 1
and is multiplied by `w_len` after each butterfly), and the butterfly sets a[k] = u + v, a[k + L/2] = u − v (mod p)
with u = a[k], v = a[k + L/2] · w. The butterflies of a stage touch disjoint pairs and read only their own pair. After
the last stage (s = K, one block, c = 0), a[t] = Σ_u a₀[u] ω^(ut) (ω^(−ut) for `invert`).

*(c) Inverse.* For `invert` the stages give Σ_u x_u ω^(−ut), and the final loop multiplies by n_inv = N^(p−2) = N⁻¹
(N < p is invertible). Applied to x = x̂: (1/N) Σ_t ω^(−jt) Σ_u x_u ω^(ut) = (1/N) Σ_u x_u Σ_t ω^((u−j)t) = x_j, since for
u ≠ j (|u − j| < N) ω^(u−j) ≠ 1 (ω has order N) and the geometric sum Σ_t (ω^(u−j))^t = (ω^((u−j)N) − 1)/(ω^(u−j) − 1)
is 0.

**Check.** `tests/test_proofs_ntt.py`, `TransformTests`: `_ntt` on every unit vector equals the DFT column
(ω^(jt))_t for N = 1, 2, 4, …, 64 (complete for these N: the map is linear), and `_ntt(·, True)` after `_ntt(·, False)`
is the identity on seeded vectors for N = 1, 2, 4, …, 1024.

## 7. Correctness of polynomial multiplication by the NTT, and its domain

**Statement.** For coefficient lists A and B with entries in [0, p) and len(A) + len(B) − 1 ≤ 2²³ (in particular
for n ≤ 2²² coefficients each), `polymul_ntt((A, B))` returns the coefficients of A · B mod p. For larger inputs the
transform size would be at least 2²⁴, for which Z_p has no root of unity of that order (section 5); no claim is made
there.

**Proof.** Let out_len = len(A) + len(B) − 1 and N the least power of two ≥ out_len (N ≤ 2²³ by assumption). `fa` is A
followed by zeros, so by section 6 the forward transform gives fa[t] = A(ω^t), likewise fb[t] = B(ω^t) (ω = ω_N). The
pointwise products are A(ω^t) B(ω^t) = C(ω^t) for C = A · B mod p, a polynomial with out_len ≤ N coefficients; so
`fc` is the DFT of C padded with zeros to length N, and the inverse transform (section 6 (c)) returns that padded
vector. The code returns its first out_len entries, the coefficients of C. (Empty A or B: `[]`.) This is the
padded case of the general fact behind the phrase "the DFT diagonalises cyclic convolution": for vectors x, y of
length N and z[k] = Σ over i + j ≡ k (mod N) of x_i y_j, ẑ[t] = Σ_{i,j} x_i y_j ω^((i+j)t) = x̂[t] ŷ[t], because
ω^(Nt) = 1; with out_len ≤ N no index wraps around, so z = C.

**Check.** `tests/test_proofs_ntt.py`, `CorrectnessTests` (sizes as in section 4, including n just above powers of
two, which force padding). V1.

## 8. Time bounds

**Statement.** (a) The schoolbook method makes exactly z · n coefficient multiplications, z the number of non-zero
coefficients of A, and takes Θ(n (1 + z)) time: Θ(n²) in the worst case (n² multiplications when no coefficient of A
is 0), and Θ(n) when A = 0. (b) The NTT method takes Θ(n log n) time on every input with n ≥ 2 coefficients each:
the transform size N satisfies 2n − 1 ≤ N ≤ 4n − 3, and the three transforms make exactly (3/2) N log₂ N butterflies.
Arithmetic mod p is unit cost: stored values are below p < 2³⁰, sums of two stored values below 2p < 2³¹, and
products (and the schoolbook's unreduced C[i + j] + a·b ≤ (p − 1) + (p − 1)²) below p² < 2⁶⁰.

**Proof.** (a) Section 1; the outer loop and the zero tests add Θ(n), the allocation of C Θ(n). (b) N is the least
power of two ≥ 2n − 1, so N/2 < 2n − 1, that is N < 4n − 2, and N ≤ 4n − 3 as both are integers. Each of the
three calls of `_ntt` on N entries: the bit-reversal loop runs N − 1 iterations, and its inner `while` loop runs at
most N − 1 times in total (each of its iterations clears a bit of j that an earlier `j |= bit` set, and there are
N − 1 of those); then log₂ N stages of N/2 butterflies with O(1) work each, and per stage one or two `pow` calls with
exponents below p, O(log p) = O(1) multiplications for the fixed p. The pointwise products and the final scaling add
Θ(N). No step depends on the coefficient values, so the time is Θ(N log N) = Θ(n log n) on every input. Every
stored value is reduced mod p (`% P` after each sum, difference and product), so it is below p; before the reduction a
sum u + v is below 2p and a product below p².

**Check.** (a) `experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "poly schoolbook nnz(A) * n
with planted zero coefficients": n = 1..40, 3 seeded inputs per n (planted zeros, section 1). (b) `tests/test_proofs_ntt.py`,
`SizeTests`: the module's `_ntt` wrapped by a spy (code unchanged), n = 1..300, 1000, 1025: exactly three calls, each on
N entries, with 2n − 1 ≤ N ≤ 4n − 3; and the number of executions of the butterfly line `u = a[k]` of the unchanged
`_ntt`, counted with `sys.settrace`, equals (3/2) N log₂ N for n = 1..64, 300, 1000; the exact counts of section 2 on
powers of two; the V2 fits.

## 9. Space bounds

**Statement.** Both methods use Θ(n) space.

**Proof.** Schoolbook: C has 2n − 1 entries, O(1) more. NTT: `fa`, `fb` and `fc` have N ≤ 4n − 3 entries each, plus
O(1) variables. The output has 2n − 1 entries. Every entry is below p (one word).

**Check.** `tests/test_proofs_ntt.py`, `SpaceTests`: the peak traced allocation divided by n is between 16 and 2000
and varies by a factor of at most 1.6 over four doubling sizes (NTT n = 256..2048 and 300..2400, schoolbook
n = 128..1024 and 150..1200).

## 10. Further remarks

**Statement.** (a) Only the pointwise products have two input-derived operands, and the counted butterfly products
have the plain twiddle factor as the other operand (`caveats`). (b) Both costs are polynomial and the exponent drops
from 2 to 1 (up to the log factor): T3.

**Proof.** (a) Section 2. (b) Sections 1, 2 and 8.

**Check.** (a) `experiments/2026-10-06c_ntt_counts.py` (probe part) and `experiments/2026-10-07_count_proof_checks.py`,
group `algebra`, line "NTT split: forward n log2 n each, pointwise 2n, inverse (log2 n + 1) n + 2n; butterfly twiddles
plain": n = 2, 4, …, 4096.
(b) The V2 fits.
