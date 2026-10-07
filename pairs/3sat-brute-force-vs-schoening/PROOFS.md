# Proofs: 3-SAT, brute force vs Schöning's random walk

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): correctness, the one-sided error bound of Schöning's walk, the
per-try success bound p(n) with explicit constants, the restart budget T(n), the running times and the space
bounds. Each section names the deterministic checks that re-run its computable facts and the ranges they cover. A
check covers only its range; the written proof covers the general statement.

The statements listed under `background` in `entry.json` (NP-completeness of 3-SAT, the k-SAT generalisation,
faster algorithms, 2-SAT) are cited, not proved here. Measured data (timing fits, planted success rates, clause
checks per assignment) are measurements and are not proved here either.

Credit: the random-walk algorithm and the idea of its analysis are Schöning's (1999). The coupling argument,
the explicit constants and the floating-point check below are written out here.

## 0. Conventions

- A formula is (n, clauses) over the variables x_1..x_n. A clause is a tuple of 0 to 3 non-zero integers
  (DIMACS literals); a literal may repeat inside a clause, and a clause may contain a literal and its negation. A
  clause of width w has w literal *positions*, counted with repetition.
- Costs. A *clause check* is one pass of the loop over the literals of a clause, a *literal check* one literal
  evaluation, a *scan* one pass over the clause list. Assignments are n-bit masks (brute force) or a list of n
  Booleans (Schöning), and operations on them are unit cost. In O-bounds m is read as max(m, 1).
- Randomness. The statements about Schöning's walk are about the algorithm with ideal randomness:
  `random.random()` is uniform on [0, 1) (so `random.random() < 0.5` has probability exactly 1/2) and
  `random.choice(c)` is uniform over the positions of c, all draws independent. The implementation uses
  Python's Mersenne Twister. The validator seeds it, so its runs are deterministic and reproducible; the
  probability statements do not apply to one seeded run.

## 1. Brute force

**1.1 Correctness.** The outer loop visits `mask = 0, 1, …, 2^n − 1`, every assignment exactly once (bit v − 1 is
the value of x_v). For a fixed mask the literal loop of a clause breaks at the first true literal; if no literal
is true (this includes the empty clause), its `else` branch breaks the clause loop, so the assignment is
abandoned. The clause loop reaches its own `else` branch, which returns True, exactly when every clause has a true
literal. So the function returns True iff some assignment satisfies every clause, and False after all 2^n
assignments otherwise. For n = 0 the single assignment is the empty one.

**1.2 Time.** At most 2^n assignments, at most m clause checks per assignment, at most 3 literal checks per clause
check: at most 3·2^n·m literal checks, O(2^n m). On an unsatisfiable formula no assignment returns True, so all
2^n assignments are examined, and each takes at least one clause check (it ends at a falsified clause): between
2^n and 2^n·m clause checks, Θ(2^n) assignments.

**1.3 Space.** The loop keeps one n-bit mask and loop indices besides the input: O(n + m) words in total.

**Checks.** `tests/test_proofs_3sat.py`, class `BruteForce`: on the seeded unsatisfiable family of `generate_scaling`,
n = 3..10, the clause list is iterated exactly 2^n times (once per assignment) and the number of clause checks lies
in [2^n, 2^n·m] (n = 3..9). Class `WorkingMemory`: the tracemalloc peak above the input stays below
4096 + 64n bytes for n = 4..12. The V1 battery (validator, n = 0..12) compares the answers with an independent
DPLL oracle.

## 2. Schöning's walk: correctness with one-sided error

**2.1 The algorithm as implemented.** If some clause is empty, return False. Otherwise repeat T(n) independent
tries: draw a uniformly random assignment; then for step = 0, 1, …, 3n: scan the clauses in input order for the
first clause falsified by the current assignment; if there is none, return True; if step < 3n, flip the variable
of a uniformly chosen literal position of that clause. After all tries return False. One try therefore checks the
assignment before each of its 3n flips and once after the last flip.

**2.2 One-sided error.** True is returned only after a scan found no falsified clause, i.e. when the current
assignment satisfies the formula. A formula with an empty clause is unsatisfiable and is answered False. Hence an
unsatisfiable formula is always answered False, and a True answer is always correct.

**2.3 Lemma (one flip).** Let a* satisfy the formula, let a be the current assignment, and let C be the first
clause falsified by a. Every literal of C is false under a, and at least one literal of C is true under a*.
Call a position of C *good* if its literal is true under a*. The variable of a good position has different values
under a and a*, so flipping it lowers the Hamming distance d(a, a*) by exactly 1. Every flip changes the distance
by exactly 1 in one direction or the other. C has at most 3 positions and at least one good one, so a good position
is chosen with probability at least 1/3.

**2.4 Lemma (coupling).** Let the formula be satisfiable, fix a satisfying assignment a*, and let one try start
from an assignment a with d(a, a*) = j. Then the try succeeds with probability at least

  q_j = C(3j, j) (1/3)^(2j) (2/3)^j.

*Proof.* Let U_1, U_2, … be independent uniform random numbers in [0, 1), independent of the start. Run the try
with the following rule for flip t: list the positions of the chosen clause C_t with the good positions first
(in any fixed way), and choose position number ⌊U_t·|C_t|⌋ (counted from 0). Given everything before flip t, this
position is uniform over the |C_t| positions, so the coupled try has the same distribution of trajectories as the
algorithm (the probability of every finite trajectory is the same product of conditional probabilities), and in
particular the same success probability.

Let B_t = 1 if U_t < 1/3 and B_t = 0 otherwise; the B_t are independent with P(B_t = 1) = 1/3. If B_t = 1 then
U_t·|C_t| < |C_t|/3 ≤ 1, so position 0 is chosen, which is good (Lemma 2.3: C_t has a good position, and good
positions come first): the distance drops by 1. If B_t = 0 the distance changes by +1 or −1, so it grows by at
most 1. Hence, as long as the try has not stopped, the distance d_t after t flips satisfies

  d_t ≤ j + Σ_{s ≤ t} (1 − 2B_s).

Let E_j be the event that exactly j of B_1, …, B_{3j} are 0 (and 2j are 1). It depends on the U's only, so
P(E_j) = C(3j, j)(2/3)^j(1/3)^(2j) = q_j. On E_j, if the try is still running after 3j flips (3j ≤ 3n since j ≤ n),
then d_{3j} ≤ j + j − 2j = 0, so the assignment is a* and the check at step 3j finds it satisfying. If the try
stopped earlier it stopped with True. For j = 0 the start is a* and the check at step 0 succeeds; q_0 = 1. So the
try succeeds on E_j, and its success probability is at least q_j. ∎

**2.5 Theorem (one try).** For a satisfiable formula, one try succeeds with probability at least

  p(n) = Σ_{j=0..n} C(n, j) 2^(−n) q_j.

*Proof.* The start is uniform on {0, 1}^n, so d(a, a*) has the Binomial(n, 1/2) distribution,
P(d = j) = C(n, j) 2^(−n). Average Lemma 2.4 over the start. ∎

**2.6 Theorem (error bound).** The tries are independent and each succeeds with probability at least p(n), so a
satisfiable formula is answered False with probability at most (1 − p(n))^T ≤ exp(−p(n)·T), using 1 − x ≤ e^(−x).
This is at most 10^(−6) whenever p(n)·T ≥ ln(10^6). For T(n) = ⌈ln(10^6)/p(n)⌉ this holds by definition.

The implementation computes T(n) in double precision (`tries_needed`). For n = 0..373 the computed value was
compared with the exact rational p(n): p(n)·T(n) ≥ ln(10^6) holds for every one of these n, and the computed T(n)
is at least ⌈ln(10^6)/p(n)⌉: equal to it for n ≤ 88, and larger by a relative 10^(−12) at most for n = 89..373.

*Overflow for every n ≥ 374.* `success_lower_bound(n)` sums the terms j = 0, 1, …, n in this order, and term j
evaluates `comb(n, j) / 2**n` (a quotient of integers, a float in [0, 1]), multiplies it by the integer
C(3j, j), which converts that integer to a float, and then by two float powers. Converting an integer to a float
raises `OverflowError` exactly when the integer is too large for a double. The two powers have the bases 1/3 and
2/3, below 1, so they can only underflow, and an underflow to 0 does not raise (a float power with a base above 1 can
raise on overflow, but none occurs here); float products overflow to infinity without raising. C(3j, j) is increasing in j (the ratio
C(3j + 3, j + 1)/C(3j, j) = (3j + 3)(3j + 2)(3j + 1)/((j + 1)(2j + 2)(2j + 1)) exceeds 1), C(1119, 373) is still
convertible and C(1122, 374) (1026 bits) is not. So for n ≤ 373 no term raises, and for every n ≥ 374 the term
j = 374 is reached and raises. `sat_schoening` returns False for a formula with an empty clause before it computes
T(n), and raises `OverflowError` for every other formula with n ≥ 374 (T(374) is about 1.7·10^49 tries, far beyond
any feasible run). So the bound 10^(−6) holds for the implementation on every input on which it answers.

**2.7 The V1 battery.** The validator's V1 battery (seeds `"<id>|v1|<n>|<trial>"`, n in `v1_sizes`, 6 trials)
contains 53 satisfiable and 31 unsatisfiable formulas, as computed with the harness's DPLL oracle. With fresh
randomness, the probability that Schöning's walk misses at least one of the 53 satisfiable ones is at most
53·10^(−6) by the union bound and 2.6.

**Checks.** `tests/test_proofs_3sat.py`:
- class `Coupling`: on 140 seeded satisfiable formulas with n = 1..7 (harness instances, planted formulas, and
  formulas with 1-, 2- and 3-literal clauses and repeated literals), the exact success probability of one try,
  computed in rational arithmetic from every start with the implementation's rules, is at least
  max over all solutions a* of q_{d(a, a*)}, and its average is at least p(n); the probability of a good position
  is at least 1/3 for every start, clause and solution of the first 60 formulas (Lemma 2.3);
- class `SchoeningCounts`: True only for satisfiable formulas and False for all unsatisfiable ones (n = 0..8,
  8 seeded formulas each);
- class `RestartBudget`: the floating-point statements of 2.6 for n = 0..373 against the exact ceiling (exact
  rational p(n); ln(10^6) enclosed to within 10^(−70)), equality for n ≤ 88; the conversion threshold of C(3j, j)
  (j = 373 convertible, 374 not); `OverflowError` for n = 374, 375, 400, 1000, and the answer False for a formula
  with an empty clause at n = 400;
- class `ComputedValues`, `test_v1_battery_composition`: the counts 53 and 31 of 2.7.

## 3. p(n) and T(n): explicit bounds

**3.1 Lemma.** Let g_j = q_j·2^j·√(j + 1). Then 0.431 ≤ g_j ≤ 1 for every j ≥ 0.

*Proof.* g_0 = 1. For j ≥ 1 use Stirling's formula with Robbins's bounds: j! = √(2πj)(j/e)^j e^(r_j) with
1/(12j + 1) < r_j < 1/(12j). Then

  C(3j, j) = (3j)!/(j!(2j)!) = √(3/(4πj)) (27/4)^j e^r,   r = r_{3j} − r_j − r_{2j},

because √(6πj)/(√(2πj)·√(4πj)) = √(3/(4πj)) and (3j)^(3j)/(j^j (2j)^(2j)) = (27/4)^j. Since all r_i > 0,
−1/(12j) − 1/(24j) < r < 1/(36j), i.e. −1/8 < r < 1/36. With q_j = C(3j, j)·2^j/27^j:

  q_j = √(3/(4πj)) 2^(−j) e^r,   g_j = √(3/(4π)) √((j + 1)/j) e^r.

As 1 < √((j + 1)/j) ≤ √2 and √(3/(4π)) = 0.48860…: 0.4886·e^(−1/8) = 0.4312 ≤ g_j ≤ 0.4886·√2·e^(1/36) = 0.7104. ∎

**3.2 Identity.** C(n, j) 2^(−n) 2^(−j) = (3/4)^n · C(n, j)(1/3)^j(2/3)^(n−j), since
(3/4)^n (1/3)^j (2/3)^(n−j) = 2^(n−j)/4^n. Writing q_j = g_j 2^(−j) (j + 1)^(−1/2) and letting J have the
Binomial(n, 1/3) distribution,

  p(n) = (3/4)^n · E[g_J (J + 1)^(−1/2)].

**3.3 Lemma.** (n/3 + 1)^(−1/2) ≤ E[(J + 1)^(−1/2)] ≤ √(3/(n + 1)).

*Proof.* Lower bound: t ↦ (t + 1)^(−1/2) is convex, so Jensen's inequality gives E[(J + 1)^(−1/2)] ≥
(E[J] + 1)^(−1/2) = (n/3 + 1)^(−1/2). Upper bound: since C(n, j)/(j + 1) = C(n + 1, j + 1)/(n + 1),

  E[1/(J + 1)] = Σ_j C(n + 1, j + 1)(1/3)^(j+1)(2/3)^(n−j) · 3/(n + 1) = 3(1 − (2/3)^(n+1))/(n + 1) ≤ 3/(n + 1),

and E[(J + 1)^(−1/2)] ≤ √(E[1/(J + 1)]) by Jensen's inequality for the concave square root. ∎

**3.4 Theorem.** For every n ≥ 0,

  0.431 · (3/4)^n · √(3/(n + 3)) ≤ p(n) ≤ (3/4)^n · √(3/(n + 1)).

Hence p(n) = Θ((3/4)^n/√n), and T(n) = ⌈ln(10^6)/p(n)⌉, which lies between ln(10^6)/p(n) and ln(10^6)/p(n) + 1,
is Θ((4/3)^n √n). *Proof.* Combine 3.1, 3.2 and 3.3 ((n/3 + 1)^(−1/2) = √(3/(n + 3))). ∎

**3.5 Computed values.** p(n)·√n/(3/4)^n = 0.8877, 0.8835, 0.8801, 0.8772, 0.8748, 0.8727, 0.8709 for
n = 14..20, i.e. between 0.87 and 0.89. The implementation's T(n) is 196, 1682 and 22371 for n = 6, 12, 20.

**Checks.** `tests/test_proofs_3sat.py`, class `Asymptotics`: 0.431 ≤ g_j ≤ 1 for j = 0..600 and the bounds of
3.4 for n = 0..300, both exactly in rational arithmetic (through squares); the identity for E[1/(J + 1)] for
n = 0..60. Class `ComputedValues`: the values of 3.5. `experiments/2026-10-07_schoening_restart_budget.py`
prints the ratio and T(n) for n = 3, 4, 6, 8, 10, 12, 14, 16, 20 from exact rationals.

## 4. Schöning's walk: running time and space

**4.1 Time on every input.** Before the tries: one scan for an empty clause (O(m)) and the computation of T(n)
(n + 1 terms, polynomial in n). Each try: n random draws for the start, at most 3n + 1 scans of at most m clause
checks (at most 3m literal checks) each, and at most 3n flips. Total O(T(n)·(n + (3n + 1)·m)) + poly(n) =
O(T(n)·n·m) = O((4/3)^n n^1.5 m) by 3.4.

**4.2 Unsatisfiable formulas without an empty clause.** No scan finds a satisfying assignment, so every try runs to
the end: exactly T(n)(3n + 1) scans, 3n·T(n) flips and n·T(n) start draws. (A formula with an empty clause is
answered False after one pass over the clause list, with no try.) Each scan stops at the first falsified clause, which
exists, so it makes between 1 and m clause checks.

**4.3 Space.** The current assignment (a list of n + 1 entries) and loop variables besides the input: O(n + m).

**Checks.** `tests/test_proofs_3sat.py`, class `SchoeningCounts`, `test_unsatisfiable_scans_flips_draws`: on the
seeded unsatisfiable family, n = 3..8, the answer is False after exactly 1 + T(n)(3n + 1) passes over the clause
list (the 1 is the empty-clause test), 3n·T(n) calls of `random.choice` and n·T(n) calls of `random.random`.
Class `WorkingMemory`: the tracemalloc peak above the input stays below 4096 + 64n bytes for n = 4..8.

## 5. The V1 oracle (`harness.py`)

`_dpll(clauses, assignment)` decides whether the formula has a satisfying assignment extending `assignment`.
*Unit propagation:* a clause with a true literal is dropped (satisfied); a clause whose literals are all assigned
and false makes the answer False; otherwise only its unassigned literals are kept. If a kept clause has exactly one
unassigned literal l, every satisfying extension makes l true, so assigning l keeps the set of satisfying
extensions unchanged. (A clause whose remaining literals repeat one literal is simply not treated as a unit, which
is harmless.) *End:* if no clause is left, the current assignment satisfies every clause: True. *Branching:*
otherwise some variable v occurs unassigned in a remaining clause, and the satisfying extensions split by the value
of v. Every step assigns a new variable, so the recursion has depth at most n and terminates. Hence `check` compares
the output with the true answer, independently of both implementations.

*Instance sizes.* For n ≥ 3, `generate` makes round(c·n) clauses with c ∈ {2, 4.26, 6}, round(5n), round(3n) + 8,
round(3n) or round(4.26n) clauses, and `generate_scaling` round(5n) + 8; for n = 1, 2 at most 4n clauses, for n = 0 at
most one. So m ≤ 6n + 8 always, and 2n ≤ m ≤ 6n + 8 for n ≥ 3 (round(2n) = 2n): m = Θ(n), as `input.size_measure`
states. The family of `generate_scaling` is
unsatisfiable by construction: the 8 clauses on (x_1, x_2, x_3) contain every sign pattern, so every assignment
falsifies the one whose literals are all false under it.

**Check.** `tests/test_proofs_3sat.py`, class `Oracle`: `_dpll` equals an exhaustive check over all assignments on
seeded formulas with n = 0..10 (including repeated and complementary literals), every scaling formula with
n = 3..10 is unsatisfiable, and 2n ≤ m ≤ 6n + 8 (n ≥ 3), m ≤ 6n + 8 (n < 3) on 1025 seeded `generate` instances
(n = 0..40) and the 38 `generate_scaling` instances with n = 3..40.
