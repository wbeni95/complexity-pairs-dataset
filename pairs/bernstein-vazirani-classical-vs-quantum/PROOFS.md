# Proofs: Bernstein–Vazirani, classical vs quantum

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
the exact counts (§1, §2), the correctness of both algorithms (§3) and the classical lower bound (§4). Each proof is
followed by the deterministic checks that re-run its computable facts and the ranges they cover. A check covers only
those ranges; the proofs cover the whole domain. Checks named "test class X" are in `tests/test_proofs_query.py`.

**Exact arithmetic.** Statements about the quantum algorithm are statements in exact arithmetic. `lib/qsim.py`
computes the same amplitudes up to floating-point rounding (the checks agree to 10⁻¹²). In the simulation the
intended outcome therefore has probability 1 − O(10⁻¹⁵), not exactly 1: the rounded probabilities may sum to
slightly less than 1, and `State.measure_all` returns index N − 1 when its random number exceeds the accumulated
probability mass.

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_phase` (a quantum query) adds 1 to `self.queries` and negates the amplitude of
every x with f(x) odd. Each implementation creates one `Oracle(table)` and returns `oracle.queries` as the second
component of its output, and `harness.py`, `reported_cost(output)` returns `output[1]`. The methods of `State` do
not use the oracle, and reading `oracle.queries` is not a query.

**Instances.** The harness has no `generate_scaling`, so V2 uses `generate(n, rng)`: s = `rng.getrandbits(n)`
(s = 0 for n = 0) and table[x] = s·x mod 2, the parity of `s & x`, for x = 0..2ⁿ − 1.

## 1. Classical: exactly n queries

**Statement.** On every input (n, table) with a table of length 2ⁿ, n ≥ 0 (in particular for every hidden s),
`bv_classical` makes exactly n queries.

**Proof.** The loop runs for i = 0..n − 1 and calls `oracle(1 << i)` once per iteration (1 << i < 2ⁿ, a valid
index); nothing else calls the oracle. For n = 0 the loop is empty and the count is 0.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "BV classical n": n = 0..16
(includes the V2 sizes n = 2, 4, 8, 12, 16). `experiments/2026-10-07_count_proof_checks.py`, group `query`, line
"BV classical exactly n on every s": every s for n = 0..8, 10 seeded s per n for n = 9..16.

## 2. Quantum: exactly 1 query

**Statement.** On every input (n, table), n ≥ 0, `bv_quantum` makes exactly 1 query.

**Proof.** It calls `oracle.apply_phase(state)` once; `State(n)`, `state.h_all()` and `state.measure_all(random)`
do not use the oracle.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "BV quantum 1": n = 1..10 (includes
the V2 sizes n = 1, 2, 4, 6, 8, 10). `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "BV quantum
exactly 1 on every s": every s for n = 0..8, 5 seeded s per n for n = 9, 10.

## 3. Correctness of both algorithms

**Statement.** For every n ≥ 0 and every hidden s, `bv_classical` returns s, and the quantum algorithm of
`bv_quantum` returns s with probability 1 in exact arithmetic (for the simulation see "Exact arithmetic" above).

**Proof.** Classical: f(e_i) = s·e_i = s_i, and the loop sets bit i of the result to f(e_i) = `oracle(1 << i)`.
Quantum: H|b⟩ = (|0⟩ + (−1)^b|1⟩)/√2 on each qubit gives H^⊗n|x⟩ = N^(−1/2) Σ_y (−1)^(x·y)|y⟩, N = 2ⁿ (`State.h(k)`
is H on qubit k, and `h_all` applies it to every qubit). So H^⊗n|0⟩ = N^(−1/2) Σₓ |x⟩, the phase query
(`Oracle.apply_phase`, which negates the amplitudes with f(x) = 1) gives N^(−1/2) Σₓ (−1)^(s·x)|x⟩, and the second
H^⊗n gives N^(−1) Σ_y Σₓ (−1)^((s⊕y)·x)|y⟩ = |s⟩, because Σₓ (−1)^(z·x) = N if z = 0 and 0 otherwise (for z ≠ 0, pair
x with x ⊕ e_i for a bit i of z). Measuring |s⟩ gives s with probability 1. ∎

**Check.** Test class `BernsteinVaziraniProofChecks`, `test_quantum_state_is_exactly_s`: for n = 0..8 and every s,
the simulated state before the measurement, built with the `lib.qsim` calls of `bv_quantum`, has |amplitude of s|² = 1
to 10⁻¹². Existing: `tests/test_qsim.py`, `test_bernstein_vazirani_is_exact` (n = 1..6); V1 (answers checked
against the full truth table).

## 4. Classical lower bound: n queries for every success probability above 1/2

**Statement.** Every classical algorithm (deterministic or randomized) that makes at most q queries on every input
outputs s, for a uniformly random s, with probability at most 2^(q−n); so on some s its success probability is at
most 2^(q−n). Hence success probability above 1/2 on every s needs q ≥ n, and the classical algorithm, with
exactly n queries (§1), is optimal (`lower_bounds`, `time_complexity`, the docstring of `classical.py`).

**Proof.** Fix a deterministic algorithm with at most q queries and let s be uniform on {0,1}ⁿ. Each query x_t is
determined by the earlier answers, so the probability of a transcript (x₁, a₁), …, (x_r, a_r), r ≤ q, given s is 1
if s·x_t = a_t for all t and 0 otherwise. Hence, given the transcript, s is uniform on the solution set of r linear
equations over GF(2), which is empty or an affine subspace of dimension at least n − r ≥ n − q; the output equals s
with probability at most 2^(q−n). Averaging over the transcripts gives the bound for the deterministic algorithm; a
randomized algorithm is a probability distribution over deterministic ones, so its success probability averaged
over s is at most 2^(q−n), hence at most 2^(q−n) for some s. If it exceeds 1/2 for every s, then 2^(q−n) > 1/2, so
q > n − 1. (Credit: the problem is from Bernstein & Vazirani 1997.) ∎

**Check.** Test class `BernsteinVaziraniProofChecks`, `test_classical_lower_bound_by_exhaustion`: for n = 1, 2, 3, an
exhaustive maximum over all deterministic adaptive query strategies with q queries (q = 0..n) answers exactly 2^q of
the 2ⁿ inputs correctly.

## 5. The remaining statements

- **Separation.** n classical queries (optimal by §4, also with randomness and success above 1/2) against 1 quantum
  query (§2, §3): a linear gap in the query model, proved here. That Simon's problem gives an exponential one is
  proved in `pairs/simon-classical-vs-quantum/PROOFS.md`; the superpolynomial separation of a recursive version of the
  problem is background (the entry's `background`).
- **Space.** Classical: the loop index and the n-bit result. Quantum: one n-qubit register (`State(n)`).
- **Caveats.** "A separation relative to an oracle; it does not prove ... and it does not imply BQP ≠ BPP" limits
  the scope and asserts nothing further.

**Check (space).** Test class `BernsteinVaziraniProofChecks`, `test_space`: `bv_quantum` creates only n-qubit states
(n = 0..8), and the result of `bv_classical` stays below 2ⁿ (n = 0..12).
