# Proofs: Deutsch–Jozsa, classical vs quantum

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
the exact counts (§1–§3), the correctness and error probabilities of the three algorithms (§4), the average cost of
the deterministic scan on random balanced functions (§5) and the exact classical lower bound (§6). Each proof is
followed by the deterministic checks that re-run its computable facts and the ranges they cover. A check covers only
those ranges; the proofs cover the whole domain. Randomized statements assume ideal randomness. Checks named "test
class X" are in `tests/test_proofs_query.py`.

**Exact arithmetic.** Statements about the quantum algorithm are statements in exact arithmetic. `lib/qsim.py`
computes the same amplitudes up to floating-point rounding (the checks agree to 10⁻¹²). In the simulation the
intended outcome therefore has probability 1 − O(10⁻¹⁵), not exactly 1: the rounded probabilities may sum to
slightly less than 1, and `State.measure_all` returns index N − 1 when its random number exceeds the accumulated
probability mass.

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_phase` (a quantum query) adds 1 to `self.queries` and negates the amplitude of
every x with f(x) odd. Each implementation creates one `Oracle(table)` and returns `oracle.queries` as the second
component of its output, and `harness.py`, `reported_cost(output)` returns `output[1]`. Nothing else changes
`queries`: the methods of `State` (`h`, `h_all`, `measure_all`) do not use the oracle, and reading the attribute
`oracle.queries` is not a query. So the reported cost is the number of calls `oracle(...)` plus the number of calls
`oracle.apply_phase(...)`.

**Scaling instance.** An input is (n, table) with a table of N = 2ⁿ bits. `generate_scaling(n, rng)` draws
c = `rng.randrange(2)` and returns either the constant table (c, …, c) or the table f(x) = c ⊕ (x >> (n − 1)),
where x >> (n − 1) is the top bit of x. For n ≥ 1 these are four functions: the two constants, and the two balanced
functions equal to c on 0..2^(n−1) − 1 and to 1 − c on 2^(n−1)..2ⁿ − 1. (For n = 0, `dj_classical` raises
`ValueError` at `1 << (n - 1)`, so its count is stated for n ≥ 1.)

## 1. Deterministic scan: 2^(n−1) + 1 in the worst case, attained exactly on four functions

**Statement.** For every n ≥ 1 and every promise input, `dj_classical` makes exactly 2^(n−1) + 1 queries if f is
constant, and exactly 1 + G queries if f is balanced, where G is the smallest x ≥ 1 with f(x) ≠ f(0); for balanced f,
G ≤ 2^(n−1). So it makes at most 2^(n−1) + 1 queries on every promise input, exactly 2^(n−1) + 1 precisely on the
four functions of `generate_scaling`, and fewer on every other promise input. In particular every scaling instance
costs exactly 2^(n−1) + 1.

**Proof.** `dj_classical` calls `oracle(0)` once, then calls `oracle(x)` once in each iteration x = 1, 2, …,
2^(n−1) and returns at the first x with `oracle(x) != first`; if no value differs, it returns after the loop. So the
count is 1 + x after a return inside the loop and 1 + 2^(n−1) otherwise. A constant f never differs: 2^(n−1) + 1. For
a balanced f, the values f(0), …, f(2^(n−1)) are 2^(n−1) + 1 values, while only 2^(n−1) points carry the value f(0);
so some x ≤ 2^(n−1) has f(x) ≠ f(0), the loop returns at x = G ≤ 2^(n−1), and the count is 1 + G ≤ 2^(n−1) + 1.
Equality holds iff G = 2^(n−1), that is, iff f = c on 0..2^(n−1) − 1 for c = f(0); then these 2^(n−1) points are all
the points with value c, so f = 1 − c on the upper half, and f(x) = c ⊕ (top bit of x). With the two constants these
are the four functions; every other promise input is balanced with G < 2^(n−1) and costs at most 2^(n−1).

**Check.** `experiments/2026-10-07_deutsch_jozsa_checks.py`: every promise input for n = 1..4 (maximum 2^(n−1) + 1,
attained exactly on the four functions). `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "DJ
deterministic 2^(n-1)+1 (scaling inputs)": n = 1..16 (includes the V2 sizes n = 2, 4, …, 16); line "DJ deterministic
on every scaling input (6 seeds per n)": n = 1..16, six seeded draws per n.
`experiments/2026-10-07_count_proof_checks.py`, group `query`, line "DJ deterministic: 1 + G (balanced), 2^(n-1)+1
(constant); maximum exactly on the four functions": every promise input for n = 1..4; for n = 5..14 the four
functions and 60 seeded promise inputs per n (20 from `generate`, 40 balanced with an equal prefix of random
length); the four functions at n = 15, 16.

## 2. Randomized: exactly K = 20 queries

**Statement.** On every input (n, table) with a table of length 2ⁿ, n ≥ 0, `dj_randomized` makes exactly K = 20
queries.

**Proof.** The set comprehension `{oracle(random.randrange(1 << n)) for _ in range(K)}` calls `oracle(...)` once in
each of its K = 20 iterations, with no early exit; nothing else calls the oracle. (The set may hold fewer than 20
values; its size does not affect the count.)

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "DJ randomized exactly 20":
n = 1..16 (includes the V2 sizes n = 1, 2, 4, 8, 12, 16). `experiments/2026-10-07_count_proof_checks.py`, group
`query`, line "DJ randomized exactly 20 on every input": n = 0..14, 20 seeded inputs per n.

## 3. Quantum: exactly 1 query

**Statement.** On every input (n, table), n ≥ 0, `dj_quantum` makes exactly 1 query.

**Proof.** It calls `oracle.apply_phase(state)` once; `State(n)`, `state.h_all()` and `state.measure_all(random)`
do not use the oracle.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "DJ quantum exactly 1": n = 1..10
(includes the V2 sizes n = 1, 2, 4, 6, 8, 10). `experiments/2026-10-07_count_proof_checks.py`, group `query`, line
"DJ quantum exactly 1 on every input": n = 0..10, 10 seeded inputs per n.

## 4. Correctness and error of the three algorithms

**Statement.** For every n ≥ 1 and every promise input: (a) `dj_classical` is always correct; (b) `dj_randomized` is
always correct on constant functions and errs on a balanced function with probability exactly 2^(1−K) = 2^(−19);
with K = ⌈log₂(1/ε)⌉ + 1 queries the error is at most ε, so O(log(1/ε)) queries suffice for error ε; (c) the quantum
algorithm of `dj_quantum` is always correct (zero error) in exact arithmetic (for the simulation see "Exact
arithmetic" above).

**Proof.** (a) If two values differ, f is not constant, so by the promise it is balanced. If the 2^(n−1) + 1 values
f(0), …, f(2^(n−1)) agree, more than half of the table has one value, so f is not balanced, hence constant.
(b) A constant f gives one answer, so the output is "constant". For a balanced f each query point is uniform and
independent, and exactly half the points carry each value, so the K answers are independent fair bits; they all
agree with probability 2·2^(−K). (c) As in the Bernstein–Vazirani proofs (§3 there), H^⊗n, the phase query and
H^⊗n give the amplitude N^(−1) Σₓ (−1)^f(x) on |0…0⟩, N = 2ⁿ. It is ±1 for constant f, so every other amplitude is 0
and the outcome is 0; it is 0 for balanced f, so the outcome is never 0. The output is "constant" iff the outcome is
0. ∎

**Check.** Test class `DeutschJozsaProofChecks`: `test_quantum_is_exact` (every promise input for n = 1..3 and 20
seeded balanced inputs for n = 4..8: the simulated probability of |0…0⟩ is 1 or 0 to 10⁻¹²);
`test_randomized_error_exact` (the unchanged `dj_randomized` with K set to k = 1..4 and its random choices
enumerated over all k-tuples of points, on every promise input, k = 1..4 for N = 4 and k = 1..3 for N = 8: the
error is 0 on constants and exactly 2^(1−k) on every balanced input). Existing: `experiments/2026-10-07_deutsch_jozsa_checks.py` checks 1–3
(exhaustive correctness of the scan for n = 1..4; quantum exactness; sampled error rates).

## 5. The deterministic scan on a uniformly random balanced function: 3 − 4/(N + 2) expected queries

**Statement.** For a uniformly random balanced f on N = 2ⁿ points (n ≥ 1), `dj_classical` makes
1 + 2N/(N + 2) = 3 − 4/(N + 2) queries in expectation: at most 3, and tending to 3 (`time_complexity`). Equivalently,
the first j values agree with probability 2 Π_{i<j} (N/2 − i)/(N − i) ≤ 2^(1−j), and the expectation is 1 plus the sum
of these probabilities over j ≥ 1.

**Proof.** By §1 the count is 1 + G, G the first x ≥ 1 with f(x) ≠ f(0). Given f(0), the values f(1), …, f(N − 1)
are a uniformly random arrangement of a = N/2 − 1 copies of f(0) and b = N/2 other values. Each copy of f(0)
precedes all b others with probability 1/(b + 1), so E[G] = 1 + a/(b + 1) = N/(N/2 + 1), and
E[1 + G] = 1 + 2N/(N + 2). Equivalently, G ≥ j iff the first j values agree, with probability
2 Π_{i<j}(N/2 − i)/(N − i) (all equal to 0 or all equal to 1), and each factor is at most 1/2; E[1 + G] =
1 + Σ_{j≥1} P(G ≥ j). ∎

**Check.** Test class `DeutschJozsaProofChecks`, `test_average_on_balanced_inputs`: the unchanged `dj_classical` on
every balanced function for n = 1..4 (2, 6, 70, 12870 functions): the mean count equals 3 − 4/(N + 2) in exact
rationals, and the product form equals it for n = 1..12. Existing: `experiments/2026-10-07_deutsch_jozsa_checks.py`
check 4 and `2026-10-07_deutsch_jozsa_followup_n8.py` (sampled means).

## 6. Exact classical lower bound: 2^(n−1) + 1 queries

**Statement.** For n ≥ 1, every deterministic algorithm that is correct on every promise input makes at least
2^(n−1) + 1 queries on each constant input, so 2^(n−1) + 1 in the worst case, and the scan of §1 is optimal. Every
zero-error randomized algorithm makes at least 2^(n−1) + 1 queries, with probability 1, on each constant input
(`lower_bounds`). Bounded-error algorithms are not covered: §4 (b) needs only K queries.

**Proof.** Run the deterministic algorithm on the constant-0 function and suppose it stops after querying a set Q of
at most 2^(n−1) distinct points. Since at least 2^(n−1) points lie outside Q, the function that is 1 on 2^(n−1) of
them and 0 elsewhere is balanced and gives the same answers on Q. The run is the same on both functions, so the
output is the same, but the correct answers differ: a contradiction. The same holds for the constant-1 function.
For a zero-error randomized algorithm, suppose that with positive probability its run on the constant-0 function
stops after at most 2^(n−1) distinct queries. Each such run is also the run, with the same random choices, on a
balanced function as above, and there are finitely many balanced functions, so for one of them the algorithm errs
with positive probability: a contradiction. ∎

**Check.** Test class `DeutschJozsaProofChecks`, `test_exact_lower_bound_by_exhaustion`: an exhaustive minimax over
all deterministic adaptive strategies that are correct on every promise input gives the worst case 2, 3, 5 for
n = 1, 2, 3; and, over all sets Q of points, the smallest Q on which no balanced function agrees with a constant
function has 2^(n−1) + 1 points (n = 1..3), which is the step of the proof.

## 7. The remaining statements

- **Separation.** Exact setting: 2^(n−1) + 1 deterministic queries (§1, §6), also for zero-error randomized
  algorithms on constant inputs (§6), against 1 exact quantum query (§3, §4): exponential, proved here. Bounded
  error: K = O(log(1/ε)) classical queries suffice (§4), so there is no asymptotic separation there. Bernstein–Vazirani
  and Simon's problem give separations that survive bounded error (proved in their entries).
- **Space.** Deterministic: the index x ≤ 2^(n−1) and the first value (O(n) bits). Randomized: the set of answers
  has at most two elements. Quantum: one n-qubit register.
- **Caveats.** "Promise problem, relative to an oracle; it does not imply BQP ≠ BPP" limits the scope; "it does not
  even separate the bounded-error query complexities" is §4 (b) together with the 1-query quantum algorithm.

**Check (space).** Test class `DeutschJozsaProofChecks`, `test_space`: `dj_quantum` creates only n-qubit states
(n = 1..8).
