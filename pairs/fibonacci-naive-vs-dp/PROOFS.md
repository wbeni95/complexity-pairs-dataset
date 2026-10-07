# Proofs: Fibonacci numbers, naive recursion vs dynamic programming vs fast doubling

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
correctness of the three implementations, their exact call or iteration counts, time and space, and the bit-size
view in `caveats`, under the machine model and the machine-model assumption on `bin` and `range` stated below and
in the entry's `background`. It also records (§7) the observation in `verification.method` about what an
instrumented input can observe on CPython 3.14.2; that observation is measured, not proved. Each section
ends with the deterministic checks of its computable facts; a check covers only the values it states, the proof
covers all n ≥ 0.

**Notation and cost model.** F(0) = 0, F(1) = 1, F(k) = F(k − 1) + F(k − 2); φ = (1 + √5)/2, so φ² = φ + 1.
MASK = 2^64 − 1; for an integer x (also negative), `x & MASK` is the residue of x mod 2^64 in [0, 2^64) (Python
integers behave as infinite two's complement). A *word operation* is an addition, subtraction, multiplication,
comparison or masking of integers below 2^130 (products of two residues are below 2^128); it costs O(1). Complexities
are in the value n. Machine model (elementary operations): a Python call and return cost O(1); iterating over a
string costs O(1) per character. Machine-model assumption on library routines (stated in the entry's `background`,
not proved here): `range(n)` is a constant-size object whose iteration yields 0..n − 1 at O(1) per step (the
documentation states the constant size), and `bin(n)` builds its '0b'-prefixed binary string in time and space
O(log n) (the documentation states the format; the time is assumed). The bounds of Theorems 2 and 3 in word
operations hold under this assumption; the exact iteration counts do not depend on it.

## 1. Two facts about F

**Lemma 1.** φ^(n−2) ≤ F(n) ≤ φ^(n−1) for every n ≥ 1.

*Proof.* n = 1: φ^(−1) ≤ 1 ≤ 1. n = 2: 1 ≤ 1 ≤ φ. For n ≥ 3, F(n) = F(n − 1) + F(n − 2) lies between
φ^(n−3) + φ^(n−4) = φ^(n−4)(φ + 1) = φ^(n−2) and φ^(n−2) + φ^(n−3) = φ^(n−1). ∎

**Lemma 2 (matrix form and doubling).** With Q = [[1, 1], [1, 0]], Q^k = [[F(k+1), F(k)], [F(k), F(k−1)]] for k ≥ 1,
and for every k ≥ 0

  F(2k) = F(k) (2F(k+1) − F(k)),   F(2k+1) = F(k)² + F(k+1)².

*Proof.* Q^1 = [[F(2), F(1)], [F(1), F(0)]], and Q^(k+1) = Q^k Q = [[F(k+1) + F(k), F(k+1)], [F(k) + F(k−1), F(k)]]
has the claimed form. For k ≥ 1, Q^(2k) = (Q^k)²: its entry (1, 2) is F(k+1)F(k) + F(k)F(k−1)
= F(k)(F(k+1) + F(k−1)) = F(k)(2F(k+1) − F(k)), and its entry (1, 1) is F(k+1)² + F(k)², which are F(2k) and
F(2k+1). For k = 0 both identities read 0 = 0 and 1 = 0 + 1. ∎

## 2. Naive recursion (`implementations/naive.py`)

**Theorem 1.** For every n ≥ 0, `fib_naive(n)` returns F(n) mod 2^64, makes exactly C(n) = 2F(n + 1) − 1 calls,
reaches recursion depth max(n, 1), and calls itself only on arguments in {0, 1, …, n} (on all of them if n ≠ 1). Hence it runs in Θ(φⁿ) word
operations and Θ(n) space.

*Proof.* Correctness by induction: for n < 2 it returns n = F(n); otherwise it returns
(F(n − 1) mod 2^64 + F(n − 2) mod 2^64) & MASK = F(n) mod 2^64. Calls: C(0) = C(1) = 1 and C(n) = 1 + C(n − 1) +
C(n − 2); then C(n) + 1 = (C(n − 1) + 1) + (C(n − 2) + 1) with C(0) + 1 = 2 = 2F(1) and C(1) + 1 = 2 = 2F(2), so
C(n) + 1 = 2F(n + 1). By Lemma 1, 2φ^(n−1) − 1 ≤ C(n) ≤ 2φⁿ − 1, and each call does O(1) word operations (one
comparison; for n ≥ 2 one addition of two residues and one masking), so the time is Θ(φⁿ). Depth: the first
recursive call of fib(m) is fib(m − 1), so the chain fib(n) → fib(n − 1) → … → fib(1) has n frames, and no chain is
longer because the argument decreases by at least 1 per level and frames with argument < 2 are leaves; for n = 0
there is one frame. The arguments decrease from n, so only 0..n occur, and for n ≥ 2 all of them do (the chain
above reaches 1, and fib(2) calls fib(0)): n + 1 distinct subproblems against 2F(n + 1) − 1 calls, which is the "pure recomputation" of `relationship`. ∎

**Check.** `tests/test_proofs_fib.py`, `test_naive`: calls of `fib_naive` (profiler hook) = 2F(n + 1) − 1, depth
max(n, 1), arguments ⊆ {0..n} (equal for n ≠ 1) and value F(n) mod 2^64 (F computed exactly with unbounded
integers, independently of the three implementations), n = 0..22; `test_phi_bounds`: Lemma 1 for n = 1..300 (exact integers against 60-digit
decimals). The V1 harness compares with the OEIS values for n ≤ 25. The V2 measurement times the recursion against
φⁿ (n = 18..28); a measurement, not part of the proof.

## 3. Bottom-up DP (`implementations/dp.py`)

**Theorem 2.** For every n ≥ 0, `fib_dp(n)` runs its loop exactly n times and returns F(n) mod 2^64; it does Θ(n)
word operations (n ≥ 1) and keeps O(1) words (a, b < 2^64; `range(n)` is an O(1) object).

*Proof.* Invariant: after k iterations, a = F(k) mod 2^64 and b = F(k + 1) mod 2^64. It holds for k = 0
(a, b = 0, 1), and the step a, b = b, (a + b) & MASK maps (F(k), F(k + 1)) mod 2^64 to (F(k + 1), F(k + 2)) mod
2^64. After n iterations the function returns a. Each iteration is one addition and one masking. ∎

**Check.** `tests/test_proofs_fib.py`, `test_dp`: the loop body line runs exactly n times (trace hook) and the
value is F(n) mod 2^64 (exact F), for n = 0..300, 2000 and 10⁴; a and b stay below 2^64 at every line event.

## 4. Fast doubling (`implementations/fast_doubling.py`)

**Theorem 3.** For every n ≥ 0, `fib_fast_doubling(n)` returns F(n) mod 2^64. Its loop runs once per character of
`bin(n)[2:]`, that is n.bit_length() = ⌊log₂ n⌋ + 1 times for n ≥ 1 (once for n = 0), with O(1) word operations per
iteration; so it does Θ(log n) word operations (n ≥ 2). Its arithmetic state is O(1) words (a, b, c, d are residues
below 2^64, the products below 2^129); in addition the implementation builds the string `bin(n)` of ⌊log₂ n⌋ + 3
characters (n ≥ 1), which is as large as the input up to a constant factor.

*Proof.* Invariant: after the first j characters of `bin(n)[2:]` (read as a binary number k_j, with k_0 = 0),
(a, b) = (F(k_j), F(k_j + 1)) mod 2^64. It holds for j = 0. In a step, c = (a · ((2b − a) & MASK)) & MASK and
d = (a·a + b·b) & MASK are F(2k) and F(2k + 1) mod 2^64 by Lemma 2 (the inner masking of 2b − a does not change the
residue of the product). For the bit 0, k_{j+1} = 2k_j and (a, b) becomes (c, d) = (F(2k), F(2k + 1)); for the bit
1, k_{j+1} = 2k_j + 1 and (a, b) becomes (d, c + d) = (F(2k + 1), F(2k + 2)). After the last character k = n. For
n = 0, `bin(0)[2:]` = "0", one step from k = 0 to k = 0 returns 0. ∎

**Check.** `tests/test_proofs_fib.py`, `test_fast_doubling`: the loop body line runs n.bit_length() times (1 at
n = 0) and the value is F(n) mod 2^64 (exact F for n ≤ 10⁴, otherwise right-to-left powering of Q mod 2^64, a
method none of the implementations uses), for n = 0..1024, the five V2 sizes 2^8, 2^16, 2^32, 2^64, 2^128 and 50
random n below 2^200 (seed 1); the largest possible products of two residues are below 2^128 and 2^129.

## 5. The bit-size view (`caveats`, README)

The input is the number n, written with s = ⌈log₂(n + 1)⌉ bits. With b = log₂ n (n = 2^b), the three costs of
Theorems 1–3 are Θ(φ^(2^b)), Θ(2^b) and Θ(b) by substitution. Since n ≥ 2^(s−1) for n ≥ 1, the DP's n iterations
are at least 2^(s−1): exponential in the input length, and so is Θ(φⁿ); fast doubling does Θ(s) iterations,
polynomial (linear) in the input length. So only fast doubling is polynomial in the input size.

The exact value F(n) has ⌊log₂ F(n)⌋ + 1 bits; since (n − 2) log₂ φ ≤ log₂ F(n) ≤ (n − 1) log₂ φ
(Lemma 1), this number lies in ((n − 2) log₂ φ, (n − 1) log₂ φ + 1], i.e. n log₂ φ + O(1) bits with log₂ φ = 0.6942…; so writing F(n) alone takes Θ(n) bit
operations, while the residue mod 2^64 takes Θ(log n) word operations (Theorem 3). This is the caveat "computing
the exact F(n) costs more because F(n) has ~0.694n bits".

**Check.** `tests/test_proofs_fib.py`, `test_bit_length`: (n − 2) log₂ φ < F(n).bit_length() ≤
(n − 1) log₂ φ + 1 for n = 1..5000.

## 6. Tags

T2: the naive recursion is Θ(φⁿ) and the DP Θ(n) for the same problem (Theorems 1, 2). T3 (secondary): the DP is
Θ(n) and fast doubling Θ(log n) (Theorems 2, 3).

## 7. The statement in `verification.method` (exact-count V2 not possible): an observation, not a proof

Read off the source: `fib_fast_doubling` applies exactly one operation to its argument, `bin(n)`; everything else
runs on the characters of the string that `bin` returns, on a and b, which start from the literals 0 and 1, and on
the module constant MASK. `fib_dp` touches its argument only through `range(n)`.

Observed behaviour of the interpreter (CPython 3.14.2, measured, not proved here): `bin` and `range` of an object
that is not an int call its `__index__` exactly once, and `bin` of an int subclass does not call an overridden
`__index__`. Together with the source reading, an instrumented input value therefore observes one operation however
long the loop runs on this interpreter, so harness instrumentation of the input cannot count the work of these two
implementations. This statement is a measurement record about CPython 3.14.2 and is not covered by a proof.

**Check.** `tests/test_proofs_fib.py`, `test_input_observes_one_operation`: an int-like value that logs every
operator applied to it sees exactly one `__index__` in fast doubling (n = 2^8, 2^16, 2^32, 2^64, 2^128, 12345) and
in the DP (n = 1000), with unchanged results; an int subclass with an overridden `__index__` sees no call in fast
doubling. `experiments/2026-10-06c_value_reach_probe.py`, Part A, reports the same.

## Claim map

| Claim (location) | Proof |
|---|---|
| naive correct, C(n) = 2F(n + 1) − 1 calls, Θ(φⁿ), Θ(n) depth | Theorem 1 |
| DP invariant, Θ(n) word operations, O(1) words | Theorem 2 |
| doubling identities, invariant, Θ(log n), O(1) words plus `bin(n)` | Lemma 2, Theorem 3 |
| bit-size view; DP exponential in the input length; F(n) has ~0.694n bits | §5 |
| T2, T3 | §6 |
| exact-count V2 impossible with the code unchanged (`verification.method`, README) | §7 (observation on CPython 3.14.2, measured) |
