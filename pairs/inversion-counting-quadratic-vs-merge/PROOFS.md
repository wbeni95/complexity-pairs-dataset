# Proofs: counting inversions, all pairs vs merge sort

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code).
Sections 1–2 prove the exact operation counts for every size of their domain; sections 3–6 prove correctness, the
time and space bounds and the separation. Each proof is followed by the deterministic scripts that check it and
the sizes they check it on. A check covers only those sizes; the proofs cover the whole domain.

## Counting convention

*Machine-model assumptions (not proved here).* Comparisons of two elements, integer additions, indexing and
`append` (amortised) cost O(1); slicing or `extend` with t elements and allocating a list of length t cost Θ(t + 1).

`harness.py`, class `CountingKey`: each of `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__` and `__ne__` adds 1 to
the module counter `_comparisons` (`_comparisons += 1`) and then compares the wrapped integers. No other operation
counts. `generate_scaling(n, rng)` wraps the values of `generate(n, rng)` (n integers drawn uniformly from [0, n])
in `CountingKey` and then sets `_comparisons = 0`; `reported_cost(output)` returns `_comparisons`. The only counted
comparisons are `vi > values[j]` in `inversions_quadratic` and `right[j] < left[i]` in `_sort_count`; both compare
two input elements, so each counts exactly 1. Not counted: `count += 1`, `cross += len(left) - i`, slicing,
`append`, `extend`, and the tests on plain ints (`len(a) <= 1`, `i < len(left)`, `j < len(right)`).

## 1. All pairs: n(n − 1)/2

**Statement.** On every sequence of n ≥ 0 elements (in particular on the scaling instance),
`inversions_quadratic` makes exactly n(n − 1)/2 comparisons. The V2 counts stated in `entry.json` at n = 250, 500,
750, 1000, 1500, 2000 are this formula (for example 1999000 at n = 2000).

**Proof.** For each i the inner loop runs over j = i + 1..n − 1 and evaluates `vi > values[j]` once, with no early
exit: Σ_{i=0..n−1} (n − 1 − i) = n(n − 1)/2.

**Check.** At the V2 sizes n = 250, 500, 750, 1000, 1500, 2000:
`experiments/2026-10-07b_count_v2_inversions_lis.py`. `experiments/2026-10-07_closed_form_checks.py`, group
`sorting`, line "inversions all pairs n(n-1)/2": n = 0..29 and the V2 sizes.
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "inversions all pairs n(n-1)/2 on other
inputs": n = 0..60, five sequences each (many ties, increasing, decreasing, constant, random).

## 2. Merge-sort counting: Σ min(left, right) ≤ C ≤ Σ (left + right − 1)

**Statement.** On every sequence of n ≥ 0 elements, the number C of comparisons made by `inversions_merge`
satisfies Σ min(ℓ, r) ≤ C ≤ Σ (ℓ + r − 1), both sums over the merges of the recursion, where a call on a list of
length L ≥ 2 merges runs of lengths ℓ = ⌊L/2⌋ and r = ⌈L/2⌉. These run lengths depend only on n, so the bounds are
lo(n) and hi(n) with lo(n) = lo(⌊n/2⌋) + lo(⌈n/2⌉) + ⌊n/2⌋, hi(n) = hi(⌊n/2⌋) + hi(⌈n/2⌉) + n − 1 and
lo = hi = 0 for n ≤ 1. Each count listed in `entry.json` (19421, 42827, 93679, 203327, 438368, 941126 at n = 2000,
4000, 8000, 16000, 32000, 64000) lies between them; for example lo(2000) = 10864 ≤ 19421 ≤ 19953 = hi(2000).

**Proof.** Given in `entry.json`, field `verification.method`. The missing steps: (a) the only counted comparison is
the one in the merge loop, and calls on lists of length ≤ 1 return without a comparison, so C is the sum of the
merge-loop iterations over the merges; (b) every merge has ℓ = ⌊L/2⌋ ≥ 1 and r = ⌈L/2⌉ ≥ 1; (c) for the upper
bound, the loop never exhausts both runs: each iteration takes one element from one run, both runs are non-empty
before it, so when the loop stops the other run still has at least one element that the loop did not take, and
there were at most ℓ + r − 1 iterations. The lengths at every call are determined by n through `mid = len(a) // 2`,
which gives the recurrences.

**Check.** At the V2 sizes n = 2000, 4000, 8000, 16000, 32000, 64000:
`experiments/2026-10-07b_count_v2_inversions_lis.py` (three samples per size, each within the bounds).
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "inversion merge: merge bounds": n = 0..39,
1000, 2000, 4000, 8000. `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "inversions merge
bounds on other inputs": n = 0..100, five sequences each; line "inversions listed V2 values: reproduced (sample 0)
and within the merge bounds": n = 2000, 4000, 8000, 16000, 32000, 64000.

## 3. Correctness of both algorithms

Write inv(s) for the number of pairs i < j with s_i > s_j (equal values are not inversions).

**All pairs.** `inversions_quadratic` tests `vi > values[j]` exactly once for every pair i < j (section 1) and adds 1
exactly when it holds, so it returns inv(values).

**Merge-sort counting.** *Claim:* for every list a, `_sort_count(a)` returns (s, inv(a)) where s is a sorted
permutation of a. Induction on L = len(a). For L ≤ 1, a is sorted and inv(a) = 0. For L ≥ 2, with mid = ⌊L/2⌋, the
pairs i < j split into pairs inside a[:mid], pairs inside a[mid:], and *cross* pairs i < mid ≤ j, so
inv(a) = inv(a[:mid]) + inv(a[mid:]) + X with X = #{(x, y) : x in a[:mid], y in a[mid:], x > y} (a count over the two
multisets). By induction `left` and `right` are the two halves sorted and cl, cr are their inversion counts. The
merge loop outputs `right[j]` when `right[j] < left[i]` and `left[i]` otherwise (`left[i] <= right[j]`). Every
element of `left` output before `right[j]` was output at a step with `left[i′] <= right[j′]` for some j′ ≤ j, so it
is ≤ `right[j]` (`right` is sorted); every element `left[i..]` still waiting is ≥ `left[i]` > `right[j]` (`left`
is sorted). So when `right[j]` is output inside the loop, exactly len(left) − i elements of `left` exceed it, and
`cross += len(left) - i` adds exactly that number. If the loop ends because `left` is exhausted, each remaining
`right[j″]` is ≥ every element of `left` (each was output at a step with `left[i′] <= right[j′]`, j′ ≤ j″), so it
contributes 0 to X, and nothing is added; if it ends because `right` is exhausted, every element of `right` was
counted inside the loop. Hence cross = Σ_{y in right} #{x in left : x > y} = X. The merged list is sorted (the
standard merge: each step outputs the smaller head, ties from `left`, and the rest is appended in sorted order), and
it is a permutation of a. So `_sort_count(a)` returns (sorted a, cl + cr + X) = (sorted a, inv(a)), and
`inversions_merge` returns inv(values). This proves the entry's "cross inversions are counted exactly once during
the merge"; the credit is CLRS.

**Check.** `tests/test_proofs_inversions.py`, `test_correct_exhaustive`: both functions equal the definition on every
sequence over {0, 1, 2} of length 0..7 (3280 sequences) and on 300 random sequences with ties of length 0..60
(seed 1); the merged list equals `sorted(values)`. The V1 harness compares both with an independent Fenwick-tree
oracle on n = 0..500.

## 4. Time

**All pairs: Θ(n²).** The outer loop runs n times and the inner loop n(n − 1)/2 times in total (section 1), each
iteration O(1): Θ(n²) for n ≥ 2, on every input.

**Merge-sort counting: Θ(n log n) on every input (n ≥ 2).** *Shape of the recursion.* By induction on the depth d,
every call at depth d has length ⌊n/2^d⌋ or ⌈n/2^d⌉: if L is one of ⌊x⌋, ⌈x⌉ (x = n/2^d), then ⌊L/2⌋ ≥ ⌊⌊x⌋/2⌋ =
⌊x/2⌋ and ⌈L/2⌉ ≤ ⌈⌈x⌉/2⌉ = ⌈x/2⌉, and these two values differ by at most 1. For d ≤ ⌊log₂ n⌋ − 1 we have
⌊n/2^d⌋ ≥ 2, so every call at such a depth splits, and (by induction on d) the calls at each depth
d ≤ ⌊log₂ n⌋ partition the n positions. At depth ⌈log₂ n⌉ every length is ≤ ⌈n/2^⌈log₂ n⌉⌉ = 1, so no call at
that depth or below merges.

*Comparisons.* A merge of runs ℓ = ⌊L/2⌋ ≤ r makes at least ℓ and at most L − 1 comparisons (section 2). At each
depth d ≤ ⌊log₂ n⌋ − 1 the merging calls partition the n positions and ⌊L/2⌋ ≥ L/3 for L ≥ 2, so they make at least
n/3 comparisons; at each depth the merging calls make at most n comparisons in total. Hence

  (n/3) ⌊log₂ n⌋ ≤ lo(n) ≤ C ≤ hi(n) ≤ n ⌈log₂ n⌉.

*Other work.* A call of length L does O(L + 1) work besides its recursive calls (two slices, at most L − 1 loop
iterations, two `extend`s), and the calls of positive length form a binary tree with n leaves, i.e. 2n − 1 calls
(one call for n = 0). The calls at one depth have total length ≤ n, and there are at most ⌈log₂ n⌉ + 1 depths, so
the total work is O(n log n + n). Together with the lower bound on C, the time is Θ(n log n) for n ≥ 2.

**Check.** `tests/test_proofs_inversions.py`, `test_level_bounds`: (n/3)⌊log₂ n⌋ ≤ lo(n) and hi(n) ≤ n⌈log₂ n⌉ for
n = 2..5000 (the recurrences of section 2); `test_call_lengths`: the lengths of the calls at each depth are
⌊n/2^d⌋ or ⌈n/2^d⌉ and the calls number 2n − 1, n = 1..300 (profiler hook). The counts of section 2 are checked by
the scripts listed there.

## 5. Space

**All pairs: O(1) words beyond the input.** Its only locals besides the input are n, count, i, vi and j: integers
and one reference to an element.

**Merge-sort counting: Θ(n).** The top call receives a copy of the input (`list(values)`, n elements), so the space
is at least n. A call at depth d holds `a` (length L_d ≤ ⌈n/2^d⌉), after its children return `left` and `right`
(together L_d), and `merged` (at most L_d): at most 3L_d elements; the slices `a[:mid]`, `a[mid:]` become the
callee's `a`, and the two slices in `extend` are temporaries of length ≤ L_d. The active calls form one path of
depth at most ⌈log₂ n⌉, so at any moment the lists referenced by the active calls hold at most
Σ_d 3⌈n/2^d⌉ ≤ 3(2n + ⌈log₂ n⌉ + 1) elements, and the temporaries at most as many again: O(n). The recursion depth
is ⌈log₂ n⌉ + 1 calls (n ≥ 1).

**Check.** `tests/test_proofs_inversions.py`, `test_space`: for n = 0..64, 100, 500 and 1000 (seed 2), the largest
total length of the lists referenced by the active calls of `_sort_count` (a trace hook reads `a`, `left`, `right`,
`merged` at every line event) is at least n and at most 6n + 3⌈log₂ n⌉ + 3, and the depth is ⌈log₂ n⌉ + 1 (1 for
n ≤ 1); the all-pairs function's locals other than the input are never lists.

## 6. The separation (T3)

Both functions return inv(values) (section 3); all pairs takes Θ(n²) and merge-sort counting Θ(n log n) on every
input (section 4). The improvement comes from counting all cross inversions of two sorted halves during one
linear merge.
