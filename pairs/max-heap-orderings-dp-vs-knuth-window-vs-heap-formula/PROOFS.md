# Proofs: maximum number of heap orderings, DP vs Knuth's root window vs the heap formula

This file proves every claim that this entry makes about its problem and its three algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the hook length formula, the correctness of the three implementations,
the optimality of the heap-shaped tree and the exactness of the window, the exact operation counts and the V2 closed
forms, the sizes of the values, the time and space bounds on every input, the facts used by the V1 oracle, and the
factual remarks. Two results are taken from a note of this repository whose proofs are written out there: Lemmas D
and E and Theorem 1 with Remark (i) of
[theorems/knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/README.md)
(section 4 below gives the translation). Statements about the literature are listed under `background` in
`entry.json` and are not proved here. Each section ends with the deterministic checks that re-run its computable
facts and the ranges they cover. A check covers only its range; the proofs cover the general statements.

## Conventions and cost model

A *binary tree* is ordered: every node has a left and a right subtree, each possibly empty. For a node v, |T_v| is
the number of nodes in its subtree, and the *hook product* of T is hp(T) = ∏_v |T_v| (hp of the empty tree = 1).
H(N) = min hp(T) over the binary trees with N nodes; H(0) = 1. For d ≥ 1, T(d) is the set of *optimal splits*: the
t ∈ {0, …, d − 1} that minimise H(t) H(d − 1 − t).

**Cost model.** The entry counts multiplications and comparisons of hook-product values as unit cost; these values
are integers of at most 4N bits (section 7). Operations on node counts d ≤ N (loop control, `range`, `max`, `min` and
comparisons of two counts, `int.bit_length`, shifts, dictionary operations of the memo keyed by d) are elementary
operations of O(1) cost in the machine model of the repository. The implementations call no library routine with a
non-trivial cost.

**Counting convention (V2).** `harness.py`, class `CountingInt`: `__mul__` (also bound as `__rmul__`) adds 1 to the
module tally `_ops["mul"]` and returns a new `CountingInt`; `__lt__`, `__le__`, `__gt__`, `__ge__` and `__eq__` add 1
to `_ops["cmp"]` and return a bool; `__hash__`, `__int__`, `__index__` and `__repr__` count nothing.
`generate_scaling(n, rng)` resets both tallies and returns (n, CountingInt(1)); `reported_cost(output)` returns the
sum of the two tallies, and `counts_by_kind()` returns them separately. A multiplication with a `CountingInt` operand
counts exactly 1: if the left operand is a plain int d, `int.__mul__` returns `NotImplemented` for a `CountingInt` and
Python calls `CountingInt.__rmul__`. The identity test `best is None`, the list replication `[one] * (n + 1)` and all
operations on node counts are plain and count nothing.

## 1. Lemma A: the hook length formula for binary trees

**Statement.** A binary tree T with N nodes has exactly N!/hp(T) heap orderings (labellings by 1..N that increase
along every path away from the root). Hence the maximum number of heap orderings over binary trees with N nodes is
N!/H(N).

**Proof.** Induction on N; the empty tree has one ordering and hp = 1. Let N ≥ 1 and let the root subtrees T_L, T_R
have a and b nodes, a + b = N − 1. In a heap ordering the root carries the label 1, since every other node is a
descendant of the root. The other N − 1 labels are split between the two subtrees in C(N − 1, a) ways, and a
labelling is a heap ordering exactly when each part, relabelled order-preservingly, is a heap ordering of its
subtree; the two choices are independent. So e(T) = C(N − 1, a)·e(T_L)·e(T_R) = (N − 1)!/(a! b!) · a!/hp(T_L) ·
b!/hp(T_R) = N!/(N·hp(T_L)·hp(T_R)) = N!/hp(T), since the root contributes the factor |T_root| = N. Maximising N!/hp(T)
is minimising hp(T). ∎

**Check.** `experiments/2026-10-07_heap_orderings_checks.py`, section A: every binary tree with N ≤ 7 nodes (626 trees)
by counting all N! labellings, and every tree with N ≤ 11 nodes (82 500 trees) by the binomial recurrence.
`tests/test_entry_heap_orderings.py`, `test_hook_length_formula` (N ≤ 6).

## 2. The recurrence and the DP

**Statement.** H(0) = 1 and H(d) = d·min_{0≤t≤d−1} H(t) H(d − 1 − t) for d ≥ 1. `min_hook_product_dp((N, one))` with
one = 1 returns H(N).

**Proof.** A binary tree with d ≥ 1 nodes is a root with a left subtree of some t nodes and a right subtree of
d − 1 − t nodes, and every such pair of subtrees gives a tree; its hook product is d·hp(T_L)·hp(T_R). All factors are
positive integers, so for a fixed t the least hook product is d·H(t)·H(d − 1 − t), and H(d) is the minimum over t.
The DP fills h[d] for d = 1, …, N in increasing order from h[0] = one = 1: by induction h[t] = H(t) for t < d, the
inner loop keeps the minimum of h[t]·h[d − 1 − t] (the first candidate is stored, a later one replaces it only if it
is strictly smaller), and h[d] = d·best = H(d). ∎

**Check.** Section C of the checks script (DP = window = heap formula = an independent table of the recurrence for
N ≤ 300 and N = 600; = the minimum over the hook products of all trees for N ≤ 20). The V1 oracle (section 9).

## 3. Lemma H: the heap-shaped tree

The *heap-shaped tree* with d nodes has the nodes 1, …, d, and node v has the children 2v and 2v + 1 when these are
≤ d. Write d + 1 = 2^H + e with 0 ≤ e < 2^H (H = ⌊log₂(d + 1)⌋). L(d) and R(d) = d − 1 − L(d) are the numbers of
nodes in its left and right root subtrees, and P(d) is its hook product (P(0) = 1).

**Statement.** For d ≥ 1:
1. The subtrees of the heap-shaped tree are heap-shaped. L(d) = 2^(H−1) − 1 + min(e, 2^(H−1)) and
   R(d) = 2^(H−1) − 1 + max(0, e − 2^(H−1)). Hence P(0) = P(1) = 1 and P(d) = d·P(L(d))·P(R(d)).
2. L(d) − L(d − 1) ∈ {0, 1} for d ≥ 2, and R(d) ≤ L(d).
3. At least one root subtree is perfect (2^j − 1 nodes for some j ≥ 0), with j ≤ H. If the other one is not perfect,
   its size s satisfies ⌊log₂(s + 1)⌋ = H − 1. A perfect tree with 2^j − 1 nodes (j ≥ 1) has two root subtrees of
   2^(j−1) − 1 nodes.
4. Seen as a full binary tree (every empty subtree replaced by a leaf), the heap-shaped tree with d nodes is the
   fully balanced tree with 2^H leaves in which the e leftmost leaves are replaced by a node with two leaves.

**Proof.** (1) The descendants of node v at relative depth j are the indices v·2^j, …, v·2^j + 2^j − 1 (induction on
j: the children of this block form the next block). Those ≤ d form a prefix of the block. If any index of the block
at depth j + 1 is ≤ d, then v·2^(j+1) ≤ d, and the whole block at depth j is present, since its last index
v·2^j + 2^j − 1 is less than v·2^(j+1) (v ≥ 1). Map v·2^j + r (0 ≤ r < 2^j) to 2^j + r: this preserves the child
relation (the children 2(v·2^j + r) and 2(v·2^j + r) + 1 map to 2(2^j + r) and 2(2^j + r) + 1), and it maps the
subtree of v onto a set of indices that consists of full levels followed by a prefix of the next level, that is onto
{1, …, |T_v|}. So the subtree of v is the heap-shaped tree with |T_v| nodes. At level ℓ ≥ 1 the left root subtree
(v = 2) owns the positions 2^ℓ, …, 2^ℓ + 2^(ℓ−1) − 1 and the right one (v = 3) the next 2^(ℓ−1). Levels 1, …, H − 1
are full, which gives 2^(H−1) − 1 nodes to each side, and the e nodes of level H fill the left half first: min(e,
2^(H−1)) to the left, max(0, e − 2^(H−1)) to the right. The hook product of a tree is the root size times the hook
products of its root subtrees, which gives the recurrence for P. (2) The heap-shaped tree with d nodes is the one
with d − 1 nodes plus node d, which lies in exactly one of the two root subtrees (d ≥ 2); so exactly one of L, R grows
by 1. R(d) ≤ L(d) because min(e, 2^(H−1)) ≥ max(0, e − 2^(H−1)) for 0 ≤ e < 2^H. (3) If e ≤ 2^(H−1), the right
subtree has 2^(H−1) − 1 nodes (perfect, j = H − 1), and the left one has 2^(H−1) − 1 + e nodes, which is perfect
(j = H) if e = 2^(H−1) and otherwise has ⌊log₂(2^(H−1) + e)⌋ = H − 1. If e > 2^(H−1), the left subtree has 2^H − 1
nodes (perfect, j = H), and the right one has e − 1 nodes with 2^(H−1) < e < 2^H, so ⌊log₂ e⌋ = H − 1. For
d = 2^j − 1 (e = 0, H = j) the formulas give L = R = 2^(j−1) − 1. (4) The nodes are levels 0, …, H − 1 (2^H − 1 nodes
of a fully balanced tree, whose 2^H leaves sit at depth H) and the e leftmost positions of level H; each of these
turns the leaf at its position into a node with two leaf children. ∎

**Check.** Section D of the checks script: the formula for L(d) against the array layout, L(d) − L(d − 1) ∈ {0, 1},
R(d) ≤ L(d) and the perfect root subtree for d ≤ 20 000; the root subtrees of the layout for d < 600; (4) for
d < 600. `tests/test_entry_heap_orderings.py`, `test_heap_left_against_layout` (d < 3000).

## 4. Theorem H (the heap shape is optimal) and Proposition W (the window is exact)

**Theorem H.** H(N) = P(N) for every N ≥ 0, and L(d) ∈ T(d) for every d ≥ 1.

**Proposition W.** The window run τ(0) = −1, H′(0) = 1 and, for d ≥ 1,
W(d) = {t ∈ ℤ : max(τ(d − 1), 0) ≤ t ≤ min(τ(d − 1) + 1, d − 1)}, H′(d) = d·min_{t∈W(d)} H′(t) H′(d − 1 − t), τ(d)
the largest minimiser in W(d), satisfies H′(d) = H(d) and τ(d) = L(d) for every d ≥ 1.

**Proof (translation to the repository note).** The note
[knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/README.md) studies, for
h: {1, …, N} → ℝ concave and nondecreasing, the recurrence C(0) = 0, C(d) = h(d) + min_{0≤t≤d−1} [C(t) + C(d−1−t)]
with its set of minimisers T(d) (its section 1), its one-dimensional restricted run with the window W(d) above,
τ′(0) = −1, C′(0) = 0 and the largest or smallest minimiser, and the heap-shaped tree with the same array layout and
the same L(d) (its Definitions). Fix d ≥ 1, let N = max(d, 2) and h(s) = ln s on {1, …, N}. Then h is concave and
strictly increasing: h(j) − h(j − 1) = ln(j/(j − 1)) is positive and decreasing in j. All values H(t) and H′(t) are
positive, and ln is strictly increasing, so C(t) = ln H(t) satisfies the note's recurrence with the same minimisers
T(t) (section 2), and, by induction on t, ln H′(t) = C′(t) for the note's run under the largest tie rule, with the
same window and the same chosen τ: comparing products H′(s) H′(t − 1 − s) selects the same minimisers, ties included,
as comparing the sums of their logarithms.

- *Theorem H.* The note's Lemma E (N ≥ 2, 1 ≤ d ≤ N) states that T(d) is an intersection of sets that all contain
  L(d) (or the whole set {0, …, d − 1}), so L(d) ∈ T(d). Then P(d) = H(d) by induction on d: P(0) = P(1) = 1 = H(0)
  = H(1), and for d ≥ 2, P(d) = d·P(L(d))·P(R(d)) = d·H(L(d))·H(d − 1 − L(d)) = d·min_t H(t) H(d − 1 − t) = H(d),
  by Lemma H(1), induction and L(d) ∈ T(d).
- *Proposition W.* The note's Theorem 1, part 1 (largest rule), gives C′(d) = C(d) and τ′(d) = τ*(d) for d ≤ N.
  Since h(N) > h(N − 1), its Remark (i) gives τ*(d) = L(d). So H′(d) = H(d) and τ(d) = L(d). ∎

**Monotonicity.** H(d) ≤ H(d + 1) for every d ≥ 0. *Proof.* An optimal tree with d + 1 ≥ 1 nodes has a node v
without children. Deleting v leaves a binary tree with d nodes in which the subtree of every ancestor of v has one
node less and every other subtree is unchanged; the factor |T_v| = 1 disappears. So H(d) ≤ hp(T − v) ≤ H(d + 1). ∎

**Check.** Section B of the checks script (Theorem H by enumerating every binary tree with N ≤ 13 nodes, 742 900 at
N = 13); section C (L(d) ∈ T(d) for every d ≤ 600 from the full sets of minimisers; the window chooses τ(d) = L(d)
for every d ≤ 5000; window = heap formula for N ≤ 5000); section F (monotonicity, N ≤ 5000).
`theorems/knuth-window-concave-length-weights/verify.py` checks the note. `tests/test_entry_heap_orderings.py`,
`test_window_trajectory_is_heap_left` (d < 1500).

## 5. Correctness of the window implementation and of the heap formula

**Window.** `min_hook_product_window((N, one))` with one = 1 is the run of Proposition W: `tau` holds τ(d − 1), `lo`
and `hi` are the ends of W(d), the loop visits t = lo, …, hi in increasing order, and the test `v <= best` lets a
later (larger) t replace the stored one on a tie, so `best_t` is the largest minimiser and `best` the minimum;
h[d] = d·best. By Proposition W it returns H′(N) = H(N).

**Heap formula.** `heap_left(d)` computes H = `(d + 1).bit_length() − 1` = ⌊log₂(d + 1)⌋, e = d + 1 − 2^H and
2^(H−1) − 1 + min(e, 2^(H−1)) = L(d) (Lemma H(1)); it is called only for d ≥ 2, so H ≥ 1. The memoised `hook(d)`
returns `one` = 1 for d ≤ 1 and d·hook(L(d))·hook(d − 1 − L(d)) otherwise, which is P(d) by Lemma H(1), by induction
on d. By Theorem H, P(N) = H(N).

**Check.** Section C of the checks script (DP = window = heap formula for N ≤ 300 and N = 600, window = heap formula
for N ≤ 5000), the V1 runs (section 9), and `tests/test_entry_heap_orderings.py`, `test_agree_and_check`,
`test_window_and_heap_large`.

## 6. Exact operation counts

**6.1 DP.** *Statement.* On (N, CountingInt(1)), N ≥ 0, `min_hook_product_dp` makes exactly N(N + 3)/2 counted
multiplications and N(N − 1)/2 counted comparisons, N(N + 1) in total. *Proof.* Every entry of h is a `CountingInt`:
`one` initially, and h[d] = d·best is one. For each d = 1, …, N the inner loop runs t = 0, …, d − 1 and evaluates
`v = h[t] * h[d - 1 - t]` (1 multiplication); for t = 0, `best is None` is true and the comparison is skipped; for
t ≥ 1, `v < best` counts 1. Then `h[d] = d * best` counts 1 through `__rmul__`. Per d: d + 1 multiplications and
d − 1 comparisons. Σ_{d=1..N} (d + 1) = N(N + 3)/2 and Σ (d − 1) = N(N − 1)/2. At N = 0 the loop does not run. ∎

**6.2 Window.** *Statement.* For N ≥ 1, `min_hook_product_window` makes exactly 3N − 1 counted multiplications and
N − 1 counted comparisons, 4N − 2 in total; at N = 0 none. *Proof.* Claim: for every d ≥ 1 the visited range
[lo, hi] = [max(τ(d − 1), 0), min(τ(d − 1) + 1, d − 1)] is [0, 0] for d = 1 and has exactly two elements for d ≥ 2,
and the chosen τ(d) lies in [0, d − 1]. For d = 1, τ(0) = −1 gives [0, 0]. For d ≥ 2, the induction hypothesis
0 ≤ τ(d − 1) ≤ d − 2 gives lo = τ(d − 1) and hi = τ(d − 1) + 1 ≤ d − 1, two elements; the chosen τ(d) is one of them,
so 0 ≤ τ(d) ≤ d − 1. (This uses only the window, not Proposition W.) Each candidate makes one multiplication; the
first candidate is stored without a comparison (`best is None`), a second one is compared once (`v <= best`); then
`d * best` makes one more multiplication. So d = 1 makes 2 multiplications and no comparison, and each d ≥ 2 makes 3
multiplications and 1 comparison: 2 + 3(N − 1) = 3N − 1 and N − 1. ∎

**6.3 Heap formula (Lemma C).** Let A(N) be the set of distinct arguments d ≥ 2 on which `hook` is called during
`min_hook_product_heap((N, one))`.

*Statement.* (a) The function makes exactly 2|A(N)| counted multiplications and no counted comparison, for every
N ≥ 0. (b) For N ≥ 2, with H = ⌊log₂(N + 1)⌋, ⌊log₂((N + 1)/3)⌋ + 1 ≤ |A(N)| ≤ 2H − 1, so the count lies between
2(⌊log₂((N + 1)/3)⌋ + 1) and 4H − 2, and it is Θ(log N). (c) |A(2^k)| = 2k − 2 for k ≥ 2 (4k − 4 multiplications),
|A(3·2^(k−1))| = 2k − 1 for k ≥ 1 (4k − 2 multiplications), and |A(2)| = |A(3)| = 1. (d) The upper bound 4H − 2 is
attained at N = 2 (H = 1) and at N = 3·2^(k−1) for every k ≥ 2 (H = k), and not at N = 3 (k = 1, H = 2: 2
multiplications, bound 6).

*Proof.* (a) `hook(d)` with d ≤ 1 returns `one` without an operation. For d ≥ 2, `d not in memo` and `d <= 1` act on
plain ints. On the first call with a given d the code evaluates `d * hook(left) * hook(d - 1 - left)` from left to
right: `hook(left)` returns a `CountingInt` (`one` or a stored value, by induction), so `d * hook(left)` counts 1
through `__rmul__`, and the product of that `CountingInt` with `hook(d - 1 - left)` counts 1. The value is stored, and
every later call with the same d returns it without an operation. No comparison involves a `CountingInt`.
(b) The arguments reached are the distinct subtree sizes of the heap-shaped tree with N nodes (the recursion follows
the subtrees, Lemma H(1); memoisation only skips repeated sizes). By Lemma H(3) every node has at most one non-perfect
root subtree, and the subtrees of a perfect tree are perfect, so the non-perfect subtrees lie on one path from the
root, d_0 = N, d_1, …, and along it ⌊log₂(d_i + 1)⌋ = H − i drops by one per step. A non-perfect size d_i ≥ 2 has
H − i ≥ 1 (⌊log₂(d + 1)⌋ = 0 means d = 0), so at most H of them occur. Every perfect subtree size is 2^j − 1 with
j ≤ H (Lemma H(3), and perfect trees have smaller perfect subtrees), and those ≥ 2 have 2 ≤ j ≤ H: at most H − 1.
Hence |A(N)| ≤ 2H − 1. Lower bound: along the left spine d_0 = N, d_{i+1} = L(d_i), Lemma H(2) gives L(d) ≥ R(d), so
d_{i+1} + 1 ≥ (d_i + 1)/2 and d_i + 1 ≥ (N + 1)/2^i; hence d_i ≥ 2 for every i ≤ log₂((N + 1)/3), and these sizes are
distinct (strictly decreasing) and all reached. So |A(N)| ≥ ⌊log₂((N + 1)/3)⌋ + 1. Both bounds are Θ(log N).
(c) For N = 2^k with k ≥ 2: H = k and e = 1, so the root subtrees have 2^(k−1) and 2^(k−1) − 1 nodes (Lemma H(1)).
By induction the sizes reached are the powers of two 2^k, …, 2, 1 and the perfect sizes 2^j − 1 for j = 0, …, k − 1;
those ≥ 2 are the k powers 2, …, 2^k and the k − 2 odd numbers 2^j − 1 with 2 ≤ j ≤ k − 1: 2k − 2 (powers of two
≥ 2 are even and 2^j − 1 is odd, so they are distinct). For N = 3·2^(k−1) with k ≥ 2: N + 1 = 2^k + 2^(k−1) + 1, so
H = k and e = 2^(k−1) + 1 > 2^(k−1), and the root subtrees have 2^k − 1 and 2^(k−1) nodes. The sizes ≥ 2 reached are N,
the perfect sizes 2^j − 1 for j = 2, …, k, and the powers of two 2, …, 2^(k−1): 1 + (k − 1) + (k − 1) = 2k − 1
(N is not a power of two, since 3 divides N, and not of the form 2^j − 1, since N + 1 is odd and at least 7, hence
not a power of two). For N = 3 (k = 1) the tree
is perfect and the only size ≥ 2 is 3. For N = 2, L(2) = 1 and R(2) = 0, and the only size ≥ 2 is 2. (d) At N = 2,
H = ⌊log₂ 3⌋ = 1 and 2·1 = 2 = 4H − 2. At N = 3·2^(k−1), k ≥ 2: H = k and 2(2k − 1) = 4H − 2. At N = 3: H = 2,
4H − 2 = 6, and the count is 2. ∎

**6.4 The V2 closed forms.** The V2 families and costs of `entry.json` are N(N + 1) for the DP on N = 16..256 and
4N − 2 for the window on N = 64..16 384 (sections 6.1 and 6.2), and 4 log₂ N − 4 for the heap formula on
N = 2^3, 2^5, …, 2^17 (section 6.3 (c), k = log₂ N ≥ 2). The counts depend on N only.

**Check.** Section E of the checks script: DP and window counts for N = 0..300; for every N ≤ 20 000 the heap formula
makes 2|A(N)| multiplications (A(N) computed by a separate traversal of the sizes, using L(d), whose formula
section D checks against the array layout), no comparison, and lies between the
bounds of (b); 4k − 4 at N = 2^k (k = 2..20); 4k − 2 at N = 3·2^(k−1) (k = 1..20); (d) at N = 2, at k = 2..20, and
not at k = 1; the V2 points. `tests/test_entry_heap_orderings.py`, `test_closed_form_counts`.

## 7. Lemma B: the size of the values

**Statement.** For N ≥ 1, 2^((N−1)/2) ≤ H(N) < 2^(4N), so H(N) has Θ(N) bits (at least (N − 1)/2 and at most 4N).
Every value that the three algorithms multiply or compare is at most H(N) or a product H(t)·H(t′) with
t + t′ ≤ N − 1, and has at most 4N bits.

**Proof.** *Upper bound.* H(N) = P(N) (Theorem H). In the heap-shaped tree a node whose subtree has height h (the
longest downward path has h edges) has a heap-shaped subtree (Lemma H(1)) with full relative levels 0, …, h − 1 and a
non-empty level h, so 2^h ≤ |T_v| < 2^(h+1). Subtrees of distinct nodes of equal height are disjoint, so at most
N/2^h nodes have height h. Hence log₂ P(N) = Σ_v log₂ |T_v| < Σ_v (h_v + 1) ≤ Σ_{h≥0} (h + 1) N/2^h = 4N (the sum is
non-empty for N ≥ 1). So H(t) ≤ 2^(4t) for every t ≥ 0, with equality only at t = 0, and
H(t)·H(t′) ≤ 2^(4(t+t′)) ≤ 2^(4(N−1)) for t + t′ ≤ N − 1. *Lower bound.* A binary tree with N ≥ 1 nodes and ℓ nodes
without children has N − 1 edges; with n_1 nodes with one child and n_2 with two, N = ℓ + n_1 + n_2 and
N − 1 = n_1 + 2n_2, so ℓ = n_2 + 1 and n_1 = N − 2ℓ + 1 ≥ 0, that is ℓ ≤ (N + 1)/2. The other N − ℓ ≥ (N − 1)/2
nodes have |T_v| ≥ 2, so hp(T) ≥ 2^((N−1)/2) for every tree, and so for H(N).
*The values.* The DP and the window multiply h[t] = H(t) by h[d − 1 − t] = H(d − 1 − t) (section 2 and
Proposition W), compare such products, whose indices add up to d − 1 ≤ N − 1, and multiply d ≤ N by such a product,
with result H(d). The heap formula multiplies d by P(L(d)) = H(L(d)), then d·P(L(d)) by P(R(d)) = H(R(d)), with
result P(d) = H(d). The values are therefore: H(t) = H(t)·H(0) for t ≤ N − 1, and H(N); products H(t)·H(t′) with
t + t′ ≤ N − 1; node counts d ≤ N ≤ H(N) (the root factor of every tree with N nodes is N); results H(d) ≤ H(N)
(monotonicity, section 4); and the intermediate d·P(L(d)) ≤ d·P(L(d))·P(R(d)) = P(d) = H(d) ≤ H(N). A value at most
H(N) < 2^(4N) has at most 4N bits, and a product H(t)·H(t′) ≤ 2^(4(N−1)) has at most 4N − 3 bits. ∎

**Check.** Section F of the checks script: both bounds for N ≤ 5000 and monotonicity for N ≤ 5000; section G: every
value multiplied or compared by the three implementations, recorded by a number type that keeps all operands and
results, is at most H(N) or of the form H(t)·H(t′) with t + t′ ≤ N − 1, for every N ≤ 120 and all three
implementations; and every such value has at most 4N bits, for every N ≤ 120 (all three), N ≤ 1000 (the window) and
N ≤ 2000 (the heap formula): 3120 runs, about 7.2 million recorded values.

## 8. Time and space on every input

**Time.** The DP makes N(N + 1) counted operations and Σ_d d = Θ(N²) iterations of loop control: Θ(N²) for N ≥ 1.
The window makes 4N − 2 counted operations and O(1) other work per d: Θ(N). The heap formula makes 2|A(N)| counted
operations, Θ(log N) for N ≥ 2 (section 6.3); each call of `hook` does O(1) word operations on node counts, and there
are at most 1 + 2|A(N)| calls (the first call, and two calls per argument computed), so O(log N) word operations.
All three count multiplications and comparisons of values of at most 4N bits (section 7) as unit cost.

**Space.** The DP and the window keep the list h of N + 1 values, of at most 4N bits each for N ≥ 1 (section 7; at
N = 0 the list is [1]), and O(1) other words: Θ(N) values. The heap formula keeps the memo, one entry per element of
A(N), and the recursion stack, whose arguments strictly decrease and all but the last of which are elements of A(N),
so its depth is at most |A(N)| + 1. For N ≥ 2, |A(N)| ≤ 2H − 1 (section 6.3(b)), so the memo has at most 2H − 1 =
O(log N) entries and the depth is at most 2H. For N ≤ 1, A(N) is empty: the memo stays empty and the depth is 1, which
is ≤ 2H for N = 1 (H = 1); at N = 0 (H = 0) the exact values are 0 entries and depth 1.

**Check.** Section E of the checks script (the counts); section G (the memo has |A(N)| entries and the recursion
depth of `hook` is at most |A(N)| + 1, N ≤ 20 000, counted by a profiler hook; the list of the DP and the window has
N + 1 entries, N ≤ 300).

## 9. Facts used by the V1 oracle (`harness.py`)

- *Tier 1, N ≤ 20.* `_all_hook_products(d)` builds S_0 = {1} and S_d = {d·a·b : 0 ≤ t ≤ d − 1, a ∈ S_t,
  b ∈ S_{d−1−t}}. By the root decomposition of section 2 (every pair of subtrees gives a tree, and every tree arises),
  S_d is exactly the set of hook products of the binary trees with d nodes, so min S_N = H(N). No minimisation is done
  before the end.
- *Tier 2, 20 < N ≤ 5000.* `cfs_formula(N)` evaluates the explicit formula of Cleary, Fischer and St. John for the
  hook product of the complete tree (background). It is a consistency check only: no claim of the entry rests on it.
  Its agreement with H(N) for N ≤ 5000 is checked in section C of the checks script.
- *Types.* `check` rejects outputs that are not integers (and booleans); the implementations return integers (or
  `CountingInt`, unwrapped first).

**Check.** Section O of the checks script: 307 deliberately wrong values rejected (the true value ± 1, twice the true
value, the hook products of the path and of the maximally balanced tree, wrong types), 48 true values accepted.
`tests/test_entry_heap_orderings.py`, `test_agree_and_check`.

## 10. Remarks in the README and in `entry.json`

**Maxima.** N!/H(N) for N = 1..13 is 1, 1, 2, 3, 8, 20, 80, 210, 896, 3360, 19200, 79200, 506880: computed exactly
from H(N) (sections 1, 2) and confirmed by exhaustive enumeration of all binary trees (section B of the checks script,
`test_maximum_heap_orderings`).

**Bit-size view.** The input N has ⌈log₂(N + 1)⌉ bits, so N ≥ 2^(b−1) for an input of b ≥ 1 bits: the DP (Θ(N²))
and the window (Θ(N)) are exponential in the input length. The output H(N) has at least (N − 1)/2 bits (section 7),
so writing it takes Ω(N) bit operations, and no algorithm is polynomial in the input length in the bit model.

**Uncounted operations.** N! and the division N!/H(N) are not part of the algorithms; the O(log N) word operations of
`heap_left` and the loop control are not counted (section 8).

**Window exactness from the uniqueness of the optimal shape (conditional; not used above).** Suppose, as Cleary,
Fischer and St. John state (Corollary 7 with c = −1 and Lemma 22; background), that the complete tree is the unique
unordered shape of minimum hook product. Then the optimal ordered trees are the orderings of the heap-shaped tree, so
T(d) ⊆ {L(d), R(d)}. In particular L(d) ∈ T(d) for every d ≥ 1, since the heap-shaped tree is one of the optimal
ordered trees. Induction on d: for d = 1, W(1) = {0} = {L(1)}, H′(1) = 1 = H(1) and τ(1) = 0 = L(1). For d ≥ 2, if
H′(t) = H(t) for t < d and τ(d − 1) = L(d − 1), then W(d) = {L(d − 1), L(d − 1) + 1} (since 0 ≤ L(d − 1) ≤ d − 2),
which contains L(d) by Lemma H(2); as L(d) ∈ T(d), the minimum over W(d) is H(d)/d, so H′(d) = H(d). The largest
minimiser in W(d) is L(d), since the only other candidate is either smaller than L(d) or equal to
L(d) + 1 > L(d) ≥ R(d), which is not in T(d); so τ(d) = L(d). This is the sense of the README's
sentence that window exactness for this weight "follows in a few lines" from the cited uniqueness. The entry's proof
is section 4, which does not use it.

**Relationship and tag.** In the value N the costs are Θ(N²), Θ(N) and Θ(log N) (section 8); the entry is tagged T3
(polynomial to faster polynomial in the value N), as the bit-size view is a caveat, in the same way as
`fibonacci-naive-vs-dp`. The V2 fits are measurements of the exact counts of section 6; they prove nothing beyond
them.

**Check.** Section C of the checks script also tests the hypothesis of the conditional remark on a finite range:
T(d) ⊆ {L(d), R(d)} for every d ≤ 600 (from the DP's full sets of minimisers).
