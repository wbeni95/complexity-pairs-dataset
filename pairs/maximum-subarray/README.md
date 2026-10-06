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

**Verification.** V1: the three agree with each other and with an independent oracle, the CLRS §4.1
divide-and-conquer algorithm (Θ(n log n)). V2: runtimes fit n³, n² and n. All three do the same work on
every input of length n.

**Sources.** Bentley, "Programming pearls: algorithm design techniques", CACM 27(9), 1984. CLRS (3rd ed.),
§4.1 and Exercise 4.1-5.
