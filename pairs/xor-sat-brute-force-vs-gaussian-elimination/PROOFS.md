# Proofs: XOR-SAT and #XOR-SAT, brute force vs Gaussian elimination

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code)
about its problem and its two algorithms, from first principles and from the code in this folder. Sections 1 and 2
prove the exact operation counts, for every size of their domains. Sections 3 to 7 prove the rest: the correctness
of both algorithms, the count 0 or 2^(n − rank A), the brute-force cost on systems with independent rows and its
worst case, the elimination bounds and the maximal row operations of X_n, and the caveats. Each proof is followed by
the deterministic scripts or tests that check it and the ranges they check; a check covers only those ranges, the
proofs cover the general statements. Statements about the literature (Schaefer's classes, the counting dichotomy,
#P-completeness) are not claims of this entry; they are listed in the `background` field of `entry.json` with their
sources, and nothing below depends on them.

## Counting convention

`harness.py`, class `CountingBit`: `__and__` (also bound as `__rand__`) and `__xor__` (also bound as `__rxor__`)
add 1 to the module counter `_ops` and return a new `CountingBit`; `__bool__` and `__eq__` add 1. An AND or XOR
with at least one `CountingBit` operand counts 1 (with a plain left operand the int method returns
`NotImplemented` and Python calls the reflected method). The mask arithmetic `(mask >> j) & 1`, `count += 1` and
`2 ** (n - r)` are on plain ints. `reported_cost(output)` returns `_ops`.

**The family X_n** (`_family(n)`, used by `generate_scaling(n, rng)`, which wraps every bit in `CountingBit` and
sets `_ops = 0`): for n ≥ 1, row 0 of A is all ones and, for k = 2, …, n, row k − 1 has ones exactly in column 0
and columns k, …, n − 1 (0-based); b is A applied to a fixed planted solution. A has rank n: row 0 plus row k − 1 is
the vector with ones in columns 1, …, k − 1, these n − 1 vectors are triangular, and row 0 is the only one with a
1 in column 0. (For n = 0, `_family` returns one row (b) with no coefficients; the entry's counts are stated for
the n × n systems, n ≥ 1.)

## 1. Brute force: (2n + 1)(2^(n+1) − 2) on X_n and on every n × n system of full rank

**Statement.** For every n ≥ 1, `xor_sat_brute_force` makes exactly (2n + 1)(2^(n+1) − 2) counted operations on
every n × n system of rank n whose entries are `CountingBit` values, in particular on X_n.

**Proof.** Every mask is examined (no early exit over masks). For a mask, the rows are scanned in order until the
first violated one. Evaluating a row costs n ANDs `row[j] & ((mask >> j) & 1)` (`row[j]` is a `CountingBit`), n
XORs `s ^ (…)` (`s` starts as the `CountingBit` b), and one truth test `if s`: 2n + 1. Row i (0-based) is evaluated
exactly for the masks that satisfy rows 0, …, i − 1. A has full rank, so these i rows are linearly independent, and
the system they form is consistent (A x = b has a solution); its solution set is an affine subspace of dimension
n − i, with 2^(n−i) points. Hence the total is (2n + 1) Σ_{i=0..n−1} 2^(n−i) = (2n + 1)(2^(n+1) − 2). (The argument
is the one in `entry.json`, `algorithms[0].correctness`.)

**Check.** `experiments/2026-10-06f_entries_xor_sat.py` (n = 1..16). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "XOR-SAT brute (2n+1)(2^(n+1)-2)": n = 1..16 on X_n (includes the V2 sizes n = 8, 10, …, 16;
n = 0 reported as outside the domain with count 1); group `extra`, line "XOR-SAT brute (2n+1)(2^(n+1)-2) on random
full-rank n x n systems": n = 1..10, 30 systems.

## 2. Gaussian elimination: n(n² + 6n − 4)/3 on X_n

**Statement.** For every n ≥ 1, `xor_sat_gauss` on X_n makes exactly n(n + 1)/2 truth tests in the forward
elimination, (n − 1)n(2n + 5)/6 XORs in the forward elimination and n(n − 1) operations in the back substitution,
in total n(n² + 6n − 4)/3. (At n = 0 it makes 1, the test of the single b.)

**Proof.** All entries of the working copy `M` are `CountingBit` (copies and XORs of such values).

*Invariant.* Before column c (0 ≤ c ≤ n − 1), r = c, and every row i ≥ c has ones exactly in columns c, …, i of
the A part (for c = 0, in column 0 and columns i + 1, …, n − 1 for i ≥ 1, and everywhere for i = 0).

*Column c.* The pivot search tests `M[c][c]` (1 truth test), which is 1, so p = c and the swap does nothing. Each of
the n − 1 − c rows i > c is tested (1 truth test each); `M[i][c]` is 1, so the row is XORed with the pivot row on
the n + 1 − c entries j = c, …, n (n + 1 − c XORs, the last one on b). For c = 0 the result has ones exactly in
columns 1, …, i (all ones plus column 0 and columns i + 1, …, n − 1); for c ≥ 1, columns c, …, i plus column c gives
columns c + 1, …, i. This is the invariant for c + 1, and every column gets a pivot.

*Sums.* Tests Σ_{c=0..n−1} (n − c) = n(n + 1)/2. XORs, with t = n − 1 − c: Σ_{t=0..n−1} t(t + 2) =
(n − 1)n(2n − 1)/6 + (n − 1)n = (n − 1)n(2n + 5)/6.

*After elimination.* r = n, so the consistency loop over rows r..m − 1 is empty. Back substitution: for pivot row
k (pivot column k), for each j = k + 1, …, n − 1 it computes `s ^ (row[j] & x[j])`, one counted AND (`row[j]` is a
`CountingBit`) and one counted XOR: 2(n − 1 − k), in all n(n − 1).

Total n(n + 1)/2 + (n − 1)n(2n + 5)/6 + n(n − 1) = n(2n² + 12n − 8)/6 = n(n² + 6n − 4)/3. At n = 0 there is no column,
and the consistency loop tests the single b once.

**Check.** `experiments/2026-10-06f_entries_xor_sat.py` (n = 1..200 and the V2 sizes). `experiments/2026-10-07_closed_form_checks.py`,
group `expdp`, line "XOR-SAT Gauss n(n^2+6n-4)/3": n = 1..128, 200, 256 (includes the V2 sizes n = 16, 24, 32, 48,
64, 96, 128; n = 0 reported as outside the domain with count 1). `experiments/2026-10-07_count_proof_checks.py`,
group `sat`, line "XOR-SAT Gauss: tests n(n+1)/2, XORs (n-1)n(2n+5)/6, back substitution n(n-1)": n = 1..60.

## Conventions for sections 3 to 7

A system is (n, rows); row i is (a_i1, …, a_in, b_i) and means a_i1 x_1 ⊕ … ⊕ a_in x_n = b_i over GF(2). A is the
m × n coefficient matrix, rank A its rank over GF(2), and an assignment is identified with its mask (bit j is
x_{j+1}). "Rows independent" means that the rows of A are linearly independent over GF(2).

Time is counted in the unit-cost model of `input.size_measure` (bit operations at unit cost, plus O(1) per executed
line). O and Θ are the usual asymptotic bounds over the inputs: a bound may fail on at most finitely many inputs, never
on an infinite family; where a size parameter can be 0 (m, n or min(m, n)), the bounds carry an explicit + 1 or + m + n,
or the hypothesis m ≥ 1 (n ≥ 1), so that no infinite family of inputs violates them (for example, with n = 0 both
algorithms still do Θ(m) work). Space counts the input (m(n + 1) bits), the working storage and the output.

## 3. Brute force: correctness

**Statement** (`algorithms[0].correctness`; `brute_force.py` docstring). `xor_sat_brute_force` returns the number of
solutions and, if there is one, the solution with the smallest mask.

**Proof.** For a mask, `s` starts as b_i and is XORed with a_ij·x_{j+1} for j = 0, …, n − 1, so at the end
s = b_i ⊕ (a_i · x), which is 0 iff row i holds; the row loop breaks at the first violated row, and its `else` branch
(no violated row) counts the mask and keeps the first one. Every mask is examined, so the count is exact and the
witness is the smallest solution mask. ∎

**Check.** `tests/test_proofs_xor_sat.py`, `test_correctness_count_and_echelon_form`: on every augmented matrix with
(m, n) in {(0, 0), (0, 2), (1..3, 0..3), (4, 1), (4, 2)} (9404 systems) and on 600 seeded random systems (n = 0..9,
m = 0..12), the count equals the number of solutions found by direct evaluation and the witness is the smallest one.

## 4. Gaussian elimination: correctness, rank and the count 0 or 2^(n − rank A)

**Statement** (`algorithms[1].correctness`, `idea`; `problem_statement`; `gaussian_elimination.py` docstring).
`xor_sat_gauss` returns the number of solutions and, if there is one, a solution. The number r of pivots equals
rank A, and the number of solutions is 0 or 2^(n − rank A); this proves the statement "the count is always 0 or
2^(n − rank(A))" of `problem_statement`.

**Proof.** *Row operations.* Swapping two rows, and replacing row i by row i ⊕ row r (i ≠ r), do not change the set
of solutions (the second is undone by applying it again, and every solution of the old rows satisfies the new row);
neither changes the span of the rows of A.

*Invariant.* Before column c is processed (c = 0, …, n − 1), with r = len(`pivots`): (E1) row k < r has a 1 in column
`pivots[k]` and 0 in every column left of it, and `pivots[0] < … < pivots[r−1] < c`; (E2) every row i ≥ r is 0 in
columns 0, …, c − 1. It holds for c = 0 (r = 0). Processing column c: if r = m the loop stops (no row is below the
pivot rows). Otherwise the search finds the first row p ≥ r with a 1 in column c. If there is none, rows ≥ r are 0
in column c as well, and (E1), (E2) hold for c + 1 with the same r. Otherwise rows r and p are swapped; then every
row i > r with a 1 in column c is replaced by row i ⊕ row r on the entries c, …, n. By (E2) both rows are 0 left of
column c, so this is the full row operation, and afterwards row i is 0 in columns 0, …, c. Row r becomes a pivot row
with its leading 1 in column c, and r grows by 1: (E1), (E2) hold for c + 1.

*After the loop* (all columns processed, or stopped at r = m): rows r, …, m − 1 are 0 in the A part (by (E2) with
c = n, or because there are none). The transformed system has the same solutions as the input. If one of these rows
has b = 1, it reads 0 = 1, so there is no solution and `(0, None)` is correct. Otherwise those rows read 0 = 0, and
the system is equivalent to the r pivot equations x_{p_k} ⊕ Σ_{j>p_k} M[k][j] x_j = M[k][n], k < r (p_k =
`pivots[k]`; (E1) gives the zeros left of p_k). For every choice of the n − r free variables (the columns that are
not pivots) there is exactly one solution: going through k = r − 1, …, 0, the equation k fixes x_{p_k} from variables
with larger index, which are free or were fixed before, since p_k < p_{k+1} < …. So there are exactly 2^(n − r)
solutions. Back substitution in the code does exactly this with every free variable 0: `x` starts as all zeros, and
for k = r − 1, …, 0 it sets `x[c]` = M[k][n] ⊕ Σ_{j=c+1..n−1} M[k][j]·x[j] for c = p_k. So the witness is a solution.

*Rank.* The r pivot rows are linearly independent (each has its leading 1 in a column where all later pivot rows are
0), the other rows are 0 in the A part, and row operations keep the span of the rows of A; so rank A = r. Hence the
count is 0 or 2^(n − rank A), and the returned value `2 ** (n - r)` is correct. (For n = 0 or m = 0 the loops are
empty or stop at once, and the same argument gives 1 or 0 solutions, or 2ⁿ.) ∎

**Check.** `test_correctness_count_and_echelon_form` (the systems of section 3): after forward elimination (read by a
line tracer at the consistency loop) r = rank A computed by an independent XOR basis, the pivot columns are strictly
increasing, every pivot row has its leading 1 at its pivot and the rows from r on are 0 in the A part; the count
equals the number of solutions, which is 0 or 2^(n − rank A); the witness is a solution, or None when there is none.
Also the validator's V1 battery with the certificate-based `check` (section 8).

## 5. Brute force: bounds, independent rows and the worst case

**Statement** (`algorithms[0].time_complexity`, `space_complexity`; `caveats`; `brute_force.py` docstring). (a) Brute
force makes at most 2ⁿ·m·(2n + 1) counted operations and runs in O(2ⁿ·(m + 1)(n + 1)) time on every input. (b) If the m
rows are independent (so m ≤ n), the system is consistent, row i (0-based) is reached by exactly 2^(n−i) assignments, an
assignment checks 2 − 2^(1−m) < 2 rows on average, and the count is exactly (2n + 1)(2^(n+1) − 2^(n−m+1)), which is
Θ(2ⁿ·n) for m ≥ 1; for m = n (full rank) it is (2n + 1)(2^(n+1) − 2) (section 1). (c) For n, m ≥ 1 the worst case
Θ(2ⁿ·m·n) is attained with dependent rows: m copies of the equation x_1 = 0 cost exactly (2n + 1)(m + 1)2^(n−1) counted
operations. (d) A decision brute force that stops at the first solution still examines all 2ⁿ assignments on an
unsatisfiable system. (e) The space is Θ(m(n + 1) + n): the input, O(1) extra words and the n-bit witness.

**Proof.** (a) 2ⁿ masks, at most m rows per mask, 2n + 1 counted operations and O(n + 1) steps per row (section 1),
O(1) further steps per mask and O(n) for the witness: O(2ⁿ(m(n + 1) + 1) + n) = O(2ⁿ(m + 1)(n + 1)).

(b) Independent rows of A span a space of dimension m, so the map x ↦ Ax is onto GF(2)^m and every right-hand side is
reached: the system, and every set of its rows, is consistent. Rows 0, …, i − 1 are independent and consistent, so
by section 4 they have 2^(n−i) common solutions, and row i is evaluated exactly for these. The total is
(2n + 1) Σ_{i=0..m−1} 2^(n−i) = (2n + 1)(2^(n+1) − 2^(n−m+1)), between (2n + 1)2ⁿ and (2n + 1)2^(n+1), and the
average number of rows per assignment is Σ_{i<m} 2^(−i) = 2 − 2^(1−m).

(c) An assignment with x_1 = 0 satisfies all m copies (2^(n−1) assignments, m rows each); one with x_1 = 1 fails at
the first copy (one row). Total (2n + 1)(m·2^(n−1) + 2^(n−1)) = (2n + 1)(m + 1)2^(n−1) ≥ (2n + 1)m·2^(n−1), which with
(a) gives Θ(2ⁿ·m·n).

(d) An unsatisfiable system has no solution at which to stop.

(e) Besides the input (m(n + 1) bits) the function keeps `count`, `first`, the mask and `s` (O(1) words; the mask is
one machine word for the n brute force can reach) and the witness of n bits. ∎

**Check.** `test_brute_independent_rows` (n = 1..10, every m ≤ n, 4 seeded systems with independent rows each): the
exact count of (b), below 2(2n + 1)2ⁿ. `test_brute_repeated_equation` (n = 1..8, m = 1..12): the exact count of (c).
`test_brute_upper_bound` (400 seeded random systems, n = 0..9, m = 0..12): at most 2ⁿ·m·(2n + 1). Operations are
counted with the harness's `CountingBit`. `test_brute_force_space` (200 seeded systems): every local variable is an
integer (or None), part of the input, or the witness.

## 6. Gaussian elimination: bounds and the maximal row operations of X_n

**Statement** (`algorithms[1].time_complexity`, `space_complexity`; `caveats`; docstring). (a) With k = min(m, n),
`xor_sat_gauss` makes at most 2nm + k·m(n + 1) + 2kn + m counted operations and runs in O(m·n·min(m, n) + m + n)
time.
(b) On n × n systems the worst case is Θ(n³): the exact count on X_n is n(n² + 6n − 4)/3 (section 2). (c) On every
n × n system forward elimination makes at most n(n − 1)/2 row operations and at most (n − 1)n(2n + 5)/6 entry XORs;
X_n attains both, so it does the maximal number of row operations. (d) Working storage and space Θ(m(n + 1) + n): the
copy M and the solution x.

**Proof.** (a) Copying the input costs O(m(n + 1)) and creating `x` costs O(n). Column c (at most n of them) costs at
most m − r tests in the pivot search and at most m − r − 1 tests below the pivot, fewer than 2m; there are at most k
pivot steps (each adds a pivot row and a pivot column), and each XORs at most m rows on at most n + 1 entries. The
consistency loop tests at most m entries, and back substitution makes 2 counted operations per entry right of a pivot,
at most 2n per pivot row. The sum is the stated bound. With O(1) further steps per executed line the time is O(nm +
k·m(n + 1) + kn + m + n + 1); since k ≤ min(m, n), each of nm, k·m and kn is at most m·n·k when k ≥ 1 and 0 when k = 0,
so this is O(m·n·min(m, n) + m + n + 1), and the + 1 matters only for the single input with m = n = 0.

(c) At the pivot step that creates pivot row k (pivot column c ≥ k), at most n − 1 − k rows lie below it, and each
row operation XORs n + 1 − c ≤ n + 1 − k entries. So there are at most Σ_{k=0..n−1} (n − 1 − k) = n(n − 1)/2 row
operations and at most Σ_{k} (n − 1 − k)(n + 1 − k) = Σ_{t=0..n−1} t(t + 2) = (n − 1)n(2n + 5)/6 entry XORs. On X_n
every column is a pivot column (c = k) and all n − 1 − k rows below are XORed (section 2), so both bounds are attained.

(d) M is a copy of the m rows of n + 1 entries; `pivots` has at most min(m, n) entries and `x` has n; the input has
m(n + 1) bits. ∎

**Check.** `test_gauss_bounds_and_maximal_row_operations`: on 600 seeded random systems (n = 1..14, half of them
square) at most the operation bound of (a) (`CountingBit`), at most n(n − 1)/2 row operations on the square ones, and
exactly n(n − 1)/2 on X_n for n = 1..14; at most (n − 1)n(2n + 5)/6 entry XORs on the square ones, and on X_n exactly
that many (as in section 2). `test_space`
(200 seeded systems): M never holds more than m(n + 1) entries and `pivots` never more than min(m, n).

## 7. The remaining claims

- *Relationship.* Gaussian elimination answers both the decision and the counting question in O(n³) bit operations
  for n × n systems (sections 4 and 6), brute force needs Θ(2ⁿ·n) on n × n full-rank systems with n ≥ 1 (section
  5 (b)); the solution set is empty or a coset of the null space of A, an affine subspace (section 4). "#XOR-SAT is easy" is this
  polynomial algorithm. The hardness of #SAT and the counting dichotomy are cited background (`background` in
  `entry.json`), not claims proved here.
- *Caveat on packed rows.* Packing a row into machine words of w bits replaces the XOR of k entries by ⌈k/w⌉ word
  XORs (the entries of one word are XORed in one operation), so the entry XORs shrink by a factor of up to w, a
  constant for a fixed word size; the tests are unchanged. This is not counted here.
- *The V1 oracle (`harness.py`, `check`).* A claimed count 0 is accepted only with a combination of input rows whose
  XOR is 0 = 1, re-verified on the input, which proves that there is no solution. A positive count is accepted only if
  it equals 2^(n − r), where r basis vectors with distinct leading columns are re-verified as combinations of input
  rows (so rank A ≥ r), n − r vectors that are 1 at one free column and 0 at the others are verified to satisfy every
  homogeneous row (they are independent, so the null space has dimension at least n − r and rank A ≤ r), and the
  witness satisfies every row; then section 4 gives exactly 2^(n − r) solutions. For n ≤ 10 the count is also
  compared with an exhaustive count.
- *Measured, not proved:* the fit values α (including 0.959 for the bare n³ and 0.996 for the bare n·2ⁿ), the V1
  agreement on 60 systems and the oracle-control tallies (1020 correct outputs accepted, 4348 wrong ones rejected) are
  results of the recorded runs (`tools/validate.py --scaling`, `experiments/2026-10-06f_entries_xor_sat.py`).
