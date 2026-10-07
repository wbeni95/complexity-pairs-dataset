# Proofs: determinant over GF(p), cofactor expansion vs Gaussian elimination

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md`, the docstrings of the code and the harness): correctness of both algorithms, their exact operation
counts, the time and space bounds, and the facts used by the V1 oracle. Each section names the deterministic checks
that re-run its computable facts and the ranges they cover. A check covers only its range; the written proof
covers the general statement.

The statements listed under `background` in `entry.json` (fast matrix multiplication, Bareiss's algorithm over the
integers, the #P-completeness of the permanent) are cited, not proved here. The V2 runtime fits are measured data.

## 0. Conventions

P = 2^31 − 1, which is prime (trial division by every d with 2 ≤ d ≤ ⌊√P⌋ = 46340). Entries are residues in
[0, P); all arithmetic is exact integer arithmetic reduced mod P, so it computes in the field GF(P) (reduction mod
P is a ring homomorphism from the integers). *Field operations* are multiplications, additions, subtractions and
reductions mod P, and inversions; with P fixed each is unit cost (an inversion is one `pow(x, P − 2, P)`: P − 2 has
31 bits, 30 of them ones, so square-and-multiply makes at most 60 multiplications). Counts below are obtained by
running the unchanged code on entries of a counting residue type (`tests/test_proofs_determinant.py`, class `C`).

The determinant is defined by the Leibniz formula det(A) = Σ_s sgn(s) Π_i A[i][s(i)], with sgn(s) = (−1)^inv(s) and
inv(s) the number of pairs i < i' with s(i) > s(i'); det of the 0 × 0 matrix is 1.

## 1. Laplace (cofactor) expansion (`cofactor.py`)

**1.1 Lemma.** For a row index r and a set S of n − r columns, let D(r, S) = Σ_σ (−1)^inv(σ) Π_{i ≥ r} A[i][σ(i)]
over the bijections σ from {r, …, n − 1} onto S (inv counted as above). Then D(n, ∅) = 1, D(0, {0, …, n − 1}) =
det(A), and, writing S_0 < S_1 < … for the elements of S,

  D(r, S) = Σ_k (−1)^k A[r][S_k] · D(r + 1, S − {S_k}).

*Proof.* Split the bijections by c = σ(r) = S_k. The inversions of σ that involve position r are the pairs (r, i')
with σ(i') < c; the values σ(i'), i' > r, are exactly the elements of S − {c}, and k of them are smaller than c.
The other inversions are those of the restriction of σ to {r + 1, …, n − 1} → S − {c}, and every such restriction
occurs once. ∎

**1.2 Correctness.** `_expand(A, r, cols)` returns D(r, cols) mod P: `cols` starts as the increasing list
0..n − 1 and stays increasing when an element is deleted, so k is the rank of c in `cols`, `k & 1` gives the sign
(−1)^k, and every intermediate value is reduced mod P (Python's `%` returns a value in [0, P)). By 1.1,
`det_cofactor(A) = _expand(A, 0, [0..n−1])` = det(A) mod P. Expanding the recursion completely gives the Leibniz
formula term by term.

**1.3 The call tree.** A call with k ≥ 1 columns left makes k calls with k − 1 columns left, so there are n!/k!
calls with k columns left, for k = n, …, 0, and Σ_{k=0..n} n!/k! calls in all. For n ≥ 1 this is ⌊e·n!⌋, since
e·n! − Σ_{k ≤ n} n!/k! = Σ_{k > n} n!/k! lies strictly between 0 and Σ_{i ≥ 1} (n + 1)^(−i) = 1/n ≤ 1.

**1.4 Exact counts and time.** Each call except the root is made inside its parent's loop together with one
multiplication `row[c] * _expand(...)`, one reduction and one addition or subtraction; each call with k ≥ 1 ends
with one more reduction; the n! calls with no column left return the constant 1. Hence, for n ≥ 1:
multiplications = additions/subtractions = ⌊e·n!⌋ − 1, reductions = (⌊e·n!⌋ − 1) + (⌊e·n!⌋ − n!), all Θ(n!).
Besides these, a call with k columns builds k child lists of length k − 1, k(k − 1) element copies, and in all
n!·Σ_{k=2..n} 1/(k − 2)! < e·n! copies. So, up to constant factors, the total work lies between n! (the leaf calls)
and n!·Σ_k (k^2 + 1)/k! ≤ 3e·n! (since Σ_{k≥0} k^2/k! = 2e): Θ(n!) time, with Θ(k^2) work at a node with k columns
left, as the entry states.

**1.5 Space.** The recursion depth is n + 1. The calls on the current path hold column lists of lengths
n, n − 1, …, 0, plus one child list under construction: O(n^2) entries, and the input has n^2 entries: Θ(n^2).

**Checks.** `tests/test_proofs_determinant.py`: class `Correctness` (both algorithms equal the Leibniz formula mod
P, exhaustively over all 0/1 matrices with n ≤ 3 and on 42 seeded matrices with n ≤ 6, including zero entries);
class `CofactorCounts` (n = 0..8: the number of calls is Σ_k n!/k! = ⌊e·n!⌋, multiplications and additions
⌊e·n!⌋ − 1, reductions as in 1.4); class `WorkingMemory` (tracemalloc peak at most 100n^2 + 8192 bytes,
n = 1..8; an upper bound only). V1 (validator) compares with the known determinant for n = 0..8.

## 2. Gaussian elimination mod P (`gaussian.py`)

**2.1 Facts about det over a field F.**
*Sign lemma.* (i) If τ swaps two adjacent positions i, i + 1, then inv(s∘τ) = inv(s) ± 1: only the pair (i, i + 1)
changes its status. (ii) A transposition of positions a < b is a product of 2(b − a) − 1 adjacent transpositions
(move the entry at a to position b in b − a adjacent steps, then the former entry at b back to a in b − a − 1 steps),
an odd number, so sgn(s∘τ) = −sgn(s) for every transposition τ. (iii) inv(s^(−1)) = inv(s): (i, i') with i < i' and
s(i) > s(i') corresponds to the pair (s(i'), s(i)) of positions of s^(−1), which is inverted there, and this is a
bijection of the inverted pairs.
(a) Swapping two rows negates det: s ↦ s∘τ (τ the transposition of the two rows) is a bijection of the
permutations that changes every sign (sign lemma (ii)) and permutes the products.
(b) Adding f times row c to row r ≠ c leaves det unchanged: det is linear in row r, so the new determinant is
det(A) + f·det(A'), where A' has row r replaced by row c; A' has two equal rows, and pairing s with s∘(r c) pairs
terms with equal products and opposite signs (a fixed-point-free pairing), so det(A') = 0.
(c) If A is upper triangular, a product Π_i A[i][s(i)] can be non-zero only if s(i) ≥ i for every i, which forces s
to be the identity; so det(A) = Π_i A[i][i].
(d) If columns 0..c of A are zero in rows c, c + 1, …, n − 1, then det(A) = 0. Those c + 1 columns are non-zero only
in the first c coordinates, so some non-trivial combination Σ_{j ≤ c} λ_j·(column j) is the zero vector. Now
det(A) = det(A^T), because s ↦ s^(−1) is a bijection that preserves the sign (sign lemma (iii)) and the product. In A^T, rows 0..c
are dependent; pick j with λ_j ≠ 0 and replace row j of A^T by Σ_{i ≤ c} λ_i·(row i). By linearity in row j and
by (b) this multiplies the determinant by λ_j, and the new row j is zero, so the new determinant is 0. Hence
λ_j·det(A^T) = 0 and det(A) = 0.

**2.2 Correctness.** Invariant before column c: M arises from A by row swaps and row additions, the entries of
columns 0..c − 1 below the diagonal are 0, and `det` ≡ (−1)^(number of swaps) · Π_{c' < c} M[c'][c'] (mod P). In
step c the code searches a row piv ≥ c with M[piv][c] ≠ 0.
- If there is none, columns 0..c are zero in rows c..n − 1, so M is singular by 2.1(d), and so is A (by (a) and (b)
  det(A) = ±det(M) = 0): returning 0 is correct.
- Otherwise it swaps rows c and piv if needed (negating `det`, 2.1(a)), multiplies `det` by the pivot, and inverts
  the pivot as x^(P−2), which is x^(−1) by Fermat's little theorem because P is prime and x ≢ 0. For every row r > c
  it sets row r to row r − f·row c with f = M[r][c]·x^(−1), which makes M[r][c] = 0 and leaves det unchanged
  (2.1(b)). The code rebuilds the row as `row[:c] + [...]`; the kept entries in columns < c are 0 in both rows
  (invariant), so this is the full row operation.
After column n − 1, M is upper triangular, det(M) = Π_c M[c][c] by 2.1(c), and det(A) = (−1)^(swaps)·det(M) ≡ `det`.
The returned `det % P` is det(A) mod P in [0, P).

**2.3 Exact counts.** On non-singular input all n columns are processed. Column c, with k = n − c, has k − 1 rows
below; each costs one multiplication for f and k multiply-subtracts `(x − f*y) % P` (columns c..n − 1). Each column
also makes one multiplication of `det` and one inversion. Hence:
- multiply-subtracts: Σ_{k=1..n} (k − 1)k = (n^3 − n)/3, about n^3/3;
- multiplications in all: (n^3 − n)/3 + n(n − 1)/2 + n = n(n + 1)(2n + 1)/6;
- inversions: n (each a fixed number of multiplications, section 0).
So Gaussian elimination makes Θ(n^3) field operations on non-singular input. On singular input it stops at the
first column without a pivot and makes at most as many: O(n^3) always. The other work (pivot search, the list
copies `row[:c] + [...]`, n − c entries kept per row) is O(n) per row update, also O(n^3).

**2.4 Space.** The working copy M has n^2 entries; `tail` and each new row are lists of at most n entries. Θ(n^2).

**Checks.** `tests/test_proofs_determinant.py`: class `Prime` (P is prime); class `Correctness` (as in section 1);
class `GaussianCounts` (on seeded non-singular matrices n = 0..40, with and without zero entries: exactly
n(n + 1)(2n + 1)/6 multiplications, (n^3 − n)/3 subtractions and n inversions; on singular matrices n = 2..15 with two
proportional rows: answer 0, at most (n^3 − n)/3 subtractions and fewer than n inversions); class `WorkingMemory`
(tracemalloc peak at most 100n^2 + 8192 bytes for n = 1, 8, …, 57).

## 3. The pair

Θ(n!) against Θ(n^3) field operations: n!/n^3 → ∞, and n! grows faster than every polynomial, so the pair improves
a super-polynomial cost to a polynomial one (tag T2). The expansion never uses 2.1(b); elimination is built on it.
The permanent has no such invariance (`pairs/permanent-naive-vs-ryser/PROOFS.md`, section 5.5).

## 4. Facts used by the harness

**4.1 Known determinant.** `generate` builds A from L (unit lower triangular), U (upper triangular) and a
permutation: row i of A is row perm[i] of L·U. Row i of L·U is row i of U plus Σ_{k<i} L[i][k]·(row k of U).
Performing these row additions for i = n − 1, …, 1 (each uses rows k < i, still rows of U) turns U into L·U, so
det(L·U) = det(U) = Π_i U[i][i] by 2.1(b) and (c). Permuting the rows multiplies det by the sign of the permutation:
a permutation is a product of transpositions (a cycle of length ℓ is a product of ℓ − 1 of them), each negating det
by 2.1(a), so det(A) = (−1)^t·det(L·U) for any t transpositions whose product is the permutation; t is even iff the
permutation has an even number of even-length cycles (a cycle of length ℓ uses ℓ − 1), which is what `_sign`
computes. So
det(A) = sign(perm)·Π_i U[i][i] mod P, the value stored in `_KNOWN`; a zero on U's diagonal gives a singular matrix.

**4.2 Random matrices.** A uniformly random n × n matrix over GF(q) is non-singular with probability
Π_{i=1..n} (1 − q^(−i)) ≥ 1 − Σ_{i ≥ 1} q^(−i) = 1 − 1/(q − 1): the rows are independent, and given i independent
rows, the next row avoids their span (q^i vectors) with probability 1 − q^(i−n). For q = P this is 1 − O(1/P), the
"non-singular with probability about 1 − 1/p" of the timing family.

**Checks.** `tests/test_proofs_determinant.py`, class `HarnessOracle`: the stored determinant equals the Leibniz
formula on 56 generated instances with n = 0..6; the count Π_{i<n} (q^n − q^i) of invertible matrices over GF(q) for
q = 2, 3 (n ≤ 3) and q = 5 (n ≤ 2), by enumeration.
