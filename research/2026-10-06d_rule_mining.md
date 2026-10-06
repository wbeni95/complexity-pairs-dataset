# Rule mining: speed-up rules as executable templates, mass screening and near-misses (2026-10-06d)

Author: delegated research agent (Claude), for the maintainer.

Status: research report. It adds no entry. Nothing in `pairs/`, `staging/`, `synthetic/`, `tools/`, `schema/`,
`lib/`, `search/`, `mutations/`, `methods/`, `index.json`, `README.md` or `RESEARCH_LOG.md` was changed. No git
command was run. Every output of this round is mechanical: **T7 at most** (generators/README.md). A match with a
named problem is a **pipeline check**, never a novelty claim.

## Provenance labels

| Label | Meaning |
|---|---|
| [mass] | `experiments/2026-10-06d_rules_mass_screen.py` (generator seed 1, screen seed 0), its outputs `candidates/2026-10-06d/<rule>.jsonl` and `summary.json`. Final run: 1920 candidates, wall time 72.0 s, 4 worker processes, below-normal priority. |
| [ana] | `experiments/2026-10-06d_rules_analysis.py` (reads the candidate store only; writes `candidates/2026-10-06d/analysis.json`). |
| [hyp] | `experiments/2026-10-06d_rules_hypotheses.py` (fresh generator seeds 2 and 3, held-out families; writes `candidates/2026-10-06d/hypotheses.json`). Final run: 71.1 s. |
| [doi] | `experiments/2026-10-06d_rules_doi_checks.py`: Crossref title, first author and year, 1 request per 1.2 s, project User-Agent. All 10 DOIs below printed a matching title and year. |
| [console] | seen during development, not machine-recorded. |
| [recalled] | from memory, not checked against the source. |

All counts are **exact instrumented operation counts**: the algorithms reach the data only through counted
primitives (an operation-table oracle, counted ring operations, a membership oracle, counted split evaluations,
counted leaf products). Wherever the specification predicts the count exactly, the harness compares the two
(`counts_equal_spec`): **0 mismatches** in every rule [mass].

---

## 1. Summary (key numbers)

- **7 rules** turned into executable templates, each with a family generator, a slow algorithm and a
  rule-produced fast algorithm: memoisation (+ state compression), transform convolution, repeated squaring,
  matroid greedy, Knuth–Yao monotone splits, bilinear rank reduction (GF(2)), meet in the middle.
- **1920 candidates** generated and screened [mass]: **1161 EXACT, 380 NEAR-MISS, 310 WRONG, 69 INVALID**.
  Deduplication leaves **1138 distinct problems** up to relabelling or equivalence (782 duplicates).
- **EXACT candidates with an exponent fit: 1106.** **1089 resolve the exponent change** (both claims fit, each
  side rejects the other's cost, all declared rivals rejected); the 17 unresolved ones are all memoisation
  candidates and are explained in section 4.1 (pre-asymptotic small-n fits and one harness artefact). The other
  55 EXACT candidates carry no fit (section 3).
- **Stated precondition => EXACT held without exception** (precision 1.000 in all 7 rules [ana]). The stated
  preconditions are often **not necessary**: EXACT without the stated precondition occurred 97 times for repeated
  squaring, 43 for Knuth, 9 for meet in the middle, 5 for greedy, 4 for state compression [ana].
- **Three refined (weaker) preconditions came out of the data and held on fresh seeds and held-out families**
  (IDEA level, section 6):
  1. binary powering is exact **iff** p_a * p_a = p_(2a) for every left power (the "square condition"), which is
     strictly weaker than power-associativity: 900/900 magmas agree, 37 exact magmas are not power-associative [hyp];
  2. memoisation with a compressed key is exact iff the dropped coordinate is a **function of the kept one on the
     reachable states**: 400/400 compress candidates on seed 3 agree, 35 of them exact without the stated
     precondition [hyp];
  3. greedy's worst ratio equals the **rank quotient** (Korte–Hausmann; [DOI OK]); the adversarial construction
     attains it within 0.0005 on 400/400 set systems [hyp].
- **Refuted on held-out data:** "translation-invariant weights w(i, j) = h(j − i) make Knuth exact" (suggested by
  concave h, 600/600 exact) fails for arbitrary h: 157/600 instances exact [hyp].
- **Repairs that turn every near-miss of a cluster exact:** transform + sparse correction (300/300 tables),
  all-solutions lookup for meet in the middle (141/141 interaction-free candidates), boundary conditioning for
  crossing interactions (92/92 additive candidates), left-power cycle detection for any finite magma (900/900).
  Each repair has a measured cost threshold beyond which the gain disappears (section 5).
- **Two errors of mine were found by the checks and corrected** (section 9): the 2-D recurrence growth constant
  (diagonal coefficient only, up to 5.3% too small; corrected rate within 0.29% of the counting DP), and a
  family (`subint_sep`) that was not QI-neutral as intended.

---

## 2. Rule catalogue

Each rule lives in `generators/rules/<module>.py` with a `CATALOGUE` dict (printed by
`python -m generators.rules list`). Builds on research/2026-10-07_patterns.md section 1 (techniques A–F); the
new content here is the executable precondition, the failure mode as a screenable property, and the repair.

| # | Rule (module) | Precondition (checked exactly per candidate) | Transformation | Cost change (counted unit) | Failure mode when the precondition fails |
|---|---|---|---|---|---|
| R1 | memoisation (`memo`) | overlapping subproblems: call tree outgrows distinct states; pure function | cache by argument / evaluate states in topological order | calls: Θ(λⁿ) → Θ(n) (1-D), Θ(λⁿ/√n) or Θ(λⁿ) → Θ(n²) (2-D), Θ(n^p) → Θ(log² n) (divisive) | one child per call: no gain (INVALID) |
| R1c | state compression (`memo`, compress1d) | stated: the dropped flag cannot influence the value (δ = 0 or no move flips it) | memoise on a projection of the state | as R1 | the flag matters: wrong values (WRONG / NEAR-MISS) |
| R2 | transform convolution (`convolution`) | index operation isomorphic to Z₂ᵏ, Z_N, Z_(N/2)×Z₂, Boolean lattice, chain, or saturating addition (verified isomorphism) | relabel, transform, pointwise product, inverse | ring ops: 2N² → Θ(N log N) (chain Θ(N)) | non-structured table: the nearest structure's transform is wrong on the outputs fed by disagreeing entries |
| R3 | repeated squaring (`magma_power`) | stated: associativity | x^e by e − 1 left multiplications → left-to-right square-and-multiply | magma ops: 2ⁿ − 2 → 2(n − 1) for e = 2ⁿ − 1 | bracketings disagree: wrong powers |
| R4 | matroid greedy (`greedy`) | exchange axiom | enumerate feasible sets → sort and add greedily | oracle calls: 2^g → g (sort comparisons not counted) | light maximal set; worst ratio = rank quotient |
| R5 | Knuth–Yao (`knuth`) | quadrangle inequality + monotone on intervals (Yao 1980) | split search restricted to [K(i, j−1), K(i+1, j)] | split evaluations: n(n+1)(n+2)/6 → Θ(n²) | non-monotone splits: too-large cost |
| R6 | bilinear rank (`bilinear`) | GF(2) tensor rank r < support m | r products of linear forms, recursively on tensor powers | leaf products: mᵈ → rᵈ | r = m: best (m−1)-term approximation is wrong; repair costs ≥ 1 product (no gain) |
| R7 | meet in the middle (`mitm`) | group operation (unique completion) and no interaction across the split | enumerate halves, look up the completing value | ops: 2ⁿ − 1 → Θ(2^(n/2)) | non-unique completion undercounts; crossing interactions corrupt half values |

**Rules catalogued but not generated (time box):** subset DP, inclusion–exclusion, augmenting paths with
potentials, randomisation (Schwartz–Zippel / Freivalds). Templates, for later generators:

| Rule | Precondition | Transformation | Cost change | Failure mode |
|---|---|---|---|---|
| subset DP | objective depends on the set of used elements + O(1) boundary, not on their order | DP over (subset, boundary) | n! → 2ⁿ poly(n) | order-dependent objective (e.g. position-dependent weights) breaks the state |
| inclusion–exclusion | covering-type constraint with cheap unconstrained counts on subsets | Σ_X (−1)^(|U∖X|) f(X)^k, f by a zeta transform | |F|^k or 3ⁿ → Θ(n 2ⁿ) | disjointness (partition) instead of covering needs the ranked version; counts mod p can give false zeros |
| augmenting paths + potentials | LP integrality / bipartite structure | shortest augmenting paths with reduced costs | n! → Θ(n³) | odd cycles (general matching) need blossoms |
| randomisation | identity of low degree d over a large field | evaluate at a random point | expansion (exponential) → poly | one-sided error ≤ d/|F|; small fields make it a near-miss |

R2 and R4–R7 are partly covered by research/2026-10-07_patterns.md generator designs G2–G4; the designs there
were not implemented, so nothing here duplicates code. R2 and R3 contain algebraic structures, but only inside
generated families; none of the existing pairs is mirrored or semiring-swapped (that is the parallel mutation
agent's pilot).

---

## 3. Generation and screening statistics [mass]

Verdict rules (`generators/rules/common.py`): EXACT = every screened instance agrees exactly (a screen, not a
proof); NEAR-MISS = exact-rate ≥ 0.5 or mean closeness ≥ 0.9; WRONG = otherwise; INVALID = ill-formed, or the
rule predicts no cost change. Closeness: 1 − relative error (counts, DP values), coordinate agreement (vectors),
greedy/optimum ratio (greedy).

| Rule | Candidates | EXACT | NEAR-MISS | WRONG | INVALID | Distinct | Clusters | Fits resolved / EXACT with fit | Distinct scaling keys |
|---|---|---|---|---|---|---|---|---|---|
| memo | 300 | 249 | 1 | 18 | 32 | 297 | 133 | 214 / 231 | 108 |
| convolution | 300 | 138 | 0 | 162 | 0 | 154 | 33 | 138 / 138 | 6 |
| magma_power | 320 | 219 | 78 | 23 | 0 | 199 | 8 | 219 / 219 | 1 |
| greedy | 260 | 182 | 78 | 0 | 0 | 153 | 15 | 182 / 182 | 1 |
| knuth | 260 | 122 | 80 | 58 | 0 | 76 | 8 | 122 / 122 | 34 |
| bilinear | 260 | 126 | 58 | 39 | 37 | 189 | 59 | 126 / 126 | 34 |
| mitm | 220 | 125 | 85 | 10 | 0 | 70 | 9 | 88 / 88 | 15 |
| **total** | **1920** | **1161** | **380** | **310** | **69** | **1138** | 265 | **1089 / 1106** | |

EXACT candidates without a fit: 55 = memo 18 (12 "mixed" recurrences with one subtractive move, which are
super-polynomial but sub-exponential and get no closed-form claim; 4 with fewer than 3 admissible sizes; 2
compress) + mitm 37 (interaction families, for which no scaling plan is defined). The 10 bilinear candidates with
rank 1 have a constant fast cost (1ᵈ = 1) and are checked by max/min of the counts, like constant claims in
tools/validate.py.

**Precondition vs verdict** [ana]:

| Rule | precondition ⇒ EXACT (precision) | share of EXACT that had the stated precondition (recall) | EXACT without stated precondition |
|---|---|---|---|
| memo (incl. compress) | 1.000 | 0.9839 | 4 |
| convolution | 1.000 | 1.000 | 0 |
| magma_power | 1.000 | 0.5571 | 97 |
| greedy | 1.000 | 0.9725 | 5 |
| knuth | 1.000 | 0.6475 | 43 |
| bilinear | 1.000 | 1.000 | 0 (by construction) |
| mitm | 1.000 | 0.928 | 9 |

### 3.1 Exponent changes of the EXACT clusters (exact counts, tolerance 0.05 unless stated) [ana]

α = slope of log(count) against log(claimed cost); the interval is [min, max] of the local slopes between
consecutive sizes (the proposed uncertainty interval for α); "cross" = fast counts fitted against the slow claim
(far from 1 means the exponent change is resolved).

| Cluster (examples) | Slow claim, α [local] | Fast claim, α [local] | Cross α |
|---|---|---|---|
| conv xor / or / and | 4ⁿ, 1.000 [1.000, 1.000] | n·2ⁿ, 0.9825 [0.9526, 0.9939] | 0.5961 |
| conv cyclic | 4ⁿ, 1.000 | n·2ⁿ, 0.9879 [0.9666, 0.9958] | 0.5993 |
| conv prod Z_(N/2)×Z₂ | 4ⁿ, 1.000 | n·2ⁿ, 0.9907 [0.9742, 0.9969] | 0.6010 |
| conv max / min (chain) | 4ⁿ, 1.000 | 2ⁿ, 1.0119 [1.0003, 1.0728] | 0.5060 |
| conv sat (lifted) | 4ⁿ, 1.000 | n·2ⁿ, 0.9643 [0.9090, 0.9867] | 0.5851 |
| magma (all EXACT classes) | 2ⁿ − 2, 1.000 | n − 1, 1.000 | 0.0314 |
| greedy (all EXACT) | 2ⁿ, 1.000 | n, 1.000 | 0.0544 |
| knuth bst | n(n+1)(n+2)/6, 1.000 | n², 1.0106 [0.9990, 1.0256] | 0.6869 |
| knuth subint | same | n², 0.9925 [0.9052, 1.0242] | 0.6747 |
| knuth convex_len / concave_len | same | n², 1.000 | 0.6798 |
| bilinear m=4, r=3 (incl. Karatsuba, GF(4)) | 4ⁿ, 1.000 | 3ⁿ, 1.000 (tol 0.02) | 0.7925 |
| bilinear m=6, r=2 | 6ⁿ | 2ⁿ | 0.3869 |
| mitm groups (add, xor, mul_unit) | 2ⁿ, 1.0005 | 2^(n/2), 0.964–0.993 | (rival 2ⁿ rejected) |
| memo1d sub, e.g. s1+s2 | 1.6180339887ⁿ, 1.000 | n, 1.000 | |

Convolution counts depend only on the structure, not on the labelling, so one fit per structure (6 keys) serves
138 candidates; likewise one key for magma powering and one for greedy (oracle-call counts depend only on n). The
harness marks reused fits `cached: true`.

---

## 4. Deduplication and clustering

**Method** (per rule; `canonical()` in each module):
- **Operation tables** (magma, small convolution tables, N ≤ 5): exact canonical form = lexicographic minimum over
  all N! relabellings (`common.canon_table_exact`).
- **Structured convolution tables**: the detector constructs an isomorphism φ to a library structure and verifies
  it on all N² entries, so "iso:<structure>:<N>" is a **certificate**, not a heuristic.
- **Larger unstructured tables** (N = 8, 16): colour-refinement fingerprint (`common.table_fingerprint`):
  isomorphic tables always collide; non-isomorphic ones may also collide, so dedup can only over-merge.
- **Set systems** (greedy): colour refinement of elements by membership profiles, then the exact minimum over
  permutations within classes when there are at most 5040 of them, else an invariant hash.
- **Tensors** (bilinear): minimum over S_a × S_b × S_c index permutations (and the x↔y swap when a = b). GL
  equivalence is deliberately not used: it preserves rank but not the naive count m, so it changes the problem.
- **Recurrences** (memo): multiset of (move, coefficient) plus combine operator; 2-D also under transposition.
- **Parametric families** (knuth, mitm): the family parameters without the instance seed.

**Clusters**: rule-specific keys (cost class for memo; structure × family for convolution; algebraic class for
magmas; family × matroid for greedy; family for knuth; format × m × r for bilinear; operation × group for mitm):
265 clusters in total [mass].

**Results**: 1920 → 1138 distinct (782 duplicates). Canonical classes with conflicting verdicts: 14 in total
(bilinear 8, knuth 5, magma 1), all NEAR-MISS vs WRONG or EXACT vs NEAR-MISS splits caused by sampling: in
bilinear the nearest rank-(m−1) tensor is chosen by scan order, which is not permutation-invariant; in knuth the
class key omits the instance seed; the magma class (exact-rates 0.5167 vs 0.45) straddles the 0.5 threshold. An
EXACT/not-EXACT split for isomorphic magmas would contradict determinism; H-M1 found **0** screen-EXACT magmas
that fail an exhaustive check (0/900).

### 4.1 The 17 unresolved fits (all memo, 10 scaling keys)

- 1 key: divisive moves [h, h] claim n^1.0 and the rival list contains "n", which is the same function: a
  **harness artefact** (rival identical to the claim), not a failed claim. Not fixed; recorded.
- 1 key: divisive [t, t] fast side α = 0.9519 against log n (outside 0.05; the states are ⌊log₃ n⌋ + O(1), a
  pre-asymptotic offset).
- 2 keys: subtractive moves with gcd > 1 (λ = 1.189, 1.272): α = 1.0695, 1.054, small counts with a constant
  offset; pre-asymptotic.
- 6 keys: 2-D recurrences at the small n that 2·10⁵ calls allow (n ≤ about 12): slow α 0.86–1.06 or fast α
  0.93–0.96. For the interior-cone move sets the spec-derived exact counts at n = 100..200 fit the corrected claim
  with α in [1.000, 1.0047] (H-R1, 28 move sets), so these are pre-asymptotic fits, not wrong claims.

---

## 5. Near-miss analysis

### 5.1 Per cluster: how close, which precondition fails, and the repaired rule

| Cluster | n | Nearness [ana] (mean exact-rate / mean closeness / worst closeness) | Failing precondition | Repaired rule (tested) |
|---|---|---|---|---|
| magma none:noncomm / comm | 70 / 31 | 0.637 / 0.637 / 0.0 and 0.579 / 0.579 / 0.0 | square condition (weaker than associativity) | cycle detection on left powers: exact on 900/900 magmas [hyp]; ≤ m + 1 operations (degenerate family, see caveat) |
| greedy indset / matching / downclosure / knapsack / basis_removed (non-matroid) | 23 / 23 / 9 / 13 / 13 | 0.880 / 0.973 / 0.333; 0.822 / 0.955 / 0.5; 0.822 / 0.953 / 0.286; 0.856 / 0.975 / 0.429; 0.939 / 0.988 / 0.5 | exchange axiom | none within greedy: the worst ratio is exactly the rank quotient q (repair = exact algorithm for that structure, e.g. matching) |
| knuth monotone_rand | 42 | 0.902 / 0.998 / 0.912 | QI | none found; root monotonicity is the real criterion (5.3) |
| knuth perturbed | 32 | 0.848 / 0.971 / 0.0 | QI (t ≤ 4 cells) | none found |
| knuth subint_lin | 41 | 0.302 / 0.845 / 0.0 | monotonicity (QI holds) | none found |
| knuth random | 30 | 0.101 / 0.598 / 0.0 | both | none |
| conv perturbed_xor / _or / _cyclic | 27+ / 9+ / 13+ | 0.0 / 0.47–0.57 / 0.125 (output coordinates) | structure (t ≤ 8 table entries) | transform + sparse correction: exact on 300/300 tables [hyp] |
| conv latin / random / sub | 42 | 0.0 / ≤ 0.47 / 0.0 | structure | same correction, but |D| is large: cheaper than naive on only 38/153 non-structured tables [hyp] |
| mitm max / addsat / mul_comp / mul_zero | 20 / 16 / 14 / 23 (seed 2) | plain exact 0/20, 3/16, 0/14, 17/23 [hyp] | unique completion | all-solutions lookup (= monoid convolution of the two half-histograms, R7∘R2): exact 141/141 [hyp] |
| mitm add_inter | 33 (seed 2) | plain exact 0/33 | no crossing interactions | boundary conditioning: exact 92/92 additive candidates [hyp] |
| bilinear r = m | 127 (seed 2) | 0.38–0.57 / 0.74–0.95 / 0.25–0.56 [ana] | rank < support | none with gain: repaired cost (m−1) + rank(residual) < m in **0/127** cases [hyp] |
| compress (flag matters) | 19 | 0.0 / 0.0–0.13 | stated precondition and the refined one | full-key memo (R1) |

### 5.2 Proposed nearness metrics, tested on the data

| Metric | Definition | Test result |
|---|---|---|
| M1 correctness rate | fraction of screened instances exact | separates clusters well, but depends on the instance distribution: greedy non-matroids reach 0.82–0.94 [ana] |
| M2 mean closeness | mean of per-instance closeness | sensitive to the output type: one wrong table entry costs 2/N output coordinates in convolution, so perturbed tables with table agreement ≥ 0.875 are WRONG by M2 |
| M3 worst-case approximation ratio | min closeness over instances | for greedy, the sampled worst over 200 random weight vectors equals q in only 72/147 non-matroids [hyp]: sampling underestimates the worst case |
| M4 structural distance | distance of the input structure from the precondition (table agreement with the nearest structure; QI/monotonicity violation counts; rank − m) | table agreement vs output agreement: Pearson r = 0.812 over 153 non-structured tables [hyp]; cheap and instance-free |
| M5 adversarial ratio | ratio on constructed worst-case instances | greedy: equals the rank quotient within 0.0005 on 400/400 systems; random weights stay ≥ q on 400/400 [hyp]. **Recommended**: it is exact, needs no sampling, and has a theorem behind it |
| M6 robustness | exact-rate per instance family | greedy non-matroids: 0.921 (0/1 weights), 0.815 (weights 1..3), 0.882 (other) [hyp]; non-matroids missed by 40 random weights in the mass screen: 5; by 200 weights: 2/147 (both basis_removed) |
| M7 exponent gap Δα with interval | α of each side, cross α, and the local-slope interval | section 3.1; for the repaired rules the gap shrinks with the repair cost (5.4) |

**Recommendation:** report M5 (or M4 where no adversary is known) as the primary nearness, M1/M6 as secondary,
and never M3 from random sampling alone.

### 5.3 Knuth: what actually decides exactness (H-K1, 5400 instances, seed 3, 10 families incl. 2 held out) [hyp]

| QI | monotone | roots monotone | exact | instances |
|---|---|---|---|---|
| yes | yes | yes | yes | 1888 |
| no | yes | yes | yes | 1055 |
| yes | no | yes | yes | 203 |
| yes | no | no | yes | 230 |
| yes | no | no | **no** | 728 |
| no | no | no | no | 1073 |
| no | no | no | yes | 224 |
| no | no | yes | yes | 335 |
| no | yes | no | yes | 195 |
| no | yes | no | no | 69 |

- Yao's conditions ⇒ exact: no counter-example (consistent with the theorem, Yao 1980 [DOI OK]).
- Root monotonicity ⇒ exact: no counter-example (expected: the restricted range contains the largest root).
- **QI without monotonicity is not enough:** 433 exact vs 728 not.
- Exact does not need root monotonicity (230 + 224 + 195 instances), so root monotonicity is sufficient, not
  necessary.

### 5.4 Merge proposals and thresholds (tested)

1. **One parametrised family per cluster.** The 219 EXACT magmas share one scaling key; the 138 EXACT convolution
   tables share six. A single T7 entry "binary powering in a finite magma satisfying the square condition" (magma
   as parameter) or "T-convolution for T isomorphic to a library structure" would carry the whole cluster.
2. **Rule composition.** MITM ∘ monoid convolution makes meet in the middle exact for every commutative monoid
   (141/141). Transform ∘ sparse correction makes the convolution rule exact for every table (300/300). Lift ∘ fold
   handles saturating addition (17/17 EXACT in the mass screen).
3. **Thresholds where a near-miss becomes exact and stays faster** [hyp]:
   - convolution: the repaired transform costs transform + 3|D| counted operations; it beats naive (2N²) while
     |D| ≤ 95 (xor, N = 16), 63 (cyclic, N = 16), 133 (or, N = 16), 13 (xor, N = 8); never at N = 4 for xor/cyclic;
   - meet in the middle with crossing interactions (n = 16, Z₃₁): boundary conditioning costs 541, 827, 1384,
     2508, 4544, 8720, 16960, 33472, 66560 operations for |B| = 0..8, against 65535–98175 for the slow side; the
     gain shrinks by about 2× per boundary vertex and survives up to |B| = n/2 here only because the slow side
     also pays for the interaction terms;
   - bilinear: no threshold exists (0/127 repairs with gain), by subadditivity of rank.

---

## 6. Rule hypotheses (IDEA level) and their tests on fresh seeds / held-out families

| ID | Hypothesis | Test | Result |
|---|---|---|---|
| H-M1 | Binary (left-to-right) powering returns the left power x^e for every e **iff** p_a * p_a = p_(2a) for all a ≥ 1 and all x | seed 2: 600 magmas (m ≤ 5); held out: 300 magmas with m = 6 (random, comm, idem, idem_comm, latin), exhaustive over e ≤ 4m + 7 | **600/600 and 300/300 agree.** Seed 2: 254 associative, 382 power-associative, 419 square-condition = 419 exact; 165 exact non-associative; **37 exact but not power-associative** (so the condition is strictly weaker). Held out: 132 exact, none associative, all power-associative |
| H-R2 | State compression is exact iff δ = 0, no flips, or the flag is a function of n on the reachable states | seed 3: 400 compress candidates | **400/400 agree**: 292 stated+refined EXACT, 35 refined-only EXACT, 70 WRONG + 3 NEAR-MISS with neither |
| H-G1 | Worst greedy ratio = rank quotient; adversarial weights attain it | seed 2: 400 set systems, 200 random weight vectors each | matroid ⇔ q = 1: 400/400; random worst ≥ q: 400/400; adversarial − q ≤ 0.0005 on 400/400. Literature: Jenkyns 1976 / Korte–Hausmann 1978 [DOI OK for the latter], so this is a **pipeline check** of a known theorem |
| H-K1 | Knuth is exact under QI alone (without monotonicity) | 5400 instances (section 5.3) | **REFUTED**: 728 of 1161 QI-only instances are not exact |
| H-K2 | Translation-invariant weights h(j − i) make Knuth exact | held-out family random_len (600 instances) | **REFUTED**: 157/600 exact. Concave non-decreasing h: 600/600 exact on seed 3 plus 36/36 mass-screen candidates. **Remaining IDEA**: concave h suffices although QI fails on every such instance. Literature status not checked |
| H-C1 | Table agreement predicts output agreement | 153 non-structured tables | r = 0.812 (supports M4 as a proxy, not a law) |
| H-T1 | Plain MITM is exact iff completions are unique | 141 interaction-free candidates | sufficient, not necessary: 121/141 agree; mul_zero is exact on 17/23 and addsat on 3/16 candidates where non-unique completions happen not to be hit |
| H-B1 | Random small GF(2) bilinear maps often have rank < support, more so with density | seed 2: 24 format × density cells | e.g. 2×3×3: 4/10 at density 0.15 up to 22/23 at 0.5; 2×3×2 at 0.15: 0/9 |
| H-R1 | The corrected 2-D growth constant matches the counting DP | 28 interior move sets | max relative difference 0.29% (the diagonal-only constant: 5.29%); α at n = 100..200 in [1.000, 1.0047]; 20 of 28 maxima at the diagonal corner |

None of these is a theorem claim. H-M1 has a two-line proof sketch (the method only squares a left power or
multiplies it by x, which is the definition; every a ≥ 1 occurs as a prefix of some e) and is very likely folklore
around power-associativity [recalled]; no literature search was made for it.

---

## 7. Promotion list (at most 15; no entry folders created)

| # | Candidate | Evidence | Literature status | Suggested destination |
|---|---|---|---|---|
| 1 | Maximum-weight basis of a binary matroid (GF(2) vectors): 2^g oracle calls → greedy with elimination | 31 EXACT linear-matroid candidates, fits resolved [ana] | Rado 1957 / Edmonds 1971 [DOI OK] | staging; low novelty next to MST (same technique) |
| 2 | OR / AND convolution via zeta–Möbius: 4ᵏ → k·2ᵏ | 23 EXACT (or+and), certificates of isomorphism | Yates 1937 [recalled]; extends the zeta-transform entry | extension of `subset-sum-zeta-transform-naive-vs-yates` (section 3.3 type), not a new pair |
| 3 | Max-convolution over a chain: N² → N via prefix sums | 22 EXACT (max+min) | folklore [recalled] | T7 |
| 4 | Cyclic convolution over Z_N and Z_(N/2)×Z₂ | 44 EXACT | Cooley–Tukey 1965 [DOI OK] | pipeline check (NTT entry exists) |
| 5 | Saturating-addition convolution by lift-and-fold | 17 EXACT | composition of known pieces | T7; example of a homomorphic-image rule |
| 6 | Karatsuba as GF(2) rank 3 of the 2-term polynomial product | rediscovered, m = 4, r = 3 | Karatsuba [recalled]; entry exists | pipeline check |
| 7 | GF(4) multiplication over GF(2), rank 3 (tensor powers: 4ᵈ → 3ᵈ) | EXACT, fits resolved | rank 3 for quadratic extensions [recalled] | T7 / methodology note |
| 8 | Knuth on convex length weights a·d² + b·d | 24 EXACT, Yao conditions hold on every instance | Yao 1980 [DOI OK] | T7 (extension of the optimal-BST entry's family) |
| 9 | Knuth on concave length weights (QI fails, still exact) | 600/600 + 36/36 | not checked | IDEA; literature check first |
| 10 | Counting subsets with a given product in Z_p^* by meet in the middle | 21/21 exact on seed 2, fits resolved | Horowitz–Sahni 1974 [DOI OK] pattern | T7; same caveat as knapsack (a DP over the group is pseudo-polynomial in p) |
| 11 | MITM with boundary conditioning for interaction graphs | 92/92 exact; cost 2^(|B|) · 2^(n/2) | split-and-list style [recalled] | methodology note |
| 12 | Square condition for binary powering | H-M1 | folklore [recalled] | methodology note (generator precondition) |
| 13 | Functional-dependence criterion for state compression | H-R2 | relates to patterns.md §1.2 (shortest-path state compression) | methodology note for generator G1 |
| 14 | Corrected 2-D call-count asymptotics (`memo.growth_2d`) | H-R1 | ACSV, Pemantle–Wilson 2002 [DOI OK, title only; theorem details recalled] | infrastructure for a 2-D recurrence generator (T7 output) |
| 15 | Rank quotient / adversarial ratio as the near-miss metric for greedy | H-G1 | Korte–Hausmann 1978 [DOI OK] | methodology note |

---

## 8. Draft research-log entries (all DRAFT; the maintainer numbers and edits them)

**DRAFT RL-a · DECISION · Rule mining harness: counted primitives, verdict thresholds, dedup.**
`generators/rules/` screens rule-produced fast algorithms against slow ones on seeded instances. Verdicts EXACT /
NEAR-MISS (exact-rate ≥ 0.5 or mean closeness ≥ 0.9) / WRONG / INVALID. Exact counts come from counted primitives;
fits use `eval_cost` and `fit_slope` imported unchanged from tools/validate.py, with the other side's claim always
added as a rival. Rationale: instrumented primitives cannot under-report (the algorithm never touches raw data);
line counting (RL-074 idea 1) was not needed. Provenance: experiment.

**DRAFT RL-b · VERIFIED · 1920 rule-mined candidates screened.**
7 rules, 1920 candidates: 1161 EXACT, 380 NEAR-MISS, 310 WRONG, 69 INVALID; 1138 distinct after dedup. 1089 of
1106 EXACT fits resolve the exponent change (tolerance 0.05; bilinear 0.02); 0 count/spec mismatches. Stated
precondition ⇒ EXACT with precision 1.000 in every rule. T7 at most. Provenance: experiment
`2026-10-06d_rules_mass_screen.py`.

**DRAFT RL-c · NEAR-MISS · Near-miss clusters and repairs.**
Per-cluster numbers in research/2026-10-06d_rule_mining.md section 5. Repairs exact on every tested candidate:
sparse correction (300/300), all-solutions MITM (141/141), boundary conditioning (92/92), cycle detection
(900/900). Gain thresholds: convolution |D| ≤ 95 (xor, N = 16); bilinear repairs never gain (0/127). Provenance:
experiment `2026-10-06d_rules_hypotheses.py`.

**DRAFT RL-d · IDEA (supported) · Weaker preconditions.**
Binary powering exact iff the square condition (900/900; 37 exact magmas not power-associative); state compression
exact iff the flag is functional on reachable states (400/400). Fresh seeds and held-out families; not theorems;
likely folklore.

**DRAFT RL-e · REFUTED · Two Knuth hypotheses.**
QI without monotonicity: 728 of 1161 instances not exact. Translation invariance: 157/600 exact on random h.
Remaining IDEA: concave non-decreasing h (600/600 and 36/36 exact although QI fails on every instance).

**DRAFT RL-f · VERIFIED (pipeline check) · Rank quotient.**
Greedy's adversarial ratio equals the rank quotient within 0.0005 on 400/400 set systems; random weights stay
above it on 400/400; matroid ⇔ q = 1 on 400/400. Known theorem (Korte–Hausmann 1978, doi:10.1016/S0167-5060(08)70322-4).

**DRAFT RL-g · CORRECTED · 2-D recurrence growth constant (agent's own error, caught by its own check).**
Old state: λ = min 1/(xy) on Σ x^a y^b = 1 (diagonal coefficient only), up to 5.29% below the counting DP. Cause:
the naive call count sums walks over all endpoints. Fix: maximum of directional rates over endpoint directions;
max deviation 0.29%; large-n α in [1.000, 1.0047]. Effect: 7 more memo fits resolve (207 → 214 of 231).

**DRAFT RL-h · CORRECTED · Held-out Knuth family was not QI-neutral (agent's own error).**
Adding g(i) + h(j) changes the degenerate QI quadruples with b = c, where w(b, b) = 0 is fixed; replaced by
g(i) − g(j). Found because the family showed QI violations on all instances in the first smoke test [console].

**DRAFT RL-i · NULL · No rule-mined candidate beats a known algorithm.**
Scope: the 7 generated families above (1920 candidates; 900 + 5400 + 400 + 300 + 200 + 400 + 400 further
hypothesis instances or candidates). Every EXACT candidate is an instance of a textbook rule; rediscoveries:
Karatsuba (GF(2) rank 3), GF(4) multiplication (rank 3), FWHT / NTT / Yates.

**DRAFT RL-j · INCONCLUSIVE · 17 memo fits unresolved.**
1 harness artefact (rival identical to the claim), 16 pre-asymptotic small-n fits; large-n spec counts support the
claims (section 4.1).

---

## 9. Decision log, bugs and dead ends

**Decisions** (decision; alternatives; evidence that settled it):
1. Counted primitives instead of line counting or timing; alternatives: `sys.monitoring` line counts (RL-074),
   wall-clock; evidence: exact equality with the spec counts in every rule (0 mismatches) and no V2 timing noise.
2. Thresholds 0.5 / 0.9 for NEAR-MISS; alternatives: a single closeness threshold; evidence: closeness alone
   misclassifies convolution (one table entry costs 2/N coordinates), exact-rate alone misclassifies greedy (high
   rate, low worst ratio). Both raw numbers are stored, so any threshold can be re-applied.
3. Dedup by exact canonical forms where cheap, certificates for structured tables, invariant fingerprints
   otherwise; alternative: full permutation search for N = 8, 16 (40320! is infeasible). Fingerprints can only
   over-merge, which is the safe direction for counting distinct problems.
4. Fits cached per scaling key where the counted operations provably do not depend on the candidate's labelling
   (convolution, magma, greedy, bilinear); every reused fit is marked.
5. Exact-form cost claims (2ⁿ − 2, n − 1, n(n+1)(n+2)/6) where the specification gives them, following the D7
   precedent of research/2026-10-07b_new_candidates.md; the time-complexity class is unchanged.
6. Bilinear maps over GF(2), where BFS gives exact ranks of all 2^(abc) tensors per format (≤ 2¹⁸ states, 1.3 s for
   2×3×3 [console]); alternative: integer ranks, which need a different search; consequence: statements hold over
   GF(2) only.
7. Fixed-carrier magma powering is degenerate (cycle detection needs ≤ m + 1 operations); kept as a rule test bed,
   labelled T7 at most.
8. No `validate.py --record` or `--scaling`; the maintainer makes the recorded run.

**Bugs I made and fixed** (all in new code; tools/validate.py untouched):
1. Calling `eval_cost` with an int n made "4**n" at n = 10¹⁵ build a huge integer: the first smoke test hung for
   more than 10 minutes and was killed. `common.log_cost` now passes float(n).
2. Rival costs such as λⁿ at n = 16000 overflow a float: log-space evaluation fallback in `common.log_cost`.
3. Greedy scaling used the screen-size predicate at larger g (index error): the predicate now travels with the
   instance.
4. 1-D memo size choice stepped by lcm of offsets and gave < 3 points: now steps by their gcd.
5. MITM boundary repair folded all subsets of the forced items instead of the full set (assertion): fixed.
6. `subint_sep` not QI-neutral (draft RL-h).
7. 2-D growth constant (draft RL-g); the first corrected version was too slow uncached (the rerun was stopped and
   restarted after caching per move set).
8. H-G1 first run reported 7 "violations" of the rank-quotient bound: q was stored rounded to 6 decimals
   (2/3 → 0.666667); comparison now uses a 10⁻⁶ margin, and the script records the artefact values ([0.666667]).
9. A unit test assumed moves s1 (flipping) + s2 (not flipping) make the compressed key lossy; it does not
   (p = (n − m) mod 2). This became hypothesis H-R2.
10. Not fixed: the rival "n" equal to the claim "n**1.0" for divisive moves [h, h] (section 4.1).

**Dead ends:** blind application of the nearest structure's transform to non-structured tables (WRONG on 162/162,
mean output agreement ≤ 0.57); Knuth on QI-only weights; near-miss repair for bilinear maps (0/127).

## 10. Open ideas

1. Concave length weights and Knuth (H-K2 remainder): prove or find the literature; test other concave families.
2. Generators for the four catalogued-only rules (subset DP, inclusion–exclusion, augmenting paths,
   randomisation), with the same harness.
3. Adversarial instance construction (M5) for the other rules: Knuth (non-monotone split witnesses), meet in the
   middle (targets hitting non-unique completions), so that near-miss metrics stop depending on sampling.
4. Bilinear maps over Z or GF(3), where ranks can differ from GF(2).
5. Use the refined preconditions as the gates of generator G1 (recurrences) and G3 (monoid powering) from
   research/2026-10-07_patterns.md.

## 11. Reproduction

From the repository root, with `PYTHONIOENCODING=utf-8` and `.venv/Scripts/python.exe` (CPython 3.14.2):

```
python experiments/2026-10-06d_rules_mass_screen.py --max-seconds 1100   # 72 s; candidate store + summary
python experiments/2026-10-06d_rules_analysis.py                          # cluster tables, analysis.json
python experiments/2026-10-06d_rules_hypotheses.py                        # 71 s; hypotheses.json
python experiments/2026-10-06d_rules_doi_checks.py                        # 10 Crossref lookups, 1.2 s apart
python -m generators.rules list                                           # rule catalogue
python -m generators.rules screen memo --seed 1 --count 50                # one rule, summary to stdout
python -m unittest discover -s tests                                      # includes tests/test_rules.py (22 tests)
```

## 12. Files created

- `generators/rules/__init__.py`, `__main__.py` (CLI), `common.py` (harness), `runner.py` (batch, dedup,
  clusters), `memo.py`, `convolution.py`, `magma_power.py`, `greedy.py`, `knuth.py`, `bilinear.py`, `mitm.py`
- `tests/test_rules.py` (22 tests). Final checks: `python -m unittest discover -s tests` ran 178 tests, OK (the
  count includes tests added by the parallel agents); `python tools/validate.py` printed "62/62 entries OK".
- `experiments/2026-10-06d_rules_mass_screen.py`, `experiments/2026-10-06d_rules_hypotheses.py`,
  `experiments/2026-10-06d_rules_analysis.py`, `experiments/2026-10-06d_rules_doi_checks.py`
- `candidates/2026-10-06d/{memo,convolution,magma_power,greedy,knuth,bilinear,mitm}.jsonl`, `summary.json`,
  `analysis.json`, `hypotheses.json` (about 1.6 MB in total)
- `results/2026-10-06d/*_full.jsonl`, `results/2026-10-06d/hypotheses.json` (gitignored bulk output)
- this report
