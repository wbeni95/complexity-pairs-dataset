# Proofs: longest common subsequence, subsequence enumeration vs dynamic programming

This file proves every claim that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): correctness of both, their time and space, and the separation. The
conditional lower bound in the entry's `background` field is cited from the literature and is not proved here. Each
section ends with the deterministic checks of its computable facts; a check covers only the inputs it states.

**Notation and cost model.** |a| = n, |b| = m. A string z is a *subsequence* of y if z = y[p_1] y[p_2] … y[p_k]
for some positions p_1 < … < p_k (an *embedding*). lcs(x, y) is the largest length of a common subsequence.
Machine model (elementary operations): character comparisons, integer operations (including `mask >> i & 1` and
`mask.bit_count()` for the word-sized masks used) and list indexing cost O(1); allocating a list of length t costs
Θ(t + 1). Machine-model assumption on a library routine (stated in the entry's `background` with its source, not
proved here): `b.find(c, j)` scans b from position j and costs O(1) plus the number of positions it examines:
j..p if the first occurrence of c at or after j is at p, and j..m − 1 if there is none. The last assumption is used
only for the upper bound of Theorem 3: any correct `find` must read every position from j up to the reported first
occurrence (or to the end of b when it returns −1), so the lower bound needs no assumption.

## 1. The greedy scan decides the subsequence relation

**Lemma 1.** Let x = x_1…x_k and y be strings. Define g_0 = −1 and g_t = the first position ≥ g_{t−1} + 1 where y has
the letter x_t (undefined if there is none). Then x is a subsequence of y if and only if g_1, …, g_k are all defined.

*Proof.* If they are defined, g_1 < … < g_k is an embedding. Conversely let p_1 < … < p_k be an embedding. By
induction g_t is defined and g_t ≤ p_t: p_1 ≥ 0 = g_0 + 1 holds the letter x_1, so g_1 exists and g_1 ≤ p_1; if
g_{t−1} ≤ p_{t−1}, then p_t ≥ p_{t−1} + 1 ≥ g_{t−1} + 1 holds x_t, so g_t exists and g_t ≤ p_t. ∎

For a mask, `lcs_brute` runs exactly this scan for x = a[S] (the letters of a at the set bits, in order) and y = b:
`j = b.find(a[i], j)` is the first position ≥ j holding a[i], and `j += 1` moves past it; the scan stops with
`is_common = False` exactly when some g_t is undefined.

## 2. Correctness of both algorithms

**Theorem 1 (enumeration).** `lcs_brute` returns lcs(a, b).

*Proof.* Every subsequence of a is a[S] for a set S of positions, and the masks 0..2ⁿ − 1 run over all such sets;
`mask.bit_count()` = |S|. By Lemma 1, a[S] is recorded as common exactly when it is a subsequence of b, and the
empty mask always is. So `best` is the largest length of a subsequence of a that is also one of b. ∎

**Lemma 2 (prefix recurrence).** Let L(i, j) = lcs(a[:i], b[:j]). Then L(0, j) = L(i, 0) = 0; if a_i = b_j then
L(i, j) = L(i − 1, j − 1) + 1; otherwise L(i, j) = max(L(i − 1, j), L(i, j − 1)) (letters indexed from 1).

*Proof.* The empty prefix has only the empty subsequence. Let c = a_i = b_j. Appending c to a common subsequence of
a[:i−1], b[:j−1] gives one of a[:i], b[:j], so L(i, j) ≥ L(i − 1, j − 1) + 1. Let z be a longest common subsequence
of a[:i], b[:j]. If z did not end with c, then zc would be longer and common; so z = z′c, and in embeddings of z in
a[:i] and in b[:j] the last letter can be moved to positions i and j (they hold c and lie after every other used
position), so z′ is common to a[:i−1], b[:j−1]: L(i, j) − 1 ≤ L(i − 1, j − 1). If a_i ≠ b_j, take embeddings of a
common subsequence z in a[:i] and b[:j]; the last letter of z cannot sit at position i of a and at position j of b
at once (the letters differ), so z is common to a[:i−1], b[:j] or to a[:i], b[:j−1]. Hence
L(i, j) ≤ max(L(i − 1, j), L(i, j − 1)), and ≥ is clear. ∎

**Theorem 2 (DP).** `lcs_dp` returns lcs(a, b).

*Proof.* Invariant: before processing a_i, `prev[j]` = L(i − 1, j) for all j (true for i = 1: all zeros). The row
sets `cur[0] = 0` = L(i, 0) and, for j = 1..m in order, `cur[j] = prev[j − 1] + 1` if a_i = b_j and
`max(prev[j], cur[j − 1])` otherwise, with `cur[j − 1]` = L(i, j − 1) already computed; by Lemma 2 this is L(i, j).
Then `prev = cur`. At the end `prev[-1]` = L(n, m) (for a = ε the initial row gives 0). ∎

**Check.** `tests/test_proofs_lcs.py`, `test_correct`: both outputs equal lcs computed by intersecting the sets of
all subsequences of a and of b (independent of both implementations) on every pair of strings over {A, C, G} with
lengths 0..4 × 0..4 (121 × 121 pairs) and on 200 random DNA pairs of lengths 0..9 (seed 1); Lemma 1 against the
subsequence sets for every x over {A, C} of length ≤ 4 and y of length ≤ 6.

## 3. Time and space of the enumeration

**Theorem 3.** For every mask the work of `lcs_brute` lies between min(n, m) and O(n + m), so the total time is
Θ(2ⁿ n) when m = n (n ≥ 1), and O(2ⁿ (n + m)) in general. Beyond the input it keeps O(1) values (the mask, j, the
flag and best); with the input the space is Θ(n + m).

*Proof.* Fix a mask. The loop over i runs at most n times, and the calls of `find` examine disjoint consecutive
ranges of positions (each starts right after the previous match), so they examine at most m positions in total:
O(n + m) work. If a[S] is a subsequence of b (in particular for the empty mask), the loop runs all n iterations. If
not, the scan fails at some `find`, which examines every position from j to m − 1, while the earlier calls examined
exactly the positions 0..j − 1; so m positions are examined. Either way the work is at least min(n, m). ∎

**Check.** `tests/test_proofs_lcs.py`, `test_enumeration_cost`: with b replaced by a `str` subclass whose `find`
counts the positions it examines (then delegates to `str.find`) and the loop body counted by a trace hook, every
mask's work lies in [min(n, m), n + m] and equals n loop iterations whenever a[S] is common, for n = 0..10 and
m ∈ {n, n ± 3} (seed 2); on a = b every mask makes n iterations. The V2 measurement times the enumeration against
2ⁿ n (n = 10..16); a measurement, not part of the proof.

## 4. Time and space of the DP

**Theorem 4.** `lcs_dp` executes its inner loop body exactly n·m times and allocates n + 1 rows of length m + 1, so
it takes Θ((n + 1)(m + 1)) time: Θ(n²) for two strings of length n, and Θ(n m) whenever both are non-empty. At most
two rows (`prev`, `cur`) are referenced at a time, so the space beyond the input is Θ(m + 1) = Θ(n).

*Proof.* No loop exits early; `prev = cur` releases the older row. ∎

**Check.** `tests/test_proofs_lcs.py`, `test_dp_cost`: the inner body line runs n·m times and the largest value of
len(prev) + len(cur) is 2(m + 1) (m + 1 for a = ε), for all lengths 0..12 × 0..12 and n = m = 50, 100 (seed 3).
The V2 measurement times the DP against n² (n = 100..800); a measurement.

## 5. The separation (T2)

Both algorithms compute lcs(a, b) (Theorems 1, 2); for |a| = |b| = n the enumeration takes Θ(2ⁿ n) (Theorem 3) and
the DP Θ(n²) (Theorem 4). The enumeration is exponential because it tries every candidate subsequence of a; the DP
has one table entry per prefix pair, (n + 1)² of them.

## Claim map

| Claim (location) | Proof |
|---|---|
| greedy leftmost scan decides the subsequence relation; enumeration correct | Lemma 1, Theorem 1 |
| enumeration Θ(2ⁿ n), Θ(n) space; docstring O(2ⁿ(n + m)) | Theorem 3 |
| DP correct (`algorithms[1].correctness`) | Lemma 2, Theorem 2 |
| DP Θ(n²), Θ(nm) for non-empty strings, Θ(n) space | Theorem 4 |
| T2: exponential enumeration vs quadratic table of prefix pairs | §5 |
