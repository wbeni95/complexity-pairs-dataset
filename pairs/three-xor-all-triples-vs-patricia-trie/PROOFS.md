# Proofs: 3XOR, all triples vs Patricia trie

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
from the code in this folder: the exact operation counts for every size of their domains (sections 1–2), the
correctness and space of the all-triples scan and the fact that it returns the lexicographically first solution
(section 3), the correctness of the Patricia-trie algorithm (section 4), its O(n² + nw) bound and its Θ(n²) worst case
for log₂ n + 1 ≤ w = O(n) (section 5), its Θ(n) space (section 6), and the statement that no counted operation runs
inside a CPython built-in (section 7). Each proof is followed by the deterministic scripts or tests that check it and
the sizes they check it on. A check covers only those sizes; the proofs cover the whole domain. `entry.json` derives
both counts in the `time_complexity` fields and sketches the correctness in `algorithms[1].correctness`; sections
1–2 and 4 give the complete arguments. Section 8 lists the measured statements.

## Counting convention

`harness.py`, class `CountingInt`, with the module tally `_ops = {"xor", "and_or", "shift", "compare", "truth"}`:
`__xor__`, `__rxor__` add to `"xor"`, `__and__`, `__rand__`, `__or__`, `__ror__` to `"and_or"`, the shifts to
`"shift"` (all through `_op`, which returns a new `CountingInt`); the six comparisons add to `"compare"` and
`__bool__` to `"truth"`; there is no hash. `reported_cost(output)` returns the sum of the tallies. An operation with
at least one `CountingInt` operand counts 1 (with a plain left operand the int method returns `NotImplemented` and
Python calls the reflected method). Plain: indices, `mask = 1 << bit`, list lengths, `isinstance` tests, list
truthiness and the index comparisons in `_order3`.

**The V2 family.** `generate_scaling(n, rng)` requires n = 2^(w−1) (a power of two), sets w = n.bit_length(), and
returns all w-bit words of odd Hamming weight, shuffled by `rng`, as `CountingInt` values; it resets the tally.
There are 2^(w−1) = n such words, none is 0, and the instance has no solution, since the XOR of three odd-weight
words has odd weight and is not 0.

## 1. All triples: C(n, 2) XORs + C(n, 3) equality tests = (n³ − n)/6

**Statement.** For every n ≥ 0 and every instance without a solution whose values are `CountingInt`,
`three_xor_all_triples` makes exactly C(n, 2) XORs and C(n, 3) equality tests, C(n + 1, 3) = (n³ − n)/6 counted
operations; one middle-loop iteration per XOR and one inner-loop iteration per test.

**Proof.** With no solution the function never returns early. The middle loop runs once per pair i < j and computes
`t = values[i] ^ values[j]` (1 XOR); the inner loop runs once per triple i < j < k and evaluates
`values[k] == t` (1 comparison). By Pascal's rule C(n, 2) + C(n, 3) = C(n + 1, 3) = (n + 1)n(n − 1)/6.

**Check.** `experiments/2026-10-06i_three_xor.py` (n = 1, 2, 4, …, 512, in total and per kind).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "3XOR all triples (n^3-n)/6": n = 1, 2, 4, …, 512
(includes the V2 sizes n = 16..512). `experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "3XOR:
counts on other shuffles, per kind, and per-round node visits and merge steps": n = 1, 2, 4, …, 256, 3 other
shuffles each.

## 2. Patricia trie on the V2 family: 7n² + 2n log₂n − 3n

**Statement.** For every n = 2^(w−1) (w ≥ 1) and every shuffle, `three_xor_patricia_trie` on the V2 family makes
exactly 7n² + 2n log₂n − 3n counted operations: n² XORs, n log₂n + n(n − 1) ANDs, as many truth tests, and 4n² − n
comparisons (4 at n = 1). The trie has n leaves and n − 1 branching nodes; each round makes 2n − 1 node visits and
2n − 1 merge steps (uncounted loop work stated in the caveats).

**Proof.** *Zero scan.* `values[i] == 0` for each i: n comparisons; no value is 0, so `zeros` is empty and
`nonzero` holds all n indices.

*Build.* Claim: `_build` is called on groups consisting of all words of the family with fixed bits above `bit`, and
such a group with r = bit + 1 remaining bits has 2^(r−1) words (the r low bits range over the 2^(r−1) patterns of
the parity that makes the total weight odd). If r = 1 the group has one word and becomes a leaf without any test.
If r ≥ 2, every word of the group is tested at `bit` with `values[i] & mask` (1 AND) and the `if` (1 truth test);
the words with that bit 0 and those with it 1 each have 2^(r−2) ≥ 1 elements, so both sides are non-empty, a
branching node is created, and both halves are of the same kind with r − 1 remaining bits. The first call has r = w.
So no bit is skipped, every word is tested at the bits w − 1, …, 1, that is w − 1 = log₂n times: n log₂n ANDs and
n log₂n truth tests. The trie is a full binary tree with n single-word leaves and n − 1 branching nodes. Because the
0-side is built first at every bit from the top, the leaves come out in ascending order, so `dvals` is the ascending
list D of the n odd-weight words. (For n = 1 the single word is a leaf at once.) `if zeros:` is false.

*One round (a = `values[a_rep]`).* `_xor_ascending` pops each of the 2n − 1 nodes once: at each of the n leaves it
computes `a ^ values[node]` (1 XOR), at each of the n − 1 branching nodes `a & mask` and the `if` (2). By the
trie-order argument in `entry.json`, `algorithms[1].correctness`, the list `xs` is {a ⊕ x : x ∈ D} in ascending
order. a and x have odd weight, so a ⊕ x has even weight, and x ↦ a ⊕ x is injective: `xs` is the ascending list E of
the n even-weight words.

*Merge.* Each step evaluates `c == dvals[j]` (1 comparison; never true, since E and D are disjoint) and
`c < dvals[j]` (1 comparison), and advances past the smaller head, so the merge consumes the words of E ∪ D (all
2^w words) in increasing order and stops as soon as one list is used up. Of the two largest words 2^w − 1 (weight w)
and 2^w − 2 (weight w − 1), one is in E and one in D; the list holding 2^w − 2 is used up exactly when 2^w − 2 has
been consumed, while the other list still holds 2^w − 1. So the merge makes 2^w − 1 = 2n − 1 steps and
2(2n − 1) = 4n − 2 comparisons, and never returns.

*Totals.* Per round n XORs, 2(n − 1) bit operations and 4n − 2 comparisons, 7n − 4; with n rounds plus the zero scan
and the build: n + 2n log₂n + n(7n − 4) = 7n² + 2n log₂n − 3n, split as stated (comparisons n + n(4n − 2) = 4n² − n).
No step depends on the shuffle.

**Check.** `experiments/2026-10-06i_three_xor.py` (n = 1, 2, 4, …, 2048, in total and per kind).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "3XOR Patricia 7n^2+2n log2 n-3n": n = 1, 2, 4,
…, 2048 (includes the V2 sizes n = 32..2048); line "3XOR Patricia per kind": n = 1, 2, 4, …, 1024.
`experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "3XOR: counts on other shuffles, per kind, and
per-round node visits and merge steps": n = 1, 2, 4, …, 256, 3 other shuffles each.

## 3. All triples: correctness, the lexicographically first solution, Θ(n³) worst case, O(1) space

`three_xor_all_triples` visits the triples i < j < k in lexicographic order (i, then j, then k ascending) and tests
`values[k] == t` with t = a_i ⊕ a_j; since a_i ⊕ a_j ⊕ a_k = 0 ⟺ a_k = a_i ⊕ a_j, it returns the first solution in
that order, which is the lexicographically first one, or `None` after the last triple if there is none. On every
no-instance it makes the C(n + 1, 3) operations of section 1, and no-instances exist for every n and every w with
2^(w−1) ≥ n (n distinct odd-weight words, section 5); on every input it makes at most that many, so its worst case is
Θ(n³). Besides the input it creates only the returned triple (3 words): O(1).

**Check.** `tests/test_proofs_three_xor.py`, `test_all_triples_lexicographically_first` (500 seeded
`harness.generate` instances, n = 0..30: the output equals the lexicographically first solution found by enumerating
all triples) and `test_space` (the instrumented peak of `tests/proof_space.py` is at most 3). The V1 battery and the
experiment compare both implementations with the independent `check`.

## 4. Patricia trie: correctness

**Kinds of solutions** (as in `entry.json`). Let a_i ⊕ a_j ⊕ a_k = 0 with i, j, k distinct. If two of the values are
equal, the third is 0 (x ⊕ x = 0); if all three are equal they are all 0. If the three are pairwise distinct, none is
0 (a_k = 0 would give a_i = a_j). So every solution is (0, 0, 0), or (x, x, 0) with x ≠ 0, or three pairwise distinct
non-zero values.

**Lemma 4.1 (the build).** For a non-empty index list G whose values agree on the bits above b, define the trie
R(G, b): a leaf G if |G| = 1, or if no bit b′ ≤ b splits G (then all its values are equal, because they agree above b
and all values lie in [0, 2^w)); otherwise, for the largest bit b′ ≤ b at which G splits into G₀ (bit 0) and G₁
(bit 1), the node (2^b′, R(G₀, b′ − 1), R(G₁, b′ − 1)). Then `_build(values, G, b, leaves)` returns R(G, b) and
appends its leaves (index lists, in their original order) to `leaves` from left to right.
*Proof.* Claim, by induction on |G|: if the explicit stack `todo` holds T + [(G, b)] and the loop is run, it next
returns to `todo` = T exactly when `done` has gained one element, R(G, b), and `leaves` has gained the leaves of
R(G, b) from left to right. The inner `while True` skips every bit at which G does not split (the group keeps its
indices and their order) until either the group has size 1 or the bits run out (a leaf: `leaves` gains G, `done` gains
G[0], and `todo` is T again), or a bit b′ splits it: then `todo` = T + [(2^b′,), (G₁, b′ − 1), (G₀, b′ − 1)]. By the
induction hypothesis (|G₀|, |G₁| < |G|), processing (G₀, b′ − 1) returns `todo` to T + [(2^b′,), (G₁, b′ − 1)] with
R(G₀) and its leaves added; then (G₁, b′ − 1) likewise; then the marker pops `right` = R(G₁) and `left` = R(G₀) and
pushes the node. The top-level call starts with `todo` = [(nonzero, w − 1)] and returns `done[0]`.

**Lemma 4.2 (the trie).** The leaves of R(nonzero, w − 1) partition the non-zero indices into the classes of equal
values, one leaf per distinct non-zero value; read from left to right they are in ascending order of value; every
branching node has two non-empty subtrees, so there are |D| leaves and |D| − 1 branching nodes (D = the distinct
non-zero values). *Proof.* A leaf holds equal values (Lemma 4.1). Two different values x < y have a highest bit b* at
which they differ; they agree above it, so they stay in one group until the group is split at b* (both sides are
non-empty), which puts x on the 0-side, to the left. So different values are in different leaves, and the leaf of x
lies left of the leaf of y. A full binary tree with |D| leaves has |D| − 1 inner nodes.

**Lemma 4.3 (the walk).** For every a, `_xor_ascending(root, a, values)` returns the pairs (a ⊕ x, rep(x)), x ∈ D,
in strictly ascending order of a ⊕ x. *Proof.* The stack walk visits every leaf once; at a branching node with mask
2^b it pushes the two children so that the left one is popped first if a has bit b = 0 and the right one first
otherwise, and every leaf of the child popped first is output before any leaf of the other (the other child stays
below on the stack). For two leaves x, y with lowest common ancestor v at bit b and x in the left subtree, x and y
agree above b and x has bit b = 0, y has bit b = 1 (Lemma 4.2); so a ⊕ x and a ⊕ y agree above b, and a ⊕ x < a ⊕ y
iff bit b of a is 0, which is exactly when the walk outputs x first. x ↦ a ⊕ x is injective, so the order is strict.

**Lemma 4.4 (the merge).** The merge of `xs` (ascending a ⊕ x) with `dvals` (D ascending, Lemma 4.2) returns at a
common value if one exists. *Proof.* Both lists are strictly ascending. Let c* = xs[i*] = dvals[j*] be a common value.
As long as no common value has been met, i ≤ i* and j ≤ j*: if xs[i] < dvals[j] then xs[i] < dvals[j] ≤ dvals[j*] =
xs[i*], so i < i* and i + 1 ≤ i*; symmetrically for j. Each step increases i + j, so the loop meets some common value
no later than at (i*, j*).

**Theorem 4.5.** `three_xor_patricia_trie` returns a triple (i, j, k) with i < j < k and a_i ⊕ a_j ⊕ a_k = 0 if one
exists, and `None` otherwise.
*Proof.* The zero scan collects the zero indices `zeros` in increasing order. If 0 occurs at least 3 times, the first
three zero indices are a solution (returned in increasing order). If no value is non-zero, n ≤ 2 and there is no
triple. If 0 occurs once or twice and some leaf holds two indices (a value x ≠ 0 twice), then (x, x, 0) is a solution;
`_order3` sorts the three distinct indices. Otherwise 0 occurs at most twice, and if it occurs, every non-zero value
occurs once; so no solution of the first two kinds exists, and only three pairwise distinct non-zero values can form
one. In the round for a ∈ D, a common value c = a ⊕ b with b, c ∈ D is a solution: c ≠ 0 gives a ≠ b, c = a would
give b = 0 and c = b would give a = 0, so a, b, c are distinct and their representatives are three distinct indices,
sorted by `_order3`. Conversely, for a solution with distinct non-zero values a, b, c, the round for a (if reached)
has c = a ⊕ b in both lists, so it returns by Lemma 4.4 (an earlier round may return another solution first). If no
round returns, no solution exists.

**Check.** `tests/test_proofs_three_xor.py`, `test_trie_correct_and_kinds` (800 seeded `harness.generate`
instances, n = 0..48: a triple is returned exactly when the harness's independent Θ(n²) decision finds one, every
output passes `check`, and each of the three kinds of solution and the no-instances occur more than 20 times) and
`test_trie_shape_and_leaf_order` (300 seeded instances, n = 0..60, and the inputs 2⁰, 2¹, …, 2^(w−1) for w = 1..39: the
leaves partition the non-zero indices into classes of equal values, the leaf representatives read left to right
give the distinct values in ascending order, and for every a ∈ D the walk lists a ⊕ D in ascending order). The V1
battery, the experiment and `tests/test_entries_2026_10_06i_three_xor.py` add further instances.

## 5. Patricia trie: O(n² + nw) on every input, Θ(n²) in the worst case for log₂ n + 1 ≤ w = O(n)

**Statement.** On every input (w, values) with n values in [0, 2^w), the algorithm makes at most
n + 2nw + |D|(7|D| − 4) ≤ n + 2nw + 7n² counted operations, and its uncounted work is of the same order, so it takes
O(n² + nw) time. For every n and w with 2^(w−1) ≥ n, i.e. w ≥ log₂ n + 1, any n distinct odd-weight w-bit words form
a no-instance on which it makes exactly n² XORs. So for log₂ n + 1 ≤ w = O(n) its worst case is Θ(n²).

**Proof.** *Upper bound.* The zero scan makes n comparisons. In the build, an index is tested (one AND, one truth
test) at a bit only while its group has at least two members, and at most once per bit (the bit decreases along each
path of the trie), so there are at most nw tests: at most 2nw counted operations, and the loop overhead is O(1) per
tested index and per bit at which a group of size ≥ 2 is examined (each such step tests at least two indices), so
O(nw). The scan of the leaves for case 3 and the lists `reps` and `dvals` cost O(|D|) and no counted operation. Each of
the |D| rounds walks the 2|D| − 1 nodes of the trie (Lemma 4.2): one XOR per leaf and one AND and one truth test per
branching node, |D| + 2(|D| − 1) counted operations; and the merge makes at most 2|D| − 1 steps (each step advances
i or j, and it stops when one of them reaches |D|), each with at most two comparisons. Per round at most 7|D| − 4
counted operations, with O(1) uncounted work per node and per merge step. Total O(n + nw + |D|²) = O(n² + nw).

*Lower bound.* Three odd-weight words XOR to a word of odd weight, which is not 0, so n distinct odd-weight words form
a no-instance without zeros (they exist since there are 2^(w−1) ≥ n odd-weight w-bit words). Then D has n elements, no
round returns, and every round's walk computes one XOR per leaf: n rounds of n XORs. With w = O(n) the upper bound is
O(n²).

**Check.** `tests/test_proofs_three_xor.py`, `test_trie_operation_bound` (300 seeded `harness.generate` instances,
n = 0..60, w = 1..64, and the inputs 2⁰, …, 2^(w−1) for w = 1, 5, 17, 40, 64, all with the harness's `CountingInt`: at
most n + 2nw + 7n² counted operations) and `test_trie_quadratic_on_distinct_odd_weight` (n = 1..69; for each n
the least w with 2^(w−1) ≥ n, that is ⌈log₂ n⌉ + 1, and larger w up to 64; seeded distinct odd-weight words: no triple
and exactly n² XORs). The V2 family
is the case w = log₂ n + 1 (section 2).

## 6. Patricia trie: Θ(n) space

**Statement.** Besides the input, the algorithm holds at least n and at most 15n + 3 words (container slots) at any
time: Θ(n) words, for every w.

**Proof.** The lists `zeros` and `nonzero` hold n indices; this is the lower bound. During the build: the pending
groups in `todo`, the finished leaves and the group of the task being processed are disjoint sets of indices (at most
n together), and the current group and the two halves being formed hold at most twice that task's group more (at most
2n); `leaves` has at most |D| entries; `done` holds at most |D| finished subtrees, and the branching nodes created are
at most |D| − 1 triples; `todo` holds at most |D| pending groups (each will contain a leaf of its own) and at most
|D| − 1 markers, so at most 2|D| entries in tuples of at most 2 slots; the popped task is a tuple of 2 slots. In all
at most n + 3n + |D| + |D| + 3|D| + 2|D| + 3|D| + 2 ≤ 14n + 2. After the build: `zeros` and `nonzero` (n), `leaves`
(|D| entries and at most n indices), the trie (3(|D| − 1) slots), `reps` and `dvals` (|D| each), the previous round's
`xs` and the list being built by the walk (|D| pairs each, 3|D| slots each), and the walk's stack (at most |D|
entries, since it holds at most one pending node per level plus the current one), plus a returned triple (3): at most
2n + 13|D| + 3 ≤ 15n + 3. The depth of the trie, up to min(n − 1, w), does not enter: the build keeps no list per
level.

**Check.** `tests/test_proofs_three_xor.py`, `test_space`: on 20 seeded `harness.generate` instances (n = 0..30), on
the inputs 2⁰, …, 2^(w−1) for w = 8, 16, 32 (a trie of depth w − 1) and on the V2 family for n = 1, 2, 8, 32, the
instrumented peak of `tests/proof_space.py` lies between n and 15n + 3.

## 7. No counted operation inside a CPython built-in

Neither implementation passes an input value, or a value computed from one, to a built-in function or container
operation that compares, hashes or computes with it: the values meet only `^`, `&`, `==`, `<` and truth tests written
in the implementations themselves; `isinstance(node, int)` is applied to trie nodes and `len` to lists of indices.
`sorted`, `min`, `max`, `dict`, `set` and `hash` are not called on values (`_order3` sorts three plain indices with
its own comparisons). This is read off the code; the identical count series under two CPython versions (experiment,
part d) are consistent with it.

## 8. Measured statements (data, not theorems)

The V2 fits and shape diagnostics, the cross-version hash, and the `sys.settrace` line counts per counted operation
in the caveats are measurements; sections 1–2 prove the exact counts that they sample, and the caveats' per-round
node and merge-step counts on the V2 family are proved in section 2.
