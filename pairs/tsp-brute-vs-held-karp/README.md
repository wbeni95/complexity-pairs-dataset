# Travelling salesman: enumeration vs Held–Karp

**Type:** T6 (open: NP-hard; background, cited), secondary T8 · **Verification:** V2

| Algorithm | Time (n cities) | Implementation |
|---|---|---|
| Permutation enumeration | Θ(n!) | [brute_force.py](implementations/brute_force.py) |
| Held–Karp DP (1962) | Θ(n²·2ⁿ) | [held_karp.py](implementations/held_karp.py) |

**Why it's here.** Factorial → single exponential (T8) is a huge improvement (proved in [PROOFS.md](PROOFS.md) and
measured by V2 runtime fits), and the result is *still* exponential. TSP is NP-hard: the Hamiltonian circuit
problem is NP-complete (Karp 1972; *background, cited*), and the one-line reduction to TSP (n ≥ 2) is proved in
PROOFS.md.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: both algorithms are correct, the enumeration
evaluates exactly (n−1)! tours (Θ(n) amortised each, assuming `itertools.permutations` behaves as its documented
code: machine-model assumption, background), and Held–Karp runs its inner loop exactly (n−1)²·2ⁿ⁻² times with a table of
2ⁿ⁻¹·(n−1) entries. [tests/test_proofs_tsp.py](../../tests/test_proofs_tsp.py) checks the computable facts.

**Sources.** Held & Karp 1962 (J. SIAM). Bellman 1962 (J. ACM). Karp 1972.
