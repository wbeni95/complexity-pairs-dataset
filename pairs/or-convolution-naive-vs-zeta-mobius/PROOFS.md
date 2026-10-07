# Proofs: OR convolution, naive vs zeta–Möbius

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
every exact operation count on its domain, the completeness of the V1 check, and the factual remarks. Sections 1
and 2 prove the exact counts; sections 3 to 9 prove the rest. Statements about the literature are not claims of this
entry: they are listed under `background` in `entry.json`, with their sources, and are not proved here. Each proof is
followed by the deterministic scripts or tests that check its computable facts and the ranges they check. A check
covers only those ranges; the proofs cover the general statements.

Notation: sets of the ground set {0, …, n − 1} are bitmasks; A | B is the union, T ⊆ S iff `T & ~S == 0`,
ζv[S] = Σ over T ⊆ S of v[T] (zeta transform) and μ = ζ⁻¹ (Möbius transform). Costs are in the unit-cost model of the
entry: a ring operation on values of O(n) bits (section 7) and an index operation each cost O(1).

## Counting convention

`harness.py`, class `CountingInt`: `__add__` (also bound as `__radd__`), `__sub__`, `__rsub__` and `__mul__` (also
bound as `__rmul__`) each add 1 to the module counter `_ops` and return a new `CountingInt`; `__eq__`, `__int__` and
`__hash__` do not count. `generate_scaling(n, rng)` sets `_ops = 0` and returns two set functions, each a tuple of
N = 2ⁿ `CountingInt` values in [−9, 9]; `reported_cost(output)` returns `_ops`.

An operation `x + y`, `x - y` or `x * y` counts exactly 1 if at least one operand is a `CountingInt` (if only `y`
is, the int method returns `NotImplemented` and Python calls the reflected method of `y`), and its result is a
`CountingInt`. Index arithmetic (`a | b`, `s & bit`, `s ^ bit`, `bit <<= 1`) is on plain ints and does not count.

## 1. Naive: 4ⁿ multiplications and 4ⁿ additions, 2 · 4ⁿ counted operations

**Statement.** For every n ≥ 0 and every input of the scaling form, `or_convolution_naive` performs exactly 4ⁿ
multiplications and 4ⁿ additions, all counted: 2 · 4ⁿ.

**Proof.** The two loops run the body `h[s] = h[s] + fa * g[b]` once for each of the N² = 4ⁿ pairs (a, b), with
no early exit. `fa * g[b]` multiplies two input values (1 count) and gives a `CountingInt`; adding it to `h[s]`
counts 1 also when `h[s]` is still the plain int 0 (through `__radd__`).

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "OR naive 2*4^n": n = 0..9 (the V2
sizes are n = 3..8). `experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "OR and XOR
convolution, zeta: counts per operation kind": n = 0..9.

## 2. Zeta–Möbius: 3n · 2^(n−1) additions and subtractions plus 2ⁿ multiplications, (3n + 2) · 2^(n−1)

**Statement.** For every n ≥ 0 and every input of the scaling form, `or_convolution_zeta_mobius` performs exactly
3n · 2^(n−1) additions and subtractions and 2ⁿ multiplications, all counted: (3n + 2) · 2^(n−1) operations (1 at
n = 0).

**Proof.** In `_zeta` the variable `bit` takes the values 1, 2, …, 2^(n−1) (the loop stops when `bit` reaches
size = 2ⁿ), n passes. In each pass exactly the 2^(n−1) indices s with `s & bit` ≠ 0 execute
`g[s] = g[s] + g[s ^ bit]`, one addition of two `CountingInt` values (every entry of `g` is one, initially and
after each update). So `_zeta` makes n · 2^(n−1) counted additions, and `_moebius`, with the same loops and `-`,
n · 2^(n−1) counted subtractions. `or_convolution_zeta_mobius` runs `_zeta` twice, the 2ⁿ products `x * y` of two
`CountingInt` values, and `_moebius` once: 2 · n · 2^(n−1) + 2ⁿ + n · 2^(n−1) = (3n + 2) · 2^(n−1). At n = 0 no
pass runs and the single product gives 1 = 2 · 2^(−1).

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `algebra`, line "zeta-Moebius (3n+2)2^(n-1)":
n = 0..16 (includes the V2 sizes n = 4, 6, …, 16). `experiments/2026-10-07_count_proof_checks.py`, group
`subsets`, line "OR and XOR convolution, zeta: counts per operation kind": n = 0..12.

## 3. Correctness of the naive method

**Statement.** For every n ≥ 0, `or_convolution_naive((f, g))` returns h with h[S] = Σ over pairs (A, B) with
A | B = S of f[A] g[B], for every S.

**Proof.** `h` starts as zeros, and the double loop visits every pair (a, b) of indices exactly once and adds
f[a] g[b] to h[a | b]. So h[S] collects exactly the pairs with a | b = S.

**Check.** `tests/test_proofs_or_convolution.py`, `CorrectnessTests`: on every pair of unit vectors for n = 0..4 (a
complete check, since the function is bilinear in (f, g)) and on 3 seeded random inputs for each n = 0..8, against a
separate definition loop. V1 (`harness.check`, complete; section 9).

## 4. Correctness of the zeta–Möbius method

**Statement.** For every n ≥ 0, `or_convolution_zeta_mobius((f, g))` returns the OR convolution h of f and g.

**Proof.** *Diagonalisation.* For every S,
ζh[S] = Σ_{T ⊆ S} Σ_{A | B = T} f[A] g[B] = Σ_{A ⊆ S, B ⊆ S} f[A] g[B] = ζf[S] · ζg[S]:
each pair (A, B) with A | B ⊆ S occurs exactly once on the left, at T = A | B, and A | B ⊆ S holds iff A ⊆ S and
B ⊆ S. *The transforms.* `_zeta` is the same code as `zeta_yates` in
`pairs/subset-sum-zeta-transform-naive-vs-yates/implementations/yates.py`, which computes ζ (that entry's PROOFS.md,
section 4); `_moebius` is the same passes with `-`, which compute μ = ζ⁻¹ (same PROOFS.md, section 5). The function
returns μ(ζf · ζg) = μ(ζh) = h. (μ is the Kronecker power of [[1, 0], [−1, 1]], whose entry at (S, T) is
Π_i [T_i ≤ S_i] (−1)^(S_i − T_i) = [T ⊆ S] (−1)^(|S| − |T|): the signed sum over subsets in the docstring of
`zeta_mobius.py`.)

**Check.** `tests/test_proofs_or_convolution.py`, `CorrectnessTests`: unit-vector pairs n = 0..4 (complete: the
function is bilinear in (f, g)), random inputs n = 0..8, and the identity `_zeta(h)` = ζf · ζg for n = 0..9 (ζf and ζg
by a separate definition scan). `tests/test_proofs_zeta.py` checks the two transforms. V1 (`harness.check`).

## 5. Time bounds

**Statement.** The naive method takes Θ(4ⁿ) = Θ(N²) time and the zeta–Möbius method Θ(n · 2ⁿ) = Θ(N log N) time
(n ≥ 1) on every input, N = 2ⁿ.

**Proof.** Naive: 4ⁿ iterations of the inner body, each with one multiplication, one addition and one index union
(section 1), plus 2ⁿ outer iterations. Zeta–Möbius: each of the three transforms runs its body `if s & bit` n · 2ⁿ
times with O(1) work, plus the copies and the 2ⁿ pointwise products: Θ(n · 2ⁿ). 4ⁿ = N² and n · 2ⁿ = N log₂ N.

**Check.** The exact counts of sections 1 and 2 (scripts listed there) and the V2 fits.

## 6. The AND convolution is the OR convolution at complemented indices

**Statement** (`notes`, `problem_statement`). Write X̄ = full ^ X for the complement of X in the ground set
(full = 2ⁿ − 1), f′[X] = f[X̄] and g′[X] = g[X̄]. The AND convolution k[S] = Σ over A & B = S of f[A] g[B] equals
h′[S̄], where h′ is the OR convolution of f′ and g′. Equivalently, the AND convolution is diagonalised by sums over
supersets.

**Proof.** Complementation is a bijection of the subsets, and A & B = S iff Ā | B̄ = S̄ (De Morgan). So
h′[S̄] = Σ_{X | Y = S̄} f[X̄] g[Ȳ] = Σ_{A & B = S} f[A] g[B] (substituting A = X̄, B = Ȳ). Applying sections 3 and 4
to f′ and g′ computes it; ζ at complemented indices is the sum over supersets.

**Check.** `tests/test_proofs_or_convolution.py`, `AndMirrorTests`: both implementations, n = 0..7, 2 seeded inputs
per n, against a direct AND-convolution loop. `experiments/2026-10-06f_entries_or_convolution.py` (100 of 100
instance-implementation pairs, n = 0..9).

## 7. Value sizes

**Statement** (`input.size_measure`). With entries of absolute value at most 9, every value computed has O(n) bits:
every value of the zeta–Möbius method has absolute value at most 81 · 8ⁿ, every value of the naive method and every
output entry h[S] at most 81 · 3^|S| ≤ 81 · 3ⁿ.

**Proof.** h[S] is a sum of 3^|S| products f[A] g[B] (the pairs with A | B = S: each element of S lies in A only, in
B only, or in both), each of absolute value at most 81; the naive method's partial sums are sub-sums of these. In the
fast method, ζf and ζg and their partial passes are sums of at most 2ⁿ entries (bound 9 · 2ⁿ), the products at most
81 · 4ⁿ, and after i Möbius passes each entry is a signed sum of 2^i products (the Möbius passes have the shape of
section 4 of the zeta entry with signs), at most 2ⁿ · 81 · 4ⁿ = 81 · 8ⁿ < 2^(3n+7). The constant input f = g = 9 gives
h[full] = 81 · 3ⁿ.

**Check.** `tests/test_proofs_or_convolution.py`, `ValueSizeTests`: the largest absolute value produced by any +, −
or × of the fast method, and the bound on h[S], for n = 0..12 on f = g = 9, f = 9 and g = −9, and 2 seeded random
inputs per n; the value 81 · 3¹⁰ at n = 10.

## 8. Space bounds

**Statement.** Both methods use Θ(2ⁿ) space.

**Proof.** Naive: the list `h` (2ⁿ entries) and O(1) variables. Zeta–Möbius: at most four lists of 2ⁿ entries are
alive at once (ζf, ζg, the pointwise products and the working copy inside `_moebius`), plus O(1) variables. The
output has 2ⁿ entries. All values have O(n) bits (section 7).

**Check.** `tests/test_proofs_or_convolution.py`, `SpaceTests`: the peak traced allocation during the call lies
between 8 · 2ⁿ and 192 · 2ⁿ + 4096 bytes, naive n = 4..9, zeta–Möbius n = 4..14.

## 9. The V1 check is complete; the T3 classification

**Statement.** (a) The check "ζh[S] = ζf[S] · ζg[S] for every S" accepts exactly the correct output, at every n
(`verification.method`). (b) Both costs are polynomial in the input size N = 2ⁿ, and the exponent drops (T3).

**Proof.** (a) By section 4 the correct h satisfies the identity. ζ is invertible (zeta entry, PROOFS.md section 5),
so ζh′ = ζf · ζg = ζh implies h′ = h for any candidate h′ of length 2ⁿ. (b) Θ(N²) and Θ(N log N) are polynomial in
N, and N log N = o(N²).

**Check.** (a) The oracle control in `experiments/2026-10-06f_entries_or_convolution.py` (86 correct outputs
accepted, 383 wrong ones rejected). (b) Arithmetic; the V2 fits.
