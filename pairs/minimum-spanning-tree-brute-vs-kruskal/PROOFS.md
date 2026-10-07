# Proofs: minimum spanning tree, enumeration vs Kruskal vs Prim

This file proves every claim that this entry makes about its problem and its three implementations (in
`entry.json`, `README.md` and the docstrings of the code), for every size of its domain, from the code in this
folder: the exact operation counts (sections 1–3, with Cayley's formula), the correctness of the three algorithms
(sections 4 and 5, with the cut property), the time bounds, including a worst-case lower bound for Kruskal
(section 6), the optimality of Prim on K_n (section 7), space (section 8) and the harness oracle (section 9). Each
proof is followed by the deterministic scripts or tests that check it and the sizes they check it on. A check covers
only those sizes; the proofs cover the whole domain. Background in `entry.json`, not claims: three machine-model
assumptions (CPython's `sorted()` runs in O(m log m) worst-case time, used only for Kruskal's upper bound; `sorted()`
is deterministic and learns about the keys only from `<` comparisons, used for Kruskal's worst-case lower bound;
`itertools.combinations` behaves like its documented equivalent code, used for the enumeration), and the algorithms
for sparse graphs.

## Counting convention

`harness.py`, class `CountingWeight`: `__add__` (also bound as `__radd__`), `__mul__` (also bound as `__rmul__`),
`__divmod__` and the six comparison methods each add 1 to the module counter `_ops`; `__add__` and `__mul__` return
a new `CountingWeight`, `__divmod__` returns plain ints. `generate_scaling(n, rng)` draws the weights of K_n
(`_scaling_draws`, values in [1, 10⁹]), wraps every off-diagonal weight in `CountingWeight` (the diagonal stays a
plain int) and sets `_ops = 0`; `reported_cost(output)` returns `_ops`. An operation with at least one
`CountingWeight` operand counts 1 (with a plain left operand the int method returns `NotImplemented` and Python calls
the reflected method). Comparisons inside the built-in `sorted()` call `__lt__` on the keys and therefore count.
Vertex indices, `in_tree`, `seen`, `reached`, `taken` and the union-find arrays are plain ints or bools. All three
implementations return 0 at once for n ≤ 1 (Kruskal has no edge then), so the domain is n ≥ 1. The enumeration
relies on the documented behaviour of `itertools.combinations` (each (n − 1)-subset of the edge list exactly once;
machine-model assumption in `entry.json`).

## 1. Enumeration: (n − 1)·C(m, n − 1) additions and n^(n−2) − 1 comparisons

**Statement.** For every n ≥ 1, `mst_brute` on K_n with `CountingWeight` weights (any values) makes exactly
(n − 1)·C(m, n − 1) counted additions and n^(n−2) − 1 counted comparisons, m = n(n − 1)/2; the values listed in
`entry.json` (75, 964, 16310, 342390 for n = 4..7) are this sum.

**Proof.** For n = 1 the function returns 0 at once and the formula gives 0 + 1 − 1 = 0. For n ≥ 2 the loop visits
each of the C(m, n − 1) edge subsets once. For each it executes `total += W[u][v]` for its n − 1 edges (counted, the
first through `__radd__` on the plain 0); the depth-first search works on plain ints. The test
`reached == n and (best is None or total < best)` compares plain ints first; it reaches `total < best` (1 counted
comparison) exactly for the connected subsets after the first one. An (n − 1)-edge subset is connected iff it is a
spanning tree, so the comparisons number τ(K_n) − 1, where τ(K_n) is the number of spanning trees of K_n.

*τ(K_n) = n^(n−2) (Cayley's formula), by double counting.* Count the sequences of n − 1 directed edges that, added
one at a time, build a spanning tree of K_n with every edge directed towards a root. (a) Choose a spanning tree
(τ(K_n) ways), a root (n) and an order of its edges ((n − 1)!): τ(K_n)·n!. (b) Start from n single-vertex rooted
trees. Before the k-th edge (k = 1, …, n − 1) there are n − k + 1 rooted trees; the new edge goes from the root r of
one tree to any vertex v of another tree (making r a child of v): n choices of v, and then n − k choices of r (any
root except that of v's tree). In every sequence counted in (a), the tail of the k-th edge has no parent among the
edges added before it, so it is the root of its current tree, and its head lies in another tree; so (a) and (b)
count the same sequences, and τ(K_n)·n! = Π_{k=1..n−1} n(n − k) = n^(n−1)(n − 1)!, hence τ(K_n) = n^(n−2).

Values: n = 4: 3·C(6, 3) + 16 − 1 = 75; n = 5: 4·210 + 124 = 964; n = 6: 5·3003 + 1295 = 16310;
n = 7: 6·54264 + 16806 = 342390.

**Check.** `experiments/2026-10-06c_mst_counts.py` (the V2 sizes n = 4..7). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "MST enumeration (n-1)C(m,n-1)+n^(n-2)-1": n = 1..7 (n = 0 reported as outside the domain).
`experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "MST enumeration and Prim: additions and
comparisons separately": n = 1..7 (enumeration), n = 1..60 (Prim), 2 seeded weight draws per n.

## 2. Kruskal: 3m packing operations + comparisons inside `sorted()` + one `divmod` per scanned key

**Statement.** For every n ≥ 1 and every input of the scaling form, `mst_kruskal` makes exactly
3m + S + K counted operations, where m = n(n − 1)/2, S is the number of comparisons `sorted()` makes on the m keys,
and K is the number of keys scanned until n − 1 edges are taken. (S depends on CPython's sort; the entry states no
closed form for it.)

**Proof.** Each key `W[u][v] * nn + u * n + v` is evaluated as ((`W[u][v] * nn`) + `u * n`) + `v`: one counted
product and two counted additions (each sum is a `CountingWeight`), 3 per edge, 3m in all; `u * n` is plain.
`sorted()` compares `CountingWeight` keys through `__lt__`: S counted comparisons. In the scan, the test
`taken == n - 1` is plain and comes first; for each key that passes it, `divmod(key, nn)` counts 1
(`__divmod__`) and returns plain ints, and everything after that (`divmod(rest, n)`, `find`, `total += w`) is
plain. So the scan counts one operation per scanned key, K in all.

**Check.** `experiments/2026-10-06c_mst_counts.py` (the V2 sizes, cross-checked against `sorted()` on the same keys and
a replay of the scan). `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Kruskal = 3m + sort
comparisons + scanned keys (decomposition)": n = 2, 3, 5, 10, 50, 100.

## 3. Prim: (n − 1)(n − 2) comparisons + (n − 1) additions = (n − 1)²

**Statement.** For every n ≥ 1, `mst_prim` on K_n with `CountingWeight` off-diagonal weights (any values) makes
exactly (n − 1)(n − 2) counted comparisons and n − 1 counted additions, (n − 1)² in all.

**Proof.** n = 1 returns 0 at once. For n ≥ 2, `best` starts as row 0; every entry `best[v]` with v ≠ 0 is a
`CountingWeight` and stays one, since it is only replaced by `row[v] = W[u][v]` with u ≠ v. In round t
(t = 1, …, n − 1), n − t vertices are outside the tree. The selection loop skips tree vertices (`not in_tree[v]`
is false, no comparison), takes the first outside vertex without comparison (`u < 0`), and compares
`best[v] < best[u]` for each of the other n − t − 1 outside vertices (both `CountingWeight`). `total += best[u]`
counts 1 (the first time through `__radd__` on the plain 0). The update loop compares `row[v] < best[v]` for the
n − t − 1 vertices still outside (`row[v]` is an off-diagonal weight). Round t costs 2(n − t − 1) + 1, and
Σ_{t=1..n−1} [2(n − t − 1) + 1] = (n − 1)(n − 2) + (n − 1) = (n − 1)².

**Check.** `experiments/2026-10-06c_mst_counts.py` (the V2 sizes n = 50..800). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "Prim (n-1)^2": n = 1..59 and the V2 sizes n = 100, 200, 400, 800 (n = 0 reported as outside the
domain). `experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "MST enumeration and Prim: additions and
comparisons separately": n = 1..60, 2 seeded weight draws per n.

## 4. Enumeration: correctness

**Lemma F (forests).** A graph with n vertices and k edges has at least n − k connected components, with equality
iff it has no cycle. Hence an (n − 1)-edge subgraph of an n-vertex graph is a spanning tree iff it is connected iff
it is acyclic.

*Proof.* Add the edges one at a time to the empty graph (n components). An edge joining two different components
lowers the count by 1 and closes no cycle; an edge inside a component leaves the count unchanged and closes a cycle
(its ends were already joined by a path). With n − 1 edges: one component ⇔ every edge lowered the count ⇔ no cycle,
and a connected acyclic spanning subgraph is a spanning tree. ∎

`mst_brute` visits every (n − 1)-subset of the m edges of K_n once (`combinations`), decides connectivity by a
depth-first search from vertex 0 (`reached == n`), and keeps the smallest total weight among the connected ones. By
Lemma F these are exactly the spanning trees, so it returns the minimum spanning tree weight; for n = 1 it returns
0, the weight of the empty tree. ∎

## 5. Kruskal and Prim: correctness (the cut property)

Weights are arbitrary integers here; K_n is connected, so minimum spanning trees (MSTs) exist.

**Lemma C (cut property).** Let F be a set of edges contained in some MST T*, let S be a vertex set such that no
edge of F joins S and V − S, and let e be an edge of minimum weight among the edges joining S and V − S. Then
F ∪ {e} is contained in some MST.

*Proof.* If e ∈ T*, done. Otherwise T* ∪ {e} contains exactly one cycle, and it passes through e. The cycle crosses
between S and V − S an even number of times, so it contains another crossing edge e′ ∈ T*; e′ ∉ F because no edge
of F crosses. T′ = T* ∪ {e} − {e′} is connected (e′ lay on the cycle) and has n − 1 edges, so it is a spanning tree,
and w(T′) = w(T*) + w(e) − w(e′) ≤ w(T*). So T′ is an MST containing F ∪ {e}. ∎

**Kruskal.** The keys `W[u][v] * n² + u * n + v` with 0 ≤ u·n + v < n² are distinct and sort the edges by
(w, u, v); `divmod` recovers w, u, v. The union-find trees always have the components of the taken edge set F as
their vertex sets: `find` returns the root of x's tree (path halving only re-points a vertex to an ancestor in the
same tree), and a taken edge links the two roots. Invariant: F is contained in some MST. When the scan takes
e = (u, v) (`find(u) != find(v)`), let S be the component of F containing u. No edge of F crosses S. Every edge f
crossing S that precedes e in the order was scanned earlier; it was not taken (it would be an edge of F crossing
S, as F only grows), so at that time its ends were in one component, and they still are (components only merge),
contradicting that f crosses S now. So e is the first crossing edge in the order, hence of minimum weight, and
Lemma C keeps the invariant. The scan takes edges until it has n − 1: while F has fewer, it has two components
joined by some edge of K_n, which is taken when scanned. An acyclic set of n − 1 edges contained in an MST is that
MST (an MST also has n − 1 edges), so `total` is the MST weight. For n = 1 there is no key and the answer is 0. ∎

**Prim.** Invariant before each round, with T the tree vertices (`in_tree`): `best[v]` = min_{x ∈ T} W[x][v] for
every v ∉ T, and the edges chosen so far (one per added vertex, each attaining its `best`) form a tree on T contained
in some MST, of weight `total`. Initially T = {0} and `best` = row 0. A round picks u ∉ T with minimum `best[u]`
(the first such u), so the edge attaining `best[u]` is a minimum-weight edge between T and V − T, and no chosen edge
crosses (T, V − T); Lemma C keeps the invariant, and the update `best[v] = min(best[v], W[u][v])` restores the
formula for T ∪ {u}. After n − 1 rounds T = V and the chosen edges form an MST of weight `total`. ∎

**Check.** The validator's V1 run compares all three implementations with each other and with the Borůvka oracle
(n = 1..7; Kruskal and Prim also at n = 20, 60, 200). `tests/test_proofs_mst.py`, class `Correctness`: all three
equal an exhaustive minimum over the spanning trees of K_n, listed by Prüfer sequences in the test, on 70 seeded
weight matrices (n = 1..7, weights 1..3 or 1..100).

## 6. Time bounds

**Enumeration: Θ(n·C(m, n − 1)) = 2^Θ(n log n), m = n(n − 1)/2, under the `itertools.combinations` assumption.**
Each subset costs Θ(n): O(n) to generate it (the assumption: O(r) per tuple with r = n − 1, after an O(m) start), n
adjacency lists, n − 1 edges, the array `seen` and a depth-first search over at most n − 1 edges. The edge list costs Θ(n²) once, and
n² = O(n·C(m, n − 1)) because C(m, n − 1) ≥ m ≥ n for n ≥ 3. The binomial bounds below give 2^Θ(n log n).

**Binomial estimate (notes).** For n ≥ 2, with M = n(n − 1)/2 and k = n − 1 (so M/k = n/2):
(2/(e·n^(3/2)))·(en/2)^(n−1) ≤ C(M, k) ≤ (en/2)^(n−1), so C(M, k) grows like (en/2)^(n−1) up to polynomial factors.
*Proof.* Upper: C(M, k) ≤ M^k/k! ≤ (eM/k)^k, since e^k ≥ k^k/k!. Lower: C(M, k) = (M^k/k!)·Π_{i<k}(1 − i/M), and
Π_{i<k}(1 − i/M) ≥ 1 − Σ_{i<k} i/M = 1 − k(k − 1)/(2M) = 2/n. The trapezoid rule for the concave ln x gives
ln k! ≤ (k + 1/2) ln k − k + 1, i.e. k! ≤ e·k^(k+1/2)·e^(−k), so M^k/k! ≥ (eM/k)^k/(e·√k) ≥ (en/2)^(n−1)/(e·√n).
Multiply. ∎ The lower bound (n/2)^(n−1) ≤ C(M, k) also holds (each factor (M − i)/(k − i) ≥ M/k).

**Kruskal: O(m + S + m log n) time, where S is the number of comparisons of `sorted()`.** Building the keys costs
O(m); `sorted()` costs O(S) plus its own overhead; the scan makes at most m iterations with two `find` calls each.
*Union by size keeps every tree of height ≤ log₂ n:* a vertex gets one level deeper only when its root is linked
under a root whose tree is at least as large (`size[ru] ≥ size[rv]` after the swap), so the size of its tree at least
doubles; path halving only shortens paths. So each `find` costs O(log n), and the scan O(m log n). Under the
machine-model assumption that `sorted()` sorts m items in O(m log m) worst-case time (background in `entry.json`;
its sources support it but do not state it as a theorem for the current CPython sort), S and the sorting time are
O(m log m), which gives O(m log m) = O(n² log n) on K_n. Without that assumption only the lower bound below is
proved.

**Kruskal's worst case is Ω(m log m) = Ω(n² log n) (decision-tree argument).** *Claim:* for every n ≥ 2 there is a
weight assignment of K_n (with weights 1..m) on which `sorted()` makes at least ⌈log₂ m!⌉ comparisons, so that
`mst_kruskal` makes at least 3m + ⌈log₂ m!⌉ + (n − 1) counted operations (§2) and takes Ω(m log m) time.
*Machine-model assumption (background in `entry.json`).* `sorted()` is deterministic and learns about the keys
only from the outcomes of `<` comparisons. (The Python documentation's Sorting HOW-TO: "The sort routines use < when making comparisons between
two objects." Determinism is a premise about the runtime, like the documented semantics of `itertools` used
elsewhere.) So, for a fixed list length and a fixed key type, which comparison it makes next, and the final
arrangement, depend only on the outcomes of the comparisons made so far.
*Proof.* For every bijection ρ from the m edges to {1, …, m}, set the weight of
edge {u, v} to ρ({u, v}). The keys are then distinct and ordered like the weights, and the list passed to `sorted()`
always lists the edges in the same order (u < v, lexicographic), so the m! choices of ρ give the m! possible
relative orders of the list. Two of them with the same outcome sequence would be rearranged in the same way, but
their correct sorted arrangements differ, so all m! outcome sequences are distinct. The runs form a binary tree
whose leaves are the outcome sequences (no outcome sequence is a proper prefix of another, since the next step is
determined by the outcomes so far); a binary tree with m! leaves has a leaf at depth ≥ log₂ m!. Finally
log₂ m! ≥ m·log₂(m/e) (from e^m ≥ m^m/m!), and m·log₂(m/e) = Θ(n² log n) for m = n(n − 1)/2. The scan scans at least
the n − 1 keys it takes. ∎

**Prim: Θ(n²) time.** n − 1 rounds, each with two loops over all n vertices and O(1) work per step, plus Θ(n) to
copy row 0: Θ(n²), linear in the m = Θ(n²) input weights. Its counted cost is exactly (n − 1)² (§3).

**Consequence for the secondary tag T3 (Kruskal → Prim).** In the worst case over the inputs of each size n, the
counted cost (and the time) of this Kruskal is Ω(n² log n), while Prim's is exactly (n − 1)² (Θ(n²) time), so the
ratio grows without bound. This uses only the decision-tree lower bound above (under its machine-model assumption)
and Prim's exact count; the matching upper bound O(n² log n) for Kruskal holds under the background sort
assumption.

**Check.** `tests/test_proofs_mst.py`, class `KruskalLowerBound`: for n = 3 and n = 4, all m! weight assignments
with weights 1..m (6 and 720 of them): the largest number of comparisons inside `sorted()` (counted with the
harness's `CountingWeight`, minus the 3m packing operations and the scanned keys) is at least ⌈log₂ m!⌉ (3 and 10).
Class `Binomial`: the two binomial bounds for n = 2..60.

## 7. Prim is optimal on K_n (caveats)

**Model.** An algorithm reads the weights one entry at a time, and its steps (and output) depend only on n and on
the values it has read; each read is at least one step.

**Claim.** For n ≥ 2, every correct deterministic algorithm reads all n(n − 1)/2 weights of K_n on the instance with
every weight 2; so Θ(n²) is optimal up to a constant factor. The same holds for every run of a zero-error randomized
algorithm: fix its random bits; the run is then a deterministic computation that must be correct on both instances
below, and the same argument applies.

*Proof.* The all-2 instance has MST weight 2(n − 1). If an algorithm does not read the weight of edge e on it,
change that weight to 1: the algorithm reads the same values, so it follows the same steps and gives the same
output. But the new instance has MST weight 2n − 3: every spanning tree has n − 1 edges, at most one of weight 1,
so it weighs at least 1 + 2(n − 2) = 2n − 3, and a spanning tree containing e weighs exactly that. One of the two
outputs is wrong. ∎

**Check.** `tests/test_proofs_mst.py`, class `AdversaryInstance`: for n = 2..8, the all-2 K_n has MST weight
2(n − 1), and lowering any single edge to 1 gives 2n − 3, by all three implementations (the enumeration for n ≤ 6).

## 8. Space

Enumeration: the edge list (m pairs) is Θ(n²); per subset it holds n adjacency lists with 2(n − 1) entries, the
array `seen` and the stack, Θ(n). Kruskal: the sorted key list, Θ(n²), plus `parent` and `size`, Θ(n). Prim: `best`
and `in_tree`, Θ(n). **Check:** `tests/test_proofs_mst.py`, class `Space`: tracemalloc peaks grow by a factor
between 2.5 and 5 per doubling of n = 25, 50, 100 for Kruskal (Θ(n²)), and by less than 2.6 for Prim (Θ(n); the
Θ(n²) matrix is input and is built before tracing starts).

## 9. The harness oracle (Borůvka)

`harness._boruvka` breaks ties by the total order on (w, u, v). Let r(e) ∈ {0, …, m − 1} be the rank of edge e in the
order of (u, v), and w′(e) = m²·w(e) + r(e). Then w′ orders the edges exactly as (w, u, v) does, all w′ are distinct,
and for every spanning tree T, w′(T) = m²·w(T) + r(T) with 0 ≤ r(T) ≤ (n − 1)(m − 1) < m², so a tree of minimum w′
also has minimum w. Fix such a tree T*. In a round, the oracle computes for each component S of the current forest F
its w′-lightest leaving edge e_S (with respect to the forest at the start of the round), and then adds these edges,
skipping one whose ends are already joined. If F ⊆ T* at the start of the round, every e_S lies in T*: otherwise the
exchange in the proof of Lemma C (with S and the edge e′ ∈ T* on the cycle) gives a spanning tree of strictly
smaller w′, because w′(e_S) < w′(e′). So F stays inside T* and never closes a cycle. Every round with two or more
components adds at least one edge, so F ends with n − 1 edges, i.e. F = T*, and the oracle returns the minimum
spanning tree weight. `check` also requires (sum of the n − 1 lightest weights) ≤ answer ≤ (weight of the path
0–1–…–(n − 1)), which holds for every minimum spanning tree (it has n − 1 distinct edges, and the path is a spanning
tree).
