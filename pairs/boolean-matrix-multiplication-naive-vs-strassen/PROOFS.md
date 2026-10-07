# Proofs: Boolean matrix multiplication, schoolbook vs Strassen over the integers

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms (including the reduction to integer
matrix multiplication), every stated time and space bound, every exact operation count on its domain, the size of
the integers, and the factual caveats. Sections 1 to 3 prove the exact counts; sections 4 to 9 prove the rest.
Statements about the literature (the relation between Boolean matrix multiplication and transitive closure) are not
claims of this entry: they are listed under `background` in `entry.json`, with their sources, and are not proved
here. Each proof is followed by the deterministic scripts or tests that check its computable facts and the ranges
they check. A check covers only those ranges; the proofs cover the general statements.

The functions `_pad`, `_add`, `_sub`, `_naive` and `_strassen` of `implementations/strassen_over_integers.py` are the
same code as in `pairs/matrix-multiplication-naive-vs-strassen/implementations/strassen.py`; the proofs about them in
[that entry's PROOFS.md](../matrix-multiplication-naive-vs-strassen/PROOFS.md) apply word for word and are cited by
section.

## Counting convention

`harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`) and `__and__` (also bound as `__rand__`)
each add 1 to the module counter `_products`; `__or__`, `__ror__`, `__add__`, `__radd__`, `__sub__`, `__rsub__`
return a new `CountingInt` without counting, and the comparisons do not count. `generate_scaling(n, rng)` sets
`_products = 0` and returns two n × n matrices of `CountingInt` entries with values 0 or 1;
`reported_cost(output)` returns `_products`.

A product `x * y` or `x & y` counts exactly 1 if at least one operand is a `CountingInt` (if only the right one is,
the plain int's method returns `NotImplemented` and Python calls `__rmul__` or `__rand__`); a product of two plain
ints does not count. A sum or difference is a `CountingInt` as soon as one operand is one. The padding zeros of
`_pad` are plain ints. An entry with value 0 is still a `CountingInt`, so the values of the 0/1 entries play no role.

## 1. Schoolbook: n³ AND and n³ OR operations

**Statement.** For every n ≥ 0 and every input, `bmm_naive` performs exactly n³ AND operations and n³ OR
operations. On the counting instances the n³ ANDs are counted and the ORs are not.

**Proof.** The three nested loops run the body `c = c | (A[i][k] & Bt[j][k])` exactly once per (i, j, k), with no
early exit: n³ ANDs and n³ ORs. Both operands of `&` are input entries, so each AND counts 1. `|` is not counted by
`CountingInt` (and its first operand `c` starts as the plain int 0).

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "boolean schoolbook n^3" (counted
ANDs): n = 0..20 and the V2 sizes n = 32, 64, 128 (the V2 size 16 is inside 0..20).
`experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "boolean schoolbook: n^3 executions of the OR
line": n = 0..20.

## 2. Strassen over the integers: 7^(log₂(n/16)) · 16³ for n a power of two ≥ 16

**Statement.** For every n = 16 · 2^k (k ≥ 0) and every input, `bmm_strassen` makes exactly
7^k · 16³ = 7^(log₂(n/16)) · 16³ counted multiplications (4096, 28672, 200704, 1404928 at n = 16, 32, 64, 128).

**Proof.** For n a power of two the loop `while size < n` ends with size = n, so `_pad` adds no zero, and every
entry of every matrix passed to `_strassen` is a `CountingInt` (the inputs are; blocks are slices; `_add` and
`_sub` of counting matrices are counting). Multiplications occur only in `_naive`; the threshold `P[i][j] > 0` and
the combination of the Mᵢ do not multiply. With T(s) the counted products on two s × s counting matrices:
T(16) = 16³ (`_naive`, since 16 ≤ `CUTOFF`), and T(s) = 7 T(s/2) for s > 16 (exactly the seven calls M1, …, M7).
So T(16 · 2^k) = 7^k · 16³.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line
"boolean Strassen 7^log2(n/16)*16^3": the V2 sizes n = 16, 32, 64, 128 (n = 1, 2, 4, 8, 15, 17, 20, 24, 31, 33, 48
are reported as outside the domain).

## 3. Padding at n = 17: 24832 counted instead of 28672

**Statement.** At n = 17, on every input, `bmm_strassen` performs 28672 multiplications, of which exactly 24832 are
counted; the others multiply two plain padding-derived ints.

**Proof.** The code of `_pad`, `_add`, `_sub`, `_naive` and `_strassen` is the same as in
`pairs/matrix-multiplication-naive-vs-strassen/implementations/strassen.py`, and so is the counting rule for
products. The proof in section 3 of
[that entry's PROOFS.md](../matrix-multiplication-naive-vs-strassen/PROOFS.md) applies word for word: seven
16 × 16 products are performed (7 · 4096 = 28672); M1, …, M6 each have a fully counting operand (4096 counted each),
and in M7 = (A12 − A22)(B21 + B22) only the 256 products with k = 0 count. Total 24832.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "Strassen n = 17: 24832 counted of
28672 performed (matmul, boolean)": n = 17, the V2 seed and 5 further seeds.

## 4. Correctness

**Statement.** For every n ≥ 0 and all n × n 0/1 matrices A and B, `bmm_naive((A, B))` and `bmm_strassen((A, B))`
return the Boolean product C, C[i][j] = 1 iff A[i][k] = B[k][j] = 1 for some k.

**Proof.** *Schoolbook.* For each (i, j), `c` starts at 0 and becomes c | (A[i][k] & B[k][j]) for k = 0, …, n − 1;
on 0/1 values & is AND and | is OR, so c = 1 iff some term A[i][k] & B[k][j] is 1.

*Reduction.* Read the entries as integers and let P = AB over the integers. Then
P[i][j] = Σ_k A[i][k] B[k][j] is the number of k with A[i][k] = B[k][j] = 1, an integer in [0, n]; so P[i][j] > 0 iff
C[i][j] = 1. *Strassen part.* `bmm_strassen` returns `[]` for n = 0; otherwise it pads A and B to the next power of
two and calls `_strassen`, which returns the exact integer product of the padded matrices, whose top-left n × n block
is P (matrix-multiplication entry, PROOFS.md section 4 (a)–(c)). It then returns 1 where `P[i][j] > 0` and 0
elsewhere, that is C.

**Check.** `tests/test_proofs_strassen.py`, `StrassenIdentityTests` (the identities, and this entry's `_strassen` run
on symbolic entries at n = 32: every entry is exactly Σ_k a[i][k] b[k][j]); `CorrectnessTests.test_bmm`: seeded 0/1
matrices at densities 0.05, 0.5, 0.9 for n = 0..12, 15, 16, 17, 31, 32, 33, 48, 64, 65, against a direct
any-witness computation, and the harness's row-union check. V1 and the oracle control in
`experiments/2026-10-06f_entries_boolean_matmul.py`.

## 5. Size of the integers

**Statement** (`input.size_measure`, `correctness`, `caveats`, docstring). All entries of P are in [0, n], and every
intermediate value of the Strassen computation has absolute value below 2n² (n ≥ 1), so the integers have O(log n)
bits: arithmetic is unit cost in the word RAM, and a signed 64-bit word holds every value for n < 2³¹. In bit
complexity each arithmetic operation on such integers costs a factor polynomial in log n.

**Proof.** P ∈ [0, n] by section 4. With input entries of absolute value at most c = 1, the matrix-multiplication
entry's PROOFS.md section 7 bounds every value by c² s²/2 for padded size s ≥ 2 (and by c² = 1 for s = 1); since
s < 2n, every value is below 2n². 2n² < 2⁶³ for n < 2³¹. An operation on integers of b = O(log n) bits costs O(b²)
bit operations by the schoolbook methods. (The docstring's cruder argument, operands at most doubling per level
down and combinations at most quadrupling per level up, also gives a polynomial bound.)

**Check.** `tests/test_proofs_strassen.py`, `MagnitudeTests`: for n = 16, 17, 32, 40, 64, 128, on all-ones and seeded
0/1 inputs, the largest absolute value produced by any +, − or × is at most s²/2.

## 6. Time bounds and the additions of Strassen's algorithm

**Statement.** (a) The schoolbook method performs exactly n³ ANDs and n³ ORs: Θ(n³) on every input. (b) Strassen's
method takes Θ(n^(log₂ 7)) arithmetic operations on O(log n)-bit integers, on every input; for n = 16 · 2^k it performs
exactly 4096 · 7^k multiplications and 5632 · 7^k − 1536 · 4^k additions and subtractions, so its additions are also
Θ(n^(log₂ 7)) (`caveats`).

**Proof.** (a) Section 1. (b) The arithmetic is that of `_strassen` (matrix-multiplication entry, PROOFS.md section 5
(b) and (c)); the threshold adds n² comparisons and the padding O(n²) list work.

**Check.** (a) The scripts of section 1. (b) `tests/test_proofs_strassen.py`, `AdditionCountTests` (this entry's code,
n = 16, 32, 64, 128); the V2 fits.

## 7. The early-exit variant

**Statement** (`caveats`). A schoolbook version that stops each entry at its first true term makes only n² ANDs on
all-one factors, but it is still Θ(n³) in the worst case, for example on all-zero factors.

**Proof.** On all-zero factors no term is true, so every entry evaluates all n terms: n³ ANDs, the same as the
entry's schoolbook method, and never more than n³ on any input. On all-one factors the first term of every entry is
true: n² ANDs. (No claim is made about other dense inputs.)

**Check.** `tests/test_proofs_strassen.py`, `EarlyExitVariantTests`: the variant (written in the test) makes exactly
n³ ANDs on all-zero and n² on all-one factors, n = 0..40.

## 8. Space bounds

**Statement.** Both methods use Θ(n²) space.

**Proof.** Schoolbook: the column list `Bt` and the output, n² entries each, O(1) more. Strassen: as in the
matrix-multiplication entry's PROOFS.md section 6, plus the output; every entry has O(log n) bits (section 5).

**Check.** `tests/test_proofs_strassen.py`, `SpaceTests` (this entry's two functions, n = 32, 64, 128).

## 9. Transfer, and the T3 classification

**Statement** (`relationship`). (a) Any algorithm that computes integer matrix products transfers to the Boolean
product in the same way, with O(n²) extra work. (b) Both costs are polynomial and the exponent drops from 3 to
log₂ 7 ≈ 2.807 (T3).

**Proof.** (a) Section 4: the Boolean product is the threshold P > 0 of the integer product P = AB of the 0/1
matrices, whose entries lie in [0, n]. (b) Sections 1, 2 and 6.

**Check.** (a) `CorrectnessTests.test_bmm` exercises the threshold on Strassen's product. (b) The V2 fits.
