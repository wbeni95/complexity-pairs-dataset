# Proofs: NAND-tree evaluation, deterministic vs randomized

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
except the randomized lower bound of Saks & Wigderson, which the entry records as background: the exact count of the
left-first algorithm (§1), the correctness of both algorithms (§2), the deterministic lower bound (§3), and the
worst-case expected cost of the randomized algorithm (§4). Each proof is followed by the deterministic checks that
re-run its computable facts and the ranges they cover. A check covers only those ranges; the proofs cover the whole
domain. Randomized statements assume ideal randomness (`random.getrandbits(1)` a fair bit). Checks named "test class
X" are in `tests/test_proofs_query.py`; "group G" refers to `experiments/2026-10-07_query_proof_checks.py`.

## Counting convention

`harness.py`, class `CountingLeaves`: `__getitem__` adds 1 to the module counter `_reads` and returns the leaf bit;
`__len__` does not count. `generate_scaling(n, rng)` returns `CountingLeaves(reluctant(n, 1, lambda h: 1))` and
sets `_reads = 0`; `reported_cost(output)` returns `_reads`. `nand_tree_left_first` reads leaves only through
`leaves[lo]` (in the case `size == 1`) and calls `len(leaves)` once, which is not counted. So the count is the
number of calls `evaluate(lo, 1)`.

**Trees and inputs.** A node is a pair (lo, size) with size a power of two; for size ≥ 2 its children are
(lo, size/2) and (lo + size/2, size/2). A leaf has the value of its bit, an internal node the value
NAND(x, y) = 1 − (x AND y) of its children. `reluctant(h, value, side)` with `side` ≡ 1 builds the right-zero
reluctant input of height h with root value `value`: a node of value 0 gets two children of value 1, a node of value
1 gets a left child of value 1 and a right child of value 0. The scaling instance is the one with root value 1.

## 1. Left-first: exactly 2^h leaf reads on the right-zero reluctant inputs, at most 2^h on every input

**Statement.** For every h ≥ 0 and every input of 2^h bits, `nand_tree_left_first` reads at most 2^h leaves. It
reads exactly 2^h leaves iff every internal node has a left child of value 1, that is, iff every node of value 1 has
exactly one child of value 0, the right one (a node of value 0 has two children of value 1 on every input). For h ≥ 1
these are exactly the two right-zero reluctant inputs, with root value 0 and 1; for h = 0 both one-leaf inputs are
read once. In particular the scaling instance costs exactly 2^h for every h ≥ 0.

**Proof.** Given in `entry.json`, field `correctness` of the left-first algorithm (the sentence beginning "Worst
case"). The missing steps:
(a) `evaluate(lo, size)` returns the value of its node and reads only leaves of its range, each at most once
(induction on size: the two recursive calls cover disjoint halves; if the left value is 0 the node is
NAND(0, y) = 1, otherwise NAND(1, y) = 1 − y). Hence, with R the number of reads, R(leaf) = 1 and R(node) = R(left)
if the left child has value 0, R(left) + R(right) if it has value 1; so R(node) ≤ size on every input.
(b) By induction, R(node) = size iff the left child has value 1 and R = size on both children, that is, iff every
internal node of its subtree has a left child of value 1. In a right-zero reluctant input every internal node has a
left child of value 1, and both subtrees are again right-zero reluctant inputs; this is the entry's D(h) = 2D(h − 1),
with D(0) = 1 from the single read `leaves[lo]`. The word "exactly" matters: for h = 1 and leaves 0, 0 the root has
value 1 and a child of value 0 on the right, but only 1 leaf is read.
(c) Given the root value r, the condition fixes every value from the root down: a node of value 0 has children 1, 1,
and a node of value 1 whose left child is 1 has right child 0, since NAND(1, y) = 1 − y. So the input is
`reluctant(h, r, lambda h: 1)`, which satisfies the condition by its definition.

**Check.** `experiments/2026-10-07b_nand_tree_counts.py`: the scaling instance for h = 0..16 (includes the V2 sizes
h = 4, 6, …, 16). `experiments/2026-10-07_closed_form_checks.py`, group `query`, line "NAND left-first 2^h":
h = 0..16. `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "NAND left-first: <= 2^h, = 2^h
exactly on the right-zero reluctant inputs": every input for h = 0..4 (65814 inputs); line "NAND left-first: 2^h on
the right-zero reluctant inputs (root 0 and root 1)": h = 0..16.

## 2. Correctness of both algorithms

**Statement.** For every h ≥ 0 and every input, `nand_tree_left_first` returns the root value, and
`nand_tree_random_order` returns it on every run (zero error); each reads every leaf at most once.

**Proof.** §1 (a) for the left-first algorithm. The randomized one differs only in the order of the two recursive
calls, chosen by a coin; the same induction applies, since NAND(0, y) = NAND(y, 0) = 1 and NAND(1, y) = NAND(y, 1) =
1 − y: if the child evaluated first is 0 the node is 1, and otherwise the node is the negation of the other child. ∎

**Check.** V1 (both algorithms against a full bottom-up evaluation, h ∈ {0, …, 8, 10, 12, 14, 16}); test class
`NandTreeProofChecks`, `test_randomized_exact_expectations` runs the randomized algorithm on every input for
h = 0..3 under every coin sequence and checks every answer.

## 3. Deterministic lower bound: every deterministic algorithm reads all 2^h leaves on some input

**Statement.** For every h ≥ 0 and every deterministic algorithm that always returns the root value, some input
makes it read all 2^h leaves. With §1, the worst case of the left-first algorithm, 2^h, is optimal (`lower_bounds`).

**Proof.** Claim, by induction on the height h of a node v: there is an adversary for the leaves below v (answering,
in whatever order the algorithm asks, every query to a leaf below v, interleaved with other queries) such that
(i) as long as some leaf below v is unread, both values of v are consistent with the answers given below v, and
(ii) when the last leaf below v is read, the adversary can give v any value w chosen at that moment. For h = 0, v is
a leaf: it is open until read, and the answer is w. For v = NAND(A, B), run the adversaries of A and B on their own
leaves. When the first of the two children, say A, has its last leaf read, give it the value 1 by (ii). While both
children have unread leaves, each can still take both values, independently (disjoint leaves), so v can be 0
(A = B = 1) or 1 (A = 0). After A = 1, v = NAND(1, B) = 1 − B with B still open, so v is open. At the last leaf of B,
which is the last leaf below v, give B the value 1 − w, so v = w. Applied to the root: as long as a leaf is unread,
the root value is not determined by the answers, so a correct algorithm cannot stop. ∎

**Check.** Test class `NandTreeProofChecks`, `test_deterministic_lower_bound_by_exhaustion`: an exhaustive minimax over
all deterministic adaptive strategies on all 2^(2^h) inputs gives exactly 1, 2, 4, 8 leaf reads for h = 0..3.

## 4. Randomized algorithm: worst-case expected cost R0(h) = Θ(λ^h), λ = (1 + √33)/4

Let R0(0) = R1(0) = 1, R0(h) = 2R1(h − 1) and R1(h) = R0(h − 1) + R1(h − 1)/2. Call an input reluctant if every node
of value 1 has exactly one child of value 0 (a node of value 0 always has two children of value 1).

**Statement.** For every h ≥ 0 and every input of height h, the expected number of leaf reads of
`nand_tree_random_order` is at most R0(h) if the root value is 0 and at most R1(h) if it is 1, with equality iff the
input is reluctant. Moreover R1(h) = aλ^h + bμ^h with μ = (1 − √33)/4, a = 1/2 + 5√33/66, b = 1/2 − 5√33/66, so
0.8703λ^h < R1(h) ≤ λ^h and 1.0324λ^h < R0(h) < 1.1862λ^h (h ≥ 1). Hence R0(h) > R1(h) for h ≥ 1: the worst case
over all inputs is R0(h) = Θ(λ^h) = Θ(N^(log₂ λ)), log₂ λ = 0.75372…, attained exactly on the reluctant inputs with
root value 0. The reluctant inputs with root value 1, among them the V2 instance, cost R1(h): the worst case among
inputs with root value 1, smaller than R0(h) for h ≥ 1 but of the same order (R0(h)/R1(h) lies between 1.03 and
1.37).

**Proof.** Let E(v) be the expected number of reads made while evaluating the subtree of v; it depends only on that
subtree, because the coins inside it are independent of everything else. A leaf has E = 1. For v = NAND(A, B):
if v = 0, both children are 1 and both are evaluated: E(v) = E(A) + E(B); if v = 1 with exactly one child of value
0, say A, then with probability 1/2 A comes first and the evaluation stops, and otherwise B and then A are evaluated:
E(v) = E(A) + E(B)/2; if both children are 0, only the first is evaluated: E(v) = (E(A) + E(B))/2. By induction on h,
E(v) ≤ R0(h) for value 0 and E(v) ≤ R1(h) for value 1, with equality iff the subtree is reluctant: the first two
cases give 2R1(h − 1) = R0(h) and R0(h − 1) + R1(h − 1)/2 = R1(h), with equality iff both subtrees are reluctant,
and the third gives at most R0(h − 1) < R1(h). For the closed form, R1(h) = R1(h − 1)/2 + 2R1(h − 2) for h ≥ 2, whose
characteristic roots are λ and μ, and a, b solve a + b = 1, aλ + bμ = 3/2 (indeed aλ + bμ = (λ + μ)/2 +
(5√33/66)(λ − μ) = 1/4 + 5/4). Since |μ/λ| < 1 and b > 0, R1(h)/λ^h = a + b(μ/λ)^h lies in [a − b, a + b] = [5√33/33, 1],
and it is below 1 for h ≥ 1; 5√33/33 = 0.87039…. Then R0(h)/λ^h = (2/λ)·R1(h − 1)/λ^(h−1) ∈ [2(a − b)/λ, 2/λ] =
[1.0324…, 1.1861…]. ∎

**Check.** Test class `NandTreeProofChecks`: `test_randomized_exact_expectations` (the unchanged
`nand_tree_random_order` with its coin replaced by every coin sequence in turn: the exact expected number of reads,
in rational arithmetic, on every input for h = 0..3 obeys the case formulas, is at most R0(h) or R1(h) by root value
with equality exactly on the reluctant inputs, and the maximum over all inputs is R0(h)); `test_closed_form` (R0, R1
from the recursion against the closed form and the bounds, h = 0..60). Group `nand` of the experiment script: the
same exact expectations on every input of height 4 (65536 inputs, from the case formulas) and on the reluctant inputs
of height 4 under every coin sequence of the unchanged implementation. Measured, not checked:
`experiments/2026-10-07b_nand_tree_counts.py` prints the sample means of the validator-seeded runs and their z-scores
against R1(h).

## 5. The remaining statements

- **Separation (T4).** Every deterministic algorithm reads N = 2^h leaves on some input (§3), while the randomized
  algorithm reads at most R0(h) = Θ(N^0.7537) leaves in expectation on every input (§4): proved here. That the
  randomized algorithm is optimal up to a constant factor among zero-error algorithms is the cited theorem of Saks &
  Wigderson (1986): background, not proved here.
- **Space.** Both algorithms recurse to depth h + 1 with O(1) local values per call: O(h).
- **V2 instance.** The right-zero reluctant input with root value 1 is a worst case for the left-first algorithm (§1)
  and the worst case among inputs with root value 1 for the randomized algorithm (§4); the overall worst case of the
  randomized algorithm is a reluctant input with root value 0, larger by a bounded factor (§4), so the fitted exponent
  is the same.

**Check (space).** Test class `NandTreeProofChecks`, `test_space`: the largest recursion depth of `evaluate` is h + 1
for both algorithms on the V2 instance, h = 0..12.
