# Eight classical complexity pairs added on 2026-10-07

**Author:** delegated research agent (Claude), for the maintainer.
**Environment:** Windows 11 Pro 10.0.26200, CPython 3.14.2 (project `.venv`). Other agents were running CPU-heavy jobs on the same machine at the same time.
**Status of the numbers.** Every α below comes from a run of `tools/validate.py --scaling -v` (labelled *validator*) or from a probe script in `experiments/` (labelled *probe*), all made in this session.
These are **console** results in the sense of RESEARCH_LOG: I did not use `--record`, because it calls `git` and I was told never to run git, so nothing was written to `ledger/runs/`.
Deterministic counts (operation counts, oracle controls, pass counts) come from `experiments/2026-10-07_*.py` scripts, and rerunning them reproduces the numbers exactly.
**Not done, because those files were off-limits to me:** RESEARCH_LOG.md entries, index.json, `tools/build_index.py`.

## Summary

| Entry (pairs/…) | Tags | Level | Oracle (independent) | V2 α, validator runs 1 / 2 / 3 / final |
|---|---|---|---|---|
| all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall | T3 | **V2** | heap Dijkstra from every source | BF×n vs n²(n−1)²: 0.973 / 0.973 / 0.972 / 0.973 · FW vs n³: 0.926 / 0.923 / 0.917 / 0.925 |
| longest-palindromic-substring | T3 | **V2** | direct verifier (palindrome; no window of length L+1, L+2; leftmost) | brute vs n³: 0.971 / 0.972 / 0.969 / 0.966 · expand vs n²: 1.008 / 0.998 / 1.008 / 1.007 · Manacher vs n: 1.015 / 1.011 / 1.019 / 1.009 |
| element-distinctness-pairs-vs-sorting | T3 | **V2** | `len(set(values)) == n` | pairs vs n²: 1.004 / 0.991 / 1.004 / 1.002 · merge sort vs n log n: 0.999 / 0.997 / 0.995 / 1.000 |
| chromatic-number-subset-dp-vs-inclusion-exclusion | T6 + T8 | **V2** | backtracking k-colouring (n ≤ 14) | DP vs 3ⁿ: 0.980 / 0.983 / 0.986 / 0.986 · BHK vs n·2ⁿ: 0.982 / 0.984 / 0.990 / 0.988 |
| range-minimum-queries-naive-vs-sparse-table | T3 | **V2** | iterative segment tree | scan vs n²: 1.016 / 1.014 / 1.004 / 1.017 · sparse table vs n log n: 1.014 / 1.007 / 1.007 / 1.006 |
| bipartite-matching-kuhn-vs-hopcroft-karp | T3 | **V2** (adversarial family) | Edmonds-matrix rank mod 2⁶¹−1 (Schwartz–Zippel, error < 10⁻¹⁵) | Kuhn vs n³: 0.975 / 0.979 / 0.975 / 0.981 · HK vs n^2.5: 0.978 / 0.985 / 0.979 / 0.975 |
| max-flow-edmonds-karp-vs-dinic | T3 | **V1** (V2 INCONCLUSIVE) | minimum over all s–t cuts (n ≤ 14) | not claimed. Probe: EK vs n⁵ 0.558, Dinic vs n⁴ 0.479 |
| 3sat-brute-force-vs-schoening | T6 + T8 | **V1** (V2 not claimed) | DPLL solver | not claimed. Probe: Schöning vs (4/3)ⁿn^2.5 0.960 but vs 2ⁿ 0.865 |

All eight pass `tools/validate.py` at their claimed level, also in a final combined run (8/8 OK). The whole-repo V1 run gives 54/54 OK.
The unit tests pass: `python -m unittest discover -s tests`, 84 tests, OK.
`tools/check_sources.py`, run on the eight entry folders only (none has an arXiv id), checked 25 identifiers, including volume, issue and pages for all 25, and found 0 problems. Two sources have no DOI: Knuth TAOCP (ISBN) and Dinic 1970.

**Oracle controls** ([experiments/2026-10-07_oracle_controls.py](../experiments/2026-10-07_oracle_controls.py), deterministic). On the exact V1 batteries, every oracle accepted every correct output it judged and rejected every deliberately perturbed one:

| Entry | Judged | Perturbed answers rejected | Composition / notes |
|---|---|---|---|
| APSP | 70 | 56/56 | 14 had nothing finite to perturb |
| Palindromes | 108 | 108/108 | |
| Element distinctness | 84 | 84/84 | 47 yes / 37 no |
| Chromatic number | 90 | 90/90 | |
| RMQ | 70 | 65/65 | |
| Matching | 111 | 111/111 | 3 not judged (a side > 160) |
| Max flow | 66 | 66/66 | 12 not judged (n > 14) |
| 3-SAT | 84 | 84/84 | 53 satisfiable / 31 unsatisfiable |

## Per entry

### 1. all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall: T3, V2
- **Claim.** Bellman–Ford from every source with exactly n − 1 passes (no early exit) costs Θ(n²m). On complete digraphs that is exactly n²(n−1)² relaxations, so Θ(n⁴). Floyd–Warshall makes exactly n³ steps on every input (no skip on D[i][k] = ∞).
- **Probe** ([apsp_timing_probe](../experiments/2026-10-07_apsp_timing_probe.py)):
  - Round 1: BF α = 0.975 against n²(n−1)² and 1.021 against n⁴ (n = 6..24); FW α = 0.909 (n = 16..128).
  - Round 2: BF α = 0.972 (n = 8..40); FW α = 0.918 (n = 32..200), with local slopes rising from 0.90 to 0.97 as n grows. The deficit is a lower-order effect.
- **Discrimination.** For pure powers, the fitted α scales with the exponent ratio. BF's measured exponent is ≈ 4 × 0.97 ≈ 3.9, so a fit against n³ would fail (≈ 1.3). FW's is ≈ 3 × 0.92 ≈ 2.8, so a fit against n⁴ would fail (≈ 0.69). The V2 check therefore does separate n⁴ from n³ here.
- **DOIs verified:** Floyd 1962 (10.1145/367766.368168), Warshall 1962 (10.1145/321105.321107), Johnson 1977 (10.1145/321992.321993), Williams 2018 (10.1137/15M1024524), Vassilevska Williams & Williams 2018 (10.1145/3186893).
  Bellman 1958 **does** have a DOI, 10.1090/qam/102435. The AMS registered it, and its title and 16(1), 87–90 match Crossref. The brief had expected none.

### 2. longest-palindromic-substring: T3, V2
- **Output.** (L, leftmost start), so that answers are unique and the oracle can verify them.
- **Worst case is aⁿ for all three algorithms.** The comparison counts were checked exactly ([palindrome_probe](../experiments/2026-10-07_palindrome_probe.py)):
  - brute force equals Σ_L (n−L+1)⌊L/2⌋ (2 743 440 at n = 320; n³/12 = 2 730 667);
  - expansion equals n²/2 + n/2 (51 360);
  - Manacher makes 2n − 3 comparisons (637).
  - On a random {a,b} string at n = 320: 100 431 / 1 596 / 1 095 comparisons (≈ n², ≈ 5n, ≤ 4n).
- **Probe.** Brute force α = 0.945 over n = 30..240 with small-n curvature, then 0.968 over 40..320 (the range used). Expansion 1.009. Manacher 1.004 on aⁿ and 0.960 on the mixed random strings.
- **DOIs verified:** Manacher 1975 (10.1145/321892.321896; the title says "smallest initial palindrome"), Apostolico–Breslauer–Galil 1995 (10.1016/0304-3975(94)00083-U).
  **Caveat:** neither paper could be read (publisher pages returned HTTP 403). The attribution "ABG observed that Manacher's algorithm finds all maximal palindromes" comes from Wikipedia, a secondary source, and the entry says so.

### 3. element-distinctness-pairs-vs-sorting: T3, V2
- **Implementations.** All pairs: exactly n(n−1)/2 comparisons on yes-instances. Explicit bottom-up merge sort plus a neighbour scan: Θ(n log n) on every input.
- **lower_bounds:** Ω(n log n) in the algebraic computation tree model over the reals (Ben-Or 1983, 10.1145/800061.808735, verified). The entry states that the bound is for real-valued inputs and does not automatically carry over to integer-exploiting models.
- **Hashing.** Expected O(n) with universal hashing is mentioned in the caveats, citing Carter & Wegman 1979 (10.1016/0022-0000(79)90044-8, verified). It is not implemented.
- **Probe.** The same merge-sort timings gave α = 1.001 against n log n, 1.125 against n (inside the tolerance) and 0.558 against n² (rejected). As for every n log n entry, the log factor is not resolvable.
- **Dropped:** Yao 1991 (10.1137/0220041). The DOI resolves ("…Functions with Finite Domains") and the paper was considered for the integer-input lower bound, but its content could not be checked.

### 4. chromatic-number-subset-dp-vs-inclusion-exclusion: T6 primary, T8 secondary, V2
- **Subset DP (what is implemented).** T ranges over *all* non-empty independent subsets of S. The inner loop makes exactly 3ⁿ − 2ⁿ iterations on every input; this was checked by count for n = 6..12.
  It is **not** Lawler's algorithm, which restricts T to maximal independent sets and runs in O((1+3^(1/3))ⁿ) ≈ O(2.4423ⁿ). The entry says this explicitly.
- **Inclusion–exclusion.** c_k = Σ_S (−1)^(n−|S|) a(S)^k, where a(S) counts the non-empty independent sets inside S. a is tabulated with BHK's recurrence (4.1), in complemented form. Then k = 1, 2, … is tried with one multiplication and one addition per subset per round.
  - Exact operation count: (2χ(G) + 2)·2ⁿ arithmetic operations on integers of at most n·χ(G) bits (≤ 180 bits at n = 18 here).
  - That is O(n·2ⁿ) with unit-cost arithmetic and O(n⁴·2ⁿ) bit operations with schoolbook multiplication.
  - BHK's own Proposition 1 uses repeated squaring instead: O(2ⁿ n k polylog(nk)) time to decide χ ≤ k.
- **Timing family.** G(n, 0.8). The χ of the V2 instances is 4, 5, 4, 6, 6, 7, 7, 8, 8, 8, 8, 9, 10 for n = 6..18, so χ/n ∈ [0.50, 0.71] and the number of rounds grows linearly over the measured range. The entry states that this is not an asymptotic claim about G(n, 0.8).
- **Probe.** The DP gave α = 0.963 over n = 6..12, and 7..13 was chosen. BHK gave 0.954 against n·2ⁿ, 1.069 against 2ⁿ (the factor n is not resolvable) and 0.674 against 3ⁿ (rejected).
- **Sources.**
  - Lawler 1976 (10.1016/0020-0190(76)90065-X): the DOI was verified, but the **paper itself was not read**. The 2.4423 bound is quoted from BHK's Table 1.2 and from Eppstein 2003's abstract and introduction.
  - BHK 2009 (10.1137/070683933): read in the authors' open-access version.
  - Moon & Moser 1965 (10.1007/BF02760024), Eppstein 2003 (10.7155/jgaa.00064), Karp 1972 (10.1007/978-1-4684-2001-2_9).
  - The text checks can be reproduced with [source_text_checks](../experiments/2026-10-07_source_text_checks.py).

### 5. range-minimum-queries-naive-vs-sparse-table: T3, V2
- **Setup.** q = n queries, and the timing family uses long queries (each longer than n/2). The total scanned length is 0.7475 / 0.7531 / 0.7496·n² at n = 800 / 1200 / 1600.
- **Probe.** The sparse table gave α = 0.989 against n log n and 1.100 against n, so the log factor is not resolvable.
- **DOIs verified:** Bender & Farach-Colton 2000 (10.1007/10719839_9), Fischer & Heun 2011 (10.1137/090779759).

### 6. bipartite-matching-kuhn-vs-hopcroft-karp: T3, V2 on a justified adversarial family
- **Family G_k** (n = V = 4k² + k, E = 2k⁴ + k²). It is a disjoint union of two gadgets:
  - K_{2a,a} with a = k². Its a unmatchable left vertices make each failing Kuhn search, and every HK phase, scan the whole gadget.
  - Paths P₂, P₄, …, P_{2k}. They are numbered and ordered so that HK's first phase takes the wrong edge of every path; phase j then repairs only path j.
- **Exact counts** ([bipartite_matching_counts](../experiments/2026-10-07_bipartite_matching_counts.py)):
  - HK ran **exactly k + 1 phases** for every k = 2, 4, …, 16.
  - Kuhn's edge scans / (V·E) = 0.1446, 0.1432, 0.1432, 0.1434, 0.1436, 0.1439, 0.1440 for k = 4..16.
  - HK's edge scans / (E·√V) = 1.0501 down to 1.0144.
  - The matching sizes equal the analytic maximum k² + k(k+1)/2.
- **Why the counts are needed.** Timing alone cannot separate the exponents ([bipartite_matching_probe](../experiments/2026-10-07_bipartite_matching_probe.py)). Kuhn also passes against n^2.5 (α = 1.168), and HK passes against n² and n³ (1.221 and 0.815). The measured exponents are ≈ 2.90 (Kuhn) and ≈ 2.43 (HK).
- **DOIs verified:** Hopcroft & Karp 1973 (10.1137/0202019), Berge 1957 (10.1073/pnas.43.9.842), Kuhn 1955 (10.1002/nav.3800020109).
  **Dropped:** the remark "Dinic runs in O(E√V) on unit-capacity bipartite networks" (Even & Tarjan 1975, 10.1137/0204043). The DOI resolves, but the paper's content was not checked.

### 7. max-flow-edmonds-karp-vs-dinic: T3, V1 (INCONCLUSIVE for V2)
- **Probe on random dense networks** ([max_flow_probe](../experiments/2026-10-07_max_flow_probe.py)):

  | n | E | EK augmentations | V·E | Dinic phases |
  |---|---|---|---|---|
  | 20 | 191 | 21 | 3 820 | 4 |
  | 40 | 770 | 40 | 30 800 | 3 |
  | 80 | 3 182 | 87 | 254 560 | 2 |
  | 160 | 12 754 | 176 | 2 040 640 | 3 |

  - Timing α: EK 0.558 against n⁵ (0.924 against n³); Dinic 0.479 against n⁴ (0.965 against n²).
- **No family attaining either bound was built,** so V2 is not claimed.
- **DOIs verified:** Edmonds & Karp 1972, Ford & Fulkerson 1956 (10.4153/CJM-1956-045-5), Zadeh 1972 (10.1145/321679.321693; cited only by its title, not read). Dinic 1970 is cited by venue (no DOI).

### 8. 3sat-brute-force-vs-schoening: T6 primary, T8 secondary, V1
- **Error control is explicit.**
  - p(n) = Σⱼ C(n,j)2⁻ⁿC(3j,j)(1/3)^(2j)(2/3)^j is a lower bound on the success probability of one try.
  - Exactly, p(n)·√n/(3/4)ⁿ lies in [0.87, 0.89] for n = 14..20.
  - The restart budget is T(n) = ⌈ln(10⁶)/p(n)⌉: 196 tries at n = 6, 1682 at n = 12, 22371 at n = 20 ([schoening_restart_budget](../experiments/2026-10-07_schoening_restart_budget.py)).
  - The one-sided error is ≤ 10⁻⁶ per call. The V1 battery has 53 satisfiable formulas, so a fresh-randomness failure has probability ≤ 53·10⁻⁶ (union bound). Runs are reproducible under the validator's seeding.
- **Why not V2:** see Near-misses.
- **DOIs verified:** Schöning 1999 (10.1109/SFFCS.1999.814612; Crossref gives no year), Cook 1971 (10.1145/800157.805047).

## Near-misses

1. **Schöning, V2 not claimed (timing cannot discriminate).** On the unsatisfiable family (random 3-CNF, m = 5n, plus the 8 clauses on (x1,x2,x3)), the n = 4..12 timings gave:
   - α = 0.960 against (4/3)ⁿn^2.5;
   - 1.225 against (4/3)ⁿn^1.5;
   - 2.082 against (4/3)ⁿ alone;
   - **0.865 against 2ⁿ**.

   Over the range pure Python can time, the polynomial factors dominate, and the fit cannot tell the claimed bound from brute force's 2ⁿ. On unsatisfiable inputs the runtime is in any case set by the restart budget, by construction.
   Measured per-step cost: 8.1 to 17.3 clause checks (0.20 to 0.30·m), i.e. Θ(m) per step ([3sat_timing_probe](../experiments/2026-10-07_3sat_timing_probe.py)).
2. **Schöning, planted unique-solution family (the brief's suggestion) does not attain the bound.** Six values of n (6..16), 5 instances each, 4000 tries per instance; uniqueness was checked by enumeration ([schoening_planted_success](../experiments/2026-10-07_schoening_planted_success.py)).
   - Mean per-try success: 0.4915, 0.2885, 0.2451, 0.1338, 0.0905, 0.0720.
   - p(n): 0.0706 … 0.0022.
   - Smallest instance ratio p̂/p(n): 5.92, 5.66, 13.16, 13.87, 15.02, 14.40.
   - Empirical base ≈ 0.822 per variable, against 0.708 for p(n) over the same range.

   The bound held on all 30 instances, but the family is far from the worst case.
3. **Max flow, downgraded to V1.** On random dense networks both algorithms are far below their bounds (numbers in entry 7). Fits against n⁵ and n⁴ would fail, and fits against the measured growth would not test the claimed bounds.
4. **Matching, timing cross-fits pass for the wrong exponents.** See entry 6. V2 is claimed only because the deterministic counts pin the family's behaviour, phase by phase. Without them it would have been V1.
5. **Factors that tolerance 0.25 cannot resolve.** These pass V2, but the fit confirms only near-linear (or 2ⁿ) growth, which each entry states:
   - log n for merge sort: α = 1.001 against n log n vs 1.125 against n;
   - log n for the sparse table: 0.989 vs 1.100;
   - the factor n in inclusion–exclusion: 0.954 vs 1.069 against 2ⁿ.
6. **Floyd–Warshall's α is below 1.** It was 0.909 to 0.926 in all runs. Local slopes rise from 0.87–0.90 at small n to 0.97 at n = 160–200, consistent with lower-order Θ(n²) overhead. It passes, but it is the lowest α among the V2 claims.
7. **RMQ, contention spike.** The first probe showed local slopes of 1.398 and then 0.495 around n = 1200 (21.4 ms). Two reruns gave 17.0 and 16.2 ms there (α = 1.013 and 1.009), so it was not reproducible: machine contention.
8. **My own errors, caught and corrected.**
   - The palindrome probe's first "random" string was built with a new `Random` per character, which made it constant. The counts were therefore identical to aⁿ. This was fixed before any number was used.
   - The APSP early-exit experiment's docstring predicted "3–4 passes, not growing with n" before the run. The run showed 3.25 → 5.22 passes (n = 8 → 64). The text was corrected, and the correction is recorded in the docstring.
   - The max-flow entry's V1 justification was drafted before its probe ran. It was replaced by the measured numbers.
9. **Bellman–Ford with early exit would have broken the Θ(n⁴) claim on the timing family.** Mean passes per source were 3.25, 3.44, 4.53 and 5.22 for n = 8..64, against n − 1. A descending-path family restores (n+1)/2 passes on average ([apsp_bellman_ford_early_exit](../experiments/2026-10-07_apsp_bellman_ford_early_exit.py)).

## Decision log

| Decision | Alternatives considered | Evidence that decided |
|---|---|---|
| Bellman–Ford without early exit, Floyd–Warshall without the D[i][k] = ∞ skip | the usual optimisations | Early exit makes random complete digraphs easy (near-miss 9), so the cost would depend on the input. Without the optimisations the cost is exactly n²(n−1)² and n³ on every input. |
| LPS output (L, leftmost start), checked by a direct O(nL) verifier | return the substring (ties make it non-unique); an O(n²) DP oracle | The verifier needs no second algorithm and judges all 108 V1 instances, up to n = 5000. Any longer palindrome contains one of length L+1 or L+2. |
| LPS timing on aⁿ only | random strings | The counts show random strings are Θ(n²)/Θ(n) for brute force/expansion, so only aⁿ tests the stated worst cases. |
| Explicit merge sort in element distinctness | `sorted()` (Timsort, C code) | It keeps the comparison-model cost explicit and both timings in pure-Python bytecode. Hashing was not implemented, because it is randomized and Python's integer hash is not universal. |
| Plain subset DP for χ (3ⁿ − 2ⁿ exactly) | Lawler's maximal-IS version | The brief asks for the variant actually implemented to be stated. The plain DP has an exact count; Lawler's needs an MIS enumerator and has no exact count. |
| BHK with k = 1, 2, … and non-empty independent sets | binary search on k with repeated squaring (BHK Prop. 1); counting the empty set too | The count (2χ+2)·2ⁿ is exact and simple. Non-empty sets match BHK's Lemma 7 and recurrence (4.1). |
| G(n, 0.8) as the χ timing family | G(n, ½) (smaller χ, fewer rounds); K_n (χ = n but trivial) | χ/n ∈ [0.50, 0.71] for n ≤ 18, so the rounds grow linearly over the measured range on non-trivial graphs. |
| RMQ: q = n long queries; explicit scan loop | `min(a[l:r+1])` (C speed) | Pure-Python loops on both sides keep the per-operation cost uniform. Long queries are needed for the quadratic worst case. |
| Iterative DFS in Kuhn, HK and Dinic | recursion with a raised recursion limit | Search paths can be long: in the K_{2a,a} gadget a Kuhn search descends through chains of matched vertices, and flow paths can have up to V − 1 edges. The depth was not measured. An iterative DFS avoids any dependence on Python's recursion limit. |
| HK removes each augmented path's left vertices for the rest of the phase | the common variant without removal | Removal makes the paths in a phase provably vertex-disjoint, exactly HK's maximal set. Correctness is the same either way. |
| Adversarial matching family as a disjoint union of two gadgets | random graphs (HK only 2–5 phases); one gadget only (Kuhn Θ(VE) but HK Θ(E)) | Each gadget attacks one algorithm. Together, with a = k², they give both worst cases on one family, confirmed by exact counts. |
| Edmonds-matrix rank as the matching oracle | a max-flow oracle (also augmenting paths) | Algebraic and independent of augmenting paths, with Schwartz–Zippel error < 10⁻¹⁵ per instance and a deterministic seed. |
| Brute-force minimum-cut oracle for max flow (n ≤ 14) | a third flow algorithm (push-relabel) | The max-flow min-cut theorem makes cut enumeration an independent oracle, with no shared code. |
| Schöning with first falsified clause in input order, T(n) from the explicit p(n) | random falsified clause; a fixed number of restarts | Schöning's analysis allows any falsified clause. The explicit p(n) gives a stated error ≤ 10⁻⁶ instead of an unspecified constant. |
| Schöning and max flow at V1 | claim V2 on unsatisfiable inputs (by-construction budget) or on random networks | Near-misses 1–3. |
| No `--record` | recording the runs in the ledger | `--record` runs `git status` / `git rev-parse`, and I was told never to run git. |
| Read open versions of sources (authors' PDF of BHK, Eppstein's JGAA PDF) | cite from memory | The publisher pages returned 403. Statements not found in readable text were dropped: Lawler's exact polynomial factor, Eppstein's improved base, Even–Tarjan, Yao 1991. |

## Open ideas

1. **Operation-count V2 (`measure: "reported"`) for classical algorithms whose exponent gaps are smaller than the tolerance** (matching, Schöning, Strassen). Exact counts discriminated what timing could not (entry 6). This needs a maintainer decision on extending RL-010 beyond query models.
2. **Max flow to V2.** Implement Zadeh's (1972) bad networks for Edmonds–Karp, and search for or construct a Dinic family with Θ(V) phases of Θ(VE) blocking-flow work. The counting harness in `max_flow_probe` can be reused to confirm such a family before any timing.
3. **Schöning, closer to the bound.** Clauses with exactly one literal true under a* make every useful flip succeed with probability exactly 1/3, but the complement of a* then satisfies the formula too and attracts the walk. Mixing in all-true clauses placed last in the clause order might break that symmetry. An incremental list of falsified clauses (O(1) per flip on bounded-occurrence formulas) would extend the timeable n range, so that the exponential could dominate the polynomial factors.
4. **Lawler's maximal-independent-set DP as a third χ algorithm** (needs an MIS enumerator), and the BHK polynomial-space variant (their Proposition 7).
5. **Element distinctness on integers.** Read Yao 1991 to decide whether the Ω(n log n) bound extends to integer inputs. Add universal hashing as a randomized third algorithm (expected O(n)).
6. **RMQ with linear preprocessing** (Bender–Farach-Colton or Fischer–Heun) as a third algorithm. Note that V2 could not separate it from the sparse table (log factor only).
7. **A stronger V2 diagnostic.** The validator's single global slope hides curvature (Floyd–Warshall). Reporting local slopes, or requiring α against the *next lower* candidate cost to fail, would make V2 discriminate (for example, Schöning would then fail against 2ⁿ).
8. **Robustness of the matching family to scan order.** Shuffling the adjacency lists probably destroys the HK phase structure. Measuring this would show how implementation-specific the family is.

## Files

- **New entries:** `pairs/<id>/` for the eight ids above. Each folder has entry.json, a hand-written README.md, harness.py and implementations/.
- **Experiments**, all `experiments/2026-10-07_*.py`, each with a docstring stating what it tried and what came out:
  - `probe_helpers` (shared timing helper);
  - `apsp_timing_probe`, `apsp_bellman_ford_early_exit`;
  - `palindrome_probe`;
  - `element_distinctness_probe`;
  - `chromatic_probe`;
  - `rmq_probe`;
  - `bipartite_matching_counts`, `bipartite_matching_probe`;
  - `max_flow_probe`;
  - `3sat_timing_probe`, `schoening_planted_success`, `schoening_restart_budget`;
  - `oracle_controls`, `doi_lookups`, `source_text_checks`.
- **Mechanical generation:** none. No entry was generated mechanically, so there is no T7 material.
