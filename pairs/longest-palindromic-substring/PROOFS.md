# Proofs: longest palindromic substring

This file proves every claim that this entry makes about its problem and its algorithms (in `entry.json`,
`README.md` and the docstrings and comments of the code): the correctness of the three algorithms, every stated
time and space bound (worst case, every input, and expectation on random strings), every exact comparison count on
its family, the lower bound in `relationship`, the soundness of the V1 oracle, and the remark on the radius arrays.
The entry cites no literature as background. Each proof is followed by the deterministic tests that check its
computable facts and the ranges they check. A check covers only those ranges; the proofs cover the general statements.

## Conventions

s is a string of length n, s[a..b] its substring from position a to b (empty if b < a). s[a..b] is a palindrome iff
s[a + t] = s[b − t] for 0 ≤ t ≤ b − a; empty and one-character strings are palindromes.

*Nesting.* For a ≤ b, s[a..b] is a palindrome iff s[a] = s[b] and s[a + 1..b − 1] is a palindrome. So around a fixed
centre the palindromes form an initial segment of radii. For a character centre i, write d1[i] for the largest k ≥ 1
with s[i − k + 1..i + k − 1] a palindrome (length 2k − 1); for the gap before position i (1 ≤ i < n; also i = 0),
d2[i] for the largest k ≥ 0 with s[i − k..i + k − 1] a palindrome (length 2k). Every palindrome s[a..b] has exactly
one centre: the character (a + b)/2 if its length is odd, the gap before (a + b + 1)/2 if it is even.

*Counting.* A comparison is one evaluation of `==` between two characters of s; the code compares characters only
this way. The tests count comparisons on the unchanged code by passing a list of instrumented characters (the code
uses only `len`, indexing and `==`), which also record the two positions and the outcome.

## 1. Brute force: comparison counts and bounds

**Statement.** (a) On aⁿ, `lps_brute` makes exactly Σ_{L=1..n} (n − L + 1)⌊L/2⌋ comparisons, which is
n³/12 + O(n²); no input of length n needs more, so Θ(n³) is its worst case. (b) On every input it runs n(n + 1)/2
tests and makes at least n(n − 1)/2 comparisons: Ω(n²) on every input. (c) On a uniformly random string over an
alphabet of σ ≥ 2 letters its expected number of comparisons lies between n(n − 1)/2 and n(n − 1), so it costs Θ(n²)
in expectation (`caveats`, docstring).

**Proof.** The test of s[i..j] (length m = j − i + 1) compares the pairs (i + u, j − u) for u = 0, 1, … while
i + u < j − u and the previous comparisons succeeded: at most ⌊m/2⌋ comparisons, exactly ⌊m/2⌋ when s[i..j] is a
palindrome, and at least 1 when m ≥ 2. (a) On aⁿ every substring is a palindrome, and there are n − L + 1 substrings
of length L. Σ (n − L + 1)(L − 1)/2 ≤ Σ (n − L + 1)⌊L/2⌋ ≤ Σ (n − L + 1)L/2 = n(n + 1)(n + 2)/12, and the left sum is
n(n + 1)(n + 2)/12 − n(n + 1)/4. Every input makes at most ⌊m/2⌋ comparisons per test, so at most the aⁿ count.
(b) The two loops run the test for every pair i ≤ j; the n(n − 1)/2 tests of length ≥ 2 make at least one comparison
each. (c) In a test of length m ≥ 2, the t-th comparison is made only if the t − 1 earlier ones succeeded; these
compare disjoint pairs of distinct positions, so they are independent events of probability 1/σ ≤ 1/2 each, and the
t-th comparison is made with probability at most 2^(−(t−1)). So a test makes at most Σ_t 2^(−(t−1)) = 2 comparisons in
expectation, and at least 1. The time adds Θ(1) per test: Θ(n²).

**Check.** `tests/test_proofs_palindrome.py`, `WorstCaseCountTests` (aⁿ, n = 0..60); `EveryInputBoundTests` (at least
n(n − 1)/2 on every string over {a, b} of length ≤ 11 and over {a, b, c} of length ≤ 7, and on seeded strings with
n = 100); `ExpectationTests.test_brute` (exact expectation by enumeration, n = 1..10 over {a, b} and 1..7 over
{a, b, c}).

## 2. Expanding around centres: comparison counts and bounds

**Statement.** (a) `lps_expand` compares every pair of positions (lo, hi), lo ≤ hi, at most once, so it makes at
most n(n + 1)/2 comparisons on every input, and exactly n(n + 1)/2 = n²/2 + n/2 on aⁿ: Θ(n²) is its worst case.
(b) On every input it makes between n + R and 3n − 1 + R comparisons, where R = Σ_i (d1[i] − 1) + Σ_i d2[i] is the sum of
the maximal palindrome radii over all centres; with the 2n − 1 centres its time is Θ(n + R). (c) On a uniformly random
string over σ ≥ 2 letters its expected number of comparisons lies between n and 5n − 2: Θ(n) in expectation.

**Proof.** At centre c the code starts with lo = ⌊c/2⌋, hi = lo + (c mod 2) and compares pairs with lo + hi = c,
moving outwards; so a pair (lo, hi) can only be compared at centre lo + hi, once. (a) On aⁿ every comparison succeeds
and the expansion stops only at the string's ends, so every pair (lo, hi) with 0 ≤ lo ≤ hi < n is compared: n(n + 1)/2
comparisons. (b) At a character centre i the first comparison is s[i] with itself (it succeeds), then d1[i] − 1 more
succeed, and one more fails unless the expansion stopped at an end: between d1[i] and d1[i] + 1 comparisons. At the gap
centre before i: d2[i] successes and at most one failure. Summing over the n character and n − 1 gap centres gives the
bounds. (c) At a character centre, after the comparison of s[i] with itself, the r-th comparison of two distinct
positions is made only if the r − 1 before it succeeded; they compare disjoint pairs, independent events of
probability 1/σ ≤ 1/2, so it is made with probability at most 2^(−(r−1)): expected cost at most 1 + 2 = 3. A gap
centre costs at most 2. Total at most 3n + 2(n − 1) = 5n − 2, and at least n (one comparison per character centre).

**Check.** `tests/test_proofs_palindrome.py`, `WorstCaseCountTests` (aⁿ, n = 0..300); `EveryInputBoundTests` (no pair
compared twice, at most n(n + 1)/2, and between n + R and 3n − 1 + R, on every string over {a, b} of length ≤ 11 and
over {a, b, c} of length ≤ 7 (R from the definition) and on seeded strings n = 100, 400, 1000 (R by a direct
expansion written in the test));
`ExpectationTests.test_expand` (exact expectation by enumeration, n = 1..14 over {a, b} and 1..9 over {a, b, c}).

## 3. Manacher's algorithm computes the radii

**Statement** (`algorithms[2].correctness`). After the two scans of `lps_manacher`, the arrays `d1` and `d2` hold the
maximal radii d1[i] and d2[i] of every centre. Moreover (mirror property), if centre i lies inside the rightmost
palindrome s[l..r] found so far, the radius at i is at least min(radius at the mirror centre, r − i + 1), and it equals
the mirror's radius when the mirror's maximal palindrome ends strictly inside s[l..r].

**Proof.** *Expansion lemma (E).* The odd loop `while i − k ≥ 0 and i + k < n and s[i − k] == s[i + k]: k += 1`, started
at some k₀ with 1 ≤ k₀ ≤ d1[i], ends with k = d1[i]: it keeps k ≤ d1[i] (a successful comparison at k makes the window
of radius k + 1 a palindrome, by nesting), and at k = d1[i] the next window is not a palindrome, so either it leaves the
string (the loop stops without a comparison) or its end characters differ (the comparison fails). It makes
d1[i] − k₀ successful comparisons and at most one failed one. The same holds for the even loop with 0 ≤ k₀ ≤ d2[i].

*Mirror lemma (M).* Let s[l..r] be a palindrome and φ(x) = l + r − x. For x, y ∈ [l, r], s[x] = s[φ(x)], and s[x..y] is
a palindrome iff s[φ(y)..φ(x)] is: the conditions s[x + t] = s[y − t] and s[φ(y) + t] = s[φ(x) − t] are the same, since
φ(x + t) = φ(x) − t and φ(y − t) = φ(y) + t.

*Odd scan.* Invariant before iteration i: d1[j] is correct for j < i, and (l, r) = (0, −1) or (l, r) is the window
of the maximal palindrome of a centre j < i whose right end r = j + d1[j] − 1 is the largest among the centres before i.
If i > r, the loop starts at k₀ = 1 ≤ d1[i]. If i ≤ r, let j be the centre of s[l..r] (l + r = 2j, j < i) and
i′ = l + r − i the mirror centre; i′ < j < i and i′ ≥ l. The loop starts at k₀ = min(d1[i′], r − i + 1) ≥ 1. The
window W′ = [i′ − k₀ + 1, i′ + k₀ − 1] is a palindrome (k₀ ≤ d1[i′]) and lies in [l, r] (its left end is
≥ i′ − (r − i) = l, its right end ≤ i′ + r − i = l + 2r − 2i ≤ r because l + r = 2j ≤ 2i), so by (M) its mirror image
[i − k₀ + 1, i + k₀ − 1] is a palindrome: k₀ ≤ d1[i]. In both cases (E) gives d1[i]. The update
`if i + k − 1 > r` keeps the invariant. *Exactness clause.* If d1[i′] < r − i + 1 (the mirror's maximal palindrome
ends strictly inside s[l..r]), the positions i′ − k₀ and i′ + k₀ lie in [l, r], so s[i′ − k₀] ≠ s[i′ + k₀] (the radius at
i′ is maximal and the next window is inside the string); their mirror images are i + k₀ and i − k₀, so
s[i − k₀] ≠ s[i + k₀] and d1[i] = k₀ = d1[i′].

*Even scan.* Invariant as above with d2 and windows [j − d2[j], j + d2[j] − 1] (when d2[j] = 0 the window is empty, and
then every later i satisfies i > r). If i > r the loop starts at k₀ = 0. If i ≤ r, let j be the gap centre of s[l..r]
(l + r + 1 = 2j, j < i) and i′ = l + r − i + 1 the mirror gap: φ maps the positions i′ − 1, i′ to i, i − 1, and
i′ < j < i, i′ ≥ l + 1. The loop starts at k₀ = min(d2[i′], r − i + 1). W′ = [i′ − k₀, i′ + k₀ − 1] is a palindrome and
lies in [l, r] (left end ≥ i′ − (r − i + 1) = l, right end ≤ i′ + r − i = l + 2r − 2i + 1 ≤ r because l + r + 1 = 2j ≤ 2i),
and φ(W′) = [i − k₀, i + k₀ − 1], so k₀ ≤ d2[i]; (E) gives d2[i]. If d2[i′] < r − i + 1, the positions i′ − k₀ − 1 and
i′ + k₀ lie in [l, r], differ, and mirror to i + k₀ and i − k₀ − 1: d2[i] = d2[i′].

**Check.** `tests/test_proofs_palindrome.py`, `ManacherRadiusTests`: the unchanged function's `d1` and `d2`, read at its
return (`sys.settrace`), equal the radii computed from the definition on every string over {a, b} of length 1..10 and
over {a, b, c} of length 1..6, and on 12 seeded strings of length 50. V1.

## 4. Correctness of brute force and of expanding around centres

**Statement.** `lps_brute` and `lps_expand` return (L, i) with L the maximum length of a palindromic substring and i the
smallest start of one of length L ((0, 0) for the empty string).

**Proof.** Let L* be the maximum length and a* the least start of a palindrome of length L*. *Brute force.* The test of
s[i..j] ends with lo ≥ hi exactly when all its pairs matched, that is when s[i..j] is a palindrome. The loops visit the
pairs (i, j) with i increasing, and the result is replaced only by a strictly longer palindrome. Before (a*, a* + L* − 1)
no palindrome of length L* is visited (none starts before a*, and for i = a* the shorter ones come first), so that pair
replaces the result, and nothing later is strictly longer. *Expansion.* At each centre the loop keeps the window
s[lo + 1..hi − 1] a palindrome (at a character centre it starts by comparing s[i] with itself) and stops when the next
window leaves the string or its end characters differ, so by nesting it ends with the maximal palindrome of that centre,
of length hi − lo − 1 and start lo + 1. A palindrome of length L* is the maximal palindrome of its centre (no longer one
exists), so the candidates include (L*, a*), and no candidate is longer. For a fixed length L the start (c − L + 1)/2
increases with the centre c, so the first centre (in the scan order c = 0, 1, …) whose maximal palindrome has length L*
has start a*; the code replaces only on a strictly longer candidate, which keeps that one. For n = 0 no centre exists and
the result is (0, 0).

**Check.** `tests/test_proofs_palindrome.py`, `CorrectnessTests`: every string over {a, b} of length ≤ 12 and over
{a, b, c} of length ≤ 8, and seeded harness strings n = 20, 40, 80 (brute force), 150, 400, against an independent
search (longest first, then leftmost). V1 (n up to 80 / 1000 / 5000).

## 5. Manacher's comparison counts

**Statement.** (a) In each of the two scans at most n comparisons succeed and at most n fail; with the O(1) further work
per iteration and the final loop, `lps_manacher` takes Θ(n) time on every input (`time_complexity`, docstring). (b) On aⁿ
it makes exactly 2n − 3 comparisons for every n ≥ 2 (n − 2 in the odd-length scan and n − 1 in the even-length scan), all
successful, and none for n ≤ 1.

**Proof.** (a) A failed comparison ends the loop, so each iteration has at most one. For the successes, compare with the
increase Δ_i ≥ 0 of r during iteration i, using the cases of section 3. *Odd scan.* If i > r, the successes number
d1[i] − 1 and the new right end i + d1[i] − 1 ≥ r + 1 + (d1[i] − 1), so Δ_i ≥ successes + 1. If i ≤ r and
d1[i′] < r − i + 1, the first comparison fails (exactness clause) and Δ_i = 0. If i ≤ r and d1[i′] ≥ r − i + 1, the loop
starts at k₀ = r − i + 1 and ends with right end i + d1[i] − 1 = r + (d1[i] − k₀): Δ_i equals the number of successes. So
in every iteration the successes are at most Δ_i, and in all at most r_final − (−1) ≤ n. *Even scan.* If i > r, the
successes number d2[i]; if d2[i] ≥ 1 the new right end i + d2[i] − 1 ≥ r + d2[i] (as i − 1 ≥ r), so Δ_i ≥ successes. The
two cases with i ≤ r are as in the odd scan. So at most n successes. Each scan has n iterations of O(1) work besides the
comparisons, and so has the final loop: Θ(n).

(b) On aⁿ no comparison fails, d1[i] = min(i, n − 1 − i) + 1 and d2[i] = min(i, n − i), and in both scans the largest right
end is n − 1. By (a), the successes of a scan equal (n − 1) − (−1) minus the excess Σ (Δ_i − successes_i). The case
"i ≤ r with the mirror's palindrome strictly inside" would start with a failed comparison, so it does not occur on aⁿ;
in the other case with i ≤ r the excess is 0. So the excess is non-zero only in the case i > r: there it is i − r in the
odd scan and i − 1 − r in the even scan. *Odd scan:* i = 0 (r = −1) has
excess 1, and then r = 0; i = 1 (r = 0) has excess 1, and then r = d1[1] ≥ 1; for i ≥ 2 the centre i − 1 has right end
min(2i − 2, n − 1) ≥ i, so i ≤ r and there is no excess. Successes n − 2. *Even scan:* i = 0 has excess 0 (and leaves
r = −1, since d2[0] = 0); i = 1 has excess 1 and sets r = 1; i = 2 (if n ≥ 3) has excess 2 − 1 − 1 = 0; for i ≥ 3 the
centre i − 1 has right end min(2i − 3, n − 1) ≥ i, so no excess. Successes n − 1. For n = 1 the odd scan makes no
comparison (i + k = n at once) and neither does the even scan (i − k − 1 < 0); for n = 0 the function returns at once.

**Check.** `tests/test_proofs_palindrome.py`, `WorstCaseCountTests`: on aⁿ for n = 0..2000, all comparisons succeed, the
total is 2n − 3 (n ≥ 2) or 0, split n − 2 / n − 1 between the scans (an odd-scan comparison compares positions with an
even sum, an even-scan comparison positions with an odd sum); `EveryInputBoundTests`: per scan at most n successes and
at most n failures on every string over {a, b} of length ≤ 11 and over {a, b, c} of length ≤ 7, and on seeded strings
n = 100, 400, 1000, 5000. `experiments/2026-10-07_palindrome_probe.py` (instrumented copies of the code) prints the same
counts at n = 10, 40, 160, 320.

## 6. Correctness of Manacher's answer

**Statement.** `lps_manacher` returns (L, i) with L the maximum length of a palindromic substring and i the smallest
start of one of length L ((0, 0) for the empty string).

**Proof.** By section 3 the candidates (2 d1[i] − 1, i − d1[i] + 1) and (2 d2[i], i − d2[i]) are the maximal
palindromes of all centres, each a palindrome. As in section 4, the palindrome of length L* starting at a* is the maximal
palindrome of its centre, so (L*, a*) is a candidate, and no candidate is longer. The final loop keeps the longest
candidate and, among equally long ones, the smallest start (`length == best_len and start < best_start`). The initial
(0, 0) is replaced by the first character centre (length 1), and the empty even candidates never replace anything. For
n = 0 the function returns (0, 0).

**Check.** `tests/test_proofs_palindrome.py`, `CorrectnessTests` (as in section 4, Manacher on all of them). V1.

## 7. The radius arrays

**Statement** (`notes`). The radius arrays list every maximal palindrome, and Σ_i d1[i] + Σ_i d2[i] is the number of
palindromic substrings (pairs a ≤ b with s[a..b] a palindrome).

**Proof.** The maximal palindrome of each centre is read off its radius (section 3). Every palindromic substring has
exactly one centre and, by nesting, a radius k with 1 ≤ k ≤ d1[i] (odd length) or 1 ≤ k ≤ d2[i] (even length); conversely
each such pair (centre, k) gives a palindromic substring.

**Check.** `tests/test_proofs_palindrome.py`, `ManacherRadiusTests`: Σ d1 + Σ d2 of the unchanged function equals a
direct count, on the strings listed in section 3.

## 8. The linear lower bound

**Statement** (`relationship`). Θ(n) is optimal up to a constant factor: on aⁿ, changing any character other than the
middle one makes the whole string a non-palindrome, so a correct deterministic algorithm must read at least n − 1
characters (at least ⌈(n − 1)/2⌉ comparisons).

**Proof.** The answer on aⁿ is (n, 0). Let p be a position with p ≠ n − 1 − p (every position if n is even, every position
except (n − 1)/2 if n is odd). Changing s[p] to another letter b makes s[p] ≠ s[n − 1 − p], so the string is not a
palindrome and its answer has length < n. If a deterministic algorithm did not read position p on input aⁿ, it would see
the same characters on the changed string, run identically and output (n, 0) there: wrong. So it reads every such p:
n − 1 positions (n odd) or n (n even). A comparison reads two characters.

**Check.** `tests/test_proofs_palindrome.py`, `LowerBoundTests.test_adversary`: for n = 1..150, changing position p of aⁿ
changes the answer exactly when p is not the middle position.

## 9. The V1 oracle

**Statement** (`harness.py`, `verification.method`). The oracle accepts (L, i) iff it is the correct answer: s[i..i+L−1]
is a palindrome, no window of length L + 1 or L + 2 is one, and no palindrome of length L starts before i.

**Proof.** A palindrome of length M > L contains, by nesting, the palindrome obtained by removing t = ⌊(M − L − 1)/2⌋
characters from each end, of length M − 2t ∈ {L + 1, L + 2}. So "no window of length L + 1 or L + 2 is a palindrome" means
that L is the maximum (given that a palindrome of length L exists), and the last condition makes i the leftmost.

**Check.** `tests/test_proofs_palindrome.py`, `LowerBoundTests.test_trimming`: for every palindrome w over {a, b} of length
M ≤ 14 and every L < M, the centred trimming has length L + 1 or L + 2 and is a palindrome. The oracle controls of
`experiments/2026-10-07_oracle_controls.py` (108 of 108 wrong answers rejected).

## 10. Space bounds

**Statement.** Brute force and expanding around centres use O(1) words; Manacher's algorithm uses Θ(n).

**Proof.** The first two keep only the indices and the best pair. Manacher allocates `d1` and `d2` (n entries each, values
at most n) and O(1) variables; the arrays are needed in full by the final loop.

**Check.** `tests/test_proofs_palindrome.py`, `SpaceTests`: peak traced allocation at most 2048 bytes for brute force
(n = 20, 40, 80) and expansion (n = 250..2000); between 16n and 80n + 4096 bytes for Manacher (n = 10⁴, 2 · 10⁴, 4 · 10⁴, on
aⁿ and on seeded strings).

## 11. The classification and the caveats

**Statement.** (a) Θ(n³) → Θ(n²) → Θ(n), all worst case (`pair_type` T3), with aⁿ attaining the two upper bounds.
(b) On random strings brute force is Θ(n²) and expansion Θ(n) in expectation, so the pair concerns worst-case inputs.
(c) The returned position is the leftmost among the longest palindromes; returning the substring instead costs O(n) more.

**Proof.** (a) Sections 1 (a), 2 (a) and 5 (a). (b) Sections 1 (c) and 2 (c). (c) Sections 4 and 6; copying a substring of
length L ≤ n costs O(n).

**Check.** The tests listed in those sections. The V2 runs time the three algorithms on aⁿ (measured data).
