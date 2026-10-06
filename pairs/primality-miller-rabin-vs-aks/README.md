# Primality testing: Miller–Rabin vs AKS

**Type:** T4 (randomized ↔ deterministic) · **Verification:** V1

| Algorithm | Model | Time (n = bits of N) | Implementation |
|---|---|---|---|
| Miller–Rabin, k rounds | randomized, one-sided error ≤ 4^(−k) | O(k·n³) | [miller_rabin.py](implementations/miller_rabin.py) |
| AKS | deterministic | Õ(n^10.5) proven; Õ(n⁶) variant | [aks.py](../primality-trial-vs-aks/implementations/aks.py) |

**Why it's a pair.** Same problem, both polynomial. AKS removes the randomness unconditionally, but its
polynomial degree is far higher. Miller's deterministic version needs the generalized Riemann hypothesis.

**Verification.** V1 against a sieve oracle (n ≤ 20 bits). Miller–Rabin uses 32 rounds, so the
check itself has a failure probability of at most 4⁻³² per composite.

**Sources.** Miller 1976 (JCSS). Rabin 1980 (J. Number Theory). Agrawal–Kayal–Saxena 2004 (Annals).
