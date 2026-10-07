# Proofs: 0/1 knapsack, subset enumeration vs meet in the middle vs capacity DP

This file proves every claim that this entry makes about its problem and its three algorithms (in `entry.json`,
`README.md` and the docstrings of the code): correctness, the exact iteration counts, the time and space bounds,
the pseudo-polynomial behaviour of the DP and the T8 improvement. The statements in the entry's `background` field
(NP-hardness, Ibarra and Kim's approximation algorithms, and the two machine-model assumptions A1, A2 below) are
cited and are not proved here; the T6 tag rests on the first of them. Each section ends with the deterministic
checks of its computable facts; a check covers only the inputs it states.

**Domain.** As in `problem_statement`: n ≥ 0 items with positive integer weights w_1..w_n and positive integer
values v_1..v_n, and an integer capacity W ≥ 0 (sections 1–3 do not use the positivity of the values; §4 does).
For W < 0 no subset fits, not even the empty one, and the maximum is undefined; the code assumes W ≥ 0.
OPT is the largest v(S) = Σ_{i∈S} v_i over the subsets S with w(S) = Σ_{i∈S} w_i ≤ W; the empty set is feasible, so
OPT exists.

**Cost model and machine-model assumptions (not proved here).** Additions and comparisons of the integers
involved, list and tuple indexing and `append` (amortised) cost O(1); building a list of t elements costs Θ(t + 1).
Two assumptions about library code are stated in the entry's `background` with their sources: (A1) the built-in
`sorted` on m items runs in O(m log m) time (basis: the current CPython list sort merges in the powersort order of
`Objects/listsort.txt`, and Munro and Wild 2018, Theorem 6, bound the comparisons of powersort with a plain merge;
CPython's galloping merges are not covered, so A1 is an assumption; Auger, Jugé, Nicaud and Pivoteau 2018 prove the
bound for the earlier TimSort merge policy); (A2) `bisect_right(a, x)` performs the halving loop `while lo < hi: mid = (lo + hi) // 2;
if x < a[mid]: hi = mid; else: lo = mid + 1`, one comparison per iteration, and returns the number of entries ≤ x
of the sorted list a (CPython's `Lib/bisect.py` and its C accelerator `Modules/_bisectmodule.c`). A1 enters only the
upper bound of section 2 (with any O(m log m) sorting routine the same bound follows); A2 enters both bounds of
section 2 and Theorem 2.

## 1. Subset enumeration (`implementations/brute_force.py`)

**Theorem 1.** `knapsack_brute` returns OPT. It runs its outer loop 2ⁿ times and its inner loop exactly n·2ⁿ times
on every input, so it takes Θ(n 2ⁿ) time (n ≥ 1). Beyond the input it keeps O(1) values: the mask (n bits) and the
sums w, v and best; with the input of 2n + 1 numbers the space is Θ(n).

*Proof.* The masks 0..2ⁿ − 1 are in bijection with the subsets of the items (bit i set ⇔ item i in S), and for each
mask the inner loop runs over all n items and adds w_i, v_i exactly for the items in S, so w = w(S) and v = v(S).
`best` starts at 0 = v(∅) (the empty set is feasible) and is the maximum of v(S) over the feasible S seen so far.
No loop exits early. ∎

**Check.** `tests/test_proofs_knapsack.py`, `test_enumeration`: the inner loop body runs n·2ⁿ times (trace hook) for
n = 0..12, and the result equals an independent recursive branch-and-include oracle on 300 random instances
(n = 0..12, weights 1..20, values 1..30, capacity 0..total; seed 1); the only locals besides the input are integers.

## 2. Meet in the middle (`implementations/meet_in_the_middle.py`)

Let h = ⌊n/2⌋, m = 2^(n−h) = 2^⌈n/2⌉.

**Lemma 1.** `_subset_sums(ws, vs)` on k items returns a list of 2^k pairs, exactly one (w(S), v(S)) for every
subset S of the k items, and builds it with 2^k − 1 new pairs.

*Proof.* Induction on the items processed: before the first item the list is [(0, 0)] for S = ∅; processing an item
(w, v) appends (sw + w, sv + v) for every existing pair, i.e. the subsets that contain the item, 2^t new pairs at the
t-th item. ∎

**Theorem 2.** `knapsack_mitm` returns OPT.

*Proof.* By Lemma 1, `left` lists every subset L of the first h items and `right` (sorted by weight, ties by value)
every subset R of the others, each with its weight and value. After the prefix loop, `best_value_up_to[t]` is the
largest value among `right[0..t]`. Every subset S of the items is a disjoint union L ∪ R in exactly one way, with
w(S) = w(L) + w(R) and v(S) = v(L) + v(R). If w(L) > W, no S containing L fits (weights are positive), and the loop
skips L. If w(L) ≤ W, then i = `bisect_right(right_weights, W − w(L))` − 1 is the last index whose weight is
≤ W − w(L); since `right_weights` is sorted, the entries 0..i are exactly the subsets R that fit together with L,
and i ≥ 0 because R = ∅ has weight 0. So v(L) + `best_value_up_to[i]` is the best value of a feasible S whose left
part is L, and the maximum over all L (starting from 0 = v(∅)) is OPT. ∎

**Theorem 3 (time).** Under A1 and A2, `knapsack_mitm` takes O(2^(n/2) n) time on every input, and under A2 it takes
Ω(2^(n/2) n) time whenever W ≥ w_1 + … + w_n; so its worst-case time is Θ(2^(n/2) n). (When few left subsets fit,
few binary searches run; no smaller total bound is claimed for such inputs, since it would depend on the sort.)

*Proof.* Upper bound: the two calls of `_subset_sums` cost O(2^h + m) (Lemma 1); sorting m pairs costs O(m log m)
= O(m n); the prefix loop costs O(m); the left loop runs 2^h times, and each `bisect_right` on m entries runs at most
⌊log₂ m⌋ + 1 = ⌈n/2⌉ + 1 iterations (from a range of size s the next one has size ⌊s/2⌋ or ⌈s/2⌉ − 1 ≤ ⌊s/2⌋). With
2^h ≤ 2^(n/2) and m ≤ √2 · 2^(n/2), the total is O(2^(n/2) n). Lower bound: if W ≥ w_1 + … + w_n, every left subset
fits, so `bisect_right` runs 2^h times on m entries. From a range of size s ≥ 1 the next size is at least
⌈s/2⌉ − 1 = ⌊(s − 1)/2⌋, so the number of iterations is at least g(m) with g(0) = 0, g(s) = 1 + g(⌊(s − 1)/2⌋), and by
induction g(s) = ⌊log₂(s + 1)⌋ (since ⌊(s − 1)/2⌋ + 1 = ⌊(s + 1)/2⌋). For m = 2^⌈n/2⌉ this is ⌈n/2⌉ comparisons per
search, 2^⌊n/2⌋ ⌈n/2⌉ ≥ 2^(n/2) n/(2√2) in total. ∎

**Theorem 4 (space).** On every input the lists `left` (2^h pairs), `right`, `right_weights` and
`best_value_up_to` (m entries each) are alive at the end, so the space is Θ(2^⌈n/2⌉) = Θ(2^(n/2)).

**Check.** `tests/test_proofs_knapsack.py`, `test_mitm`: the result equals the enumeration on 300 random instances
(n = 0..14, seed 2); on the family W = total weight (n = 2..20, seed 3) the comparisons made inside `bisect_right`
(counted with an instrumented number type wrapped around the weights) number between 2^⌊n/2⌋ ⌈n/2⌉ and
2^⌊n/2⌋ (⌈n/2⌉ + 1); the sizes of `left`, `right`, `right_weights` and `best_value_up_to` at return are 2^⌊n/2⌋ and
2^⌈n/2⌉; and, as a finite illustration of the cost-model assumption, the `<` evaluations on weights during the sort
number at most m⌈log₂ m⌉ on these inputs. The V2 measurement times the algorithm against 2^(n/2) n (n = 16..36); a
measurement, not part of the proof.

## 3. Capacity DP (`implementations/dp.py`)

**Theorem 5.** `knapsack_dp` returns OPT. Its inner loop runs exactly Σ_i max(0, W − w_i + 1) times, so it takes
Θ(W + n + Σ_i max(0, W − w_i + 1)) = O(n(W + 1)) time on every input, and Θ(nW) whenever every w_i ≤ W/2 (then each
item contributes at least W/2 + 1 iterations); its worst case for given n and W is Θ(nW). The list `best` has
W + 1 entries, so the space beyond the input is Θ(W) (W ≥ 1).

*Proof.* Invariant: after the first t items, `best[c]` is the largest value of a subset of items 1..t of weight
≤ c, for every 0 ≤ c ≤ W. It holds for t = 0 (all zeros: only the empty set). For item t + 1 = (w, v), the loop
visits c = W, W − 1, …, w in decreasing order and sets `best[c]` to the larger of `best[c]` and `best[c − w] + v`.
Since c − w < c and the c's decrease, `best[c − w]` has not yet been changed in this pass, so it still holds the value
for items 1..t. A subset of items 1..t + 1 of weight ≤ c either avoids item t + 1 (best value `best[c]`) or contains
it (best value `best[c − w]` + v, possible only if c ≥ w); for c < w only the first case exists and `best[c]` is
unchanged. So the invariant holds after the pass, and `best[W]` = OPT at the end. Each item contributes the
iterations c = W..w, max(0, W − w + 1) of them; the list costs Θ(W + 1) to build. ∎

**Corollary (the pseudo-polynomial behaviour, `relationship`, README).** If W ≥ max_i w_i, the iteration count is
I(W) = n(W + 1) − S with S = Σ_i w_i, and n ≤ S ≤ n·max_i w_i. Doubling W (adding one bit to it) gives
I(2W)/I(W) = 2 + (S − n)/(nW + n − S), which lies between 2 and 2 + (max_i w_i − 1)/(W + 1 − max_i w_i) and tends to
2 as W/max_i w_i grows: the running time roughly doubles when W is much larger than the item weights, although the
input grows by one bit. With all weights 1 the count is nW, polynomial in the value W and exponential in its bit
length ⌊log₂ W⌋ + 1. The DP's O(n(W + 1)) is smaller than the meet-in-the-middle worst case Ω(2^(n/2) n) when
W = o(2^(n/2)).

**Corollary (the harness, `verification.method`).** The harness draws w_i ∈ [1, 20] and sets W = ⌊S/2⌋. For
n ≥ 40, W ≥ ⌊n/2⌋ ≥ 20 ≥ max_i w_i, so I(W) = n(W + 1) − S lies between (n − 2)W + n − 1 ≥ (n − 2)⌊n/2⌋ and
n(10n + 1): the DP's work is Θ(n²) on this family, which is why its V2 fit uses n² (n = 50..400). The fit says
nothing about large W.

**Check.** `tests/test_proofs_knapsack.py`, `test_dp`: the inner body line runs Σ_i max(0, W − w_i + 1) times and the
result equals the enumeration, on 300 random instances (n = 0..12, capacities 0..total + 5; seed 4); the doubling
ratio formula is exact on 200 random instances with W ≥ max w (seed 5); on the harness family the count lies in
[(n − 2)⌊n/2⌋, n(10n + 1)] for n = 40..400 (step 20, seed 6); len(best) = W + 1.

## 4. Tags and the separation

T8 (secondary): enumeration takes Θ(n 2ⁿ) on every input (Theorem 1) and meet in the middle Θ(2^(n/2) n) in the
worst case (Theorem 3, under the machine-model assumptions A1 and A2), both exact for the same problem (Theorems 1, 2); the ratio 2^(n/2) tends to infinity, and
both stay exponential. T6 (primary) rests on the background statement that 0/1 knapsack is NP-hard, so that an
algorithm polynomial in the input size would imply P = NP; the DP is not such an algorithm (Corollary above). The
V1 check's greedy bound holds because the greedy packing is a feasible subset, so its value is ≤ OPT, and
OPT ≤ Σ v_i because the values are positive (for a negative value this fails: w = (3), v = (−1), W = 5 gives
OPT = 0 > −1).

## Claim map

| Claim (location) | Proof |
|---|---|
| enumeration correct, Θ(2ⁿ n), space | Theorem 1 |
| meet in the middle correct (`algorithms[1].correctness`) | Lemma 1, Theorem 2 |
| meet in the middle Θ(2^(n/2) n) (worst case, under the machine-model assumptions A1, A2), Θ(2^(n/2)) space | Theorems 3, 4 |
| DP correct, Θ(nW) pseudo-polynomial (worst case), Θ(W) space | Theorem 5 |
| adding one bit to W roughly doubles the DP's time when W ≫ the weights; DP beats both when W ≪ 2^(n/2) | Corollary in §3 |
| DP's V2 fit n² is specific to the harness (W = Θ(n)) | Corollary in §3 |
| T8 improvement; T6 rests on background; greedy lower bound in V1 | §4 |
