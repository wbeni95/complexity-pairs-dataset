# Greatest common divisor: trial divisors vs Euclid's algorithm

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given a, b ≥ 0, compute gcd(a, b). n is the bit length of max(a, b).

| Algorithm | Time (n-bit inputs) | Implementation |
|---|---|---|
| Trial divisors (d = min(a, b) downwards) | Θ(2ⁿ) iterations, worst case (coprime inputs) | [trial.py](implementations/trial.py) |
| Euclid | O(n) division steps (after Lamé); O(n²) bit operations | [euclid.py](implementations/euclid.py) |

**Why it's a pair.** Scanning candidate divisors is linear in the *value* min(a, b), so it is exponential in
the input length. Euclid's identity gcd(a, b) = gcd(b, a mod b) shrinks the numbers geometrically: at most
about 1.44 n steps, with consecutive Fibonacci numbers as the worst case.

**Verification.** V1: agreement with each other and with `math.gcd` (oracle only), including zeros and
large common factors. V2 uses consecutive Fibonacci numbers, which are coprime and are the worst case for Euclid.
Trial divisors fit 2ⁿ at n = 14–22 bits. Euclid's runtimes fit n² at n = 4000–64000 bits; this is a
measurement, not a check of its O(n²) bit complexity. The O(n) step count is not timed, because at word size
interpreter overhead dominates; it is proved and counted exactly instead (see Proofs).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: correctness of both algorithms, the exact
iteration count min(a, b) − gcd(a, b) + 1 of trial divisors, the step bound log_φ(min(a, b)) + 2 (after Lamé)
with the Fibonacci worst case, the O(n²) bit-operation bound, and the space bounds.
[tests/test_proofs_gcd.py](../../tests/test_proofs_gcd.py) re-checks the computable facts.

**Background** (cited; not claims of this entry). Faster, subquadratic gcd algorithms exist (half-gcd method;
Knuth, TAOCP Vol. 2). Euclid's algorithm goes back to Euclid's *Elements*; Lamé (1844) bounded its number of
division steps.

**Sources.** Knuth, TAOCP Vol. 2 (3rd ed.). Lamé 1844, *Comptes Rendus de l'Académie des Sciences*.
