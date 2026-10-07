Author: delegated research agent (Claude), for the maintainer.

# Mutation pilot, 2026-10-06d: MIRROR and OPERATION SWAP over the validated pairs

Provenance labels follow RESEARCH_LOG.md. Every number below comes from the recorded run
`python experiments/2026-10-06d_mut_pilot.py --trials-scale 5` (records in `mutations/records/2026-10-06d/`), from
`python experiments/2026-10-06d_mut_boundary_map.py` (which only reads those records), or from
`python experiments/2026-10-06d_mut_literature.py` (Crossref/DataCite responses). These are agent-report numbers and
have not been re-run by the maintainer. Operation counts are exact; the `elapsed_s` fields in the records are
wall-clock times and only informational.

## 1. Summary

The owner's idea was to "morph" validated pairs and see which fast algorithms survive. A mutation changes the
**problem** (objective, comparison, algebra) and runs the **implementations**. The brute side defines the mutated
problem, and the cost is measured, never assumed.

- **Engine:** `mutations/`, standard library only. Implementations run as in-memory copies of the repository code,
  either unchanged on injected element types or after targeted AST rewrites. Nothing under `pairs/`, `staging/` or
  `synthetic/` was modified. Unit tests check that the copies leave the source files unchanged (SHA-256).
- **Recorded run:** 369 mutants and **233 532 differential tests**, taking 141.8 s with 4 worker processes at
  below-normal priority.
- **Outcomes:** SURVIVED **176**, KILLED **84**, INVALID **69**, TRIVIAL **39**, INCONCLUSIVE **1**. 4 mutants are
  flagged NEAR-MISS.
  - MIRROR (27 mutants): TRIVIAL 19, KILLED 7, INVALID 1.
  - OPSWAP (342 mutants): SURVIVED 176, KILLED 77, INVALID 68, TRIVIAL 20, INCONCLUSIVE 1.
- **Cost fits:** 30 survivors were measured by exact operation counts. In 29 of them the claimed cost fits within
  tolerance and is the only candidate that fits, with **215 rival costs rejected**. The one failure is
  measurement-related (section 6).
- **Main result:** a property was checked mechanically on every substituted structure. For **every fast algorithm
  with mixed outcomes, a single property or a pair of properties separates exactly** the structures on which it
  survived from those on which it did not (section 4). Examples:
  - Strassen, Karatsuba, Ryser and Kirchhoff/Bareiss need an additive inverse.
  - FWHT needs an additive inverse and 1+1 ≠ 0.
  - The sparse table needs an idempotent ⊕.
  - Square-and-multiply needs power-associativity, not associativity: octonions survive while two non-power-associative magmas are killed.
  - Dijkstra, and Floyd–Warshall/Bellman–Ford on cyclic digraphs, need absorptivity (1 ⊕ a = 1).
  - Kadane and Held–Karp in ⊕-form need only distributivity.
- **No novelty is claimed.** Every survival in the boundary map is a known fact or a mechanical consequence of one;
  the pilot rediscovers it, which serves as a pipeline check. The most interesting kill is **Knuth's quadratic
  optimal-BST speed-up under (max,+)**: it is KILLED at agreement 0.8662 over 800 tests, with counterexample p = (0,0,0),
  q = (0,0,0,1) (recursion 3, Knuth 2). Among the tested selective structures, it survives exactly on the absorptive
  ones. Its literature status is [recalled]; we did not read Knuth 1971 or Yao 1980 beyond their bibliographic records.

*Correction (2026-10-07):* the "needs" and "only" statements above are separations observed on the 6–13 structures
tested per algorithm (§4: correlation, not proof), not proved conditions. For example, for the left-to-right
powering method `generators/rules/magma_power.py` argues that the weaker square condition p_a·p_a = p_2a is what is
needed, so "needs power-associativity" is not shown. "Every survival … is a known fact" is a belief: the literature
status in §8 is recalled, with only bibliographic records checked.

## 2. What was built

| Module | Content |
|---|---|
| `mutations/algebra.py` | 12 semirings and probes: Z, Z7, GF2, (min,+), (max,+), (max,min), (min,max), Bool, Viterbi = (max,×) on [0,1], (min,×) on Z>0, (max,×) on Z with negatives (not a semiring), and (min,+) with negatives. Also 10 ⊕-monoids/magmas (Sum, Min, Max, Xor, Or, And, Gcd, Concat, Minus, LeftZero), 8 ⊗-magmas (MulMod, AddMod, Min, Circle, Mat2, Octonion, Skew, CommNA) and Z_p for p = 998244353, 7681, 97, 17, 1000003. Element wrappers: `make_ring_elem` for (+,×)-origin code and `make_tropical_elem` for (min/max,+)-origin code, where `+` means ⊗ and `<` is the ⊕-order, checked for selectivity at run time. `Rev` reverses comparisons. `check_properties` tests the algebraic laws. |
| `mutations/rewrite.py` | `load_copy`: source → AST → targeted transforms → fresh module object. Transforms: compare flip, call swap, `sorted(reverse=True)`, selection → ⊕ (IfExp), relaxation → ⊕-accumulation, module-constant swap, expression replace (sentinel flip). A pattern that matches nothing raises an error, so silent no-op mutants cannot occur (*correction 2026-10-07: a matched pattern can still leave the code unchanged, e.g. a compare flip on `==`; see the module docstring*). |
| `mutations/engine.py` | `Mutant`, differential testing on seeded instances, a 5 s per-call watchdog, shrinking (smallest failing size first, then simpler values), classification, NEAR-MISS flags, and cost fitting. Fitting **imports** `tools/validate.py` (`fit_slope`, `eval_cost`), which is not modified. |
| `mutations/oracles.py` | Generic brute-force oracles over any structure: ⊕ over simple paths, over spanning trees and over subarrays; max cut; longest simple path. |
| `mutations/targets.py` | The 369 mutants: 14 OPSWAP builders and 1 MIRROR builder. |
| `mutations/related_karatsuba.py` | Polynomial Karatsuba. This is a closely related problem: the repository's Karatsuba multiplies integers with carries, which has no semiring reading. |
| `mutations/literature.py` | References and their verification (Crossref, DataCite fallback, arXiv), one connection, rate-limited. |

**Modes.**
- **io:** input/output transformation around unchanged code (negation, reciprocal, complement, ring embedding).
- **inject:** an unchanged copy run on injected element types.
- **ast** and **ast+inject:** a rewritten copy, optionally on injected element types.

**Classification rules** (from the `engine.py` docstring):
- **SURVIVED:** 0 disagreements and ≥ 10 tests.
- **KILLED:** at least 1 disagreement; the counterexample is shrunk.
- **TRIVIAL:** survived, but the mutant is a known reparametrisation. The reason is recorded.
- **INVALID:** an operation the code needs does not exist in the structure (`UndefinedOp`), comparisons with no total
  order (`OrderError`), a literal with no meaning there (`LiftError`), a crash, or a watchdog timeout.
- **INCONCLUSIVE:** the oracle failed.
- **NEAR-MISS** (a flag on KILLED): agreement ≥ 0.9, or the subject/oracle ratio within [0.5, 2] on every disagreement.

**Controls inside the map.** These cells are the original problems and are expected to survive:
- MinPlus for FW, BF, Dijkstra, Prim, Held–Karp and Knuth;
- MaxPlusZ for Kadane;
- Z for Strassen, Karatsuba, Ryser, FWHT and Kirchhoff;
- Z998244353 for the NTT;
- Sum for Yates.

## 3. Boundary map (fast algorithm × structure)

S = SURVIVED, K = KILLED, I = INVALID, T = TRIVIAL, ? = INCONCLUSIVE, * = NEAR-MISS, – = not tested. Tests per
mutant are in the records. Typical counts are 450–1050 per cell (sizes × trials × 5); the unchanged Strassen copy
has 60 tests at n = 17 and 24, and its CUTOFF=1 copy has 420 tests at n ≤ 8.

| Fast algorithm (mode) | Z | Z7 | GF2 | (min,+) | (max,+) | (max,min) | (min,max) | Bool | Viterbi | (min,×)Z>0 | (max,×)Z± | (min,+)Z± |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Strassen, unchanged and CUTOFF=1 (inject) | S | S | S | I | I | I | I | I | I | – | I | – |
| … with `a - b := a ⊕ b` probe | – | – | – | K | K | K | K | K | K | – | K | – |
| Strassen on a ring embedding (io) | – | – | – | S (Yuval) | – | S (thresholds) | – | S (0/1 ⊂ Z) | – | – | – | – |
| polynomial Karatsuba (inject) | S | S | S | I | I | I | – | I | – | – | – | – |
| Ryser (inject) | S | S | S | I | I | I | I | I | – | – | – | – |
| FWHT (inject) | S | S | I | I | I | I | – | I | – | – | – | – |
| Kirchhoff + Bareiss, weighted (inject) | S | S | S | I | – | I | – | I | – | – | – | – |
| Floyd–Warshall and Bellman–Ford, digraphs (inject) | I | I | K | S | K | S | S | S | S | S | – | K |
| same, DAGs (inject) | I | I | K | S | S | S | S | S | S | S | – | S |
| FW and BF relaxation → ⊕, digraphs (ast) | K | K | K | S | K | S | S | S | S | S | – | K |
| same, DAGs (ast) | K | K | K | S | S | S | S | S | S | S | – | S |
| Dijkstra (inject) | I | I | – | S | K | S | S | S | S | S | K | K |
| Kadane (inject) | I | I | K | – | S (MaxPlusZ) | S | S | S | S | S | K | S |
| Kadane selection → ⊕ (ast) | S | S | S | – | S | S | S | S | S | S | K | S |
| Prim (inject) | I | I | K | S | S | S | S | S | S | S | K | S |
| Kruskal (inject) | I | I | I | I | I | I | I | I | I | I | I | I |
| Held–Karp (inject) | I | I | K | S | S | S | S | S | S | – | K | – |
| Held–Karp relaxation → ⊕ (ast) | S | S | S | S | S | S | S | S | S | – | K | – |
| Knuth's optimal-BST DP (inject) | I | I | – | S | **K*** | S | S | – | S | S | – | – |

The ⊕-only and ⊗-only transforms:

| Fast algorithm | survived | killed / other |
|---|---|---|
| Yates zeta transform (⊕-monoid) | Sum, Min, Max, Xor, Or, And, Gcd, Concat, Z7, GF2, Bool, (min,+) | Minus K (n = 0: `[-1]` → oracle 1, Yates −1); LeftZero ? (no identity, so the oracle's `acc = 0` has no meaning) |
| Sparse table, O(1) query with overlapping blocks (⊕-monoid) | Max, Or, And, Gcd, LeftZero (Min = T) | Sum K, Xor K, Concat K, Minus K: all at n = 1 with query (0, 0), where the two blocks coincide, e.g. Sum `[-2]` → −4 |
| Square-and-multiply (⊗-magma) | AddMod, Min, Circle, Mat2, **Octonion** (MulMod = T) | Skew K (a = 983, e = 7: oracle 556, subject 555), CommNA K (a = 541, e = 6: 997 vs 385) |
| NTT with constants swapped in a copy (P, G = least primitive root) | Z998244353 (v₂(p−1) = 23), Z7681 (v₂ = 9) | Z97 K at n = 17 (size 64 > 2⁵), Z17 K at n = 9 (size 32 > 2⁴), Z1000003 K at n = 2 (size 4 > 2¹) |
| NTT unchanged, with the roots of Z_998244353 hard-wired (inject) | – | Z7681 K, Z K, GF2 K, (min,+) I |

**Cross-pair links** (TRIVIAL by design: known identities that land on other entries of the dataset):
- The (min,+) permanent equals the assignment problem. The repository's Hungarian method agrees with the injected
  permutation sum on 450 tests, and its addition/subtraction count fits n³ with α = 1.0854 (tolerance 0.1).
- Over GF(2), permanent = determinant. A copy of the determinant entry's Gaussian elimination with P = 2 agrees on 700 tests.

**MIRROR family (27 mutants).**
- **TRIVIAL (19).** These survived but are known reparametrisations:
  - MST → maximum spanning tree, by negation, `Rev` injection, `sorted(reverse=True)`, AST flips in Prim and the
    enumeration, and complement weights c − w;
  - reciprocal weights (MST, Dijkstra);
  - Kadane → minimum subarray (3 modes);
  - Hungarian → max-weight assignment by negation;
  - Held–Karp → max TSP (negation, and an AST flip with sentinel −inf);
  - LIS → longest decreasing subsequence, inversions → non-inversions, RMQ → range maximum (`Rev`).
- **KILLED (7):**
  - Dijkstra → longest simple path, by negation, by an AST flip with sentinel −inf, and by naive `Rev` injection;
  - closest pair → farthest pair (D&C with min → max and flipped strip tests; n = 4, points (0,0),(0,0),(0,1),(0,1): oracle 1, subject 0);
  - Stoer–Wagner → max cut, by negation and by flipped comparisons (both NEAR-MISS);
  - Held–Karp on `Rev` with the sentinel `math.inf` not flipped.
- **INVALID (1):** Hungarian on `Rev` values. All 12 tests in the 60 s mutant budget hit the 5 s watchdog: the
  reversed comparisons never reach the augmenting `break`.

## 4. Property analysis (mechanical)

Properties are checked by `algebra.check_properties` (stored in `mutations/records/2026-10-06d/properties.jsonl`).
- **Scope:** exhaustive on finite carriers (Bool, GF2, Z7, Z17, Z97). On infinite carriers, the stated bounded
  sample domain (`Structure.domain`, ≤ 20 000 triples). For Z_p with p prime, roots of unity are computed exactly
  (k | p−1, witness g^((p−1)/k)).
- **Evidence status:** a failed law always comes with a witness. A law that held on a sample domain is evidence, not proof.

The separator search (`experiments/2026-10-06d_mut_boundary_map.py`) considers 15 Boolean properties and reports the
properties, or pairs, whose truth value equals "survived" on every tested structure. TRIVIAL, INCONCLUSIVE and
sign-dropping probes are excluded.

| Fast algorithm | Exact separator found | Reading |
|---|---|---|
| Strassen (both copies), polynomial Karatsuba, Ryser, Kirchhoff + Bareiss | `add_inverse_exists` | Their identities use subtraction. Without it the copy cannot even run (INVALID). Dropping signs (`a − b := a ⊕ b`) is KILLED in every semiring. Smallest counterexamples have n = 2, e.g. (min,+) Strassen, X = [[0,0],[0,0]], Y = [[0,1],[0,1]], entry (1,1): oracle 1, subject 0. |
| FWHT | `add_inverse_exists & one_plus_one_nonzero` | GF(2) has inverses but N = 2ⁿ = 0, so `x // N` is undefined (INVALID). Z survives without 2 being invertible because the division is exact on the image (W W = N I). `two_invertible` alone is therefore not the right property. |
| NTT | not in the Boolean list | Survives iff the transform size divides p − 1, i.e. a primitive root of that order exists; checked exactly per p (table above). |
| Floyd–Warshall, Bellman–Ford on digraphs (unchanged and ⊕-form) | `absorptive_one_plus_a_is_one` | Cycles never help. Smallest kills are n = 2: (max,+) with W[0][1] = 0, W[1][0] = 1 (positive cycle); (min,+) with negatives, W[1][0] = −4. |
| the same on DAGs | `add_idempotent` (= `add_selective` here) | No cycles, so absorptivity is not needed. The ⊕-form is still KILLED on Z/Z7/GF2 already at n = 1 (D[0][0]: oracle 1, subject 1 ⊕ 1 = 2), because the in-place update with D[k][k] = 1 counts paths twice. The plain triple loop computes the closure only when ⊕ is idempotent (the Kleene-star form is a different algorithm; Lehmann 1977). |
| Dijkstra | `absorptive_one_plus_a_is_one` | Survives on (min,+) with w ≥ 0, (max,min), (min,max), Bool, Viterbi and (min,×) on Z>0; killed on (max,+), (min,+) with negatives and (max,×) with negatives; INVALID on Z and Z7 (⊕ not selective). |
| Kadane (unchanged) | `add_selective & distributive` (pairs) | The comparison `ending_here < 0` needs an order; the recurrence needs distributivity. (max,×) on Z is selective but not distributive (witness in properties.jsonl) and is KILLED at n = 2: [−1, −1] → oracle 1, Kadane −1. |
| Kadane, selection → ⊕ | `distributive_left` (and right) | In ⊕-form, E_j = x_j ⊕ (E_{j−1} ⊗ x_j) works in every distributive structure tested, including Z, Z7 and GF2 (sum over subarrays of products). |
| Prim | `add_selective & distributive` (pairs) | (max,×) with negatives K at n = 3; GF2 K (xor on {0,1} passes the run-time order test on distinct pairs, so the copy ran with Boolean semantics). Kruskal is INVALID everywhere because it packs weights into integer keys `w·n² + u·n + v`, which is not a semiring operation. |
| Held–Karp (unchanged / ⊕-form) | `add_selective & distributive` / `distributive` | The DP over (set, last city) is exact for any distributive structure: (+,×) counts weighted Hamiltonian cycles, Bool decides existence. |
| Knuth's optimal-BST DP | `absorptive_one_plus_a_is_one` | Survives on (min,+), (max,min), (min,max), Viterbi and (min,×); KILLED on (max,+) (NEAR-MISS). Absorptivity makes "more frequencies" never better, which resembles Yao's monotonicity condition [recalled; not checked against the paper]. |
| Sparse table | `add_idempotent` | Overlapping blocks count the overlap twice. LeftZero (a ⊕ b = a, associative, idempotent, non-commutative) survives, so commutativity is not needed. |
| Square-and-multiply | `mul_power_associative_to_6` | Octonions are not associative (witness in properties.jsonl) but survive 1000 tests; Skew and CommNA fail power-associativity and are KILLED. |
| Yates zeta | `add_associative` and `add_identity` (each exact) | The only kill (Minus, n = 0) comes from the code's `acc = 0`: 0 is only a right identity of a − b. Concat (non-commutative) survives because naive and Yates sum the submasks in the same (descending) order, so commutativity is not needed for this pair of implementations. |

Correlation, not proof. Each separator is exact on the 6–13 structures tested and is consistent with the algebraic
reason given in the "Reading" column. A wider structure library could split a separator that currently looks single.

## 5. Ring embeddings: killed by code swap, rescued by an input transformation

The OPSWAP KILLED/INVALID verdict for Strassen applies to *this code over this algebra*. It does not say that no fast
algorithm exists. Three io mutants embed the semiring into Z and run the unchanged integer Strassen:

| Structure | Embedding | Tests | Status | Cost |
|---|---|---|---|---|
| Bool | {F,T} → {0,1}, then entry > 0 | 160 | SURVIVED | multiplications 28672, 200704, 1404928 at n = 32, 64, 128 (= 7^k·16³ exactly); α = 1.0 against n^log2(7); all 12 library rivals rejected |
| (min,+) | a → (n+1)^(M−a), decode from the leading base-(n+1) digit | 160 | SURVIVED | Strassen's operation count, but on Θ(M log n)-bit integers: pseudo-polynomial in the weights (not fitted) |
| (max,min) | one Boolean product per distinct value t | 90 | SURVIVED | (number of distinct values) × Strassen (≤ 21 here): pseudo-polynomial |

These are rediscoveries of known reductions: Boolean product via integer product, Fischer–Meyer 1971 [DOI OK] and
Munro 1971 [DOI OK]; (min,+) via big-number products, Yuval 1976 [DOI OK]. For truly subcubic (max,min) products,
see Vassilevska, Williams and Yuster (STOC 2007 [DOI OK]; Theory of Computing 2009, DOI registered without a title,
so the title is unverified) and Duan–Pettie 2009 [DOI OK].

## 6. Survivors: measured cost

All counts are exact: the number of ⊗ (or ⊕, comparison, or all ring operations, as stated) performed by the subject
on seeded scaling instances. Tolerance is 0.03 unless stated. Library = the 13 default expressions in
`engine.DEFAULT_LIBRARY` unless a narrower list is given in `targets.py`.

| Subject (structure) | measure | n | counts | claimed | α | only claimed fits? |
|---|---|---|---|---|---|---|
| Strassen, unchanged (Z, Z7, GF2) | ⊗ | 32, 64, 128 | 28672, 200704, 1404928 | n^log2(7) | 1.0 | yes (12 rejected each) |
| Floyd–Warshall ((min,+), digraphs) | ⊗ | 16–128 | 4055 … 2071307 | n³ | 0.9995 | yes |
| Floyd–Warshall ((max,min)) | ⊗ | 16–128 | 4007 … 2063143 | n³ | 1.0052 | yes |
| Floyd–Warshall (Bool) | ⊗ | 16–128 | 3195, 31809, 262080, 2097024 | n³ | **1.0372** | **no**: outside 0.03 (see below) |
| Dijkstra ((max,min), Viterbi) | ⊗ | 32–256 | 611 … 33491 / 597 … 33336 | n² (tol 0.05) | 0.9631 / 0.9681 | yes |
| Prim ((max,min), (min,max)) | comparisons | 32–256 | 930, 3906, 16002, 64770 = (n−1)(n−2) | n² | 1.02 | yes |
| Kirchhoff + Bareiss (Z7) | ⊗ | 16, 32, 64 | 2030, 18910, 162750 | (n−2)(n−1)(2n−3)/3 | 1.0 | yes (n², n² log n, n³, n⁴ rejected) |
| Held–Karp ⊕-form ((max,min) / Z) | ⊗ | 6–12 | 165 … 56331 / 165 … 56241 | (n−1)(n−2)2^(n−3) + n − 1 | 1.0 / 1.0005 | yes (5 rejected) |
| Kadane ⊕-form (Z, Z7) | all ops | 64–4096 | 189, 765, 3069, 12285 = 3n − 3 | n | 1.0036 | yes |
| Ryser (Z7) | all ops | 6–12 | 1037 … 128987 | n·2ⁿ | 0.994 | yes |
| FWHT (Z, Z7) | all ops | 6–12 | 1856 … 229376 = (3n+2)2ⁿ | n·2ⁿ | 0.9928 | yes |
| NTT copy (Z7681) | ⊗ | 16–256 | 272 … 7424 | 3n log₂n + 5n | 1.0 | yes |
| polynomial Karatsuba (Z7, GF2) | ⊗ | 16–256 | 81 … 6561 = 3^log₂n | n^log2(3) | 1.0 | yes |
| Yates (Min, Or, Gcd) | ⊕ | 6–12 | 192 … 24576 = n·2^(n−1) | n·2ⁿ | 1.0 | yes |
| sparse table (Max, Gcd) | ⊕ | 64–4096 | 328 … 45070 | n log n | 1.0147 | yes (n, n² rejected) |
| square-and-multiply (Mat2, Octonion) | ⊗ | 8–128 bits | 15 … 255 = 2n − 1 for e = 2ⁿ − 1 | n | 1.0209 | yes |
| Hungarian (cross-link) | ± on inputs | 16–128 | 1956 … 1983220 | n³ (tol 0.1) | 1.0854 | yes |

**Bool Floyd–Warshall fit (1 of 30, not passed).** Only operations with an injected operand are counted. Absent
edges are the code's plain `INF` literals, and plain+plain additions are not counted. The random density of
`gen_digraph` (0.3/0.6/1.0, drawn per instance) therefore changes the counted fraction between n values. The
algorithm performs n³ steps on every input; the counter does not see them all. This is classified as a measurement
artifact, not a scaling failure.

## 7. Near-misses (all KILLED)

| Mutant | Tests | Agreement | Ratio on disagreements | Smallest counterexample |
|---|---|---|---|---|
| Knuth's optimal-BST DP over (max,+) | 800 | 0.8662 | subject/oracle in [0.6593, 0.9977] | n = 3, p = (0,0,0), q = (0,0,0,1): recursion 3, Knuth 2 |
| Stoer–Wagner −sw(−W) as max cut | 750 | 0.7413 | [0.7083, 0.9873] | n = 4, edges 0–1, 1–3, 2–3 of weight 1: max cut 3, subject 2 |
| Stoer–Wagner with both comparisons flipped | 750 | 0.7293 | [0.7391, 0.987] | n = 4, a path of 3 unit edges: 3 vs 2 |
| Ryser over (max,+) with signs dropped | 525 | 0.4305 | [1.011, 1.857] | n = 2, [[0,1],[0,1]]: 1 vs 2 |

None of them is an algorithm: an approximately right answer is not a pair (START_HERE section 6).
- Max-cut kill: max cut is NP-hard (Karp 1972 [DOI OK]), so a polynomial exact algorithm was never expected.
- Ryser ratio: the ratio is an upper estimate, because ⊕ = max over all column subsets dominates.

## 8. Literature status of notable results

Checked through the Crossref API, with the DataCite fallback (32 [DOI OK]); arXiv was not needed. Six references
have no identifier and stay [recalled]: Mohri 2002, Karatsuba–Ofman 1962, Ryser 1963, Yates 1937, Garey–Johnson 1979,
TAOCP vol. 2. **Scope:** only bibliographic records were checked (title and year). No paper text was read, so "known"
below means known from recall, with the citation's existence verified.

| Result | Status |
|---|---|
| Boolean closure by Warshall's loop (FW over Bool) | known: Warshall 1962 [DOI OK] |
| FW / algebraic path problems need closed or absorptive semirings | known: Lehmann 1977 [DOI OK]; Mohri 2002 [recalled]; Gondran–Minoux 2008 [DOI OK] |
| widest / bottleneck paths by Dijkstra | known: Pollack 1960 [DOI OK], Hu 1961 [DOI OK] |
| bottleneck spanning trees by MST algorithms | known: Camerini 1978 [DOI OK] |
| greedy depends only on the order of the weights (reciprocal / complement mirrors) | known: Edmonds 1971 [DOI OK] |
| Boolean / (min,+) / (max,min) products via fast ring products | known: Fischer–Meyer 1971, Munro 1971, Yuval 1976, Vassilevska–Williams–Yuster 2007, Duan–Pettie 2009 (all [DOI OK]) |
| (min,+) product barrier | Williams 2018 [DOI OK] (n³/2^Ω(√log n)), cited for context |
| NTT needs a root of unity of the transform order | known: Pollard 1971 [DOI OK] |
| tropical permanent = assignment; permanent mod 2 = determinant | known: Kuhn 1955 [DOI OK]; Valiant 1979 [DOI OK] |
| Held–Karp DP | Held–Karp 1962 [DOI OK], Bellman 1962 [DOI OK]; the (+,×) counting reading is [recalled] |
| sparse table needs idempotence | known: Bender–Farach-Colton 2000 [DOI OK] (sparse table for RMQ); the idempotence requirement is [recalled] |
| square-and-multiply needs only power-associativity; octonions are power-associative (alternative algebras) | [recalled] (Artin's theorem; no source verified) |
| Knuth's speed-up fails for maximum-cost BSTs | not found in the literature we checked. Scope: bibliographic records of Knuth 1971 [DOI OK] and Yao 1980 [DOI OK] only; no full text read. A small mechanical observation, no novelty claimed. |
| longest simple path / max cut are NP-hard (mirror kills) | Garey–Johnson 1979 [recalled], Karp 1972 [DOI OK] |
| farthest pair ≠ closest-pair D&C | the farthest pair is solved by convex hull plus rotating calipers: Preparata–Shamos 1985 [DOI OK] [recalled content]; Shamos–Hoey 1975 [DOI OK] |

**Literature corrections made during the run:**
- Duan–Pettie was first recalled as `10.1137/1.9781611973068.42`, which Crossref resolves to "Inserting a Vertex
  into a Planar Graph". A Crossref bibliographic query gave `.43`, now [DOI OK].
- The ToC 2009 DOI of Vassilevska–Williams–Yuster exists in Crossref without a title. The STOC 2007 version
  `10.1145/1250790.1250876` was found by query and is [DOI OK].

## 9. Bugs I made and fixed (all before the recorded run)

1. **Late-binding closures in cost lambdas** (zeta, xorconv, ntt, karatsuba, permanent). `lambda n: g(n, …)` captured
   the loop's last generator. The first-pass zeta fits for Or and Gcd crashed on MinPlus float samples; Ryser's
   count ran on MinMax samples, which went unnoticed because Ryser's count does not depend on the data. Fixed by
   binding `g=g`. First-pass records are kept in `results/mutations_2026-10-06d_firstpass/` (gitignored).
2. **`max_cut_brute` skipped every valid bipartition at n = 2** (the loop started at mask 1 and dropped empty T
   wrongly), returning None. This caused two false MIRROR kills in the smoke run. Fixed: masks 0 … 2^(n−1) − 2.
3. **The digraph shrinker added back-edges to DAG instances**, so shrunk "DAG" counterexamples were not DAGs. Fixed:
   only entries with i < j are simplified for DAGs.
4. **Relaxation → accumulation double-counts when the initial value is itself a candidate.** The max-subarray brute
   force starts with `best = a[0]` and then adds subarray [0,0] again. Under non-idempotent ⊕ the rewritten brute side
   is wrong; it is KILLED at n = 1 on Z, Z7 and GF2 and kept in the records as a control showing this limitation of
   the rewrite. The oracle for max subarray is therefore the generic `oracles.subarray_sum_product`, not the
   rewritten brute force.
5. **Kirchhoff on tropical instances read the diagonal literal 0 as a carrier value** ((min,+) 0 = unit). This produced
   3 spurious disagreements next to the INVALID verdict. Fixed by mapping the diagonal to S.zero.
6. **Roots-of-unity search looked only in a 41-element sample for large p** (unit test failure for Z1000003). Fixed:
   exact for prime p.
7. **An infinite loop (Hungarian on `Rev`) hung the first smoke run** for over 10 minutes. Fixed by the 5 s
   per-call watchdog, which now turns such mutants into INVALID ("exceeds limits").
8. **A first draft of a min-cut "complement" mutant used an invented formula** that is not a valid transformation.
   It was removed before any run (decision D5).

## 10. Decision log

| # | Decision | Alternatives considered | Evidence that settled it |
|---|---|---|---|
| D1 | Semantics of a mutated problem = the brute side (or a generic oracle over S), never the fast side | defining semantics by formula | the brief; and the generic oracles agree with the repository's brute copies wherever both run (e.g. MST enumeration under injection SURVIVED on all 9 selective structures against `oracles.spanning_trees`) |
| D2 | Code-level swap by **operator injection plus targeted AST rewrites**, not global AST rewriting | rewriting every `+`/`<` | a global rewrite would hit index arithmetic and loop bounds; targeted patterns raise an error if they match nothing (unit test `test_unmatched_pattern_is_an_error`) |
| D3 | Missing operations are **INVALID**, plus a separate sign-dropping probe (`a − b := a ⊕ b`) that can be KILLED | only one of the two | INVALID alone hides whether a natural misuse would silently give wrong answers; the probe is KILLED for all 7 structures without additive inverse for Strassen (both copies, 14 mutants), all 4 for Karatsuba and all 5 for Ryser |
| D4 | Order-based code on non-selective ⊕ raises `OrderError` (INVALID), and a separate ⊕-accumulation rewrite is tested | silently comparing by some order | turns "the code is order-based" into a recorded, mechanically checked fact (FW/BF/Dijkstra/Prim/Held–Karp/Kadane on Z, Z7) |
| D5 | No min-cut complement mutant | c − w complement weights | cut_(c−w)(S) = c\|S\|\|T\| − cut_w(S) depends on \|S\|, so no instance transformation maps max cut to min cut; the complement operator was applied to MST instead (TRIVIAL, affine) |
| D6 | Polynomial Karatsuba written in `mutations/` (closely related problem) | semiring-swap the integer Karatsuba | carries have no semiring meaning |
| D7 | Strassen tested both unchanged (CUTOFF 16, n = 17/24) and as a CUTOFF=1 copy (n ≤ 8) | unchanged only | below the cutoff Strassen *is* schoolbook; CUTOFF=1 gives n = 2 counterexamples, while the unchanged copy has only n ≥ 17 ones |
| D8 | Exact operation-count expressions as the claimed costs where lower-order terms matter (NTT, Kirchhoff, Held–Karp) | leading term only | leading-term fits missed tolerance in the first pass (NTT α = 0.9545, Kirchhoff 1.0542, Held–Karp 1.0518–1.0523); this is the practice of the NTT entry (RL-062) |
| D9 | No new entries written | writing up to 5 entries | ~2.5 h budget used by the engine and pilot; each entry needs its own harness, scaling family and V2 run; "If unsure, propose instead of writing" |
| D10 | Recorded run with trials ×5 | ×1 | tests are cheap (whole run 141.8 s); status counts were identical to the ×1 first pass (results/…firstpass) |
| D11 | MIRROR comparison flip by `Rev` injection *and* AST flips; naive flips without the sentinel flip kept as KILLED | dropping them | they show that a comparison flip needs the sentinels (±inf) flipped too: Dijkstra and Held–Karp on `Rev` return inf |

## 11. Dead ends, limits and open ideas

**Not run, or partial:**
- LCS and edit distance: no clean semiring reading of the repository code. The LCS DP takes the diagonal without
  max when characters match, a dominance shortcut valid only for (max,+) with unit weights. Matrix-chain was skipped
  as redundant with the optimal-BST recursion/cubic DP, which is TRIVIAL by construction (same expression DAG).
- Fibonacci fast doubling is covered by Mat2 square-and-multiply.
- Independent set ↔ vertex cover: no such pair in `pairs/`.
- The Bool permanent → bipartite matching link was not wired (input formats differ).
- LeftZero zeta is INCONCLUSIVE (no identity element).

**Limits:**
- Survival is evidence on small instances: n ≤ 8 for most differential tests, n ≤ 24 for Strassen and 450–1050
  tests per cell. It is not a proof.
- Property checks on infinite carriers use bounded sample domains.

*Forward-looking content is not published (RL-086).*

## 12. Proposed entries (not written; for the maintainer to decide)

*Forward-looking content is not published (RL-086).*

## 13. Draft RESEARCH_LOG entries (DRAFT, for the maintainer)

**DRAFT · DECISION · Mutation engine for pairs (mutations/).** Mutations act on problems and implementations, never on
cost formulas. The brute side, or a generic oracle over the substituted structure, defines the mutated problem. Fast
algorithms run as in-memory copies (unchanged on injected element types, or after targeted AST rewrites); `pairs/`
is never modified. Outcomes: SURVIVED / KILLED (shrunk counterexample) / TRIVIAL / INVALID / INCONCLUSIVE, plus a
NEAR-MISS flag. Survivors are measured by exact operation counts and fitted with `tools/validate.py`'s `fit_slope`
against a cost library with rivals. Rationale: decisions D1–D4 and D11 of research/2026-10-06d_mutation_pilot.md.

**DRAFT · VERIFIED · Operation-swap boundary map (agent report).** 369 mutants and 233 532 differential tests:
SURVIVED 176, KILLED 84, INVALID 69, TRIVIAL 39, INCONCLUSIVE 1. For every fast algorithm with mixed outcomes, a
mechanically checked property separates its survivors exactly:
- additive inverse: Strassen, Karatsuba, Ryser, Kirchhoff/Bareiss;
- additive inverse and 1+1 ≠ 0: FWHT;
- primitive root of the transform order: NTT;
- absorptivity: Dijkstra, FW/BF on cyclic digraphs, Knuth's speed-up;
- idempotent ⊕: FW/BF on DAGs, sparse table;
- power-associativity: square-and-multiply (octonions survive);
- distributivity: Kadane and Held–Karp in ⊕-form.

Correlation on 6–13 structures each, consistent with known algebra; no novelty claimed. Records: `mutations/records/2026-10-06d/`.

**DRAFT · VERIFIED · Ring embeddings rescue Strassen (pipeline rediscovery).** Integer Strassen on embedded inputs
computes the Boolean product (160 tests; ⊗ = 7^k·16³ exactly, α = 1.0), the (min,+) product through Yuval's
encoding (160 tests; pseudo-polynomial bit size), and the (max,min) product by thresholds (90 tests). Fischer–Meyer
1971, Munro 1971 and Yuval 1976 are [DOI OK].

**DRAFT · NEAR-MISS · Knuth's optimal-BST speed-up under (max,+).** KILLED: agreement 0.8662 over 800 tests,
subject/oracle in [0.6593, 0.9977], smallest counterexample p = (0,0,0), q = (0,0,0,1) (recursion 3, Knuth 2). It
survives on all absorptive selective structures tested. Literature: not found in the bibliographic records we
checked (Knuth 1971, Yao 1980 [DOI OK]; no full text read).

**DRAFT · NEAR-MISS · Stoer–Wagner as a max-cut algorithm (mirror).** Both negation and comparison flip are KILLED
(agreement 0.7413 / 0.7293 over 750 tests, ratio ≥ 0.708). Expected, since max cut is NP-hard (Karp 1972 [DOI OK]).

**DRAFT · NULL · MIRROR family.** All 19 MIRROR survivors are known trivial reparametrisations (negation, order dual,
affine complement, reciprocal weights). The 7 kills are expected: longest path, farthest pair, max cut. Scope: the
27 mutants of `targets.mirror_all` on 10 pairs.

**DRAFT · CORRECTED · Agent's own errors before the recorded run.** Eight items: late-binding closures in cost
lambdas; `max_cut_brute` at n = 2; DAG shrinker; relaxation → accumulation double count; Kirchhoff diagonal; root
search; watchdog for infinite loops; a removed invalid complement mutant. Details in section 9. The recorded run
postdates all fixes.

**DRAFT · CORRECTED · Literature identifiers.** Duan–Pettie 2009 is `10.1137/1.9781611973068.43`, not `.42`. The
Vassilevska–Williams–Yuster ToC 2009 DOI has no title in Crossref, so the STOC 2007 DOI `10.1145/1250790.1250876` is
cited as verified.

**DRAFT · INCONCLUSIVE · Two measurement gaps.** The Bool Floyd–Warshall ⊗-count fit gives α = 1.0372 against n³
(tolerance 0.03), because counting misses plain-literal operations under variable density; the algorithm makes n³
steps regardless. The LeftZero zeta transform cannot be tested because the oracle needs an identity.

## 14. Reproduction

```
set PYTHONIOENCODING=utf-8
.venv/Scripts/python.exe experiments/2026-10-06d_mut_pilot.py --trials-scale 5   # all mutants -> mutations/records/2026-10-06d/*.jsonl (141.8 s here)
.venv/Scripts/python.exe -m mutations props                                       # properties.jsonl
.venv/Scripts/python.exe experiments/2026-10-06d_mut_boundary_map.py              # counts, boundary map, separators (reads records only)
.venv/Scripts/python.exe experiments/2026-10-06d_mut_literature.py                # DOI checks (network, rate-limited)
.venv/Scripts/python.exe -m mutations summary                                     # one-line-per-mutant markdown table
.venv/Scripts/python.exe -m mutations run --only matmul,apsp                      # a subset
.venv/Scripts/python.exe -m unittest tests.test_mutations                         # 16 tests
```
The run is deterministic: instance seeds are `"2026-10-06d|<mutant id>|<n>|<trial>"`, scaling seeds are
`"2026-10-06d|scaling|<tag>|<n>"`, and counts are exact. Final checks after the run: `python -m unittest discover -s tests`
ran 178 tests, all OK (110 before this round, the 16 added here, and tests added by parallel agents);
`python tools/validate.py` gave 62/62 entries OK.

## 15. Files created

- `mutations/__init__.py`, `mutations/__main__.py`, `mutations/algebra.py`, `mutations/rewrite.py`, `mutations/engine.py`,
  `mutations/oracles.py`, `mutations/targets.py`, `mutations/literature.py`, `mutations/related_karatsuba.py`
- `mutations/records/2026-10-06d/`: `apsp.jsonl`, `dijkstra.jsonl`, `karatsuba.jsonl`, `matmul.jsonl`,
  `maxsubarray.jsonl`, `mirror.jsonl`, `ntt.jsonl`, `obst.jsonl`, `permanent.jsonl`, `power.jsonl`, `rmq.jsonl`,
  `spanning.jsonl`, `tsp.jsonl`, `xorconv.jsonl`, `zeta.jsonl`, `properties.jsonl`, `literature.jsonl`,
  `literature_queries.jsonl` (660 KB in total)
- `tests/test_mutations.py`
- `experiments/2026-10-06d_mut_pilot.py`, `experiments/2026-10-06d_mut_boundary_map.py`, `experiments/2026-10-06d_mut_literature.py`
- `research/2026-10-06d_mutation_pilot.md` (this report)
- Not committed (`results/` is gitignored): `results/2026-10-06d_boundary_map.md` (generated analysis output),
  `results/mutations_2026-10-06d_firstpass/` (first-pass records, trials ×1, before the closure fix)
