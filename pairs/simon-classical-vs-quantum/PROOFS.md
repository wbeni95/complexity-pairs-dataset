# Proofs: Simon's problem, classical vs quantum

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
the exact count per round (§1), the correctness and the expected queries of the classical collision search (§2),
the distribution of one quantum round (§3), the classical post-processing (§4), the expected number of rounds (§5)
and the classical lower bound (§6). Each proof is followed by the deterministic checks that re-run its computable
facts and the ranges they cover. A check covers only those ranges; the proofs cover the whole domain. Randomized
statements assume ideal randomness. Checks named "test class X" are in `tests/test_proofs_query.py`.

**Exact arithmetic.** Statements about the quantum algorithm are statements in exact arithmetic. `lib/qsim.py`
computes the same amplitudes up to floating-point rounding (the checks agree to 10⁻¹²). In the simulation the
intended outcome therefore has probability 1 − O(10⁻¹⁵), not exactly 1: the rounded probabilities may sum to
slightly less than 1, and `State.measure_all` returns index N − 1 when its random number exceeds the accumulated
probability mass. (Here a fall-through outcome y = N − 1 lies outside s^⊥ when s has odd parity.)

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_xor_and_measure_output` (one quantum query U_f followed by measuring the output
register) adds 1 to `self.queries`. Each implementation creates one `Oracle(table)` and returns `oracle.queries` as
the second component of its output, and `harness.py`, `reported_cost(output)` returns `output[1]`. The methods of
`State` (`h_all`, `measure_all`) do not use the oracle, and reading `oracle.queries` is not a query.

**Instances.** The harness has no `generate_scaling`, so V2 uses `generate(n, rng)` (n ≥ 1): a hidden s ≠ 0 and a
random relabelling of the cosets {x, x ⊕ s}.

## 1. Simon's algorithm: one query per round

**Statement.** On every input (n ≥ 1) and every run, `simon_quantum` makes exactly one query in each round (one
pass of its `while` loop) and no query outside the rounds, so it reports exactly the number R of rounds (the
docstring of `quantum.py`: "Each round is H^n, one query U_f with the output register measured, then H^n and a
measurement"; `entry.json`: "Each round (Hadamard, one query, Hadamard, measure)"). R is random; every statement
about R, such as its expectation E(n) in `entry.json`, is therefore a statement about the reported count.

**Proof.** Each pass of `while len(rows) < n - 1` creates `State(n)`, applies `state.h_all()` (no query), calls
`oracle.apply_xor_and_measure_output(state, random)` once (1 query), applies `state.h_all()` and
`state.measure_all(random)` (no query), and then reduces y against `rows` with integer operations only. The code
after the loop (the free bit and the back-substitution) uses no query. So the count is R. (For n = 1 the loop
condition `len(rows) < 0` is false at once: R = 0.)

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Simon quantum: queries = rounds":
n = 1..10, 12 seeded instances per n (includes the V2 sizes n = 3, 4, 6, 8, 10; rounds counted as executions of the
line `state = State(n)`).

## 2. Classical collision search: correctness, expected queries, space

**Statement.** For every input (n ≥ 1, hidden s ≠ 0) and every run, `simon_classical` returns s; its number Q of
queries has P(Q > q) = Π_{i=0}^{q−1} (N − 2i)/(N − i), N = 2ⁿ, so Q ≤ N/2 + 1 and

E[Q] = 2^N / C(N, N/2), with √(πN/2) < E[Q] < √(πN/2) e^(1/(3N)),

that is, E[Q] ~ √(π/2)·2^(n/2) = Θ(2^(n/2)). The dictionary `seen` holds Q − 1 values at the return (expected
Θ(2^(n/2)), at most 2^(n−1)); the list `order` holds 2ⁿ indices.

**Proof.** Under the promise f(x) = f(y) with x ≠ y iff y = x ⊕ s, so f is 2-to-1 with the pairs {x, x ⊕ s}, and the
first repeated value, at x after x′ = `seen[f(x)]`, gives x′ ⊕ x = s. The loop is the loop of
`pairs/collision-problem-classical-vs-quantum/implementations/classical.py` with a different return value, so the
law, the exact expectation and the bounds are §4 of `pairs/collision-problem-classical-vs-quantum/PROOFS.md`, which
holds for every fixed 2-to-1 function: Q > q iff the first q points of the uniform order lie in distinct pairs. ∎

**Check.** Test class `SimonProofChecks`, `test_classical_law_by_enumeration`: the unchanged `simon_classical` on
every permutation of the domain (the shuffle replaced by each one), for every s ≠ 0 at n = 1, 2 and for s = 1, 6 at
n = 3: the answer is always s and the distribution of Q is exactly the product law. The formula 2^N/C(N, N/2) and its interval are
checked in `CollisionProofChecks`, `test_classical_expectation_formula` (n = 1..10).

## 3. One round of Simon's algorithm: y is uniform on {y : y·s = 0}

**Statement.** In exact arithmetic, in every round, independently of the earlier rounds, the measured y is uniformly
distributed on s^⊥ = {y ∈ {0,1}ⁿ : y·s ≡ 0 (mod 2)}, a set of 2^(n−1) elements.

**Proof.** The algorithm acts on an n-qubit input register and an n-qubit output register (2n qubits). After H^⊗n on
the input register and one query U_f|x⟩|0⟩ = |x⟩|f(x)⟩ the state is N^(−1/2) Σₓ |x⟩|f(x)⟩. The output register is
never acted on again, so measuring it right after the query does not change the distribution of the final
measurement of the input register (operators on the input register commute with a measurement of the output
register). The outcome is a value v = f(x₀) with probability 2/N, and the input register becomes
(|x₀⟩ + |x₀ ⊕ s⟩)/√2. After H^⊗n, using H^⊗n|x⟩ = N^(−1/2) Σ_y (−1)^(x·y)|y⟩ (the tensor product of
H|b⟩ = (|0⟩ + (−1)^b|1⟩)/√2), the amplitude of y is (2N)^(−1/2)(−1)^(x₀·y)(1 + (−1)^(s·y)): its square is 2/N if
y·s = 0 and 0 otherwise, for every v. Each round starts from a fresh state. ∎

The simulation does exactly this: `Oracle.apply_xor_and_measure_output` samples v with probability
Σ_{x∈f⁻¹(v)} |a_x|² and returns the renormalised input register on f⁻¹(v) (the caveat of the entry), and
`State.h_all` applies H to every qubit.

**Check.** Test class `SimonProofChecks`, `test_round_distribution_in_simulation`: for n = 1..6, every s ≠ 0 and 3
seeded instances per s, the simulated input register after the query and the second `h_all` has probability 2/N on
every y ∈ s^⊥ and 0 elsewhere, to 10⁻¹². Existing: `tests/test_qsim.py`, `test_deferred_measurement_collapse` and
`test_deferred_measurement_statistics`.

## 4. The classical post-processing returns s

**Statement.** For n ≥ 1, if every y fed to the loop lies in s^⊥, the code returns s when the loop ends.

**Proof.** Invariant of `rows` (a dictionary pivot ↦ row): every row lies in s^⊥ (rows are XORs of measured y's);
bit p of `rows[p]` is 1; and no row has a 1 at another pivot. Reducing y: XOR-ing `rows[p]` into y when bit p of y is
1 clears bit p and changes no other pivot bit, so the reduced y has no pivot bit, and it is 0 iff y lies in the span
of the rows (every nonzero XOR of rows has a pivot bit). If the reduced y ≠ 0, its top bit p is not a pivot; XOR-ing y
into every row with bit p set clears bit p there without touching pivot bits, and y becomes `rows[p]`: the invariant
holds, and the rows stay linearly independent. When the loop ends there are n − 1 independent rows in s^⊥, which has
dimension n − 1, so they span s^⊥. Exactly one bit `free` is not a pivot, and each row is `rows[p]` = 2^p, plus
2^free if its bit `free` is 1. The returned s has bit `free` = 1 and bit p equal to bit `free` of `rows[p]`, so
row·s = 2·(bit `free` of the row) ≡ 0 for every row: s ≠ 0 is orthogonal to the span s^⊥, hence s lies in
(s^⊥)^⊥ = {0, s}. For n = 1 the loop does not run, `free` = 0 and the returned value is 1 = s. ∎

**Check.** Test class `SimonProofChecks`, `test_post_processing`: for n = 1..6, every s ≠ 0 and 30 seeded random
sequences of y ∈ s^⊥ per s, the unchanged `simon_quantum` (with the measured y's supplied by a stand-in for `State`
and `Oracle`) returns s, after exactly as many rounds as it takes the sequence to reach rank n − 1.

## 5. The number of rounds: E(n) = Σ_{j=1}^{n−1} 1/(1 − 2^(−j)) < n + 0.6067; post-processing cost

**Statement.** The number R of rounds (= queries, §1) has expectation
E(n) = Σ_{j=1}^{n−1} 1/(1 − 2^(−j)) = n − 1 + Σ_{j=1}^{n−1} 1/(2^j − 1) < n + 0.6067 for every n ≥ 1 (`time_complexity`).
The classical post-processing makes O(n) XORs of n-bit words per round, O(n²) bit operations, so O(n³) expected bit
operations in all.

**Proof.** With r independent rows (0 ≤ r ≤ n − 2), their span is a subspace of s^⊥ with 2^r elements, and by §3
the next y lies in s^⊥ uniformly, independently of the past, so it raises r with probability
1 − 2^r/2^(n−1) = 1 − 2^(r−n+1). The waiting times at the levels r = 0, …, n − 2 are geometric with these
parameters, and E(n) = Σ_r 1/(1 − 2^(r−n+1)) = Σ_{j=1}^{n−1} 1/(1 − 2^(−j)) (j = n − 1 − r), which equals
n − 1 + Σ_j 1/(2^j − 1). The infinite sum: its partial sum to j = 40 is 1.60669515241438… (exact rationals) and the
tail is at most Σ_{j>40} 2^(1−j) = 2^(−39), so Σ_{j≥1} 1/(2^j − 1) < 1.6067, and E(n) < n + 0.6067 (the limit
constant 1.6066951… is the Erdős–Borwein constant). Cost: a round reduces y against at most n − 1 rows and updates at
most n − 1 rows, each an XOR of n-bit integers; the final loop is O(n) more. With E[R] < n + 0.61 the expected total
is O(n³) bit operations. ∎

**Check.** Test class `SimonProofChecks`, `test_expected_rounds`: for n = 1..5 and every s ≠ 0, the probability that
a uniform y ∈ s^⊥ is independent of the rows equals 1 − 2^(r−n+1) for every subspace of s^⊥ (all subspaces
enumerated), E(n) in exact rationals equals the closed form, the bound holds for n = 1..64, and
`test_post_processing` counts at most 2(n − 1) row XORs per round. Existing:
`experiments/2026-10-06_simon_expected_queries.py` (simulated means against E(n), n = 2..8).

## 6. Classical lower bound: Ω(2^(n/2)) queries

**Statement.** Let s be uniform on {0,1}ⁿ ∖ {0} and f(x) = L({x, x ⊕ s}) with L a uniformly random injective
labelling of the 2^(n−1) cosets by values in {0,1}ⁿ (every such f satisfies the promise). Every deterministic
algorithm with at most q queries, with C = q(q − 1)/2 < M = 2ⁿ − 1, outputs s with probability at most
(C + 1)/(M − C). Hence every randomized algorithm that outputs s with probability at least 1/2 on every input makes
q queries with q(q − 1)/2 ≥ (2ⁿ − 3)/3, so q > √((2^(n+1) − 6)/3) for n ≥ 2 (for n = 1 the radicand is negative and
the statement is empty), which is at least 0.73·2^(n/2) for n ≥ 4; one with at most T expected queries and success
at least 2/3 has 6T > √((2^(n+1) − 6)/3) (n ≥ 2). So Ω(2^(n/2)) queries are
necessary, and the collision search (§2) is optimal up to a constant factor. (Credit: Simon 1997.)

**Proof.** Fix a deterministic algorithm; repeated queries can be dropped. Consider a history in which the queried
points x₁, …, x_i received pairwise distinct values v₁, …, v_i, and let D = {x_a ⊕ x_b : a < b}. The queries are
determined by the earlier answers, so the probability of this history given s is 0 if s ∈ D (then two queried points
share a coset and a value), and otherwise it is the probability that i given distinct cosets receive the labels
v₁, …, v_i, which is the same for all such s. Hence, given the history, s is uniform on S = {s ≠ 0 : s ∉ D}, with
|S| ≥ M − i(i − 1)/2. The next query x shows a repeated value iff s = x ⊕ x_a for some a ≤ i, which has probability
at most i/|S|; and if the algorithm stops, its output is s with probability at most 1/|S|. So the probability of
seeing a repeated value within q queries is at most Σ_{i<q} i/(M − C) = C/(M − C), and the probability of a correct
output without one is at most 1/(M − C): the bound. If a randomized algorithm succeeds with probability at least 1/2
on every input, its average over this distribution is at least 1/2, and so is that of some deterministic algorithm
in its support; then either C ≥ M or (C + 1)/(M − C) ≥ 1/2, and in both cases C ≥ (M − 2)/3. For expected
queries, stop before query ⌊6T⌋ + 1 and use Markov's inequality, as in the collision proofs. ∎

**Check.** Test class `SimonProofChecks`, `test_posterior_lemma_by_enumeration` (n = 2: all 36 functions of the
distribution; for every sequence of distinct points and every answer sequence, the conditional distribution of s is
uniform on S, and the conditional probability of a repeated value at the next query is #{a : x ⊕ x_a ∈ S}/|S|) and
`test_lower_bound_by_exhaustion` (n = 2: exhaustive minimax over all adaptive strategies on the 36 functions, equal
to the optimum over pattern strategies for q = 0..3; n = 3, 4: exhaustive optimum over strategies that see the equality pattern of the answers, which by the lemma carries all
the information about s; the optimum is below (C + 1)/(M − C) for every q with C < M). Group `simon` of
`experiments/2026-10-07_query_proof_checks.py`: the posterior lemma for n = 3 on all 11760 functions and all
sequences of up to 3 distinct points.

## 7. The remaining statements

- **Separation.** E[R] < n + 0.61 quantum queries (§5) against Ω(2^(n/2)) classical queries (§6) and Θ(2^(n/2)) for
  the collision search (§2): an exponential separation in the query model, both sides proved here.
- **Space.** Classical: §2. Quantum: 2n qubits (input and output registers, §3); the simulation stores only the n-qubit
  input register, by the deferred measurement of §3.
- **Caveats.** The deferred-measurement statement is proved in §3. "A separation relative to an oracle; it does not
  by itself imply BQP ≠ BPP for explicit problems" limits the scope and asserts nothing further.
