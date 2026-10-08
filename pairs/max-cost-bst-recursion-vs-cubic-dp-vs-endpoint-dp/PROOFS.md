# Proofs: maximum-cost BST and inclusion-monotone interval DP, plain recursion vs cubic DP vs endpoint DP

This file, together with the proofs in the entry's `README.md` that section 5 indexes, proves every claim that this
entry makes (in `entry.json`, `README.md` and the docstrings of the code). Sections 1–4 prove the exact operation
counts for every size of their domain. Section 5 lists where each theorem is proved in the README and proves the
remaining claims: the correspondence with triangulations, the characterisation of BST weights as separable tables,
the size of the numbers, and the time and space bounds. Each proof is followed by the deterministic scripts that
check it and the sizes they check it on. A check covers only those sizes; the proofs cover the whole domain.

## Counting convention

`harness.py`, class `CountingInt`: `__lt__`, `__le__`, `__gt__` and `__ge__` each call `_cmp`, which adds 1 to the
module counter `_comparisons` (`_comparisons += 1`) and compares the wrapped values; `__add__` (also bound as
`__radd__`) adds 1 to `_additions` and returns a new `CountingInt`. `__neg__` returns a new `CountingInt` without
counting; `__eq__`, `__hash__` and the constructor count nothing. `generate_scaling(n, rng)` draws a family from
`SCALING_FAMILIES` (29 integer families: the 14 BST families in the form (p, q), the general monotone families
except `g_rational` and `g_product` in the form ("max", w), and the anti-monotone families except `a_reciprocal` in
the form ("min", w)), builds the instance with `instance_of`, replaces every number by a `CountingInt`
(`wrap_counting`; the unused entries w[i][j], j ≤ i, stay `None`) and then calls `reset_counters()`;
`reported_cost(output)` returns `_comparisons`. The additions in `caveats` are `_additions` after the same call.

An addition with at least one `CountingInt` operand counts 1 and returns a `CountingInt` (with a plain left operand,
`int.__add__` returns `NotImplemented` and Python calls `__radd__`); `0 + 0` on plain ints counts nothing. A
comparison whose left operand is a `CountingInt` counts 1. Not counted: indices and `range` bounds, `i == j`,
`best is None` (an identity test), `first == "max"` and the plain bool `maximise`.

**The two forms.** Each implementation first calls its own copy of `_interval_weights(instance)`. In the table form
(sense, w) it returns `first == "max"`, n = len(w) − 1 and w itself, with no arithmetic. In the BST form (p, q) it
returns `True`, n = len(p) and the table built row by row with `acc = q[i]` and `acc = acc + p[j - 1] + q[j]` for
j = i + 1..n: 2 counted additions per pair i < j, n(n + 1) in all, and every w[i][j] (i < j) is a `CountingInt`.
The test `(cand > best if maximise else cand < best)` evaluates exactly one of its two comparisons.

**Every input** below means every instance in either form whose numbers are all `CountingInt`: any values (integers
or fractions, any signs), either sense, whether or not the precondition of the endpoint DP holds. The interval
(i, j), 0 ≤ i ≤ j ≤ n, holds the nodes i + 1..j and has length L = j − i.

**Two facts used in every section.** (i) *Values.* The empty interval has the plain value 0 (`return 0`,
`c[i][i] = 0`), and every non-empty interval has a `CountingInt` value, since w[i][j] (i < j) is one in both
forms: `w[i][j] + best` in all three implementations, and `c[i][i + 1] = w[i][i + 1]` in `maxbst_endpoint`. So for L ≥ 2 every candidate
`cand = c(i, k − 1) + c(k, j)` has a non-empty side (k − 1 > i or k < j): it is one counted addition and a
`CountingInt`. For L = 1 the only candidate of the recursion and the cubic DP is `0 + 0`, a plain int, uncounted.
(ii) *Running optimum.* An interval loops over its candidates; for the first, `best is None` is true and `or`
short-circuits, so there is no comparison; each later candidate evaluates one comparison of `cand`, a `CountingInt`
(L ≥ 2), with `best`: exactly 1. So an interval with t ≥ 1 candidates makes t − 1 comparisons. The outcome of a
comparison only selects which value is stored, never the loop structure, so no count below depends on the values or
the sense.

## 1. Plain recursion: 3ⁿ calls, (3^(n−1) − 1)/2 comparisons

**Statement.** On every input, `maxbst_recursive` calls its inner function `cost` exactly 3ⁿ times for every
n ≥ 0, and makes exactly (3^(n−1) − 1)/2 comparisons for every n ≥ 1 (0 for n = 0, where the formula gives −1/3),
in both forms and both senses.

**Proof.** The recurrences and their solutions are given in `entry.json`, field `algorithms[0].correctness`
("Count (read off the code)"). The steps it leaves out: a call `cost(i, j)` with i = j returns the plain 0 at once
(1 call, no comparison). A call with L = j − i ≥ 1 calls `cost(i, k − 1)` and `cost(k, j)` for k = i + 1..j, of
lengths k − 1 − i and j − k, each of which runs over 0..L − 1 as k does. It makes L − 1 comparisons itself (fact
(ii); for L = 1 there is one candidate), and `_interval_weights` makes none. So with K(0) = 1, C(0) = 0:
K(L) = 1 + 2 Σ_{t<L} K(t) and C(L) = (L − 1) + 2 Σ_{t<L} C(t) for L ≥ 1.
Then K(1) = 3 and C(1) = 0; for L ≥ 2, subtracting the identity for L − 1 gives K(L) = 3K(L − 1) and
C(L) = 3C(L − 1) + 1. Hence K(L) = 3^L, and C(L) = (3^(L−1) − 1)/2 by induction
(3(3^(L−2) − 1)/2 + 1 = (3^(L−1) − 1)/2). The top call `cost(0, n)` gives the statement.

**Check.** At the V2 sizes n = 5..11: `experiments/2026-10-07_max_cost_bst_checks.py`, section N (comparisons and
calls; n = 0..9 on all 32 families, n = 10..12 on the families `small`, `g_submax` and `a_neg_submax`).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "maxBST recursion (3^(n-1)-1)/2": n = 0..11,
one instance per n drawn by `generate_scaling` with the V2 seeds (n = 0 reported as outside the domain); line
"maxBST recursion: 3^n calls of cost()": n = 0..10 on the families `g_submax`, `g_subsum`, `g_length`, `bits`,
`small`, `zero`. `experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "max-cost: comparisons and
additions (table form; BST form + n(n+1)) on inputs outside the precondition": n = 0..9; line "max-cost recursion:
3^n calls on inputs outside the precondition": n = 0..9 (both on iid tables under max and under min, signed BST
frequencies, monotone tables under min and anti-monotone tables under max, 2 instances each).

## 2. Cubic DP: (n + 1)n(n − 1)/6 comparisons, n(n + 1)(n + 2)/6 candidate roots

**Statement.** On every input and for every n ≥ 0, in both forms and both senses, `maxbst_cubic` evaluates exactly
n(n + 1)(n + 2)/6 candidate roots (executions of `cand = c[i][k - 1] + c[k][j]`, uncounted loop work) and makes
exactly (n + 1)n(n − 1)/6 = C(n + 1, 3) comparisons.

**Proof.** Given in `entry.json`, field `algorithms[1].correctness` (L − 1 comparisons per interval of length L,
summed to C(n + 1, 3)), and in the docstring of `cubic_dp.py`. The missing steps: there are n − L + 1 intervals of
length L; each tries k = i + 1..j, that is L candidates, and makes L − 1 comparisons by fact (ii). With m = L − 1:
Σ_{m=0..n−1} (n − m)m = n · n(n − 1)/2 − (n − 1)n(2n − 1)/6 = (n + 1)n(n − 1)/6, and
Σ_{m=0..n−1} (n − m)(m + 1) = (n + 1)n(n − 1)/6 + n(n + 1)/2 = n(n + 1)(n + 2)/6. For n = 0 there is no interval
and both counts are 0.

**Check.** At the V2 sizes n = 16, 32: `experiments/2026-10-07_max_cost_bst_checks.py`, section N (n = 0..40 on
all 32 families, n = 41..60 on `small`, `g_submax` and `a_neg_submax`); the validator run in the same section prints
the counts at all four V2 sizes, 680, 5456, 43680 and 349504, the closed form at n = 16, 32, 64, 128.
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "maxBST cubic
(n+1)n(n-1)/6": n = 0..40, 64, 128 (one instance per n drawn by `generate_scaling` with the V2 seeds; all V2 sizes);
group `extra`, line "max cubic DP candidate roots n(n+1)(n+2)/6 (uncounted)": n = 0..24, one instance per n.
`experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "max-cost cubic DP candidate roots
n(n+1)(n+2)/6 (uncounted)": n = 0..16 on all 32 families; line "max-cost: comparisons and additions (table form;
BST form + n(n+1)) on inputs outside the precondition": n = 0..30.

## 3. Endpoint DP: n(n − 1)/2 comparisons, two candidates per interval

**Statement.** On every input and for every n ≥ 0, in both forms and both senses, `maxbst_endpoint` evaluates
exactly 2 candidates for each interval of length L ≥ 2 and none for the intervals of length 1, and makes exactly
n(n − 1)/2 comparisons, one per interval of length ≥ 2.

**Proof.** Given in `entry.json`, field `algorithms[2].correctness` ("Count: one comparison per interval of length
>= 2"), and in the docstring of `endpoint_dp.py`. The missing steps: the length-1 loop only stores
`c[i][i + 1] = w[i][i + 1]`. For L ≥ 2 the loop runs over the tuple `(i + 1, j)`, whose two entries differ; the
first candidate sets `best`, and the second, `c[i][j - 1] + c[j][j]` with (i, j − 1) non-empty, is a `CountingInt`
and is compared once (fact (ii)). There are n − L + 1 intervals of length L, and
Σ_{L=2..n} (n − L + 1) = Σ_{t=1..n−1} t = n(n − 1)/2 (0 for n ≤ 1).

**Check.** At the V2 sizes n = 32, 64, 128, 256, 512: `experiments/2026-10-07_max_cost_bst_checks.py`, section N
(n = 0..80 on all 32 families, and n = 100, 128, 150, 200, 256, 512 on `small`, `g_submax` and `a_neg_submax`).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "maxBST endpoint n(n-1)/2": n = 0..60, 64,
128, 256, 512 (one instance per n drawn by `generate_scaling` with the V2 seeds).
`experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "max-cost endpoint DP: exactly 2 candidates per
interval of length L >= 2 (uncounted)": n = 0..16 on all 32 families, every L; line "max-cost: comparisons and
additions (table form; BST form + n(n+1)) on inputs outside the precondition": n = 0..60.

## 4. Additions (caveats)

**Statement.** On every input in the table form, for both senses: `maxbst_recursive` makes exactly
(11 · 3^(n−2) − 1)/2 additions for every n ≥ 2 (1 for n = 1, 0 for n = 0); `maxbst_cubic` makes exactly
n(n + 1)(n + 2)/6 − n + n(n + 1)/2 for every n ≥ 0; `maxbst_endpoint` makes exactly 3n(n − 1)/2 for every n ≥ 0.
In the BST form each implementation makes n(n + 1) more, all of them in `_interval_weights` while tabulating w.

**Proof.** *Tabulating w.* Shown under "The two forms": n(n + 1) additions in the BST form, none in the table form,
before the DP starts. The rest of each implementation is the same in both forms.

*Recursion.* A call with L ≥ 2 adds its L candidates (fact (i)) and computes `w[i][j] + best` (1): L + 1 in its
own frame. A call with L = 1 has the uncounted candidate `0 + 0` and computes `w[i][j] + 0` (1, left operand a
`CountingInt`). A call with L = 0 adds nothing. So A(0) = 0, A(1) = 1, and A(L) = L + 1 + 2 Σ_{t<L} A(t) for L ≥ 2
(the children as in section 1). Thus A(2) = 3 + 2 · 1 = 5, and for L ≥ 3 subtracting the identity for L − 1 gives
A(L) = 3A(L − 1) + 1, i.e. A(L) + 1/2 = 3^(L−2) (A(2) + 1/2) = 11 · 3^(L−2)/2. (At L = 1 the form would give 4/3.)

*Cubic DP.* Every interval computes `w[i][j] + best` (1); an interval of length L ≥ 2 also adds its L candidates.
Total n(n + 1)/2 + Σ_{L=2..n} (n − L + 1)L = n(n + 1)/2 + n(n + 1)(n + 2)/6 − n (section 2, minus the n candidates
of length 1).

*Endpoint DP.* The length-1 loop adds nothing. An interval of length ≥ 2 adds its 2 candidates and computes
`w[i][j] + best`: 3. Total 3n(n − 1)/2 (section 3).

**Check.** `experiments/2026-10-07_max_cost_bst_checks.py`, section N: the additions, with n(n + 1) more in the BST
form; recursion n = 0..9, cubic DP n = 0..40 and endpoint DP n = 0..80 on all 32 families, and recursion
n = 10..12, cubic DP n = 41..60 and endpoint DP n = 100, 128, 150, 200, 256, 512 on `small`, `g_submax` and
`a_neg_submax`.
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "maxBST additions: (11*3^(n-2)-1)/2 rec
(n>=2), cubic n(n+1)(n+2)/6-n+n(n+1)/2, endpoint 3n(n-1)/2; BST form + n(n+1)": n = 0..10 (recursion n = 2..10)
on the families `g_submax`, `g_subsum`, `g_length`, `bits`, `small`, `zero`.
`experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "max-cost additions split: _interval_weights
n(n+1) (BST form) / 0 (table form), DP part = table-form closed form": n = 0..20 (recursion n = 0..8) on all 32
families; line "max-cost: comparisons and additions (table form; BST form + n(n+1)) on inputs outside the
precondition": recursion n = 0..9, cubic DP n = 0..30, endpoint DP n = 0..60.

## 5. Correctness, the theorems and the other claims

The entry's theorems are proved in its `README.md`; this section says where, checks that every claim is covered,
and proves the claims that the README states without proof. Machine-model assumptions (not proved here): list
allocation of length t costs Θ(t + 1), indexing and `append` (amortised) cost O(1), a Python call costs O(1), and
arithmetic and comparisons of the weights count as unit operations (as in `input.size_measure`). The statements in the entry's `background` field (the
content of Qian and Wang's Lemma 1 and of its exchange argument) are cited, not proved; the README's own proof of
Theorem E′ does not use them.

### 5.1 Where each theorem is proved

| Claim (location) | Proof |
|---|---|
| c(0, n) is the optimum over all binary trees of Σ_v w(I_v), in either direction (`problem_statement`, `algorithms[0].correctness`) | README, Lemma A (the min form by negation, Corollary 1) |
| the BST cost is Σ_v w(I_v) with w(i, j) = q_i + Σ_{l=i+1..j} (p_l + q_l) (`problem_statement`) | README, "Lemma (cost as a sum over nodes)" |
| the cost is the weighted number of key comparisons (`problem_statement`, README "Main instance") | a search compares the searched value with every key on its root path: level + 1 comparisons for a key, level for a gap (written out in the optimal-BST entry's PROOFS.md, section 6) |
| plain recursion and cubic DP correct for any weights and either direction | README Lemma A; the cubic DP fills every interval after its subintervals |
| rotation changes Δ_R, Δ_L | README, Lemma B |
| Δ_R + Δ_L ≥ 0 for monotone weights (the only use of monotonicity) | README, Lemma C |
| Theorem E′ (a)–(c): an optimal path tree, an endpoint maximiser, the endpoint recurrence; the endpoint DP is correct under the precondition (`algorithms[2].correctness`, `relationship`) | README, Theorem E′ (Claim and induction) |
| the min form with anti-monotone weights | README, Corollary 1 |
| strict monotonicity: every optimal root is an endpoint, every optimal tree a path (`notes`) | README, Corollary 2 |
| monotone ⇔ the local inequalities; the harness tests it in O(n²) | README, Remark (a local test) |
| BST weights are monotone ⇔ q_{l−1} + p_l ≥ 0 (l = 1..n − 1) and p_l + q_l ≥ 0 (l = 2..n); in particular for p, q ≥ 0 (`caveats`, `algorithms[2].correctness`) | README, "When BST weights are monotone" |
| Theorem E (the maximum-cost BST with p, q ≥ 0) | README, Corollary (Theorem E) |
| positive key frequencies (or strict adjacent sums): every maximising root is an endpoint (`notes`) | README, Corollary (positive key frequencies) |
| entries −∞ (monotone in the extended order): the endpoint recurrence is exact in (max, +); the mirror for +∞ under min (negate, as in Corollary 1); +∞ under max not covered (`caveats`, `verification.proofs`); for +∞ entries without −∞ entries a pointer to the theorem note endpoint-law-split-dependent-weights (`caveats`, README) | README, "Extension to −∞ entries"; the pointer's statement (the endpoint recurrence gives c on every interval, and every interval has an optimal path tree) is the note's Proposition 8, proved in that note |
| no failure is possible for n ≤ 2 (README, counterexamples) | every root of an interval with at most 2 nodes is an endpoint |
| exact comparison counts, calls, additions | sections 1–4 |

The counterexamples, controls and exhaustive counts in `caveats`, `verification.method` and the README are finite
computations, reproduced by `experiments/2026-10-07_max_cost_bst_checks.py` (sections B, C, E1–E5, O, N) and partly
by `tests/test_entry_max_cost_bst.py`; the "smallest counterexample" statements are scoped to the n = 3 tables with
values 0..2 ordered by the sum of their entries, which is exactly what the script searches.

### 5.2 The correspondence with triangulations (README "Source", `sources[0].note`)

**Proposition 5.1.** For 0 ≤ i ≤ j, the binary trees on the interval (i, j) (nodes i + 1..j) correspond one to one
to the triangulations of the convex polygon with the vertices v_i, v_{i+1}, …, v_{j+1} (for i = j: the single edge
v_i v_{i+1}, no triangle). Under this correspondence, a node k whose subtree spans (lo, hi) is the triangle
v_lo v_k v_{hi+1} with base chord v_lo v_{hi+1}, and a right rotation at a node is a diagonal flip. For i = 0,
j = n, the n − 1 diagonals of the triangulation are exactly the base chords of the n − 1 non-root nodes, so for
chord weights ω and w(lo, hi) = ω(v_lo v_{hi+1}), Σ_v w(I_v) = Σ_{diagonals} ω + ω(v_0 v_{n+1}): the value of a tree
and the weight of its triangulation (diagonals only, or diagonals plus the fixed sides) differ by a constant.

*Proof.* Induction on j − i. For j > i, every triangulation of the polygon v_i..v_{j+1} has exactly one triangle on
the side v_i v_{j+1}; its apex is some v_k with i < k ≤ j, and it splits the polygon into the polygons v_i..v_k and
v_k..v_{j+1}, which are triangulated independently. A tree on (i, j) is a root k with independent subtrees on
(i, k − 1) and (k, j), whose polygons are v_i..v_{(k−1)+1} = v_i..v_k and v_k..v_{j+1}. Matching the root with the
triangle v_i v_k v_{j+1} and recursing gives the bijection and the description of the triangles. The diagonals: the
base chord of a non-root node spanning (lo, hi) joins v_lo and v_{hi+1} with hi + 1 − lo ≥ 2 and (lo, hi) ≠ (0, n),
so it is a diagonal; distinct nodes span distinct intervals, and a triangulation of an (n + 2)-gon has n − 1
diagonals, so these are all of them; the root's base chord v_0 v_{n+1} is a side. Rotation: let k span (lo, hi)
with left child k_L spanning (lo, k − 1). Their triangles v_lo v_k v_{hi+1} and v_lo v_{k_L} v_k form the
quadrilateral v_lo v_{k_L} v_k v_{hi+1} with diagonal v_lo v_k. After the right rotation, k_L spans (lo, hi) and k
spans (k_L, hi): the triangles v_lo v_{k_L} v_{hi+1} and v_{k_L} v_k v_{hi+1}, the same quadrilateral with the other
diagonal v_{k_L} v_{hi+1}; no other node changes its interval (README, Lemma B). ∎

In the triangulation picture, monotonicity under inclusion says that a chord v_b v_{c+1} nested inside v_a v_{d+1}
(a ≤ b < c ≤ d) weighs at most as much as the outer one.

**Check.** `tests/test_proofs_maxbst.py`, `test_triangulation_correspondence`: for n = 0..7, the map from trees to
diagonal sets is injective onto all triangulations (Catalan(n) of them, compared with a separate enumeration of
triangulations), Σ_v w(I_v) = Σ_{diagonals} ω + ω(v_0 v_{n+1}) for random chord weights (seed 1), and every right
rotation at every node with a left child changes exactly one diagonal, v_lo v_k → v_{k_L} v_{hi+1}.

### 5.3 BST weights are exactly the separable tables (README, "Verification")

**Proposition 5.2.** A table w(i, j), 0 ≤ i < j ≤ n, is the table of BST weights of some (signed) frequencies
p_1..p_n, q_0..q_n if and only if w(i, j) = F(j) − G(i) for some F, G. The table is of this form if and only if
w(a, c) + w(b, d) = w(a, d) + w(b, c) for all a < b < c < d (the test the checks script uses).

*Proof.* BST weights: w(i, j) = F(j) − G(i) with F(j) = Σ_{l≤j} (p_l + q_l) and G(i) = F(i) − q_i. Conversely, given
F (on 1..n) and G (on 0..n − 1), put q_0 = −G(0), q_i = F(i) − G(i) for 1 ≤ i ≤ n − 1, q_n = 0, p_1 = F(1) − q_1 and
p_j = F(j) − F(j − 1) − q_j for 2 ≤ j ≤ n. Then Σ_{l≤j} (p_l + q_l) = F(j) for j ≥ 1 (telescoping), and
F(i) − q_i = G(i) for 1 ≤ i ≤ n − 1, while 0 − q_0 = G(0); so the BST weights of (p, q) are F(j) − G(i). For the
second statement, "only if" is immediate. "If": for rows i < i′ the difference w(i, j) − w(i′, j) does not depend on
j > i′ (the condition with a = i, b = i′ and two values c < d of j); call it D(i, i′). Put G(0) = 0,
G(i + 1) = G(i) + D(i, i + 1) for i ≤ n − 2, and F(j) = w(i, j) + G(i), which does not depend on i < j because
w(i, j) + G(i) = w(i + 1, j) + G(i + 1) for i + 1 < j. ∎

**Check.** `tests/test_proofs_maxbst.py`, `test_separable_tables`: the construction reproduces 300 random separable
tables (n = 0..9, seed 2) as BST weights; the four-point test accepts every BST table and agrees with the existence
of F, G (computed as in the proof) on 300 random integer tables, separable or not (seed 3).

### 5.4 The size of the numbers (`input.size_measure`)

In the BST form with p, q ≥ 0 and S = Σ p_m + Σ q_g, a BST on n keys has key levels ≤ n − 1 and gap levels ≤ n, so
every cost is at most n·S ≤ (n + 1)·S. Every value the implementations compute lies in [0, n·S] for n ≥ 1: each
w(i, j) ≤ S; a tree on (i, j) has j − i nodes, each with an interval inside (i, j), so its value is at most
(j − i) w(i, j) by monotonicity, and so are c(i, j) and every candidate. So the numbers need only O(log n) more bits
than the input numbers.

**Check.** `tests/test_proofs_maxbst.py`, `test_size_of_numbers`: on 200 BST instances from the 14 BST families,
n = 1..40 (seed 4), every entry of the cubic DP's table lies in [0, n·S], and for n ≤ 7 the largest cost over all
tree shapes is at most n·S.

### 5.5 Time and space

*Plain recursion.* Section 1 gives exactly 3ⁿ calls; a call of length L does O(1 + L) work (L candidates). The sum of
the lengths over all calls is Λ(n) with Λ(0) = 0, Λ(L) = L + 2 Σ_{t<L} Λ(t), i.e. Λ(L) = (3^L − 1)/2. With the
Θ(n²) tabulation in the BST form, the time is Θ(3ⁿ). The length decreases by at least 1 from a call to its callee,
and the chain cost(0, n) → cost(1, n) → … → cost(n, n) (first root k = i + 1) has n + 1 calls: the nesting depth is
n + 1. The weight table has (n + 1)² entries in the BST form; in the table form it is the input itself, with
n(n + 1)/2 weights. So the space is Θ(n²) for the table and Θ(n) for the recursion.

*Cubic DP and endpoint DP.* Sections 2 and 3 give n(n + 1)(n + 2)/6 and 2·n(n − 1)/2 candidates; each allocates the
(n + 1)² table c (and, in the BST form, the (n + 1)² table w). So the cubic DP takes Θ(n³) time and the endpoint DP
Θ(n²) time on every input, both with Θ(n²) space. Θ(n²) is the cost of the endpoint DP, not a lower bound for the
problem (no lower bound is claimed).

**Check.** `tests/test_proofs_maxbst.py`, `test_time_and_space`: the nesting depth of `cost` is n + 1 and the sum of
the interval lengths over its calls is (3ⁿ − 1)/2 (profiler hook), n = 0..9; the table c of both DPs (and w in the
BST form) has n + 1 rows of length n + 1 at return, n = 0..40, in both forms (seed 5).

### 5.6 The separations (T2, T3)

All three implementations return c(0, n) under the precondition (the recursion and the cubic DP on every input;
§5.1). T2: Θ(3ⁿ) for the recursion against Θ(n³) for the cubic DP (§5.5). T3: Θ(n³) against Θ(n²) for the endpoint
DP, by Theorem E′.
