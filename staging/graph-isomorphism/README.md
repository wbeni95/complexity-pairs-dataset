<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Graph isomorphism: moderately exponential vs quasi-polynomial

**Type:** T6, T8 (open / unpaired) · **Verification:** V0

**Problem.** Given two graphs on n vertices, decide whether they are isomorphic.

**Input.** n = number of vertices. Size: O(n^2) bits (adjacency matrices).

| Algorithm | Model | Time | Space |
|---|---|---|---|
| brute force over permutations | classical-deterministic | O(n! n^2) | O(n^2) |
| Babai-Luks canonical labeling | classical-deterministic | exp(O(sqrt(n log n))) | exp(O(sqrt(n log n))) |
| Babai's quasi-polynomial algorithm | classical-deterministic | exp((log n)^O(1)) (quasi-polynomial) | quasi-polynomial |

**Relationship.** n! -> exp(sqrt(n log n)) -> quasi-polynomial exp(polylog n). A polynomial-time algorithm is open. Polynomial algorithms exist for restricted classes, e.g. bounded degree (Luks 1982).

**Caveats.** In January 2017 Harald Helfgott found an error in the analysis of Babai's algorithm. Babai repaired it within days, restoring the quasi-polynomial bound. GI is not known to be NP-complete (that would collapse the polynomial hierarchy to its second level). No efficient quantum algorithm is known either: the relevant hidden subgroup problem over the symmetric group resists Fourier sampling.

**Notes.** Interesting for the quantum question because quantum computers are NOT known to help here, unlike factoring.

**Verification.** Cited from the literature.

**Sources.**

- Luks, E. M. (1982). *Isomorphism of graphs of bounded valence can be tested in polynomial time*. Journal of Computer and System Sciences 25(1), 42-65. [doi:10.1016/0022-0000(82)90009-5](https://doi.org/10.1016/0022-0000(82)90009-5)
- Babai, L.; Luks, E. M. (1983). *Canonical labeling of graphs*. STOC 1983, 171-183. [doi:10.1145/800061.808746](https://doi.org/10.1145/800061.808746)
- Babai, L. (2016). *Graph isomorphism in quasipolynomial time*. STOC 2016. [doi:10.1145/2897518.2897542](https://doi.org/10.1145/2897518.2897542) [arXiv:1512.03547](https://arxiv.org/abs/1512.03547)
