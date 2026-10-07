# Proofs: minimum finding, classical vs quantum (Dürr–Høyer)

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
the exact counts (§1, §2), the classical lower bounds and the quantum lower bound (§3), the analysis of the BBHT
exponential search that Dürr–Høyer uses (§4), and Dürr–Høyer's expected time, success probability and expected
query count, with the constants of the implementation (§5). Each proof is followed by the deterministic checks that
re-run its computable facts and the ranges they cover. A check covers only those ranges; the proofs cover the whole
domain. Randomized statements assume ideal randomness. It uses Lemma G, Corollary G2, §5 and Theorem Q of
`pairs/grover-search-classical-vs-quantum/PROOFS.md`; §4 is also used by
`pairs/collision-problem-classical-vs-quantum/PROOFS.md`.

Checks named "test class X" are in `tests/test_proofs_query.py`; "group G" refers to
`experiments/2026-10-07_query_proof_checks.py`.

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_phase_where` adds 2 to `self.queries` (one application of a phase flip that depends
on the value f(x): compute and uncompute) and negates the amplitude of every x with `predicate(x, f(x))` true. Each
implementation creates one `Oracle(table)` and returns `oracle.queries` as the second component of its output, and
`harness.py`, `reported_cost(output)` returns `output[1]`. Nothing else changes `queries`: the methods of `State`
(`uniform`, `measure_all`, `reflect_about_uniform`) and the code of `lib/qsearch.py` itself do not use the oracle,
and reading `oracle.queries` is not a query.

**Instances.** The harness has no `generate_scaling`, so V2 uses `generate(n, rng)`: a uniformly random
permutation of 0..N − 1, N = 2ⁿ.

## 1. Classical scan: exactly N queries and N − 1 comparisons

**Statement.** On every input (n, table) with a table of length N = 2ⁿ, n ≥ 0, `minimum_scan` makes exactly N
queries and evaluates the comparison `v < best_value` exactly N − 1 times (the comparisons are not queries and are
not counted by the oracle).

**Proof.** `minimum_scan` calls `oracle(0)` once; then, for each x = 1..N − 1, it calls `oracle(x)` once and
evaluates `v < best_value` once, with no early exit. Total N queries and N − 1 comparisons (for n = 0: 1 query and
none).

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "min finding classical N=2^n":
n = 0..16 (includes the V2 sizes n = 2, 4, …, 16). `experiments/2026-10-07_count_proof_checks.py`, group `query`,
line "minimum scan: N queries, N-1 comparisons": n = 0..12, 5 seeded permutations per n (comparisons counted as
executions of that line).

## 2. Dürr–Høyer: queries = 2 per Grover iteration + 1 per observed candidate + 1

**Statement.** On every input (n ≥ 1) and every run, the count reported by `minimum_durr_hoyer` (that is,
`durr_hoyer_run(instance, random)` with the paper's time-out) is exactly 2I + M + 1, where I is the number of Grover
iterations performed (calls of `qsearch.grover_iteration`) and M is the number of observed candidates (the value
`measurements` returned by `durr_hoyer_run`). I and M are random; the identity holds on every run.

**Proof.** The oracle is used in exactly four places:
- step 1: `ty = oracle(y)`, once (1 query);
- `phase(state)` calls `oracle.apply_phase_where(...)` (2 queries). In `lib/qsearch.py`, `exponential_search`
  calls `phase` only through `grover_iteration(state, phase)`, which calls it once, and every call of
  `grover_iteration` is one Grover iteration (it is followed by `iterations += 1`): 2 queries per iteration;
- `check(x)` executes `measurements += 1` and `oracle(x)`; `exponential_search` calls `check` once after each of its
  measurements: 1 query per observed candidate;
- the time-out branch of stage 2(a) executes `measurements += 1` and `tx = oracle(x)`: again 1 query per observed
  candidate. Its measurement `State.uniform(n).measure_all(rng)` is not a query.

So `oracle.queries` = 1 + 2I + M whenever the run returns.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Durr-Hoyer: queries = 2 x
iterations + candidates + 1": n = 1..8 (12 seeded runs per n) and n = 10, 12 (3 per n), with the paper's time-out
(102 runs; Grover iterations counted by a pass-through wrapper of `qsearch.grover_iteration`).

## 3. Correctness of the scan and the lower bounds (classical and quantum)

**Statement.** (a) `minimum_scan` returns the index of the minimum. (b) For N ≥ 2 and integer values (any ordered
set with no least and no greatest element), every always-correct deterministic algorithm reads all N entries on
every input, and a zero-error randomized algorithm reads all of them with probability 1; so the scan's N probes are optimal for exact algorithms. On tables known to be
permutations of 0..N − 1 (as the harness draws them), N − 1 probes suffice. (c) Every classical algorithm that
outputs the index of the minimum with probability at least p on every table of distinct integers, with at most q
probes, has q ≥ pN − 1; an always-correct one makes at least (N − 1)/2 expected probes on some input; one with at
most T expected probes and success at least 2/3 has T ≥ (N − 2)/12. (d) Every quantum algorithm with success at
least p on every input makes at least (pN − 1)/(4√N) queries; Ω(√N) for bounded error.

**Proof.** (a) The loop keeps `best_value` equal to the minimum of the entries read so far and `best` its index;
it reads every entry. (b) Suppose an always-correct algorithm stops on input T without reading entry z. Its answers
are consistent with the table T₁ that agrees with T on the read entries, gives z a value below all of them and the
other unread entries distinct values above all of them, and with the table T₂ that gives the unread entries distinct
values above all read values, the largest to z. The minimum of T₁ is at z, and that of T₂ is not (N ≥ 2). Both
tables produce the same run, so the output is wrong on one of them: a contradiction. For a zero-error randomized
algorithm, every run that stops early on T is, by the same construction with its random choices fixed, a wrong run
on one of the countably many integer tables, and each of these has probability 0, so the early-stopping runs have
probability 0. On a permutation of 0..N − 1 the value of the last unread entry is
determined by the N − 1 values read. (c) Reduction from unstructured search: given a search instance with one marked
x\*, answer a probe of position x with 0 if x is marked and with x + 1 otherwise (one query of the search oracle per
probe). These are distinct integers whose minimum is at x\*, so any minimum-finding algorithm becomes a search
algorithm with the same number of queries and the same success probability, and §5 (i)–(iii) of the Grover proofs
give the three bounds. (d) Theorem Q of the Grover proofs with F_x the table T_x (T_x[x] = 0, T_x[y] = y + 1 for
y ≠ x) and F_ref the table y ↦ y + 1: F_x differs from F_ref only at x, and the minimum of T_x is at x. For an
algorithm with at most T expected queries and success probability p on every input (as Dürr–Høyer, §5: p > 0.525),
stop it before query ⌊cT⌋ + 1 (c > 1/p): by Markov's inequality it is stopped with probability at most 1/c, so the
truncated algorithm has success at least p − 1/c with at most cT queries, and cT ≥ ((p − 1/c)N − 1)/(4√N). For
example c = 6 and p = 0.525 give T ≥ (0.358N − 1)/(24√N) = Ω(√N), so Dürr–Høyer is optimal up to a constant factor. ∎

**Check.** Test class `MinimumFindingProofChecks`, `test_exact_lower_bound_by_exhaustion`: exhaustive minimax over
all deterministic adaptive strategies, N = 2, 3, 4: with distinct values from a set of N + 1 integers the worst case
of the best strategy is N probes; on the permutations of 0..N − 1 it is N − 1. The search bounds are checked in
`GroverProofChecks` (`test_classical_lower_bound_by_exhaustion`, `test_hybrid_inequality`).

## 4. The BBHT exponential search (`lib/qsearch.exponential_search`, no budget)

**Setting.** N = 2ⁿ ≥ 2, t marked elements with 1 ≤ t ≤ N − 1, θ ∈ (0, π/2) with sin²θ = t/N, and
m₀ = 1/sin 2θ = N/(2√(t(N − t))). The schedule `bbht_schedule` gives m_s = min(λ^s, √N), λ = 6/5 (s = 0, 1, …), and
round s draws j uniformly from {0, …, M_s − 1}, M_s = ⌈m_s⌉, applies j Grover iterations to the uniform
superposition, measures, and checks the outcome (the `check` callable of the caller decides the marking predicate,
which is the predicate the phase flip uses). Rounds use fresh states and fresh randomness. By Lemma G, round s
succeeds with probability P_s = (1/M_s) Σ_{j<M_s} sin²((2j + 1)θ).

**Lemma B (credit: BBHT 1998, Lemma 2).** P_s = 1/2 − sin(4M_sθ)/(4M_s sin 2θ). Hence P_s ≥ 1/2 − m₀/(4M_s), and
P_s ≥ 1/4 whenever M_s ≥ m₀.

**Proof.** sin²x = (1 − cos 2x)/2, and for α = 2θ ∈ (0, π), Σ_{j=0}^{M−1} cos((2j + 1)α) = sin(2Mα)/(2 sin α),
because 2 sin α cos((2j + 1)α) = sin((2j + 2)α) − sin(2jα) telescopes. ∎

**Theorem E.** Let I(t) be the expected total number of Grover iterations and R the number of rounds. Then
I(t) < 9m₀, E[R] < log_{6/5} m₀ + 5, the search ends with probability 1, and the returned element is uniformly
distributed on the marked set. For t ≤ 3N/4, m₀ ≤ √(N/t), so I(t) < 9√(N/t). (Credit: BBHT 1998, Theorem 3, for the
form O(√(N/t)); the constant 9 is the one proved here, and the constants of BBHT and of Dürr–Høyer are not used.)

**Proof.** Let A_s be the event that round s is executed; P(A_s) = Π_{r<s}(1 − P_r), and the expected number of
iterations of round s, given A_s, is (M_s − 1)/2. So I(t) = Σ_s P(A_s)(M_s − 1)/2 and E[R] = Σ_s P(A_s).
Since t(N − t) ≥ N − 1, m₀ ≤ N/(2√(N − 1)) ≤ √N, so s₀ = min{s : M_s ≥ m₀} exists (m_s = √N for large s), and
M_s ≥ m₀ for all s ≥ s₀ (M_s is nondecreasing).
Rounds before s₀: M_s < m₀ ≤ √N, so m_s = λ^s, M_s − 1 < λ^s and λ^(s₀−1) ≤ M_(s₀−1) < m₀. Their iterations sum to
less than (1/2) Σ_{s<s₀} λ^s < (1/2) λ^(s₀−1) · λ/(λ − 1) < (1/2) · 6m₀ = 3m₀.
Rounds from s₀ on: P_s ≥ 1/4 (Lemma B), so P(A_(s₀+u)) ≤ (3/4)^u, and M_(s₀+u) − 1 < λ^(s₀+u) with λ^(s₀) < λm₀
(by the line above if s₀ ≥ 1; if s₀ = 0, λ⁰ = 1 ≤ m₀ as sin 2θ ≤ 1). Their iterations contribute less than
Σ_u (3/4)^u λ^u · λm₀/2 = (λm₀/2)/(1 − 3λ/4) = 6m₀, since 3λ/4 = 0.9 < 1. Total: I(t) < 9m₀.
E[R] ≤ s₀ + Σ_u (3/4)^u = s₀ + 4, and s₀ < log_λ m₀ + 1 (from λ^(s₀−1) < m₀ if s₀ ≥ 1). P(A_s) → 0, so the search
ends with probability 1, and by Lemma G the element measured in the successful round is uniform on the marked set.
For t ≤ 3N/4, N − t ≥ N/4 gives √(t(N − t)) ≥ √(tN)/2, so m₀ ≤ √(N/t). ∎

**Exact expectations.** With q_iter queries per iteration and q_check per round, the expected cost is
Σ_s P(A_s)(q_iter(M_s − 1)/2 + q_check). From the first s with m_s = √N on, all rounds are identical, so the rest of
the series is geometric. This is the sum that `lib.qsearch.expected_cost_exponential` evaluates in floating point.

**Check.** Test class `MinimumFindingProofChecks`, `test_exponential_search_theorem`: I(t) < 9m₀ and
E[R] < log_{6/5} m₀ + 5 (the series of the proof, evaluated in floating point) for every t = 1..N − 1, n = 1..11,
and for 600 values of t at n = 12..16; Lemma B against the direct average for n = 1..6 and every t, M = 1..40.
Existing: `tests/test_qsim.py`, `test_lemma2_closed_form`, and the simulated-versus-exact comparison
`test_simulated_costs_match_exact_expectations`.

## 5. Dürr–Høyer as implemented: Lemma 1, Lemma 2, Theorem 1, expected queries

Domain: n ≥ 1, distinct values. (For n = 0, `durr_hoyer_run` does not terminate: the search for an element below
the only one makes zero-iteration rounds forever, because ⌈√1⌉ = 1; the entry's statements are for n ≥ 1.) Time is
counted as in the code and the paper: n = lg N per stage 2(a) and 1 per Grover iteration. The *infinite algorithm*
is `durr_hoyer_run` with `budget=None`: stage 2(a), the exponential search without budget for
{j : T[j] < T[y]}, and the new threshold, repeated; T_min is the time at which the threshold first holds the
minimum.

**Lemma 1 (credit: Dürr & Høyer 1996, Lemma 1).** In the infinite algorithm, the element of rank r (rank 1 = the
minimum) is ever the threshold with probability exactly 1/r.

**Proof.** The first threshold is uniform. When the threshold has rank r′ ≥ 2, the search has the r′ − 1 smaller
elements marked; by Theorem E it ends with probability 1 and returns an element uniform on them, so the next rank
is uniform on {1, …, r′ − 1}. With q_r the probability that rank r is visited, q_r = 1/N + Σ_{r′=r+1}^{N} q_{r′}/(r′ − 1).
By downward induction q_r = 1/r: q_N = 1/N, and if q_{r′} = 1/r′ for all r′ > r, then
q_r = 1/N + Σ_{r′=r+1}^{N} (1/(r′ − 1) − 1/r′) = 1/r. ∎

**Lemma 2 (with the constants proved here).** E[T_min] = Σ_{r=2}^{N} (1/r)(n + I(r − 1)) < 0.95 · m_DH, where
m_DH = (45/4)√N + (7/10) lg²N is the bound of Dürr & Høyer's Lemma 2. In particular E[T_min] < m_DH.

**Proof.** While the threshold has rank r ≥ 2, the run spends n time units in stage 2(a) and the iterations of one
search with r − 1 marked elements, whose expectation is I(r − 1) whatever happened before; by Lemma 1 and linearity,
E[T_min] = Σ_{r≥2} (1/r)(n + I(r − 1)). First part: Σ_{r=2}^{N} 1/r ≤ ln N = n ln 2 < 0.6932n, so it is below
0.6932n². Second part: by Theorem E it is below 9A(N), A(N) = Σ_{t=1}^{N−1} m₀(t)/(t + 1). For t ≤ N/2,
m₀(t) = (1/2)√(N/t)(1 − t/N)^(−1/2) ≤ (1/2)√(N/t)(1 + c t/N) with c = 2(√2 − 1) (the chord of the convex function
(1 − x)^(−1/2) on [0, 1/2]); summing, with S = Σ_{t≥1} 1/((t + 1)√t) and Σ_{t≤K} t^(−1/2) ≤ 2√K, these terms give at
most (S/2)√N + c/√2. For t > N/2, with u = N − t, m₀(t)/(t + 1) < N/(2t^(3/2)√u) < √2/(√N √u), and these terms give
at most (√2/√N) · 2√(N/2) = 2. So A(N) < (S/2)√N + 2 − √2 + 2 < (S/2)√N + 2.586, and S < 1.861 (the partial sum to
10⁴ plus the tail bound Σ_{t>K} t^(−3/2) < 2/√K). Hence E[T_min] < 0.6932n² + 8.3745√N + 23.28. For n ≥ 7,
0.95 m_DH − (this bound) = 2.313√N − 0.0282n² − 23.28 > 0 (it is 1.50 at n = 7 and increasing). For n = 1..6 the
bound n(H_N − 1) + 9A(N), with the finite sums evaluated, is below 0.95 m_DH (its largest ratio to m_DH, at n = 6, is 0.762). ∎

**Theorem 1 (as implemented; credit: Dürr & Høyer 1996, Theorem 1).** For n ≥ 1, `minimum_durr_hoyer` returns the
index of the minimum with probability greater than 1/2 (at least 0.525), and every run ends with probability 1.

**Proof.** Let B = 22.5√N + 1.4n² = 2m_DH be the time-out. Run the infinite algorithm with the same random choices
and suppose T_min < B. Before the stage 2(a) of every threshold of rank ≥ 2 the elapsed time τ satisfies
τ + n ≤ T_min < B, so the stage is not interrupted; the following search, with total I_s iterations, satisfies
τ + n + I_s ≤ T_min < B, so it never meets its budget test (a round starts only while iterations < B − τ − n, an
iteration is made only while iterations + 1 ≤ B − τ − n). So the budgeted run makes the same steps until the
threshold holds the minimum; afterwards no step can replace it, since a replacement needs a strictly smaller value
(both in `check` and in the time-out branch of stage 2(a)). Hence the run fails only if T_min ≥ B, and by Markov's
inequality and Lemma 2, P(T_min ≥ B) ≤ E[T_min]/B < 0.95/2 = 0.475. (`durr_hoyer_budget` evaluates B in floating
point, with relative error far below the margin 0.025.) Termination: once the threshold is the minimum, no element is
marked; every round after the first of a search has M ≥ 2 (√N ≥ √2 > 6/5), so it makes j ≥ 1 iterations with
probability at least 1/2, and the time-out is reached with probability 1. ∎

**Expected queries.** For n ≥ 1, E[queries] ≤ (4 + 1/n)B + 4 = O(√N) (`time_complexity`: "O(sqrt N) queries";
the number of queries of a run is random and has no fixed upper bound, because rounds with j = 0 cost no time).
*Proof.* By §2 the count is 1 + 2I + M. Every iteration adds 1 to the time, which never exceeds B, so I ≤ B. M counts
the observed candidates: one per round, plus at most one in the time-out branch of stage 2(a). The first round of
each search has j = 0; there are at most B/n searches, since each is preceded by n time units. Rounds with j ≥ 1
make at least one iteration, except possibly the last round of the run: at most B + 1. A later round of a search has
j = 0 with probability 1/M ≤ 1/2 given the past; the sum over these rounds of 1{j = 0} − 1{j ≥ 1}/(M − 1) is a
martingale with increments bounded by 1, and their number has finite expectation (each has j ≥ 1 with probability at
least 1/2, and at most B + 1 rounds have j ≥ 1), so by optional stopping the expected number of these rounds with
j = 0 is at most the expected number with j ≥ 1, at most B + 1. So E[M] ≤ B/n + 2(B + 1) + 1. ∎ The measured mean is
about 2B (`verification`); that factor is a measurement, not a proof. The per-run facts of this proof (time ≤ B,
time = n·(number of searches) + I, I ≤ B, number of searches ≤ B/n, queries = 1 + 2I + M) are checked below.

**Success 1 − 2^(−c).** Run the algorithm c times independently, read the c returned entries (c queries) and output
the index of the smallest value. This fails only if every run fails, with probability at most 2^(−c), and costs
O(c√N) expected queries. ∎

**Check.** Test class `MinimumFindingProofChecks`: `test_lemma1_exact` (q_r = 1/r from the recursion in exact
rational arithmetic, N = 2..64), `test_lemma2_bound` (the finite bound below 0.95 m_DH for n = 1..6, the exact
E[T_min] from the exact search expectations below it for n = 1..10, and the analytic inequality for n = 7..200,
with S bounded as in the proof). Group `minimum` of the experiment script: for n = 2..6 and 60 seeds per n, the
unchanged `durr_hoyer_run` with the paper's budget returns the minimum in every run in which the infinite run with
the same seed has T_min < B (the coupling of the proof), and the empirical failure rate is below 1/2; for n = 1..8
and 20 seeds per n, every run satisfies the per-run facts of "Expected queries" (iterations and searches counted
by pass-through wrappers of `qsearch.grover_iteration` and `qsearch.exponential_search`), and the mean count is
below (4 + 1/n)B + 4 (ratio 0.48 to 0.81). Existing:
`experiments/2026-10-07_minimum_finding.py` (simulated time and queries of the infinite algorithm against their
exact expectations, |z| ≤ 1.01 for n = 2..10; 0 failures in 14000 runs of the budgeted algorithm).

## 6. The remaining statements

- **Space.** Scan: two indices and one value (O(n) bits for values below N). Dürr–Høyer: one n-qubit register and
  the register for the value T[j] that each marking computes and uncomputes (`lib/qsim.Oracle.apply_phase_where`
  does not materialise it); the classical threshold and the dictionary `last` hold O(1) values.
- **Relationship.** Θ(N) classical queries (§1 upper, §3 (c) lower, also with bounded error) and Θ(√N) quantum
  queries (§5 upper, §3 (d) lower): a quadratic separation in the query model, proved here. The measured crossover
  (the simulated mean quantum count exceeds N at every measured N ≤ 2048 and is below it at the measured N = 4096 and
  8192) is a measurement of this implementation, recorded in the experiment, not a proof.
- **Caveats.** The query accounting (2 per Grover iteration, 1 per observed candidate) is the counting convention of
  §2. "Bounded error ≥ 1/2" is Theorem 1. "The quantum query count is largely set by design": by §5, I ≤ B on every
  run.
