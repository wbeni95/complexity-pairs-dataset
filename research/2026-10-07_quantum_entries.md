# 2026-10-07: Quantum-vs-classical entries (agent report)

Scope: extend the quantum-vs-classical part of the dataset, recording the evidence honestly and keeping proven
(oracle/query model), conjectured, contested and dequantized cases distinct.
Environment: Windows 11 Pro 10.0.26200, CPython (repo `.venv`), run on 2026-10-06/07 local time.
Provenance labels follow RESEARCH_LOG.md: *experiment* means a deterministic script in `experiments/`, and
*external* means a public API or web page.

## 0. Summary

| Entry | Tag | Level | Classical | Quantum | Measured (V2) |
|---|---|---|---|---|---|
| `pairs/deutsch-jozsa-classical-vs-quantum` | T9 | V2 | exact deterministic **2ⁿ⁻¹+1** (worst case); randomized bounded-error **20** (O(1)) | **1**, exact | α = 1.000; constant-cost max/min 1.000 and 1.000 |
| `pairs/collision-problem-classical-vs-quantum` | T9 | V2 | Θ(√N) (birthday) | Θ(N^⅓) (BHT), two variants | α = 1.003 / 1.021 / 1.164 |
| `pairs/minimum-finding-classical-vs-quantum` | T9 | V2 | exactly N | O(√N) bounded error (Dürr–Høyer) | α = 1.000 / 0.886 |
| `staging/element-distinctness-quantum-walk` | T9 | V0 | Θ(N) queries | Θ(N^⅔) (Ambainis walk; Aaronson–Shi lower bound) | n/a |
| `staging/forrelation` | T9 | V0 | Ω(√N / log N), O(√N) | 1 query (bounded error) | n/a |
| `staging/linear-systems-hhl` | **T6** | V0 | O(N√κ) | poly(log N, κ) under strong input assumptions | n/a |

Other results:
- *Reusable machinery.* Two primitives were added to `lib/qsim.py` without changing existing behaviour. A new module,
  `lib/qsearch.py`, provides known-count Grover search, BBHT exponential search with an optional time-out, and
  **exact** expected-cost calculators. A new test file, `tests/test_qsim.py`, has 18 tests.
- *Existing T9 entries.* Query counts are **identical** before and after (section 4).
- *Tests.* The full suite passes: 84 tests, including tests other agents added tonight.
- *Validation.* `tools/validate.py --scaling -v` passes for all six new entries.
- *Sources.* `tools/check_sources.py` on the six new entries found 1 problem (an arXiv-year mismatch) in 31
  identifiers; after the fix, the affected entry re-checked with 0 problems (section 5).

**One real bug was caught by the theory-vs-simulation comparison.** The first BHT implementation stopped querying the
classical set K at the first internal collision. Its query counts were systematically below the exact formula, and
it was fixed (section 3.2).

## 1. Files added or changed

- **Changed:** `lib/qsim.py`. Added `State.uniform` and `Oracle.apply_phase_where`; existing code untouched.
- **New library and tests:** `lib/qsearch.py`, `tests/test_qsim.py`.
- **New pairs entries**, each with `entry.json`, hand-written `README.md`, `harness.py` and `implementations/`:
  - `pairs/deutsch-jozsa-classical-vs-quantum/`: implementations `classical.py`, `randomized.py`, `quantum.py`;
  - `pairs/collision-problem-classical-vs-quantum/`: implementations `classical.py`, `bht.py`;
  - `pairs/minimum-finding-classical-vs-quantum/`: implementations `classical.py`, `durr_hoyer.py`.
- **New staging entries** (`entry.json` + `README.md`): `staging/element-distinctness-quantum-walk/`,
  `staging/forrelation/`, `staging/linear-systems-hhl/`. The READMEs were generated with
  `tools/build_index.entry_readme`, so they have the same style and marker as the other staging READMEs; `index.json`
  was not touched.
- **Experiments**, all deterministic except the source check:
  - `experiments/2026-10-07_deutsch_jozsa_checks.py`
  - `experiments/2026-10-07_deutsch_jozsa_followup_n8.py`
  - `experiments/2026-10-07_collision_expected_queries.py`
  - `experiments/2026-10-07_collision_classical_n8_followup.py`
  - `experiments/2026-10-07_minimum_finding.py`
  - `experiments/2026-10-07_qsearch_expected_cost.py`
  - `experiments/2026-10-07_source_checks.py` (network; external provenance)
- **Stale, not touched (by rule):** `index.json` and the README pairs table.

## 2. Reusable machinery

**Additions to `lib/qsim.py`:**
- **`State.uniform(n)`** writes down H⊗ⁿ|0⟩ directly. A test checks that it equals `State(n)` followed by `h_all()`.
- **`Oracle.apply_phase_where(state, predicate)`** applies |x⟩ → (−1)^[predicate(x, f(x))]|x⟩ and charges **two
  queries**: U_f to compute f(x), a query-free phase flip, and U_f again to uncompute. This is the honest cost of
  searching for a property of a *non-Boolean* oracle value (BBHT 1998, sections 3.1 and 7: one Grover iteration
  "requires two table look-ups (including one for uncomputation purposes)"). The existing `apply_phase` stays at one
  query, because there f is Boolean (phase kickback).

**`lib/qsearch.py`:**
- `search_known_count(n, phase, check, t, rng)` runs ⌊π/(4θ)⌋ iterations with sin²θ = t/N, then measures and checks,
  repeating on failure. It is Las Vegas, and the failure probability per attempt is ≤ t/N (BBHT section 3).
- `exponential_search(n, phase, check, rng, budget=None)` is BBHT section 4: m = 1, λ = 6/5, j uniform in
  {0..⌈m⌉−1}, then m ← min(λm, √N). The optional iteration budget implements Dürr–Høyer's time-out; on
  interruption the current state is measured and checked.
- `expected_cost_known(N, t, q_iter, q_check)` and `expected_cost_exponential(...)` give the **exact** expected
  number of queries for the precise schedules implemented. Once m saturates at √N, the infinite tail is summed in
  closed form.
- `bbht_lemma2` (closed-form success probability) and `bbht_theorem3_bound` ((9/2)·m0) are provided for tests.

The callers supply `phase(state)` and `check(x)`, each charging its own queries. A new amplitude-amplification entry
therefore needs only a predicate and a harness, and it gets an exact expected count for free. That expected count is
what made the bug in section 3.2 visible.

**Validation of the machinery** (tests and experiment):
- *Unit tests* (`tests/test_qsim.py`, 18):
  - norm preservation under H, the diffusion operator and both phase oracles;
  - the Hadamard involution (single qubit and H⊗ⁿ);
  - diffusion equals H⊗ⁿ(2|0⟩⟨0|−I)H⊗ⁿ applied literally;
  - `measure_all` collapse and statistics;
  - query counting (1 / 1 / 2 / 1 for a classical call, `apply_phase`, `apply_phase_where` and
    `apply_xor_and_measure_output`);
  - deferred-measurement collapse: exact renormalised amplitudes on f⁻¹(v) over 200 random states, and P(v) = 2/N
    statistics;
  - Bernstein–Vazirani exact for every s, n ≤ 6;
  - Grover success probability = sin²((2j+1)θ) at every step;
  - BBHT Lemma 2 closed form equal to the direct average;
  - known-count failure ≤ t/N on a grid;
  - exact exponential-search expectation ≤ the Theorem 3 bound;
  - simulated means equal to the exact expectations (|z| < 4, 3000 runs each);
  - budget interruption.
- *Experiment* (`experiments/2026-10-07_qsearch_expected_cost.py`): 25 (N, t) settings with 8000–20000 runs each.
  - Known count: 11 z-scores, combined −0.57, max |z| = 2.96 (N = 64, t = 2; mean 9.0036 vs exact 9.0074, with a
    tiny s.e. of 0.0013 because the count is almost deterministic).
  - Exponential search: 14 z-scores, combined +0.24, max |z| = 1.83.
  - Deterministic cases: for t = N/4 (N = 16, t = 4 and N = 64, t = 16) **every** run used exactly 3 queries. This is
    BBHT's "solution found with certainty after a single iteration". For N = 256, t = 1, all 8000 runs used 25 queries
    (exact expectation 25.0013).

## 3. Per-entry results

### 3.1 Deutsch–Jozsa (`pairs/deutsch-jozsa-classical-vs-quantum`, T9, V2)

**Claims, with their exact settings.**
- *Exact setting.* Quantum uses 1 query with zero error (the one-query form, Cleve–Ekert–Macchiavello–Mosca 1998).
  Classically, 2ⁿ⁻¹+1 queries are necessary and sufficient in the worst case for any **always-correct** algorithm.
  - *Adversary argument (given in the entry).* Answer 0 to the first 2ⁿ⁻¹ distinct queries. The constant-0 function
    and the balanced function that is 1 exactly on the unqueried points both stay consistent.
  - *Zero-error randomized.* The same argument forces 2ⁿ⁻¹+1 queries on **every** constant input for zero-error
    randomized (Las Vegas) algorithms.
- *Bounded-error setting.* K random queries err only on balanced inputs, with probability exactly 2¹⁻ᴷ; the
  implementation uses K = 20. This is O(1), so there is **no** asymptotic separation. The entry says so in its
  title, a boxed note in the README, `relationship` and `caveats`.

**What "worst case" means for a fixed deterministic query order.** For the order 0, 1, 2, …, the algorithm makes
exactly 2ⁿ⁻¹+1 queries on precisely four promise inputs: the two constants and f(x) = c ⊕ (top bit of x). These four
are what `generate_scaling` draws. An exhaustive check over **all** promise inputs for n = 1..4 (4, 8, 72 and 12872
functions) confirmed that the maximum is 2ⁿ⁻¹+1 = 2, 3, 5, 9, attained on exactly those 4 inputs, with 0 wrong
answers. A different fixed order has different worst-case inputs, but by the adversary argument every order has some.

**V2** (`validate.py --scaling`):

| Algorithm | Fit | Measured counts |
|---|---|---|
| Deterministic, worst-case inputs | α = 1.000 vs 2^(n−1)+1 | 3, 9, 33, 129, 513, 2049, 8193, 32769 for n = 2..16 (step 2) |
| Randomized | max/min = 1.000 | 20 at every n |
| Quantum | max/min = 1.000 | 1 at every n |

Samples: on the worst-case inputs the deterministic count is exact, so one instance per n suffices. The other two
counts are constant by construction.

**Theory vs simulation** (`experiments/2026-10-07_deutsch_jozsa_checks.py`):
- *Quantum exactness.* Max |1 − P(0)| over constant functions is 3.1e-15, and max P(0) over balanced functions is
  3.9e-34 (exhaustive for n ≤ 4, plus 50 random balanced functions per n for n = 5..10).
- *Randomized error rate vs 2¹⁻ᵏ* (20000 balanced instances each):

| k | error rate | 2¹⁻ᵏ | z |
|---|---|---|---|
| 1 | 1.00000 | 1 | n/a |
| 2 | 0.50140 | 0.5 | +0.40 |
| 3 | 0.24700 | 0.25 | −0.98 |
| 4 | 0.12700 | 0.125 | +0.86 |
| 6 | 0.03100 | 0.03125 | −0.20 |
| 8 | 0.00780 | 0.00781 | −0.02 |

  Constant functions were misclassified 0 times.
- *Deterministic algorithm on random balanced f vs the exact 1 + N/(N/2+1):*

| n | mean ± s.e. | exact | z |
|---|---|---|---|
| 2 | 2.3338 ± 0.0033 | 2.3333 | +0.12 |
| 4 | 2.7801 ± 0.0074 | 2.7778 | +0.31 |
| 6 | 2.9419 ± 0.0094 | 2.9394 | +0.27 |
| **8** | **2.9617 ± 0.0097** | **2.9845** | **−2.37** |
| 10 | 3.0278 ± 0.0232 | 2.9961 | +1.36 |
| 12 | 2.9980 ± 0.0221 | 2.9990 | −0.05 |

  The n = 8 value is kept as recorded. A pre-declared replication with a fresh seed and 200000 instances
  (`..._deutsch_jozsa_followup_n8.py`) gave 2.9865 ± 0.0031, z = **+0.65**, so the −2.37 was chance (11 z-scores
  in the script; P(max |z| ≥ 2.37) ≈ 18%).

**Sources.** Deutsch & Jozsa 1992 (doi:10.1098/rspa.1992.0167) and Cleve et al. 1998 (doi:10.1098/rspa.1998.0164;
arXiv quant-ph/9708016) were both verified, including volume, issue and pages. The DJ 1992 text could not be
accessed (royalsocietypublishing.org returned 403). "Original algorithm used two queries; one-query form by Cleve et
al." is therefore attributed per a secondary source (the Wikipedia article, which cites both papers), and the entry
says so. The lower bound is proven in the entry and does not rest on that attribution.

### 3.2 Collision problem (`pairs/collision-problem-classical-vs-quantum`, T9, V2)

**Claims.**
- *Classical randomized: Θ(√N).* On a uniformly random 2-to-1 function, after i collision-free queries *any* next
  query completes a pair with probability **exactly** i/(N−i). This was derived for the entry and agrees with the
  closed form C(N/2,q)·2^q / C(N,q). Hence P(success with q queries) ≤ q²/(2(N−q)) + 1/(N−q−1), and Yao's principle
  gives Ω(√N).
- *Classical deterministic exact:* N/2+1 in the worst case.
- *Quantum:*
  - lower bound Ω(N^⅓): Aaronson & Shi 2004. Their proof needs a codomain of size ≥ 3N/2, as stated by Kutin 2005;
    the harness uses a codomain of size 2N. Kutin 2005 and Ambainis 2005 remove the condition;
  - upper bound O(N^⅓): Brassard–Høyer–Tapp.

**Relation to Simon's problem (stated precisely in the entry).** Simon's functions are exactly the 2-to-1 functions
whose pairs are the cosets {x, x⊕s}. On them, finding a collision and finding s are equivalent (s = a⊕b, and {0, s}
is a collision); the BHT arXiv note makes this remark.
- *With the XOR structure:* O(n) = O(log N) quantum queries (exponential speedup).
- *Without it:* Θ(N^⅓) (polynomial speedup, proven optimal).
- *Classically:* both are Θ(√N).

**Implementations.**
- *Classical birthday:* random order until a value repeats.
- *`collision_bht`:* K = {0..k−1} with k = round(N^⅓) (BHT: "an arbitrary subset"). It uses Grover with the **known**
  count t = k, which is what BHT do for r-to-1 functions.
- *`collision_bht_exponential`:* random K plus BBHT exponential search, which BHT prescribe for functions that are
  not exactly r-to-1. This was the requested unknown-t version.

Every Grover iteration costs 2 queries and every measured candidate 1 query. BHT's proof counts one evaluation of F
per evaluation of the marking function H; see decision D1.

**A bug caught by theory vs simulation (two runs, both kept).**

| Run | classical, n = 4, 6, 8, 10, 12, 14, 16 | BHT known t, n = 3, 6, 9, 12, 15 | BHT exponential, n = 3, 6, 9, 12, 15 |
|---|---|---|---|
| 1 (early exit inside K) | −0.92, +1.05, **+3.19**, +0.15, −2.12, +0.27, +0.49 | +0.57, −1.97, **−2.73**, −1.61, −1.56 | +0.99, +0.95, +0.32, +0.46, −1.00 |
| 2 (BHT step order) | identical (same seeds, unchanged code) | +0.57, −0.57, −0.87, −0.41, −1.31 | +0.99, +1.71, +0.81, +0.76, −0.96 |

The table shows z-scores of the empirical mean against the exact expectation.
- *Run 1, cause.* The known-t means were systematically low. The code stopped querying K at the first collision found
  inside K, while the exact formula (and BHT's steps 1–3) query all k points first.
- *Fix.* `bht.py` now queries all of K, then checks. The formula was not changed.
- *Run 2 means* (exact in brackets):

| n | BHT known t | BHT exponential |
|---|---|---|
| 3 | 4.5808 ± 0.0164 (4.5714) | 5.0485 ± 0.0397 (5.0092) |
| 6 | 10.5712 ± 0.0395 (10.5939) | 11.0813 ± 0.0870 (10.9326) |
| 9 | 20.2980 ± 0.0485 (20.3403) | 25.7533 ± 0.2164 (25.5790) |
| 12 | 40.2375 ± 0.0962 (40.2768) | 57.2065 ± 0.5917 (56.7587) |
| 15 | 81.6400 ± 0.4752 (82.2602) | 117.1500 ± 3.1143 (120.1352) |

  Samples were 4000, 4000, 4000, 2000 and 300 runs for n = 3, 6, 9, 12, 15. The run-2 combined z is −1.16 for known
  t and +1.48 for the exponential variant.
- *Exponential variant.* Its four positive z-scores in run 2 led to the separate high-precision check of the search
  itself (section 2: combined +0.24 over 14 settings). The positive run was chance.
- *Classical n = 8.* z = +3.19 with unchanged code, then a pre-declared replication with fresh seeds and 40000
  instances gave 20.1704 ± 0.0478 vs 20.0726, z = **+2.05**. That called for a decisive follow-up
  (`..._collision_classical_n8_followup.py`):
  - exact rational E[Q] = 20.072619, sd 9.5403;
  - an independent sampler bypassing harness, Oracle and implementation: 10⁶ samples, 20.0636 ± 0.0095,
    z = **−0.95**, χ² = 50.1 on 60 d.o.f.;
  - the full pipeline with 200000 fresh instances: 20.0824 ± 0.0214, z = **+0.46**, χ² = 47.5 on 55 d.o.f.

  Verdict: chance. There is no bias in the formula or the pipeline.

**V2 and sample-size justification.** Delta method: Var(α) = Σ wᵢ² (sdᵢ / (meanᵢ·√S))², using the per-n spread
measured in run 2.

| Algorithm | Cost | n | Samples | α (exact expectations) | predicted s.e. | α (validator) | z |
|---|---|---|---|---|---|---|---|
| classical birthday | 2^(n/2) | 4..16 step 2 | 100 | 0.997 | 0.012 | **1.003** | +0.5 |
| BHT, known t | 2^(n/3) | 3..15 step 3 | 40 | 1.027 | 0.013 | **1.021** | −0.46 |
| BHT, exponential | 2^(n/3) | 3..15 step 3 | 100 | 1.154 | 0.022 | **1.164** | +0.45 |

Validator counts:
- classical: 4.83, 9.8, 19.61, 40.43, 83.7, 150.4, 317.5;
- known t: 4.55, 11, 20.68, 39.12, 83;
- exponential: 4.69, 10.21, 27.1, 51.84, 117.6.

**Exact large-n behaviour** (no simulation; Part C of the experiment). E(n)/N^⅓ for the exponential variant rises:

| n | 3 | 6 | 9 | 12 | 15 | 18 | 21 | 24 | 27 | 30 |
|---|---|---|---|---|---|---|---|---|---|---|
| E(n)/N^⅓ | 2.505 | 2.733 | 3.197 | 3.547 | 3.754 | 3.845 | 3.878 | 3.892 | 3.896 | 3.896 |

The exact slope is 1.154 over n = 3..15 but **1.009 over n = 15..30**. For known t the ratio sits at about 2.57
(slope 1.000 over 15..30). The classical E/√N converges to 1.2533 = √(π/2). The 1.164 in V2 is therefore
pre-asymptotic, not a wrong exponent.

**V1.** The problem is a **relation** (N/2 valid answers), so `harness.equal` returns True and correctness rests on
`check()` against the instance. This is documented in the harness and in `verification.method`.

**Sources.** All verified:
- BHT LATIN '98, doi:10.1007/BFb0054319 (Crossref title "Quantum cryptanalysis of hash and claw-free functions", pp.
  163–169);
- the BHT arXiv note quant-ph/9705002, listed as a separate source because its title differs, which would otherwise
  trip the title check;
- BBHT, doi:10.1002/(SICI)1521-3978(199806)46:4/5<493::AID-PROP493>3.0.CO;2-P. It was found by Crossref
  bibliographic search, and vol 46, issue 4-5, pp. 493–505 verified;
- Aaronson & Shi, doi:10.1145/1008731.1008735 (51(4), 595–605);
- Kutin 2005, doi:10.4086/toc.2005.v001a002 (1, 29–36);
- Ambainis 2005, doi:10.4086/toc.2005.v001a003 (1, 37–46);
- Simon 1997.

For the two Theory of Computing DOIs, Crossref has no title. Titles were confirmed on theoryofcomputing.org, and
`check_sources.py` accepts them through its year/volume/page fallback.

### 3.3 Minimum finding (`pairs/minimum-finding-classical-vs-quantum`, T9, V2)

**Claims.**
- *Classical:* exactly N queries for exact algorithms. Ω(N) holds even with bounded error, by reduction from
  unstructured search: T[x] = 0 if x is marked, else x+1, which gives distinct values at one search query per probe.
- *Quantum:* O(√N) with bounded error (Dürr–Høyer), and Ω(√N) by the same reduction plus BBBV 1997.
- *Summary:* a quadratic separation, tight.

**Implementation.** Dürr–Høyer is implemented **literally**:
- random initial threshold;
- repeated BBHT searches for "T[j] < T[y]";
- time-out 22.5√N + 1.4 lg²N in the paper's time units (lg N per initialisation, 1 per Grover iteration, stages 1,
  2(c) and 3 free). This makes Theorem 1 (success ≥ 1/2) apply as written.

Queries are counted separately: 1 for T[y], 2 per Grover iteration, and 1 per observed candidate.

**Theory vs simulation** (`experiments/2026-10-07_minimum_finding.py`).
- **A. The paper's "infinite algorithm"**, run until the threshold holds the minimum. Exact expectations come from
  Lemma 1 (rank r is ever chosen with probability 1/r) and the exact BBHT costs.

| n | runs | time: mean (exact) | z | queries: mean (exact) | z | Lemma-2 bound m0 | exact/m0 |
|---|---|---|---|---|---|---|---|
| 2 | 4000 | 2.72 (2.72) | +0.23 | 4.33 (4.28) | +0.80 | 25.30 | 0.107 |
| 4 | 4000 | 11.54 (11.64) | −1.01 | 11.10 (11.19) | −0.69 | 56.20 | 0.207 |
| 6 | 3000 | 29.19 (29.30) | −0.45 | 27.66 (27.39) | +0.83 | 115.20 | 0.254 |
| 8 | 2000 | 60.67 (60.87) | −0.34 | 64.17 (64.45) | −0.33 | 224.80 | 0.271 |
| 10 | 1000 | 118.07 (117.32) | +0.50 | 145.40 (145.15) | +0.10 | 430.00 | 0.273 |

  The paper's bound is loose by a factor of 3.7 to 9.3.
- **B. The published algorithm.** 0 failures in 14000 runs. One-sided 95% upper bounds on the failure rate:

| n | runs | 95% upper bound on failure rate | mean queries (sd) | classical N |
|---|---|---|---|---|
| 2 | 4000 | 0.075% | 188.47 (11.37) | 4 |
| 4 | 4000 | 0.075% | 273.58 (13.18) | 16 |
| 6 | 3000 | 0.10% | 481.10 (20.19) | 64 |
| 8 | 2000 | 0.15% | 888.29 (28.33) | 256 |
| 10 | 1000 | 0.30% | 1674.40 (38.87) | 1024 |

- **C. Crossover with the classical N:** n = 11: 2297.9 vs 2048 (ratio 1.122); n = 12: 3189.1 vs 4096 (0.779);
  n = 13: 4468.7 vs 8192 (0.545); 0 failures. The quantum count falls below N only between **N = 2048 and N = 4096**.

**V2.**
- *Classical:* α = 1.000 against 2ⁿ (exactly N).
- *Dürr–Høyer:* α = **0.886** against 2^(n/2) over n = 4..12, with 5 samples. The predicted value from the part B/C
  means is 0.889. The count is nearly fixed by the time-out (sd/mean ≤ 4.8% for n ≥ 4), and the predicted s.e. of α
  with 5 samples is < 0.01.
- *Same fit over n = 2..10:* **0.800** (near-miss; section 6).

**Sources.**
- Dürr & Høyer, arXiv quant-ph/9607014. The title was verified via the arXiv API, and the algorithm, the time-out,
  Lemma 1/2 and Theorem 1 were read in the v2 PDF.
- BBHT: the algorithm and Theorem 3 were read in the arXiv v1 PDF, which the entry notes.
- BBBV 1997 (already in the repo).

### 3.4 Staging entries (V0, cited only)

- **`staging/element-distinctness-quantum-walk`** (T9).
  - *Classical:* Ω(N) randomized, by an elementary reduction from OR on N−1 bits, given in the entry.
  - *Quantum:* Θ(N^⅔). The upper bound is Ambainis 2007 (doi:10.1137/S0097539705447311, SIAM J. Comput. 37(1),
    210–239, verified). The lower bound is Aaronson–Shi 2004; Ambainis 2005 covers small ranges.
  - *Notes.* The query bound was quoted from the arXiv abstract. The arXiv id moved into a `note` because its year
    (2003) differs from the journal's (2007) by more than the checker's 3-year slack. The entry cross-references the
    classical-time pair `pairs/element-distinctness-pairs-vs-sorting`, which another agent added tonight.
- **`staging/forrelation`** (T9).
  - *Claims.* 1 quantum query vs Ω(√N/log N) randomized classical queries, with the O(√N) classical upper bound
    obtained from the paper's simulation theorem. The paper also proves this gap optimal for one-query algorithms.
    All of this was verified against the arXiv abstract 1411.5729; the DOI was already verified.
  - *Raz–Tal.* Stated exactly as their ECCC abstract says: one quantum query, advantage Ω(1/log N), versus at most
    polylog(N)/√N for quasi-polynomial constant-depth circuits, yielding an oracle with BQP ⊄ PH. Both DOIs verified.
  - *Withheld:* the claim that "the Raz–Tal distribution is a variant of Forrelation" (the abstract does not say it),
    and Forrelation's explicit thresholds (not verified).
- **`staging/linear-systems-hhl`** (**T6**, justified in `relationship`; decision D12).
  - *Classical:* O(N√κ), as stated in the HHL abstract.
  - *Quantum:* poly(log N, κ).
  - *Conditional barrier.* HHL's universality result (as summarised by Aaronson 2015) means that a classical
    poly(log N, κ, 1/ε) algorithm for the general sparse case would imply BQP = BPP. This is recorded in
    `lower_bounds` with setting **CONDITIONAL**.
  - *Caveats.* Aaronson's four caveats are quoted from the author's preprint of the Nature Physics article: loading
    |b⟩; applying e^{−iAt}; κ; and the output being a state rather than x. So are "extremely artificial" instances
    and the passive-QRAM remark.
  - *Low-rank dequantization:* Chia–Lin–Wang 2018 (O(poly(k, κ, ‖A‖_F, 1/ε)·polylog(m, n))), Gilyén–Lloyd–Tang 2018,
    and Chia et al. 2022 ("low-rank regression"). All are arXiv-verified, and Chia et al. is DOI-verified.

## 4. Existing T9 entries: before and after the `lib/qsim.py` change

Command: `./.venv/Scripts/python tools/validate.py pairs/bernstein-vazirani-classical-vs-quantum pairs/grover-search-classical-vs-quantum pairs/simon-classical-vs-quantum --scaling -v`

**Before** (qsim.py md5 a5e5d313d0fd5cf89a70531416e3927c):
```
      V2 classical: query the unit vectors [reported]: cost=n  alpha=1.000 (tol 0.25)  ok  [0.0s]  n=2: 2, n=4: 4, n=8: 8, n=12: 12, n=16: 16
      V2 Bernstein-Vazirani quantum algorithm [reported]: cost=1  constant cost: max/min = 1.000 (tol 0.01)  ok  [0.0s]  n=1: 1, n=2: 1, n=4: 1, n=6: 1, n=8: 1, n=10: 1
[OK] pairs\bernstein-vazirani-classical-vs-quantum  claimed V2
      V2 classical random-order search [reported]: cost=2**n  alpha=0.992 (tol 0.25)  ok  [0.1s]  n=2: 2.275, n=4: 8.025, n=6: 28.1, n=8: 133.8, n=10: 491.9, n=12: 2205, n=14: 7817
      V2 Grover's algorithm [reported]: cost=2**(n/2)  alpha=0.924 (tol 0.25)  ok  [0.1s]  n=2: 2, n=4: 4, n=6: 7, n=8: 13, n=10: 26, n=12: 51
[OK] pairs\grover-search-classical-vs-quantum  claimed V2
      V2 classical collision search [reported]: cost=2**(n/2)  alpha=0.993 (tol 0.25)  ok  [1.0s]  n=4: 5.275, n=6: 10.32, n=8: 19.55, n=10: 40.85, n=12: 84.08, n=14: 165.1, n=16: 314.5
      V2 Simon's quantum algorithm [reported]: cost=n  alpha=1.121 (tol 0.25)  ok  [0.9s]  n=2: 1.65, n=3: 3.425, n=4: 4.525, n=6: 6.875, n=8: 8.825, n=10: 10.82
[OK] pairs\simon-classical-vs-quantum  claimed V2

3/3 entries OK
```

**After** (final qsim.py md5 b794ae64aa92cb4a42115e1113dbd301; run at the end of the session):
```
      V2 classical: query the unit vectors [reported]: cost=n  alpha=1.000 (tol 0.25)  ok  [0.0s]  n=2: 2, n=4: 4, n=8: 8, n=12: 12, n=16: 16
      V2 Bernstein-Vazirani quantum algorithm [reported]: cost=1  constant cost: max/min = 1.000 (tol 0.01)  ok  [0.0s]  n=1: 1, n=2: 1, n=4: 1, n=6: 1, n=8: 1, n=10: 1
[OK] pairs\bernstein-vazirani-classical-vs-quantum  claimed V2
      V2 classical random-order search [reported]: cost=2**n  alpha=0.992 (tol 0.25)  ok  [0.1s]  n=2: 2.275, n=4: 8.025, n=6: 28.1, n=8: 133.8, n=10: 491.9, n=12: 2205, n=14: 7817
      V2 Grover's algorithm [reported]: cost=2**(n/2)  alpha=0.924 (tol 0.25)  ok  [0.1s]  n=2: 2, n=4: 4, n=6: 7, n=8: 13, n=10: 26, n=12: 51
[OK] pairs\grover-search-classical-vs-quantum  claimed V2
      V2 classical collision search [reported]: cost=2**(n/2)  alpha=0.993 (tol 0.25)  ok  [1.0s]  n=4: 5.275, n=6: 10.32, n=8: 19.55, n=10: 40.85, n=12: 84.08, n=14: 165.1, n=16: 314.5
      V2 Simon's quantum algorithm [reported]: cost=n  alpha=1.121 (tol 0.25)  ok  [0.9s]  n=2: 1.65, n=3: 3.425, n=4: 4.525, n=6: 6.875, n=8: 8.825, n=10: 10.82
[OK] pairs\simon-classical-vs-quantum  claimed V2

3/3 entries OK
```
A `diff` of the two outputs, with the wall-clock `[x.xs]` fields stripped, is empty: **identical query counts and
α values**. An intermediate "after" run, made right after the qsim change, was also identical.

## 5. Sources: verified and dropped

**DOIs verified against Crossref** (title, year, volume, issue and pages), with `experiments/2026-10-07_source_checks.py`
and then `tools/check_sources.py` on the six new entries. That run checked 31 identifiers, 20 also on volume/issue/pages,
and found 1 problem, fixed below. After the fix, the affected entry was re-checked with 0 problems; the other five
were not re-run, to avoid a further arXiv request.

| Source | DOI | Registered details |
|---|---|---|
| Deutsch & Jozsa 1992 | 10.1098/rspa.1992.0167 | 439(1907), 553–558 |
| Cleve, Ekert, Macchiavello & Mosca 1998 | 10.1098/rspa.1998.0164 | 454(1969), 339–354 |
| Brassard, Høyer & Tapp 1998 (LATIN) | 10.1007/BFb0054319 | pp. 163–169 |
| Aaronson & Shi 2004 | 10.1145/1008731.1008735 | 51(4), 595–605 |
| Ambainis 2007 | 10.1137/S0097539705447311 | 37(1), 210–239 |
| Aaronson & Ambainis 2015 | 10.1145/2746539.2746547 | pp. 307–316 |
| Harrow, Hassidim & Lloyd 2009 | 10.1103/PhysRevLett.103.150502 | 103(15) |
| Aaronson 2015 | 10.1038/nphys3272 | 11(4), 291–293 |
| Chia et al. 2022 | 10.1145/3549524 | 69(5) |
| Raz & Tal 2019 | 10.1145/3313276.3316315 | pp. 13–23 |
| Raz & Tal 2022 | 10.1145/3530258 | 69(4), 1–21 |
| Kutin 2005 | 10.4086/toc.2005.v001a002 | 1, 29–36; Crossref has no title, confirmed on the journal site |
| Ambainis 2005 | 10.4086/toc.2005.v001a003 | 1, 37–46; Crossref has no title, confirmed on the journal site |
| Boyer, Brassard, Høyer & Tapp 1998 | 10.1002/(SICI)1521-3978(199806)46:4/5<493::AID-PROP493>3.0.CO;2-P | 46(4-5), 493–505 |
| Bennett, Bernstein, Brassard & Vazirani 1997 | (already in repo) | |
| Simon 1997 | (already in repo) | |
| Grover 1996 | (already in repo) | |
| Beals, Buhrman, Cleve, Mosca & de Wolf 2001 | 10.1145/502090.502097 | 48(4), 778–797; verified for section 8 only, not cited in an entry |

**arXiv ids verified through the API** (title and year): quant-ph/9607014, quant-ph/9705002, quant-ph/9605034,
quant-ph/9708016, quant-ph/0311001, quant-ph/0111102, quant-ph/0112086, 1411.5729, 0811.3171, 1910.06151,
1811.04909, 1811.04852.

**External accesses.**
- arXiv: 3 API calls (two batched abstract queries plus one batch inside `check_sources.py`) and 3 PDF downloads
  (Dürr–Høyer, BBHT and BHT, to read exact algorithm statements and constants).
- Web: theoryofcomputing.org (2 pages), the ECCC TR18-107 abstract, Aaronson's preprint PDF, and Wikipedia (DJ
  article, a secondary source). royalsocietypublishing.org returned 403.

**Fixed.** The Ambainis 2007 arXiv year (2003) exceeded the checker's 3-year slack, so the arXiv id moved to `note`.

**Dropped as unverifiable** (deliberately not stated):
- DJ 1992's exact original formulation;
- the LNCS volume number of LATIN '98 (Crossref holds none);
- Forrelation's numeric thresholds;
- "Raz–Tal uses a Forrelation variant";
- Ambainis's running-time bound;
- HHL's exact s and ε dependence (only the abstract statement plus Aaronson's rough summary log(N)·κ·s/ε);
- "minimum finding is a building block of many algorithms".

**No candidate DOI failed.**

## 6. Near-misses (with numbers)

1. **Dürr–Høyer fit near the tolerance edge.** α = 0.800 against 2^(n/2) over n = 2..10 (from 1000–4000 runs per
   n), 0.05 inside the 0.25 band. The cause is explicit lower-order terms: the 1.4 lg²N term of the time-out, and
   about 75–100 classical candidate checks per run (at N = 4 a run uses 188 queries). Over n = 4..12, α = 0.886.
   Both values are in the entry.
2. **BHT with exponential search: α = 1.164** (exact 1.154), 0.09 from the edge. It is pre-asymptotic: the exact
   slope over n = 15..30 is 1.009.
3. **Quantum count above classical at all V1/V2 sizes for minimum finding.**

   | N | 4 | 16 | 64 | 256 | 1024 | 2048 | 4096 | 8192 |
   |---|---|---|---|---|---|---|---|---|
   | quantum / classical | 47× | 17× | 7.5× | 3.5× | 1.64× | 1.12× | 0.78× | 0.55× |

   The asymptotic separation is real, but with the published constants the crossover lies between N = 2048 and 4096.
4. **Deutsch–Jozsa separates only from exact classical algorithms.** With error 2⁻¹⁹ a classical algorithm uses 20
   queries at every n; with error ε it uses about log₂(2/ε). The exponential gap is 1 vs 2ⁿ⁻¹+1 in the exact
   setting only.
5. **Constant factors from query accounting.** Two queries per Grover iteration doubles the quantum constant
   relative to BHT's and Dürr–Høyer's own accounting. Exponents are unaffected.
6. **Empirical vs theory:**
   - BHT known t, run 1: z = −2.73 at n = 9, and four of five values negative. This was **real** (early exit) and fixed.
   - Classical collision n = 8: z = +3.19, then +2.05 in the replication. Resolved as chance by an exact rational
     check, a 10⁶-sample independent sampler (z = −0.95) and 200000 pipeline instances (z = +0.46).
   - DJ n = 8: z = −2.37. Resolved by replication (z = +0.65).
   - qsearch N = 64, t = 2: z = −2.96. A single setting; the combined z over 11 known-count settings is −0.57.
7. **Paper bounds are loose.** The exact expected time of Dürr–Høyer's infinite algorithm is 10.7%–27.3% of the
   Lemma 2 bound m0. Their time-out (2·m0) is therefore generous, which is consistent with 0 observed failures.

## 7. Decision log

- **D1. Two queries per Grover iteration for value-derived predicates.**
  - *Evidence:* BBHT sections 3.1 and 7 state two table look-ups per iteration because of uncomputation.
  - *Alternative:* BHT's own count (one evaluation of F per evaluation of H). It was rejected as less strict; the
    entry states the difference.
  - *Unaffected:* the existing Grover entry keeps one query per iteration, because its f is Boolean.
- **D2. Minimal additions to `qsim.py`, with the algorithms in a new `lib/qsearch.py`.** This keeps the measuring
  instrument small and leaves its existing behaviour bit-for-bit unchanged (section 4). Alternative: put everything in
  qsim.py, which would increase the risk to existing counts.
- **D3. Two BHT implementations.**
  - *Evidence:* BHT's note uses the known-count Grover for 2-to-1 (t = k exactly). It prescribes random K plus the
    generalized (unknown-t) search only for functions that are not exactly r-to-1.
  - *Choice:* implement both. The request was for BBHT; faithfulness to the paper required the known-t version.
- **D4. BHT step order made literal** (all k classical queries before the internal collision check), after the run-1
  discrepancy. Alternative: keep the early exit and change the formula. Rejected, to stay with the paper's algorithm;
  the effect is small, but the exactness check is only meaningful if code and formula describe the same procedure.
- **D5. Collision `equal()` returns True** (a relation problem); `check()` verifies each output. Alternative:
  canonical outputs, which would require changing the problem.
- **D6. Collision codomain of size 2N** (≥ 3N/2), so that the Aaronson–Shi proof applies as originally stated. Kutin
  and Ambainis are cited anyway.
- **D7. DJ includes the bounded-error randomized algorithm as an implemented algorithm.** The entry thus shows the
  O(1) classical cost in its own V1/V2 data rather than only in prose. `lower_bounds` uses model
  `classical-deterministic` (as requested), with the setting spelling out exact, zero-error randomized, and not
  bounded-error.
- **D8. DJ worst-case generator** = the 4 functions maximising the fixed-order algorithm's count, verified by
  exhaustion for n ≤ 4.
- **D9. DJ lower-bound source** is an elementary adversary argument written into the entry, because the 1992 text was
  inaccessible. The attribution of the 2-query original and the 1-query version is marked as coming from a
  secondary source.
- **D10. Dürr–Høyer implemented literally**, with the paper's time-out in the paper's time units, so that Theorem 1
  applies. Queries are counted separately.
  - *Rejected:* a tuned smaller budget (it loses the proven guarantee).
  - *Rejected:* stopping when the minimum is reached (the algorithm cannot know that; it is only used as a diagnostic
    in experiment part A).
- **D11. Dürr–Høyer V2 over n = 4..12** instead of 2..10; both α values are reported. Evidence: lower-order terms
  dominate at N = 4 (188 queries for 4 entries).
- **D12. HHL tagged T6.**
  - *Not T9:* no unconditional lower bound exists; only the conditional BQP = BPP barrier.
  - *Not T5:* dequantization covers low-rank matrices with length-squared sampling access, a different problem and
    input model; no dequantization is known for the sparse full-rank case.
  - *Not "no tag":* the schema requires one, and T6 is the dataset's "unpaired / open" class, as for factoring.
- **D13. Element distinctness and Forrelation are staged at V0 with T9** (proven query separations, not yet
  implemented). Forrelation is implementable (section 8); the quantum walk is heavier.
- **D14. Staging READMEs generated with `tools/build_index.entry_readme`.** This guarantees the generated-README style
  and freshness without running `build_index.py`, which would rewrite `index.json` (forbidden).
- **D15. Sample sizes from the predicted standard error of α** (delta method), not by trial and error. All predicted
  α values matched the validator within 0.5 s.e.
- **D16. No `validate.py --record` run**, because `--record` calls `git` internally and git was not to be run.
- **D17. Large z-scores were never "fixed" by re-seeding.** Every original result is kept, and replications were
  declared before being run, with new seeds and larger samples.

## 8. Open ideas

*Forward-looking content is not published (RL-086).*

## 9. Updated short map of the classical-vs-quantum evidence

**Tier 1, proven relative to an oracle (query model).**

| Problem | Classical | Quantum | Kind of gap | Entry |
|---|---|---|---|---|
| Deutsch–Jozsa | 2ⁿ⁻¹+1 exact; **O(1) bounded error** | 1, exact | exponential **only vs exact classical** | `pairs/deutsch-jozsa-…` (V2) |
| Bernstein–Vazirani | n | 1 | linear | existing (V2) |
| Unstructured search | Θ(N) | Θ(√N) | quadratic, tight (BBBV limit) | existing (V2) |
| Minimum finding | Θ(N) | Θ(√N), bounded error | quadratic, tight; crossover N ≈ 2–4·10³ with published constants | `pairs/minimum-finding-…` (V2) |
| Collision (2-to-1, no structure) | Θ(√N) | Θ(N^⅓) | polynomial, tight | `pairs/collision-problem-…` (V2) |
| Element distinctness | Θ(N) | Θ(N^⅔) | polynomial, tight | `staging/element-distinctness-…` (V0) |
| Simon (2-to-1 **with** XOR structure) | Θ(2^(n/2)) | O(n) | exponential | existing (V2) |
| Forrelation | Ω(√N/log N), O(√N) | 1 | ~√N, proven optimal for 1 query | `staging/forrelation` (V0) |
| Discrete log, generic groups | Ω(√p) | poly(log p) | exponential | existing staging |
| BQP ⊄ PH relative to an oracle | n/a | n/a | n/a | Raz–Tal, cited in `staging/forrelation` |

**Lesson made concrete by this batch:** within the same 2-to-1 promise, the XOR structure turns a polynomial
speedup (collision) into an exponential one (Simon). Without structure, black-box speedups found so far in the
dataset are polynomial and provably capped (search, minimum, collision, element distinctness).

**Tier 2, conjectured.** Factoring and discrete log (existing), plus **HHL linear systems (T6)**. HHL is BQP-complete
(via its universality result), so a classical polylog algorithm for the general sparse case would give BQP = BPP.
Practical instances carry four caveats (input loading, e^{−iAt}, κ, readout) that can each remove the speedup.

**Counter-evidence (dequantization).** Recommendation systems (existing), plus **low-rank linear systems / regression**:
classical poly(k, κ, ‖A‖_F, 1/ε)·polylog(dim) with sampling access (Chia–Lin–Wang; Gilyén–Lloyd–Tang; Chia et al.).
This is recorded inside the HHL entry rather than as a separate T5, because it is a different problem.

**One-line update.** Quantum advantage is proven in black-box models. It is exponential where there is structure
(Simon, discrete log, Forrelation) or where the classical side must be exact (DJ), and only polynomial (√, ⅓, ⅔)
for unstructured tasks. It is conjectured for factoring, discrete log and HHL-type problems, and has evaporated for
low-rank machine-learning and linear-algebra tasks under sampling access.

## 10. Draft RESEARCH_LOG entries (for the maintainer; RESEARCH_LOG.md was not edited)

- **VERIFIED · Deutsch–Jozsa entry (T9, V2).** Measured values: α = 1.000 on worst-case inputs, constant 20 and 1.
  - Worst case 2ⁿ⁻¹+1, by exhaustion for n ≤ 4, attained on exactly 4 inputs.
  - Quantum P(0) exact to 3.1e-15.
  - Randomized error matches 2¹⁻ᵏ (|z| ≤ 0.98).
  - Random-balanced mean matches 1 + N/(N/2+1), with one z = −2.37 replicated to +0.65.
  - Provenance: experiments `2026-10-07_deutsch_jozsa_checks.py` and `_followup_n8.py`.
- **CORRECTED · BHT implementation step order.**
  - Old state: an early exit inside K; known-t z = +0.57, −1.97, −2.73, −1.61, −1.56.
  - Fix: all of K is queried first.
  - New state: z = +0.57, −0.57, −0.87, −0.41, −1.31.
  - Provenance: `experiments/2026-10-07_collision_expected_queries.py`.
- **VERIFIED · Collision entry (T9, V2).** α = 1.003 / 1.021 / 1.164, against predictions from exact expectations of
  0.997 ± 0.012, 1.027 ± 0.013 and 1.154 ± 0.022. The exponential variant is pre-asymptotic (slope 1.009 over
  n = 15..30). Classical n = 8 anomaly (z = +3.19, then +2.05) resolved as chance: exact rational E, independent
  10⁶ sampler z = −0.95, pipeline z = +0.46.
- **VERIFIED · Minimum-finding entry (T9, V2).**
  - Fits: α = 1.000 / 0.886 (n = 4..12); α = 0.800 over n = 2..10 is a near-miss.
  - Infinite-algorithm time and queries match exact expectations within |z| ≤ 1.01.
  - 0/14000 failures under the published time-out.
  - Crossover with classical N between 2048 and 4096.
- **DECISION · Query accounting.** A phase on a predicate of a non-Boolean oracle value costs 2 queries
  (`Oracle.apply_phase_where`; BBHT sections 3.1 and 7). New `lib/qsearch.py` with exact expected costs, and
  `tests/test_qsim.py` (18 tests). Existing T9 counts are identical before and after.
- **DECISION · HHL tagged T6** (not T9, not T5), with the reasons in D12.
- **VERIFIED · Sources for the 2026-10-07 quantum entries.** 31 identifiers; 1 problem (Ambainis 2007 arXiv year vs
  journal year), fixed by moving the arXiv id to `note`; re-check 0 problems.

## 11. For the maintainer

*Forward-looking content is not published (RL-086).*
