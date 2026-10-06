# Polynomial multiplication over Z_p: schoolbook vs NTT (FFT)

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time (n coefficients each) | Implementation |
|---|---|---|
| Schoolbook convolution | Θ(n²) | [naive.py](implementations/naive.py) |
| Number-theoretic transform | Θ(n log n) | [ntt.py](implementations/ntt.py) |

**Why it's a pair.** Evaluating at roots of unity turns convolution into pointwise multiplication. With
p = 998244353 = 119·2²³ + 1, the roots of unity live in Z_p and all arithmetic is exact.

**Verification.** V1: both implementations agree, and an independent evaluation check A(x)·B(x) = C(x)
passes. V2: the fits are n² and n log n. A log factor cannot be resolved this way, but quadratic
behaviour would be caught.

**Sources.** Cooley & Tukey 1965 (Math. Comp.). Schönhage & Strassen 1971 (Computing).
Heideman, Johnson & Burrus 1984 (history, back to Gauss).
