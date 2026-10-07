# Minimum spanning tree: edge-subset enumeration vs Kruskal (and Prim)

**Type:** T2 (naive-exp → poly) · **Verification:** V2

**Problem.** Given the complete graph Kₙ with positive integer edge weights, return the total weight of a
minimum spanning tree.

| Algorithm | Time (Kₙ, m = n(n−1)/2 edges) | Implementation |
|---|---|---|
| All (n−1)-edge subsets | Θ(n · C(n(n−1)/2, n−1)) = 2^Θ(n log n) | [brute_force.py](implementations/brute_force.py) |
| Kruskal + union-find (1956) | O(m log m) = O(n² log n) | [kruskal.py](implementations/kruskal.py) |
| Prim, array version (1957) | Θ(n²), linear in the input | [prim.py](implementations/prim.py) |

**Why it's a pair.** By the cut property the lightest edge across any cut is safe, so greedy choices
never need to be undone and no search is needed. Even listing only the spanning trees would not help,
because Kₙ has n^(n−2) of them (Cayley).

**Prim is optimal on Kₙ.** An adversary that answers 2 to every weight query can still give any unread edge
weight 1, which changes the answer from 2(n − 1) to 2n − 3. So every correct deterministic algorithm reads all
n(n−1)/2 weights, and Prim's Θ(n²) is optimal up to a constant factor.

**The longer line (sparse graphs).** Chazelle 2000: O(m α(m, n)) deterministic. Karger–Klein–Tarjan 1995:
expected O(m), randomized.

**Verification.** V1: all three agree with each other and with an independent Borůvka oracle, including
inputs with many tied weights. V2 uses exact counts of comparisons and arithmetic operations on input
weights. The weights are wrapped in a counting type, and the implementations are unchanged. Kruskal packs
each edge into the key w·n² + u·n + v, and that key stays a counting value, so the comparisons inside
`sorted()` are counted too.
- Kruskal: 3m packing operations + sort comparisons + one divmod per scanned key. α = 0.998 against
  n² log n, and the rivals n² (α 1.094), n² log² n and n³ are rejected.
- Prim: exactly (n−1)². α = 1.007 against n², and the rivals n² log n (α 0.918) and n³ are rejected.
- Enumeration: exactly (n−1)·C(m, n−1) + n^(n−2) − 1, on n = 4..7 only, since n = 8 already has
  1.18 million subsets. α = 0.995 against n·C(m, n−1). The rivals C(m, n−1), n²·C(m, n−1) and n^(n−2)
  are rejected.

Tolerance is 0.03. The log factor between Kruskal and Prim is now resolved. Kruskal's sort comparisons
depend on the Python version: under 3.12.10 they are 0.17–0.30% fewer than under 3.14.2, with the same α
and the same verdicts.

**Sources.** Borůvka 1926. Cayley 1889. Kruskal 1956 (Proc. AMS). Prim 1957 (BSTJ). Karger, Klein & Tarjan 1995.
Chazelle 2000.
