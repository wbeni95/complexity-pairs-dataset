Author: delegated research agent (Claude), for the maintainer.

# Round 2026-10-06f: seven known, named pairs as new verified entries

Date: 2026-10-06. Environment: Windows 11 Pro 10.0.26200, CPython 3.14.2 (project venv, jsonschema only); the
cross-version check also used CPython 3.12.10 (`py -3.12`). Two sub-agents (Claude) wrote three of the entries under
my direction (planar perfect matchings; Hamiltonian cycles and maximum-weight independent set). I re-ran their
validator checks, experiments and tests myself; numbers below marked "re-run" were reproduced by me, all others come
from my own scripts. No wall-clock V2 this round: every V2 is an exact count. No novelty is claimed; all seven pairs
are known results.

## 1. Summary

| # | Entry (pairs/…) | Tags | Level | V2 α per algorithm (tol 0.02, exact counts) | Rivals, all rejected (α) |
|---|---|---|---|---|---|
| 1 | horn-sat-brute-force-vs-unit-propagation | T2 | V2 | brute force 1.000; unit propagation 1.000 | 2ⁿ 1.081, n²2ⁿ 0.865; n log n 0.895, n² 0.500 |
| 2 | xor-sat-brute-force-vs-gaussian-elimination | T2 | V2 | brute force 1.000; Gaussian elimination 1.000 | 2ⁿ 1.120, n²2ⁿ 0.897; n² 1.439, n⁴ 0.720 |
| 3 | boolean-matrix-multiplication-naive-vs-strassen | T3 | V2 | schoolbook 1.000; Strassen over ℤ 1.000 | n^log₂7 1.069, n² 1.500; n³ 0.936, n² 1.404 |
| 4 | hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion | T6 + T8 | V2 | enumeration 1.000; inclusion–exclusion 1.000; Held–Karp count 1.000 | (n−1)! 1.071, n·n! 0.938, n²2ⁿ 2.130; n²2ⁿ 1.112, n⁴2ⁿ 0.897, 3ⁿ 0.923; n2ⁿ 1.144, n³2ⁿ 0.938, 3ⁿ 0.811 |
| 5 | planar-perfect-matchings-enumeration-vs-kasteleyn | T2 | V2 | enumeration 1.000; Kasteleyn + Bareiss 1.000 | 2^(n/2) 0.696, n·φ^(n/2) 0.885, n³ 2.464; n² 1.532, n⁴ 0.766, n³ log n 0.943 |
| 6 | max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp | T2 | V2 | exhaustive search 1.000; column DP 1.000 | 8ⁿ 1.130, n²8ⁿ 0.896, 4ⁿ 1.695; n² 0.501, n log n 0.862 |
| 7 | or-convolution-naive-vs-zeta-mobius | T3 | V2 | naive 1.000; zeta–Möbius 1.000 | n2ⁿ 1.562, 3ⁿ 1.262, n4ⁿ 0.877; 2ⁿ 1.149, n²2ⁿ 0.868, 3ⁿ 0.725 |

(α values from `tools/validate.py --scaling -v <entry>`, each run by me.)

All 7 entries pass `tools/validate.py <entry>` (V1) and `tools/validate.py --scaling <entry>` (V2) at tolerance 0.02.
Totals (computed with code from the per-entry numbers below):
- **V2:** 15 fits, all exact counts. Every α is 1.000 to three decimals, because each cost expression is the exact
  closed form, or proportional to it.
- **Rivals:** 38 declared, 38 rejected. The smallest rival distance is |α − 1| = 0.057 (Kasteleyn against n³ log n).
  The log-factor diagnostic is resolved in all 15 fits.
- **V1:** 674 instances and 1317 implementation runs (replays of `validate.run_v1`).
- **Oracle controls:** 16651 deliberately wrong outputs rejected, 64 left undecided (Hamiltonian cycles at
  n = 11..14), 0 accepted. Of the correct outputs, 3564 were accepted, 12 undecided (Hamiltonian cycles) and 0
  rejected.
- **Whole repository:**
  - `tools/validate.py` (V1, all entries): **69/69 OK** (62 existing + 7 new; 41.5 s).
  - `python -m unittest discover -s tests`: **274 tests OK**, 1 skipped (80.8 s). That includes 35 new tests in four
    files: 12 mine, 6 for planar, 17 for Hamiltonian cycles and MIS.
- **Cross-version:** the 15 V2 count series are identical under CPython 3.12.10 and 3.14.2.
- **Citations:** 28 identifiers checked, 0 problems.
- **Not regenerated:** index.json and the README table (build_index.py was off-limits this round). CI's index
  freshness check will therefore fail until `tools/build_index.py` is run.

## 2. Per entry

### 2.1 Horn-SAT — `pairs/horn-sat-brute-force-vs-unit-propagation` (T2, V2)

- **Problem and output.** Satisfiability of Horn CNF; the output is the least model or None. Brute force scans masks
  0..2ⁿ−1 and stops at the first satisfying assignment, which for a Horn formula is exactly the least model (models are
  closed under intersection, and every model contains the least one bit by bit). Both implementations therefore return
  the same tuple, and V1 compares them with `==`.
- **Algorithms.** Brute force with early exit per clause; Dowling–Gallier unit propagation with clause counters and
  occurrence lists (raises ValueError on a clause with two positive literals).
- **Oracle.** Naive forward chaining (full passes until no change; no counters, no occurrence lists). It accepts an
  assignment only if it equals the derived set and satisfies every clause, and None only if the derived set violates a
  clause (a proof). For n ≤ 10 it also cross-checks by exhaustive search.
- **Instance families (V1).** Random Horn CNF (ratios 0.5–4, widths 1–4); planted derivation chains, satisfiable and
  unsatisfiable; repeated literals, tautologies, unit goals, empty clauses; definite-clause formulas; the V2 family under
  renaming. V1 battery: 56 instances, 104 implementation runs (scratchpad replay of `validate.run_v1`).
- **V2 family Hₙ** (designed so that brute force cannot stop early and fails late):
  (¬x₁ ∨ ¬xⱼ ∨ xⱼ₊₁) for j = n−1 down to 2, then (x₁), (¬x₁ ∨ x₂), (¬xₙ). It is unsatisfiable, so all 2ⁿ assignments
  are examined, and the half with x₁ false passes the n − 2 star clauses before failing at (x₁).
  - Brute force: exactly E(n) = (2n + 13)·2ⁿ⁻² − 2n − 4 literal evaluations, 6 counted operations each. I derived this
    twice: by solving for the coefficients on n = 3..7 and testing n = 3..16, and by hand: (n−1)·2ⁿ⁻¹ for x₁ false,
    plus 15·2ⁿ⁻² − 2n − 4 for x₁ true (clause Sⱼ is reached by (n−j+1)·2^(j−1) assignments, at 2.5 evaluations on
    average). [experiment: horn_sat, section 1]
  - Unit propagation: exactly 12n − 7 (by inspection: building 7n − 5, propagation 5n − 2; confirmed for n = 3..300
    and the V2 sizes). [experiment, section 2]
  - On Hₙ, naive forward chaining needs exactly n full passes (n = 3..200), i.e. Θ(n²) clause visits, so the family
    separates linear propagation from the quadratic naive method. [experiment, section 3]
- **V2 fits** (validator, re-checked by the experiment): brute force α = 1.000 against (2n+13)·2ⁿ − 8n − 16 on
  n = 8..16, rivals 2ⁿ 1.081 and n²·2ⁿ 0.865 rejected; propagation α = 1.000 against 12n − 7 on n = 1000..32000, rivals
  n log n 0.895 and n² 0.500 rejected. The bare n·2ⁿ would give 0.961, outside the band, so the exact form is used
  (RL-062). The log-factor diagnostic is resolved in both fits.
- **Oracle control** ([experiments/2026-10-06f_entries_horn_sat.py](../experiments/2026-10-06f_entries_horn_sat.py)):
  1040 instances (n = 0..12). All 1040 correct outputs were accepted. All 2816 wrong outputs were rejected: 465 flipped
  bits, 271 strictly larger models, 505 None for satisfiable formulas, 535 all-false assignments for unsatisfiable
  formulas, 1040 wrong lengths.
- **Uncounted work.** The counter decrements use plain clause indices and are not counted. They are O(L) and bounded by
  the counted reads; stated in the caveats.

### 2.2 XOR-SAT and #XOR-SAT — `pairs/xor-sat-brute-force-vs-gaussian-elimination` (T2, V2)

- **One entry for decision and counting** (decision log D2). Output (count, witness); `equal` compares counts and
  witness existence, and `check` verifies the witness.
- **Input.** The dense augmented matrix [A | b]. Brute force pays 2n + 1 counted operations per row evaluation whatever
  the row's sparsity; elimination works on dense rows.
- **Algorithms.**
  - Brute force: examines all 2ⁿ assignments (counting cannot stop at the first solution), abandoning an assignment at
    its first violated row.
  - Forward Gaussian elimination: first-row pivot, eliminating below only. Consistency test, count 2^(n−r), and a
    witness by back substitution.
- **Oracle (certificate-based, independent).**
  - Packs the rows into integers and builds an XOR basis keyed by the *highest* coefficient, tracking the combination of
    input rows behind each basis vector.
  - "No solution" is accepted only with a re-verified combination equal to 0 = 1.
  - A count is accepted only if it equals 2^(n−r): r re-verified independent combinations bound the rank from below;
    n − r null-space vectors, verified against every input row, plus a verified witness bound the count from below.
  - For n ≤ 10 it also counts exhaustively (itertools.product).
- **Instance families (V1).** Random dense, sparse 3-XOR, planted consistent, planted plus a contradicting row-sum,
  rank-deficient (repeats, sums, zero rows), the V2 family permuted. 60 instances, 108 runs.
- **V2 family Xₙ.** Rows: all ones; x₁ + x_{k+1} + … + xₙ for k = 2..n; b from a planted solution. It has full rank,
  so every prefix of rows is independent and consistent.
  - Brute force: exactly (2n + 1)(2ⁿ⁺¹ − 2), since row i is reached by 2ⁿ⁻ⁱ assignments; checked for n = 1..16.
  - Elimination: the first row turns all others into prefixes x₂ + … + x_k, the maximal elimination pattern: exactly
    n(n² + 6n − 4)/3 operations. Derived from the loop structure: tests n(n+1)/2, XORs (n−1)n(2n+5)/6, back
    substitution n(n−1); checked for n = 1..200 and 256.
  - Exactly the same counts hold for every n × n full-rank system for brute force; the elimination count is specific to
    Xₙ.
- **V2 fits.** Brute force α = 1.000 on n = 8..16, rivals 2ⁿ 1.120 and n²·2ⁿ 0.897 rejected. Elimination α = 1.000 on
  n = 16..128, rivals n² 1.439 and n⁴ 0.720 rejected. The bare n³ would give 0.959 (outside the band); the bare n·2ⁿ
  gives 0.996.
- **Oracle control** ([experiments/2026-10-06f_entries_xor_sat.py](../experiments/2026-10-06f_entries_xor_sat.py)): all
  1020 correct outputs accepted. All 4348 wrong outputs rejected: count + 1, count × 2, count / 2, (0, None) for
  consistent systems, a claimed solution for inconsistent ones, a violating witness, a missing witness. That is 2868 at
  n ≤ 10 (exhaustive count active) and 1480 at n = 11..40, where only the certificates decide.
- **Boundary**, with citations in the entry: affine is Schaefer's tractable class for decision. By the Creignou–Hermann
  dichotomy, affine languages are the only ones counted in polynomial time, so #2-SAT and #Horn-SAT are #P-complete
  while #XOR-SAT is easy. Valiant 1979 (SIAM J. Comput.) is cited for #P-completeness of counting satisfying
  assignments.

### 2.3 Boolean matrix multiplication — `pairs/boolean-matrix-multiplication-naive-vs-strassen` (T3, V2)

- **Algorithms.**
  - Schoolbook Boolean AND/OR with no early exit: n³ ANDs on every input.
  - Integer Strassen on the 0/1 embedding (cutoff 16, power-of-two padding), then P[i][j] > 0. The code is a
    self-contained copy of the repository's integer Strassen; the entry states that all integers have O(log n) bits.
- **Oracle.** Row union with bitmasks: row i of C is the OR of the rows of B selected by row i of A. No inner products.
- **V1.** n = 0..10, 17, 31, 40, 64; densities 0.05–0.9; zero, all-ones, identity and permutation factors. 45 instances,
  90 runs.
- **V2.** CountingInt counts scalar products (integer multiplications, or ANDs). On n = 16, 32, 64, 128: schoolbook
  exactly n³; Strassen exactly 7^(log₂(n/16))·16³ = 4096, 28672, 200704, 1404928. Both α = 1.000. Rivals: schoolbook
  n^log₂7 1.069 and n² 1.500; Strassen n³ 0.936 and n² 1.404; all rejected.
- **Oracle control** ([experiments/2026-10-06f_entries_boolean_matmul.py](../experiments/2026-10-06f_entries_boolean_matmul.py)):
  240 correct products accepted. All 906 wrong outputs rejected: 240 flipped entries, 132 integer products AB (where
  they differ from C), 157 transposes, 137 products BA, 240 wrong shapes.
- **Negative controls** (same experiment). The same Strassen code run directly on Boolean values gives wrong products
  on 25 of 40 random instances with + and − read as OR, and on 33 of 40 with XOR (arithmetic mod 2). This isolates the
  mutation-pilot finding (RL-080, section 5): the embedding into ℤ, not the code, rescues Strassen.
- **Padding.** At n = 17 (padded to 32) the count is 24832, not 28672, because products of two padding zeros (plain
  integers) are not counted; V2 uses powers of two only. Stated in the caveats.
- **Transitive closure** is mentioned with citations (the titles of Fischer–Meyer and Munro; Warshall) but not
  implemented (decision D3).

### 2.4 Counting Hamiltonian cycles — `pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion`

(T6 primary, T8 secondary, V2.) Written by sub-agent A; re-run by me: validator V1 and V2, experiment, tests.

- **Problem.** Directed Hamiltonian cycles of a digraph given as a 0/1 matrix, each counted once.
  - Conventions: n ≤ 1 gives 0, n = 2 gives A[0][1]·A[1][0].
  - For symmetric matrices with n ≥ 3 the answer is twice the undirected count.
- **Tags.** The decision problem is NP-complete (Karp 1972), and a graph is Hamiltonian iff the count is positive, so
  a polynomial counting algorithm would give P = NP: T6 primary. n! → 2ⁿ·poly(n): T8 secondary. #P-completeness is
  not claimed, since no source with such a title was checked.
- **Algorithms.**
  - Permutation enumeration: stops at the first missing arc, so Θ(n!) is its worst case.
  - Inclusion–exclusion over T ∋ 0: closed walks of length n by a walk DP, Θ(n) numbers of memory.
  - Held–Karp/Bellman counting DP over (subset, end vertex): Θ(n·2ⁿ) memory.
  - Correctness of both DPs is proved in entry.json.
  - Recorded trade-off: inclusion–exclusion is slower by Θ(n) but needs polynomial memory.
- **Oracle.**
  - Closed forms valid at every n: complete digraph (n−1)!; minus one arc (n−1)! − (n−2)!; not strongly connected 0;
    single directed cycle 1; Cₙ 2; unequal bipartite sides 0; K_{m,m} m!(m−1)!.
  - Otherwise a DFS count, complete for n ≤ 10 and capped at 200 000 nodes above.
  - Of the 112 validator instances, 109 were judged exactly. The other 3 (n = 14) were judged by necessary conditions:
    degree-product bounds, and an even count for symmetric inputs. Re-run.
- **V1.** 112 instances, 296 runs, re-run. Enumeration runs up to n = 9, inclusion–exclusion up to 12, Held–Karp on
  all sizes. The closed forms agreed with exhaustive DFS on 39 graphs. The Petersen graph is used as a computed test
  only (0 cycles in all four methods), with no claim attached.
- **V2 on Kₙ.** CountingInt counts truth tests, comparisons and +, −, × on entry-derived values.
  - Enumeration: exactly n!.
  - Inclusion–exclusion: exactly n(n−1)(n+2)·2ⁿ⁻² + 2ⁿ⁻¹ − 1.
  - Held–Karp: exactly (n−1)(n−2)·2ⁿ⁻² + 2(n−1).
  - Derived by hand and confirmed for n = 2..10, 2..13 and 2..16. Both DP counts are identical on random graphs,
    because nothing branches on an entry.
  - Fits: α = 1.000 for all three; rivals in the summary table. Bare leading terms: n³2ⁿ gives 0.993 (inclusion–
    exclusion), and n²2ⁿ gives 1.031 (Held–Karp, outside the band), hence the exact forms.
- **Oracle control** (experiments/2026-10-06f_entries_hamiltonian.py, re-run), 410 instances:
  - 3535 wrong outputs: ±1, ×2, ÷2 (the undirected count), ×n (counted once per start vertex), (n−1)!, negative,
    float, bool, None. 3471 rejected, 64 undecided (n = 11: 4, 12: 30, 13: 16, 14: 14), **0 accepted**.
  - Correct outputs: 398 accepted, 12 undecided, 0 rejected.
  - Above n = 10 the V1 evidence for general graphs is the pairwise agreement of inclusion–exclusion and Held–Karp
    (n ≤ 12); the entry states this.
- **Sub-agent self-corrections.**
  - A caveat figure: it first said (n−1)²·2ⁿ⁻²; the correct membership-test count is (n−1)²(2ⁿ⁻² − 1), verified in
    experiment §9.
  - An n = 2 generator gave answer 0 on 8 of 8 validator seeds. The draw order was changed; now 5 of 8 have answer 1.

### 2.5 Planar (grid) perfect matchings — `pairs/planar-perfect-matchings-enumeration-vs-kasteleyn` (T2, V2)

Written by sub-agent B; re-run by me (validator V1 and V2, experiment, 6 unit tests: all reproduced).

- **Problem.** The dimer partition function of the a × b grid with non-negative integer edge weights (weight 0 = edge
  absent), as (a, b, W) with W a full N × N matrix. 0/1 weights count the perfect matchings of spanning subgraphs; unit
  weights count domino tilings. The size parameter is n = N. Vertex deletions (holes) cannot be expressed; the entry
  says so.
- **Algorithms.**
  - Backtracking enumeration: match the first unmatched vertex to its right or lower neighbour.
  - Kasteleyn signs (+1 horizontal, (−1)^c on the vertical edge in column c) on the black × white matrix, then the
    Bareiss determinant and its absolute value.
  - The entry proves the sign rule: alternating cycles, Euler's formula f = p + l − 1, and the inner vertices matched
    among themselves.
- **Oracle.** A transfer-matrix (broken-profile) DP at width min(a, b), sharing no code with the implementations. The
  experiment validates that oracle against:
  - Fibonacci numbers on ladders (80) and parity on paths (122);
  - brute force over (N/2)-edge subsets on all 35 shapes with N ≤ 12 (350);
  - transposition (200);
  - a product-of-cosines formula for unit rectangles up to 10 × 10 (100; a numerical cross-check, source not cited);
  - the permanent of the black × white matrix (112).

  0 failures in all of them.
- **V1.** 280 instances, 520 runs (re-run), n = 0..144; the enumeration runs up to n = 48.
- **V2 family:** the unit (n/2) × 2 ladder.
  - Enumeration: exactly L(n/2 + 2) − 3 multiplications (Lucas numbers), proven from the recursion
    E(m) = E(m−1) + E(m−2) + 3 and checked for even n = 2..60. α = 1.000 on n = 16..52. Rivals 2^(n/2) 0.696,
    n·φ^(n/2) 0.885 and n³ 2.464 rejected.
  - Kasteleyn: exactly (n−2)n(n−1)/8 multiplications and divisions, checked for even n = 2..120 and 256, and equal on
    297 random instances with non-zero answers (53 needed a row swap). α = 1.000 on n = 16..256. Rivals n² 1.532,
    n⁴ 0.766 and n³ log n 0.943 rejected. The bare n³ would give 1.021, outside the band.
- **Oracle control** (re-run): 270 correct accepted. All 1334 wrong outputs rejected: answer ± 1, 2 × answer, float and
  bool types, the unit-weight count ignoring W, |det| and det of the unsigned matrix, the signed det without abs.
- **Negative control (the signs do real work).** |det| of the unsigned matrix is wrong on 286 of 480 even-N instances,
  starting with the unit 2 × 2 grid: det [[1,1],[1,1]] = 0 against the answer 2. det K is negative on 39 of them, and
  its sign is constant per shape (109 shapes).
- **Orientation matters for the enumeration.** On the 2 × m ladder numbered along the long side the count is
  Θ(m·φ^m), e.g. 684816 against 271440 at m = 24, with a derived closed form checked for m = 1..24. The entry documents
  this and uses the m × 2 orientation.
- **My edits to B's entry** (wording only, no numbers changed):
  - removed a caveat sentence naming an unimplemented alternative determinant route;
  - replaced "the classical cosine product" by "a product-of-cosines formula … (a numerical cross-check only)", in the
    README, entry.json and the experiment docstring, because its attribution is unchecked.
- **Boundary**, with citations: the 0/1 permanent (= counting bipartite perfect matchings) is #P-complete (Valiant 1979,
  TCS); planar graphs escape through the signed determinant. Linked to `pairs/permanent-naive-vs-ryser`.

### 2.6 Maximum-weight independent set on bounded-pathwidth grids — `pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp`

(T2, V2.) Written by sub-agent A; re-run by me: validator V1 and V2, experiment, tests.

- **Problem.** k × n grid with per-square diagonal codes 0–3 (all 3 = the king's graph) and non-negative vertex
  weights. Output (value, optimal set); `equal` compares values.
  - Why diagonals: a square with a diagonal contains a triangle, so the graph is not bipartite.
  - Without diagonals the problem reduces to a minimum cut, a reduction proved in the entry itself, so plain grids
    would already be polynomial by max-flow. The entry says so, and says the flow method is not implemented.
- **Algorithms.**
  - Exhaustive search over all 2ᴺ subsets: every subset's weight summed in full, no early exit.
  - Column DP over the path decomposition: bags are two adjacent columns, width 2k − 1. States are the F_{k+2}
    column-independent masks, with all F_{k+2}² pairs tested per column.
- **Parameter dependence**, stated explicitly in the entry:
  - linear in n for every fixed k;
  - Θ(F_{k+2}²·n) = Θ(φ^(2k)·n) in k;
  - exponential in n for square grids (k = n), though not in N = n²;
  - k-dependence at n = 20, as DP additions for k = 1..8: 58, 97, 195, 352, 647, 1159, 2066, 3645 (re-run).
- **Oracle.** Verifies the returned set (distinct vertices, independent, exact weight). It compares the value with a
  vertex-by-vertex DP over the last k + 1 vertices in column-major order: a different decomposition (width k + 1) and
  different code.
- **V1.** 88 instances, 136 runs (re-run); the two algorithms are compared on 48 instances. 600 extra instances, 0
  failures.
- **V2.** 3 × n king's graph, seeded weights 1..9; additions only are counted (comparisons tallied separately and
  excluded).
  - Exhaustive search: exactly 3n·2^(3n−1), fitted as n·8ⁿ (proportional), on n = 2..6. N·2^(N−1) also holds on 77
    random instances with any k and zero weights.
  - DP: exactly 10n − 5 = n·P₃ + (n−1)·F₅, on n = 100..3200. The general form holds on 420 random instances with
    positive weights.
  - With zero weights the DP count misses up to 6 additions (59 of 420 instances), because two plain zeros meet.
    Documented; the V2 family has positive weights.
- **Oracle control** (experiments/2026-10-06f_entries_mis_pathwidth.py, re-run): 330 instances.
  - 3393 wrong outputs, **all rejected**: ±1 with the same set; suboptimal sets with honest weight; non-independent
    sets with honest weight, including the optimum computed without diagonals; duplicate and out-of-grid vertices;
    the empty set; wrong types.
  - All 510 correct outputs accepted.

### 2.7 OR convolution — `pairs/or-convolution-naive-vs-zeta-mobius` (T3, V2)

- **Algorithms.** All index pairs, 2·4ⁿ ring operations. Zeta(f), zeta(g), pointwise product, Möbius:
  (3n + 2)·2ⁿ⁻¹ ring operations. The existing zeta entry is untouched.
- **Oracle.** The zeta identity ζ(h)[S] = ζ(f)[S]·ζ(g)[S] for **every** S, with ζ computed by submask enumeration
  (Θ(3ⁿ), not the Yates passes). ζ is invertible, so the check is complete at every n. For n ≤ 10 it also evaluates
  the definition at 6 seeded sets.
- **V1.** n = 0..8, 10 (zeta–Möbius also 11): 33 instances, 63 runs.
- **V2.** Counts exactly 2·4ⁿ (n = 0..10) and (3n + 2)·2ⁿ⁻¹ (n = 1..16).
  - Naive: α = 1.000 against 4ⁿ on n = 3..8; rivals n·2ⁿ 1.562, 3ⁿ 1.262 and n·4ⁿ 0.877 rejected.
  - Fast: α = 1.000 against (3n+2)·2ⁿ on n = 4..16; rivals 2ⁿ 1.149, n²·2ⁿ 0.868 and 3ⁿ 0.725 rejected.
  - The 3ⁿ rival separates the fast method from the naive zeta transform's cost.
- **AND convolution** is the complement mirror (A ∩ B = S iff ∁A ∪ ∁B = ∁S). It was checked for both implementations
  on n = 0..9 (100/100) and is recorded as a note, not as a separate pair.
- **Oracle control** ([experiments/2026-10-06f_entries_or_convolution.py](../experiments/2026-10-06f_entries_or_convolution.py)):
  86 correct accepted. All 383 wrong outputs rejected: 86 off-by-one entries, 71 AND convolutions, 72 XOR convolutions,
  76 results without the Möbius step, 78 wrong lengths.
- **Bug I made and fixed** (F1). The first `check` tested the zeta identity on 48 sampled sets for n > 8. The control
  showed it missed 4 of the 86 off-by-one errors, because a changed entry is seen only by its supersets. I replaced it
  with the complete submask check before any V1 run was recorded. A unit test now pins three single-entry errors at
  n = 11.

## 3. Citation checks

Script: [experiments/2026-10-06f_entries_sources.py](../experiments/2026-10-06f_entries_sources.py) (external: Crossref,
DataCite fallback, arXiv). It uses the matching rules of `tools/check_sources.py`: title overlap ≥ 70%, year ± 1 (± 3
for arXiv), and volume, issue and pages parsed from the venue string. Rate limits were ≤ 1 request/s to Crossref and
≤ 1 per 3 s to arXiv, over one connection, with the project User-Agent.

**Result: 27 sources, 28 identifiers (27 DOIs + 1 arXiv id), 0 problems.** Every source cited by the seven entries is
in that list.

| Entry | Sources (all DOI OK; volume, issue and pages as registered) |
|---|---|
| Horn-SAT | Dowling & Gallier 1984, J. Logic Programming 1(3) 267–284; Horn 1951, J. Symbolic Logic 16(1) 14–21; Minoux 1988, IPL 29(1) 1–12; Schaefer 1978, STOC 216–226; Cook 1971, STOC 151–158 |
| XOR-SAT | Schaefer 1978; Creignou & Hermann 1996, Inf. Comput. 125(1) 1–12; Valiant 1979, SIAM J. Comput. 8(3) 410–421 |
| BMM | Fischer & Meyer 1971, SWAT 129–131; Munro 1971, IPL 1(2) 56–58; Strassen 1969, Numer. Math. 13 354–356; Warshall 1962, J. ACM 9(1) 11–12 |
| Hamiltonian cycles | Kohn, Gottlieb & Kohn 1977, ACM '77 294–300; Karp 1982, ORL 1(2) 49–51; Bax 1993, IPL 47(4) 203–207; Held & Karp 1962, J. SIAM 10(1) 196–210; Bellman 1962, J. ACM 9(1) 61–63; Karp 1972, Complexity of Computer Computations 85–103 |
| MIS (pathwidth) | Arnborg & Proskurowski 1989, DAM 23(1) 11–24; Bodlaender 1996, SIAM J. Comput. 25(6) 1305–1317; Robertson & Seymour 1983, JCTB 35(1) 39–61; Karp 1972 |
| Planar matchings | Kasteleyn 1961, Physica 27(12) 1209–1225 (Crossref title: "The statistics of dimers on a lattice"); Temperley & Fisher 1961, Phil. Mag. 6(68) 1061–1063; Valiant 1979, TCS 8(2) 189–201; Bareiss 1968, Math. Comp. 22(103) 565–578. Elkies, Kuperberg, Larsen & Propp 1992 (also arXiv math/9201305) was checked but is not cited, because the input format cannot express Aztec diamonds |
| OR convolution | Björklund, Husfeldt, Kaski & Koivisto 2007, STOC 67–74; Kennes 1992, IEEE Trans. SMC 22(2) 201–223 |

Left out because they cannot be checked: Furman 1970 (Soviet Math. Dokl., no DOI), Kasteleyn 1967 (book chapter, no
DOI), Yates 1937 (book).

**Content claims resting on source text that was not checked** (only bibliographic data was checked):
- Horn 1951 as the origin of the name; Schaefer 1978 for the Horn and affine tractable classes; Cook 1971 for the
  NP-completeness of SAT.
- Creignou–Hermann's counting dichotomy (affine ⇒ FP, otherwise #P-complete) and the consequence for #2-SAT and
  #Horn-SAT; Valiant 1979 (SIAM) for #P-completeness of counting satisfying assignments.
- Fischer–Meyer and Munro for the reduction of BMM to integer multiplication (their titles support only the BMM and
  transitive-closure link); Warshall for Θ(n³) transitive closure.
- BHKK 2007 for the covering product.
- Valiant 1979 (TCS) for the #P-completeness of the 0/1 permanent; Kasteleyn 1961 as the method behind the signed
  determinant. The sign rule itself is proved in the entry.
- Sub-agent A's entries:
  - Karp 1972 for the NP-completeness of Hamiltonian circuit (directed and undirected), CLIQUE and NODE COVER.
  - Kohn–Gottlieb–Kohn, Karp 1982 and Bax as origins of inclusion–exclusion counting.
  - Bellman and Held–Karp for the (subset, end vertex) recurrence.
  - Arnborg–Proskurowski for DP over bounded-width decompositions (general terms only; no claim that MWIS is among
    their listed problems).
  - Robertson–Seymour for path-width.
  - Bodlaender: the note matches its title.

## 4. Cross-version check of the exact counts

Script: [experiments/2026-10-06f_entries_cross_version.py](../experiments/2026-10-06f_entries_cross_version.py). It
recomputes every V2 count series with the validator's seeding.

Run under CPython 3.14.2 (venv) and 3.12.10 (`py -3.12`): 15 series (all algorithms of all 7 entries).
**Identical value for value**, with the same SHA-256 `83584d1fcd62afe31d98c7ebe15aa1bfa7ccbb4bd93808ff40cafaed7620e71a`
on both. An earlier run over the five entries then finished (10 series) also matched (`5f689870…`).

None of my four entries passes counted values through `sorted`, `min` or `max` (RL-069). The planar entry applies
`abs()` once, which counts nothing.

## 5. Not finished, and why

- **Transitive closure** (decision D3). I left it out as a separate entry because its count-based V2 conflicts with
  unchanged, natural code. Repeated squaring and Fischer–Meyer/Munro divide-and-conquer both threshold integer products
  back to 0/1 between Boolean products. `1 if p > 0 else 0` yields plain integers, so the next product's operations
  would no longer be counted. Keeping the count would need an unnatural threshold such as `p // p`, or a V1-only entry.
  The BMM entry mentions transitive closure with checked citations.
- Every entry in the target list was written; none is in `staging/`.
- Sub-agents A and B finished all three delegated entries at V2.

## 6. Decision log

| # | Decision | Alternatives considered | Evidence that settled it |
|---|---|---|---|
| D1 | Horn-SAT returns the least model, so V1 compares with `==` | compare satisfiability only (as 2-SAT does) | the first satisfying mask of a Horn formula is its least model (proof in brute_force.py); 520 sanity instances and the 56-instance V1 battery agree exactly |
| D2 | One XOR entry answering decision and counting | two entries | elimination gives both at once; a counting brute force examines all 2ⁿ anyway; a decision-only entry would duplicate the code with an early stop. The counting side carries the boundary (Creignou–Hermann) |
| D3 | BMM only; transitive closure not implemented | TC with Warshall vs repeated squaring vs Fischer–Meyer/Munro divide-and-conquer | thresholding between stages breaks input-derived counting (section 5); no wall-clock V2 this round |
| D4 | Dense [A \| b] input for XOR-SAT | sparse variable lists | dense rows give exact, structure-independent brute-force counts on every full-rank system, and input-derived entries for elimination |
| D5 | Worst-case V2 families built per algorithm order (Hₙ, Xₙ) | random instances | random clause order makes brute force fail early (2-SAT entry caveat). Xₙ is the maximal forward-elimination pattern and still has full rank, so the brute-force formula holds |
| D6 | Exact closed forms as cost expressions everywhere (RL-062) | bare leading terms | bare n·2ⁿ (Horn) 0.961 and bare n³ (XOR) 0.959 fall outside 0.02; bare n³ (Kasteleyn) 1.021 likewise |
| D7 | Schoolbook BMM without early exit | `any()`-style early exit | exact n³ on every input; the early-exit variant is still Θ(n³) worst case (stated in caveats) |
| D8 | OR convolution only; AND as a checked mirror note | two entries | complementation is a reindexing (the mutation pilot classes such mirrors as trivial); 100/100 mirror checks |
| D9 | Delegate three entries to two sub-agents and do all citation checks centrally | all seven myself | time; network rules (one connection, rate limits) are easiest to keep with one checker |
| D10 | Rival sets: neighbouring exponents plus the competing algorithm's cost | single rival | every fit rejects at least two rivals, and the log-factor diagnostic is resolved in every fit |
| D11 (B) | Size parameter n = N (vertices) for the planar entry; V2 on the m × 2 ladder | ladder length; 2 × m orientation | one meaning of n for all V1 shapes; on 2 × m the enumeration is Θ(m·φ^m) (684816 vs 271440 at m = 24) |
| D12 (B) | Kasteleyn matrix built densely from W with negation only | structural plain zeros | every entry is input-derived, so all Bareiss arithmetic is counted. The sub-agent states this as an argument, not tested |
| D13 (A) | Hamiltonian cycles: count everything on entry-derived values | count products only | nothing branches on an entry, so the DP counts are input-oblivious (equal on random graphs) |
| D14 (A) | MIS: count additions only | include comparisons | the comparison count depends on the number of independent sets and has no clean closed form |
| D15 (A) | MIS returns an optimal set | value only | makes the oracle certificate-based (set verified, value compared) |

## 7. Failures, bugs fixed, near-misses

- **F1 (bug, fixed).** The sampled OR-convolution oracle missed 4 of 86 single-entry errors at n ≥ 9; it was replaced by
  the complete check (section 2.7).
- **F2 (fixed before any run).** A Bash heredoc in this shell collapsed `\\` to `\`, which left an invalid escape
  (SyntaxWarning) in the zeta–Möbius docstring. I reworded it and compiled every new file with warnings as errors:
  clean.
- **F3 (removed claims).** I removed two uncited statements from my own drafts: a sentence on "four Russians" savings
  (BMM notes), and one saying elimination via fast matrix multiplication exists (XOR caveats and README). Neither could
  be backed by a checked source.
- **NEAR-MISS N1.** For the OR convolution, the bare n·2ⁿ would also pass (α 0.989), so here the exact form is a choice,
  not a necessity. Stated in the caveats.
- **NEAR-MISS N2 (sub-agent B).** On the 2 × m orientation the ladder enumeration is Θ(m·φ^m), not Θ(φ^m). A V2 on that
  orientation against φ^m would have mis-stated the cost, and the rival n·φ^(n/2) guards against it.
- **F4 (sub-agent A, fixed).** The Held–Karp caveat first stated (n−1)²·2ⁿ⁻² membership tests; the correct figure,
  (n−1)²(2ⁿ⁻² − 1), was verified in the experiment.
- **F5 (sub-agent A, fixed).** The MIS n = 2 generator gave answer 0 on 8 of 8 validator seeds (seed luck). The draw
  order was changed; 5 of 8 now have answer 1.
- **F6 (sub-agent B, noted).** The "−1 on every vertical edge" signing turned out to equal the unsigned matrix up to row
  and column signs (480/480). It is kept in the experiment, labelled as not an independent control.
- **NEAR-MISS N3 (sub-agent A).** The Hamiltonian-cycle oracle cannot decide 64 of 3535 wrong outputs at n = 11..14,
  for general graphs where neither a closed form nor the capped DFS applies. None was accepted; the entry rests on
  inclusion–exclusion/Held–Karp agreement there.
- **Edits by me to B's entry:** see section 2.5 (wording only).

## 8. Notes for the validator and schema (no change made)

- The validator now prints `shape …: SKIPPED (no_shape_block)` for all my entries (the other agent's change in
  progress). None of the new entries has a `shape` block. The counts at n = 2ᵏ (BMM, Kasteleyn) and on consecutive n
  (XOR brute force, OR convolution, zeta-type counts) are the kind of sequences the shape diagnostic targets.
- I have no change to request.

## 9. Draft RESEARCH_LOG entries (DRAFT; for the maintainer to edit and number)

**RL-A · VERIFIED · Seven known pairs added at V2 (exact counts, rivals)** — DRAFT
Agent report (round 2026-10-06f; research/2026-10-06f_new_entries.md). Three of the seven were written by
sub-agents and re-run by the agent.

| Entry | Tags | V2 (exact counts, tol 0.02) |
|---|---|---|
| horn-sat-brute-force-vs-unit-propagation | T2 | brute force 6((2n+13)2ⁿ⁻² − 2n − 4) on an unsatisfiable family ordered so that half the assignments fail late; unit propagation 12n − 7 |
| xor-sat-brute-force-vs-gaussian-elimination | T2 | brute force (2n+1)(2ⁿ⁺¹ − 2); elimination n(n² + 6n − 4)/3 on a maximal-elimination full-rank family |
| boolean-matrix-multiplication-naive-vs-strassen | T3 | n³ ANDs vs 7^(log₂(n/16))·16³ multiplications (integer Strassen on the 0/1 embedding) |
| hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion | T6 + T8 | n! vs n(n−1)(n+2)2ⁿ⁻² + 2ⁿ⁻¹ − 1 vs (n−1)(n−2)2ⁿ⁻² + 2(n−1) |
| planar-perfect-matchings-enumeration-vs-kasteleyn | T2 | L(n/2+2) − 3 vs (n−2)n(n−1)/8 (n = vertices, unit ladder) |
| max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp | T2 | 3n·2^(3n−1) vs 10n − 5 (3 × n king's graph) |
| or-convolution-naive-vs-zeta-mobius | T3 | 2·4ⁿ vs (3n+2)·2ⁿ⁻¹ |

- **Fits:** 15, all α = 1.000. 38 rivals, all rejected; the smallest distance is 0.057 (Kasteleyn vs n³ log n). The
  log factor is resolved in every fit.
- **Closed forms:** each count was derived and then confirmed over a range of n (listed per entry).
- **V1:** 674 instances, 1317 runs.
- **Oracle controls:** 16651 wrong outputs rejected, 64 undecided (Hamiltonian cycles at n = 11..14, documented),
  0 accepted.
- **Boundaries recorded with citations:**
  - #XOR-SAT is easy while #2-SAT and #Horn-SAT are #P-complete (Creignou–Hermann 1996);
  - planar perfect matchings are a signed determinant while the 0/1 permanent is #P-complete (Valiant 1979);
  - Horn and XOR are tractable Schaefer classes, while CNF-SAT is NP-complete (Cook 1971).
- **Whole repository:** validator 69/69 OK; unit tests 274 OK (1 skipped).

**RL-B · DECISION · Entry scope in round 2026-10-06f** — DRAFT
1. XOR-SAT and #XOR-SAT form one entry, with output (count, witness), because elimination answers both at once.
2. AND convolution is recorded as the complement mirror of the OR entry, not as a separate pair (checked 100/100).
3. Boolean matrix multiplication is added without transitive closure (see RL-E).
4. Every cost expression is the exact closed form or proportional to it (RL-062). Bare leading terms would fail the
   0.02 band in three fits: Horn n·2ⁿ 0.961, XOR n³ 0.959, Kasteleyn n³ 1.021.

**RL-C · CORRECTED · Agent and sub-agent self-corrections before any recorded run** — DRAFT
- **OR-convolution oracle.** It tested the zeta identity on 48 sampled sets for n > 8 and missed 4 of 86 single-entry
  errors (a changed entry is seen only by its supersets). It was replaced by a complete O(3ⁿ) submask check; a unit
  test pins the case.
- **Uncited claims removed:** "four Russians" savings (BMM) and elimination via fast matrix multiplication (XOR-SAT).
- **Planar entry wording:** "classical cosine product" (unchecked attribution) became a numerical cross-check note,
  and a sentence naming an unimplemented alternative was removed.
- **Hamiltonian cycles:** a caveat figure, (n−1)²·2ⁿ⁻², was corrected to (n−1)²(2ⁿ⁻² − 1).
- **MIS:** the n = 2 generator gave answer 0 on all validator seeds; the draw order was fixed.

**RL-D · VERIFIED · Exact counts of the new entries are identical across Python versions** — DRAFT
`experiments/2026-10-06f_entries_cross_version.py` under CPython 3.14.2 and 3.12.10 (the version CI uses): 15 series,
identical, SHA-256 83584d1f…. No count passes through sorted/min/max (RL-069).

**RL-E · INCONCLUSIVE · Transitive closure not added: count-based V2 conflicts with natural code** — DRAFT
Repeated squaring and the Fischer–Meyer/Munro divide-and-conquer both threshold integer products back to 0/1 between
Boolean products. A natural threshold (`1 if p > 0 else 0`) returns plain integers, so later operations would not be
counted. A count-preserving threshold would be unnatural code, and wall-clock V2 was excluded this round.

**RL-F · VERIFIED · Citations of the new entries** — DRAFT
`experiments/2026-10-06f_entries_sources.py`, external: 27 sources, 28 identifiers (Crossref; arXiv for one), 0
problems on title, year, volume, issue and pages. Left out as unverifiable: Furman 1970, Kasteleyn 1967, Yates 1937.
Content claims resting on unchecked source text are listed in section 3 of the report.

**RL-G · NEAR-MISS · Orientation-dependent enumeration cost and undecided oracle cases** — DRAFT
- **Ladder orientation.** On the 2 × m ladder numbered along the long side, the planar enumeration is Θ(m·φ^m), not
  Θ(φ^m): 684816 against 271440 at m = 24, with a closed form checked for m = 1..24. V2 uses the m × 2 orientation,
  and the rival n·φ^(n/2) is rejected (α 0.885).
- **Undecided cases.** The Hamiltonian-cycle oracle leaves 64 of 3535 wrong outputs undecided at n = 11..14 (none
  accepted).

## 10. Reproduction

From the repository root, with `export PYTHONIOENCODING=utf-8`:

```
.venv/Scripts/python.exe experiments/2026-10-06f_entries_sources.py            # network; ~40 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_horn_sat.py            # ~4 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_xor_sat.py             # ~40 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_boolean_matmul.py      # ~8 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_or_convolution.py      # ~3 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_planar_matchings.py    # ~24 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_hamiltonian.py        # ~35 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_mis_pathwidth.py       # ~5 s
.venv/Scripts/python.exe experiments/2026-10-06f_entries_cross_version.py > a.txt
py -3.12 experiments/2026-10-06f_entries_cross_version.py > b.txt               # same sha256 line expected
for e in horn-sat-brute-force-vs-unit-propagation xor-sat-brute-force-vs-gaussian-elimination \
         boolean-matrix-multiplication-naive-vs-strassen or-convolution-naive-vs-zeta-mobius \
         planar-perfect-matchings-enumeration-vs-kasteleyn hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion \
         max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp; do
  .venv/Scripts/python.exe tools/validate.py pairs/$e
  .venv/Scripts/python.exe tools/validate.py --scaling -v pairs/$e
done
.venv/Scripts/python.exe -m unittest discover -s tests
.venv/Scripts/python.exe tools/validate.py
```

## 11. Files created

All paths are relative to the repository root. Runs also created `__pycache__/` folders, which are not listed.

**Entries (7 folders, 37 files)**
- `pairs/horn-sat-brute-force-vs-unit-propagation/`: entry.json, README.md, harness.py, implementations/brute_force.py,
  implementations/unit_propagation.py
- `pairs/xor-sat-brute-force-vs-gaussian-elimination/`: entry.json, README.md, harness.py,
  implementations/brute_force.py, implementations/gaussian_elimination.py
- `pairs/boolean-matrix-multiplication-naive-vs-strassen/`: entry.json, README.md, harness.py, implementations/naive.py,
  implementations/strassen_over_integers.py
- `pairs/or-convolution-naive-vs-zeta-mobius/`: entry.json, README.md, harness.py, implementations/naive.py,
  implementations/zeta_mobius.py
- `pairs/planar-perfect-matchings-enumeration-vs-kasteleyn/` (sub-agent B): entry.json, README.md, harness.py,
  implementations/enumeration.py, implementations/kasteleyn_bareiss.py
- `pairs/hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion/` (sub-agent A): entry.json, README.md, harness.py,
  implementations/enumeration.py, implementations/inclusion_exclusion.py, implementations/held_karp_counting.py
- `pairs/max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp/` (sub-agent A): entry.json, README.md,
  harness.py, implementations/brute_force.py, implementations/column_dp.py

**Experiments**
- `experiments/2026-10-06f_entries_sources.py`
- `experiments/2026-10-06f_entries_horn_sat.py`
- `experiments/2026-10-06f_entries_xor_sat.py`
- `experiments/2026-10-06f_entries_boolean_matmul.py`
- `experiments/2026-10-06f_entries_or_convolution.py`
- `experiments/2026-10-06f_entries_cross_version.py`
- `experiments/2026-10-06f_entries_planar_matchings.py` (B)
- `experiments/2026-10-06f_entries_hamiltonian.py` (A)
- `experiments/2026-10-06f_entries_mis_pathwidth.py` (A)

**Tests**
- `tests/test_entries_2026_10_06f.py`
- `tests/test_entries_2026_10_06f_planar.py` (B)
- `tests/test_entries_2026_10_06f_hamiltonian.py` (A)
- `tests/test_entries_2026_10_06f_mis.py` (A)

**Report:** `research/2026-10-06f_new_entries.md` (this file).

No other repository file was modified. The other agent's `experiments/2026-10-06f_shape_survey.py` shares the round
prefix but is not mine.

