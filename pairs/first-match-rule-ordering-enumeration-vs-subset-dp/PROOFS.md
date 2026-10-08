# Proofs: first-match rule ordering, enumeration vs subset DP

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code). Sections 1 and 2 prove the exact operation counts of the V2 family,
for every size of their domain, from the code in this folder. Sections 3 to 10 prove the other claims: correctness
of both algorithms, the time and space bounds on every input, the NP-hardness reduction, the equivalence with the
linear ordering problem, the facts used by the V1 oracle and the statements about uncounted operations. Each proof
is followed by the deterministic scripts that check it and the sizes they check it on. A check covers only those
sizes; the proofs cover the whole domain. `entry.json` already outlines both counts in the `time_complexity`
fields; the proofs below give the steps that the outline leaves out.

The statements listed under `background` in `entry.json` are cited, not proved here: the NP-completeness of FEEDBACK
ARC SET and of the linear ordering problem, and the descriptions of the literature (Yee et al., Schmitt & Martignon,
MaxDL, CORELS, Held & Karp, Bodlaender et al.). The NP-hardness of this entry's problem is claimed *relative to*
the first of them: the reduction and the membership in NP are proved in section 7, and the NP-completeness of
FEEDBACK ARC SET is cited.

## Counting convention

`harness.py`, class `CountingInt`, with the module tally `_ops = {"truth", "compare", "add", "bit"}`: `__add__`,
`__radd__`, `__sub__`, `__rsub__` add 1 to `_ops["add"]`; `__lshift__`, `__and__`, `__rand__`, `__or__`, `__ror__`
add 1 to `_ops["bit"]` (all through `_op`, which returns a new `CountingInt`); the six comparison methods add 1 to
`_ops["compare"]`; `__bool__` adds 1 to `_ops["truth"]`. `reported_cost(output)` returns the sum of the four
tallies.

An operation with at least one `CountingInt` operand counts exactly 1 (if only the right operand is one, the int
method returns `NotImplemented` and Python calls the reflected method), and its result is a `CountingInt`; an
operation on two plain ints counts nothing. `sum(...)` starts from the plain int 0. Plain: `total = 0`,
`gain = [0] * k`, `best[0] = 0`, `base = 0`, the subset arithmetic `s & bit`, `s | bit`, the identity tests
`best is None`, `best[t] is None`, and the truth of a Python list (`if not rules[i]`).

**The V2 family.** `generate_scaling(n, rng)` sets k = n and builds m = k items with `cyclic_items(k)`: item i is
matched by rules i and (i + 1) mod k. The match flags, the costs (random in 1..9) and the defaults are
`CountingInt`; the counter is reset (`reset_counter`). For k ≥ 2 every item is matched by exactly two distinct
rules, and every rule r matches exactly the items r and r − 1 (mod k), two items, or the two items 0 and 1 when
k = 2. For k = 1 the single item is matched by the single rule.

## 1. Enumeration: k!(k + 1)(k + 3)/3 − 1 on the V2 family

**Statement.** On the V2 family with k ≥ 2 (and also k = 0), `first_match_order_enumeration` makes exactly
k!·k(k + 1)/3 truth tests, k!·k additions and k! − 1 comparisons, in total k!(k + 1)(k + 3)/3 − 1 counted
operations. (At k = 1 it makes 2.)

**Proof.** For each of the k! orders and each item i, the loop `for r in order` tests `row[r]` (1 truth test,
`__bool__` of a match flag) at each position until the first rule matching i, then executes
`total = total + cost[i][r]` (1 counted addition; the first one of an order through `__radd__` on the plain 0) and
breaks. Every item has a matching rule, so the `else` branch never runs. Per order: k additions, and for item i as
many truth tests as the position (counted from 1) of the earlier of its two rules a, b.

Over all k! orders that position sums to k!·Σ_{j≥1} P(min ≥ j) for a uniformly random order. min(pos a, pos b) ≥ j
exactly when a and b both stand in the k − j + 1 positions j..k, which holds for (k − j + 1)(k − j)(k − 2)! of the
k! orders: P(min ≥ j) = C(k − j + 1, 2)/C(k, 2). By the hockey-stick identity Σ_{j=1..k} C(k − j + 1, 2) =
Σ_{i=1..k} C(i, 2) = C(k + 1, 3), so the sum of positions is k!·C(k + 1, 3)/C(k, 2) = k!(k + 1)/3 per item, and
k!·k(k + 1)/3 for the k items.

After the first order, `best is None` is false, and `total < best` compares two `CountingInt` values (both are sums
of k ≥ 2 counted additions): 1 comparison for each of the other k! − 1 orders. Total
k!·k(k + 1)/3 + k!·k + k! − 1 = k!(k + 1)(k + 3)/3 − 1. At k = 0 the single empty order makes no operation, which the
formula also gives. At k = 1 the single order makes 1 truth test and 1 addition, 2, while the formula gives 5/3.

**Check.** `experiments/2026-10-07_first_match_checks.py` (k = 2..8). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "FM enumeration k!(k+1)(k+3)/3-1": k = 0 and 2..8 (includes the V2 sizes k = 4..8; k = 1 reported
as outside the domain with count 2); line "FM enumeration per kind: truth k!k(k+1)/3, add k!k, compare k!-1": k = 0
and 2..8.

## 2. Subset DP: 3k² + (7k − 2)·2^(k−1) + 2 on the V2 family

**Statement.** On the V2 family with k ≥ 1, `first_match_order_subset_dp` makes exactly k² + k·2^k truth tests,
k² + k·2^k bit operations, k² + k·2^k + 1 additions and k·2^(k−1) − 2^k + 1 comparisons, in total
3k² + (7k − 2)·2^(k−1) + 2 counted operations. The components are those listed in `entry.json`: 3k² for building
`rules` and `masks`, 2k·2^k capture tests, k·2^(k−1) gain additions, k·2^(k−1) transition additions,
k·2^(k−1) − 2^k + 1 comparisons and 1 final addition. (The entry states the total for k ≥ 2; it also holds at
k = 1. At k = 0 the count is 0, while the formula gives 1.)

**Proof.** *Building (k² truth, k² bit, k² add).* `rules` evaluates `if match[i][r]` for all k rules of each of
the m = k items: k² truth tests. `masks` evaluates `match[i][r] << r` (1 bit operation each) and sums the k terms
of each item with `sum`, which starts from the plain 0: k counted additions per item. Total k² shifts and k²
additions.

*Capture tests (k·2^k truth, k·2^k bit).* For each of the 2^k sets s and each item i, `masks[i] & s` counts 1 bit
operation and `not (...)` 1 truth test.

*Gain additions (k·2^(k−1)).* Item i is uncaptured by s exactly when s contains none of its rules: for k ≥ 2 that
is 2^(k−2) sets, and the item then adds `cost[i][r]` into `gain[r]` for its two rules (2 counted additions, the
first into a plain 0 through `__radd__`); in all k · 2^(k−2) · 2 = k·2^(k−1). For k = 1 the single item is uncaptured
only for s = ∅ and adds 1 cost: 1 = k·2^(k−1).

*Transition additions (k·2^(k−1)).* Claim: every `value = best_s + gain[r]` counts and is a `CountingInt`. For
s = ∅, `best_s` is the plain 0, but every item is uncaptured, so `gain[r]` has received the costs of the items that
rule r matches (at least one), and is a `CountingInt`. For s ≠ ∅, `best_s = best[s]` was stored while a smaller set
s − {r'} was processed (sets are processed in increasing order), and by induction it is such a value. Hence each of
the Σ_s (k − |s|) = k·2^(k−1) pairs (s, r ∉ s) counts 1, also where `gain[r]` is still the plain 0.

*Comparisons (k·2^(k−1) − 2^k + 1).* A set t ≠ ∅ is reached |t| times; the first arrival short-circuits at
`best[t] is None`, every later one evaluates `value < best[t]` on two `CountingInt` values. Total
Σ_{t≠∅} (|t| − 1) = k·2^(k−1) − 2^k + 1.

*Final addition (1).* Every item has a rule, so `if not rules[i]` (list truth, plain) never adds a default and
`base` stays the plain 0; `best[size - 1] + base` counts 1. The reconstruction works on plain ints.

Summing: truth k² + k·2^k, bit k² + k·2^k, add k² + 2k·2^(k−1) + 1 = k² + k·2^k + 1, compare k·2^(k−1) − 2^k + 1,
total 3k² + 3k·2^k + k·2^(k−1) − 2^k + 2 = 3k² + (7k − 2)·2^(k−1) + 2. At k = 0 there is no item and no transition,
and `best[0] + base` adds two plain zeros: 0.

**Check.** `experiments/2026-10-07_first_match_checks.py` (k = 2..18). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "FM DP 3k^2+(7k-2)2^(k-1)+2": k = 1..18 (includes the V2 sizes k = 6..14; k = 0 reported as
outside the domain with count 0); line "FM DP 0 at k=0": k = 0; line "FM DP per kind: truth k^2+k2^k, bit k^2+k2^k, add k^2+k2^k+1, compare
k2^(k-1)-2^k+1": k = 1..14. `experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "first match DP:
components (build, capture, gain, transition, final)": k = 1..12.

## 3. Correctness of the enumeration

Notation: M_i = {r : match[i][r] = 1} is the match set of item i; an item is *captured* by the first rule of the
order that lies in M_i; price(order) = Σ_i (cost[i][r_i] if M_i ≠ ∅, with r_i the capturing rule, else default[i]).

`permutations(range(k))` yields each of the k! orders once (for k = 0 the empty order; its documented behaviour, a
machine-model assumption listed in `background`, see `pairs/permanent-naive-vs-ryser/PROOFS.md` section 0.1). For each order, the inner
loop scans the order until the first rule r with `match[i][r]` true, adds `cost[i][r]` and stops; if no rule matches
it adds `default[i]`. So `total` = price(order). The first order is stored, and a later order replaces the stored one
only if its total is strictly smaller, so the function returns min price and an order attaining it (the first one
in the generation order).

## 4. Correctness of the subset DP

**4.1 Key fact.** If S is the set of rules placed before r, then r captures exactly the items i with r ∈ M_i and
M_i ∩ S = ∅, whatever the order inside S: an item with a rule of S in M_i was captured earlier, one without is not
captured yet. Write gain(S, r) = Σ cost[i][r] over these items.

**4.2 Theorem.** For every set S of rules, after the loop has processed all subsets of S, best[S] is the minimum,
over the orders of S, of the total price of the items captured by S (those with M_i ∩ S ≠ ∅); best[∅] = 0.

*Proof.* Induction on |S|. For S ≠ ∅ and an order of S with last rule r, the items captured by S are those captured
by S − {r} and those captured by r, which by 4.1 are the items with r ∈ M_i and M_i ∩ (S − {r}) = ∅, paying
gain(S − {r}, r) whatever the order of S − {r}. The first part costs at least best[S − {r}], with equality for a
suitable order of S − {r} (induction). Hence the minimum over the orders of S is
min_{r ∈ S} best[S − {r}] + gain(S − {r}, r). The code processes the sets in increasing integer order, so S − {r} < S
is complete when it is processed; processing s computes gain(s, r) for every r ∉ s in one pass over the items
(an item is uncaptured iff `masks[i] & s` = 0) and lowers `best[s | {r}]` to `best[s] + gain[r]`, so after all
subsets of S are processed best[S] is that minimum. ∎

**4.3 Answer and order.** Every order of all k rules captures exactly the items with M_i ≠ ∅; the others pay their
defaults whatever the order. So the optimum is best[all] + Σ_{M_i = ∅} default[i], which the code returns. `last[t]`
records a rule r attaining the minimum for t (the first arrival, replaced only by a strictly smaller value), and
walking back from the full set through t − {last[t]} lists an order whose prefixes attain best at every step; by the
induction of 4.2 this order has price equal to the optimum.

**4.4 Set-dependent costs.** The proof of 4.2 uses only that the price paid by an item captured by r depends on
(i, r) and on the *set* S of rules placed before r. So the same recurrence, with gain(S, r) = Σ c(i, r, S) over the
items captured by r, is exact for any cost c(i, r, S) that depends only on that set. (The implementation supports
cost[i][r] only; the generalisation is checked with a separate test implementation.)

**Checks.** `tests/test_proofs_first_match.py`: class `Correctness`, `test_against_all_orders` (both algorithms
return the minimum over all k! orders, and their order attains it, on 56 seeded instances with k = 0..6);
`test_set_dependent_costs` (4.4, 42 seeded instances with k = 0..6, random set-dependent costs, against brute force).
`experiments/2026-10-07_first_match_checks.py` §2 and the V1 battery compare the implementations with the oracle.

## 5. Time on every input

**5.1 Enumeration.** Per order and item at most k match tests and one addition; one comparison per order after the
first: O(k!·k·m) counted operations for k, m ≥ 1. The generator itself does O(k·k!) work in total under the
machine-model assumption (Lemma 0.1 of `pairs/permanent-naive-vs-ryser/PROOFS.md`), which is within O(k!·k·m) for
m ≥ 1. So the time bounds O(k!·k·m) and Θ(k!·k·m) below are conditional on that assumption; the exact counts use only
the documented behaviour (every order once). More precisely, with every entry counted (the harness's `CountingInt`), on every
instance with m ≥ 1 items:

  truth tests = k!·Σ_i ℓ_i,  additions = k!·m,  comparisons = k! − 1,

where ℓ_i = (k + 1)/(t_i + 1) for an item with t_i = |M_i| ≥ 1 and ℓ_i = k for t_i = 0. *Proof.* For t ≥ 1 given
rules, the position of the first of them in a uniformly random order is ≥ j iff all t lie in positions j..k, which
has probability C(k − j + 1, t)/C(k, t); summing over j = 1..k (hockey stick: Σ_j C(k − j + 1, t) = C(k + 1, t + 1))
gives the expected position C(k + 1, t + 1)/C(k, t) = (k + 1)/(t + 1), so the k! orders contribute k!(k + 1)/(t + 1)
truth tests for the item. An item with t = 0 scans all k rules in every order. The additions and comparisons are as
in section 1. ∎ Consequently, if every item matches at most c rules, the enumeration makes at least
k!·m·k/(c + 1) truth tests (ℓ_i ≥ (k + 1)/(c + 1) if t_i ≥ 1, and ℓ_i = k if t_i = 0), so Θ(k!·k·m) for fixed c (the
claim of the docstring of `enumeration.py`). Section 1 is the case
t_i = 2.

**5.2 Subset DP.** Per subset: one list of k gains, m capture tests, the gain additions of the uncaptured items, k
bit tests and k − |S| transitions. An item with t ≥ 1 rules is uncaptured for the 2^(k−t) sets avoiding M_i and then
adds t costs; t·2^(k−t) ≤ 2^(k−1) because t ≤ 2^(t−1). An item with t = 0 adds nothing. Building `rules` and `masks`
takes O(km) ≤ O(m·2^k), the defaults O(m), the reconstruction O(k). In total Θ(2^k (k + m)) on every input (with
k + m read as at least 1).

**Checks.** `tests/test_proofs_first_match.py`: class `EnumerationCounts` (the identity of 5.1 for k ≤ 12, and the
sum of first positions over all orders by enumeration for k ≤ 6; the three exact counts on 48 seeded instances with
k = 1..6, all kinds of the harness generator); class `DPWork` (executions of the capture test, the gain addition and
the transition line of the unchanged code are m·2^k, Σ_i t_i 2^(k−t_i) ≤ m·2^(k−1) and k·2^(k−1), on 36 seeded
instances with k = 0..8).

## 6. Space

The enumeration keeps the permutation generator (O(k) words under the machine-model assumption, Lemma 0.1 of
`pairs/permanent-naive-vs-ryser/PROOFS.md`), the current order, `total`, `best` and `best_order`: Θ(k) besides the
input. The DP keeps `best` and `last` (2^k entries each), one gain list of k entries, and `rules` and `masks`
(O(km)): Θ(2^k) table entries.

**Check.** `tests/test_proofs_first_match.py`, class `WorkingMemory`: the DP's tracemalloc peak lies between 16·2^k
and 160·2^k bytes for k = 8..15; the enumeration's peak stays below 4096 + 64k bytes for k = 2..8 (no growth with
k!).

## 7. NP-hardness: the reduction from FEEDBACK ARC SET (claim) and membership in NP

**Decision versions.** FM-DEC: given an instance and an integer K, is there an order with price ≤ K? FAS: given a
digraph D = (V, A) and an integer K, is there F ⊆ A with |F| ≤ K such that D − F is acyclic?

**7.1 FM-DEC is in NP.** An order is a certificate; its price is computed in O(km) time.

**7.2 Reduction.** Given (D, K): a loop (u, u) is a cycle, so it lies in every feedback arc set. Let L be the number
of loops, D' = D without its loops and K' = K − L. If K' < 0, output a fixed no-instance (for example one rule and
one item matched by it with cost 1, and K = 0). Otherwise take the vertices of D' as rules and, for every arc u → v
of D', an item matched exactly by u and v with cost 0 for u and cost 1 for v (and cost 0 at the other positions,
which are ignored); threshold K'. The construction takes polynomial time (|A| items of k entries).

**7.3 Lemma.** For every order of the rules, price(order) is the number of arcs of D' that point backwards (v before
u for an arc u → v). *Proof.* The item of u → v is captured by whichever of u, v comes first: cost 0 if u, cost 1
if v. ∎

**7.4 Lemma.** The minimum number of backward arcs over all orders equals the minimum size of a feedback arc set of
D'. *Proof.* The backward arcs of an order form a feedback arc set: the remaining arcs all point forwards, so they
contain no cycle. Conversely, for a feedback arc set F, D' − F is acyclic and has a topological order; in it only
arcs of F can point backwards, so it has at most |F| backward arcs. ∎

**7.5 Theorem.** (D, K) is a yes-instance of FAS iff the constructed instance is a yes-instance of FM-DEC. *Proof.*
D has a feedback arc set of size ≤ K iff D' has one of size ≤ K − L (add or remove the loops), iff (by 7.3 and 7.4)
some order has price ≤ K'. If K' < 0, D has none. ∎ With non-negative integer arc weights and cost w for the arc's
head, the same lemmas give the weighted version (minimum total weight); there K is lowered by the total weight of
the loops. The constructed instances have exactly two
matching rules per item, so by section 8 the reduction also lands in the linear ordering problem.

**Conclusion.** FAS reduces to FM-DEC in polynomial time and FM-DEC is in NP. Given the NP-completeness of FAS
(background: Karp 1972), FM-DEC is NP-complete and the optimisation problem is NP-hard; a polynomial-time algorithm
would then imply P = NP. This conditional statement is what the primary tag T6 rests on.

**Checks.** `tests/test_proofs_first_match.py`, class `Reduction` (36 seeded digraphs with 1..6 vertices and up to
10 arcs, 23 of them with loops: the minimum feedback arc set by brute force equals the DP optimum of the reduced
instance plus the number of loops, and the decision answers agree for every threshold K = 0..|A|).
`experiments/2026-10-07_first_match_checks.py` §3 (300 random weighted loopless digraphs: optimum = brute-force
minimum feedback arc set weight; reduced price = backward weight on 39 314 orders);
`tests/test_entry_first_match.py`, `test_feedback_arc_set_reduction`.

## 8. At most two matching rules: the linear ordering problem

**8.1 From first-match to linear ordering.** Suppose every item matches at most two rules. An item with no rule
pays its default and one with a single rule pays that rule's cost, in every order. For an item with
M_i = {a, b}, a < b, the price is cost[i][a] if a comes before b and cost[i][b] otherwise, i.e.
cost[i][b] + (cost[i][a] − cost[i][b])·[a before b]. Summing, price(order) = C + Σ_{a ≠ b} W[a][b]·[a before b] with a
constant C and W[a][b] = Σ over the items with M_i = {a, b} of (cost[i][a] − cost[i][b]): minimising the price is the
linear ordering problem for the matrix −W (maximise the forward weight).

**8.2 From linear ordering to first-match.** Given an integer matrix W (maximise Σ W[a][b] over the pairs with a before
b), let w = max_{a ≠ b} W[a][b] (w = 0 if k ≤ 1, when there is no pair) and create, for every pair a < b, an item
matched by a and b with cost[i][a] =
w − W[a][b] and cost[i][b] = w − W[b][a] (both ≥ 0) and default 0. Then price(order) = C(k, 2)·w − (forward weight
of the order), so the optimal orders coincide and the optimum values determine each other.

Together, the instances whose items match at most two rules are exactly the linear ordering problem.

**Checks.** `tests/test_proofs_first_match.py`, class `LinearOrdering` (8.1: price = C + forward weight for every order
of 29 seeded instances with k = 1..6; 8.2: the DP optimum of the constructed instance equals C(k, 2)·w minus the
brute-force linear ordering maximum, 30 seeded matrices with k = 1..6). `experiments/2026-10-07_first_match_checks.py`
§4 (25 741 (instance, order) pairs) and `tests/test_entry_first_match.py`, `test_at_most_two_rules_is_linear_ordering`.

## 9. Facts used by the V1 oracle (`harness.py`)

- `order_cost` recomputes the price from positions: each item is captured by its matching rule of smallest position,
  which is the first-match rule.
- *Lower bound.* An item with M_i ≠ ∅ pays the cost of some rule of M_i, at least min_{r ∈ M_i} cost[i][r]; an item
  with M_i = ∅ pays its default. So every order costs at least `lower_bound`, a claimed cost below it is impossible,
  and an order attaining it is optimal.
- *Branch and bound.* At a prefix, `so_far` is the price of the items already captured and `remaining_lb` the sum of
  the cheapest matching costs of the others; every completion costs at least `so_far + remaining_lb` (plus the fixed
  defaults). A prefix is pruned only if this bound is at least the best complete order found so far, so no strictly
  better order is lost, and the search returns the optimum when it finishes.
- *Improving move.* An order with a lower price proves that the claimed order is not optimal.

**Check.** `tests/test_proofs_first_match.py`, class `Oracle` (lower bound ≤ optimum and branch and bound = DP
optimum on 40 seeded instances with k = 0..7); the oracle controls of `experiments/2026-10-07_first_match_checks.py` §5.

## 10. Uncounted operations (caveats)

- *Plain-integer additions and comparisons.* A gain to which no uncaptured item contributes stays the plain 0, and a
  `best[S]` reached only through plain zeros stays plain (for example when the rules in S match no item); additions
  and comparisons with two plain operands are not counted. On the V2 family this does not happen: every gain at
  S = ∅ and every best[S] with S ≠ ∅ is a counted value (section 2, transition additions).
- *Same order on the V2 family.* The DP tests `s & bit` for all k rules of every subset (k·2^k plain bit tests) and
  forms `s | bit` for the k − |S| transitions (k·2^(k−1)); the counted total on the V2 family is
  3k^2 + (7k − 2)·2^(k−1) + 2 (section 2). Both are Θ(k·2^k), so on the V2 family the uncounted bookkeeping is of the
  same order as the counted operations.
- *Sizes.* Every total and every best value is a sum of at most m input numbers (one cost or default per item), so
  unit-cost arithmetic is a polynomial-factor simplification of bit complexity.
