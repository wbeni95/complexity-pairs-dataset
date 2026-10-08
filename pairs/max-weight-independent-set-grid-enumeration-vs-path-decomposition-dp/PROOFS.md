# Proofs: maximum-weight independent set on grids, exhaustive search vs column DP

This file proves every claim that this entry makes about its problem and its two implementations (in `entry.json`,
`README.md` and the docstrings of the code), for every size of its domain, from the code in this folder: the exact
operation counts (sections 1–3), the graph facts (section 4), correctness, time and space of both algorithms
(sections 5 and 6), the statements about the harness oracle (section 7), the reduction of grids without diagonals
to a minimum cut (section 8) and the other numbers in the README (section 9). Each proof is followed by the
deterministic scripts or tests that check it and the sizes they check it on. A check covers only those sizes; the
proofs cover the whole domain. NP-hardness on general graphs and linear-time tree decompositions are background in
`entry.json`, not claims.

## Counting convention

`harness.py`, class `CountingInt`, with the module tally `_ops = {"add", "compare"}`: `__add__`, `__radd__`,
`__sub__` and `__rsub__` add 1 to `_ops["add"]` and return a new `CountingInt`; the six comparison methods add 1 to
`_ops["compare"]`. `reported_cost(output)` returns `_ops["add"]` only; comparisons are tallied separately.
`generate_scaling(n, rng)` returns the 3 × n king's graph (k = 3, diagonal code 3 in every square) with weights
1..9 wrapped in `CountingInt` (`king_instance`) and resets the tally.

An addition or comparison with at least one `CountingInt` operand counts 1 (with a plain left operand the int method
returns `NotImplemented` and Python calls the reflected method); a sum with a `CountingInt` operand is a
`CountingInt`, whatever its value. Plain: the starting values `total = 0`, `best_value = 0`, the masks, the states
and all bit tests. "Every instance" below means every instance whose weights are `CountingInt` values (k ≥ 1, as the
problem statement requires).

## 1. Exhaustive search: N·2^(N−1) additions on every instance, (3/2)n·8ⁿ for k = 3

**Statement.** For every k ≥ 1, n ≥ 0 and every instance (any diagonals, any weights, zeros included),
`mwis_brute_force` makes exactly N·2^(N−1) counted additions, N = kn; for k = 3 this is
3n·2^(3n−1) = (3/2)n·8ⁿ.

**Proof.** The loop visits every mask of the N vertices, with no early exit. For a mask, `total = total + weights[r][c]`
runs once per member (the first through `__radd__` on the plain 0), and nothing else adds. Each vertex is a member
of 2^(N−1) masks, so there are N·2^(N−1) additions (0 for N = 0).

**Check.** `experiments/2026-10-06f_entries_mis_pathwidth.py` (77 random instances with N ≤ 15 and zero weights, and the V2
family n = 1..6). `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "MIS brute N2^(N-1), N=3n": n = 0..6 (includes the V2 sizes n = 2..6).
`experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "MIS exhaustive N2^(N-1) on random instances (any
k, diagonals, zero weights)": 40 seeded instances, k = 1..4, n = 0..4, N ≤ 12.

## 2. Column DP: n·P_k + (n − 1)·F_{k+2} additions for n ≥ 1 and positive weights, 10n − 5 for k = 3

**Statement.** For every k ≥ 1, n ≥ 1 and every instance with positive weights (any diagonals), `mwis_column_dp`
makes exactly n·P_k + (n − 1)·F_{k+2} counted additions, where F_{k+2} is the number of column states and P_k the
total number of rows over all column states; for k = 3 (P_3 = F_5 = 5) this is 10n − 5. (For n = 0 it returns at
once with no operation.)

**Proof.** *States.* `states` lists the s ∈ [0, 2^k) with `s & (s >> 1) == 0`, the subsets of a k-vertex path with
no two adjacent rows. Their number a(k) satisfies a(k) = a(k − 1) + a(k − 2) (row k − 1 absent, or present with row
k − 2 absent), a(1) = 2 = F_3, a(2) = 3 = F_4, so a(k) = F_{k+2}. For k = 3 the states are 0, 1, 2, 4, 5, with
P_3 = 0 + 1 + 1 + 1 + 2 = 5.

*Column weights.* `column_weight(c, s)` adds the weights of the popcount(s) rows of s, each a counted addition
(the first through `__radd__`); for s = 0 it returns the plain 0 and otherwise a `CountingInt`. It is called once
per state for column 0 and once per state for each column c ≥ 1: n·P_k additions.

*Transitions.* For c ≥ 1 and each state s, the inner loop scans all states t; t = 0 is compatible with every s (all
three tests are 0), and it comes first, so `m` is set (to `best[0]`) and the arg-max keeps the first maximal entry.
Then `column_weight(c, s) + m` is evaluated once. Claim: it always counts. For s ≠ 0 the column weight is a
`CountingInt`. For s = 0 every state t is compatible, so m is the first maximal entry of the previous row `best`:
- at c = 1, `best[0]` is the plain 0 but the state {row 0} (s = 1) has the positive weight w(0, 0) as a
  `CountingInt`, so the maximum is reached only at `CountingInt` entries and m is one;
- at c ≥ 2, every entry of the previous row is a `CountingInt` (it is the result of a counted addition), so m is
  one.

So each of the F_{k+2} states of each column c ≥ 1 adds 1: (n − 1)·F_{k+2}. The final arg-max and the back-tracking
only compare. Total n·P_k + (n − 1)·F_{k+2}, and 5n + 5(n − 1) = 10n − 5 for k = 3.

**Zero weights.** For every instance with non-negative weights (zeros allowed) and n ≥ 1 the count is exactly
n·P_k + (n − 1)·F_{k+2} − z, where z is the number of c ∈ {1, …, n − 1} such that every weight in columns 0..c − 1 is
0. *Proof.* The additions inside `column_weight` always count (each weight is a `CountingInt`), and
`column_weight(c, s)` is a `CountingInt` for s ≠ 0 and the plain 0 for s = 0. So the only addition that can go
uncounted is `column_weight(c, 0) + m`, and it does exactly when m is a plain int. The entries of a row for s ≠ 0 are
`CountingInt`s; the entry for s = 0 is plain only if its own addition went uncounted (or c = 0), and then its value
is 0. For s = 0 every t is compatible, and the scan keeps the first maximal entry (strict `>`), so m is plain iff the
entry for t = 0 of the previous row is plain and maximal, i.e. iff that entry is plain and the whole previous row is
0 (weights are non-negative). A row best_{c−1} is identically 0 iff all weights in columns 0..c − 1 are 0
(best_{c−1}(s) ≥ w_{c−1}(s), and best_{c−1}(0) is the maximum of the row before). By induction on c, the addition for
(c, 0) goes uncounted iff columns 0..c − 1 have only zero weights. ∎ For positive weights z = 0.

**Check.** `experiments/2026-10-06f_entries_mis_pathwidth.py` (420 random instances, n = 1, 4, …, 40, k = 1..6, positive
weights, and the V2 family). `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "MIS DP 10n-5": n = 1..59
and the V2 sizes n = 100, 200, 400, 800, 1600, 3200 (n = 0 reported as outside the domain with count 0); line "MIS DP 0
at n=0": n = 0; line "MIS DP general k: nP_k+(n-1)F_{k+2} (k=1..8, king's graph)": k = 1..8,
n = 1, 2, 3, 7, 20 (it prints the values 58, 97, 195, 352, 647, 1159, 2066, 3645 for n = 20 listed in `entry.json`).
`experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "MIS DP nP_k+(n-1)F_{k+2} on random diagonal
patterns, positive weights": k = 1..6, n = 1..12, 2 seeded instances each. `tests/test_proofs_mwis.py`, class
`ZeroWeights`: the form with z on 600 seeded instances with many zero weights (k = 1..6, n = 1..12).

## 3. Column DP, uncounted work and comparisons: (n − 1)·F_{k+2}² compatibility tests, 6n − 2 comparisons for k = 3

**Statement.** For every k ≥ 1 and n ≥ 1, `mwis_column_dp` makes exactly (n − 1)·F_{k+2}² compatibility tests (the
test `t & s`, on plain ints; 25 per column for k = 3; (n − 1)F_{k+2}² = 76, …, 57475 for n = 20, k = 1..8). On the
3 × n king's graph with positive weights it makes exactly 6n − 2 counted comparisons (tallied separately).

**Proof.** *Compatibility tests.* For each column c ≥ 1, each of the F_{k+2} states s scans all F_{k+2} states t, and
the first test `t & s` runs for each pair.

*Comparisons.* With diagonal code 3, `down = up = 0b11`. For c ≥ 1 the compatible states t of each s are:
s = 0: all five; s = 1 (row 0): t ∈ {0, 4} (t must avoid row 0, and `((s & up) << 1) & t` excludes row 1);
s = 2 (row 1): only t = 0 (`((t & down) << 1) & s` excludes 1 and 5, `((s & up) << 1) & t` excludes 4);
s = 4 (row 2): t ∈ {0, 1} (`((t & down) << 1) & s` excludes 2); s = 5 (rows 0 and 2): only t = 0 (`t & s` leaves
{0, 2}, and `((t & down) << 1) & s` excludes 2). The first compatible t (t = 0) is stored without comparison
(`m is None`), and each later one makes one comparison `best[j] > m` with `best[j]` a `CountingInt` (j ≥ 1 at
c = 1, any j later): 4 + 1 + 0 + 1 + 0 = 6 per column. The final arg-max compares `best[i] > best[j]` for
i = 1..4, with `best[i]` a `CountingInt`: 4. Total 6(n − 1) + 4 = 6n − 2.

*Comparisons for every k.* For every k ≥ 1, n ≥ 1 and every instance, the DP evaluates `best[j] > m` once for every
compatible pair (t, s) except the first compatible t of each s, and `best[i] > best[j]` F_{k+2} − 1 times at the end.
The state s = 0 is compatible with all F_{k+2} states, every s with at least t = 0. So each column c ≥ 1 makes between
F_{k+2} − 1 and F_{k+2}·(F_{k+2} − 1) comparisons, and the total lies between n·(F_{k+2} − 1) and
(n − 1)·F_{k+2}·(F_{k+2} − 1) + F_{k+2} − 1: linear in n for every fixed k. With positive weights every compared
`best` entry other than the stored first one is a `CountingInt` (as in the k = 3 case), so the separate tally equals
this number.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "MIS DP comparisons 6n-2 (k=3,
tallied separately)": n = 1..59; group `extra`, line "MIS DP compatibility tests (n-1)F_{k+2}^2 (uncounted)":
k = 1..5, n = 1, 2, 5, 10. `experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "MIS DP
compatibility tests (n-1)F_{k+2}^2 at n = 20, k = 1..8": k = 1..8, n = 20. `tests/test_proofs_mwis.py`, class
`Comparisons`: the tally lies within the general bounds on 300 seeded instances with positive weights (k = 1..6,
n = 1..15, random diagonal codes).

## 4. Model and graph facts

Cost model: word RAM. Masks of k bits (the DP) and of N = kn bits (the exhaustive search, whose loop counter already
runs to 2^N) count as O(1) words, and weights as unit-cost integers, as the entry states. Both implementations end
with `sorted()` of the chosen vertices; its cost is bounded only under the machine-model assumption, background in
`entry.json`, that `sorted()` sorts m items in O(m log m) worst-case time.

**Edges.** Every edge joins two vertices of the same column (vertical edges) or of adjacent columns (horizontal edges
and diagonals). Without diagonals the graph is bipartite: colour (r, c) by the parity of r + c; every edge changes
r + c by 1. A square with a diagonal contains a triangle: code 1, the diagonal (r, c)–(r + 1, c + 1), with
(r, c)–(r, c + 1)–(r + 1, c + 1); code 2, the diagonal (r, c + 1)–(r + 1, c), with (r, c)–(r, c + 1)–(r + 1, c). So
with any diagonal the graph is not bipartite.

## 5. Exhaustive search: correctness, Θ(N·2^N) time, Θ(N) space

`neighbours[i]` is the bitmask of the neighbours of vertex i (built from `_edges`, which lists exactly the edges of
the problem statement). For each mask, `independent` stays true iff no member has a neighbour in the mask, i.e. iff
the mask is an independent set, and `total` is its weight. The empty set (weight 0, independent) is the starting
best; a mask replaces the best only if it is independent and strictly heavier, so the result is the first
maximum-weight independent set in increasing mask order, with its weight. ∎

Time: 2^N masks, N iterations of O(1) word operations each, plus O(N) to build the neighbour masks; the independence
test `neighbours[i] & mask` runs once per member of each mask, exactly N·2^(N−1) times. Listing the chosen set takes
a pass over the N indices and `sorted()` of at most N vertices, O(N log N) under the sort assumption (§4). Total
Θ(N·2^N) for N ≥ 1, i.e. 2^Θ(n) for every fixed k. Space: `vertices`, `index` and `neighbours` have N
entries each (N words for the masks): Θ(N).

## 6. Column DP: correctness, time and space

**The compatibility test.** Let t be a state of column c − 1 and s a state of column c (bit r = row r). The edges
between the two columns are: the horizontal edges (r, c − 1)–(r, c), present in both t and s iff bit r of `t & s` is
set; the diagonal (r, c − 1)–(r + 1, c) of code 1 in square (r, c − 1), whose ends are both chosen iff bit r of
`t & down` and bit r + 1 of s are set, i.e. iff `((t & down) << 1) & s` has bit r + 1; the diagonal
(r, c)–(r + 1, c − 1) of code 2, whose ends are both chosen iff bit r of `s & up` and bit r + 1 of t are set, i.e. iff
`((s & up) << 1) & t` has bit r + 1. So t and s pass all three tests iff no edge joins them. The states
(`s & (s >> 1) == 0`) are exactly the subsets of a column with no vertical edge.

**Lemma I.** A vertex set I is independent iff each I_c = I ∩ (column c) is a state and I_{c−1}, I_c are compatible
for every c ≥ 1. (Every edge lies within a column or between adjacent columns, §4.)

**Lemma V.** For every c and state s, `best_c(s)` = the maximum weight of an independent set of columns 0..c that
meets column c in s; and following the stored choices back from (c, s) produces such a set.

*Proof.* Induction on c. c = 0: the only such set is s, of weight w_0(s) = `column_weight(0, s)`. c ≥ 1: the state
t = 0 is compatible with every s, so the maximum is over a non-empty set. If J is independent in columns 0..c with
J_c = s, then J − s is independent in columns 0..c − 1, meets column c − 1 in a state t compatible with s, and weighs
at most `best_{c−1}(t)`; so w(J) ≤ w_c(s) + max_t `best_{c−1}(t)` = `best_c(s)`. Conversely, for the stored maximizer
t, the set built back from (c − 1, t), plus s, is independent by Lemma I and weighs `best_c(s)`. ∎

The answer is the maximum of `best_{n−1}` (every independent set meets the last column in some state), returned
with the set rebuilt from the stored choices. For n = 0 the answer is (0, ()). ∎

**Number of states.** a(k) = F_{k+2} (§2). φ^(j−2) ≤ F_j ≤ φ^(j−1) for j ≥ 2: it holds for j = 2 (1 ≤ 1 ≤ φ) and
j = 3 (φ ≤ 2 ≤ φ²), and F_{j+1} = F_j + F_{j−1} with φ^a + φ^(a−1) = φ^(a+1) (φ² = φ + 1) carries both bounds from
j − 1, j to j + 1. So F_{k+2} = Θ(φ^k), F_{k+2}² = Θ(φ^(2k)), and 2^k ≤ φ^(2k) ≤ F_{k+2}² (φ² > 2). Also
F_{k+2} ≥ k + 1: F_3 = 2, F_4 = 3, and F_{j+1} = F_j + F_{j−1} ≥ F_j + 1.

**Time.** Listing the states scans 2^k masks once. Column 0 costs O(k·F_{k+2}). Each column c ≥ 1 costs O(k) for
`down` and `up`, exactly F_{k+2}² compatibility tests (§3) of O(1) word operations, and F_{k+2} calls of
`column_weight` of O(k) each. The final arg-max costs O(F_{k+2}) and the rebuild of the chosen list O(nk). With
k + 1 ≤ F_{k+2} and 2^k ≤ F_{k+2}², all this is O(F_{k+2}²·n) for n ≥ 1, and at least (n − 1)·F_{k+2}² ≥ n·F_{k+2}²/2
for n ≥ 2: Θ(F_{k+2}²·n) = Θ(φ^(2k)·n). The last step, `sorted()` of the chosen list, is not part of this bound: the
list has at most n·⌈k/2⌉ vertices (a state has no two adjacent rows), so it costs O(nk·log(nk)) under the sort
assumption (§4). For every fixed k the time is therefore Θ(n) apart from the final sort and O(n log n) with it; for
k = Θ(n), e.g. square grids (k = n), it is 2^Θ(n), exponential in n but 2^Θ(√N) in N = n². For k = O(log n) it is
polynomial in n (F_{k+2}² ≤ φ^(2k+2)).

**Space.** `back` holds n − 1 lists of F_{k+2} indices, and `states`, `best`, `new_best`, `choice` hold F_{k+2}
entries; the rebuilt set has at most nk ≤ n·F_{k+2} vertices: Θ(F_{k+2}·n) for n ≥ 2. Keeping only the current row
(without `back`) would compute the value alone in Θ(F_{k+2}) space. **Check:** `tests/test_proofs_mwis.py`, class `Space`:
the tracemalloc peak of the DP on the 3 × n king's graph grows by a factor between 1.5 and 2.6 per doubling of
n = 200, 400, 800 (measured 2.26 and 2.22), and that of the exhaustive search by less than 4 from N = 6 to N = 12
(Θ(N), not Θ(2^N)).

**Path decomposition (n ≥ 2).** The bags B_c = column c ∪ column c + 1 (c = 0..n − 2) have 2k vertices (width
2k − 1), cover every edge (§4), and each vertex lies in one or two consecutive bags: a path decomposition of width
2k − 1. (For n = 1 there are no such bags.)

**Check.** `tests/test_proofs_mwis.py`, class `Correctness`: both implementations equal a brute-force optimum
written in the test (all subsets, edges rebuilt from the definition) on 120 seeded instances with N ≤ 12 (k = 1..5,
random diagonal codes or none, weights 0..9 with many zeros) and on every diagonal pattern of the 2 × 2, 2 × 3, 3 × 2
and 3 × 3 grids (292 instances, seeded weights 0..9), and the returned sets are independent with the returned
weight. Class
`CompatibilityTest`: for k = 1..5 and all four diagonal codes per square, the three bit tests reject exactly the pairs
(t, s) joined by an edge. Class `States`: F_{k+2} states and P_k = 1, 2, 5, 10, 20, 38 for k = 1..6. The validator's
V1 run and the experiment script compare both implementations with the harness oracle.

## 7. The harness oracle (caveats)

In column-major order v_0, v_1, … (index c·k + r for (r, c)), the earlier neighbours of (r, c) are (r − 1, c)
(1 position back), (r, c − 1) (k back), (r − 1, c − 1) (k + 1 back, a diagonal of code 1 or 3 in square
(r − 1, c − 1)) and (r + 1, c − 1) (k − 1 back, a diagonal of code 2 or 3 in square (r, c − 1)); `blocked` sets
exactly the window bits 0, k − 1, k, k − 2 of those that exist. So every edge joins vertices at most k + 1 positions
apart, the bags {v_{i−k−1}, …, v_i} (those indices that exist) form a path decomposition of width at most k + 1,
namely min(N, k + 2) − 1 (each vertex lies in at most k + 2 consecutive bags), and the window of the last k + 1 vertices contains every earlier neighbour of the next vertex. By induction
over the vertices, the table maps each window pattern to the largest weight of an independent set of the processed
prefix with that pattern, so `profile_dp_value` returns the optimum. The states are masked to k + 1 bits, so there
are at most 2^(k+1) of them; each of the N = kn vertices costs O(1) dictionary operations per state:
O(2^k·k·n) dictionary operations, and 2^k·k/F_{k+2}² ≤ k·(2/φ²)^k → 0, so this grows more slowly in k than the
column DP's F_{k+2}²·n.

**Check.** `tests/test_proofs_mwis.py`, class `OracleWindow`: the local `blocked` of the running
`profile_dp_value` is read with `sys.settrace` for every vertex and equals the earlier-neighbour bits computed in the
test from the definition, on every diagonal pattern with (k − 1)(n − 1) ≤ 4 squares (k, n ≤ 5) and on 200 seeded
instances with random per-square codes (k = 1..6, n = 1..6); every edge joins vertices at most k + 1 positions apart,
and the table never holds more than 2^(k+1) states. `profile_dp_value` equals the brute-force optimum on the
instances of `Correctness`.

## 8. Notes: grids without diagonals reduce to a minimum cut

**Claim.** Let G be bipartite with colour classes X, Y and weights w ≥ 0, and K = w(V) + 1. In the network with
arcs σ → u of capacity w(u) (u ∈ X), v → τ of capacity w(v) (v ∈ Y) and u → v of capacity K for every edge uv
(u ∈ X, v ∈ Y), the minimum σ–τ cut capacity equals the minimum weight of a vertex cover, and the maximum weight of
an independent set equals w(V) minus it.

*Proof.* For a cut S (σ ∈ S, τ ∉ S) put C(S) = (X − S) ∪ (Y ∩ S). If no K-arc leaves S, every edge uv has u ∉ S or
v ∈ S, i.e. u ∈ C(S) or v ∈ C(S): C(S) is a vertex cover, and the capacity of S is exactly w(C(S)). Conversely
every vertex cover C equals C(S) for S = {σ} ∪ (X − C) ∪ (Y ∩ C), which no K-arc leaves. A cut that a K-arc leaves
has capacity ≥ K > w(V) ≥ w(X), the capacity of the cover X. So the minimum cut is the minimum cover weight. A set is
independent iff its complement is a vertex cover, so the maximum independent weight is w(V) minus the minimum
cover weight. ∎

By [the max-flow entry's PROOFS.md](../max-flow-edmonds-karp-vs-dinic/PROOFS.md) (Lemma M, the correctness part of
§3 for Edmonds–Karp and Theorem DI for Dinic, with the time bounds of Theorems EK and DI), either of its
implementations computes the maximum flow value, which equals the minimum cut, in time polynomial in N (integer
capacities; N + 2 vertices and at most 3N edges). So for grids without diagonals (bipartite, §4) the optimum value
is computed in polynomial time by max flow. An optimal set can be read off a minimum cut S, as (X ∩ S) ∪ (Y − S), the
complement of the cover C(S); the max-flow implementations return only the value. The flow method is not part of
this entry's implementations.

**Check.** `tests/test_proofs_mwis.py`, class `BipartiteFlow`: on 40 seeded grids without diagonals (k ≤ 4, n ≤ 6),
w(V) minus the max-flow entry's Dinic value on this network equals the column DP's optimum.

## 9. Other numbers in the README

N·2^(N−1) at k = 3, n = 20 is 60·2^59 ≈ 3.46·10^19. **Check:** `tests/test_proofs_mwis.py`, class `States`.
