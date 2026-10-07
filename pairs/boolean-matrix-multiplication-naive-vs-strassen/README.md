# Boolean matrix multiplication: schoolbook vs Strassen over the integers

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact product counts with rivals)

**Problem.** For n × n 0/1 matrices A and B compute the Boolean product C[i][j] = OR over k of (A[i][k] AND B[k][j]).

| Algorithm | Products (counted, exact) | Time | Implementation |
|---|---|---|---|
| Schoolbook (Boolean AND/OR, no early exit) | n³ ANDs | Θ(n³) | [naive.py](implementations/naive.py) |
| Strassen over ℤ on the 0/1 embedding, then P[i][j] > 0 | 7^(log₂(n/16))·16³ | Θ(n^log₂7) ≈ Θ(n^2.807) | [strassen_over_integers.py](implementations/strassen_over_integers.py) |

**Why it is here.** Strassen's algorithm needs subtraction, which the Boolean semiring ({0,1}, OR, AND) does not have.
The fix is to change the problem, not the algorithm: read the bits as integers and compute the integer product P = AB.
P[i][j] counts the k with A[i][k] = B[k][j] = 1, so C[i][j] = 1 exactly when P[i][j] > 0. Every faster integer matrix
multiplication algorithm transfers the same way. The integers stay in a range
polynomial in n (below 2n² in absolute value), so they have O(log n) bits. The integer version of the pair is
[matrix-multiplication-naive-vs-strassen](../matrix-multiplication-naive-vs-strassen/).

**Verification.**
- *V1:* both implementations return identical matrices for n = 0..10, 17, 31, 40, 64 (above the cutoff of 16), at
  densities 0.05–0.9 and with zero, all-ones, identity and permutation factors. The independent `check` forms each row
  of C as the bitwise OR of the rows of B selected by row i of A, a row-union formulation with no inner products.
- *Oracle control* ([experiment](../../experiments/2026-10-06f_entries_boolean_matmul.py)): 240 correct products
  accepted; all 906 wrong outputs rejected (flipped entries, the integer product AB, Cᵀ, BA, wrong shape).
- *Negative controls:* the same Strassen code run directly on Boolean values is wrong on 25 of 40 random instances
  with OR in place of subtraction, and on 33 of 40 over GF(2) (XOR, i.e. the product mod 2).
- *V2:* an instrumented integer counts every scalar product (multiplication, or AND for the schoolbook method) of the
  unchanged implementations. On n = 16, 32, 64, 128: schoolbook exactly n³, Strassen exactly 7^(log₂(n/16))·16³
  (4096, 28672, 200704, 1404928).

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| schoolbook vs n³ | 1.000 | n^log₂7: 1.069, n²: 1.500 |
| Strassen vs n^log₂7 | 1.000 | n³: 0.936, n²: 1.404 |

**Caveats.** Only products are counted, as in the integer entry; Strassen's additions are also Θ(n^log₂7). In bit
complexity Strassen carries an extra factor polylogarithmic in n for its O(log n)-bit integers (a signed 64-bit word
holds every value for n < 2³¹). For n that is not a power of two the matrices are padded, and products of two padding
zeros are not counted: n = 17 gives 24832 instead of 28672. V2 therefore uses powers of two.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the correctness of both
algorithms (the reduction P[i][j] > 0, Strassen's identities, the recursion and the padding), the time and space
bounds, the exact counts for all sizes of their domains, the exact addition count 5632·7^k − 1536·4^k for n = 16·2^k,
the early-exit variant and the size of the integers. It names the scripts and tests that check each one
(`tests/test_proofs_strassen.py` among them).

**Background (cited, not proved here).** Fischer & Meyer (1971) and Munro (1971) relate Boolean matrix
multiplication to the transitive closure of a directed graph; Warshall's algorithm (1962) computes the closure
directly. Transitive closure is not implemented here.

**Sources.** Fischer & Meyer, SWAT 1971. Munro, IPL 1971. Strassen, Numer. Math. 1969. Warshall, J. ACM 1962.
