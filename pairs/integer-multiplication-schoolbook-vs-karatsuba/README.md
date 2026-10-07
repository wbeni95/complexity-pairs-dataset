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

**The longer line.** Toom–Cook → Schönhage–Strassen 1971, O(n log n log log n) → Fürer 2007 →
Harvey–van der Hoeven 2021, O(n log n) (bit operations, multitape Turing machine).

**Verification.** V1: both agree with each other and with Python's built-in integer product, which is used
only as the oracle in `harness.check`. V2 counts **digit multiplications exactly** with an int-like digit type
(`CountingDigit`); the implementations are unchanged. Schoolbook makes exactly n², and Karatsuba (cutoff 32)
exactly 3^(log₂(n/32))·32², on n = 64..2048 (the closed form needs inputs in which no recursion node has equal
halves in both factors; the random digits used meet this). Both fit at tolerance 0.02 with α = 1.000. Each rival is
rejected: Karatsuba's counts against n² give α = 0.792, and the schoolbook counts against n^log₂3 give 1.262.
The earlier timing fit could not reject n² for Karatsuba (RL-056).

**Sources.** Karatsuba & Ofman 1962 (Doklady AN SSSR). Knuth, TAOCP Vol. 2, §4.3.3.
Schönhage & Strassen 1971. Fürer 2009 (SICOMP). Harvey & van der Hoeven 2021 (Annals of Math.).
