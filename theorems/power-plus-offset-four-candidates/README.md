# The cheapest representation k = X^d + C for d ≥ 3: four candidate roots, and a polynomial count

> **🟠 Own result.** No prior literature was found after a documented search; what was searched is listed under
> [Literature search](#literature-search). This is a statement about that search, not a claim of priority.

## Setting

For an integer v let L(v) be the number of binary digits of |v|, with L(0) = 1. Fix an integer d ≥ 2. A non-negative
integer k can be written as k = X^d + C with a root X ≥ 0 and the offset C = k − X^d, at the cost

  f_k(X) = L(X) + L(C) + [C < 0]

bits (root digits, offset digits, one sign bit for a negative offset). Let r = ⌊k^(1/d)⌋ be the integer d-th root of
k, the largest r ≥ 0 with r^d ≤ k. For n ≥ 0 let

  S_n = { k : 0 ≤ k < 2ⁿ, f_k(X) ≤ n − 4 for some X ≥ 0 },

and write v = n − 4, B = 2ⁿ − 1 and T = ⌊B^(1/d)⌋ + 1.

For d = 2 this is the problem of the pair entry
[square-plus-offset-count-enumeration-vs-intervals-vs-groups](../../pairs/square-plus-offset-count-enumeration-vs-intervals-vs-groups/),
where three candidate roots 0, r, r + 1 suffice (Lemma A, proved in its
[PROOFS.md](../../pairs/square-plus-offset-count-enumeration-vs-intervals-vs-groups/PROOFS.md), section 2). This note
treats d ≥ 3; Theorems 3 and 4 also cover d = 2.

## Statement

**Theorem 1 (four candidates).** For every d ≥ 3 and every integer k ≥ 0,

  min_{X ≥ 0} f_k(X) = min( f_k(0), f_k(1), f_k(r), f_k(r + 1) ).

**Corollary 2 (where the three candidates of the square case fail).** Let d ≥ 3. If
min(f_k(0), f_k(r), f_k(r + 1)) > min_X f_k(X), then k = 2^p for some p ≥ 1, and X = 1 is the unique minimiser. Such
k exist for every d ≥ 3: k = 2^(d+1) has r = 2 and f_k(0) = d + 3, f_k(1) = d + 2, f_k(2) = d + 3, f_k(3) ≥ d + 3.
For d = 3 this is k = 16, with f(0) = 6, f(1) = 5, f(2) = 6, f(3) = 7.

**Theorem 3 (one interval per root).** For a root X let w = v − L(X). If w ≥ 1 let
I_X = [max(0, X^d − m), X^d + 2^w − 1] with m = 2^(w−1) − 1 for w ≥ 2 and m = 0 for w = 1; if w ≤ 0 let I_X = ∅.
Then, for every d ≥ 2 and n ≥ 0,

  S_n = ⋃_{X=0}^{T} ( I_X ∩ [0, B] ).

**Theorem 4 (a polynomial count).** For every d ≥ 2 and n ≥ 0, the algorithm A3_d described below returns |S_n|. It
processes at most ⌊n/d⌋ + 2 groups of roots and uses O((⌊n/d⌋ + 2)²·log d) word operations, which is
O((n²/d²)·log d) for 2 ≤ d ≤ n. For n ≥ 1 every integer it computes has absolute value below 2^(n+2) (for n = 0 at
most 5); the exponent d is part of the input, and the power algorithm reads its binary digits. The cost model is the
word RAM with words of n + 3 bits and unit-cost addition, subtraction, multiplication, integer division, comparison,
shifts and bit length; d-th powers and integer d-th roots are not unit operations and are paid for in full.

Theorems 1 and 3 also give simpler exact methods: an enumeration of all k < 2ⁿ with four cost evaluations per k
(correct by Theorem 1), and a sweep over the T + 1 intervals of Theorem 3 in X order (correct by Theorem 3 and
Lemma C below). This note analyses only A3_d and registers no pair for d ≥ 3; the pair entry compares the three
methods for d = 2.

## Proofs

L is non-decreasing in |v|, and for w ≥ 1, L(v) ≤ w holds iff |v| ≤ 2^w − 1.

**Lemma 0 (window).** If X^d − k ≥ 2^L(k), then f_k(X) > f_k(0).

*Proof.* Then C ≤ −2^L(k), so f_k(X) ≥ 1 + (L(k) + 1) + 1 > 1 + L(k) = f_k(0). ∎

### Proof of Theorem 1

We show f_k(X) ≥ min(f_k(0), f_k(r), f_k(r + 1)) for every X ∉ {0, 1, r, r + 1}.

(i) **X ≥ r + 2.** Then X^d > (r + 1)^d > k, so f_k(X) = L(X) + L(X^d − k) + 1. Since X > r + 1 and
X^d − k > (r + 1)^d − k > 0, monotonicity of L gives f_k(X) ≥ L(r + 1) + L((r + 1)^d − k) + 1 = f_k(r + 1). (This case
holds for every d ≥ 1.)

(ii) **2 ≤ X ≤ r − 1 and L(X) = L(r).** Then k − X^d > k − r^d ≥ 0, so
f_k(X) = L(X) + L(k − X^d) ≥ L(r) + L(k − r^d) = f_k(r).

(iii) **2 ≤ X ≤ r − 1 and a := L(X) < b := L(r).** Here a ≥ 2, and k ≥ r^d ≥ 3^d. Let p = L(k) − 1, so
2^p ≤ k < 2^(p+1) and f_k(0) = p + 2. Suppose f_k(X) ≤ p + 1. As C = k − X^d > 0, this means a + L(C) ≤ p + 1, so
C ≤ 2^(p+1−a) − 1. Then X^d = k − C > 2^p − 2^(p+1−a) ≥ 2^(p−1) (because a ≥ 2), and X ≤ 2^a − 1 gives
2^(p−1) < 2^(ad), i.e. ad ≥ p. On the other hand r ≥ 2^(b−1) and r^d ≤ k < 2^(p+1) give (b − 1)d < p + 1, so
(b − 1)d ≤ p, and a ≤ b − 1 gives ad ≤ p. Hence ad = p. Put u = 2^a ≥ 4. Then

  k = X^d + C ≤ (u − 1)^d + 2^(p+1−a) − 1 = (u − 1)^d + 2u^(d−1) − 1.

For d ≥ 3, (1 − 1/u)^d ≤ (1 − 1/u)³ = 1 − 3/u + 3/u² − 1/u³, so

  ((u − 1)^d + 2u^(d−1) − 1)/u^d < (1 − 1/u)^d + 2/u ≤ 1 − 1/u + 3/u² − 1/u³ ≤ 1,

where the last step is u² − 3u + 1 ≥ 0, true for u ≥ 3. Hence k < u^d = 2^(ad) = 2^p ≤ k, a contradiction. So
f_k(X) ≥ f_k(0) in case (iii).

Every X ∉ {0, 1, r, r + 1} with X ≥ 2 is either ≥ r + 2 (case (i)) or ≤ r − 1 (cases (ii), (iii), as L(X) ≤ L(r)). ∎

For d = 2 the bound of case (iii) equals u² exactly, so this argument does not apply; the square case is proved
differently in the pair entry (its Lemma A), where 0, r and r + 1 suffice.

### Proof of Corollary 2

The proof of Theorem 1 shows f_k(X) ≥ min(f_k(0), f_k(r), f_k(r + 1)) for every X ∉ {0, 1, r, r + 1}. So if this
three-candidate minimum exceeds min_X f_k(X), then 1 ∉ {r, r + 1}, the minimum is attained at X = 1 and at no other
root, and f_k(1) < f_k(0). For k = 0, f_0(1) = 1 + L(−1) + 1 = 3 > 2 = f_0(0). For k ≥ 1,
f_k(1) = 1 + L(k − 1) and f_k(0) = 1 + L(k), and L(k − 1) < L(k) holds iff k is a power of two other than 1 (for
k = 1 both sides are 1).

Existence for every d ≥ 3: let k = 2^(d+1). Since (3/2)^d ≥ (3/2)³ = 27/8 > 2, we have 2^d ≤ k < 3^d, so r = 2. Then
f_k(0) = 1 + L(2^(d+1)) = d + 3, f_k(1) = 1 + L(2^(d+1) − 1) = d + 2 and f_k(2) = 2 + L(2^(d+1) − 2^d) = 2 + L(2^d) =
d + 3. Since (3/2)^d ≥ 27/8 > 5/2, we have 3^d ≥ 5·2^(d−1), i.e. 3^d − 2^(d+1) ≥ 2^(d−1), so
f_k(3) = 2 + L(3^d − 2^(d+1)) + 1 ≥ 2 + d + 1 = d + 3. Hence min(f_k(0), f_k(r), f_k(r + 1)) = d + 3 > d + 2 = f_k(1),
and the first part applies. For d = 3 (k = 16): f(0) = 1 + L(16) = 6, f(1) = 1 + L(15) = 5, f(2) = 2 + L(8) = 6,
f(3) = 2 + L(−11) + 1 = 7, and every X ≥ 4 = r + 2 costs at least f(3) by case (i). ∎

### Proof of Theorem 3

I_X = {k ≥ 0 : f_k(X) ≤ v}: for C ≥ 0 the condition is L(C) ≤ w, i.e. C ≤ 2^w − 1 (also for C = 0, as L(0) = 1 ≤ w);
for C < 0 it is L(|C|) ≤ w − 1, i.e. |C| ≤ 2^(w−1) − 1 if w ≥ 2, and impossible if w = 1; for w ≤ 0 nothing
qualifies, as L ≥ 1. So S_n = ⋃_{X ≥ 0} (I_X ∩ [0, B]). For k ≤ B we have r ≤ ⌊B^(1/d)⌋, so r + 1 ≤ T, and by case (i)
of the proof of Theorem 1 (valid for every d) every X ≥ r + 2 costs at least f_k(r + 1). So the roots X ≤ T
suffice. ∎

### Algorithm A3_d and the proof of Theorem 4

For a root X with w = v − L(X) ≥ 1 let s = 2^w − 1 and J_X = [X^d − m, X^d + s] (unclipped; I_X = J_X ∩ [0, ∞)).
Group l consists of the roots X ∈ {0, 1} for l = 1 and X ∈ [2^(l−1), 2^l − 1] for l ≥ 2; inside a group w = v − l,
s and m are constant.

**Lemma C (left ends increase).** If X < Y and w(Y) ≥ 1, then X^d − m(X) < Y^d − m(Y).

*Proof.* L(X) ≤ L(Y), so w(X) ≥ w(Y) and m(X) ≥ m(Y), since m is non-decreasing in w; and X^d < Y^d. ∎

Because L is non-decreasing, the roots X ≤ T with w ≥ 1 form an initial segment of {0, …, T}, and by Lemma C those
among them with left end X^d − m ≤ B form an initial segment [0, x_top] (non-empty iff n ≥ 6, as 0 is in it iff
w(0) = n − 5 ≥ 1). Roots with left end above B contribute nothing to Theorem 3. Let U = ⋃_{X ≤ x_top} J_X and let H
be the largest right end X^d + s over X ≤ x_top. Then

  |S_n| = |U| − m₁ − max(0, H − B),

where m₁ is the m of group 1:
- *below 0:* J_0 = [−m₁, 2^(n−5) − 1] has the smallest left end (Lemma C) and a non-negative right end, so
  U ∩ (−∞, −1] = [−m₁, −1];
- *above B:* every y ∈ U with y > B lies in some J_X with X ≤ x_top, so y ≤ H; conversely, if B < y ≤ H, the root Y
  with right end H has left end ≤ B < y, so y ∈ J_Y. Hence U ∩ [B + 1, ∞) = [B + 1, H] (empty if H ≤ B).

|U| is measured by a sweep in X order: keep the current component [c, e] (e = largest right end so far); J_X starts
a new component iff its left end exceeds e + 1, otherwise the component becomes [c, max(e, X^d + s)].

**Lemma D (D is increasing).** D(X) = X^d − (X − 1)^d is strictly increasing for X ≥ 1 and d ≥ 2.

*Proof.* D(X + 1) − D(X) = (X + 1)^d + (X − 1)^d − 2X^d = 2 Σ_{j≥1} C(d, 2j) X^(d−2j) ≥ 2·C(d, 2)·X^(d−2) > 0. ∎

**Lemma E (one group).** Let the group l have first root g_s and last root g_e = min(2^l − 1, T, ⌊(B + m)^(1/d)⌋)
(its last root with left end ≤ B), g_s < g_e, and let E be the right end e after J_(g_s) has been swept. Let
t_A = ⌊(E + 1 + m)^(1/d)⌋ + 1 and let t_B be the smallest X ∈ (g_s, g_e] with D(X) > 2^w + m, or g_e + 1 if there is
none. For X ∈ (g_s, g_e], J_X starts a new component iff X ≥ t_A and X ≥ t_B. Hence, with x_s = max(g_s + 1, t_A, t_B):
the roots g_s + 1, …, min(x_s − 1, g_e) extend the current component to the right end
max(E, min(x_s − 1, g_e)^d + s); and if x_s ≤ g_e, each root X ∈ [x_s, g_e − 1] is a component J_X of its own, of size
s + m + 1 = 2^w + m, and J_(g_e) becomes the current component.

*Proof.* Inside the group the right ends increase, and E is at least every right end before the group and the right
end of J_(g_s); so just before X ∈ (g_s, g_e] the current right end is max(E, (X − 1)^d + s). J_X starts a new
component iff X^d − m > E + 1, i.e. X^d > E + 1 + m, i.e. X ≥ t_A, and X^d − m > (X − 1)^d + s + 1, i.e.
D(X) > s + 1 + m = 2^w + m, i.e. X ≥ t_B (Lemma D; E + 1 + m ≥ 1 since E is at least the right end of J_0). Both
conditions are upward closed in X, so the starting roots of (g_s, g_e] are exactly [x_s, g_e]. A non-starting root
extends the component to max(e, X^d + s). For a starting X < g_e the next root starts a component too, so its left
end exceeds X^d + s + 1, and by Lemma C so does every later left end: J_X is a whole component. ∎

**The algorithm A3_d.** Compute T. For l = 1, 2, …: stop if w = v − l < 1, if the first root g_s of group l exceeds
T, or if g_e < g_s (then no later root has left end ≤ B). Otherwise sweep J_(g_s); if g_e > g_s, compute t_A (one
integer d-th root), t_B (binary search over (g_s, g_e], valid by Lemma D) and apply Lemma E. At the end return
|U| − m₁ − max(0, H − B), or 0 if no group was processed (n ≤ 5, where S_n = ∅ because every representation costs
at least 2 bits). Correctness follows from Theorem 3, Lemma C, the formula for |S_n| above and Lemma E.

**Cost.**
- *Groups.* Group l ≥ 2 is processed only if 2^(l−1) ≤ T. Since (2ⁿ − 1)^(1/d) < 2^(n/d) < 2^(⌊n/d⌋+1), we have
  T ≤ 2^(⌊n/d⌋+1), so l ≤ L(T) ≤ ⌊n/d⌋ + 2.
- *Powers.* x^d by left-to-right binary exponentiation takes ⌊log₂ d⌋ squarings and popcount(d) − 1 further
  multiplications, at most 2⌊log₂ d⌋ in total.
- *Roots.* The integer d-th root of q ≥ 1 by bisection on [0, 2^⌈L(q)/d⌉] (where (2^⌈L(q)/d⌉)^d ≥ 2^L(q) > q) takes
  exactly ⌈L(q)/d⌉ steps. Each step tests x^d ≤ q with the power algorithm and, before each product a·b, the test
  a > ⌊q/b⌋ (which is equivalent to a·b > q for b ≥ 1); so a step costs O(log d) word operations and no product
  exceeds q. Here x ∈ {0, 1} is answered directly; for x ≥ 2 every intermediate value of the power algorithm is
  x^j with j ≤ d (and b ≥ 2), so if a test a > ⌊q/b⌋ fires, then x^d > q and the step answers "no" without forming
  the product.
- *Per group:* at most two integer d-th roots (g_e and t_A) of numbers below 2^(n+2), each with
  ⌈L(q)/d⌉ ≤ ⌈(n + 2)/d⌉ ≤ ⌊n/d⌋ + 2 steps; at most l D-evaluations in the binary search (group l has at most 2^(l−1)
  roots); at most three further d-th powers; O(1) other operations.
- *Total.* With g* = ⌊n/d⌋ + 2 groups at most, there are at most 2g* + 1 roots, each with at most g* steps, and at
  most Σ_{l≤g*} l ≤ g*² D-evaluations; each step or evaluation costs O(log d) word operations. So A3_d uses
  O(g*²·log d) word operations. For d ≤ n, g* ≤ 3n/d.
- *Sizes.* Let n ≥ 6. Then 1 ≤ w ≤ n − 5 in every processed group, so m < 2^(n−6), s < 2^(n−5) and
  2^w + m < 2^(n−4); group indices and first roots are at most 2^L(T) ≤ 2T. For X ≤ x_top, X^d ≤ B + m < 2^(n+1),
  and so are the D-values compared in the binary search; left ends are at least −m₁ > −2^(n−6), and right ends are
  below B + m + 2^w < 2^(n+1); the root arguments B, B + m and E + 1 + m are below 2^(n+2). Every running size of the
  sweep, and every product (g_e − x_s + 1)(s + m + 1) (the total size of pairwise disjoint intervals J_X, X ∈ [x_s, g_e],
  that lie in U), is at most |U| < 2^(n+1) + 2^(n−6) + 1. More precisely, |U| ≤ (largest right end) + m₁ + 1 <
  2ⁿ(1 + 3/64) + 2^(n−6) = 2ⁿ(1 + 4/64), so a running size plus one right end, as formed when the sweep adds before it
  subtracts, is below |U| + B + m + 2^w < 2ⁿ(2 + 7/64) < 2^(n+2). A bisection for an argument q runs on
  [0, 2^⌈L(q)/d⌉] ⊆ [0, 2^⌈(n+2)/2⌉], so its lo + hi is below 2^(⌈(n+2)/2⌉+1) ≤ 2^(n+2), and its products and
  quotients stay ≤ q; the binary search for t_B adds two numbers at most g_e + 1 ≤ T + 1. For 1 ≤ n ≤ 5 the algorithm
  only computes v, B < 2ⁿ, T (a bisection on [0, 2^⌈L(B)/d⌉] ⊆ [0, 2^⌈n/2⌉]) and w = n − 5 ∈ [−4, 0], and stops. So
  for n ≥ 1 every integer it computes has absolute value below 2^(n+2). For n = 0 it computes v = −4, B = 0, T = 1
  and w = −5 and stops. ∎

## Verification

```bash
python theorems/power-plus-offset-four-candidates/verify.py
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and runs in about
half a minute on a laptop. It exits with code 0 only if every check passes. It checks:

- Corollary 2: the example d = 3, k = 16 (X = 1 the unique minimiser); for d = 3..8 and every k < 2^18, that
  every k at which the three candidates 0, r, r + 1 miss the minimum is a power of two ≥ 2 with X = 1 the only
  minimiser; and the values k = 2^(d+1) for d = 3..400 (r = 2, the four costs, X = 1 the only minimiser in the
  window of Lemma 0);
- Theorem 1 against a brute force over all roots in the window of Lemma 0, for d = 3..8 and **every k < 2^18**:
  0 mismatches; Lemma 0 itself on a small range; the case-(iii) inequality (u − 1)^d + 2u^(d−1) − 1 < u^d for
  u = 2^a, a = 2..40, d = 3..60 (and equality for d = 2); f_k(1) < f_k(0) iff k = 2^p, p ≥ 1 (k < 2^16);
- Theorem 3: the sorted union of the clipped intervals equals the brute-force count, d = 3..8, n = 0..18, and the
  one-pass sweep in X order (Theorem 3 with Lemma C) equals the sorted union, d = 3..8, n = 0..40;
- Theorem 4: A3_d equals the brute-force count (d = 3..8, n = 0..18) and the sorted union, which uses neither Lemma C
  nor the grouping (d = 2 for n ≤ 40, d = 3 for n ≤ 57, d = 4..7 for n ≤ 76); for d = 2 it reproduces the values of
  the pair entry (|S_13| = 1 104, |S_29| = 77 512 574, |S_39| = 79 393 042 353);
- the structure used by A3_d: strictly increasing left ends and component starts forming a suffix of every group
  (d = 3..5, n = 6..36), Lemma D (X ≤ 2000, d = 2..12), L(x_top) ≤ ⌊n/d⌋ + 2 (d = 2..11, n = 6..200);
- the cost facts: bisection roots are exact with exactly ⌈L(q)/d⌉ steps for every q (4 000 seeded q < 2^700,
  d = 2..40), powers take at most 2⌊log₂ d⌋ multiplications (d = 2..199), and inside A3_d (d = 3, 4, 5;
  n = 64, 256, 1024, 2048) at most ⌊n/d⌋ + 2 groups, at most l D-evaluations in group l, exactly ⌈L(q)/d⌉ steps for
  every root, and no product, root argument (B, B + m, H + 1 + m), run of isolated intervals, |U| or H of 2^(n+2) or
  more; the inequalities ⌈(n + 2)/d⌉ ≤ ⌊n/d⌋ + 2 (d = 2..200, n = 0..2000) and ⌊n/d⌋ + 2 ≤ 3n/d (d = 2..200, n = d..2000) of
  the cost proof;
- the word sizes of Theorem 4: an instrumented copy of the script's implementation of A3_d, rewritten so that every
  integer value of every expression except the exponent d is recorded, returns the same results, and every recorded
  value is below 2^(n+2) for n = 1..200 and at most 5 for n = 0 (d = 2..8).

## Literature search

Searched in October 2026, together with the square case: Crossref (3 queries), arXiv (4 queries) and OpenAlex
(2 queries), with generic keywords on counting integers close to perfect squares or perfect powers, integers
expressible as a power plus a small offset, and the bit length or description length of such representations.
Titles, metadata and deposited abstracts were screened. Nothing relevant was found. The search was shallow
(metadata only, no full texts, no citation chasing). The only related hit, Rissanen (1983), *A universal prior for
integers and estimation by minimum description length*, was afterwards read in part (its introduction, pp. 416–417,
and pp. 422–424 of its Section 3): it concerns a universal prior for integers, and these pages do not contain these
results. It is not used as evidence.

## Scope

- The cost function exactly as defined (L(0) = 1, a sign bit only for negative offsets), exact integer arithmetic.
  Theorem 1 and Corollary 2 hold for every k ≥ 0 and every d ≥ 3; Theorems 3 and 4 are stated for the budget n − 4
  and every d ≥ 2.
- Theorem 4 is an upper bound in the stated model. No lower bound is claimed.
- Corollary 2 says where the three candidates can fail, and that they fail for every d ≥ 3 (at k = 2^(d+1)); it
  does not determine all such k.
- The note does not register the enumeration, the interval sweep and A3_d as a validated pair for d ≥ 3.

## Sources

- J. Rissanen (1983). *A universal prior for integers and estimation by minimum description length*. The Annals of
  Statistics 11(2). [doi:10.1214/aos/1176346150](https://doi.org/10.1214/aos/1176346150). The one related hit of the
  literature search; read in part (its introduction, pp. 416–417, and pp. 422–424 of its Section 3): it concerns a universal
  prior for integers, and these pages do not contain the results of this note. Not a base of this note and not used
  as evidence for any statement.
