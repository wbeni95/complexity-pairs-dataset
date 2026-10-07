# Proofs: counting spanning trees, enumeration vs Kirchhoff

This file proves every claim that this entry makes about its problem and its two implementations (in `entry.json`,
`README.md` and the docstrings of the code), for every size of its domain, from the code in this folder: the exact
operation counts (sections 1 and 2), the correctness, time and space of the enumeration (sections 3 and 4), the
matrix-tree theorem (section 5), the correctness of the Kirchhoff–Bareiss implementation, including the absence of
row swaps on every graph (section 6), and the sizes of the numbers (section 7). Each proof is followed by the
deterministic scripts or tests that check it and the sizes they check it on. A check covers only those sizes; the
proofs cover the whole domain.

## Counting convention

`harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`), `__floordiv__` and `__rfloordiv__` add 1 to
the module counter `_ops` and return a new `CountingInt`; `__add__` (also bound as `__radd__`), `__sub__`,
`__rsub__` and `__neg__` return a new `CountingInt` without counting; comparisons and truth tests do not count.
`generate_scaling(n, rng)` returns the adjacency matrix of K_n with every entry (the zero diagonal included) a
`CountingInt`, and sets `_ops = 0`; `reported_cost(output)` returns `_ops`. A product or floor division with at least
one `CountingInt` operand counts 1 (with a plain left operand the int method returns `NotImplemented` and Python
calls the reflected method). Graphs are simple: A is a symmetric 0/1 matrix with zero diagonal, n ≥ 1 (the entry
excludes n = 0).

## 1. Enumeration: C(m, n − 1) edge subsets

**Statement.** For every graph with n ≥ 1 vertices and m edges, `count_spanning_trees_enumeration` examines exactly
C(m, n − 1) edge subsets (1,184,040 for K_8). On K_n, m = n(n − 1)/2 and
(n/2)^(n−1) ≤ C(n(n − 1)/2, n − 1) ≤ (en/2)^(n−1).

**Proof.** `edges` lists the m pairs u < v with `A[u][v]` true, and the loop runs once for each element of
`combinations(edges, n - 1)`, which yields every (n − 1)-subset exactly once (documented behaviour of
`itertools.combinations`, a machine-model assumption in `entry.json`): C(m, n − 1) iterations (C(28, 7) =
1,184,040 for K_8). For the bounds let M = n(n − 1)/2 and k = n − 1 ≥ 1, so M/k = n/2 and M ≥ k for n ≥ 2. Then
C(M, k) = Π_{i=0..k−1} (M − i)/(k − i) and each factor is ≥ M/k, which gives the lower bound; and
C(M, k) ≤ M^k/k! ≤ (eM/k)^k, since e^k ≥ k^k/k! (one term of the series of e^k). For n = 1 both sides are 1.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "spanning-tree enumeration:
C(m, n-1) subsets examined": n = 1..8 on K_n and on 3 seeded random graphs per n. (The enumeration's V2 is a timing
fit, not a count.)

## 2. Kirchhoff–Bareiss: (n − 2)(n − 1)(2n − 3)/2 multiplications and exact divisions on every connected graph

**Statement.** For every connected graph with n ≥ 1 vertices whose adjacency entries are `CountingInt` values,
`count_spanning_trees_kirchhoff` makes exactly (n − 2)(n − 1)(2n − 3)/2 counted multiplications and exact
divisions, and no row swap occurs; on a disconnected graph it makes at most that many. On K_n for the V2 sizes
n = 16, 32, 64, 128 these are 3045, 28365, 244125, 2024253.

**Proof.** Let N = n − 1. L0 is the N × N matrix with `sum(A[i])` on the diagonal and `-A[i][j]` elsewhere, that
is the Laplacian L = D − A without the row and column of vertex n − 1; for n ≥ 2 all its entries are `CountingInt`
(`sum` adds `CountingInt` values to the plain 0 through `__radd__`; `-A[i][j]` calls `__neg__`), and building it
counts nothing. For n = 1 and n = 2 the routine makes no product (N = 0 returns at once, N = 1 has no loop step),
and the formula gives 0.

*L0 is positive definite for a connected graph.* For real x_0, …, x_{N−1}, set x_{n−1} = 0. Then
xᵀ L0 x = Σ_i deg(i) x_i² − 2 Σ_{i<j<n−1} A_ij x_i x_j = Σ over edges uv of (x_u − x_v)². This is 0 only if x is
constant along every edge, hence on the connected graph constant, hence 0 because x_{n−1} = 0.

*Its leading principal minors are positive.* A leading principal submatrix P of L0 is positive definite (take x
supported on its indices). A positive definite matrix P = [[p, qᵀ], [q, R]] has p = e₁ᵀ P e₁ > 0, and its Schur
complement R − q qᵀ/p is positive definite (for y ≠ 0, the vector x = (−qᵀy/p, y) gives
yᵀ(R − q qᵀ/p)y = xᵀ P x > 0); by Schur's formula (Lemma B of
[the planar matchings entry's PROOFS.md](../planar-perfect-matchings-enumeration-vs-kasteleyn/PROOFS.md))
det P = p · det(R − q qᵀ/p), which is positive by induction on the size.

*Counting.* `_bareiss_det` here is the same routine as in the planar matchings entry (only the names `N`, `a` differ
from `m`, `f`), so Lemma B applies: by B.3 no swap occurs and the loop runs to the end, and by B.1 it makes exactly
(N − 1)N(2N − 1)/2 = (n − 2)(n − 1)(2n − 3)/2 counted operations. On a disconnected graph the loop may stop early
(B.1): at most that many.

**Check.** `experiments/2026-10-07b_spanning_tree_counts.py` (K_n for n = 1..70 and 128, and random connected graphs).
`experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "Kirchhoff (n-2)(n-1)(2n-3)/2": n = 1..70 and 128 (includes the V2 sizes n = 16, 32, 64, 128;
n = 0 reported as outside the domain); group `extra`, line "Kirchhoff (n-2)(n-1)(2n-3)/2 on random connected graphs":
n = 2..29. `experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "Kirchhoff: no swap and the exact
count on random connected graphs, at most the count on disconnected ones": n = 2..30, 3 seeded connected and 3
seeded disconnected graphs per n.

## 3. Enumeration: correctness

*Forests.* A graph with n vertices and k edges has at least n − k components, with equality iff it is acyclic (add
the edges one at a time: an edge joining two components lowers the count by 1 and closes no cycle, an edge inside a
component keeps the count and closes a cycle). So an (n − 1)-edge set is a spanning tree iff it is acyclic, and
every spanning tree has n − 1 edges.

*Union-find.* With a fresh `parent`/`size` pair per subset, the trees of the union-find structure always have the
components of the edges processed so far as their vertex sets: `_find` returns the root of x's tree (path halving
re-points x to its grandparent in the same tree), and a processed edge links two different roots. An edge closes a
cycle iff its ends are already in one component, i.e. iff `ru == rv`, where the subset is rejected; otherwise the
`else` branch of the loop counts it. `combinations(edges, n - 1)` yields every (n − 1)-subset of the m edges exactly
once (the `itertools` assumption), so the count is τ(G). For n = 1 the only subset is the empty one, counted once (τ = 1); if m < n − 1 there is no
subset and the answer is 0. ∎

## 4. Enumeration: time and space

**Union by size keeps every tree of height ≤ log₂ n.** A vertex gets one level deeper only when its root is linked
under a root whose tree is at least as large (`size[ru] ≥ size[rv]` after the swap), so the size of its tree at least
doubles; path halving only shortens paths. So each `_find` costs O(log n).

**Bounds.** Building the edge list reads n(n − 1)/2 matrix entries: Θ(n²). Each subset costs O(n) to generate
(the `itertools` assumption: O(r) per tuple with r = n − 1, after an O(m) start), Θ(n) to create `parent` and
`size`, plus at most n − 1 edges with two `_find` calls each: Θ(n) and O(n log n). So the time is
O(n² + n·log n·C(m, n − 1)) under that assumption, and Ω(n² + n·C(m, n − 1)), the bounds stated in the entry. For fixed n,
C(m, n − 1) is non-decreasing in m ≤ n(n − 1)/2, so the bounds are largest on K_n, where §1 gives
(n/2)^(n−1) ≤ C(n(n − 1)/2, n − 1) ≤ (en/2)^(n−1): 2^Θ(n log n).

**Space.** The edge list (m pairs), the pool and index state of `combinations` (m + n − 1 entries), one subset tuple
and the two arrays: Θ(m + n) besides the input.

**Check.** `tests/test_proofs_stc.py`, class `UnionFind`: with the module's own `_find` and the same linking rule, every
tree height stays ≤ log₂ n over 200 seeded random union sequences (n = 2..64). Class `Space`: the tracemalloc peak of
the enumeration on cycles with two chords grows by less than a factor 3 per doubling of n = 10, 20, 40 (Θ(m + n)).

## 5. The matrix-tree theorem

Let G be a graph on V = {0, …, n − 1} (n ≥ 2) with edges e_1, …, e_m. Orient each edge e = uv arbitrarily and let B
be the n × m incidence matrix: B[u][e] = 1, B[v][e] = −1, all other entries 0. Then B·Bᵀ = L = D − A (the diagonal
entry v counts the edges at v; the entry (u, v), u ≠ v, is −1 for an edge uv and 0 otherwise). For a vertex r let
B_r be B without row r; then B_r·B_rᵀ = L_r, the Laplacian without row and column r.

**Cauchy–Binet.** For a k × m matrix P and an m × k matrix Q, det(PQ) = Σ_{|S| = k} det(P[:, S])·det(Q[S, :]).
*Proof.* By multilinearity of the determinant in the columns of PQ, whose column j is Σ_l Q[l][j]·P[:, l],
det(PQ) = Σ_{f: [k] → [m]} (Π_j Q[f(j)][j])·det(P[:, f(1)], …, P[:, f(k)]). Terms with f not injective have a repeated
column and vanish; grouping the injective f by their image S and their order gives Σ_S det(P[:, S])·det(Q[S, :]). ∎

**Lemma T.** For every set S of n − 1 edges, det B_r[:, S] = ±1 if S is a spanning tree and 0 otherwise.

*Proof.* If S is not a spanning tree, it is disconnected (§3), so some component C of (V, S) does not contain r. The
sum of the rows of B_r[:, S] over the vertices of C is 0: an edge of S inside C contributes +1 and −1, and no edge of
S leaves C. So the rows are dependent and the determinant is 0. If S is a spanning tree, induct on n: for n = 2 the
matrix is (±1). For n ≥ 3, a tree has at least two leaves, so there is a leaf v ≠ r; its row has a single non-zero
entry, ±1, in the column of its edge e. Expanding along that row leaves ±det of the matrix of the tree S − e on
V − {v} with row r deleted, which is ±1 by induction. ∎

**Theorem (matrix-tree theorem; Kirchhoff 1847).** For every r, det L_r = τ(G).
*Proof.* By Cauchy–Binet with P = B_r and Q = B_rᵀ, det L_r = Σ_{|S| = n−1} (det B_r[:, S])², which by Lemma T is the
number of spanning trees. ∎ For a disconnected graph τ = 0, so det L_r = 0.

**All cofactors are equal.** Every cofactor (−1)^(i+j)·det L^(i,j) of L (row i and column j deleted, i = j or not)
equals τ(G). *Proof.* Let adj(L) be the matrix of cofactors (transposed), so L·adj(L) = adj(L)·L = det(L)·I = 0,
because L·1 = 0 makes L singular. If rank L ≤ n − 2, every (n − 1) × (n − 1) minor is 0, so all cofactors are 0. If
rank L = n − 1, the kernel of L is spanned by the all-ones vector 1; every column of adj(L) lies in it, so every
column is constant, and since L is symmetric the same holds for the rows (adj(L)·L = 0). So all entries of adj(L) are
equal, to the principal cofactor det L_r = τ(G). ∎

## 6. Kirchhoff–Bareiss: correctness, no row swap on any graph, time

`count_spanning_trees_kirchhoff` builds L0 = L_{n−1} (the row and column of the last vertex removed) and returns
`_bareiss_det(L0)`, which is det L0 by Lemma B of
[the planar matchings entry's PROOFS.md](../planar-perfect-matchings-enumeration-vs-kasteleyn/PROOFS.md) (the
routine is the same; B.4 if the loop runs to the end, B.2 if it returns 0). By §5, det L0 = τ(G). For n = 1, L0 is the
0 × 0 matrix and the function returns 1 = τ. ∎

**The swap branch is never taken, on connected and disconnected graphs alike.** L0 is symmetric and positive
semidefinite: xᵀ L0 x = Σ over edges uv of (x_u − x_v)² (with x_{n−1} = 0). Suppose the loop reaches step k with no
swap so far. By the invariant of Lemma B, `prev` = det C for the leading k × k block C of L0 (C empty and `prev` = 1
for k = 0), and `prev` ≠ 0 (it is 1 or an earlier pivot that passed the zero test), so C is invertible. Write
L0 = [[C, Q], [Qᵀ, D]] and S = D − Qᵀ C⁻¹ Q. By Schur's formula applied to the minors of the invariant,
`M[i][j]` = det C · S[i − k][j − k] for i, j ≥ k. S is positive semidefinite: for any y, the vector
x = (−C⁻¹Q y, y) gives xᵀ L0 x = yᵀ S y ≥ 0. If the pivot `M[k][k]` is 0, then S[0][0] = 0, and positive
semidefiniteness forces the whole first column of S to be 0 (each 2 × 2 principal minor S[i][i]·S[0][0] − S[i][0]²
must be ≥ 0), so every `M[r][k]` (r > k) is 0: the routine returns 0 without swapping. So on reduced Laplacians the
routine never swaps. It returns early only when a leading principal minor of L0 of order at most n − 2 is 0, which by
§2 (all leading principal minors are positive on connected graphs) happens only on disconnected graphs.

**Time.** Building L0 costs Θ(n²) additions (`sum(A[i])` over n entries for each of the n − 1 rows) and negations.
The elimination makes exactly (n − 2)(n − 1)(2n − 3)/2 multiplications and exact divisions on every connected graph
and at most that many otherwise (§2): Θ(n³) arithmetic operations in the worst case, attained on every connected
graph.

**Check.** `tests/test_proofs_stc.py`, class `MatrixTree`: on 84 seeded random graphs (n = 1..7, including
disconnected ones), both implementations equal a spanning-tree count by subset enumeration written in the test, and
every cofactor, principal (det L_r, r = 0..n − 1) and off-diagonal ((−1)^(i+j)·det L^(i,j), i ≠ j), computed by
exact rational elimination in the test, equals it; Lemma T is checked on
every (n − 1)-subset of 30 graphs with n ≤ 6. Class `NoSwap`: the zero-pivot search of the routine (the module-level
name `next`, replaced by a counting wrapper; the implementation file is unchanged) is never entered on 200 connected
graphs and, on 200 disconnected graphs, is entered at most once per graph and never finds a row (n = 2..20; it is
entered on 162 of them; on the others the loop reaches the end and the last pivot is 0).

## 7. Sizes of the numbers, bit complexity

Every row of L0 has the degree d ≤ n − 1 on the diagonal and at most d entries −1, so its Euclidean norm is √(d² + d) ≤
√(n(n − 1)) < n. By Hadamard's inequality (proof in §7 of the planar matchings entry's PROOFS.md) every k × k minor
of L0 with k ≥ 1 is below n^k ≤ n^(n−1) in absolute value. By the invariant of Lemma B every stored entry is such a
minor (rows permuted), and a product before a division is below n^(2(n−1)), so a difference of two products is below
2·n^(2(n−1)): all values have O(n log n) bits. The answer satisfies τ(G) ≤ τ(K_n) = n^(n−2) (every spanning tree of
G is one of K_n; Cayley's formula, proved in §1 of the minimum-spanning-tree entry's PROOFS.md), so it has at most
(n − 2)·log₂ n + 1 bits. With M(b) bounding the cost of one multiplication or exact division of b-bit integers
(O(b²) for schoolbook arithmetic), the bit complexity is O(n³·M(n log n)), i.e. O(n⁵ log² n) with schoolbook
arithmetic: polynomial in the n²-bit input. Space: (n − 1)² integers of O(n log n) bits.

**Check.** `tests/test_proofs_stc.py`, class `NumberSizes`: with the entries wrapped in a type that records the largest
absolute value of every stored quotient and every intermediate product or difference, on K_n (n = 2..30) and 60
seeded random graphs: stored values < n^(n−1), intermediates < 2·n^(2(n−1)), and the answer ≤ n^(n−2). Class `Space`:
the tracemalloc peak of the Kirchhoff function on K_n grows by a factor between 3 and 8 per doubling of n = 16, 32, 64
(Θ(n²) integers whose size grows with n).
