# Proofs: worst-case total imbalance of merging adjacent piles, cubic DP vs endpoint DP

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
together with the proofs it cites from the theorem note
[endpoint-law-split-dependent-weights](../../theorems/endpoint-law-split-dependent-weights/) (Theorem 1, Lemma 11,
Corollary 12 and the correspondence between merge trees and trees in its Setting). Sections 1 and 2 prove the exact
operation counts for every n, from the code in this folder. Sections 3 to 8 prove correctness, the time and space
bounds, the size of the numbers, the facts used by the V1 oracle and the factual caveats. Each proof is followed by
the deterministic scripts that check it and the ranges they check. A check covers only its range; the proofs cover
every n.

The statements in the `background` field of `entry.json` (the content of Qian and Wang's Lemma 1, and the code of a
2020 developer-community article for the merge cost L + R) are cited, not proved here, and no claim depends on them.

## Counting convention and machine model

`harness.py`, class `CountingInt`: `__add__` (also bound as `__radd__`), `__sub__` and `__rsub__` add 1 to the
module counter `_arithmetic` and return a new `CountingInt`; `__lt__`, `__le__`, `__gt__` and `__ge__` call `_cmp`,
which adds 1 to `_comparisons`. `__eq__`, `__hash__` and the constructor count nothing. An operation with at least
one `CountingInt` operand counts exactly 1 (with a plain left operand, `int.__add__` returns `NotImplemented` and
Python calls the reflected method); an operation on two plain ints counts nothing. `generate_scaling(n, rng)` draws
one of the 11 integer families (`SCALING_FAMILIES`), builds the instance with `instance_of`, replaces every size by a
`CountingInt` (`wrap_counting`) and resets both counters; `reported_cost(output)` returns `_comparisons`, and
`counters()` returns (`_comparisons`, `_arithmetic`).

**Every input** below means every tuple of `CountingInt` sizes, whatever their values and signs. Rows are the
intervals i..j of pile indices, 0 ≤ i < j ≤ n, of length L = j − i; there are n − L + 1 rows of length L.

**Three facts used in every section.**
- (i) *Prefix sums.* `prefix[0]` is the plain 0, and `prefix[t]` for t ≥ 1 is a `CountingInt`: `0 + s₀` goes through
  `__radd__`, every later sum adds two `CountingInt` values. Building them makes n + 1 counted additions.
- (ii) *One candidate split.* For i < k ≤ j, `prefix[k] - prefix[i]` (left operand a `CountingInt`, since k ≥ 1) and
  `prefix[j + 1] - prefix[k]` are 2 counted subtractions; `merge_cost` evaluates `left >= right` once (1 counted
  comparison) and then exactly one of `left - right` and `right - left` (1 counted subtraction, a `CountingInt`); the
  two additions `+ c[i][k - 1] + c[k][j]` have a `CountingInt` left operand and count 2 (also when `c[·][·]` is the
  plain 0 of an empty part). So every candidate costs exactly 1 comparison and 5 additions or subtractions, and its
  value `cand` is a `CountingInt`.
- (iii) *Running maximum.* For the first candidate of a row, `best is None` is true and `or` short-circuits; every
  later candidate evaluates `cand > best` once. A row with t candidates makes t − 1 such comparisons.

The outcome of a comparison only selects which value is stored, never the loop structure, so no count below depends
on the values. No counted operation happens inside a CPython built-in: the code calls only `len`, `range` and
`list.append`, and every counted comparison is one of the explicit `>=` and `>` above.

**Machine model.** Elementary operations cost O(1): indexing, allocating a list of length t in Θ(t + 1),
`list.append` (amortised), a Python call, loop control, and every addition, subtraction and comparison of two
size-derived values (the comparison model of the entry; section 6 bounds the size of these numbers).

## 1. Cubic DP: exact counts

**Statement.** On every input and for every n ≥ 0, `merge_max_imbalance_cubic` evaluates exactly n(n+1)(n+2)/6
candidate splits, makes exactly n(n+1)(2n+1)/6 comparisons, of which n(n+1)(n+2)/6 are inside `merge_cost` and
(n+1)n(n−1)/6 between candidate values, and exactly (n + 1) + 5n(n+1)(n+2)/6 additions and subtractions.

**Proof.** A row of length L tries the L splits k = i+1..j. By (ii) and (iii) it makes L merge-cost comparisons,
L − 1 candidate comparisons and 5L additions or subtractions. Summing over the n − L + 1 rows of each length:
Σ_{L=1..n} (n + 1 − L)L = (n+1)·n(n+1)/2 − n(n+1)(2n+1)/6 = n(n+1)(n+2)/6 candidates;
Σ_{L=1..n} (n + 1 − L)(L − 1) = n(n+1)(n+2)/6 − n(n+1)/2 = (n+1)n(n−1)/6 candidate comparisons; in all
n(n+1)(n+2)/6 + (n+1)n(n−1)/6 = n(n+1)(2n+1)/6 comparisons; and with (i), (n + 1) + 5·n(n+1)(n+2)/6 additions and
subtractions. For n = 0 there is no row: 0 comparisons and the single prefix addition, as the formulas give. ∎

**Check.** `tests/test_entry_merge_imbalance.py`: `test_comparison_and_arithmetic_counts` (comparisons and additions,
n = 0..40, for all 11 integer families at every n, asserted equal across the families); `test_candidate_only_counts`
(`merge_cost` called n(n+1)(n+2)/6 times, the rest of the comparisons (n+1)n(n−1)/6, n = 0..30, one seeded family per
n). The validator's V2 run counts the comparisons at n = 16, 32, 64, 128.

## 2. Endpoint DP: exact counts

**Statement.** On every input and for every n ≥ 0, `merge_max_imbalance_endpoint` evaluates exactly n² candidate splits,
makes exactly n(3n−1)/2 comparisons, of which n² are inside `merge_cost` and n(n−1)/2 between candidate values, and
exactly (n + 1) + 5n² additions and subtractions.

**Proof.** A row of length 1 runs over the tuple `(j,)`: one candidate, 1 merge-cost comparison, no candidate
comparison. A row of length L ≥ 2 runs over `(i + 1, j)`, two different splits: 2 merge-cost comparisons and 1
candidate comparison. There are n rows of length 1 and Σ_{L=2..n} (n + 1 − L) = n(n−1)/2 rows of length ≥ 2, so
n + 2·n(n−1)/2 = n² candidates and merge-cost comparisons, n(n−1)/2 candidate comparisons, n + 3n(n−1)/2 = n(3n−1)/2
comparisons in all, and with (i) and (ii) (n + 1) + 5n² additions and subtractions. ∎

**Check.** `tests/test_entry_merge_imbalance.py`: `test_comparison_and_arithmetic_counts` (n = 0..80, all 11 integer
families at every n); `test_candidate_only_counts` (n² merge-cost calls and n(n−1)/2 candidate comparisons,
n = 0..30). The validator's V2 run counts the comparisons at n = 32, 64, 128, 256, 512.

## 3. Correctness of the cubic DP (any sizes)

**Merge orders and merge trees.** A merge order (a sequence of n merges that ends in one pile) defines a merge tree:
the full binary tree whose leaves are s₀, …, sₙ in this order and whose internal nodes are the merges. Every merge
tree arises from some merge order (perform its merges bottom-up, children before parents), and the cost of a merge
depends only on the sizes of the two merged blocks, which are the leaf sums of the node's two subtrees. So the total
cost depends only on the merge tree, and the maximum over merge orders is the maximum over merge trees.

**Lemma 3.1.** For a row i..j with j > i, the merge trees of the row are in bijection with the triples
(k, T_L, T_R) with i < k ≤ j, T_L a merge tree of i..k−1 and T_R a merge tree of k..j, and the cost of the tree is
|S(i, k−1) − S(k, j)| + cost(T_L) + cost(T_R).

*Proof.* The leaves of the root's left subtree form a non-empty prefix i..k−1 of the row and those of its right
subtree the non-empty rest k..j, so i < k ≤ j; conversely any such k and any two merge trees of the blocks form a
merge tree. The root merge joins blocks of sizes S(i, k−1) and S(k, j). (This is the correspondence of the note's
Setting.) ∎

**Theorem 3.2.** For any sizes (any signs), the cubic DP returns c(0, n), the maximum cost over all merge trees of
the row 0..n, and for every row c[i][j] is the maximum over the merge trees of i..j.

*Proof.* `prefix[t] = S(0, t−1)`, so `prefix[k] - prefix[i] = S(i, k−1)` and `prefix[j + 1] - prefix[k] = S(k, j)`, and
`merge_cost(left, right)` returns `left - right` if `left >= right` and `right - left` otherwise, which is
|left − right|. Rows are
filled by increasing length, so c[i][k−1] and c[k][j] are final when row i..j is filled. Induction on j − i with
Lemma 3.1: c[i][i] = 0 is the cost of the single-pile tree, and the best tree with last split k costs
|S(i, k−1) − S(k, j)| + c[i][k−1] + c[k][j], since the two subtrees range independently; the code takes the maximum
over all k. ∎

**Check.** `tests/test_entry_merge_imbalance.py`, `test_exhaustive_equality`: the cubic DP equals the maximum over all
explicitly enumerated merge trees (`harness.brute_force`) on every size vector with n ≤ 4 and sizes 0..4, n = 5 and
sizes 0..3, n = 6 and sizes 0..2 (10 188 vectors; every contiguous sub-row of such a vector is itself in the set, so
every row is covered); `test_negative_sizes_counterexample` (negative sizes);
`theorems/endpoint-law-split-dependent-weights/verify.py`, part S (merge trees, enumerated as nested pairs and costed
from leaf sums, give the same optimum as the recurrence, for max(L, R), |L − R| and min(L, R), n ≤ 5, signed sizes
included). The validator's V1 battery compares
both implementations with `check()`.

## 4. Correctness of the endpoint DP (sizes ≥ 0)

**Claim.** For s₀, …, sₙ ≥ 0 the endpoint DP returns c(0, n), and its table equals the cubic DP's table on every row.

*Proof.* The README, section "Correctness of the endpoint DP", proves the Corollary: for sizes ≥ 0 every row i..j
with j > i has (a) a maximising split k ∈ {i+1, j}, (b) the endpoint recurrence and (c) an optimal caterpillar. Its
proof applies Theorem 1 of the note with Lemma 11 of the note (the weights w(i, k, j) = |S(i, k−1) − S(k, j)|
satisfy two-sided RS3w, hence RS3w, for sizes ≥ 0); both are proved in the note's README. The stronger condition RS3
fails for this weight (section 8), so the note's Corollary 2 is not used. The endpoint DP runs the recurrence of
section 3 with the splits restricted to `(j,)` for rows of length 1 (the only split) and to `(i + 1, j)` otherwise. By
induction on the length, every row's table entry is the maximum over a set of splits that contains a maximising one,
so it equals c(i, j). ∎

**Check.** `tests/test_entry_merge_imbalance.py`, `test_exhaustive_equality` (10 188 vectors, as in section 3);
`theorems/endpoint-law-split-dependent-weights/verify.py`, part E (Lemma 11 on the grid 0..12 and 5 000 rationals;
two-sided RS3w and the endpoint law on the merge tables of the same 10 188 vectors, optimal caterpillars by
enumeration for n ≤ 5). The validator's V1 battery: `check()` certifies the output on every instance (section 7).

## 5. Time and space

**Statement.** On every input, the cubic DP takes Θ(n³) time and the endpoint DP Θ(n²) time; both use Θ(n²) space.

**Proof.** Besides the candidates (sections 1 and 2, O(1) work each), the code builds the prefix list of n + 2
entries and the table `c` of n + 1 lists of length n + 1, and visits the n(n+1)/2 rows with O(1) work each outside
the candidate loop. So the cubic DP does Θ(n(n+1)(n+2)/6 + (n+1)²) = Θ(n³) work and the endpoint DP
Θ(n² + (n+1)²) = Θ(n²), for n ≥ 1; the space is the (n + 1)² table plus O(n). Θ(n²) is the cost of the endpoint DP,
not a lower bound for the problem; no lower bound is claimed.

**Check.** `tests/test_entry_merge_imbalance.py`, `test_time_and_space`: at the return of each implementation (profiler
hook), `c` has n + 1 rows of length n + 1 and `prefix` has n + 2 entries, n = 0..40 (cubic) and 0..80 (endpoint); the
candidate counts are those of `test_candidate_only_counts`.

## 6. The size of the numbers

**Statement.** For sizes ≥ 0 with total S = S(0, n), every value the two DPs compute lies in [0, n·S]: prefix sums
and block sizes in [0, S], merge costs in [0, S], candidates and table entries c[i][j] in [0, (j − i)·S(i, j)].

**Proof.** Block sizes are sums of non-negative sizes inside the row. A merge cost |L − R| lies between 0 and
L + R ≤ S(i, j). A merge tree of the row i..j has j − i merges, each costing at most S(i, j), so every candidate and
c(i, j) lie in [0, (j − i)·S(i, j)]. For integer sizes the numbers therefore need only O(log n) more bits than the
largest size; for rational sizes every value is an integer combination of the sizes with coefficients of absolute value
at most max(n, 1), so, over the common denominator of the sizes, its bit length is polynomial in the input length. In
both cases unit-cost arithmetic is a polynomial-factor simplification of bit complexity. (Every value is a block sum, in
which each size has the coefficient 0 or 1, or a sum of at most n merge costs, each a block sum or a difference of two
disjoint block sums, in which each size has a coefficient in [−n, n].)

**Check.** `tests/test_entry_merge_imbalance.py`, `test_size_of_numbers`: every table entry of both DPs lies in
[0, (j − i)·S(i, j)] on 120 seeded instances from the 12 V1 families, n = 0..40.

## 7. Facts used by the V1 oracle (`harness.py`)

- *Enumeration (n ≤ 9).* `merge_trees(m)` builds the merge trees of m piles by the recursion of Lemma 3.1 (every last
  split k, every pair of subtrees), so it lists each merge tree exactly once, Catalan(m − 1) of them. `tree_cost`
  sums `cost` over the merges with block sizes summed directly from the sizes. So `brute_force` is the exact
  maximum.
- *Certificate (10 ≤ n ≤ 150), lower bound.* The tree built top-down in `certificate` is a merge tree: each step
  records the merge (a, a+1, b), joining pile a to the block a+1..b, or (a, b, b), joining the block a..b−1 to pile b,
  and recurses on the block. Its cost, summed from direct block sums, is the cost of a merge tree, so it is at most the
  optimum.
- *Certificate, upper bound.* U(a, a) = 0 by construction. If U(a, b) ≥ |S(a, k−1) − S(k, b)| + U(a, k−1) + U(k, b)
  holds for every row a < b and every split a < k ≤ b (the loop checks every one), then every merge tree of the row
  a..b costs at most U(a, b), by induction over the last merge with Lemma 3.1: its cost is
  |S(a, k−1) − S(k, b)| + cost(T_L) + cost(T_R) ≤ |S(a, k−1) − S(k, b)| + U(a, k−1) + U(k, b) ≤ U(a, b). This
  holds however U was computed, so a valid certificate does not assume the endpoint law.
- *Verdict.* An output below the lower bound or above a valid upper bound is wrong (`False`); if the bounds meet,
  the optimum is that value and the output must equal it; otherwise, and above n = 150, `check` returns `None`.

**Check.** `tests/test_entry_merge_imbalance.py`: `test_certificate_matches_enumeration` (valid, both bounds equal to
the enumeration, 60 seeded instances with n = 1..8); `test_check_accepts_and_rejects` (the true value is accepted and
the value ± 1 rejected, n = 0..10, 12, 16, 25, 4 seeded instances each); `test_check_certifies_the_v1_battery`
(`check` returns True for both outputs on all 192 instances of the validator's V1 battery, with its seeds).

## 8. The caveats and the README's limits

- *Negative sizes.* For sizes (0, −1, 1, 0) the five merge trees cost 4, 3, 2, 2, 3 (the README lists every merge);
  the maximum 4 is attained only by the middle split, and the endpoint DP returns 3.
- *Min direction.* For sizes (0, 1, 1, 0) the five merge trees cost 2, 3, 4, 4, 3 under the sum of |L − R|; the
  minimum 2 needs the middle split, and the best caterpillar costs 3.
- *RS3 fails.* For sizes (1, 0, 1, 2) the single index tuple (0, 1, 2, 3, 3) has Δ_R = 2 and Δ_L = −3 (computed by
  hand in the README), so Δ_R + Δ_L < 0; the endpoint DP is still exact there (section 4).
- *Split dependence.* For sizes (1, 1, 0) the row 0..2 has the split costs |1 − 1| = 0 at k = 1 and |2 − 0| = 2 at
  k = 2, so this merge cost is not a function of the row alone.
- *No lower bound* is claimed; Θ(n²) is the cost of the endpoint DP (section 5).

**Check.** `tests/test_entry_merge_imbalance.py`: `test_negative_sizes_counterexample`, `test_min_direction_control`,
`test_hand_computed_tree_costs` (every merge of the five trees, both examples), `test_rs3_fails_but_the_law_holds`,
`test_split_dependence`; `theorems/endpoint-law-split-dependent-weights/verify.py`, part C (the RS3 failure and the
negative-size example).

## 9. The pair (T3)

Under the precondition s ≥ 0 both implementations return c(0, n) (sections 3 and 4). The cubic DP takes Θ(n³) time and
the endpoint DP Θ(n²) (section 5); the exact comparison counts are n(n+1)(2n+1)/6 and n(3n−1)/2 on every input
(sections 1 and 2).

## Claim map

| Claim (location) | Proof |
|---|---|
| problem statement: the maximum over merge orders equals the maximum over merge trees and c(0, n) (`problem_statement`, README "Problem") | section 3 |
| cubic DP correct for any sizes (`algorithms[0].correctness`, README) | section 3 |
| endpoint DP exact for sizes ≥ 0; an optimal caterpillar (`algorithms[1].correctness`, `relationship`, README Corollary) | section 4; note Theorem 1, Lemma 11, Corollary 12 |
| exact comparison counts, merge-cost and candidate-only counts (`time_complexity`, `relationship`, README table) | sections 1 and 2 |
| additions and subtractions (`caveats`) | sections 1 and 2 |
| Θ(n³), Θ(n²) time; Θ(n²) space (`time_complexity`, `space_complexity`) | section 5 |
| the counts depend on n only; no counted comparison in a built-in (`verification.method`, README V2) | counting convention |
| the V1 oracle and its certificate (`verification.method`, README V1, harness docstring) | section 7 |
| negative sizes, min direction, RS3 fails, split dependence, no lower bound (`caveats`, `notes`, README) | section 8 |
| T3 | section 9 |
