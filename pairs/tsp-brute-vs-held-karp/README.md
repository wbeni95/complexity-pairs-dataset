# Travelling salesman: enumeration vs Held–Karp

**Type:** T6 (open: NP-hard), secondary T8 · **Verification:** V2

| Algorithm | Time (n cities) | Implementation |
|---|---|---|
| Permutation enumeration | Θ(n!) | [brute_force.py](implementations/brute_force.py) |
| Held–Karp DP (1962) | Θ(n²·2ⁿ) | [held_karp.py](implementations/held_karp.py) |

**Why it's here.** Factorial → single exponential (T8) is a huge, verified improvement, and the result
is *still* exponential. TSP is NP-hard.

**Sources.** Held & Karp 1962 (J. SIAM). Bellman 1962 (J. ACM). Karp 1972.
