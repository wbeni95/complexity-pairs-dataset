# Proofs: assignment problem, permutation enumeration vs the Hungarian method

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code), from
the code in this folder: correctness, exact counts and space of the enumeration (section 1), correctness, the O(n³)
worst-case bound and space of the Hungarian implementation (sections 2–4), the separation (section 5) and the
maximisation remark (section 6). Each proof is followed by the deterministic tests or scripts that check it and the
sizes they check it on; a check covers only those sizes, the proofs cover every n. Section 7 lists the statements
that are measured data, not theorems. The statements listed under "Background" in `entry.json` are cited, not proved
here.

**Cost model.** Entries are integers of bounded size in the harness, so each arithmetic operation, comparison, index
operation and list operation costs Θ(1). The enumeration calls the standard-library generator
`itertools.permutations`; what it is assumed to do is stated as a machine-model assumption in section 1 and in the
`background` of `entry.json`.

## 1. Enumeration: correctness, n! permutations, n·n! matrix reads, Θ(n·n!) time, Θ(n) space

**Machine-model assumption (background).** CPython's `itertools.permutations(range(n))` behaves like the "roughly
equivalent" Python code given in its documentation: it yields every permutation of `range(n)` exactly once, as
n-tuples in lexicographic order (this is its documented behaviour), it does O(n·n!) work in total over the whole run,
and it keeps O(n) words of state. Lemma 1.1 proves the two cost properties for the documented code; that the C
implementation has the same costs is assumed, not proved.

**Lemma 1.1 (the documented code).** Run the documented generator with r = n ≥ 0 to the end. Its `for` loop body
runs exactly Σ_{k=0}^{n−1} n!/k! ≤ e·n! times in total; the rotations `indices[i:] = indices[i+1:] + indices[i:i+1]`
move Σ_{k=0}^{n−1} n!/k! ≤ e·n! entries in total; it yields n! tuples of n entries each. So its total work is
O(n·n!), that is amortised O(n) per permutation, although a single step can rotate Σ_i (n − i) = Θ(n²) entries. Its
state is `pool`, `indices` and `cycles` (n entries each) and the tuple being built: O(n) words.
*Proof.* For n = 0 the code yields the empty tuple and stops (the `while n` loop does not run); all sums are empty.
Let n ≥ 1. After the first yield, each pass of the `while` loop runs the `for` loop over i = n − 1, n − 2, …: it
decrements `cycles[i]`; if that reaches 0 the entry is reset to n − i (a *rollover*) and the loop goes on to i − 1,
otherwise it yields and breaks; if every entry rolls over, the `else` branch returns. So `cycles` is a counter whose
digit i counts down through n − i values. Let D_i and R_i be the numbers of decrements and rollovers of digit i over
the whole run. The run ends in the pass in which digit 0 rolls over, which is its n-th decrement (it starts at n):
D_0 = n and R_0 = 1. Digit i is decremented exactly in the passes where digit i + 1 rolls over, so D_i = R_{i+1}; in
the last pass every digit rolls over, so the decrements of every digit end with a rollover, and
D_{i+1} = (n − i − 1)·R_{i+1} = (n − i − 1)·D_i. Hence D_i = n!/(n − i − 1)! and R_i = n!/(n − i)!. Digit n − 1 is
decremented in every pass, so there are D_{n−1} = n! passes: n! − 1 that yield, and the last one, in which the
generator returns. The number of `for` iterations is Σ_i n!/(n − i − 1)! = Σ_{k=0}^{n−1} n!/k!; a rollover of
digit i rotates n − i entries, so the rotations move Σ_i (n − i)·n!/(n − i)! = Σ_{k=0}^{n−1} n!/k! entries; and
Σ_k 1/k! ≤ e. Each of the n! yields builds an n-tuple from `indices[:n]`.

**Statement.** `assignment_brute` returns the minimum of Σ_i C[i][π(i)] over all permutations π (0 for n = 0). On
every n × n input it costs exactly n! permutations and reads exactly n·n! matrix entries (n per permutation). Its
time is Ω(n·n!) on every input, unconditionally, and Θ(n·n!) under the assumption above. Besides the input it holds
Θ(n) words under the assumption: the current permutation tuple (n slots) and the generator's O(n) state.

**Proof.** The loop runs once for every tuple `perm` produced by `permutations(range(n))`, which (assumption) is
every permutation of 0..n − 1 exactly once (n! of them; for n = 0 the single empty tuple). For each,
`sum(C[i][perm[i]] for i in range(n))` reads the n entries C[i][perm[i]] (n row reads `C[i]` and n entry reads) and
computes the cost of that assignment; `best` keeps the minimum (`best is None` only before the first permutation). So
the result is the minimum over all permutations, every perfect matching of K_{n,n} being one, and the read counts
are n·n!. The cost evaluations take Θ(n) time each, Θ(n·n!) in all; this is a lower bound on the running time that
does not depend on the generator's cost. With the generator's O(n·n!) total work (assumption, Lemma 1.1 for the
documented code) the total is Θ(n·n!). Space: the locals are `n`, `best`, `cost` (integers) and `perm`, an n-tuple;
the generator expression holds no container; the generator object holds O(n) words of state (assumption).

**Check.** `tests/test_proofs_assignment.py`, `test_enumeration_counts` (n = 0..8, one seeded matrix each: the result
equals the subset DP of `harness.py`, exactly n·n! row reads and n·n! entry reads, and `permutations(range(n))` yields
n! distinct tuples), `test_documented_permutations_code` (n = 0..8: the documented code, run with counters, yields
exactly the tuples of `itertools.permutations(range(n))` in the same order, its `for` iterations and rotated entries
both equal Σ_{k=0}^{n−1} n!/k!, and the largest work of one step is n(n + 1)/2 rotated entries plus n iterations)
and `test_space` (n = 0..6: the instrumented peak of `tests/proof_space.py`, container slots bound to local
variables, equals n). The V1 battery compares both implementations for n = 0..8.

## 2. The Hungarian implementation: notation and invariants

Rows are x = 1..n (row x is `C[x - 1]`), columns are y = 1..n (column y is entry `y - 1` of a row), and column 0 is a
sentinel; `match[y]` is the row of column y (0 = free). An *iteration* is one execution of the body of `while True`.
During the search for row i, `match[0] = i`; for a column c that is 0 or matched, write x_c = `match[c]`. Let u⁰, v⁰
be the potentials when the search for row i starts, and r(x, y) = C[x][y] − u⁰[x] − v⁰[y] the reduced cost.

**Invariants before the search for row i.**
- (J1) r(x, y) ≥ 0 for every row x < i and every column y;
- (J2) r(match[y], y) = 0 for every matched column y;
- (J3) exactly i − 1 columns are matched, to the rows 1..i − 1, one each; u⁰[x] = 0 for every x ≥ i.

They hold for i = 1 (all potentials 0, nothing matched).

**Lemma H0 (iterations; every input).** The search for row i runs at most i iterations; iteration t evaluates `cur`
exactly n − t + 1 times. Hence at most n(n + 1)/2 iterations and at most n(n + 1)(2n + 1)/6 reduced-cost
evaluations in all, and O(n³) time on every input.

*Proof.* Iteration t marks `j0` as used (the column selected by iteration t − 1, or 0 for t = 1) and runs the first
loop over the unused columns 1..n. In iteration 1 every `minv[j]` (j ≥ 1) is `INF` and becomes the finite `cur`, so
`delta` is finite and `j1` ≥ 1 is set; later `minv` values stay finite. So each iteration selects an unused column
`j1`; if it is free the loop ends before it is marked, otherwise it is marked used in the next iteration. The columns
selected by iterations 1..t − 1 are therefore distinct matched columns, and by (J3) only i − 1 columns are matched:
t ≤ i. In iteration t the used real columns are those t − 1, so `cur` is evaluated for the n − t + 1 unused ones, and
the second loop runs n + 1 times. Summing, Σ_{i=1..n} Σ_{t=1..i} (n − t + 1) = Σ_{s=1..n} s² = n(n + 1)(2n + 1)/6
evaluations and Σ_i i = n(n + 1)/2 iterations. Each iteration costs Θ(n); the augmentation walk visits distinct
columns (Lemma H1(e)), at most i + 1 per row; allocating `minv` and `used` costs Θ(n) per row and the final sum
Θ(n). Total O(n³).

**Lemma H1 (the search keeps Dijkstra's labels).** Let Δ_t be the sum of the `delta` values of iterations
1..t − 1 (Δ_1 = 0). Give each column its *label* when it is selected: λ(0) = 0, and λ(c) = Δ_{s+1} if c is selected by
iteration s. At the start of iteration t, with j0 the column it marks:
- (a) every used column c has u[x_c] = u⁰[x_c] + (Δ_t − λ(c)) and v[c] = v⁰[c] − (Δ_t − λ(c));
- (b) every unused column j ≥ 1 has v[j] = v⁰[j], and for t ≥ 2 its *tentative label* minv[j] + Δ_t equals
  min over used c of (λ(c) + r(x_c, j)), attained by c = way[j];
- (c) j0 is unused, λ(j0) = Δ_t, and u[x_{j0}] = u⁰[x_{j0}].

Consequences: (d) tentative labels never increase, and the label of the selected column is the minimum tentative
label (after the first loop of its iteration), with the smallest index among ties; (e) way[j] is a column marked
before j was selected (in iteration 1 every unused j gets way[j] = 0, so no value from an earlier row survives), so
following `way` from any selected column reaches 0 through distinct columns; (f) the labels of the columns selected by
iterations 1, 2, … are non-decreasing (λ(0) = 0 may exceed the first of them, since the first `delta` can be
negative).

*Proof.* Induction on t. For t = 1 nothing is used, j0 = 0, x_0 = i and u[i] = 0 = u⁰[i] by (J3). In iteration t, j0
becomes used; (a) holds for it because Δ_t − λ(j0) = 0, by (b) and (c) (for c = 0 the value v[0] plays no role
elsewhere). For every unused j, `cur` = C[x_{j0}][j] − u[x_{j0}] − v[j] = r(x_{j0}, j), and `if cur < minv[j]`
replaces minv[j] by cur and way[j] by j0; so minv[j] + Δ_t becomes min(old value, λ(j0) + r(x_{j0}, j)), which is (b)
with j0 added (for t = 1 it is λ(0) + r(i, j)). Then `delta` is the minimum of `minv` over the unused columns and `j1`
the smallest index attaining it (the test `minv[j] < delta` runs over ascending j). The second loop adds `delta` to
u[x_c] and subtracts it from v[c] for used c, and subtracts it from minv[j] for unused j: this is (a) and (b) with
Δ_{t+1} = Δ_t + delta, and λ(j1) = Δ_{t+1} is the minimum tentative label. If `j1` is matched, its row x_{j1} ≠ i
belongs to no used column, so its potential was never shifted in this search: (c) for t + 1.
(d) and (e) follow from (b) and the selection rule. (f): after the second loop of iteration t − 1 every unused
minv[j] is ≥ 0 (delta was their minimum); in iteration t ≥ 2 the new values are cur = r(x_{j0}, j) ≥ 0 by (J1),
since j0 ≠ 0 is matched to a row < i; so delta ≥ 0 from iteration 2 on.

**Lemma H1′ (a cheapest augmenting path).** Let D_i be the digraph on the columns 0..n with an arc c → j of length
r(x_c, j) for every c that is 0 or matched and every column j ≥ 1, j ≠ c (free columns have no outgoing arcs). Every
selected column c has λ(c) = dist_{D_i}(0, c), and the final (free) column j* has λ(j*) = min over free columns f of
dist_{D_i}(0, f). The way-chain j*, way[j*], …, 0 read backwards corresponds to an augmenting path from row i
(row i, its column, the row matched to that column, …, ending at the free column j*) whose reduced cost (the sum of r
over its non-matching edges; matching edges have r = 0 by (J2)) is minimal among all augmenting paths from row i.

*Proof.* Arcs out of matched columns have length ≥ 0 by (J1); no arc enters 0, so every path from 0 starts with
exactly one arc out of 0, and adding the same constant K to all arcs out of 0 shifts every path length and every
tentative and final label by K without changing any selection. Choose K so that all arcs are ≥ 0. Then the usual
Dijkstra argument applies: by (b), λ(c) is the length of the path given by the way-chain, so λ(c) ≥ dist(0, c);
conversely, a shortest 0–c path leaves the set of columns marked before c's selection at a first column j′ (the
column before j′, call it p, was marked and, by induction, λ(p) = dist(0, p)), and then
λ(c) ≤ minv[j′] + Δ ≤ λ(p) + r(x_p, j′) ≤ dist(0, c) by (d), (b) and the non-negative arc lengths. The same
argument with any free column f in place of c gives λ(j*) ≤ dist(0, f). An augmenting path from row i alternates
non-matching and matching edges and corresponds exactly to a path in D_i from 0 to a free column, of the same
reduced cost.

**Lemma H2 (one search keeps the invariants).** After the search for row i and its augmentation, (J1)–(J3) hold
for i + 1, and every matched pair is tight.

*Proof.* Let j* be the final column and Λ = λ(j*) (the value of Δ after the last second loop; j* is selected but
never marked). By (a), the new potentials are u′[x_c] = u⁰[x_c] + (Λ − λ(c)) and v′[c] = v⁰[c] − (Λ − λ(c)) for every
used column c; all other potentials are unchanged, in particular v′[j] = v⁰[j] for unused j (j* included). Call a
row *reached* if it is x_c for a used column c = c_x (row i is reached through column 0). For a row x ≤ i and a
column y, r′(x, y) = C[x][y] − u′[x] − v′[y] is:
- x reached, y used (y ≥ 1): r′ = r(x, y) + λ(c_x) − λ(y). If c_x was marked before y was selected (always when
  c_x = 0), then by (b) and (d) λ(y) ≤ λ(c_x) + r(x, y). If y was selected before c_x, then λ(y) ≤ λ(c_x) by (f) and
  r(x, y) ≥ 0 by (J1) (x < i). If y = c_x, r(x, y) = 0 by (J2). So r′ ≥ 0.
- x reached, y unused: r′ = r(x, y) − (Λ − λ(c_x)). The final tentative label of y is ≤ λ(c_x) + r(x, y) by (b), and
  Λ is at most every final tentative label (d). So r′ ≥ 0.
- x not reached (so x < i), y used (y ≥ 1): r′ = r(x, y) + (Λ − λ(y)) ≥ r(x, y) ≥ 0, by (f) (y was selected before
  j*) and (J1).
- x not reached, y unused: r′ = r(x, y) ≥ 0.

*Tight arcs.* For a selected column j, (b) at its selection gives λ(j) = λ(way[j]) + r(x_{way[j]}, j); by the first
case (if j is used) or the second case (j = j*, with λ(j*) = Λ), r′(x_{way[j]}, j) = 0. Matched pairs (x_c, c) with
c used stay tight (first case with y = c_x), and matched pairs with unused columns are unchanged.

*Augmentation.* `while j0: j1 = way[j0]; match[j0] = match[j1]; j0 = j1`, started at j0 = j*, walks the chain
j* = c_0, c_1 = way[c_0], …, c_q = 0 (Lemma H1(e)) and sets match[c_k] to the old match[c_{k+1}] (c_{k+1} is changed
only in the next step). Each new pair (x_{c_{k+1}}, c_k) is a tree arc, hence tight. The rows x_{c_1}, …, x_{c_q} = i
are distinct; each of the first q − 1 moves from column c_k to c_{k−1}, and row i gets c_{q−1}. So afterwards the
rows 1..i are matched to i distinct columns (the old ones and j*), every pair is tight ((J2) for i + 1), (J1) holds
for the rows ≤ i by the four cases, and the rows x > i were never shifted ((J3)).

## 3. The Hungarian implementation: optimality

**Theorem.** For every n × n integer matrix, `assignment_hungarian` returns the minimum assignment cost (0 for n = 0).

**Proof.** By Lemma H2 and induction, after the search for row n the n rows are matched to the n columns by a
permutation π (π(x) = the column of x), r(x, π(x)) = 0 for all x, and r(x, y) ≥ 0 for all x, y, now with the final
potentials u, v. For every permutation σ, Σ_x C[x][σ(x)] = Σ_x r(x, σ(x)) + Σ_{x=1..n} u[x] + Σ_{y=1..n} v[y]
≥ Σ u + Σ v = Σ_x C[x][π(x)] (weak duality: the potentials certify that π is optimal). The function returns
Σ_{j=1..n} C[match[j] − 1][j − 1], the cost of π. All values are Python integers after the first iteration (only the
initial `minv` entries are `INF`), so every comparison is exact.

**Check.** `tests/test_proofs_assignment.py`, `test_hungarian_invariants_and_certificate` (n = 1..12, 20, 30, two
`harness.generate` matrices and two uniform matrices in [−50, 50] per n: at the line `match[0] = i` of the running
code, (J1)–(J3) hold for the current u, v, match; at the return, every reduced cost is ≥ 0, the matching is a
permutation, and the returned value equals Σu + Σv) and `test_hungarian_optimal` (n = 0..9, 8 matrices per n,
against the subset DP of `harness.py`). The V1 battery compares the two implementations for n = 0..8 and the subset
DP for n ≤ 12.

## 4. The Hungarian implementation: O(n³) time and Θ(n) space

**Statement.** O(n³) time on every input (Lemma H0: at most n(n + 1)/2 iterations, at most n(n + 1)(2n + 1)/6
reduced-cost evaluations). Besides the input, the containers bound to its local variables are exactly six lists of
n + 1 entries (u, v, match, way, and, per row, minv and used, each replacing the previous row's list): 6(n + 1) words
for n ≥ 1, which is Θ(n).

**Proof.** Time: Lemma H0. Space: the only containers the function creates are these lists; `row` is a row of the
input. While a new `minv` or `used` list is being created, the previous one still exists, so the true peak is at most
7(n + 1) words; the check measures the containers bound to local variables between statements.

**Check.** `tests/test_proofs_assignment.py`, `test_hungarian_iteration_and_evaluation_bounds` (n = 0..30, 40, 60;
three `harness.generate` matrices and three uniform matrices per n: matrix rows and an outer tuple that count every
read show at most i iterations for row i, at most n(n + 1)/2 in all, and at most n(n + 1)(2n + 1)/6 reduced-cost
evaluations; only these upper bounds are asserted) and `test_space` (n = 0..16, 24: the instrumented peak equals
6(n + 1), and 0 for n = 0). `experiments/2026-10-07_assignment_random_matrix_counts.py` checks the same two upper
bounds on uniform [0, 99] matrices, n = 30..200 ([PASS] lines).

## 5. The separation (T2)

Enumeration takes Ω(n·n!) time on every input, unconditionally, and Θ(n·n!) under the assumption of section 1; the
Hungarian implementation takes O(n³) (section 4). The separation needs only Ω(n·n!) and O(n³): n·n!/n³ → ∞, so the
gap is factorial against cubic. The V2 fits (timing, measured) are data about the
implementations, not part of the proof.

## 6. Maximisation

For every matrix, max_π Σ_i C[i][π(i)] = −min_π Σ_i (−C[i][π(i)]): negation reverses the order of the costs of all
permutations. So the maximisation version is solved by running either implementation on −C and negating the result.

**Check.** `tests/test_proofs_assignment.py`, `test_maximisation_by_negation` (n = 0..7, four matrices each: the
maximum over all permutations equals minus the Hungarian value of −C).

## 7. Measured statements (data, not theorems)

- The V2 timing fits (enumeration against n·n!, Hungarian against n³ on the column-dominant family
  C[i][j] = 1000j + noise). That the Hungarian runtimes grow like n³ on this family is measured; no lower bound is
  proved here.
- On uniformly random matrices with entries in [0, 99], the searches used only part of the worst-case bounds of
  Lemma H0: 8% to 28% of the iteration bound and 11% to 36% of the evaluation bound (n = 30, 50, 75, 100, 150, 200;
  three seeded matrices each; `experiments/2026-10-07_assignment_random_matrix_counts.py`, [DATA] lines).

*A fact used in the description of the timing family (not measured).* On C[i][j] = 1000j + r(i, j) with r in
[0, 999], every row ranks the columns in the same order: C[i][j] ≤ 1000j + 999 < 1000(j + 1) ≤ C[i][j + 1].
