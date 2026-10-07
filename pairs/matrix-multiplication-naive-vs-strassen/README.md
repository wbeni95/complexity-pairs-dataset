# Matrix multiplication: schoolbook vs Strassen

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact multiplication counts)

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Schoolbook | Θ(n³) | [naive.py](implementations/naive.py) |
| Strassen (1969) | Θ(n^2.807) | [strassen.py](implementations/strassen.py) |

**The longer line.** Coppersmith–Winograd 1990 (ω < 2.376) → … → Alman et al. 2024 (ω < 2.371339).
AlphaTensor (2022) found rank-47 schemes for 4×4 over GF(2), giving ω ≤ log₄47 ≈ 2.7773 in characteristic 2.

**How V2 is reached.** Timing cannot tell n³ from n^2.807 at feasible sizes (RL-006). The harness therefore
counts the scalar multiplications of the unchanged implementations with an instrumented number type (for n
not a power of two, products of padding zeros with each other are not counted, so V2 uses powers of two).
Schoolbook does exactly n³; Strassen (cutoff 16) does exactly 7^(log₂(n/16))·16³ for n = 16·2^k. Each fit uses tolerance
0.02, and the other algorithm's cost is a declared *rival* that must not fit: Strassen's counts against n³
give α = 0.936, so n³ is rejected. Additions are not counted.

**Sources.** Strassen 1969. Coppersmith & Winograd 1990. arXiv:2404.16349. Fawzi et al., Nature 2022.
