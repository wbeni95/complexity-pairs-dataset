# Perfect matchings of grid graphs (dimers): backtracking enumeration vs Kasteleyn's signed determinant

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (exact operation counts for both algorithms, with rivals)

**Problem.** Input: the a × b grid graph (vertex u = r·b + c) and an N × N symmetric matrix W of non-negative integer
edge weights, N = a·b, non-zero only on grid edges (weight 0 = edge absent). Output: the exact sum over all perfect
matchings of the product of their edge weights (the dimer partition function). With 0/1 weights this counts the
perfect matchings of a spanning subgraph of the grid; with all weights 1 it counts the domino tilings of the
a × b rectangle (8 × 8: 12 988 816). N = 0 gives 1 (the empty matching), odd N gives 0. The size parameter n is N.

| Algorithm | Cost (n = N vertices) | Implementation |
|---|---|---|
| Backtracking: match the first unmatched vertex to its right or lower neighbour, recurse | O(n·2^(n/2)); at least the number of perfect matchings. On the unit (n/2) × 2 ladder: exactly L(n/2+2) − 3 = Θ(φ^(n/2)) multiplications (L = Lucas numbers) | [enumeration.py](implementations/enumeration.py) |
| Kasteleyn signs on the black × white weight matrix, Bareiss fraction-free determinant, absolute value | Θ(n³) arithmetic operations: exactly (n−2)·n·(n−1)/8 multiplications and exact divisions whenever the answer is non-zero | [kasteleyn_bareiss.py](implementations/kasteleyn_bareiss.py) |

**Why it is here.** Colour the grid like a chessboard. Every perfect matching is then a bijection from black to
white vertices, i.e. a term of the permanent of the black × white weight matrix B. Permanents are hard in general:
computing permanents of 0/1 matrices, that is counting perfect matchings of bipartite graphs, is #P-complete
(Valiant 1979; background in entry.json; see [permanent-naive-vs-ryser](../permanent-naive-vs-ryser/)). For the planar grid there is a way out.
Put sign +1 on horizontal edges and (−1)^c on the vertical edge (r, c)–(r+1, c). Then every unit square has sign
product −1, every perfect matching appears in det K with the same sign, and the count is |det K|, an
(n/2) × (n/2) determinant (Kasteleyn 1961; Temperley & Fisher 1961 is an exact result for the same dimer problem).

**Why the signs work (full proof in [PROOFS.md](PROOFS.md), section 6).** Two perfect matchings differ by disjoint alternating cycles. A cycle C
with 2l edges around p inner vertices and f unit squares changes the permutation sign by (−1)^(l−1) and the edge
signs by (−1)^f. Euler's formula gives f = p + l − 1, so the total factor is (−1)^p. Since no grid edge crosses C,
the inner vertices are matched among themselves, so p is even and the factor is +1. Zero weights only delete
terms, so every spanning subgraph uses the signs of the full rectangle. The argument uses planarity twice, through
Euler's formula and through the fact that no edge crosses a cycle. Without the signs the determinant is wrong: for
the unit 2 × 2 grid the unsigned matrix is [[1, 1], [1, 1]], with determinant 0 instead of 2.

**Bit size.** "Θ(n³)" counts arithmetic operations. Every Bareiss value is a minor of K. Each row of K has at most
4 non-zero entries, so by Hadamard's inequality every minor is at most (2·w_max)^(n/2), and the integers have
O(n log(2·w_max)) bits. The bit complexity is O(n³·M(n log(2·w_max))), where M(b) bounds one multiplication or
exact division of b-bit integers (O(b²) schoolbook), polynomial in the input size (PROOFS.md, section 7). Measured on a
10 × 10 grid with weights up to 10⁹: 1475 bits stored, against a bound of 1544.

**Verification.**
- *V1:* both implementations agree and the independent `check` accepts on 280 instances, n = 0..144 (enumeration
  up to n = 48). The instances are unit rectangles, random 0/1 edge subsets, weights 0..3 and up to 10⁹, ladders,
  paths, odd N and N = 0. `check` is a transfer-matrix ("broken profile") DP over the cells with a bitmask of
  covered cells, at width min(a, b); PROOFS.md, section 8 proves it exact. The experiment tests that DP against:
  - Fibonacci numbers on ladders and parity on paths;
  - brute force over (N/2)-edge subsets on all 35 shapes with N ≤ 12;
  - transposition;
  - a product-of-cosines formula for unit rectangles up to 10 × 10 (floating point, rounded; a numerical cross-check only);
  - the permanent of B.

  It found no failures. Extended battery: 1609 more instances, 0 failures.
- *Oracle control:* `check` rejected all 1334 wrong outputs presented and accepted all 270 correct ones. The wrong
  outputs were answer ± 1, 2 × answer, float and bool types, the signed det K without abs, the (absolute)
  determinant of the unsigned matrix, and the unit-weight count ignoring W.
- *Negative control:* |det B| (no signs) is wrong on 286 of 480 even-N instances and on every unit ladder m × 2,
  m = 2..30. det K itself is negative on 39 of them, always for shapes such as 2 × 3, 2 × 7 and 6 × 3. Its sign
  never differs between instances of one shape, as the proof predicts.
- *V2:* a CountingInt type in the harness counts every multiplication and floor division of the unchanged
  implementations on the unit (n/2) × 2 ladder. Both closed forms are proven in PROOFS.md and checked for every
  even n up to 60 (enumeration) and up to 120 and 256 (Kasteleyn). The Kasteleyn count is the same on 297 random
  instances with non-zero answers, 53 of which needed a row swap.

| Fit (tolerance 0.02, exact counts) | α | Rivals (must not fit) |
|---|---|---|
| enumeration vs L(n/2+2) − 3, n = 16..52 step 4 | 1.000 | 2^(n/2): 0.696, n·φ^(n/2): 0.885, n³: 2.464 |
| Kasteleyn vs (n−2)·n·(n−1)/8, n = 16..256 doubling | 1.000 | n²: 1.532, n⁴: 0.766, n³ log n: 0.943 |

Both fits resolve the log factor (diagnostic 0.962 / 1.040 and 0.925 / 1.088). The bare n³ would give α = 1.021,
outside the tolerance; this is why the exact form is used (RL-062).

**Caveats.**
- Only rectangles and their edge-deleted subgraphs are covered. Vertex deletions (holes, other boundaries) cannot
  be expressed in this input format, and the sign rule is proved here only for rectangles and their spanning
  subgraphs; other graphs are outside this entry.
- Weights must be non-negative.
- The enumeration's cost depends on the vertex order. On the 2 × m ladder, numbered along the long side, the count
  is F(m+3) − 2 + ((m−1)F(m) + 2m·F(m−1))/5 = Θ(m·φ^m), e.g. 684 816 against 271 440 for m = 24, because each tiling
  of row 0 is finished by its own chain of row-1 steps. V2 uses the m × 2 orientation.
- Counts include multiplications and divisions only.

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves Bareiss's elimination, the
enumeration's correctness and bounds, Kasteleyn's sign lemma for the a × b grid and its spanning subgraphs, and the
bit-size bounds; [tests/test_proofs_planar.py](../../tests/test_proofs_planar.py) checks their computable parts.

**Sources.** Kasteleyn 1961 (Physica 27(12), 1209–1225). Temperley & Fisher 1961 (Phil. Mag. 6(68), 1061–1063).
Valiant 1979 (Theoret. Comput. Sci. 8(2), 189–201). Bareiss 1968 (Math. Comp. 22(103), 565–578). Script:
[experiments/2026-10-06f_entries_planar_matchings.py](../../experiments/2026-10-06f_entries_planar_matchings.py).
Neighbours: [spanning-tree-count-enumeration-vs-kirchhoff](../spanning-tree-count-enumeration-vs-kirchhoff/)
(counting by a determinant) and [permanent-naive-vs-ryser](../permanent-naive-vs-ryser/) (the sign-free, hard case).
