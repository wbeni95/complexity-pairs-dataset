# Determinant over GF(p): cofactor expansion vs Gaussian elimination

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Compute det(A) mod p for an n × n matrix over GF(p), p = 2³¹ − 1. Because p is fixed,
every field operation is unit cost.

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Laplace (cofactor) expansion | Θ(n!) | [cofactor.py](implementations/cofactor.py) |
| Gaussian elimination mod p | Θ(n³) | [gaussian.py](implementations/gaussian.py) |

**Why it's a pair.** The expansion never uses the fact that row operations leave the determinant
unchanged. Elimination does, and reduces the matrix to triangular form in Θ(n³). With fast matrix
multiplication the cost drops further, to O(n^ω) (Bunch & Hopcroft 1974).

**Contrast with the permanent.** Drop the signs and the same sum over permutations becomes the
permanent, which is #P-complete (Valiant 1979). See
[permanent-naive-vs-ryser](../permanent-naive-vs-ryser/README.md).

**Verification.** V1: the harness builds each matrix as a row-permuted L·U, so its determinant is known
in advance. Both implementations must match it, including singular matrices and cases that need row
swaps. V2: runtimes fit n! and n³.

**Sources.** Bareiss 1968. Bunch & Hopcroft 1974. Strassen 1969. Valiant 1979.
