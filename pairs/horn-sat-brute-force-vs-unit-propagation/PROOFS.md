# Proofs: Horn-SAT, brute force vs unit propagation

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its two algorithms, from first principles and from the code in this folder. Sections 1 to 3
prove the exact operation counts, for every size of their domains. Sections 4 to 10 prove the rest: the least model,
the correctness of both algorithms, their time and space bounds, the worst case of brute force for every L,
dual-Horn formulas, the caveats and the soundness of the V1 oracle. Each proof is followed by the deterministic
scripts or tests that check it and the ranges they check; a check covers only those ranges, the proofs cover the
general statements. Statements about the literature (NP-completeness of CNF satisfiability, Schaefer's classes,
Minoux's algorithm) are not claims of this entry; they are listed in the `background` field of `entry.json` with
their sources, and nothing below depends on them. Citations give credit; they are never part of a proof.

## Counting convention

`harness.py`, class `CountingLit`: every arithmetic method (`__abs__`, `__neg__`, `__add__`, `__sub__`, `__and__`,
`__rshift__`, `__rrshift__` and the other reflected forms) adds 1 to the module counter `_ops` through `_arith` and
returns a new `CountingLit`; every comparison adds 1 through `_cmp` and returns a plain bool; `__index__` (also
used as `__int__`), `__hash__` and `__bool__` each add 1. `generate_scaling(n, rng)` raises for n < 3, otherwise
returns (n, clauses) for the family H_n with every literal a `CountingLit`, and sets `_ops = 0`;
`reported_cost(output)` returns `_ops`. So the domain of both counts is n ≥ 3.

A binary operation with a `CountingLit` operand counts 1 (if the left operand is a plain int, the int method
returns `NotImplemented` and Python calls the reflected method); indexing a list with a `CountingLit` calls its
`__index__` (1 count). Plain: the clause index `c`, the counters `k` and `counter[c]`, the mask, the booleans in
`value`, and the head `h = 0` of a clause without positive literal.

**The family H_n** (`_family(n)`), in this order: the star clauses S_j = (¬x1 ∨ ¬x_j ∨ x_{j+1}) for
j = n − 1, n − 2, …, 2 (literals in the order −1, −j, j + 1), then F1 = (x1), F2 = (¬x1 ∨ x2), G = (¬x_n). It is
unsatisfiable: F1 forces x1, F2 then x2, S_2, …, S_{n−1} in turn x3, …, x_n, and G forbids x_n.

## 1. Brute force: (2n + 13)2^(n−2) − 2n − 4 literal evaluations, 6 operations each

**Statement.** For every n ≥ 3, `horn_sat_brute_force` on H_n makes exactly (2n + 13)2^(n−2) − 2n − 4 literal
evaluations, (n − 1)2^(n−1) of them on the assignments with x1 false, and 6((2n + 13)2^(n−2) − 2n − 4) counted
operations. (The fitted cost expression (2n + 13)2ⁿ − 8n − 16 is 4 times the number of evaluations.)

**Proof.** *Six operations per evaluation.* `((mask >> (abs(lit) - 1)) & 1) == (lit > 0)` makes `abs(lit)`
(`__abs__`), `- 1` (`__sub__`), `mask >> …` with a plain left operand (`__rrshift__`), `& 1` (`__and__`), `lit > 0`
(`__gt__`) and the final `==` (`__eq__`, returning a plain bool): 6 counts, and nothing else in the loop counts.

*All 2ⁿ masks are examined*, since H_n is unsatisfiable, and each mask scans the clauses in order, each clause
literal by literal until a true literal, and moves to the next mask at the first falsified clause.

*The rest of the count* is the argument in `entry.json`, `algorithms[0].correctness`: the 2^(n−1) masks with x1
false spend one evaluation on each S_j (¬x1 is true) and one on F1 (false): (n − 1)2^(n−1). With x1 true, S_j costs 2
evaluations if x_j is false and 3 if x_j is true (then it fails exactly when x_{j+1} is false); S_j is reached
exactly when no earlier star clause S_{j'} (j' > j) failed, that is when x_{j+1}, …, x_n contains no 1 followed
by 0, i.e. is non-decreasing (n − j + 1 patterns), with x_2, …, x_j free. So S_j costs 5(n − j + 1)2^(j−2) in
this half. The identity it uses: with i = j − 2, M = n − 3,
Σ_{i=0..M} (n − 1 − i)2^i = (n − 1)(2^(M+1) − 1) − ((M − 1)2^(M+1) + 2) = 3·2^(n−2) − n − 1,
so the star clauses cost 15·2^(n−2) − 5n − 5. The n masks with x1 true and x_2, …, x_n non-decreasing pass every
S_j; each spends 1 evaluation on F1 (true) and 2 on F2 (it fails unless x2 is true), and only the all-true mask
reaches G (1 evaluation, false): 3n + 1. Total (n − 1)2^(n−1) + 15·2^(n−2) − 5n − 5 + 3n + 1 =
(2n + 13)2^(n−2) − 2n − 4.

**Check.** `experiments/2026-10-06f_entries_horn_sat.py` (n = 3..16). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "Horn brute 6((2n+13)2^(n-2)-2n-4)": n = 3..16 (includes the V2 sizes n = 8, 10, …, 16; n < 3
raises, as stated). `experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "Horn brute: evaluations
in the x1-false half (n-1)2^(n-1), 6 operations each": n = 3..14.

## 2. Unit propagation: 12n − 7 (building 7n − 5, propagation 5n − 2)

**Statement.** For every n ≥ 3, `horn_sat_unit_propagation` on H_n makes exactly 12n − 7 counted operations:
7n − 5 while building (3 per negative literal, 1 per positive literal, 1 for the fact test of F1) and 5n − 2 while
propagating (3 per variable set true, 2 per firing clause with a head).

**Proof.** *Building.* For each literal, `lit > 0` counts 1. For a negative literal, `occurs[-lit]` counts
`__neg__` and `__index__` (2 more); `k += 1` is plain. For a positive literal, `h != 0` is evaluated on the plain
`h = 0` (each clause of H_n has at most one positive literal), so it short-circuits uncounted, and `h = lit`.
After the literals, `k == 0` is plain; only F1 has k = 0, and its `h == 0` compares the `CountingLit` head (1
count) before the head is queued. Costs: each S_j 3 + 3 + 1 = 7, F1 1 + 1 = 2, F2 3 + 1 = 4, G 3; total
7(n − 2) + 9 = 7n − 5.

*Propagation.* `occurs[1]` lists the n − 2 star clauses and F2, `occurs[j]` (2 ≤ j ≤ n − 1) only S_j, and
`occurs[n]` only G; the counters start at 2 for each S_j and at 1 for F2 and G. The queue holds one variable at a
time. Popping a variable v that is not yet true costs `value[v]` (read), `value[v] = True` and `occurs[v]`: three
`__index__` calls; `counter[c] -= 1` and `counter[c] == 0` are plain. A clause that fires with a head h costs
`h == 0` and `value[h]` (2). In order: x1 is popped (3), decrements every S_j to 1 and fires F2 (2), queuing x2;
for j = 2, …, n − 1, x_j is popped (3) and fires S_j (2), queuing x_{j+1}; x_n is popped (3) and fires G, whose
head is the plain 0, so `h == 0` is not counted and the function returns `None`. Total 3n + 2(n − 1) = 5n − 2, and
7n − 5 + 5n − 2 = 12n − 7.

**Check.** `experiments/2026-10-06f_entries_horn_sat.py` (n = 3..300 and the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "Horn unit propagation 12n-7": n = 3..300 and the V2 sizes n = 1000, 2000, 4000, 8000, 16000,
32000 (n < 3 raises, as stated). `experiments/2026-10-07_count_proof_checks.py`, group `sat`, line "Horn unit
propagation: building 7n-5, propagation 5n-2": n = 3..200.

## 3. The oracle's naive forward chaining: n full passes on H_n

**Statement.** For every n ≥ 3, the harness's `_naive_chaining` makes exactly n passes over the clause list of
H_n, that is n(n + 1) clause visits.

**Proof.** Pass 1: no star clause fires (x1 is not yet true), F1 sets x1, F2 then sets x2. By induction, pass t
(2 ≤ t ≤ n − 1) starts with exactly x1, …, x_t true and sets exactly x_{t+1}: a star clause S_j fires iff x_j is
true and x_{j+1} is not, which at the start holds only for j = t; S_{t+1} is visited before S_t (descending order),
so x_{t+1} set by S_t does not make S_{t+1} fire in the same pass; F1 and F2 have true heads, and G has no head.
Pass n starts with all variables true, sets nothing, and ends the `while changed` loop. Each pass visits all n + 1
clauses.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `extra`, line "Horn oracle: naive forward chaining
makes exactly n passes on H_n": n = 3..200.

## Conventions for sections 4 to 10

A formula is (n, clauses); a clause is a tuple of non-zero integers (v for x_v, −v for ¬x_v) and means the
disjunction of its literals, so an empty clause is false. An assignment is identified with the set M ⊆ {1, …, n} of
its true variables, and mask(M) = Σ_{v∈M} 2^(v−1) is the integer whose bit v − 1 is the value of x_v. A clause C is
*Horn* if at most one variable occurs positively in it (the code accepts a repeated positive literal and raises
`ValueError` for two different ones). Its *head* h(C) is that variable (none for a goal clause) and its *body* B(C)
is the set of variables that occur negatively. C is true in M iff B(C) ⊄ M or (h(C) exists and h(C) ∈ M); a
tautology (¬x_v ∨ x_v) has B = {v} and h = v and is true in every M. A *fact* is a clause with a head and an empty
body. m is the number of clauses and L the number of literal occurrences.

Time is counted in the unit-cost word model: an executed line whose operands have O(1) words costs O(1), and building a
list of k entries costs O(k). O and Θ are the usual asymptotic bounds over the inputs: a bound may fail on at most
finitely many inputs, never on an infinite family; where a size parameter can be 0 (L, m), the bounds carry an
explicit + 1, so that no infinite family of inputs violates them (for example, a list of empty clauses has L = 0, yet
brute force scans 2ⁿ masks). Space counts the input (n + m + L numbers, as in `input.size_measure`), the working
storage and the output, in words.

## 4. Horn models are closed under intersection; the least model

**Statement** (`problem_statement`, `algorithms[0].correctness`). If M₁ and M₂ are models of a Horn formula, so is
M₁ ∩ M₂. Hence every satisfiable Horn formula has a least model: the intersection M* of all its models is a model
and is contained in every model.

**Proof.** Let C be a clause. If B(C) ⊄ M₁ ∩ M₂, a negative literal of C is true in M₁ ∩ M₂. Otherwise B(C) ⊆ M₁ and
B(C) ⊆ M₂; since C is true in M₁, it has a head and h(C) ∈ M₁, and likewise h(C) ∈ M₂, so h(C) ∈ M₁ ∩ M₂ and C is
true. A satisfiable formula has finitely many (at least one) models, so applying the closure repeatedly shows that
their intersection M* is a model; it is contained in every model by definition. ∎

**Check.** `tests/test_proofs_horn_sat.py`, `test_closure_least_model_and_correctness`: every pair of models is
closed under intersection and the intersection of all models is a model, on every formula with n = 3 made of at most
two distinct Horn clauses (all 32 clause types: 529 formulas) and on 1500 seeded random Horn formulas (n = 1..6,
with repeated literals, tautologies and empty clauses).

## 5. Brute force: correctness and the least model

**Statement** (`algorithms[0].idea`, `correctness`; `brute_force.py` docstring). On every CNF formula
`horn_sat_brute_force` returns None iff the formula is unsatisfiable, and otherwise the satisfying assignment with the
smallest mask. On a satisfiable Horn formula this is the least model M*.

**Proof.** The test `((mask >> (abs(lit) - 1)) & 1) == (lit > 0)` is true iff the literal is true under the
assignment with that mask. The innermost `for` loop breaks at the first true literal (the clause is true); its
`else` branch runs iff no literal is true (the clause is false, including the empty clause) and breaks the clause
loop, which moves on to the next mask. The clause loop's `else` branch runs iff no clause is false, and then the
function returns (x₁, …, x_n) read off the mask. Masks are tried in the order 0, 1, …, 2ⁿ − 1, so the function returns
the satisfying assignment with the smallest mask, or None after the last mask iff there is none. For a Horn formula
every model M contains M* (section 4), so mask(M) − mask(M*) = Σ_{v∈M∖M*} 2^(v−1) ≥ 0, with equality only for M = M*;
hence the smallest satisfying mask is mask(M*). ∎

**Check.** `test_closure_least_model_and_correctness` (the formulas of section 4): the output equals the assignment
of the smallest model mask, which equals the intersection of all models, and is None exactly for the unsatisfiable
formulas. Also the validator's V1 battery (`entry.json`, `verification.method`).

## 6. Unit propagation: correctness

**Statement** (`algorithms[1].correctness`; `unit_propagation.py` docstring). On every Horn formula
`horn_sat_unit_propagation` terminates and returns None iff the formula is unsatisfiable, and otherwise the least
model.

**Proof.** *Build pass.* For each clause c in order the code records h = the head (0 if none) and k = the number of
negative literal occurrences, appends c to `occurs[v]` once for each occurrence of ¬x_v in c, and stores
`head[c] = h`, `counter[c] = k`. If k = 0 and h = 0 the clause has no literal at all, so it is empty and the formula
is unsatisfiable: returning None is correct. If k = 0 and h ≠ 0 the clause is a fact and h is pushed on the queue.
Otherwise the build pass records every clause, and no variable is true yet.

*(a) Counter invariant.* Throughout the propagation loop, `counter[c]` is the number of negative literal
occurrences in clause c whose variable is not (yet) true. It holds at the start, since nothing is true. A variable v
is set true at most once (a popped variable that is already true is skipped by `continue`), and when it is, the loop
over `occurs[v]` decrements `counter[c]` once for each occurrence of ¬x_v in c.

*(b) Pushes.* Every pushed variable is the head of a clause whose body is entirely true at the moment of the push: a
fact (empty body), or a clause whose counter has just reached 0, by (a). A counter only decreases and reaches 0 at
most once, and a fact's counter never changes (a fact has no negative occurrence), so each clause causes at most one
push; there are at most m pushes, and the loop terminates.

*(c) Soundness: every variable set true lies in every model.* Let v₁, v₂, … be the variables in the order in which
they are set true. v_t was pushed earlier as the head of a clause C whose body was then entirely true, that is
B(C) ⊆ {v₁, …, v_{t−1}}. By induction on t these variables lie in every model M; C is true in M and B(C) ⊆ M, so
h(C) = v_t ∈ M.

*(d) A firing goal clause.* If a counter reaches 0 at a clause with head 0, the clause has no positive literal and,
by (a), its whole body is true, hence contained in every model by (c). The clause is false in every model, so the
formula is unsatisfiable and returning None is correct.

*(e) Normal end.* Suppose the queue empties without a return, and let D be the set of true variables; the output is
the indicator of D. Every clause C is true in D: if B(C) ⊄ D, a negative literal is true. If B(C) ⊆ D, `counter[c]`
is 0 by (a). It reached 0 either in the build pass (then C is a fact and its head was pushed) or at the decrement
caused by its last body variable (then its head is not 0, since otherwise the function would have returned, and the
head was pushed unless it was already true). Every pushed variable is popped before the queue is empty and is then
true. So h(C) ∈ D. Hence D is a model; by (c) it is contained in every model, so the formula is satisfiable and D is
its least model (section 4).

The function terminates (b). It returns None only in the build pass at an empty clause or in case (d), so only for
unsatisfiable formulas; otherwise it ends normally with the least model (e). An unsatisfiable formula has no model, so
for it the function cannot end normally and returns None. ∎

**Check.** `test_closure_least_model_and_correctness` (the formulas of section 4): the output equals the least model,
or None exactly for the unsatisfiable formulas. Also the validator's V1 battery and
`experiments/2026-10-06f_entries_horn_sat.py`, section 4 (1040 seeded instances, n = 0..12).

## 7. Unit propagation: time, space and the uncounted decrements

**Statement** (`algorithms[1].time_complexity`, `space_complexity`; `caveats`; `relationship`). On every input
`horn_sat_unit_propagation` runs in O(n + L + 1) time and uses O(n + L + 1) working storage; on every input without an
empty clause it runs in Θ(n + L) time; the space is Θ(n + m + L) with the input counted. The counter decrements, which
use plain clause indices and are not counted by `CountingLit`, happen at most once per negative literal occurrence, so
at most L times.

**Proof.** Let m′ be the number of clauses the build pass reads (all m, or the clauses up to and including the first
empty one) and L′ ≤ L their number of literals. Every clause read, except possibly the last, is non-empty, so
m′ ≤ L′ + 1.
- *Build pass:* creating `value` and `occurs` costs O(n); each clause read costs O(1) besides its literals, and each
  literal costs O(1) (one test `lit > 0`, then either the head check or one append and `k += 1`). Total
  O(n + m′ + L′).
- *Propagation:* there are at most m′ pushes (section 6 (b)) and as many pops, each O(1) besides the scan of
  `occurs[v]`, which happens only when v is newly set true, so at most once per variable. These scans take
  Σ_v |occurs[v]| = (number of negative occurrences read) ≤ L′ steps in all, each one decrement plus O(1). The output
  costs O(n).

Total O(n + m′ + L′) = O(n + L + 1). Without an empty clause the build pass reads all L literals and creates two
lists of n + 1 entries, so the time is also Ω(n + L); and then n + L ≥ 1 except for the empty formula over no
variables, so O(n + L + 1) = O(n + L). Working storage:
`value` and `occurs` have n + 1 entries, the lists in `occurs` hold the negative occurrences read (≤ L′ entries),
`head` and `counter` have at most m′ entries, and the queue never holds more than the number of pushes, m′. That is
O(n + L + 1); with the input (n + m + L numbers) and the output (n values), the space is Θ(n + m + L). The decrement
`counter[c] -= 1` runs once per entry of a scanned list `occurs[v]`, so at most once per negative occurrence (at
most L times); in the build pass every negative literal costs 3 counted operations (`lit > 0`, `-lit` and the index
of `occurs[-lit]`), so the uncounted decrements are fewer than the counted operations. ∎

On the V2 family the exact count 12n − 7 (section 2) is a special case.

**Check.** `test_unit_propagation_work_and_space`: on 1500 seeded random Horn formulas (n = 1..60; empty clauses
possible in a third of them) the literal test runs exactly L′ times, the decrement at most (number of negative
occurrences read) times, `value[v] = True` at most n times and the pop at most m′ times; the queue never exceeds m′
entries, `occurs` never holds more than the negative occurrences read and `head` never more than m′ entries; and the
number of executed lines lies between L′ and 15m′ + 11L′ + 2n + 14 (constants read off the code: at most 15 executed
lines per clause read, 11 per literal read and 2 per variable).

## 8. Brute force: bounds, the V2 family and the worst case for every L

**Statement** (`algorithms[0].time_complexity`, `space_complexity`; `input`; `caveats`). (a) On every input
`horn_sat_brute_force` makes at most 2ⁿ·L literal evaluations and at most 2ⁿ·(L + 1) clause scans, so it runs in
O(2ⁿ·(L + 1)) time. (b) On H_n (n ≥ 3), m = n + 1, L = 3n − 2, and the time is Θ(2ⁿ·n) = Θ(2ⁿ·m). (c) For every n ≥ 3 and every
L ≥ 3n − 2 there is an unsatisfiable Horn formula with n variables and L literal occurrences on which brute force makes
at least 2ⁿ·L/6 literal evaluations, so the worst case is Θ(2ⁿ·L) for every such L. (d) The space is Θ(n + m + L): the
input, O(1) extra words and the output.

**Proof.** (a) At most 2ⁿ masks are examined. For one mask the clauses are scanned in order until the first false
one; a scanned clause costs at most |C| literal evaluations, and an empty clause is false at once and ends the mask.
So a mask costs at most L literal evaluations and at most (number of non-empty clauses) + 1 ≤ L + 1 clause scans, each
O(1) besides its evaluations; the output costs O(n) ≤ O(2ⁿ).

(b) H_n has the n − 2 star clauses (3 literals each), (x1), (¬x1 ∨ x2) and (¬x_n): m = n + 1 and
L = 3(n − 2) + 4 = 3n − 2. By section 1 brute force makes (2n + 13)2^(n−2) − 2n − 4 literal evaluations, at least
the (n − 1)2^(n−1) of the half with x1 false and at most 2ⁿ·L by (a); both bounds are Θ(2ⁿ·n). Every scanned clause
of H_n costs at least one evaluation, so the clause scans and the other work are within constant factors of the
evaluations, and the time is Θ(2ⁿ·n) = Θ(2ⁿ·m).

(c) Let H_{n,k} be H_n with k ≥ 0 copies of the goal clause (¬x1) inserted between the star clauses and (x1). It is
unsatisfiable (it contains H_n) and has L = 3n − 2 + k, so every L ≥ 3n − 2 occurs. Every mask with x1 false passes
the n − 2 star clauses and the k copies with one evaluation each (¬x1 is true and comes first) and fails at (x1):
n − 1 + k evaluations, for 2^(n−1) masks. For k ≥ 1 this gives at least (n − 1 + k)2^(n−1) ≥ 2ⁿ·L/6 evaluations,
since 3(n − 1 + k) ≥ 3n − 2 + k for k ≥ 1. For k = 0 the exact count of section 1 exceeds 2ⁿ(3n − 2)/6 by
(43/12)2ⁿ − 2n − 4 > 0. (Exactly: the masks with x1 true cost 15·2^(n−2) − 5n − 5 evaluations in the star clauses,
as in section 1, and the n masks that pass all of them fail at the first copy after one evaluation, so for k ≥ 1 the
total is (2n + 2k + 13)2^(n−2) − 4n − 5.)

(d) Besides the input, the function keeps the mask and the loop variables (O(1) words; the mask is one machine word
for the n that brute force can reach, as `input.size_measure` states) and builds the output tuple of n values. ∎

**Check.** `tests/test_proofs_horn_sat.py`: `test_brute_force_bounds` (600 seeded random Horn formulas, n = 1..8,
some with empty clauses; literal evaluations counted exactly with the harness's `CountingLit`, 6 operations each, and
clause scans counted by a clause type that counts its iterations): at most 2ⁿ·L evaluations and 2ⁿ·(L + 1) scans;
`test_worst_case_for_every_L` (n = 3..10, k = 0..30): L = 3n − 2 + k, the exact counts above, and at least 2ⁿ·L/6.
`test_brute_force_space` (200 seeded formulas, n = 1..8): every local variable is an integer or part of the input.
The H_n count itself: section 1.

## 9. Dual-Horn formulas

**Statement** (`notes`). Dual-Horn formulas (at most one negative literal per clause) are handled by the same
algorithm after negating every variable.

**Proof.** Let F be dual-Horn and F′ the formula obtained by replacing every literal l by −l; F′ is Horn. For an
assignment M let M^c = {1, …, n} ∖ M. A literal l is true in M iff −l is true in M^c, so M is a model of F iff M^c is
a model of F′. Hence F is satisfiable iff F′ is, and if unit propagation returns the least model D of F′ (section
6), then D^c is a model of F; as complementation reverses inclusion, D^c is the greatest model of F. ∎

**Check.** `test_dual_horn_by_negation`: 800 seeded random dual-Horn formulas (n = 1..8): unit propagation on the
negated formula returns None iff the dual-Horn formula has no model, and otherwise the complement of its output is
the model with the largest mask, which contains every model.

## 10. The remaining claims

- *Caveat: formulas without facts.* If a formula has neither facts nor empty clauses, every clause contains a negative
  literal, which is true when all variables are false. So mask 0 satisfies every clause, and brute force scans each
  clause once and returns the all-false assignment. (An empty clause is not a fact but makes the formula
  unsatisfiable, so the caveat excludes empty clauses.) Check: `test_no_facts_mask_zero` (500 seeded formulas,
  n = 1..10): the output is all-false and there are exactly m clause scans.
- *Caveats on satisfiable formulas and on H_n.* Brute force stops at the least model (section 5), so it examines the
  masks 0, …, mask(M*) and no others. On H_n the 2^(n−1) masks with x1 false pass the n − 2 star clauses (their
  first literal ¬x1 is true) and fail at (x1) (section 1).
- *Relationship: "Horn-SAT is in P".* Unit propagation decides satisfiability, and returns the least model, in
  O(n + L + 1) time (sections 6 and 7), polynomial in the input size; each clause fires at most once (section 6 (b)).
  Brute force is exponential on H_n (section 8 (b)).
- *The V1 oracle (`harness.py`, `check`).* `_naive_chaining` repeats full passes, setting the head of every clause
  whose body is true, until a pass changes nothing; let D be its result. Every variable of D lies in every model (the
  argument of section 6 (c), by induction over the order of setting), and at the end every clause whose body lies in
  D and which has a head has its head in D. If some goal clause (including an empty clause) has its body in D, it is
  false in every model, so accepting None is sound. Otherwise every goal clause has a body variable outside D, so D
  is a model, hence the least model, and `check` accepts an assignment iff it equals D and satisfies every clause. So
  `check` accepts exactly the correct outputs. Cost: every pass but the last sets at least one more variable, so
  there are at most n + 1 passes, each of O(m + L + 1) steps; the exact number of passes on H_n is section 3.
- *Measured, not proved:* the fit values α of the V2 runs (including α = 0.961 for the bare n·2ⁿ), the V1 agreement
  on the validator's 56 formulas, and the oracle-control tallies (1040 correct outputs accepted, 2816 wrong ones
  rejected) are results of the recorded runs, reproduced by `tools/validate.py --scaling` and
  `experiments/2026-10-06f_entries_horn_sat.py`.
