# Maximum subarray sum: brute force vs running sums vs Kadane

**Type:** T3 (poly → faster poly) · **Verification:** V2

**Problem.** Given n ≥ 1 integers (negatives allowed), find the largest sum of a non-empty contiguous subarray.

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force (sum every subarray) | Θ(n³) | [brute_force.py](implementations/brute_force.py) |
| Running sums | Θ(n²) | [running_sum.py](implementations/running_sum.py) |
| Kadane's linear scan | Θ(n) | [kadane.py](implementations/kadane.py) |

**Why it's a pair.** Every step removes recomputation. The quadratic algorithm extends each sum by one
element instead of re-adding it. Kadane keeps only the best subarray ending at the current position,
because any better subarray ending one step later must extend it.

**Verification.** V1: the three agree with each other and with an independent oracle, a
divide-and-conquer algorithm (Θ(n log n); CLRS). V2: runtimes fit n³, n² and n. The loop counts of all three depend
only on n, so random inputs are worst-case inputs for these counts.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: correctness of the three algorithms (Kadane's
invariant included), the exact counts n(n+1)(n+2)/6, n(n+1)/2 and n − 1 on every input, O(1) words of space, the
two caveats (the empty-subarray variant; every correct algorithm reads every element), and the correctness and
Θ(n log n) cost of the divide-and-conquer oracle. [tests/test_proofs_max_subarray.py](../../tests/test_proofs_max_subarray.py)
re-checks the computable facts.

**Sources.** Bentley, "Programming pearls: algorithm design techniques", CACM 27(9), 1984. CLRS (3rd ed.).
