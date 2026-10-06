# Comparison sorting: insertion sort vs merge sort

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Return a sorted copy of a list of n integers. The input must not be modified.

| Algorithm | Time | Implementation |
|---|---|---|
| Insertion sort | Θ(n + inversions): Θ(n²) worst case and on random input | [insertion_sort.py](implementations/insertion_sort.py) |
| Merge sort | Θ(n log n) on every input | [merge_sort.py](implementations/merge_sort.py) |

**Why it's a pair.** Each element move in insertion sort removes exactly one inversion, and a random list has
about n²/4 of them. Merge sort's divide and conquer needs only log₂ n levels of linear merging.

**Lower bound.** Any comparison sort needs log₂(n!) = n log₂ n − O(n) comparisons, in the worst case and on
average, and therefore in expectation for randomized comparison sorts too (Knuth §5.3.1, plus Yao's principle).
Merge sort is optimal in this model. Integer sorting outside it (radix sort, Han–Thorup) can be faster.

**Verification.** V1: agreement with each other and with `sorted()` (oracle only), with no input mutation.
V2 on uniformly random lists: insertion sort (average case) fits n², and merge sort fits n log n. At the
default tolerance a plain-n fit would also pass for merge sort, so the log factor itself is not isolated.

**Sources.** Knuth, TAOCP Vol. 3 (2nd ed.), §5.2.1, §5.2.4, §5.3.1. CLRS (3rd ed.), ch. 2 and §8.1.
