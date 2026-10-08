# Proofs: closest pair, all pairs vs divide and conquer

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
from the code in this folder: the exact operation counts for every size of their domains (sections 1–2), the
correctness, time and space of the all-pairs scan (section 3), the correctness of divide and conquer (section 4), its
packing lemma and Θ(n log n) time (section 5) and its space (section 6), and the separation with the reduction from
element distinctness (section 7). Each proof is followed by the deterministic scripts or tests that check it and the
sizes they check it on. A check covers only those sizes; the proofs cover the whole domain. Section 8 lists the
measured statements. The statements listed under "Background" in `entry.json` are cited, not proved here; one of
them is the machine-model assumption on the built-in sort and `min()`, which the upper time and space bounds of
sections 5 and 6 use and say so.

## Counting convention

`harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`) adds 1 to the module counter `_mults`, and
`__pow__` with exponent 2 adds 1 (any other exponent raises). `__add__`, `__radd__`, `__sub__` and `__rsub__` return
a new `CountingInt` without counting; the comparison methods add to the separate counter `_comparisons`, which is
not reported. `generate_scaling(n, rng)` returns n points whose two coordinates are `CountingInt` (values in
[0, 10⁹)) and sets `_mults = _comparisons = 0`; `reported_cost(output)` returns `_mults`. Every difference of two
coordinates is a `CountingInt`, so every product or square of such a difference counts exactly 1. Both
implementations raise `ValueError` for n < 2, so the domain of every count below is n ≥ 2.

## 1. All pairs: n(n − 1)/2 distance evaluations, n(n − 1) multiplications

**Statement.** For every n ≥ 2 and every input, `closest_pair_brute` evaluates exactly n(n − 1)/2 squared distances
and makes exactly n(n − 1) counted multiplications. The values listed in `entry.json` (15500 at n = 125, …,
3998000 at n = 2000) are n(n − 1).

**Proof.** The double loop runs once for each pair i < j, n(n − 1)/2 times, with no early exit. Each iteration
computes `dx * dx + dy * dy` with `dx`, `dy` differences of coordinates, hence two counted products; the addition
and the comparison `d < best` do not count multiplications. Total 2 · n(n − 1)/2 = n(n − 1).

**Check.** At the V2 sizes n = 125, 250, 500, 1000, 2000: `experiments/2026-10-07b_count_v2_closest_pair.py`.
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "closest pair brute n(n-1) mults":
n = 2..29 and the V2 sizes (n = 0, 1 raise `ValueError`, as stated).

## 2. Divide and conquer: strip filter S(n), base cases 2 per pair, strip scan the rest

**Statement.** For every n ≥ 2 and every input, the counted multiplications of `closest_pair_dc` split into three
parts:
- the strip filter makes exactly S(n) squarings, where S(s) = 0 for s ∈ {2, 3} and
  S(s) = s + S(⌊s/2⌋) + S(⌈s/2⌉) for s ≥ 4 (for example S(64000) = 955392);
- the base cases make exactly 2 products per pair of points inside each leaf of the recursion, that is
  B(n) = Σ over leaves of 2·C(s, 2) (s ∈ {2, 3} points per leaf);
- the strip scan makes the rest: 1 product for every examined pair (a, b) at which the loop breaks and 3 for every
  examined pair at which it does not.

**Proof.** The only multiplications on counted values are in `_dist2`, in the strip filter
`(p[0] - xm) ** 2` and in the strip scan; `sorted`, `min` and the merge only compare. A call `_solve(px, lo, hi)`
with s = hi − lo points:
- If s ≤ 3 (a leaf; the top-level call has s = n ≥ 2 and every recursive call has s ≥ 2, since it is made only for
  s ≥ 4 on ⌊s/2⌋ and ⌈s/2⌉ points), it evaluates `_dist2` once for each of the C(s, 2) pairs, and each evaluation
  makes the two counted products `dx * dx` and `dy * dy`. It makes no squaring.
- If s ≥ 4, it recurses on `px[lo:mid]` and `px[mid:hi]` with mid = (lo + hi) // 2, so on
  mid − lo = ⌊s/2⌋ and hi − mid = ⌈s/2⌉ points. `merged` then holds all s points, and the strip filter evaluates
  `(p[0] - xm) ** 2` once per point: s counted squarings (`p[0] - xm` is a `CountingInt`, and `**` calls
  `CountingInt.__pow__` with exponent 2).

Summing over the recursion tree gives S(n) squarings and B(n) base-case products. In the strip scan each examined
pair computes `dy * dy` (1 count) for the test `dy * dy >= best`; if the loop does not break, it computes
`d = dx * dx + dy * dy` (2 more counts). No other multiplication occurs. The value S(64000) = 955392 follows from
the recursion (64000 → 32000 → 16000 → 8000 → 4000 → 2000 → 1000 → 500 → 250 → 125 → 62, 63 → …).

**Check.** At the V2 sizes n = 1000, 2000, 4000, 8000, 16000, 32000, 64000:
`experiments/2026-10-07b_count_v2_closest_pair.py` (totals, checked equal to the values listed in `entry.json`).
`experiments/2026-10-07_closed_form_checks.py`, group
`sorting`, lines "closest pair D&C strip filter S(n)=n+S(fl)+S(cl), S(2)=S(3)=0" and "closest pair D&C base cases:
2 products per pair in leaves": n = 2..39 and the V2 sizes (it prints S(64000) = 955392).
`experiments/2026-10-07_count_proof_checks.py`, group `algebra`, line "closest pair D&C strip scan = examined pairs
+ 2 x non-breaking pairs": n = 2..60 and n = 1000, 4000.

The divide-and-conquer totals listed in `entry.json` (14523, …, 1436363) are measured values of one seeded instance
per size (the script above reproduces them exactly); the strip scan depends on the input and has no closed form.

## 3. All pairs: correctness, Θ(n²) time, O(1) extra space

`closest_pair_brute` computes `dx * dx + dy * dy` = (x_i − x_j)² + (y_i − y_j)² for every pair i < j (section 1:
n(n − 1)/2 evaluations, no early exit) and keeps the minimum, so it returns the minimum squared distance over all
pairs i ≠ j; Python integers make every value exact. Each evaluation costs Θ(1) in the entry's cost model
(coordinates below 10⁹), so the time is Θ(n²) on every input. Its locals are integers and the input's own tuples, so
it creates no container: O(1) words besides the input.

**Check.** The V1 battery (n = 2..500) against the plane-sweep oracle. `tests/test_proofs_closest_pair.py`,
`test_correct_on_adversarial_inputs` (420 seeded point sets, n = 2..70, seven kinds: generic, tiny grid with
duplicates, one vertical line, square lattice, two columns straddling the median, coincident points on the median
line, clusters with negative coordinates; against `harness.check` and between the two implementations) and
`test_space` (56 point sets: the instrumented peak of `tests/proof_space.py` is 0 for the all-pairs scan).

## 4. Divide and conquer: correctness

**Statement.** For every input of n ≥ 2 points with integer coordinates, `closest_pair_dc` returns the minimum
squared distance over all pairs i ≠ j.

**Lemma 4.1.** For every call `_solve(px, lo, hi)` with s = hi − lo ≥ 2, where `px` is the list of all points sorted
by (x, y): it returns (δ², Y) with δ² the minimum squared distance among the points px[lo:hi] and Y those points
sorted by y.

*Proof.* Induction on s. For s ≤ 3 the call takes the minimum of `_dist2` over all pairs and sorts the slice by y
(`sorted` with `key=lambda p: p[1]`). For s ≥ 4, mid = (lo + hi) // 2 gives halves of ⌊s/2⌋ ≥ 2 and ⌈s/2⌉ ≥ 2 points,
so the induction hypothesis applies to both calls. Let xm = px[mid][0]; since px is sorted by x, every left point has
x ≤ xm and every right point has x ≥ xm. `best` starts as min(δ_l², δ_r²).

*The merge.* Each step appends the smaller head of `left` and `right` (the left one on ties), and the remainders
are appended at the end. Invariant: `merged` is sorted by y, and each of its elements has y at most that of every
element remaining in either list (a head is ≤ everything after it in its own sorted list, and the chosen head is ≤
the other head). So `merged` is the s points sorted by y.

*Cross pairs.* Let p (left) and q (right) satisfy d²(p, q) < `best` (the value before the scan). Then
(x_q − x_p)² < `best`, and x_p ≤ xm ≤ x_q gives (xm − x_p)² ≤ (x_q − x_p)² and (x_q − xm)² ≤ (x_q − x_p)², so both are
in `strip` (the filter `(p[0] - xm) ** 2 < best`), which inherits the y order of `merged`.

*The scan.* `best` only decreases, and is always the squared distance of some pair of the call's points or one of
δ_l², δ_r². For strip positions a < b, y_b ≥ y_a. The inner loop for a breaks at the first b′ with (y_{b′} − y_a)² ≥
the current `best`; every later b has y_b − y_a ≥ y_{b′} − y_a ≥ 0, so d²(a, b) ≥ (y_b − y_a)² ≥ the current `best`,
and skipping it cannot miss a pair below the final value. Now let the true minimum be d²(p, q). If both are in one
half, `best` ≤ min(δ_l², δ_r²) ≤ d²(p, q) from the start. Otherwise p and q are a cross pair; if d²(p, q) ≥
min(δ_l², δ_r²) again there is nothing to show, and if it is smaller, both are in the strip, say at positions a < b,
and the scan for a either reaches b and sets `best` ≤ d²(p, q), or breaks at some b′ ≤ b with
`best` ≤ (y_{b′} − y_a)² ≤ (y_b − y_a)² ≤ d²(p, q). So the final `best` is the minimum, and the call returns it with
`merged`.

*Proof of the statement.* `closest_pair_dc` raises `ValueError` for n < 2 and otherwise returns the δ² of
`_solve(px, 0, n)` with px = `sorted(points)`, sorted by (x, y). All values are Python integers, so every comparison
is exact (the proofs use this).

**Check.** As in section 3: the V1 battery (n = 2..3000) and `tests/test_proofs_closest_pair.py`,
`test_correct_on_adversarial_inputs`.

## 5. Divide and conquer: the packing lemma and Θ(n log n) time

**Lemma 5.1 (packing).** In the scan of a call, every strip position a examines at most 8 positions b (computes
`dy` for them) and makes the full distance computation (`dx`, `d`) for at most 7 of them.

*Proof.* Let δ² = min(δ_l², δ_r²) be `best` when the strip is built. If δ = 0 the strip is empty, since
(x − xm)² < 0 is impossible. Otherwise, a position b > a passes the test `dy * dy >= best` only if (y_b − y_a)² <
`best` ≤ δ², i.e. 0 ≤ y_b − y_a < δ, and every strip point has |x − xm| < δ. So a and every b that passes lie in the
rectangle [xm − δ, xm + δ] × [y_a, y_a + δ]. Its left half [xm − δ, xm] × [y_a, y_a + δ] is the union of four closed
squares of side δ/2, each of diameter δ/√2 < δ; two left points have squared distance ≥ δ_l² ≥ δ², so each square
holds at most one left point: at most 4 left points in the rectangle (left points have x ≤ xm). Likewise at most 4
right points in the right half. So the rectangle holds at most 8 strip points including a: at most 7 positions pass
the test (each gets the full computation), and the loop examines at most one more, at which it breaks.

**Lemma 5.2 (the recursion).** Let S(n) = Σ of s over the calls with s ≥ 4 (the internal nodes of the recursion
tree), as in section 2. For n ≥ 4, n(⌊log₂ n⌋ − 1) ≤ S(n) ≤ n⌈log₂ n⌉; the tree has at most n/2 leaves, and the
recursion depth is at most log₂(n − 1).

*Proof.* By induction on the depth d, the nodes at depth d have sizes ⌊n/2^d⌋ or ⌈n/2^d⌉ (halving a size in
{⌊m⌋, ⌈m⌉}, m = n/2^d, gives sizes in {⌊m/2⌋, ⌈m/2⌉}) and their point sets partition the n points, as long as the
level exists. If ⌊n/2^d⌋ ≥ 4, every node at depth d is internal and the level contributes exactly n to S(n); this
holds for d = 0, …, ⌊log₂ n⌋ − 2, which gives the lower bound. A node at depth d has size ≤ ⌈n/2^d⌉, which is
< 4 once 2^d ≥ n/3, so internal nodes occur only at depths d < log₂(n/3), at most ⌈log₂ n⌉ levels, each contributing
at most n. Leaves have 2 or 3 points and are disjoint: at most n/2. A node at depth d has size at most
(n − 1)/2^d + 1, and calls are made only for sizes ≥ 2, so 2^d ≤ n − 1.

**Machine-model assumption (background).** The built-in sort runs in O(m log m) time with O(m) extra space on m
items, and `min()` over k values takes O(k) time. `closest_pair_dc` calls the sort once on the n points and once in
every leaf, on at most 3 points (1 + #leaves calls, with at most n/2 leaves by Lemma 5.2; 489 calls at n = 1000). It
calls `min()` once in every leaf, over at most 3 values, and once in every internal call, `min(best_l, best_r)` over 2
values; the recursion tree is a full binary tree with #leaves − 1 internal calls, so there are 2·#leaves − 1 `min()`
calls in all (975 at n = 1000). Under the assumption each of these leaf and internal built-in calls costs O(1).

**Statement (time).** Under the assumption, `closest_pair_dc` takes Θ(n log n) time on every input with n ≥ 2.
Without it, the work outside the built-in calls is Θ(n log n), and the lower bound Ω(n log n) holds on every input.

*Proof.* A leaf (2 or 3 points) costs O(1) besides its built-in calls: at most 3 distances and a slice of ≤ 3 points;
its `min()` over ≤ 3 values and its sort of ≤ 3 items cost O(1) under the assumption. An
internal call with s points costs Θ(s) besides its two recursive calls: `min(best_l, best_r)` costs O(1) under the
assumption, the merge appends each of the s points once
(Θ(s) comparisons and appends), the filter squares s values (section 2), and the scan makes at most 8 steps per strip
point (Lemma 5.1), each O(1); the slices `left[i:]`, `right[j:]` cost O(s). Summing over the tree, the time is
Θ(S(n) + number of leaves) = Θ(n log n) by Lemma 5.2. The lower bound Ω(n log n) holds on every input without the
assumption: the filter alone makes S(n) ≥ n(⌊log₂ n⌋ − 1) squarings. The initial sort of the n points by (x, y)
costs O(n log n) under the assumption, which is the only part of the upper bound that is not proved here.

**Check.** `tests/test_proofs_closest_pair.py`, `test_strip_packing` (280 seeded point sets of the seven kinds of
section 3, n = 2..70; the examined and fully computed positions are counted per strip position of every call from the
running code: at most 8 and 7; the largest values met are 4 and 3) and `test_strip_filter_sum_bounds` (the bounds
of Lemma 5.2 for n = 4..5000, and S(64000) = 955392), and `test_builtin_call_counts` (n = 2..119 and 1000, wrappers
for `sorted` and `min` placed in the module's globals: 1 + #leaves sorts, one on n points and the others on at most 3,
and 2·#leaves − 1 `min()` calls on at most 3 values; 489 and 975 at n = 1000). The filter count S(n) is checked
against the running code as listed in section 2.

## 6. Divide and conquer: Θ(n) space

**Statement.** Besides the input, `closest_pair_dc` holds Θ(n) words under the assumption: counting one word per
container slot, the lists of its own code hold at least n (the sorted list `px`) and at most 5n + ⌈log₂ n⌉ + 6 at any
time, and the built-in sort's working space is O(n) under the assumption.

*Proof.* `px` has n slots. Consider the active calls, of sizes s_0 = n > s_1 > … > s_k (the last one running). A call
that is not the last is inside one of its recursive calls; while it is in the second one it holds `left`, with
⌊s_d/2⌋ slots, and otherwise nothing. The last call holds at most `left`, `right` (s_k slots together), `merged`
(s_k) and `strip` (≤ s_k), or, in a leaf, a slice and a sorted list of ≤ 3 points each: at most max(3s_k, 6). Since
s_{d+1} ≤ ⌈s_d/2⌉, s_d ≤ (n − 1)/2^d + 1, so Σ_{d<k} ⌊s_d/2⌋ ≤ (n − 1) + k/2 with k ≤ log₂(n − 1) (Lemma 5.2), and
3s_k ≤ 3n. Total at most n + (n − 1) + k/2 + 3n + 6 ≤ 5n + ⌈log₂ n⌉ + 6. The points themselves are the input's
tuples. The count includes every list a call holds, including those it is still building; the top-level frame also
holds the returned list (n slots) after the recursion, when no other call is active. The working space of the
built-in sort is not counted above; under the assumption it is O(n), so the total is Θ(n).

**Check.** `tests/test_proofs_closest_pair.py`, `test_space` (56 seeded point sets, n = 2..70: the instrumented peak
lies between n and 5n + ⌈log₂ n⌉ + 6).

## 7. The separation, and the reduction from element distinctness

*Separation (T3).* All pairs takes Θ(n²) time on every input (section 3) and divide and conquer Θ(n log n) on every
input under the assumption on the built-in sort (section 5); so the tag rests on that assumption.

*Zero answer.* The minimum squared distance is 0 if and only if two of the points coincide, since
(x_i − x_j)² + (y_i − y_j)² = 0 exactly when both differences are 0. So n reals x_1, …, x_n are pairwise distinct iff
the points (x_i, 0) have a positive minimum distance: element distinctness reduces to closest pair with no extra
operation. *Conditional optimality:* if the background lower bound for element distinctness in the algebraic
computation tree model on real inputs holds (Ben-Or 1983), the reduction gives Ω(n log n) for closest pair in that
model, and divide and conquer matches it up to a constant factor there under the sort assumption (its operations on
coordinates are comparisons, subtractions and multiplications, and section 5 does not use integrality). This
statement is conditional on that background lower bound and is not a theorem about the integer inputs of this
entry.

**Check.** `tests/test_proofs_closest_pair.py`, `test_correct_on_adversarial_inputs` also checks that the answer is 0
exactly on the inputs with a repeated point.

## 8. Measured statements (data, not theorems)

The divide-and-conquer totals listed in `entry.json` (one seeded instance per size) and their ratios to n log₂ n,
the share of the strip filter in them (61.5% to 66.5%), the V2 fits, the earlier timing fit, and the comparison
counts under Python 3.12.10 and 3.14.2 are measurements; section 2 proves the decomposition that they split.
