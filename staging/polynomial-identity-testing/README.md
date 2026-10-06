<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Polynomial identity testing: randomized polynomial vs deterministic (open)

**Type:** T6, T4 (open / unpaired) · **Verification:** V0

**Problem.** Given an arithmetic circuit C computing a polynomial over a field F (or the integers), decide whether the polynomial is identically zero.

**Input.** s = circuit size (number of gates); the degree d <= 2^s. Size: O(s log s) bits plus constants.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| expand into monomials | classical-deterministic | exponential in s in general (a size-s circuit can have 2^Omega(s) monomials, e.g. prod_i (x_i + 1)) | exponential |
| Schwartz-Zippel random evaluation | classical-randomized | poly(s) (over Z, evaluate modulo a random prime to keep numbers small) | poly(s) |

**Relationship.** Randomized polynomial time (coRP) is known; a deterministic polynomial algorithm is OPEN. Kabanets and Impagliazzo showed that derandomizing PIT would imply circuit lower bounds that are themselves long-standing open problems.

**Caveats.** Deterministic polynomial-time PIT is known for many restricted circuit classes (e.g. read-once formulas, bounded-depth special cases). AKS primality is a derandomization of one specific identity test, (X + a)^N = X^N + a.

**Notes.** The canonical example where randomness is known to help and nobody can remove it. Compare primality-miller-rabin-vs-aks, where the derandomization succeeded.

**Verification.** Cited from the literature.

**Sources.**

- DeMillo, R. A.; Lipton, R. J. (1978). *A probabilistic remark on algebraic program testing*. Information Processing Letters 7(4), 193-195. [doi:10.1016/0020-0190(78)90067-4](https://doi.org/10.1016/0020-0190(78)90067-4)
- Zippel, R. (1979). *Probabilistic algorithms for sparse polynomials*. EUROSAM '79, LNCS 72, 216-226. [doi:10.1007/3-540-09519-5_73](https://doi.org/10.1007/3-540-09519-5_73)
- Schwartz, J. T. (1980). *Fast probabilistic algorithms for verification of polynomial identities*. Journal of the ACM 27(4), 701-717. [doi:10.1145/322217.322225](https://doi.org/10.1145/322217.322225)
- Kabanets, V.; Impagliazzo, R. (2004). *Derandomizing polynomial identity tests means proving circuit lower bounds*. Computational Complexity 13, 1-46. [doi:10.1007/s00037-004-0182-6](https://doi.org/10.1007/s00037-004-0182-6)
