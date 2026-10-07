# Proofs: collision problem, classical vs Brassard–Høyer–Tapp

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
except the quantum lower bound, which the entry records as background: the exact counts (§1–§3), the law and the
exact expectation of the classical search (§4), the correctness and the expected query counts of both quantum
algorithms (§5), and the classical lower bounds (§6). Each proof is followed by the deterministic checks that re-run
its computable facts and the ranges they cover. A check covers only those ranges; the proofs cover the whole domain.
Randomized statements assume ideal randomness. It uses Lemma G and Corollary G2 of
`pairs/grover-search-classical-vs-quantum/PROOFS.md` and Theorem E (§4) of
`pairs/minimum-finding-classical-vs-quantum/PROOFS.md`. Checks named "test class X" are in
`tests/test_proofs_query.py`.

## Counting convention

`lib/qsim.py`, class `Oracle`: `Oracle.__call__` (a classical query `oracle(x)`) adds 1 to `self.queries` and
returns `table[x]`; `Oracle.apply_phase_where` adds 2 to `self.queries` (one application of a phase flip that depends
on the value f(x): compute and uncompute) and negates the amplitude of every x with `predicate(x, f(x))` true. Each
implementation creates one `Oracle(table)` and returns `oracle.queries` as the second component of its output, and
`harness.py`, `reported_cost(output)` returns `output[1]`. Nothing else changes `queries`: the methods of `State` and
the code of `lib/qsearch.py` itself do not use the oracle, and reading `oracle.queries` is not a query.

**Instances.** The harness has no `generate_scaling`, so V2 uses `generate(n, rng)` (n ≥ 1): the N = 2ⁿ points are
split into N/2 pairs by a random perfect matching and each pair gets its own label, so f is 2-to-1 and takes exactly
N/2 distinct values.

## 1. Classical birthday search: at most N/2 + 1 queries

**Statement.** On every 2-to-1 input (n ≥ 1) and every run, `collision_classical` makes at most N/2 + 1 queries
(`time_complexity`: "at most N/2 + 1"; `correctness`: "by pigeonhole one appears within N/2 + 1 queries"; the
docstring of `classical.py`: "At most N/2 + 1 queries (pigeonhole)").

**Proof.** The loop queries the points in the order of a permutation of 0..N − 1, one `oracle(x)` per point, and
returns at the first point whose value is already in `seen`. The values of the earlier points are pairwise distinct
(each was stored in `seen` without a repeat), and f takes only N/2 distinct values, so at most N/2 queries come
before the returning one: at most N/2 + 1 in all. In particular the final `raise` is never reached on a 2-to-1
input.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "collision classical: <= N/2+1":
n = 1..14, 30 seeded runs per n.

## 2. Brassard–Høyer–Tapp, both versions: k + 2 per Grover iteration + 1 per measured candidate

**Statement.** On every 2-to-1 input (n ≥ 1) and every run, `collision_bht` and `collision_bht_exponential` first
make exactly k = `subset_size(n)` = max(1, round(2^(n/3))) classical queries (k = N^(1/3) = 2^(n/3) for every n
divisible by 3 up to 60, so k = 2, 4, 8, 16, 32 at the V2 sizes n = 3, 6, 9, 12, 15). If two points of K collide, the
run ends there with exactly k queries. Otherwise each Grover iteration adds 2 queries and each measured candidate 1,
so a run with I Grover iterations and C measured candidates reports exactly k + 2I + C (the docstring of `bht.py`:
"(k queries)", "2 queries" per Grover iteration, "Every measured candidate is checked with one classical query";
`entry.json`: "counting 2 queries per Grover iteration").

**Proof.** `pairs = [(x, oracle(x)) for x in K]` queries each of the k points of K once (K = `range(k)`, or
`random.sample(range(1 << n), k)`, k distinct points; k ≤ 2ⁿ for n ≥ 1), all before the collision test. The value
k = 2^(n/3) for n = 3, 6, …, 60 is checked below. The loop over `pairs` makes no query and returns if it meets a
repeated value. Otherwise the remaining queries are made only by `phase`
(`oracle.apply_phase_where`, 2 queries per call) and by `check` (`oracle(x)`, 1 query per call). In
`lib/qsearch.py`, `phase` is called only by `grover_iteration`, once per Grover iteration, and `check` once after
each measurement, both in `search_known_count` and in `exponential_search` (called without a budget). Step 4 uses the
value stored by the last `check`, without a query.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "BHT: queries = k + 2 x iterations
+ candidates": n = 1..12 (10 seeded runs per n and version) and n = 15 (3 runs per version), 246 runs, 22 of them
with a collision inside K (Grover iterations and measurements counted by pass-through wrappers of
`qsearch.grover_iteration` and `State.measure_all`); line "BHT: k = 2^(n/3) when 3 divides n": n = 3, 6, …, 60.

## 3. Known-count version: ⌊π/(4θ)⌋ Grover iterations per attempt

**Statement.** If K = {0, …, k − 1} contains no collision, each attempt of `collision_bht` (one pass of the loop in
`search_known_count`) makes exactly m Grover iterations and one check, where m = `known_count_iterations(N, k)`; a run
that ends after A attempts reports exactly k + A(2m + 1) queries. For n = 1..40, m = ⌊π/(4θ)⌋ with sin²θ = k/N (the
docstring of `bht.py`: "floor(pi / (4 theta)) iterations, repeated on failure"; `entry.json`: "m = floor(pi/(4
theta))"). The number A ≥ 1 of attempts is random.

**Proof.** `search_known_count(n, phase, check, t, rng)` is called with t = len(K) = k. It computes
`iterations = known_count_iterations(1 << n, t)` once; each attempt runs `grover_iteration` that many times (2
queries each, section 2) and then `check(x)` once (1 query), and the search returns at the first attempt whose check
succeeds. With the k queries of step 1 (section 2), A attempts give k + A(2m + 1). The value:
`known_count_iterations` returns `math.floor(math.pi / (4 * grover_angle(N, t)) + _EPS)` with
`grover_angle(N, t)` = asin(√(t/N)) and `_EPS` = 10⁻⁹. For n = 1, 2, k = N/2, so θ = π/4, π/(4θ) = 1, and the check
confirms m = 1. For n = 3..40 the check verifies sin²(π/(4(m + 1))) < k/N < sin²(π/(4m)), that is,
m < π/(4θ) < m + 1 (sin² increases on [0, π/2], and θ ≤ π/4 since k ≤ N/2), with π and the sines computed to 70
digits.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "BHT: queries = k + 2 x iterations
+ candidates": the runs of section 2, with Grover iterations = m × attempts in every run of `collision_bht` without
a collision in K; line "BHT: code's m = floor(pi/(4 theta))": n = 1..40.

## 4. Classical birthday search: law, exact expectation, space

**Statement.** For every 2-to-1 input on N = 2ⁿ ≥ 2 points (m = N/2 pairs) and every run, `collision_classical`
returns two distinct indices with equal values, and its number Q of queries satisfies
P(Q > q) = Π_{i=0}^{q−1} (N − 2i)/(N − i) for q ≥ 0 (the factor i = 0 is 1, so this is the product over
i = 1..q − 1 of the docstring of `classical.py`). Hence

E[Q] = Σ_{q≥0} P(Q > q) = 4^m / C(2m, m) = 2^N / C(N, N/2), and √(πN/2) < E[Q] < √(πN/2) · e^(1/(3N)),

so E[Q] ~ √(πN/2) ≈ 1.2533√N = Θ(2^(n/2)). The dictionary `seen` holds Q − 1 entries when the run returns (expected
E[Q] − 1 = Θ(√N), at most N/2); the list `order` holds N indices.

**Proof.** The loop queries the points in the order of a uniformly random permutation and returns at the first point
whose value is already in `seen`, that is, whose partner came earlier; the returned pair is that point and its
partner, two distinct points with equal values. So Q > q iff the first q points lie in q distinct pairs. Given that
the first i do, the next point is uniform among the N − i others, of which exactly i are partners of earlier points:
this gives the product. For q ≤ m, Π_{i<q} (2m − 2i)/(2m − i) = [2^q m!/(m − q)!]·[(2m − q)!/(2m)!]
= 2^q C(2m − q, m)/C(2m, m), and the product is 0 for q > m. The identity Σ_{q=0}^{m} 2^q C(2m − q, m) = 4^m: with
j = m − q it reads Σ_{j=0}^{m} C(m + j, j) 2^(−(m+j+1)) = 1/2, and the left side is the probability that, in fair
coin tosses, heads reach m + 1 before tails do (the game ends after m + 1 heads and j ≤ m tails, last toss heads),
which is 1/2 by symmetry. The bounds: Robbins' form of Stirling's formula, k! = √(2πk)(k/e)^k e^(r_k) with
1/(12k + 1) < r_k < 1/(12k), gives 4^m/C(2m, m) = √(πm) e^(2r_m − r_(2m)), and
0 < 2/(12m + 1) − 1/(24m) < 2r_m − r_(2m) < 1/(6m) − 1/(24m + 1) < 1/(6m); with m = N/2 this is the stated
interval. Each pass stores one value in `seen` except the last. ∎

**Check.** Test class `CollisionProofChecks`, `test_classical_law_by_enumeration`: the unchanged
`collision_classical`, run on every permutation (the shuffle replaced by each one) of a 2-to-1 input with N = 2, 4, 8:
the distribution of Q is exactly the product law, every answer is a collision, and the size of `seen` at the return
(read by a trace of the frame, on every permutation for N ≤ 4 and on every 20th for N = 8) is Q − 1; `test_classical_expectation_formula`: the sum of the products equals
2^N/C(N, N/2) in exact rational arithmetic and lies in the interval, for n = 1..10. Existing:
`experiments/2026-10-07_collision_expected_queries.py` Part A and `2026-10-07_collision_classical_n8_followup.py`
(simulated means against the exact expectation).

## 5. Brassard–Høyer–Tapp: correctness and expected queries

Let k = `subset_size(n)` = max(1, round(x)), x = 2^(n/3) = N^(1/3), so x/2 < k < 1.5x (x > 1, round(x) > x − 1/2),
and 1 ≤ k ≤ N/2 for n ≥ 1 (n = 1, 2: k = 1, 2 = N/2; n ≥ 3: x + 1/2 ≤ 2^(n−1)).

**Statement.** For every 2-to-1 input with n ≥ 1:
(a) both versions always return a collision, and every run ends with probability 1;
(b) if the k points of K contain no collision, the marking H(x) = [f(x) ∈ L and L[f(x)] ≠ x] marks exactly the k
partners of the points of K;
(c) known-count version (K = {0, …, k − 1}): if K contains a collision the run makes exactly k queries; otherwise
each attempt succeeds independently with probability p = sin²((2m + 1)θ) ≥ 1 − k/N ≥ 1/2, with sin²θ = k/N and
m = ⌊π/(4θ)⌋, and the expected number of queries is exactly k + (2m + 1)/p. Over the harness distribution (a
uniformly random perfect matching; the labels do not matter) K is collision-free with probability
P_nc(k) = Π_{i=1}^{k−1} (N − 2i)/(N − i), so the expected count is k + P_nc(k)(2m + 1)/p (`time_complexity`);
(d) exponential version (K a uniformly random k-subset): on every input the expected count is
k + P_nc(k)(2I(k) + C(k)), where I(k) and C(k) are the expected numbers of Grover iterations and of rounds of the
exponential search with k marked elements (minimum-finding proofs, §4);
(e) both expected counts are Θ(N^(1/3)) on every input: at least k > N^(1/3)/2, and at most
(1.5 + π√2)N^(1/3) + 2 < 6N^(1/3) + 2 (known count) and 1.5N^(1/3) + 18√2·N^(1/3) + log_{6/5}√N + 5 (exponential).

**Proof.** (a) If two points of K have equal values, the run returns them (distinct points, equal values).
Otherwise the search returns an x₁ for which `check(x₁)` held, that is, f(x₁) ∈ L and L[f(x₁)] ≠ x₁, and the
output is the pair {L[f(x₁)], x₁}: distinct points with equal values. Termination follows from the success
probabilities in (c) and from Theorem E (minimum-finding proofs, §4), since by (b) at least one point is marked.
(b) L maps each of the k distinct values of K to its point. A point x ∈ K has L[f(x)] = x, so it is unmarked. A
point x ∉ K has f(x) ∈ L iff its partner is in K, and then L[f(x)] is that partner, not x. The partners of the k
points of K are k distinct points (pairs are disjoint), none in K (no collision in K).
(c) `phase` (`Oracle.apply_phase_where` with the predicate H) is the phase flip on the marked set, so by Lemma G of
the Grover proofs with t = k each attempt of `search_known_count` measures a marked point with probability
p = sin²((2m + 1)θ), m = `known_count_iterations(N, k)` = ⌊π/(4θ)⌋ (§3 checks the code's value for n = 1..40), and
`check` accepts exactly the marked points. Attempts use fresh states and fresh randomness, so the number A of
attempts is geometric with mean 1/p, and by §3 the count is k + A(2m + 1), whose expectation is k + (2m + 1)/p.
Corollary G2 gives 1 − p ≤ k/N ≤ 1/2. For the harness distribution: relabelling the points by a uniformly random
permutation maps a fixed matching to a uniform one, so P(K collision-free) equals the probability that the first k
points of a uniform permutation lie in distinct pairs, which is the product of §4 with q = k.
(d) For every fixed input, a uniformly random k-subset is collision-free with probability P_nc(k) by the same
computation. Given that, by (b) the exponential search runs with k marked points; each Grover iteration costs 2
queries and each round one check, so its expected cost is 2I(k) + C(k); the k queries of K are always made.
(e) Lower bound: the k queries of K. Known count: p ≥ 1/2 and m ≤ π/(4θ) ≤ (π/4)√(N/k) (θ ≥ sin θ = √(k/N)), so
(2m + 1)/p ≤ π√(N/k) + 2, and √(N/k) < √(2N/x) = √2·N^(1/3). Exponential: k ≤ N/2 ≤ 3N/4, so by Theorem E,
I(k) < 9√(N/k) < 9√2·N^(1/3), and C(k) < log_{6/5} m₀ + 5 ≤ log_{6/5} √N + 5 (m₀ ≤ √N). ∎

**The computed constants.** The expected counts of (c) and (d), evaluated in floating point (the product P_nc(k),
`lib.qsearch.expected_cost_known` and `expected_cost_exponential` with 2 queries per iteration and 1 per check), give
E/N^(1/3) in [2.564, 2.572] for the known-count version at n = 15, 18, …, 30 (the sizes of the experiment's
Part C; k = N^(1/3) there) and in [2.536, 2.572] at every n = 15..30; and in [3.844, 3.897] for the exponential
version at every n = 18..30. These are evaluations of the proved formulas at finitely many sizes; no limit is proved.

**Check.** Test class `CollisionProofChecks`: `test_bht_marked_set_and_success_probability` (for n = 1..8 and 5
seeded inputs per n, with K = {0..k − 1} and with one seeded random K per input: if K is collision-free the predicate marks
exactly the k partners, and the simulated state after m iterations, built with the unchanged predicate and the
`lib.qsim` operators, puts probability p = sin²((2m + 1)θ) on them, to 10⁻⁹); `test_pnc_by_enumeration` (P_nc(k) over
all 105 perfect matchings of 8 points and all 945 of 10 points, k = 1..5, exact rationals); `test_bht_constants` (the
three ranges above and the bounds of (e) for n = 1..30). Existing: §2 and §3 checks (the exact counts), and
`experiments/2026-10-07_collision_expected_queries.py` (simulated means against these exact expectations).

## 6. Classical lower bounds

**Statement.** Let N = 2ⁿ ≥ 4.
(a) Randomized, bounded error: on a 2-to-1 function drawn as in the harness (uniformly random perfect matching,
distinct labels drawn uniformly from a codomain of size at least N/2), every deterministic algorithm with at most
q ≤ N − 2 queries outputs a collision with probability at most q(q − 1)/(2(N − q + 1)) + 1/(N − q − 1). Hence every
randomized algorithm that outputs a collision with probability at least 1/2 on every 2-to-1 input makes more than
√N/2 queries on some input (N ≥ 16), and one with at most T expected queries and success at least 2/3 has
T > √N/12. So Ω(√N) queries are necessary, and the birthday search (§4) is optimal up to a constant factor.
(b) Deterministic, exact: every always-correct deterministic algorithm makes at least N/2 + 1 queries on some input;
N/2 + 1 suffice (§1).

**Proof.** (a) Fix a deterministic algorithm; repeated queries can be dropped. Consider a history in which the first
i queried points z₁, …, z_i received pairwise distinct values. The queries are determined by the earlier answers, so
the probability of this history given the matching μ is 0 if two z's are matched in μ, and otherwise the probability
that i given distinct pairs receive i given distinct labels, the same for all such μ. Hence, given the history, μ is
uniform over the matchings in which z₁, …, z_i are pairwise unmatched. This conditional distribution is invariant
under permutations of the N − i unqueried points, and the partners of the z's are i distinct unqueried points, so
the set of partners is a uniformly random i-subset of the unqueried points. Therefore the next query (an unqueried
point) completes a pair with probability exactly i/(N − i), and P(some pair is completed within q queries) is at most
Σ_{i<q} i/(N − i) ≤ q(q − 1)/(2(N − q + 1)). If the algorithm stops after i ≤ q collision-free queries and outputs
{a, b}: two queried points are not a pair; a queried z with an unqueried b is a pair with probability 1/(N − i); two
unqueried points are a pair only if both lie among the N − 2i unqueried non-partners, which are matched among
themselves uniformly, with probability
[(N − 2i)(N − 2i − 1)/((N − i)(N − i − 1))]·[1/(N − 2i − 1)] ≤ 1/(N − i − 1). So a correct guess has probability at
most 1/(N − q − 1), which proves the bound. For q ≤ √N/2 and N ≥ 16 it is at most 1/7 + 1/13 < 1/2. A randomized
algorithm with success at least 1/2 on every input has average success at least 1/2 under this distribution, so some
deterministic algorithm in its support does: hence q > √N/2. With at most T expected queries, stopping before query
⌊6T⌋ + 1 loses at most 1/6 by Markov's inequality, so 6T > √N/2.
(b) Adversary: answer each new query with a new value, for the first N/2 distinct queries (at most N/2 values are
needed). Suppose the algorithm outputs {a, b} after i ≤ N/2 queries, all with distinct values; let Q be the queried
set and U the rest, |U| = N − i ≥ i. Build a 2-to-1 function consistent with the answers in which a and b are not a
pair: if both are queried, any consistent function. Otherwise pair every queried point with its own unqueried point
and the remaining unqueried points among themselves (N − 2i is even), choosing the pairing so that a and b are not
matched: if exactly one of them is queried, say a ∈ Q and b ∈ U, give b a queried partner other than a when i ≥ 2, and give a an unqueried partner other
than b when i = 1 (|U| ≥ 3); if a, b ∈ U, give a a queried partner when i ≥ 1, and a partner other than b when i = 0
(N ≥ 4). Give the queried pairs the answered values and the other pairs new distinct values. The output is wrong on
this function, so the algorithm must make N/2 + 1 queries on the adversary's input. (For N = 2 the only pair is a
correct output with no query, hence N ≥ 4.) ∎

The same bound also follows from the Simon lower bound (`pairs/simon-classical-vs-quantum/PROOFS.md`, §6), because
every Simon function is 2-to-1 and a collision reveals s; the proof above is direct.

**Check.** Test class `CollisionProofChecks`: `test_birthday_lemma_by_enumeration` (N = 8: for every ordered sequence
of up to 4 distinct points and all 105 matchings, the conditional probability that the next point completes a pair,
given a collision-free prefix, is exactly i/(N − i), and a guessed pair has the stated probability, both for a
queried and an unqueried point and for two unqueried points);
`test_lower_bounds_by_exhaustion` (N = 4 and 8: the exhaustive optimum over all adaptive strategies that see the
equality pattern of the answers, which is as strong as seeing the labels since the labels are uniform given the
pattern, is below the bound of (a) for every q ≤ N − 2, and the exhaustive worst case of the best exact strategy is
N/2 + 1 = 3 and 5).

## 7. The remaining statements

- **Relation to Simon's problem.** Simon's functions are the 2-to-1 functions whose pairs are the cosets {x, x ⊕ s};
  a collision {a, b} gives s = a ⊕ b, and conversely {0, s} is a collision. Simon's algorithm needs fewer than
  n + 0.61 expected queries (`pairs/simon-classical-vs-quantum/PROOFS.md`, §5) and both problems need Θ(√N) classical
  queries (§4 and §6 here; Simon proofs §2 and §6). That no quantum algorithm does better than Θ(N^(1/3)) without the
  XOR structure is the cited lower bound of Aaronson & Shi (2004), Kutin (2005) and Ambainis (2005): background, not
  proved here.
- **Space.** Classical: §4. BHT: one n-qubit register; the dictionary L holds the k = Θ(N^(1/3)) values of K, and the
  marking reads it in superposition (a quantum-readable memory of k entries). This follows from the code.
- **Caveats.** Query accounting: 2 queries per Grover iteration and 1 per measured candidate (§2); with any constant
  numbers per iteration and per candidate the proofs of §5 give the same Θ(N^(1/3)), with other constants. The fit of
  the exponential-search variant over n = 3..15 (slope 1.154, and its compatibility with 2^(n/2)) is a measurement.
