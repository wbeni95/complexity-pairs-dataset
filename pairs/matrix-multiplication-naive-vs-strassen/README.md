# Matrix multiplication: schoolbook vs Strassen

**Type:** T3 (poly → faster poly) · **Verification:** V1

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Schoolbook | Θ(n³) | [naive.py](implementations/naive.py) |
| Strassen (1969) | Θ(n^2.807) | [strassen.py](implementations/strassen.py) |

**The longer line.** Coppersmith–Winograd 1990 (ω < 2.376) → … → Alman et al. 2024 (ω < 2.371339).
AlphaTensor (2022) found rank-47 schemes for 4×4 over GF(2), giving ω ≤ 2.774 in characteristic 2.

**Why only V1.** The exponent gap (0.19) is too small for pure-Python timing at feasible sizes to
confirm reliably. The measured per-doubling ratios were ~7.3 for Strassen and ~7.8 for schoolbook,
which is consistent with the theory but not a clean V2.

**Sources.** Strassen 1969. Coppersmith & Winograd 1990. arXiv:2404.16349. Fawzi et al., Nature 2022.
