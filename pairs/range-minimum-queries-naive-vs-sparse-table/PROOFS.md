# Proofs: range minimum queries, scan vs sparse table

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
every exact operation count on its domain, the properties of the scaling family, and the remarks in the caveats and
notes. Sections 1 and 2 prove the exact counts; sections 3 to 8 prove the rest. Statements about the literature
(further preprocessing schemes) are not claims of this entry: they are
listed under `background` in `entry.json`, with their sources, and are not proved here. Each proof is followed by the
deterministic scripts or tests that check its computable facts and the ranges they check. A check covers only those
ranges; the proofs cover the general statements.

## Counting convention

`harness.py`, class `CountingKey`: each of `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__`, `__ne__` adds 1 to the
module counter `_comparisons` and compares the wrapped values. `generate_scaling(n, rng)` draws the values and
q = n queries with `_scaling_draws`, wraps every value (not the query indices) in `CountingKey` and sets
`_comparisons = 0`; `reported_cost(output)` returns `_comparisons`. Index arithmetic and the `log2` table are on
plain ints and are not counted. A comparison of two `CountingKey` values counts exactly 1 (Python calls one rich
comparison method). The sparse table also uses the built-in `min` with two arguments: under CPython, `min(a, b)`
evaluates the single rich comparison `b < a` (there is no identity shortcut for `<`), so it counts exactly 1.

Every query (l, r) of every instance satisfies 0 ≤ l ≤ r < n (harness `_queries`), and there are q = n queries.

## 1. Scan: Σ (r − l)

**Statement.** On every instance, `rmq_naive` makes exactly Σ over the queries of (r − l) comparisons.

**Proof.** For a query (l, r) the loop `for i in range(l + 1, r + 1)` runs r − l times and evaluates `x < m` once
per iteration, with `x` a value of the instance; nothing else compares values (`m = values[l]` and `out.append`
do not compare). Summing over the queries gives the statement.

**Check.** `experiments/2026-10-06c_rmq_counts.py` (the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `sorting`, line "RMQ scan sum(r-l) (instance formula)": n = 1..39 and n = 200, 400, 600, 800, 1200, 1600.

## 2. Sparse table: Σ_{j=1..K} (n − 2^j + 1) + n, and n log₂n − n + log₂n + 2 on powers of two

**Statement.** On every instance with n ≥ 1 values and q = n queries, `rmq_sparse_table` makes exactly
Σ_{j=1..K} (n − 2^j + 1) + n comparisons, K = ⌊log₂ n⌋. When n = 2^K this equals n log₂n − n + log₂n + 2.

**Proof.** The `while (1 << j) <= n` loop builds level j for j = 1, …, K. Level j is a list comprehension over
`range(n - (1 << j) + 1)`, that is n − 2^j + 1 entries, each `min(prev[i], prev[i + half])` of two values of
the instance (level 0 is the list of values, and every later entry is one of them), so each entry costs exactly
one comparison. Each of the q = n queries then evaluates `a <= b` once on two table entries (1 comparison); the
`log2` table and the index computations are plain. Total Σ_{j=1..K}(n − 2^j + 1) + n.

For n = 2^K: Σ_{j=1..K}(n + 1) − Σ_{j=1..K} 2^j = K(n + 1) − (2^(K+1) − 2) = Kn + K − 2n + 2, and adding n gives
n log₂n − n + log₂n + 2. (At n = 1, K = 0: no level is built, one query, 1 = 0 − 1 + 0 + 2.)

**Check.** `experiments/2026-10-06c_rmq_counts.py` (the V2 sizes n = 2000, 4000, 8000, 16000, 64000, 128000, plus
n = 10, 100, 1000 and 2^11..2^17; the V2 size 32000 is checked by the next line).
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "RMQ sparse table sum_{j=1..K}(n-2^j+1)+n":
n = 1..69 and the V2 sizes 2000, 4000, 8000, 16000, 32000, 64000, 128000; line "RMQ sparse n log2 n - n + log2 n + 2
(n=2^K)": n = 1, 2, 4, 8, 16, 32, 64, 128, 1024 (and n = 3, 5, 6, 7, 2000 reported as outside the power-of-two
domain).

## 3. Correctness of the scan

**Statement.** For every instance, `rmq_naive` returns min(values[l..r]) for every query (l, r), 0 ≤ l ≤ r < n.

**Proof.** For a query, m starts as values[l] and, for i = l + 1, …, r, is replaced by values[i] when that is
smaller; so after step i, m = min(values[l..i]).

**Check.** `tests/test_proofs_rmq.py`, `CorrectnessTests`: n = 1..60, 100, 257, 1000, two value ranges, every query
for n ≤ 30 and the harness's mixed queries otherwise, against `min` of the slice. V1 (an independent segment tree).

## 4. Correctness of the sparse table

**Statement.** For every instance with n ≥ 1, `rmq_sparse_table` returns min(values[l..r]) for every query; for
n = 0 it returns the empty tuple (no query is possible).

**Proof.** *log2 table.* log2[1] = 0 and log2[L] = log2[⌊L/2⌋] + 1, so by induction log2[L] = ⌊log₂ L⌋ (for
2^k ≤ L < 2^(k+1), 2^(k−1) ≤ ⌊L/2⌋ < 2^k). *Levels.* Claim: `table[j][i]` = min(values[i .. i + 2^j − 1]) for
0 ≤ i ≤ n − 2^j. True for j = 0 (a copy of the values). Level j is built while 2^j ≤ n, with
`table[j][i] = min(prev[i], prev[i + 2^(j−1)])`; the window of length 2^j at i is the union of the windows of length
2^(j−1) at i and at i + 2^(j−1), both inside [0, n − 1] for i ≤ n − 2^j, and the minimum of a union is the minimum of
the two minima. *Queries.* For a query, k = log2[r − l + 1] = ⌊log₂(r − l + 1)⌋, so 2^k ≤ r − l + 1 < 2^(k+1). The
windows [l, l + 2^k − 1] and [r − 2^k + 1, r] lie in [l, r] (the first ends at or before r, the second starts at or
after l), and they cover it: the first ends at l + 2^k − 1 and the second starts at r − 2^k + 1 ≤ l + 2^k, because
r − l + 1 < 2^(k+1), so there is no gap between them. Their indices are valid table entries (l ≤ n − 2^k and
r − 2^k + 1 ≤ n − 2^k). The minimum over [l, r] is the smaller of the two window minima, because min is idempotent
(an element in the overlap counted twice does not change the minimum); `a if a <= b else b` returns it.

**Check.** `tests/test_proofs_rmq.py`, `TableInvariantTests`: from the unchanged function's local variables at its
return (via `sys.settrace`), n = 1..130, 1000, 1025: every level has n − 2^j + 1 entries equal to the window minima,
and `log2[L]` = ⌊log₂ L⌋. `CorrectnessTests` as in section 3. V1 and the oracle controls.

## 5. Time bounds and the scaling family

**Statement.** (a) The scan takes Θ(q + Σ (r − l + 1)) time on every instance; with queries of length O(1) it takes
Θ(n) for q = n (`caveats`), and on the scaling family Θ(n²). (b) On the scaling family every range is longer than
n/2 (q = n queries); for 4 | n the expected total scanned length Σ (r − l + 1) is exactly n (3n/4 + 1) and the
expected scan count Σ (r − l) is exactly 3n²/4. (The entry's figures "0.75 n² within 0.5% at n = 800, 1200, 1600" are
measured on the seeded instances, not proved.) (c) The sparse table takes Θ(n log n) preprocessing time and O(1)
time per query, Θ(n log n + q) in total on every instance with n ≥ 2, so Θ(n log n) for q = n.

**Proof.** (a) A query costs one assignment, r − l loop steps with one comparison each, and one append: Θ(r − l + 1).
With lengths O(1) and q = n the sum is Θ(n). (b) `_queries(n, rng, long_only=True)` draws l uniformly from
[0, max(1, ⌊n/4⌋)) and r uniformly from [⌊3n/4⌋, n). For n ≥ 4: l ≤ ⌊n/4⌋ − 1 ≤ n/4 − 1 and r ≥ ⌊3n/4⌋ ≥ (3n − 3)/4,
so r − l + 1 ≥ n/2 + 5/4 > n/2; for n = 1, 2, 3, l = 0 and r = n − 1, length n > n/2. Hence, for n ≥ 3, the scan
makes Σ (r − l) ≥ n (n/2 + 1/4) comparisons (for n = 3 each query has r − l = 2 ≥ 7/4), and at most n (n − 1) for
every n: Θ(n²). For 4 | n, E[l] = (n/4 − 1)/2 and
E[r] = (3n/4 + n − 1)/2, so E[r − l + 1] = 3n/4 + 1, and linearity of expectation over the n queries gives the
stated expectations. (c) The `log2` table costs Θ(n). Level j (1 ≤ j ≤ K = ⌊log₂ n⌋) has n − 2^j + 1 entries of O(1)
work each; Σ_{j=1..K} (n − 2^j + 1) is at most K (n + 1) and, since n − 2^j + 1 ≥ n − 2^(K−1) + 1 > n/2 for j ≤ K − 1,
at least (K − 1) n/2; so Θ(n log n) for n ≥ 2 (for n = 2, 3 a constant). A query does a table lookup of `log2`, two
index computations, two lookups and one comparison: O(1). No step depends on the values except the result of each
comparison.

**Check.** (a), (c) The exact counts of sections 1 and 2 (scripts listed there) and the V2 fits.
(b) `tests/test_proofs_rmq.py`, `ScalingFamilyTests`: every query longer than n/2 for n = 1..400 (the V2 seed scheme
and 3 more seeds per n), and the exact mean 3n/4 + 1 of r − l + 1 over all (l, r) pairs for n = 4, 8, …, 400. The
measured ratios: `experiments/2026-10-07_rmq_probe.py` (0.7475, 0.7531, 0.7496 at n = 800, 1200, 1600).

## 6. Space bounds

**Statement.** The scan uses O(1) space besides the output; the sparse table uses Θ(n log n) space.

**Proof.** Scan: the variables m, x, l, r, i, plus the output (the list `out` and its tuple copy, q entries each).
Sparse table: the table has Σ_{j=0..K} (n − 2^j + 1) = (K + 1)(n + 1) − 2^(K+1) + 1 entries, which is Θ(n log n) by the
bounds of section 5 (c), plus the `log2` table (n + 1 entries) and the output.

**Check.** `tests/test_proofs_rmq.py`, `TableInvariantTests` (the exact number of table entries, n = 1..130, 1000,
1025) and `SpaceTests`: scan peak at most 24 q + 4096 bytes (n = 1000..16000); sparse-table peak divided by n log₂ n
between 8 and 200 and varying by a factor of at most 1.5 over n = 2000..32000.

## 7. Other idempotent associative operations

**Statement** (`notes`). The sparse table answers range queries for any associative and idempotent operation (such
as max, gcd, bitwise and, bitwise or) in the same way, but not sums, because the two blocks would count the overlap
twice.

**Proof.** Let ∘ be associative with x ∘ x = x for all x, and write fold(I) for the ∘-product over a contiguous
range I in order. The level recursion is the same as in section 4 (fold of the union of two adjacent windows). For a
query, the two windows X and Y overlap in a non-empty range O (|X| + |Y| = 2^(k+1) > r − l + 1), and with
X = X′O, Y = OY′ as consecutive pieces, fold(X) ∘ fold(Y) = fold(X′) ∘ fold(O) ∘ fold(O) ∘ fold(Y′) =
fold(X′) ∘ fold(O) ∘ fold(Y′) = fold([l, r]) by associativity and idempotence. No commutativity is used. For +, the
array [1, 1, 1] and the query (0, 2) give the windows [0, 1] and [1, 2] and the answer 2 + 2 = 4 ≠ 3.

**Check.** `tests/test_proofs_rmq.py`, `IdempotentOperationTests`: the sparse table written with the operation as a
parameter (the same loops as the code) answers every query exactly for max, gcd, and, or on seeded arrays, n = 1..40;
with + it returns 4 on the counterexample.

## 8. Remarks in the caveats; the T3 classification

**Statement.** (a) With short queries (length O(1)) the scan costs Θ(n) and beats the sparse table's Θ(n log n)
preprocessing, so the pair is stated for q = n queries of length Θ(n). (b) With q queries in general, the totals are
Θ(n log n + q) for the sparse table and Θ(q + Σ (r − l + 1)) for the scan; so for q much larger than n log n the
sparse table costs Θ(q), and the comparison with the scan is decided by the query lengths. (c) For q = n long queries
the costs are Θ(n²) and Θ(n log n): both polynomial, the exponent drops (T3).

**Proof.** (a) Section 5 (a) and (c): Θ(n) = o(n log n). (b) Section 5 (a) and (c), which hold for every q.
(c) Section 5.

**Check.** (c) The V2 fits on exact counts.
