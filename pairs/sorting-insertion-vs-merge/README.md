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
V2 counts **key comparisons exactly**: the harness wraps the random values in an instrumented key type
(`CountingKey`), and the implementations are unchanged. On uniformly random lists, insertion sort (average
case, mean of 3 seeded samples, n = 250..4000) makes 0.997–1.015 × n²/4 comparisons, α = 0.999 against n².
Merge sort (n = 1000..64000) makes n log₂ n − c·n with c = 1.25–1.27, α = 1.011 against n log n. With
tolerance 0.03 the counts reject every declared rival: n log n (α = 1.743) and n² log n (0.931) for insertion
sort; n (1.126), n log² n (0.918) and n² (0.563) for merge sort. So the log factor is resolved, which the
earlier timing fit could not do. Details: `experiments/2026-10-07b_count_v2_sorting.py` and
`research/2026-10-07b_count_based_v2.md`.

**Sources.** Knuth, TAOCP Vol. 3 (2nd ed.), §5.2.1, §5.2.4, §5.3.1. CLRS (3rd ed.), ch. 2 and §8.1.
