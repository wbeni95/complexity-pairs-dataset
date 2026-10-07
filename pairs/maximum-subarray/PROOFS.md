# Proofs: maximum subarray sum, brute force vs running sums vs Kadane's scan

This file proves every claim of this entry (in `entry.json`, `README.md` and the docstrings of the code) from the
code in this folder: the correctness of the three algorithms, their exact loop counts on every input, the space
bounds, the facts in the caveats and notes, and the correctness and Θ(n log n) cost of the divide-and-conquer
oracle in `harness.py`. Statements about the literature are in the entry's `background` field. Timing fits are
measurements. Each section ends with the deterministic checks that re-run its computable facts and their ranges.

## Conventions

The input is a list a[0..n−1] of n ≥ 1 integers. S(i, j) = a[i] + … + a[j] for 0 ≤ i ≤ j < n, and
M = max S(i, j), the answer. As the entry's size measure states, arithmetic and comparisons on the values are
unit cost; with |a[k]| ≤ 100 (the harness range) every sum has absolute value at most 100n. An **element read**
is one evaluation of `a[index]`.

## 1. Brute force: correctness and the exact count n(n+1)(n+2)/6

**Statement.** `max_subarray_brute(a)` returns M. On every input of length n its innermost loop body runs exactly
n(n+1)(n+2)/6 times; the middle loop body runs n(n+1)/2 times; it reads exactly 1 + n(n+1)(n+2)/6 elements. Hence
its running time is Θ(n³) on every input.

**Proof.** The loops run over all pairs 0 ≤ i ≤ j ≤ n − 1, and for each pair the innermost loop sets
s = a[i] + … + a[j] = S(i, j). `best` starts at a[0] = S(0, 0), one of the candidates, and is replaced whenever
s > best, so at the end best = max S(i, j) = M. The loop bounds depend on n only. The innermost body runs
Σ_(0≤i≤j≤n−1) (j − i + 1) = Σ_(L=1..n) L (n + 1 − L) times (L = j − i + 1 takes the value L for n + 1 − L pairs),
and Σ L(n + 1 − L) = (n + 1) n(n + 1)/2 − n(n + 1)(2n + 1)/6 = n(n + 1)[3(n + 1) − (2n + 1)]/6 = n(n + 1)(n + 2)/6.
The only reads are a[0] once and a[k] once per innermost iteration. Each loop iteration costs O(1). ∎

**Check.** V1 (`python tools/validate.py pairs/maximum-subarray`): n = 1..10, 15, 20, 40, 60 against the
oracle of section 7. `tests/test_proofs_max_subarray.py`, `CountTests.test_brute_force_reads`: reads counted by a
list subclass for n = 1..60 on seeded inputs.

## 2. Running sums: correctness and the exact count n(n+1)/2

**Statement.** `max_subarray_quadratic(a)` returns M; its inner body runs exactly n(n+1)/2 times and it reads
exactly 1 + n(n+1)/2 elements on every input, so its time is Θ(n²) on every input.

**Proof.** For fixed i, after the inner iteration for j the variable s equals S(i, j): s = 0 before the first one,
and the iteration for j adds a[j] to S(i, j − 1). So the same candidates S(i, j) as in section 1 are compared with
best, which starts at S(0, 0). The inner body runs Σ_i (n − i) = n(n + 1)/2 times, reading a[j] once; plus the read
of a[0]. ∎

**Check.** V1: n ≤ 200. `tests/test_proofs_max_subarray.py`, `CountTests.test_running_sum_reads`: n = 1..200.

## 3. Kadane's scan: correctness and the exact count n − 1

**Statement.** `max_subarray_kadane(a)` returns M. Its loop runs exactly n − 1 times and it reads exactly n
elements on every input, so its time is Θ(n). Invariant: after the iteration for j (and initially, for j = 0),
`ending_here` = E_j := max_(0≤i≤j) S(i, j) and `best` = M_j := max_(0≤i≤l≤j) S(i, l).

**Proof.** Initially ending_here = best = a[0] = E_0 = M_0. Let j ≥ 1. A non-empty subarray ending at j is either
a[j] alone or a[i..j] with i ≤ j − 1, whose sum is S(i, j − 1) + a[j]; the largest of the latter is E_(j−1) + a[j].
So E_j = max(a[j], E_(j−1) + a[j]) = a[j] + max(0, E_(j−1)). The code sets ending_here to x = a[j] if
E_(j−1) < 0 and to E_(j−1) + x otherwise, which is exactly a[j] + max(0, E_(j−1)). A subarray of a[0..j] either
ends at j or lies in a[0..j−1], so M_j = max(M_(j−1), E_j), which is what the update of best computes. After the
last iteration best = M_(n−1) = M. The loop runs for j = 1..n−1, reading a[j] once each, plus the read of a[0];
each iteration costs O(1). ∎

**Check.** V1: n ≤ 1000. `tests/test_proofs_max_subarray.py`: `CountTests.test_kadane_reads` (n = 1..2000) and
`KadaneInvariantTests.test_invariant` (the values of `ending_here` and `best` after every iteration, read with
`sys.settrace`, equal E_j and M_j computed by brute force, on 300 seeded lists with n ≤ 30).

## 4. Space: O(1) words

**Statement.** Each of the three implementations uses O(1) words besides the input.

**Proof.** Each keeps a fixed set of integer variables (brute force: n, best, i, j, s, k; running sums: n, best, i,
s, j; Kadane: best, ending_here, j, x) and creates no list or other container (the `range` objects are constant
size). Every value is an index below n or a sum of at most n input values, which fits in one word of
O(log n + log max|a[k]|) bits. ∎

**Check.** `tests/test_proofs_max_subarray.py`, `SpaceTests.test_only_integer_locals`: traced with
`sys.settrace`, every local other than the input list is an int with absolute value at most 100n, and the number of
locals is at most 7, on seeded inputs with n = 1..60.

## 5. Caveats: the empty-subarray variant, and every element must be read

**Statement (a).** The variant that allows the empty subarray has answer max(0, M); it differs from M exactly when
every element is negative.

**Proof.** If some a[i] ≥ 0, then M ≥ S(i, i) ≥ 0 and max(0, M) = M. If every element is negative, every non-empty
sum is negative, so M < 0 = max(0, M). ∎

**Statement (b).** Every correct algorithm (deterministic, or randomized and always correct) reads every element
on every input, so it needs at least n reads and Kadane's scan is optimal up to a constant factor.

**Proof.** Suppose that on input a (on some run, for a randomized algorithm) the algorithm never reads a[i]. Let a′
equal a except a′[i] = V := 1 + Σ_k |a[k]|. On a′ the same run reads the same values and makes the same choices,
so it returns the same answer. But M(a) ≤ Σ_k |a[k]| < V ≤ M(a′), since the single element a′[i] is a candidate.
So the answer is wrong on a or on a′. ∎

**Check.** `tests/test_proofs_max_subarray.py`, `CaveatTests`: (a) every list with n ≤ 5 and values in [−3, 3];
(b) for every list with n ≤ 4 and values in [−2, 2] and every position i, raising a[i] to 1 + Σ|a[k]| changes M.

## 6. Relationship: a strict chain Θ(n³) → Θ(n²) → Θ(n)

**Statement.** All three solve the same problem; their running times are Θ(n³), Θ(n²) and Θ(n) on every input, so
each step is a strict asymptotic improvement. Their loop counts depend only on n, so random inputs are worst-case
inputs for these counts.

**Proof.** Sections 1–3: the counts are exact functions of n, independent of the values; the only data-dependent
work is the update of best, at most one assignment per loop iteration. ∎

## 7. The divide-and-conquer oracle in `harness.py`: correctness and Θ(n log n) reads

**Statement.** `_divide_and_conquer(a, lo, hi)` returns the largest sum of a non-empty subarray of a[lo:hi] for
every hi − lo ≥ 1. Its number of element reads T(m), m = hi − lo, satisfies T(1) = 1,
T(m) = m + T(⌊m/2⌋) + T(⌈m/2⌉), and m(⌊log₂ m⌋ + 1) ≤ T(m) ≤ m(⌈log₂ m⌉ + 1); it makes 2m − 1 calls. So it runs
in Θ(n log n) time.

**Proof.** *Correctness*, by induction on m. For m = 1 the only subarray is a[lo]. For m ≥ 2 let mid =
⌊(lo + hi)/2⌋, so lo < mid < hi. A subarray of a[lo:hi] lies in a[lo:mid], lies in a[mid:hi], or contains both
a[mid − 1] and a[mid]. The first two kinds are handled by the recursive calls (induction). A subarray of the third
kind is a[i..j] with lo ≤ i ≤ mid − 1 < mid ≤ j ≤ hi − 1, and its sum is S(i, mid − 1) + S(mid, j), where the two
parts can be chosen independently; the first loop computes left = max_i S(i, mid − 1) and the second
right = max_j S(mid, j), so left + right is the best sum of the third kind.

*Reads.* A call with m = 1 reads one element. A call with m ≥ 2 reads mid − lo elements in the first loop and
hi − mid in the second, m in total, then recurses on lengths ⌊m/2⌋ and ⌈m/2⌉. For m ≥ 2, with K = ⌈log₂ m⌉ and
F = ⌊log₂ m⌋: from 2^(K−1) < m ≤ 2^K, ⌈log₂⌈m/2⌉⌉ = K − 1, and from 2^F ≤ m < 2^(F+1), ⌊log₂⌊m/2⌋⌋ = F − 1. By
induction, T(m) ≤ m + ⌊m/2⌋ K + ⌈m/2⌉ K = m(K + 1) (both halves have ceiling-log at most K − 1), and
T(m) ≥ m + ⌊m/2⌋ F + ⌈m/2⌉ F = m(F + 1) (both halves have floor-log at least F − 1). The number of calls C(m)
satisfies C(1) = 1, C(m) = 1 + C(⌊m/2⌋) + C(⌈m/2⌉), whose solution is 2m − 1. Each call does O(1) work besides its
reads. ∎

**Check.** `tests/test_proofs_max_subarray.py`, `OracleTests`: reads counted with a list subclass equal the
recurrence and lie within the two bounds for n = 1..600, 1000, 1023, 1024, 1025, 2000; the oracle equals brute force
on 500 seeded lists with n ≤ 40.
