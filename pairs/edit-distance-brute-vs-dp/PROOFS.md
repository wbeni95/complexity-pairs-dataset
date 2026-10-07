# Proofs: edit distance, plain recursion vs Wagner–Fischer DP

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its two algorithms: correctness, the exact call count and the asymptotics of the plain
recursion, the time and space of both algorithms, the subproblem count, and the shortcut in `caveats`. The
statements in the entry's `background` field (the conditional lower bound, Masek and Paterson's faster algorithm) are
cited from the literature and are not proved here. Each section ends with the deterministic checks of its computable facts;
a check covers only the sizes it states, the proof covers all sizes.

**Cost model and machine-model assumptions (not proved here).** Character comparisons, additions and `min` of three
small integers cost O(1); a call of `d` does O(1) work besides its recursive calls; the DP's inner loop body costs
O(1); allocating a list of length t costs Θ(t + 1), and indexing costs O(1).

## 1. Edit scripts and alignments

**Definitions.** An *operation* on a string z is a substitution of z[p] by a letter, a deletion of z[p], or an
insertion of a letter before position p (0 ≤ p ≤ |z|). ed(x, y), the edit distance, is the least number of
operations that transform x into y (it exists: |x| deletions and |y| insertions do it). An *alignment* of x and y
is a sequence of columns, each of the form (c, c′), (c, −) or (−, c′) with letters c, c′, such that the top
letters read in order spell x and the bottom letters spell y. A column (c, c) costs 0; (c, c′) with c ≠ c′,
(c, −) and (−, c′) cost 1. al(x, y) is the least cost of an alignment of x and y.

**Lemma 1.** ed(x, y) = al(x, y) for all strings x, y.

*Proof.* (ed ≤ al.) Let A be an alignment of cost t; we build a script of t operations, by induction on the number
of columns. With no columns, x = y = ε and the empty script works. Otherwise let κ be the first column and A′ the
rest, of cost t′. An operation at position p of a string z acts in the same way at position p + 1 of cz on the part
after the first letter; call this *shifting*. If κ = (c, c), then x = cx′, y = cy′, A′ aligns x′ and y′, and the
shifted script of A′ turns x into y with t′ = t operations. If κ = (c, c′), c ≠ c′, substitute position 0 by c′
and then apply the shifted script of A′: 1 + t′ = t. If κ = (c, −), A′ aligns x′ and y; delete position 0, then
apply the script of A′: 1 + t′ = t. If κ = (−, c′), A′ aligns x and y′; apply the script of A′, then insert c′ at
position 0: t′ + 1 = t.

(al ≤ ed.) *Claim:* if z′ is obtained from z by one operation, then al(z, y) ≤ al(z′, y) + 1 for every y. Take an
optimal alignment A′ of z′ and y. A substitution at p: give the column that holds z′[p] the top letter z[p]; its
cost changes by at most 1, and the top row spells z. A deletion of z[p]: insert the column (z[p], −) right after
the column that holds z′[p − 1] (at the front if p = 0); the top row spells z, and the cost grows by 1. An
insertion of the letter c before position p of z (so z′[p] = c): the column that holds z′[p] is (c, e) or (c, −);
replace (c, e) by (−, e) (its cost becomes 1, a change of at most +1), or delete the column (c, −) (a change of −1);
the top row spells z. This proves the claim. Now let o_1, …, o_s turn x into y, with intermediate strings
x = z_0, z_1, …, z_s = y. The all-match alignment gives al(y, y) = 0, and the claim gives
al(z_{r−1}, y) ≤ al(z_r, y) + 1, so al(x, y) ≤ s. ∎

**Lemma 2 (recurrences).** al(ε, y) = |y| and al(x, ε) = |x|. If x = cx′ and y = c′y′, then
al(x, y) = min(al(x′, y) + 1, al(x, y′) + 1, al(x′, y′) + [c ≠ c′]). If x = x″c and y = y″c′, then
al(x, y) = min(al(x″, y) + 1, al(x, y″) + 1, al(x″, y″) + [c ≠ c′]).

*Proof.* An alignment of ε and y consists of the |y| columns (−, y[t]) in order, so its cost is |y|; likewise for
(x, ε). For non-empty x and y, the first column of any alignment is (c, c′), (c, −) or (−, c′); removing it leaves an
alignment of (x′, y′), (x′, y) or (x, y′) respectively, and putting such a column in front of any alignment of these
pairs gives an alignment of (x, y). Costs add, so minimising gives the first recurrence. The same argument with the
last column gives the second. ∎

**Lemma 3 (triangle inequality).** ed(x, z) ≤ ed(x, y) + ed(y, z), and ed(y, cy) ≤ 1 and ed(cy, y) ≤ 1 for a letter c.
*Proof.* Concatenate the two scripts; one insertion turns y into cy, and one deletion turns cy into y. ∎

## 2. Correctness of both algorithms

**Theorem 1 (plain recursion).** For all strings a, b and 0 ≤ i ≤ |a|, 0 ≤ j ≤ |b|, the call `d(i, j)` of
`edit_distance_brute` returns ed(a[i:], b[j:]). In particular the function returns ed(a, b).

*Proof.* Induction on (|a| − i) + (|b| − j). If i = |a|, the call returns |b| − j = al(ε, b[j:]); if j = |b|, it
returns |a| − i = al(a[i:], ε) (Lemma 2). Otherwise it returns the minimum of d(i + 1, j) + 1, d(i, j + 1) + 1 and
d(i + 1, j + 1) + [a[i] ≠ b[j]]; by induction these are the three terms of the first recurrence of Lemma 2 for
x = a[i:], y = b[j:], so the call returns al(a[i:], b[j:]) = ed(a[i:], b[j:]) (Lemma 1). ∎

This proves the entry's "Exhaustive over all alignments": the recursion minimises over every first column, hence
(by induction) over every alignment, and Lemma 1 equates alignments with edit scripts.

**Theorem 2 (Wagner–Fischer DP).** `edit_distance_dp` returns ed(a, b).

*Proof.* Write E(i, j) = ed(a[:i], b[:j]). Before the row loop, `prev[j] = j` = E(0, j) (Lemma 2). Suppose that
before row i (1 ≤ i ≤ |a|) `prev[j]` = E(i − 1, j) for all j. The row sets `cur[0] = i` = E(i, 0), and then, for
j = 1..|b| in increasing order, `cur[j] = min(prev[j] + 1, cur[j − 1] + 1, prev[j − 1] + (a[i−1] != b[j−1]))`;
when `cur[j]` is computed, `cur[j − 1]` = E(i, j − 1) already holds, so by the second recurrence of Lemma 2 and
Lemma 1, `cur[j]` = E(i, j). Then `prev = cur`. After the last row (or at once if a = ε) the function returns
`prev[-1]` = E(|a|, |b|) = ed(a, b). ∎

**Corollary (the shortcut in `caveats`).** If a[i] = b[j], then d(i, j) = d(i + 1, j + 1), so a recursion that
returns d(i + 1, j + 1) at once on a character match is still correct.

*Proof.* Let c = a[i] = b[j], x′ = a[i+1:], y′ = b[j+1:]. By Lemma 3, ed(x′, y′) ≤ ed(x′, cy′) + 1 and
ed(x′, y′) ≤ 1 + ed(cx′, y′); that is, d(i + 1, j) + 1 ≥ d(i + 1, j + 1) and d(i, j + 1) + 1 ≥ d(i + 1, j + 1).
The third term of the minimum is d(i + 1, j + 1) + 0, so the minimum equals d(i + 1, j + 1) (Theorem 1). ∎

The shortcut makes the cost depend on the input: on a = b (length n) it follows the diagonal and makes n + 1 calls;
on two strings with no common letter it never applies and makes exactly as many calls as the plain recursion,
(3 D(n, n) − 1)/2 (section 3).

**Check.** `tests/test_proofs_editdist.py`, `test_correct_against_edit_script_search`: ed computed by breadth-first
search over single operations (alphabet A, C, G, T), independently of both implementations, equals both outputs on
every pair of strings over {A, C, G} of lengths 0..3 (40 × 40 pairs) and on 60 random pairs of DNA strings of
lengths 0..4 (seed 1); `test_dp_unequal_lengths`: both implementations agree on 300 random pairs of unequal lengths
0..7 (seed 2); `test_shortcut_variant`: the shortcut recursion (written in the test) equals the DP on 400 random
pairs of lengths 0..8 (seed 3), makes n + 1 calls on a = b and (3 D(n, n) − 1)/2 calls on strings over disjoint
alphabets, n = 0..8.

## 3. The plain recursion: calls, leaves, depth, Θ((3 + 2√2)ⁿ/√n)

Let |a| = |b| = n.

**Lemma 4 (call tree).** The call d(i, j) is a leaf exactly when i = n or j = n; every other call has exactly 3
children, (i + 1, j), (i, j + 1) and (i + 1, j + 1). The number of leaves is D(n, n), where D(u, 0) = D(0, v) = 1
and D(u, v) = D(u − 1, v) + D(u, v − 1) + D(u − 1, v − 1) (Delannoy numbers), and the number of calls is
(3 D(n, n) − 1)/2.

*Proof.* The first sentence is read off the code (`min` evaluates all three arguments). Let Λ(i, j) be the number
of leaves below the call (i, j). Then Λ(i, j) = 1 if i = n or j = n, and otherwise
Λ(i, j) = Λ(i + 1, j) + Λ(i, j + 1) + Λ(i + 1, j + 1). With u = n − i and v = n − j this is the Delannoy recurrence,
so Λ(0, 0) = D(n, n). (Equivalently, as `entry.json` puts it: the root-to-leaf paths are the lattice paths from
(0, 0) with steps (1, 0), (0, 1), (1, 1) stopped at their first point with i = n or j = n; such a path extends to
(n, n) in exactly one way, by steps along the line it has reached, since any other step leaves [0, n]²; and every
lattice path to (n, n) arises exactly once, by cutting it at its first point on one of the two lines. D(n, n)
counts the lattice paths to (n, n) by the same recurrence over the last step.) In a tree where every internal node
has 3 children, N = 1 + 3I and N = I + Λ, so Λ = 2I + 1 and N = (3Λ − 1)/2. ∎

**Lemma 5 (closed form).** D(u, v) = Σ_k C(u, k) C(v, k) 2^k; in particular D(n, n) = Σ_k C(n, k)² 2^k ≥ 2ⁿ.

*Proof.* S(u, v) = Σ_k C(u, k) C(v, k) 2^k satisfies S(u, 0) = S(0, v) = 1. For u, v ≥ 1 write P_k = C(u − 1, k)
C(v − 1, k). Pascal's rule applied to both factors gives C(u, k) C(v, k) = P_k + P_{k−1} + X_k with
X_k = C(u − 1, k) C(v − 1, k − 1) + C(u − 1, k − 1) C(v − 1, k), and applied to one factor it gives
C(u − 1, k) C(v, k) + C(u, k) C(v − 1, k) + P_k = 3P_k + X_k. So
S(u, v) − [S(u − 1, v) + S(u, v − 1) + S(u − 1, v − 1)] = Σ_k 2^k (P_{k−1} − 2P_k) = Σ_k 2^{k+1} P_k − Σ_k 2^{k+1} P_k
= 0. Hence S satisfies the Delannoy recurrence and boundary values, and S = D. The term k = n gives D(n, n) ≥ 2ⁿ. ∎

**Lemma 6 (depth).** For n ≥ 1 the longest root-to-leaf path of the call tree has 2n calls; for n = 0 the only
call is the root. So the recursion depth is 2n (n ≥ 1).

*Proof.* Along a path, i + j grows by 1 or 2 per step. An internal call has i, j ≤ n − 1, so i + j ≤ 2n − 2, and a
path has at most 2n − 1 internal calls (with i + j = 0, 1, …, 2n − 2) followed by one leaf: at most 2n calls.
Alternating steps (1, 0) and (0, 1) reach (n − 1, n − 1) after 2n − 2 steps with 2n − 1 internal calls, and one more
step reaches a leaf: exactly 2n. ∎

**Lemma 7 (subproblems).** The argument pairs of the calls are exactly the (n + 1)² pairs in {0, …, n}².

*Proof.* Every argument lies in {0, …, n}², since i and j grow only while both are ≤ n − 1. Every (i, j) with
i, j ≤ n − 1 is reached from (0, 0) by unit steps through internal calls; (n, j) with j ≤ n − 1 is a child of
(n − 1, j); (i, n) with i ≤ n − 1 is a child of (i, n − 1); (n, n) is a child of (n − 1, n − 1) (n ≥ 1; for n = 0
the root is (0, 0)). ∎

**Theorem 3 (asymptotics).** Let λ = 3 + 2√2 (= 5.83 to two decimals). For every n ≥ 1,

  3 · 10⁻⁴ ≤ D(n, n) √n / λⁿ ≤ 6,

so D(n, n) = Θ(λⁿ/√n). The largest term of Σ_k C(n, k)² 2^k sits at k_m = ⌈(2 − √2)n − (√2 − 1)⌉, within 1 of
(2 − √2)n, and it is Θ(λⁿ/n).

*Proof.* Write a_k = C(n, k)² 2^k, x* = 2 − √2, H(x) = −x ln x − (1 − x) ln(1 − x) and f(x) = 2H(x) + x ln 2 on
(0, 1).

*Peak.* a_{k+1}/a_k = 2((n − k)/(k + 1))², which is ≥ 1 iff √2 (n − k) ≥ k + 1, i.e. k ≤ x*n − (√2 − 1). So the
a_k increase up to k_m and decrease after it.

*The exponent.* f′(x) = 2 ln((1 − x)/x) + ln 2 vanishes at (1 − x)/x = 1/√2, i.e. at x = x*. With y = 1 − x* = √2 − 1
and x* = √2·y: 2H(x*) + x* ln 2 = −2x* ln(√2 y) − 2y ln y + x* ln 2 = −2(x* + y) ln y = −2 ln(√2 − 1)
= 2 ln(√2 + 1) = ln λ. f″(x) = −2/(x(1 − x)) ≤ −8, so g(x) = f(x) + 4(x − x*)² is concave with g′(x*) = 0, hence

  f(x) ≤ ln λ − 4(x − x*)²   for all x ∈ (0, 1).                                                     (U)

On I = [x* − 1/4, x* + 1/4] = [1.75 − √2, 2.25 − √2] ⊂ (0, 1) we have x(1 − x) ≥ (2.25 − √2)(√2 − 1.25) > 0.1372,
so |f″| < 14.58 and f(x) + 7.29(x − x*)² is convex on I with derivative 0 at x*, hence

  f(x) ≥ ln λ − 7.29 (x − x*)²   for x ∈ I.                                                         (L)

*Stirling bounds (self-contained).* Let d_m = ln m! − (m + ½) ln m + m for m ≥ 1. Then
d_m − d_{m+1} = (m + ½) ln(1 + 1/m) − 1. With x = 1/(2m + 1) we have 1 + 1/m = (1 + x)/(1 − x) and m + ½ = 1/(2x),
so d_m − d_{m+1} = artanh(x)/x − 1 = Σ_{t≥1} x^{2t}/(2t + 1). This series is larger than its first term
x²/3 = 1/(3(2m + 1)²), which exceeds 12/((12m + 1)(12m + 13)) = 1/(12m + 1) − 1/(12m + 13) (because
(12m + 1)(12m + 13) − 36(2m + 1)² = 24m − 23 > 0), and smaller than (x²/3) Σ_{t≥0} x^{2t} = x²/(3(1 − x²)) =
1/(12m(m + 1)) = 1/(12m) − 1/(12(m + 1)). So d_m decreases, d_m − 1/(12m) increases, the limit κ = lim d_m exists,
and summing the differences from m on gives

  m! = e^κ m^{m+½} e^{−m} e^{ρ_m}   with   1/(12m + 1) < ρ_m < 1/(12m)   (m ≥ 1).

Since d_1 = 1, κ = 1 − ρ_1 lies in (11/12, 12/13). (In fact e^κ = √(2π), but only the two bounds are used.) For
1 ≤ k ≤ n − 1 this gives C(n, k) = e^{−κ} √(n/(k(n − k))) e^{nH(k/n)} e^{ρ_n − ρ_k − ρ_{n−k}} with
−1/6 < ρ_n − ρ_k − ρ_{n−k} < 1/12, so

  a_k = e^{−2κ} (n/(k(n − k))) e^{n f(k/n)} θ_k,   e^{−1/3} < θ_k < e^{1/6},   e^{−24/13} < e^{−2κ} < e^{−11/6}
  (1 ≤ k ≤ n − 1).                                                                                    (S)

*Upper bound.* a_0 = 1 and a_n = 2ⁿ. Split 1 ≤ k ≤ n − 1 into S1 = {|k − x*n| ≤ n/4} and S2 (the rest). On S1,
k ≥ (1.75 − √2)n > 0.3357n and n − k ≥ (√2 − 1.25)n > 0.1642n, so n/(k(n − k)) = 1/k + 1/(n − k) < 9.1/n; on S2,
n/(k(n − k)) ≤ 2 and, by (U), e^{n f(k/n)} ≤ λⁿ e^{−n/4}. On S1, (U) gives e^{n f(k/n)} ≤ λⁿ g(k) with
g(t) = e^{−4(t − x*n)²/n}. For this unimodal g with maximum 1, Σ_{k∈ℤ} g(k) ≤ 2 + ∫ g = 2 + √(πn)/2 (each integer
k ≤ x*n − 1 has g(k) ≤ ∫_k^{k+1} g, each k ≥ x*n + 1 has g(k) ≤ ∫_{k−1}^k g, and at most two integers lie in
between). Altogether, with (S),

  D(n, n) √n / λⁿ ≤ (1 + 2ⁿ)√n/λⁿ + 9.1 e^{1/6} e^{−11/6} (2/√n + √π/2) + 2 e^{1/6} e^{−11/6} n^{3/2} e^{−n/4}.

Here 9.1 e^{1/6} e^{−11/6} < 1.719 and 2 e^{1/6} e^{−11/6} < 0.3778. The first term is at most 2 · 2ⁿ √n/λⁿ ≤ 0.69
(its maximum, at n = 1), the second at most 1.719 · 2.887 < 4.97, the third at most 0.3778 · 6^{3/2} e^{−1.5} < 1.24
(the maximum of n^{3/2} e^{−n/4} over the integers is at n = 6); the sum is below 6.9. For n ≥ 9 the bound is below
6 (first term < 0.01, second < 1.719 · (2/3 + 0.887) < 2.68, third < 1.24; total < 3.93), and for n ≤ 8 the exact values are below
0.57 (check). This gives the upper bound 6.

*Lower bound.* Let n ≥ 16 and take the integers k with |k − x*n| ≤ √n; there are at least 2√n − 1 ≥ √n of them.
For each, |k/n − x*| ≤ 1/√n ≤ 1/4, so k/n ∈ I and 1 ≤ k ≤ n − 1 (k ≥ 0.3357n ≥ 5, n − k ≥ 0.1642n ≥ 2), and (L)
gives n f(k/n) ≥ n ln λ − 7.29. With k(n − k) ≤ n²/4 and (S), a_k ≥ (4/n) e^{−24/13 − 1/3 − 7.29} λⁿ
≥ (4/n) e^{−9.4695} λⁿ, so D(n, n) ≥ √n · (4/n) e^{−9.4695} λⁿ > 3.08 · 10⁻⁴ λⁿ/√n. For 1 ≤ n ≤ 15 the exact values of D(n, n)√n/λⁿ lie in
[0.514, 0.569] (check). This gives the lower bound 3 · 10⁻⁴.

*The largest term.* For n ≥ 16, k_m ∈ S1, so a_{k_m} < (1.719/n) λⁿ; and the integer k nearest to x*n has
|k/n − x*| ≤ 1/(2n), so (L) and (S) give a_{k_m} ≥ a_k ≥ (4/n) e^{−24/13 − 1/3 − 7.29/(4n)} λⁿ. ∎

(The ratio D(n, n)√n/λⁿ actually increases from 0.515 at n = 1 to 0.5726 at n = 2000; Θ needs only the bounds.)

**Theorem 4 (time and space of the recursion).** `edit_distance_brute` makes exactly (3 D(n, n) − 1)/2 calls, so it
runs in time Θ(D(n, n)) = Θ((3 + 2√2)ⁿ/√n) on every pair of length-n strings, and its recursion depth is 2n
(n ≥ 1), so it uses Θ(n) space (2n frames of O(1) size, plus the input of 2n characters).

*Proof.* Lemmas 4 and 6 and Theorem 3, with O(1) work per call. Since D(n, n) ≥ 2ⁿ (Lemma 5), the recursion is
exponential. ∎

**Check.** `tests/test_proofs_editdist.py`, `test_recursion_calls_leaves_depth`: the calls of `d` (counted with a
profiler hook on the unchanged code) equal (3 D(n, n) − 1)/2, the leaves (calls with i = n or j = n) equal
D(n, n) = Σ_k C(n, k)² 2^k, the maximal depth is 2n (1 at n = 0), and the argument pairs are all of {0, …, n}²,
for n = 0..8, two random pairs each (seed 4); `test_delannoy_closed_form`: the recurrence equals the closed form for
0 ≤ u, v ≤ 30; `test_asymptotic_bounds`: 3·10⁻⁴ ≤ D(n, n)√n/λⁿ ≤ 6 for n = 1..400 and n = 1000, 2000 (exact
integers, 60-digit decimals), the values in [0.514, 0.569] for n = 1..15 and below 0.57 for n ≤ 8, the peak index
k_m for n = 1..300, (S) with (U), (L) at every k for n = 16..200; `test_stirling_steps`: the two inequalities
for d_m − d_{m+1} for m = 1..3000 (50-digit decimals), the numeric constants of the upper and lower bound, and
11/12 < ln √(2π) < 12/13 as an illustration. The V2 measurement times the recursion against
(3 + 2√2)ⁿ/√n (n = 5..9); that fit is a measurement, not part of the proof.

## 4. The DP: time and space

**Theorem 5.** `edit_distance_dp` executes its inner loop body exactly |a|·|b| times and allocates |a| + 1 rows of
length |b| + 1, so it runs in time Θ((|a| + 1)(|b| + 1)): Θ(n²) for two strings of length n, and Θ(|a|·|b|) whenever
both strings are non-empty (then (|a| + 1)(|b| + 1) ≤ 4|a||b|). At any time at most two rows are referenced
(`prev` and `cur`; the older row is released when `prev = cur` rebinds it, and the expression that builds `cur` makes
one temporary list of length |b|), so the space beyond the input is Θ(|b| + 1) = Θ(n).

*Proof.* The outer loop runs once per letter of a, the inner once per letter of b, with no early exit. ∎

The bound Θ(|a|·|b|) fails if one string is empty: for b = ε the code still runs |a| outer iterations.

**Check.** `tests/test_proofs_editdist.py`, `test_dp_iterations_and_rows`: the inner body line runs |a|·|b| times
(line events of a trace hook) and the largest value of len(prev) + len(cur) over the run is 2(|b| + 1) (|b| + 1 if
a = ε), for all pairs of lengths 0..12 × 0..12 (one random pair each, seed 5) and n = 50, 100. The V2 measurement
times the DP against n² (n = 100..800); a measurement, not part of the proof.

## 5. The separation

The recursion makes at least (3 · 2ⁿ − 1)/2 calls (Lemma 5) and Θ((3 + 2√2)ⁿ/√n) in total; the DP solves the same
problem (Theorems 1 and 2) in Θ(n²). The recursion is exponential only because it re-solves the (n + 1)² distinct
subproblems (Lemma 7), each many times: the DP fills one table entry per subproblem. This is the T2 claim.

## Claim map

| Claim (location) | Proof |
|---|---|
| recursion correct (`algorithms[0].correctness`, README) | §1, Theorem 1 |
| DP correct (`algorithms[1].correctness`) | §1, Theorem 2 |
| leaves D(n, n), calls (3 D(n, n) − 1)/2 (`algorithms[0].time_complexity`, `brute_force.py`) | Lemmas 4, 5 |
| D(n, n) = Σ_k C(n, k)² 2^k = Θ((3 + 2√2)ⁿ/√n), largest term Θ(λⁿ/n) near (2 − √2)n | Lemma 5, Theorem 3 |
| recursion Θ(D(n, n)) time, Θ(n) space | Theorem 4, Lemma 6 |
| DP Θ(n²), Θ(|a||b|) for non-empty strings (`input.parameter`), Θ(n) space, two rows | Theorem 5 |
| (n + 1)² distinct subproblems (`relationship`, README) | Lemma 7 |
| the shortcut on a match is valid and makes the cost input-dependent (`caveats`) | Corollary in §2 |
| T2: exponential recursion vs polynomial DP for the same problem | §5 |
