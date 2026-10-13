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

**Background (cited) and an own step: the Jerrum–Snir lower bound.** Jerrum and Snir (J. ACM 1982,
§4.4, display on p. 890) consider straight-line programs that use only min and + (constants allowed). They prove
that every such program computing the Hamiltonian-circuit polynomial, whose value over non-negative weights is the
optimal tour length, needs at least (n−1)[(n−2)·2ⁿ⁻³ + 1] additions (n ≥ 3), and that this is attainable.
- Held–Karp is such a program in the n(n−1) entries, and it makes exactly this many additions of weights (PROOFS.md
  Theorem 5).
- Jerrum and Snir state the bound for all real, or all non-negative real, weights. PROOFS.md Lemma 6 (own) transfers
  it to this entry's integer inputs: no (min, +) straight-line program that outputs the optimal tour length for
  every non-negative integer matrix uses fewer additions (Corollary 7).
- Nothing is claimed for programs with branching, which can help exponentially over (min, +) (Jerrum–Snir §5.2), nor
  for symmetric inputs.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: both algorithms are correct, the enumeration
evaluates exactly (n−1)! tours (Θ(n) amortised each, assuming `itertools.permutations` behaves as its documented
code: machine-model assumption, background), and Held–Karp runs its inner loop exactly (n−1)²·2ⁿ⁻² times with a table of
2ⁿ⁻¹·(n−1) entries. Section 5 counts the additions of Held–Karp and proves Lemma 6.
[tests/test_proofs_tsp.py](../../tests/test_proofs_tsp.py) checks the computable facts.

**Sources.** Held & Karp 1962 (J. SIAM). Bellman 1962 (J. ACM). Karp 1972. Jerrum & Snir 1982 (J. ACM; lower bound
for (min, +) straight-line programs).
