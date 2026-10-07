# Matrix multiplication: schoolbook vs Strassen

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact multiplication counts)

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Schoolbook | Θ(n³) | [naive.py](implementations/naive.py) |
| Strassen (1969) | Θ(n^2.807) | [strassen.py](implementations/strassen.py) |

**The longer line (background, cited; not proved here).** Coppersmith–Winograd 1990 → … →
Alman et al. 2024 (ω < 2.371339 in arXiv:2404.16349 v1–v2, SODA 2025; version 3 of 2026-08-19 states ω < 2.371177).
AlphaTensor (Fawzi et al. 2022, Fig. 3) found a scheme that multiplies 4×4 matrices with 47 multiplications over GF(2).
If a rank-47 bilinear scheme for ⟨4,4,4⟩ over GF(2) exists, then applying it recursively gives ω ≤ log₄47 ≈ 2.7773 in
characteristic 2; that conditional step is proved in [PROOFS.md](PROOFS.md) (section 8). Two levels of Strassen's
algorithm use 7² = 49 multiplications for 4×4 matrices.

**How V2 is reached.** Timing cannot tell n³ from n^2.807 at feasible sizes (RL-006). The harness therefore
counts the scalar multiplications of the unchanged implementations with an instrumented number type (for n
not a power of two, products of padding zeros with each other are not counted, so V2 uses powers of two).
Schoolbook does exactly n³; Strassen (cutoff 16) does exactly 7^(log₂(n/16))·16³ for n = 16·2^k. Each fit uses tolerance
0.02, and the other algorithm's cost is a declared *rival* that must not fit: Strassen's counts against n³
give α = 0.936, so n³ is rejected. Additions are not counted.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the correctness of both
algorithms (Strassen's seven-product identities, which never commute two factors, the recursion and the padding), the
time and space bounds, the exact multiplication counts for all sizes of their domains, the exact addition count
5632·7^k − 1536·4^k for n = 16·2^k, and the value sizes. It names the scripts and tests that check each one
(`tests/test_proofs_strassen.py` among them, with a symbolic check of the code's identities).

**Sources.** Strassen 1969. Coppersmith & Winograd 1990. arXiv:2404.16349. Fawzi et al., Nature 2022.
