# Proofs: matrix multiplication, schoolbook vs Strassen

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
every exact operation count on its domain, the value sizes behind the unit-cost model, and the step from a fixed-size
multiplication scheme to an exponent bound. Sections 1 to 3 prove the exact counts; sections 4 to 9 prove the rest.
Statements about the literature (the line of exponent bounds after Strassen, and the existence of the AlphaTensor
scheme) are not claims of this entry: they are listed under `background` in `entry.json`, with their sources, and
are not proved here. Each proof is followed by the deterministic scripts or tests that check its computable facts and
the ranges they check. A check covers only those ranges; the proofs cover the general statements.

## Counting convention

`harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`) adds 1 to the module counter `_mults`;
`__add__`, `__radd__`, `__sub__`, `__rsub__` return a new `CountingInt` without counting. `generate_scaling(n, rng)`
sets `_mults = 0` and returns two n × n matrices of `CountingInt` entries (values in [−9, 9]);
`reported_cost(output)` returns `_mults`.

A product `x * y` counts exactly 1 if at least one operand is a `CountingInt`: if `x` is one, `x.__mul__` runs; if
only `y` is one, `int.__mul__` returns `NotImplemented` and Python calls `y.__rmul__`. A product of two plain ints
does not count. A sum or difference is a `CountingInt` as soon as one operand is one (by the same rule), and a
plain int only if both operands are plain. The padding zeros of `_pad` are plain ints.

## 1. Schoolbook: n³

**Statement.** For every n ≥ 0 and every input, `matmul_naive` makes exactly n³ counted multiplications.

**Proof.** For each of the n² pairs (i, j) the generator inside `sum` evaluates `A[i][k] * Bt[j][k]` for
k = 0, …, n − 1, with both operands input entries (`CountingInt`). That is n³ counted products; `sum` only adds.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "matmul schoolbook n^3":
n = 0..20 and the V2 sizes n = 32, 64, 128, 256.

## 2. Strassen: 7^(log₂(n/16)) · 16³ for n = 16 · 2^k

**Statement.** For every n = 16 · 2^k (k ≥ 0) and every input, `matmul_strassen` makes exactly
7^k · 16³ = 7^(log₂(n/16)) · 16³ counted multiplications.

**Proof.** For n a power of two the loop `while size < n` ends with size = n, so `_pad` adds no zero. Every entry of
every matrix passed to `_strassen` is then a `CountingInt`: the inputs are, the blocks `A11`, …, `B22` are slices,
and `_add` and `_sub` of two counting matrices give counting entries. Multiplications occur only in `_naive`; the
combination of the Mᵢ only adds and subtracts. Let T(s) be the counted products of `_strassen` on two s × s counting
matrices, s = 16 · 2^j. If s = 16 ≤ `CUTOFF`, `_naive` evaluates `a * b` for every (row, column, k), s³ = 16³
counted products. If s > 16, the call makes exactly the seven calls M1, …, M7 on s/2 × s/2 counting matrices and no
other product, so T(s) = 7 T(s/2). Hence T(16 · 2^k) = 7^k · 16³.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line
"matmul Strassen 7^log2(n/16)*16^3": n = 16 and the V2 sizes n = 32, 64, 128, 256 (n = 1, 2, 4, 8, 15, 17, 20, 24,
31, 33, 48 are reported as outside the domain).

## 3. Padding at n = 17: 24832 counted of 28672 performed

**Statement.** At n = 17, on every input, `matmul_strassen` performs 28672 multiplications, of which exactly 24832
are counted; the uncounted ones are products of two plain ints that come from padding zeros alone.

**Proof.** size = 32, so the top call splits the padded 32 × 32 matrices into 16 × 16 blocks and makes seven calls
on 16 × 16 matrices, each of which goes straight to `_naive` (16 ≤ `CUTOFF`): 7 · 16³ = 28672 products are
performed. Which entries are counting: `A11` (rows and columns 0..15 of A) is fully counting; `A12` (rows 0..15,
columns 16..31) is counting exactly in its column 0 (column 16 of A); `A21` exactly in its row 0; `A22` exactly at
(0, 0) (entry A[16][16]); the same for B. A sum or difference of two blocks is counting exactly where one of them
is. In `_naive(X, Y)` the product for (i, j, k) is `X[i][k] * Y[k][j]`, counted iff `X[i][k]` or `Y[k][j]` is
counting.
- M1 = (A11 + A22)(B11 + B22), M3 = A11 (B12 − B22), M5 = (A11 + A12) B22, M6 = (A21 − A11)(B11 + B12): the left
  operand is fully counting (it contains `A11`), so all 4096 products count.
- M2 = (A21 + A22) B11 and M4 = A22 (B21 − B11): the right operand is fully counting, so all 4096 count.
- M7 = (A12 − A22)(B21 + B22): the left operand is counting exactly in column 0 (column 0 of `A12`, and `A22`
  adds only (0, 0)), the right operand exactly in row 0. So (i, j, k) counts iff k = 0: 16 · 16 = 256 products.

Total 6 · 4096 + 256 = 24832.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "Strassen n = 17: 24832 counted of
28672 performed (matmul, boolean)": n = 17, the V2 seed and 5 further seeds. (The line "matmul Strassen
7^log2(n/16)*16^3" of `experiments/2026-10-07_closed_form_checks.py` also prints the count 24832 at n = 17.)

## 4. Correctness

**Statement.** For every n ≥ 0 and all n × n integer matrices A and B, `matmul_naive((A, B))` and
`matmul_strassen((A, B))` return AB.

**Proof.** *Schoolbook.* Entry (i, j) is `sum(A[i][k] * Bt[j][k] for k in range(n))` with `Bt[j]` the column j of
B: the definition Σ_k A[i][k] B[k][j].

*(a) Strassen's seven products.* Let R be any ring (associative, with 1, not necessarily commutative), and let
A11, A12, A21, A22, B11, B12, B21, B22 ∈ R. With the seven products of `_strassen`,

M1 = (A11 + A22)(B11 + B22) = A11B11 + A11B22 + A22B11 + A22B22,
M2 = (A21 + A22)B11 = A21B11 + A22B11,
M3 = A11(B12 − B22) = A11B12 − A11B22,
M4 = A22(B21 − B11) = A22B21 − A22B11,
M5 = (A11 + A12)B22 = A11B22 + A12B22,
M6 = (A21 − A11)(B11 + B12) = A21B11 + A21B12 − A11B11 − A11B12,
M7 = (A12 − A22)(B21 + B22) = A12B21 + A12B22 − A22B21 − A22B22,

each expansion uses only the distributive laws and x(−y) = (−x)y = −xy, and keeps every A-factor to the left of
every B-factor; no two factors are commuted. Adding:

C11 = M1 + M4 − M5 + M7 = A11B11 + A12B21 (the terms A11B22, A22B11, A22B22, A22B21, A12B22 cancel),
C12 = M3 + M5 = A11B12 + A12B22 (A11B22 cancels),
C21 = M2 + M4 = A21B11 + A22B21 (A22B11 cancels),
C22 = M1 − M2 + M3 + M6 = A21B12 + A22B22 (A11B11, A11B22, A22B11, A21B11, A11B12 cancel).

These are the four blocks of the 2 × 2 block product, so the identities hold in every ring, in particular in the
ring of h × h integer matrices.

*(b) The recursion.* Claim: for every power of two s and s × s integer matrices X, Y, `_strassen(X, Y)` returns XY.
For s ≤ `CUTOFF` = 16, `_naive` evaluates the definition (rows of X against columns of Y). For s > 16, h = s/2 is a
power of two; the code takes the four h × h blocks of each operand (`A11` = rows 0..h − 1, columns 0..h − 1, and so
on); by induction the seven recursive calls return the seven products of (a) computed in the ring of h × h integer
matrices; `_add` and `_sub` are entrywise; and the result is assembled as [[C11, C12], [C21, C22]]. Splitting the
sum Σ_k X[i][k] Y[k][j] at k = h shows that the blocks of XY are X11Y11 + X12Y21, …, X21Y12 + X22Y22, which by (a)
are C11, …, C22.

*(c) Padding.* `matmul_strassen` returns `[]` for n = 0. Otherwise size is the smallest power of two ≥ n, and
`_pad` returns the size × size matrices A′ = [[A, 0], [0, 0]] and B′ = [[B, 0], [0, 0]]. By (b) the call returns
A′B′, and by the block product A′B′ = [[AB, 0], [0, 0]]; the code returns its top-left n × n block, AB.

The instrumented entries of the V2 instances (`CountingInt` in `harness.py`) add, subtract and multiply their
values exactly like integers, so the same holds on them.

**Check.** `tests/test_proofs_strassen.py`, `StrassenIdentityTests`: the four identities expanded as non-commutative
bilinear forms in the eight block symbols (A-symbol always left), from an independent transcription of the seven
products; and the unchanged `_strassen` of this entry (and of the Boolean entry) run at n = 32, one level above the
cutoff, on symbolic entries a[i][k], b[k][j]: every output entry is exactly the bilinear form Σ_k a[i][k] b[k][j].
`CorrectnessTests`: seeded integer matrices with entries in [−9, 9] at n = 0..12, 15, 16, 17, 31, 32, 33, 48, 64,
65 (sizes that need padding included). V1 (`harness.check`, an exact entry-by-entry recomputation).

## 5. Time bounds and the additions of Strassen's algorithm

**Statement.** (a) The schoolbook method makes n³ multiplications and n³ additions: Θ(n³) time on every input.
(b) For n = 16 · 2^k, Strassen's code performs exactly 4096 · 7^k multiplications and exactly
5632 · 7^k − 1536 · 4^k additions and subtractions. (c) For every n, Strassen's code takes Θ(n^(log₂ 7)) time on
every input (unit-cost arithmetic; section 7).

**Proof.** (a) Each of the n² entries is a `sum` of n products; `sum` starts from 0 and adds each product: n
multiplications and n additions per entry.

(b) Let s = 16 · 2^j be the size of a call. A leaf (s = 16) runs `_naive`: 16³ products and, as in (a), 16³
additions. An internal call (s > 16) computes ten operand sums or differences (`A11 + A22`, `B11 + B22`,
`A21 + A22`, `B12 − B22`, `B21 − B11`, `A11 + A12`, `A21 − A11`, `B11 + B12`, `A12 − A22`, `B21 + B22`) and eight in
the combinations (three for C11, one each for C12 and C21, three for C22), each on (s/2)² entries: 18 (s/2)² = 4.5 s²;
the block slicing and the final assembly are list operations, not arithmetic. So the additions satisfy
A(16) = 4096 and A(s) = 7 A(s/2) + 4.5 s², and the multiplications P(16) = 4096, P(s) = 7 P(s/2). Hence
P(16 · 2^k) = 4096 · 7^k (performed products; section 2 counts the subset with an instrumented operand), and

A(16 · 2^k) = 4096 · 7^k + Σ_{j=0..k−1} 7^j · 4.5 · (16 · 2^(k−j))² = 4096 · 7^k + 1152 · 4^k · ((7/4)^k − 1)/(3/4)
= 5632 · 7^k − 1536 · 4^k.

(c) For 1 ≤ n ≤ 16 the call is one `_naive` on at most 16 × 16 matrices: O(1). For 16 < n, the padded size is
s = 16 · 2^k with s/2 < n ≤ s. Each internal call does Θ(s²) list work (slices, `_add`, `_sub`, assembly) besides its
4.5 s² additions, and each leaf Θ(1); so the total is Θ(P + A) = Θ(7^k) by (b), and the padding costs Θ(s²) = O(7^k).
With 7^k = (s/16)^(log₂ 7) and n ≤ s < 2n this is Θ(n^(log₂ 7)).

**Check.** (a) `experiments/2026-10-07_closed_form_checks.py` (multiplications, section 1). (b)
`tests/test_proofs_strassen.py`, `AdditionCountTests`: an instrumented integer counting +, − and × on the unchanged
code of both entries, n = 16, 32, 64, 128 (k = 0..3): additions 5632 · 7^k − 1536 · 4^k and multiplications
4096 · 7^k exactly. (c) The V2 fits on exact multiplication counts.

## 6. Space bounds

**Statement.** Both methods use Θ(n²) space.

**Proof.** Schoolbook: the column list `Bt` (n² references) and the output (n² entries), O(1) more. Strassen: the
padded copies and the output take Θ(s²) with n ≤ s < 2n. Consider a call of size s > 16. While one of its recursive
calls runs, it holds its eight blocks (2 s² entries in all), at most six finished products and the two operands of
the running call (each (s/2)² entries); during the combinations it holds the blocks, the seven products, the four
C-blocks and one temporary block. So the call's own live data is at most c · s² entries for a constant c, and the
peak satisfies S(s) ≤ c s² + S(s/2) (only one recursive call runs at a time), S(16) = O(1), hence
S(s) ≤ (4/3) c s² + O(1). Every entry is an integer of O(log n) bits (section 7), one word in the unit-cost model.
The output alone has n² entries.

**Check.** `tests/test_proofs_strassen.py`, `SpaceTests`: for n = 32, 64, 128 the peak traced allocation divided by
n² is between 8 and 400 and varies by a factor of at most 1.5 (a quantity growing like n^2.807 would vary by a factor
of about 3.1 over this range), for both methods.

## 7. Value sizes (unit cost)

**Statement** (`input.size_measure`, "small integers in the harness, so arithmetic is unit cost"). If every input
entry has absolute value at most c ≥ 1 (c = 9 in the harness) and the padded size is s ≥ 2, every value that
Strassen's code computes has absolute value at most c² s²/2 < 2c² n²; the schoolbook method's values are at most
c² n. So all values have O(log n) bits.

**Proof.** Number the calls by depth j (the top call has depth 0 and size s, a call at depth j has size s/2^j).
*Operands.* The operands of a call at depth j have entries of absolute value at most 2^j c: true at depth 0 (padding
zeros included), and a child's operands are blocks or sums or differences of two blocks of its parent's operands.
*Results.* By section 4 a call at depth j returns the exact product of its operands, whose entries are at most
(s/2^j) · (2^j c)² = s 2^j c² in absolute value. *Values inside a call.* A leaf (size ≤ 16) computes the partial
sums of one entry of its product: at most (s/2^j) · 4^j c² = s 2^j c². An internal call at depth j has size
s/2^j > 16, so 2^j < s/16; its operand sums are at most 2^(j+1) c, its seven products at most s 2^(j+1) c², and
the partial sums in the combinations (at most four products) at most 8 s 2^j c² < c² s²/2. A leaf at depth j ≥ 1 has
size 16 = s/2^j, so s 2^j c² = c² s²/16; a leaf at depth 0 has size s ≤ 16 and its values are at most s c² ≤ c² s²/2
for s ≥ 2. The operand bounds 2^(j+1) c ≤ s c are below c² s²/2 too. Finally s < 2n. The schoolbook partial sums are
sums of at most n products of absolute value at most c².

**Check.** `tests/test_proofs_strassen.py`, `MagnitudeTests`: the largest absolute value produced by any +, − or ×
of the unchanged code, n = 16, 17, 32, 40, 64, 128, on the all-9 times all-(−9) input and on seeded inputs (c = 9),
and for the Boolean entry's copy on all-ones and seeded 0/1 inputs (c = 1): at most c² s²/2 in every case.

## 8. From a fixed-size scheme to an exponent bound

**Statement** (`relationship`, `notes`, README). (a) Let K be a commutative ring and suppose that k × k matrices can be
multiplied by a bilinear scheme with r products whose coefficients lie in K (products
M_t = (Σ α_t[i, j] A_ij)(Σ β_t[j, l] B_jl) and C_il = Σ_t γ_t[l, i] M_t), valid in K, that is, the Brent equations
Σ_t α_t[i, j] β_t[j′, l] γ_t[l′, i′] = [j = j′][l = l′][i′ = i] hold in K. If r > k², then n × n matrices over any
commutative K-algebra can be multiplied with O(n^(log_k r)) ring operations, so ω ≤ log_k r over every field that
contains K. (b) Applied recursively, Strassen's scheme (k = 2, r = 7, valid over the integers by section 4) is this
entry's algorithm; two levels of it (its Kronecker square) form a scheme for 4 × 4 matrices with 7² = 49 products.
(c) Conditional statement: if a rank-47 bilinear scheme for ⟨4, 4, 4⟩ over GF(2) exists (background: Fawzi et al.
2022, Fig. 3), then ω ≤ log₄ 47 ≈ 2.7773 for every field of characteristic 2. The existence of such a scheme is not
proved here. Only a recursive application of a fixed-size scheme gives an asymptotic statement.

**Proof.** (a) Let R be the ring of m × m matrices over a commutative K-algebra; K acts on R by central scalars.
For block matrices with blocks in R, expanding Σ_t γ_t[l, i] M_t by distributivity gives
Σ over (i1, j1, j2, l2) of (Σ_t α_t[i1, j1] β_t[j2, l2] γ_t[l, i]) A_{i1 j1} B_{j2 l2}, with every A-block left of every
B-block, so by the Brent equations it equals Σ_j A_ij B_jl, the block product. Recursing on blocks as in section 4 (b)
multiplies km × km matrices with r products of m × m matrices plus a fixed number e of block operations: additions
of two m × m blocks and multiplications of an m × m block by a coefficient of K (forming the linear combinations
Σ α_t[i, j] A_ij, Σ β_t[j, l] B_jl and Σ_t γ_t[l, i] M_t), each costing m² ring operations. For n = k^L this gives r^L
scalar products, and the other operations satisfy A(k^L) = r A(k^(L−1)) + e k^(2(L−1)), so
A(k^L) ≤ e Σ_j r^j k^(2(L−1−j)) = O(r^L) because r > k². For other n, pad to the next power of k (< kn), which costs a
constant factor: O(n^(log_k r)) operations, hence ω ≤ log_k r. (b) Section 4; the Kronecker square of a rank-7
scheme for ⟨2, 2, 2⟩ is a scheme for ⟨4, 4, 4⟩ with 7 · 7 = 49 products. (c) A field of characteristic 2 contains
GF(2), so a scheme valid over GF(2) is valid over it, and (a) applies with k = 4, r = 47 > 16 = k²;
log₄ 47 = ln 47 / ln 4 = 2.77729…
A single fixed-size scheme only multiplies fixed-size matrices; the exponent comes from the recursion in (a).

**Check.** `tests/test_proofs_strassen.py`, `SchemeRecursionTests`: a direct recursive application of GF(2) schemes
(Strassen's scheme from `search/gf2mm.py`, k = 2, r = 7, n = 2, 4, 8, 16; its Kronecker square, k = 4, r = 49,
n = 4, 16): both schemes pass the exact GF(2) verifier, the recursion returns AB mod 2 on seeded 0/1 matrices and
makes exactly r^L scalar products; log₄ 47 rounds to 2.7773.

## 9. Further remarks

**Statement.** (a) Over the integers all arithmetic of both methods is exact. (b) Both costs are polynomial and the
exponent drops from 3 to log₂ 7 ≈ 2.807 (`pair_type` T3).

**Proof.** (a) Only +, − and × on Python integers occur (no division, no rounding). (b) Sections 5 (a) and (c);
log₂ 7 = 2.8073… < 3.

**Check.** (b) The V2 fits on exact counts (each algorithm's rival rejected).
