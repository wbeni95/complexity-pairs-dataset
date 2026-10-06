# 3-SAT: brute force vs Schöning's random walk

**Type:** T6 (open: NP-complete), secondary T8 · **Verification:** V1

**Problem.** Decide whether a CNF formula with at most 3 literals per clause (n variables, m clauses) is
satisfiable.

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force over all assignments | O(2ⁿ·m) | [brute_force.py](implementations/brute_force.py) |
| Schöning's random walk (Monte Carlo, error ≤ 10⁻⁶) | O((4/3)ⁿ·n^1.5·m) | [schoening.py](implementations/schoening.py) |

**How the error is controlled.** One try (random start, 3n flips of a random variable in a falsified
clause) succeeds on a satisfiable formula with probability at least
p(n) = Σⱼ C(n,j)·2⁻ⁿ·C(3j,j)·(1/3)^(2j)·(2/3)^j ≈ 0.88·(3/4)ⁿ/√n. Each flip moves toward a fixed solution
with probability ≥ 1/3. The implementation runs T(n) = ⌈ln(10⁶)/p(n)⌉ tries (196 at n = 6, 1682 at
n = 12), so a satisfiable formula is missed with probability ≤ 10⁻⁶. "Satisfiable" answers are always
correct.

**Why only V1.** Two measurements argue against V2:
1. Over the n range pure Python can time (4..12), Schöning's runtimes on unsatisfiable formulas fit
   (4/3)ⁿ·n^2.5 (α = 0.960), but they also fit 2ⁿ (α = 0.865). The polynomial factors dominate there, so the
   fit cannot tell the claimed bound from brute force. On unsatisfiable inputs the runtime is in any case
   fixed by the restart budget.
2. Planted unique-solution formulas are far from the worst case: per-try success was 5.7–15× above p(n)
   ([experiment](../../experiments/2026-10-07_schoening_planted_success.py)).

**Verification.** V1: both agree with each other and with an independent DPLL oracle on random, planted,
unsatisfiable and mixed-width formulas, n ≤ 12 (reproducible under the validator's seeding).

**Sources.** Schöning, FOCS 1999. Cook, STOC 1971.
