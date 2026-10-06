# Horn-SAT: brute force vs linear-time unit propagation

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (exact operation counts, with rivals)

**Problem.** Given a CNF formula over n variables in which every clause has at most one positive literal (a Horn
formula), decide whether it is satisfiable and, if so, output its least model: the satisfying assignment whose true
variables are true in every satisfying assignment. It exists because the models of a Horn formula are closed under
intersection.

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force over all 2ⁿ assignments (stops at the first satisfying one) | O(2ⁿ·L); Θ(2ⁿ·m) on the worst-case family | [brute_force.py](implementations/brute_force.py) |
| Unit propagation with clause counters (Dowling–Gallier 1984) | Θ(n + L) | [unit_propagation.py](implementations/unit_propagation.py) |

L is the total number of literal occurrences, m the number of clauses.

**Why it is here.** A Horn clause ¬y₁ ∨ … ∨ ¬y_k ∨ h is the implication y₁ ∧ … ∧ y_k → h. The variables that are true in
every model can therefore be computed forward from the facts. A counter per clause records how many of its premises are
still open, so each clause fires at most once and the whole computation is linear. Horn formulas are one of Schaefer's
(1978) tractable classes of Boolean constraints, next to 2-SAT ([two-sat-brute-force-vs-scc](../two-sat-brute-force-vs-scc/))
and XOR-SAT ([xor-sat-brute-force-vs-gaussian-elimination](../xor-sat-brute-force-vs-gaussian-elimination/)); for
general CNF formulas satisfiability is NP-complete (Cook 1971; see
[3sat-brute-force-vs-schoening](../3sat-brute-force-vs-schoening/)).

Brute force scans the masks 0, 1, …, 2ⁿ − 1 and stops at the first satisfying one. For a Horn formula that is exactly the
least model, since every model contains it bit by bit. Both implementations therefore return the same tuple, and V1
compares them with `==`.

**Verification.**
- *V1:* both implementations agree on 56 formulas (n = 0..14 for brute force, up to 300 for propagation): random Horn
  CNF, planted derivation chains (satisfiable, and unsatisfiable with a goal on the derived variables), repeated
  literals, tautologies, empty clauses, definite-clause formulas and the V2 family under renaming. The independent
  `check` recomputes the derived set by *naive* forward chaining (full passes until nothing changes). It accepts an
  assignment only if it equals that set and satisfies every clause, and accepts "unsatisfiable" only if the derived set
  violates a clause, which is a proof. For n ≤ 10 it also cross-checks by exhaustive search.
- *Oracle control* ([experiment](../../experiments/2026-10-06f_entries_horn_sat.py)): 1040 correct outputs accepted;
  all 2816 wrong ones rejected (flipped bits, strictly larger models, "unsatisfiable" for satisfiable formulas, an
  assignment for unsatisfiable ones, wrong lengths).
- *V2:* a counting literal type counts every operation on input-derived values; the implementations are unchanged.
  Family Hₙ: (¬x₁ ∨ ¬xⱼ ∨ xⱼ₊₁) for j = n−1 down to 2, then (x₁), (¬x₁ ∨ x₂), (¬xₙ). It is unsatisfiable, so brute force
  examines all 2ⁿ assignments. Half of them (x₁ false) pass the n − 2 star clauses before failing, which gives exactly
  (2n + 13)·2ⁿ⁻² − 2n − 4 literal evaluations, 6 counted operations each (derived by hand; checked for n = 3..16).
  Propagation does exactly 12n − 7 operations (by inspection; checked for n = 3..300). On the same family, naive
  forward chaining needs exactly n full passes, i.e. Θ(n²) clause visits.

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| brute force vs (2n + 13)·2ⁿ − 8n − 16, n = 8..16 | 1.000 | 2ⁿ: 1.081, n²·2ⁿ: 0.865 |
| unit propagation vs 12n − 7, n = 1000..32000 | 1.000 | n log n: 0.895, n²: 0.500 |

**Caveats.** On satisfiable formulas brute force stops early. A formula without facts is satisfied by mask 0 at once, so
the worst-case family must be unsatisfiable, with its clauses ordered so that assignments fail late. With clauses in
random order the count grows like 2ⁿ, not m·2ⁿ. The fitted cost is the exact count's form; the bare n·2ⁿ gives α = 0.961.
The propagation count leaves out the counter decrements, which use plain clause indices. Each negative literal is
decremented at most once and costs a counted operation when it is read, so the uncounted part is O(L).

**Sources.** Dowling & Gallier, J. Logic Programming 1984. Horn, J. Symbolic Logic 1951. Minoux, IPL 1988. Schaefer,
STOC 1978. Cook, STOC 1971.
