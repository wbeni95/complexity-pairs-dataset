# 3XOR: all triples vs a Patricia trie (deterministic quadratic)

**Type:** T3 (poly → faster poly) · **Verification:** V2 (exact operation counts, with rivals)

**Problem.** Input: an integer w ≥ 1 and n integers a₀..aₙ₋₁ in [0, 2ʷ). Output: indices i < j < k with
aᵢ ⊕ aⱼ ⊕ aₖ = 0 (bitwise exclusive or), or None if there are none. Any such triple is correct, so different
algorithms may return different triples.

| Algorithm | Time (n words of w bits) | Space | Implementation |
|---|---|---|---|
| All triples: t = aᵢ ⊕ aⱼ for every pair, then scan k > j for aₖ = t | Θ(n³) worst case; exactly (n³ − n)/6 word operations on every no-instance | O(1) | [all_triples.py](implementations/all_triples.py) |
| Patricia trie: zero scan, trie over the nonzero values, then for each a one linear pass that lists a ⊕ x in ascending order and merges it with the sorted values | O(n² + n·w); Θ(n²) worst case for w = O(n); exactly 7n² + 2n·log₂n − 3n on the V2 family | Θ(n) words | [patricia_trie.py](implementations/patricia_trie.py) |

**Why it is here.** If three values at distinct indices XOR to 0, then either two of them are equal and the third is
0, or all three are distinct and nonzero. The first case needs only a zero scan and the multiplicities of the
values. For the second case, put the distinct nonzero values D into a path-compressed binary trie. Its leaves, read
left to right, are D in ascending order. XOR with a fixed a swaps the two subtrees at every branching node whose bit
a has. So a walk that takes the right child first at those nodes lists a ⊕ x for all x ∈ D in ascending order, in
linear time and without sorting. Merging that list with D finds a common value c = a ⊕ b if there is one. This
follows the idea of the deterministic quadratic algorithm of Dietzfelbinger, Schlag & Walzer (2018); the code here
is an independent implementation. The correctness proof (the case analysis, the trie order and the merge) is in
entry.json.

**Verification.**
- *V1:* the validator runs n = 0..8, 10, 12, 16, 24, 32, 48, 64, 100, 150, 300 and 600, 8 instances per size
  (160 instances, 312 implementation runs; all triples up to n = 300). 79 instances have a solution and 81 do not.
  n ≤ 2 never has one; both answers occur at 15 of the 17 sizes n ≥ 3 (not at n = 4, all no, and n = 300, all yes).
  The instances mix five kinds:
  - words of ⌊log₂n⌋ + 1..3 bits (mostly yes);
  - random 64-bit words, with a planted triple half of the time;
  - words of odd Hamming weight (never a solution);
  - duplicates and 0..3 zeros on a pool of odd-weight words, which isolates the solutions (0, 0, 0) and (x, x, 0);
  - words of 1..4 bits.
- *Oracle:* `check` is independent of both implementations. A returned triple must be a tuple of three ints (bool,
  float, str and lists are rejected) with 0 ≤ i < j < k < n and XOR 0. None is judged by a hash-based Θ(n²) pair scan
  with a Counter that discounts the pair's own indices, as in the 3SUM harness. `equal` compares only whether a
  triple was found.
- *Experiment* ([script](../../experiments/2026-10-06i_three_xor.py)):
  - 525 more instances for both implementations (248 yes, 277 no) and 20 for the trie alone (n = 300, 600):
    0 disagreements, 0 check failures;
  - **oracle control:** 2977 deliberately wrong outputs on 360 instances, **all rejected**. They include a triple with
    nonzero XOR, a repeated index whose XOR is 0 ((i, i, z) with a_z = 0), unsorted indices, negative indices that
    alias a real solution through Python's negative indexing, out-of-range indices, the wrong arity, bool, float and
    str entries (including (False, True, k) where a₀ ⊕ a₁ ⊕ aₖ = 0), None on a yes-instance and a triple on a
    no-instance. All 720 outputs of the two implementations were accepted.
- *V2:* the scaling instance for n = 2^(w−1) is the set of all w-bit words of odd Hamming weight (w = log₂n + 1),
  shuffled, with values of a counting integer type. It counts every ⊕, &, |, shift, comparison and truth test on
  input-derived values. Three odd-weight words never XOR to 0, so neither algorithm stops early. For each a, the
  list a ⊕ D is the set of even-weight words, which interleaves with D, so the merge runs 2n − 1 steps. The counts
  equal the hand-derived closed forms for every n checked (all triples n = 1..512, the trie n = 1..2048, powers of
  two), also per kind of operation, and do not depend on the shuffle.

| Fit (tolerance 0.02) | α | Rivals (must not fit) | Shape diagnostic |
|---|---|---|---|
| all triples vs (n³ − n)/6, n = 16..512 | 1.000 | n²: 1.500, n³·log n: 0.929, n⁴: 0.750 | doubling n = 1..512: MATCH n³ |
| Patricia trie vs 7n² + 2n·log₂n − 3n, n = 32..2048 | 1.000 | n³: 0.664, n²·log n: 0.911, n·log n: 1.678 | doubling n = 1..2048: MATCH n² |

The log-factor diagnostic is resolved in both fits. The bare leading terms would also fit (n³: 1.0003, n²: 0.9966),
but the cost expressions are the exact closed forms (RL-062). CPython 3.14.2 and 3.12.10 give identical count series
(same SHA-256), and no counted operation runs inside a CPython built-in.

**Caveats.**
- Word operations on w-bit words are counted at unit cost, as on a word RAM.
- Building the trie takes up to n·w bit tests, so the trie algorithm is O(n² + n·w). The Θ(n²) bound needs
  w = O(n). On the V2 family w = log₂n + 1, and the build is the lower-order term 2n·log₂n.
- Θ(n³) is the worst case of all triples, reached on every no-instance. On yes-instances both algorithms stop at the
  first triple they find.
- Loop control, index bookkeeping and the allocation of tuples and trie nodes on plain integers are not counted.
  They are of the same order as the counted operations: one loop iteration per counted operation for all triples,
  and per round 2n − 1 node visits and 2n − 1 merge iterations against 7n − 4 counted operations for the trie. As one
  overall measure, sys.settrace counts 2.05 executed source lines per counted operation for all triples and 3.01 for
  the trie at n = 64.
- Both implementations assume values in [0, 2ʷ).
- The entry makes no claim about the fastest known algorithm for 3XOR and states no lower bound.

**Sources.** Dietzfelbinger, Schlag & Walzer, MFCS 2018 (the deterministic quadratic Patricia-trie idea). Jafargholi
& Viola, Algorithmica 2016 (3XOR studied alongside 3SUM in fine-grained complexity).
