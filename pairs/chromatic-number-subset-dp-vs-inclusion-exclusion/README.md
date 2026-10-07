# Chromatic number: subset DP vs inclusion–exclusion

**Type:** T6 (open: NP-hard; cited background), secondary T8 · **Verification:** V2

**Problem.** Compute the chromatic number χ(G) of an n-vertex graph.

| Algorithm | Time (n vertices) | Implementation |
|---|---|---|
| Subset DP over all independent sets | Θ(3ⁿ): exactly 3ⁿ − 2ⁿ inner iterations | [subset_dp.py](implementations/subset_dp.py) |
| Inclusion–exclusion (Björklund–Husfeldt–Koivisto 2009) | (2χ + 2)·2ⁿ − 2 arithmetic operations = O(n·2ⁿ) unit-cost | [inclusion_exclusion.py](implementations/inclusion_exclusion.py) |

**What exactly is implemented.** The DP removes one independent set T ⊆ S at a time and lets T range over
*all* independent subsets of S, which gives Σ_S 2^|S| = 3ⁿ. Lawler's refinement (1976), with T ranging only
over *maximal* independent sets of G[S], gives O((1 + 3^(1/3))ⁿ) = O(2.4423ⁿ) through the Moon–Moser bound;
that is cited background and is not what this entry implements or times.

Inclusion–exclusion counts covers instead of searching. If a(S) is the number of non-empty independent
sets inside S, then c_k = Σ_S (−1)^(n−|S|) a(S)^k counts k-tuples of independent sets covering V, and χ is
the least k with c_k > 0. The implementation tabulates a(S) in one pass. It then tries k = 1, 2, …,
with one multiplication and one addition per subset per round. (BHK's Proposition 1 raises to the k-th
power by repeated squaring instead; cited background.)

**Verification.** V1: both agree with each other and with an independent backtracking k-colouring oracle
on random, empty, complete, cycle, bipartite and triangle-union graphs, n ≤ 14. V2 on G(n, 0.8): runtimes
fit 3ⁿ and n·2ⁿ. On these instances χ/n stays between 0.50 and 5/7 ≈ 0.714 for n ≤ 18, so the number of rounds
grows linearly. The fit cannot resolve the factor n (α = 0.954 against n·2ⁿ, 1.069 against 2ⁿ) but
rejects 3ⁿ (α = 0.674).

Exact counts by harness instrumentation were examined
([research/2026-10-06c_count_v2_remaining.md](../../research/2026-10-06c_count_v2_remaining.md)) and are not
possible with the implementations unchanged. With n and the edge endpoints instrumented, input-derived values
reach only the Θ(2ⁿ) masks of the tabulation pass, plus setup and index conversions. The χ rounds multiply and
add values built from the literals `[1] * size` and `[0] * size`, at indices from `range(size)`. So the timing
fits stay, and the factor n is still unresolved in the V2 measurement.

**Proofs.** [PROOFS.md](PROOFS.md) proves both algorithms correct, proves the exact counts 3ⁿ − 2ⁿ and
(2χ + 2)·2ⁿ − 2, the bit sizes (table entries at most nχ bits, running sums at most n(χ + 1)) and the space bounds.
[tests/test_proofs_chromatic.py](../../tests/test_proofs_chromatic.py) checks the counts by counting executed
source lines of the unchanged code (n ≤ 10), and the correctness on every graph with n ≤ 5.

**Sources.** Lawler, IPL 5(3), 1976. Björklund, Husfeldt & Koivisto, SIAM J. Comput. 39(2), 2009 (read in
the authors' open-access version). Moon & Moser, Israel J. Math. 3(1), 1965. Eppstein, JGAA 7(2), 2003.
Karp 1972.
