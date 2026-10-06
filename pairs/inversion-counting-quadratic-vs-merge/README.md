# Counting inversions: all pairs vs merge sort

**Type:** T3 (poly → faster poly) · **Verification:** V2

| Algorithm | Time | Implementation |
|---|---|---|
| All pairs | Θ(n²) | [pairs_scan.py](implementations/pairs_scan.py) |
| Merge-sort counting | Θ(n log n) | [merge_count.py](implementations/merge_count.py) |

**Why it's a pair.** Cross inversions between two sorted halves can be counted in linear time while merging.

**Verification.** V1 against an independent Fenwick-tree oracle. V2 fits n² and n log n.

**Sources.** CLRS Problem 2-4. Knuth, TAOCP Vol. 3, §5.1.1.
