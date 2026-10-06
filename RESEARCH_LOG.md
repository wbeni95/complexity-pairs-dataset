# Research log

The project's lab notebook. **Every result is recorded here, whether a claim held, failed, was corrected or
stayed undecided**, with exact numbers and with the provenance of those numbers. Entries are never
edited after the fact except to fix typos. A later finding gets a new entry that references the old one.

## Entry types

| Type | Meaning |
|---|---|
| VERIFIED | A claim was tested and held. |
| REFUTED | A claim was tested and found false. |
| CORRECTED | An error was found and fixed (code, text, tag, citation or method). The old state is recorded. |
| INCONCLUSIVE | Tested, but the evidence cannot decide. The claim is not raised. |
| DECISION | A methodological or policy choice that changes what counts as evidence. |
| NULL | A search found nothing within a stated scope. This is never evidence of impossibility (START_HERE section 6). |
| NEAR-MISS | Something almost worked: how close (numbers), why it fell short, and what might fix it. Kept because near-misses often point to the next attempt. |
| IDEA | A hypothesis or direction not yet tested, with what motivates it (evidence or literature). Dropped directions are recorded too, with the concrete reason. |

Entries may carry a **Rationale:** line giving the considerations behind a decision or an attempt, including
alternatives that were rejected and why, so that later work can reuse or revisit them.

## Provenance labels

- **ledger:** a machine-recorded run of `tools/validate.py --record` in [ledger/runs/](ledger/runs/) (environment, git state, every measured value).
- **experiment:** a deterministic script in [experiments/](experiments/); rerunning it reproduces the numbers.
- **console:** output seen during a session but not machine-recorded. It is less reproducible; timings vary between runs.
- **agent report:** stated by a delegated agent and not independently re-run by the maintainer, unless the entry says so.
- **external:** a public API response (Crossref, DataCite, arXiv).

## Roles

- **owner:** Benjamin Weisz. He directs the project, makes or delegates its decisions, decides on publication and on
  contact with other researchers, and is responsible for the content.
- **maintainer:** the AI assistant (Claude, by Anthropic) that does the day-to-day work under the owner's direction:
  code, entries, runs, analyses, consolidating agent reports and writing this log. Errors attributed to "the
  maintainer" in this log are the AI's. "The maintainer's machine" is the owner's computer, on which all local runs
  were made.
- **agent** (also *delegated agent*, *research agent*): an autonomous AI sub-agent that the maintainer starts for a
  bounded task. Its numbers are labelled *agent report* unless they were re-run.

This section was added in RL-078. Earlier entries use these words with these meanings and are not reworded.

Environment for all 2026-10-06 entries: Windows 11 Pro 10.0.26200, AMD64 (AMD Family 26 Model 68),
CPython 3.14.2, jsonschema 4.26.0.

---

## 2026-10-06

### RL-001 · DECISION · Repository layout and enforced verification levels
`pairs/` holds V1+ entries, `staging/` holds V0 entries and `synthetic/` holds T7 entries; `tools/validate.py` enforces this. Levels are cumulative.
V1 means at least two implementations agree on a seeded battery (plus an independent `check` oracle where available) and do not mutate their input.
V2 means a log-log fit of measured cost against the claimed cost has slope 1 ± 0.25 for **every** implemented algorithm.
V3 additionally requires cited proofs. The validator ships with unit tests (14) asserting that it **rejects** false claims: wrong scaling, disagreeing outputs, input mutation, misplaced levels or tags, and a false query-count claim.

### RL-002 · VERIFIED · Fibonacci: φⁿ, n and log n
First V2 run (console): naive recursion α = 0.997 against φⁿ (n = 18..28), DP α = 1.001 against n (n = 10⁴..10⁶), fast doubling α = 0.996 against log n (n = 2⁸..2¹²⁸).
The recorded run (RL-021) gives 1.004 / 0.997 / 1.100. Affects: `pairs/fibonacci-naive-vs-dp`.

### RL-003 · VERIFIED · The AKS implementation decides primality, including step-5-only composites
1. AKS, trial division and Miller–Rabin agree on every N ∈ [0, 3000): 0 disagreements.
2. 13 semiprimes N = p·q whose prime factors both exceed AKS's r were all reported composite. They get past steps 1–4, so the polynomial-congruence step 5 rejected them. Examples: 95477 = 307·311 (r = 293), 96091 = 307·313 (r = 281), 122491 = 347·353 (r = 317).

AKS timing per prime (console): 1009 (10 bits) 0.048 s, 4093 (12 bits) 0.093 s, 16381 (14 bits) 0.261 s, 65521 (16 bits) 0.553 s, 262139 (18 bits) 1.018 s.
Provenance: experiment `experiments/2026-10-06_aks_step5_composites.py`, rerun with identical output. Affects: both primality entries.

### RL-004 · INCONCLUSIVE · AKS scaling not measurable here → primality entries stay V1
AKS's polynomial (Õ(n^10.5) proven, Õ(n⁶) for the Lenstra–Pomerance variant) dominates only far beyond the bit lengths pure Python can time, so no V2 claim is made.
Trial division alone fits 2^(n/2) (α = 1.092 and 1.118 in two console runs; random n-bit primes vary in size within [2ⁿ⁻¹, 2ⁿ)).

### RL-005 · CORRECTED · The Dijkstra implementation exited early, so its runtime depended on the instance
**Old state:** the loop stopped once the target vertex was settled. First V2 run (console): α = 1.166 against n², with a jump at n = 200 → 300 (0.962 ms → 7.78 ms, a factor of 8.1 where 2.25 is expected).
**Cause:** the running time depended on where the target fell in the settling order, so it was not Θ(n²) on every instance.
**Fix:** all n vertices are settled. Re-run (console) gives α = 1.014; the recorded run gives 1.005.
This is the kind of error V2 exists to catch. Affects: `pairs/shortest-path-enumeration-vs-dijkstra`.

### RL-006 · INCONCLUSIVE · Strassen vs schoolbook: the exponent gap is not resolvable → V1
One timing run (console): Strassen (cutoff 16) took 1.8 / 13.6 / 98.7 / 721.0 ms for n = 32 / 64 / 128 / 256, per-doubling ratios 7.6, 7.3, 7.3 (theory 2^2.807 = 7.0).
Schoolbook took 1.9 / 13.7 / 106.3 ms for n = 32 / 64 / 128, ratios 7.2, 7.8 (theory 8).
The gap 3 − 2.807 = 0.19 in the exponent lies inside the tolerance band, so V2 could not discriminate between the two algorithms. The entry stays at V1.

### RL-007 · VERIFIED · Plain matrix-chain recursion is Θ(3ⁿ), sharper than the textbook's Ω(2ⁿ)
The recurrence T(n) = Σₖ (T(k) + T(n−k)) + Θ(n) gives T(n) = 3T(n−1) + Θ(1) = Θ(3ⁿ). CLRS proves only Ω(2ⁿ).
Fit against 3ⁿ for n = 7..12: α = 0.994 (console) and 0.998 (recorded run, RL-021). Affects: `pairs/matrix-chain-recursion-vs-dp`.

### RL-008 · VERIFIED · Citations, first pass (titles and years)
51 DOIs resolved with matching titles and years, 0 problems (external).
- **Control:** an unrelated DOI submitted under a wrong title was flagged as a mismatch, which shows the checker can fail.
- **Registry:** the LIPIcs DOI 10.4230/LIPIcs.ITCS.2017.49 is registered with DataCite, not Crossref, so the checker gained a DataCite fallback.
- **arXiv:** titles were checked for 9 arXiv ids, and author lists for 7 of them.
- **Rate limit:** a later batch query returned HTTP 429, so the checker now honours Retry-After.

### RL-009 · DECISION · License (by the user)
Use is free for personal, educational and non-commercial research. Commercial use requires a paid license, and the fees fund the research.
Data is under CC BY-NC 4.0 and code under PolyForm Noncommercial 1.0.0; see COMMERCIAL.md. The official license texts were downloaded, not reproduced from memory.
The licenses cover this repository's own expression, not published algorithms or mathematical facts.

### RL-010 · DECISION · Tags T8 and T9, `lower_bounds`, query-count V2
- **T8** (super-poly → faster super-poly). T6 stays primary when polynomial time is open.
- **T9** (proven quantum advantage in a query model). The validator requires a quantum algorithm and a cited classical lower bound.
- **Query-count V2:** V2 may fit implementation-reported operation counts (`measure: "reported"`) instead of time. This is needed because simulating quantum algorithms costs exponential time while the claim concerns oracle queries.
- **Counting rule:** "validated pairs" = V1+ in `pairs/` carrying any of T1–T5, T8, T9.

### RL-011 · REFUTED · The seed list's classification of AlphaDev sorting as T3
START_HERE section 4 listed "small-case sorting (AlphaDev)" under T3. Section 1 requires an *asymptotic* difference, and AlphaDev's sort3–sort5 routines are O(1) vs O(1) for fixed k: fewer instructions, the same complexity class.
Under the charter's own definition, the entry is therefore not a pair. It was moved to `notes/constant-factor-alphadev.md` as a methodology note.

### RL-012 · CORRECTED · Knapsack: secondary tag T2 removed, meet in the middle added
**Old state:** secondary tag T2 (naive-exp → poly) was attached to the capacity DP. Θ(nW) is pseudo-polynomial, exponential in the bit length of W, so T2 was wrong.
**New state:** T6 + T8, with the T8 pair being enumeration Θ(2ⁿn) → Horowitz–Sahni meet in the middle Θ(2^(n/2)n).
Recorded fits (RL-021): 0.978 / 0.992 / 1.055. The DP's fit is against n², valid only because the harness has W = Θ(n), as the entry states.

### RL-013 · VERIFIED · Query counts of the T9 algorithms
- **Bernstein–Vazirani:** classical exactly n queries (n = 2, 4, 8, 12, 16); quantum exactly 1 query for every n = 1..10.
- **Grover:** quantum queries 2, 4, 7, 13, 26, 51 for n = 2, 4, …, 12. This is exactly ⌊(π/4)·2^(n/2)⌋ iterations plus one confirming classical query; every first attempt succeeded.
- **Grover, classical:** random-order search is ≈ (N+1)/2. At n = 14 the mean over 40 instances was 7817 against an expectation of 8192.5.
- **Simon, classical:** collision search fits 2^(n/2) (α = 0.993, recorded).

Provenance: ledger (RL-021) and console.

### RL-014 · CORRECTED · Randomized implementations were not reproducible
**Old state:** implementations drew from the unseeded global `random` module. With 10 samples per n, two unseeded runs gave the Simon quantum fit α = 0.988 and α = 1.155 (console), so the counts differed between runs.
**Fix:** the validator now re-seeds `random` before every implementation call, using a seed derived from (entry, phase, n, trial or sample, algorithm). Two consecutive seeded runs then gave identical query counts, with α = 1.233 both times (console).
Because that value lies close to the tolerance edge, and the 10-sample mean at n = 2 (1.5) was far from E(2) = 2 (see RL-015), the samples were raised to 40, which gives α = 1.121 (recorded, RL-021).
Wall-clock timings remain inherently non-reproducible, which is why the ledger records them together with the environment.

### RL-015 · VERIFIED · Simulated Simon uses the theoretically expected number of queries
The exact expectation is E(n) = Σⱼ₌₁ⁿ⁻¹ 1/(1 − 2⁻ʲ) = n + 0.6067 − o(1). Empirical mean ± 1 s.e. against E(n):

| n | instances | mean ± s.e. | E(n) | z |
|---|---|---|---|---|
| 2 | 4000 | 2.0155 ± 0.0221 | 2.0000 | +0.70 |
| 3 | 4000 | 3.3643 ± 0.0254 | 3.3333 | +1.22 |
| 4 | 4000 | 4.4710 ± 0.0256 | 4.4762 | −0.20 |
| 6 | 3000 | 6.5790 ± 0.0300 | 6.5751 | +0.13 |
| 8 | 1500 | 8.5840 ± 0.0426 | 8.5989 | −0.35 |

All five agree within 1.3 standard errors. This checks the simulator and the post-processing quantitatively, beyond the O(n) claim. Provenance: experiment `experiments/2026-10-06_simon_expected_queries.py`, rerun with identical output.

### RL-016 · CORRECTED · The maintainer misstated an expected slope in the Simon entry
**Old text** (never committed): "the expected log-log slope against n over n = 2..10 is slightly below 1".
**Computation:** the exact E(n) has slope **1.0186** over n = 2, 3, 4, 6, 8, 10. E(2) = 2 exactly, and the additive term grows from 0 toward 0.6067. The text was corrected.

### RL-017 · CORRECTED · Unverifiable details removed or sourced
- LIS: the claim that Fredman (1975) proves optimality up to lower-order terms could not be checked against the paper, so it was removed (agent-flagged).
- Inversion counting: the page numbers "161-173" for Chan–Pătraşcu (SODA 2010) were unchecked and removed. The DOI was verified.
- Karatsuba: the remark that Karatsuba refuted Kolmogorov's quadratic-time conjecture was removed, because its source (Karatsuba 1995) could not be found in Crossref. Toom–Cook is now attributed to Knuth TAOCP Vol. 2, §4.3.3.
- Permanent: the uncited claim that no (2−ε)ⁿ algorithm is known was removed (agent-flagged).
- Sources added after verification: Han & Thorup 2002 (doi:10.1109/SFCS.2002.1181890) and Logan & Shepp 1977 (doi:10.1016/0001-8708(77)90030-5). Vershik & Kerov 1977 was added by venue only, marked "not machine-verified".
- Aaronson & Arkhipov 2013: the DOI exists, but Crossref has no title for it. It is now accepted because its year, volume (9) and pages (143–252) all match the Crossref record.

### RL-018 · VERIFIED (agent report, re-verified) · 12 new classical pairs by two delegated agents
The agents added modular exponentiation, gcd, maximum subarray, sorting, KMP, LIS, Karatsuba, assignment (Hungarian), determinant, permanent, closest pair and MST.
The agents' methodology findings, as they reported them:
- **Hungarian, random matrices:** on uniformly random cost matrices the Hungarian method grows clearly slower than n³ (α ≈ 0.82). Timing therefore uses a worst-case family that forces about n²/2 search steps.
- **Euclid:** at word size the fit against n is not clean (α ≈ 1.34). V2 instead checks the O(n²) bit-cost bound at 4000–64000 bits.
- **Kruskal:** a first version sorting (w, u, v) tuples gave α ≈ 1.19 against n² log n, attributed to CPython memory effects at ≥ 10⁵ edges. Packing each edge into one integer key gives the same order and α ≈ 1.0–1.06.
- **Log factors:** for merge sort, patience sorting, closest pair, NTT and inversions, the V2 fit cannot separate n log n from n. It does rule out n². Each entry states this.

All 12 entries were re-run by the maintainer in the recorded run (RL-021).

### RL-019 · VERIFIED · Citations, second pass (titles, years, volume, issue, pages)
102 identifiers (DOIs and arXiv ids) were checked, with 0 problems. For 86 DOI sources the cited venue details were compared field by field with Crossref: 74 volumes, 62 issues and 82 page ranges, all agreeing.
26 sources have no DOI or arXiv id (books by ISBN, old proceedings) and cannot be checked automatically. Provenance: external, via `tools/check_sources.py`.

### RL-020 · DECISION · Evidence must be recorded
At the user's request (2026-10-06), every confirmation, refutation and correction is logged here. `tools/validate.py --record` writes every result and measurement to `ledger/runs/`, and ad-hoc checks live in `experiments/` as deterministic scripts.

### RL-021 · VERIFIED · First full recorded run: 36/36 entries pass their claimed level
Ledger file: [ledger/runs/20261006T005329Z.json](ledger/runs/20261006T005329Z.json), made before the first commit (git_commit null, dirty tree).
- **V1:** run on 28 entries, with 1830 instances and 3714 implementation runs.
- **V2:** 55 measurements, all passing. α ranges from 0.924 to 1.121; the Bernstein–Vazirani quantum algorithm passes the constant-cost check with max/min = 1.000. Per-algorithm values are below.

| Entry | Algorithm | Measure | Claimed cost | Result |
|---|---|---|---|---|
| assignment-brute-vs-hungarian | permutation enumeration | time | `n * factorial(n)` | α = 0.971 |
| assignment-brute-vs-hungarian | Hungarian method | time | `n**3` | α = 0.966 |
| bernstein-vazirani-classical-vs-quantum | classical: unit vectors | queries | `n` | α = 1.000 |
| bernstein-vazirani-classical-vs-quantum | Bernstein–Vazirani (quantum) | queries | `1` | max/min = 1.000 |
| closest-pair-brute-vs-divide-conquer | all pairs | time | `n**2` | α = 1.011 |
| closest-pair-brute-vs-divide-conquer | Shamos–Hoey | time | `n * log(n)` | α = 0.998 |
| determinant-cofactor-vs-gaussian | cofactor expansion | time | `factorial(n)` | α = 1.009 |
| determinant-cofactor-vs-gaussian | Gaussian elimination mod p | time | `n**3` | α = 0.972 |
| edit-distance-brute-vs-dp | plain recursion | time | `(3 + 2*sqrt(2))**n / sqrt(n)` | α = 0.995 |
| edit-distance-brute-vs-dp | Wagner–Fischer | time | `n**2` | α = 1.046 |
| fibonacci-naive-vs-dp | naive recursion | time | `phi**n` | α = 1.004 |
| fibonacci-naive-vs-dp | bottom-up DP | time | `n` | α = 0.997 |
| fibonacci-naive-vs-dp | fast doubling | time | `log(n)` | α = 1.100 |
| gcd-trial-vs-euclid | trial divisors | time | `2**n` | α = 1.044 |
| gcd-trial-vs-euclid | Euclid (bit cost) | time | `n**2` | α = 0.961 |
| grover-search-classical-vs-quantum | classical random order | queries | `2**n` | α = 0.992 |
| grover-search-classical-vs-quantum | Grover (quantum) | queries | `2**(n/2)` | α = 0.924 |
| integer-multiplication-schoolbook-vs-karatsuba | schoolbook | time | `n**2` | α = 1.004 |
| integer-multiplication-schoolbook-vs-karatsuba | Karatsuba | time | `n**log2(3)` | α = 1.022 |
| inversion-counting-quadratic-vs-merge | all pairs | time | `n**2` | α = 1.043 |
| inversion-counting-quadratic-vs-merge | merge-sort counting | time | `n * log(n)` | α = 1.028 |
| knapsack-01-brute-vs-dp | subset enumeration | time | `2**n * n` | α = 0.978 |
| knapsack-01-brute-vs-dp | meet in the middle | time | `2**(n/2) * n` | α = 0.992 |
| knapsack-01-brute-vs-dp | capacity DP (W = Θ(n) here) | time | `n**2` | α = 1.055 |
| lcs-brute-vs-dp | subsequence enumeration | time | `2**n * n` | α = 0.984 |
| lcs-brute-vs-dp | dynamic programming | time | `n**2` | α = 1.022 |
| longest-increasing-subsequence | subset enumeration | time | `2**n * n` | α = 0.986 |
| longest-increasing-subsequence | quadratic DP | time | `n**2` | α = 1.015 |
| longest-increasing-subsequence | patience sorting | time | `n*log(n)` | α = 1.012 |
| matrix-chain-recursion-vs-dp | plain recursion | time | `3**n` | α = 0.998 |
| matrix-chain-recursion-vs-dp | bottom-up DP | time | `n**3` | α = 0.950 |
| maximum-subarray | brute force | time | `n**3` | α = 0.982 |
| maximum-subarray | running sums | time | `n**2` | α = 1.030 |
| maximum-subarray | Kadane | time | `n` | α = 0.966 |
| minimum-spanning-tree-brute-vs-kruskal | (n−1)-edge subset enumeration | time | `n * C(n(n-1)/2, n-1)` | α = 0.980 |
| minimum-spanning-tree-brute-vs-kruskal | Kruskal | time | `n**2 * log(n)` | α = 1.015 |
| minimum-spanning-tree-brute-vs-kruskal | Prim (array) | time | `n**2` | α = 1.008 |
| modular-exponentiation-repeated-vs-square-multiply | repeated multiplication | time | `2**n` | α = 1.002 |
| modular-exponentiation-repeated-vs-square-multiply | square-and-multiply | time | `n` | α = 0.999 |
| permanent-naive-vs-ryser | sum over permutations | time | `n * factorial(n)` | α = 0.988 |
| permanent-naive-vs-ryser | Ryser (Gray code) | time | `n * 2**n` | α = 0.987 |
| polynomial-multiplication-naive-vs-ntt | schoolbook convolution | time | `n**2` | α = 1.035 |
| polynomial-multiplication-naive-vs-ntt | NTT | time | `n * log(n)` | α = 0.984 |
| shortest-path-enumeration-vs-dijkstra | simple-path enumeration | time | `n * factorial(n - 2)` | α = 0.966 |
| shortest-path-enumeration-vs-dijkstra | Dijkstra (array) | time | `n**2` | α = 1.005 |
| simon-classical-vs-quantum | classical collision search | queries | `2**(n/2)` | α = 0.993 |
| simon-classical-vs-quantum | Simon (quantum) | queries | `n` | α = 1.121 |
| sorting-insertion-vs-merge | insertion sort (random input) | time | `n**2` | α = 0.987 |
| sorting-insertion-vs-merge | merge sort | time | `n*log(n)` | α = 0.980 |
| string-matching-naive-vs-kmp | naive (worst case, m = n/2) | time | `n**2` | α = 1.021 |
| string-matching-naive-vs-kmp | Knuth–Morris–Pratt | time | `n` | α = 1.003 |
| three-sum-cubic-vs-quadratic | all triples (no-solution input) | time | `n**3` | α = 0.946 |
| three-sum-cubic-vs-quadratic | sort + two pointers | time | `n**2` | α = 1.012 |
| tsp-brute-vs-held-karp | permutation enumeration | time | `factorial(n)` | α = 0.988 |
| tsp-brute-vs-held-karp | Held–Karp | time | `n**2 * 2**n` | α = 1.007 |

What these numbers do and do not show: a passing fit means the measured growth is *consistent with* the claimed
cost over the measured range, within ±0.25 in the log-log slope. It does not prove the asymptotic bound (V3 is for
proofs), and it cannot resolve log factors or exponent gaps smaller than the tolerance (see RL-006).

### RL-022 · VERIFIED · Recorded run on the first commit; run-to-run stability
Ledger file: [ledger/runs/20261006T005747Z.json](ledger/runs/20261006T005747Z.json), made at commit `d8ddc584a963a550bc6c8fa08be90deca53e3193` with a clean tree.
- **Result:** 36/36 entries pass their claimed level. All 55 V2 measurements pass, with α from 0.924 to 1.128. V1 ran on 28 entries: 1830 instances, 3714 implementation runs.
- **Stability against RL-021** (same code and machine, minutes apart): the largest change in a time-based α was 0.028 (fast doubling 1.100 → 1.128; inversion counting, all pairs, 1.043 → 1.015). All 5 query-count fits were **identical**, which confirms the reproducibility fix of RL-014.

### RL-023 · VERIFIED · All claims also pass in an independent environment (CI)
GitHub Actions run 37397178645 (push of `29202a0`; runner `ubuntu-latest`; Python 3.12 via actions/setup-python) completed with every job successful:
- `validate`: unit tests, schema and folder rules, V1;
- `scaling`: every V2 claim re-measured;
- `sources`: every DOI / arXiv id.

This is the first time all V2 fits were reproduced on a different OS and Python version from the maintainer's machine (Windows, CPython 3.14.2). Provenance: external (GitHub Actions). The per-job logs are kept by GitHub, not in this repository.

### RL-024 · DECISION · Near-misses, ideas and pair generators are kept (user request)
Two entry types were added: NEAR-MISS (with the numbers) and IDEA (with what motivates it), plus an optional **Rationale:** line.
Every script that produced or attempted a result is kept, including failed attempts.
Scripts that manufacture candidate pairs live in `generators/`, under a rule that separates two classes:
- **Mechanical transformations** (un-memoising, bloating) produce T7 synthetic entries, which are never counted.
- **Searches with an exact verifier** count only if they beat the best known algorithm. A rediscovery is a pipeline check.

**Rationale:** START_HERE section 5 warns that training only on bloated pairs teaches "un-bloating the obvious". Keeping the generators, labelled honestly, preserves their value as infrastructure without inflating the headline count.

### RL-025 · VERIFIED · First pair generator: linear recurrences → 4 synthetic (T7) entries at V2
`generators/linear_recurrence.py` turns coefficients c into a full entry: naive recursion, DP and companion-matrix power, with cost claims derived from the specification.
The naive cost is λⁿ, where λ is the largest real root of xᵏ = Σ_{i∈S} xᵏ⁻ⁱ for the support S of c, computed by bisection. The V2 sizes are chosen automatically.

Generated and validated (console; validator `--scaling`):

| Entry | λ | α naive | α DP | α matrix |
|---|---|---|---|---|
| synthetic/linear-recurrence-c1-1-1 | 1.8392867552 | 0.999 | 0.998 | 1.050 |
| synthetic/linear-recurrence-c1-1-1-1 | 1.9275619755 | 1.001 | 1.000 | 1.084 |
| synthetic/linear-recurrence-c1-0-1 | 1.4655712319 | 1.002 | 1.000 | 1.065 |
| synthetic/linear-recurrence-c2-3 | 1.6180339887 | 1.001 | 0.995 | 1.008 |

The λ prediction holds to within 0.002 in every case. This also confirms the claim that the naive call count depends only on *which* coefficients are nonzero: c = (2, 3) has the same λ = φ as Fibonacci.
`tests/test_generators.py` (5 tests) checks λ against known constants (φ; tribonacci 1.839286755214161), the characteristic-polynomial residual, rejection of non-exponential supports, agreement of the generated code with an independent reference sequence, and the T7 tagging.

### RL-026 · CORRECTED · Process: an instruction phrasing stopped three overnight agents
Four background agents were started (pattern mining, classical entries, quantum entries, search environment). The maintainer then sent each one an addendum asking it to document "the reasoning behind" its choices.
Three of the four terminated with an API safeguard error labelled `reasoning_extraction`, right after receiving the addendum. Their partial output was one empty directory, which was removed; no files were damaged.
The three were relaunched with the same mandates, and the documentation request was rephrased as decision logs, near-miss records and open ideas.

**Lesson:** ask agents for *documentation of decisions and evidence*, not for their internal reasoning.

---

## 2026-10-06 (overnight agents, consolidated by the maintainer; heading date corrected, see RL-055)

Four background agents worked in separate areas. Their full reports, with every number, decision log, near-miss and
open idea, are in [research/](research/):
- [classical_entries](research/2026-10-07_classical_entries.md)
- [quantum_entries](research/2026-10-07_quantum_entries.md)
- [patterns](research/2026-10-07_patterns.md) and [technique_mapping](research/2026-10-07_technique_mapping.json)
- [search_flipgraph](research/2026-10-07_search_flipgraph.md)

The entries below summarise them. The maintainer re-verified every entry in the recorded run (RL-044); numbers
marked "agent report" were not re-run by the maintainer.

### RL-027 · VERIFIED · Eight new classical pairs
Recorded α values (RL-044):

| Entry | Level | Recorded α |
|---|---|---|
| all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall | V2 | 0.973 / 0.923 |
| longest-palindromic-substring | V2 | 0.966 / 1.005 / 0.997 |
| element-distinctness-pairs-vs-sorting | V2 | 1.000 / 1.002 |
| chromatic-number-subset-dp-vs-inclusion-exclusion (T6 + T8) | V2 | 0.982 / 0.986 |
| range-minimum-queries-naive-vs-sparse-table | V2 | 1.009 / 1.000 |
| bipartite-matching-kuhn-vs-hopcroft-karp | V2 | 0.977 / 0.982 |
| max-flow-edmonds-karp-vs-dinic | V1 | — |
| 3sat-brute-force-vs-schoening (T6 + T8) | V1 | — |

Each harness has an oracle independent of both implementations. The agent's control experiment reports that every oracle rejects deliberately wrong outputs, e.g. 111/111 for matching and 84/84 for 3-SAT (agent report; `experiments/2026-10-07_oracle_controls.py`).
The chromatic-number DP is the plain variant with exactly 3ⁿ − 2ⁿ inner steps, not Lawler's O(2.4423ⁿ) version; the entry says so.

### RL-028 · NEAR-MISS · Schöning: timing cannot separate (4/3)ⁿ from 2ⁿ in the range Python can time → V1
On unsatisfiable formulas, n = 4..12: α = 0.960 against (4/3)ⁿ·n^2.5 and α = 0.865 against 2ⁿ. Both pass, so the fit does not discriminate.
The suggested planted unique-solution family is far from the worst case: success per try was 5.7–15× above the proven bound p(n) on all 30 instances (agent report).

### RL-029 · INCONCLUSIVE · Max flow: random networks are far from the worst case → V1
Edmonds–Karp made only 21–176 augmentations, and Dinic needed 2–4 phases. Fits against the claimed bounds would fail (α = 0.558 vs n⁵, 0.479 vs n⁴). No worst-case family was built (agent report).

### RL-030 · NEAR-MISS · Matching: timing passes even for wrong exponents; V2 rests on exact counts
On the agent's adversarial family (K_{2a,a} plus graded paths, a = k²), timing passes not only for the claimed exponents but also for wrong ones (Kuhn vs n^2.5: 1.168; Hopcroft–Karp vs n²: 1.221, vs n³: 0.815).
The exact counts pin the behaviour down:
- exactly k + 1 Hopcroft–Karp phases for every k = 2..16;
- Kuhn's edge scans ≈ 0.144·V·E;
- Hopcroft–Karp's ≈ 1.01–1.05·E√V.

V2 is kept, but this shows the ±0.25 timing test is not discriminative here; see RL-040.

### RL-031 · CORRECTED · Agent self-corrections in the classical batch (all before any number was used)
- A palindrome probe built its "random" string from a fresh RNG per character, so the string was constant.
- An early-exit docstring predicted "3–4 passes" before the run; the measurement gave 3.25 → 5.22 passes (n = 8 → 64).
- The max-flow V1 justification was drafted before its probe ran.

Each was corrected to the measured numbers (agent report).

### RL-032 · VERIFIED · Three new T9 pairs and three new staging entries
Recorded α values (RL-044):
- **deutsch-jozsa** (V2): α = 1.000 for the deterministic exact algorithm on worst-case inputs; constant 20 for the randomized algorithm (error 2⁻¹⁹) and constant 1 for the quantum one. The entry states prominently that the gap exists only against **exact** classical algorithms.
- **collision-problem** (V2): 1.003 / 1.021 / 1.164. The last variant is pre-asymptotic: the exact slope over n = 15..30 is 1.009.
- **minimum-finding** (V2): 1.000 / 0.886.

Staging: element-distinctness-quantum-walk (T9), forrelation (T9), linear-systems-hhl (**T6**: there is no proven classical lower bound, and the dequantization results address a different, low-rank problem).
The three existing T9 entries report identical query counts before and after the `lib/qsim.py` change (agent report §4). In RL-044 they are also identical to RL-022 (5/5 reported fits).

### RL-033 · CORRECTED · BHT implementation stopped querying its classical set early (caught by theory vs simulation)
The first collision-finder version gave z = +0.57, −1.97, −2.73, −1.61, −1.56 against the exact expected query count. Four of five were negative, which pointed to a real bias.
After the fix (all of K is queried first, as in the paper): z = +0.57, −0.57, −0.87, −0.41, −1.31 (agent report; `experiments/2026-10-07_collision_expected_queries.py`).

### RL-034 · NEAR-MISS · Quantum batch: fits near the edge, late crossovers, chance anomalies
- **Dürr–Høyer:** α = 0.800 over n = 2..10, from lower-order terms in the time-out, so V2 uses n = 4..12 (0.886). With the published constants the quantum count only drops below classical N between N = 2048 and 4096.
- **Suspicious z-scores, each checked with replications declared in advance:**
  - classical collision, n = 8: +3.19, then +2.05; an independent 10⁶-sample sampler gave −0.95;
  - Deutsch–Jozsa, n = 8: −2.37, then +0.65;
  - a single exponential-search setting: −2.96, with the combined z over 11 settings −0.57.

  All are consistent with chance, and the original values are kept (agent report).

### RL-035 · DECISION · Query accounting and reusable quantum-search tooling
A phase conditioned on a predicate of a non-Boolean oracle value costs 2 queries (compute and uncompute; Boyer–Brassard–Høyer–Tapp). The new code is `Oracle.apply_phase_where` and `lib/qsearch.py`, which provides known-count Grover, exponential search for an unknown count, and exact expected costs; it is covered by `tests/test_qsim.py` (18 tests).
Constants are therefore up to 2× higher than in some papers' accounting. Exponents are unaffected.

### RL-036 · VERIFIED (pipeline) and NULL · Flip-graph search for GF(2) matrix multiplication schemes
The `search/` package has two exact verifiers of the Brent equations that share no code, 47 unit tests (a mutation check shows they catch broken moves), and a CLI: `python -m search flip|verify|sortnet`. Results (agent report; 77 saved schemes, all re-verified in a separate step):
- **2×2:** rank 7 from rank 8 on 10/10 seeds, in 48–1,577 flips. An exhaustive check of 19,702 subspaces found **no rank-6 scheme over GF(2)**; that check was validated against an independent computation on 7,096 tensors.
- **3×3:** rank 23 (Laderman's) on 10/10 seeds, in 13,470–709,024 flips; the 10 schemes are pairwise inequivalent. **NULL for rank 22** in 9.8·10⁷ further flips.
- **4×4:** the best walk without a factor cap reached 52 (660M flips). With a cap of 4, one walk in 14 reached 49 in 1.6M flips; that scheme is very likely Strassen ⊗ Strassen, equivalence not proven. **NULL for rank ≤ 48** in about 1.05·10⁹ steps. Rank 47 is known to exist (AlphaTensor), so the null result reflects the search, not the problem.
- **Sorting networks, n = 2..8:** sizes 1, 3, 5, 9, 12, 16, 19, all equal to the known optima. These are fixed-size objects, so this is pipeline validation only.
- **Context (maintainer, via one arXiv API query):** Rudich & Rousseau, "Lower Bound of 22 for 3x3 Matrix Multiplication over the Integers", arXiv:2610.01639 (2026-10-01). It claims rank ≥ 22 for 3×3 recursive algorithms with integer constants, which would rule out beating Strassen's exponent with any 3×3 scheme over Z. It is a preprint, not yet peer-reviewed, and GF(2) is a different setting.

Compute: about 85 minutes, single process, below-normal priority.

### RL-037 · CORRECTED · log₄47 = 2.7773, not "≈ 2.774"
The maintainer had written 2.774 in `notes/constant-factor-alphadev.md`, in the `relationship` of `pairs/matrix-multiplication-naive-vs-strassen`, and in its README. log 47 / log 4 = 2.777294…; all three were corrected. Found by the search agent.

### RL-038 · CORRECTED · Process: the CPU-priority line in the maintainer's briefs did nothing
`ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)` fails silently on 64-bit CPython: it returns 0 with error 6 (invalid handle), because ctypes truncates the handle.
The other agents therefore probably ran at normal priority, so their timing runs competed for CPU. The maintainer's final recorded run (RL-044) was made with no other Python process running.
A correct version, which declares the argument types and reads the priority back, is in `search/machine.py`.
Also recorded: the search agent ran one read-only `git status` despite the brief, and about 2 minutes of its early smoke tests ran at normal priority.

### RL-039 · VERIFIED (measured) · When memoisation is enough: distinct subproblems in the stored slow recursions
The pattern agent traced the unchanged slow implementations to count their distinct subproblems (agent report; `experiments/2026-10-07_subproblem_redundancy.py`):

| Implementation | Distinct subproblems |
|---|---|
| Fibonacci | n + 1 |
| edit distance | (n+1)² |
| matrix chain | n(n+1)/2 |
| cofactor determinant | **2ⁿ** |
| shortest-path DFS | **n·2^(n−3) + 1** |

The closed forms were read off the tables, not proven. So memoising the natural key gives a polynomial algorithm for the first three but not for the last two, whose fast algorithms need a structural insight: row-operation invariance, and dropping the visited set. This is a measurable form of the START_HERE section 5 warning about "un-bloating".

### RL-040 · IDEA · Count-based V2 for classical entries, and a discriminating V2 diagnostic
Proposed independently by two agents:
1. **Operation counts:** let classical implementations report exact operation counts (e.g. an instrumented number type counting multiplications). This would make small exponent gaps resolvable: Strassen 7ᵏ vs 8ᵏ, matching, Schöning.
2. **Discriminating diagnostic:** report local slopes, or require the fit against the next-lower plausible cost to *fail*, so that a V2 pass rules out the slower alternative.

Not adopted yet; this needs a DECISION.

### RL-041 · IDEA · Candidates for the next round (pattern report §3; costs mostly recalled, to be checked when implemented)
- **XOR convolution:** naive 4ⁿ vs fast Walsh–Hadamard n·2ⁿ, the classical twin of the Hadamard step in Bernstein–Vazirani, Deutsch–Jozsa and Forrelation.
- **Zeta transform:** 3ⁿ vs Yates n·2ⁿ.
- **Regex matching:** backtracking vs Thompson NFA. Backtracking on (a?)ⁿaⁿ took exactly (n/2+2)·2ⁿ − 1 steps for every even n ≤ 20 (measured).
- **Global minimum cut:** brute force vs Stoer–Wagner.
- **NAND-tree evaluation:** deterministic 2ʰ vs randomized ((1+√33)/4)ʰ leaf reads; the tag is to be decided.
- **Optimal BST:** n³ DP vs Knuth's n².

40 candidates in total, with their traps.

### RL-042 · DECISION · Two questions raised by the pattern agent
- **Lehman factoring (candidate 28): not implemented.** Factoring stays catalogued as open (START_HERE section 10).
- **NAND-tree tag:** decided when the entry is implemented. The proposal is T4 primary with T3 secondary, because randomisation changes the exponent.

### RL-043 · NULL · Pair generators beyond linear recurrences: designs only
The pattern report §5 proposes generator designs:
- a bilinear-scheme amplifier fed by the flip-graph search;
- a branching-rule synthesiser (honest only as upper bounds);
- a small Boolean-function composer;
- shared gates for every generator: a resolvability check that blocks undecidable V2 claims, a subproblem profiler, and deduplication.

None was implemented tonight.

### RL-044 · VERIFIED · Recorded run over all 54 entries before committing the overnight work
Ledger: [ledger/runs/20261006T025704Z.json](ledger/runs/20261006T025704Z.json), at base commit `ae69311` with uncommitted agent work in the tree (so `git_dirty` is true), and no other Python process running.
- **Result:** 54/54 entries pass their claimed level (pairs: 34 at V2, 5 at V1; staging: 11 at V0; synthetic: 4 at V2). V1 covered 43 entries, 2812 instances and 5917 implementation runs.
- **V2:** 88 measurements, all passing, α from 0.886 to 1.164.
- **Stability against RL-022:** the reported-count fits are identical (5/5). The largest timing α change on unchanged entries is 0.033 (fast doubling, 1.128 → 1.095).
- **Unit tests:** 84 OK.
- **Citations:** 157 identifiers checked, 0 problems; 131 sources also compared on volume, issue and pages; 35 sources have no DOI or arXiv id.
- **Index:** 39 validated pairs (up from 28), 12 entries with T6, 9 with T9, 4 synthetic (T7).

### RL-045 · VERIFIED · Recorded run on the committed overnight state
Ledger: [ledger/runs/20261006T030338Z.json](ledger/runs/20261006T030338Z.json), made at commit `7511ea9` with a clean tree.
- **Result:** 54/54 entries pass their claimed level. All 88 V2 measurements pass, with α from 0.886 to 1.164.
- **Stability against RL-044:** all 14 query-count series are **identical** value for value. The largest change in a timing α is 0.015 (matrix-chain plain recursion).

### RL-046 · VERIFIED · The overnight state also passes CI (independent environment)
GitHub Actions runs 37407158461 (`7511ea9`) and 37407344397 (`834b66f`) succeeded in every job (validate, scaling, sources) on `ubuntu-latest` with Python 3.12.
All 88 V2 claims, including the 11 new pairs, the 3 new T9 query-count fits and the 4 synthetic entries, were therefore reproduced on a second OS and Python version. Provenance: external (GitHub Actions).

---

## 2026-10-06 (morning; heading date corrected, see RL-055)

### RL-047 · DECISION and VERIFIED · Discriminating V2 (rivals) and exact-count V2 for classical entries; Strassen raised to V2
**Decision** (follows RL-040): `harness.scaling.rivals` lists cost expressions that the same measurements must **not** fit (|α − 1| > tolerance). A V2 claim with rivals therefore *excludes* the named slower or faster alternative, not just "fits the claim".
Classical entries may also use `measure: "reported"` with exact operation counts produced by instrumentation. Implementations must stay unchanged and the count must come from the harness.

**First use:** `pairs/matrix-multiplication-naive-vs-strassen`.
- The harness counts every scalar multiplication through an instrumented number type, `CountingInt`, padding zeros included.
- **Counts** on n = 32, 64, 128, 256: schoolbook exactly n³; Strassen (cutoff 16) exactly 7^(log₂(n/16))·16³ (28 672 / 200 704 / 1 404 928 / 9 834 496).
- **Fits** at tolerance 0.02 (the counts are exact): α = 1.000 for both claims.
- **Rivals:** Strassen's counts against n³ give α = 0.936, rejected. The schoolbook counts against n^log₂7 give α = 1.069, rejected.
- **Products:** with counting entries, both implementations give the same products as plain integers for n ≤ 64 (console).

The entry moved from V1 (RL-006) to V2.
**Rationale:** RL-006 showed that timing cannot separate 3 from 2.807. Exact counts remove the noise, so a tight tolerance plus a rival makes the separation explicit. Additions are not counted.
`tests/test_validate.py` has 2 new tests: a rival that also fits makes V2 fail; a rival that does not fit leaves V2 passing.

### RL-048 · VERIFIED (measured) · Timing fits never resolve log factors; only exact counts do
Every fit now carries an informational diagnostic: α against cost·log n and against cost/log n.
In the recorded run (RL-050), 82 of the 90 V2 measurements had a computable diagnostic. The other 8 are constant costs or variants whose cost is degenerate over n_values.
**Only 5 of the 82 resolve a log factor** (both variants outside the tolerance band), and all 5 are exact counts:
- Bernstein–Vazirani, classical (α 0.601 / 2.58);
- Grover, quantum (0.685 / 1.318);
- Simon, quantum (0.653 / 3.146);
- Strassen counts (0.926 / 1.087);
- schoolbook counts (0.930 / 1.081).

**None of the 77 timing fits at tolerance 0.25 resolves a log factor.** A timing-based V2 therefore means "growth consistent with the claim *up to logarithmic factors*". The README's level table now says so.
**Follow-up IDEA:** move more entries to exact-count V2 with rivals (e.g. comparison counts for sorting, edge scans for matching), where the claim includes or excludes a log factor.

### RL-049 · DECISION · Background execution and compiled kernels (by the user)
1. **Background runs:** every run longer than a few seconds goes in the background with an explicit time budget and a completion signal. The maintainer does not watch it and stays available meanwhile. Timing-sensitive runs must not overlap CPU-heavy jobs.
   A foreground recorded run was interrupted by the user to make this point. It had written no ledger file; the run was repeated in the background (RL-050).
2. **Compiled kernels (C/C++, or single-file Rust):** allowed only if they build in seconds, as single-file programs in separate processes. Memory safety is treated as untrusted:
   - bounds checks in test builds;
   - differential tests against the Python reference, run once in the test suite, not on every run;
   - every produced result re-verified by the exact Python verifier before it is saved or claimed.

**Rationale (measured, RL-036):** finding is expensive and checking is cheap. Re-verifying all 77 saved schemes took 2.4 s, against about 5100 s of search, i.e. about 0.05%. A compiled kernel speeds up the 99.95% part, and the cheap exact check rules out false results from memory errors.

### RL-050 · VERIFIED · Recorded run after adding rivals and exact-count V2
Ledger: [ledger/runs/20261006T070542Z.json](ledger/runs/20261006T070542Z.json), base commit `83b12c3`, with the RL-047 changes uncommitted in the tree (`git_dirty` true), run in the background.
**Result:** 54/54 entries pass their claimed level. All 90 V2 measurements pass, including the two count-based ones with rivals.

### RL-051 · VERIFIED · Single-file Rust compiles in under a second here; CI green on `92db882`
**Measurement (console):** `rustc -O` on a dependency-free, kernel-sized file took 0.87 s cold, then 0.22 s and 0.25 s. With `-C opt-level=1` it took 0.21 s.
The long builds the user had experienced come from cargo and dependencies, not from rustc on a small file.
**Decision (by the user):** compiled kernels are written in single-file Rust without cargo. C would be about as fast for this kind of loop, but Rust gives memory safety by default and nothing needs installing.
**CI:** GitHub Actions run 37427874381 on `92db882` succeeded in validate, scaling and sources (external).

### RL-052 · VERIFIED and CORRECTED · Rust flip-graph kernel; a no-op plus transition caught by coverage checking
**Built:**
- `search/kernel/flipwalk.rs`: flips, zero-term removal and two-factor merges, plus transitions, restarts, weight cap, seeded SplitMix64, time and step budgets. It runs as a separate process at below-normal priority.
- `search/rust_kernel.py`: builds the kernel, cached by source SHA-256 (0.42 s for a full build), runs single or parallel walks, and **re-verifies every result** with the exact Brent-equation verifier and a random-matrix check. A failing result raises KernelResultError and is never saved; `save_scheme` also refuses unverified schemes.
- `search/kernel_reference.py`: a line-by-line Python mirror.

**Differential test** (`tests/test_search_rust.py`): Rust and the Python mirror give identical best schemes, step counts, counters and improvement histories on 6 configurations, covering plus transitions, weight-cap rejections and restarts. A further test asserts that the restart branch is actually exercised.
Other tests: the 2×2 run reaches rank 7 and passes both independent verifiers; malformed input exits cleanly with code 2; a corrupted scheme is rejected.

**CORRECTED (maintainer's design error):** the first plus transition rewrote a⊗b⊗c + a'⊗b'⊗c' as (a+a')⊗b⊗c + a'⊗b⊗c + a'⊗b'⊗c'. Its first two terms share b and c, so the merge rule immediately undid it, and the move was a no-op.
The differential test still passed, because both implementations shared the bug. It was found only by checking which branches the tests exercised: restarts were 0 in every case.
The fix uses the non-collapsing form a⊗b⊗c + a'⊗b'⊗c' = (a+a')⊗b⊗c + a'⊗(b+b')⊗c' + a'⊗b⊗(c+c'), whose cross terms cancel in pairs. It requires a≠a', b≠b' and c≠c'.
After the fix, 200 plus transitions raise a 2×2 scheme from rank 8 to 23 and it still verifies; a regression test was added.
**Lesson:** a differential test proves agreement, not correctness. Branch coverage and invariant tests must accompany it.

**Speed (console, one core, before the fix):** 4×4 walks ran at 2.1·10⁷ steps/s (3.6·10⁶ successful flips/s), against about 2.4·10⁵ flips/s for the Python driver of RL-036 (1.6M flips in 6.6 s). That is at least 15× per core in flips, before using the 16 logical cores.
The move policies of the two drivers differ, so this comparison is approximate. Plus transitions happen at most once per 50 000-step plateau, so the fix does not materially change throughput; post-fix numbers come from the next recorded runs.

### RL-053 · DECISION · License changed to fully open: code Apache-2.0, data CC BY 4.0 (by the user)
This supersedes RL-009. The repository is no longer non-commercial: code is under the Apache License 2.0 (`LICENSE`), and data and documentation are under CC BY 4.0 (`LICENSE-DATA`). See `NOTICE`.
`COMMERCIAL.md` and the PolyForm Noncommercial text were removed. The commercial-relicensing clause in CONTRIBUTING was replaced by "inbound = outbound" under the same licenses.
Added `CITATION.cff` (author Benjamin Weisz; type dataset; validated with cffconvert against CFF schema 1.2.0) and a "How to cite" section with BibTeX in the README. The official license texts were downloaded from apache.org and creativecommons.org.
**Rationale:** the user prioritises reliability and reputation, with positive effects on their other projects, over license income. Openness maximises reuse, independent re-verification and citation.
CC BY 4.0 is the license researchers expect for data, and it explicitly asks for attribution when material is shared. The licenses themselves do not compel academic citation. Citations come from scholarly norms and from making citing easy: a DOI per release (Zenodo, planned at public release), CITATION.cff, and a dataset paper or preprint (planned).
The change was made while the repository is private with no external contributors. Once a version is published under Apache 2.0, that grant cannot be withdrawn.

### RL-054 · VERIFIED (rediscovery of the best known 4×4 rank) and NULL · First parallel Rust search, 30 minutes on 12 processes
Script: `experiments/2026-10-07_rust_parallel_30min.py`. It ran three jobs of 4 walk processes each, every walk limited to 1800 s, at below-normal priority. Logs are in `search/runs/2026-10-07_rust_*.jsonl`; verified schemes in `search/schemes/rust-2026-10-07/`.

| Job | Setting | Best rank per seed (time first reached) |
|---|---|---|
| A | 4×4×4 from the standard algorithm, weight cap 4, seeds 1–4 | 52, 52, 52, 52 (3.7–25.6 s), then no further improvement |
| B | 4×4×4 from the standard algorithm, no cap, seeds 5–8 | 49 (1.3 s), 49 (195 s), 50 (1159 s), **47 (726.7 s, step 1.23·10¹⁰)** |
| C | 3×3×3 from a saved rank-23 scheme, target 22, seeds 1–4 | 23, 23, 23, 23 |

Throughput was 1.27–2.30·10⁷ steps/s per process with 12 processes running concurrently.

**Rank 47, 4×4×4 over GF(2):** this matches the best known rank over GF(2) (Fawzi et al. 2022, AlphaTensor).
- The scheme passes both independent exact verifiers (`verify`, `verify_explicit`) and 200 random GF(2) matrix-pair checks; the checks took 0.05 s.
- It is **not** valid over the integers as it stands, so it is a characteristic-2 result, like AlphaTensor's.
- Applied recursively, it gives exponent log₄47 = 2.7773 in characteristic 2, below Strassen's log₂7 = 2.8074.
- This is a **VERIFIED rediscovery** of a known rank, not a new record. Whether the scheme is equivalent to a published rank-47 scheme was not checked.
- For comparison, the Python driver's best over about 1.05·10⁹ steps was 49 (RL-036).

**NULL:**
- 3×3×3 rank 22 over GF(2), in about 1.65·10¹¹ steps (2.75·10¹⁰ flips) from one rank-23 start; rank 22 over GF(2) remains open as far as we know.
- 4×4×4 below 52 under weight cap 4, in about 9.6·10¹⁰ steps.

**NEAR-MISS / deviation:** with this kernel the weight cap of 4 *hurt*: all capped walks stuck at 52, while uncapped walks reached 49, 50 and 47. The Python driver (RL-036) had found the cap helpful (one capped walk reached 49). The move policies differ (plus-transition form, restarts, candidate selection), so the effect of the cap depends on the policy and should not be generalised.

**IDEA:** add a dataset entry for characteristic 2, "Strassen recursion vs recursive rank-47 4×4 scheme", with V2 on exact multiplication counts. The exponent gap is small: the rival's α would be log₂7 / log₄47 = 1.0108, so the tolerance must be below 0.0108. Exact counts at powers of 4 give α = 1.000 exactly, which makes this discriminable (the method of RL-047).

---

## 2026-10-06 (late morning: second autonomous round, consolidated by the maintainer)

Four background agents. Their detailed reports are in research/:
- [count_based_v2](research/2026-10-07b_count_based_v2.md)
- [new_candidates](research/2026-10-07b_new_candidates.md)
- [search_formats](research/2026-10-07b_search_formats.md)
- [deviations](research/2026-10-07b_deviations.md)

The file-name prefix "2026-10-07b" is an identifier, not a date (RL-055). Numbers marked "agent report" were not re-run by the maintainer unless stated. Every entry was re-validated in the recorded run (RL-064).

### RL-055 · CORRECTED · Wrong date on the overnight and morning work
The maintainer labelled the overnight round and the following work "2026-10-07". Everything happened on **2026-10-06**, local time UTC+2; the ledger timestamps (UTC) and git commit dates agree.
The two RESEARCH_LOG section headings and the event dates inside entries, lib/ and tests were corrected; earlier entries were not otherwise rewritten.
The prefixes "2026-10-07_" and "2026-10-07b_" in file names (experiments/, research/, search/runs/) and the directory names `search/schemes/rust-2026-10-07*` are kept as **stable identifiers**. Renaming more than 100 referenced files would risk broken links. The deviation agent found the mismatch.

### RL-056 · VERIFIED and CORRECTED · Deviation analysis, and the fixes made by the maintainer
The deviation agent analysed the 5 ledger runs recorded before 09:08 local (agent report; scripts `experiments/2026-10-07b_*`, 10 files).
**Checks that found nothing wrong:**
- every deterministic count matches its closed form exactly (Grover, Bernstein–Vazirani, Deutsch–Jozsa, minimum-finding classical, Strassen and schoolbook);
- all randomized means are within |z| < 2 of their exact expectations;
- all 54 α values in the RL-021 table match the ledger;
- index entries match the entry files.

**Findings and actions:**

| # | Finding (agent report) | Action |
|---|---|---|
| F1 | Matching: timing data fitted the other algorithm's cost too (Hopcroft–Karp against n³: α ≈ 0.82; Kuhn against n^2.5: ≈ 1.17) | **fixed** by count-based V2 with rivals (RL-057) |
| F2 | Karatsuba: timing data also fitted n² (α 0.806–0.811) | **fixed by the maintainer** (below) |
| F3 | Collision, BBHT variant: neither the measured means nor the exact expectations over n = 3..15 rule out 2^(n/2) (α 0.776 / 0.770) | **fixed**: the known-t variant declares 2^(n/2) as a rival and rejects it (α = 0.681). The BBHT variant is documented as pre-asymptotic in this range and gets no such rival. |
| F4 | Chromatic inclusion–exclusion: the timing fit cannot tell n·2ⁿ from 2ⁿ (α 0.905 against 2ⁿ passes) | **open**; the entry already states it (IDEA, RL-061) |
| F5 | Simon quantum: α 1.121 was 1.80 standard errors above the exact-E slope; n = 2 supplied 83% of the variance | **fixed**: n_values 3, 4, 6, 8, 10 with 100 instances. Recorded α = 0.970 against an exact-E slope of 0.9573 over these n. |
| F6 | Run-to-run stability reflects timing noise only, because each run uses the same seeded instance per n | **documented** here. Instance variation is covered only by `samples`. |
| F7 | Maximum subarray: the instance type (all-negative, all-positive, mixed) changed with n, which bent Kadane's local slopes (0.778 / 1.235) | **fixed**: `generate_scaling` always draws mixed signs |
| F8 | Provenance: the only rival-based evidence sat in one run on a dirty tree | addressed by RL-064 (recorded run) and the follow-up run on the clean commit |
| F9 | High-exponent timing fits have α < 1 with rising local slopes, from pre-asymptotic lower-order terms (Floyd–Warshall would need n > 703 to reach a local slope of 0.99) | Floyd–Warshall **fixed** by exact counts (exactly n³ − n, RL-057); others documented |
| F10 | All five log n fits have α > 1 with falling slopes (untested hypothesis: cheap small-integer arithmetic) | **open** (IDEA) |
| low | Secondary T3 tag applied unevenly | **fixed**: T3 added to Fibonacci (DP Θ(n) → fast doubling Θ(log n)) and MST (Kruskal O(n² log n) → Prim Θ(n²)) |

**Maintainer's fixes, validated with `--scaling -v` (console):**
- **Karatsuba:** a counting digit type, `CountingDigit`, propagates through the carry and borrow arithmetic. On powers of two the counts are schoolbook = n² exactly and Karatsuba = 3^(log₂(n/32))·32² exactly (e.g. 248 832 at n = 1024). Products were checked against the big-integer oracle. Both fits give α = 1.000 at tolerance 0.02, and the rivals are rejected (Karatsuba against n²: 0.792; schoolbook against n^log₂3: 1.262).
- **Collision:** the classical birthday counts reject 2^(n/3) (α 1.505).
- **Simon:** the classical counts reject n (α 2.957), and the quantum counts reject 2^(n/2) (α 0.473).
- **Inversion counting:** a stale caveat ("the V2 fit cannot resolve the log factor") was corrected, since the exact counts now resolve it.

### RL-057 · VERIFIED · Count-based, discriminating V2 for 8 more entries
The agent converted sorting, element distinctness, bipartite matching, inversion counting, LIS, closest pair, APSP and string matching (agent report; re-validated in RL-064).
- **Instrumentation:** instrumented element, weight or character types are passed in through `generate_scaling`. Implementations and V1 are unchanged, and the scaling inputs keep the same seeded draws.
- **Scale:** 17 algorithm fits and 36 declared rivals, all rivals rejected. The tolerance is 0.03 throughout; the largest |α − 1| is 0.0140 and the smallest rival distance 0.0644.
- **Log factor resolved in 16 of 17 fits**, against 0 of 77 under timing (RL-048). The exception is LIS subset enumeration, which counts comparisons rather than loop steps; for an exponential algorithm a log factor is not a meaningful alternative.
- **Matching:** the counts now reject Kuhn against n^2.5 and Hopcroft–Karp against n² and n³, which RL-030 timing had accepted. The harness counts equal the earlier instrumented-copy counts value for value.
- **Cross-version check:** all 17 count series are identical under CPython 3.12.10 and 3.14.2 (same SHA-256).

Exact closed forms observed include all pairs n(n−1)/2, Bellman–Ford n²(n−1)², Floyd–Warshall n³ − n, naive matching (n−m+1)m and KMP 4n − 6.

Proxies to keep in mind:
- the closest-pair divide and conquer counts multiplications only; comparisons inside CPython's `sorted()`/`min()` differ by version (39 380 vs 39 445 at n = 1000);
- string matching passes its scaling input as tuples of a counting character type.

### RL-058 · VERIFIED · Eight new pairs at V2
The agent and its four sub-agents added the entries below; the maintainer's recorded run is RL-064 (agent report).

| Entry | Tags | V2 |
|---|---|---|
| xor-convolution-naive-vs-walsh-hadamard | T3 | exact ring operations 2·4ⁿ vs (3n+2)·2ⁿ |
| subset-sum-zeta-transform-naive-vs-yates | T3 | exact additions 3ⁿ vs n·2ⁿ⁻¹ |
| regex-matching-backtracking-vs-thompson | T2 | exact comparisons on (a?)ⁿaⁿ: (n+2)·2ⁿ⁻¹ − 1 vs n(n+1) |
| global-min-cut-brute-vs-stoer-wagner | T2 | exact additions and comparisons |
| optimal-bst-recursion-vs-dp-vs-knuth | T2 + T3 | exact comparisons; the recursion makes exactly 3ⁿ calls |
| two-sat-brute-force-vs-scc | T2 | exact operation counts; the SCC count 49(n+2) is read off the data, not proven |
| spanning-tree-count-enumeration-vs-kirchhoff | T2 | enumeration **timed** (α 0.961 / 0.995 / 0.980 over 3 runs); Bareiss exact counts |
| nand-tree-evaluation-deterministic-vs-randomized | T4 + T3 | exact leaf reads; the randomized algorithm uses the mean of 200 seeded runs |

- All declared rivals are rejected, and the log factor is resolved in every count-based fit.
- **XOR convolution:** the entry states the quantum link precisely: W = 2^(n/2)·H^⊗n, and one transform stage corresponds to one Hadamard gate. This is not a quantum speed-up for computing the transform.
- **NAND tree:** the randomized lower bound is stated for zero-error algorithms only (Saks–Wigderson 1986, confirmed through secondary sources). The deterministic 2ʰ bound comes from an adversary argument written in the entry, not checked against a publication.
- **Sources dropped as unverifiable:** Snir 1985 (the guessed DOI belonged to another paper), Farhi–Goldstone–Gutmann 2008 (no Crossref title) and Yates 1937 (book).

### RL-059 · VERIFIED (rediscoveries), NULL and a measured obstacle · Rust searches across formats
Agent report. The maintainer checked that no saved scheme is below its best known rank; all 112 pass both verifiers and 200 random checks according to the agent's separate re-verification step.

**Best known ranks.**
- **Verified by the agent with both exact verifiers on published scheme files:** AlphaTensor's GF(2) factorisations (20 formats, including 4×4×4 rank 47 and 4×4×5 rank 63) and 13 Kauers–Moosbauer files (4×4×4 rank 47 and 4×4×5 rank 60 valid over GF(2) only). The downloaded files were not added to the repository.
- **Over general rings, 4×4×4 = 48:** complex coefficients (AlphaEvolve) or rational coefficients (Dumas–Pernet–Sedoglavic), the latter not valid in characteristic 2.
- **47 is still the best known 4×4×4 rank over GF(2)** in every source consulted. Perminov's and Kauers–Wood's lists were not checked format by format, so any future rank-46 claim needs a full literature check.

**Small formats** (8 seeds each, 30–180 s per walk):
- (2,2,3) 11, (2,2,4) 14, (2,3,3) 15, (2,3,4) 20, (2,4,4) 26, (3,3,4) 29 and (3,3,5) 36: best known reached by 8/8 seeds, the slowest after 20.8 s.
- (3,4,4) 38: 6/8.
- (3,4,5) 47: 1/8.
- (4,4,5): 0/8, best 64 against 60 known.

**4×4×4 statistic.** 24 new seeds × 900 s, uncapped: **0/24 reached 47 or 48** (exact 95% interval for 47: 0–0.142). Pooled with RL-054 that is 1/28 (0.001–0.183), so RL-054's 47 was a lucky walk, not the typical outcome.
**Measured obstacle:** 19 of the 20 rank-49 endpoints have no two terms sharing a factor, so **no flip is possible** there. 18 of them have the factor-rank invariant of Strassen ⊗ Strassen. The walks that got there idled; their higher steps/s is empty scanning.

**NULL:**
- rank 46 from RL-054's rank-47 scheme: 1073 s plus 8 × 120 s, about 5.2·10¹⁰ steps in total;
- below the best known rank for all ten formats within these budgets.

**Inequivalence:** RL-054's rank-47 scheme has a factor-rank invariant different from the AlphaTensor and the Kauers–Moosbauer rank-47 files, so it is provably inequivalent to **those two**. Whether it is new among *all* published rank-47 schemes was not checked (IDEA, RL-061).

**Unplanned second execution, an accidental reproducibility check.** `experiments/2026-10-07b_small_formats.py` ran a second time, 10:55–11:07 local, after the agent had written its report. It was the agent's background job; the maintainer waited for it to finish instead of killing it, so that no log was cut off mid-write.
Consequences:
- every small-format log in `search/runs/2026-10-07b_small_*.jsonl` contains each seed **twice** (16 lines per format);
- the search compute exceeded the stated budget by about 12 minutes.

Across all 80 walk pairs, the **best rank reached was identical** in both executions, e.g. (3,4,5) gave 48, 48, 51, 51, 49, 48, 47, 48 both times. The kernel is deterministic per seed, apart from the time budget cut-off.

### RL-060 · CORRECTED · Process: an auxiliary tool broke the project environment
Installing `cffconvert` 2.0.0 into `.venv` to validate CITATION.cff (RL-053) left jsonschema at **3.2.0** (previously 4.26.0). `tools/validate.py` then refused to run ("jsonschema is required"), because it needs Draft 2020-12.
Two agents noticed. They worked around it with private environments (jsonschema 4.26.0) and re-ran their final validations after the fix; the shared venv was not touched by them.
The maintainer removed `cffconvert` and restored jsonschema 4.26.0 from requirements.txt; `validate.py --static` then gave 62/62 OK. CI was unaffected, because it installs from requirements.txt.
**Lesson:** auxiliary tools go into a separate environment, never into the project's `.venv`.

### RL-061 · IDEA · Next steps from this round
1. **Kernel:** detect dead ends (no pair of terms shares a factor) and leave them at once with a plus transition or restart, instead of idling for 50 000 steps. This changes trajectories, so `kernel_reference.py` must mirror it and the differential test must cover it.
2. **Novelty audit of RL-054's rank-47 scheme** against all published 4×4 GF(2) rank-47 schemes (AlphaTensor's full set, the Kauers–Moosbauer flip-graph sets, later catalogues), using invariants and equivalence tests.
3. **Remaining timing fits whose claims contain a log factor:** Fibonacci fast doubling, MST Kruskal, NTT and sparse-table RMQ. Convert them to exact counts.
4. **Chromatic number:** count-based V2 able to reject 2ⁿ (F4).
5. **F10:** test the small-integer arithmetic hypothesis behind the log n fits.

### RL-062 · DECISION · Cost expressions may use exact closed forms
A cost expression may be the exact closed form of the count, e.g. (n+7)·2ⁿ for 2-SAT or (n−1)³ for Kirchhoff, when it lies in the claimed Θ class. `time_complexity` must still state the Θ class, and the exact form must be stated next to it in the entry.
**Rationale:** exact counts carry lower-order terms. Fitting the bare leading term would force wider tolerances, and that would cost the rival and log-factor checks: e.g. n·2ⁿ gives α 0.958 for the 2-SAT data, and n³ gives 1.041 for Kirchhoff. Strassen's leading form works only because its counts are exact powers on the measured n.

### RL-063 · INCONCLUSIVE · Zenodo DOI for v0.1.0 not issued
The GitHub webhook delivered the v0.1.0 release event, and Zenodo answered **202** to `released`. The 409 answers to `published` and `created` are Zenodo rejecting duplicate events for the same release.
No Zenodo record appeared in the public API within about 65 minutes (two polling runs, four query forms). The likely cause is a metadata problem on Zenodo's side; the error is visible only in the owner's Zenodo account.
Action: `.zenodo.json` was added, with explicit metadata and a single license (cc-by-4.0, the dataset license). It takes precedence over CITATION.cff, whose license field is a list of two. Retried with release v0.2.0.

### RL-064 · VERIFIED · Recorded run over all 62 entries after the second round
Ledger: [ledger/runs/20261006T090819Z.json](ledger/runs/20261006T090819Z.json), at base commit `805a202` with this round's work uncommitted in the tree (`git_dirty` true), on a quiet machine (no search process running).
- **Result:** 62/62 entries pass their claimed level (pairs: 43 at V2, 4 at V1; staging: 11 at V0; synthetic: 4 at V2). V1 covered 51 entries, 3447 instances and 7323 implementation runs.
- **V2:** 108 measurements, all passing (56 wall-clock, 52 exact reported counts), α from 0.886 to 1.164.
- **Rivals:** 94 declared, **94 rejected**.
- **Log-factor diagnostic:** computed for 100 fits and resolved in **40, all of them exact counts**; 0 of the timing fits resolve it, consistent with RL-048.
- **Unit tests:** 91 OK.
- **Citations:** 173 identifiers checked, 0 problems; 147 sources also compared on volume, issue and pages; 37 sources have no DOI or arXiv id.
- **Index:** 47 validated pairs (up from 39), 12 entries with T6, 9 with T9, 4 synthetic.

### RL-065 · VERIFIED · Recorded run on the committed second-round state
Ledger: [ledger/runs/20261006T091245Z.json](ledger/runs/20261006T091245Z.json), at commit `aedbdc6` with a clean tree.
- **Result:** 62/62 entries pass their claimed level. All 108 V2 measurements pass, and all 94 declared rivals are rejected.
- **Stability against RL-064:** all 52 exact-count series are **identical** value for value. The largest change in a timing α is 0.009.

### RL-066 · VERIFIED · Zenodo DOI issued for v0.2.0
Release v0.2.0 (2026-10-06 09:15:40 UTC) produced Zenodo record 23184029 two seconds later. Version DOI: **10.5281/zenodo.23184029**; concept DOI, for all versions: **10.5281/zenodo.23184028**.
Both DOIs resolve, via DataCite (title checked) and doi.org (HTTP 302 to Zenodo). They were added to CITATION.cff (`doi`, `identifiers`) and to the README (badge, BibTeX `doi`).
v0.1.0 never produced a record (RL-063), while v0.2.0, the first release with `.zenodo.json`, did so at once. This is consistent with the metadata hypothesis (a list of two licenses in CITATION.cff), but not proven, because the v0.1.0 error is visible only in the owner's Zenodo account.

### RL-067 · VERIFIED · CI green on every commit of the second round
GitHub Actions (`ubuntu-latest`, Python 3.12) succeeded in validate, scaling and sources for all four commits:
- `aedbdc6`: second-round state, run 37441375674;
- `038b9e3`: recorded run RL-065, run 37441721503;
- `cd28ddc`: citation version 0.2.0, run 37441727738;
- `a232962`: Zenodo DOI, run 37441885450.
So the 47 validated pairs, the 94 rival rejections and the exact-count V2 fits also reproduce on a second OS and Python version. Provenance: external (GitHub Actions).

---

## 2026-10-06 (afternoon: third round, consolidated by the maintainer)

Three background agents. Their detailed reports are in research/:
- [count_v2_remaining](research/2026-10-06c_count_v2_remaining.md)
- [kernel_deadends](research/2026-10-06c_kernel_deadends.md)
- [novelty_audit](research/2026-10-06c_novelty_audit.md)

Numbers marked "agent report" were not re-run by the maintainer unless stated. All entries were re-validated in the recorded run (RL-075).

### RL-068 · VERIFIED and INCONCLUSIVE · Remaining timing fits: 3 converted to exact counts, 2 cannot be
Agent report; re-validated in RL-075.

**Converted:**
- **range-minimum-queries:** value comparisons; a two-argument `min()` calls `__lt__` exactly once, which was checked.
- **polynomial-multiplication-ntt:** multiplications with an input-derived operand. Schoolbook gives exactly n²; the NTT gives exactly 3n·log₂n + 5n for n a power of two, used as the cost expression (RL-062).
- **minimum-spanning-tree:** comparisons and +, *, divmod on input weights, for all three algorithms. Packed integer keys are themselves counting values, so `sorted()` calls their `__lt__`. Prim gives exactly (n−1)², and the enumeration exactly (n−1)·C(m, n−1) + n^(n−2) − 1.

All 7 fits pass at tolerance 0.03 (common valid window [0.0073, 0.0652)), all 18 rivals are rejected, and the log factor is resolved in every one.

**Not convertible with unchanged implementations (INCONCLUSIVE, documented in the entries):**
- **fibonacci fast doubling:** a propagating tracer sees one `__index__` call (from `bin(n)`); all arithmetic is on values created from the literals 0 and 1.
- **chromatic number:** the χ·2ⁿ multiplications and the 3ⁿ − 2ⁿ submask steps have no input-derived operand. Deviation finding F4 stays open.

**Partial counts:** the NTT count misses the twiddle updates, `pow()`, padding-zero products and all additions and reductions; the MST counts miss the union-find work and the enumeration's DFS. Both entries say so.

### RL-069 · CORRECTED · Exact counts are not always identical across Python versions
RL-057 reported that all 17 count series were identical under CPython 3.12.10 and 3.14.2. For the newly converted **Kruskal** counts this does not hold: under 3.12.10, the version CI uses, they are 0.17–0.30% lower, entirely in the comparisons inside `sorted()` (agent report).
α is 0.9982 against 0.9980, so the verdicts are unchanged. The other 6 new series are identical across the two versions.
**Rule from now on:** a count that includes comparisons made inside CPython built-ins (`sorted`, `min`, `max`, …) may depend on the Python version. The entry must say so, and V2 must not rest on an exact equality across versions.

### RL-070 · CORRECTED · RL-054's rank-47 scheme is a rediscovery of a published scheme
The novelty audit found that the rank-47 scheme of RL-054 (`search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.json`) is **equivalent** to a scheme Kauers and Moosbauer have published since October 2022: `http://www.algebra.uni-linz.ac.at/people/mkauers/matrix-mult/solutions/444/47/b0/jb050da4aa249f5a.exp` (directory date 2022-10-27).
- **Certificate:** the cyclic shift (a,b,c) → (b,c,a), then the sandwich P a Q⁻¹ ⊗ Q b R⁻¹ ⊗ R c P⁻¹ with P = 49571, Q = 65191, R = 6073 (bitmask encoding; rows in the report). It maps our 47 terms exactly onto the published 47.
- **Check:** the certificate was re-checked with separate list arithmetic and brute-force inverses. The same group element also maps the standard algorithm to a valid scheme, which confirms it is a symmetry of the tensor.
- The two schemes share no terms, so only an equivalence test could reveal the identity.

RL-054's wording ("matches the best known rank; a rediscovery, not a new record") stands. The scheme itself is now known to be **a published scheme up to equivalence**.
RL-059's statement that it is inequivalent to one AlphaTensor file and one Kauers–Moosbauer file remains true, but is superseded: those were not all the published schemes.

### RL-071 · VERIFIED · Equivalence testing; a rank-47 class not among the published classes we could obtain
**Tool:** `search/equivalence.py` (16 unit tests in `tests/test_search_equivalence.py`).
- **Group:** the one Kauers and Moosbauer state (ISSAC 2023 §2): GL(4,2)³ sandwiches, the cyclic shift, transposition and term permutations; AlphaTensor uses the same action. The de Groote 1978 papers were not read, so this is not claimed to be the full isotropy group. Equivalence certificates hold under any larger group; inequivalence is relative to this group.
- **Invariants,** each with a preservation argument in the report: the factor-rank profile, the ordered profile over S₃, per-term ranks plus the characteristic polynomial of abc, and colour refinement over pairs of terms.
- **Exact test:** a complete backtracking search returning a checked certificate or "none". No pair was left undecided.

**Collection.** 99 129 public 4×4×4 rank-47 GF(2) scheme files, all passing both exact verifiers. They contain only **25 distinct term sets**: the 99 101 files under `x47/` are 4 schemes repeated with their products in different orders. The 25 sets form **exactly 4 equivalence classes**: AlphaTensor; Kauers–Moosbauer (the flips-repo file and the arXiv:2210.04045 scheme are equivalent); Zaru's FastMatrixF2 (doi:10.5281/zenodo.22823115); and the class containing RL-054's scheme.
Sources and pinned versions are in the report. No third-party scheme file was added to the repository.

**Result.** The five rank-47 schemes from RL-072 (seeds 610, 617, 618, 622 and the benchmark's seed 707) are pairwise equivalent, each with a certificate. Their factor-rank profile proves them **inequivalent to all four published classes**.
The strongest allowed statement is therefore: *this rank-47 class is inequivalent to all 99 129 published 4×4×4 rank-47 GF(2) schemes we could obtain (4 classes)*. It is **not** a claim of absolute novelty: Kauers and Moosbauer report more than 100 000 rank-47 schemes, while their public directory holds 23 distinct ones. It is the same rank, so it is not a new pair and changes no exponent.

### RL-072 · VERIFIED (exactness) and NULL (benefit) · Dead-end detection in the Rust kernel
**Design** (agent report):
- A failed candidate search proves that term i's factor at position p is unique. These facts are stamped per cell, with an epoch counter that advances on every scheme change.
- Once r of the 3r cells are stamped, a deterministic completion sweep checks the rest.
- The scheme is a dead end exactly when all 3r cells carry the current stamp. The detection is exact in both directions, with the argument in the report, and leaves the dead end at once (restart or plus transition).
- `--dead-end 0` reproduces the old kernel exactly: 17/17 step-limited cases match a verbatim copy of the old source, whose checksum equals the kernel recorded in RL-054 and RL-059.

Mirrored in `kernel_reference.py`. The differential tests cover both modes and assert that the branch is exercised. One gap: a dead end left through a restart is not asserted, because it never occurred in any probe.

**Throughput (8 walks at once):**
- at a dead end: flips/s ×49 (1.91·10⁴ → 9.41·10⁵);
- away from dead ends: about 5% slower (medians 0.981 and 0.964), with machine drift not separated.

The agent's first note ("no measurable overhead") was wrong and was corrected.

**Measurement** (seeds 601–624, 900 s each, 8 at a time, 11:44–12:29 local): rank 47 in **4/24** walks (95% CI 0.047–0.374), against 0/24 in RL-059 (Fisher p = 0.109). Reaching rank ≤ 49 was 14/24 against 20/24.
**But the four rank-47 walks owe nothing to the escape.** Re-run with `--dead-end 0`, all four reach the same rank-47 scheme at the same step (`experiments/2026-10-06c_counterfactual_old_kernel.py`); the 0/24 → 4/24 difference lies between seed sets.
**NULL:**
- no walk left a rank-49 dead end, despite 1.94·10⁸ escapes in 8 298 s, because each walk's escapes landed on only 2–11 distinct dead ends;
- rank 46: about 1.18·10¹⁰ steps after reaching 47.

**Decision:** the detection stays available and on by default, since it is exact and cheap, but it is not expected to raise the rate of reaching 47. Detecting a change from 1/28 to 4/24 would need about 83 walks per arm.

### RL-073 · CORRECTED · Process: too many requests to an academic server
To collect published schemes, the novelty agent made about 99 000 HTTP requests to the Linz server of Kauers' directory in roughly 30 minutes, over 4 parallel connections, all cached and none repeated. That is about 55 requests per second against a university web server, which is not considerate use. The brief set no rate limit; that omission is the maintainer's.
**Rule from now on:** crawls of third-party servers are rate-limited (at most about 1–2 requests per second, one connection), prefer bulk archives or repositories, and identify themselves in the User-Agent. The cache (outside the repository) makes any repeat unnecessary.

### RL-074 · IDEA · Next steps from the third round
1. **Line-execution counts** via `sys.monitoring` (a prototype exists in `experiments/2026-10-06c_value_reach_probe.py`) would give exact counts for Fibonacci fast doubling (bit_length(n) loop steps) and chromatic number (χ·2ⁿ multiplications; 3ⁿ − 2ⁿ submask steps). This is a methodology change, counting executions of code lines rather than operations on values, so it needs a DECISION. For chromatic number the instance family also matters: χ/n wanders between 0.500 and 0.636 on G(n, 0.8); the complement of a perfect matching (χ = n/2) is an untested alternative.
2. **Search:** stronger escapes, such as several plus transitions, a tabu on recently visited dead ends, or portfolio restarts, compared on the same seeds with about 83 walks per arm.
3. **The rank-47 class of RL-071:** a check against further collections, if any appear. Contacting the authors of the known collections is an outward-facing step and is left to the owner.

### RL-075 · VERIFIED · Recorded run after the third round
Ledger: [ledger/runs/20261006T104637Z.json](ledger/runs/20261006T104637Z.json), at base commit `1dd6556` with this round's work uncommitted, on a quiet machine.
- **Result:** 62/62 entries pass. V1 covered 51 entries, 3447 instances and 7323 implementation runs.
- **V2:** 108 measurements, all passing (59 exact reported counts, 49 wall-clock), α from 0.886 to 1.164.
- **Rivals:** 113 declared, **113 rejected**.
- **Log-factor diagnostic:** resolved in 47 fits, all exact counts.
- **Unit tests:** 110 OK.
- **Citations:** 173 identifiers checked, 0 problems; 147 sources also compared on volume, issue and pages.

### RL-076 · VERIFIED · Third-round state: clean recorded run and CI
Ledger: [ledger/runs/20261006T105123Z.json](ledger/runs/20261006T105123Z.json), at commit `10e7896` with a clean tree.
- **Result:** 62/62 entries pass. All 108 V2 measurements pass, and 113 of 113 rivals are rejected.
- **Stability against RL-075:** all 59 exact-count series are identical; the largest change in a timing α is 0.014.
- **CI:** GitHub Actions run 37452518800 on `10e7896` succeeded in validate, scaling and sources (`ubuntu-latest`, Python 3.12). The Kruskal counts differ across Python versions (RL-069), but the verdicts are the same under Python 3.12.

### RL-077 · DECISION · Contacting the authors of the published rank-47 collections (prepared; the owner sends)
Only the authors of the known collections can say whether the rank-47 class of RL-071 is new: Kauers and Moosbauer report more than 100 000 schemes, but have published 23 distinct ones. With the owner's approval, an e-mail to Manuel Kauers (JKU Linz) and Jakob Moosbauer (now University of Warwick) was drafted. Their addresses were taken from their own papers (arXiv:2212.01175; arXiv:2502.04514).
For it, `experiments/2026-10-06c_export_exp.py` exports two schemes in their `.exp` text format:
- the class representative, `search/schemes/rust-2026-10-06c/4x4x4_rank47_seed618.exp`;
- RL-054's scheme, `search/schemes/rust-2026-10-07/4x4x4_rank47_seed8.exp`, for checking the RL-070 certificate.
Both round-trip exactly through the audit's parser and pass both verifiers.
The class's factor-rank profile (sorted rank triple → number of terms) is 111:1, 112:3, 113:9, 123:12, 133:9, 222:6, 223:6, 333:1. RL-054's profile is 111:2, 112:4, 113:6, 122:5, 123:16, 133:4, 222:5, 223:1, 233:2, 333:2.
The e-mail claims no novelty. It asks whether the scheme is in their collection, and it apologises for the crawl load of RL-073. Any reply will be logged.

### RL-078 · DECISION · Disclosure of AI assistance
**Finding.** Until now the repository showed the AI's part only indirectly. Every commit carries a `Co-Authored-By: Claude …` line, and the reports in research/ name their author as a "delegated research agent (Claude)". The README, CITATION.cff, .zenodo.json and NOTICE did not mention it.
In this log, "the maintainer" (27 uses before this entry) always meant the AI assistant, but a reader would naturally take it to mean the owner. Examples are the errors attributed to the maintainer in RL-016, RL-052 and RL-073, which were the AI's.

**Decision (owner).** The AI's role is stated explicitly:
- **README:** a new section, "How this project is made".
- **This log:** a Roles section in the header defines owner, maintainer and agent. Earlier entries are not reworded.
- **CITATION.cff** (abstract) and **.zenodo.json** (description): one paragraph each. The Zenodo record of v0.2.0 keeps its old description; .zenodo.json takes effect at the next release.
- **CONTRIBUTING.md:** one sentence that used "the maintainer" in this sense was reworded.
- **START_HERE.txt:** a line in the decisions log.

**Unchanged.** Benjamin Weisz remains the only listed author. Authorship carries responsibility for the content, which the owner holds; this matches common policy, for example arXiv's, that AI tools are disclosed but not listed as authors.
**Rationale:** the project's value rests on transparency. An AI role that readers can only infer from commit metadata is not transparent, and errors must be attributable to whoever made them.

**The RL-077 e-mail** was sent by the owner on 2026-10-06, before this disclosure. It does not mention the AI assistance; the audit report it links to names its author as a delegated research agent (Claude). Any reply will be logged.

---

## 2026-10-06 (evening: fourth round, consolidated by the maintainer)

Four background agents. The owner proposed "morphing" the validated pairs (crossing, mirroring, changing operations, taking reciprocals) and asked for three things: rule mining over hundreds or thousands of generated candidates, a methodology survey, and a search in less-explored matrix formats. The detailed reports:
- [mutation_pilot](research/2026-10-06d_mutation_pilot.md)
- [rule_mining](research/2026-10-06d_rule_mining.md)
- [methodology](research/2026-10-06d_methodology.md), with the short guide [notes/discovery-methods.md](notes/discovery-methods.md)
- [exotic_formats](research/2026-10-06d_exotic_formats.md)

The maintainer re-ran the main experiments of every agent (RL-080 to RL-083). Every status, verdict and headline number reproduced exactly; only wall-clock fields differ. Numbers outside those re-runs are agent reports.

### RL-079 · DECISION · Mutations act on problems and implementations, not on cost formulas
A cost formula (n³, 2ⁿ) is a measured property of an algorithm, not the pair itself. Transforming the formula alone (its reciprocal, a mirror image, a mix of two formulas) gives an expression with no problem and no algorithm behind it, so nothing can be verified; START_HERE rejects such rewrites.
The owner's idea is therefore applied one level down:
- mirror, swap operations, cross and simplify the **problems and implementations**;
- use the slow side as the oracle, since it evaluates any objective or algebra;
- **measure** the cost change with exact counts instead of assuming it.

**Rationale:** every output stays checkable to the validator's standard. Formula-level structure remains useful as a map of gaps for literature search.

### RL-080 · VERIFIED (rediscoveries) and NEAR-MISS · Mutation pilot: where fast algorithms survive mirroring and operation swaps
**Engine:** `mutations/` (16 tests).
- Fast algorithms run as in-memory copies of the repository's implementations: either unchanged on substituted value types, or after targeted AST rewrites.
- The slow side, or a generic brute-force oracle, defines the mutated problem.
- Nothing under pairs/, staging/ or synthetic/ is modified; a test checks the source hashes.

**Outcomes:** 369 mutants and 233 532 differential tests. Every kill comes with a shrunk minimal counterexample.

| Family | Mutants | Survived | Killed | Invalid | Trivial | Inconclusive |
|---|---|---|---|---|---|---|
| MIRROR | 27 | 0 | 7 | 1 | 19 | 0 |
| OPSWAP | 342 | 176 | 77 | 68 | 20 | 1 |

**Boundary map.** It is exact on the 6–13 structures tested per algorithm, but a correlation, not a proof.

| Fast algorithm | Survives exactly where |
|---|---|
| Strassen, polynomial Karatsuba, Ryser, Kirchhoff/Bareiss | an additive inverse exists |
| FWHT | an additive inverse exists and 1+1 ≠ 0 |
| NTT | a primitive root of the transform size exists |
| Dijkstra; Floyd–Warshall and Bellman–Ford on cyclic digraphs | 1 ⊕ a = 1 |
| Floyd–Warshall and Bellman–Ford on DAGs; sparse table | ⊕ is idempotent |
| square-and-multiply | power-associativity (octonions survive 1000 tests) |

**Strassen rescued by input transformations** (known results, rediscovered): integer Strassen on embedded inputs gives
- the Boolean product;
- the (min,+) product, via Yuval's encoding;
- the (max,min) product, via thresholds.

The last two are pseudo-polynomial in the weights.

**Cost:** 30 survivors were measured by exact counts.
- In 29, the claimed cost is the only one that fits, and 215 rivals are rejected.
- The exception is Boolean Floyd–Warshall (α = 1.0372 against n³), a counting gap: operations on plain literals are not counted while the edge density varies (INCONCLUSIVE).

**NEAR-MISS:**
- **Knuth's optimal-BST speed-up under (max,+)** agrees on 0.8662 of 800 tests. Smallest counterexample: p = (0,0,0), q = (0,0,0,1), where the recursion gives 3 and Knuth gives 2.
  - No literature statement was found, but only the bibliographic records of Knuth 1971 and Yao 1980 were checked, not the papers.
  - The maintainer's expectation, not checked: the speed-up's quadrangle-inequality condition is stated for minimisation, and maximisation reverses it.
- **Stoer–Wagner as a max-cut algorithm** is killed, with ratio ≥ 0.708.

**Limit:** Kruskal is INVALID everywhere because the repository implementation packs weights into integer sort keys. This is a property of our implementation, not of Kruskal's algorithm.

**MIRROR:** all 19 survivors are known trivial reparametrisations. The 7 kills (longest path, farthest pair, max cut) are expected.

**Maintainer re-run:** `experiments/2026-10-06d_mut_pilot.py --trials-scale 5`, then `python -m mutations props` and `experiments/2026-10-06d_mut_boundary_map.py`. All 446 records are identical except the `elapsed_s` field.

**Data:** records in `mutations/records/2026-10-06d/` (660 KB). Literature: 32 identifiers [DOI OK]. The agent corrected one wrong DOI: Duan–Pettie 2009 is …068.43, not .42.

### RL-081 · VERIFIED, NULL and REFUTED · Rule mining: 1920 generated candidates, nothing beyond textbook rules
**Package:** `generators/rules/` (22 tests). Seven rules as executable templates, each with a family generator and a common screen:
- memoisation (with state compression);
- transform convolution;
- repeated squaring;
- matroid greedy;
- Knuth–Yao monotone splits;
- GF(2) bilinear rank;
- meet in the middle.

**Screen:** 1920 candidates gave 1161 EXACT, 380 NEAR-MISS, 310 WRONG and 69 INVALID, with 1138 distinct after canonical deduplication.
- **Exponent fits:** for 1089 of the 1106 EXACT candidates with a fit, the exact-count fit resolves the exponent change.
- **The 17 unresolved** are memoisation fits: 16 do not reach the asymptote at small n, and 1 is a harness artefact (a rival identical to the claim, not fixed).
- **Count check:** instrumented counts and spec-derived counts agree wherever both exist.

**NULL:** no candidate beats a known algorithm. The bilinear rule rediscovered Karatsuba (GF(2) rank 3) and GF(4) multiplication; the convolution rule rediscovered FWHT, NTT and Yates. All output is T7 at most.

**Preconditions:** a stated precondition implied EXACT in every rule (precision 1.000). They are often not necessary, though: 97 magma, 43 Knuth, 9 meet-in-the-middle, 5 greedy and 4 compression candidates were EXACT without them.

**IDEA** (supported on fresh seeds and held-out families; not theorems):
- **Binary powering** is exact iff p_a·p_a = p_2a for every left power, which is weaker than power-associativity. 900/900 magmas agree, and 37 exact ones are not power-associative. Likely folklore; the literature was not checked.
- **A compressed memo key** is exact iff the dropped coordinate is a function of the kept one on the reachable states (400/400).
- **Concave length weights** made Knuth's speed-up exact on 600/600 instances, although the quadrangle inequality failed on all of them. Open. A possible explanation, not checked: with length-only weights the value depends only on the interval length.

**REFUTED:**
- Knuth's speed-up under the quadrangle inequality alone (728 of 1161 instances not exact);
- translation-invariant weights (157/600 exact).

**VERIFIED (pipeline check):** the greedy algorithm's adversarial ratio equals the Korte–Hausmann rank quotient within 0.0005 on 400/400 set systems.

**Repairs** that make whole near-miss clusters exact:
- transform plus sparse correction (300/300);
- all-solutions lookup for meet in the middle (141/141);
- boundary conditioning for cross-split interactions (92/92);
- cycle detection for magmas (900/900).

Bilinear repairs never gained (0/127).

**Nearness metric:** use the adversarial ratio or a structural distance, not sampled ratios. For greedy, sampling reached the rank quotient on only 72 of 147 non-matroids.

**Maintainer re-run:** `experiments/2026-10-06d_rules_mass_screen.py`, `…_hypotheses.py` and `…_analysis.py`. All 1920 verdicts are identical; only the `seconds` fields differ.

**Data:** store `candidates/2026-10-06d/` (1.7 MB). The promotion list has 15 items. The only staging-level one is the maximum-weight basis of a binary matroid, which has low novelty next to the MST entry.

### RL-082 · VERIFIED and INCONCLUSIVE · Methodology: exact formula recognition, log-factor identifiability, polynomial-method certificates, a tractability predictor
**Output:** package `methods/` (20 tests); a survey of four areas with 117 checked identifiers; the guide `notes/discovery-methods.md`. Of the identifiers, 114 are OK, 1 is OK without a year, and 2 Theory of Computing DOIs have empty Crossref titles while their arXiv versions match.

**Formula recognition:**
- For 12 of 12 slow-algorithm count sequences in the dataset, a guessed exact recurrence gives the growth constant λ with its minimal polynomial and the polynomial exponent θ. All match the entries' claims. Example: plain-recursion edit distance gives λ = 3+2√2 (x²−6x+1) and θ = −1/2.
- An independent route (ratio method plus LLL) agrees 12/12.
- Cofactor determinant is flagged as factorial-type.
- The MST enumeration count gives no recurrence of order ≤ 4 and degree ≤ 4 from 39 terms. NULL; this is not evidence of non-holonomicity.

**Log factors (sharpens RL-048):**
- On the grids of ledger run 20261006T105123Z, with perfect noise-free data, 0 of 44 timing fits could resolve a log factor at tolerance ±0.25. The largest tolerance that would resolve one is 0.1015. The cause is the tolerance on the given span of n, not noise.
- Counts at n = 2^k give the exponent and the log power exactly through Berlekamp–Massey: NTT (x−2)² → n log n; Karatsuba x−3; Strassen x−7; Yates (x−2)² → N log N.
- Monte Carlo (truth n log n, 8 points on [10³, 10⁵]): the correct model is chosen 81.0% of the time at σ = 0.03 and 57.8% at σ = 0.1. The usual confusion is with n^1.1.

**Polynomial method:**
- Exact adeg₁/₃(ORₙ) for 70 values of n ≤ 256, each with a primal and a dual certificate. Fit 0.7246·√n, log-log slope 0.4748 for n ≥ 16: the Ω(√N) bound behind Grover's optimality.
- Parity has adeg = n for n ≤ 16.
- Majority has slope 0.8738 on odd n ≤ 41 against the theorem's linear growth: INCONCLUSIVE as an asymptotic statement on this range.
- On all 222 NPN classes of 4-bit functions, deg ≤ s² (Huang 2019), s ≤ bs ≤ C ≤ D and deg ≤ D hold.

**Schaefer predictor:**
- Polymorphism and syntactic classifications agree on all 276 relations of arity ≤ 3.
- The predicted polynomial algorithm agrees with brute force on 900/900 instances, with valid witnesses; affine counting 2^(n−rank) agrees on 150/150.
- Negative control: Horn propagation on NAE-3-SAT gives an invalid witness on 200/200.

**Not done:** exact quantum query complexity by SDP (no solver in the standard library), and the matroid and TU demos.

**Maintainer re-run:** the four experiments and the tests reproduced every number above.

**The agent's own errors,** all fixed before the final runs and listed in the report:
- a wrong λ comparison;
- an LLL acceptance test that accepted 34x−55 for φ and at first used the true error;
- a negative control that could not fail;
- too few terms for global min cut;
- an inconclusive dominance test.

### RL-083 · VERIFIED (calibration), NULL and CORRECTED · Less-explored matrix formats: records table, block starts, no scheme below a record
**Motivation:** an outside suggestion that larger or "exotic" formats may still hide lower ranks. The maintainer's assessment before the run:
- possible in less-searched rectangular formats;
- unlikely in 5×5 and 6×6, where expert groups search with large compute;
- our kernel did not yet reach the record for (4,4,5) (RL-059: best 64 against 60).

**Records table** for all 35 formats 2 ≤ n ≤ m ≤ p ≤ 6:
- 372 published scheme files all verify over GF(2): Kauers–Moosbauer flips @e31a0a0f (37), Kauers' meta-flip-graph repository @12c26b29 (309), Arai–Ichikawa–Hukushima (2), Moosbauer–Poole (4), AlphaTensor (20).
- **GF(2) vs general rings:** GF(2) is ahead in (4,4,4) 47/48, (4,4,5) 60/61 and (4,5,5) 73/76, and behind in (2,4,5) 33/32, (3,3,6) 42/40 and (3,6,6) 82/80.
- The Q records 32 and 40 verify over Q but have denominators 2 and 8, so they do not reduce to GF(2) as they stand. An equivalent 2-integral scheme is not excluded.
- Source oddity: KM's `366-85-mod2.exp` holds 86 terms.
- The Linz server was not contacted.

**Targets:** (3,3,6) → ≤ 41, (2,4,5) → 32, (2,5,6) → ≤ 46, (4,4,5) → ≤ 59.
- Ranks 41, 46 and 59 would give exponents 2.7929, 2.8053 and 2.7915: below log₂7 = 2.80735, but none below log₄47 = 2.7773.
- (2,4,5) at 32 (2.8185) would be a format record only.

**Block starts** (`search/blocks.py`: direct sums of verified smaller schemes) close the (4,4,5) gap:
- 6/24 walks reach the record 60, starting from (4,4,1)+(4,4,4) = 63, against 0/8 before.
- The six rank-60 schemes are pairwise inequivalent, and inequivalent to KM's published file, by the factor-rank profile. They are rediscoveries of the best known rank.
- For (3,4,5), block starts reach 48 in 23/24 walks against 12/24 from the standard start (Fisher p = 0.0007), but 47 in 0/24. The standard start reached 47 in 1/8, an exact reproduction of RL-059's seeds 1–8.

**Kernel option `--full-reduce`** (default off): removes a term when the terms sharing one of its factors have linearly dependent factors in a second position.
- **VERIFIED (exactness):** mirrored in `kernel_reference.py`, with differential and planted-dependency tests. `--full-reduce 0` is identical to the pre-round kernel in 14/14 step-limited cases.
- **NULL (benefit):** no gain, at 0.46–0.81 of the plain kernel's speed.
- The agent's first version allocated memory on every scan (0.33–0.46 of the speed). The fix gives identical trajectories, and the affected arms were re-run.
- Kernel SHA-256: 69837abe… → 6933efaf….

**NULL:** 160 walks, 3.89·10¹¹ steps and 24 000 walk-seconds (about 106 min of wall clock, at most 4 processes) found nothing below a best known GF(2) rank.

**NEAR-MISS:**
- (3,3,6): 9 pairwise inequivalent schemes at 43.
- (4,4,5): walks from the published and from our own rank-60 schemes found no 59.

**Obstacle:** (2,5,6) under the default plateau and slack never improves from 60 or 50. With plateau 2000 and slack 1 the walks descend at once, but the best within 300 s was 51.

**Maintainer checks:** see RL-084.

**CORRECTED (maintainer):** three exponents in the agent's report were written by hand and were off (formula 3·ln r / ln(nmp)):
- (2,5,6) at 46 is 2.8053, not 2.8020;
- (4,4,5) at 59 is 2.7915, not 2.7917;
- (2,4,5) at 32 is 2.8185, not 2.8186.

They are corrected in the report with a note. No conclusion changes, since 2.8053 is still below log₂7.

### RL-084 · VERIFIED · Recorded run and maintainer checks after the fourth round
Ledger: [ledger/runs/20261006T143136Z.json](ledger/runs/20261006T143136Z.json). Base commit `e575dd0`, with this round's work uncommitted; the run was made on a quiet machine after all agents had finished.
- **Result:** 62/62 entries pass. V1 covered 51 entries, 3447 instances and 7323 implementation runs.
- **V2:** 108 measurements, all passing (59 exact counts, 49 wall-clock); 113 of 113 rivals rejected; log factor resolved in 47 fits.
- **Stability against RL-076:** all 59 exact-count series are identical; the largest change in a timing α is 0.0164.
- **Unit tests:** 178 OK (110 before this round). **Citations:** 173 identifiers, 0 problems.
- **Kernel identity:** `experiments/2026-10-06d_fmt_identity.py` — with `--full-reduce 0`, the changed kernel is identical to the pre-round kernel in 14/14 step-limited cases.
- **Schemes:** all 141 schemes saved in `search/schemes/rust-2026-10-06d/` were re-verified by a separate script (verify, verify_explicit, 50 random checks, rank equal to the file name): 141 pass, none is below a best known rank.
- **Equivalence:** `experiments/2026-10-06d_fmt_analysis.py` confirms 7 distinct factor-rank profiles among the six rank-60 (4,4,5) schemes and KM's published one.
- **Agents' experiments:** re-run as stated in RL-080 to RL-082, all reproduced.

### RL-085 · IDEA · Next steps from the fourth round
1. **Exact shape diagnostic** for exact-count V2 (methodology recommendation 1; the code is in `methods/recurrences.py`). Start it as informational output; making it part of V2 needs a DECISION.
2. **Entry candidates:** known, named problems, each needing the usual V1/V2 and verified citations.
   - From the mutation pilot: Boolean matrix multiplication and transitive closure, bottleneck paths, counting Hamiltonian cycles, weighted spanning-tree sums.
   - From the methodology survey: Horn-SAT, XOR-SAT, #XOR-SAT.
   - From rule mining: OR/AND convolution, as an extension of the zeta entry.
   - From the outside suggestion: bit-parallel algorithms in the word-RAM (log-factor gaps), and restricted graph classes with proven bounds (planar separators, bounded treewidth).
   - Bit tricks for a fixed word size are constant factors and stay out of scope (START_HERE).
3. **Search:**
   - an exact SAT attack on (2,4,5) at rank 32 over GF(2);
   - a pool of rank-48 (3,4,5) schemes;
   - block starts from all four rank-47 4×4×4 classes;
   - equivalence testing for non-square formats;
   - format-dependent plateau and slack.
4. **Open checks:**
   - the (max,+) Knuth near-miss and the concave-weights observation against the literature;
   - exact quantum query complexity by SDP, in a separate venv.
