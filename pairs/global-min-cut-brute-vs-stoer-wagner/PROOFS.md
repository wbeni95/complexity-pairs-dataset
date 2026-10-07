# Proofs: global minimum cut, brute force vs Stoer–Wagner

This file proves every claim that this entry makes about its problem and its two implementations (in `entry.json`,
`README.md` and the docstrings of the code), for every size of its domain, from the code in this folder: the exact
operation counts (sections 1 and 2), the problem facts (section 3), the correctness of both algorithms (sections 4
and 5, including the cut-of-the-phase lemma), the time and space bounds (section 6), the sizes of the numbers
(section 7) and the harness oracle (section 8). Each proof is followed by the deterministic scripts or tests that
check it and the sizes they check it on. A check covers only those sizes; the proofs cover the whole domain. The
README section "Where the closed forms come from" outlines the same counts. Statements about other algorithms
(the Fibonacci-heap bound, Karger–Stein) are background in `entry.json`, not claims.

## Counting convention

`harness.py`, class `CountingWeight`: `__add__` (also bound as `__radd__`) adds 1 to the module counter `_adds`
and returns a new `CountingWeight`; the six comparison methods call `_cmp`, which adds 1 to `_cmps`.
`generate_scaling(n, rng)` returns a symmetric n × n matrix whose entries are all `CountingWeight` (off-diagonal
weights 1..9, diagonal 0) and sets both counters to 0; `reported_cost(output)` returns `_adds + _cmps`.

An addition or comparison with at least one `CountingWeight` operand counts exactly 1 (if only the right operand is
one, the int method returns `NotImplemented` and Python calls the reflected method), and a sum with a
`CountingWeight` operand is a `CountingWeight`. Not counted: index and mask arithmetic, the identity tests
`best is None`, `t is not None`, the test `v != s` and `list.remove`, which compare plain vertex numbers, and the
dictionary `key`, whose keys are plain ints. Neither implementation lets a weight decide whether an operation runs
(only which vertex is selected), so both counts are the same on every n × n matrix of `CountingWeight` entries.
Both return `None` for n < 2 without any operation, so the domain is n ≥ 2.

## 1. Brute force: n(n − 1)2^(n−3) additions and 2^(n−1) − 2 comparisons

**Statement.** For every n ≥ 2 and every input, `min_cut_brute_force` makes exactly n(n − 1)2^(n−3) counted
additions and 2^(n−1) − 2 counted comparisons.

**Proof.** The loop visits the 2^(n−1) − 1 masks of non-empty sets S ⊆ {1..n − 1}; with s = |S| (1 ≤ s ≤ n − 1),
the other side T has n − s ≥ 1 vertices. `w = w + row[v]` runs once per pair (u, v) ∈ S × T, s(n − s) ≥ 1 counted
additions (the first through `__radd__` on the plain 0), so `w` is a `CountingWeight`. The test
`best is None or w < best` short-circuits for the first mask and counts 1 comparison for each of the other
2^(n−1) − 2 masks. With m = n − 1, using Σ_s C(m, s)s = m·2^(m−1) and Σ_s C(m, s)s² = m(m + 1)2^(m−2):
Σ_s C(m, s)s(m + 1 − s) = (m + 1)m·2^(m−1) − m(m + 1)2^(m−2) = m(m + 1)2^(m−2) = n(n − 1)2^(n−3).

**Check.** `experiments/2026-10-07b_global_min_cut_counts.py` (n = 2..14). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "min cut brute n(n-1)2^(n-3)+2^(n-1)-2": n = 0..14 (includes the V2 sizes n = 6, 8, …, 14;
n = 0, 1 reported as outside the domain); line "min cut brute: adds n(n-1)2^(n-3), cmps 2^(n-1)-2": n = 2..14;
group `extra`, line "min cut brute and Stoer-Wagner on other weight draws (3 per n)": n = 2..12.
`experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "min cut: counts on sparse matrices with zero
weights": n = 2..12, 3 seeded matrices per n.

## 2. Stoer–Wagner: (n − 1)(n − 2)(n + 3)/6 additions and n(n − 1)(n − 2)/6 + n − 2 comparisons

**Statement.** For every n ≥ 2 and every input, `min_cut_stoer_wagner` makes exactly (n − 1)(n − 2)(n + 3)/6
counted additions and n(n − 1)(n − 2)/6 + n − 2 counted comparisons, in total (n − 2)(2n² + n + 3)/6. A phase on k
vertices makes (k − 1)(k − 2)/2 key additions, k − 2 merge additions, (k − 1)(k − 2)/2 selection comparisons, and one
comparison with the best cut in every phase but the first.

**Proof.** All entries of `G` are `CountingWeight` (copies, then sums of such values), and so is every `key[v]`.
The outer loop runs n − 1 phases, on k = n, n − 1, …, 2 active vertices (each phase removes t from `active`).

*One phase on k vertices.* `rest` starts with k − 1 vertices. While `rest` has r vertices (r = k − 1, …, 1): the
selection loop compares `key[v] > key[sel]` for the r − 1 vertices after `rest[0]` (r − 1 comparisons);
`rest.remove(sel)` compares plain ints; the update loop computes `key[v] + G[sel][v]` for the r − 1 remaining
vertices (r − 1 additions). Over r = k − 1, …, 1: (k − 1)(k − 2)/2 comparisons and as many additions. Then
`best is None or cut_of_phase < best` counts 1 comparison except in the first phase. The merge loop runs over the
k − 1 vertices left in `active` and computes `G[s][v] + G[t][v]` for the k − 2 of them other than s (k − 2
additions; `v != s` compares plain ints).

*Sums.* With j = k − 1 = 1, …, n − 1: additions Σ_j [j(j − 1)/2 + (j − 1)] = Σ_j (j − 1)(j + 2)/2, and for
N = n − 1, Σ_{j=1..N} (j² + j − 2)/2 = N(N − 1)(N + 4)/6 = (n − 2)(n − 1)(n + 3)/6. Comparisons
Σ_{j=1..n−1} C(j, 2) + (n − 2) = C(n, 3) + n − 2 = n(n − 1)(n − 2)/6 + n − 2. Total
(n − 2)[(n − 1)(n + 3) + n(n − 1) + 6]/6 = (n − 2)(2n² + n + 3)/6.

**Check.** `experiments/2026-10-07b_global_min_cut_counts.py` (n = 2..40, 48..256).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Stoer-Wagner (n-2)(2n^2+n+3)/6": n = 0..40
and n = 48, 64, 128, 256 (includes the V2 sizes n = 32, 64, 128, 256; n = 0, 1 reported as outside the domain);
line "Stoer-Wagner: adds (n-1)(n-2)(n+3)/6, cmps n(n-1)(n-2)/6+n-2": n = 2..40; group `extra`, line "min cut brute
and Stoer-Wagner on other weight draws (3 per n)": n = 2..12. `experiments/2026-10-07_count_proof_checks.py`, group
`sat`, line "min cut: counts on sparse matrices with zero weights": n = 2..12, 3 seeded matrices per n.

## 3. Problem facts

**Disconnected graphs.** If the graph (edges = pairs with W[u][v] > 0) is disconnected, let S be one connected
component; no positive-weight pair joins S and V − S, so the cut (S, V − S) weighs 0, and no cut weighs less since
all weights are non-negative. So the answer is 0. For n < 2 no partition into two non-empty sides exists, and both
implementations return `None` (first lines of both functions).

**The diagonal is never read.** The brute force reads `W[u][v]` only for u ∈ S and v ∈ T, which are disjoint.
Stoer–Wagner reads `G[a][v]` and `G[sel][v]` only for v in `rest` (which no longer contains `sel`, and never
contained a), and in the merge `G[s][v]`, `G[t][v]` only for v ≠ s in `active`, after t has been removed. So both
implementations ignore the diagonal. The harness's subset oracle uses row sums (degrees), which include the
diagonal, so it assumes a zero diagonal.

**Check.** `tests/test_proofs_mincut.py`, class `ProblemFacts`: answer 0 on 60 seeded disconnected graphs
(n = 2..12); unchanged answers of both implementations after a random non-zero diagonal is added (60 graphs).

## 4. Brute force: correctness

Every partition of V into two non-empty sides has exactly one side T containing vertex 0, and the other side S is a
non-empty subset of {1, …, n − 1}. The loop visits each such S once (bit i of `mask` ⇔ vertex i + 1 ∈ S), computes
w = Σ_{u ∈ S, v ∈ T} W[u][v], the weight of the cut, and keeps the minimum. ∎

## 5. Stoer–Wagner: correctness

Write w(X, Y) = Σ_{x ∈ X, y ∈ Y} W[x][y] for disjoint vertex sets X, Y, and λ(H) for the minimum cut weight of a
graph H with at least two vertices. All weights are non-negative.

**Representation.** Each active vertex x stands for a set X(x) of original vertices; the sets of the active vertices
partition V, and initially X(x) = {x}. Invariant: `G[x][y]` = w(X(x), X(y)) for active x ≠ y. Merging t into s
(X(s) := X(s) ∪ X(t), `G[s][v] = G[s][v] + G[t][v]` and `G[v][s] = G[s][v]` for the other active v, t removed)
keeps it. So the current graph H has the active vertices and the weights `G`, and the cuts of H are exactly the cuts
(S, V − S) of the original graph that split no set X(x), with the same weight.

**One phase.** With A the set of vertices added so far (initially {a}, a = `active[0]`), the loop keeps
`key[v]` = w(A, v) in H for every v in `rest`: it starts as `G[a][v]`, and when `sel` joins A every remaining key
grows by `G[sel][v]`. It selects a vertex with maximum key (the first one in `rest` order), so the order
a = v_1, v_2, …, v_k is a *maximum-adjacency order*: w(A_i, v_i) ≥ w(A_i, y) for every y added after v_i, where
A_i = {v_1, …, v_{i−1}}. At the end, t = v_k, s = v_{k−1} (s = a when k = 2) and `cut_of_phase` = `key[t]`
= w(V(H) − {t}, t), the weight of the cut ({t}, V(H) − {t}) of H.

**Lemma P (cut of the phase; Stoer & Wagner 1997, Lemma 3.1).** In every graph H with non-negative weights and every
maximum-adjacency order ending in s, t, the cut ({t}, rest) is a minimum s–t cut: w(A_t, t) ≤ w(C) for every cut C
of H that separates s and t, where A_t is the set of vertices before t.

*Proof.* Fix C. Call v_i (i ≥ 2) *switching* if v_i and v_{i−1} lie on different sides of C, and let C_v be the set of
edges of C with both ends in A_v ∪ {v}, where A_v is the set of vertices before v. We show w(A_v, v) ≤ w(C_v) for
every switching v, by induction along the order. For the first switching vertex v, all vertices of A_v lie on the
side of v_1 (no earlier vertex is switching) and v on the other side, so C_v consists of the edges between A_v and v:
equality. Let v be switching and u the previous switching vertex. Then
w(A_v, v) = w(A_u, v) + w(A_v − A_u, v) ≤ w(A_u, u) + w(A_v − A_u, v) ≤ w(C_u) + w(A_v − A_u, v),
by the maximum-adjacency choice of u (v was still available when u was added) and by induction. The vertices of
A_v − A_u (from u up to the vertex before v) lie on the side of u, because none of them after u is switching, and
v lies on the other side, because v is switching; so every edge between A_v − A_u and v belongs to C_v, and none of them
belongs to C_u (they contain v ∉ A_u ∪ {u}). As C_u ⊆ C_v and all weights are non-negative,
w(C_u) + w(A_v − A_u, v) ≤ w(C_v). Finally t is switching (s and t are separated), and C_t = C, so
w(A_t, t) ≤ w(C). ∎

**Lemma G (merging; Stoer & Wagner 1997, Theorem 2.1).** Let H have k ≥ 3 vertices, let s, t be any two of them, and
H/st the graph with s and t merged. Then λ(H) = min(λ_st(H), λ(H/st)), where λ_st(H) is the minimum weight of a cut
of H separating s and t.

*Proof.* The cuts of H/st are exactly the cuts of H that do not separate s and t, with the same weight, and every
cut of H either separates s and t or does not. ∎

**Theorem SW.** `min_cut_stoer_wagner` returns λ(G) for every n ≥ 2.

*Proof.* By induction on the number k of active vertices: the minimum of the cuts of the phases still to be run on
the current graph H equals λ(H). For k = 2 the only cut of H is ({t}, {s}), which is the cut of the phase. For k ≥ 3, the cut of the phase
weighs λ_st(H) by Lemma P (it is itself an s–t cut), the remaining phases run on H/st and give λ(H/st) by
induction, and Lemma G gives λ(H). The value `best` is the minimum of the cuts of the phases. ∎

**Check.** `tests/test_proofs_mincut.py`, class `Correctness`: both implementations equal a subset enumeration
written in the test (a direct sum over the cut edges) on 132 seeded harness instances, n = 0..10, 12 per size.
Class `CutOfThePhase`: a separate maximum-adjacency phase with random tie-breaking, written in the test, gives a cut
equal to the minimum s–t cut by enumeration on 210 seeded random graphs with n = 2..8 and zero weights (Lemma P).

## 6. Time and space bounds (including the uncounted work)

**Brute force: Θ(n²·2ⁿ) time, Θ(n) space besides the input (n ≥ 2).** Each of the 2^(n−1) − 1 masks costs Θ(n) for
building S and T (two list comprehensions over n − 1 vertices) plus |S|·|T| additions and O(1) other work. By §1 the
additions total n(n − 1)2^(n−3), so the time is Θ(n·2ⁿ + n²·2ⁿ) = Θ(n²·2ⁿ). The lists S and T have n entries
together, and `w`, `best`, `mask` are single values: Θ(n) space (counting a weight value or an n-bit mask as O(1)
words). In terms of the input size N = n², 2ⁿ = 2^√N, so the time is 2^Θ(√N).

**Stoer–Wagner: Θ(n³) time, Θ(n²) space (n ≥ 2).** Cost model: each access to the dictionary `key` (a lookup, an
insertion or an update) counts as one word operation, like a list access. The copy `G` costs Θ(n²) time and is the
Θ(n²) space. A phase on k active vertices builds `rest` and `key` in Θ(k); in the round with r vertices left in `rest`, the selection scan,
`rest.remove(sel)` and the key update cost Θ(r) each; `active.remove(t)` and the merge loop cost Θ(k). So the phase
costs Θ(k²), and Σ_{k=2..n} Θ(k²) = Θ(n³), Θ(N^1.5) in the input size N = n². The uncounted work (list building,
removals, index scans) is therefore of the same order as the counted weight operations of §1 and §2, as the caveats
state.

**Check.** `tests/test_proofs_mincut.py`, class `Space`: the tracemalloc peak of one call grows by less than a
factor 2 from n = 8 to n = 12 for the brute force (Θ(n); a Θ(2ⁿ) peak would grow 16-fold), and by a factor between
2.5 and 5 per doubling of n = 32, 64, 128 for Stoer–Wagner, with peak/n² below 16 bytes (Θ(n²); measured ratios 3.2
and 3.5).

## 7. Sizes of the numbers

Let B be the largest weight. Every value that either implementation computes is at most n²B/4: the brute force's
partial sums are at most w(S, T) ≤ |S|·|T|·B; Stoer–Wagner's `G[x][y]` = w(X(x), X(y)) and its keys
w(A, v) = w(∪_{x ∈ A} X(x), X(v)) are weights between two disjoint sets of original vertices, at most
|X|·|Y|·B ≤ (n²/4)·B because |X| + |Y| ≤ n; `best` is one of these values. With b-bit weights (B ≤ 2^b − 1) every
value is below n²·2^b/4, so it has at most b + 2·log₂ n bits, and each addition or comparison costs O(b + log n)
bit operations.

**Check.** `tests/test_proofs_mincut.py`, class `NumberSizes`: weights wrapped in a type that records the largest
value produced by an addition, on 102 seeded harness instances (n = 2..12 for both implementations, 16, 20, 24 for
Stoer–Wagner): the largest value is at most n²B/4.

## 8. The harness oracle

`harness.check` takes the minimum over t = 1..n − 1 of a maximum 0–t flow in the symmetric capacity matrix W. A
directed cut S (0 ∈ S, t ∉ S) of that network has capacity Σ_{u ∈ S, v ∉ S} W[u][v], the weight of the undirected
cut (S, V − S); every global cut separates vertex 0 from some t; so the minimum over t of the minimum 0–t cut is the
global minimum cut. The flow routine `_max_flow` augments along breadth-first paths in a residual matrix until t is
unreachable; then the set S reachable from 0 has residual capacity 0 on every pair leaving S, which makes the flow
value equal to the capacity of S, as in Lemma M of
[the max-flow entry's PROOFS.md](../max-flow-edmonds-karp-vs-dinic/PROOFS.md) (the matrix stores, for each ordered
pair, capacity minus net flow, and the sum of these residuals over the pairs leaving S is c(S) − |f|). It
terminates because every augmentation adds at least 1 to an integer flow bounded by the weight of the cut around
vertex 0. For n ≤ 10, `check` also enumerates all subsets with Σ_{u ∈ S} deg(u) − 2·w(S, S), which equals
w(S, V − S) when the diagonal is zero.
