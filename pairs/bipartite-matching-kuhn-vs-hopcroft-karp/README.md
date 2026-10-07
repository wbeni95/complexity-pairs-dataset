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

**Worst cases have to be built.** On the 8 random graphs measured (V = 100..800, p = 0.05 and 0.5) Hopcroft–Karp
needed only 2 to 5 phases, so these inputs do not show its √V factor. The timing family G_k (V = 4k² + k) is a
disjoint union of two gadgets:
- a dense K_{2a,a} with a = k². Its a unmatchable left vertices make each of Kuhn's a failing searches read the
  lists of its root and of all a matched gadget vertices (a(a + 1) of the gadget's 2a² entries), and every
  Hopcroft–Karp phase read all 2a² entries in its breadth-first search;
- paths P₂, P₄, …, P_{2k}, numbered and ordered so that Hopcroft–Karp's first phase picks the "wrong" edge of
  every path. Phase j can then repair only path j.

Exact counts for every k ≥ 1 (proved in [PROOFS.md](PROOFS.md), sections 2–3); the
[experiment](../../experiments/2026-10-07_bipartite_matching_counts.py) and the V2 counts agree with them. Kuhn
makes exactly (7k⁶ + 9k⁴ + 11k² − 3k)/6 edge scans, Θ(V·E) = Θ(V³), with ratio to V·E tending to 7/48 ≈ 0.146.
Hopcroft–Karp runs **exactly k + 1 phases** with (24k⁵ + 9k⁴ + 4k³ + 24k² − 25k + 12)/6 edge scans, with ratio
to E·√V tending to 1. On every input Kuhn makes at most n_left·E ≤ V·E scans, so over graphs with V vertices
the worst cases are Θ(V³) for Kuhn (for every V ≥ 5, padding G_k with isolated vertices) against O(V^2.5) for
Hopcroft–Karp.

**Verification.** V1: both agree with each other and with an independent algebraic oracle: the rank of the
Edmonds matrix with random entries mod 2⁶¹ − 1, which equals the matching size except with probability
< 10⁻¹⁵. V2: on G_k, the harness counts **edge scans exactly** with an instrumented adjacency-list type
(`CountingNeighbours`); the implementations are unchanged, and the counts equal those of the instrumented
copies in the experiment above. As functions of n = V, Kuhn's scans fit n³ (α = 1.005, k = 3..11) and
Hopcroft–Karp's fit n^2.5 (α = 1.004, k = 4..15). With tolerance 0.03 the counts reject the rivals that the
timing fit could not reject at tolerance 0.25 (RL-030): Kuhn against n^2.5 (α = 1.207), Hopcroft–Karp against n²
(1.255) and n³ (0.837). Details: `experiments/2026-10-07b_count_v2_matching.py` and
`research/2026-10-07b_count_based_v2.md`.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry from the code: the exact operation counts for
all sizes of their domains, the correctness of both algorithms (with Berge's criterion and the Hopcroft–Karp lemmas),
the bound of fewer than √(2V) + 1 phases for V ≥ 1, the time and space bounds, the separation over all V, the
oracle's error bound, and that matchings are the integral flows of a unit-capacity network. It names the scripts and
tests (among them `tests/test_proofs_matching.py`) and the sizes that check each statement.

**Sources.** Hopcroft & Karp, SIAM J. Comput. 2(4), 1973. Berge, PNAS 43(9), 1957. Kuhn, Naval Res.
Logist. Q. 2, 1955.
