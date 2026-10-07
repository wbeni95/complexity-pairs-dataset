# Proofs: longest increasing subsequence

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of the three algorithms, every stated time and space
bound, every exact operation count on its domain, and the reduction used by the V1 oracle. Sections 1 to 3 prove the
exact counts; sections 4 to 10 prove the rest. Statements about the literature (the papers on random Young
tableaux, Fredman's analysis) are not claims of this entry: they are listed under `background` in `entry.json`,
with their sources, and are not proved here. Each proof is followed by the deterministic scripts or tests that check
its computable facts and the ranges they check. A check covers only those ranges; the proofs cover the general
statements.

## Counting convention

`harness.py`, class `CountingKey`: each of `__lt__`, `__le__`, `__gt__`, `__ge__`, `__eq__` and `__ne__` adds 1 to
the module counter `_comparisons` (`_comparisons += 1`) and then compares the wrapped integers. No other operation
counts. `generate_scaling` builds the list of `CountingKey` and then sets `_comparisons = 0`;
`reported_cost(output)` returns `_comparisons`. Every counted comparison in the code compares two elements of the
input list, so Python calls the left operand's method once and each counts exactly 1: `a[i] <= last` in
`lis_subsets` (`last` is an earlier element of `a`), `a[j] < ai` in `lis_quadratic`, `tails[mid] < x` in
`lis_patience` (`tails` holds elements of `a`). Not counted: `last is not None` (an identity test), the tests on
plain ints (`mask >> i & 1`, `L[j] + 1 > li`, `li > best`, `size > best`, `lo < hi`, `lo == len(tails)`), and the
list operations.

**Scaling instance.** `generate_scaling(n, rng)` returns x_1 < x_2 < … < x_n with x_1 = d_1 and
x_k = x_(k−1) + d_k, each gap d_k drawn from `rng.randint(1, 10)`: a strictly increasing list of n elements.

## 1. Subset enumeration: n·2^(n−1) − 2ⁿ + 1 comparisons and 2ⁿ·n inner steps

**Statement.** On every list of n ≥ 0 elements (in particular on the scaling instance), `lis_subsets` makes
exactly n·2^(n−1) − 2ⁿ + 1 comparisons, and its inner loop `for i in range(n)` runs exactly 2ⁿ·n times. The
values listed in `entry.json` (20481 at n = 12, …, 2097153 at n = 18) are this formula.

**Proof.** The outer loop runs over the 2ⁿ masks and the inner loop over all n positions for each mask; neither has
an early exit (`increasing = False` does not stop the loop): 2ⁿ·n inner steps. For a mask with s set bits, the
first chosen index finds `last is None`, so the `and` stops before the comparison; every later chosen index makes
the comparison `a[i] <= last` once. So the mask costs max(s − 1, 0), whatever the values. Summing,
Σ_{s=0..n} C(n, s)·max(s − 1, 0) = Σ_s C(n, s)(s − 1) + 1 = n·2^(n−1) − 2ⁿ + 1 (the term s = 0 contributes −1 to
the middle sum and 0 to the left one). At n = 0 both sides are 0. At n = 12: 12·2048 − 4096 + 1 = 20481; at
n = 18: 18·131072 − 262144 + 1 = 2097153.

**Check.** At the V2 sizes n = 12..16: `experiments/2026-10-07b_count_v2_inversions_lis.py` (it runs the code at
n = 10..16; for n = 17, 18 it evaluates the formula instead of running the code).
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "LIS subsets n2^(n-1)-2^n+1": n = 0..18
(all V2 sizes 12..18). `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "LIS subsets
n2^(n-1)-2^n+1 on other inputs": n = 0..12, five lists each (many ties, increasing, decreasing, constant, random);
line "LIS subsets inner steps 2^n n (line count)": n = 0..10.

## 2. Quadratic DP: n(n − 1)/2

**Statement.** On every list of n ≥ 0 elements, `lis_quadratic` makes exactly n(n − 1)/2 comparisons. The values
listed in `entry.json` (4950 at n = 100, …, 1279200 at n = 1600) are this formula.

**Proof.** For each i the inner loop runs over j = 0..i − 1 and evaluates `a[j] < ai` once (the second operand of
the `and` is on plain ints). So the count is Σ_{i=0..n−1} i = n(n − 1)/2. At n = 1600: 1600·1599/2 = 1279200.

**Check.** At the V2 sizes n = 100, 200, 400, 800, 1600: `experiments/2026-10-07b_count_v2_inversions_lis.py`.
`experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "LIS DP n(n-1)/2": n = 0..40, 100, 200, 400,
800, 1600. `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "LIS DP n(n-1)/2 on other
inputs": n = 0..60, five lists each.

## 3. Patience sorting on increasing input: Σ_{j=2..n} ⌊log₂ j⌋

**Statement.** On every strictly increasing list of n ≥ 0 elements (in particular on the scaling instance),
`lis_patience` makes exactly Σ_{j=2..n} ⌊log₂ j⌋ comparisons. For n ≥ 1 this equals (n + 1)K − 2^(K+1) + 2 with
K = ⌊log₂ n⌋. The values listed in `entry.json` (113631, 387248, 1468946, 4875732 at n = 10000, 30000, 100000,
300000) are this sum.

**Proof.** Before element x_(i+1) is read (i = 0..n − 1), `tails` holds x_1, …, x_i: true for i = 0, and since
x_(i+1) is larger than every entry, every probe `tails[mid] < x` is true, so the search ends with lo = len(tails)
and x is appended. With lo ≤ hi, `mid = (lo + hi) // 2` = lo + ⌊ℓ/2⌋ for the length ℓ = hi − lo, and a true probe
sets lo = mid + 1, which leaves the length ℓ − ⌊ℓ/2⌋ − 1 = ⌊(ℓ − 1)/2⌋. So a search over ℓ entries makes c(ℓ)
probes with c(0) = 0 and c(ℓ) = 1 + c(⌊(ℓ − 1)/2⌋). We show c(ℓ) = ⌊log₂(ℓ + 1)⌋ by induction: ⌊(ℓ − 1)/2⌋ + 1 =
⌊(ℓ + 1)/2⌋, and for every integer y ≥ 2, ⌊log₂⌊y/2⌋⌋ = ⌊log₂ y⌋ − 1 (if 2^k ≤ y < 2^(k+1), k ≥ 1, then
2^(k−1) ≤ ⌊y/2⌋ < 2^k); with y = ℓ + 1 this gives c(ℓ) = 1 + ⌊log₂(ℓ + 1)⌋ − 1. The total is
Σ_{i=0..n−1} ⌊log₂(i + 1)⌋ = Σ_{j=2..n} ⌊log₂ j⌋ (the term j = 1 is 0).

For the closed form, count for each k = 1..K the j ≤ n with ⌊log₂ j⌋ ≥ k, that is j ≥ 2^k: Σ_{j=1..n} ⌊log₂ j⌋ =
Σ_{k=1..K} (n − 2^k + 1) = K(n + 1) − 2^(K+1) + 2. At n = 10000, K = 13: 10001·13 − 16384 + 2 = 113631; at
n = 300000, K = 18: 300001·18 − 524288 + 2 = 4875732.

**Check.** At the V2 sizes n = 10000, 30000, 100000, 300000: `experiments/2026-10-07b_count_v2_inversions_lis.py`
(also n = 1000, 3000). `experiments/2026-10-07_closed_form_checks.py`, group `sorting`, line "LIS patience
sum_{j=2..n} floor(log2 j)": n = 0..69 and the V2 sizes. `experiments/2026-10-07_count_proof_checks.py`, group
`strings`, line "LIS patience sum floor(log2 j) on other strictly increasing inputs": n = 0..300, three gap ranges
each; line "LIS identity sum_{j<=n} floor(log2 j) = (n+1)K-2^(K+1)+2, and listed V2 values": n = 1..2000 and the
V2 sizes.

## 4. Correctness of the subset enumeration

**Statement.** For every list a, `lis_subsets(a)` returns the length of a longest strictly increasing subsequence
(0 for the empty list).

**Proof.** Subsequences correspond one to one to index subsets, that is masks. For a mask, the scan visits the chosen
indices in increasing order; `increasing` becomes False exactly when some chosen a[i] is ≤ the previously chosen
element, so it stays True iff the chosen subsequence is strictly increasing; `size` counts the chosen indices. `best`
is the largest size over the increasing masks (the empty mask gives 0).

**Check.** `tests/test_proofs_lis.py`, `CorrectnessTests.test_exhaustive`: every list of length ≤ 6 over {0, 1, 2, 3}
against an independent brute force. V1 (n ≤ 14, against the LCS oracle).

## 5. Correctness of the quadratic DP

**Statement.** For every list a, `lis_quadratic(a)` returns the length of a longest strictly increasing subsequence.

**Proof.** Claim: after iteration i, L[i] is the length of a longest strictly increasing subsequence ending at
position i. A subsequence ending at i is either a[i] alone or ends with a[j], a[i] for some j < i with a[j] < a[i], and
then its part ending at j is a strictly increasing subsequence ending at j, of length at most L[j] (induction);
conversely a longest subsequence ending at such a j extends by a[i]. The code sets
L[i] = max(1, max{L[j] + 1 : j < i, a[j] < a[i]}). Every increasing subsequence ends somewhere, so the answer is
max L (0 for n = 0), which `best` tracks. (Credit: CLRS, 3rd ed.)

**Check.** `tests/test_proofs_lis.py`, `CorrectnessTests`: every list of length ≤ 7 over {0, 1, 2, 3}, and agreement
with patience sorting on seeded lists up to n = 2000. V1.

## 6. Correctness of patience sorting

**Statement.** For every list a, `lis_patience(a)` returns the length of a longest strictly increasing subsequence.
Invariant: after reading a prefix P, `tails` has length LIS(P), tails[k] is the least last element of a strictly
increasing subsequence of P of length k + 1, and `tails` is strictly increasing.

**Proof.** For a prefix P write T_P(k) for the least last element of a strictly increasing subsequence of P of length
k + 1 (k < LIS(P)), and T_P(k) = +∞ for k ≥ LIS(P). *T_P is strictly increasing:* a subsequence of length k + 2 ending
at T_P(k + 1) has its first k + 1 elements increasing and ending below T_P(k + 1), so T_P(k) < T_P(k + 1).
*Binary search:* on a strictly increasing list, the loop keeps lo ≤ pos ≤ hi for pos = the first index with
tails[pos] ≥ x (len(tails) if there is none): a probe with tails[mid] < x shows pos > mid (all earlier entries are
smaller too), otherwise pos ≤ mid; it stops with lo = hi = pos. *Step:* let P′ = P followed by x. The strictly
increasing subsequences of P′ of length k + 1 are those of P and those ending with x, which exist iff k = 0 or some
increasing subsequence of P of length k ends below x, that is iff k = 0 or T_P(k − 1) < x. So
T_P′(k) = min(T_P(k), x) if k = 0 or T_P(k − 1) < x, and T_P′(k) = T_P(k) otherwise. With pos as above
(tails = T_P by the invariant): for k < pos, T_P(k) < x, so T_P′(k) = T_P(k); for k = pos, T_P(pos − 1) < x (or
pos = 0) and T_P(pos) ≥ x, so T_P′(pos) = x; for k > pos, T_P(k − 1) ≥ T_P(pos) ≥ x, so T_P′(k) = T_P(k). The code
writes x at position pos (appending when pos = len(tails)), which is exactly T_P′; LIS(P′) = LIS(P) + 1 iff
T_P(LIS(P) − 1) < x iff pos = len(tails). The result `len(tails)` is LIS(a). (Credit: for distinct elements `tails`
is the first row of Schensted's insertion tableau, Schensted 1961; CLRS, 3rd ed.)

**Check.** `tests/test_proofs_lis.py`, `PatienceInvariantTests`: the unchanged function's `tails`, read at its return
(`sys.settrace`), after every prefix of 3 seeded lists with many ties for each n = 1..60, equals the least last
elements computed independently from the DP lengths, and is strictly increasing. `CorrectnessTests` (every list of
length ≤ 7 over {0, 1, 2, 3}). V1.

## 7. Time bounds

**Statement.** (a) The subset enumeration takes Θ(2ⁿ n) time on every input. (b) The DP makes n(n − 1)/2
comparisons and takes Θ(n²) time on every input. (c) Patience sorting makes at most n (1 + log₂ L) comparisons and
takes O(n (1 + log L)) ≤ O(n log n) time (n ≥ 2), L the answer; on strictly increasing input it makes
Σ_{j=2..n} ⌊log₂ j⌋ ≥ n log₂ n − 3n comparisons, so Θ(n log n) is its worst case. (d) Its cost is not Θ(n log L) on
every input: n − L decreasing elements followed by L larger increasing ones (answer L + 1) cost exactly
(n − L − 1) + Σ_{j=2..L+1} ⌊log₂ j⌋ comparisons, Θ(n) for L = ⌊√n⌋, while n log₂ L grows like (n/2) log₂ n.
(e) The constants c in "n log₂ n − c n" of `verification.method` are (n log₂ n − count)/n for the exact count of
section 3: 1.9246, 1.9644, 1.9202, 1.9422 at n = 10000, 30000, 100000, 300000.

**Proof.** (a) Section 1: 2ⁿ n inner steps of O(1) work, no early exit. (b) Section 2, with O(1) work per pair and
O(n) outside the inner loop. (c) A probe of the binary search on ℓ ≥ 1 candidates leaves ⌊(ℓ − 1)/2⌋ (true probe) or
⌊ℓ/2⌋ (false probe) candidates, so a search makes at most c(ℓ) comparisons with c(0) = 0 and
c(ℓ) = 1 + c(⌊ℓ/2⌋), that is c(ℓ) = ⌊log₂ ℓ⌋ + 1 for ℓ ≥ 1. The length of `tails` never decreases and ends at L, so
each search is over at most L entries: at most n (⌊log₂ L⌋ + 1) comparisons, plus O(1) work per element. On increasing
input the count is the sum of section 3, (n + 1)K − 2^(K+1) + 2 with K = ⌊log₂ n⌋ > log₂ n − 1 and 2^(K+1) ≤ 2n, which
is at least (n + 1)(log₂ n − 1) − 2n + 2 ≥ n log₂ n − 3n. (d) The first element is appended without a comparison; each
later decreasing element meets `tails` = [previous element], makes one false comparison and replaces it: n − L − 1
comparisons. Each of the L larger elements is appended after a search over ℓ = 1, …, L entries with all probes true,
⌊log₂(ℓ + 1)⌋ comparisons (section 3). For L = ⌊√n⌋ the total is at most n + (L + 1) log₂(L + 1) = Θ(n).
(e) Arithmetic from the closed form of section 3.

**Check.** (a), (b) The scripts of sections 1 and 2. (c) `tests/test_proofs_lis.py`, `PatienceCostTests.test_upper_bound`:
counted comparisons at most n (1 + log₂ L) on seeded harness inputs, n = 1..300, 1000, 5000; the scripts of section 3.
(d) `test_not_theta_n_log_l`: the exact count and answer at n = 10000 and 40000 with L = ⌊√n⌋, and count < n log₂ L / 3.
(e) `test_listed_constants`.

## 8. The reduction used by the V1 oracle

**Statement** (`notes`, `harness.py`). The length of a longest strictly increasing subsequence of a equals the length
of a longest common subsequence of a and b = sorted(set(a)).

**Proof.** b is strictly increasing. A common subsequence of a and b is a subsequence of a whose values occur in b in
the same order, so it is strictly increasing. Conversely, a strictly increasing subsequence of a consists of distinct
values of a in increasing order, which is a subsequence of b. So the common subsequences are exactly the strictly
increasing subsequences of a.

**Check.** `tests/test_proofs_lis.py`, `CorrectnessTests.test_exhaustive`: LCS(a, sorted(set(a))) equals the brute
force on every list of length ≤ 7 over {0, 1, 2, 3}.

## 9. Space bounds

**Statement.** The subset enumeration uses O(1) words (the n-bit mask counted as one word, which needs n ≤ the word
length; O(n) bits in general), the DP Θ(n) and patience sorting Θ(L) ≤ Θ(n).

**Proof.** Subset enumeration: the variables mask, size, last, increasing, i and best. DP: the list L of n entries and
O(1) variables. Patience: `tails`, of length at most L and exactly L at the end, and O(1) variables.

**Check.** `tests/test_proofs_lis.py`, `SpaceTests`: subset enumeration peak at most 2048 bytes for n = 6..14; DP
peak between 8n and 40n + 4096 bytes for n = 200..3200 (3 seeded inputs each); patience between 8L and 16L + 4096
bytes on increasing input (L = n = 10⁴..8 · 10⁴) and at most 2048 bytes on a constant input of length 10⁵ (L = 1).

## 10. The T2 and T3 classifications

**Statement.** Θ(2ⁿ n) → Θ(n²) is an exponential-to-polynomial step on the same problem (T2), and Θ(n²) →
O(n log n) a polynomial improvement (secondary tag T3).

**Proof.** Section 7 (a)–(c): 2ⁿ n is exponential, n² and n log n are polynomial, and n log n = o(n²).

**Check.** The V2 fits on exact counts (rivals rejected).
