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

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves that both algorithms are
correct, that merge-sort counting makes between (n/3)⌊log₂ n⌋ and n⌈log₂ n⌉ comparisons and runs in Θ(n log n) on
every input, and the space bounds; [tests/test_proofs_inversions.py](../../tests/test_proofs_inversions.py) checks
them on stated ranges.

**Sources.** CLRS (3rd ed.). Knuth, TAOCP Vol. 3. Chan & Pătraşcu, SODA 2010 (further literature, cited for context).
