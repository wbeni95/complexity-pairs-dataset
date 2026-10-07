# Knuth's root window is exact for concave nondecreasing length weights

> **Provenance: literature (pending).** This may be an own extension of the cited results; the closest source
> (Batty–Pelling–Rogers 1982) was not accessible, so this could not be established.
>
> Bases: Glassey–Karp (1976); Batty–Pelling–Rogers (1982), SIAM J. Algebraic Discrete Methods 3(1),
> doi:10.1137/0603002; Cleary–Fischer–St. John, arXiv:2502.12854. What is known about their content, and how it
> relates to this note, is in [Literature](#literature).

## Setting

Let n ≥ 1 and let w(i, j) be real weights for 0 ≤ i < j ≤ n. The interval recurrence

    c(i, i) = 0,   c(i, j) = w(i, j) + min_{i<k≤j} [ c(i, k−1) + c(k, j) ]      (0 ≤ i < j ≤ n)        (R)

is the recurrence of optimal binary search trees: k is the root of the subtree on the keys i+1, …, j (see also the
pair [optimal-bst-recursion-vs-dp-vs-knuth](../../pairs/optimal-bst-recursion-vs-dp-vs-knuth/)). Knuth (1971)
restricted the search for the root. With K(i, i) = i, the *restricted run* computes, for j − i = 1, 2, …, n,

    c′(i, j) = w(i, j) + min_{k ∈ W(i,j)} [ c′(i, k−1) + c′(k, j) ],
    W(i, j)  = { k : max(K(i, j−1), i+1) ≤ k ≤ min(K(i+1, j), j) },

and stores the chosen minimiser as K(i, j). For j = i + 1 the window is {i + 1}. Under the **largest tie rule**
K(i, j) is the largest minimiser in W(i, j), under the **smallest tie rule** the smallest one. The run is *exact* if
c′(i, j) = c(i, j) for all 0 ≤ i < j ≤ n. When the windows are non-empty, their sizes telescope along each diagonal,
so the run examines O(n²) candidate roots in total instead of the Θ(n³) of (R). The classical sufficient condition
for exactness is the quadrangle inequality (Yao 1980). This note concerns **length weights** w(i, j) = h(j − i). For
concave h they satisfy the reverse inequality (Remark 3).

## Statement

**Definitions.**

- The *heap-shaped tree with d keys* (d ≥ 1) has the nodes 1, …, d, and node v has the children 2v and 2v + 1 when
  these are ≤ d (a complete binary tree whose last level is filled from the left). L(d) is the number of nodes in the
  left subtree of the root, and HR(d) = d − 1 − L(d) is the number in the right subtree. Explicitly, with
  d + 1 = 2^H + e and 0 ≤ e < 2^H: L(d) + 1 = 2^(H−1) + min(e, 2^(H−1)) and
  HR(d) + 1 = 2^(H−1) + max(0, e − 2^(H−1)).
- For h: {1, …, N} → ℝ let k_max = max{ j ∈ {2, …, N} : h(j) > h(j−1) }, or k_max = 1 if there is no such j, and
  Q = 2^⌊log₂ k_max⌋.
- τ*(d) = d − 1 − min(HR(d), Q − 1) for 1 ≤ d ≤ N.

**Theorem.** Let N ≥ 1 and let h: {1, …, N} → ℝ be concave, h(j+1) − h(j) ≤ h(j) − h(j−1) for 2 ≤ j ≤ N − 1, and
nondecreasing, h(j) ≥ h(j−1) for 2 ≤ j ≤ N. Let 1 ≤ n ≤ N and w(i, j) = h(j − i). Then Knuth's restricted run on
(R) is exact under the largest and under the smallest tie rule, and for every interval, with d = j − i,

    K(i, j) = i + 1 + τ*(d)                       (largest rule),
    K(i, j) = i + 1 + min(HR(d), Q − 1)           (smallest rule).

In words: under the largest rule the root of an interval with d keys has min(HR(d), Q − 1) keys on its right. The
run follows the root of the heap-shaped tree while the heap's right subtree has at most Q − 1 keys. From then on the
right part stays at Q − 1 keys and only the left part grows. The smallest rule gives the mirror image. Since the
run is exact, every K(i, j) is an optimal root, so the tree read off from K is optimal.

**Corollary.** If h: {1, 2, …} → ℝ is concave and nondecreasing, Knuth's restricted run with w(i, j) = h(j − i) is
exact for every n under both tie rules, with K(i, j) as in the Theorem. Here τ*(d) may be computed from the
restriction of h to {1, …, N} for any N ≥ d: the value does not depend on N (Proposition 5).

**Remarks on the statement.**

- (i) If h(N) > h(N−1), then k_max = N and HR(d) ≤ Q − 1 for every d ≤ N (proof after Lemma H), so τ*(d) = L(d):
  the run follows the heap root throughout.
- (ii) If h is constant, then Q = 1 and τ*(d) = d − 1, and every split is optimal.
- (iii) For concave h with N ≥ 2, "nondecreasing" is equivalent to h(N) ≥ h(N−1), because the differences
  h(j) − h(j−1) are nonincreasing in j.

## Proof

### 1. Reduction to one dimension

Let C(0) = 0 and, for 1 ≤ d ≤ N,

    C(d) = h(d) + min_{0≤t≤d−1} F_d(t),    F_d(t) = C(t) + C(d−1−t),    T(d) = { t : F_d(t) = min F_d }.

Here t is the number of keys to the left of the root. For a tie rule, the *one-dimensional run* is τ′(0) = −1,
C′(0) = 0 and, for d ≥ 1,

    W(d)  = { t ∈ ℤ : max(τ′(d−1), 0) ≤ t ≤ min(τ′(d−1) + 1, d − 1) },
    C′(d) = h(d) + min_{t ∈ W(d)} [ C′(t) + C′(d−1−t) ],

with τ′(d) the largest (resp. smallest) t ∈ W(d) attaining this minimum. We write τ′ for the largest rule and τ′_s
for the smallest one, and C′_s for the values of the latter.

**Lemma 0.** Let w(i, j) = h(j − i). Then c(i, j) = C(j − i), and for each tie rule c′(i, j) = C′(j − i) and
K(i, j) = i + 1 + τ′(j − i).

*Proof.* Induction on d = j − i, with k = i + 1 + t: the left part (i, k−1) has t keys and the right part (k, j)
has d − 1 − t keys. The first claim follows at once. For the run with d = 1, W(i, i+1) = {i+1} corresponds to
W(1) = {0}. For d ≥ 2, the induction hypothesis gives K(i, j−1) = i + 1 + τ′(d−1) and K(i+1, j) = i + 2 + τ′(d−1).
Both lie in [i+1, j] because 0 ≤ τ′(d−1) ≤ d − 2, so W(i, j) corresponds to {τ′(d−1), τ′(d−1) + 1} = W(d), where
the clipping in W(d) is inactive. The compared values are c′(i, k−1) + c′(k, j) = C′(t) + C′(d−1−t), and k increases
with t, so the tie rules correspond. ∎

So the Theorem follows from Theorem 1 below. By Lemma 0, applied to intervals of length d ≤ n ≤ N, exactness means
C′(d) = C(d) for d ≤ n, and the formulas for K are those for τ′ and τ′_s. (The first n steps of the one-dimensional
run use only h(1), …, h(n).)

**Theorem 1.** Under the hypotheses of the Theorem, for every d ∈ {1, …, N}:
1. the largest rule gives C′(d) = C(d) and τ′(d) = τ*(d);
2. the smallest rule gives C′_s(d) = C(d) and τ′_s(d) = d − 1 − τ*(d) = min(HR(d), Q − 1).

### 2. Trees and the leaf form

A *tree* is a full binary tree whose internal nodes are the keys; with d keys it has d + 1 leaves. For an internal
node v, size(v) is the number of keys in its subtree and λ_v = size(v) + 1 the number of leaves below it. The cost of
a tree T with d keys under f is cost_f(T) = Σ_v f(size(v)), summed over the internal nodes. By induction on d, C(d)
is the least cost_h(T) over trees with d keys, and F_d(t) is the least total cost of the two root subtrees when the
left one has t keys. So T(d) is the set of root splits of the optimal trees.

Counting leaves is convenient: A(x) = C(x − 1) for x ≥ 1. A root with t keys on the left has the *leaf split*
(t + 1, d − t) of x = d + 1 leaves, and F_d(t) = A(t + 1) + A(d − t).

Two families of comparison costs, defined for all s ≥ 1: the **caps** h_k(s) = min(s, k) for k ≥ 1, and the
**linear cost** h_lin(s) = s. C_k, A_k, F^k_d, T_k(d) and C_lin, A_lin, F^lin_d, T_lin(d) are the corresponding
objects. In leaf terms a node costs min(λ_v − 1, k), resp. λ_v − 1.

The heap-shaped tree with x leaves means the heap-shaped tree with x − 1 keys. Both of its root subtrees are again
heap-shaped. For x ≥ 2, write x = 2^H + e with 0 ≤ e < 2^H. Its leaf split is

    (a, b) = ( 2^(H−1) + min(e, 2^(H−1)),  2^(H−1) + max(0, e − 2^(H−1)) ),                                    (S)

that is, (2^(H−1) + e, 2^(H−1)) if e ≤ 2^(H−1) and (2^H, x − 2^H) otherwise. The reason: the heap with
x − 1 = 2^H − 1 + e keys has full levels 0, …, H − 1, and level H holds e keys filled from the left. The left subtree
receives the first min(e, 2^(H−1)) of them, and both subtrees are again filled from the left. Always a ≥ b ≥ 2^(H−1).

### 3. Lemmas

**Lemma A (representation).** Let N ≥ 2, h concave and nondecreasing on {1, …, N}, and Δh(j) = h(j) − h(j−1) for
2 ≤ j ≤ N. Then for 1 ≤ s ≤ N

    h(s) = κ + a·s + Σ_{k=2}^{N−1} c_k · min(s, k),

with a = Δh(N) ≥ 0, c_k = Δh(k) − Δh(k+1) ≥ 0 and κ = h(1) − a − Σ_k c_k. Moreover k_max = N if a > 0, and
k_max = max{ k : c_k > 0 } if a = 0 and h is not constant.

*Proof.* Telescoping gives Δh(j) = a + Σ_{k=j}^{N−1} c_k for 2 ≤ j ≤ N. Hence
h(s) − h(1) = Σ_{j=2}^{s} Δh(j) = a(s − 1) + Σ_k c_k · #{ j : 2 ≤ j ≤ min(s, k) } = a(s − 1) + Σ_k c_k (min(s, k) − 1).
The signs come from monotonicity (a) and concavity (c_k). Finally, Δh(j) > 0 holds iff a > 0 or c_k > 0 for some
k ≥ j, which gives k_max. ∎

**Lemma B (linear cost).** E(x) := A_lin(x) = x(D + 1) − 2^(D+1) + 1 with D = ⌊log₂ x⌋. Every complete tree (all
leaves on at most two adjacent levels) attains it, in particular the heap-shaped tree, and
E(x + 1) − E(x) = ⌊log₂ x⌋ + 1. Hence E is convex and linear with slope j + 1 on each interval [2^j, 2^(j+1)].

*Proof.* Σ_v λ_v is the external path length (EPL), the sum of the leaf depths, so cost_lin(T) = EPL − (x − 1).
Suppose leaves of depths y ≤ x′ − 2 exist, where x′ is the largest depth. The deepest leaves come in sibling pairs.
Remove such a pair, which makes its parent a leaf of depth x′ − 1, and give the leaf of depth y two children. This
changes the EPL by −2x′ + (x′ − 1) − y + 2(y + 1) = y − x′ + 1 < 0. So every minimiser is complete. A complete tree
with u leaves at depth D + 1 and x − u at depth D, with 0 ≤ u < x, satisfies (x − u) + u/2 = 2^D (Kraft's equality),
so D = ⌊log₂ x⌋, u = 2(x − 2^D) and EPL = xD + 2(x − 2^D). Subtracting x − 1 gives the formula. The increment is a
direct computation, inside a dyadic block and across a power of two. The formula is classical; it is formula (3.1)
of Fredman and Knuth (1974), with n = x − 1. ∎

**Lemma C (closed form for a cap).** Let k ≥ 1, J = ⌊log₂(k + 1)⌋, P = 2^J (so 2 ≤ P ≤ k + 1 < 2P),
δ = k + 1 − P ∈ {0, …, P − 1}, and

    g(x) = #{ y ∈ {0, …, x − 1} : y mod P < δ } = ⌊x/P⌋·δ + min(x mod P, δ).

Then A_k(x) = E(x) for 1 ≤ x ≤ k + 1, and A_k(x) = Jx + g(x) − k for x ≥ P. The two expressions agree on [P, k + 1].

*Proof.* (a) If x ≤ k + 1, every internal node has λ_v ≤ k + 1, so the cap is inactive and A_k(x) = E(x).

(b) *Lower bound, every x ≥ 1.* Let T have x leaves, and let U be the set of internal nodes v with λ_v ≥ k + 2.
U is closed under taking ancestors, and each of its nodes costs exactly k. Call the maximal subtrees whose root has
λ ≤ k + 1 the *pieces* (a single leaf may be a piece). The pieces partition the leaves. They hang at the external
positions of the top tree U, so there are m = |U| + 1 of them, with leaf counts λ_1, …, λ_m summing to x. Inside a
piece every node has λ ≤ k + 1, so a piece costs at least E(λ_i) by Lemma B. Hence
cost(T) ≥ k(m − 1) + Σ_i E(λ_i) = Σ_i [k + E(λ_i)] − k. Two facts finish the bound:

- (F1) k + E(λ) ≥ Jλ + g(λ) for 1 ≤ λ ≤ k + 1, with equality on [P, k + 1]. For λ = P + e with 0 ≤ e ≤ δ: E has
  slope J + 1 on [P, 2P] ⊇ [P, k + 1], and k + E(P) = (P + δ − 1) + (J − 1)P + 1 = JP + δ, so
  k + E(λ) = Jλ + δ + e = Jλ + g(λ). For λ ≤ P: E(λ) − Jλ is nonincreasing on [1, P] (its increments are
  ⌊log₂ λ⌋ + 1 − J ≤ 0), so E(λ) − Jλ ≥ E(P) − JP = 1 − P. Also k − g(λ) = k − min(λ, δ) ≥ k − δ = P − 1. Add the
  two inequalities.
- (F2) g is subadditive. g(a + b) − g(a) counts the y ∈ [a, a + b) with y mod P < δ. Write b = mP + r with
  0 ≤ r < P. The m full periods contribute mδ, and the last r consecutive integers have distinct residues, so they
  contribute at most min(r, δ). The total is at most g(b).

So cost(T) ≥ Σ_i [Jλ_i + g(λ_i)] − k ≥ Jx + g(x) − k.

(c) *Upper bound, x ≥ P.* Write x = qP + e with q ≥ 1 and 0 ≤ e < P. Take any binary top tree with m − 1 internal
nodes, each costing at most k, and hang complete trees with λ_i leaves at its m external positions. Each complete
tree costs exactly E(λ_i), because its nodes have λ ≤ λ_i ≤ k + 1.
- If e < δ: take m = q pieces of sizes P + ⌊e/q⌋ or P + ⌈e/q⌉. All lie in [P, P + e] ⊆ [P, k], where E has slope
  J + 1. The cost is at most k(q − 1) + qE(P) + (J + 1)e = Jx + qδ + e − k = Jx + g(x) − k.
- If e ≥ δ: take m = q + 1 pieces of sizes ⌊x/(q+1)⌋ or ⌈x/(q+1)⌉. All lie in [P/2, P], because
  qP/(q+1) ≥ P/2 and x < (q + 1)P, and E has slope J there. The cost is at most
  kq + (q + 1)E(P) − J((q + 1)P − x) = Jx + (q + 1)δ − k = Jx + g(x) − k.

Agreement on [P, k + 1] is the equality case of (F1). ∎

In what follows f_k = A_k + k. So f_k(x) = Jx + g(x) for x ≥ P, f_k(x) = E(x) + k for x ≤ k + 1, and
g(y + mP) = g(y) + mδ, g(mP) = mδ.

**Lemma D (the heap is optimal).** For every k ≥ 1 and x ≥ 1, the heap-shaped tree with x leaves attains A_k(x).
It also attains E(x) = A_lin(x).

*Proof.* Linear cost: the heap-shaped tree is complete (Lemma B). Caps, by induction on x. For x ≤ k + 1 the heap
is complete and no cap is active, so its cost is E(x) = A_k(x). Let x ≥ k + 2. The root costs k, and the root
subtrees are heap-shaped with leaf counts (a, b) from (S). By induction the cost is k + A_k(a) + A_k(b), so it
suffices to show f_k(a) + f_k(b) = f_k(x). Since x > P, the exponent in (S) satisfies H ≥ J.
(i) a, b ≥ P. One of a, b is a power of two ≥ P (b = 2^(H−1) or a = 2^H), hence a multiple of P. So
g(x) = g(a) + g(b) and f_k(x) = f_k(a) + f_k(b).
(ii) b < P. Since 2^(H−1) ≤ b < P, we get H = J, x ∈ [P, 2P) and e = x − P ≥ δ + 1 (as x ≥ k + 2), so
f_k(x) = Jx + 2δ. If e ≥ P/2, then (a, b) = (P, e). Here f_k(P) = JP + δ, and f_k(e) = E(e) + k = Je + δ, because
E(e) = E(P) − J(P − e) = Je − P + 1. The sum is J(P + e) + 2δ. If e < P/2, then (a, b) = (P/2 + e, P/2) with both
parts below P ≤ k + 1, and f_k(a) + f_k(b) = 2E(P/2) + Je + 2k = (J − 2)P + 2 + Je + 2(P + δ − 1) = J(P + e) + 2δ.
The case a < P ≤ b cannot occur, since a ≥ b. ∎

(Lemma D also follows from Theorem 6 and Lemma 22 of Cleary, Fischer and St. John (2025) by a limit argument; the
proof above does not use it. See [Literature](#literature).)

**Lemma E (additivity).** Let h be as in Lemma A, N ≥ 2 and 1 ≤ d ≤ N. Then

    C(d)   = κd + a·C_lin(d) + Σ_k c_k C_k(d),
    F_d(t) = κ(d − 1) + a·F^lin_d(t) + Σ_k c_k F^k_d(t),
    T(d)   = ∩_{k : c_k > 0} T_k(d), intersected with T_lin(d) if a > 0

(an empty intersection means {0, …, d − 1}), and every T_k(d) and T_lin(d) contains L(d).

*Proof.* For every tree T with d ≤ N keys all sizes are ≤ N, so Lemma A gives
cost_h(T) = κd + a·cost_lin(T) + Σ_k c_k cost_k(T). Minimising, "≥" holds termwise since the coefficients are ≥ 0,
and equality holds at the heap by Lemma D. Applying this at t and d − 1 − t gives the formula for F_d. The subtrees of
the heap are heaps, so cost_k(heap_d) = h_k(d) + F^k_d(L(d)); since this equals C_k(d) = h_k(d) + min F^k_d, we get
L(d) ∈ T_k(d), and likewise L(d) ∈ T_lin(d). Hence min F_d equals κ(d − 1) + a·min F^lin_d + Σ_k c_k min F^k_d,
attained at L(d), and F_d(t) attains it iff every term with a positive coefficient is minimal at t. ∎

**Lemma F (forcing).** Let D ≥ 1, let A be A_k for a cap k ≥ 2^D or A_lin, and let x ∈ (3·2^(D−1), 2^(D+1)]. Then

    [ A(2^D + 1) + A(x − 2^D − 1) ] − [ A(2^D) + A(x − 2^D) ] = 1.

*Proof.* All four arguments lie in [2^(D−1), 2^D + 1]. For a cap this interval lies in [1, k + 1], so A = E by
Lemma C(a); for the linear cost A = E by definition. By Lemma B,
E(2^D + 1) − E(2^D) = D + 1. With b = x − 2^D ∈ (2^(D−1), 2^D], E(b) − E(b − 1) = ⌊log₂(b − 1)⌋ + 1 = D. ∎

**Lemma G (frozen split).** Let k ≥ 1 and J′ ≥ 0 with k < 2^(J′+1), Q = 2^(J′), and x ≥ 3Q. Then
A_k(x) = A_k(x − Q) + A_k(Q) + k, i.e. the leaf split (x − Q, Q) is optimal for the cap k. (The root costs
min(x − 1, k) = k, since x − 1 ≥ 2Q − 1 ≥ k.)

*Proof.* Let P_k = 2^⌊log₂(k+1)⌋ ≤ k + 1 ≤ 2Q. If P_k ≤ Q, then P_k divides Q, and x − Q ≥ 2Q ≥ P_k and Q ≥ P_k,
so the closed form of Lemma C applies to x, x − Q and Q. Then g(x) = g(x − Q) + g(Q), hence
f_k(x) = f_k(x − Q) + f_k(Q). If P_k > Q, then P_k = 2Q = k + 1, δ = 0 and f_k(y) = (J′ + 1)y for y ≥ P_k; also
x − Q ≥ 2Q = P_k, and Q < P_k ≤ k + 1 gives f_k(Q) = E(Q) + k = (J′ − 1)Q + 1 + 2Q − 1 = (J′ + 1)Q. ∎

**Lemma H (heap shape).** Let x = d + 1.

- (a) For d ≥ 2: HR(d) − HR(d − 1) ∈ {0, 1}.
- (b) For d ≥ 2: HR(d) = HR(d − 1) + 1 iff x ∈ (3·2^(D−1), 2^(D+1)] for some D ≥ 1, and then L(d) + 1 = 2^D.
- (c) For d ≥ 1 and Q = 2^J (J ≥ 0): HR(d) ≥ Q iff x ≥ 3Q + 1.

(HR(0) is not defined, so (a) and (b) start at d = 2.)

*Proof.* By (S), for x ∈ [2^H, 2^(H+1)) the right leaf count is HR(d) + 1 = 2^(H−1) + max(0, x − 3·2^(H−1)) and the
left one is 2^(H−1) + min(x − 2^H, 2^(H−1)). Inside a block the right count grows by 1 exactly when x > 3·2^(H−1),
and the left count is then 2^H. Across a block boundary, x − 1 = 2^(H+1) − 1 to x = 2^(H+1), the right count goes
from 2^H − 1 to 2^H, and the left count at x = 2^(H+1) is 2^H. This proves (a) and (b), where D = H inside a block
and D = H at x = 2^(H+1). (c): the right count is at least 2^(H−1) and at most 2^H − 1. If H − 1 ≥ J + 1, both
sides of (c) hold (x ≥ 2^H ≥ 4Q). If H − 1 = J, the right count is Q + max(0, x − 3Q), which is ≥ Q + 1 iff
x ≥ 3Q + 1. If H ≤ J, both sides fail (right count ≤ Q − 1, and x < 2Q). ∎

*Proof of Remark (i).* If h(N) > h(N−1), then k_max = N ≥ 2 and Q > N/2, so 3Q + 1 > 3N/2 + 1 ≥ N + 2 > d + 1 for
every d ≤ N, and Lemma H(c) gives HR(d) ≤ Q − 1.

### 4. Proof of Theorem 1

*N = 1.* Only d = 1 occurs. W(1) = {0} = T(1), so C′(1) = C′_s(1) = h(1) = C(1) and τ′(1) = τ′_s(1) = 0 = τ*(1),
since HR(1) = 0.

*N ≥ 2.* Write h as in Lemma A. If a = 0 and h is not constant, let k* = max{ k : c_k > 0 } = k_max. If a > 0, the
linear cost plays the role of k* below. Put ρ(d) = min(HR(d), Q − 1), so τ*(d) = d − 1 − ρ(d). By Lemma H(a), ρ has
steps in {0, 1} for d ≥ 2, so τ*(d) − τ*(d − 1) ∈ {0, 1}. Also 0 ≤ ρ(d) ≤ HR(d) ≤ d − 1, so 0 ≤ τ*(d) ≤ d − 1.

*Largest rule.* We show C′(d) = C(d) and τ′(d) = τ*(d) by induction on d. The case d = 1 is as for N = 1. Let
d ≥ 2. By the induction hypothesis C′ = C below d, so the compared values agree with F_d on W(d). Also
W(d) = {τ*(d−1), τ*(d−1) + 1}, where clipping is inactive since 0 ≤ τ*(d−1) ≤ d − 2, and τ*(d) ∈ W(d). It suffices
to show

- (i) τ*(d) ∈ T(d), and
- (ii) if τ*(d) = τ*(d−1), then τ*(d−1) + 1 ∉ T(d).

Then τ*(d) is a global minimiser of F_d and the largest minimiser on W(d), so C′(d) = C(d) and τ′(d) = τ*(d).

(i) If h is constant, F_d is constant and T(d) = {0, …, d − 1}. Otherwise, if HR(d) ≤ Q − 1, then
τ*(d) = L(d) ∈ T(d) by Lemma E. Otherwise HR(d) ≥ Q, so x = d + 1 ≥ 3Q + 1 by Lemma H(c). Then a = 0: if a > 0,
then k_max = N and Q > N/2, so 3Q + 1 > N + 1 ≥ x, a contradiction. Now τ*(d) = d − Q, which is the leaf split
(x − Q, Q). Every k with c_k > 0 satisfies k ≤ k_max < 2^(⌊log₂ k_max⌋ + 1) = 2Q. So Lemma G, with
J′ = ⌊log₂ k_max⌋ and x ≥ 3Q, gives A_k(x − Q) + A_k(Q) = A_k(x) − k = C_k(d) − h_k(d) = min F^k_d, where
h_k(d) = k since d ≥ 3Q > k. Hence d − Q ∈ T_k(d) for every such k, and d − Q ∈ T(d) by Lemma E.

(ii) If τ*(d) = τ*(d−1), then ρ(d) = ρ(d−1) + 1. This forces HR(d−1) ≤ Q − 2 and HR(d) = HR(d−1) + 1 ≤ Q − 1; in
particular h is not constant (for constant h, Q = 1 and ρ ≡ 0). So τ*(d) = L(d), and by Lemma H(b),
x ∈ (3·2^(D−1), 2^(D+1)] for some D ≥ 1, with heap leaf split (2^D, b), where b = x − 2^D ∈ (2^(D−1), 2^D]. The
split τ*(d−1) + 1 = L(d) + 1 is the leaf split (2^D + 1, b − 1). From b = HR(d) + 1 ≤ Q = 2^⌊log₂ k_max⌋ and
b > 2^(D−1) we get 2^D ≤ Q ≤ k_max. Lemma F with the cap k* (or the linear cost if a > 0) gives
F^{k*}_d(L(d) + 1) − F^{k*}_d(L(d)) = 1. By Lemma E every other term of F_d is minimal at L(d). Hence
F_d(L(d) + 1) − F_d(L(d)) ≥ c_{k*} > 0 (≥ a > 0 in the linear case), and L(d) + 1 ∉ T(d).

*Smallest rule.* By induction, τ′_s(d) = d − 1 − τ′(d) and C′_s(d) = C′(d). For d = 1 both runs give 0 and h(1).
For d ≥ 2, the smallest-rule window {τ′_s(d−1), τ′_s(d−1) + 1} = {d − 2 − τ′(d−1), d − 1 − τ′(d−1)} is the image of
W(d) under t ↦ d − 1 − t. The compared values are F_d (by the induction hypothesis and the largest-rule result),
and F_d(t) = F_d(d − 1 − t). So both windows have the same minimum, C′_s(d) = C′(d) = C(d), and the smallest
minimiser of the mirrored window is the mirror image of the largest minimiser of W(d). ∎

### 5. Independence of N; proof of the Corollary

**Proposition 5.** Let h be concave and nondecreasing on {1, …, N} and 1 ≤ d ≤ M ≤ N. Write τ*_M(d) for τ*(d)
computed from the restriction of h to {1, …, M}. Then τ*_M(d) = τ*_N(d).

*Proof.* It suffices to compare M = d with N. Let k_d and k_N be the values of k_max on {1, …, d} and {1, …, N}, and
Q_d, Q_N the corresponding powers of two. If k_d < d, then Δh(j) = 0 for k_d < j ≤ d. Concavity gives Δh(j) ≤ 0
for all j > k_d, monotonicity gives Δh(j) ≥ 0, so h is constant on [k_d, N] and k_N = k_d. If k_d = d (this includes d = 1, where HR(1) = 0), then HR(d) ≤ Q_d − 1 by the argument of Remark (i), and
Q_N ≥ Q_d because k_N ≥ k_d. Both formulas then give d − 1 − HR(d). ∎

The run itself depends only on h(1), …, h(d) up to step d, so Proposition 5 also follows from Theorem 1. The direct
proof shows that the formula is consistent on its own. *Proof of the Corollary:* apply the Theorem to the
restriction of h to {1, …, n} for each n, and use Proposition 5.

## Remarks

1. **Both hypotheses are needed in general.** Outside the hypotheses the run can fail, under both tie rules:
   - h = (0, 1, −2, −5), concave but not monotone: first wrong value at d = 4;
   - h = (0, 1, 1, 1, 2, 2, 2), nondecreasing but not concave: first wrong value at d = 7;
   - h = (0, −3, −2, 0, 2), convex and not monotone: first wrong value at d = 5.

   Among all h on {1, …, 7} with h(1) = 0 and differences in [−2, 2], the run is exact under both rules for 28 of
   the 28 concave nondecreasing h, 132 of the 182 concave h that are not nondecreasing, 647 of the 701 nondecreasing
   h that are not concave, and 7 268 of the remaining 14 714. So failing a hypothesis does not always break the run.
2. **The tie rule matters.** For h(s) = min(s, 5) − 1: T(9) = {1, …, 7} and T(10) = {2, 3, 6, 7}. The largest rule
   has τ′(8) = 4 and picks τ′(9) = 5 from W(9) = {4, 5}. A rule that picks 4 at d = 9 gets W(10) = {4, 5}, which
   misses T(10), so that rule is not exact. The theorem says that the two extreme rules never fall into such a trap.
3. **Not a quadrangle-inequality case.** For concave h and positions p ≤ q < r ≤ s, put m = r − q ≥ 1, u = q − p
   and v = s − r. Then w(p, r) + w(q, s) − w(p, s) − w(q, r) = [h(m + u) − h(m)] − [h(m + u + v) − h(m + v)] ≥ 0,
   since both brackets are sums of u consecutive differences of h and the second one is shifted to the right. So
   length weights satisfy the *reverse* quadrangle inequality. The largest optimal roots need not be monotone either: for
   h(s) = min(s, 2) on {1, …, 4}, T(3) = {1} and T(4) = {0, 1, 2, 3}. The largest optimal root of an interval of
   length 4 is then i + 4, while that of its right sub-interval of length 3 is i + 3, so K(i, j) ≤ K(i+1, j) fails
   for the largest optimal roots. The convexity method of Fredman and Knuth (1974) does not apply either: for
   h(s) = min(s, 5) − 1 the increments of C for d = 1, …, 10 are (0, 1, 1, 2, 2, 1, 1, 2, 2, 1), so C is not convex.
4. **Explicit optimum.** The proof gives C_k(d) = J(d + 1) + g(d + 1) − k whenever d + 1 ≥ P (Lemma C), and for
   general concave nondecreasing h, C(d) = κd + a·E(d + 1) + Σ_k c_k C_k(d) (Lemma E).

## Literature

- **Knuth (1971)** introduced the restricted root window for optimal binary search trees. **Yao (1980)** is the
  standard reference for the quadrangle-inequality condition under which the restriction is exact. By Remark 3,
  length weights with concave h satisfy the reverse inequality, so that condition does not apply here.
- **Fredman and Knuth (1974)** study M(0) = g(0), M(n+1) = g(n+1) + min_{0≤k≤n} (αM(k) + βM(n−k)). With
  α = β = 1, g(0) = 0 and g = h this is the one-dimensional recurrence of §1. For convex g (with a condition at the
  start; their Theorem 1) they prove that M is convex. Their Lemma, formula (1.2), after de Bruijn, implies that if
  k is a minimiser at n, then k or k + 1 is a minimiser at n + 1: this is the convex counterpart of the window
  property. For affine nondecreasing h the hypotheses of their Theorem 1 and of this note overlap, and the exactness
  part of the Theorem then follows from their results with the reduction of §1. The formula of Lemma B is their
  formula (3.1). Their method rests on the convexity of M, which fails for concave h (Remark 3).
- **Glassey and Karp (1976)** and **Batty, Pelling and Rogers (1982).** The abstract of Batty, Pelling and Rogers
  (Crossref record) treats f(n) = min Σ_{i≤r} f(a_i) + g(n) over r-tuples of integers 0 ≤ a_i < n with Σ a_i = n. For
  r = 2 this has the form of the leaf recurrence A of §2, with g(x) = h(x − 1). It gives conditions under which the
  balanced split is optimal ("satisfied by many nonnegative convex sequences"), and states: "A similar recurrence
  relation is found for the solution when g satisfies certain concavity conditions." The full text was not
  accessible. Chen and Chen (2003, pp. 667–669) describe these results as follows. For increasing concave g, the best
  dividing rule is the "balanced power-of-d" rule underlying their heap recurrence; for two parts this is the heap
  split (S) of this note. For two parts they cite Glassey and Karp (1976), among others. They describe the result of
  Batty, Pelling and Rogers as covering any number of parts and generalizing it. This covers the heap-optimality
  ingredient (Lemma D, and its consequence for h through Lemma E) for increasing concave h, with priority to 1976
  and 1982.
- **Cleary, Fischer and St. John (2025)**, Theorem 6 with Lemma 22: for f strictly increasing and strictly concave,
  Σ_{internal v} f(number of leaves below v) has the GFB tree as its unique minimiser, and the GFB tree is the
  complete tree, the heap-shaped tree of this note. Lemma D for every concave nondecreasing h follows by a limit
  argument: apply the theorem to the piecewise-linear interpolation of x ↦ h(x − 1) plus ε·log x, and let ε → 0.
- **What this note adds, as far as could be established.** The bases give the optimal value and one optimal split,
  the heap split, of the one-dimensional recurrence. For concave h, the sources listed above, as far as they were
  read, do not address Knuth's restricted window in the interval recurrence, the tie rules, the trajectory once h
  becomes constant (k_max < N), or Lemmas C, F and G. When h is strictly increasing on {1, …, N}, the trajectory is
  the heap root (Remark (i)), so in
  that sub-case the additional content is only the exactness of the window under the two tie rules. Whether the
  full text of Batty, Pelling and Rogers covers non-strict monotonicity, all optimal splits, ties or the window could
  not be checked; this is why the note is marked pending.

## Scope

- Length weights w(i, j) = h(j − i) with real h. Exact arithmetic is assumed: ties are decided by exact equality.
- Only the largest and the smallest tie rule. Other deterministic or random rules can fail (Remark 2).
- The hypotheses are concavity and monotonicity on {1, …, N}. Remark 1 shows that neither can be dropped in general;
  it does not claim that every h violating them fails.
- The statement is about the values c(i, j) and the roots K(i, j) chosen by the run. Running time is not claimed
  beyond the O(n²) bound for non-empty windows.

## Verification

```bash
python theorems/knuth-window-concave-length-weights/verify.py
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and runs in
about 15 seconds on a laptop. It exits with code 0 only if every check passes. It checks:

- the heap facts: formula (S) against the array layout, and Lemma H (a)–(c), for d ≤ 20 000;
- Lemmas B, C (closed form, F1, F2), D, F and G against the dynamic program (caps k ≤ 64, up to 521 leaves; F1 for
  k < 300), and Lemmas A and E on 200 seeded random h;
- the Theorem (largest rule exact, trajectory τ*, smallest rule exact, mirrored trajectory):
  - on all 2^(N−1) supports of (c_2, …, c_{N−1}, a) for N = 2, …, 16 (65 534 supports), with unit weights and with
    seeded random weights 1…7;
  - on all integer h with h(1) = 0 and nonincreasing differences in [0, B] for (B, N) = (3, 16), (4, 14), (6, 12),
    (8, 10);
  - on 150 seeded random h (integer and fraction values) with N ≤ 200;
  - and that τ*_N(d) does not depend on N;
- the interval form: an independent implementation of the restricted run (both tie rules) against the full Θ(n³)
  dynamic program, with the formulas for K(i, j), on 200 seeded h with n ≤ 30;
- the boundary controls and examples of Remarks 1–3, the reverse quadrangle inequality (all integer h on {1, …, 8}
  with h(1) = 0 and nonincreasing differences in [0, 4]), and N = 1, 2 for all h with values in −3…3.

By Lemma E, T(d) depends only on which of a, c_2, …, c_{N−1} are positive, and the run's values and choices are
determined by T(1), …, T(N). Given Lemma E, the unit-weight support enumeration therefore covers every concave
nondecreasing real h with N ≤ 16. The random-weight and bounded-integer checks test the Theorem without relying on
Lemma E.

## Sources

- D. E. Knuth (1971). *Optimum binary search trees*. Acta Informatica 1(1), 14–25.
  [doi:10.1007/BF00264289](https://doi.org/10.1007/BF00264289)
- F. F. Yao (1980). *Efficient dynamic programming using quadrangle inequalities*. Proceedings of the 12th Annual
  ACM Symposium on Theory of Computing (STOC '80), 429–435. [doi:10.1145/800141.804691](https://doi.org/10.1145/800141.804691)
- M. L. Fredman, D. E. Knuth (1974). *Recurrence relations based on minimization*. Journal of Mathematical Analysis
  and Applications 48(2), 534–559. [doi:10.1016/0022-247X(74)90176-0](https://doi.org/10.1016/0022-247X(74)90176-0)
- C. R. Glassey, R. M. Karp (1976). *On the optimality of Huffman trees*. SIAM Journal on Applied Mathematics 31(2),
  368–378. [doi:10.1137/0131030](https://doi.org/10.1137/0131030). Not read; content as described by Chen and Chen
  (2003).
- C. J. K. Batty, M. J. Pelling, D. G. Rogers (1982). *Some recurrence relations of recursive minimization*. SIAM
  Journal on Algebraic Discrete Methods 3(1), 13–29. [doi:10.1137/0603002](https://doi.org/10.1137/0603002).
  Abstract only; the full text was not accessible.
- W.-M. Chen, G.-H. Chen (2003). *Divide-and-conquer recurrences associated with generalized heaps, optimal merge,
  and related structures*. Theoretical Computer Science 292(3), 667–677.
  [doi:10.1016/S0304-3975(01)00336-X](https://doi.org/10.1016/S0304-3975(01)00336-X)
- S. Cleary, M. Fischer, K. St. John (2025). *The GFB tree and tree imbalance indices*. arXiv:2502.12854; Bulletin
  of Mathematical Biology 87(10). [doi:10.1007/s11538-025-01522-1](https://doi.org/10.1007/s11538-025-01522-1)
