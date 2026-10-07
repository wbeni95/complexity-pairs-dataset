# Proofs: linear ordering, enumeration vs subset DP

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md`, the docstrings of the code and the harness). Sections 1 and 2 prove the exact operation counts, for
every size of their domain, from the code in this folder. Sections 3 to 10 prove the other claims: the equivalences
in the problem statement, correctness of both algorithms, time and space on every input, the running-row-sum variant
of the caveats, the statement about uncounted operations, and the facts used by the V1 oracle. Each proof is
followed by the deterministic scripts that check it and the sizes they check it on. A check covers only those sizes;
the proofs cover the whole domain.

The statements listed under `background` in `entry.json` (NP-hardness of the linear ordering problem and
NP-completeness of feedback arc set, the history of the recurrence) are cited, not proved here.

## Counting convention

`harness.py`, class `CountingInt`, with the module tally `_ops = {"compare", "add"}`: `__add__`, `__radd__`,
`__sub__` and `__rsub__` add 1 to `_ops["add"]` (through `_add`, which returns a new `CountingInt`); the six
comparison methods add 1 to `_ops["compare"]`. `generate_scaling(n, rng)` returns an n × n matrix of `CountingInt`
entries in 0..9 and resets the tally (`reset_counter`); `reported_cost(output)` returns the sum of both tallies.

An addition or comparison with at least one `CountingInt` operand counts exactly 1 (if only the right operand is
one, the int method returns `NotImplemented` and Python calls the reflected method), and a sum with a `CountingInt`
operand is a `CountingInt`. Plain ints: the literal starting values `value = 0`, `gain = 0`, `best[0] = 0`, all index
and mask arithmetic, and the identity tests `best is None`, `best[t] is None`. The outcome of a comparison only
decides which value is stored; it never changes which operations run. So every count below is the same on every
n × n matrix of `CountingInt` entries.

## 1. Enumeration: n!(n(n − 1)/2 + 1) − 1

**Statement.** For every n ≥ 0 and every input, `linear_ordering_enumeration` makes exactly n(n − 1)/2 counted
additions per order and n! − 1 counted comparisons, in total n!(n(n − 1)/2 + 1) − 1 operations.

**Proof.** The loop runs over all n! orders. For each, `value = value + row[order[q]]` runs once per pair p < q,
n(n − 1)/2 times, each a counted addition (the first through `__radd__` on the plain 0). If n ≥ 2, `value` is then
a `CountingInt`. The test `best is None or value > best` short-circuits for the first order, and for every later
order evaluates `value > best` on two `CountingInt` values: 1 counted comparison, n! − 1 in all. For n ≤ 1 there is
a single order and no pair, so nothing counts, and the formula gives 1 · 1 − 1 = 0.

**Check.** `experiments/2026-10-06i_linear_ordering.py` (n = 2..8). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "LO enumeration n!(n(n-1)/2+1)-1": n = 0..8 (includes the V2 sizes n = 4..8).
`experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "linear ordering: counts per kind on other
matrices": n = 0..8, 3 seeded matrices per n with entries in −9..9.

## 2. Subset DP: 2^(n−2)(n + 4)(n − 1) + 1 for n ≥ 2

**Statement.** For every n ≥ 2 and every input, `linear_ordering_subset_dp` makes exactly n(n − 1)2^(n−2) gain
additions, n·2^(n−1) additions `best_s + gain` and n·2^(n−1) − 2^n + 1 comparisons, in total
2^(n−2)(n + 4)(n − 1) + 1 counted operations. (At n = 0 it makes 0 operations, which the formula also gives; at
n = 1 it makes 0, not 1.)

**Proof.** The outer loop visits every set s in increasing order, and for each v ∉ s forms t = s ∪ {v}.

*Gain additions.* The inner loop adds `row[u]` for every u ≠ v outside t, that is n − |s| − 1 counted additions
(the first through `__radd__` on the plain 0; with no term, `gain` stays the plain 0). Summed over the pairs
(s, v ∉ s): Σ_s (n − |s|)(n − |s| − 1) = Σ_k C(n, k)(n − k)(n − k − 1) = n(n − 1)2^(n−2).

*Value additions.* Claim: for n ≥ 2, every stored `best[t]` with t ≠ ∅ is a `CountingInt`, and every
`best_s + gain` counts. For s = ∅, `best_s` is the plain 0 but `gain` has n − 1 ≥ 1 counted terms, so it is a
`CountingInt`. For s ≠ ∅, `best[s]` was stored while an earlier set s − {w} < s was processed, and by induction on s
it is a `CountingInt`. In both cases `value = best_s + gain` counts 1 and is a `CountingInt`, and the stored
`best[t]` is such a value. There are Σ_s (n − |s|) = n·2^(n−1) pairs (s, v).

*Comparisons.* A set t ≠ ∅ is reached once for each v ∈ t (from s = t − {v}), |t| times. At the first arrival
`best[t] is None` short-circuits and the value is stored; each later arrival evaluates `value > best[t]` on two
`CountingInt` values, 1 counted comparison. Total Σ_{t≠∅} (|t| − 1) = n·2^(n−1) − (2^n − 1).

The reconstruction loop works on plain ints. Total:
n(n − 1)2^(n−2) + 2 · n·2^(n−1) − 2^n + 1 = 2^(n−2)(n² + 3n − 4) + 1 = 2^(n−2)(n + 4)(n − 1) + 1.

*n ≤ 1.* At n = 0 no pair (s, v) exists. At n = 1 the only pair is s = ∅, v = 0, whose gain has no term, so
`value` = plain 0 + plain 0 and nothing counts.

**Check.** `experiments/2026-10-06i_linear_ordering.py` (n = 2..15). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "LO DP 2^(n-2)(n+4)(n-1)+1": n = 0..15 (includes the V2 sizes n = 6..14; n = 1 reported as
outside the domain with count 0); line "LO DP per kind: add n(n-1)2^(n-2)+n2^(n-1), compare n2^(n-1)-2^n+1":
n = 2..13. `experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "linear ordering: counts per kind
on other matrices": n = 0..12, 3 seeded matrices per n, gain and value additions separated.

## 3. The problem statement

Let value(order) = Σ W[a][b] over the pairs with a before b, and back(order) the same sum over the pairs with b before
a (diagonal entries excluded in both).

- *Minimising the backward weight is the same problem:* value(order) + back(order) = Σ_{a ≠ b} W[a][b], a constant, so
  an order maximises value iff it minimises back.
- *0/1 matrices of a digraph:* with W[a][b] = 1 iff a → b is an arc (a ≠ b; the diagonal, where loops would sit, is
  ignored, and a loop lies in every feedback arc set), back(order) is the number of arcs that point backwards. The
  backward arcs of an order form a feedback arc set (the forward arcs contain no cycle), and for a feedback arc set
  F a topological order of the acyclic digraph without F has only arcs of F pointing backwards. So
  min back = the minimum size of a feedback arc set, and the linear ordering problem on 0/1 matrices is the feedback
  arc set problem (the same lemma is proved in `pairs/first-match-rule-ordering-enumeration-vs-subset-dp/PROOFS.md`,
  section 7).

**Checks.** `tests/test_proofs_linear_ordering.py`, class `ProblemStatement` (value + back = constant for every order,
n ≤ 6; total arcs − DP optimum = brute-force minimum feedback arc set on 24 seeded digraphs with n = 1..6 and random
diagonal bits).

## 4. Correctness of the enumeration

`permutations(range(n))` yields every order once (its documented behaviour, a machine-model assumption listed in
`background`, see `pairs/permanent-naive-vs-ryser/PROOFS.md` section 0.1); for each the double loop adds W[order[p]][order[q]] over p < q,
which is value(order) (no diagonal entry is read). The first order is stored and replaced only by a strictly larger
value, so the function returns the maximum and an order attaining it.

## 5. Correctness of the subset DP

**5.1 Key fact.** If the set S of elements placed first is known and v is placed next, the pairs that start at v and
end at an element placed later are the pairs (v, u) with u ∉ S ∪ {v}, whatever the order inside S. Write
gain(S, v) = Σ_{u ∉ S ∪ {v}} W[v][u].

**5.2 Theorem.** best[S] is the maximum, over the orders of S, of the weight of the pairs (a, b) with a ∈ S placed
before b (b in S or not); best[∅] = 0. *Proof.* Induction on |S|. In an order of S with last element v, the pairs
starting at v contribute gain(S − {v}, v) by 5.1, and the pairs starting at the other elements of S do not depend on
where v stands among the later elements, so they contribute at most best[S − {v}], with equality for a suitable order
of S − {v}. Hence best[S] = max_{v ∈ S} best[S − {v}] + gain(S − {v}, v). The code processes the sets in increasing
integer order (S − {v} < S), computes each gain from scratch (the inner loop adds W[v][u] for u ≠ v outside
t = S ∪ {v}) and keeps the maximum. ∎ For S = all elements every pair has its first element in S, so
best[all] = max value. `last[t]` records an element attaining the maximum (the first arrival, replaced only by a
strictly larger value), and walking back from the full set lists an order attaining best[all].

**Check.** `tests/test_proofs_linear_ordering.py`, class `Correctness` (both algorithms return the maximum over all
n! orders and an order attaining it, on 40 seeded matrices with n = 0..7, all kinds of the harness generator).

## 6. Time and space on every input

The counts of sections 1 and 2 do not depend on the entries, so Θ(n!·n^2) (enumeration) and Θ(n^2·2^n) (DP) hold on
every input; for the enumeration this includes the generator, whose O(n·n!) total work (amortised O(n) per order) is
dominated, given the machine-model assumption (Lemma 0.1 of `pairs/permanent-naive-vs-ryser/PROOFS.md`). Including loop control: the enumeration's inner loops run n(n − 1)/2 times per order, and the DP's
u-loop runs n times for each of the n·2^(n−1) pairs (S, v ∉ S), n^2·2^(n−1) iterations. Space: the enumeration keeps
the generator (O(n) words under the same assumption), the current order and two values, Θ(n) besides the input; the DP keeps `best` and `last`, 2^n entries
each: Θ(2^n) table entries.

**Check.** `tests/test_proofs_linear_ordering.py`, class `WorkingMemory`: the DP's tracemalloc peak lies between
16·2^n and 160·2^n bytes for n = 8..15; the enumeration's peak stays below 4096 + 64n bytes for n = 2..8.

## 7. Running row sums: Θ(n 2^n) time with Θ(n 2^n) memory (not implemented)

Let out[v][U] = Σ_{u ∈ U, u ≠ v} W[v][u]. For U ≠ ∅ with lowest element u_0, out[v][U] = out[v][U − {u_0}] + [u_0 ≠ v]·W[v][u_0],
one addition at most per entry. Of the n(2^n − 1) entries with U ≠ ∅, Σ_v 2^(n−1−v) = 2^n − 1 have u_0 = v and are
copies, so the table takes (n − 1)(2^n − 1) additions. Then gain(S, v) = out[v][complement of (S ∪ {v})] is a table
lookup, and the DP of section 5 makes n·2^(n−1) additions. In total Θ(n·2^n) time and Θ(n·2^n) memory, against
Θ(n^2·2^n) time and Θ(2^n) memory for the implemented DP.

**Check.** `tests/test_proofs_linear_ordering.py`, class `RowSumVariant` (a test implementation of the variant: same
optimum as the entry's DP, n·2^n table entries and exactly (n − 1)(2^n − 1) + n·2^(n−1) additions, n = 0..12).

## 8. Uncounted operations are of the same order

The DP's uncounted inner-loop tests `u != v and not (t >> u) & 1` run n^2·2^(n−1) times (section 6), and the counted
operations number 2^(n−2)(n + 4)(n − 1) + 1 (section 2), and (n + 4)(n − 1) = n^2 + 3n − 4. The ratio tends to 2 and
lies in [1, 4] for every n ≥ 2:
- ratio ≥ 1 ⇔ n^2·2^(n−1) − 2^(n−2)(n^2 + 3n − 4) ≥ 1 ⇔ 2^(n−2)(n^2 − 3n + 4) ≥ 1, true since n^2 − 3n + 4 ≥ 2 for every
  integer n ≥ 2 and 2^(n−2) ≥ 1;
- ratio ≤ 4 ⇐ n^2·2^(n−1) ≤ 4·2^(n−2)(n^2 + 3n − 4) ⇔ 2n^2 ≤ 4n^2 + 12n − 16 ⇔ 0 ≤ 2n^2 + 12n − 16, true for n ≥ 2 (at
  n = 1 the right side is −2; there the counted total is 0 and the ratio is not defined).
So the uncounted loop control is of the same order, Θ(n^2·2^n).

**Check.** `tests/test_proofs_linear_ordering.py`, class `UncountedWork` (executions of that line of the unchanged code
= n^2·2^(n−1), and the ratio within [1, 4], n = 1..10).

## 9. Facts used by the V1 oracle (`harness.py`)

- `order_value` recomputes value(order) from positions.
- *Upper bound:* every pair {a, b} contributes either W[a][b] or W[b][a] to value(order), at most the larger one, so
  value(order) ≤ `upper_bound` for every order; a value above it is impossible, and an order attaining it is optimal.
- *Branch and bound:* at a prefix, `so_far` is the weight of the pairs decided by the prefix and `remaining_ub` the
  upper bound for the undecided pairs; every completion has value at most `so_far + remaining_ub`, and a prefix is
  pruned only if this is at most the best complete value found, so no strictly better order is lost and the search
  returns the optimum when it finishes.
- *Improving move:* an order with a larger value proves that the claimed order is not optimal.
- *Hidden acyclic instances* (non-negative entries only from earlier to later elements of a hidden order): the hidden
  order takes every off-diagonal entry, so it attains the upper bound and is optimal.

**Check.** `tests/test_proofs_linear_ordering.py`, class `Oracle` (upper bound ≥ optimum and branch and bound = DP
optimum, 36 seeded matrices with n = 0..8); the oracle controls of `experiments/2026-10-06i_linear_ordering.py`.

## 10. The pair

n!·(n(n − 1)/2 + 1) − 1 against 2^(n−2)(n + 4)(n − 1) + 1: the ratio grows without bound (n!/2^n → ∞), and the
second count is at least 2^(n−2) for n ≥ 2, so the improvement is super-polynomial to smaller super-polynomial
(tag T8). The primary tag T6 rests on the NP-hardness of the problem, which is background (cited, not proved here).
