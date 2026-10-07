# Determinant over GF(p): cofactor expansion vs Gaussian elimination

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Compute det(A) mod p for an n × n matrix over GF(p), p = 2³¹ − 1. Because p is fixed,
every field operation is unit cost.

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Laplace (cofactor) expansion | Θ(n!): exactly ⌊e·n!⌋ − 1 multiplications (n ≥ 1) | [cofactor.py](implementations/cofactor.py) |
| Gaussian elimination mod p | Θ(n³): exactly (n³ − n)/3 multiply-subtracts on non-singular input | [gaussian.py](implementations/gaussian.py) |

**Why it's a pair.** The expansion never uses the fact that row operations leave the determinant
unchanged. Elimination does, and reduces the matrix to triangular form in Θ(n³). With fast matrix
multiplication the cost drops further, to O(n^ω) (Bunch & Hopcroft 1974; cited background).

**Contrast with the permanent.** Drop the signs and the same sum over permutations becomes the
permanent, which is #P-complete (Valiant 1979; cited background). See
[permanent-naive-vs-ryser](../permanent-naive-vs-ryser/README.md).

**Verification.** V1: the harness builds each matrix as a row-permuted L·U, so its determinant is known
in advance. Both implementations must match it, including singular matrices and cases that need row
swaps. V2: runtimes fit n! and n³.

**Proofs.** [PROOFS.md](PROOFS.md) proves both algorithms correct from the Leibniz formula, gives their exact
operation counts and space bounds, and proves the facts the harness relies on (the known determinant of a
row-permuted L·U, the primality of p). [tests/test_proofs_determinant.py](../../tests/test_proofs_determinant.py)
re-runs them on stated ranges.

**Sources.** Bareiss 1968. Bunch & Hopcroft 1974. Strassen 1969. Valiant 1979. Alman, Duan, Vassilevska Williams,
Xu, Xu & Zhou 2024.
