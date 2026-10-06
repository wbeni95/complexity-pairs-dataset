# Polynomial multiplication over Z_p: schoolbook vs NTT (FFT)

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time (n coefficients each) | Implementation |
|---|---|---|
| Schoolbook convolution | Θ(n²) | [naive.py](implementations/naive.py) |
| Number-theoretic transform | Θ(n log n) | [ntt.py](implementations/ntt.py) |

**Why it's a pair.** Evaluating at roots of unity turns convolution into pointwise multiplication. With
p = 998244353 = 119·2²³ + 1, the roots of unity live in Z_p and all arithmetic is exact.

**Verification.** V1: both implementations agree, and an independent evaluation check A(x)·B(x) = C(x)
passes. V2 uses exact counts of multiplications with an input-derived operand. The coefficients are
wrapped in a counting type, and the implementations are unchanged.
- Schoolbook: exactly n². α = 1.000, and the rivals n log n and n² log n are rejected.
- NTT, n a power of two: exactly 3n·log₂n + 5n, which is the cost expression used. α = 1.000, and the
  rivals n (α 1.111), n log² n and n² are rejected.

Tolerance is 0.03. The log factor is now resolved; the earlier timing fit could not resolve it.
Not counted: the twiddle-factor updates and `pow()` calls, which work on plain integers the implementation
creates itself; first-stage products with a padding zero; and all additions and reductions mod p.

**Sources.** Cooley & Tukey 1965 (Math. Comp.). Schönhage & Strassen 1971 (Computing).
Heideman, Johnson & Burrus 1984 (history, back to Gauss).
