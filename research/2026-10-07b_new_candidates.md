# New candidate entries, batch 2026-10-07b

Author: coordinating research agent (delegated by the maintainer), with four sub-agents (one entry each: global
minimum cut, optimal BST, 2-SAT, spanning-tree counting). Every entry was re-validated by the coordinator.

Status: **8 new entries in `pairs/`, all claiming and passing V2.** Seven of them use only exact reported counts with
rivals (RL-047). One algorithm, spanning-tree enumeration, uses timing; the reason is given below.
- Unit tests: 91 OK.
- check_sources run on each new folder: 0 problems.
- Not touched: RESEARCH_LOG.md, index.json, existing entries, tools/, schema/, lib/, tests/. No git was run.

**Provenance labels used below:**

| Label | Meaning |
|---|---|
| [val] | validator output (`tools/validate.py <entry> --scaling -v`) on 2026-10-07 |
| [exp: name] | `experiments/2026-10-07b_<name>.py`, deterministic, with the outcome in its docstring |
| [proof] | closed form derived by hand (derivation in the entry) and checked against the counts at every n in the experiment |
| [data] | closed form read off the data, not proven |
| [DOI OK] | resolved with `lookup_doi`; venue details matched with `crossref_record` |

## 0. Environment problem found

The repo `.venv` has **jsonschema 3.2.0**, which has no `Draft202012Validator`. `tools/validate.py` therefore exits
with "jsonschema is required" in that venv. `requirements.txt` asks for `jsonschema>=4.18`.
- The likely cause is the cffconvert 2.0.0 install of RL-053: cffconvert, pykwalify and pyrsistent sit in the same
  site-packages, and cffconvert 2.x pins jsonschema 3 (recalled, not checked).
- I did not modify `.venv`. All validation and unit tests here ran in a scratch venv built from `requirements.txt`
  (CPython 3.14.2, jsonschema 4.26.0), outside the repo.

## 1. Summary

| Entry | Tags | Level | Measure | Algorithms: α (tolerance) | Rivals (α, all rejected) |
|---|---|---|---|---|---|
| `xor-convolution-naive-vs-walsh-hadamard` | T3 | V2 | ring ops (+ − × //) | naive 1.000 (0.05); FWHT 0.987 (0.05) | naive: n2ⁿ 1.587, n4ⁿ 0.885; FWHT: 2ⁿ 1.162, n²2ⁿ 0.858, 4ⁿ 0.581 |
| `subset-sum-zeta-transform-naive-vs-yates` | T3 | V2 | additions | naive 1.000 (0.02); Yates 1.000 (0.02) | naive: n2ⁿ 1.315, n3ⁿ 0.886, 4ⁿ 0.792; Yates: 2ⁿ 1.161, n²2ⁿ 0.877, 3ⁿ 0.733 |
| `regex-matching-backtracking-vs-thompson` | T2 | V2 | symbol–char comparisons | backtracking 0.974 (0.035); memoised 0.981 (0.05); Thompson 0.981 (0.05) | bt: 2ⁿ 1.131, n²2ⁿ 0.854, n² 3.386; poly: n 1.962, n³ 0.654, n2ⁿ 0.058 |
| `global-min-cut-brute-vs-stoer-wagner` | T2 | V2 | weight additions + comparisons | brute 1.002 (0.03); Stoer–Wagner 1.007 (0.03) | brute: n³ 2.838, 2ⁿ 1.305, n2ⁿ 1.134, n³2ⁿ 0.897; SW: n²2ⁿ 0.037, n⁴ 0.755, n² 1.510, n² log³n 1.128 |
| `optimal-bst-recursion-vs-dp-vs-knuth` | T2 + T3 | V2 | cost comparisons | recursion 1.002 (0.04); cubic DP 1.001 (0.04); Knuth 1.010 (0.04) | rec: 2ⁿ 1.587, 4ⁿ 0.794, 4ⁿ/n^1.5 0.923; cubic: n² 1.501, n⁴ 0.750; Knuth: n³ 0.674, n 2.021, n log n 1.668, n² log n 0.914 |
| `two-sat-brute-force-vs-scc` | T2 | V2 | operations on input-derived literals | brute 1.000 (0.02, cost (n+7)·2ⁿ); APT 0.999 (0.02) | brute: 2ⁿ 1.077, n²2ⁿ 0.862; APT: n log n 0.895, n² 0.500 |
| `spanning-tree-count-enumeration-vs-kirchhoff` | T2 | V2 | enumeration: **time**; Kirchhoff: mult./div. counts | enumeration 0.980 (0.25; other runs 0.961, 0.995); Bareiss 1.014 (0.03, cost (n−1)³) | enum: n! 1.566, 2ⁿ 4.199; Bareiss: n⁴ 0.781, n² 1.562 |
| `nand-tree-evaluation-deterministic-vs-randomized` | T4 + T3 | V2 | leaf reads (randomized: mean of 200) | left-first 1.000 (0.02); randomized 0.995 (0.05) | left-first: λⁿ 1.327, n2ⁿ 0.860; randomized: 2ⁿ 0.750, 1.5ⁿ 1.282, nλⁿ 0.818 |

All α values are [val]. The validator's log-factor diagnostic is **resolved** for every count-based fit. It is not
resolved for the timed enumeration, as RL-048 predicts.

## 2. Per entry

### 2.1 XOR convolution (coordinator)

**Problem.** h[k] = Σ over i⊕j=k of a[i]b[j], over the integers, for vectors of length N = 2ⁿ.
- Input entries are in [−9, 9], so values have O(n) bits.
- Costs: Θ(4ⁿ) = Θ(N²) vs Θ(n·2ⁿ) = Θ(N log N). This is T3, because both are polynomial in the input length N.

**Counted.** A `CountingInt` in the harness counts every +, −, ×, // made by the unchanged implementations.
- Naive: exactly 2·4ⁿ [proof].
- FWHT: exactly (3n+2)·2ⁿ, that is 3 transforms of n·2ⁿ add/sub each, plus 2ⁿ products and 2ⁿ exact divisions [proof].
- Checked for naive n = 0..9 and FWHT n = 0..14 [exp: xor_convolution_counts]. Outputs are identical to
  plain-integer runs.

**Tolerance.** 0.05. The FWHT's exact deviation is 0.0125, caused by the 2·2ⁿ term. The smallest rival gap is 0.068
(n2ⁿ/log n, from the diagnostic).

**Oracle.** The convolution theorem is checked character by character with popcount parities; no transform code is
used.
- For n ≤ 8, all 2ⁿ characters are checked. This determines h uniquely, so the check is complete.
- At n = 11, 48 seeded characters are checked (a spot check).

**Quantum link, as written in the entry.**
- W = 2^(n/2)·H^⊗n, and one FWHT stage corresponds to one Hadamard gate.
- This is not a quantum speed-up for computing W·v: a quantum computer only samples an index. The advantages in the
  BV, DJ and Forrelation entries are in oracle queries.
- Forrelation's Φ is one FWHT after all 2N values have been read.

**DOIs.**
- Fino & Algazi 1976, 10.1109/TC.1976.1674569 [DOI OK]: C-25(11), 1142–1146. The venue is written as
  "C-25 (no. 11)" because check_sources parsed "C-25(11)" as volume 25 (a near-miss, §4).
- Bernstein & Vazirani 1997 [DOI OK].

### 2.2 Zeta transform (coordinator)

**Problem.** ζf(S) = Σ over T⊆S of f(T). Costs: Θ(3ⁿ) = Θ(N^1.585) vs Θ(n·2ⁿ). T3.

**Counted.** Additions.
- Naive: exactly 3ⁿ.
- Yates: exactly n·2ⁿ⁻¹.
- Both are [proof] and were checked for n = 0..12 [exp: zeta_transform_counts].
- Both fits give α = 1.000 exactly, so the tolerance is 0.02. The smallest rival gap is 0.064.

**Oracle.** A definitional scan over all masks with T & ~S = 0. It checks every S for n ≤ 8, and 64 S plus the full
set above that.

**DOIs.** Björklund–Husfeldt–Kaski–Koivisto, STOC 2007, 67–74 [DOI OK].
- **Dropped:** Yates 1937. It is a book and could not be checked; the entry names the method after it in a caveat
  only.

### 2.3 Regex matching (coordinator)

**Dialect, defined in the entry.** Atoms are a–z or '.', each with an optional '?' or '*'. No groups, alternation,
anchors or backreferences. Matching is full match.

**Size and family.** n means at most 2n atoms and at most 2n text characters. The witness family is
P_n = ((a?)ⁿaⁿ, aⁿ).

**Counted.** Symbol–character comparisons, through an instrumented text character.
- Backtracking (consume first): exactly (n+2)·2ⁿ⁻¹ − 1 [proof]. All 2ⁿ branches of the n optional atoms are explored
  because the only accepting branch is explored last; phase 2 adds Σ C(n,j)(n−j).
- Memoised backtracking: n(n+1) [proof].
- Thompson: n(n+1) [proof]. The active set before character j+1 is {j..n+j}.
- Checked for backtracking n = 0..16, and for memoised and Thompson n = 0..16, 24, 32, 48 and 64
  [exp: regex_counts].
- General bounds: backtracking O(2^(m+|t|)) (call-tree depth ≤ m+|t|); the other two O(m·|t|).
- Thompson's closure was written in O(m) per step, without a sort, so that no hidden log factor enters the time
  claim.

**Oracle.** Python `re.fullmatch` (an independent engine, used only as the oracle).
- The experiment battery found 0 disagreements in 3300 instances (2275 matches).
- V1: n ≤ 24, 6 trials. About a quarter of the instances for n ≤ 12 are P_n.

**Tags.** T2. Memoisation of the natural key (i, j) is enough here, which is the positive case of RL-039.

**DOIs.** Thompson 1968, CACM 11(6), 419–422 [DOI OK].

### 2.4 Global minimum cut (sub-agent; re-validated)

**Problem.** Symmetric non-negative integer weight matrix. The output is the minimum cut weight; for n < 2 it is None.

**Counted.** Weight additions plus comparisons, through `CountingWeight`.
- Brute force: 2ⁿ⁻³(n²−n+4) − 2.
- Stoer–Wagner (array): (n−2)(2n²+n+3)/6.
- Both are [proof], checked for brute force n = 2..14 and Stoer–Wagner n = 2..40 plus larger n up to 256.

**Oracle.** The minimum over t of the max flow from 0 to t (Edmonds–Karp written in the harness). For n ≤ 10 it also
enumerates subsets with a different cut formula.
- Battery: 96 instances in six families.
- Negative controls: output+1 is rejected on 84/84.

**Rival result of note.** The exact counts reject n² log³ n (α = 1.128). This is the Karger–Stein cost, which the
pattern report found timing could not separate (ρ = 1.050).

**DOIs [DOI OK].**
- Stoer & Wagner, J. ACM 44(4) 585–591.
- Nagamochi & Ibaraki, SIAM J. Discrete Math. 5(1) 54–66.
- Karger & Stein, J. ACM 43(4) 601–640 (context only).
- Edmonds & Karp, J. ACM 19(2) 248–264 (oracle).

The O(nm + n² log n) heap bound comes from secondary pages only.

### 2.5 Optimal BST (sub-agent; re-validated)

**Formulation.** Knuth 1971, with weights p and q. Three algorithms; tags T2 + T3, following the
longest-increasing-subsequence precedent.

**Counted.** Comparisons of cost values.
- Plain recursion: exactly 3ⁿ calls (counted with `sys.setprofile`) and (3ⁿ⁻¹−1)/2 comparisons [proof]. **This
  confirms the pattern report's estimated Θ(3ⁿ).**
- Cubic DP: (n+1)n(n−1)/6 comparisons [proof].
- Knuth: Σ_L (r[n−L+1][n] − r[0][L−1]) ≤ (n−1)² [proof]. The bound is attained by the V2 family (heavy end keys).
  On 7 other families the count is 0.39–0.61·n², with α 0.993–1.013.

**Oracle.** Explicit enumeration of all BST shapes for n ≤ 10. For n ≤ 60, a separately written memoised recursion:
the same recurrence in independent code, so weaker independence. Above 60, None.

**CORRECTED (sub-agent self-correction, before any claim).** The first draft said a random choice among tied roots
breaks Knuth's algorithm. Experiments refuted this.
- Five tie rules gave 0 wrong values on 6006 tie-heavy instances, and 0 on a wider probe of 6840 instances
  [exp: optimal_bst_ties].
- What does fail: a root table that mixes largest and smallest optimal roots is non-monotone on 3417/6006 instances.

**DOIs [DOI OK].** Knuth 1971, Acta Inf. 1(1) 14–25; Yao 1980 STOC 429–435.
- Their content is "as commonly cited", not re-read.
- CLRS is cited by ISBN; the section number is recalled.
- **Dropped:** the CLRS exercise number, the claim that Yao uses the largest root, and a Garsia–Wachs note.

### 2.6 2-SAT (sub-agent; re-validated)

**Output.** An assignment or None. `equal` compares satisfiability only.

**V2 family W_n.** A star of clauses on x1, an UNSAT core on x2 and x3, and an implication chain; m = 2n+2.

**Counted.** Every operation on input-derived literals (`CountingLit`: arithmetic, comparisons, hash, `__index__`).
- Brute force: (n+7)·2ⁿ⁻¹ + 2 literal evaluations, at 6 operations each [proof].
- APT: exactly 49(n+2) [data, not proven]. The 2n DFS-root accesses are not counted, which is O(n) of uncounted work.

**Oracle.** Certificate-based throughout.
- A returned assignment is checked against all clauses.
- UNSAT is accepted only with a proof: exhaustive search for n ≤ 12; otherwise implication paths x⇝¬x and ¬x⇝x
  found by BFS, located with a separate Kosaraju SCC.

**DOIs [DOI OK].**
- Aspvall–Plass–Tarjan, IPL 8(3) 121–123.
- Tarjan, SIAM J. Comput. 1(2) 146–160.
- Even–Itai–Shamir, SIAM J. Comput. 5(4) 691–703. Its 2-SAT content is recalled.
- Papadimitriou is not cited, because the random walk was not implemented.

**Convention question.** The brute-force claim is fitted against the exact form (n+7)·2ⁿ. Bare n·2ⁿ gives
α = 0.958, and m·2ⁿ gives 0.966, both outside 0.02. See §5, D7.

### 2.7 Counting spanning trees (sub-agent; re-validated)

**Input and output.** An adjacency matrix with n ≥ 1; the output is the exact τ(G).

**Kirchhoff with Bareiss.** Counted multiplications and exact divisions: exactly (n−2)(n−1)(2n−3)/2 on every
connected graph [proof]. Checked for n = 1..70 and n = 128.
- Bit-size caveat: intermediates are minors, below n^(n−1) by Hadamard, so they have O(n log n) bits. The bit
  complexity O(n³·M(n log n)) is stated.
- Claimed cost: (n−1)³, the cube of the reduced dimension. Against n³, α would be 1.041, which needs a tolerance
  above 0.042, and then n³ log n would not be resolved. See D8.

**Enumeration: timed, best of 3, on K_n, n = 4..8.** Instance instrumentation cannot see its per-subset work: after
listing the edges it uses its own ints. An edge-list input would hide Bareiss's arithmetic instead. Three validator
runs gave α = 0.961, 0.995 and 0.980.

**Oracle (no shared code).** DFS connectivity; tree → 1; K_n → Cayley; memoised deletion–contraction up to 24 edges;
otherwise a different cofactor by Fraction elimination.
- Additional checks: 1600 more instances with 0 failures; Bareiss against Leibniz on 600 general matrices, 326 of
  which needed row swaps.

**Sources.**
- Kirchhoff 1847 [DOI OK]: Ann. Phys. 148(12) 497–508; Crossref holds the German title.
- Bareiss 1968 [DOI OK]: Math. Comp. 22(103) 565–578.
- Cayley 1889: no DOI, same details as in the MST entry.

### 2.8 NAND-tree evaluation (coordinator)

**Tags.** T4 primary, T3 secondary, as proposed in RL-042.
- The validator's T4 rule requires at least one classical-randomized and one classical-deterministic algorithm. It
  is satisfied.
- `lower_bounds` lists both models.

**Counted.** Leaf reads, through an instrumented leaf sequence, on the right-zero reluctant input with root value 1.
This input is worst case for both algorithms.
- Left-first: exactly 2ʰ reads [proof], checked for h = 0..16.
- Randomized: the mean of 200 seeded runs per h.
  - Exact expectation from the recurrence R0(h) = 2R1(h−1), R1(h) = R0(h−1) + R1(h−1)/2 [proof]. The eigenvalues
    are (1 ± √33)/4.
  - The exact expectations fit at α = 0.998.
  - Over 40 alternative seed sets: α mean 0.997, sd 0.0047, range 0.989–1.008.
  - The validator's means equal my reproduction value for value, and lie within 2.0 standard errors of the exact
    expectation at every h [exp: nand_tree_counts].

**Lower bounds, stated precisely.**
- *Deterministic: 2ʰ.* By an adversary argument, which I wrote out in the entry. It is not checked against a
  published proof, and the entry says so.
- *Randomized: Ω(λʰ) for zero-error (Las Vegas) algorithms only*, from Saks–Wigderson 1986. I confirmed the statement
  through secondary sources found by one web search (the Boolean Zoo "Iterated nand" page; arXiv:1506.06399), not
  from the paper itself. These secondary sources say the directional algorithm is optimal, with zero-error
  complexity Θ(((1+√33)/4)^d).
- No claim is made for bounded-error algorithms.

**Sources and drops.**
- Saks & Wigderson, FOCS 1986, 29–38 [DOI OK].
- **Dropped:** Snir 1985. The DOI I guessed, 10.1016/0304-3975(85)90024-6, resolves to a different paper ("A simple
  proof for the completeness of Floyd's method").
- **Dropped:** Farhi–Goldstone–Gutmann 2008. Crossref stores no title, so it would fail check_sources' title
  match. The quantum line is mentioned in `notes` without a citation.

## 3. Candidates not reached or rejected

All eight requested candidates were implemented. Within them, these options were skipped:
- **Karger–Stein** in the min-cut entry: its V1 check would be probabilistic, and the time box.
- **Papadimitriou's random walk** in 2-SAT: its V1 check would be probabilistic, and its source has no Crossref year.
- **Subset convolution** as a third zeta-transform pair.

Other pattern-report candidates (7, 8, 11–40) were outside this brief.

## 4. NEAR-MISSES (with numbers)

1. **Regex backtracking at tolerance 0.06:** the fit passed (α = 0.974), but the log-factor diagnostic was **not
   resolved**: n2ⁿ/log n fitted at 1.044. Tolerance 0.035 resolves it, because the exact deviation is only 0.026
   [val, both runs].
2. **Regex poly fits on n = 4..64:** α = 0.9638 against n². The entry uses n = 8..128, where α = 0.981 [exp].
3. **XOR venue string:** "C-25(11)" was parsed by check_sources as volume 25, against Crossref's "C-25", and reported
   as a DETAIL MISMATCH. Rewritten as "C-25 (no. 11)": 0 problems.
4. **Snir 1985 DOI guess** resolved to a different 1985 TCS paper; dropped.
5. **2-SAT, random clauses in front of an UNSAT core:** the brute-force cost per assignment stays at about 36 (36.15,
   36.11, 35.56, 38.49, 35.91 for n = 8..16). That is Θ(2ⁿ), not m·2ⁿ: α = 1.0036 against 2ⁿ, 0.8926 against n·2ⁿ.
   The structured family W_n was needed (sub-agent).
6. **2-SAT brute force against bare n·2ⁿ:** α = 0.9577; against m·2ⁿ, 0.9664. Both are outside 0.02, hence the
   exact-form cost (sub-agent).
7. **Spanning-tree enumeration timing** cannot reject nearby super-exponential costs. Even noise-free, the claim's
   cost model fits n^(n−2) at 1.2026, C(m, n−1) without the factor n at 1.0621, and nⁿ at 1.0543, all within 0.25
   (sub-agent).
8. **Kirchhoff against n³** instead of (n−1)³: α = 1.0412, and n³·log n would then not be resolved (sub-agent).
9. **NAND randomized:** the validator-seeded mean at h = 14 lies 2.0 standard errors below the exact expectation
   (1327.41 vs 1404.86). It is harmless for the fit, which stays at α = 0.995.
10. **Optimal BST:** a root table mixing largest and smallest optimal roots is non-monotone on 3417/6006 instances,
    while the algorithm itself is robust to tie rules (sub-agent).

## 5. DECISION LOG

- **D1. Delegation.** Four entries (4, 5, 6, 7) went to parallel sub-agents with a shared brief; I wrote 1, 2, 3
  and 8.
  - Alternative: do everything sequentially; it would not fit the 80-minute box.
  - Evidence: all four came back at V2, and their claims were re-validated together with mine (7/7 OK, then 1/1 for
    spanning trees).
- **D2. Scratch venv, not repairing `.venv`.** Repairing would mean changing a shared environment while other agents
  run, and could break cffconvert. A scratch venv from `requirements.txt` reproduces the documented setup.
- **D3. XOR convolution over the integers, not mod p.** This avoids the modular-inverse trap the pattern report
  mentions. The final division by N is exact over the integers (W·W = N·I), with O(n)-bit values.
- **D4. Count all ring operations for the FWHT, not only multiplications.** Multiplications alone are 2·2ⁿ, which
  would understate the Θ(n·2ⁿ) cost carried by the butterflies.
- **D5. Regex size parameter.** At most 2n atoms and at most 2n characters, so that V1's random instances and V2's
  P_n share one n. Earlier drafts used n = number of atoms in V1 but the family parameter in V2; that was caught
  before the first validation.
- **D6. Memoised backtracking added as a third regex algorithm.** It makes the RL-039 point (memoising the natural key
  suffices) measurable.
  - Evidence: it makes exactly as many comparisons on P_n as Thompson, n(n+1).
- **D7. Exact-form cost expressions** (2-SAT brute force (n+7)·2ⁿ; Kirchhoff (n−1)³). Both are members of the
  claimed Θ class; the time_complexity fields state Θ(n·2ⁿ) and Θ(n³).
  - Alternative: bare forms with wider tolerances, which would lose rival or log discrimination (near-misses 6 and
    8).
  - Strassen's precedent used n^log₂7, not the exact 7^k·16³.
- **D8. NAND tolerance 0.05.** Chosen from the exact-expectation deviation (0.002) plus the empirical seed spread
  (sd 0.005). The 2ʰ rival gap is 0.25; the pattern report's timing-free probe at 40 samples had found the margin
  "small".
- **D9. NAND worst-case input.** The right-zero reluctant input serves both algorithms. All reluctant inputs give the
  random-order algorithm the same expected cost, while left-first needs 0-children on the right.
- **D10. No Snir or FGG citations** (§2.8), per the "drop unverifiable details" rule.
- **D11. Spanning-tree enumeration timed** (sub-agent). Counting would require changing the input encoding, which
  would hide Kirchhoff's arithmetic, or an interpreter hook judged fragile. V2 for that algorithm therefore means
  "consistent up to log factors and nearby super-exponential costs" (near-miss 7).

## 6. OPEN IDEAS

*Forward-looking content is not published (RL-086).*

## 7. Files

New entries:
- `pairs/xor-convolution-naive-vs-walsh-hadamard/`
- `pairs/subset-sum-zeta-transform-naive-vs-yates/`
- `pairs/regex-matching-backtracking-vs-thompson/`
- `pairs/nand-tree-evaluation-deterministic-vs-randomized/`
- `pairs/global-min-cut-brute-vs-stoer-wagner/`
- `pairs/optimal-bst-recursion-vs-dp-vs-knuth/`
- `pairs/two-sat-brute-force-vs-scc/`
- `pairs/spanning-tree-count-enumeration-vs-kirchhoff/`

Experiments, `experiments/2026-10-07b_*.py`:
- `doi_checks`
- `xor_convolution_counts`
- `zeta_transform_counts`
- `regex_counts`
- `nand_tree_counts`
- `global_min_cut_counts`
- `optimal_bst_counts`
- `optimal_bst_ties`
- `two_sat_counts`
- `spanning_tree_counts`

Not done:
- a RESEARCH_LOG entry;
- `tools/build_index.py`;
- a recorded ledger run (`--record`).
