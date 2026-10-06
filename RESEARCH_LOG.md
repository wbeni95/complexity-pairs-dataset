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
