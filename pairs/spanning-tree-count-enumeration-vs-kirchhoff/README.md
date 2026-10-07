# Counting spanning trees: edge-subset enumeration vs Kirchhoff (Bareiss)

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (Kirchhoff: exact operation counts; enumeration: timing)

Input: a simple undirected graph on n ≥ 1 vertices as an n × n 0/1 adjacency matrix. Output: the exact number
τ(G) of spanning trees (0 if G is disconnected, 1 for n = 1).

| Algorithm | Cost (n vertices, m edges) | Implementation |
|---|---|---|
| Try all (n−1)-edge subsets, union-find acyclicity test | O(n² + n log n·C(m, n−1)) (under the `itertools.combinations` assumption in entry.json), Ω(n² + n C(m, n−1)); on K_n C(n(n−1)/2, n−1) = 2^Θ(n log n) subsets | [enumeration.py](implementations/enumeration.py) |
| Kirchhoff's matrix-tree theorem, Bareiss fraction-free determinant | Θ(n³) arithmetic operations: exactly (n−2)(n−1)(2n−3)/2 multiplications and exact divisions on every connected graph | [kirchhoff_bareiss.py](implementations/kirchhoff_bareiss.py) |

**Why it is here.** Listing is hopeless on complete graphs: K_n has n^(n−2) spanning trees (Cayley), and the
enumeration looks at C(n(n−1)/2, n−1) ≥ (n/2)^(n−1) candidate edge sets. Kirchhoff's theorem says τ(G) is any
cofactor of the Laplacian L = D − A, so one (n−1) × (n−1) determinant counts all trees at once. Counting is easy
here although listing is not.

**Bit size.** "Θ(n³)" counts arithmetic operations. Bareiss keeps everything in the integers: each intermediate
entry is a minor of the reduced Laplacian, below n^(n−1) in absolute value by Hadamard's inequality, so the numbers
have O(n log n) bits and the bit complexity is O(n³ M(n log n)) (M(b): one multiplication or exact division of
b-bit integers), still polynomial in the n²-bit input. On reduced
Laplacians no zero pivot ever needs a row swap (the matrix is positive definite iff G is connected, and positive
semidefinite otherwise; proof in PROOFS.md, section 6), but the implementation keeps general pivoting; the
experiment script tests that branch on general integer matrices.

**Verification.** V1: both implementations agree for n = 1..8 on random, complete, tree, tree-plus-edges, cycle
and deliberately disconnected graphs (Kirchhoff alone up to n = 40). The independent `check` uses depth-first
search (0 if disconnected), trees (1), Cayley's n^(n−2) for K_n, memoised deletion–contraction on multigraphs up to
24 edges, and otherwise a different cofactor (vertex 0 deleted) by Gaussian elimination over the rationals.
V2, Kirchhoff: the harness feeds K_n with entries of an instrumented integer type that counts every multiplication
and division of the unchanged implementation. The counts are (n−2)(n−1)(2n−3)/2 exactly; against (n−1)³ the fit gives
α = 1.014 (tolerance 0.03), while the rivals n⁴ (α = 0.781) and n² (α = 1.562) are rejected and the log-factor
diagnostic is resolved. V2, enumeration: it performs no arithmetic on the entries, so it is timed (best of 3) on
K_n, n = 4..8, against n·C(n(n−1)/2, n−1); n! and 2ⁿ are rejected as rivals. Timing cannot tell this cost from
n^(n−2) (noise-free α = 1.20), see the caveats in entry.json.

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves the enumeration's correctness
and bounds, the matrix-tree theorem, the absence of row swaps on every reduced Laplacian and the bit-size bounds;
[tests/test_proofs_stc.py](../../tests/test_proofs_stc.py) checks their computable parts.

**Sources.** Kirchhoff 1847 (Annalen der Physik 148(12), 497–508). Bareiss 1968 (Math. Comp. 22(103), 565–578).
Cayley 1889 (Quart. J. Pure Appl. Math. 23, 376–378). Script:
[experiments/2026-10-07b_spanning_tree_counts.py](../../experiments/2026-10-07b_spanning_tree_counts.py).
