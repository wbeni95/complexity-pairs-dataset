# 3-SAT: brute force vs Schöning's random walk

**Type:** T6 (open: NP-complete; cited background), secondary T8 · **Verification:** V1

**Problem.** Decide whether a CNF formula with at most 3 literals per clause (n variables, m clauses) is
satisfiable.

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force over all assignments | O(2ⁿ·m) | [brute_force.py](implementations/brute_force.py) |
| Schöning's random walk (Monte Carlo, error ≤ 10⁻⁶) | O((4/3)ⁿ·n^1.5·m) | [schoening.py](implementations/schoening.py) |

**How the error is controlled.** One try (random start, 3n flips of a random variable in the first falsified
clause) succeeds on a satisfiable formula with probability at least
p(n) = Σⱼ C(n,j)·2⁻ⁿ·C(3j,j)·(1/3)^(2j)·(2/3)^j. Each flip moves toward a fixed solution with probability
≥ 1/3, and a coupling with independent Bernoulli(1/3) steps turns this into the bound p(n). Stirling's formula
and Jensen's inequality give 0.431·(3/4)ⁿ·√(3/(n+3)) ≤ p(n) ≤ (3/4)ⁿ·√(3/(n+1)), so p(n) = Θ((3/4)ⁿ/√n)
(the constant is 0.87–0.89 for n = 14..20). The implementation runs T(n) ≥ ⌈ln(10⁶)/p(n)⌉ tries, computed in
floating point (equal for n ≤ 88, larger by a relative 10⁻¹² at most up to n = 373; 196 at n = 6, 1682 at
n = 12), so a satisfiable formula is missed with probability ≤ 10⁻⁶. "Satisfiable" answers are always correct.
For n ≥ 374 the floating-point computation overflows, and the implementation raises an overflow error on every
formula without an empty clause instead of answering.

**Why only V1.** Two measurements argue against V2:
1. Over the n range pure Python can time (4..12), Schöning's runtimes on unsatisfiable formulas fit
   (4/3)ⁿ·n^2.5 (α = 0.960), but they also fit 2ⁿ (α = 0.865). The polynomial factors dominate there, so the
   fit cannot tell the claimed bound from brute force. On unsatisfiable inputs the runtime is in any case
   fixed by the restart budget.
2. Planted unique-solution formulas are far from the worst case: per-try success was 5.7–15× above p(n)
   ([experiment](../../experiments/2026-10-07_schoening_planted_success.py)).

**Verification.** V1: both agree with each other and with an independent DPLL oracle on random, planted,
unsatisfiable and mixed-width formulas, n ≤ 12 (reproducible under the validator's seeding).

**Proofs.** [PROOFS.md](PROOFS.md) proves the correctness of both algorithms, the one-sided error bound (with the
coupling step written out), the explicit bounds on p(n) and T(n), the running times and the space bounds.
[tests/test_proofs_3sat.py](../../tests/test_proofs_3sat.py) re-runs their computable facts on stated ranges.

**Background (cited, not proved here).** 3-SAT is NP-complete (Cook 1971), which is the reason for the T6 tag.
For k-SAT the walk gives (2(k−1)/k)ⁿ up to polynomial factors (Schöning 1999). Faster exponential algorithms are
known (PPSZ and its successors; see staging/boolean-satisfiability). 2-SAT is solvable in linear time (Aspvall,
Plass & Tarjan 1979).

**Sources.** Schöning, FOCS 1999. Cook, STOC 1971. Paturi, Pudlák, Saks & Zane, J. ACM 2005. Hertli, SIAM J.
Comput. 2014. Aspvall, Plass & Tarjan, IPL 1979.
