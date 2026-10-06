# Primality testing: trial division vs AKS

**Type:** T1 (exp → poly, same problem) · **Verification:** V1

**Problem.** Given N, decide whether N is prime. Input size n = bit length of N.

| Algorithm | Time (n = bits of N) | Implementation |
|---|---|---|
| Trial division | Θ(2^(n/2)) worst case | [trial_division.py](implementations/trial_division.py) |
| AKS (2004) | Õ(n^10.5) proven; Õ(n⁶) Lenstra–Pomerance variant | [aks.py](implementations/aks.py) |

**Why it's a pair.** Same problem, same deterministic model. Trial division is exponential in the input
length. AKS was the first unconditional deterministic polynomial-time test.

**Verification.** V1: both agree with each other and with a sieve oracle on random n-bit inputs
(n ≤ 20; AKS up to 16 bits, where its polynomial-congruence step really runs). Trial division's
2^(n/2) growth is measured. AKS's is not, so the entry stays at V1.

**Caveat.** Trial division is polynomial in the *value* N. It is exponential only in the input *length*,
and the input length is the measure that counts.

**Sources.** Agrawal, Kayal, Saxena, *PRIMES is in P*, Annals of Math. 2004.
Lenstra & Pomerance, *Primality testing with Gaussian periods*, JEMS 2019.
