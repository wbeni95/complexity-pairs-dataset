# Proofs: planar perfect matchings, enumeration vs Kasteleyn

This file proves every claim that this entry makes about its problem and its two implementations (in `entry.json`,
`README.md` and the docstrings of the code), for every size of its domain, from the code in this folder: the exact
operation counts (sections 1, 2 and 4), Bareiss's elimination (section 3, Lemma B), the correctness and bounds of
the enumeration (section 5), Kasteleyn's sign lemma for the a × b grid and its spanning subgraphs (section 6, proved
for exactly the graphs this entry uses), the sizes of the numbers and the bit complexity (section 7), and the
exactness of the harness oracle (section 8). Each proof
is followed by the deterministic scripts or tests that check it and the sizes they check it on. A check covers only
those sizes; the proofs cover the whole domain. `entry.json` already outlines the ladder count in
`algorithms[0].correctness`; the proofs below give the steps that the outline leaves out. The #P-completeness of
the permanent is background in `entry.json`, not a claim.

## Counting convention

`harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`), `__floordiv__` and `__rfloordiv__` add 1 to
the module counter `_ops` and return a new `CountingInt`; additions, subtractions, negations, `abs`, comparisons and
truth tests return values without counting. `generate_scaling(n, rng)` (n even, n ≥ 2) returns the unit-weight
(n/2) × 2 ladder (`ladder(n // 2)`) with every entry of the N × N weight matrix W wrapped in `CountingInt`, zeros
included, and sets `_ops = 0`; `reported_cost(output)` returns `_ops`.

A product or floor division with at least one `CountingInt` operand counts 1 (with a plain left operand the int
method returns `NotImplemented` and Python calls the reflected method), and its result is a `CountingInt`; so is
every sum, difference or negation with a `CountingInt` operand. Vertex u = r·b + c in an a × b grid.

## 1. Enumeration on the m × 2 ladder: L(m + 2) − 3 multiplications (m = n/2)

**Statement.** For every m ≥ 1, `count_perfect_matchings_enumeration` on the unit m × 2 ladder makes exactly
L(m + 2) − 3 = φ^(m+2) + (−1/φ)^(m+2) − 3 counted multiplications (L = Lucas numbers, L(0) = 2, L(1) = 1); with
m = n/2 these are the values 120, 319, …, 710644 listed in `entry.json` for n = 16, …, 52. The ladder has F(m + 1)
perfect matchings (F = Fibonacci numbers, F(1) = F(2) = 1).

**Proof.** Every multiplication is `W[u][v] * extend(u + 1)` with the `CountingInt` factor `W[u][v]`, executed once per
child of a node of the search tree; the test `W[u][v]` is a truth test (not counted). Let E(k) be the number of
multiplications made by a call whose first unmatched vertex is the left cell of a row with k ≥ 0 free rows below and
including it, all rows above being matched (the root call has k = m).
- k = 0: `u == N`, return 1, no multiplication: E(0) = 0.
- The left cell u = (r, 0) has the partners u + 1 (right cell, `c + 1 < b`) and, if k ≥ 2, u + 2 (left cell of the
  next row). Right partner: 1 multiplication, and `extend(u + 1)` skips the matched right cell and starts at the next
  row: 1 + E(k − 1). Lower partner: 1 multiplication, then `extend(u + 1)` starts at the right cell (r, 1), whose only
  partner is (r + 1, 1) (no right neighbour, `c + 1 < b` fails), unmatched: 1 more multiplication, after which the
  next unmatched vertex is the left cell of row r + 2: 2 + E(k − 2).

So E(1) = 1 and E(k) = E(k − 1) + E(k − 2) + 3 for k ≥ 2. U(k) = E(k) + 3 satisfies U(k) = U(k − 1) + U(k − 2),
U(0) = 3 = L(2), U(1) = 4 = L(3), hence U(k) = L(k + 2) and E(m) = L(m + 2) − 3; the closed form is Binet's formula
L(k) = φ^k + (−1/φ)^k, which satisfies the same recursion and initial values. The leaves (complete matchings) satisfy
T(k) = T(k − 1) + T(k − 2), T(0) = T(1) = 1, so T(m) = F(m + 1).

**Check.** `experiments/2026-10-06f_entries_planar_matchings.py` (the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "ladder enumeration L(n/2+2)-3": n = 2, 4, …, 60 (includes the V2 sizes n = 16, 20, …, 52).
`experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "ladder answers: F(m+1) matchings on the m x 2
ladder, >= 2^(N/4) on even grids": m = 1..30, and the even grids a, b ∈ {2, 4, 6}.

## 2. Enumeration on the 2 × m ladder: F(m + 3) − 2 + ((m − 1)F(m) + 2mF(m − 1))/5 multiplications

**Statement.** For every m ≥ 1, `count_perfect_matchings_enumeration` on the unit 2 × m ladder (the same graph with
a = 2 rows of m vertices) makes exactly F(m + 3) − 2 + ((m − 1)F(m) + 2mF(m − 1))/5 counted multiplications
(684816 for m = 24, against 271440 for the 24 × 2 ladder).

**Proof.** While row 0 has an unmatched vertex, the first unmatched vertex u = (0, c) is in row 0 (row 0 has the
smaller indices), every vertex left of it in row 0 is matched, and its partners are (0, c + 1) (if c + 1 < m, always
unmatched then) and (1, c) (always unmatched then, since a vertex (1, c') is matched only together with (0, c')).
So the row-0 phase chooses, from left to right, a part of length 2 (horizontal edge) or 1 (vertical edge), one
multiplication per part, and never gets stuck (the vertical edge is always available). Its search tree has one edge
for every composition of some p ∈ {1, …, m} into parts 1 and 2 (the parts chosen so far), and there are F(p + 1)
such compositions, so the row-0 phase makes Σ_{p=1..m} F(p + 1) = F(m + 3) − 2 multiplications (using
Σ_{i=1..N} F(i) = F(N + 2) − 1).

Once row 0 is matched, the unmatched vertices of row 1 are exactly the columns under the horizontal edges of row 0,
which come in adjacent pairs (c, c + 1). The first unmatched vertex (1, c) has no lower neighbour and its right
neighbour (1, c + 1) is unmatched, so it is matched to it with one multiplication; this repeats without dead ends.
So every complete composition of m adds one multiplication per part 2. The total number H(m) of parts 2 over all
compositions of m satisfies H(m) = H(m − 1) + H(m − 2) + F(m − 1) (first part 1, or first part 2 followed by one of
the F(m − 1) compositions of m − 2), H(1) = 0, H(2) = 1. G(m) = ((m − 1)F(m) + 2mF(m − 1))/5 gives G(1) = 0,
G(2) = 1, and, using F(m − 3) = F(m − 1) − F(m − 2),
5G(m − 1) + 5G(m − 2) + 5F(m − 1) = (3m − 1)F(m − 1) + (m − 1)F(m − 2) = (m − 1)F(m) + 2mF(m − 1) = 5G(m),
so H = G. Total F(m + 3) − 2 + G(m). For m = 24: F(27) − 2 + G(24) = 196416 + 488400 = 684816.

**Check.** `experiments/2026-10-06f_entries_planar_matchings.py` (m = 1..24). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "2 x m ladder enumeration F(m+3)-2+((m-1)F(m)+2mF(m-1))/5": m = 1..24.

## 3. Lemma B: the Bareiss routine `_bareiss_det`

**Lemma B.** Let M be an m × m integer matrix (m ≥ 1) passed to `_bareiss_det`.
1. If the loop runs through all k = 0, …, m − 2 without returning, it makes exactly 3·Σ_{t=1..m−1} t² =
   (m − 1)m(2m − 1)/2 multiplications and floor divisions, and fewer if it returns early. On `CountingInt` entries
   each of them counts 1.
2. It returns early (the `swap is None` branch) only if det M = 0.
3. If every leading principal minor of M is non-zero, it never swaps and never returns early.
4. If it does not return early, it returns det M exactly.

**Proof.** *1.* Step k updates the entries (i, j), k < i, j ≤ m − 1, each with `row_i[j] * pivot`, `f * row_k[j]` and
`// prev`: 3(m − 1 − k)² operations; summing over k gives 3·Σ_{t=1..m−1} t². On `CountingInt` entries every entry
of M stays a `CountingInt`, and `prev` is the plain 1 at k = 0 and a `CountingInt` pivot later, so all of them count.
The zero test and the swap search only compare.

*Schur's formula.* For an invertible k × k block C, [[C, Q], [R, D]] = [[I, 0], [R C⁻¹, I]] · [[C, Q], [0, D − R C⁻¹ Q]],
so det [[C, Q], [R, D]] = det C · det(D − R C⁻¹ Q).

*Invariant.* Before step k, let A' be M's input with its rows permuted by the swaps made so far (a swap at step k'
exchanges two rows ≥ k'). Then for all i, j ≥ k, `M[i][j]` = det A'[{0..k−1, i}, {0..k−1, j}], and
`prev` = det A'[0..k−1, 0..k−1] ≠ 0. This holds at k = 0 (empty minors are 1). Assume it before step k, and let
C = A'[0..k−1, 0..k−1].
- A swap of rows k and r > k of M exchanges two rows whose entries in columns ≥ k are minors involving original rows
  k and r only, so it is the same as swapping those rows of A'; the invariant is kept.
- If `M[k][k]` and every `M[r][k]` (r > k) are 0, then by Schur's formula, for every i ≥ k,
  0 = det A'[{0..k−1, i}, {0..k−1, k}] = det C · (A'[i][k] − A'[i][0..k−1] C⁻¹ A'[0..k−1][k]). With
  v = C⁻¹ A'[0..k−1][k], column k of A' equals A'[·][0..k−1] v in every row (rows < k by the definition of v), so
  det A' = 0 and det M = ± det A' = 0. This proves 2.
- Otherwise `pivot` = det A'[0..k, 0..k] ≠ 0. For i, j > k let B = A'[{0..k, i}, {0..k, j}] with core C and 2 × 2
  Schur complement S (rows k, i; columns k, j). By Schur's formula det B = det C · det S, and each minor keeping one
  of the rows k, i and one of the columns k, j equals det C times the corresponding entry of S. Hence
  `M[i][j] * pivot − M[i][k] * M[k][j]` = (det C)² · det S = `prev` · det B, the division is exact, and the new
  `M[i][j]` is det B. With the new `prev` = `pivot`, the invariant holds before step k + 1.

*3.* If no swap happened before step k, A' = M and `M[k][k]` = det M[0..k, 0..k] ≠ 0, so step k does not swap; by
induction no step swaps or returns early.

*4.* After the last step the invariant (with k = m − 1) gives `M[m-1][m-1]` = det A', and each swap changes the sign
of the determinant once, which `sign` records; so the returned value is det M.

## 4. Kasteleyn–Bareiss: (m − 1)m(2m − 1)/2 = (N − 2)N(N − 1)/8 multiplications and divisions

**Statement.** For every instance with N vertices whose weight matrix entries are `CountingInt` values,
`count_perfect_matchings_kasteleyn` makes exactly (m − 1)m(2m − 1)/2 = (N − 2)N(N − 1)/8 counted multiplications and
exact divisions (m = N/2) when the answer is non-zero, whatever row swaps occur; at most that many when the answer is
0; none for odd N. On the V2 sizes n = 16, 32, 64, 128, 256 these are 420, 3720, 31248, 256032, 2072640.

**Proof.** N = 0 returns 1 and odd N returns 0 before any operation (the formula also gives 0 at N = 0). For even
N ≥ 2, K is the m × m matrix of entries `W[x][y]` or `-W[x][y]`, all `CountingInt`; building it only negates. The
function returns |`_bareiss_det(K)`|. If the elimination returns early, the result is 0. So whenever the returned
value is non-zero the loop has run to the end, and Lemma B.1 gives exactly (m − 1)m(2m − 1)/2 counted operations,
independently of the swaps; if the returned value is 0 the loop may have stopped early: at most that many. The
returned value is the answer: by Lemma B.4 it is |det K|, and |det K| is the weighted number of perfect matchings by
Lemma K (§6). With m = N/2, (m − 1)m(2m − 1)/2 = (N − 2)N(N − 1)/8.

**Check.** `experiments/2026-10-06f_entries_planar_matchings.py` (n = 2..120 even and 256, and 297 random even-N
instances with non-zero answers, 53 with a row swap). `experiments/2026-10-07_closed_form_checks.py`, group `expdp`,
line "Kasteleyn (n-2)n(n-1)/8": n = 2, 4, …, 120 and 128, 256 (includes the V2 sizes).
`experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "Kasteleyn count on random grids: = form if
answer != 0, <= form if 0": 300 seeded random weighted grids with even N ≤ 64 (weights 0..3, zeros included).

## 5. Enumeration: correctness and bounds

**Correctness.** The vertices matched at a call are exactly the ends of the edges chosen on the way to it, so a leaf
(`u == N`) corresponds to a perfect matching, the set of its chosen edges. Let M be a perfect matching of the grid
graph whose edges all have non-zero weight, and consider a call reached by choosing only edges of M. Its first
unmatched vertex u has its M-partner among its later neighbours u + 1 (if c + 1 < b) and u + b (if r + 1 < a),
because every vertex before u is matched (by edges of M); that partner is still unmatched, so exactly one child
chooses the M-edge of u, and the other child gives u a different partner, hence leads only to other matchings. By
induction M is reached at exactly one leaf. A leaf (`u == N`) returns 1,
and `total = total + W[u][v] * extend(u + 1)` multiplies the weights along the path: the sum over the leaves is
Σ_M Π_{e ∈ M} W(e). Edges of weight 0 are skipped; they contribute only zero products. N = 0: the root is a leaf
(answer 1). N odd: every leaf would match all N vertices in pairs, impossible, so the answer is 0. ∎

**O(N·2^(N/2)) on every instance.** Each node has at most 2 children, and each level of the tree matches 2 vertices,
so the depth is at most N/2 and there are fewer than 2^(N/2+1) nodes. A node costs O(N) (the scan for the next
unmatched vertex) plus O(1). So the time is O(N·2^(N/2)) for N ≥ 1; along a root-to-leaf path the scans only move
forward (each call starts at u + 1 of its parent), as the docstring says.

**At least the number of perfect matchings.** Every perfect matching with non-zero weights is a distinct leaf
(above). On unit weights: the m × 2 ladder has F(m + 1) perfect matchings (§1), Θ(φ^m) = Θ(φ^(N/2)) by Binet's
formula; an a × b grid with a, b even splits into N/4 disjoint 2 × 2 blocks, each with its 2 perfect matchings (two
horizontal or two vertical edges), and independent choices give 2^(N/4) distinct perfect matchings.

**Prime N.** If N is prime, the only shapes are 1 × N and N × 1, both paths, in which each vertex has at most one
later neighbour: the tree is a single path of at most N/2 + 1 nodes, and the scans move forward along it, so the time
is O(N).

**Uncounted work on the ladder family.** On the unit m × 2 ladder (u = 2r + c) each call of `extend` makes O(1)
list operations, comparisons and truth tests besides its scan, and the scan (`u += 1`) takes at most 2 steps: the
root starts at the unmatched vertex 0; after the horizontal edge (r, 0)–(r, 1) the child starts at the matched
(r, 1) and stops at (r + 1, 0) or at N (1 step); after the vertical edge (r, 0)–(r + 1, 0) the child starts at the
unmatched (r, 1) (0 steps), whose only partner is (r + 1, 1), and its child starts at the matched (r + 1, 0), passes
the matched (r + 1, 1) and stops at row r + 2 or at N (2 steps). The non-root calls are exactly the counted
multiplications, so each of these kinds of work is O(1) per counted operation, as the caveats state.

**Space.** The array `matched` (N entries) and the recursion, at most N/2 + 1 frames deep: Θ(N) besides the input,
plus the subtotals, each at most the answer for a sub-grid, of O(N·log(2·w_max)) bits (§7).

**Check.** `tests/test_proofs_planar.py`, class `EnumerationTree`: on 120 seeded random grids (N ≤ 20, weights 0..3)
the number of `extend` calls is below 2^(N/2+1) and at least the number of leaves with a perfect matching (counted
by the test), and the recursion depth is at most N/2 + 1; on 1 × N and N × 1 paths with prime N ≤ 31 there are at
most N/2 + 1 calls; on the m × 2 ladders (m = 1..20) the scan step `u += 1` (counted with `sys.settrace`) runs at most
2 times per call. The counts F(m + 1) and 2^(N/4) are checked by the count-check script named in §1.

## 6. Kasteleyn's signs on the a × b grid

The entry uses the signs on the full a × b grid (all 2N − a − b grid edges) for every instance; weight 0 only
removes terms. We prove the sign lemma for exactly these graphs: the a × b grid graphs and their spanning subgraphs.

**Setup.** Black vertices: r + c even; white: r + c odd; every grid edge joins a black and a white vertex. If N is odd
there are (N + 1)/2 black vertices, so there is no perfect matching and the answer 0 is returned directly. Let N be
even, m = N/2, black = (x_0, …, x_{m−1}) and white = (y_0, …, y_{m−1}) in index order, and
K[i][j] = ε(x_i y_j)·W[x_i][y_j], with ε = −1 on the vertical edges (r, c)–(r + 1, c) with c odd and ε = +1 on all other
pairs (W is 0 on non-neighbours). By the Leibniz formula,
det K = Σ_σ sgn(σ) Π_i K[i][σ(i)] over the permutations σ of {0..m − 1}. A term is non-zero only if every x_i y_σ(i)
is a grid edge with non-zero weight, i.e. σ comes from a perfect matching M (σ_M(i) = the index of x_i's partner);
its term is sgn(σ_M)·ε(M)·w(M), with ε(M) = Π_{e ∈ M} ε(e) and w(M) = Π_{e ∈ M} W(e) ≥ 0. Weight-0 edges give zero
terms, so the sum may run over all perfect matchings M of the full grid.

**Lemma K.** sgn(σ_M)·ε(M) is the same for all perfect matchings M of the a × b grid. Hence det K = ±Z, and Z = |det K|
because Z ≥ 0.

*Proof.* Let M, M′ be perfect matchings. Every vertex has degree 0 or 2 in the symmetric difference M Δ M′, so M Δ M′
is a disjoint union of simple cycles C_1, …, C_q, each alternating between M and M′ edges; a cycle with 2l edges has
l black vertices.

*Permutation part.* σ_{M′}^(−1) ∘ σ_M maps each black vertex x to the black vertex matched by M′ to M(x)'s white
partner; it fixes the black vertices outside the cycles and is an l-cycle on the black vertices of each C_j. So
sgn(σ_M)·sgn(σ_{M′}) = Π_j (−1)^(l_j − 1).

*Sign part.* ε(M)·ε(M′) = Π_{e ∈ M Δ M′} ε(e) (common edges appear twice) = Π_j ε(C_j), where ε(C) is the product of
the signs around C.

*A unit square has sign product −1:* its two horizontal edges have +1, and its vertical edges lie in columns c and
c + 1, one of which is odd: (−1)^c·(−1)^(c+1) = −1.

*A cycle.* A simple cycle C of the grid graph is a simple closed polygon made of unit segments; let f be the number of
unit squares inside it and p the number of grid vertices strictly inside. Each edge of C borders exactly one unit
square inside C, and each grid edge strictly inside C borders two of them (both inside). So the product of the
square sign products over the f inside squares is ε(C) (inner edges cancel): ε(C) = (−1)^f. Counting edge–square
incidences, 4f = 2l + 2·(number of inner edges), so there are 2f − l inner edges. The plane graph formed by C and
everything inside it is connected (from an inside vertex, walk right along its row until the first vertex of C; the
edges walked lie inside C), and its faces are the f inside squares and the outer face. Euler's formula
V − E + F = 2 gives (2l + p) − (2l + 2f − l) + (f + 1) = 2, so f = p + l − 1. Therefore the cycle contributes
(−1)^(l−1)·ε(C) = (−1)^(l−1)·(−1)^(p+l−1) = (−1)^p.

*p is even.* Every vertex of C is matched by M along C (C alternates). A grid edge from a vertex strictly inside C to
a vertex strictly outside would have to cross C, but grid edges meet C only at grid vertices and a unit edge has no
grid vertex in its interior; so M matches the p inside vertices among themselves, and p is even.

So sgn(σ_M)·ε(M) = sgn(σ_{M′})·ε(M′)·Π_j (−1)^(p_j) = sgn(σ_{M′})·ε(M′). ∎

The returned value is |`_bareiss_det`(K)| = |det K| (Lemma B.4, or 0 = det K after an early return, Lemma B.2),
which is Z by Lemma K. For N = 0 the function returns 1 (the empty matching). ∎

**Without the signs.** The same expansion without ε gives Σ_σ Π_i W[x_i][y_σ(i)] = Σ_M w(M): the count is the
permanent of the black × white weight matrix (the boundary remark in `relationship`).

**Check.** `tests/test_proofs_planar.py`, class `SignLemma`: for every shape with N even and N ≤ 16 (a, b ≥ 1),
sgn(σ_M)·ε(M) is computed for every perfect matching M (listed by the test's own search) and is the same within each
shape; and class `Permanent`: the permanent of the black × white weight matrix equals the implementations' answer on
60 seeded random weighted grids with N ≤ 12.

## 7. Sizes of the numbers, bit complexity

**Hadamard's inequality.** |det A| ≤ Π_i ‖a_i‖ for the rows a_i of a real square matrix (trivial if A is singular;
otherwise Gram–Schmidt on the rows writes A = L·Q with L lower triangular, Q with orthonormal rows, and
|L_ii| ≤ ‖a_i‖, so |det A| = Π_i |L_ii|). Each row of K has at most 4 non-zero entries
of absolute value ≤ w_max, so every row of every square submatrix of K has norm ≤ 2·w_max.

**Bounds.** By the invariant of Lemma B, every entry stored by Bareiss is a (k + 1) × (k + 1) minor of K with its rows
permuted (k + 1 ≤ m), so its absolute value is at most (2·w_max)^(k+1) ≤ (2·w_max)^(N/2) (w_max ≥ 1; for w_max = 0
everything is 0). A product before a division multiplies two such values, and the difference of two products is at
most 2·(2·w_max)^N. So every value has O(N·log(2·w_max)) bits. The answer is at most (2·w_max)^(N/2) as well
(the input-size remark). The input has N² entries, of which the 2N − a − b grid edges appear twice:
a(b − 1) + b(a − 1) = 2N − a − b.

**Bit complexity.** Θ(N³) arithmetic operations (§4) on integers of O(N·log(2·w_max)) bits, plus Θ(N²) reads and
negations of input entries: O(N³·M(N·log(2·w_max))), where M(b) bounds the cost of one multiplication or exact
division of b-bit integers (M(b) = O(b²) for schoolbook arithmetic, which gives O(N⁵·log²(2·w_max))). This is
polynomial in the input size (at least N² entries of at least log₂(w_max + 1) bits).

**Space.** K has N²/4 entries, each of O(N·log(2·w_max)) bits: Θ(N²) integers.

**Check.** `tests/test_proofs_planar.py`, class `NumberSizes`: with weights wrapped in a type that records the largest
absolute value of every product, difference and quotient, on 60 seeded random grids (N ≤ 36, weights 0..3 and up to
10^9), every stored value is at most (2·w_max)^(N/2) and every intermediate at most 2·(2·w_max)^N. Class `Space`:
the tracemalloc peak of the Kasteleyn function on unit m × 2 ladders grows by a factor between 3 and 6 per doubling
of N = 32, 64, 128.

## 8. The harness oracle (transfer-matrix DP)

`harness.transfer_matrix_count(a, b, W)` returns 1 for N = 0. Otherwise it walks the cells of a `rows` × `width`
grid in row-major order, cell i = r·width + c, with width = min(a, b); if b > a it uses the transposed grid, whose
cell (r, c) is the input vertex (c, r). Transposition maps grid edges to grid edges with the same weights, so the
answer is unchanged. Below, "edge" means a grid edge with non-zero weight; edges of weight 0 contribute only zero
products and are skipped by the code (`if w:`).

**Invariant.** Before cell i is processed, `states` maps each mask to Σ w(P) over the edge sets P such that:
- every cell < i is covered by exactly one edge of P, no cell is covered twice, and every edge of P has its smaller
  cell < i;
- the cells ≥ i covered by P are exactly those i + j with bit j of the mask set.

Such cells lie in {i, …, i + width − 1}: an edge from a cell j < i ends at j + 1 or j + width ≤ i − 1 + width.
Masks therefore have at most `width` bits.

*Start* (i = 0): only P = ∅, mask 0, weight 1: `states = {0: 1}`.

*Step.* Fix P counted at cell i.
- If cell i is covered (bit 0), no edge of P starts at i. The same P is counted at cell i + 1 with mask `mask >> 1`.
- Otherwise every extension P′ that covers cell i adds exactly one edge whose smaller cell is i. That edge goes to
  the right neighbour i + 1, which needs c + 1 < width and cell i + 1 uncovered (bit 1 clear), and gives mask
  (`mask >> 1`) | 1. Or it goes to the cell below, i + width, which needs r + 1 < rows; that cell is never covered
  yet (it is beyond the mask), and the edge gives mask (`mask >> 1`) | (1 << (width − 1)), i.e. `top`.
- In each case the weight is multiplied by the edge's weight. These are exactly the code's three branches, and each
  P′ at cell i + 1 arises from exactly one P at cell i (delete its edge with smaller cell i, if any). So the
  invariant holds at i + 1.

*End.* After the last cell, mask 0 collects exactly the edge sets that cover every cell exactly once, i.e. the
perfect matchings. So `states.get(0, 0)` is Σ_M w(M), the answer. For odd N no such set exists, and the result is 0. ∎

The harness docstring's cost, O(N·2^width) dictionary operations, follows: there are at most 2^width masks per cell.

**Check.** The experiment script compares this DP with Fibonacci numbers on ladders, with parity on paths, with
brute force over (N/2)-edge subsets on all 35 shapes with N ≤ 12, under transposition, and with the permanent
(0 failures). `tests/test_proofs_planar.py`, class `Permanent`, compares this DP, both implementations and the
permanent on 60 seeded weighted grids with N ≤ 12; the validator's V1 run compares the implementations with this DP.
