# Deviation and anomaly analysis of the recorded evidence (2026-10-07b)

**Scope.** All five ledger files in `ledger/runs/` (20261006T005329Z, 005747Z, 025704Z, 030338Z, 070542Z): 90
(entry, algorithm) series with V2 measurements, 74 of them timing fits and 16 reported counts in the latest run. Also
`index.json`, every `entry.json`, `tools/validate.py` and the numeric claims of `RESEARCH_LOG.md` RL-001..RL-054.
Nothing in the entries, tools or log was modified. Every number below comes from a ledger file (cited by its stamp)
or from a script in `experiments/2026-10-07b_*.py`; each script's docstring says what it computes.

**Snapshot caveat.** Another agent was editing the working tree while this analysis ran. Between 10:01 and 10:07
local time, 5 entries were changed (sorting, element distinctness, matching, inversion counting, LIS) and 5 were
added (XOR convolution, zeta transform, global min cut, optimal BST, regex matching). None of these changes is in
any ledger run. The findings below concern the **recorded evidence**, which predates all of them. The newest ledger
file was written at 09:07 local. Where a finding is probably being addressed by that in-progress work, the table
says so.

**Provenance.** Ledger: the five files above. Experiment scripts:
- `2026-10-07b_ledger_stability.py`: stability and local slopes
- `2026-10-07b_theory_vs_ledger.py`: closed forms
- `2026-10-07b_cross_fits.py`: post-hoc rivals and passing bands
- `2026-10-07b_instance_audit.py`: which instances are timed
- `2026-10-07b_consistency.py`: index, ledger and tag checks
- `2026-10-07b_log_claims_check.py`: RESEARCH_LOG numbers against the ledger
- `2026-10-07b_patterns.py`: α by cost class
- `2026-10-07b_lower_order_fits.py`: two-term fits
- `2026-10-07b_rival_margin_precheck.py`: noise-free rival margins
- `2026-10-07b_kadane_instance_type_timing.py`: the only re-measurement, about 1–3 s per run, under CPU contention

---

## Prioritised findings

Severity levels:
- **high:** the recorded evidence does not support the separation that the V2 claim implies.
- **medium:** the claim passes, but its evidence is fragile, misdescribed or hides structure.
- **low:** provenance or bookkeeping.

| # | Finding | Evidence | Severity | Note |
|---|---|---|---|---|
| F1 | **Matching: the recorded timing V2 does not separate Kuhn from Hopcroft–Karp.** HK's times also fit Kuhn's n³, and Kuhn's times also fit HK's n^2.5. No rivals were declared. | Cross-fit, ledger 025704Z / 030338Z / 070542Z: HK data vs n³ gives α = 0.818 / 0.817 / 0.819; Kuhn data vs n^2.5 gives 1.172 / 1.169 / 1.170. All are inside 1 ± 0.25. In the recorded evidence, the exact counts come only from an agent experiment (RL-030). | high | The working tree now has `measure: reported`, tolerance 0.03 and rivals (10:03), but no recorded run yet. |
| F2 | **Karatsuba: the measurements also fit schoolbook n².** The schoolbook data reject Karatsuba's n^log₂3 only by a hair. | Cross-fit over 5 runs: Karatsuba data vs n² gives α = 0.810 / 0.810 / 0.809 / 0.811 / 0.806, which passes. Schoolbook data vs n^1.585 gives 1.267 / 1.263 / 1.271 / 1.272 / 1.273, a margin of only 0.013–0.023. | high | — |
| F3 | **Collision, BBHT variant: neither the measurements nor the exact expectations over n = 3..15 exclude the classical 2^(n/2).** In the V2 range the T9 separation rests on the known-t variant alone, which rejects 2^(n/2) with margin 0.069. | Recorded BBHT means vs 2^(n/2): α = 0.776 in all 3 runs, which passes. The exact expectations against 2^(n/2) give 0.7696 (`theory_vs_ledger.py`), which also passes. Known-t: recorded 0.681, exact 0.6844, both rejected. | high (for any reading of this fit as separation evidence) | 2^(n/2) as a rival of this fit would fail. Exact slope over n = 15..30 is 1.009 (RL-032). |
| F4 | **Chromatic number, inclusion–exclusion: the claimed cost n·2ⁿ is not the operation count on the timing instances, and the fit cannot tell n·2ⁿ from 2ⁿ.** | χ(G) of the 9 exact timing graphs (G(n, 0.8), n = 10..18) is 6, 7, 7, 8, 8, 8, 8, 9, 10 (χ/n = 0.50–0.64). Fitting the exact operation-count model (2χ+2)·2ⁿ against n·2ⁿ gives α = 0.9638. Plain 2ⁿ against n·2ⁿ gives 0.9047, which also passes. Recorded α = 0.984. | medium | — |
| F5 | **Simon, quantum: the recorded α = 1.121 is a 1.8-s.e. draw dominated by the n = 2 point.** The exact-E(n) slope is 1.0186. | Mean at n = 2 is 1.65 vs E = 2 (z = −1.57, exact variance). Delta-method s.e.(α) = 0.0569 at 40 samples, and n = 2 contributes 83% of Var(α). (recorded − exact)/s.e. = +1.80. Without n = 2: recorded 0.960, exact 0.957. | medium | The cost span is only 5×. |
| F6 | **Run-to-run stability measures timing noise only.** Every run times the same seeded single instance per n (samples = 1 for all 74 timing fits), so instance effects are frozen in and look perfectly stable. | Validator: `random.Random(f"{id}|v2|{n}")` with samples defaulting to 1. Max timing-α spread over the 5 runs is 0.044 (section 1), yet max-subarray and LCS show reproducible local-slope jumps (F7, F16). | medium | — |
| F7 | **Maximum subarray: the timing instances change type between n values.** The harness has no `generate_scaling`, and its generator mixes all-negative, all-non-negative and mixed arrays. | Instance audit: Kadane's n = 100 000 instance is all-negative and its n = 10⁶ instance all-non-negative; brute force has all-negative at n = 150 and all-non-negative at 200. Re-measurement (two interpretable runs, under contention): per-element time is ×0.63–0.94 (all-negative) and ×0.75–0.96 (all-non-negative) of mixed, all 24 round-ratios below 1. The predicted local slopes 0.697 / 1.332 / 0.894 have the same direction and similar size as the recorded 0.778 / 1.235 / 0.895 (070542Z), overshooting the first two. | medium | — |
| F8 | **The only discriminating (rival-based) V2 evidence comes from a dirty tree.** Strassen counts appear in one run only (070542Z, `git_dirty` true, base 83b12c3 plus the uncommitted RL-047 changes). | Ledger run metadata: 2 of 5 runs are on a clean commit (005747Z at d8ddc58, 030338Z at 7511ea9). 005329Z has git_commit null; 025704Z and 070542Z are dirty. | medium | — |
| F9 | **Every timing fit with claimed exponent ≥ 2.5 has α < 1 and a rising local slope.** One lower-order term n^(p−1) explains it. Floyd–Warshall (α = 0.925, the lowest timing α) would need n > 703 for its local slope to exceed 0.99; the largest measured n is 200. | 10/10 fits in 070542Z (α 0.925–0.982) and 40/40 run-fits across the ledger. The two-term fit T = a·n^p + b·n^(p−1) reproduces the recorded α to within ±0.001 (3-decimal values) in 8 of 9 n^p fits (max-subarray brute: 0.966 vs 0.974). It cuts the relative RMS residual 4.68–21.80× (1.39× for max-subarray brute, whose residual is the instance mix). b/a = 6.85–21.76. | medium (systematic, explained) | — |
| F10 | **The five log n fits have α > 1, a slope falling from 1.02–1.27 to 0.92–1.04, and only a 16× cost span.** These are fast doubling and four companion-matrix powers. | 070542Z: α 1.001–1.087. Fast doubling local slopes are 1.265, 1.080, 1.060, 0.963, and the spread over 5 runs is 0.040 (1.087–1.128), the second largest of all. Hypothesis, untested: the first few doubling steps work on small integers (F(k) < 2³⁰ for k ≤ 44), which CPython handles cheaply. Their number is roughly fixed, while the total number of steps grows with log n, so the average cost per step rises with n until it saturates. linear-recurrence-c2-3 (α 1.001) does not show the pattern, which the hypothesis has not explained. | medium | — |
| F11 | **Dürr–Høyer uses more queries than the classical scan at 4 of the 5 measured n.** | 070542Z: quantum/classical ratio is 17.15, 7.43, 3.38, 1.64 and 0.77 at n = 4, 6, 8, 10, 12. α = 0.886 (margin 0.136). | low | Already in RL-034. |
| F12 | **Grover's α = 0.924 is deterministic and pre-asymptotic, not noise.** | The closed form ⌊(π/4)·2^(n/2)⌋ + 1 has slope 0.9245 over n = 2..12, matching the record exactly, and 0.9996 over n = 14..40. | low | — |
| F13 | **The working tree is ahead of both the index and the ledger.** | At 10:03: 56 entries on disk vs 54 in `index.json` (written 09:03); more were added by 10:07. At 10:03, 3 entries' current `scaling` (measure, tolerance, rivals; sorting also n_values) differed from 070542Z and 2 new entries had no record; by 10:05–10:06 inversion counting and LIS had changed too. | low (transient) | — |
| F14 | **The T3 secondary tag is applied inconsistently.** LIS carries it for its n² → n log n step; Fibonacci (n → log n) and MST (n² log n → n²) have a poly → faster-poly step without it. | `2026-10-07b_consistency.py` §4. | low | — |
| F15 | **Dates disagree.** RESEARCH_LOG sections "2026-10-07 (overnight)" and "(day)" cite ledger files stamped 2026-10-06, and the files themselves have 2026-10-06 mtimes. | For example, RL-044 under "2026-10-07" cites 20261006T025704Z (UTC). `experiments/2026-10-07_dataset_stats.py` has mtime 2026-10-06 03:43 +0200. The shell clock read 2026-10-06 during this analysis. | low | — |
| F16 | **LCS subsequence enumeration: local slopes oscillate reproducibly** between 0.825 and 1.403. The brute force exits early, so per-mask cost depends on the instance (hypothesis, untested). | 070542Z local slopes: 0.897, 1.123, 0.842, 0.994, 0.825, 1.403. Last-minus-first drift is +0.48 / +0.48 / +0.50 / +0.51 / +0.51 over 5 runs. The implementation breaks when `b.find` fails, so time per mask lies between Θ(1) and Θ(n + m). | low | — |

---

## 1. Stability across recorded runs

Script: `2026-10-07b_ledger_stability.py`. Each series' spread is computed within an identical configuration (same
measure, cost, n_values, samples and tolerance). **No series changed configuration across the 5 runs** (0 of 90).

**Timing fits (74).**
- Only 3 fits have a spread above 0.02:
  - inversion counting, merge-sort counting: 0.044 (1.028, 1.004, 0.991, 0.988, 0.984);
  - Fibonacci fast doubling: 0.040 (1.100, 1.128, 1.095, 1.101, 1.087);
  - inversion counting, all pairs: 0.031 (1.043, 1.015, 1.013, 1.011, 1.018).
- The next largest are Gaussian elimination at 0.017 and matrix-chain plain recursion at 0.016. Every other timing
  fit stays at or below 0.016.
- The merge-sort-counting series moves *monotonically* down over the five runs, though five values are too few to
  call that a trend.

**Closest to the tolerance edge** (smallest margin = tol − |α − 1| over all runs):

| Series | Measure | Margin | α (runs) |
|---|---|---|---|
| collision, BHT with BBHT exponential search | counts | **0.086** | 1.164 ×3 |
| Fibonacci fast doubling | time | 0.122 | 1.087–1.128 |
| Simon, quantum | counts | 0.129 | 1.121 ×5 |
| Dürr–Høyer | counts | 0.136 | 0.886 ×3 |
| linear-recurrence-c1-1-1-1, companion matrix (T7) | time | 0.162 | 1.079–1.088 |
| Floyd–Warshall | time | 0.173 | 0.923–0.925 |
| Grover, quantum | counts | 0.174 | 0.924 ×5 |
| linear-recurrence-c1-0-1, companion matrix (T7) | time | 0.176 | 1.066–1.074 |
| knapsack capacity DP | time | 0.186 | 1.055–1.064 |
| linear-recurrence-c1-1-1, companion matrix (T7) | time | 0.191 | 1.049–1.059 |
| 3SUM all triples | time | 0.196 | 0.946–0.951 |
| GCD trial divisors | time | 0.198 | 1.044–1.052 |

Strassen and schoolbook counts sit at α = 1.000 exactly, with tolerance 0.02 and margin 0.020.

**Reported counts** were identical value for value in every pair of consecutive runs: 6/6, 6/6, 14/14 and 14/14
(`2026-10-07b_log_claims_check.py`).

**The log's stability claims hold** (same script):
- RL-022: largest change 0.0277 (fast doubling 1.1001 → 1.1278).
- RL-044: 0.0329 (fast doubling 1.1278 → 1.0949).
- RL-045: 0.0149 (matrix-chain plain recursion 1.0051 → 0.9902).
- 030338Z → 070542Z: 0.0139 (the same series).

**Limitation, which is F6.** These spreads say nothing about instance variability, because every run times the same
instance at each n.

## 2. Curvature: local slopes

Script: `2026-10-07b_ledger_stability.py`. The local slope between consecutive n is
s_i = Δln y / Δln cost. The script also reports α over the first and the second half of the n values. The drift
column of the script is checked for sign consistency across all runs, which tells real curvature from noise.

**Largest second-half minus first-half α** (latest run). For each listed series, the last-minus-first local-slope
drift has the same sign in every run that recorded it; count series are identical across runs anyway.

| Series | α | α first half → second half | Local slopes | Reading |
|---|---|---|---|---|
| Simon, quantum (counts) | 1.121 | 1.478 → 0.888 | 1.801, 0.968, 1.032, 0.868, 0.915 | one low point at n = 2 (F5) |
| collision BBHT (counts) | 1.164 | 1.265 → 1.059 | 1.122, 1.408, 0.936, 1.182 | pre-asymptotic (exact slope 1.154 over these n) plus sampling noise |
| max-subarray brute force | 0.974 | 0.929 → 1.093 | 0.922, 0.942, 0.884, 1.118, 1.055 | instance-type switches at n = 150 and 200 (F7) |
| Fibonacci fast doubling | 1.087 | 1.172 → 1.011 | 1.265, 1.080, 1.060, 0.963 | falling slope; drift −0.29 / −0.52 / −0.30 / −0.34 / −0.30 over 5 runs (F10) |
| companion matrix c1-1-1 (T7) | 1.050 | 1.124 → 0.972 | 1.161, 1.088, 1.022, 0.922 | same pattern |
| inversion counting, all pairs | 1.018 | 1.099 → 0.948 | 1.157, 0.980, 0.965, 0.948, 0.948 | high first step (n = 250 → 500) in all 5 runs |
| knapsack meet in the middle | 0.988 | 0.942 → 1.063 | 0.909, 0.976, 0.965, 0.979, **1.149** | last step (n = 32 → 36) is +0.23 / +0.23 / +0.23 / +0.24 / +0.24 above the first in all 5 runs; plausibly the 2¹⁸-element lists leaving cache (untested) |
| Wagner–Fischer DP | 1.046 | 1.007 → 1.106 | 0.993, 1.035, 1.042, 1.101, 1.115 | rising above 1; the same holds for LCS DP (0.967 → 1.055) |
| Dürr–Høyer (counts) | 0.886 | 0.829 → 0.933 | 0.794, 0.864, 0.954, 0.911 | lower-order lg² N term in the time-out |
| LCS subsequence enumeration | 0.987 | 0.971 → 1.048 | 0.897, 1.123, 0.842, 0.994, 0.825, 1.403 | reproducible oscillation (F16) |

**Floyd–Warshall** (the user's example; its α of 0.923–0.925 is the lowest timing α in every run):
- Local slopes 0.894, 0.931, 0.913, 0.939, 0.941, 0.965, rising throughout.
- `2026-10-07b_lower_order_fits.py` fits T = a·n³ + b·n² with b/a = 21.76. The relative RMS residual falls from
  0.136 (one term) to 0.012, and the model reproduces α = 0.926.
- The model's local slope exceeds 0.99 only for n > 703, while n_values stop at 200. So the low α is a pre-asymptotic
  n² term: per-(k, i) overhead worth about 22 inner iterations. It is not a measurement error.

**Maximum subarray, Kadane** (local slopes 0.994, 1.004, **0.778, 1.235**, 0.895):
- `2026-10-07b_instance_audit.py` shows that the n = 100 000 instance is all-negative (Kadane's reset branch fires on
  100% of elements) and the n = 10⁶ instance is all-non-negative (`best` updated on 99.0% of elements). The others
  have mixed signs.
- The re-measurement, `2026-10-07b_kadane_instance_type_timing.py` (n = 100 000, under CPU contention from the other
  agent's flipwalk jobs), was run three times:
  - Run 1: ratios to mixed of 0.774 / 0.734 / 0.763 (all-negative) and 0.869 / 0.891 / 0.893 (all-non-negative).
  - Run 2: the rounds disagreed, so it is not interpreted.
  - Run 3: 9-round medians 0.694 (range 0.631–0.942) and 0.881 (range 0.754–0.955), with predicted local slopes
    0.697 / 1.332 / 0.894 against the recorded 0.778 / 1.235 / 0.895. The predictions have the right direction and
    similar size, overshooting the first two.
- The direction is confirmed, and the magnitude is noisy. This is consistent with the instance-mix explanation but
  does not prove it.
- Running sums shows the same switch: n = 200 is all-non-negative, with local slopes 0.866 into it and 1.178 out of it.

**Checked, nothing anomalous:** 60 of the 74 timing fits have |second-half α − first-half α| ≤ 0.05.

## 3. Theory vs measurement

Script: `2026-10-07b_theory_vs_ledger.py`. Every reported-count series in every run (values are identical across
runs) is compared with an exact value or an exact expectation.

**Deterministic counts: all match exactly, 0 mismatches.**
- Bernstein–Vazirani: classical n (n = 2, 4, 8, 12, 16) and quantum 1 (n = 1..10).
- Deutsch–Jozsa: classical deterministic 2ⁿ⁻¹ + 1 at all 8 n (3 … 32 769), randomized 20 and quantum 1.
- Minimum finding, classical: N.
- **Grover, quantum:** 2, 4, 7, 13, 26, 51 = ⌊(π/4)·2^(n/2)⌋ + 1, as RL-013 states.
- **Strassen:** 28 672, 200 704, 1 404 928 and 9 834 496 = 7^log₂(n/16)·16³ at n = 32..256. Schoolbook gives n³
  exactly (RL-047 confirmed).

**Randomized means against exact expectations.** z uses the exact variance where it is available.

| Series | Max \|z\| (at n) | Notes |
|---|---|---|
| Simon, quantum, E(n) = Σ 1/(1−2⁻ʲ) | 1.57 (n = 2: 1.65 vs 2.0000) | other z: +0.37, +0.19, +1.15, +0.86, +0.84 |
| Simon, classical (birthday on a 2-to-1 function) | 0.67 | all within 0.7 |
| collision, classical birthday | 1.52 (n = 4: 4.83 vs 5.0922) | |
| Grover, classical, E = (N+1)/2, Var = (N²−1)/12 | 1.51 (n = 6: 28.1 vs 32.5) | |
| collision, BHT known t | about 1.69 (n = 12) | variance taken from the agent's run-2 table (agent report) |
| collision, BHT exponential | about 1.86 (n = 12: 51.84 vs 56.7587) | same source |

None exceeds 2 in absolute value; the means are consistent with theory.

**Fitted α against the α of the exact predictions:**
- Simon quantum: 1.1210 vs 1.0186 (+1.80 s.e., see F5).
- Grover classical: 0.9924 vs 0.9793 (+1.14 s.e., s.e. 0.0115).
- Simon classical: 0.9927 vs 0.9971 (−0.23 s.e.).
- Collision classical: 1.0032 vs 0.9971 (+0.49 s.e.).
- BHT known t: 1.0209 vs 1.0266.
- BBHT: 1.1640 vs 1.1544.
- Grover quantum: 0.9245 vs 0.9245 (deterministic).

**Pre-asymptotic exact slopes:**
- Simon E(n) against n: 1.0132 over n = 2..10, 0.9549 over n = 3..10, 0.9733 over n = 2..30, 0.9662 over n = 10..30.
  So the true α depends on the range by several hundredths even with no noise at all.
- Grover's closed form: 0.9245 over n = 2..12 and 0.9996 over n = 14..40.

**Self-caught error in this analysis** (also in the decision log). The first version of the script matched algorithm
names by substring. The BBHT variant's name contains "unknown", which contains "known", so it was silently compared
with the known-t expectations, which made the BBHT means look 29–43% too high. A comparison with the agent's table in
`research/2026-10-07_quantum_entries.md` (exact 5.0092 … 120.1352) exposed it, and it was fixed before any number was
used. The corrected relative deviations are −6.4%, −6.6%, +6.0%, −8.7% and −2.1%.

## 4. Consistency checks

**4a. index.json vs disk** (`2026-10-07b_consistency.py`, run at about 10:03 local):
- The disk then held 56 entries and the index 54. The difference is the two new entries
  `global-min-cut-brute-vs-stoer-wagner` (T2) and `xor-convolution-naive-vs-walsh-hadamard` (T3). On disk that gives
  41 validated pairs vs 39 in the index, V2 41 vs 39, T2 12 vs 11 and T3 17 vs 16.
- More entries were added by 10:07.
- For the 54 indexed entries, every row (level, pair_type, secondary_tags, path, algorithm names, time_complexity
  text, implemented flag) matches its `entry.json`: **0 mismatches**.
- With the two new entries excluded, the counts match the disk: 39 validated pairs; 12 entries with T6, 11 of them
  primary; 9 entries with T9, 8 of them primary; 4 synthetic; 12 entries with a quantum algorithm; levels V0 11, V1 4,
  V2 39.

**4b. Latest ledger vs current entries.**
- `bipartite-matching`, `element-distinctness` and `sorting-insertion-vs-merge` now declare `measure: reported`,
  tolerance 0.03 and rivals. So do `inversion-counting` and LIS, which changed after this check ran and were inspected
  at about 10:05–10:10. The ledger has only timing for all five.
- The new entries have no ledger record.
- Each V2 claim in that state rests on no recorded evidence until the next `--record` run.

**4c. Numeric claims in RESEARCH_LOG vs the ledger** (`2026-10-07b_log_claims_check.py`): every claim checked holds.
- RL-021: 55 V2 measurements, α 0.924..1.121, V1 on 28 entries with 1830 instances and 3714 runs. All 54 α values of
  its table match 005329Z to 3 decimals (0 mismatches); the 55th row is the constant Bernstein–Vazirani check.
- RL-022: α up to 1.128.
- RL-044 and RL-045: 88 V2, α 0.886..1.164, V1 on 43 entries with 2812 instances and 5917 runs.
- RL-048/RL-050: 90 V2, 82 diagnostics, 5 resolving, all count-based.
- RL-027 and RL-032 values match the first run that recorded them.
- One minor provenance difference: RL-030 quotes Kuhn vs n^2.5 = 1.168 and HK vs n³ = 0.815 (agent console). The
  ledger cross-fits give 1.169–1.172 and 0.817–0.819. They are consistent, but not the same numbers.

**4d. Claimed level vs evidence.** Using the entry's other algorithms as post-hoc rivals
(`2026-10-07b_cross_fits.py`: 103 cross-fits, 97 rejected, each verdict the same in every run that has both
series), only these 6 pass:
- matching, both directions (F1);
- Karatsuba vs n² (F2);
- BBHT vs 2^(n/2) (F3);
- Kruskal vs n² (1.100–1.114) and Prim vs n² log n (0.915–0.924). These two are expected: both are "fast" algorithms
  and the log factor cannot be resolved (RL-048). They do not affect the pair's separation.

**Timing does not resolve the log factor in any of the 8 timing fits whose cost multiplies a polynomial by
log n** (070542Z diagnostics; RL-048):
- the seven n log n fits: closest pair, element distinctness by sorting, inversion counting by merge, LIS patience
  sorting, merge sort, NTT and the sparse table;
- Kruskal's n² log n.

For the 5 pure log n fits the diagnostic cannot be computed at all, because log n / log n is constant. The n log n
passing bands span effective exponents of about 0.87–1.49 (section 5). Under timing, V2 for these entries means
"consistent up to log factors", as RL-048 already states.

**4e. time_complexity text vs harness.scaling.cost.** Manual review of all 39 V2 entries:
- **One substantive mismatch: chromatic inclusion–exclusion (F4).** The text says (2χ+2)·2ⁿ and Θ(n·2ⁿ) only when
  χ = Θ(n). The harness claims n·2ⁿ on G(n, 0.8), where χ/n is 0.50–0.64 at n ≤ 18. Asymptotically χ is about
  n/(2 log_b n) with b = 1/(1−p) = 5, which is a standard random-graph result, not checked here. So n·2ⁿ is an upper
  bound, not the Θ that the timing family attains.
- **Implicit but correct encodings:**
  - matching: cost n³ and n^2.5 with n = V, relying on E = Θ(V²) on the adversarial family;
  - knapsack DP: n² because W = Θ(n), which the entry states;
  - Euclid: n² in bit cost, which the entry states;
  - LCS brute force: the text says Θ(2ⁿ n), and the implementation's docstring says Θ(2ⁿ(n+m)), but the code ends a
    mask's scan early when `b.find` fails, so Θ holds only on inputs without early exits (F16).

**4f. Tags vs algorithms.**
- The validator's tag rules (T4, T5, T9, T7) pass in all runs.
- LP's secondary T6 is justified by its caveat: a strongly polynomial LP algorithm is open.
- Conditional lower bounds are marked in `setting`: edit distance and LCS are conditional on SETH, and 3SUM rests on
  the 3SUM conjecture.
- One convention gap (F14).

## 5. Weakest V2 claims, ranked

How the ranking is computed:
1. Does the entry's own slower cost also fit the fast algorithm's data (section 4d)?
2. The margin to the tolerance edge.
3. The cost span.
4. Timing only, with no rivals.
5. Whether the cost model matches the instances.

The **passing band** (`2026-10-07b_cross_fits.py` B) makes "how discriminating" concrete. At tolerance 0.25 a timing
fit accepts any alternative power law n^q with q roughly in [0.8·p_eff·α, 1.33·p_eff·α]. For example:
- Hungarian n³ accepts q ∈ [2.32, 3.87];
- an n log n fit accepts effective exponents in about [0.87, 1.49];
- a 2ⁿ claim accepts bases in about [1.74, 2.52] (trial divisors: [1.785, 2.628]);
- Held–Karp's n²·2ⁿ accepts effective bases [2.03, 3.24], so its data would also pass 3ⁿ.

| Rank | Entry (algorithm) | Weakness | Note |
|---|---|---|---|
| 1 | bipartite matching (both) | the separation is not resolved in either direction; timing only, no rivals (F1) | — |
| 2 | integer multiplication (Karatsuba) | data also fit n²; the schoolbook-side rejection margin is 0.013–0.023 (F2) | — |
| 3 | collision (BBHT variant) | smallest margin (0.086); pre-asymptotic; does not exclude 2^(n/2) (F3) | the exact formula gives slope 1.009 over n = 15..30 (RL-032) |
| 4 | chromatic number (inclusion–exclusion) | cost model ≠ instances; 2ⁿ, χ·2ⁿ and n·2ⁿ are not distinguishable (F4) | — |
| 5 | Simon (quantum) | α = 1.121 is driven by n = 2; span 5×; s.e. 0.057 (F5) | — |
| 6 | all n log n timing claims (7) and Kruskal | log factor unresolvable; passing band [0.87, 1.49] | — |
| 7 | Fibonacci fast doubling and companion-matrix log n (4, three of them T7) | span 16×; falling local slope; margin down to 0.122 (F10) | — |
| 8 | maximum subarray (all three) | instance type changes with n (F7) | — |
| 9 | Dürr–Høyer | α = 0.886 (margin 0.136); quantum > classical below n = 12 (F11) | — |
| 10 | Floyd–Warshall and the other n^2.5+ fits | α 0.925–0.982 from lower-order terms (F9) | — |

**Not weak** (for contrast):
- Exact deterministic counts (Strassen, Deutsch–Jozsa, Bernstein–Vazirani, minimum finding classical, Grover
  quantum).
- Exponential slow algorithms against polynomial fast ones, where every cross-fit rejects by a wide margin. Examples:
  Hungarian against permutation enumeration gives α = 0.006, and closest-pair all-pairs data against n log n gives
  1.741.

## 6. Patterns across the dataset

Script: `2026-10-07b_patterns.py`. Timing fits are grouped by claimed cost, using the effective exponent over the
n range.

| Group | Fits (latest) | Mean α | α < 1 | Mean (2nd half − 1st half) | Positive drift | Pooled over 5 runs |
|---|---|---|---|---|---|---|
| poly, exponent ≥ 2.5 | 10 | 0.964 | **10** | +0.049 | **10** | 40/40 α < 1, 40/40 rising |
| poly, exponent 1.5–2.5 | 20 | 1.014 | 2 | +0.003 | 8 | 10/94 α < 1 |
| lin (n, n log n) | 16 | 0.996 | 10 | +0.006 | 9 | 40/66 α < 1 |
| log n | 5 | 1.058 | 0 | −0.108 | 0 | 0/17 α < 1, 0/17 rising |
| exponential / factorial | 23 | 0.992 | 17 | +0.012 | 15 | 73/103 α < 1 |

**Reading:**
1. **Cubic and higher: systematically α < 1 with rising slope.** This is lower-order terms. Over the 9 pure n^p cases
   (`lower_order_fits.py`), b/a ranges from 6.85 (Gaussian elimination) to 21.76 (Floyd–Warshall); the two matching
   fits (n³ and n^2.5) have b/a of 10.37 and 10.51. One n^(p−1) term cuts the residual 4.68–21.80× in 8 of the 9.
   The exception is max-subarray brute force (1.39×), where the instance mix dominates. Constant per-row Python overhead (loop setup, row lookups) is the
   natural candidate. The fit is consistent with this explanation but does not prove it.
2. **Log n: systematically α > 1 with falling slope.** This is the opposite curvature: the cost per step grows with n
   before it saturates. The small-integer hypothesis of F10 is untested, and c2-3 does not fit it cleanly.
3. **Quadratic: mostly α ≥ 1.**
   - Two DP tables have local slopes that rise *above* 1 at the largest n: Wagner–Fischer reaches 1.115 at
     n = 600 → 800, and LCS DP 1.055. This is consistent with a memory-hierarchy effect (an n² table of Python ints;
     untested).
   - The capacity DP of knapsack has the largest poly2 α (1.060), with an irregular slope sequence of 1.114, 1.079,
     0.884, 1.123, 1.028.
4. **Exponential and factorial: slightly below 1 (mean 0.992), flat slopes.**
   - Shortest-path enumeration (0.965) and permutation enumeration for assignment (0.972) are flat over n = 8..11 and
     6..9. The per-leaf work therefore grows more slowly than the claimed factor n over these tiny ranges. Python
     enumeration overhead per permutation is the natural candidate.
   - GCD trial divisors is the one exponential above 1 (1.044–1.052, local slopes 1.052, 1.047, 1.052, 1.024). Its
     cost text allows an extra n-bit-division factor, which could explain it, but this was not tested.
5. **Quantum counts.** Every non-exact quantum count fit is pre-asymptotic (Simon, BHT, BBHT, Dürr–Høyer, Grover); the
   pre-asymptotic part is computable exactly from closed forms (section 3).

---

## Near misses

**Cross-fits rejected by less than 0.1** (`2026-10-07b_cross_fits.py`, latest run). Here "X data vs Y" means X's
recorded values fitted against Y's claimed cost.

| Fit | α | Margin |
|---|---|---|
| schoolbook multiplication data vs n^log₂3 | 1.273 | **0.023** |
| Floyd–Warshall data vs n²(n−1)² | 0.689 | 0.061 |
| chromatic inclusion–exclusion data vs 3ⁿ | 0.686 | 0.064 |
| running sums data vs n³ | 0.686 | 0.064 |
| BHT known t data vs 2^(n/2) | 0.681 | 0.069 |
| palindrome expand data vs n³ | 0.670 | 0.080 |
| 3SUM two-pointer data vs n³ | 0.670 | 0.080 |
| Bellman–Ford data vs n³ | 1.340 | 0.090 |

General rule: an n² algorithm's data reject n³ only if its α < 1.125. Every n³ → n² pair is therefore one
pre-asymptotic drift of +0.125 away from losing its implicit separation.

**Noise-free rival margins in the working-tree configs** (`2026-10-07b_rival_margin_precheck.py`, about 10:05,
in-progress files):
- **n² vs rival n² log n: margins +0.035 to +0.041** at tolerance 0.03 (element distinctness, inversion counting,
  sorting);
- n log n vs rivals n and n·log² n: +0.059 to +0.083;
- Strassen: +0.044 and +0.049;
- XOR convolution naive vs n·4ⁿ: +0.065.

Exact counts with lower-order terms (e.g. merge-sort comparisons, n log₂ n − Θ(n)) will use part of the 0.03 band.
The size of that part depends on the count definition, which was not checked here.

**Other close calls:**
- Simon quantum would have read α ≈ 1.0186 with an n = 2 mean equal to E(2). It reads 1.121, 1.80 s.e. away
  (predicted s.e. 0.0569).
- Fast doubling's α reached 1.128 in run 005747Z, a margin of 0.122.

## Decision log

- **Analyse the ledger, not live re-measurements.** Alternative: re-run `validate.py --scaling`. Rejected because the
  brief forbids heavy runs while another agent runs CPU-heavy searches (flipwalk processes were visible). The ledger
  also holds every value needed. The only re-measurement is the Kadane check: about 1–3 s per run, interpreted only as
  ratios within a round, with all three runs reported.
- **Spread is computed within an identical configuration.** Without this, a harness change would look like
  instability. The deciding evidence: 0 configuration changes across the 5 runs, so the per-series spread is all
  timing noise.
- **Local slopes are reported against the claimed cost, not ln n.** This makes "1" the target for every cost class.
  The half-split α was added because single local slopes are noisy (for example, Grover's 0.807 is a floor effect).
  The sign consistency across runs separates curvature from noise.
- **Post-hoc rivals come from the entry's own other algorithms.** Alternative: arbitrary alternatives such as cost·n^±δ.
  Rejected as the primary test, because the entry's own slower cost is the one alternative that the pair's
  separation claim must exclude. Arbitrary alternatives appear as the passing band instead.
- **Exact variances where available.** For Simon quantum, the per-n variance is the sum of geometric variances; for
  birthday search, it comes from the survival function. For BHT, the agent's run-2 sd is used and labelled agent
  report. Alternative: the empirical sd. Not available, because the ledger stores means only.
- **Name matching in the theory script is now ordered** ("exponential" before "known") after the substring bug
  (section 3). Deciding evidence: the agent's exact table did not match the first output.
- **The in-progress entries are excluded from the findings, except as a snapshot.** Files changed while the analysis
  ran (10:01–10:07). Analysing a moving target would give non-reproducible statements, and the ledger is the
  citable evidence.
- **χ(G) uses the harness's own oracle.** This avoids a new, unverified colouring routine. `_colourable` is the oracle
  that V1 already relies on.

## Open ideas

*Forward-looking content is not published (RL-086).*
