# Zeta transform (sums over subsets): submask enumeration vs Yates' method

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact addition counts with rivals)

ζf(S) = Σ over T ⊆ S of f(T), for every subset S of an n-element set (input: N = 2ⁿ values).

| Algorithm | Additions (counted, exact) | Time | Implementation |
|---|---|---|---|
| Submask enumeration | 3ⁿ | Θ(3ⁿ) = Θ(N^1.585) | [naive.py](implementations/naive.py) |
| Yates' method (fast zeta) | n·2ⁿ⁻¹ | Θ(n·2ⁿ) = Θ(N log N) | [yates.py](implementations/yates.py) |

**Why it's here.** One pass per element replaces enumerating every submask of every set. The zeta matrix is the
n-th Kronecker power of [[1,0],[1,1]], the same structure the fast Walsh–Hadamard transform exploits with
[[1,1],[1,−1]] (see [xor-convolution-naive-vs-walsh-hadamard](../xor-convolution-naive-vs-walsh-hadamard/)). It is
the building block of fast subset convolution (Björklund et al. 2007) and of many inclusion–exclusion algorithms.
The input has 2ⁿ entries, so both costs are polynomial in the input size (T3).

**Verification.** V1: both agree for n = 0..8, 10, 12 and pass an independent oracle that scans all masks with
T & ~S = 0 (every S for n ≤ 8, a seeded sample above). V2: an instrumented integer counts the additions of the
unchanged implementations; the counts are exactly 3ⁿ and n·2ⁿ⁻¹ for every n = 0..12. Both fits give α = 1.000 at
tolerance 0.02; rivals rejected: naive vs n·2ⁿ 1.315, n·3ⁿ 0.886, 4ⁿ 0.792; Yates vs 2ⁿ 1.161, n²·2ⁿ 0.877, 3ⁿ 0.733.
See `experiments/2026-10-07b_zeta_transform_counts.py`.

**Sources.** Björklund, Husfeldt, Kaski & Koivisto, STOC 2007, 67–74. (Yates 1937, the origin of the name, is a
book and was not checked.)
