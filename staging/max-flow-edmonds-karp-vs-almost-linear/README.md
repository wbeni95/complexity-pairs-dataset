<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Maximum flow: Edmonds-Karp vs push-relabel vs almost-linear time

**Type:** T3 (poly → faster poly) · **Verification:** V0

**Problem.** Given a directed graph with integer edge capacities, a source s and a sink t, compute the value of a maximum s-t flow.

**Input.** n vertices, m edges (capacities polynomially bounded integers for the almost-linear bound). Size: Theta(m log U) bits, U = largest capacity.

| Algorithm | Model | Time | Space |
|---|---|---|---|
| Edmonds-Karp | classical-deterministic | O(n m^2) | O(m) |
| push-relabel (Goldberg-Tarjan) | classical-deterministic | O(n m log(n^2 / m)) with dynamic trees | O(m) |
| almost-linear-time max flow (Chen et al.) | classical-randomized | m^(1+o(1)) | m^(1+o(1)) |

**Relationship.** All polynomial; O(n m^2) -> O(n m log(n^2/m)) -> m^(1+o(1)).

**Caveats.** The almost-linear algorithm is far from practical; its m^(o(1)) factor hides large terms. The m^(1+o(1)) bound assumes polynomially bounded integer capacities.

**Notes.** Path to V1: implement Edmonds-Karp and push-relabel (FIFO, O(n^3)) as a T3 pair with V2 scaling; keep the almost-linear algorithm as cited.

**Verification.** Cited from the literature; not yet independently implemented.

**Sources.**

- Ford, L. R.; Fulkerson, D. R. (1956). *Maximal flow through a network*. Canadian Journal of Mathematics 8, 399-404. [doi:10.4153/CJM-1956-045-5](https://doi.org/10.4153/CJM-1956-045-5)
- Edmonds, J.; Karp, R. M. (1972). *Theoretical improvements in algorithmic efficiency for network flow problems*. Journal of the ACM 19(2), 248-264. [doi:10.1145/321694.321699](https://doi.org/10.1145/321694.321699)
- Goldberg, A. V.; Tarjan, R. E. (1988). *A new approach to the maximum-flow problem*. Journal of the ACM 35(4), 921-940. [doi:10.1145/48014.61051](https://doi.org/10.1145/48014.61051)
- Chen, L.; Kyng, R.; Liu, Y. P.; Peng, R.; Probst Gutenberg, M.; Sachdeva, S. (2022). *Maximum Flow and Minimum-Cost Flow in Almost-Linear Time*. FOCS 2022. [arXiv:2203.00671](https://arxiv.org/abs/2203.00671)
