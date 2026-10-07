# Integer multiplication: schoolbook vs Karatsuba

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Multiply two n-digit non-negative integers given as little-endian lists of base-2¹⁵ digits.
The result is a list of 2n digits.

| Algorithm | Time (n digits) | Implementation |
|---|---|---|
| Schoolbook | Θ(n²) | [schoolbook.py](implementations/schoolbook.py) |
| Karatsuba (1962) | Θ(n^log₂3) ≈ Θ(n^1.585) | [karatsuba.py](implementations/karatsuba.py) |

**Why it's a pair.** Three half-size products are enough instead of four, because
x₀y₁ + x₁y₀ = x₀y₀ + x₁y₁ − (x₁ − x₀)(y₁ − y₀). Below 32 digits the recursion falls back to schoolbook, which changes
only the constants.

**The longer line (background, cited; not proved here).** Toom–Cook (Knuth, TAOCP Vol. 2) →
Schönhage–Strassen 1971 → Fürer 2009 → Harvey–van der Hoeven 2021, O(n log n) bit operations on a multitape Turing
machine (abstract).

**Verification.** V1: both agree with each other and with Python's built-in integer product, which is used
only as the oracle in `harness.check`. V2 counts **digit multiplications exactly** with an int-like digit type
(`CountingDigit`); the implementations are unchanged. Schoolbook makes exactly n², and Karatsuba (cutoff 32)
exactly 3^(log₂(n/32))·32², on n = 64..2048 (the closed form needs inputs in which no recursion node has equal
halves in both factors; the random digits used meet this). Both fit at tolerance 0.02 with α = 1.000. Each rival is
rejected: Karatsuba's counts against n² give α = 0.792, and the schoolbook counts against n^log₂3 give 1.262.
The earlier timing fit could not reject n² for Karatsuba (RL-056).

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the correctness of both
algorithms (with the carry and borrow helpers), the word-size bound (every value computed from digits below 2³⁰;
indices have O(log n) bits), the time bounds for every n (the recursion shape and the exact number 3^d·⌈n/2^d⌉² of
digit multiplications performed), the space bounds, and the exact counts for all sizes of their domains. It names the scripts and tests that check each one
(`tests/test_proofs_karatsuba.py` among them).

**Sources.** Karatsuba & Ofman 1962 (Doklady AN SSSR). Knuth, TAOCP Vol. 2.
Schönhage & Strassen 1971. Fürer 2009 (SICOMP). Harvey & van der Hoeven 2021 (Annals of Math.).
