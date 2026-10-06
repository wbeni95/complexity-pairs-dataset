# Counting inversions: all pairs vs merge sort

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| All pairs | Θ(n²) | [pairs_scan.py](implementations/pairs_scan.py) |
| Merge-sort counting | Θ(n log n) | [merge_count.py](implementations/merge_count.py) |

**Why it's a pair.** Cross inversions between two sorted halves can be counted in linear time while merging.

**Verification.** V1 against an independent Fenwick-tree oracle. V2 counts **element comparisons exactly**
with an instrumented element type (`CountingKey`) on the same random inputs; the implementations are
unchanged. All pairs makes exactly n(n−1)/2 (α = 1.001 against n², n = 250..2000). Merge-sort counting makes
n log₂ n − c·n with c = 1.255–1.267 (α = 1.010 against n log n, n = 2000..64000). With tolerance 0.03,
every declared rival is rejected: n log n (α = 1.735) and n² log n (0.930) for all pairs; n (1.119),
n log² n (0.920) and n² (0.560) for merge-sort counting. So the log factor is resolved. Details:
`experiments/2026-10-07b_count_v2_inversions_lis.py` and `research/2026-10-07b_count_based_v2.md`.

**Sources.** CLRS Problem 2-4. Knuth, TAOCP Vol. 3, §5.1.1.
