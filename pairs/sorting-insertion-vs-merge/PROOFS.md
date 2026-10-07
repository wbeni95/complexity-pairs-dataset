# Proofs: comparison sorting, insertion sort vs merge sort

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings and comments of the code): the correctness of both algorithms, every stated time and
space bound (worst case, average case and every input), every exact operation count on its domain, and the
Ω(n log n) lower bound for comparison sorting in the worst case, on average and for randomized algorithms. Sections 1
to 3 prove the exact counts; sections 4 to 10 prove the rest. Statements about the literature (faster integer
sorting outside the comparison model) are not claims of this entry: they are listed under `background` in
`entry.json`, with their sources, and are not proved here. Each proof is followed by the deterministic scripts or
tests that check its computable facts and the ranges they check. A check covers only those ranges; the proofs cover
the general statements.

## Counting convention

`harness.py`, class `CountingKey`: each of `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__` and `__ne__` adds 1 to
the module counter `_comparisons` (`_comparisons += 1`) and then compares the wrapped integers. No other operation
counts. `generate_scaling(n, rng)` wraps the values of `generate(n, rng)` (n integers drawn uniformly from
[−n, n], so ties occur) in `CountingKey` and then sets `_comparisons = 0`; `reported_cost(output)` returns
`_comparisons`. The only counted comparisons are `a[j] > key` in `insertion_sort` and `right[j] < left[i]` in
`merge_sort` (as the harness docstring says, insertion sort compares only with `>` and merge sort only with `<`);
both compare two input elements, so each counts exactly 1. Not counted: `list(xs)`, slicing, `append`, `extend`,
and the tests on plain ints (`j >= 0`, `len(xs) <= 1`, `i < len(left)`, `j < len(right)`).

For an input x_0, …, x_(n−1) write g_i = #{p < i : x_p > x_i} and I = Σ_i g_i, the number of inversions (pairs
p < q with x_p > x_q).

The entry states no exact comparison count for merge sort: its listed values (8701 at n = 1000, …, 941409 at
n = 64000) are measured on seeded instances (`experiments/2026-10-07b_count_v2_sorting.py` reproduces them).

## 1. Insertion sort: Σ_i (g_i + [g_i < i]) comparisons

**Statement.** On every list of n ≥ 0 elements, `insertion_sort` makes exactly Σ_{i=1..n−1} (g_i + [g_i < i])
comparisons. On a strictly decreasing list (I = n(n − 1)/2) this is n(n − 1)/2. The insertion-sort means listed
in `entry.json` (15574.67, 63461.67, 250154.67, 999716.33, 3990076 at n = 250, 500, 1000, 2000, 4000) are the means
of this formula over the three seeded V2 instances at each size (samples 0, 1, 2 of `tools/validate.py`).

**Proof.** Invariant: before iteration i, `a[0..i−1]` holds x_0, …, x_(i−1) in non-decreasing order and
`a[i..]` is untouched (true for i = 1). In iteration i, `key = a[i]` = x_i and j = i − 1. The `while` test checks
`j >= 0` first (plain ints, no comparison) and then compares `a[j] > key`. The elements of the sorted prefix that
are larger than x_i are its last g_i entries, so the first g_i comparisons are true; each shifts `a[j]` one place
right and lowers j. Then j = i − 1 − g_i. If g_i < i, the next comparison `a[j] > key` is false (1 more); if
g_i = i, j = −1 and the loop stops at `j >= 0` without a comparison. `a[j + 1] = key` puts x_i after every
element ≤ x_i, which restores the invariant. So iteration i costs g_i + [g_i < i]. On a strictly decreasing list
g_i = i for every i, so the cost is Σ_{i=1..n−1} i = n(n − 1)/2.

**Check.** `experiments/2026-10-07b_count_v2_sorting.py` compares the formula with the count at n = 50, 100, 250,
500 (sample 0) and reproduces the three-sample means at the V2 sizes n = 250, 500, 1000, 2000, 4000.
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "insertion sort sum_i g_i + [g_i < i]
(instance formula)": n = 0..29, 50, 100, 250, 500, 1000 (sample 0). `experiments/2026-10-07_count_proof_checks.py`,
group `strings`, line "insertion sort sum_i g_i+[g_i<i] on other inputs (n(n-1)/2 on strictly decreasing)":
n = 0..60, five lists each (many ties, increasing, decreasing, constant, random); line "insertion sort listed V2
means = mean of the instance formula over the 3 seeded instances": n = 250, 500, 1000, 2000, 4000.

## 2. Insertion sort: element moves = inversions

**Statement.** On every list of n ≥ 1 elements, the shift `a[j + 1] = a[j]` runs exactly I times, and each shift
removes exactly one inversion; the outer loop runs n − 1 times, so the two loops run n − 1 + I iterations in all
(the "work" of the docstring of `implementations/insertion_sort.py`). The number of comparisons is
n − 1 + I − #{i ≥ 1 : g_i = i} ≤ n − 1 + I.

**Proof.** By section 1, iteration i makes g_i shifts, so there are Σ_i g_i = I shifts. During iteration i, think of
`key` as standing in the gap at position j + 1. A shift moves `a[j]`, which is larger than `key`, from position j
to j + 1 and the gap to j: an adjacent transposition of the pair (a[j], key), which reverses the order of this one
inverted pair and of no other pair, so it removes exactly one inversion. `range(1, len(a))` gives n − 1 outer
iterations for n ≥ 1. The comparison count is Σ_{i≥1} (g_i + 1) − #{i ≥ 1 : g_i = i}.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "insertion sort: shifts = I,
outer iterations n-1, comparisons n-1+I-#{i: g_i = i}": n = 1..40, five lists each (line counts of the unchanged
function).

## 3. Merge sort: ⌈log₂ n⌉ levels of merges

**Statement.** For every n ≥ 1, the recursion of `merge_sort` merges on exactly ⌈log₂ n⌉ levels: the calls at
depths 0, …, ⌈log₂ n⌉ − 1 include calls on lists of length ≥ 2 (which merge), and every deeper call has length
≤ 1. On each level every element takes part in at most one merge; it takes part in exactly one merge on every
level if and only if n is a power of two. (So "the merges on each level touch every element once", in the docstring
of `implementations/merge_sort.py`, holds exactly for powers of two; otherwise the last level leaves some elements
out.)

**Proof.** A call on a list of length ℓ ≥ 2 splits it into lengths ⌊ℓ/2⌋ and ⌈ℓ/2⌉ and merges after both return;
a call with ℓ ≤ 1 makes no call and no merge. By induction on the depth d, every call at depth d has a length
between ⌊n/2^d⌋ and ⌈n/2^d⌉ (using ⌊⌊x⌋/2⌋ = ⌊x/2⌋ and ⌈⌈x⌉/2⌉ = ⌈x/2⌉ for real x), and the path that always
takes the right half has length exactly ⌈n/2^d⌉. So there is a call of length ≥ 2 at depth d if and only if
⌈n/2^d⌉ ≥ 2, that is n > 2^d, that is d ≤ ⌈log₂ n⌉ − 1. The calls at one depth work on disjoint parts of the list,
so each element is in at most one merge per level. If n = 2^k, every call at depth d < k has length 2^(k−d) ≥ 2, so
every element is merged on every level. If n is not a power of two, let K = ⌈log₂ n⌉ ≥ 2. Every call at depth
d ≤ K − 2 has length ≥ ⌊n/2^d⌋ ≥ 2, so the 2^(K−1) calls at depth K − 1 exist and cover all n elements; their
lengths are 1 or 2 (because 1 < n/2^(K−1) < 2) and sum to n < 2^K, so at least one has length 1, and its element is
in no merge on level K − 1.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "merge sort: ceil(log2 n) merge
levels; each element in at most one merge per level, in exactly one on every level iff n is a power of two":
n = 1..300, 511, 512, 513, 1000, 1024.

## 4. Correctness of insertion sort

**Statement.** For every list xs, `insertion_sort(xs)` returns a new list with the elements of xs in non-decreasing
order and does not modify xs.

**Proof.** `a = list(xs)` is a copy; only `a` is written. By the invariant of section 1, after the last iteration
(i = n − 1) a[0..n − 1] holds x_0, …, x_(n−1) in non-decreasing order. (Each iteration only shifts entries of the
prefix and writes `key` into the gap, so `a` stays a rearrangement of xs.)

**Check.** `tests/test_proofs_sorting.py`, `CorrectnessTests`: n = 0..60, 100, 500, five input kinds (random with
ties, increasing, decreasing, constant, random distinct): output equals `sorted`, input unchanged, output a new list.
V1 (the validator also checks non-mutation).

## 5. Correctness and stability of merge sort

**Statement.** For every list xs, `merge_sort(xs)` returns a new list with the elements of xs in non-decreasing
order, does not modify xs, and is stable: elements with equal keys keep their input order (code comment "take from
the left on ties: the sort is stable").

**Proof.** *Merge.* Let `left` and `right` be sorted. Each loop iteration appends the smaller head (the left head on
ties, since it appends `right[j]` only if `right[j] < left[i]`) and advances that list; when one list is exhausted
the rest of the other, already sorted, is appended. Every appended element is ≤ every element appended after it:
the heads are the minima of the remaining parts of their sorted lists, so the appended head is the minimum of all
remaining elements. So `out` is the sorted merge of all elements. *Induction on n.* For n ≤ 1, `list(xs)` is a sorted
copy. For n ≥ 2, the slices are copies of the two halves, sorted by induction, and merged. Only slices and new lists
are created, so xs is not modified. *Stability.* By induction, `left` and `right` keep the input order among equal
keys; every element of `left` precedes every element of `right` in the input; on equal heads the merge takes the
left one first, and within each list the order is kept.

**Check.** `tests/test_proofs_sorting.py`, `CorrectnessTests` (as in section 4) and `test_merge_stable`: keys in
{0, …, 3} with input positions as tags, n = 0..79, compared by key only: the output order equals the order of
(key, position).

## 6. Insertion sort: time on every input, worst case, average case

**Statement.** (a) Insertion sort takes Θ(n + I) time on every input, I the number of inversions: Θ(n) on sorted
input and Θ(n²) on reversed input (I = n(n − 1)/2). (b) On a uniformly random order of n distinct elements,
E[I] = n(n − 1)/4 and the expected number of comparisons is n(n − 1)/4 + n − H_n (H_n = 1 + 1/2 + … + 1/n); for the
harness distribution (n values drawn independently and uniformly from [−n, n]), E[I] = n(n − 1)/4 · 2n/(2n + 1). So
insertion sort takes Θ(n²) time on average (`time_complexity`, docstring "n(n − 1)/4 expected inversions").

**Proof.** (a) By section 2 the loops run n − 1 + I iterations for n ≥ 1, each O(1), plus the Θ(n) copy. The number
of comparisons lies between max(n − 1, I) and n − 1 + I (section 2; each outer iteration makes at least one
comparison, because either g_i < i or g_i = i ≥ 1). Sorted input has I = 0; strictly decreasing input has every pair
inverted, I = n(n − 1)/2. (b) I = Σ over pairs p < q of [x_p > x_q]. For i.i.d. values, P(x_p > x_q) = (1 − P(x_p =
x_q))/2 by symmetry; for a uniformly random order of distinct elements P(x_p = x_q) = 0, and for the uniform
distribution on the 2n + 1 integers of [−n, n] it is 1/(2n + 1), so P(x_p > x_q) = n/(2n + 1). Linearity of
expectation over the n(n − 1)/2 pairs gives both values of E[I]. For distinct elements in random order, the
comparison count is Σ_{i≥1} (g_i + [g_i < i]) (section 1), and g_i = i exactly when x_i is the smallest of
x_0, …, x_i, which has probability 1/(i + 1); so the expectation is E[I] + Σ_{i=1..n−1} (1 − 1/(i + 1)) =
n(n − 1)/4 + n − H_n. Both expectations of I are Θ(n²) (2n/(2n + 1) ≥ 2/3 for n ≥ 1).

**Check.** `tests/test_proofs_sorting.py`, `InsertionAverageTests`: exhaustively over all n! orders for n = 1..8
(both expectations exactly, in rational arithmetic), and over all (2n + 1)^n lists with entries in [−n, n] for
n = 1..5 (E[I] exactly, and the comparison count equals the formula of section 1 on every list). The scripts of
sections 1 and 2.

## 7. Merge sort: Θ(n log n) on every input

**Statement.** For every n ≥ 2 and every input, merge sort makes between (n/3)⌊log₂ n⌋ and n⌈log₂ n⌉ comparisons
and takes Θ(n log n) time; this is the solution of T(n) = 2T(n/2) + Θ(n) (`time_complexity`).

**Proof.** A merge of lists of lengths a and b makes at least min(a, b) comparisons (each iteration advances one of
the two indices by 1, and the loop runs until one list is exhausted) and at most a + b − 1. By section 3 the merges
happen on ⌈log₂ n⌉ levels, and on each level the merges involve disjoint sets of elements, so each level makes at
most n comparisons: at most n⌈log₂ n⌉. For the lower bound, every call at depth d has length at least ⌊n/2^d⌋
(section 3); for d ≤ ⌊log₂ n⌋ − 1 this is at least 2, so all calls at depth d merge and together they contain all n
elements. A call of length ℓ ≥ 2 makes at least ⌊ℓ/2⌋ ≥ ℓ/3 comparisons, so each of these ⌊log₂ n⌋ levels makes at
least n/3. Time: a call of length ℓ ≥ 2 does Θ(ℓ) work outside its recursive calls (two slices, the merge, the
extends), and a call of length ≤ 1 O(1); summing over the levels (Θ(n) per level on the ⌊log₂ n⌋ full levels, O(n)
on each of the at most ⌈log₂ n⌉ + 1 levels in all) gives Θ(n log n).

**Check.** `tests/test_proofs_sorting.py`, `MergeBoundsTests`: n = 2..300, 511, 512, 513, 1000, 1024, five input
kinds, comparisons counted with the harness's `CountingKey`. The script of section 3 (merge levels).

## 8. The Ω(n log n) lower bound for comparison sorting, and the optimality of merge sort

**Statement** (`lower_bounds`, `relationship`, README). In the comparison model (the elements are accessed only by
comparing two of them), every correct sorting algorithm makes at least log₂(n!) = n log₂ n − O(n) comparisons in
the worst case and on average over a uniformly random order of n distinct elements; every randomized comparison sort
that is always correct makes at least log₂(n!) comparisons in expectation on some input. Merge sort is therefore
optimal among comparison sorts up to lower-order terms.

**Proof.** Fix n and n distinct keys; the inputs are their n! orders. On distinct keys each comparison has two
possible outcomes (an equality test is always false and gives no information). *Deterministic algorithms.* The
algorithm's actions, including which input element it outputs at each position, depend on the input only through
the outcomes of its comparisons. So the runs form a binary tree: a node is a sequence of outcomes, a run on input π
follows the path of its outcomes and ends at a leaf ℓ(π). Two orders π ≠ σ of distinct keys need different
rearrangements to be sorted, so ℓ(π) ≠ ℓ(σ), and no ℓ(π) lies on the path to another ℓ(σ) (a run stops at its leaf).
Write d(π) for the number of comparisons on π, the depth of ℓ(π). *Worst case:* a binary tree has at most 2^D nodes
at depth D and at most 2^D pairwise incomparable nodes of depth ≤ D, so max_π d(π) ≥ log₂(n!). *Average:* assign to
each node of depth d the set of infinite 0/1 sequences that start with its outcome sequence, of measure 2^(−d); the
sets of the n! pairwise incomparable leaves are disjoint, so Σ_π 2^(−d(π)) ≤ 1 (Kraft's inequality). By convexity of
x ↦ 2^(−x), 2^(−avg d) ≤ avg 2^(−d) ≤ 1/n!, so the average of d(π) is at least log₂(n!). *Randomized algorithms.* An
algorithm that uses random bits r, independent of the input, and always sorts correctly is, for each fixed r, a
deterministic comparison sort, so E_π[d(π, r)] ≥ log₂(n!) for each r. Averaging over r (all quantities are
non-negative, so the order of the averages can be exchanged), E_π[E_r d(π, r)] ≥ log₂(n!), hence some π has
E_r d(π, r) ≥ log₂(n!). (This is the easy direction of Yao's minimax principle.) *The size of log₂(n!).*
n! ≤ nⁿ, and eⁿ = Σ_k n^k/k! ≥ nⁿ/n! gives n! ≥ (n/e)ⁿ; so n log₂ n − n log₂ e ≤ log₂(n!) ≤ n log₂ n.
*Optimality.* Merge sort makes at most n⌈log₂ n⌉ < n log₂ n + n comparisons on every input (section 7), which exceeds
the lower bound by at most n(1 + log₂ e) = O(n).

**Check.** `tests/test_proofs_sorting.py`, `LowerBoundTests`: the two bounds on log₂(n!) for n = 1..2000; for both
implementations and n = 1..8, the outcome sequences on the n! orders of distinct keys are n! distinct sequences, none
a prefix of another, with Σ 2^(−length) ≤ 1, maximum length ≥ ⌈log₂ n!⌉ and mean length ≥ log₂ n!.

## 9. Space bounds

**Statement.** Insertion sort uses Θ(n) space for the output copy and O(1) extra; merge sort uses Θ(n) auxiliary
space.

**Proof.** Insertion sort allocates only the copy `a` and the variables i, j, `key`. Merge sort: a call of length ℓ
holds, besides its argument, the two slices (ℓ in all, each alive while it is sorted), the sorted halves `left` and
`right` (ℓ in all) and `out` (ℓ); its recursive calls run one at a time, so the peak satisfies S(ℓ) ≤ c ℓ + S(⌈ℓ/2⌉)
for a constant c, hence S(n) ≤ 2c n + O(log n) = O(n); the output has n entries.

**Check.** `tests/test_proofs_sorting.py`, `SpaceTests`: for n = 1000..16000 (doubling) the peak traced allocation
divided by n is between 8 and 200 and varies by a factor of at most 1.5, for both algorithms.

## 10. Remarks in the caveats; the T3 classification

**Statement.** (a) Insertion sort is linear on sorted lists and, more generally, Θ(n + I) (section 6); its average
case on random input, measured in V2, is Θ(n²), the same order as its worst case. (b) The lower bound of section 8 is
proved for the comparison model only; merge sort is optimal among comparison sorts. (c) It is not optimal for integer
sorting in general (`caveats`): counting sort sorts n integers from [−n, n] (the harness range) with O(n) word
operations and no comparison of two elements. (d) Θ(n²) (worst and average case) → Θ(n log n): both polynomial, the
exponent drops (T3).

**Proof.** (a) Section 6. (b) Section 8 uses that the algorithm accesses the elements only by comparisons. (c)
Counting sort: set 2n + 1 counters to 0; for each element x add 1 to counter x + n; then for v = −n, …, n append v
as many times as counter v + n says. The output contains each value exactly as often as the input, in increasing
order, so it is the sorted list. The work is (2n + 1) + n + (2n + 1) + n steps of O(1) each (initialise, count, scan
the counters, append), O(n) in all, and no two elements are compared. So outside the comparison model the
Ω(n log n) bound does not hold for these inputs. (d) Sections 6 and 7.

**Check.** (c) `tests/test_proofs_sorting.py`, `CountingSortTests`: counting sort (written in the test, operating
on plain integers) returns `sorted(xs)` on the harness inputs and on the five input kinds for n = 0..299, with at most
6n + 2 counted steps and no element comparison. (d) The V2 fits on exact counts (each algorithm's rivals rejected).
