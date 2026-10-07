# Permanent: sum over permutations vs Ryser's formula

**Type:** T6 (open: #P-complete; cited background) + T8 (super-poly → faster super-poly) · **Verification:** V2

**Problem.** Compute perm(A) = Σ over permutations s of Πᵢ A[i][s(i)] exactly, for an n × n integer matrix.

| Algorithm | Time (n × n) | Implementation |
|---|---|---|
| Sum over all permutations | Θ(n · n!): exactly n·n! multiplications and n! additions (n ≥ 1) | [naive.py](implementations/naive.py) |
| Ryser's formula (1963), Gray-code order | Θ(n · 2ⁿ): exactly (2n+1)(2ⁿ−1) additions and multiplications, plus 2ⁿ⁻¹ + [n odd] negations (n ≥ 1) | [ryser.py](implementations/ryser.py) |

The naive sum's running time and space assume the documented cost of `itertools.permutations` (a machine-model
assumption, see PROOFS.md section 0.1); the operation counts do not.

**Why it's here.** Inclusion–exclusion over column subsets turns n! into 2ⁿ, and the result is still
exponential. The permanent is #P-complete even for 0/1 matrices (Valiant 1979; cited background), so a
polynomial algorithm would give FP = #P.

**Contrast with the determinant.** The determinant is the same sum with signs, and Gaussian elimination computes it
with O(n³) field operations ([determinant-cofactor-vs-gaussian](../determinant-cofactor-vs-gaussian/README.md)).
Mod 2 the signs disappear, so perm(A) ≡ det(A) (mod 2) is easy. The hard part is the exact value.

**BosonSampling** (cited background). Photon output probabilities in a linear-optical network are |perm|² of
submatrices of its unitary. That is the basis of Aaronson & Arkhipov's proposed quantum-advantage experiment. It
samples from that distribution; it does not compute permanents.

**Verification.** V1: both agree, and `harness.check` compares with an independent subset DP (n ≤ 12) and
with det mod 2. V2: runtimes fit n·n! and n·2ⁿ.

**Proofs.** [PROOFS.md](PROOFS.md) proves the correctness of both algorithms (Ryser's formula and the Gray-code
order), their exact operation counts, the space bounds, the sizes of the integers and the facts used by the
oracle. [tests/test_proofs_permanent.py](../../tests/test_proofs_permanent.py) re-runs them on stated ranges,
including perm(Jₙ) = n! and the derangement numbers perm(Jₙ − I).

**Sources.** Ryser 1963 (Carus Monograph 14). Valiant 1979. Glynn 2010. Jerrum, Sinclair & Vigoda 2004.
Aaronson & Arkhipov 2013 (Theory of Computing 9).
