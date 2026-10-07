# Proofs: 3SUM, all triples vs sorting with two pointers

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code), from
the code in this folder: correctness, exact counts on no-instances, the worst-case time and the space of both
algorithms (sections 1–2), the separation (section 3) and that the timing instances are no-instances (section 4).
Each proof is followed by the deterministic tests that check it and the sizes they check it on; a check covers only
those sizes, the proofs cover every n. Section 5 lists the measured statements. The statements listed under
"Background" in `entry.json` are cited, not proved here; one of them is the machine-model assumption on the built-in
sort, which the upper time and space bounds of section 2 use and say so.

**Cost model.** Values are integers of magnitude O(n²) in the harness, so each addition, negation, comparison and
index operation costs Θ(1). A *no-instance* is an input with no i < j < k such that a_i + a_j + a_k = 0.

## 1. All triples: correctness, exact counts, Θ(n³) worst case, O(1) space

**Statement.** `three_sum_brute` answers correctly on every input. It computes `target` = −(a_i + a_j) once per pair
i < j and tests `values[k] == target` once per triple i < j < k up to the first hit; so on every no-instance it makes
exactly C(n, 2) target computations and C(n, 3) equality tests, and at most these numbers on every input. Its time is
Θ(n³) in the worst case and its extra space O(1).

**Proof.** The loops visit the triples i < j < k in lexicographic order, and a_i + a_j + a_k = 0 ⟺ a_k = −(a_i + a_j).
The function returns true at the first triple that passes and false after the last one; so it answers correctly, and
on a no-instance it never returns early: the middle loop body runs once per pair and the inner test once per triple.
No-instances exist for every n (for example any n positive values, section 4), so the worst case is Θ(n³): at most
C(n, 2) + C(n, 3) loop bodies of Θ(1) work on every input, exactly that many on no-instances. The locals are integers
and the target, so no container is created.

**Check.** `tests/test_proofs_three_sum.py`, `test_correct` (600 seeded inputs, n = 0..40: `harness.generate`, values
in [−5, 5] with many zeros and repeats, all-positive values, and values from {−8, −2, 0, 1, 4}; against an exhaustive
triple search, plus nine fixed small cases such as (0, 0, 0), (0, 0) and (3, 3, −6)), `test_counts` (400 seeded
inputs, n = 0..45, with an integer type that counts equality tests and negations: exactly C(n, 3) and C(n, 2) on
every no-instance, at most that otherwise) and `test_space` (40 inputs: the instrumented peak of
`tests/proof_space.py` is 0). The V1 battery (n = 0..60) compares with the hash-based oracle.

## 2. Sort + two pointers: correctness, (n − 1)(n − 2)/2 steps, Θ(n²) worst case, Θ(n) space

**Statement.** `three_sum_quadratic` answers correctly on every input. Its while loop runs at most n − 2 − i times for
each i, so at most (n − 1)(n − 2)/2 pointer steps in all for n ≥ 1 (none for n = 0, where the formula would give 1),
and exactly that many on every no-instance. Apart from the call of the built-in sort, its time is Θ(n²) in the worst
case (on every no-instance) and can be smaller on yes-instances. Assuming the built-in sort runs in O(n log n) time
with O(n) extra space (machine-model assumption, background; any O(n²) time bound would do), the total time is Θ(n²)
in the worst case and the extra space Θ(n): the sorted copy, n words, and the sort's working space.

**Proof.** Let a be the sorted list (non-decreasing); it holds the input values with their multiplicities, so a
solution exists in the input iff a[i] + a[j] + a[k] = 0 for some positions i < j < k of a.

*Correctness.* Fix i. Invariant at each test of `j < k`: no pair (j′, k′) with i < j′ < k′ ≤ n − 1 and j′ < j or
k′ > k has a[i] + a[j′] + a[k′] = 0. It holds at the start (j = i + 1, k = n − 1). Let s = a[i] + a[j] + a[k]. If
s = 0 the function returns true with i < j < k. If s < 0, then for every k′ with j < k′ ≤ k, a[i] + a[j] + a[k′] ≤ s
< 0, and pairs with k′ > k are excluded already; so no solution has j′ = j, and j += 1 keeps the invariant. If s > 0,
symmetrically for every j′ with j ≤ j′ < k, a[i] + a[j′] + a[k] ≥ s > 0, so no solution has k′ = k, and k −= 1 keeps
it. When the loop ends (j = k), every pair is excluded. So if a solution with first index i exists, the scan for i
returns true; every solution has i ≤ n − 3, so the loop over i finds one if there is one, and every true answer is a
solution.

*Counts.* Each step either returns or lowers k − j by 1; k − j starts at n − 2 − i and the loop stops at 0. So the
scan for i makes at most n − 2 − i steps, and exactly n − 2 − i on a no-instance (it never returns). Summing over
i = 0..n − 3 gives (n − 2) + … + 1 = (n − 1)(n − 2)/2 for n ≥ 1 (an empty sum, 0, for n = 1 and 2; for n = 0 the
loop over i is empty too). Each step costs Θ(1) (two additions, at most two comparisons).

*Time.* So the part after the sort is Θ(n²) on every no-instance and O(n²) on every input; it can stop after O(1)
steps on a yes-instance, which is why the bound is a worst case. The sort of the n values is one call of the
built-in, O(n log n) under the assumption; that is the only part of the upper bound not proved here. The lower bound
Ω(n²) on no-instances does not depend on it.

*Space.* The only container of the function's own code is `a`, n slots; the rest are integers. The built-in sort's
working space is O(n) under the assumption.

**Check.** `tests/test_proofs_three_sum.py`, `test_correct` (as in section 1), `test_counts` (exactly
(n − 1)(n − 2)/2 pointer steps on every no-instance and at most that otherwise, counted as the `s == 0` tests; the
sort uses only `<`) and `test_space` (the instrumented peak equals n).

## 3. The separation (T3)

All triples takes Θ(n³) time in the worst case (section 1), and sorting with two pointers Θ(n²) in the worst case
(section 2). The Ω(n²) worst case of the second algorithm and the Θ(n³) of the first are proved here; the O(n²) upper
bound of the second holds under the machine-model assumption on the built-in sort (background; in fact any O(n²)
bound for the sort would do), so the tag rests on that assumption.

## 4. The timing instances are no-instances

`generate_scaling` draws every value from [1, 10n²], so any three of them have a positive sum: every scaling instance
is a no-instance, and both algorithms run their full counts of sections 1 and 2 on it.

**Check.** `tests/test_proofs_three_sum.py`, `test_scaling_instances_are_no_instances` (n = 0, 1, 2, 3, 10, 40, 60,
80).

## 5. Measured statements (data, not theorems)

The V2 timing fits against n³ and n² are measurements of the running times on the scaling instances; sections 1–2
prove the step counts behind them.
