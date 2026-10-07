# Proofs: string matching, naive vs KMP

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its two matchers, from first principles and from the code in this folder. Sections 1 to 4
prove the exact comparison counts and the KMP comparison bounds, for every size of their domains. Sections 5 to 11
prove the rest: the correctness of both matchers (the failure function and the scan of KMP), the worst case of the
naive matcher, KMP's Θ(n + m) on every input, the optimality caveat, and the expected cost of the naive matcher on
random text. Each proof is followed by the deterministic scripts or tests that check it and the ranges they check; a
check covers only those ranges, the proofs cover the general statements. Citations give credit; they are never part
of a proof. The KMP proofs of sections 2, 3, 6, 7 and 8 also cover the identical code in
`pairs/multi-pattern-matching-naive-vs-aho-corasick/implementations/kmp_each.py`.

## Counting convention

`harness.py`, class `CountingChar`: `__eq__` and `__ne__` each add 1 to the module counter `_comparisons`
(`_comparisons += 1`) and then compare the wrapped characters. No other operation counts. `generate_scaling`
builds both strings as tuples of `CountingChar` and sets `_comparisons = 0`; `reported_cost(output)` returns
`_comparisons`. Both implementations compare two characters of these tuples, so Python calls the left operand's
`__eq__` or `__ne__` once per comparison: every character comparison counts exactly 1. Index arithmetic, `len()`
and the tests `j < m`, `k > 0`, `q > 0`, `q == m` are on plain ints and are not counted.

**Scaling instance.** `generate_scaling(n, rng)` sets m = n // 2, T = aⁿ and P = `"a" * (m - 1) + "b"`. For
m ≥ 1 this is P = a^(m−1)b of length m. (For n ≤ 1, m = 0 and Python's `"a" * (-1)` is empty, so P = b has length
1; no count below is stated for n = 1.)

## 1. Naive matching: (n − m + 1)m

**Statement.** On every input with n ≥ m ≥ 1, `count_naive` makes at most (n − m + 1)m comparisons. On
T = aⁿ, P = a^(m−1)b (m ≥ 1, n ≥ m − 1) it makes exactly (n − m + 1)m. On the scaling instance this is
(n − m + 1)m with m = n // 2, for n = 0 and every n ≥ 2; the values listed in `entry.json` (10100 at n = 200, …,
2561600 at n = 3200) are this formula.

**Proof.** `count_naive` runs the `while` loop once for each of the n − m + 1 alignments `i` (none if
n − m + 1 ≤ 0). The loop compares `text[i + j] == pattern[j]` only while `j < m`, so it makes at most m
comparisons per alignment: at most (n − m + 1)m in all. On T = aⁿ, P = a^(m−1)b every alignment compares
P[0..m−2] = a with a (true, m − 1 comparisons) and then P[m−1] = b with a (false, 1 comparison), so it makes
exactly m. For n ≥ m − 1 the number of alignments is n − m + 1 ≥ 0, which gives (n − m + 1)m. On the scaling
instance with n ≥ 2 we have m = n // 2 ≥ 1 and n ≥ m − 1, so the count is (n − m + 1)m; at n = 0 there is no
alignment and both sides are 0.

**Check.** At the V2 sizes n = 200, 400, 800, 1600, 3200: `experiments/2026-10-07b_count_v2_apsp_strings.py`.
`experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "KMP-entry naive (n-m+1)m, m=n//2":
n = 0..40 and the V2 sizes (n = 1 reported as outside the domain). `experiments/2026-10-07_count_proof_checks.py`,
group `strings`, line "naive (n-m+1)m on a^n, a^(m-1)b": m = 1..30, n = m − 1..m + 40; line
"naive <= (n-m+1)m": 3000 seeded random pairs, n = 0..60, m = 1..12.

## 2. KMP failure table: 3m − 6

**Statement.** `_failure(P)` makes at most 3(m − 1) comparisons on every pattern of length m ≥ 1, and exactly
3m − 6 on P = a^(m−1)b for every m ≥ 3.

**Proof of the bound.** fail[j] ≤ j for every j: fail[0] = 0, and fail[q] is the value of k at the end of
iteration q, where k ≤ q − 1 at the start of iteration q (k starts at 0, rises by at most 1 per iteration, and
`k = fail[k - 1]` never raises it). In iteration q every true `while` test `pattern[q] != pattern[k]` is followed
by `k = fail[k - 1] ≤ k − 1`, so it lowers k by at least 1; at most one `while` test is false; and the `if` test
runs once. Over the m − 1 iterations k rises by at most m − 1 in total and never goes below 0, so there are at most
m − 1 true `while` tests, and the total is at most (m − 1) + (m − 1) + (m − 1) = 3(m − 1).

**Proof of 3m − 6.** P[0..m−2] = a and P[m−1] = b. By induction, after iteration q (1 ≤ q ≤ m − 2), k = q and
fail[q] = q:
- q = 1: k = 0, so `k > 0` is false and the `while` test makes no comparison; `pattern[1] == pattern[0]` is
  a = a, true (1 comparison); k = 1.
- 2 ≤ q ≤ m − 2: k = q − 1 ≥ 1; `pattern[q] != pattern[k]` is a ≠ a, false (1); `pattern[q] == pattern[k]` is
  true (1); k = q. Cost 2.

Iteration q = m − 1: k = m − 2 ≥ 1, fail[j] = j for 1 ≤ j ≤ m − 2 and fail[0] = 0. Each `while` test compares
b with a, which is true (1 comparison), and sets k = fail[k − 1] = k − 1. This happens for k = m − 2, …, 1, that
is m − 2 times; at k = 0 the test `k > 0` stops the loop without a comparison. Then `pattern[m-1] == pattern[0]`
is b = a, false (1). Total: 1 + 2(m − 3) + (m − 2) + 1 = 3m − 6.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "KMP failure table 3M-6 (M>=3;
1 at M=2; 0 at M=1)": the patterns of n = 0..40 and of the V2 sizes 3000, 10000, 30000, 100000, 300000.
`experiments/2026-10-07_count_proof_checks.py`, group `strings`, line "KMP failure table 3m-6 on a^(m-1)b":
m = 3..30; line "KMP failure table <= 3(m-1)": 3000 seeded random pairs, n = 0..60, m = 1..12.

## 3. KMP scan: 3n − m

**Statement.** The scan loop of `count_kmp` makes at most 3n comparisons on every input, and exactly 3n − m on
T = aⁿ, P = a^(m−1)b for every m ≥ 3 and n ≥ m − 1.

**Proof of the bound.** q starts at 0. Per text character the `if` test runs once and at most one `while` test is
false. Every true `while` test is followed by `q = fail[q - 1] ≤ q − 1` (fail[j] ≤ j, section 2). q rises only in
the `if` branch, by at most 1 per character, so over n characters there are at most n true `while` tests. Total at
most 3n. (The reset `q = fail[q - 1]` after a full match only lowers q further.)

**Proof of 3n − m.** The failure table of P = a^(m−1)b is fail[j] = j for 0 ≤ j ≤ m − 2 (section 2).
- Character 1: q = 0, the `while` test stops at `q > 0` without a comparison; `c == pattern[0]` is a = a (1);
  q = 1.
- Characters 2, …, m − 1: before character t, q = t − 1 ∈ [1, m − 2]; `c != pattern[q]` is a ≠ a, false (1);
  `c == pattern[q]` is true (1); q = t. Cost 2 each. After character m − 1, q = m − 1.
- Every later character: q = m − 1; `c != pattern[m-1]` is a ≠ b, true (1), q = fail[m − 2] = m − 2 ≥ 1;
  `c != pattern[m-2]` is false (1); `c == pattern[m-2]` is true (1); q = m − 1 again. Cost 3 each.

q never reaches m, so the branch `q == m` (plain ints) never runs. With n ≥ m − 1 characters the total is
1 + 2(m − 2) + 3(n − m + 1) = 3n − m.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `strings`, line "KMP scan 3n-M (n>=6)":
n = 6..40 and the V2 sizes. `experiments/2026-10-07_count_proof_checks.py`, group `strings`, line
"KMP scan 3n-m on a^n, a^(m-1)b": m = 3..30, n = m − 1..m + 40; line "KMP scan <= 3n": 3000 seeded random pairs,
n = 0..60, m = 1..12.

## 4. KMP total on the scaling instance: 3n + 2m − 6

**Statement.** On the scaling instance (m = n // 2) `count_kmp` makes exactly 3n + 2m − 6 comparisons for every
n ≥ 6, that is 4n − 6 for even n and 4n − 7 for odd n; the values listed in `entry.json` (11994 at n = 3000, …,
1199994 at n = 300000) are this formula.

**Proof.** For n ≥ 6, m = n // 2 ≥ 3 and n ≥ m − 1, so sections 2 and 3 apply: (3m − 6) + (3n − m) = 3n + 2m − 6.
For even n, m = n/2 gives 4n − 6; for odd n, m = (n − 1)/2 gives 4n − 7.

**Outside the domain** (the entry claims nothing there): for n ≤ 3 the pattern is P = b, the failure table makes
no comparison and the scan one per character (`c == pattern[0]` is false, q stays 0): n in all. For n = 4, 5 the
pattern is P = ab: the failure table makes 1 comparison; the scan makes 1 for the first character and 2 for each
later one (`a != b` true, q = fail[0] = 0, then `a == a`): 2n in all. The entry's V2 sizes and its shape grid
[6, 30] lie in n ≥ 6.

**Check.** At the V2 sizes n = 3000, 10000, 30000, 100000, 300000:
`experiments/2026-10-07b_count_v2_apsp_strings.py`. `experiments/2026-10-07_closed_form_checks.py`, group
`strings`, lines "KMP 3n+2m-6, m=n//2" and "KMP 4n-6-[n odd] (corrected form, n>=6)": n = 0..40 and the V2 sizes
(n ≤ 5 reported as outside the domain); line "KMP small-n forms: n (n<=3), 2n (n=4,5)": n = 0..40.

## Conventions for sections 5 to 11

T is the text (length n), P the pattern (length m ≥ 1); s[:k] is the prefix of length k and s[i:] the suffix from
position i. A *border* of a string s is a string that is both a proper prefix and a suffix of s (the empty string is
a border of every non-empty s); π(s) is the length of the longest border. An occurrence of P *ends at* position t if
T[t − m + 1 .. t] = P; occurrences correspond one to one to their end positions, so counting end positions counts the
positions i of `problem_statement`, overlapping ones included.

Cost model: character comparisons as counted by `CountingChar` (section "Counting convention"), and for time the
unit-cost model with O(1) per executed line and O(k) to build a list of k entries.

## 5. Naive matching: correctness and the worst case

**Statement** (`algorithms[0].correctness`, `time_complexity`, `space_complexity`; `relationship`; `naive.py`
docstring). `count_naive` returns the number of occurrences. Its worst case over the inputs with given n and m is
exactly max(n − m + 1, 0)·m comparisons, which is Θ(nm) when m ≤ cn for a constant c < 1 and Θ(n²) for m = n // 2. It
uses O(1) extra words.

**Proof.** The loop tries every alignment i = 0, …, n − m and counts it iff the `while` loop reaches j = m, i.e. iff
T[i + j] = P[j] for all j < m. Section 1 shows the bound (n − m + 1)m for n ≥ m and the exact value (n − m + 1)m on
T = aⁿ, P = a^(m−1)b for n ≥ m − 1; for m > n the range of alignments is empty and nothing is compared, which matches
max(n − m + 1, 0)·m. If m ≤ cn with c < 1, then
n − m + 1 ≥ (1 − c)n, so (n − m + 1)m ≥ (1 − c)nm. For m = n // 2, (n − m + 1)m ≥ (n/2)(n − 1)/2. Besides the input the
function keeps n, m, `count`, i and j. ∎

**Check.** `tests/test_proofs_kmp.py`, `test_correctness` (all texts over {a, b} of length at most 8 with all
patterns of length 1..4, and 1000 seeded random pairs over {a, b, c}): the count equals the direct count.
`test_naive_space`: every local variable is an integer or part of the input (all pairs over {a, b} with n ≤ 6,
m ≤ 3). The bound and the exact worst case: section 1.

## 6. The KMP failure function

**Statement** (`algorithms[1].idea`; `kmp.py` docstring). `_failure(P)` returns fail with fail[q] = π(P[:q + 1]) for
q = 0, …, m − 1.

**Lemma 6.1 (border chain).** For a non-empty string s, the border lengths of s are exactly π(s), π(s[:π(s)]),
π applied again, …, down to 0.

*Proof.* Each listed value is a border length of s, because a border of a border of s is a border of s. Conversely let
b be a border length of s with b < π(s). Both s[:b] and s[:π(s)] are suffixes of s, the first shorter, so s[:b] is a
suffix of s[:π(s)]; it is also a prefix of it, so b is a border length of s[:π(s)], and by induction on the length it
appears in the chain of s[:π(s)]. ∎

**Lemma 6.2 (extension).** For a string s and a character c, b ≥ 1 is a border length of sc iff b − 1 is a border
length of s (including b − 1 = 0) and s[b − 1] = c.

*Proof.* For 1 ≤ b ≤ |s|, (sc)[:b] = s[:b − 1]s[b − 1] and the suffix of sc of length b is (the suffix of s of length
b − 1) followed by c. They are equal iff s[:b − 1] is a suffix of s, i.e. a border (b − 1 < |s|), and s[b − 1] = c. ∎

**Proof of the statement.** fail[0] = 0 = π(P[:1]). Assume that at the start of iteration q (1 ≤ q ≤ m − 1),
k = fail[q − 1] = π(P[:q]) (true for q = 1, since k starts at 0, and maintained because the iteration ends with
fail[q] = k). By Lemma 6.2, π(P[:q + 1]) = 1 + max{b : b a border length of P[:q] with P[b] = P[q]}, or 0 if there is
no such b. The `while` loop runs through the border lengths of P[:q] from the largest down, since
`k = fail[k - 1]` = π(P[:k]) is the next one (Lemma 6.1), and stops at the first k with P[q] = P[k] or at k = 0; then
the `if` test adds 1 iff P[q] = P[k]. So fail[q] = π(P[:q + 1]). ∎

**Check.** `test_failure_function`: fail[q] equals the longest proper border computed by brute force, for every
pattern over {a, b} of length at most 10 and over {a, b, c} of length at most 6.

## 7. KMP: correctness of the scan

**Statement** (`algorithms[1].correctness`; `kmp.py` docstring). `count_kmp` returns the number of occurrences. More
precisely, after the `if` test for text character t, q is the largest l ≤ m such that P[:l] is a suffix of T[:t + 1];
and at the end of the iteration for t, q is the largest l ≤ m − 1 with that property.

**Proof.** Write q_t for the value of q at the end of the iteration for character t (q_{−1} = 0, the value before the
first character), and assume q_{t−1} = max{l ≤ m − 1 : P[:l] is a suffix of T[:t]}. A prefix P[:l] with l ≥ 1 is a
suffix of T[:t + 1] iff P[:l − 1] is a suffix of T[:t] and P[l − 1] = T[t]. The lengths l − 1 ≤ m − 1 with P[:l − 1] a
suffix of T[:t] are q_{t−1} and the border lengths of P[:q_{t−1}]: a shorter such prefix is a suffix of P[:q_{t−1}]
(both are suffixes of T[:t]) and a prefix of it, hence a border, and conversely a border of P[:q_{t−1}] is a suffix of
T[:t]. By Lemma 6.1 these are q_{t−1}, then the values reached by `q = fail[q - 1]` (only 0 when q_{t−1} = 0). The
`while` loop runs through them from the largest down and stops at the first q with T[t] = P[q] (or at 0), and the `if`
test adds 1 iff T[t] = P[q] (q ≤ m − 1, so P[q] exists). So after the `if` test, q = max{l ≤ m : P[:l] is a suffix of
T[:t + 1]} = q′. If q′ = m, P ends at t: `count` grows by 1 and q becomes fail[m − 1] = π(P); the prefixes P[:l] with l
< m that are suffixes of T[:t + 1] are then exactly the borders of P (both are suffixes, the shorter one a prefix of P),
so q_t = π(P) is the largest of them. If q′ < m, no occurrence ends at t and q_t = q′. Hence `count` grows exactly at
the end positions of occurrences. ∎

The method is Knuth, Morris and Pratt's (1977); the proof above is this project's. It contains the statement in
`algorithms[1].correctness`: after a mismatch the scan keeps the longest border of the matched part, and no alignment
in between can match, because a matching alignment would give a longer suffix of the text that is a prefix of P.

**Check.** `test_correctness` (the pairs of section 5): the count equals the direct count. `test_scan_state`: at the
line after the `if` test, q equals the largest l ≤ m with P[:l] a suffix of the text read, for every text over {a, b}
of length at most 7 and every pattern of length 1..4.

## 8. KMP: Θ(n + m) on every input, the parts, space

**Statement** (`algorithms[1].time_complexity`, `space_complexity`; `kmp.py` docstring; `relationship`). On every
input the failure table makes between m − 1 and 3(m − 1) comparisons and the scan between n and 3n, so KMP makes
between n + m − 1 and 3n + 3m − 3 comparisons and runs in Θ(n + m) time; Θ(n) when m = Θ(n). The bounds 3n and
3(m − 1) are tight up to lower-order terms (3n − m and 3m − 6 on T = aⁿ, P = a^(m−1)b). The failure table uses Θ(m)
space.

**Proof.** The upper bounds are sections 2 and 3; their tightness is the exact counts there. Lower bounds: each of the
m − 1 iterations of `_failure` makes the `if` comparison, and each of the n characters of the scan makes the `if`
comparison. Time: the work is O(1) per comparison and per loop iteration, plus building `fail` (m entries), so it is
Θ(n + m) (the loops have m − 1 and n iterations). If m = Θ(n), then n + m = Θ(n). `fail` has m entries. ∎

**Check.** `test_comparison_bounds`: all pairs over {a, b} with n ≤ 8 and m ≤ 6, and 1000 seeded random pairs over
{a, b, c} (n ≤ 60, m ≤ 12): failure-table comparisons in [m − 1, 3(m − 1)] and scan comparisons in [n, 3n] (the scan
count is the total minus a separate count of `_failure`). `test_space`: `fail` has m entries (all patterns over
{a, b} of length 1..8). The tight cases: section 2 and 3 checks.

## 9. KMP is optimal up to a constant factor for m ≤ n (caveat)

**Statement** (`caveats`). For every n and every m ≤ n, on T = aⁿ and P = a^m every algorithm that is always correct
and accesses the text only by reading characters must read all n text characters; so its worst case over the inputs
with these n and m is at least n ≥ (n + m)/2, and KMP's O(n + m) is optimal up to a constant factor on the class
m ≤ n. (The caveat's example P = a is the case m = 1.)

**Proof.** The count on aⁿ is n − m + 1. Changing text position i to b removes every alignment that covers i, and at
least one alignment covers i (since m ≤ n), so the count drops. If an algorithm, deterministic or using random bits,
did not read position i in some run on aⁿ, the same run on the changed text reads the same characters and gives the
same output, which is wrong for one of the two texts. ∎

**Check.** `test_adversary`: for 1 ≤ m ≤ n ≤ 12, the count of a^m in aⁿ is n − m + 1 and drops when any single
character is changed to b (and KMP returns the right count on every changed text).

## 10. The naive matcher on random text (caveat)

**Statement** (`caveats`; `README.md`). On a uniformly random text of length n over σ ≥ 2 letters, for a pattern of
length m whose letters lie in the alphabet, the naive matcher makes on average exactly
max(n − m + 1, 0)·Σ_{j<m} σ^(−j) comparisons, at most max(n − m + 1, 0)·σ/(σ − 1) ≤ 2n: O(n), much less than its worst
case. (If some pattern letter is not in the alphabet, the average is smaller.)

**Proof.** In one alignment the (j + 1)-st comparison happens iff the first j text characters of the alignment equal
P[0..j − 1], which has probability σ^(−j) (independent uniform characters; probability 0 for j ≥ 1 if a needed letter
is missing). By linearity of expectation an alignment costs Σ_{j<m} σ^(−j) < σ/(σ − 1) ≤ 2 on average, and there are
max(n − m + 1, 0) alignments. ∎

**Check.** `test_naive_expected_cost`: summing the counted comparisons over all texts, the average equals the formula
exactly (σ = 2, n = 0..8, patterns of length 1..4; σ = 3, n = 0..5, length 1..3), and is at most 2n.

## 11. The remaining claims

- *Relationship.* The naive worst case is Θ(max(n − m + 1, 0)·m) and KMP is Θ(n + m) on every input (sections 5 and
  8); with m = n // 2 this is Θ(n²) against Θ(n). The naive matcher re-reads up to m − 1 text characters after a
  mismatch (the next alignment starts one position later); KMP's `for c in text` reads each text character once.
- *The V1 oracle (`harness.py`, `check`).* It counts with `str.find`, restarting one position after each match, so
  it finds every position i with T[i..i + m − 1] = P once, overlapping ones included.
- *Measured, not proved:* the fit values α, the tolerance discussion, the V1 agreement and the agreement of the
  implementations on tuples and strings are results of the recorded runs (`tools/validate.py --scaling`,
  `experiments/2026-10-07b_count_v2_apsp_strings.py`).
