# Proofs: permanent, sum over permutations vs Ryser's formula

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md`, the docstrings of the code and the harness): correctness, exact operation counts, the time and space
bounds, the sizes of the integers, the facts used by the V1 oracle, and the closed forms used as spot checks. Each
section names the deterministic checks that re-run its computable facts and the ranges they cover. A check covers
only its range; the written proof covers the general statement.

The statements listed under `background` in `entry.json` (#P-completeness, Glynn's formula, the approximation
scheme for non-negative matrices, BosonSampling) are cited, not proved here. The V2 runtime fits are measured
data.

Credit: the inclusion–exclusion formula is Ryser's (1963).

## 0. Conventions

A is an n × n integer matrix with |A[i][j]| ≤ M, M ≥ 1. perm(A) = Σ_s Π_i A[i][s(i)] over the permutations s of
{0, …, n − 1}; perm of the 0 × 0 matrix is 1 (one empty permutation, empty product 1).

*Arithmetic operations* are the additions, subtractions, multiplications and negations whose operands are
entries of A or values computed from entries. They are counted by running the unchanged code on matrices whose
entries are a counting integer type (`tests/test_proofs_permanent.py`, class `Counted`, which counts `+`, `-`,
`*` and unary `-` with at least one counted operand; an operation of two plain integers is not counted). Index
arithmetic, the Gray-code mask and the size counter of Ryser's loop are plain integers and are not counted.
Arithmetic is unit cost; section 4 bounds the sizes of the integers. Other elementary operations (list and tuple
indexing, appending, loop control) cost O(1).

## 0.1 The library routine `itertools.permutations` (machine-model assumption)

**Assumption (background).** CPython's `itertools.permutations(range(n))` behaves like the "roughly equivalent"
Python code given in its documentation: it yields every permutation of `range(n)` exactly once, n! tuples in
lexicographic order (this is its documented behaviour), it does O(n·n!) work in total over the whole run (amortised
O(n) per tuple, although a single step can take Θ(n^2)), and it keeps O(n) words of state. Lemma 0.1 proves the cost
properties for the documented code; that the C implementation has the same costs is assumed, not proved. Every
claim below that charges the generator's work or state is conditional on this assumption, which is listed in the
`background` of this entry and of the entries that cite this section (first-match rule ordering, linear ordering,
Hamiltonian cycle counting).

**Lemma 0.1 (the documented code, r = n).** Run to the end, the documented generator yields the n! permutations; its
`for` loop body runs exactly Σ_{k=0..n−1} n!/k! ≤ e·n! times; its rotations `indices[i:] = indices[i+1:] +
indices[i:i+1]` move Σ_{k=0..n−1} n!/k! ≤ e·n! entries in total; and each of the n! yields builds a tuple of n
entries. So its total work is O(n·n!), amortised O(n) per tuple, while the work between two yields can be
Σ_{i=1..n−1} (n − i) = n(n − 1)/2 rotated entries (and n(n + 1)/2 in the final pass). Its state is `pool`, `indices`
and `cycles` (n entries each) and the tuple being built: O(n) words.

*Proof.* For n = 0 the code yields the empty tuple and stops (the `while n` loop does not run). Let n ≥ 1. After the
first yield, each pass of the `while` loop runs the `for` loop over i = n − 1, n − 2, …: it decrements `cycles[i]`; if
that reaches 0, the entry is reset to n − i (a *rollover*, which rotates the n − i entries `indices[i:]`) and the loop
goes on to i − 1; otherwise it swaps two entries, yields and breaks; if every entry rolls over, the `else` branch
returns. So `cycles` is a counter whose digit i counts down through n − i values. Digit n − 1 starts at 1 and rolls
over in every pass. Digit i < n − 1 is decremented exactly in the passes where digit i + 1 rolls over, and it rolls
over on every (n − i)-th decrement. By induction from i = n − 1 down, with n! passes (n! − 1 that yield, and the last,
in which digit 0 rolls over and the generator returns): digit i is decremented n!/(n − i − 1)! times and rolls over
n!/(n − i)! times. The number of `for` iterations is Σ_i n!/(n − i − 1)! = Σ_{k=0..n−1} n!/k!; a rollover of digit i
rotates n − i entries, so the rotations move Σ_i (n − i)·n!/(n − i)! = Σ_{k=0..n−1} n!/k! entries; Σ_k 1/k! ≤ e. A
yielding pass rolls over at most the digits n − 1, …, 1, which rotate Σ_{i=1..n−1} (n − i) = n(n − 1)/2 entries
(attained when all of them roll over); the final pass rolls over every digit, n(n + 1)/2. ∎

**Check.** `tests/test_proofs_permutations.py` (n = 0..8: the documented code yields exactly the tuples of
`itertools.permutations(range(n))`, in order; the iteration and rotation totals equal Σ_k n!/k!; the largest work
between two yields is n(n − 1)/2 (n ≥ 2) and n(n + 1)/2 in the final pass; the state is 3n entries).

## 1. Sum over all permutations (`naive.py`)

**1.1 Correctness.** `itertools.permutations(range(n))` yields each of the n! permutations exactly once (for
n = 0 the single empty tuple; its documented behaviour, section 0.1). For each, the loop multiplies the n entries A[i][p[i]] into `prod` (starting from
1) and adds the product to `total` (starting from 0). So the result is perm(A), and 1 for n = 0.

**1.2 Exact count.** Per permutation: n multiplications (`prod *= A[i][p[i]]`, the first one 1 · entry) and one
addition. For n ≥ 1 all of them have a counted operand: n·n! multiplications and n! additions, (n + 1)·n!
arithmetic operations. For n = 0 the single addition is 0 + 1 on plain integers and nothing is counted.

**1.3 Time and space (given the assumption of section 0.1).** The inner loop costs Θ(n) per permutation, n·n! in
total. The generator does O(n·n!) work over the whole run, amortised O(n) per tuple (a single step can cost
Θ(n^2), Lemma 0.1). So the time is Θ(n·n!). Besides the input, the generator state (O(n) words), the current tuple,
`prod` and `total` take Θ(n) words.

**Checks.** `tests/test_proofs_permanent.py`: class `Correctness` (exhaustive over all 0/1 matrices with n ≤ 3,
seeded matrices with entries in [−2, 3] for n ≤ 7, against an independent row expansion); class `Counts`,
`test_naive_counts` (n = 0..8); class `WorkingMemory` (tracemalloc peak below 4096 + 64n bytes, n = 1..8).
`tests/test_proofs_permutations.py` checks Lemma 0.1.

## 2. Ryser's formula with Gray-code order (`ryser.py`)

**2.1 Ryser's formula.** For n ≥ 1, perm(A) = (−1)^n Σ_{S ⊆ {0..n−1}} (−1)^|S| Π_i Σ_{j∈S} A[i][j].

*Proof.* Expanding the product, Π_i Σ_{j∈S} A[i][j] = Σ_f Π_i A[i][f(i)] over all maps f from the rows to S. So
the right-hand side is (−1)^n Σ_f w(f)·Σ_{S ⊇ f(rows)} (−1)^|S| over all maps f from rows to columns, with
w(f) = Π_i A[i][f(i)]. For a set U of columns, Σ_{S ⊇ U} (−1)^|S| = (−1)^|U| Σ_{R ⊆ complement of U} (−1)^|R|, which is
(−1)^n if U is all n columns and 0 otherwise (Σ_{R ⊆ X} (−1)^|R| = (1 − 1)^|X| = 0 for X ≠ ∅). So only the maps
onto all n columns survive, each with weight (−1)^n·(−1)^n = 1. A map from n rows onto n columns is a bijection,
i.e. a permutation, and the sum is perm(A). ∎

**2.2 Gray-code order.** Let g(k) = k XOR (k >> 1). Claim: g(k − 1) XOR g(k) = 2^v, where v is the index of the
lowest set bit of k, and g is a bijection of {0, …, 2^n − 1}. *Proof.* k XOR (k − 1) = 2^(v+1) − 1 (bits 0..v), and
(k >> 1) XOR ((k − 1) >> 1) = (k XOR (k − 1)) >> 1 = 2^v − 1, so their XOR is 2^v. g is injective because k is
recovered from g(k) bit by bit from the top (bit i of k is the XOR of the bits i, i + 1, … of g(k)), hence a
bijection. ∎ The loop starts with `gray = 0` and, at step k = 1, …, 2^n − 1, flips bit v of `gray`, so by induction
`gray` = g(k) after step k: the loop visits every non-empty column set S exactly once. The empty set contributes
the product of n empty sums, 0, for n ≥ 1, so skipping it is correct.

**2.3 Bookkeeping.** After each step `rowsum[i]` = Σ_{j∈S} A[i][j] for every row i (one column enters or leaves
S, and its entries are added or subtracted), and `size` = |S|. The step adds (−1)^|S|·Π_i rowsum[i] to `total`,
and the final result is (−1)^n·total. By 2.1 and 2.2 this is perm(A); n = 0 returns 1 directly.

**2.4 Exact count.** Each of the 2^n − 1 steps makes n additions or subtractions on `rowsum`, n multiplications
(`prod` starts as the plain 1) and one addition into `total`, and it negates `prod` when |S| is odd. In the counted
model every one of these has a counted operand for n ≥ 1: at step 1 column 0 enters, so every `rowsum[i]` becomes a
counted value and stays one. There are 2^(n−1) odd sets, and the final negation happens when n is odd. In total:
(n + 1)(2^n − 1) additions and subtractions, n(2^n − 1) multiplications and 2^(n−1) + [n odd] negations, i.e.
(2n + 1)(2^n − 1) + 2^(n−1) + [n odd] arithmetic operations: Θ(n 2^n). The uncounted mask and size updates are O(1)
per step.

**2.5 Space.** `cols = list(zip(*A))` is a transposed copy, n tuples of n entries: Θ(n^2). The working state
(`rowsum`, `size`, `gray`, `total`, `prod`) is Θ(n) words.

**Checks.** `tests/test_proofs_permanent.py`: class `Correctness` (as in section 1, and Ryser's formula 2.1
evaluated directly over all subsets for n ≤ 7); class `GrayCode` (the claim of 2.2 for n ≤ 16); class `Counts`,
`test_ryser_counts` (n = 1..12, the four kinds separately); class `WorkingMemory` (tracemalloc peak at most
16n^2 + 4096 bytes, n = 1..14; an upper bound only, because CPython reuses small tuples from free lists without
a traced allocation). The V1 battery compares both implementations with the harness's subset DP for
n ≤ 12.

## 3. The improvement and the T8 tag

(n + 1)·n! / ((2n + 1)(2^n − 1)) grows without bound (n!/2^n → ∞), and both counts are super-polynomial
(n·2^n ≥ 2^n). So the pair improves a super-polynomial cost to a smaller super-polynomial one, which is the T8
classification.

## 4. Sizes of the integers

With |A[i][j]| ≤ M: in `naive.py`, |prod| ≤ M^n and |total| ≤ n!·M^n ≤ (nM)^n. In `ryser.py`, |rowsum[i]| ≤ nM,
|prod| ≤ (nM)^n and |total| ≤ (2^n − 1)(nM)^n < (2nM)^n. So every integer has at most n·log2(2nM) + 1 bits,
O(n log(nM)) for n ≥ 2. Schoolbook arithmetic on such integers costs O((n log(nM))^2) bit operations, a polynomial
factor over the unit-cost counts.

**Check.** `tests/test_proofs_permanent.py`, class `Counts`, `test_value_sizes`: the largest absolute value of any
counted intermediate stays within these bounds (naive n = 1..7, Ryser n = 1..10, entries in [−4, 4]).

## 5. Facts used by the harness and the spot checks

**5.1 perm(A) ≡ det(A) (mod 2).** det(A) = Σ_s sgn(s) Π_i A[i][s(i)] and sgn(s) = ±1 ≡ 1 (mod 2).

**5.2 `_det_mod2`.** Gaussian elimination over GF(2) on bit-mask rows: a row swap changes the determinant only by
a sign (irrelevant mod 2), adding one row to another leaves it unchanged, and the final matrix is upper triangular
with ones on the diagonal (det 1), unless a column has no pivot, in which case the first c + 1 columns of the
reduced matrix are supported on c rows, the matrix is singular and the determinant is 0. The same argument over
any field is written out in `pairs/determinant-cofactor-vs-gaussian/PROOFS.md`, section 2.

**5.3 `_subset_dp`.** ways[S] = Σ over bijections from the rows 0..|S| − 1 onto S of the product of the entries.
Induction on |S|: in such a bijection row i = |S| − 1 goes to some column j ∈ S and the other rows form a bijection
onto S − {j}. So ways[full] = perm(A). It makes Σ_S |S| = n·2^(n−1) multiplications and as many additions.

**5.4 Closed forms.** perm(J_n) = n! for the all-ones matrix (every product is 1). perm(J_n − I) is the number of
permutations without fixed points (a product is 1 iff no s(i) = i, and 0 otherwise), the derangement number D_n,
with D_0 = 1 (the empty permutation), D_1 = 0, and D_n = (n − 1)(D_{n−1} + D_{n−2}) for n ≥ 2. *Proof of the
recurrence.* Let s be a derangement of {1, …, n} and j = s(n) ≠ n (n − 1 choices). If s(j) = n, removing n and j leaves
a derangement of the other n − 2 elements, and every such derangement arises once: D_{n−2}. If s(j) ≠ n, let i_0 be
the element with s(i_0) = n (i_0 ∉ {j, n}) and define s' on {1, …, n − 1} by s'(i_0) = j and s'(i) = s(i) otherwise;
s' is a derangement (s'(i_0) = j ≠ i_0), and s is recovered from (s', j) by s(n) = j, s(i_0) = n with i_0 = s'^(−1)(j);
every derangement s' gives such an s (s(j) = s'(j) ≠ n). So this case has D_{n−1} derangements for each j.

**5.5 The determinant contrast.** The determinant is the same sum with the signs sgn(s); over a field it takes
O(n^3) field operations by Gaussian elimination (`pairs/determinant-cofactor-vs-gaussian/PROOFS.md`, section 2).
The permanent has no such row-operation invariance: perm([[1, 1], [1, 1]]) = 2, but subtracting the first row from
the second gives perm([[1, 1], [0, 0]]) = 0.

**Checks.** `tests/test_proofs_permanent.py`: class `Harness` (5.1 and 5.2 against an exact rational determinant,
n = 0..8; 5.3 against the naive sum and its operation count, n = 0..7); class `ClosedForms` (5.4: both
implementations for n = 0..8, Ryser for n = 0..12; 5.5 example).
