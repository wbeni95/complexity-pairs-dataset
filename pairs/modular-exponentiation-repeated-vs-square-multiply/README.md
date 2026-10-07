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
multiplications, so it is optimal up to a factor 2 in that count. Window methods get to n + O(n / log n).

**Caveat (input size).** The fixed modulus makes each multiplication O(1). For a k-bit modulus, multiply both
costs by the cost of one k-bit modular multiplication.

**Verification.** V1: agreement with each other and with the built-in `pow(a, e, m)` (oracle only).
V2: on e = 2ⁿ − 1, runtimes fit 2ⁿ and n
(`python tools/validate.py pairs/modular-exponentiation-repeated-vs-square-multiply --scaling -v`).

**Sources.** Knuth, TAOCP Vol. 2 (3rd ed.), §4.6.3.
