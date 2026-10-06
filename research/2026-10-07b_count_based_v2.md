# Count-based, discriminating V2 for eight classical entries

Date: 2026-10-06 (local), work session 09:54–10:25. Follows RL-040, RL-047 and RL-048.
Author: delegated research agent (Claude), for the maintainer.

Every number here comes from a run made in this session. The provenance is given per section: the script
under `experiments/`, or `tools/validate.py`. No timing is reported. All V2 values are exact operation counts
on seeded inputs, so CPU load from parallel agents cannot affect them.

**Environment.**
- Python 3.14.2, project `.venv`, for all experiments and the final validator runs.
- At the start of the session `.venv` had jsonschema 3.2.0, installed as a cffconvert dependency at 09:35, so
  `tools/validate.py` failed on import. The intermediate validator runs therefore used jsonschema 4.26.0
  installed with `pip --target` into the scratchpad and put first on `PYTHONPATH`. The shared venv was left
  untouched.
- After the maintainer repaired `.venv` (jsonschema 4.26.0, cffconvert removed), every final number was re-run
  with plain `./.venv`:
  - `tools/validate.py <8 entries> --scaling -v`: 8/8 OK. The α, rival and diagnostic lines were identical to
    the workaround run.
  - unit tests: 91 OK.
  - `tools/validate.py --static`: 62/62 OK.
- Cross-version check: Python 3.12.10 (`py -3.12`, standard library only).

## Summary

| Entry | Converted? | Counted quantity | Log factor resolved now? |
|---|---|---|---|
| sorting-insertion-vs-merge | yes | key comparisons | yes, both |
| element-distinctness-pairs-vs-sorting | yes | comparisons between input values | yes, both |
| bipartite-matching-kuhn-vs-hopcroft-karp | yes | edge scans (adjacency entries read) | yes, both |
| inversion-counting-quadratic-vs-merge | yes | element comparisons | yes, both |
| longest-increasing-subsequence | yes (3 algorithms) | element comparisons | DP and patience yes; subset enumeration **no** (0.982) |
| closest-pair-brute-vs-divide-conquer | yes | multiplications (a squaring counts as one) | yes, both |
| all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall | yes | relaxation steps (weight additions) | yes, both |
| string-matching-naive-vs-kmp | yes | character comparisons | yes, both |

- **All 8 candidates were converted, 17 algorithm fits in total.** All 17 pass at tolerance 0.03, and all 36
  declared rivals are rejected.
- **The log-factor diagnostic is resolved for 16 of the 17 fits.** All 17 were timing fits before this change,
  and RL-048 found that no timing fit resolves a log factor.
- **The counts are independent of the Python version.** All 17 count series are identical under Python 3.12.10
  and 3.14.2.
- **Instrumentation only.** Every count comes from the harness (an instrumented element, key, weight, character
  or adjacency-list type passed in by `generate_scaling`). No file under `implementations/` was edited: all 17
  implementation files are dated 02:25–03:42, before this session.
- **V1 is unchanged.** `generate` is unchanged in all eight harnesses. Only `generate_scaling`, `reported_cost`
  and the counting class were added; a `generate_scaling` that already existed was wrapped, with the same draws
  in the same order.

**Common tolerance window.** Tolerance is 0.03 for every fit. From `experiments/2026-10-07b_count_v2_summary.py`,
which uses the validator's own `run_v2`:
- the largest |α − 1| over the 17 fits is 0.0140;
- the smallest distance |α_rival − 1| over all declared rivals is 0.0644;
- so any tolerance in [0.0140, 0.0644) gives the same verdicts.

0.03 satisfies 2 × 0.0140 ≤ 0.03 ≤ 0.0644 / 2 (decision D2).

## 1. Per entry

In every list below:
- α is the validator's fitted slope, shown to 3 decimals as `tools/validate.py` prints it;
- "diag" is the validator's diagnostic: α against cost·log n / α against cost/log n;
- counts are listed in n order.

### 1.1 sorting-insertion-vs-merge: converted

**What is counted.** `CountingKey` wraps the values of `generate()`: uniform on [−n, n], with the same seeded
values the earlier timing fit used, so insertion sort is measured in its average case. Every `<`, `<=`, `>`,
`>=`, `==`, `!=` is counted. Insertion sort compares only with `>`, merge sort only with `<`.

**Cross-check.** The instrumented count equals a closed form computed from the input alone:
- for each i, let g_i = the number of earlier elements larger than a_i;
- the count is Σ_i (g_i + [g_i < i]);
- equal at n = 50, 100, 250, 500 (731, 2990, 15452, 62822).

**Insertion sort.** Claim n², 3 seeded samples, n = 250, 500, 1000, 2000, 4000.
- Mean counts: 15574.67, 63461.67, 250154.67, 999716.33, 3990076, i.e. 0.997–1.015 × n²/4.
- α = 0.999.
- Rivals: n log n α = 1.743, rejected; n² log n 0.931, rejected.
- Diag 0.931 / 1.078, resolved.

**Merge sort.** Claim n log n, 1 sample, n = 1000, 2000, 4000, 8000, 16000, 32000, 64000.
- Counts: 8701, 19408, 42854, 93621, 203198, 438577, 941409, i.e. n log₂ n − c·n with c = 1.2523–1.2659.
- α = 1.011. The excess over 1 comes from the −c·n term.
- Rivals: n 1.126, n log² n 0.918, n² 0.563; all rejected.
- Diag 0.918 / 1.126, resolved.

Script: `experiments/2026-10-07b_count_v2_sorting.py`.

### 1.2 element-distinctness-pairs-vs-sorting: converted

**What is counted.** `CountingKey` wraps the n distinct values of the existing `generate_scaling` (same draws).
`==` in the all-pairs scan; `<=` and `==` in the sort-and-scan.

**All pairs.** Claim n², n = 500, 1000, 1500, 2000, 3000, 4000.
- Counts: exactly n(n−1)/2 (124750, 499500, 1124250, 1999000, 4498500, 7998000).
- α = 1.000.
- Rivals: n log n 1.757, n² log n 0.936; both rejected.
- Diag 0.936 / 1.075, resolved.

**Sort, then compare neighbours.** Claim n log n, n = 1000, 2000, …, 128000.
- Counts: 9710, 21426, 46876, 101729, 219403, 471108, 1006063, 2140632, i.e. n log₂ n − c·n with
  c = 0.2421–0.2558. This includes the n − 1 neighbour tests.
- The merge part lies within bounds computed from run lengths alone at every n.
- α = 1.002.
- Rivals: n 1.111, n log² n 0.912, n² 0.556; all rejected.
- Diag 0.912 / 1.111, resolved.

Script: `experiments/2026-10-07b_count_v2_element_distinctness.py`.

### 1.3 bipartite-matching-kuhn-vs-hopcroft-karp: converted

**What is counted.** `CountingNeighbours`, a tuple subclass, wraps each adjacency list of the existing
adversarial family G_k (n = V = 4k² + k). It counts every entry read by indexing or by iteration; `len()` is not
counted.

**Cross-check.** The harness counts equal, value for value, the counts of the explicit-counter copies in
`experiments/2026-10-07_bipartite_matching_counts.py`, for every k used. Its two counting functions were
extracted by AST, because that script has no `__main__` guard. Hopcroft–Karp ran exactly k + 1 phases for every
k = 4..15.

**Kuhn.** Claim n³, k = 3..11, n = 39..495.
- Counts: 987, 5190, 19210, 56439, 140945, 312092, 630000, 1181845, 2088999 (0.1431–0.1480 V·E).
- α = 1.005.
- Rival n^2.5: α = 1.207, **rejected**. The timing fit had passed against it (1.168, RL-030).
- Diag 0.941 / 1.079, resolved.

**Hopcroft–Karp.** Claim n^2.5, k = 4..15, n = 68..915.
- Counts: 4572, 13602, 33313, 71227, 137782, 246812, 416027, 667493, 1028112, 1530102, 2211477, 3116527
  (1.0153–1.0501 E·√V).
- α = 1.004.
- Rivals: n² 1.255 and n³ 0.837, both **rejected**. Timing had passed both (1.221 and 0.815).
- Diag 0.936 / 1.083, resolved.

Script: `experiments/2026-10-07b_count_v2_matching.py`.

### 1.4 inversion-counting-quadratic-vs-merge: converted

**What is counted.** `CountingKey` wraps the values of `generate()`: [0, n], with the same seeds as the earlier
timing fit. The harness previously had no `generate_scaling`.

**All pairs.** Claim n², n = 250, 500, 750, 1000, 1500, 2000.
- Counts: exactly n(n−1)/2 (31125 … 1999000).
- α = 1.001.
- Rivals: n log n 1.735, n² log n 0.930; both rejected.
- Diag 0.930 / 1.084, resolved.

**Merge-sort counting.** Claim n log n, 1 sample, n = 2000, …, 64000.
- Counts: 19421, 42827, 93679, 203327, 438368, 941126, i.e. c = 1.2553–1.2668.
- Every count lies within the merge bounds; the 3-sample spread is ≤ 0.11% of the count.
- α = 1.010.
- Rivals: n 1.119, n log² n 0.920, n² 0.560; all rejected.
- Diag 0.920 / 1.119, resolved.

Script: `experiments/2026-10-07b_count_v2_inversions_lis.py`.

### 1.5 longest-increasing-subsequence: converted (all three algorithms)

**What is counted.** `CountingKey` wraps the existing strictly increasing scaling input (same draws). Every count
equals a closed form in n; each was checked at every n used.

**Subset enumeration.** Claim 2ⁿ·n, n = 12..18.
- Closed form n·2ⁿ⁻¹ − 2ⁿ + 1: one `<=` per chosen index after the first, summed over all masks.
- Counts: 20481, 45057, 98305, 212993, 458753, 983041, 2097153.
- α = 1.014.
- Rivals: 2ⁿ 1.113, 2ⁿ·n² 0.931; both rejected.
- Diag 0.982 / 1.049, **not resolved** (see near-misses).
- This counts comparisons, not the 2ⁿ·n loop steps of the entry's `time_complexity`. Those steps are integer
  bit operations, which the harness cannot see.

**Quadratic DP.** Claim n², n = 100, 200, 400, 800, 1600.
- Counts: exactly n(n−1)/2 (4950 … 1279200).
- α = 1.002.
- Rivals: n log n 1.713, n² log n 0.923; both rejected.
- Diag 0.923 / 1.094, resolved.

**Patience sorting.** Claim n log n, n = 10000, 30000, 100000, 300000.
- Closed form Σ_{j=2..n} ⌊log₂ j⌋. A binary search over s tails that are all smaller than x makes
  ⌊log₂(s+1)⌋ comparisons.
- Counts: 113631, 387248, 1468946, 4875732, i.e. c = 1.92–1.96.
- α = 1.012.
- Rivals: n 1.105, n log² n 0.933, n² 0.553; all rejected.
- Diag 0.933 / 1.105, resolved.

Script: `experiments/2026-10-07b_count_v2_inversions_lis.py`.

### 1.6 closest-pair-brute-vs-divide-conquer: converted (multiplications, not comparisons)

**What is counted.** `CountingInt` wraps every coordinate of the existing `generate_scaling` (same draws).
Differences, sums and products of coordinates stay `CountingInt`. Every multiplication is counted, and a
squaring `** 2` counts as one.
- With `CountingInt`, both implementations return the same answers as on plain integers (n = 2, 3, 4, 7, 50,
  300).

**All pairs.** Claim n², n = 125..2000.
- Counts: exactly n(n−1) (15500 … 3998000).
- α = 1.001.
- Rivals: n log n 1.721, n² log n 0.926; both rejected.
- Diag 0.926 / 1.090, resolved.

**Divide and conquer.** Claim n log n, n = 1000..64000.
- Counts: 14523, 31335, 68047, 147196, 314573, 674959, 1436363, i.e. 1.406–1.457 · n log₂ n.
- Breakdown:
  - strip filter S(n) = n + S(⌊n/2⌋) + S(⌈n/2⌉) for n > 3, zero otherwise; exact, 61.5–66.5% of the count;
  - base cases, 2 per pair;
  - the data-dependent strip scan, 28.7–31.1%.
- α = 0.993; the three seeded samples give 0.993–0.995.
- Rivals: n 1.105, n log² n 0.902, n² 0.553; all rejected.
- Diag 0.902 / 1.105, resolved.

Script: `experiments/2026-10-07b_count_v2_closest_pair.py`.

### 1.7 all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall: converted

**What is counted.** `CountingWeight` wraps every off-diagonal weight of the existing complete-digraph
`generate_scaling` (same draws). It counts additions, i.e. one per relaxation step. Answers are unchanged
(n = 5, 12, 20).

**Bellman–Ford × n.** Claim n²(n−1)², n = 8..40.
- Counts: exactly n²(n−1)² (3136 … 2433600). Every addition `dist[u] + w` involves an input weight.
- α = 1.000.
- Rival n³: α = 1.377, rejected.
- Diag 0.921 / 1.094, resolved.

**Floyd–Warshall.** Claim n³, n = 32..200.
- Counts: exactly n³ − n (32736 … 7999800). The n steps with i = j = k add the implementation's own diagonal
  zeros and are invisible to the weight type.
- α = 1.000.
- Rival n²(n−1)²: α = 0.745, rejected.
- Diag 0.929 / 1.083, resolved.

Script: `experiments/2026-10-07b_count_v2_apsp_strings.py`.

### 1.8 string-matching-naive-vs-kmp: converted

**What is counted.** A `str` cannot carry instrumented characters. The scaling instance T = aⁿ, P = a^(m−1)b
(m = n // 2) is therefore passed as tuples of `CountingChar`, which counts `==` and `!=`.
- The implementations use only `len()`, indexing, iteration and `==`/`!=`.
- They return the same answers on tuples as on strings, on the scaling instances and on 200 random small
  (text, pattern) pairs.

**Naive.** Claim n², n = 200..3200.
- Counts: exactly (n − m + 1)·m (10100 … 2561600).
- α = 0.998.
- Rivals: n 1.997, n² log n 0.928; both rejected.
- Diag 0.928 / 1.080, resolved.

**KMP.** Claim n, n = 3000..300000.
- Counts: exactly 3n + 2m − 6 = 4n − 6 (11994 … 1199994). The failure function makes 3m − 6 and the scan 3n − m.
- α = 1.000.
- Rivals: n log n 0.910, n² 0.500; both rejected.
- Diag 0.910 / 1.109, resolved.

Script: `experiments/2026-10-07b_count_v2_apsp_strings.py`.

## 2. Near-misses (with numbers)

- **The LIS subset-enumeration diagnostic is not resolved.** α against 2ⁿ·n·log n is 0.982 (distance 0.018 <
  0.03). On n = 10..16 it is 0.980, and on n = 14..20 (closed form only, not run) it is 0.983. The claim against
  the declared rivals 2ⁿ (1.113) and 2ⁿ·n² (0.931) is still discriminated. A log-factor rival is not a
  meaningful alternative for this exponential algorithm, so no entry text depends on it.
- **Lower-order terms set the floor of the tolerance.** At tolerance 0.01, four fits would fail:
  - merge sort, α 1.0114;
  - merge-sort inversion counting, 1.0101;
  - patience sorting, 1.0120;
  - subset enumeration, 1.0140.

  All four come from −c·n-type terms. At Strassen's 0.02 all 17 would pass, with the smallest margin 0.006.
- **The old n ranges were closer to the edge.** Patience sorting on n = 1000..100000 gives α = 1.018, and subset
  enumeration on n = 10..16 gives 1.019. Insertion sort on n = 100..3200 with one sample gives α = 0.983, with a
  local slope of 0.883 between n = 100 and 200, from sampling noise in the inversion count. With 3 samples on the
  same range it gives 0.994. All of these would still pass at 0.03; the ranges were moved anyway (D5).
- **Smallest margins on the rival side.**
  - The element-distinctness all-pairs rival n² log n sits at 0.936 (distance 0.064). This is the smallest rival
    distance, so any tolerance ≥ 0.064 would let that rival fit.
  - Kuhn's diagnostic distance is 0.059 (0.941), the smallest among the resolved diagnostics.
- **Kuhn's ratio has not settled.** Scans / (V·E) moves from 0.1480 (k = 3) to 0.1431 (k = 7) and back to 0.1435
  (k = 11). α is 1.005 over k = 3..11 and 1.008 over k = 5..11.
- **Closest-pair divide and conquer jitters locally.** Its local slopes are 0.9749, 0.9937, 0.9976, 0.9896, 1.0015,
  0.9966, from the data-dependent strip scan (about 29–31% of the count). The global α differs by only 0.0016
  across three seeded samples.
- **Comparisons were tried for closest pair and dropped.** Including comparisons made inside CPython's
  `sorted()` and `min()`, the counts fit n log n with α = 1.007 under Python 3.14.2. But they differ between
  Python versions: at n = 1000, 39380 under 3.12.10 against 39445 under 3.14.2
  (`experiments/2026-10-07b_count_v2_cross_version.py`).
- **Floyd–Warshall reports n³ − n, not n³.** The instrumentation cannot see the n diagonal steps 0 + 0 at
  i = j = k. The effect on α is below 0.001.

## 3. Decision log

- **D1 Instrumented types in the harness, not instrumented copies.** V2 must measure the implementation that
  V1 checks.
  - The alternative, copying the implementations with counters as in
    `experiments/2026-10-07_bipartite_matching_counts.py`, measures a different program.
  - It is kept as a cross-check: the harness and copy counts agree exactly for matching.
  - **Deciding evidence:** that agreement, plus closed-form agreement for at least one algorithm in each of the
    other 7 entries. Merge-based counts have no closed form, so they were checked against bounds instead.
- **D2 One tolerance, 0.03, for all 17 fits.**
  - **Rule:** at least 2× the largest lower-order deviation (2 × 0.0140 = 0.028), and at most half the smallest
    rival distance (0.0644 / 2 = 0.032).
  - **Alternatives:**
    - 0.02 (Strassen's): passes, but leaves 0.006 margin for subset enumeration;
    - 0.05: still rejects every rival (smallest distance 0.064), but the rival-side margin would only be 0.014;
    - per-fit tolerances: harder to audit.
  - **Deciding evidence:** the window [0.0140, 0.0644) from the summary script.
- **D3 Same inputs as the previous timing V2.** `generate_scaling` wraps exactly the values the timing fit used:
  `generate()`'s draws for sorting and inversions, the existing `generate_scaling` draws elsewhere, in the same
  order. Only the measured quantity changes. No input family was changed.
- **D4 Samples.**
  - 3 for insertion sort. Its count is input-dependent: the three samples at n = 250 were 15452, 15666 and 15606.
  - 1 everywhere else:
    - exact closed forms, which are input-independent;
    - merge-based counts, with 3-sample spreads ≤ 0.098% (sorting) and ≤ 0.11% (inversions);
    - closest pair, with per-sample α 0.9933 / 0.9949 / 0.9949.
- **D5 Three n ranges were moved up, so that the leading term dominates.**
  - insertion sort: 100..3200 → 250..4000, against small-n sampling noise;
  - subset enumeration: 10..16 → 12..18, α 1.019 → 1.014;
  - patience sorting: 1000..100000 → 10⁴..3·10⁵, α 1.018 → 1.012.

  All other n_values are unchanged. Runtime cost: in the final validator run the slowest single fit took 3.7 s
  (Floyd–Warshall), and the V2 parts of all 17 fits took 19.3 s in total (sum of the validator's per-fit times).
- **D6 Rivals.**
  - the other algorithm's cost;
  - plus log-factor neighbours: n and n log² n for n log n claims, n² log n for n² claims;
  - factor-n neighbours 2ⁿ and 2ⁿ·n² for subset enumeration;
  - n^2.5 for Kuhn, and n² and n³ for Hopcroft–Karp, as the brief asked.

  For APSP and matching, log-factor rivals were not declared; their log factor is covered by the diagnostic
  (resolved in all 4 fits).
- **D7 Closest pair counts multiplications, not comparisons.** The deciding evidence is the cross-version
  difference above. Multiplications all happen in the implementations' own Python code, and all 17 V2 count
  series hash identically under 3.12.10 and 3.14.2 (sha256 `26ea1a9e…d01c`). The entry's caveats state the
  limit: the comparisons of the initial sort and of the merges are not counted.
- **D8 String matching uses tuples of `CountingChar`.**
  - **Alternative not tried:** a `str` subclass overriding `__getitem__`/`__iter__`, which would keep
    `isinstance(text, str)` true. Its elements would still not be `str` characters, so it buys nothing for these
    implementations, which use only the sequence protocol.
  - **Deciding evidence:** equal answers on 200 random pairs and on the scaling instances.
- **D9 APSP counts additions only.** Counting comparisons too would double the count without changing α.
- **D10 No recorded ledger run and no RESEARCH_LOG entry.** `--record` calls git, which this brief forbids.
  RESEARCH_LOG is the maintainer's to edit.
- **D11 No timing was measured**, so the "3 runs" rule for timing did not apply.

## 4. Open ideas

- **Convert the four remaining timing fits whose claims contain a log factor.** Found by scanning all
  `pairs/*/entry.json`; not touched here:
  - `fibonacci-naive-vs-dp` (fast doubling, log n);
  - `minimum-spanning-tree-brute-vs-kruskal` (n² log n);
  - `polynomial-multiplication-naive-vs-ntt` (n log n);
  - `range-minimum-queries-naive-vs-sparse-table` (n log n).

  NTT can count modular multiplications with a `CountingInt`, if its implementation does arithmetic through
  Python operators; this was not checked.
- **Insertion sort worst case.** Reversed input gives exactly n(n−1)/2 comparisons, a deterministic alternative
  to the average case. It would need its own instance family, and `generate_scaling` is shared by both
  algorithms.
- **A version-independent comparison count for closest pair.** Count only comparisons whose operands are
  products, i.e. squared distances or gaps. That would exclude the sort's coordinate comparisons; it is untested.
- **Ledger stability.** A recorded run (`--record`) by the maintainer would make the 17 count series part of the
  ledger. Since they are exact and version-independent, future runs should reproduce them value for value,
  which `experiments/2026-10-07b_ledger_stability.py` could check.
- **Exactness across the dataset.** Exact counts plus closed forms (10 of the 17 fits here have one) would let
  the validator check *equality* with the closed form instead of a slope. That would be a stronger V2, but it
  needs a schema change (not proposed here).
