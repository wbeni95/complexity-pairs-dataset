# Proofs: counting n-bit integers with a cheap representation X² + C

This file proves every claim that this entry makes about its problem and its three algorithms (in `entry.json`,
`README.md` and the docstrings of the code). Section 1 proves the exact counts reported for V2, for every n, from
the code in `implementations/`. Sections 2 to 7 prove the lemmas and the correctness of the three algorithms,
section 8 the word sizes, section 9 the time and space bounds, section 10 the facts used by the V1 oracle and
section 11 the remaining factual statements. Each proof is followed by the deterministic checks of its computable
facts and the ranges they cover. A check covers only its range; the proofs cover the whole domain.

Nothing in this entry rests on the literature. The one item under `background` in `entry.json` is the
machine-model assumption of section 0. The literature search in README.md is a statement about that search
(provenance), not a claim about the problem.

Checks referred to below:
- **X**: `experiments/2026-10-07_square_plus_offset_checks.py`, by section letter (X §A, …) and check line;
- **U**: `tests/test_entry_square_plus_offset.py`, by test name;
- **V**: `python tools/validate.py pairs/square-plus-offset-count-enumeration-vs-intervals-vs-groups --scaling -v`
  (the V1 runs and the V2 counts).

## 0. Definitions, elementary facts and cost model

For an integer v, L(v) is the number of binary digits of |v|, with L(0) = 1. For k ≥ 0 and X ≥ 0 let C = k − X² and
f_k(X) = L(X) + L(C) + [C < 0]. For n ≥ 0, S_n = {k : 0 ≤ k < 2ⁿ, f_k(X) ≤ n − 4 for some X ≥ 0}. Throughout,
r = isqrt(k) = ⌊√k⌋, v = n − 4, B = 2ⁿ − 1 and T = isqrt(B) + 1.

In the code, `bit_length(v)` (implementations) and `_L(v)` (harness) compute L: for v ≠ 0, `abs(v).bit_length()`
is the number of binary digits of |v| (the documented meaning of `int.bit_length`), and L(0) = 1 is set explicitly.
`representation_cost(k, x)` and `_cost(k, x)` return L(x) + L(c) for c = k − x² ≥ 0 and L(x) + L(c) + 1 for c < 0,
that is f_k(x).

Elementary facts:
- **(F1)** L is non-decreasing in |v|, and for w ≥ 1, L(v) ≤ w iff |v| ≤ 2^w − 1.
- **(F2)** f_k(X) ≥ 2 for all k and X, since L ≥ 1. Hence S_n = ∅ for n ≤ 5, where n − 4 ≤ 1.
- **(F3)** T ≤ 2^(n/2) + 1, because isqrt(B) ≤ √B < 2^(n/2). So T² ≤ 2ⁿ + 2^(n/2+1) + 1, which is below 2^(n+2) for
  every n ≥ 0 (T = 1 for n = 0), and T² + 2^(n−5) < 2^(n+1) for n ≥ 6 (there 2^(n/2+1) ≤ 2ⁿ/4, 2^(n−5) = 2ⁿ/32 and
  1 < 2ⁿ/2).
- **(F4)** For even n ≥ 0, isqrt(2ⁿ − 1) = 2^(n/2) − 1 and T = 2^(n/2): for n ≥ 2,
  (2^(n/2) − 1)² = 2ⁿ − 2^(n/2+1) + 1 ≤ 2ⁿ − 1 < (2^(n/2))², and isqrt(0) = 0. For odd n ≥ 3,
  2^((n−1)/2) < T < 2^((n+1)/2): 2^(n−1) ≤ 2ⁿ − 1 gives isqrt(B) ≥ 2^((n−1)/2), and T ≤ 2^(n/2) + 1 < 2^((n+1)/2)
  because 2^(n/2)(√2 − 1) > 1 for n ≥ 3. Consequently L(T) = ⌊n/2⌋ + 1 for every n ≥ 2 (L(T) = 1 for n = 0 and 2 for
  n = 1), and T is a power of two for every even n but for no odd n ≥ 3.

**Cost model (machine-model assumption, listed under `background`).** Statements about word operations, time and
space are made on a word RAM with words of n + 3 bits:
- addition, subtraction, multiplication, integer division, comparison, shifts and `int.bit_length` on integers of
  absolute value below 2^(n+2) cost one word operation each (section 8 shows that for n ≥ 1 the three algorithms
  handle no other integers; n = 0 is a single constant-size case);
- creating a `range` and each step of iterating over it cost O(1) word operations, and a range object takes O(1)
  words;
- `math.isqrt(q)` returns ⌊√q⌋, and one call with 0 ≤ q < 2^(n+2) costs O(n) word operations.

The Python documentation states what `int.bit_length` and `math.isqrt` return, that a range yields start,
start + step, … below stop, and that a range object always takes the same small amount of memory. The costs are
assumed, not proved here. The exact counts (section 1), every correctness statement and the word sizes (section 8)
do not depend on the assumed costs; they use only the documented results. A3 does not call `math.isqrt`: it uses the Newton iteration of section 6, which is
analysed in the model itself.

## 1. The exact counts reported for V2

Each implementation returns (|S_n|, work), and `harness.reported_cost` returns work.

**1.1 Enumeration (A1).** *Statement.* For every n ≥ 0, `count_by_enumeration(n)` reports exactly 3·2ⁿ evaluations
of f_k.

*Proof.* The loop `for k in range(1 << n)` runs 2ⁿ times. Each iteration evaluates `representation_cost` once with
x = 0 and once for each x in (r, r + 1), and executes `evaluations += 3` once. Nothing else changes `evaluations`,
which starts at 0. ∎

*Check.* X §V "enumeration: exactly 3 * 2^n cost evaluations" (n = 0..22); U `test_exact_work_counts` (n = 0..14);
V: the V2 fit on n = 6, 8, …, 16 and the shape block on n = 1..16.

**1.2 Interval sweep (A2).** *Statement.* For every n ≥ 0, `count_by_interval_sweep(n)` reports exactly
T + 1 = isqrt(2ⁿ − 1) + 2 roots, which is 2^(n/2) + 1 for every even n.

*Proof.* `examined += 1` is the first statement of the body of `for x in range(T + 1)`, which runs T + 1 times;
`continue` skips only later statements. The even case is (F4). ∎

*Check.* X §V "interval sweep: exactly isqrt(2^n - 1) + 2 roots" (n = 0..42, and even n = 0..42);
U `test_exact_work_counts` (n = 1..30; even n = 0..30); V: the V2 fit on n = 12, 16, …, 32 and the shape block on
n = 2, 4, …, 32.

**1.3 Root groups (A3).** *Statement.* For every n ≥ 0, `count_by_groups(n)` reports exactly
max(0, min(L(T), n − 5)) groups. This is 0 for n ≤ 5, 5 for n = 10, and ⌊n/2⌋ + 1 for every n ≥ 11, so n/2 + 1 on
the V2 sizes n = 12, 24, …, 384 and on the shape grid n = 12, 14, …, 60.

*Proof.* The loop of `count_groups` takes l = 1, 2, … in turn. It sets a = 0 for l = 1 and a = 2^(l−1) otherwise,
and w = v − l, and it stops at the first l with a > T or w < 1. Otherwise it executes `groups += 1` and moves on to
l + 1. Now a ≤ T iff l ≤ L(T): for l = 1 because T ≥ 1, and for l ≥ 2 because 2^(l−1) ≤ T iff l − 1 ≤ L(T) − 1.
Also w ≥ 1 iff l ≤ n − 5. Both conditions are monotone in l, so exactly the groups l = 1, …, min(L(T), n − 5) are
processed, and none if this minimum is ≤ 0. By (F4), L(T) = ⌊n/2⌋ + 1 for n ≥ 2, and ⌊n/2⌋ + 1 ≤ n − 5 iff
⌈n/2⌉ ≥ 6 iff n ≥ 11. For n = 10 the minimum is min(6, 5) = 5. For n ≤ 5, n − 5 ≤ 0. ∎

*Check.* X §S "L(T) = floor(n/2) + 1" (n = 2..3000) and "groups = max(0, min(L(T), n - 5))" (n = 0..400); X §V
"groups: exactly floor(n/2) + 1 root groups" (n = 11..400); X §T (n = 200: 101 groups); U `test_exact_work_counts`
(n = 11..300); V: the V2 fit on n = 12, 24, …, 384 and the shape block on n = 12, 14, …, 60.

The three reported counts are functions of n alone; the only library result they use is `math.isqrt`'s
documented value ⌊√q⌋ (in A2's T), so they do not depend on the Python version.

## 2. Lemma 0 and Lemma A

**Lemma 0 (a window for brute force).** If X² − k ≥ 2^L(k), then f_k(X) > f_k(0). So every minimiser of f_k
satisfies X² < k + 2^L(k).

*Proof.* Then C = k − X² ≤ −2^L(k), so L(C) ≥ L(k) + 1 and f_k(X) ≥ 1 + (L(k) + 1) + 1 > 1 + L(k) = f_k(0). ∎

**Lemma A (three candidates suffice).** For every integer k ≥ 0: min_{X ≥ 0} f_k(X) = min(f_k(0), f_k(r), f_k(r + 1)).

*Proof.* We show f_k(X) ≥ min(f_k(0), f_k(r), f_k(r + 1)) for every X ∉ {0, r, r + 1}.

(i) **X ≥ r + 2.** Then X² > (r + 1)² > k, so C < 0 and f_k(X) = L(X) + L(X² − k) + 1. Since X > r + 1 and
X² − k > (r + 1)² − k > 0, monotonicity of L gives f_k(X) ≥ L(r + 1) + L((r + 1)² − k) + 1 = f_k(r + 1).

(ii) **1 ≤ X ≤ r − 1 and L(X) = L(r).** Then k − X² > k − r² ≥ 0, so f_k(X) = L(X) + L(k − X²) ≥ L(r) + L(k − r²) =
f_k(r).

(iii) **1 ≤ X ≤ r − 1 and a := L(X) < b := L(r).** Here r ≥ 2, so k ≥ 4. Let p = L(k) − 1, so 2^p ≤ k < 2^(p+1) and
f_k(0) = p + 2. From 2^⌊p/2⌋ ≤ 2^(p/2) ≤ √k < 2^((p+1)/2) ≤ 2^(⌊p/2⌋+1) we get 2^⌊p/2⌋ ≤ r < 2^(⌊p/2⌋+1), so
b = ⌊p/2⌋ + 1. If f_k(X) ≥ f_k(0) there is nothing to show, so assume f_k(X) ≤ p + 1. Then C = k − X² > 0 and
L(C) ≤ p + 1 − a, i.e. C < 2^(p+1−a).

- *a ≥ 2.* Then C < 2^(p−1), and k ≥ 2^p gives X² > 2^(p−1). With X < 2^a this gives 2a > p − 1, i.e. 2a ≥ p.
  Together with a ≤ b − 1 = ⌊p/2⌋, p is even and a = q := p/2. Now X ≤ 2^q − 1, so
  k < X² + 2^(q+1) ≤ 2^(2q) − 2^(q+1) + 1 + 2^(q+1) = 2^(2q) + 1. With k ≥ 2^(2q) this forces k = 2^(2q), r = 2^q and
  f_k(r) = (q + 1) + 1 = q + 2. Also C = k − X² ≥ 2^(2q) − (2^q − 1)² = 2^(q+1) − 1 ≥ 2^q, so
  f_k(X) ≥ q + (q + 1) = 2q + 1 ≥ q + 2 = f_k(r), because q ≥ 1.
- *a = 1.* Then X = 1, and k − 1 < 2^p gives k = 2^p (with p ≥ 2) and f_k(1) = 1 + L(2^p − 1) = p + 1.
  - If p = 2q is even (q ≥ 1): r = 2^q and f_k(r) = q + 2 ≤ 2q + 1 = f_k(1).
  - If p = 2q + 1 is odd (q ≥ 1): k = 2^(2q+1) is not a square, so d₁ = k − r² ≥ 1 and d₂ = (r + 1)² − k ≥ 1, with
    d₁ + d₂ = 2r + 1. From 2^q ≤ √k = 2^(q+1/2) we get 2^q ≤ r < 2^(q+1/2), and 2^(q+1/2) + 1 < 2^(q+1) for q ≥ 1, so
    L(r) = L(r + 1) = q + 1. (The bound 2^q ≤ r cannot be made strict: k = 8 has r = 2 = 2^1.) Hence
    f_k(r) = q + 1 + L(d₁) and f_k(r + 1) = q + 2 + L(d₂). If both exceeded f_k(1) = 2q + 2, then d₁ ≥ 2^(q+1) and
    d₂ ≥ 2^q, so 2r + 1 ≥ 3·2^q. With r < 2^(q+1/2) < 1.4143·2^q this gives 0.1714·2^q < 1, i.e. q ≤ 2. The two
    remaining cases fail directly: k = 8 has r = 2 and d₂ = 1 < 2^1, and k = 32 has r = 5 and d₁ = 7 < 2^3. So
    min(f_k(r), f_k(r + 1)) ≤ f_k(1).

Every X ∉ {0, r, r + 1} falls under (i), or under (ii) or (iii) (X < r implies L(X) ≤ L(r)). ∎

**Remark (roots below r).** A root below r can be cheaper than r, so the lemma does not follow from comparing every
root with r alone. For k = 80 (r = 8): f(0) = 8, f(7) = 3 + L(31) = 8, f(8) = 4 + L(16) = 9, and the minimum is
f(9) = 4 + L(−1) + 1 = 6. By Lemma 0 only X ≤ 14 can be minimisers (14² = 196 < 80 + 2^7 = 208 ≤ 15²), and every
X ≤ 14 other than 9 costs at least 8, so the minimum is attained only at r + 1 = 9. In the proof, X = 7 falls under
case (iii) (L(7) = 3 < L(8) = 4).

**Decision version.** By Lemma A, k ∈ S_n iff min(f_k(0), f_k(r), f_k(r + 1)) ≤ n − 4: one integer square root and
three cost evaluations.

*Check.* X §A: Lemma A against a brute force over all roots in the window of Lemma 0 for every k < 2^18 (0
mismatches); Lemma 0 on k < 2^10 with the 40 roots past the window; the cases k = 8 and k = 32 with their r, d₁, d₂
and costs; k = 8 attaining 2^q = r; k = 80 (all costs X = 0..14, the window, case (iii)). U
`test_lemma_a_against_all_roots` (every k < 2^12), `test_examples`.

## 3. Lemma B (one interval per root)

**Lemma B.** For a root X let w = v − L(X). If w ≥ 1, let I_X = [max(0, X² − m), X² + 2^w − 1] with m = 2^(w−1) − 1
if w ≥ 2 and m = 0 if w = 1; if w ≤ 0, let I_X = ∅. Then

  S_n = ⋃_{X=0}^{T} ( I_X ∩ [0, B] ).

*Proof.* I_X = {k ≥ 0 : f_k(X) ≤ v}: for C ≥ 0 the condition is L(C) ≤ w, i.e. C ≤ 2^w − 1 (also for C = 0, since
L(0) = 1 ≤ w); for C < 0 it is L(|C|) ≤ w − 1, i.e. |C| ≤ 2^(w−1) − 1 if w ≥ 2, and no negative C qualifies if
w = 1; if w ≤ 0 nothing qualifies, as L ≥ 1 (all by (F1)). Hence S_n = ⋃_{X≥0} (I_X ∩ [0, B]). For k ≤ B we have
r ≤ isqrt(B) and r + 1 ≤ T, and every X ≥ r + 2 satisfies f_k(X) ≥ f_k(r + 1) by case (i) of Lemma A. So a k covered
by some X > T is also covered by r + 1 ≤ T, and the roots X ≤ T suffice. ∎

Only case (i) of Lemma A is used here. Clipping can leave an interval empty: for n = 13, T = 91, L(91) = 7, w = 2 and
m = 1, so X = 91 has X² − m = 8 280 > B = 8 191. Such an interval contributes nothing.

*Check.* X §B: the sorted union equals the brute-force count (all roots in the window of Lemma 0, every k) for
n = 1..16; the example n = 13, X = 91. X §C: interval sweep = groups = sorted union for n = 0..42.

## 4. Correctness of A1 and A2

**4.1 A1 returns |S_n|.** By induction, r = isqrt(k − 1) when iteration k ≥ 1 starts, and r = 0 = isqrt(0) for
k = 0. Since r² ≤ k and isqrt(k) ≤ isqrt(k − 1) + 1, the loop `while (r + 1) * (r + 1) <= k: r += 1` increments r
isqrt(k) − isqrt(k − 1) ∈ {0, 1} times and stops at r = isqrt(k), the largest r with r² ≤ k. Summing over k, it
increments r exactly isqrt(2ⁿ − 1) times and evaluates its test 2ⁿ + isqrt(2ⁿ − 1) times; the comparison
`best <= budget` is made exactly 2ⁿ times. Then
best = min(f_k(0), f_k(r), f_k(r + 1)) = min_X f_k(X) by Lemma A, and `covered` counts the k < 2ⁿ with
min_X f_k(X) ≤ n − 4, that is |S_n|. ∎

**4.2 A2 returns |S_n|.** For each x ≤ T the loop skips w < 1 (I_x = ∅), computes lo = max(0, x² − m) and
hi = min(x² + 2^w − 1, B), so that I_x ∩ [0, B] = [lo, hi] if lo ≤ hi, and skips the empty ones. By Lemma C
(section 5) the left ends x² − m strictly increase over the roots with w ≥ 1, so the left ends lo of the intervals
that are not skipped are non-decreasing in x. For intervals taken in order of non-decreasing left ends, the merge
keeps this invariant: [start, end] is the union of the intervals taken since the last component was closed, end is
the largest right end so far, and `total` is the size of the closed components. An interval with lo ≤ end + 1
overlaps or touches [start, end] and has lo ≥ start, so the union becomes [start, max(end, hi)]. An interval with
lo > end + 1 is disjoint from and not adjacent to every earlier interval, and so is every later one, so the closed
component is a component of the whole union. At the end, total = |⋃_{x≤T} (I_x ∩ [0, B])| = |S_n| by Lemma B. ∎

*Check.* X §C: enumeration = interval sweep = groups for n = 0..22, interval sweep = groups = sorted union for
n = 0..42. X §V "enumeration, counted in an instrumented copy": exactly isqrt(2ⁿ − 1) increments of r,
2ⁿ + isqrt(2ⁿ − 1) evaluations of the loop test and 2ⁿ budget comparisons, n = 0..16. V: V1 against the independent
oracle (section 10) for n = 0..17, 19, …, 33, 34. U `test_agree_and_check`.

## 5. A3: Lemmas C, D, E and Theorem A3

For a root X with w = v − L(X) ≥ 1 write s = 2^w − 1 and J_X = [X² − m, X² + s] (unclipped, so I_X = J_X ∩ [0, ∞)).
Let R be the set of roots X ≤ T with w ≥ 1; since L is non-decreasing, R is an initial segment of {0, …, T}. With
U = ⋃_{X∈R} J_X, Lemma B gives

  |S_n| = |U| − |U ∩ (−∞, −1]| − |U ∩ [B + 1, ∞)|.

Group l consists of the roots X ∈ {0, 1} for l = 1 and X ∈ [2^(l−1), 2^l − 1] for l ≥ 2, cut at T. Inside a group,
w = v − l, s and m are constant.

**Lemma C (left ends increase).** For X < Y in R: X² − m(X) < Y² − m(Y).

*Proof.* L(X) ≤ L(Y), so w(X) ≥ w(Y) and m(X) ≥ m(Y), because m = 2^(w−1) − 1 (or 0 for w = 1) is non-decreasing in
w; and X² < Y². ∎

So U can be measured by one sweep in X order, as in 4.2: keep the current component [c, e] (e = largest right end so
far); J_X starts a new component iff its left end exceeds e + 1, and otherwise the component becomes
[c, max(e, X² + s)].

**Lemma D (a group in O(1) steps).** Let [a, b] be a group (a < b) and let E be the right end e after J_a has been
swept. Put t₁ = ⌊(s + m + 2)/2⌋ + 1 and t₂ = isqrt(E + 1 + m) + 1. For X ∈ (a, b], J_X starts a new component iff
X ≥ t₁ and X ≥ t₂. Consequently, with x_s = max(a + 1, t₁, t₂): the roots a + 1, …, min(x_s − 1, b) extend the current
component to the right end max(E, min(x_s − 1, b)² + s); and if x_s ≤ b, every root X ∈ [x_s, b − 1] is a component
J_X of its own, of size s + m + 1 = 2^w + m, and J_b becomes the current component.

*Proof.* Inside the group the right ends X² + s increase, and E ≥ every right end before the group, so the right end
of the current component just before X ∈ (a, b] is max(E, (X − 1)² + s). Thus J_X starts a new component iff
X² − m > (X − 1)² + s + 1, i.e. 2X > s + m + 2, i.e. X ≥ t₁, and X² − m > E + 1, i.e. X ≥ t₂ (E + 1 + m ≥ 0
because E is at least the right end of J_0, which is positive). Both conditions are upward closed in X, so the
starting roots of (a, b] are exactly [x_s, b]. A non-starting root extends the component to max(e, X² + s). For a
starting X < b, the next root starts a component too, so its left end exceeds X² + s + 1, and by Lemma C every later
left end does as well: J_X is a whole component. ∎

The first group is {0, 1}; there t₁ ≥ 2 because s ≥ 1, so J_1 always joins J_0.

**Lemma E (the parts outside [0, B]).** Assume R ≠ ∅ (equivalently n ≥ 6, since w(0) = n − 5).
- (a) U ∩ (−∞, −1] = [−m₁, −1], where m₁ is the m of group 1. Indeed J_0 = [−m₁, s] with s ≥ 1, and by Lemma C no
  left end is smaller than −m₁.
- (b) U ∩ [B + 1, ∞) is the union of the intervals [max(X² − m, B + 1), X² + s] over the X ∈ R with X² + s > B, and
  their left ends are non-decreasing in X (Lemma C). In a group these X are the roots with X ≥ isqrt(B − s) + 1
  (B − s ≥ 0, because s ≤ 2^(n−5) − 1).
- (c) At most two X ∈ R satisfy X² + s ≥ 2ⁿ.

*Proof of (c).* For such X, w ≤ v − 1 = n − 5 gives X² > 2ⁿ − 2^w ≥ 2ⁿ − 2^(n−5) > 2^(n−1), so X > 2^((n−1)/2). For
odd n this power of two is an integer, so X ≥ 2^((n−1)/2) + 1 and L(X) ≥ (n + 1)/2; for even n, X > 2^(n/2−1) gives
L(X) ≥ n/2. In both cases L(X) ≥ n/2, hence w ≤ n − 4 − n/2 and 2^w ≤ 2^(n/2−4). So every such X lies in the real
interval (√(2ⁿ − 2^(n/2−4)), 2^(n/2) + 1], because T ≤ 2^(n/2) + 1. Its length is
1 + 2^(n/2−4)/(2^(n/2) + √(2ⁿ − 2^(n/2−4))) < 1 + 2^(−4), so it contains at most two integers. ∎

**Theorem A3.** For every n ≥ 0, `count_by_groups(n)` returns |S_n|.

*Proof.* For n ≤ 5 no group is processed (w = n − 5 ≤ 0 already for l = 1), `start` stays None and the function
returns 0, which is |S_n| by (F2). For n ≥ 6, `count_groups` processes the groups l = 1, …, min(L(T), n − 5)
(section 1.3), which are exactly the groups that meet R. For each group [a, b] (b = min(2^l − 1, T)) it does the
following.
- It sweeps J_a by the generic rule (start a component if `start` is None, close the current one and start a new
  one if a² − m > end + 1, otherwise extend `end`). Then `end` is the E of Lemma D.
- If b > a, it computes t1 = t₁, t2 = isqrt_newton(end + 1 + m) + 1 = t₂ (section 6) and xs = x_s, sets `end` to
  max(`end`, min(xs − 1, b)² + s) if xs − 1 ≥ a + 1, and, if xs ≤ b, closes the current component, adds the sizes
  (b − xs)·(s + m + 1) of the components J_X, X ∈ [xs, b − 1], and makes J_b the current component. This is Lemma D.
- It appends to `tops` the parts [max(x² − m, B + 1), x² + s] of the roots x ∈ [x0, b] of the group with
  x0 = max(a, isqrt_newton(B − s) + 1): these are the roots of the group with x² + s > B, by Lemma E(b). (The branch
  `q < 0` is never taken, because B − s ≥ 0.)

`below` is set to m₁ in group 1. After the loop the last component is closed, so `closed` = |U| (Lemmas C and D:
the sweep in X order measures the union, and every closed part is a whole component). The parts in `tops` have
non-decreasing left ends (Lemma E(b)), so the same merge as in 4.2 gives `above` = |U ∩ [B + 1, ∞)|. The function
returns closed − below − above = |U| − m₁ − |U ∩ [B + 1, ∞)| = |S_n| by Lemma E(a) and Lemma B. ∎

*Check.* X §S: strictly increasing left ends (Lemma C) and component starts forming a suffix of every group
(Lemma D), n = 5..36 (895 002 roots); the part below 0, n = 6..60, every root, without using Lemma C; Lemma E(c) as
recorded by the implementation (n = 5..400) and by a direct count that does not use it (n = 6..3000). X §C:
groups = enumeration (n = 0..22) and = interval sweep = sorted union (n = 0..42). V: V1 against the independent
oracle for n = 0..17, 19, …, 33, 34. U `test_agree_and_check` (n ≤ 30), `test_group_structure` (n = 5..300),
`test_above_range_direct` (n = 6..300).

## 6. Lemma N (integer square root by Newton's iteration)

**Lemma N.** For an integer q ≥ 1 start from x₀ = 2^⌈L(q)/2⌉ and iterate y = ⌊(x + ⌊q/x⌋)/2⌋; stop as soon as
y ≥ x and return x. The result is ⌊√q⌋, after at most ⌊log₂(2 + log₂ q)⌋ + 2 iterations.

*Proof.* ⌊(x + ⌊q/x⌋)/2⌋ = ⌊(x + q/x)/2⌋ ≥ ⌊√q⌋ by the AM–GM inequality, so no iterate drops below ⌊√q⌋ (x₀ > √q
because q < 2^L(q)). If x > ⌊√q⌋, then x > √q, so q/x < x and y < x. Hence the loop stops exactly when x = ⌊√q⌋.
For the count, let y₀ = x₀ and y_(t+1) = φ(y_t) with φ(y) = (y + q/y)/2, which is increasing on [√q, ∞). While
x_t > ⌊√q⌋ we have √q < x_t ≤ y_t (induction: x_(t+1) ≤ φ(x_t) ≤ φ(y_t)). The relative error ε_t = y_t/√q − 1
satisfies ε_(t+1) = ε_t²/(2(1 + ε_t)) ≤ ε_t²/2, and ε₀ ≤ 1 because √q ≥ 2^((L(q)−1)/2) and x₀ ≤ 2^((L(q)+1)/2);
so ε_t ≤ 2^(1−2^t). For t* = ⌊log₂(2 + log₂ q)⌋ we have 2^(t*+1) > 2 + log₂ q, hence ε_(t*)·√q < 1 and
x_(t*) < √q + 1, i.e. x_(t*) ≤ ⌊√q⌋ + 1. One more step reaches ⌊√q⌋ if necessary, and one more step is the stopping
test, so at most t* + 2 iterations are made. ∎

`isqrt_newton` is this iteration: it returns 0 for q = 0; otherwise it starts from
`1 << ((q.bit_length() + 1) // 2)` = 2^⌈L(q)/2⌉, and one iteration is one execution of the loop body (t = x + q // x,
y = t // 2, the test y ≥ x). In exact integers, t* + 2 is the largest t with 2^(2^t − 2) ≤ q, plus 2, which is how
the checks compute it.

*Check.* X §N: equal to `math.isqrt` on every q < 2^16 and on 20 000 seeded q < 2^600 (85 536 values), within the
step bound there and on every square root A3 computes for n = 1..400 (80 965 calls). U `test_newton_isqrt` (every
q < 2^12 and 3 000 seeded q < 2^400).

## 7. The square roots of A3

*Statement.* For every n ≥ 1 every argument q of `isqrt_newton` in A3 is below 2^(n+2), and each call makes at most
⌊log₂(2 + log₂ q)⌋ + 2 ≤ ⌊log₂(n + 4)⌋ + 2 iterations (q ≥ 1). For every n ≥ 11, A3 makes exactly n + 2 calls.

*Proof.* One call is for T. In each processed group there is one call with argument B − s, and, if b > a, one with
argument end + 1 + m. b = a happens only if T = a = 2^(l−1) for a processed group l ≥ 2, that is when T is a power of
two and the group L(T) is processed. For n ≥ 11 all L(T) groups are processed (section 1.3), and by (F4) T is a power
of two iff n is even. So there are 1 + 2(⌊n/2⌋ + 1) − [n even] = n + 2 calls. The arguments are B < 2ⁿ, B − s < 2ⁿ
and end + 1 + m < 2^(n+1) + 2^(n−6) (section 8), all below 2^(n+2). With log₂ q < n + 2 Lemma N gives the iteration
bound; ⌊log₂(n + 4)⌋ + 2 is computed exactly as (n + 4).bit_length() + 1. ∎

*Check.* X §V: "exactly n + 2 integer square roots" (n = 11..400) and "every square-root argument is below 2^(n+2)
and needs at most floor(log2(n + 4)) + 2 iterations" (n = 1..400, 80 965 calls), both counted by a wrapper around the
function; X §N (the exact bound of Lemma N on every call, n = 1..400). U `test_exact_work_counts` (n = 11..300, by
the implementation's own call counter).

## 8. Word sizes

*Statement.* For every n ≥ 1, every integer that A1, A2 or A3 forms (run as the validator runs them, without the
optional statistics argument of `count_groups`) has absolute value below 2^(n+2): every value of every expression in
their code, including loop variables, counters, intermediate products and the internal values of Newton's
iteration. For n = 0 every such integer has absolute value at most 5 (the budget n − 4 = −4 and
w = −5).

*Proof.* Let n ≥ 1. Common to all three: n, v = n − 4 (|v| ≤ max(3, n)), small constants, 2ⁿ = `1 << n` and B. A bit
length of a number below 2^(n+2) is at most n + 2, so every cost f is at most 2(n + 2) + 1 = 2n + 5 < 2^(n+2).

- *A1.* k < 2ⁿ; r ≤ isqrt(2ⁿ − 1), so r + 1 ≤ T and (r + 1)·(r + 1) ≤ T² < 2^(n+2) by (F3). For x ∈ {0, r, r + 1},
  x·x ≤ T² and |c| = |k − x²| ≤ max(k, x²) < 2^(n+2). `covered` ≤ 2ⁿ and `evaluations` ≤ 3·2ⁿ < 2^(n+2).
- *A2.* x ≤ T, `examined` ≤ T + 1, and w = v − L(x) satisfies v − L(T) ≤ w ≤ v − 1, so
  |w| ≤ |v| + L(T) ≤ max(3, n) + ⌊n/2⌋ + 2 < 2^(n+2). A root with w ≥ 1 exists only for n ≥ 6; then
  2^(w−1) ≤ 2^w ≤ 2^(n−5), m < 2^(n−6), x·x ≤ T² < 2^(n+1), x² − m > −2^(n−6), x² + 2^w − 1 ≤ T² + 2^(n−5) < 2^(n+1)
  (F3); lo, hi, start and end lie in [0, B], end + 1 ≤ 2ⁿ, and `total` and every end − start + 1 are sizes of
  disjoint subsets of [0, B], at most 2ⁿ. `isqrt(B)` has argument and result below 2ⁿ.
- *A3, n ≤ 5.* The function computes v, B < 2ⁿ, T ≤ 6 by Newton's iteration on q = B (its values are covered by
  the last item), l = 1, a = 0 and w = n − 5 ∈ [−4, 0], and stops.
- *A3, n ≥ 6.* The loop computes a and w for l ≤ min(L(T), n − 5) + 1, so a ≤ 2^L(T) ≤ 2T; for a processed group
  b ≤ T and (1 << l) − 1 < 2T; 1 ≤ w ≤ n − 5, so m < 2^(n−6) and s < 2^(n−5); t₁ ≤ s + m + 2 < 2ⁿ. Left ends are
  at least −m₁ > −2^(n−6) (Lemma C), and right ends at most T² + s < 2^(n+1) (F3); a², b², x² and min(xs − 1, b)² are
  at most T². end + 1 + m < 2^(n+1) + 2^(n−6), so t₂ < 2^(n/2+1) + 1 and xs = max(a + 1, t₁, t₂) < 2^(n+2). Every
  count (`closed`, `below`, `above`, each end − start + 1) is at most |U| ≤ (largest right end) − (smallest left
  end) + 1 < 2^(n+1) + 2^(n−6) + 1 < 2^(n+2), and the products (b − xs)(s + m + 1) are sizes of disjoint parts of U,
  hence at most |U|. B + 1 = 2ⁿ, B − s < 2ⁿ, and the entries of `tops` lie in [B + 1, T² + s]. The result is
  |S_n| ≤ 2ⁿ.
- *Newton's iteration* on q with 1 ≤ q < 2^(n+2) (every call, section 7), n ≥ 2: ⌊√q⌋ ≤ x ≤ x₀ = 2^⌈L(q)/2⌉ ≤
  2^((n+3)/2) and ⌊q/x⌋ ≤ q/⌊√q⌋ < (⌊√q⌋ + 1)²/⌊√q⌋ ≤ ⌊√q⌋ + 3, so x + ⌊q/x⌋ < 2^((n+3)/2) + 2^((n+2)/2) + 3 < 2^(n+2);
  y ≤ t/2, and (q.bit_length() + 1)//2 ≤ n + 2. For n = 1 the only call is on q = 1, and every value it forms is at
  most 2. q = 0 is answered directly.

For n = 0: A1 handles k = 0, r = 0, the costs 2, 2, 3, c ∈ {0, −1}, 3 evaluations and the budget −4; A2 handles
B = 0, T = 1, x ≤ 1, `examined` ≤ 2 and w = −5; A3 handles B = 0, T = 1, a = 0 and w = −5. ∎

So for n ≥ 1 every arithmetic operation, comparison, shift and bit length of the three implementations is one word
operation of the model of section 0.

*Check.* X §W: each implementation's source is rewritten so that every integer value an expression evaluates to
(names read, constants, operators, calls, subscripts, and every augmented assignment's target) is recorded, and the
rewritten code returns the same results; every value is below 2^(n+2) for n ≥ 1 and at most 5 for n = 0 (A1:
n = 0..16, A2: n = 0..34, A3: n = 0..400; the largest values seen at n = 0 are 4, 5 and 5; as a control, every run
records a value ≥ 2ⁿ). X §V: T² < 2^(n+2) (n = 0..400), T² + 2^(n−5) < 2^(n+1) (n = 6..400), and the values the
implementation records itself (n = 6..400). U `test_word_sizes_traced` (A1 n ≤ 10, A2 n ≤ 20, A3 n ≤ 120),
`test_group_structure` (n = 6..300).

## 9. Time and space

All bounds are in the model of section 0; the lower bounds count loop iterations and do not depend on it.

**9.1 A1: Θ(2ⁿ) word operations, O(1) words.** The loop runs 2ⁿ times. Its test of r runs 2ⁿ + isqrt(2ⁿ − 1)
times in total (section 4.1), and each iteration makes three evaluations of f_k with O(1) word operations each, one
comparison with the budget and at most two counter updates. So it makes between 2ⁿ and c·2ⁿ word operations for a constant c. It keeps k, r, best, c, covered,
evaluations, the budget and the range object: O(1) words.

**9.2 A2: Θ(2^(n/2)) word operations, O(1) words.** The loop runs T + 1 times with O(1) word operations each, and
T + 1 > √(2ⁿ − 1) ≥ 2^((n−1)/2) for n ≥ 1, and T + 1 ≤ 2^(n/2) + 2 (F3). The single call `isqrt(B)` costs O(n) by the
assumption of section 0. So A2 makes Θ(2^(n/2)) word operations; the lower bound Ω(2^(n/2)) holds without the
assumption. It keeps O(1) variables and one range object: O(1) words.

**9.3 A3: O(n log n) word operations, O(1) words.** It processes at most ⌊n/2⌋ + 1 groups for every n ≥ 2 (section
1.3), with O(1) word operations per group outside the square roots and the loop over `tops`. It computes at most
2(⌊n/2⌋ + 1) + 1 integer square roots, each with at most ⌊log₂(n + 4)⌋ + 2 iterations of O(1) word operations
(section 7). The loop over the roots that reach above B runs at most twice in total (Lemma E(c)), and so does the
final merge. Hence O(n) word operations outside the square roots, O(n log n) in all, and O(n) if an integer square
root counted as one operation. `tops` holds at most two pairs, and the other variables are O(1) words. ∎

*Check.* The counts behind these bounds are checked as listed in sections 1, 4.1 and 7 (for A1 in particular
X §V "enumeration, counted in an instrumented copy", n = 0..16). V: the V2 fits of the three
reported counts (α = 1.000 for 3·2ⁿ, 2^(n/2) + 1 and n/2 + 1, all rivals rejected).

## 10. Facts used by the V1 oracle (`harness.py`)

- `brute_force_count(n)`: for every k < 2ⁿ, top = isqrt(k + 2^L(k) − 1) is the largest X with X² < k + 2^L(k); by
  Lemma 0 every X > top costs more than X = 0, which is in the range, so the minimum over X = 0..top is min_X f_k(X).
  It uses neither Lemma A nor Lemma B, and it returns |S_n|.
- `sorted_union_count(n)`: the clipped intervals of Lemma B for X = 0..T, the non-empty ones sorted and merged as in
  4.2 (sorting makes the left ends non-decreasing), so it returns |S_n| by Lemma B. It uses neither Lemma C nor the
  grouping.
- `check(n, output)` returns False unless the output is a pair of integers (not bools) with 0 ≤ count ≤ 2ⁿ; it
  compares the count with `brute_force_count` for n ≤ 12 and with `sorted_union_count` for 13 ≤ n ≤ 34, and returns
  None (undecided) above n = 34. The harness has its own L and f and shares no code with the implementations.

*Check.* X §B (brute force = sorted union, n = 1..16), X §C (sorted union = A2 = A3, n = 0..42); U
`test_agree_and_check` (all three algorithms and `check` for n ≤ 14, A2 = A3 and `check` of A3 for n = 15..30;
None at n = 64), `test_check_rejects_wrong_outputs`
(count ± 1, a bare count, a float, a bool); V (the V1 runs).

## 11. Other statements

- **Values.** The values of |S_n| in README.md (n = 6..16, 20, 24, 29, 32, 40), in `notes` and in the unit tests
  (n = 5, 26, 39) are outputs of algorithms proved correct above. *Check.* X §T (interval sweep = groups = stated
  value for all 19 values), X §C (A1 = A2 = A3 for n ≤ 22); U `test_known_values`.
- **|S_n| = 0 for n ≤ 5:** (F2). *Check.* X §T (all three algorithms, n = 0..5).
- **At n = 200, A3 processes 101 groups:** section 1.3. *Check.* X §T.
- **Input and output size.** The instance is the number n, of L(n) = ⌊log₂ n⌋ + 1 bits for n ≥ 1. |S_n| ≤ 2ⁿ, so the
  output has at most n + 1 bits.
- **Bit-size view.** With b = L(n) input bits, n ≥ 2^(b−1), so A3's ⌊n/2⌋ + 1 groups (n ≥ 11) are at least 2^(b−2):
  A3 is polynomial in the value n but not in the input length, and A1 and A2 are exponential in n. *Check.* X §V
  "⌊n/2⌋ + 1 ≥ 2^(L(n)−2)", n = 1..100 000.
- **Tags.** T2: A1 makes Θ(2ⁿ) and A3 O(n log n) word operations (sections 9.1, 9.3). T8 (secondary): A1 and A2 are
  both super-polynomial, and A2 is faster by a factor Θ(2^(n/2)) (sections 9.1, 9.2). "2^(n/2) is not the complexity
  of the problem" means that A3 solves it with O(n log n) word operations in the same model. No lower bound for the
  problem and no optimality of any algorithm is claimed.
- **Scope of the budget.** Lemma A is about min f_k and does not use the budget; Lemma B, Lemma E(c) and the counts
  use the budget n − 4.
- **The case X^d + C, d ≥ 3** (README, Scope): three candidate roots are not enough for any d ≥ 3, since k = 2^(d+1)
  needs the fourth candidate X = 1. This is Corollary 2 of the theorem note
  `theorems/power-plus-offset-four-candidates` (proof in its README.md, check in its verify.py).
