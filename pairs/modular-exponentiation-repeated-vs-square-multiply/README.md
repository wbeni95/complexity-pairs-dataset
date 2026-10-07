# Modular exponentiation: repeated multiplication vs square-and-multiply

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given a ≥ 0 and e ≥ 0, compute aᵉ mod m for the fixed 64-bit prime m = 2⁶⁴ − 59.
n is the bit length of e.

| Algorithm | Multiplications mod m (n = bits of e) | Implementation |
|---|---|---|
| Repeated multiplication | Θ(e) = Θ(2ⁿ) | [repeated.py](implementations/repeated.py) |
| Left-to-right square-and-multiply | Θ(n) (n squarings, ≤ n multiplications) | [square_multiply.py](implementations/square_multiply.py) |

**Why it's a pair.** Multiplying by a, e times, is linear in the *value* of e and therefore exponential in its
length. Squaring reuses a^(2^i) and turns each bit of e into at most two multiplications.

**Lower bound.** In the addition-chain model at least ⌈log₂ e⌉ ≥ n − 1 multiplications are needed (e ≥ 1). Without
its two trivial products (1·1 and 1·a), square-and-multiply makes (n − 1) + (popcount(e) − 1) ≤ 2(n − 1) ≤ 2⌈log₂ e⌉
multiplications, so it is optimal up to a factor 2 in that count.

**Caveat (input size).** The fixed modulus makes each multiplication O(1). For a k-bit modulus, multiply both
costs by the cost of one k-bit modular multiplication.

**Verification.** V1: agreement with each other and with the built-in `pow(a, e, m)` (oracle only).
V2: on e = 2ⁿ − 1, runtimes fit 2ⁿ and n
(`python tools/validate.py pairs/modular-exponentiation-repeated-vs-square-multiply --scaling -v`).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: that m = 2⁶⁴ − 59 is the largest prime
below 2⁶⁴ (a Lucas certificate and a divisor of each larger number), correctness of both algorithms, the exact
counts e and n + popcount(e), the space bounds, the addition-chain lower bound and the factor-2 statement.
[tests/test_proofs_modexp.py](../../tests/test_proofs_modexp.py) re-checks the computable facts.

**Background** (cited; not claims of this entry). Window methods (2^k-ary, sliding window) need fewer
multiplications on long exponents (Knuth). Modular exponentiation is the basic operation of RSA (Rivest, Shamir, Adleman
1978) and of Diffie–Hellman key exchange (1976).

**Sources.** Knuth, TAOCP Vol. 2 (3rd ed.). Rivest, Shamir, Adleman, CACM 21(2), 1978. Diffie, Hellman,
IEEE Trans. Inf. Theory 22(6), 1976.
