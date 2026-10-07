<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Discrete logarithm: generic and index-calculus algorithms vs Shor's quantum algorithm

**Type:** T6, T9 (open / unpaired) · **Verification:** V0

**Problem.** Given a cyclic group G of prime order p with generator g, and h in G, find x with g^x = h. (For the index-calculus bound: G = the multiplicative group of the prime field GF(q).)

**Input.** n = bit length of the group order. Size: O(n) bits per group element.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| baby-step giant-step | classical-deterministic | O(sqrt(p)) = O(2^(n/2)) group operations | O(sqrt(p)) group elements |
| Pollard rho for logarithms | classical-randomized | O(sqrt(p)) group operations (heuristic), O(1) memory | O(1) group elements |
| number field sieve for discrete logs in GF(q) | classical-randomized | L_q[1/3, (64/9)^(1/3)]: sub-exponential (heuristic); applies to finite fields, NOT to generic groups such as elliptic curves | L_q[1/3, ...] |
| Shor's algorithm | quantum | polynomial in n (O(n^3) gates with schoolbook arithmetic) | O(n) qubits |

**Relationship.** Shoup (1997) gives an Omega(sqrt(p)) lower bound on the group operations of generic classical algorithms (cited, not checked here), while Shor's algorithm uses polynomially many (cited). In GF(q)* the number field sieve is sub-exponential under heuristic assumptions (cited). For general elliptic-curve groups, apart from known special classes, no classical algorithm better than the generic O(sqrt(p)) is known (a statement about the state of knowledge, not a theorem; not checked here).

**Caveats.** Shoup's lower bound holds only for GENERIC algorithms (which use the group as a black box); it says nothing about algorithms that exploit the representation. Not targeted operationally (START_HERE section 10).

**Notes.** Notable for the classical-vs-quantum question: in the black-box (generic group) model the classical/quantum gap (Omega(sqrt p) vs poly) is established in the literature (Shoup 1997; Shor 1997; cited, not checked here), unlike in the plain Turing-machine setting, where it is only conjectured.

**Verification.** Cited from the literature.

**Sources.**

- Shanks, D. (1971). *Class number, a theory of factorization, and genera*. Proceedings of Symposia in Pure Mathematics 20, AMS, 415-440. [doi:10.1090/pspum/020/0316385](https://doi.org/10.1090/pspum/020/0316385)
- Pollard, J. M. (1978). *Monte Carlo methods for index computation (mod p)*. Mathematics of Computation 32(143), 918-924. [doi:10.1090/S0025-5718-1978-0491431-9](https://doi.org/10.1090/S0025-5718-1978-0491431-9)
- Gordon, D. M. (1993). *Discrete logarithms in GF(p) using the number field sieve*. SIAM Journal on Discrete Mathematics 6(1), 124-138. [doi:10.1137/0406010](https://doi.org/10.1137/0406010)
- Shoup, V. (1997). *Lower bounds for discrete logarithms and related problems*. EUROCRYPT '97, LNCS 1233, 256-266. [doi:10.1007/3-540-69053-0_18](https://doi.org/10.1007/3-540-69053-0_18)
- Shor, P. W. (1997). *Polynomial-Time Algorithms for Prime Factorization and Discrete Logarithms on a Quantum Computer*. SIAM Journal on Computing 26(5), 1484-1509. [doi:10.1137/S0097539795293172](https://doi.org/10.1137/S0097539795293172)
