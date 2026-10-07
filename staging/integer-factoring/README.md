<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Integer factoring: classical algorithms vs Shor's quantum algorithm

**Type:** T6, T8 (open / unpaired) · **Verification:** V0

**Problem.** Given a composite integer N, output a nontrivial factor of N.

**Input.** n = bit length of N. Size: n bits.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| trial division | classical-deterministic | O(2^(n/2)) | O(n) |
| Pollard rho | classical-randomized | O(N^(1/4)) = O(2^(n/4)) heuristically (birthday bound on the smallest prime factor) | O(n) |
| general number field sieve (GNFS) | classical-randomized | exp(((64/9)^(1/3) + o(1)) (ln N)^(1/3) (ln ln N)^(2/3)), i.e. L_N[1/3, 1.923]: sub-exponential (heuristic) | L_N[1/3, ...] |
| Shor's algorithm | quantum | O(n^3) quantum gates with schoolbook modular arithmetic (O(n^2 log n log log n) with fast multiplication) | O(n) qubits |

**Relationship.** No classical polynomial-time algorithm is known; the best classical algorithms are sub-exponential (heuristically L[1/3]; rigorously L[1/2] randomized, Lenstra-Pomerance 1992). Shor's algorithm is polynomial on a quantum computer.

**Caveats.** Factoring is NOT known to be NP-hard and is in NP intersect coNP, so it is not believed to be NP-complete. Catalogued as OPEN (T6). This project does not target factoring operationally (START_HERE section 10).

**Notes.** Central evidence for quantum advantage: a problem believed hard classically with a polynomial quantum algorithm. No theorem we know of rules out a classical polynomial algorithm; one would only break the belief that factoring is hard (and much deployed cryptography).

**Verification.** Cited from the literature.

**Sources.**

- Pollard, J. M. (1975). *A Monte Carlo method for factorization*. BIT Numerical Mathematics 15(3), 331-334. [doi:10.1007/BF01933667](https://doi.org/10.1007/BF01933667)
- Lenstra, A. K.; Lenstra, H. W., Jr. (eds.) (1993). *The development of the number field sieve*. Lecture Notes in Mathematics 1554, Springer. [doi:10.1007/BFb0091534](https://doi.org/10.1007/BFb0091534)
- Lenstra, H. W., Jr.; Pomerance, C. (1992). *A rigorous time bound for factoring integers*. Journal of the American Mathematical Society 5(3), 483-516. [doi:10.1090/S0894-0347-1992-1137100-0](https://doi.org/10.1090/S0894-0347-1992-1137100-0)
- Shor, P. W. (1997). *Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer*. SIAM Journal on Computing 26(5), 1484-1509. [doi:10.1137/S0097539795293172](https://doi.org/10.1137/S0097539795293172)
