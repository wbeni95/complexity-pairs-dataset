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

**The longer line (sparse graphs).** Chazelle 2000: O(m α(m, n)) deterministic. Karger–Klein–Tarjan 1995:
expected O(m), randomized.

**Verification.** V1: all three agree with each other and with an independent Borůvka oracle, including
inputs with many tied weights. V2: runtimes fit the subset count (n = 4..7 only, since n = 8 already has
1.18 million subsets), n² log n and n².

**Sources.** Borůvka 1926. Cayley 1889. Kruskal 1956 (Proc. AMS). Prim 1957 (BSTJ). Karger, Klein & Tarjan 1995.
Chazelle 2000.
