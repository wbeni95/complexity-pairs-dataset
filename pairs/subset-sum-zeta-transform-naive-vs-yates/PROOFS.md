# Proofs: zeta transform, submask enumeration vs Yates' method

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
every exact operation count on its domain, and the factual remarks. Sections 1 and 2 prove the exact counts;
sections 3 to 9 prove the rest. Statements about the literature are not claims of this entry: they are listed under
`background` in `entry.json`, with their sources, and are not proved here. Each proof is followed by the
deterministic scripts or tests that check its computable facts and the ranges they check. A check covers only those
ranges; the proofs cover the general statements.

Notation: a set S of the ground set {0, …, n − 1} is the bitmask with bit i set iff i ∈ S; T ⊆ S iff `T & ~S == 0`.
Costs are in the unit-cost model of the entry: an addition of two values of O(n) bits (section 8) and an index
operation each cost O(1).

## Counting convention

`harness.py`, class `CountingInt`: `__add__` (also bound as `__radd__`), `__sub__` and `__rsub__` each add 1 to the
module counter `_ops` and return a new `CountingInt`; `__eq__`, `__int__` and `__hash__` do not count.
`generate_scaling(n, rng)` sets `_ops = 0` and returns a tuple of N = 2ⁿ `CountingInt` values in [−9, 9];
`reported_cost(output)` returns `_ops`. An addition with at least one `CountingInt` operand counts exactly 1 (if
only the right operand is one, `int.__add__` returns `NotImplemented` and Python calls `__radd__`). Index arithmetic
(`(t - 1) & s`, `s & bit`, `s ^ bit`, the test `t == 0`) is on plain ints and does not count.

## 1. Submask enumeration: Σ_S 2^|S| = 3ⁿ additions

**Statement.** For every n ≥ 0 and every input of the scaling form, `zeta_naive` makes exactly
Σ over S of 2^|S| = 3ⁿ counted additions.

**Proof.** *The inner loop visits every submask of s exactly once.* Order the submasks of s by their value. For a
submask t > 0 let p be its lowest set bit. Then t − 1 agrees with t above p, has 0 at p and 1 at every position
below p, so r = `(t - 1) & s` agrees with t above p, has 0 at p, and equals s below p; thus r < t. A submask u of s
with u < t first differs from t at some bit q ≥ p (t has no bit below p), where u has 0 and t has 1. If q > p, u is
also smaller than r, which agrees with t at q and above. If q = p, u agrees with r above p and has 0 at p, and its
bits below p are bits of s, so u ≤ r. Hence r is the largest submask of s smaller than t. The loop starts at t = s, the largest submask, steps to the next smaller
one each time, and stops after processing t = 0 (`if t == 0: break`). So it runs once per submask, 2^|s| times.

*Counting.* Each iteration evaluates `acc = acc + f[t]` once; the first time `acc` is the plain int 0 and the
addition counts through `__radd__`, later both operands are `CountingInt`. So set s costs 2^|s| additions, and
Σ_s 2^|s| = Σ_{k=0..n} C(n, k) 2^k = (1 + 2)ⁿ = 3ⁿ.

**Check.** `experiments/2026-10-07b_zeta_transform_counts.py` (n = 0..12). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "zeta naive 3^n": n = 0..11 (includes the V2 sizes n = 4..11).

## 2. Yates' method: n · 2^(n−1) additions

**Statement.** For every n ≥ 0 and every input of the scaling form, `zeta_yates` makes exactly n · 2^(n−1) counted
additions (0 at n = 0).

**Proof.** `bit` takes the values 1, 2, …, 2^(n−1), n passes. In each pass exactly the 2^(n−1) indices s with
`s & bit` ≠ 0 execute `g[s] = g[s] + g[s ^ bit]`, one addition of two `CountingInt` values (every entry of `g` is
one, initially and after each update). Total n · 2^(n−1).

**Check.** `experiments/2026-10-07b_zeta_transform_counts.py` (n = 0..12). `experiments/2026-10-07_closed_form_checks.py`,
group `algebra`, line "Yates n2^(n-1)": n = 0..16 (includes the V2 sizes n = 4, 6, …, 16).

## 3. Correctness of the submask enumeration

**Statement.** For every n ≥ 0 and every vector f of length 2ⁿ, `zeta_naive(f)` returns ζf, that is
`out[s]` = Σ over t ⊆ s of f[t] for every s.

**Proof.** For each s the inner loop visits every submask of s exactly once (section 1, first part: it starts at
t = s, steps from each submask t > 0 to the largest submask of s below t, and stops after t = 0). Each visit adds
f[t] to `acc`, which starts at 0, and `out[s] = acc` is stored after the loop.

**Check.** `tests/test_proofs_zeta.py`, `SubmaskStepTests`: for every s < 2¹¹ the visited sequence equals the
submasks of s in decreasing order. `CorrectnessTests`: on every unit vector for n = 0..8 (a complete check of the
map, because the function only adds entries and is therefore linear with integer coefficients) and on 3 seeded
random vectors for each n = 0..10. The V1 run compares with an independent definition-scan oracle (`harness.check`).

## 4. Correctness of Yates' method

**Statement.** For every n ≥ 0 and every vector f of length 2ⁿ, `zeta_yates(f)` returns ζf.

**Proof.** `bit` takes the values 2⁰, 2¹, …, 2^(n−1) (the loop runs while `bit < size` = 2ⁿ); call the pass with
`bit` = 2^i pass i, and let g_i be the list after passes 0, …, i − 1 (g_0 = f, a copy). Invariant:

g_i[S] = Σ { f[T] : T ⊆ S and T agrees with S on every element ≥ i }.

For i = 0 the only such T is S. *In-place reads.* In pass i the indices written are those containing i, and the
index read, S ^ 2^i = S ∖ {i}, does not contain i; so every read in pass i sees the value from before the pass, and
g_(i+1)[S] = g_i[S] if i ∉ S, and g_(i+1)[S] = g_i[S] + g_i[S ∖ {i}] if i ∈ S. *Step.* If i ∉ S, a subset T of S
has i ∉ T, so agreeing with S on the elements ≥ i is the same as agreeing on the elements ≥ i + 1. If i ∈ S, the
subsets T ⊆ S that agree with S on the elements ≥ i + 1 split by whether i ∈ T: those with i ∈ T agree with S on
the elements ≥ i (sum g_i[S]); those with i ∉ T are exactly the subsets of S ∖ {i} that agree with S ∖ {i} on the
elements ≥ i (sum g_i[S ∖ {i}]). So the invariant holds for i + 1. After the n passes the condition on the
elements ≥ n is empty, and g_n[S] = Σ over T ⊆ S of f[T]. For n = 0 no pass runs and g = f = ζf.

**Check.** `tests/test_proofs_zeta.py`, `CorrectnessTests` (unit vectors n = 0..8, complete; random vectors
n = 0..10). V1 (`harness.check`).

## 5. The Kronecker structure and the Möbius inverse

**Statement.** (a) The zeta matrix Z_n, Z_n[S][T] = [T ⊆ S], is the n-fold Kronecker power of
Z₁ = [[1, 0], [1, 1]], and pass i of Yates' method applies the factor that acts on element i. (b) Its inverse, the
Möbius transform, is the n-fold Kronecker power of [[1, 0], [−1, 1]]; computed by the same passes with subtraction
it costs n · 2^(n−1) operations.

**Proof.** (a) [T ⊆ S] = Π_i [T_i ≤ S_i] over the bits i, and [t ≤ s] = Z₁[s][t] for s, t ∈ {0, 1}; a product over
the bits of 2 × 2 entries indexed by the bits is the definition of the Kronecker power. By section 4, pass i maps g
to P_i g with (P_i g)[S] = Σ over t ∈ {0, 1} of Z₁[S_i][t] · g[S with bit i set to t]: the Kronecker product with Z₁
at position i and identities elsewhere. (b) Z₁ · [[1, 0], [−1, 1]] = I, and by the mixed-product property the
Kronecker power of [[1, 0], [−1, 1]] is the inverse of Z_n. The factor at position i maps g to
g[S] − [i ∈ S] g[S ∖ {i}]; a pass of the same shape as Yates' with `-` in place of `+` applies it (the in-place
argument of section 4 is unchanged), the factors at different positions commute, and n passes of 2^(n−1)
subtractions each give n · 2^(n−1). This Möbius transform is `_moebius` in
`pairs/or-convolution-naive-vs-zeta-mobius/implementations/zeta_mobius.py`; its count is proved there
(PROOFS.md, section 2).

**Check.** `tests/test_proofs_zeta.py`, `KroneckerAndMoebiusTests`: the Kronecker power equals Z_n for n = 1..5;
`_moebius(zeta_yates(f)) = f` and `zeta_yates(_moebius(f)) = f` on seeded vectors for n = 0..10;
Z₁ · [[1, 0], [−1, 1]] = I.

## 6. Time bounds

**Statement.** `zeta_naive` takes Θ(3ⁿ) time and `zeta_yates` Θ(n · 2ⁿ) time (n ≥ 1), on every input. In the input
length N = 2ⁿ these are Θ(N^(log₂ 3)) and Θ(N log N).

**Proof.** `zeta_naive`: the inner loop runs once per pair (s, t ⊆ s), 3ⁿ times in total (section 1), with O(1)
work per iteration (one addition, one test `t == 0`, one step `(t - 1) & s`); the outer loop adds 2ⁿ ≤ 3ⁿ
iterations of O(1) work. `zeta_yates`: the copy costs 2ⁿ, and the n passes run the body `if s & bit` exactly n · 2ⁿ
times, each O(1). 3ⁿ = (2ⁿ)^(log₂ 3) and n · 2ⁿ = N log₂ N.

**Check.** The exact counts of sections 1 and 2 (scripts listed there) and the V2 fits.

## 7. Space bounds

**Statement.** Both algorithms use Θ(2ⁿ) space.

**Proof.** `zeta_naive` allocates `out` (2ⁿ entries) and O(1) variables; `zeta_yates` allocates the copy `g`
(2ⁿ entries) and O(1) variables. The output has 2ⁿ entries, so neither can use less. Every value fits in O(n) bits
(section 8).

**Check.** `tests/test_proofs_zeta.py`, `SpaceTests`: the peak traced allocation during the call lies between
8 · 2ⁿ bytes (one list slot per entry) and 64 · 2ⁿ + 4096 bytes, for `zeta_naive` at n = 6..12 and `zeta_yates`
at n = 6..15.

## 8. Value sizes

**Statement.** With entries of absolute value at most 9 (the harness range), every value that either algorithm
computes has absolute value at most 9 · 2ⁿ, so it has O(n) bits; the bound is attained.

**Proof.** Every value computed is a sum of f[T] over a set of distinct T: the partial sums of `acc` run over
distinct submasks (section 3), and g_i[S] is a sum over a set of distinct T (section 4). There are at most 2ⁿ such
T, so |value| ≤ 9 · 2ⁿ < 2^(n+4). The constant input f ≡ 9 gives ζf[S] = 9 · 2^|S|, which is 9 · 2ⁿ at the full
set.

**Check.** `tests/test_proofs_zeta.py`, `ValueSizeTests`: the constant input 9 at n = 0..12 (Yates; naive up to
n = 11).

## 9. The T3 classification

**Statement.** Both costs are polynomial in the input size, and the exponent drops (`pair_type` T3).

**Proof.** The input has N = 2ⁿ integers of O(1) bits. By section 6 the costs are Θ(N^(log₂ 3)) = Θ(N^1.585) and
Θ(N log N): both polynomial in N, with Θ(N log N) = o(N^1.585).

**Check.** Arithmetic; the V2 fits measure the two exponents on exact counts.
