# Proofs: element distinctness, all pairs vs sorting

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
from the code in this folder: the exact operation counts for every size of their domains (sections 1–2), the
correctness, time and space of the all-pairs scan (section 3) and of the merge-sort algorithm (section 4), the
lower bound in the comparison model stated in `lower_bounds` (section 5), and the reduction to closest pair
(section 6). Each proof is followed by the deterministic scripts or tests that check it and the sizes they check it
on. A check covers only those sizes; the proofs cover the whole domain. Section 7 lists the measured statements. The
statements listed under "Background" in `entry.json` (Ben-Or's algebraic lower bound, universal hashing) are cited,
not proved here.

## Counting convention

`harness.py`, class `CountingKey`: each of `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__` and `__ne__` adds 1 to
the module counter `_comparisons` (`_comparisons += 1`) and then compares the wrapped integers. No other operation
counts. `generate_scaling(n, rng)` draws n distinct values with `rng.sample(range(-10 ** 9, 10 ** 9), n)`, wraps
them in `CountingKey` and then sets `_comparisons = 0`; `reported_cost(output)` returns `_comparisons`. The counted
comparisons are `values[j] == x` in `distinct_all_pairs`, `a[i] <= a[j]` in `_merge_sort` and `a[k - 1] == a[k]`
in `distinct_by_sorting`. Each compares two input values (in `_merge_sort` every pass writes every position of
`buf` before the swap `a, buf = buf, a`, so the `None` entries of the initial `buf` are never compared), so each
counts exactly 1. Not counted: copying, the assignments to `buf`, and the tests on plain ints (`width < n`,
`i < mid`, `j < hi`).

## 1. All pairs: n(n − 1)/2 on yes-instances

**Statement.** On every input of n ≥ 0 pairwise distinct values (in particular on the scaling instance),
`distinct_all_pairs` makes exactly n(n − 1)/2 comparisons; the values listed in `entry.json` (124750 at n = 500, …,
7998000 at n = 4000) are this formula. On every input it makes at most n(n − 1)/2. On an input with an equal pair,
let (i*, j*) be the first pair i < j, in the order of the two loops (i ascending, then j ascending), with
x_i = x_j; then it makes exactly Σ_{p<i*} (n − 1 − p) + (j* − i*) comparisons, which equals n(n − 1)/2 if and only
if (i*, j*) = (n − 2, n − 1), that is if and only if the last two values are equal and all other pairs differ.

**Proof.** The loops visit the pairs (i, j), i < j, in that order and compare `values[j] == x` once per visited
pair; the function returns false at the first equal pair and true after the last pair. On distinct input every test
is false, so all Σ_{i=0..n−1} (n − 1 − i) = n(n − 1)/2 pairs are compared. Otherwise the comparisons stop at
(i*, j*), whose position in the order is Σ_{p<i*} (n − 1 − p) + (j* − i*); it is the last position n(n − 1)/2 only
for the last pair (n − 2, n − 1). At n = 4000: 4000·3999/2 = 7998000.

**Check.** At the V2 sizes n = 500, 1000, 1500, 2000, 3000, 4000:
`experiments/2026-10-07b_count_v2_element_distinctness.py`. `experiments/2026-10-07_closed_form_checks.py`, group
`sorting`, line "distinctness all pairs n(n-1)/2 (distinct input)": n = 0..29 and the V2 sizes.
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "distinctness all pairs n(n-1)/2 on other
distinct inputs": n = 0..60, three inputs each (increasing, decreasing, random); line "distinctness all pairs on
no-instances: index of the first equal pair in scan order (= n(n-1)/2 iff it is (n-2, n-1))": n = 2..40, 12
inputs each (4 of them with only the last pair equal).

## 2. Sorting, then neighbours: merge bounds plus n − 1 neighbour tests

**Statement.** On every input of n ≥ 0 values, the number C of comparisons made by `_merge_sort` satisfies
Σ min(ℓ, r) ≤ C ≤ Σ (ℓ + r − 1), both sums over the blocks of the bottom-up passes whose two runs are non-empty;
in the pass with `width` = w, the block starting at s has runs of lengths ℓ = min(w, n − s) and
r = min(w, max(n − s − w, 0)), which depend only on n. The `while` loop of `_merge_sort` runs exactly ⌈log₂ n⌉
passes for n ≥ 1 (none for n = 0). On every input of n ≥ 1 distinct values, `distinct_by_sorting` makes these merge
comparisons plus exactly n − 1 neighbour tests (none for n = 0). The merge part of each count listed in
`entry.json` (9710, 21426, 46876, 101729, 219403, 471108, 1006063, 2140632 at n = 1000, 2000, …, 128000, minus
n − 1) lies within these bounds; for example 9710 − 999 = 8711 lies in [4932, 8985] at n = 1000.

**Proof.** The merge bounds are given in `entry.json`, field `verification.method`. The missing step: a block whose
right run is empty (mid = hi = n, at the end of a pass) makes no comparison, since the test `j < hi` fails at once
and the block is only copied; so the sums range over the blocks with ℓ, r ≥ 1, and for those the argument of the
entry applies.

*Passes.* `width` takes the values 1, 2, 4, …, and the loop runs while `width < n`, so it runs for 2^k with
2^k < n, that is for k = 0, …, ⌈log₂ n⌉ − 1 when n ≥ 1 (none for n = 1), and not at all for n = 0.

*Neighbour tests.* On distinct values the sorted list has no two equal neighbours, so the test `a[k - 1] == a[k]`
is false for every k = 1..n − 1 and the loop never returns early: n − 1 comparisons for n ≥ 1, and
`range(1, 0)` is empty for n = 0.

**Check.** At the V2 sizes n = 1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000:
`experiments/2026-10-07b_count_v2_element_distinctness.py` (merge part within the bounds).
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "distinctness sort: merge bounds + (n-1)
neighbour tests": n = 0..39, 1000, 2000, 4000, 8000. `experiments/2026-10-07_count_proof_checks.py`, group
`strings`, line "distinctness bottom-up merge part within run-length bounds on every input": n = 0..120, six inputs
each (with and without ties); line "distinctness neighbour tests n-1 on distinct inputs (n >= 1; 0 at n = 0)": the
distinct inputs among them; line "distinctness merge passes ceil(log2 n) (line count)": n = 0..129, 255, 256, 257,
1000; line "distinctness listed V2 values: reproduced (sample 0), merge part within the bounds": the eight V2
sizes.

## 3. All pairs: correctness, Θ(n²) worst case, O(1) extra space

`distinct_all_pairs` compares `values[j] == x` for the pairs i < j in loop order and returns false at the first equal
pair, true after the last one; so it returns true exactly when all pairs differ (true for n ≤ 1, where there is no
pair). By section 1 it makes at most n(n − 1)/2 comparisons on every input and exactly n(n − 1)/2 on every
yes-instance, each with O(1) further work (values up to 10¹⁸ in magnitude, compared at unit cost), so its worst-case
time is Θ(n²). Its locals are integers and one input value, so it creates no container: O(1) words besides the input.

**Check.** The V1 battery (n = 0..300) against the hash-set oracle. `tests/test_proofs_distinctness.py`,
`test_both_correct` (400 seeded inputs, n = 0..130: distinct values, many ties, only the last two equal, sorted and
reverse-sorted) and `test_space` (20 seeded inputs: the instrumented peak of `tests/proof_space.py` is 0).

## 4. Sort, then compare neighbours: correctness, Θ(n log n) on every input, Θ(n) space

**Lemma 4.1 (one merge).** Let a[lo:mid] and a[mid:hi] be sorted (non-decreasing). The block loop of `_merge_sort`
writes into buf[lo:hi] these hi − lo elements in sorted order. *Proof.* Invariant: buf[lo:k] holds a[lo:i] and
a[mid:j] (as a multiset), is sorted, and each of its elements is ≤ every element of a[i:mid] and of a[j:hi]. It holds
at the start (empty). If a[i] ≤ a[j], then a[i] is ≤ every remaining element (its own run is sorted, and
a[i] ≤ a[j] ≤ a[j′] for j′ ≥ j), so writing it keeps the invariant; the case a[j] < a[i] is symmetric. When one run
is used up, the rest of the other is sorted and ≥ everything written, and the two tail loops copy it.

**Lemma 4.2 (passes).** Before the pass with `width` = w, every block a[lo:lo + w] (lo a multiple of w, the last block
possibly shorter) is sorted, and a holds the input values. *Proof.* True for w = 1. The pass merges the blocks
[lo, lo + w) and [lo + w, lo + 2w) (clipped at n) into buf by Lemma 4.1; a last block whose right run is empty is just
copied. Every position of buf is written, so after the swap `a, buf = buf, a` the blocks of length 2w are sorted and
a holds the input values. The loop stops when w ≥ n, when the single block a[0:n] is sorted (for n ≤ 1 there is no
pass and a = list(values) is sorted).

**Correctness.** `_merge_sort` returns the values sorted (Lemma 4.2). If two input values are equal, every element
between their two copies in the sorted list equals them too, so some adjacent pair is equal; an adjacent equal pair
is an equal pair of the input. So `distinct_by_sorting` answers correctly.

**Time.** By section 2 there are ⌈log₂ n⌉ passes for n ≥ 1. Each pass writes each of the n positions of buf exactly
once and makes at most one comparison per write (at most n comparisons), plus O(1) per block; so each pass costs Θ(n)
on every input, and the neighbour scan O(n). Total Θ(n log n) on every input with n ≥ 2. The number of comparisons is
at most n⌈log₂ n⌉ + n − 1.

**Space.** The containers are `a` = list(values) and `buf`, n slots each, and the returned list is `a`: exactly 2n
words besides the input, Θ(n).

**Check.** `tests/test_proofs_distinctness.py`, `test_merge_sort_pass_invariant_and_output` (200 seeded inputs,
n = 0..130, with and without ties: at the line `width *= 2` of the running code, every block of length 2w of `a` is
sorted; the passes have widths 1, 2, 4, …, below n; the output is the sorted input), `test_both_correct` and
`test_space` (the instrumented peak equals 2n). The merge bounds and the pass count are checked as listed in section
2.

## 5. A lower bound in the comparison model (`lower_bounds`)

**Model.** A *comparison tree* for n inputs has internal nodes labelled with two positions i ≠ j and three children,
for the outcomes a_i < a_j, a_i = a_j and a_i > a_j; each leaf answers yes or no. A deterministic algorithm that
accesses the input values only by comparing two of them, with an outcome that is a function of the three-way outcome
(such as `<=` or `==`), is described for each n by such a tree with the same number of comparisons on every input:
its computation is determined by the outcomes. Both implementations of this entry are such algorithms (the harness
runs them on `CountingKey` values, which support comparisons and nothing else).

**Theorem.** Every comparison tree that decides element distinctness of n inputs has depth at least ⌈log₂(n!)⌉
≥ n log₂ n − n log₂ e. So every comparison algorithm makes at least that many comparisons on some input of n
distinct integers (a permutation of 1..n). The merge-sort algorithm makes at most n⌈log₂ n⌉ + n − 1, so it is optimal
among comparison algorithms up to a factor that tends to 1.

**Proof.** Let π be an input that is a permutation of 1..n (a_k = π(k)); it is a yes-instance, so its path ends at a
yes-leaf. For r = 1..n − 1 let p and q be the positions with a_p = r and a_q = r + 1. Suppose no node on the path of π
compares p with q. Change a_q to r. A comparison on the path that does not involve q is unchanged. One between q and
a position k ≠ p compares a_k ∉ {r, r + 1} with r + 1 before and with r after, and for an integer a_k ∉ {r, r + 1},
a_k < r ⟺ a_k < r + 1. So the changed input follows the same path to the same yes-leaf, although two of its values
are equal: a contradiction. Hence the path of π compares the positions of r and r + 1 for every r, and its outcomes
say that the position of r holds a smaller value than the position of r + 1. A permutation σ that reaches the same
leaf satisfies the same outcomes, so σ(p_1) < σ(p_2) < … < σ(p_n), where p_r is the position of r in π; this forces
σ = π. So the n! permutations reach n! different leaves. Their paths use only the < and > branches (their values are
distinct), so these leaves lie in a binary tree, whose depth is therefore at least log₂(n!). Finally
e^n = Σ_k n^k/k! ≥ n^n/n!, so n! ≥ (n/e)^n and log₂(n!) ≥ n log₂ n − n log₂ e. The upper bound for the merge-sort
algorithm is section 4, and (n⌈log₂ n⌉ + n − 1)/(n log₂ n − n log₂ e) → 1. (Credit: this is the classical counting
argument for comparison sorting; see Knuth 1998.)

**Scope.** The theorem holds for integer inputs, but only for algorithms that use comparisons alone. Ben-Or's
Ω(n log n) bound for algebraic computation trees on real inputs (background) allows arithmetic as well; neither bound
covers algorithms that use the representation of integers, such as hashing (background).

**Check.** `tests/test_proofs_distinctness.py`, `test_comparison_lower_bound`: log₂(n!) ≥ n log₂ n − n log₂ e for
n = 1..3000; for n = 1..4, an exhaustive minimax search over the 1, 3, 13 and 75 weak orders of n values finds the
minimum worst-case depth of a comparison tree deciding distinctness to be 0, 1, 3 and 5, equal to ⌈log₂(n!)⌉; and
n(n − 1)/2 and n⌈log₂ n⌉ + n − 1 are at least ⌈log₂(n!)⌉ for n = 1..199.

## 6. Reduction to closest pair (notes)

n numbers x_1, …, x_n are pairwise distinct if and only if the points (x_i, 0) have a positive minimum squared
distance, since (x_i − x_j)² + 0² = 0 exactly when x_i = x_j. This is the reduction that
`pairs/closest-pair-brute-vs-divide-conquer` uses (its PROOFS.md, section 7).

## 7. Measured statements (data, not theorems)

The V2 fits, the sorting counts n log₂ n − c·n with c = 0.24 to 0.26 on the seeded instances, and the earlier timing
fits are measurements; sections 1–2 prove the exact counts and bounds that they sample.
