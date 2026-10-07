# 0/1 knapsack: enumeration vs meet in the middle vs pseudo-polynomial DP

**Type:** T6 (open: no poly-in-input-size algorithm known; background, cited), secondary T8 · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| Subset enumeration | Θ(2ⁿ·n) | [brute_force.py](implementations/brute_force.py) |
| Meet in the middle (Horowitz–Sahni 1974) | Θ(2^(n/2)·n) in the worst case (machine-model assumptions below) | [meet_in_the_middle.py](implementations/meet_in_the_middle.py) |
| Capacity DP | Θ(n·W) in the worst case, **pseudo-polynomial** | [dp.py](implementations/dp.py) |

**The pair (T8).** Enumeration → meet in the middle halves the exponent. The improvement is proved in
[PROOFS.md](PROOFS.md), under two machine-model assumptions (background): the built-in sort runs in O(m log m)
(basis: CPython's list sort merges in the powersort order of `Objects/listsort.txt`, for which Munro & Wild 2018,
Theorem 6, bound the comparisons of a plain merge; the galloping merges are not covered, so this is an assumption),
and `bisect_right` runs the documented halving loop (CPython source). It is also measured by V2 runtime fits, and the result is still exponential.

**The cautionary point.** W is a *number*, and the input contains only log W bits for it. Adding one
bit to W roughly doubles the DP's running time when W is much larger than the item weights, so Θ(nW) is
exponential in the input size. *Background (cited, not a claim of this entry):* knapsack is NP-hard (Karp 1972),
and a truly polynomial algorithm would imply P = NP.

**Verification.** V1: all three agree, and the result respects a greedy lower bound. V2: the fits are
2ⁿn, 2^(n/2)n and n². The DP's n² holds only because this harness has W = Θ(n); it says nothing
about large W.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: correctness of all three algorithms,
exactly n·2ⁿ inner iterations for enumeration, the worst-case Θ(2^(n/2)·n) of meet in the middle (under the
machine-model assumptions that the built-in sort is O(m log m) and that `bisect_right` runs the documented halving
loop), exactly Σ max(0, W − wᵢ + 1) inner iterations for the DP, and the doubling when a bit
is added to W. The capacity must be W ≥ 0. [tests/test_proofs_knapsack.py](../../tests/test_proofs_knapsack.py)
checks the computable facts.

**Sources.** Karp 1972. Horowitz & Sahni 1974 (J. ACM). Ibarra & Kim 1975 (J. ACM). Auger, Jugé, Nicaud &
Pivoteau 2018 (arXiv:1805.08612). Munro & Wild, ESA 2018. CPython `Objects/listsort.txt`, `Lib/bisect.py`,
`Modules/_bisectmodule.c`.
