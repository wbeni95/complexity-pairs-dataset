# Proofs: first-match rule ordering, enumeration vs subset DP (and the subset DP with zeta-transformed gains)

This file proves the claims that this entry makes about its problem and its three algorithms (in `entry.json`,
`README.md` and the docstrings of the code). Sections 1 and 2 prove the exact operation counts of the V2 family,
for every size of their domain, from the code in this folder. Sections 3 to 10 prove the other claims: correctness
of both algorithms, the time and space bounds on every input, the NP-hardness reduction, the equivalence with the
linear ordering problem, the facts used by the V1 oracle and the statements about uncounted operations. Section 11
proves every claim about the third algorithm, the subset DP with zeta-transformed gains (`zeta_dp.py`): its
correctness, its exact counts (on every instance and on the V2 family), its executed operations, time and space on
every input, and its comparison with the subset DP. Each proof
is followed by the deterministic scripts that check it and the sizes they check it on. A check covers only those
sizes; the proofs cover the whole domain. `entry.json` already outlines both counts in the `time_complexity`
fields; the proofs below give the steps that the outline leaves out.

The statements listed under `background` in `entry.json` are cited, not proved here: the NP-completeness of FEEDBACK
ARC SET and of the linear ordering problem, and the descriptions of the literature (Yee et al., Schmitt & Martignon,
MaxDL, CORELS, Held & Karp, Bodlaender et al., Koivisto & Sood). The NP-hardness of this entry's problem is claimed
*relative to* the first of them: the reduction and the membership in NP are proved in section 7, and the
NP-completeness of FEEDBACK ARC SET is cited.

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
`best is None`, `best[t] is None`, and the truth of a Python list (`if not rules[i]`). For `zeta_dp.py` the plain
values are listed in section 11.5.

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
(O(km)): Θ(2^k) table entries. The zeta variant keeps Θ(k·2^k) table entries (section 11.7).

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
- *The zeta variant.* Its tables start from a counted zero, so its counts include every transform addition
  (section 11.5); only its plain subset arithmetic is uncounted, as here.
- *Sizes.* Every total and every best value is a sum of at most m input numbers (one cost or default per item), so
  unit-cost arithmetic is a polynomial-factor simplification of bit complexity. In the zeta variant every table
  entry is a sum of at most m input costs as well.

## 11. The third algorithm: subset DP with zeta-transformed gains (`zeta_dp.py`)

This section proves every claim about `implementations/zeta_dp.py`: its correctness (11.2–11.4), its exact counts
in the counting convention on every instance and on the V2 family (11.5, 11.6), its executed operations, time and
space on every input (11.7), and the comparison with the subset DP (11.8).

**Credit (background).** Koivisto & Sood (2004) compute, for every variable i of a Bayesian network,
α_i(S) = Σ_{T ⊆ S} β_i(T), a sum over subsets that they call the Möbius transform (§4, p. 557). They evaluate it with
a fast transform over the subset lattice (Figure 2 and Proposition 7, pp. 558–559, a truncated form of the standard
fast transform, for which they cite Kennes & Smets 1991 on pp. 557–558), and they sum over all orders of the
variables with the recursion g(S) = Σ_{i ∈ S} q_i(S − {i}) α_i(S − {i}) g(S − {i}) over the subset lattice, in which
only the unordered set of predecessors matters (Proposition 6, pp. 556–557; Theorem 8, p. 559). Their §5 states the
max-product counterpart (Theorem 11, p. 561) and omits the algorithmic details. The algorithm of this section uses
the same technique, a transform over the subset lattice whose values feed a dynamic program over the sets of elements
placed so far, with a sum transform read at the complement of the placed set and a min-plus recurrence. These
adaptations are routine and are not claimed as new. The fast transform is Yates' method (Yates 1937), as in
`pairs/subset-sum-zeta-transform-naive-vs-yates`. Everything below is proved here; the citations are credit.

**11.1 The algorithm.** Notation of section 3; t_i = |M_i|, L = Σ_i t_i (the matching (item, rule) pairs) and m₀ the
number of items with M_i = ∅. For a set W of rules, W^c is its complement (`full ^ s` in the code) and A_b = {b + 1,
…, k − 1} the bits above b (A_{−1} = all rules). For every rule r and set U of rules, a_r[U] = Σ_{i : M_i = U}
cost[i][r] if r ∈ U, and a_r[U] = 0 if r ∉ U; ζa_r[W] = Σ_{U ⊆ W} a_r[U]. The code (1) builds `rules` as
`subset_dp.py` does; (2) creates the tables, every entry starting as the 0 of the costs' number type (11.5), for each
item with M_i ≠ ∅ forms the bit mask u of M_i from the plain rule indices and adds cost[i][r] into `a[r][u]` for every
r ∈ M_i, and for each item with M_i = ∅ adds default[i] into `base`; (3) for each rule r runs Yates' passes b = 0, …,
k − 1: for w = 0, …, 2^k − 1 with b ∈ w, `a[r][w] = a[r][w] + a[r][w − 2^b]`; (4) runs the recurrence of section 4
over s = 0, …, 2^k − 1 in increasing order, with `value = best[s] + a[r][s^c]` for every r ∉ s, storing the first
arrival at t = s ∪ {r} and replacing it only by a strictly smaller value; (5) returns `best[all] + base` and the order
rebuilt from `last`.

**11.2 Lemma (gain identity).** For every set S and every rule r ∉ S, gain(S, r) = ζa_r[S^c].

*Proof.* Item i contributes cost[i][r] to gain(S, r) iff r ∈ M_i and M_i ∩ S = ∅ (4.1), that is iff r ∈ M_i ⊆ S^c.
Grouping the items by U = M_i, Σ_{U ⊆ S^c} a_r[U] = Σ_{U ⊆ S^c, r ∈ U} Σ_{i : M_i = U} cost[i][r] = gain(S, r),
because a_r[U] = 0 when r ∉ U. ∎

**11.3 Lemma (Yates' passes).** After step 2, a[r][U] = a_r[U] for every r and U. For b = −1, 0, …, k − 1, after the
passes for the bits 0, …, b (no pass for b = −1),

  a[r][W] = Σ {a_r[U] : U ⊆ W and U ∩ A_b = W ∩ A_b}   for every set W.

In particular (b = k − 1, A_b = ∅) a[r][W] = ζa_r[W] when step 3 ends.

*Proof.* Step 2 adds cost[i][r] into a[r][M_i] exactly for the items with r ∈ M_i, so a[r][U] = a_r[U]; this is the
claim for b = −1. Induction on b: pass b changes only entries a[r][w] with b ∈ w, and the entry it reads,
a[r][w − 2^b], has b ∉ w − 2^b, so it still holds its value after pass b − 1 (the update in place reads only entries
that the pass does not change). For b ∈ W the new value is the old value at W plus the old value at W − {b}; by the
induction hypothesis these are the sums over the sets U ⊆ W that agree with W on A_{b−1} (so b ∈ U) and over the sets
U ⊆ W − {b} that agree with W − {b} on A_{b−1} (so b ∉ U); together these are exactly the sets U ⊆ W with
U ∩ A_b = W ∩ A_b. For b ∉ W the entry is unchanged, and every U ⊆ W agrees with W at b (b ∉ U), so the two ranges
coincide. ∎

**11.4 Theorem (correctness).** On every instance `first_match_order_zeta_dp` returns exactly the pair that
`first_match_order_subset_dp` returns: the minimum price and an optimal order.

*Proof.* The recurrence starts after step 3 and does not write into `a`, so at every pair (s, r ∉ s) it reads
a[r][s^c] = ζa_r[s^c] = gain(s, r) (11.3, 11.2). `subset_dp.py` processes the same pairs in the same order (s
increasing, r increasing) and adds the same integer gain(s, r), collected by its pass over the items (4.2). Both apply
the same rule (store the first arrival, replace only by a strictly smaller value), so by induction over this common
sequence of steps their tables `best` and `last` are equal after every step; hence they return the same best[all]
and rebuild the same order. Both add exactly the defaults of the items with M_i = ∅ (step 2 here). By section 4 (4.2,
4.3) this pair is the optimum with an optimal order. At k = 0 both return (Σ_i default[i], ()). ∎

**Checks.** `tests/test_proofs_first_match_zeta.py`: class `Correctness` (the minimum over all k! orders and an
attaining order on 56 seeded instances with k = 0..6; the same pair as the subset DP on 60 seeded instances with
k = 0..9); class `Transform` (the tables before every pass and after the last one, read from the unchanged code by a
tracer, against 11.3, and the gain identity 11.2 for every S and r ∉ S, on 36 seeded instances with k = 0..5).
`experiments/2026-10-13_first_match_zeta_checks.py` §3 (250 seeded instances with k = 0..12: the same pair as the
subset DP in all 250; the brute-force optimum with an attaining order in all 218 with k ≤ 7; `check` accepts all 248
outputs it can decide and leaves 2 undecided at k ≥ 8) and §5 (negative controls: copies of the code that read the
gain at s instead of s^c, leave out one pass or leave out the defaults give wrong costs on 149, 101 and 76 of the 218
instances with k ≤ 7; a copy that resolves ties by ≤ stays optimal but returns a different order from the subset DP
on 129 of 250).

**11.5 Theorem (counted operations on every instance).** The tables start from `zero = type(cost[0][0])(0)`, the 0 of
the costs' number type, which on a counted instance is a `CountingInt` (constructing it is not an operation of the
convention). Every addition into a table entry then has a counted operand, so the counts record all of the
transform's additions; tables started from the plain 0 would leave the additions of two plain zeros uncounted. Plain
here, besides the list under "Counting convention": `zero` when k = 0 or m = 0, the masks u and all subset arithmetic
(`u |= 1 << r`, `w & bit`, `w ^ bit`, `full ^ s`, `s & bit`, `s | bit`), and the truth of the list `rules[i]`.

On every instance whose entries are all `CountingInt`, with k ≥ 1 and m ≥ 1, `first_match_order_zeta_dp` makes exactly
k·m truth tests, no bit operation, L + m₀ + k²·2^(k−1) + k·2^(k−1) + 1 additions and k·2^(k−1) − 2^k + 1 comparisons,
in total

  k·m + L + m₀ + k²·2^(k−1) + k·2^k − 2^k + 2

counted operations. With m = 0 it makes none; with k = 0 and m ≥ 1 it makes m + 1 additions and nothing else.

*Proof.* *Truth tests and bit operations.* The comprehension evaluates `if match[i][r]` for the k·m pairs (one
`__bool__` each). No other truth test or bit operation involves a `CountingInt`: `if rules[i]` tests a list,
`best[t] is None` is an identity test, and the masks and sets are plain.

*Table entries.* Every entry starts as the `CountingInt` zero and changes only by additions with a `CountingInt`
operand, so it is a `CountingInt` at all times.

*Additions.* For each item with M_i ≠ ∅ and each r ∈ M_i, `a[r][u] + cost[i][r]` counts: L additions. For each item
with M_i = ∅, `base + default[i]` counts: m₀. Step 3 executes `z[w] + z[w ^ bit]` once for each rule r, each pass b
and each of the 2^(k−1) sets w containing b, every time on two table entries: k²·2^(k−1) additions. The recurrence
executes `best_s + a[r][rest]` for the Σ_s (k − |s|) = k·2^(k−1) pairs (s, r ∉ s), each with the operand a[r][rest]:
k·2^(k−1) additions, and every value it stores is a `CountingInt`. `best[full] + base` counts 1, as best[full] is a
stored value (k ≥ 1).

*Comparisons.* A set t ≠ ∅ is reached |t| times; the first arrival short-circuits at `best[t] is None`, and each of
the other Σ_{t ≠ ∅} (|t| − 1) = k·2^(k−1) − 2^k + 1 arrivals evaluates `value < best[t]` on two `CountingInt` values.
The reconstruction works on plain ints.

*m = 0 or k = 0.* With m = 0 there is no entry: `zero` is the plain 0, every table entry, gain and stored value is a
plain int, and nothing counts. With k = 0 and m ≥ 1 there is no rule and no table; every item adds its default into
`base` (m counted additions), and `best[0] + base` counts 1 because `base` is a `CountingInt`. ∎

**11.6 Corollary (the V2 family).** On the V2 family with k ≥ 2, `first_match_order_zeta_dp` makes exactly k² truth
tests, 2k + 1 + (k² + k)·2^(k−1) additions (2k table additions, k²·2^(k−1) transform additions, k·2^(k−1) transition
additions and 1 final addition) and k·2^(k−1) − 2^k + 1 comparisons, in total

  k² + 2k + 2 + (k² + 2k − 2)·2^(k−1)

counted operations. At k = 0 and k = 1 it makes 0 and 5.

*Proof.* m = k, m₀ = 0 and k·m = k²; for k ≥ 2 every item is matched by two rules, so L = 2k, and 11.5 gives
k² + 2k + k²·2^(k−1) + k·2^k − 2^k + 2 = k² + 2k + 2 + (k² + 2k − 2)·2^(k−1). At k = 1 the single item is matched by
the single rule (L = 1): 1 + 1 + 1 + 2 − 2 + 2 = 5. At k = 0 there is no item: 0. ∎

*Against the subset DP (section 2).* The difference of the two V2 counts is
(k² + 2k + 2 + (k² + 2k − 2)·2^(k−1)) − (3k² + (7k − 2)·2^(k−1) + 2) = (k² − 5k)·2^(k−1) − 2k² + 2k. For 2 ≤ k ≤ 5 it
is negative (22, 69, 202, 565 counted operations against 38, 105, 258, 605). For k ≥ 6 it is positive: it equals
2k((k − 5)·2^(k−2) − (k − 1)), and (k − 5)·2^(k−2) − (k − 1) is 11 at k = 6 and increases with k. The quotient of
the two counts tends to infinity like k/7: both counts divided by 2^(k−1) are (k² + 2k − 2) + o(1) and (7k − 2) + o(1).
So on the V2 family the variant makes more counted operations than the subset DP for every k ≥ 6.

**Checks.** `experiments/2026-10-13_first_match_zeta_checks.py` §1 (the closed form and the split by kind for
k = 2..17, which include the V2 sizes k = 6..14; 0 and 5 at k = 0, 1; the same counts for other drawn costs) and §2
(Theorem 11.5 on 270 seeded instances of all six generator kinds with k = 0..8: exact counts on the 229 with
k, m ≥ 1, none on the 18 with m = 0, m + 1 additions on the 23 with k = 0 and m ≥ 1); §5 (a copy with one extra
counted addition per transition, and a copy whose tables start from the plain 0, each change the V2 count at all 13
sizes k = 2..14). `tests/test_proofs_first_match_zeta.py`, class `Counts` (Theorem 11.5 on 48 seeded instances with
k = 0..7; Corollary 11.6 for k = 0..12; the comparison with the subset DP's V2 count for k = 2..40) and class
`NegativeControls`.

**11.7 Executed operations, time and space on every input.** The code executes: k·m match tests (the comprehension);
the mask line `u |= 1 << r` and the table addition L times each; the default addition m₀ times; in step 3, k·k·2^k
bit tests `w & bit` and exactly k·k·2^(k−1) transform additions (k rules, k passes, 2^(k−1) sets containing the pass's
bit); the transition line and the comparison line k·2^(k−1) times each (section 4: Σ_s (k − |s|)), of which
k·2^(k−1) − 2^k + 1 evaluate `value < best[t]`; one final addition; besides the allocation of the k tables of 2^k
entries, `best` and `last` (2^k entries each), and a reconstruction of k steps. By 11.5 the counted operations are
exactly these match tests, additions and comparisons; as in the subset DP (section 10), only the plain subset
arithmetic is not counted (the k²·2^k bit tests, the masks and the sets), which is of the same order. Every executed
line is O(1) in the unit-cost model of this entry, so for k ≥ 1 the time is Θ(k²·2^k + k·m) on every input: the
transform alone executes k²·2^(k−1) additions and the comprehension k·m match tests, and everything else is
O(k·2^k + k·m) (L ≤ k·m, m₀ ≤ m). The k·m term is reading the match flags: the bound includes reading the input. The
working memory is Θ(k·2^k) table entries (the k tables, `best` and `last`), besides the rule lists (O(k·m)).

**Checks.** `experiments/2026-10-13_first_match_zeta_checks.py` §4 (line-execution counts of the unchanged code on
300 seeded instances with k = 0..9: the mask and table lines L times, the default line m₀ times, k²·2^k bit tests,
k²·2^(k−1) transform additions, k·2^(k−1) transitions and comparison lines). `tests/test_proofs_first_match_zeta.py`,
class `Work` (the same line counts on 36 seeded instances with k = 0..8) and class `WorkingMemory` (the tracemalloc
peak lies between 8k·2^k and 16(k + 2)·2^k bytes for k = 8..14).

**11.8 Comparison with the subset DP.**

*(a) As k → ∞.* Measure both algorithms in executed operations (time in the unit-cost model). By 5.2 and 11.7 there
are absolute constants c₁, …, c₄ > 0 with c₁·2^k(k + m) ≤ T_DP ≤ c₂·2^k(k + m) and
c₃(k²·2^k + k·m) ≤ T_ζ ≤ c₄(k²·2^k + k·m) on every instance with k ≥ 1. Hence T_DP/T_ζ lies within constant factors
of ρ = 2^k(k + m)/(k²·2^k + k·m) = (k + m)/(k² + k·m/2^k). Let m = m(k) be any function of k.
- If m/k² → ∞: k·m/2^k = o(m) and k² = o(m), so the denominator is o(m), and ρ → ∞.
- If m/k² → 0: ρ ≤ (k + m)/k² → 0.
- If m/k² does not tend to ∞, then m ≤ Ck² for some C and infinitely many k, and there ρ ≤ (k + Ck²)/k² ≤ C + 1. If
  m/k² does not tend to 0, then m ≥ εk² for some ε > 0 and infinitely many k, and there
  ρ ≥ m/(k² + k·m/2^k) = 1/(k²/m + k/2^k) ≥ 1/(1/ε + k/2^k), which is at least ε/2 once k/2^k ≤ 1/ε.

So, as k → ∞ with m any function of k, the variant is asymptotically faster than the subset DP (T_DP/T_ζ → ∞) exactly
when m/k² → ∞, and slower (T_DP/T_ζ → 0) exactly when m/k² → 0, that is m = o(k²); when m = Θ(k²) the two are within
constant factors of each other. Both bounds include reading the input (the k·m match tests).

*(b) Bounded k.* Fix k ≥ 1 and let m → ∞. By 5.2 and 11.7 both algorithms take Θ(m) time, so only the constant
factor can differ. In the counting convention (every entry a `CountingInt`) it is of order 2^k/k:
- The subset DP makes, on every instance, k·m + m·2^k truth tests (k per item for `rules`, one per item and set for
  the capture test), k·m + m·2^k bit operations (k shifts per item for `masks`, one `&` per item and set; `masks[i]`
  is a `CountingInt` since k ≥ 1), k·m + G + m₀ + R additions with G = Σ_{i : t_i ≥ 1} t_i·2^(k−t_i) (k per item in
  `sum`, which starts from the plain 0; the gain additions of 5.2, each with the operand cost[i][r]; one per default)
  and 0 ≤ R ≤ k·2^(k−1) + 1 (transitions and the final addition), and at most k·2^(k−1) − 2^k + 1 comparisons. (If
  every rule matches an item, every gain at s = ∅ is a `CountingInt`, so by induction on |s| every stored value is
  one; then R = k·2^(k−1) + 1 and the comparisons are exactly k·2^(k−1) − 2^k + 1.)
- The variant makes k·m truth tests, L + m₀ table additions and, by 11.5 (m ≥ 1), exactly
  k²·2^(k−1) + k·2^k − 2^k + 2 further counted operations, which do not depend on m.

So the subset DP counts Σ_i d(t_i) + R₁ and the variant Σ_i v(t_i) + R₂, with d(t) = 3k + 2^(k+1) + t·2^(k−t) and
v(t) = k + t for t ≥ 1, d(0) = 3k + 2^(k+1) + 1 and v(0) = k + 1, 0 ≤ R₁ ≤ k·2^k − 2^k + 2 and
R₂ = k²·2^(k−1) + k·2^k − 2^k + 2. Every quotient f(t) = d(t)/v(t) lies in
[2^k/k + 3/2, 5·2^(k−1)/k + 3]: d(t) ≥ 3k + 2^(k+1) and v(t) ≤ 2k; d(t) ≤ 3k + 2^(k+1) + 2^(k−1) (t·2^(k−t) ≤ 2^(k−1)
for t ≥ 1, section 5.2, and 1 ≤ 2^(k−1)) and v(t) ≥ k. The quotient Σ_i d(t_i)/Σ_i v(t_i) lies between the smallest
and the largest f(t_i), Σ_i v(t_i) ≥ k·m → ∞, and R₁, R₂ are bounded. Hence, as m → ∞, every limit point of (counted
operations of the subset DP)/(counted operations of the variant) lies in [2^k/k + 3/2, 5·2^(k−1)/k + 3]; if every
item has the same number t ≥ 1 of matching rules, the quotient tends to f(t), for example f(2) = 2590/12 ≈ 215.8 at
k = 10. The constant is stated in the entry's counting convention, in which a capture test of the subset DP is two
operations (an `&` and a truth test) and building its rule lists and masks is 3k operations per item.

*(c) The V2 family* has m = k = o(k²), and there the variant is the slower algorithm: by 11.6 it makes more counted
operations than the subset DP for every k ≥ 6, the quotient growing like k/7, and in executed operations it makes
k²·2^(k−1) transform additions against Θ(k·2^k) operations of the subset DP (5.2).

**Checks.** `tests/test_proofs_first_match_zeta.py`, class `Counts`, `test_subset_dp_per_item_counts` (the subset
DP's counts per kind on 42 seeded instances with k = 1..7: exact truth tests and bit operations, additions and
comparisons exact when every rule matches an item and within the bounds otherwise); class `Comparison` (every f(t)
in the interval for k = 1..40 and t = 0..k, exactly in rational arithmetic; on a family with k = 6 and every item
matched by two rules, the counted totals equal m·d(2) + R₁ and m·v(2) + R₂ exactly, and their quotient approaches
f(2) = 89/4 for m = 12, 192, 3072). Part (a) rests on the bounds of 5.2 and 11.7, whose computable facts are checked
there.
