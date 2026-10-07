# Proofs: unstructured search, classical vs Grover

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code):
the exact count of §1, the correctness, expectations and success probabilities of both algorithms (§2–§4), and the
lower bounds on both sides (§5, §6). Each proof is followed by the deterministic checks that re-run its computable
facts and the ranges they cover. A check covers only those ranges; the proofs cover the whole domain. Randomized
statements assume ideal randomness (`random.shuffle` a uniform permutation, `rng.random()` uniform on [0, 1)); the
checks use fixed seeds or enumerate all outcomes. §3 and §6 are general and are also used by
`pairs/collision-problem-classical-vs-quantum` and `pairs/minimum-finding-classical-vs-quantum`.

Checks named "test class X" are in `tests/test_proofs_query.py`.

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_phase` (a quantum query) adds 1 to `self.queries` and negates the amplitude of
the marked x. Each implementation creates one `Oracle(table)` and returns `oracle.queries` as the second component
of its output, and `harness.py`, `reported_cost(output)` returns `output[1]`. The methods of `State` (`h_all`,
`reflect_about_uniform`, `measure_all`) do not use the oracle, and reading `oracle.queries` is not a query.

**Instances.** The harness has no `generate_scaling`, so V2 uses `generate(n, rng)`: N = 2ⁿ positions with exactly
one marked position, drawn uniformly.

## 1. Grover: k + 1 queries per attempt, k = ⌊(π/4)√N⌋

**Statement.** On every input and every run, each attempt of `search_grover` (one pass of its `while True` loop)
makes exactly k phase-oracle queries and one classical query, where k is the value
`math.floor(math.pi / 4 * math.sqrt(1 << n))`; a run that ends after A attempts reports exactly A(k + 1) queries
(the docstring of `grover.py`: "Each attempt runs k = floor(pi/4 * sqrt(N)) Grover iterations (phase-oracle query
+ diffusion), measures, and confirms the candidate with one classical query"). For n = 0..64 this k equals
⌊(π/4)√N⌋, N = 2ⁿ; at the V2 sizes n = 2, 4, 6, 8, 10, 12 it is 1, 3, 6, 12, 25, 50. The number A ≥ 1 of attempts
is random.

**Proof.** `iterations` is computed once, before the loop. Each pass creates `State(n)`, applies `state.h_all()`
(no query), runs `iterations` times `oracle.apply_phase(state)` (1 query each) and `state.reflect_about_uniform()`
(no query), measures with `state.measure_all(random)` (no query) and calls `oracle(candidate)` once (1 query); it
returns iff that value is 1. So each pass costs `iterations` + 1 queries, and a run with A passes costs
A(`iterations` + 1). The value: the check below verifies 4k ≤ π√N < 4(k + 1) for n = 0..64 with exact integer
arithmetic (π enclosed between two rationals with denominator 10⁵⁰), so k = ⌊(π/4)√N⌋ there.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Grover: queries = A(k+1)":
n = 0..12, 12 seeded instances per n (includes the V2 sizes; attempts counted as executions of the line
`state = State(n)`); line "Grover: code's k = floor(pi sqrt(N)/4)": n = 0..64.

## 2. Classical random-order search

**Statement.** On every input (n ≥ 0, one marked position x\*), `search_classical` returns x\*. Its number Q of
queries is uniform on {1, …, N}; so E[Q] = (N + 1)/2 = Θ(2ⁿ) and Q ≤ N on every run. It stores the N-entry list
`order` (O(N) words).

**Proof.** `order` is a uniformly random permutation of 0..N − 1, queried in that order, and the loop returns the
first x with `oracle(x)` = 1, which is x\* (the only marked position); the final `raise` is unreachable under the
promise. Q is 1 plus the position of x\* in `order`, and the position of a fixed element in a uniform permutation is
uniform on {0, …, N − 1}. Hence P(Q = j) = 1/N for j = 1..N and E[Q] = (N + 1)/2.

**Check.** Test class `GroverProofChecks`, `test_classical_query_count_is_uniform`: the unchanged
`search_classical`, run on every permutation (the shuffle replaced by each permutation in turn) and every marked
position, for n = 0..3: the counts are exactly uniform on 1..N and the answer is always x\*.

## 3. The rotation lemma (Grover iterations), and the simulator's operators

**Lemma G.** Let N ≥ 1, let M ⊆ {0, …, N − 1} with |M| = t, 1 ≤ t ≤ N, and let θ ∈ (0, π/2] with
sin²θ = t/N. Let u = N^(−1/2) Σₓ |x⟩, let O be the phase flip on M (|x⟩ ↦ −|x⟩ for x ∈ M, |x⟩ ↦ |x⟩ otherwise)
and D = 2|u⟩⟨u| − I. Then for every j ≥ 0 the vector (DO)ʲu has amplitude sin((2j + 1)θ)/√t on every x ∈ M and
cos((2j + 1)θ)/√(N − t) on every x ∉ M. Consequently a measurement in the computational basis gives an element of M
with probability sin²((2j + 1)θ), and, conditioned on that event, an element uniformly distributed on M.

**Proof.** If t = N, then θ = π/2, u is the uniform vector on M, Ou = −u and D(−u) = −u, so (DO)ʲu = (−1)ʲu, and
(−1)ʲ = sin((2j + 1)π/2); the claim holds. Let t < N, g = t^(−1/2) Σ_{x∈M} |x⟩, b = (N − t)^(−1/2) Σ_{x∉M} |x⟩ and
v(φ) = sin φ · g + cos φ · b. Then u = v(θ). On the real plane spanned by g and b: Og = −g and Ob = b, so
O v(φ) = v(−φ). The vector w = v(θ + π/2) is a unit vector orthogonal to u in this plane, Du = u and Dw = −w; writing
v(φ) = cos(φ − θ) u + sin(φ − θ) w gives D v(φ) = cos(φ − θ) u − sin(φ − θ) w = v(2θ − φ). Hence
DO v(φ) = v(φ + 2θ), and (DO)ʲ v(θ) = v((2j + 1)θ), whose amplitudes are the stated ones. The probability of M is
t · sin²((2j + 1)θ)/t, and all amplitudes on M are equal. ∎

**Corollary G2 (known number of marked elements).** With m = ⌊π/(4θ)⌋, the failure probability after m
iterations is cos²((2m + 1)θ) ≤ sin²θ = t/N.

**Proof.** m ≤ π/(4θ) < m + 1 gives 2mθ ≤ π/2 < 2mθ + 2θ, so δ = (2m + 1)θ − π/2 lies in (−θ, θ]. Then
cos²((2m + 1)θ) = sin²δ ≤ sin²θ, because |δ| ≤ θ ≤ π/2 and sin² increases on [0, π/2]. ∎

**The simulator implements these operators exactly** (up to floating-point rounding). `State(n)` followed by
`h_all()` is u, because the Hadamard on every qubit maps |0…0⟩ to the uniform vector (`State.h(k)` maps the pair
(a_i, a_{i+2^k}) to ((a + b)/√2, (a − b)/√2), the Hadamard on qubit k). `Oracle.apply_phase` negates exactly the
amplitudes with f(x) = 1, so it is O for M = {x : f(x) = 1}. `State.reflect_about_uniform` maps a to 2·mean(a) − a,
and 2u⟨u|a⟩ is the vector with every entry 2 Σ_y a_y / N, so it is D. Finally D = H^⊗n (2|0⟩⟨0| − I) H^⊗n (the
`caveats`), because H^⊗n|0⟩ = u and H^⊗n is a real symmetric involution; neither form uses the oracle.

**Check.** Test class `GroverProofChecks`, `test_simulated_state_matches_lemma_g`: for n = 0..10 and t = 1, 2, 3,
N/4 (where defined), the simulated state after j = 0..8 iterations agrees with the amplitudes of Lemma G to 10⁻⁹,
and `test_known_count_corollary`: δ ∈ (−θ, θ] and the failure bound for every N = 2ⁿ, n = 1..12, and every
t = 1..N. Existing: `tests/test_qsim.py`, `test_diffusion_matches_definition` (D against its definition, n = 1..5)
and `test_grover_amplitudes_match_closed_form`.

## 4. Grover's algorithm: always correct, success probability per attempt, expected queries

Here t = 1, sin θ = 1/√N, k = ⌊(π/4)√N⌋ and p = sin²((2k + 1)θ). The statements hold for every n with this k. The
code computes k in floating point; it equals ⌊(π/4)√N⌋ for n ≤ 64 (§1; in fact for every n ≤ 109), so the statements
hold for the code there. For n = 110..139 the code's k is below this floor by 1, 1, 2, 2, 4, 5, 8, 10, 17, 20, 35, 41,
70, 83, 141, 167, 282, 334, 564, 669, 1129, 1339, 2259, 2678, 4518, 5357, 9036, 10715, 18072, 21431 (n = 110, 111,
…, 139), and there (d) fails for the code: (k + 1)/p − π√N/4 is −0.10 at n = 110. The simulation cannot reach such n.

**Statement.** For every n ≥ 0:
(a) the output is always the marked position;
(b) each attempt succeeds independently with probability p, so the number of attempts A is geometric with mean
1/p, and the expected number of queries is exactly (k + 1)/p;
(c) 1 − p ≤ (1/(N − 1))·(1 + π/(4√(N − 1)))² for N ≥ 2, which is O(1/N), and at most 1.4468/(N − 1) for N ≥ 16;
p = 1, 1/2, 1, 121/128 for n = 0, 1, 2, 3, so p ≥ 1/2 for every n (the `caveats`: one attempt succeeds only with
probability 1/2 at n = 1);
(d) (π/4)√N < (k + 1)/p < (π/4)√N + 2.9 for every n, and < (π/4)√N + 1.45 for n ≥ 4; so the expected count is
(π/4)√N + O(1) = Θ(2^(n/2)), and the classical confirmation costs only O(1) expected extra queries over the k
iterations: (k + 1)/p − k < 3.9.

**Proof.** (a) The run returns `candidate` only after `oracle(candidate)` returned 1.
(b) Each attempt starts from a fresh `State(n)` and draws fresh randomness for its measurement. By Lemma G with
t = 1 and j = k the measurement gives x\* with probability p, and the confirming query returns 1 iff the candidate
is x\*. So A is geometric with parameter p (p > 0 by (c)), E[A] = 1/p, and by §1 the count is A(k + 1).
(c) Let δ = (2k + 1)θ − π/2, so 1 − p = cos²((2k + 1)θ) = sin²δ ≤ δ². For N ≥ 2, θ ∈ (0, π/4] and
1/√N = sin θ ≤ θ ≤ tan θ = 1/√(N − 1). Upper side: k ≤ π√N/4, so
δ ≤ (π√N/2)θ + θ − π/2 ≤ (π/2)(√(N/(N − 1)) − 1) + θ ≤ π/(4(N − 1)) + 1/√(N − 1), using √(1 + x) − 1 ≤ x/2.
Lower side: k > π√N/4 − 1, so δ > (π√N/2 − 2)θ + θ − π/2 = (π√N/2)θ − π/2 − θ ≥ −θ ≥ −1/√(N − 1). Hence
|δ| ≤ 1/√(N − 1) + π/(4(N − 1)), which is the bound; for N ≥ 16 the factor (1 + π/(4√(N − 1)))² is at most
(1 + π/(4√15))² < 1.4468. The values for n ≤ 3 are direct: k = 0, 1, 1, 2 and θ = π/2, π/4, π/6, arcsin(1/√8).
(d) Lower: (k + 1)/p ≥ k + 1 > π√N/4. Upper, n ≥ 4: p ≥ 1 − 1.4468/15 > 0.9, so
(k + 1)/p − π√N/4 < (k + 1)(1 − p)/p + 1 ≤ (π√N/4 + 1)·1.4468/(0.9(N − 1)) + 1, and
(π√N/4 + 1)/(N − 1) is decreasing in N (as a function of s = √N: (as + 1)/(s² − 1) has negative derivative for
s > 1), so it is at most (π + 1)/15 < 0.2762 for N ≥ 16, which gives < 1.45. For n = 0..3 the values of
(k + 1)/p − π√N/4 are 0.2146, 2.8893, 0.4292, 0.9521. The last claim: (k + 1)/p − k ≤ ((k + 1)/p − π√N/4) + 1. ∎

**Check.** Test class `GroverProofChecks`, `test_success_probability_and_expectation`: for n = 0..200, with
k = ⌊(π/4)√N⌋ computed exactly (integer square root, π enclosed between two rationals; equal to the code's k for
n ≤ 109, and below it by exactly the gaps listed above for n = 110..139) and p in 120-digit decimal arithmetic (Machin's formula for π, Taylor series for arcsin and sin), p satisfies
the bound (c) and p ≥ 1/2, and (k + 1)/p lies in the interval (d) (double precision would not do: 1 − p is below
10⁻¹⁶ from n = 53 on); `test_simulated_state_matches_lemma_g` (above) checks that the simulated success probability after k
iterations is p for n = 0..10. V1 (the answer is checked against the table) and V2 (the averaged counts fit 2^(n/2))
are the measurements of the simulation.

## 5. Classical lower bound: Ω(N) queries, deterministic or randomized

**Statement.** Let N ≥ 1.
(i) If a classical algorithm (deterministic or randomized) makes at most q queries on every input and every run
and outputs the marked position with probability at least p on every input, then q ≥ pN − 1.
(ii) If it is always correct, then on some input its expected number of queries is at least
(N − 1)(N + 2)/(2N) ≥ (N − 1)/2.
(iii) If its expected number of queries is at most T on every input and its success probability is at least 2/3
on every input, then T ≥ (N − 2)/12.
So Ω(N) = Ω(2ⁿ) queries are needed in each setting, and the random-order search of §2 is optimal up to a constant
factor.

**Proof.** (i) Let x\* be uniform on {0, …, N − 1} and fix a deterministic algorithm B with at most q queries. On
input x\*, every answer is 0 until B queries x\*. Let y₁, …, y_r (r ≤ q) be the queries B makes when all answers are
0, and g its output in that case. If x\* ∉ {y₁, …, y_r}, B sees only zeros and outputs g. So B is correct only if
x\* ∈ {y₁, …, y_r, g}, a set of at most q + 1 positions, and P(B correct) ≤ (q + 1)/N. A randomized algorithm is a
probability distribution over such B (fix its random choices), so its success probability averaged over x\* is at
most (q + 1)/N; if it is at least p on every input, then p ≤ (q + 1)/N.
(ii) Fix a deterministic B that is always correct. While all answers have been 0 and at least two positions are
unqueried, two inputs (one marked position each) are consistent with the answers and need different outputs, so
B cannot stop. Hence on the all-zero branch B queries y₁, y₂, … until it finds x\* or has made N − 1 queries, and
its cost on input x\* = y_j is at least j (j ≤ N − 1), and on the last remaining position at least N − 1. On
uniform x\* its expected cost is at least (1/N)(Σ_{j=1}^{N−1} j + N − 1) = (N − 1)(N + 2)/(2N). A zero-error
randomized algorithm is a distribution over such B (outcomes of its random choices that would err on some input
have probability 0, as there are finitely many inputs), so its expected cost on uniform x\*, and hence on some x\*,
is at least that.
(iii) Stop the algorithm before its query number ⌊6T⌋ + 1 and output 0. By Markov's inequality it is stopped with
probability at most 1/6 on every input, so the truncated algorithm succeeds with probability at least
2/3 − 1/6 = 1/2 with at most 6T queries; by (i), 6T ≥ N/2 − 1. ∎

(The random-order search makes (N + 1)/2 expected queries, 1/N more than the bound (ii), because it does not stop
when one position is left.)

**Check.** Test class `GroverProofChecks`, `test_classical_lower_bound_by_exhaustion`: for N = 1..6, an exhaustive
minimax over all deterministic adaptive query strategies on the N inputs gives exactly min(N, q + 1) correctly
answered inputs with q queries (q = 0..N), and the minimum total cost of an always-correct strategy is exactly
Σ_{j=1}^{N−1} j + N − 1.

## 6. Quantum lower bound: Ω(√N) queries (the hybrid argument)

**Model.** A quantum query algorithm with T queries acts on C^N ⊗ W (query register ⊗ workspace): it applies fixed
unitaries U₀, O, U₁, O, …, O, U_T to a fixed initial unit vector and measures the final state with a projective
measurement {Π_y} whose outcomes y are the outputs. The oracle of a function F on {0, …, N − 1} is
O_F |i⟩|w⟩ = |i⟩ V_{F(i)} |w⟩ with unitaries V_v on W; this covers the phase oracle (V_v = (−1)^v I), the XOR oracle
|i, b⟩ ↦ |i, b ⊕ F(i)⟩ and `Oracle.apply_phase_where` (two XOR queries). Intermediate measurements can be deferred to
the end, a classical query is a quantum query on a basis state, and a general measurement is a projective one on a
larger workspace, so the model covers every algorithm in this dataset.

**Lemma H.** Let F_ref and F_x (x = 0, …, N − 1) be functions on {0, …, N − 1} such that F_x differs from F_ref
at most at position x. For a T-query algorithm let ψ^x and ψ^ref be its final states with the oracles O_{F_x} and
O_{F_ref}. Then Σₓ ‖ψ^x − ψ^ref‖ ≤ 2T√N.

**Proof.** Let φ_s be the state just before query s + 1 in the run with O_{F_ref} (s = 0, …, T − 1). Replacing the
oracle query by query, ψ^x − ψ^ref = Σ_s W_{s,x} (O_{F_x} − O_{F_ref}) φ_s, where W_{s,x} is the unitary made of
the later steps with O_{F_x}. Since O_{F_x} − O_{F_ref} = |x⟩⟨x| ⊗ (V_{F_x(x)} − V_{F_ref(x)}) has norm at most 2
and vanishes off |x⟩, ‖ψ^x − ψ^ref‖ ≤ Σ_s 2a_{s,x} with a_{s,x} = ‖(|x⟩⟨x| ⊗ I)φ_s‖. For each s,
Σₓ a_{s,x}² = ‖φ_s‖² = 1, so Σₓ a_{s,x} ≤ √N by the Cauchy–Schwarz inequality. Summing over s gives 2T√N. ∎

**Theorem Q.** If, for every x, the algorithm outputs x with probability at least p when its oracle is O_{F_x},
then T ≥ (pN − 1)/(4√N). (F_ref need not be a valid input.)

**Proof.** Let q_x = ‖Π_x ψ^ref‖², so Σₓ q_x ≤ 1, and d_x = ‖ψ^x − ψ^ref‖. For unit vectors a, b and a
projector Π, ‖Πa‖² − ‖Πb‖² = (‖Πa‖ − ‖Πb‖)(‖Πa‖ + ‖Πb‖) ≤ 2‖a − b‖, so p ≤ q_x + 2d_x. Summing over x and using
Lemma H: pN ≤ 1 + 4T√N. ∎

**Search (this entry).** Take F_x = the table with the single 1 at x and F_ref = the all-zero table (not a valid
input). Every quantum algorithm that finds the marked position with probability at least 2/3 on every input makes
at least (2N/3 − 1)/(4√N) = √N/6 − 1/(4√N) queries; one with expected at most T queries on every input and success
at least 2/3 makes T ≥ (N/2 − 1)/(24√N) (truncate at 6T queries as in §5 (iii)). So Ω(√N) = Ω(2^(n/2)) queries are
necessary, and Grover's algorithm, with (π/4)√N + O(1) expected queries (§4), is optimal up to a constant factor.
This is the "limit" of the entry: black-box search over N = 2ⁿ candidates needs Ω(2^(n/2)) quantum queries, a square
root and not an exponential saving. (Credit: Bennett, Bernstein, Brassard & Vazirani 1997.)

**Check.** Test class `GroverProofChecks`, `test_hybrid_inequality`: for N = 4 and 8 with a 2-dimensional
workspace, T = 1, 2, 3 and 20 seeded random choices of the unitaries U_s (Gram–Schmidt of Gaussian matrices) and of
the oracle's V_v, Σₓ ‖ψ^x − ψ^ref‖ ≤ 2T√N; also for Grover's own iterations with F_ref = 0, n = 2..8.

## 7. The remaining statements

- **Space.** Classical: the list `order` (N indices, §2). Grover: one n-qubit register (`State(n)`, 2ⁿ amplitudes
  in the simulation); the phase oracle and the diffusion act on it alone.
- **Relationship.** Θ(N) classically (§2 upper, §5 lower) and Θ(√N) quantumly (§4 upper, §6 lower): a quadratic
  separation in the query model, proved here.
- **Caveats.** The diffusion identity is in §3. "A separation relative to an oracle; it does not imply BQP ≠ BPP"
  limits the scope of the result and asserts nothing further.

**Check (space).** Test class `GroverProofChecks`, `test_space`: during `search_grover` every `State` created has
n qubits (n = 1..8), and `order` in `search_classical` has length N (n = 0..10).
