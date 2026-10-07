# Count-based V2 for the remaining log-factor and factor-n timing fits

Date: 2026-10-06 (local), work session 11:30–11:52. Follows RL-047, RL-048, RL-057 and RL-061 items 3–4
(deviation finding F4), and uses RL-062.
Author: delegated research agent (Claude), for the maintainer.

**Provenance.**
- Every number below comes from a run made in this session: a script under `experiments/2026-10-06c_*.py`, or
  `tools/validate.py`.
- All V2 values reported are exact operation counts on the validator's seeded inputs. CPU load from parallel
  agents cannot affect them.
- No timing number is reported as evidence. The Fibonacci and chromatic entries still have timing fits, and
  they were run only for pass/fail, as rule 6 requires.

**Environment.**
- Project `.venv`, Python 3.14.2, for all experiments and validator runs.
- Cross-version check under Python 3.12.10 (`py -3.12`, standard library only), which is CI's version.
- Helper: `experiments/2026-10-07b_count_v2_helpers.py`, from the previous round, is imported unchanged by the
  scripts. Its `counts()` reproduces the validator's seeds and call sequence, and its fits use the validator's
  own `eval_cost` and `fit_slope`.

## Summary

| Entry | Converted? | Counted quantity | α (tol 0.03) | Rivals rejected | Factor resolved? |
|---|---|---|---|---|---|
| range-minimum-queries-naive-vs-sparse-table | **yes** (both) | comparisons between values | scan 1.001; sparse table 1.007 | 3/3; 3/3 | **yes** (log n), both fits |
| polynomial-multiplication-naive-vs-ntt | **yes** (both) | multiplications with an input-derived operand | schoolbook 1.000; NTT 1.000 (exact form) | 2/2; 3/3 | **yes** (log n), both fits |
| minimum-spanning-tree-brute-vs-kruskal | **yes** (all 3) | comparisons and +, *, divmod on input weights | Kruskal 0.998; Prim 1.007; enumeration 0.995 | 3/3; 2/2; 3/3 | **yes** (Kruskal vs Prim log n) |
| fibonacci-naive-vs-dp | **no** | — | timing fit kept | — | no |
| chromatic-number-subset-dp-vs-inclusion-exclusion | **no** | — | timing fits kept | — | no (F4 stays open) |

- **Scale:** 7 algorithm fits converted, 18 declared rivals, all rejected. Common tolerance window
  [0.0073, 0.0652): largest |α − 1| = 0.0073 (RMQ sparse table), smallest rival distance 0.0652 (MST
  enumeration against C(m, n−1)).
  *Correction (2026-10-07): the number of declared rivals is 19, as the table above shows (3 + 3 + 2 + 3 + 3 + 2 + 3)
  and as ledger/runs/20261006T104637Z.json records; all 19 are rejected.*
- **Log factor:** the validator's log-factor diagnostic is resolved in all 7 fits
  (`experiments/2026-10-06c_count_v2_summary.py`). All 7 were timing fits before.
- **Implementations unchanged:** every file under `implementations/` of the five entries is dated
  01:42–03:38, before this session. V1 is unchanged: `generate` was not touched. In RMQ and MST, the old
  `generate_scaling` body became `_scaling_draws`, so the draws are the same values in the same order. NTT had
  no `generate_scaling`; the new one calls `generate`, which is what V2 used before.
- **Cross-version:** under 3.12.10 every count series is identical except Kruskal's. Kruskal's counts are
  0.17–0.30% lower there, entirely in the comparisons made inside `sorted()`, with α 0.9982 instead of 0.9980
  and the same verdicts.
- **Two entries not converted, and why.** Fibonacci fast doubling and chromatic inclusion–exclusion do their
  dominant arithmetic on values the implementation creates from literals. An instrumented input value never
  takes part in that arithmetic; this was demonstrated with a propagating tracer type (§4, §5).
  - The reason is recorded in both entries (`verification.method`, README).
  - Their timing fits stay, and their claimed level (V2) is unchanged.

Final validator runs (console):
- `tools/validate.py <the 5 entries> --scaling -v`: 5/5 OK;
- `tools/validate.py --static`: 62/62 OK;
- unit tests: 110 OK.

## 1. range-minimum-queries-naive-vs-sparse-table: converted

**What is counted.** `generate_scaling` makes the same draws as before. The values are wrapped in
`CountingKey`, which counts `<`, `<=`, `>`, `>=`, `==` and `!=`; the query index pairs stay plain ints.
- Scan: the comparisons are `x < m`.
- Sparse table: the comparison inside each two-argument `min(prev[i], prev[i + half])` of the table build,
  plus `a <= b` per query.

**`min()` calls `__lt__`.** Checked directly (`experiments/2026-10-06c_rmq_counts.py`):
- `min(x, y)` on two counting values makes exactly 1 counted comparison, for the orders (3, 5), (5, 3) and
  (4, 4);
- `min(x, y, z)` makes 2.

**Answers unchanged.** With counting values, both implementations return the same minima as on plain ints, on
7 scaling instances and 300 random `generate()` instances.

**Closed forms**, computed from the instance alone; equality checked at every n listed:
- scan: Σ (r − l) over the queries, at n = 50..3200;
- sparse table: Σ_{j=1..K} (n − 2^j + 1) + n, K = ⌊log₂ n⌋, at 9 non-powers of two and at 2^11..2^17. On
  n = 2^K this is n log₂ n − n + log₂ n + 2.

**Scan.** Claim n², n = 200, 400, 600, 800, 1200, 1600, 2400, 3200 (unchanged).
- Counts: 29538, 121008, 268195, 481249, 1081149, 1921516, 4303139, 7680595, i.e. 0.7385–0.7563 · n².
- α = 1.001.
- Rivals: n log n 1.741, n² log n 0.931, n³ 0.668; all rejected.
- Diag 0.931 / 1.083, resolved.

**Sparse table.** Claim n log n, n = 2000, 4000, 8000, 16000, 32000, 64000, 128000 (unchanged).
- Counts: 19964, 43917, 95822, 207631, 447248, 958481, 2044946.
- α = 1.007; local slopes 1.0102 falling to 1.0051.
- Rivals: n 1.113, n log² n 0.920, n² 0.556; all rejected.
- Diag 0.920 / 1.113, resolved.
- On powers of two 2^11..2^17 (computed, not adopted): the leading term gives α 1.0074 and the exact form
  1.0000, with the same rival verdicts.

**Is the factor resolved?** Yes. The rival n gives α = 1.113 on the counts. The earlier timing fit gave 1.100
against n, inside its tolerance (`experiments/2026-10-07_rmq_probe.py`).

## 2. polynomial-multiplication-naive-vs-ntt: converted

**What is counted.** `CountingCoeff` is an int-like coefficient type that propagates through `+`, `-`, `*`
and `%`. It counts every multiplication with at least one input-derived operand.

**Answers unchanged.** Both implementations give the same coefficients as on plain ints, on 203 instances: 200
random, n ∈ {1, 2, 3, 5, 8, 9, 16, 17, 31, 64, 100}, plus n = 512, 1024, 2048
(`experiments/2026-10-06c_ntt_counts.py`).

**What the type sees.** A second, experiment-only type separates products whose two operands are both
input-derived from products with one plain-int operand:
- schoolbook: all n² products have two input-derived operands;
- NTT: only the 2n pointwise products have two input-derived operands (16 / 1024 / 8192 at n = 8 / 512 / 4096);
- every NTT butterfly product `a[k + half] * w` has a plain twiddle factor (96 / 15360 / 159744 of them).

**Not seen:**
- the twiddle updates `w = w * w_len % P`, one per butterfly;
- `pow()`;
- the first-stage butterflies, where `a[k + half]` is always a padding zero (a plain int): after bit reversal,
  the n input coefficients occupy the even positions of the size-2n array;
- all additions, subtractions and reductions mod p.

All of this is stated in the entry's caveats.

**Schoolbook.** Claim n², n = 100, 200, 300, 400, 600, 800.
- Counts: exactly n² (10000 … 640000). No scaling draw is 0, and the `if a:` skip of zero coefficients
  never triggers.
- α = 1.000.
- Rivals: n log n 1.697, n² log n 0.918; both rejected.
- Diag 0.918 / 1.098, resolved.

**NTT.** n = 512, 1024, 2048, 4096, 8192, 16384, powers of two, so the transform size is exactly 2n.
- Counts: 16384, 35840, 77824, 167936, 360448, 770048.
- These are exactly **3n·log₂n + 5n**, checked for n = 2^3..2^15. The parts:
  - (log₂(2n) − 1)·n per forward transform;
  - 2n pointwise products;
  - log₂(2n)·n butterfly products and 2n scalings in the inverse transform.
- Cost expression: the exact form `n*(3*log2(n) + 5)` (RL-062, decision D3). `time_complexity` still says
  Θ(n log n) and states the exact count next to it.
- α = 1.000.
- Rivals: n 1.111, n log² n 0.885, n² 0.555; all rejected.
- Diag 0.897 / 1.129, resolved.
- The leading term n log n on the same counts gives α = 0.9854 (near-miss list).

**Is the factor resolved?** Yes. The rival n gives α = 1.111. The earlier timing fit could not separate n log n
from n (RL-018).

## 3. minimum-spanning-tree-brute-vs-kruskal: converted (all three algorithms)

**The packed-key question (RL-018).** Kruskal sorts integer keys w·n² + u·n + v. If w is a `CountingWeight`,
the key is computed by `CountingWeight.__mul__` and `__add__`, so **the key itself is a `CountingWeight`**.
`sorted()` then calls its `__lt__` for every comparison (checked: the packed key's type is CountingWeight, and
its value equals the plain key). `__divmod__` returns plain ints, which the implementation uses as the weight
and as vertex indices. The packing therefore does not hide the sort from instrumentation.

**What is counted:** every comparison and every arithmetic operation (+, *, divmod) with an input weight as an
operand. This one rule is used for all three algorithms (D5).
- With counting weights, all three implementations return the same MST weight as on plain ints, on 200 random
  `generate()` instances (n ≤ 7, ties included).
- Kruskal and Prim also agree on 4 scaling instances (n = 20..200).
- Script: `experiments/2026-10-06c_mst_counts.py`.

**Kruskal.** Claim n² log n, n = 50, 100, 200, 400, 800 (unchanged).

Breakdown, cross-checked by `sorted()` on the same keys and by a replay of the scan on plain ints. Here
m = n(n−1)/2, and the counts are for Python 3.14.2:

| n | total | sort comparisons | 2m additions + m multiplications | divmods (scanned keys) | total / (m log₂ m) |
|---|---|---|---|---|---|
| 50 | 14811 | 11056 | 3675 | 80 | 1.1786 |
| 100 | 69526 | 54453 | 14850 | 223 | 1.1444 |
| 200 | 319007 | 258696 | 59700 | 611 | 1.1225 |
| 400 | 1438399 | 1197374 | 239400 | 1625 | 1.1069 |
| 800 | 6400007 | 5437640 | 958800 | 3567 | 1.0951 |

- α = 0.998 (0.9980; local slopes 0.9979–0.9980).
- Rivals: n² 1.094, n² log² n 0.917, n³ 0.729; all rejected.
- Diag 0.917 / 1.094, resolved.
- On n = 100..1200 (computed, not adopted): α 0.9979, rivals 1.0842 / 0.9243 / 0.7228.

**Prim.** Claim n², same n.
- Count: 2(n − r − 1) comparisons in round r = 1..n−1, (n−1)(n−2) in total, plus n−1 additions. That is
  exactly (n−1)²: 2401, 9801, 39601, 159201, 638401.
- α = 1.007 against n² (1.0000 against (n−1)²).
- Rivals: n² log n 0.918, n³ 0.671; both rejected.
- Diag 0.918 / 1.114, resolved.

**Enumeration.** Claim n·C(m, n−1), n = 4..7 (unchanged).
- Count: exactly (n−1)·C(m, n−1) additions + (n^(n−2) − 1) comparisons. There is one `total < best` per
  connected subset after the first, and by Cayley's formula there are n^(n−2) connected subsets.
- Counts: 75, 964, 16310, 342390.
- α = 0.995.
- Rivals: C(m, n−1) 1.065, n²·C(m, n−1) 0.934, n^(n−2) 1.210; all rejected.
- Diag 0.957 / 1.036, resolved.

**Not counted:** the union-find work (plain vertex ints) and the enumeration's depth-first search.

**Cross-version (Kruskal).**
- Python 3.12.10 gives 14766, 69346, 318302, 1435596, 6388918, which is 0.17–0.30% fewer.
- The breakdown under 3.12 shows that the whole difference is in the sort comparisons (11011 / 54273 / 257991 /
  1194571 / 5426551). The independent `sorted()` replay agrees within each version.
- α = 0.9982; rivals 1.0943 / 0.9175 / 0.7295. Same verdicts; CI (3.12) passes too.
- The cause inside CPython's sort was not investigated.

**Is the factor resolved?** Yes. Kruskal's counts reject n² (α 1.094), and Prim's counts reject n² log n
(α 0.918). This is the log factor between the two algorithms of the secondary T3 tag.

## 4. fibonacci-naive-vs-dp (fast doubling): not converted

**Why not, precisely** (`experiments/2026-10-06c_value_reach_probe.py`, Part A):
- **The input reaches the code only through `bin(n)`.** n was replaced by `Tracer`, an int-like type that
  propagates through every arithmetic, bitwise and shift operator and logs every dunder call. The complete log
  of a fast-doubling run is `{'__index__': 1}` for n = 2^8, 2^16, 2^32, 2^64, 2^128 and 12345. The results are
  unchanged, although the loop runs bit_length(n) = 9 … 129 times. That single call is `bin(n)` converting its
  argument.
- **An int subclass gets no hook at all.** Its overridden `__index__` is called 0 times, both by `bin()`
  directly and by fast doubling: CPython accepts int subclasses without calling `__index__`.
- **The loop is invisible.** It iterates over the characters of the `str` that `bin()` builds in C. All
  arithmetic is on `a` and `b`, which start from the literals 0 and 1, and on the module constant `MASK`. No
  operand is ever instance-derived.
- **The bottom-up DP** likewise logs only `{'__index__': 1}` (from `range(n)`, n = 1000).

**Instance-derived count available:** one call, constant in n. Any "count" reported for this algorithm would
have to be computed from n by the harness, i.e. assumed rather than measured.
**Entry:** the reason is added to `verification.method` and the README. The timing fit stays, with no level
change.

## 5. chromatic-number-subset-dp-vs-inclusion-exclusion: not converted (F4 stays open)

**Why not, precisely** (Part A of the same script, on the validator-seeded G(n, 0.8) instances). Here n and
every edge endpoint are `Tracer`s.
- **Inclusion–exclusion**, n = 8 / 10 / 12 / 14 (χ = 4 / 6 / 7 / 8): 964 / 3358 / 12719 / 49768 logged
  operations in total.
  - `__invert__` and `__rand__` occur exactly 2ⁿ − 1 times each: the tabulation pass, `S & ~closed[v]`, where
    `closed[v]` is instance-derived through the edges.
  - `__index__` occurs 357 / 1171 / 4316 / 16697 times, mostly the `a[...]` lookups of that pass.
  - The rest is O(n²) setup (`__or__`, `__ror__`, `__rlshift__`), plus one `__add__` (`n + 1`), one `__mod__`
    and two `__eq__`.
  - **None of the χ·2ⁿ round multiplications appears** (1024 / 6144 / 28672 / 131072 of them).
  - The reason: in `x = p[S] * a[S]` and `total ± x`, the list `p` comes from the literal `[1] * size` and `a`
    from `[0] * size`. The entries of `a` are list entries + list entries + literal 1, and the indices S come
    from `range(size)`. `range()` converts its bound once in C, so the instance reaches the rounds only as one
    `__index__` call per round, `range(size)`.
- **Subset DP** (n = 8 / 10 / 12):
  - `__gt__` occurs exactly 2ⁿ − 1 times. That is the first `c < best` of each S, while `best` is still the
    instrumented n, and it is reflected to `Tracer.__gt__`.
  - `__and__` = `__bool__` occur 44 / 75 / 113 times, and `__index__` 98 / 142 / 214 times.
  - None of the 3ⁿ − 2ⁿ submask steps appears (6305 / 58025 / 527345 of them). They run on plain ints from
    `range()`.

So **arithmetic on instrumented integers cannot see the inclusion–exclusion rounds**. Counting them with 2ⁿ as
a rival, as the brief asked, is not possible with the implementation unchanged.
**Entry:** the reason is added to `verification.method` and the README. The timing fits stay, and the factor n
is still unresolved.

**What exact counts would show if they could be taken** (Part B, a prototype of a *different* method, not
adopted, D1). `sys.monitoring` counted executions of single source lines of the unchanged code:
- `x = p[S] * a[S]` runs exactly χ(G)·2ⁿ times on n = 10..18, with χ = 6, 7, 7, 8, 8, 8, 8, 9, 10.
- The subset DP's `T = (T - 1) & S` runs exactly 3ⁿ − 2ⁿ times on n = 7..10.

Fits of the χ·2ⁿ counts, for information only:

| Fit | α | Verdict at 0.03 |
|---|---|---|
| χ·2ⁿ vs n·2ⁿ | 0.9714 | passes, by a margin of 0.0014 |
| χ·2ⁿ vs 2ⁿ | 1.0737 | rejected |
| χ·2ⁿ vs n²·2ⁿ | 0.8869 | rejected |
| χ·2ⁿ vs 3ⁿ | 0.6774 | rejected |

- The diagnostic is **not** resolved (0.9371 / 1.0084), and the local slopes range from 0.889 to 1.076 as χ
  grows in steps.
- The implementation's own operation total, (2χ + 2)·2ⁿ, is a formula evaluated with the measured χ, not a
  count. It gives α 0.9638 against n·2ⁿ, which would **fail** at 0.03, and 1.0652 against 2ⁿ.
  *Correction (2026-10-07): the exact total is (2χ + 2)·2ⁿ − 2 (RESEARCH_LOG.md RL-091).*
- **Consequence for F4:** the "factor n" is really a factor χ(G). On this instance family χ/n stays between 0.500 and
  0.636 over n = 10..18 (6/10 … 10/18; 8/16 at the minimum), without settling. So even exact counts would separate n·2ⁿ from 2ⁿ only narrowly here. The obstacle
  is the instance family as well as the measurement method.

## 6. Near-misses (with numbers)

- **NTT leading term:** α = 0.9854 against n log n (|α − 1| = 0.0146; local slopes 0.980–0.989). It passes at
  0.03 but uses half the tolerance, so the exact form 3n·log₂n + 5n (α 1.0000) was adopted instead.
- **Kruskal is the only version-dependent series:** 0.17–0.30% between 3.12.10 and 3.14.2, with α 0.9982 vs
  0.9980.
  - A future CPython sort change could move these counts further.
  - A uniform change of level leaves α untouched. α would move by 0.03 only if count/(n² log n) drifted by
    about 20% between n = 50 and n = 800 (cost span 437.4; 437.4^0.03 = 1.20). The measured version
    difference drifts by 0.13 percentage points (0.30% → 0.17%).
- **MST enumeration has the tightest margins:** smallest rival distance 0.0652 (rival C(m, n−1), α 1.065) and
  smallest diagnostic distance 0.0363 (0.957 / 1.036). n stops at 7, because n = 8 means 1 184 040 subsets
  (8 288 280 counted additions). n = 8 was not tried.
- **Chromatic prototype:** χ·2ⁿ against n·2ⁿ passes by 0.0014 only (α 0.9714), and the docstring formula would
  fail (0.9638); see §5.
- **RMQ scan:** smallest rival distance 0.0688 (n² log n, α 0.931). Local slopes 0.981–1.017, from the query
  draws.
- **A guess corrected before use.** The first draft of the RMQ script's docstring, written before the run,
  guessed α 1.022 for the sparse table's leading term. The run gave 1.0073. The docstring now carries the
  measured value and notes the correction.
- **An unsupported sentence removed.** A draft sentence in the Fibonacci entry claimed that timing cannot tell
  log n from log² n. For cost = log n the validator's diagnostic is not computable, because cost/log n is
  constant, so there was no evidence for the sentence, and it was deleted before validation.

## 7. Decision log

**D1. Value instrumentation only; line-execution counting prototyped, not adopted.**
- RL-047 defines count-based V2 as instrumentation through the harness, with the count coming from instrumented
  values.
- `sys.monitoring` line counts are also harness-side and leave the implementations unchanged, but they count
  *source-line executions*, not operations on data. They also need a process-wide monitoring hook that the
  harness would switch on in `generate_scaling` and off in `reported_cost`; if the implementation raises
  in between, the hook stays on. And they require CPython ≥ 3.12.
- Adopting them is a methodology change. The prototype is kept as evidence
  (Part B).
- **Deciding evidence:** the counts are exact (bit_length(n), χ·2ⁿ, 3ⁿ − 2ⁿ), so the method works. Whether it
  is sanctioned is not for this agent to decide.

**D2. One tolerance, 0.03, for all 7 fits.**
- Window [0.0073, 0.0652).
- Rule from the previous round: at least 2 × the largest deviation (0.0146) and at most half the smallest
  rival distance (0.0326). 0.03 satisfies both and matches the previous 17 fits.
- **Alternative considered:** 0.02, Strassen's tolerance. It would also pass every fit and reject every rival,
  with a 0.0127 margin on the sparse table. It was rejected for consistency with RL-057.

**D3. Leading term or exact form.**
- **Rule:** keep the leading term when |α − 1| < tol/3 = 0.01; otherwise use the exact closed form (RL-062),
  if there is one.
- NTT, 0.0146: exact form `n*(3*log2(n) + 5)`. It holds on powers of two, which all the NTT n_values are.
- RMQ sparse table (0.0073), Prim (0.0066), enumeration (0.0046), Kruskal (0.0020) and the scan (0.0014): the
  leading term was kept.
  - The sparse table's exact form needs ⌊log₂ n⌋, which the cost grammar cannot express on the unchanged,
    non-power-of-two n.
  - Kruskal has no closed form, because the sort comparisons depend on the data.

**D4. n_values unchanged in all 7 fits.**
- The leading terms already dominate: every |α − 1| ≤ 0.0073.
- With the old n_values the inputs are exactly the ones the timing fits used, so only the measured quantity
  changes.

**D5. MST: all three algorithms converted, with one counting rule.**
- `generate_scaling` is shared. Converting only Kruskal would have Prim and the enumeration timed on
  instrumented weights, which is a different program from the one timed before.
- Counting "every comparison and arithmetic operation with an input weight as an operand" is needed for the
  enumeration. Counting comparisons alone there would count only spanning trees (n^(n−2) − 1), not the
  subsets that dominate its cost.
- **Alternative considered:** sort comparisons only for Kruskal. It would give the same verdicts, since the
  sort is 74.6–85.0% of the total, but would need a per-algorithm rule.

**D6. Kruskal's count includes comparisons inside `sorted()`, although they depend on the Python version.**
- The previous round dropped `sorted()` comparisons for closest pair, because a version-independent
  alternative existed (multiplications, RL-057 D7).
- Here the sort *is* the log factor, and no version-independent alternative exists with the implementation
  unchanged.
- **Deciding evidence:** the measured dependence (0.17–0.30%) changes no verdict, and CI's 3.12 passes.

**D7. Rivals.**
- Each fit names the other algorithm's cost.
- Log-factor neighbours:
  - n and n log² n for n log n claims;
  - n² log n for n² claims;
  - n² and n² log² n for Kruskal.
- n³ as a coarse upper rival for RMQ scan, Kruskal and Prim.
- Factor-n neighbours C(m, n−1) and n²·C(m, n−1) for the enumeration, plus n^(n−2), the spanning-tree count
  alone.

**D8. NTT counts multiplications only**, as for Strassen and Karatsuba. The twiddle-factor products are not
visible, and the entry states this. The counted part is a fixed, exact closed form, so the fit is not
contaminated by what is missing.

**D9. Fibonacci and chromatic: no conversion and no level change**; the reason is documented in the entries.
Their timing fits still pass (`--scaling` run, pass/fail only).

**D10. No RESEARCH_LOG, ledger, index or git operations** (forbidden by the brief). `--record` would call git
and was not used.

## 8. Validation record (console, this session)

- `tools/validate.py pairs/range-minimum-queries-naive-vs-sparse-table --scaling -v`: OK. α values as in §1.
- `tools/validate.py pairs/polynomial-multiplication-naive-vs-ntt --scaling -v`: OK. α values as in §2.
- `tools/validate.py pairs/minimum-spanning-tree-brute-vs-kruskal --scaling -v`: OK. α values as in §3.
- `tools/validate.py pairs/fibonacci-naive-vs-dp pairs/chromatic-number-subset-dp-vs-inclusion-exclusion --scaling -v`:
  2/2 OK. These are timing fits; no timing is reported.
- Final combined run, `tools/validate.py <all 5 entries> --scaling -v`: 5/5 OK (exit 0). The 7 count fits
  printed the same α, rival and diagnostic values as above.
- `tools/validate.py --static`: 62/62 OK (exit 0).
- `python -m unittest discover -s tests`: 110 tests OK.

## 9. Open ideas

*Forward-looking content is not published (RL-086).*

## 10. Files

New:
- `experiments/2026-10-06c_rmq_counts.py`
- `experiments/2026-10-06c_ntt_counts.py`
- `experiments/2026-10-06c_mst_counts.py`
- `experiments/2026-10-06c_value_reach_probe.py`
- `experiments/2026-10-06c_count_v2_summary.py`
- this report.

Edited:
- `harness.py`, `entry.json` and `README.md` of range-minimum-queries-naive-vs-sparse-table,
  polynomial-multiplication-naive-vs-ntt and minimum-spanning-tree-brute-vs-kruskal;
- `entry.json` and `README.md` of fibonacci-naive-vs-dp and chromatic-number-subset-dp-vs-inclusion-exclusion
  (documentation only; their harnesses are untouched).

No file under `implementations/` was edited.
