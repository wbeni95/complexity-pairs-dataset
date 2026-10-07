# 0/1 knapsack: enumeration vs meet in the middle vs pseudo-polynomial DP

**Type:** T6 (open: no poly-in-input-size algorithm known), secondary T8 · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| Subset enumeration | Θ(2ⁿ·n) | [brute_force.py](implementations/brute_force.py) |
| Meet in the middle (Horowitz–Sahni 1974) | Θ(2^(n/2)·n) | [meet_in_the_middle.py](implementations/meet_in_the_middle.py) |
| Capacity DP | Θ(n·W), **pseudo-polynomial** | [dp.py](implementations/dp.py) |

**The pair (T8).** Enumeration → meet in the middle halves the exponent. The improvement is measured
(V2 runtime fits; the meet-in-the-middle bound is not derived here), and the result is still exponential.

**The cautionary point.** W is a *number*, and the input contains only log W bits for it. Adding one
bit to W roughly doubles the DP's running time when W is much larger than the item weights, so Θ(nW) is
exponential in the input size. Knapsack is
NP-hard (Karp 1972), and a truly polynomial algorithm would imply P = NP.

**Verification.** V1: all three agree, and the result respects a greedy lower bound. V2: the fits are
2ⁿn, 2^(n/2)n and n². The DP's n² holds only because this harness has W = Θ(n); it says nothing
about large W.

**Sources.** Karp 1972. Horowitz & Sahni 1974 (J. ACM). Ibarra & Kim 1975 (J. ACM, FPTAS).
