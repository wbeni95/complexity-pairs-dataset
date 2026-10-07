# Proofs: optimal binary search tree, plain recursion vs cubic DP vs Knuth

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code).
Sections 1–5 prove the exact operation counts for every size of their domain. Sections 6–9 prove the rest: the
problem's cost and the correctness of the recurrence (§6), the correctness of Knuth's restricted root search for
non-negative frequencies with any tie rule inside the range, by the quadrangle-inequality argument written out for
this entry's weights (§7), the time and space bounds (§8), and the separations (§9). Each proof is followed by the
deterministic scripts that check it and the sizes they check it on. A check covers only those sizes; the proofs
cover the whole domain.

## Counting convention

*Machine-model assumptions (not proved here).* Additions and comparisons of the frequencies and costs count as unit
operations (as in `input.size_measure`); indexing costs O(1); allocating a list of length t costs Θ(t + 1); a Python
call costs O(1); `sum` over a generator of t terms costs Θ(t + 1) plus the generator's work.

`harness.py`, class `CountingInt`: `__lt__`, `__le__`, `__gt__` and `__ge__` each call `_cmp`, which adds 1 to the
module counter `_comparisons` (`_comparisons += 1`) and compares the wrapped values; `__add__` (also bound as
`__radd__`) adds 1 to `_additions` and returns a new `CountingInt`. `__eq__`, `__hash__` and the constructor count
nothing. `generate_scaling(n, rng)` calls `reset_counters()` (both counters 0) and returns
`_heavy_ends(n, rng, CountingInt)`, which computes its weights on plain ints and only then wraps them;
`reported_cost(output)` returns `_comparisons`. The additions in `caveats` are `_additions` after the same call.

An addition with at least one `CountingInt` operand counts 1 and returns a `CountingInt` (with a plain left operand,
`int.__add__` returns `NotImplemented` and Python calls `__radd__`); `0 + 0` on plain ints counts nothing. A
comparison whose left operand is a `CountingInt` counts 1. Not counted: indices and `range` bounds, `i == j`,
`best is None` (an identity test), and the root table `r` of `obst_knuth` (it stores plain ints). The built-in
`sum()` in the recursion's `weight` starts from the plain int 0 and adds each `CountingInt` item with the generic
addition, so each of its additions counts 1, the first one (`0 + item`) through `__radd__`.

**Every input** below means every instance (p, q) of `CountingInt` tuples with len(p) = n and len(q) = n + 1,
whatever the values (also negative ones). Write w(i, j) = q_i + Σ_{m=i+1..j} (p_m + q_m); the interval (i, j),
0 ≤ i ≤ j ≤ n, holds the keys i + 1..j and has length L = j − i.

**Scaling instance.** `_heavy_ends(n, rng, CountingInt)` draws p_1..p_n and q_0..q_n uniformly from 0..9. For
n ≥ 1 it sets p_1 = p_n = 0, lets S be the sum of all weights (so S is the sum of all weights except p_1 and p_n),
and sets p_1 = p_n = M with M = nS + 1. (For n = 1, p_1 = p_n is a single weight.)

**Two facts used in every section.** (i) *Values.* In all three implementations the empty interval has the plain
value 0 and every non-empty interval has a `CountingInt` value: `weight(i, j)` is `q[i] + sum(...)` and
`cost(i, j)` is `weight(i, j) + best`; in the DPs `w[i][i] = q[i]`, `w[i][j] = w[i][j - 1] + p[j - 1] + q[j]`
and `c[i][j] = w[i][j] + best` (in `obst_knuth`, `c[i][i + 1] = w[i][i + 1]`). So for L ≥ 2 every candidate
`cand = c(i, k − 1) + c(k, j)` has a non-empty side (k − 1 > i or k < j): it is one counted addition and a
`CountingInt`. For L = 1 the only candidate is `0 + 0`, a plain int, uncounted. (ii) *Running minimum.* An
interval loops over its candidates; for the first, `best is None` is true and `or` short-circuits, so there is no
comparison; each later candidate evaluates `cand < best` (`cand <= best` in `obst_knuth`) with `cand` a
`CountingInt` (L ≥ 2): exactly 1 comparison. So an interval with t ≥ 1 candidates makes t − 1 comparisons. The
outcome of a comparison only selects which value (and root) is stored, never the loop structure.

## 1. Plain recursion: 3ⁿ calls, (3^(n−1) − 1)/2 comparisons

**Statement.** On every input, `obst_recursive` calls its inner function `cost` exactly 3ⁿ times for every n ≥ 0,
and makes exactly (3^(n−1) − 1)/2 comparisons for every n ≥ 1 (0 for n = 0, where the formula gives −1/3).

**Proof.** The recurrences and their solutions are given in `entry.json`, field `algorithms[0].correctness`. The
steps it leaves out: a call `cost(i, j)` with i = j returns the plain 0 at once (1 call, no comparison). A call with
L = j − i ≥ 1 calls `cost(i, k − 1)` and `cost(k, j)` for k = i + 1..j, of lengths k − 1 − i and j − k, each of
which runs over 0..L − 1 as k does. It makes L − 1 comparisons itself (fact (ii); for L = 1 there is one candidate),
and `weight` makes none. So with K(0) = 1, C(0) = 0:
K(L) = 1 + 2 Σ_{t<L} K(t) and C(L) = (L − 1) + 2 Σ_{t<L} C(t) for L ≥ 1.
Then K(1) = 3 and C(1) = 0; for L ≥ 2, subtracting the identity for L − 1 gives K(L) = 3K(L − 1) and
C(L) = 3C(L − 1) + 1. Hence K(L) = 3^L, and C(L) = (3^(L−1) − 1)/2 by induction
(3(3^(L−2) − 1)/2 + 1 = (3^(L−1) − 1)/2). The top call `cost(0, n)` gives the statement; no step depends on the
values.

**Check.** At the V2 sizes n = 5..11: `experiments/2026-10-07b_optimal_bst_counts.py`, part 1 (calls and
comparisons, n = 0..11, families small, zero and wide). `experiments/2026-10-07_closed_form_checks.py`, group
`expdp`, line "OBST recursion (3^(n-1)-1)/2": n = 0..11 (n = 0 reported as outside the domain); line "OBST
recursion: 3^n calls of cost()": n = 0..11 (both on the scaling family with the V2 seeds).
`experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "OBST recursion: 3^n calls, (3^(n-1)-1)/2
comparisons (n>=1, 0 at n=0) on every family and signed values": n = 0..9, the ten V1 families and two kinds of
signed values.

## 2. Cubic DP: (n + 1)n(n − 1)/6 comparisons, n(n + 1)(n + 2)/6 candidate roots

**Statement.** On every input and for every n ≥ 0, `obst_cubic` evaluates exactly n(n + 1)(n + 2)/6 candidate
roots (executions of `cand = c[i][k - 1] + c[k][j]`, uncounted loop work) and makes exactly
(n + 1)n(n − 1)/6 = C(n + 1, 3) comparisons.

**Proof.** Given in `entry.json`, field `algorithms[1].correctness` (L − 1 comparisons per interval of length L,
summed to C(n + 1, 3)), and in the docstring of `cubic_dp.py` (Σ_L (n − L + 1)L candidates). The missing steps:
there are n − L + 1 intervals of length L; each tries k = i + 1..j, that is L candidates, and makes L − 1
comparisons by fact (ii). With m = L − 1:
Σ_{m=0..n−1} (n − m)m = n · n(n − 1)/2 − (n − 1)n(2n − 1)/6 = (n + 1)n(n − 1)/6, and
Σ_{m=0..n−1} (n − m)(m + 1) = (n + 1)n(n − 1)/6 + n(n + 1)/2 = n(n + 1)(n + 2)/6. For n = 0 there is no interval
and both counts are 0.

**Check.** At the V2 sizes n = 16, 32: `experiments/2026-10-07b_optimal_bst_counts.py`, part 1 (comparisons,
n = 0..40, all ten V1 families). `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "OBST cubic
(n+1)n(n-1)/6": n = 0..40, 64, 128 (scaling family, V2 seeds; all V2 sizes); group `extra`, line "optimal cubic DP
candidate roots n(n+1)(n+2)/6 (uncounted)": n = 0..24, one instance per n. `experiments/2026-10-07_count_proof_checks.py`, group
`bst`, line "OBST cubic DP: comparisons (n+1)n(n-1)/6, additions n(n+1)(n+2)/6+3n(n+1)/2-n, candidate roots
n(n+1)(n+2)/6": n = 0..30, the ten V1 families and two kinds of signed values.

## 3. Knuth: Σ_{L=2..n} (r[n−L+1][n] − r[0][L−1]) ≤ (n − 1)² comparisons on every input

**Statement.** Let r be the root table that `obst_knuth` builds: r[i][i + 1] = i + 1, and for j − i ≥ 2,
r[i][j] = `best_k`, the largest k of the search range r[i][j − 1]..r[i + 1][j] whose candidate is minimal. On every
input and for every n ≥ 0:
- (a) every search range is non-empty, i + 1 ≤ r[i][j] ≤ j, and r[i][j − 1] ≤ r[i][j] ≤ r[i + 1][j] for j − i ≥ 2;
- (b) for each length L ≥ 2, the intervals of length L evaluate
  Σ_i (r[i+1][i+L] − r[i][i+L−1] + 1) = (n − L + 1) + r[n−L+1][n] − r[0][L−1] ≤ 2n − L candidates;
- (c) `obst_knuth` makes exactly Σ_{L=2..n} (r[n−L+1][n] − r[0][L−1]) comparisons, and this is at most (n − 1)².

The bound uses only property (a) of the implementation's own table, which follows from the code for any values. It
does not use Knuth's monotonicity theorem, which the entry cites for the correctness of the value (that the
restricted range contains an optimal root), not for the count.

**Proof.** The telescoping in (b) is given in `entry.json`, field `algorithms[2].time_complexity`, and the
non-empty ranges in field `algorithms[2].correctness`; all steps follow.

(a) Induction on L = j − i. L = 1: the length-1 loop sets r[i][i + 1] = i + 1. L = 2: the range is
r[i][i + 1]..r[i + 1][i + 2] = i + 1..i + 2. L ≥ 3: r[i][j − 1] lies in its own range, whose upper end is
r[i + 1][j − 1], and r[i + 1][j] lies in its own range, whose lower end is r[i + 1][j − 1]; so
r[i][j − 1] ≤ r[i + 1][j − 1] ≤ r[i + 1][j] and the range is non-empty. Hence the first candidate sets `best_k`,
which then always holds a member of the range: r[i][j − 1] ≤ r[i][j] ≤ r[i + 1][j]. By induction
r[i][j − 1] ≥ i + 1 and r[i + 1][j] ≤ j, so i + 1 ≤ r[i][j] ≤ j. In particular each of the n(n − 1)/2 intervals of
length ≥ 2 evaluates at least one candidate; the n intervals of length 1 evaluate none (their root is set
directly).

(b) The interval (i, i + L) evaluates r[i+1][i+L] − r[i][i+L−1] + 1 candidates. In the sum over i = 0..n − L, the
term +r[i+1][i+L] cancels the term −r[i′][i′+L−1] with i′ = i + 1, leaving
(n − L + 1) + r[n−L+1][n] − r[0][L−1]. By (a), r[n−L+1][n] ≤ n and r[0][L−1] ≥ 1, so the sum is at most 2n − L.

(c) The length-1 loop has no comparison. By fact (ii), an interval of length ≥ 2 makes one comparison fewer than
it has candidates, so by (b) the intervals of length L make r[n−L+1][n] − r[0][L−1] ≤ n − 1 comparisons. Summing
over L = 2..n gives the exact count and the bound (n − 1)(n − 1). For n ≤ 1 the sum is empty and the count is 0.

**Check.** `experiments/2026-10-07b_optimal_bst_counts.py`, part 1: the count equals the same sum evaluated on the
table of largest optimal roots of a separate cubic DP, n = 0..40, all ten V1 families.
`experiments/2026-10-07_closed_form_checks.py`, group `extra`, line "OBST Knuth comparisons <= (n-1)^2 on all ten
families": n = 1..40, 2 instances per family. `experiments/2026-10-07_count_proof_checks.py`, group `bst`, lines
"Knuth root table: r[i][i+1] = i+1, i < r[i][j] <= j, r[i][j-1] <= r[i][j] <= r[i+1][j] (implementation's table)",
"Knuth comparisons = sum_{L=2..n} (r[n-L+1][n] - r[0][L-1]) with the implementation's own r" and "Knuth
comparisons <= (n-1)^2 on every input (n >= 1)": n = 0..40, 3 instances each of the ten V1 families and of two kinds
of signed values; line "Knuth candidates of length L: (n-L+1) + r[n-L+1][n] - r[0][L-1] <= 2n - L": n = 0..25,
every L, the same twelve kinds.

## 4. Knuth on the scaling family: (n − 1)²

**Statement.** On the scaling family, for every n ≥ 1, `obst_knuth` chooses r[0][m] = 1 and r[m][n] = n for
1 ≤ m ≤ n − 1 and makes exactly (n − 1)² comparisons (n = 0: 0 comparisons, where the formula gives 1). Moreover
k_1 is the unique optimal root of every interval (0, m) and k_n the unique optimal root of every interval (m, n),
1 ≤ m ≤ n − 1 (docstring of `_heavy_ends`). By section 3, (n − 1)² is the largest count over all inputs with n
keys, so this family is a worst case.

**Proof.** *Lemma (values).* Let all weights be ≥ 0. Then w is monotone under inclusion: w(i′, j′) ≤ w(i, j) for
i ≤ i′ ≤ j′ ≤ j, because w(i′, j′) sums a subset of the non-negative weights q_i..q_j, p_{i+1}..p_j that w(i, j)
sums. Let d be a table with d(i, i) = 0 and, for j > i, d(i, j) = w(i, j) + d(i, k − 1) + d(k, j) for some
k ∈ [i + 1, j]. Then w(i, j) ≤ d(i, j) ≤ (j − i) w(i, j) for all j > i. By induction on j − i: d ≥ 0 everywhere
(w ≥ 0), so d(i, j) ≥ w(i, j); and d(i, k − 1) ≤ (k − 1 − i) w(i, j), d(k, j) ≤ (j − k) w(i, j) (induction and
monotonicity, as both are sub-intervals of (i, j); both sides are 0 for an empty interval), so
d(i, j) ≤ (1 + (k − 1 − i) + (j − k)) w(i, j) = (j − i) w(i, j).
The lemma applies to the values of `obst_knuth`'s table c: `w[i][j]` equals w(i, j); `c[i][i + 1] = w[i][i + 1]`
(k = i + 1); and for j − i ≥ 2, `c[i][j] = w[i][j] + best`, where `best` is the candidate of k = `best_k`, since the
two are assigned together (`best, best_k = cand, k`), and k ∈ [i + 1, j] by section 3 (a). It applies equally to the
optimal costs c* of the recurrence, with k an optimal root.

*Weights on the family.* Let n ≥ 3. An interval (i, j) with 1 ≤ i < j ≤ n − 1 contains neither p_1 nor p_n, so
w(i, j) ≤ S. An interval (0, j) with j ≥ 1 contains p_1, and an interval (i, n) with i ≤ n − 1 contains p_n, so its
weight is at least M = nS + 1.

*Prefix intervals: r[0][m] = 1.* For m = 1 the length-1 loop sets it. Let 2 ≤ m ≤ n − 1 and, by induction,
r[0][m − 1] = 1; the range is k = 1..r[1][m], and r[1][m] ≥ 2 by section 3 (a). The candidate k = 1 is
c[0][0] + c[1][m] ≤ (m − 1) w(1, m) ≤ (n − 2)S. Every candidate k ≥ 2 is c[0][k − 1] + c[k][m] ≥ w(0, k − 1) ≥ M,
which exceeds (n − 2)S. So k = 1, the first candidate, sets `best`, and `cand <= best` is false for every later k:
`best_k` stays 1.

*Suffix intervals: r[m][n] = n.* For m = n − 1 the length-1 loop sets it. Let 1 ≤ m ≤ n − 2 and, by induction,
r[m + 1][n] = n; the range is k = r[m][n − 1]..n, and r[m][n − 1] ≤ n − 1. The candidate k = n is
c[m][n − 1] + c[n][n] ≤ (n − 1 − m) w(m, n − 1) ≤ (n − 2)S, and every candidate k ≤ n − 1 is
c[m][k − 1] + c[k][n] ≥ w(k, n) ≥ M. The candidate k = n comes last; `best` is then the minimum of the earlier
candidates, which is ≥ M, so `cand <= best` is true and `best_k` = n.

For n = 1, 2 every claimed root is set by the length-1 loop (m = 1 = n − 1 when n = 2).

*Count.* By section 3 (c) the count is Σ_{L=2..n} (r[n−L+1][n] − r[0][L−1]). For L = 2..n, both 1 ≤ L − 1 ≤ n − 1
and 1 ≤ n − L + 1 ≤ n − 1, so every term is n − 1, and there are n − 1 terms: (n − 1)². For n = 1 there is no term
and the count is 0 = (n − 1)²; for n = 0 it is 0.

*Unique optimal roots.* By the lemma for c*, the root k = 1 gives w(0, m) + c*(1, m) ≤ w(0, m) + (n − 2)S, while
every root k ≥ 2 gives w(0, m) + c*(0, k − 1) + c*(k, m) ≥ w(0, m) + M. So for
2 ≤ m ≤ n − 1, k_1 is the only optimal root of (0, m) (for m = 1 it is the only root). The suffix case is the
mirror image. The count above does not use this fact: it shows directly which roots the implementation keeps.

**Check.** At the V2 sizes n = 32, 64, 128, 256, 512: `experiments/2026-10-07_closed_form_checks.py`, group
`expdp`, line "OBST Knuth (n-1)^2 (heavy ends)": n = 0..60, 64, 128, 256, 512 (V2 seeds; n = 0 reported as outside
the domain). `experiments/2026-10-07b_optimal_bst_counts.py`, part 1: n = 0..40 and 48, 64, 96, 128, one instance
each. `experiments/2026-10-07_count_proof_checks.py`, group `bst`, lines "heavy ends: Knuth comparisons (n-1)^2
(n >= 1; 0 at n = 0)", "heavy ends: implementation picks r[0][m] = 1 and r[m][n] = n (1 <= m <= n-1)", "heavy
ends: w(i,j) <= c[i][j] <= (j-i) w(i,j) for the implementation's c" and "heavy ends: root 1 (n) is the unique
optimal root of every (0, m) ((m, n)), 1 <= m <= n-1" (the last one with a separate DP that lists all optimal
roots): n = 0..40, 5 instances per n.

## 5. Additions (caveats)

**Statement.** On every input: `obst_recursive` makes exactly (35 · 3^(n−2) − 3)/2 additions for every n ≥ 2 (4 for
n = 1, 0 for n = 0); `obst_cubic` makes exactly n(n + 1)(n + 2)/6 + 3n(n + 1)/2 − n for every n ≥ 0; `obst_knuth`
makes exactly its number of comparisons plus 2n², for every n ≥ 0.

**Proof.** *Recursion.* `weight(i, j)` with L = j − i ≥ 1 makes L additions `p[m - 1] + q[m]`, L additions inside
`sum()` (the first is `0 + item`) and `q[i] + sum(...)`: 2L + 1. A call with L ≥ 2 adds its L candidates (fact
(i)), calls `weight` (2L + 1) and computes `weight(i, j) + best` (1): 3L + 2 in its own frame. A call with L = 1
has the uncounted candidate `0 + 0`, `weight` (3) and `weight(i, j) + 0` (1, left operand a `CountingInt`): 4. A call
with L = 0 adds nothing. So A(0) = 0, A(1) = 4, and A(L) = 3L + 2 + 2 Σ_{t<L} A(t) for L ≥ 2 (the children as in
section 1). Thus A(2) = 8 + 2 · 4 = 16, and for L ≥ 3 subtracting the identity for L − 1 gives
A(L) = 3A(L − 1) + 3, i.e. A(L) + 3/2 = 3^(L−2) (A(2) + 3/2) = 35 · 3^(L−2)/2. (At L = 1 the form would give 13/3.)

*Cubic DP.* Every interval makes 2 additions for `w[i][j]` and 1 for `w[i][j] + best`; an interval of length
L ≥ 2 also adds its L candidates. Total 3 · n(n + 1)/2 + Σ_{L=2..n} (n − L + 1)L = 3n(n + 1)/2 + n(n + 1)(n + 2)/6 − n
(section 2, minus the n candidates of length 1).

*Knuth.* The length-1 loop makes 2 additions per interval for `w[i][i + 1]` and none for `c[i][i + 1]`: 2n. An
interval of length ≥ 2 makes 2 for `w[i][j]`, 1 for `w[i][j] + best`, and one per candidate, that is its number of
comparisons plus 1 (section 3 (c)). Total 2n + 4 · n(n − 1)/2 + (comparisons) = (comparisons) + 2n².

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "OBST additions: rec
(35*3^(n-2)-3)/2 (n>=2), cubic n(n+1)(n+2)/6+3n(n+1)/2-n, Knuth cmp+2n^2": recursion n = 2..11 and cubic DP
n = 0..11 on the scaling family (V2 seeds), Knuth n = 0..40 and 128 on all ten V1 families.
`experiments/2026-10-07_count_proof_checks.py`, group `bst`, line "OBST recursion additions (35*3^(n-2)-3)/2
(n>=2; 4 at n=1)": n = 1..9; line "OBST cubic DP: comparisons (n+1)n(n-1)/6, additions n(n+1)(n+2)/6+3n(n+1)/2-n,
candidate roots n(n+1)(n+2)/6": n = 0..30; line "Knuth additions = comparisons + 2n^2": n = 0..40, 3 instances
each; all on the ten V1 families and two kinds of signed values.

## 6. The problem and the recurrence

Here the frequencies are non-negative integers (the problem's domain); w(i, j) = q_i + Σ_{m=i+1..j} (p_m + q_m).
A BST on the interval (i, j) is empty if i = j (it is the single external node gap i), and otherwise a root key
k_k (i < k ≤ j) with a left BST on (i, k − 1) and a right BST on (k, j). Its cost is
cost(T) = Σ_{m=i+1..j} p_m (level(k_m) + 1) + Σ_{g=i..j} q_g level(gap g), with levels counted from its root (0).

**Lemma 6.1 (cost decomposition).** The empty tree costs 0, and a tree with root k_k and subtrees L, R costs
w(i, j) + cost(L) + cost(R). Hence c(i, j), defined by the recurrence of the entry, is the least cost of a BST on
(i, j), and k attains the minimum in the recurrence exactly when some optimal BST on (i, j) has root k_k.

*Proof.* In the empty tree gap i has level 0. Under a root, every key and gap of L and R has its level in T equal
to its level in its subtree plus 1, and the root key has level 0. So cost(T) = p_k + Σ_{L,R} p_m (level + 2) +
Σ_{L,R} q_g (level + 1) = cost(L) + cost(R) + p_k + Σ_{m≠k} p_m + Σ_{g=i..j} q_g = cost(L) + cost(R) + w(i, j),
because the gaps of L and R are i..k − 1 and k..j. L and R range independently over the BSTs on (i, k − 1) and
(k, j), so induction on j − i gives the rest. ∎

*Comparisons.* A search with three-way comparisons compares the searched value with every key on its root path. A
successful search for k_m makes level(k_m) + 1 comparisons, and an unsuccessful one ending in gap g makes
level(gap g) comparisons (the keys above that external node). So the cost is the frequency-weighted number of key
comparisons, as the problem statement says.

*A variant cost.* If every external node is counted at level + 1 instead, the cost of every tree grows by the same
constant Σ_g q_g, so the optimal trees are the same.

**Lemma 6.2 (size of the numbers).** Let S = Σ p_m + Σ q_g. Every BST on n keys has key levels ≤ n − 1 and gap
levels ≤ n, so every cost is at most n·S ≤ (n + 1)·S. Every value that the three implementations compute (w, c,
candidates c(i, k − 1) + c(k, j), w + best) lies in [0, n·S] for n ≥ 1 (for n = 0 only w(0, 0) = q_0 = S and the
result 0 occur): w(i, j) ≤ S; the lemma of section 4 gives
c(i, j) ≤ (j − i) w(i, j) for every table built by the recurrence with any root choice (so for the values of the
recursion and for the tables of both DPs); and a candidate of (i, j) is at most (k − 1 − i) w(i, k − 1) +
(j − k) w(k, j) ≤ (j − i − 1) w(i, j) by Lemma 7.1(b). So the numbers need only O(log n) more bits than the input
numbers (`input.size_measure`).

**Correctness of the plain recursion and the cubic DP.** `obst_recursive` evaluates the recurrence top-down, so by
Lemma 6.1 it returns the least cost over all BSTs on k_1..k_n. `obst_cubic` evaluates the same recurrence for
increasing lengths; the subintervals of an interval are shorter and already filled, so it returns the same value.

**Check.** `tests/test_proofs_obst.py`, `test_cost_and_recurrence`: for every tree shape (the harness's explicit
enumeration, costed from the levels) the variant cost minus Knuth's cost is Σ q_g and the cost is at most n·S, and
the minimum over shapes equals all three implementations, on 120 random instances with n = 0..7 from all ten V1
families (seed 1); every entry of the cubic DP's tables w and c lies in [0, n·S], n = 0..60 (seed 2). The V1
battery of the validator also checks all three against the shape enumeration for n ≤ 10.

## 7. Knuth's restricted root search is exact

Write c_k(i, j) = c(i, k − 1) + c(k, j) for i < k ≤ j (so c(i, j) = w(i, j) + min_k c_k(i, j)). This section proves,
for non-negative frequencies, that the range r[i][j − 1]..r[i + 1][j] always contains an optimal root, whatever
minimiser was kept in the earlier ranges. The argument is the quadrangle-inequality method (credit: Knuth 1971 for
optimum BSTs; Yao 1980 for the general form), written out here for this entry's recurrence and weights.

**Lemma 7.1 (the weights).** If all p_m, q_g ≥ 0, then for all i ≤ i′ ≤ j ≤ j′:
- (a) w(i, j) + w(i′, j′) = w(i′, j) + w(i, j′) (the quadrangle inequality, with equality);
- (b) w(i′, j) ≤ w(i, j′) (monotone under inclusion).

*Proof.* With F(j) = Σ_{l=1..j} (p_l + q_l) and G(i) = F(i) − q_i we have w(i, j) = F(j) − G(i), which gives (a).
For (b), w(i, j′) − w(i′, j) = [F(j′) − F(j)] + [G(i′) − G(i)], where F(j′) − F(j) = Σ_{l=j+1..j′} (p_l + q_l) ≥ 0,
and G(i′) − G(i) is 0 if i′ = i and q_i + Σ_{l=i+1..i′} p_l + Σ_{l=i+1..i′−1} q_l ≥ 0 if i′ > i. ∎

**Lemma 7.2 (c satisfies the quadrangle inequality).** If all frequencies are ≥ 0, then for all
0 ≤ i ≤ i′ ≤ j ≤ j′ ≤ n: c(i, j) + c(i′, j′) ≤ c(i′, j) + c(i, j′).

*Proof.* Induction on ℓ = j′ − i. If i = i′ or j = j′ both sides are equal. Otherwise i < i′ ≤ j < j′, and every
instance of the inequality used below has a smaller ℓ.

*Case i′ = j.* Since c(j, j) = 0 we must show c(i, j) + c(j, j′) ≤ c(i, j′). Let z be an optimal root of (i, j′),
so c(i, j′) = w(i, j′) + c(i, z − 1) + c(z, j′). If z ≤ j, then z is a root of (i, j), so
c(i, j) ≤ w(i, j) + c(i, z − 1) + c(z, j); the inequality for (z, j, j, j′) (smaller ℓ since z > i) gives
c(z, j) + c(j, j′) ≤ c(z, j′); and w(i, j) ≤ w(i, j′) (Lemma 7.1(b)). Adding: c(i, j) + c(j, j′) ≤ c(i, j′). If
z > j, then z is a root of (j, j′), so c(j, j′) ≤ w(j, j′) + c(j, z − 1) + c(z, j′); the inequality for
(i, j, j, z − 1) (smaller ℓ since z − 1 < j′) gives c(i, j) + c(j, z − 1) ≤ c(i, z − 1); and w(j, j′) ≤ w(i, j′).
Adding gives the claim.

*Case i′ < j.* Let y be an optimal root of (i′, j) and z one of (i, j′). If z ≤ y, then z is a root of (i, j)
(i < z ≤ y ≤ j) and y one of (i′, j′) (i′ < y ≤ j ≤ j′), so
c(i, j) + c(i′, j′) ≤ [w(i, j) + c(i, z − 1) + c(z, j)] + [w(i′, j′) + c(i′, y − 1) + c(y, j′)].
By Lemma 7.1(a), w(i, j) + w(i′, j′) = w(i′, j) + w(i, j′); by the inequality for (z, y, j, j′) (smaller ℓ since
z > i), c(z, j) + c(y, j′) ≤ c(y, j) + c(z, j′). So the right side is at most
[w(i′, j) + c(i′, y − 1) + c(y, j)] + [w(i, j′) + c(i, z − 1) + c(z, j′)] = c(i′, j) + c(i, j′). If z > y, then y is a
root of (i, j) (i < i′ < y ≤ j) and z one of (i′, j′) (i′ < y < z ≤ j′), and the same computation uses the
inequality for (i, i′, y − 1, z − 1) (i′ ≤ y − 1 ≤ z − 1, smaller ℓ since z − 1 < j′):
c(i, y − 1) + c(i′, z − 1) ≤ c(i′, y − 1) + c(i, z − 1). ∎

**Lemma 7.3 (exchange).** If all frequencies are ≥ 0:
- (M1) for i < k < k′ ≤ j < n: c_{k′}(i, j + 1) − c_k(i, j + 1) ≤ c_{k′}(i, j) − c_k(i, j);
- (M2) for i + 1 < k < k′ ≤ j: c_k(i, j) − c_{k′}(i, j) ≤ c_k(i + 1, j) − c_{k′}(i + 1, j).

*Proof.* (M1): Lemma 7.2 for (k, k′, j, j + 1) gives c(k, j) + c(k′, j + 1) ≤ c(k′, j) + c(k, j + 1); add
c(i, k − 1) + c(i, k′ − 1) to both sides. (M2): Lemma 7.2 for (i, i + 1, k − 1, k′ − 1) (valid since k ≥ i + 2)
gives c(i, k − 1) + c(i + 1, k′ − 1) ≤ c(i + 1, k − 1) + c(i, k′ − 1); add c(k, j) + c(k′, j) to both sides. ∎

In words: (M1) a larger root that is at least as good as a smaller one stays so when the right end grows; (M2) a
smaller root that is at least as good as a larger one for (i + 1, j) is at least as good for (i, j).

**Theorem 7.4 (any tie rule).** Let all frequencies be ≥ 0. Consider a *run* that sets r(i, i + 1) = i + 1 and
c′(i, i + 1) = w(i, i + 1), and then, for j − i = 2, 3, …, n, sets
c′(i, j) = w(i, j) + min_{r(i, j−1) ≤ k ≤ r(i+1, j)} [c′(i, k − 1) + c′(k, j)] and lets r(i, j) be ANY minimiser in that
range. Then every range is non-empty, c′(i, j) = c(i, j), and r(i, j) is an optimal root of (i, j), for all i < j.
In particular `obst_knuth`, which is such a run with the largest minimiser (`cand <= best` moves to later roots),
returns the optimal cost c(0, n).

*Proof.* Induction on j − i. Length 1: the only root is i + 1, and c(i, i + 1) = w(i, i + 1). Length ≥ 2: the range
is non-empty by section 3 (a), whose argument uses only that each chosen root lies in its own range. By induction,
c′ = c on all shorter intervals, so the compared values are c_k(i, j). Let a = r(i, j − 1) and b = r(i + 1, j);
by induction a is an optimal root of (i, j − 1) and b one of (i + 1, j), and a ≤ b. Let k* be an optimal root of
(i, j). If k* < a, then k* is also a root of (i, j − 1), and (M1) with (k, k′) = (k*, a) on (i, j − 1) gives
c_a(i, j) − c_{k*}(i, j) ≤ c_a(i, j − 1) − c_{k*}(i, j − 1) ≤ 0, so a is an optimal root of (i, j). If k* > b, then
b ≥ i + 2 and k* is a root of (i + 1, j), and (M2) with (k, k′) = (b, k*) gives
c_b(i, j) − c_{k*}(i, j) ≤ c_b(i + 1, j) − c_{k*}(i + 1, j) ≤ 0, so b is optimal. Otherwise k* lies in the range. In
every case the range [a, b] contains an optimal root, so the minimum over the range equals min_k c_k(i, j),
c′(i, j) = c(i, j), and every minimiser in the range is an optimal root. ∎

**Corollary 7.5 (monotone largest optimal roots).** Let K(i, j) be the largest optimal root of (i, j). Then
K(i, j − 1) ≤ K(i, j) ≤ K(i + 1, j) for j − i ≥ 2.

*Proof.* If K(i, j) < K(i, j − 1) =: a, then (M1) with (k, k′) = (K(i, j), a) on (i, j − 1) shows that a is also
optimal for (i, j), contradicting the maximality of K(i, j). If K(i, j) =: k′ > K(i + 1, j) =: b, then (M2) with
(k, k′) = (b, k′) gives 0 ≤ c_b(i, j) − c_{k′}(i, j) ≤ c_b(i + 1, j) − c_{k′}(i + 1, j), so k′ is optimal for (i + 1, j),
contradicting the maximality of b. ∎

**Arbitrary optimal roots are not monotone (caveat).** With all weights 0 every root of every interval is optimal.
The table that takes the largest optimal root j for even i and the smallest i + 1 for odd i has, for any n ≥ 3,
r(0, 3) = 3 > 2 = r(1, 3), so it violates r(i, j) ≤ r(i + 1, j); in particular it is non-monotone for every n ≥ 4,
as `caveats` says. (Theorem 7.4 does not need monotone tables: a run only ever compares inside its own ranges.)

**Relation to the theorem note.** The note
[knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/) treats length weights
w(i, j) = h(j − i) with concave h, which satisfy the reverse quadrangle inequality (its Remark 3), and proves
exactness of the same restricted run there with different, case-specific lemmas. Its observation that non-empty
ranges telescope is section 3 (b) here; none of its other lemmas is needed for this entry's weights, which are
covered by Lemmas 7.1–7.3.

**Check.** `tests/test_proofs_obst.py`, `test_weights_quadrangle`: Lemma 7.1 (a), (b) on 200 random non-negative
instances, n = 0..8 (seed 3); `test_c_quadrangle`: Lemma 7.2 for every quadruple on every instance with
frequencies in {0, 1, 2} for n = 0..3, in {0, 1} for n = 4, 5, and on 300 random instances from the V1 families
with n = 0..12 (seed 4); `test_any_tie_rule`: runs written in the test with the largest, smallest, random and an
alternating tie rule give c′ = c and only optimal roots (checked against the full optimal root sets) on 400
tie-heavy instances, n = 2..10 (seed 5), and `obst_knuth`'s own tables c and r (read at return) satisfy the same;
`test_monotone_largest_roots`: Corollary 7.5 on the same instances; `test_mixed_table_not_monotone`: the mixed table
on zero weights violates r(0, 3) ≤ r(1, 3) for n = 3..12. `experiments/2026-10-07b_optimal_bst_ties.py` (5 tie
rules, 6006 tie-heavy instances; the mixed table) reports the same findings.

## 8. Time and space

**Plain recursion: Θ(3ⁿ) time, depth n + 1.** Section 1 gives exactly 3ⁿ calls. A call on an interval of length
L ≥ 1 does O(L + 1) work (L candidates, and `weight` sums L terms). Let Λ(L) be the sum of the lengths of all calls
below and including a call of length L; then Λ(0) = 0 and Λ(L) = L + 2 Σ_{t<L} Λ(t), so Λ(1) = 1 and
Λ(L) = 3Λ(L − 1) + 1, i.e. Λ(L) = (3^L − 1)/2. The total work is Θ(3ⁿ + Λ(n)) = Θ(3ⁿ); recomputing w(i, j) in
every call does not change this (`caveats`). The length decreases by at least 1 from a call to its callee, and the
first root k = i + 1 calls cost(i, i) and then cost(i + 1, j), so the chain cost(0, n) → cost(1, n) → … → cost(n, n)
has n + 1 calls: the nesting depth of `cost` is n + 1, and the space is Θ(n) (O(1) frames per call).

**Cubic DP: Θ(n³) time, Θ(n²) space.** Section 2 gives n(n + 1)(n + 2)/6 candidates; the tables w and c have
(n + 1)² entries each.

**Knuth: Θ(n²) time and space on every input.** By section 3 (b) the candidates of length L number
(n − L + 1) + r[n−L+1][n] − r[0][L−1], between n − L + 1 and 2n − L; summed over L = 2..n this is between
n(n − 1)/2 and (n − 1)(3n − 2)/2. The three tables w, c, r have (n + 1)² entries each, and the length-1 loop does
O(n). So the time and the space are Θ(n²), for any values (this count does not use §7). For non-negative frequencies
the result is also correct (Theorem 7.4).

**Check.** `tests/test_proofs_obst.py`, `test_time_and_space`: the nesting depth of `cost` is n + 1 (profiler hook)
and the sum of the interval lengths over all calls is (3ⁿ − 1)/2, for n = 0..9; the tables of both DPs have n + 1
rows of length n + 1 at return, and Knuth's candidates lie between n(n − 1)/2 and (n − 1)(3n − 2)/2, for
n = 0..60 (seed 6). The exact comparison counts are checked by the scripts of sections 1–5.

## 9. The separations (T2, T3)

All three implementations return the optimal cost (§6, Theorem 7.4). T2: the recursion is Θ(3ⁿ) and the cubic DP
Θ(n³) (§8); the recursion recomputes the (n + 1)(n + 2)/2 intervals. T3: the cubic DP is Θ(n³) and Knuth's DP
Θ(n²) on every input (§8), because the root ranges telescope (section 3 (b)).

## Claim map (beyond the counts of sections 1–5)

| Claim (location) | Proof |
|---|---|
| cost = weighted comparisons; recurrence; recursion and cubic DP correct | §6, Lemma 6.1 |
| costs at most (n + 1) × total frequency (`input.size_measure`) | Lemma 6.2 |
| the variant cost (external nodes at level + 1) differs by Σ q_j, same optimal trees (`caveats`, README) | §6 |
| w satisfies the quadrangle inequality with equality and is monotone | Lemma 7.1 |
| c satisfies the quadrangle inequality; the roots can be chosen monotone | Lemma 7.2, Corollary 7.5 |
| Knuth's range contains an optimal root; any minimiser kept works; no range is empty | Theorem 7.4, section 3 (a) |
| arbitrary optimal roots need not be monotone (e.g. zero weights, n ≥ 4) | §7 |
| recursion Θ(3ⁿ) despite recomputing w; Θ(n) depth; cubic Θ(n³), Θ(n²) space; Knuth Θ(n²) on every input | §8 |
| T2 and T3 | §9 |
