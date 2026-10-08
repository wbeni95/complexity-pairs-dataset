# Counting n-bit integers with a cheap representation X² + C: enumeration vs interval sweep vs root groups

> **🟠 Own result.** No prior literature was found after a documented search; what was searched is listed under
> [Literature search](#literature-search). This is a statement about that search, not a claim of priority.

**Type:** T2 (naive-exp → poly), secondary T8 (super-poly → faster super-poly) · **Verification:** V2 (exact work
counts, with rivals)

**Problem.** For an integer v let L(v) be the number of binary digits of |v|, with L(0) = 1. A non-negative integer k
can be written as k = X² + C with an integer root X ≥ 0 and the offset C = k − X². This representation costs

  f_k(X) = L(X) + L(C) + [C < 0]

bits: the digits of the root, the digits of the offset, and one sign bit if the offset is negative. For n ≥ 0 let

  S_n = { k : 0 ≤ k < 2ⁿ, f_k(X) ≤ n − 4 for some X ≥ 0 }

be the integers below 2ⁿ that have a representation of at most n − 4 bits. Given n, output |S_n|.
The budget n − 4 is part of the definition; Lemma A below does not depend on it. The *decision version* (given n and
k, is k ∈ S_n?) is answered by Lemma A with one integer square root and three cost evaluations.

| Algorithm | Work reported for V2 (exact) | Word operations | Space | Implementation |
|---|---|---|---|---|
| A1: enumeration of all k with three candidate roots | 3·2ⁿ cost evaluations | Θ(2ⁿ) | O(1) words (in the word-RAM model of the entry, machine-model assumption, background) | [enumeration.py](implementations/enumeration.py) |
| A2: sweep over one interval per root | isqrt(2ⁿ − 1) + 2 roots (2^(n/2) + 1 for even n) | Θ(2^(n/2)) | O(1) words (in the word-RAM model of the entry, machine-model assumption, background) | [interval_sweep.py](implementations/interval_sweep.py) |
| A3: root groups of equal bit length | ⌊n/2⌋ + 1 groups (n ≥ 11) | O(n log n): O(n) arithmetic operations and n + 2 integer square roots (n ≥ 11) | O(1) words (in the word-RAM model of the entry, machine-model assumption, background) | [groups.py](implementations/groups.py) |

**Cost model.** Word RAM with words of n + 3 bits; addition, subtraction, multiplication, integer division,
comparison, shifts and bit length cost one operation each. For n ≥ 1, every integer the three algorithms handle has
absolute value below 2^(n+2) (for n = 0 at most 5). An integer square root is not a unit operation: A3 computes it by
Newton's iteration in O(log n) steps (Lemma N). If it were counted as one operation, A3 would use O(n) operations.
How the Python code is mapped to this model (range iteration, the one call of `math.isqrt` in A2) is a stated
machine-model assumption, listed under `background` in entry.json; the word-operation and space bounds in the table
hold under it. The exact counts and the correctness of the algorithms do not depend on the assumed costs; they use
only the documented results of these routines.

**Why A3 matters.** A2 is exponentially faster than A1, but 2^(n/2) is not the complexity of the problem: A3 needs only
polynomially many operations in n. No lower bound is claimed for any algorithm.

**Values** (computed by A2 and A3, and by A1 up to n = 16, in the checks script; |S_n| = 0 for n ≤ 5, because
every representation costs at least 2 > n − 4 bits):

| n | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 | 16 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| \|S_n\| | 3 | 8 | 21 | 51 | 127 | 257 | 565 | 1 104 | 2 378 | 4 578 | 9 748 |

| n | 20 | 24 | 29 | 32 | 40 |
|---|---|---|---|---|---|
| \|S_n\| | 158 800 | 2 552 128 | 77 512 574 | 654 251 008 | 167 502 757 888 |

At n = 200, A3 processes 101 groups.

## Main facts

Notation: r = isqrt(k) = ⌊√k⌋, B = 2ⁿ − 1, T = isqrt(B) + 1.

- **Lemma A (three candidates suffice).** For every k ≥ 0, min_X f_k(X) = min(f_k(0), f_k(r), f_k(r + 1)). A root
  below r can be cheaper than r (k = 80: f(7) = 8 < f(8) = 9; the minimum f(9) = 6 is attained only at r + 1), so
  the lemma needs a case analysis on bit lengths, not a comparison with r alone.
- **Lemma B (one interval per root).** For a root X with w = n − 4 − L(X) ≥ 1, the k ≥ 0 with f_k(X) ≤ n − 4 form
  the interval [max(0, X² − m), X² + 2^w − 1], with m = 2^(w−1) − 1 for w ≥ 2 and m = 0 for w = 1; S_n is the union
  of these intervals over X = 0..T, clipped to [0, B].
- **Lemmas C, D, E (root groups).** The left ends X² − m strictly increase with X. Inside a group of roots with the
  same bit length, the roots after the first one that start a new component of the union form a suffix of the
  group, found with two closed-form thresholds; the part of the union below 0 is [−m₁, −1], where m₁ is the m of
  X = 0, and at most two roots have intervals reaching 2ⁿ or above.
- **Lemma N.** Newton's iteration from 2^⌈L(q)/2⌉ returns ⌊√q⌋ after at most ⌊log₂(2 + log₂ q)⌋ + 2 iterations.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact work counts of all three algorithms
for every n (section 1), Lemmas 0 and A (section 2), Lemma B (section 3), the correctness of A1 and A2 (section 4),
Lemmas C, D, E and the correctness of A3 (section 5), Lemma N (section 6), the n + 2 square roots of A3 (section 7),
the word sizes (section 8), the time and space bounds (section 9), the facts the V1 oracle uses (section 10) and the
remaining statements of this page (section 11), each with the deterministic checks of its computable facts.

## Verification

- **V1.** The validator runs n = 0..17, 19, 21, …, 33, 34, 40, 64, 100 and 200 (one instance per n: the instance is
  n). A1 runs up to n = 16, A2 up to n = 34, A3 on every size. `check` in [harness.py](harness.py) is independent of
  the three implementations: for n ≤ 12 it is a brute force over all roots in the window of Lemma 0 (it uses neither
  Lemma A nor Lemma B); for 13 ≤ n ≤ 34 it is the union of the intervals of Lemma B, sorted and merged (no use of
  Lemma C or of the grouping); above, it returns None.
- **V2 (exact counts, `measure: "reported"`).** Each implementation returns (|S_n|, work). A1: 3·2ⁿ, fitted on
  n = 6..16 (even), rivals 2^(n/2), n·2ⁿ, 3ⁿ. A2: 2^(n/2) + 1, fitted on n = 12..32 (step 4), rivals 2ⁿ, n·2^(n/2),
  n³. A3: n/2 + 1 (groups), fitted on n = 12, 24, …, 384, rivals n², n log n, log n, 2^(n/2). All V2 sizes are even,
  where the closed forms are exact. The shape blocks use consecutive grids (step 2 for A2 and A3).
- **Checks script** [experiments/2026-10-07_square_plus_offset_checks.py](../../experiments/2026-10-07_square_plus_offset_checks.py)
  (standard library, deterministic, about a minute on a laptop):
  - Lemma A against a brute force over all roots in the window of Lemma 0, for **every k < 2^18**: 0 mismatches;
    Lemma 0 itself; the boundary cases k = 8 and k = 32 and the example k = 80;
  - Lemma B: sorted union = brute force over all roots, n = 1..16, and its example of an empty clipped interval
    (n = 13, X = 91);
  - A1 = A2 = A3 for n = 0..22, and A2 = A3 = sorted union for n = 0..42;
  - the structure used by A3: left ends strictly increasing (Lemma C) and component starts forming a suffix of every
    group (Lemma D), n = 5..36; the part below 0 (every root), n = 6..60; at most two roots above B (Lemma E(c)),
    n = 5..400 as recorded by A3 and n = 6..3000 by a direct count that does not use A3; L(T) = ⌊n/2⌋ + 1,
    n = 2..3000; the number of groups, n = 0..400;
  - Lemma N: Newton's square root equals `math.isqrt` on every q < 2^16 and on 20 000 seeded q < 2^600, within the
    step bound (computed in exact integers) there and on every square root A3 computes for n = 1..400;
  - the exact work counts above (n + 2 square roots of arguments below 2^(n+2) for n = 11..400, counted by a wrapper),
    and A1's counts of PROOFS.md section 4.1 (increments of r, loop tests, budget comparisons) for n = 0..16;
  - the word sizes: an instrumented copy of each implementation records every integer value of every expression
    (A1: n = 0..16, A2: n = 0..34, A3: n = 0..400); all are below 2^(n+2) for n ≥ 1 and at most 5 for n = 0;
  - |S_n| = 0 for n ≤ 5, and every value in the tables above.
- **Unit tests** [tests/test_entry_square_plus_offset.py](../../tests/test_entry_square_plus_offset.py) (about a
  second): agreement and `check` for n ≤ 30, rejected wrong outputs, the exact counts, Lemma A for every k < 2^12, the
  examples, at most two roots above B (n ≤ 300, also by a direct count), the word sizes (instrumented copies), Lemma N.

## Literature search

Searched in October 2026: Crossref (3 queries), arXiv (4 queries) and OpenAlex (2 queries), with generic keywords on
counting integers close to perfect squares or perfect powers, integers expressible as a square or power plus a small
offset, and the bit length or description length of such representations. Titles, metadata and deposited abstracts
were screened. Nothing relevant was found. The search was shallow (metadata only, no full texts, no citation
chasing). The only related hit, Rissanen (1983), *A universal prior for integers and estimation by minimum description
length*, was afterwards read in part (its introduction, pp. 416–417, and pp. 422–424 of its Section 3): it concerns a
universal prior for integers, and these pages do not contain this result. It is not used as evidence.

## Scope

- The problem as defined: L(0) = 1, a sign bit only for negative offsets, the budget n − 4, exact integer arithmetic.
  Lemma A is about min f_k and holds for every k; Lemma B, Lemma E(c) and the counts are stated for the budget n − 4.
- The entry claims correctness of all three algorithms, the exact work counts reported for V2, and the stated upper
  bounds on word operations in the stated model. It claims no lower bound and no optimality, not even of A3.
- The V2 count of A3 is the number of root groups; the O(n log n) word-operation bound is proved, not measured.
- For powers X^d, three candidate roots are not enough for any d ≥ 3: k = 2^(d+1) needs the fourth candidate X = 1
  (Corollary 2 of the theorem note
  [power-plus-offset-four-candidates](../../theorems/power-plus-offset-four-candidates/)).

## Sources

- J. Rissanen (1983). *A universal prior for integers and estimation by minimum description length*. The Annals of
  Statistics 11(2). [doi:10.1214/aos/1176346150](https://doi.org/10.1214/aos/1176346150). The one related hit of the
  literature search; read in part (its introduction, pp. 416–417, and pp. 422–424 of its Section 3): it concerns a universal
  prior for integers, and these pages do not contain the result of this entry. Not a base of this entry and not used
  as evidence for any statement.
- Python Software Foundation. *The Python Standard Library*: `int.bit_length` and ranges
  ([Built-in Types](https://docs.python.org/3/library/stdtypes.html)), `math.isqrt`
  ([math](https://docs.python.org/3/library/math.html)), read on 2026-10-07. Background only: the machine-model
  assumption of PROOFS.md section 0.
