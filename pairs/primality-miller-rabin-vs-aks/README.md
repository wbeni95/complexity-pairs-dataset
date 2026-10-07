# Primality testing: Miller–Rabin vs AKS

**Type:** T4 (randomized ↔ deterministic) · **Verification:** V1

| Algorithm | Model | Time (n = bits of N) | Implementation |
|---|---|---|---|
| Miller–Rabin, k ≥ 1 rounds | randomized, one-sided error < 4^(−k) | O(k·n³) | [miller_rabin.py](implementations/miller_rabin.py) |
| AKS | deterministic | O(n^16.5) schoolbook, Õ(n^10.5) fast arithmetic; Ω(n⁵) on primes | [aks.py](../primality-trial-vs-aks/implementations/aks.py) |

**Why it's a pair.** Same problem, both polynomial. AKS removes the randomness unconditionally, but it needs
Ω(n⁵) operations on every large prime, against O(k·n³) for Miller–Rabin.

**Verification.** V1 against a sieve oracle (n ≤ 20 bits). Miller–Rabin uses 32 rounds with pseudo-random
bases that the validator seeds, so the run is reproducible; with independent uniform bases a composite would pass
with probability < 4⁻³².

**Proofs.** [PROOFS.md](PROOFS.md) proves the Miller–Rabin claims: the round tests exactly the strong-witness
condition, primes always pass, at least 3/4 of the bases are witnesses for every odd composite (so one round errs
with probability < 1/4), O(k·n³) time, O(n) space, PRIMES ∈ coRP, and the comparison with AKS. The AKS claims are
proved in [../primality-trial-vs-aks/PROOFS.md](../primality-trial-vs-aks/PROOFS.md).
[tests/test_proofs_primality.py](../../tests/test_proofs_primality.py) re-checks the computable facts.

**Background** (cited; not claims of this entry). Miller's deterministic version runs in polynomial time
assuming the extended Riemann hypothesis (Miller 1976). Lenstra and Pomerance (2019) give a variant of AKS that
runs in time (log N)⁶ (2 + log log N)^c; their abstract states that AKS proved the same with 21/2 in place of 6.

**Sources.** Miller 1976 (JCSS). Rabin 1980 (J. Number Theory). Agrawal–Kayal–Saxena 2004 (Annals).
Lenstra–Pomerance 2019 (JEMS).
