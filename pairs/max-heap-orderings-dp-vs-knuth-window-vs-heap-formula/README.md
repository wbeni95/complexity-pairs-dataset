# Maximum number of heap orderings of a binary tree (minimum hook product): DP over the root split vs Knuth's root window vs the heap formula

**Type:** T3 (poly → faster poly, in the value N) · **Verification:** V2 (exact operation counts) ·
**Provenance:** literature (credit: Cleary, Fischer & St. John 2025, for the optimal tree; see [Credit](#credit)).
Every claim below is proved in [PROOFS.md](PROOFS.md) or in the repository note it names, and checked by the scripts
listed under [Verification](#verification). The exactness of Knuth's window for this weight was not found stated in
the sources read; with the uniqueness of the optimal shape (Cleary, Fischer & St. John, Corollary 7 with Lemma 22) it
follows in a few lines (PROOFS.md §10, conditional on that cited result). The proof used here is the case h = ln of the repository note
[knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/), whose provenance is
undetermined (it may be our own result) because sources that might contain its general statement could not be read;
this does not concern its proof.

**Problem.** Given N ≥ 0, compute

  H(N) = min over binary trees T with N nodes of ∏_{v ∈ T} |T_v|,

where |T_v| is the number of nodes in the subtree rooted at v (the *hook product*; H(0) = 1). A *heap ordering* of
T labels its nodes by 1..N so that labels increase along every path away from the root. By the hook length formula
(Lemma A), T has exactly N!/∏_v |T_v| heap orderings, so **the maximum number of heap orderings of a binary tree
with N nodes is N!/H(N)**. Binary trees are ordered (each node has a left and a right subtree, possibly empty).
The instance is (N, one), where `one` is the number 1, the hook product of the empty tree, in the integer type the
implementations compute with (a Python int; the V2 harness passes a counting integer).

| Algorithm | Time (value N) | Exact multiplications + comparisons of hook-product values | Implementation |
|---|---|---|---|
| DP over the root split | Θ(N²) | N(N+1) = N(N+3)/2 + N(N−1)/2 | [dp.py](implementations/dp.py) |
| Knuth's root window, largest tie rule | Θ(N) | 4N − 2 = (3N − 1) + (N − 1), N ≥ 1 | [knuth_window.py](implementations/knuth_window.py) |
| Heap formula | Θ(log N) | ≤ 4⌊log₂(N+1)⌋ − 2 multiplications, N ≥ 2; exactly 4k − 4 at N = 2^k (k ≥ 2) | [heap_formula.py](implementations/heap_formula.py) |

**Why it's here.** The DP is the direct recurrence over root splits. The heap-shaped tree is optimal (Theorem H),
and Knuth's restricted window with two candidates per size is exact for this weight (Proposition W), which removes
a factor N; evaluating the heap's hook product directly removes another. All costs are in the value N; see
[Limits](#limits) for the bit-size view.

## Results

Every statement here is proved in [PROOFS.md](PROOFS.md) (section numbers in brackets); Theorem H and
Proposition W are the case h = ln of the repository note
[knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/), whose proofs are written
out there, and PROOFS.md §4 gives the translation.

- **Lemma A (hook length formula)** [§1]. A binary tree T with N nodes has exactly N!/∏_v |T_v| heap orderings. So
  maximising the number of heap orderings is the same as minimising the hook product.
- **The DP** [§2]. H(0) = 1 and H(d) = d · min_{0≤t≤d−1} H(t) H(d−1−t); the minimising t form the set T(d) of
  *optimal splits*.
- **Lemma H (the heap-shaped tree)** [§3]. The heap-shaped tree with d nodes has the nodes 1, …, d, and node v has the
  children 2v and 2v + 1 when these are ≤ d. With d + 1 = 2^H + e, 0 ≤ e < 2^H, its left and right root subtrees are
  heap-shaped with L(d) = 2^(H−1) − 1 + min(e, 2^(H−1)) and R(d) = 2^(H−1) − 1 + max(0, e − 2^(H−1)) nodes, so its hook
  product P satisfies P(0) = P(1) = 1, P(d) = d · P(L(d)) · P(R(d)). Moreover L(d) − L(d−1) ∈ {0, 1}, R(d) ≤ L(d),
  one root subtree is perfect, and the tree is the fully balanced tree with 2^H leaves in which the e leftmost leaves
  are replaced by cherries (the *complete tree* with d + 1 leaves in the terminology of Cleary, Fischer & St. John).
- **Theorem H (the heap shape is optimal)** [§4]. H(N) = P(N) for every N ≥ 0, and L(d) ∈ T(d) for every d ≥ 1.
  Also H(d) ≤ H(d + 1).
- **Proposition W (Knuth's window is exact)** [§4]. Run the window: τ(0) = −1 and, for d ≥ 1,
  W(d) = {t : max(τ(d−1), 0) ≤ t ≤ min(τ(d−1) + 1, d − 1)}, H′(d) = d · min_{t ∈ W(d)} H′(t) H′(d−1−t), and τ(d) is
  the largest minimiser in W(d) (H′(0) = 1). Then H′(d) = H(d) and τ(d) = L(d) for every d ≥ 1.
- **Lemma B (size of the values)** [§7]. 2^((N−1)/2) ≤ H(N) < 2^(4N) for N ≥ 1, so H(N) has Θ(N) bits. Every value
  the three algorithms multiply or compare is at most H(N) or a product H(t)·H(t′) with t + t′ ≤ N − 1 (the heap
  formula's intermediate d·P(L(d)) is at most P(d) = H(d)), so it has at most 4N bits.
- **Lemma C (cost of the heap formula)** [§6.3]. For N ≥ 2, the memoised recursion for P evaluates at most 2H − 1
  distinct arguments d ≥ 2, H = ⌊log₂(N+1)⌋, with two multiplications each: at most 4H − 2 multiplications and no
  comparisons, and at least 2(⌊log₂((N+1)/3)⌋ + 1) multiplications, so Θ(log N). For N = 2^k (k ≥ 2) it makes
  exactly 4k − 4; for N = 3 · 2^(k−1) (k ≥ 1) exactly 4k − 2. For k ≥ 2 this equals the upper bound 4H − 2 (H = k),
  which is therefore attained; it is also attained at N = 2 (H = 1, two multiplications). At k = 1 (N = 3, H = 2) the
  count is 2.
- **Counts of the DP and the window** [§6.1, §6.2]. The DP makes, for each d, d candidate products, d − 1
  comparisons and one final multiplication: N(N+3)/2 multiplications and N(N−1)/2 comparisons. The window has one
  candidate for d = 1 and exactly two for every d ≥ 2 (the window itself keeps 0 ≤ τ(d−1) ≤ d − 2): 3N − 1
  multiplications and N − 1 comparisons for N ≥ 1.

## Limits

- **Bit-size view.** The input is the integer N, ⌈log₂(N+1)⌉ bits, so the DP and the window are exponential in the
  input length (as the DP of [fibonacci-naive-vs-dp](../fibonacci-naive-vs-dp)). The output H(N) has Θ(N) bits
  (Lemma B), so no algorithm is polynomial in the input length in the bit model. All stated costs count
  multiplications and comparisons of these integers as unit cost.
- **Not counted.** N! and the division N!/H(N); the O(log N) word operations on node counts d ≤ N that compute L(d);
  loop control (PROOFS.md §8, §10).
- **Tie rule.** The window is implemented and proved with the largest tie rule only.
- **No lower bound** for the problem is claimed.

## Verification

The [checks script](../../experiments/2026-10-07_heap_orderings_checks.py) is deterministic and runs in under a
minute; the [entry's tests](../../tests/test_entry_heap_orderings.py) repeat the essential checks in a few seconds.
The proofs in [PROOFS.md](PROOFS.md) cover all N; the scripts check the statements on the ranges given. Every check
line starts with `[PASS]` or `[FAIL]`, and the script ends with `ALL CHECKS PASSED`.

- **V1.** The three implementations agree with each other and with an oracle (`harness.check`) on N = 0..40 and 16
  larger sizes up to 5000 (the DP up to N = 600). The oracle has two tiers:
  - N ≤ 20: the set of hook products of *all* binary trees with N nodes, built bottom-up (every value of every tree
    is kept), and the output must equal its minimum;
  - N ≤ 5000: as a consistency check, the explicit formula of Cleary, Fischer & St. John for the hook product of
    the complete tree (their Corollary 18 with c = −1 and the subtree counts of their Theorem 17, computed from
    its case formula).
- **Checks script.**
  - (A) Lemma A by counting all N! labellings of every binary tree with N ≤ 7 nodes (626 trees), and by the binomial
    recurrence for every tree with N ≤ 11 nodes (82 500 trees).
  - (B) Theorem H by enumerating every binary tree with N ≤ 13 nodes (742 900 at N = 13): the minimum hook product
    equals P(N). The maxima N!/H(N) for N = 1..13 are 1, 1, 2, 3, 8, 20, 80, 210, 896, 3360, 19200, 79200, 506880.
  - (C) DP = window = heap formula for every N ≤ 300 and N = 600; window = heap formula = the explicit formula for
    N ≤ 5000; = the minimum over all hook products for N ≤ 20. L(d) ∈ T(d) for every d ≤ 600 (from the DP's full sets
    of optimal splits), and T(d) ⊆ {L(d), R(d)} for d ≤ 600 (the hypothesis of the conditional remark in PROOFS.md
    §10); Proposition W: the window chooses τ(d) = L(d) for every d ≤ 5000.
  - (D) Lemma H: the formula for L(d) against the array layout, L(d) − L(d−1) ∈ {0, 1}, R(d) ≤ L(d) and the perfect
    root subtree, for d ≤ 20 000; the root subtrees of the layout for d < 600; the complete-tree description (4)
    for d < 600.
  - (E) The exact counts: DP and window for N = 0..300; heap formula for every N ≤ 20 000 (two multiplications per
    distinct argument ≥ 2, at most 4⌊log₂(N+1)⌋ − 2 and at least 2(⌊log₂((N+1)/3)⌋ + 1)), exactly 4k − 4 at
    N = 2^k for k = 2..20, and 4k − 2 at N = 3 · 2^(k−1) for k = 1..20; the upper bound 4⌊log₂(N+1)⌋ − 2 is
    attained at N = 2 and at N = 3 · 2^(k−1) for k = 2..20.
  - (F) Lemma B: 2^((N−1)/2) ≤ H(N) < 2^(4N) for N ≤ 5000, and H(d) ≤ H(d + 1) for d < 5000.
  - (G) Lemma B for the values: every value multiplied or compared is at most H(N) or a product H(t)·H(t′) with
    t + t′ ≤ N − 1 (N ≤ 120) and has at most 4N bits (N ≤ 120 for the DP, 1000 for the window, 2000 for the heap
    formula); the memo of the heap formula has |A(N)| entries and its recursion depth is at most |A(N)| + 1
    (N ≤ 20 000); the DP and the window keep N + 1 values (N ≤ 300).
  - (O) Oracle control: 307 of 307 deliberately wrong values rejected (the true value ± 1, twice the true value,
    the hook products of the path and of the maximally balanced tree, wrong types), 48 of 48 true values accepted.
- **V2 (exact counts, `measure: "reported"`).** `generate_scaling` returns (N, CountingInt(1)); CountingInt counts
  every multiplication and comparison in which a hook-product value takes part, with the implementations unchanged.
  The counts depend on N only. All three fits give α = 1.000 at tolerance 0.02.

  | Algorithm (n values) | Claimed count | Rivals (α), all rejected |
  |---|---|---|
  | DP (16..256) | n(n+1) | n 1.980, n log n 1.585, n^1.5 1.320, n² log n 0.881, n³ 0.660 |
  | window (64..16384) | 4n − 2 | √n 2.003, log n 6.508, n log n 0.869, n^1.5 0.668, n² 0.501 |
  | heap formula (2³..2¹⁷, powers of two) | 4 log₂ n − 4 | √n 0.397, n^0.25 0.794, (log n)² 0.594, n 0.199 |

- **Shape diagnostic:** MATCH for all three: n² (n = 1..24), n¹ (n = 1..24) and (log n)¹ on the doubling grid
  n = 4..65536.

## Background

Cited, not claims of this entry (the entry's `background` field lists them with their sources):

- Cleary, Fischer and St. John (2025) state that their GFB tree is the unique minimiser of ∏ (n_v + c) over the
  internal vertices, for every c > −2, among rooted binary trees with n leaves (Corollary 7), and that the GFB tree is
  the complete tree (Lemma 22). They give explicit formulas for the minimum (Theorem 17, Corollary 18), which the V1
  oracle uses as a consistency check.
- Knuth (1971) introduced the restricted root window for optimal binary search trees.

## Credit

- S. Cleary, M. Fischer and K. St. John (2025) published that the complete tree (the heap-shaped tree, Lemma H(4))
  is the unique minimiser of ∏ (n_v + c) over the internal vertices, for every c > −2, among unlabeled rooted binary
  trees with n leaves (their Corollary 7 with their Lemma 22, which identifies their GFB tree with the complete tree;
  c = −1 is the hook product, with n = N + 1 leaves and n_v − 1 = |T_v|), and
  the corresponding statement for the ŝ-shape statistic Σ log(n_v − 1) (Corollary 10), which they describe as
  answering an open question. They also give explicit formulas for the minimum (Theorem 17, Corollary 18), used
  above as a consistency check. Earlier literature on the underlying recurrence for increasing concave costs is
  discussed in the repository note [knuth-window-concave-length-weights](../../theorems/knuth-window-concave-length-weights/).
- The restricted root window is due to D. E. Knuth (1971), who introduced it for optimal binary search trees.

## Sources

- S. Cleary, M. Fischer, K. St. John (2025). *The GFB tree and tree imbalance indices*. Bulletin of Mathematical
  Biology 87(10). [doi:10.1007/s11538-025-01522-1](https://doi.org/10.1007/s11538-025-01522-1); arXiv:2502.12854.
- D. E. Knuth (1971). *Optimum binary search trees*. Acta Informatica 1(1), 14–25.
  [doi:10.1007/BF00264289](https://doi.org/10.1007/BF00264289).
