# Proofs: XOR convolution, naive vs fast Walsh–Hadamard transform

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
every exact operation count on its domain, the completeness of the V1 check, the operand sizes, and the factual
remarks in the caveats and notes. Sections 1 and 2 prove the exact counts; sections 3 to 9 prove the rest.
Statements about the literature or about quantum computation in general are not claims of this entry: they are
listed under `background` in `entry.json`, with their sources, and are not proved here. Each proof is followed by the
deterministic scripts or tests that check its computable facts and the ranges they check. A check covers only those
ranges; the proofs cover the general statements.

Notation: indices are n-bit strings (bitmasks), x · y = popcount(x & y) mod 2, χ_s(x) = (−1)^(s·x), N = 2ⁿ, and W is
the N × N matrix W[x][y] = (−1)^(x·y). Costs are in the unit-cost model of the entry: a ring operation on values of
O(n) bits (section 7) and an index operation each cost O(1).

## Counting convention

`harness.py`, class `CountingInt`: `__add__` (also bound as `__radd__`), `__sub__`, `__rsub__`, `__mul__` (also
bound as `__rmul__`) and `__floordiv__` each add 1 to the module counter `_ops` and return a new `CountingInt`;
`__eq__`, `__int__` and `__hash__` do not count. `generate_scaling(n, rng)` sets `_ops = 0` and returns two vectors,
each a tuple of N = 2ⁿ `CountingInt` values in [−9, 9]; `reported_cost(output)` returns `_ops`.

An operation with at least one `CountingInt` operand counts exactly 1 (if only the right operand is one, the int
method returns `NotImplemented` and Python calls the reflected method), and its result is a `CountingInt`. `int`
has no `__iadd__`, so `h[k] += x` is evaluated as `h[k] = h[k] + x`. Index arithmetic (`i ^ j`, loop counters) is
plain and does not count.

## 1. Naive: 4ⁿ multiplications and 4ⁿ additions, 2 · 4ⁿ counted operations

**Statement.** For every n ≥ 0 and every input of the scaling form, `xor_convolution_naive` performs exactly 4ⁿ
multiplications and 4ⁿ additions, all counted: 2 · 4ⁿ.

**Proof.** The body `h[i ^ j] += ai * b[j]` runs once for each of the N² = 4ⁿ pairs (i, j), with no early exit.
`ai * b[j]` multiplies two input values (1 count); the addition counts 1 also when `h[i ^ j]` is still the plain
int 0 (through `__radd__`).

**Check.** `experiments/2026-10-07b_xor_convolution_counts.py` (n = 0..9). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "XOR naive 2*4^n": n = 0..9 (includes the V2 sizes n = 3..9).
`experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "OR and XOR convolution, zeta: counts per
operation kind": n = 0..9.

## 2. FWHT: 3n · 2ⁿ additions and subtractions, 2ⁿ multiplications, 2ⁿ divisions, (3n + 2) · 2ⁿ

**Statement.** For every n ≥ 0 and every input of the scaling form, `xor_convolution_fwht` performs exactly
3n · 2ⁿ additions and subtractions (2ⁿ per stage of each transform), 2ⁿ multiplications and 2ⁿ exact divisions,
all counted: (3n + 2) · 2ⁿ operations.

**Proof.** In `_fwht`, `half` takes the values 1, 2, …, 2^(n−1), n stages. A stage visits each block
`range(start, start + 2 * half)` and, for its first half, executes the butterfly `a[i] = u + v`,
`a[i + half] = u - v`: 2^(n−1) butterflies per stage, each with one counted addition and one counted subtraction
(every entry of `a` is a `CountingInt`, initially and after each update), 2ⁿ per stage and n · 2ⁿ per transform.
`xor_convolution_fwht` runs `_fwht` three times (3n · 2ⁿ), the 2ⁿ products `x * y` of two `CountingInt` values, and
the 2ⁿ divisions `x // size` with `x` a `CountingInt` (`__floordiv__`, 1 count each). Total (3n + 2) · 2ⁿ.

**Check.** `experiments/2026-10-07b_xor_convolution_counts.py` (n = 0..14). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "FWHT (3n+2)2^n": n = 0..14 (includes the V2 sizes n = 4, 6, …, 14).
`experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "OR and XOR convolution, zeta: counts per
operation kind": n = 0..12.

## 3. Correctness of the naive method

**Statement.** For every n ≥ 0, `xor_convolution_naive((a, b))` returns h with h[k] = Σ over i ^ j = k of
a[i] b[j].

**Proof.** `h` starts as zeros and the double loop visits every pair (i, j) once, adding a[i] b[j] to h[i ^ j].

**Check.** `tests/test_proofs_xor_convolution.py`, `CorrectnessTests`: every pair of unit vectors for n = 0..4 (a
complete check, since the function is bilinear in (a, b)) and 3 seeded random inputs for each n = 0..9, against a
separate definition loop. V1 (`harness.check`).

## 4. Correctness of the FWHT method

**Statement.** For every n ≥ 0, `_fwht(v)` returns W v, and `xor_convolution_fwht((a, b))` returns the XOR
convolution h of a and b; the final division by N is exact.

**Proof.** *Characters are multiplicative.* s & (i ^ j) = (s & i) ^ (s & j), and popcount(x ^ y) ≡ popcount(x) +
popcount(y) (mod 2), so s · (i ^ j) = s · i + s · j (mod 2) and χ_s(i ^ j) = χ_s(i) χ_s(j).

*Convolution theorem.* (W h)[s] = Σ_k h[k] χ_s(k) = Σ_{i, j} a[i] b[j] χ_s(i ^ j) = (Σ_i a[i] χ_s(i))(Σ_j b[j] χ_s(j))
= (W a)[s] (W b)[s].

*W W = N I.* (W W)[x][z] = Σ_y (−1)^(y·x + y·z) = Σ_y (−1)^(y·(x ^ z)). For x = z every term is 1 (sum N). For x ≠ z
pick a bit t set in x ^ z; y ↦ y ^ 2^t pairs the indices and flips the sign of the term, so the sum is 0. W is
symmetric.

*The stages compute W.* In the stage with `half` = 2^s, the blocks `range(start, start + 2 * half)` partition the
indices, and for each i in the first half of a block (bit s of i is 0) the butterfly replaces (a[i], a[i + 2^s]) by
(u + v, u − v), u = a[i], v = a[i + 2^s]. Each index is touched by exactly one butterfly, which reads only its two
entries, so the stage maps a to a′ with a′[x] = Σ over t ∈ {0, 1} of H₁[x_s][t] · a[x with bit s set to t], where
H₁ = [[1, 1], [1, −1]]: the Kronecker product with H₁ at bit s and identities elsewhere. The stages for
s = 0, …, n − 1 commute (they act on different bits) and their product has entry Π_s H₁[x_s][y_s] = Π_s (−1)^(x_s y_s)
= (−1)^(x·y) = W[x][y]. So `_fwht(v)` = W v (for n = 0 no stage runs and W = [1]).

*The algorithm.* fa = W a, fb = W b, `prod` = (W a)·(W b) = W h (convolution theorem), and `_fwht(prod)` = W W h = N h.
Every entry N h[k] is an integer multiple of N, so `x // size` returns h[k] exactly (Python's floor division of an
exact multiple, negative ones included, is the exact quotient).

**Check.** `tests/test_proofs_xor_convolution.py`, `TransformTests`: multiplicativity exhaustive for n = 0..6;
`_fwht` on every unit vector equals the column of W (complete, the map is linear) and applying it twice gives N times
the vector, n = 0..7; W is the Kronecker power of H₁, n = 1..5. `CorrectnessTests` (unit-vector pairs n = 0..4,
complete; random n = 0..9). V1 (`harness.check`, complete for n ≤ 8, section 9).

## 5. Time bounds

**Statement.** The naive method takes Θ(4ⁿ) = Θ(N²) time and the FWHT method Θ(n · 2ⁿ) = Θ(N log N) time (n ≥ 1),
on every input.

**Proof.** Naive: 4ⁿ inner iterations with one multiplication, one addition and one XOR each (section 1). FWHT: each
of the three transforms runs n stages of 2^(n−1) butterflies of O(1) work (section 2), plus 2ⁿ products, 2ⁿ
divisions and the copies: Θ(n · 2ⁿ). 4ⁿ = N² and n · 2ⁿ = N log₂ N.

**Check.** The exact counts of sections 1 and 2 (scripts listed there) and the V2 fits.

## 6. Space bounds

**Statement.** Both methods use Θ(2ⁿ) space.

**Proof.** Naive: the list `h` (2ⁿ entries) plus O(1) variables. FWHT: at most five lists of 2ⁿ entries are alive at
once (fa, fb, `prod`, the result h of the third `_fwht`, and the list of quotients while it is built), plus O(1)
variables. The output has 2ⁿ entries. Each entry is an integer of O(n) bits (section 7), one word in the unit-cost
model; in bytes, an integer object grows with its bit length.

**Check.** `tests/test_proofs_xor_convolution.py`, `SpaceTests`, with a byte bound derived for CPython that grows with
the integer sizes and is therefore valid for every n: the peak traced allocation is at least 8 · 2ⁿ bytes and at most
2ⁿ · (6 · 9 + 5 · b(8 + 3n)) + 4096 bytes for the FWHT (five lists and one transient copy while a list grows, at most
9 bytes per slot since CPython over-allocates a growing list by at most one eighth, and at most five integer objects
per entry, b(β) being the size of an integer object of β bits rounded up to 16 bytes) and at most
2ⁿ · (9 + b(7 + n)) + 4096 bytes for the naive method (|h[k]| ≤ 81 · 2ⁿ < 2^(7+n)); checked for naive n = 4..10 and
FWHT n = 4..15.

## 7. Operand sizes

**Statement** (`caveats`, `input.size_measure`). If every entry of a and b has absolute value below 2^B, then the
operands of the two forward transforms stay below 2^(B + n), the pointwise products below 2^(2B + 2n), and the
operands of the inverse transform below 2^(2B + 3n). With the harness entries (|entry| ≤ 9 < 2⁴) every intermediate
value has O(n) bits.

**Proof.** A butterfly (u, v) ↦ (u + v, u − v) gives values of absolute value at most 2 max(|u|, |v|), so a stage at
most doubles the largest absolute value. The forward transforms start below 2^B and have n stages: below 2^(B + n).
Products of two such values are below 2^(2B + 2n), and the n stages of the inverse transform bring them below
2^(2B + 3n). The quotients are the entries of h; h[k] is a sum of N products of absolute value below 2^(2B), so
|h[k]| < 2^(2B + n). With B = 4 all values are below 2^(3n + 8).

**Check.** `tests/test_proofs_xor_convolution.py`, `BitGrowthTests`: the largest absolute value produced by any
operation in each phase, n = 0..12, B = 4 and 10, on the constant input 2^B − 1 (which reaches 2ⁿ (2^B − 1) in the
forward transform), on (2^B − 1, −(2^B − 1)) and on 2 seeded inputs per (n, B).

## 8. Rings where N is a zero divisor

**Statement** (`caveats`). Over a commutative ring R in which N = 2ⁿ is a zero divisor, for example Z₂ (where N = 0
for n ≥ 1) or Z₄, the pointwise product (W a)·(W b) does not determine the XOR convolution h, so h must be computed
differently. Over the integers N is not a unit, but it is not a zero divisor: N h determines h, and the division of the
entry's method is exact (section 4).

**Proof.** Let c ≠ 0 with N c = 0, and let 𝟙 be the all-ones vector. W 𝟙 = N e₀, because Σ_y (−1)^(x·y) is N for x = 0
and 0 otherwise (section 4). So W (c 𝟙) = c N e₀ = 0 = W 0. The inputs (a, b) = (c 𝟙, e₀) and (0, e₀) have the XOR
convolutions c 𝟙 ≠ 0 and 0 (e₀ is the unit of XOR convolution), but the same pointwise product (W a)·(W b) = W h = 0.
So no procedure that works from the transforms can return h on both. Over Z₂ more is true: −1 = 1, every entry of W is
1 and W has rank 1, so even the unit vectors e₀ and e₁ have the same transform. Over the integers, N h = W((W a)·(W b))
(section 4) and N ≠ 0 in the domain Z, so h is determined and `x // size` returns it exactly.

**Check.** `tests/test_proofs_xor_convolution.py`, `ModTwoTests`: over Z₂, e₀ and e₁ have the same transform
(n = 1..8); over Z₄ (c = 2), the transform of 2 · 𝟙 is 0 while 2 · 𝟙 is the XOR convolution of (2 · 𝟙, e₀) (n = 1..8).

## 9. The V1 check, the T3 classification, and the remarks in the notes

**Statement.** (a) The V1 check, the convolution theorem tested at every character, determines h uniquely
(`verification.method`, n ≤ 8). (b) Both costs are polynomial in the input size N = 2ⁿ and the exponent drops (T3).
(c) W = 2^(n/2) H^⊗n, where H = 2^(−1/2) [[1, 1], [1, −1]], and H^⊗n is the product of the n single-qubit Hadamard gates
I ⊗ … ⊗ H ⊗ … ⊗ I; `lib/qsim.py` (`State.h_all`) applies it this way, one butterfly stage per qubit with 2ⁿ additions
and subtractions per stage. (d) The Forrelation quantity Φ(f, g) = N^(−3/2) Σ_y (W f)[y] g[y] is computed exactly by one
FWHT, N products and a sum once the 2N values are known. (e) Yates' zeta transform has the same stage structure with
[[1, 0], [1, 1]] in place of [[1, 1], [1, −1]].

**Proof.** (a) The check tests (W h′)[s] = (W a)[s] (W b)[s] for every s; by section 4 the right side is (W h)[s]. W is
invertible over the rationals (W W = N I), so W h′ = W h forces h′ = h. (b) Θ(N²) and Θ(N log N) are polynomial in N,
and N log N = o(N²). (c) H^⊗n[x][y] = Π_s 2^(−1/2) (−1)^(x_s y_s) = 2^(−n/2) W[x][y]; the product of the single-qubit
gates is the Kronecker product (as for the stages in section 4). `State.h(k)` performs, for every index i with bit k
clear, the butterfly (x, y) ↦ ((x + y) s, (x − y) s) with s = 2^(−1/2): 2^(n−1) butterflies, 2ⁿ additions and
subtractions per qubit, and `h_all` applies it to every qubit. (d) Direct from the definition of Φ and section 4.
(e) Proved in `pairs/subset-sum-zeta-transform-naive-vs-yates/PROOFS.md`, section 5.

**Check.** (a) V1 (`harness.check`). (c), (d) `tests/test_proofs_xor_convolution.py`, `QuantumRemarkTests`:
`State.h_all` on every basis state equals the column of W times 2^(−n/2), n = 0..6; the one-transform value of Φ
equals the double sum on seeded ±1 functions, n = 0..7. (e) `tests/test_proofs_zeta.py`.
