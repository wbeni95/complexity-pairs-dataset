# 2-SAT: brute force vs implication graph + SCC

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (exact operation counts, with rivals)

**Problem.** Given a CNF formula over n variables whose m clauses have at most 2 literals each, decide whether it
is satisfiable and, if so, output a satisfying assignment.

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force over all 2ⁿ assignments | O(2ⁿ·m); Θ(2ⁿ·m) worst case | [brute_force.py](implementations/brute_force.py) |
| Aspvall–Plass–Tarjan: implication graph + Tarjan SCC (iterative) | Θ(n + m) | [aspvall_plass_tarjan.py](implementations/aspvall_plass_tarjan.py) |

**Why it is here.** A clause (a ∨ b) is the same as the two implications ¬a → b and ¬b → a. The formula is
unsatisfiable exactly when some x and ¬x lie in one strongly connected component of this implication graph, and
otherwise the components' topological order gives a satisfying assignment. That turns an exponential search into
one linear-time depth-first search. With three literals per clause the problem becomes NP-complete: see the
boundary note [notes/boundary-2sat-vs-3sat.md](../../notes/boundary-2sat-vs-3sat.md) and the entry
[3sat-brute-force-vs-schoening](../3sat-brute-force-vs-schoening/).

**Verification.**
- *V1:* both implementations agree on satisfiability on 60 formulas (n up to 14 for brute force, up to 3000 for
  the SCC algorithm): random, planted-satisfiable, forced-unsatisfiable, with unit clauses, repeated literals,
  tautologies and empty clauses. The harness's `check` verifies every returned assignment against all clauses. It
  accepts "unsatisfiable" only with a proof: an empty clause; exhaustive search for n ≤ 12; or, for larger n, an
  explicit pair of implication paths x ⇝ ¬x and ¬x ⇝ x found by breadth-first search (the variable is located
  with a separate Kosaraju SCC implementation).
- *V2:* a counting literal type in the harness counts every operation on input-derived values. The implementations
  are unchanged. The instances come from the unsatisfiable family Wₙ: (x₁ ∨ xⱼ) for j = 2..n, a 4-clause
  unsatisfiable core on x₂, x₃, and the chain x₁ → x₂ → … → xₙ, so m = 2n + 2. Half of all assignments (x₁ true)
  pass the n − 1 star clauses before failing in the core, so brute force does exactly 3(n + 7)·2ⁿ + 12
  operations ((n + 7)·2ⁿ⁻¹ + 2 literal evaluations, derived by hand and checked for n = 3..16). The SCC algorithm
  does exactly 49(n + 2) (read off the data for n = 3..300 and the V2 sizes, not proven).

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| brute force vs (n + 7)·2ⁿ, n = 8..16 | 1.000 | 2ⁿ: 1.077, n²·2ⁿ: 0.862 |
| SCC vs n, n = 1000..32000 | 0.9995 | n log n: 0.895, n²: 0.500 |

Both fits also resolve the log factor (RL-048). [Experiment](../../experiments/2026-10-07b_two_sat_counts.py).

**Caveats.** Brute force stops at the first falsified clause, so its worst case needs a structured family. With
random clauses in front of the core the counts grow like 2ⁿ (α = 1.004 against 2ⁿ), not like m·2ⁿ. The fitted cost
is the exact count's form (n + 7)·2ⁿ: at n ≤ 16 the lower-order term matters, and the bare n·2ⁿ gives α = 0.958.
The SCC count leaves out the list accesses at the 2n DFS roots (plain integers from `range`), an O(n) part.
Papadimitriou's randomized walk (expected O(n²) flips) is not implemented.

**Sources.** Aspvall, Plass & Tarjan, IPL 1979. Tarjan, SIAM J. Comput. 1972. Even, Itai & Shamir, SIAM J.
Comput. 1976 (an earlier polynomial algorithm; recalled).
