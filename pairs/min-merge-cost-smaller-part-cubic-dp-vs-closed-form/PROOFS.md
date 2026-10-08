# Proofs: merging adjacent piles at the cost of the smaller part, cubic DP vs the closed form S − max s

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code).
The closed form (Proposition) and the endpoint law (Corollary) are proved in the README; section 4 indexes them and
proves what the code adds. Sections 1 and 2 prove the exact operation counts for every n, from the code in this
folder. Sections 3 to 8 prove correctness, the time and space bounds, the size of the numbers, the facts used by the
V1 oracle and the factual caveats. Each proof is followed by the deterministic scripts that check it and the ranges
they check. A check covers only its range; the proofs cover every n.

The statement in the `background` field of `entry.json` (the content of Qian and Wang's Lemma 1) is cited, not proved
here, and no claim depends on it.

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

**Three facts about the cubic DP.**
- (i) *Prefix sums.* `prefix[0]` is the plain 0, and `prefix[t]` for t ≥ 1 is a `CountingInt`: `0 + s₀` goes through
  `__radd__`, every later sum adds two `CountingInt` values. Building them makes n + 1 counted additions.
- (ii) *One candidate split.* For i < k ≤ j, `prefix[k] - prefix[i]` (left operand a `CountingInt`, since k ≥ 1) and
  `prefix[j + 1] - prefix[k]` are 2 counted subtractions; `merge_cost` evaluates `left <= right` once (1 counted
  comparison) and returns one of its arguments, a `CountingInt`; the two additions `+ c[i][k - 1] + c[k][j]` have a
  `CountingInt` left operand and count 2 (also when `c[·][·]` is the plain 0 of an empty part). So every candidate
  costs exactly 1 comparison and 4 additions or subtractions, and its value `cand` is a `CountingInt`.
- (iii) *Running minimum.* For the first candidate of a row, `best is None` is true and `or` short-circuits; every
  later candidate evaluates `cand < best` once. A row with t candidates makes t − 1 such comparisons.

The outcome of a comparison only selects which value is stored, never the loop structure, so no count below depends
on the values. No counted operation happens inside a CPython built-in: the cubic DP calls only `len`, `range` and
`list.append`, the closed form only slicing, and every counted comparison is one of the explicit `<=`, `<` and `>` in
the code.

**Machine model.** Elementary operations cost O(1): indexing, allocating a list or tuple of length t in Θ(t + 1)
(this includes the slice `sizes[1:]`, a new tuple of n references in CPython), `list.append` (amortised), a Python
call, loop control, and every addition, subtraction and comparison of two size-derived values (the comparison model
of the entry; section 6 bounds the size of these numbers).

## 1. Cubic DP: exact counts

**Statement.** On every input and for every n ≥ 0, `merge_min_smaller_cubic` evaluates exactly n(n+1)(n+2)/6
candidate splits, makes exactly n(n+1)(2n+1)/6 comparisons, of which n(n+1)(n+2)/6 are inside `merge_cost` and
(n+1)n(n−1)/6 between candidate values, and exactly (n + 1) + 2n(n+1)(n+2)/3 additions and subtractions.

**Proof.** A row of length L tries the L splits k = i+1..j. By (ii) and (iii) it makes L merge-cost comparisons,
L − 1 candidate comparisons and 4L additions or subtractions. Summing over the n − L + 1 rows of each length:
Σ_{L=1..n} (n + 1 − L)L = (n+1)·n(n+1)/2 − n(n+1)(2n+1)/6 = n(n+1)(n+2)/6 candidates;
Σ_{L=1..n} (n + 1 − L)(L − 1) = n(n+1)(n+2)/6 − n(n+1)/2 = (n+1)n(n−1)/6 candidate comparisons; in all
n(n+1)(n+2)/6 + (n+1)n(n−1)/6 = n(n+1)(2n+1)/6 comparisons; and with (i), (n + 1) + 4·n(n+1)(n+2)/6 additions and
subtractions. For n = 0 there is no row: 0 comparisons and the single prefix addition, as the formulas give. ∎

**Check.** `tests/test_entry_merge_smaller.py`: `test_comparison_and_arithmetic_counts` (n = 0..40, for all 11
integer families at every n, asserted equal across the families); `test_candidate_only_counts` (`merge_cost` called
n(n+1)(n+2)/6 times, the rest of the comparisons (n+1)n(n−1)/6, n = 0..30, one seeded family per n). The validator's
V2 run counts the comparisons at n = 16, 32, 64, 128.

## 2. Closed form: exact counts

**Statement.** On every input and for every n ≥ 0, `merge_min_smaller_closed_form` makes exactly n comparisons and
n + 1 additions and subtractions (n additions and one subtraction).

**Proof.** `total = sizes[0]` and `largest = sizes[0]` count nothing. The loop runs over the n sizes s₁, …, sₙ; each
iteration evaluates `total + s` (two `CountingInt` operands: 1 addition) and `s > largest` (1 comparison), and the
assignment `largest = s` counts nothing. The return computes `total - largest` (1 subtraction). For n = 0 the loop is
empty: 0 comparisons and 1 subtraction. ∎

**Check.** `tests/test_entry_merge_smaller.py`, `test_comparison_and_arithmetic_counts` (n = 0..199, 1000 and 4096,
all 11 integer families at every n). The validator's V2 run counts the comparisons at n = 16, 64, 256, 1024, 4096.

## 3. Correctness of the cubic DP (any sizes)

**Merge orders and merge trees.** A merge order (a sequence of n merges that ends in one pile) defines a merge tree:
the full binary tree whose leaves are s₀, …, sₙ in this order and whose internal nodes are the merges. Every merge
tree arises from some merge order (perform its merges bottom-up, children before parents), and the cost of a merge
depends only on the sizes of the two merged blocks, which are the leaf sums of the node's two subtrees. So the total
cost depends only on the merge tree, and the minimum over merge orders is the minimum over merge trees.

**Lemma 3.1.** For a row i..j with j > i, the merge trees of the row are in bijection with the triples
(k, T_L, T_R) with i < k ≤ j, T_L a merge tree of i..k−1 and T_R a merge tree of k..j, and the cost of the tree is
min(S(i, k−1), S(k, j)) + cost(T_L) + cost(T_R).

*Proof.* The leaves of the root's left subtree form a non-empty prefix i..k−1 of the row and those of its right
subtree the non-empty rest k..j, so i < k ≤ j; conversely any such k and any two merge trees of the blocks form a
merge tree. The root merge joins blocks of sizes S(i, k−1) and S(k, j). ∎

**Theorem 3.2.** For any sizes (any signs), the cubic DP returns c(0, n), the minimum cost over all merge trees of
the row 0..n, and for every row c[i][j] is the minimum over the merge trees of i..j.

*Proof.* `prefix[t] = S(0, t−1)`, so `prefix[k] - prefix[i] = S(i, k−1)` and `prefix[j + 1] - prefix[k] = S(k, j)`, and
`merge_cost(left, right)` returns `left` if `left <= right` and `right` otherwise, which is min(left, right). Rows are
filled by increasing length, so c[i][k−1] and c[k][j] are final when row i..j is filled. Induction on j − i with
Lemma 3.1: c[i][i] = 0 is the cost of the single-pile tree, and the best tree with last split k costs
min(S(i, k−1), S(k, j)) + c[i][k−1] + c[k][j], since the two subtrees range independently; the code takes the minimum
over all k. The argument uses no property of min(L, R), so the same recurrence, with any merge cost f in place of
min(L, R) in `merge_cost`, is correct for every merge cost. ∎

**Check.** `tests/test_entry_merge_smaller.py`, `test_exhaustive_equality_closed_form_and_endpoint_law`: the cubic DP
equals the minimum over all explicitly enumerated merge trees (`harness.brute_force`) on every size vector with n ≤ 4
and sizes 0..4, n = 5 and sizes 0..3, n = 6 and sizes 0..2 (10 188 vectors; every contiguous sub-row is itself in the
set); `test_negative_sizes_counterexample` (negative sizes);
`theorems/endpoint-law-split-dependent-weights/verify.py`, part S (merge trees, enumerated as nested pairs and costed
from leaf sums, give the same optimum as the recurrence, for max(L, R), |L − R| and min(L, R), n ≤ 5, signed sizes
included). The same recurrence with the merge costs max(L, R) and
|L − R| under max is checked against the tree enumeration by the tests of the two sibling entries.

## 4. The closed form, its code, and the endpoint law (sizes ≥ 0)

- *Proposition* (README, section "The closed form", with proof): for s₀, …, sₙ ≥ 0 and every row i..j,
  c(i, j) = S(i, j) − M(i, j) with M(i, j) = max(sᵢ, …, sⱼ); the lower bound by induction over the last merge, the
  upper bound by a caterpillar that starts at a largest pile and adds the neighbouring piles in any order that keeps
  the block contiguous.
- *The code.* Loop invariant of `merge_min_smaller_closed_form`: after the iterations for s₁, …, s_t, `total` is
  S(0, t) and `largest` is max(s₀, …, s_t) (the update `largest = s` happens exactly when s > largest). After the
  loop, t = n, and the return value is S(0, n) − max sₗ = c(0, n) by the Proposition.
- *Corollary* (README, section "The endpoint law", with proof): for sizes ≥ 0 every row i..j with j > i has a
  minimising split k ∈ {i+1, j}.
- *The endpoint DP is exact.* The endpoint DP runs the recurrence of section 3 with the splits restricted to `(j,)`
  for rows of length 1 (the only split) and to `(i + 1, j)` otherwise. By the Corollary and induction on the length,
  every row's value is the minimum over a set of splits that contains a minimising one, so it equals c(i, j). It
  evaluates n + 2·n(n−1)/2 = n² candidates (n rows of length 1, n(n−1)/2 longer rows), so it takes Θ(n²) time in the
  model above.

**Check.** `tests/test_entry_merge_smaller.py`: `test_exhaustive_equality_closed_form_and_endpoint_law` (on every row
of the 10 188 vectors the DP value is S − max, and some minimising split is an end);
`test_every_caterpillar_from_a_largest_pile_attains_the_closed_form` (every caterpillar whose first merge involves a
largest pile costs S − max s, every vector with n ≤ 5); `test_endpoint_dp_is_exact` (an endpoint DP written in the
test equals the cubic DP on the 10 188 vectors); `theorems/endpoint-law-split-dependent-weights/verify.py`, part C
(the endpoint law for min(L, R) under min on 8 001 vectors). The validator's V1 battery: `check()` certifies the
closed form's output on every instance (section 7).

## 5. Time and space

**Statement.** On every input, the cubic DP takes Θ(n³) time and Θ(n²) space. The closed form takes Θ(n) time and
O(n) space besides the input: the slice `sizes[1:]` (n references), and otherwise O(1) words.

**Proof.** Cubic DP: besides the candidates (section 1, O(1) work each), the code builds the prefix list of n + 2
entries and the table `c` of n + 1 lists of length n + 1, and visits the n(n+1)/2 rows with O(1) work each outside
the candidate loop: Θ(n(n+1)(n+2)/6 + (n+1)²) = Θ(n³) time for n ≥ 1, and the (n + 1)² table plus O(n) space. Closed
form: the slice costs Θ(n + 1), and the loop runs n times with O(1) work each, so Θ(n) time for n ≥ 1; its state is
the slice and the three names `total`, `largest` and `s`. No lower bound for the problem is claimed.

**Check.** `tests/test_entry_merge_smaller.py`: `test_time_and_space` (at the return of the cubic DP, profiler hook:
`c` has n + 1 rows of length n + 1 and `prefix` n + 2 entries, n = 0..40; the candidate counts are those of
`test_candidate_only_counts`); `test_closed_form_state` (at the return of the closed form its local variables are
exactly `sizes`, `total`, `largest` and, for n ≥ 1, `s`, n = 0..49).

## 6. The size of the numbers

**Statement.** For sizes ≥ 0 with total S = S(0, n), every value the cubic DP computes lies in [0, n·S]: prefix sums
and block sizes in [0, S], merge costs in [0, S], candidates and table entries c[i][j] in [0, (j − i)·S(i, j)]. The
closed form's values lie in [0, S].

**Proof.** Block sizes are sums of non-negative sizes inside the row. A merge cost min(L, R) lies between 0 and
L + R ≤ S(i, j). A merge tree of the row i..j has j − i merges, each costing at most S(i, j), so every candidate and
c(i, j) lie in [0, (j − i)·S(i, j)]. The closed form's `total` and `largest` lie in [0, S], and so does S − max s.

**Check.** `tests/test_entry_merge_smaller.py`, `test_size_of_numbers`: every table entry of the cubic DP lies in
[0, (j − i)·S(i, j)] on 120 seeded instances from the 12 V1 families, n = 0..40.

## 7. Facts used by the V1 oracle (`harness.py`)

- *Enumeration (n ≤ 9).* `merge_trees(m)` builds the merge trees of m piles by the recursion of Lemma 3.1 (every last
  split k, every pair of subtrees), so it lists each merge tree exactly once, Catalan(m − 1) of them. `tree_cost`
  sums `cost` over the merges with block sizes summed directly from the sizes. So `brute_force` is the exact
  minimum.
- *Certificate (10 ≤ n ≤ 150), upper bound.* `certificate` starts at a pile of largest size and records the merges
  (lo − 1, lo, hi), which join pile lo − 1 to the block lo..hi, until lo = 0, and then (lo, hi + 1, hi + 1), which join
  the block lo..hi to pile hi + 1, until hi = m − 1. This is a merge tree; its cost, summed from direct block sums, is
  at least the optimum.
- *Certificate, lower bound.* B(a, b) = S(a, b) − max(s_a, …, s_b) is computed from direct sums and maxima. If
  B(a, a) = 0 for every a and B(a, b) ≤ min(S(a, k−1), S(k, b)) + B(a, k−1) + B(k, b) for every row a < b and every
  split a < k ≤ b (the code checks all of these), then every merge tree of the row a..b costs at least B(a, b), by
  induction over the last merge with Lemma 3.1. This holds whatever the sizes, so a valid certificate does not assume
  the closed form.
- *Verdict.* An output below a valid lower bound or above the upper bound is wrong (`False`); if the bounds meet, the
  optimum is that value and the output must equal it; otherwise, and above n = 150, `check` returns `None`.

**Check.** `tests/test_entry_merge_smaller.py`: `test_certificate_matches_enumeration` (valid, both bounds equal to
the enumeration, 60 seeded instances with n = 1..8); `test_check_accepts_and_rejects` (the true value is accepted and
the value ± 1 rejected, n = 0..10, 12, 16, 25, 4 seeded instances each); `test_check_certifies_the_v1_battery`
(`check` returns True for both outputs on all 192 instances of the validator's V1 battery, with its seeds).

## 8. The caveats, the limits and the rotation conditions

- *Negative sizes.* For sizes (−1, 0, 0) the two merge trees cost −2 and −1 (the README lists every merge); the
  minimum is −2, and the formula gives −1.
- *Max direction.* For sizes (1, 1, 1, 1) the tree ((s₀s₁)(s₂s₃)) costs 4 under the sum of min(L, R) and each of the
  four caterpillars 3, so maximising this total is a different problem, where neither the closed form nor the endpoint
  rule applies.
- *The rotation conditions of the note fail on some non-negative sizes.* For w(i, k, j) = min(S(i, k−1), S(k, j)) and
  four piles, the README computes (Δ_R, Δ_L) = (0, 1) for (0, 1, 1, 2) and (−1, 2) for (1, 1, 2, 4), so RS3 for −w
  fails, and (1, 0) for (2, 1, 0, 1), so RS3w for −w fails. So the note's min forms do not give the endpoint law for all
  non-negative sizes; the entry derives it from the closed form (section 4). Nothing is claimed about other routes.
- *Split dependence.* For sizes (1, 1, 0) the row 0..2 has the split costs min(1, 1) = 1 at k = 1 and min(2, 0) = 0 at
  k = 2, so this merge cost is not a function of the row alone.
- *No lower bound* is claimed.

**Check.** `tests/test_entry_merge_smaller.py`: `test_negative_sizes_counterexample`, `test_max_direction_control`,
`test_hand_computed_tree_costs`, `test_mirrored_rotation_conditions_fail` (the three examples, and the endpoint law on
their rows), `test_split_dependence`; `theorems/endpoint-law-split-dependent-weights/verify.py`, part C (the same
rotation-condition examples).

## 9. The pair (T3)

Under the precondition s ≥ 0 both implementations return c(0, n) (sections 3 and 4). The cubic DP takes Θ(n³) time and
the closed form Θ(n) (section 5); the exact comparison counts are n(n+1)(2n+1)/6 and n on every input (sections 1 and
2).

## Claim map

| Claim (location) | Proof |
|---|---|
| problem statement: the minimum over merge orders equals the minimum over merge trees and c(0, n) (`problem_statement`, README "Problem") | section 3 |
| cubic DP correct for any sizes and any merge cost (`algorithms[0].correctness`, `notes`, README) | section 3 |
| closed form c(i, j) = S(i, j) − M(i, j) for sizes ≥ 0; the closed-form code (`algorithms[1].correctness`, `relationship`, README Proposition) | README Proposition; section 4 |
| endpoint law and exact endpoint DP, Θ(n²) (`relationship`, README Corollary) | README Corollary; section 4 |
| exact comparison counts, candidate-only count (`time_complexity`, `relationship`, README table) | sections 1 and 2 |
| additions and subtractions (`caveats`) | sections 1 and 2 |
| Θ(n³) time, Θ(n²) space; Θ(n) time, O(n) space besides the input (`time_complexity`, `space_complexity`) | section 5 |
| the counts depend on n only; no counted comparison in a built-in (`verification.method`, README V2) | counting convention |
| the V1 oracle and its certificate (`verification.method`, README V1, harness docstring) | section 7 |
| negative sizes, max direction, rotation conditions, split dependence, no lower bound (`caveats`, `notes`, README) | section 8 |
| T3 | section 9 |
