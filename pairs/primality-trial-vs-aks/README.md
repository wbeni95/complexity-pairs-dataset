# Primality testing: trial division vs AKS

**Type:** T1 (exp → poly, same problem) · **Verification:** V1

**Problem.** Given N, decide whether N is prime. Input size n = bit length of N.

| Algorithm | Time (n = bits of N) | Implementation |
|---|---|---|
| Trial division | Θ(2^(n/2)) worst case | [trial_division.py](implementations/trial_division.py) |
| AKS (2004) | polynomial: O(n^16.5) bit operations (schoolbook), Õ(n^10.5) with fast arithmetic | [aks.py](implementations/aks.py) |

**Why it's a pair.** Same problem, same deterministic model. Trial division is exponential in the input
length. AKS is an unconditional deterministic polynomial-time test (proved here).

**Verification.** V1: both agree with each other and with a sieve oracle on random n-bit inputs
(n ≤ 20; AKS up to 16 bits, where its polynomial-congruence step really runs). Trial division's
2^(n/2) growth is measured. AKS's is not, so the entry stays at V1.

**Caveat.** Trial division is polynomial in the *value* N. It is exponential only in the input *length*,
and the input length is the measure that counts.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: trial division's correctness, exact
division count and Θ(2^(n/2)) worst case (with Bertrand's postulate); that the AKS implementation returns True
exactly for primes, for every N, with r ≤ max(16, n(n² + 1)²); its O(n^16.5) (schoolbook) and Õ(n^10.5)
(fast arithmetic) time and O(n⁶) space bounds; and an Ω(n⁵) lower bound on primes. In steps 2 and 5 the implementation
uses an exact rational λ with log₂ N ≤ λ ≤ n in place of log₂ N and computes ⌊λ²⌋ and ⌊√φ(r)·λ⌋ exactly; these
can exceed the values with log₂ N (by one at N = 229533671885360152), which the proof allows.
[tests/test_proofs_primality.py](../../tests/test_proofs_primality.py) and
[experiments/2026-10-07_primality_proof_checks.py](../../experiments/2026-10-07_primality_proof_checks.py)
re-check the computable facts.

**Background** (cited; not claims of this entry). Lenstra and Pomerance (2019) give a variant that runs in time
(log N)⁶ (2 + log log N)^c; their abstract states that AKS proved the same with 21/2 in place of 6. The V2
generator's 12-base Miller–Rabin test is used only below 318665857834031151167461, a composite that passes all
twelve bases and the smallest such number, ψ12 (Sorenson & Webster, arXiv:1509.00864, Theorem 1.1; cited, not
checked here).

**Sources.** Agrawal, Kayal, Saxena, *PRIMES is in P*, Annals of Math. 2004.
Lenstra & Pomerance, *Primality testing with Gaussian periods*, JEMS 2019.
Sorenson & Webster, *Strong pseudoprimes to twelve prime bases*, Math. Comp. 2017 (arXiv:1509.00864).
Nair, *On Chebyshev-type inequalities for primes*, Amer. Math. Monthly 1982.
