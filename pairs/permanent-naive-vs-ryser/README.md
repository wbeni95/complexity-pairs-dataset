# Permanent: sum over permutations vs Ryser's formula

**Type:** T6 (open: #P-complete) + T8 (super-poly → faster super-poly) · **Verification:** V2

**Problem.** Compute perm(A) = Σ over permutations s of Πᵢ A[i][s(i)] exactly, for an n × n integer matrix.

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Sum over all permutations | Θ(n · n!) | [naive.py](implementations/naive.py) |
| Ryser's formula (1963), Gray-code order | Θ(n · 2ⁿ) | [ryser.py](implementations/ryser.py) |

**Why it's here.** Inclusion–exclusion over column subsets turns n! into 2ⁿ, and the result is still
exponential. The permanent is #P-complete even for 0/1 matrices (Valiant 1979), so a polynomial algorithm
would give FP = #P.

**Contrast with the determinant.** The determinant is the same sum with signs, and is O(n³)
([determinant-cofactor-vs-gaussian](../determinant-cofactor-vs-gaussian/README.md)). Mod 2 the signs
disappear, so perm(A) ≡ det(A) (mod 2) is easy. The hard part is the exact value.

**BosonSampling.** Photon output probabilities in a linear-optical network are |perm|² of submatrices of
its unitary. That is the basis of Aaronson & Arkhipov's proposed quantum-advantage experiment. It samples
from that distribution; it does not compute permanents.

**Verification.** V1: both agree, and `harness.check` compares with an independent subset DP (n ≤ 12) and
with det mod 2. V2: runtimes fit n·n! and n·2ⁿ.

**Sources.** Ryser 1963 (Carus Monograph 14). Valiant 1979. Glynn 2010. Jerrum, Sinclair & Vigoda 2004.
Aaronson & Arkhipov 2013 (Theory of Computing 9).
