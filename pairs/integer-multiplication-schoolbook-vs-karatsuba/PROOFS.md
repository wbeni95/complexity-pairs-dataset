# Proofs: integer multiplication, schoolbook vs Karatsuba

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound
(for every n, not only for powers of two), every exact operation count on its domain, and the word-size bound behind
the unit-cost model. Sections 1 to 3 prove the exact counts; sections 4 to 9 prove the rest. Statements about the
literature (the later, faster algorithms and the models they are stated in) are not claims of this entry: they are
listed under `background` in `entry.json`, with their sources, and are not proved here. Each proof is followed by the
deterministic scripts or tests that check its computable facts and the ranges they check. A check covers only those
ranges; the proofs cover the general statements.

Notation: B = 2¹⁵ = `BASE`; a digit list d_0, …, d_(L−1) (little-endian) has value Σ d_k B^k; "the digits of V" means
the list of base-B digits of V, of a stated length. For t ≥ 0, `t & MASK` = t mod B and `t >> BITS` = ⌊t/B⌋; for
−B ≤ t < 0 the same expressions give t mod B ∈ [0, B) and ⌊t/B⌋ = −1 (Python's bitwise operations on negative
integers act on the two's-complement expansion).

## Counting convention

`harness.py`, class `CountingDigit`: `__mul__` (also bound as `__rmul__`) adds 1 to the module counter `_mults`;
every other arithmetic method (`__add__`, `__sub__`, `__rsub__`, `__neg__`, `__and__`, `__or__`, `__rshift__`,
`__lshift__`, and their reflected forms) returns a new `CountingDigit` without counting, and comparisons, `__bool__`
and `__index__` do not count. `generate_scaling(n, rng)` draws two n-digit factors with digits uniform in
[1, 2^15 − 1], wraps every digit in `CountingDigit` and sets `_mults = 0`; `reported_cost(output)` returns `_mults`.

A product `x * y` counts exactly 1 if at least one operand is a `CountingDigit` (if only `y` is, `int.__mul__`
returns `NotImplemented` and Python calls `y.__rmul__`); a product of two plain ints does not count. Any other
operation with a `CountingDigit` operand returns a `CountingDigit`. `CountingDigit.__ne__` compares digit values.

## 1. Schoolbook: n² digit multiplications

**Statement.** For every n ≥ 0, `multiply_schoolbook` performs exactly n² multiply-adds on every input, and on
`CountingDigit` inputs exactly n² counted multiplications.

**Proof.** The inner statement `t = res[k] + ai * bj + carry` runs once for each pair (i, j), n² times, with no
early exit, and contains the only multiplication. Both `ai` and `bj` are input digits, so on `CountingDigit`
inputs each product counts 1.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "integer schoolbook n^2":
n = 0..32 and the V2 sizes n = 64, 128, 256, 512, 1024.

## 2. Karatsuba below the cutoff: n² for n ≤ 32

**Statement.** For 0 ≤ n ≤ 32, `multiply_karatsuba` makes exactly n² counted multiplications on `CountingDigit`
inputs.

**Proof.** n = 0 returns `[]` without multiplying. For 1 ≤ n ≤ 32 = `CUTOFF`, `_karatsuba` calls `_schoolbook`
directly, which evaluates `xi * yj` once per pair of input digits (section 1): n² counted products.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "Karatsuba n<=32: n^2":
n = 0..32.

## 3. Karatsuba: 3^(log₂(n/32)) · 32² for n = 32 · 2^k, exactly when no node has equal halves in both factors

**Statement.** Let n = 32 · 2^k (k ≥ 0) and let both factors consist of `CountingDigit` digits. Call a recursive
call `_karatsuba(x, y)` with more than 32 digits a node, with halves x0, x1 and y0, y1 as in the code. Then
`multiply_karatsuba` makes exactly 3^k · 32² = 3^(log₂(n/32)) · 32² counted multiplications (for example 248832 at
n = 1024) if and only if no node has x1 = x0 and y1 = y0 (equal digit lists in both factors); otherwise it makes
fewer. With constant digits at n = 64 it makes 2048 instead of 3072.

**Proof.** Every length in the recursion is 32 · 2^j: at L = 32 · 2^j > 32, m = h = L/2, so `x[:m] + [0] * (h - m)`
adds no padding, and the three recursive calls get h = L/2 digits each. The recursion tree therefore has 3^k leaves,
each a call of `_schoolbook` on 32 digits. Multiplications occur only in `_schoolbook`; the test `sx * sy > 0`
multiplies the plain ints returned as signs. So the count is the number of leaf products `xi * yj` in which `xi` or
`yj` is a `CountingDigit`, at most 3^k · 32².

*Which lists are counting.* Claim: at every call, each of the lists x and y is either all `CountingDigit` or all
plain zeros. It holds at the top call. The slices x0, x1, y0, y1 inherit it. `_abs_diff(x1, x0)` gets two halves
of the same list, so both are counting or both are plain zeros. If they are equal digit by digit (always the case
for plain zeros) it returns `[0] * len(a)`, plain zeros. Otherwise both are counting, and `out = list(a)` (after a
possible swap) is overwritten at every position k = 0..len − 1 by `_sub_at`, which writes `t & MASK` with
`t = res[k] - d - borrow` built from counting digits, so `out` is all counting. The same holds for `dy`.

*If no node has equal halves in both factors, every leaf product counts.* Claim: at every call, x or y is all
counting. At the top call both are. At a node where x is all counting (the case y is symmetric): z0 gets x0 and z2
gets x1, both all counting. For z1 = `_karatsuba(dx, dy)`: if x1 ≠ x0, dx is all counting. If x1 = x0, the
condition gives y1 ≠ y0; then y is not all plain zeros (those have equal halves), so y is all counting and dy is all
counting. At a leaf one of the two lists is all counting, so all 32² products count, and the total is 3^k · 32².

*If some node has x1 = x0 and y1 = y0, the count is smaller.* Then dx and dy are plain zeros, and every list in the
subtree of that z1 call is plain zeros (slices and `_abs_diff` of plain zeros are plain zeros). That subtree has at
least one leaf, all of whose products multiply two plain ints and count 0, so the total is below 3^k · 32².

*Constant digits at n = 64.* The root has x1 = x0 and y1 = y0, so z1 counts 0, while z0 and z2 are leaves on
counting digits with 32² = 1024 counted products each: 2048, against 3 · 1024 = 3072.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "Karatsuba 3^log2(n/32)*32^2":
n = 32 and the V2 sizes n = 64, 128, 256, 512, 1024, 2048 on the seeded V2 instances (equal to the closed form, so by
the equivalence proved above these instances meet the condition); n = 1, 16, 31, 33, 48, 63, 65, 96, 100 are reported
as outside the domain. Its information line "Karatsuba equal-halves inputs" prints 2048 for constant digits at
n = 64 (and 4096 at n = 128, 2048 and 6144 for periodic digits, all below the closed form).
`experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "Karatsuba: count = closed form iff no node
has equal halves in both factors": n = 64, 128, 256 on 60 seeded inputs with planted equal halves at random nodes
(40 of them below the closed form), each compared with the exact count predicted by the proof (1024 per leaf, except
the leaves below the z1 call of a node with equal halves in both factors), and the constant-digit value 2048 at
n = 64.

## 4. Correctness of the schoolbook method

**Statement.** For digit lists a (length p) and b (length q) with digits in [0, B), `multiply_schoolbook((a, b))`
returns the p + q digits of a · b. (The same holds for `_schoolbook` in `karatsuba.py`, which is the same code.)

**Proof.** Write a_i, b_j for the digits and P_i = (Σ_{i′<i} a_(i′) B^(i′)) · b. Invariant before row i: `res` holds
the p + q digits of P_i, all in [0, B), and `res[k]` = 0 for k ≥ i + q (true for i = 0). In row i, with k = i + j,
the loop keeps value(res) + carry · B^(k+1) = P_i + a_i (Σ_{j′≤j} b_(j′) B^(j′)) B^i and 0 ≤ carry < B: the step
computes t = res[k] + a_i b_j + carry ≤ (B − 1) + (B − 1)² + (B − 1) = B² − 1, stores t mod B and carries
⌊t/B⌋ ≤ B − 1, and t B^k = (t mod B) B^k + ⌊t/B⌋ B^(k+1). After the loop, `res[i + q] = carry` writes a position that
was 0, so `res` holds P_(i+1) and the positions ≥ i + 1 + q are untouched. After row p − 1, value(res) = a · b with
p + q digits in [0, B). (Row i writes positions i..i + q only; position i + q < p + q.)

**Check.** `tests/test_proofs_karatsuba.py`, `CorrectnessTests`: n = 0..70, 96, 100, 127, 128, 129, 200, 257, five
kinds of factors (uniform, all digits B − 1, runs of 0 and B − 1, equal halves), against Python's integer product:
length 2n, every digit in [0, B), value correct. V1 (`harness.check`).

## 5. Correctness of Karatsuba's method

**Statement.** For every n ≥ 0 and digit lists a, b of length n with digits in [0, B), `multiply_karatsuba((a, b))`
returns the 2n digits of a · b. All three recursive products of a call have the same length.

**Proof.** *Helpers.* (i) `_add_at(res, src, off)`: if the digits of `res` and `src` are in [0, B) and
value(res) + value(src) · B^off < B^len(res), then afterwards `res` holds the digits of that sum, and no position
≥ len(res) is accessed. In the first loop t = res[k] + d + carry ≤ 2B − 1, so the carry stays in {0, 1}; throughout,
value(res) + carry · B^k equals the old value plus the part of src added so far, times B^off, which is below
B^len(res); if the carry loop reached k = len(res) with carry 1, that quantity would be ≥ B^len(res). (ii)
`_sub_at(res, src, off)`: if the result value(res) − value(src) · B^off is ≥ 0, afterwards `res` holds its digits:
t = res[k] − d − borrow lies in [−B, B − 1], so t mod B ∈ [0, B) is stored and the borrow −⌊t/B⌋ is 0 or 1;
value(res) − borrow · B^k equals the old value minus the part subtracted so far, which is ≥ 0, so the borrow loop
cannot pass the last position (value(res) < B^len(res)). (iii) `_abs_diff(a, b)` for lists of equal length L: if no
digit differs, A = B and it returns L zeros and sign 0; otherwise at the highest differing position i, A > B iff
a[i] > b[i] (the higher digits agree and the lower ones contribute less than B^i), and after the swap `_sub_at`
computes the L digits of |A − B| by (ii); the sign is that of A − B.

*Induction on L.* For L ≤ 32, `_karatsuba` returns `_schoolbook(x, y)`, the 2L digits of XY (section 4). For L > 32:
m = ⌊L/2⌋ ≥ 16 and h = L − m = ⌈L/2⌉ ∈ {m, m + 1}. `x0` is x[:m] padded with h − m high zeros (value
X0 = X mod B^m) and `x1` = x[m:] (h digits, value X1), so X = X0 + X1 B^m; the same for y. Since h < L, by induction
z0 and z2 are the 2h digits of X0Y0 and X1Y1; `dx` (h digits) and `sx` are |X1 − X0| and its sign, likewise `dy`,
`sy`; z1 holds the 2h digits of |X1 − X0| · |Y1 − Y0|, so (X1 − X0)(Y1 − Y0) = sx · sy · value(z1), and z1 is 0 when
sx · sy = 0. `mid` (2h + 1 digits) receives z0 and z2 (partial values below 2B^(2h) ≤ B^(2h+1), so (i) applies), then
loses z1 if sx · sy > 0 and gains it otherwise; in both cases the result is
X0Y0 + X1Y1 − (X1 − X0)(Y1 − Y0) = X0Y1 + X1Y0,
which is ≥ 0 (so (ii) applies) and below 2B^(2h) (so (i) applies). `res` (2L digits) receives z0 at offset 0, z2 at
offset 2m (positions up to 2m + 2h − 1 = 2L − 1) and `mid` at offset m (positions up to m + 2h ≤ 2L − 1, as m ≥ 1);
all three are ≥ 0 and the final value is X0Y0 + (X0Y1 + X1Y0) B^m + X1Y1 B^(2m) = (X0 + X1 B^m)(Y0 + Y1 B^m) = XY
< B^(2L), so every partial sum fits and (i) applies. `multiply_karatsuba` rejects unequal lengths, returns `[]` for
n = 0 (the empty product of two 0-digit numbers) and otherwise returns `_karatsuba(a, b)`.

*Equal sizes.* The three recursive calls get x0, y0, then x1, y1, then dx, dy: h digits each, because |X1 − X0| is
written with h digits (no carry digit), which is the point of the subtractive form.

**Check.** `tests/test_proofs_karatsuba.py`, `CorrectnessTests` (as in section 4; the factors with equal halves make
z1 = 0 at the top node, and odd n exercise h = m + 1). V1 (`harness.check`, incl. carry-stress and B^n − 1 inputs).

## 6. Word size

**Statement** (`input.size_measure`, docstrings). Every value computed from digits in either implementation (the
digits themselves, digit products and sums, carries, borrows and the signs) has absolute value at most B² − 1 < 2³⁰,
so each digit operation is a single-word operation (the entry's "below 2³¹" holds a fortiori). Index and length
arithmetic (`k`, `m`, `h`, `2 * L`, `2 * h + 1`) is separate: those values are at most 2n + 1 and have O(log n) bits.

**Proof.** Schoolbook steps (both files): t ≤ B² − 1 and the carry is below B (section 4). `_add_at`: t ≤ 2B − 1,
carry ∈ {0, 1}. `_sub_at`: −B ≤ t ≤ B − 1, borrow ∈ {0, 1}. `sx * sy` ∈ {−1, 0, 1}. Digits are in [0, B). The bound is
attained: all digits B − 1 give t = B² − 1 in the first schoolbook row.

**Check.** `tests/test_proofs_karatsuba.py`, `ValueBoundTests`: an int-like digit records the largest absolute value
of every result computed from digits (indices are plain ints and are not recorded), n = 1, 2, 31, 32, 33, 64, 65,
100, 129 on the five factor kinds, for both implementations: at most B² − 1, attained by the schoolbook method on
all-maximal digits.

## 7. Time bounds for every n

**Statement.** (a) The schoolbook method makes exactly n² multiply-adds and takes Θ(n²) time on every input. (b) For
n > 32, let d be the least j with ⌈n/2^j⌉ ≤ 32. Then all calls of Karatsuba's recursion at depth j have ⌈n/2^j⌉ digits,
the 3^d leaves have between 17 and 32 digits, the digit multiplications performed number exactly 3^d · ⌈n/2^d⌉², which
lies between 17² (n/32)^(log₂ 3) and 32² (n/16)^(log₂ 3), and the time is Θ(n^(log₂ 3)) on every input. (For n ≤ 32
the method is the schoolbook method: n² multiplications.) This solves T(n) = 3 T(⌈n/2⌉) + Θ(n) explicitly, and the
cutoff 32 changes constant factors only.

**Proof.** (a) Section 1; the loops do O(1) work per multiply-add, plus Θ(n) to allocate `res`.

(b) A call with L > 32 digits makes three calls with ⌈L/2⌉ digits each (section 5), and ⌈⌈x⌉/2⌉ = ⌈x/2⌉ for real x,
so the calls at depth j number 3^j and have ℓ_j = ⌈n/2^j⌉ digits. The leaves are the calls at depth d. As ℓ_(d−1) ≥ 33,
ℓ_d = ⌈ℓ_(d−1)/2⌉ ≥ 17. From ℓ_d ≤ 32, n/2^d ≤ 32; from ℓ_(d−1) > 32, n/2^(d−1) > 32. So n/32 ≤ 2^d < n/16 and
3^d = (2^d)^(log₂ 3) lies in [(n/32)^(log₂ 3), (n/16)^(log₂ 3)). Digits are multiplied only in `_schoolbook` (the
other product, `sx * sy`, multiplies two signs), ℓ_d² times per leaf: 3^d ℓ_d² with 17 ≤ ℓ_d ≤ 32. Time: a leaf costs
Θ(ℓ_d²) = Θ(1); an internal call with ℓ digits does at least 1 and at most c · ℓ work for a constant c (slices and
padding, two `_abs_diff` scans, the `_add_at` / `_sub_at` calls, each of which runs over its source and then
propagates a carry over at most the length of its target, and the allocation of `mid` and `res`). So the time is at
least 3^d and at most Θ(3^d) + c Σ_{j<d} 3^j (n/2^j + 1) ≤ Θ(3^d) + c (2n (3/2)^d + 3^d) = Θ(3^d), using n/2^d ≤ 32.
Hence Θ(n^(log₂ 3)). For n = 32 · 2^k this gives d = k and 3^k · 32² performed multiplications (section 3 counts them
on the instrumented digits).

**Check.** `tests/test_proofs_karatsuba.py`, `RecursionShapeTests`: the module's `_schoolbook` is wrapped by a spy (the
code is unchanged), n = 1..300 and 383, 384, 385, 511, 512, 513, 600: the leaf calls are exactly 3^d calls on
⌈n/2^d⌉ digits (17..32), the performed multiplications equal 3^d ⌈n/2^d⌉² and lie within the stated bounds; for
n ≤ 32 one schoolbook call on n digits. The V2 fits on exact counts (section 3).

## 8. Space bounds

**Statement.** Both methods use Θ(n) space.

**Proof.** Schoolbook: `res` (2n digits) and O(1) variables. Karatsuba: the calls run one after another, so at any
moment at most one call per depth is active. A call at depth j with ℓ_j digits holds O(ℓ_j) digits (its arguments,
`x0`, `x1`, `y0`, `y1`, `z0`, `z2`, `dx`, `dy`, `z1`, `mid` and `res`, each of at most 2ℓ_j + 1 digits). Summing over
the at most d + 1 = O(log n) depths gives O(Σ_j (n/2^j + 1)) = O(n). The output has 2n digits. Each digit is one word
(section 6).

**Check.** `tests/test_proofs_karatsuba.py`, `SpaceTests`: for n = 128, 256, 512, 1024 the peak traced allocation
divided by n is between 16 and 1000 and varies by a factor of at most 1.5 across the four sizes, for both methods.

## 9. Further remarks

**Statement.** (a) Since n digits are 15n bits and every digit operation is O(1) bit operations (section 6), the
exponents are the same in bit complexity (`input.size_measure`). (b) Both costs are polynomial and the exponent drops
from 2 to log₂ 3 ≈ 1.585 (`pair_type` T3).

**Proof.** (a) A digit operation on numbers below 2³⁰ costs O(1) bit operations, and the bit length 15n is Θ(n).
(b) Section 7; log₂ 3 = 1.5849… < 2.

**Check.** (b) The V2 fits on exact counts (each algorithm's rival rejected).
