# Greatest common divisor: trial divisors vs Euclid's algorithm

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given a, b ≥ 0, compute gcd(a, b). n is the bit length of max(a, b).

| Algorithm | Time (n-bit inputs) | Implementation |
|---|---|---|
| Trial divisors (d = min(a, b) downwards) | Θ(2ⁿ) iterations, worst case (coprime inputs) | [trial.py](implementations/trial.py) |
| Euclid | O(n) division steps (Lamé); O(n²) bit operations | [euclid.py](implementations/euclid.py) |

**Why it's a pair.** Scanning candidate divisors is linear in the *value* min(a, b), so it is exponential in
the input length. Euclid's identity gcd(a, b) = gcd(b, a mod b) shrinks the numbers geometrically: at most
about 1.44 n steps, with consecutive Fibonacci numbers as the worst case.

**Verification.** V1: agreement with each other and with `math.gcd` (oracle only), including zeros and
large common factors. V2 uses consecutive Fibonacci numbers, which are coprime and are Lamé's worst case.
Trial divisors fit 2ⁿ at n = 14–22 bits. Euclid fits n² at n = 4000–64000 bits, which is its bit
complexity. The O(n) step count is not timed, because at word size interpreter overhead dominates.

**Beyond the pair.** Half-gcd algorithms (Knuth–Schönhage) reach O(M(n) log n) bit operations.

**Sources.** Knuth, TAOCP Vol. 2 (3rd ed.), §4.5.2–4.5.3. Lamé 1844, *Comptes Rendus* 19, 867–870.
