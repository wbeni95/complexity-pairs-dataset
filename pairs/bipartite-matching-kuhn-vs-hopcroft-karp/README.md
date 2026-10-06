# Maximum bipartite matching: Kuhn vs Hopcroft–Karp

**Type:** T3 (poly → faster poly) · **Verification:** V2 (on an adversarial family, see below)

**Problem.** Find the size of a maximum matching in a bipartite graph with V vertices and E edges.

| Algorithm | Time | Implementation |
|---|---|---|
| Kuhn: one augmenting-path DFS per left vertex | O(V·(V + E)) = O(V·E) | [kuhn.py](implementations/kuhn.py) |
| Hopcroft–Karp (1973): phases of disjoint shortest augmenting paths | O((V + E)·√V) | [hopcroft_karp.py](implementations/hopcroft_karp.py) |

**Why it's a pair.** Kuhn may traverse the whole graph for each single augmentation. Hopcroft–Karp
augments along a maximal set of vertex-disjoint shortest paths per traversal, and the shortest length
grows every phase, which leaves only O(√V) phases.

**Worst cases have to be built.** On random graphs Hopcroft–Karp needed only 2 to 5 phases, so random inputs
do not show its √V factor. The timing family G_k (V = 4k² + k) is a disjoint union of two gadgets:
- a dense K_{2a,a} with a = k². Its a unmatchable left vertices make each of Kuhn's failing searches, and
  every Hopcroft–Karp phase, scan the whole gadget;
- paths P₂, P₄, …, P_{2k}, numbered and ordered so that Hopcroft–Karp's first phase picks the "wrong" edge of
  every path. Phase j can then repair only path j.

Exact counts ([experiment](../../experiments/2026-10-07_bipartite_matching_counts.py)): Hopcroft–Karp ran
**exactly k + 1 phases** for k = 2, 4, …, 16. Kuhn's edge scans settle at 0.144·V·E, and Hopcroft–Karp's at
1.01–1.05·E·√V.

**Verification.** V1: both agree with each other and with an independent algebraic oracle: the rank of the
Edmonds matrix with random entries mod 2⁶¹ − 1, which equals the matching size except with probability
< 10⁻¹⁵. V2: on G_k, runtimes fit n³ (Kuhn) and n^2.5 (Hopcroft–Karp), n = V. A timing fit alone cannot
separate exponents 3 and 2.5 at tolerance 0.25. The exact counts above carry that part of the claim.

**Sources.** Hopcroft & Karp, SIAM J. Comput. 2(4), 1973. Berge, PNAS 43(9), 1957. Kuhn, Naval Res.
Logist. Q. 2, 1955.
