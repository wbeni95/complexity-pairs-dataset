# Exact iteration count of the entry's Hungarian implementation: row-monotone worst case and rectangular counts

> **Provenance: own extension.** Base: the folklore bound of O(n) iterations per inserted row, hence O(n³) time (O(n²m)
> for rectangular inputs), for this form of the Hungarian method (shortest augmenting paths with potentials, rows
> inserted one at a time). The only source read that states it is the cp-algorithms article "Hungarian algorithm for
> solving the assignment problem", which presents, in C++, the code that the entry's implementation transcribes line by
> line. Edmonds and Karp (1972), of which the abstract and one section were read, state the O(n³) bound for the n × n
> assignment problem, without a per-row or exact iteration count. Lemma 1 proves the bound in exact form. This note
> gives exact values where the base gives an order: row i takes **exactly i** iterations on every matrix with
> non-decreasing rows, so that family attains the exact worst case of the code, with exact counts also for rectangular
> matrices. Details are in [Literature](#literature).

## Setting

The pair [assignment-brute-vs-hungarian](../../pairs/assignment-brute-vs-hungarian/) implements the Hungarian method
as successive shortest augmenting paths with potentials (`implementations/hungarian.py`). For an n × n matrix C the
code keeps row potentials u[1..n], column potentials v[0..n], `match[j]` (the row of column j, 0 if free) and `way[j]`,
with column 0 a sentinel. It inserts rows i = 1, …, n. For row i it sets `match[0] = i`, `j0 = 0`, `minv[·] = ∞`,
`used[·] = False` and repeats the body of `while True` (one **iteration**):

1. mark j0 used; i0 = match[j0];
2. for every unused column j = 1, …, n in increasing order: evaluate `cur = C[i0][j] − u[i0] − v[j]`; if cur < minv[j],
   set minv[j] = cur and way[j] = j0; if minv[j] < delta, set delta = minv[j] and j1 = j;
3. for every column j = 0, …, n: if used, u[match[j]] += delta and v[j] −= delta; otherwise minv[j] −= delta;
4. j0 = j1; stop if column j0 is free.

Then it augments along `way` back to column 0. Rows and columns are 1-based as in the code. The comparisons in step 2
are strict and run over increasing j, so **j1 is the smallest index among the unused columns with minimal minv**.

The **rectangular form** for an m × n matrix with m ≤ n is the same code with rows 1, …, m and columns 1, …, n (the
loops over columns run to n). For m = n it is the entry's code.

Cost measures: the number of iterations, and the number of evaluations of `cur`. Every iteration also runs the loop of
step 3 over n + 1 columns.

## Statements

**Lemma 1 (every input; the base bound in exact form).** In the rectangular form (m ≤ n), the search for row i runs
at most i iterations, and iteration t evaluates `cur` exactly n − t + 1 times. Hence at most m(m + 1)/2 iterations and
at most (n + 1)m(m + 1)/2 − m(m + 1)(m + 2)/6 = m(m + 1)(3n − m + 1)/6 evaluations of `cur` in total; for m = n, at most
n(n + 1)/2 iterations and n(n + 1)(2n + 1)/6 evaluations.

**Theorem 2 (exact count).** Let C be an m × n matrix with m ≤ n and integer (or exact rational) entries whose rows
are non-decreasing: C[x][1] ≤ C[x][2] ≤ … ≤ C[x][n] for every x. Then the search for row i runs **exactly i
iterations**: its first i − 1 iterations select the columns 1, …, i − 1 (in some order), and iteration i selects column
i. After row i the matched columns are exactly {1, …, i}.

**Corollary 3 (exact counts; worst case).** On every such matrix the code runs m(m + 1)/2 iterations and evaluates `cur`
exactly (n + 1)m(m + 1)/2 − m(m + 1)(m + 2)/6 = m(m + 1)(3n − m + 1)/6 times. For square matrices this is n(n + 1)/2
iterations and n(n + 1)(2n + 1)/6 evaluations, with n·n(n + 1)/2 steps of the loop in step 2 and (n + 1)·n(n + 1)/2 of
the loop in step 3. By Lemma 1 these are the maxima over all inputs of the same size: **every matrix with non-decreasing
rows is a worst case of this implementation** in both cost measures. The entry's timing family `generate_scaling`,
C[i][j] = 1000·j + r(i, j) with 0-based column index j and r(i, j) ∈ {0, …, 999}, has strictly increasing rows, so it
attains the exact worst case; for the validator's six
instances (n, iterations, evaluations) = (30, 465, 9455), (50, 1275, 42925), (75, 2850, 143450), (100, 5050, 338350),
(150, 11325, 1136275), (200, 20100, 2686700).

**Proposition 4 (rectangular inputs need only the first m columns).** If m ≤ n and the rows are non-decreasing, some
optimal assignment of the m rows to distinct columns uses only the columns 1, …, m. So the entry's square code on the
m × m submatrix of the first m columns returns the optimum (Proposition 6) with exactly m(m + 1)(2m + 1)/6 evaluations of
`cur`, while the rectangular form on the whole matrix makes exactly m(m + 1)(3n − m + 1)/6: Θ(m³) against Θ(m²n). For
example (10, 1000): 385 against 54 835; (30, 300): 9455 against 135 005; (40, 41): 22 140 against 22 960.

**Proposition 5 (no speed-up for square row-monotone inputs).** For an n × n integer matrix C and an integer
M > max C − min C, let C′[x][y] = C[x][y] + M·y for the columns y = 1, …, n. Then C′ has strictly increasing rows, and
every permutation π has cost′(π) = cost(π) + M·n(n + 1)/2. So C and C′ have the same optimal permutations, C′ is computed
with O(n²) unit-cost operations (max C − min C and n² additions), and the entry's code runs its exact worst case on C′
(Theorem 2). Hence any algorithm for square inputs with non-decreasing rows solves every square input with O(n²)
additional unit-cost operations (build C′, subtract M·n(n + 1)/2 from the optimum): a reduction. (With 0-based column
indices y = 0, …, n − 1 the shift is M·n(n − 1)/2.)

**Proposition 6 (the square code is correct).** On every n × n integer (or exact rational) matrix the entry's code
returns
min_π Σ_x C[x][π(x)].

**Remark (the hypothesis matters).** For C = ((0, 1), (1, 0)) the search for row 2 runs one iteration, not two, so
Theorem 2 fails without non-decreasing rows.

## Proof

Fix the row i being inserted. Let u⁰, v⁰ be the potentials at the start of its search, and for a row x ≤ i and a
column y ≥ 1 let red(x, y) = C[x][y] − u⁰_x − v⁰_y. Let x_0 = i and, for a matched column c, x_c = match[c]. The digraph
𝒟 has the columns 0, …, n as vertices and an arc c → y of length red(x_c, y) for every column y ≥ 1, y ≠ c, from c = 0 and
from every matched column c. Free columns have no outgoing arcs, and **no arc enters column 0**. d(·) denotes the
distance from column 0 in 𝒟.

**Invariants** (before the search for row i): (I1) red(x, y) ≥ 0 for every row x < i and every column y ≥ 1;
(I2) red(x_c, c) = 0 for every matched column c; (I3) v⁰_y = 0 for every free column y; and u⁰_i = 0. They hold before
row 1, when all potentials are 0 and no column is matched.

### Lemma 1

A free column that is selected ends the loop before it is marked used (step 4). So the columns marked used in
iterations 2, …, t are the columns selected in iterations 1, …, t − 1; they are distinct (j1 is chosen among the unused
columns) and matched. Every search ends with an augmentation that keeps the matched columns matched and matches the
final column, so before row i exactly i − 1 columns are matched. Hence t − 1 ≤ i − 1. In iteration t the unused columns
among 1, …, n number n − (t − 1) ≥ n − i + 1 ≥ 1, and step 2 evaluates `cur` once for each; after iteration 1 every minv
is finite, so j1 always exists. Summing n − t + 1 over t ≤ i and i ≤ m gives the totals:
Σ_{t=1}^{i} (n − t + 1) = i(n + 1) − i(i + 1)/2, and Σ_{i=1}^{m} of this is (n + 1)m(m + 1)/2 − m(m + 1)(m + 2)/6. ∎

### Lemma D (the search is Dijkstra's algorithm on 𝒟; the invariants are preserved)

(a) Let Δ_t be the sum of the deltas of iterations 1, …, t − 1, and λ(c) the value of Δ when column c was marked used
(λ(0) = 0). At the start of iteration t, for every used column c, u_{x_c} = u⁰_{x_c} + Δ_t − λ(c) and
v_c = v⁰_c − (Δ_t − λ(c)); for every unused column j ≥ 1, minv[j] + Δ_t = min over used c of λ(c) + red(x_c, j), and
way[j] is a minimiser. The column selected in iteration t is the unused column with the least *tentative label*
minv[j] + Δ_t (the smallest index among ties), and its label becomes its λ. This is Dijkstra's algorithm from column 0
on 𝒟, and every column c ≠ 0 that is marked used has λ(c) = d(c).

(b) After the last iteration and the augmentation, (I1)–(I3) hold for the rows 1, …, i and the new matching, every arc
way[j] → j of the search tree has red′ = 0 for the new potentials, and the final column j* has v = 0.

*Proof.* (a) Induction over iterations. In iteration t the newly used column j0 has λ(j0) = Δ_t. Its row x_{j0} and the
unused columns j still have their starting potentials (potentials change only for used columns and their rows), so
`cur` = red(x_{j0}, j), and the update of minv[j] restores the statement with j0 added. Step 3 shifts the used potentials
and the unused minv by delta, which is the statement for Δ_{t+1} = Δ_t + delta, and the selected j1 has label
minv[j1] + Δ_t = Δ_{t+1}. So each iteration selects an unused column of least tentative label and relaxes the arcs out of
the newly used column: Dijkstra's algorithm. The arcs out of matched columns have length ≥ 0 by (I1). The arcs out of
column 0 may be negative, but no arc enters column 0, so every path from 0 starts with exactly one arc out of 0; adding a
constant K to those arcs adds K to every distance and to every tentative label of a column ≠ 0, and changes no selection.
With K large enough all lengths are ≥ 0, and the standard facts about Dijkstra's algorithm apply: a column is selected
with label equal to its distance, the labels of the columns selected in iterations 1, 2, … are non-decreasing, and when a
column with label L is selected, every column with distance < L is already used. (The label 0 of column 0 itself may
exceed the first selected label, since the first delta may be negative.)

(b) Let Λ = λ(j*), the label of the final column. The final potentials are u′_{x_c} = u⁰_{x_c} + Λ − λ(c) and
v′_c = v⁰_c − (Λ − λ(c)) for the used columns c; all other potentials are unchanged, in particular v′_{j*} = v⁰_{j*} = 0
by (I3). For a row x ≤ i (call x *reached* if x = x_c for a used c) and a column y ≥ 1, red′(x, y) = C[x][y] − u′_x − v′_y:
- x reached via c, y used: red′ = red(x, y) + λ(c) − λ(y) ≥ 0, since λ(y) = d(y) ≤ d(c) + red(x, y) = λ(c) + red(x, y);
- x reached via c, y unused: red′ = red(x, y) − (Λ − λ(c)) ≥ 0, since y's final tentative label is ≤ λ(c) + red(x, y)
  (c was relaxed) and ≥ Λ (j* had the least label);
- x not reached, y used: red′ = red(x, y) + Λ − λ(y) ≥ red(x, y) ≥ 0 (x < i, (I1), and λ(y) ≤ Λ);
- x not reached, y unused: unchanged.
So (I1) holds for the rows 1, …, i. A tree arc p → j with p = way[j] has λ(j) = λ(p) + red(x_p, j) if j is used, and
Λ = λ(p) + red(x_p, j*) for j = j*, so red′ = 0 in both cases; matched pairs of used columns stay tight (the two shifts
cancel), and the other matched pairs are unchanged. The augmentation along the tree path from column 0 to j* gives each
path column the row of its tree parent, a tight pair; so (I2) holds. A free column was never used (a used real column is
matched), so its v is still 0: (I3). Row i + 1 has never been touched, so u_{i+1} = 0. ∎

*Proof of Proposition 6.* The augmentation of each search walks `way` back to column 0 through columns selected
strictly earlier, so its path p_0 = 0, p_1, …, p_k = j* is simple; it gives column p_{s+1} the old row of p_s, so the
matched columns keep distinct rows and row i is added. After row n the n columns (Lemma 1) therefore hold the n rows
exactly once: the final matching is a permutation π*. (I1) and (I2) hold for all rows with the final potentials u, v. For every permutation π, Σ_x C[x][π(x)] = Σ_x red(x, π(x)) + Σ_x u_x + Σ_y v_y ≥ Σ_x u_x + Σ_y v_y,
with equality for π* by (I2); the code returns the cost of π*. ∎

### Lemma T (tight tree)

Suppose the search for row i selected all i − 1 matched columns and ended at the column j*. Then at the start of the
search for row i + 1, every matched column, j* included, can be reached from j* in 𝒟 by arcs of length 0.

*Proof.* The search tree T (parent of j = way[j]) contains column 0, the i − 1 used columns and j*. Label the tree arc
p → j by the row ρ(j) = old match[p] (ρ(j) = i if p = 0). By Lemma D(b), ρ(j) is tight with j, and also with p if p ≠ 0
(matched pairs of used columns stay tight). The augmentation along the tree path 0 = p_0, p_1, …, p_k = j* sets
new match[p_{s+1}] = old match[p_s]; the other columns keep their rows. Arcs of length 0 at the start of the next search:
a column c off the path keeps its row, which is tight with all tree children of c; a path column p_{s+1} now holds the row
old match[p_s], which is tight with p_s (if s ≥ 1) and with all tree children of p_s. So from p_k one reaches
p_{k−1}, …, p_1 and all children of p_0, …, p_{k−1}, and then all their descendants off the path. j* has no children,
because it was never used. Every column of T other than 0 lies below some p_s with s ≤ k − 1, so it is reached. ∎

### Theorem 2

Induction on i, using Lemma D(b) for (I1)–(I3).

*i = 1.* All potentials are 0, so minv[j] = C[1][j] in iteration 1. Column 1 is the smallest index with the least value
(the row is non-decreasing), so it is selected, it is free, and the search ends after one iteration.

*Step i → i + 1 (i + 1 ≤ m).* The matched columns are 1, …, i; column i was the final column of row i's search, so
v_i = 0 by Lemma D(b), and the free columns i + 1, …, n have v = 0 by (I3).
1. *d(i) ≤ d(f) for every free column f.* Take a shortest path to f; its last arc is c → f with row x = x_c (c is column 0
   or a matched column). Then red(x, i) ≤ red(x, f), because C[x][i] ≤ C[x][f] and v_i = v_f = 0. If c = i, then
   d(i) = d(c) ≤ d(c) + red(x, f), as red(x, f) ≥ 0 by (I1); otherwise d(i) ≤ d(c) + red(x, i) ≤ d(c) + red(x, f). In both
   cases d(i) ≤ d(f).
2. By Lemma T, whose hypothesis is the statement for row i, every matched column c has d(c) ≤ d(i). So every matched
   column has d(c) ≤ L := min over free f of d(f).
3. *All matched columns are selected before any free column.* Let f* be the first free column selected. Its label is
   d(f*) = L: a free f with d(f) < d(f*) would have been selected earlier. Every column with distance < L is used at that
   time (Lemma D(a)). If a matched column c were still unused, then d(c) = L; the first unused column c′ on a shortest
   path from 0 to c has a used predecessor on that path, so its tentative label is d(c′) = L; and c′ is matched (free
   columns have no outgoing arcs, so they occur on a path only at its end). Then c′ ≤ i < i + 1 ≤ f*, and both carry the
   least label L, so the code would select a column of index ≤ c′, not f*: a contradiction.
4. So the first i iterations select the i matched columns. In iteration i + 1 every arc into a free column has been
   relaxed, so the free columns carry their final labels d(f). The argument of step 1 with i + 1 in place of i (column
   i + 1 is free, so it is not inside any path) gives d(i + 1) ≤ d(f) for every free f; column i + 1 has the smallest
   index among them (it exists, as i + 1 ≤ m ≤ n), so it is selected and the loop stops. The search ran i + 1
   iterations, and the augmentation matches column i + 1. ∎

Nothing in Lemmas 1, D, T or in steps 1–4 uses m = n, so the theorem holds for the rectangular form. Exact comparisons
are needed for the tie-breaks: after iteration 1 every minv is an integer (or an exact rational), so all comparisons in
step 2 are exact.

### Corollary 3, Propositions 4 and 5

*Corollary 3.* By Theorem 2, row i's search runs i iterations, and iteration t evaluates `cur` n − t + 1 times
(Lemma 1); sum as in Lemma 1. Lemma 1 shows these are maxima. For the family: 1000(j + 1) + r′ − (1000j + r) ≥ 1000 −
999 > 0, so the rows are strictly increasing.

*Proposition 4.* Take an optimal injection. If it uses a column > m, then at most m − 1 rows use the columns 1, …, m, so
some column c ≤ m is unused; moving a row x from its column y > m to c changes the cost by C[x][c] − C[x][y] ≤ 0 (c < y).
Repeating removes every column > m. The m × m submatrix also has non-decreasing rows, so Corollary 3 gives its count,
and Proposition 6 its correctness. The full count is Θ(m²n) because m(m + 1)(2n + 1)/6 ≤ m(m + 1)(3n − m + 1)/6 ≤
m(m + 1)(3n + 1)/6 for 1 ≤ m ≤ n.

*Proposition 5.* C′[x][y + 1] − C′[x][y] = C[x][y + 1] − C[x][y] + M ≥ M − (max C − min C) > 0. A permutation uses every
column once, so it gains Σ_{y=1}^{n} M·y = M·n(n + 1)/2. Theorem 2 applies to C′. ∎

*Remark.* For C = ((0, 1), (1, 0)): row 1 selects column 1 (one iteration, delta = 0, all potentials stay 0). Row 2's
iteration 1 evaluates cur = 1 for column 1 and cur = 0 for column 2, selects the free column 2 and stops.

## Literature

- **The base, as read.** The cp-algorithms article "Hungarian algorithm for solving the assignment problem"
  (translated from e-maxx.ru; read: the passages on the O(n³) algorithm and the implementation) presents, in C++, the
  code that the entry's implementation transcribes line by line, attributes it to Andrey Lopatin, and states: "Each
  row is processed in time O(n²), since only O(n) potential recalculations could occur (each in time O(n))", with total
  complexity "O(n³) or, if the problem is rectangular, O(n²m)" (its n rows and m columns, n ≤ m). Lemma 1 is that
  bound in exact form. This web article is the only source read that states the per-row bound, so the per-row form is
  cited here as a folklore bound with that article as the evidence.
- **Edmonds and Karp (1972)** (read in an archived copy of the publisher's PDF: the abstract and Section 2.1). The
  abstract states that their algorithm "solves the n X n assignment problem in O(n³) steps"; Theorem 6 reads "If all
  the capacities are integers, then the computation terminates after at most f*(t, s) flow augmentations." Neither part
  gives a per-row or an exact iteration count, or anything on matrices with monotone rows.
- **Credit.** Kuhn (1955), Munkres (1957) and Tomizawa (1971), as in the entry; these papers could not be accessed.
- **What goes beyond the base:** the exact count i for every matrix with non-decreasing rows (Theorem 2), so that this
  family is an exact worst case of the code (Corollary 3); the exact counts for rectangular matrices and the reduction
  to the first m columns (Proposition 4); and Proposition 5. No source stating these was found; the searches covered
  worst-case iteration counts of the Hungarian algorithm and assignment problems with sorted or monotone rows
  (OpenAlex, arXiv, Crossref; titles and abstracts).

## Scope

- The entry's code and its rectangular form (rows ≤ columns), with integer or exact rational entries. Floating-point
  entries with rounding are not covered (ties must be decided exactly).
- The counts are of iterations and of evaluations of `cur`; the loop of step 3 adds n + 1 steps per iteration.
- Proposition 5 is a reduction between inputs; it does not say anything about other algorithms beyond the additive O(n²)
  cost of the shift.

## Verification

```bash
python theorems/hungarian-exact-iteration-count/verify.py           # about 7 s
python theorems/hungarian-exact-iteration-count/verify.py --full    # adds the exhaustive 6 x 6 case over {0, 1}
```

Deterministic (fixed seeds), standard library only, no network; exit code 0 only if every check passes. The square
checks run the **unchanged** entry code: it is given a matrix object that records each row read (one per iteration) and
each entry read (one per evaluation of `cur`), and from this record the script recovers, for every row, the number of
iterations, the columns scanned in each iteration, and the column selected by each iteration except the last. It checks:

- the closed forms of Lemma 1 and Corollary 3 for all 0 ≤ m ≤ n ≤ 60, and the Θ(m²n) sandwich;
- Theorem 2 and Corollary 3 (exactly i iterations, n − t + 1 evaluations in iteration t, selections 1, …, i − 1 in the
  first i − 1 iterations, total n(n + 1)(2n + 1)/6) on every matrix with non-decreasing rows for n = 2, 3, 4 over
  {−1, 0, 1} (36, 1000 and 50 625 matrices), n = 2, 3 over {0, …, 3} (100 and 8000), n = 5 over {0, 1} (7776; with
  `--full` also n = 6, 117 649); on 306 seeded random row-monotone matrices (ties, negative and constant rows, n ≤ 12 and
  n = 50, 80); on 200 seeded row-monotone matrices with exact rational entries (n ≤ 10); on 120 instances of `generate_scaling` (n = 1–40); and the six validator instances above;
- Lemma 1 and Proposition 6 on 900 seeded general matrices (n ≤ 12; the value against the entry harness's subset DP), and
  the Remark's 2 × 2 example;
- Lemma D, Lemma T and the invariants (I1)–(I3) on the internal state of the rectangular form: at every selection the
  label equals the distance in 𝒟 computed by an independent Bellman–Ford, the labels are non-decreasing, the tree arcs are
  tight after the last update, (I1)–(I3) hold before every row and at the end, and Lemma T's reachability holds whenever
  its hypothesis does; on all 12 961 row-monotone matrices of four exhaustive rectangular scopes and on 400 seeded general
  matrices (m ≤ n ≤ 8, entries in −20..20);
- the rectangular form: identical to the entry code for m = n (value, iterations, evaluations, selections; 200 seeded
  matrices); on all 13 417 row-monotone matrices of the scopes (m, n, entries) = (1, 4, 0..2), (2, 3, −1..1),
  (2, 4, 0..2), (3, 4, 0..2), (2, 5, 0..2), (3, 5, 0..2) and on 300 seeded ones: Theorem 2, the exact counts of both runs,
  and Proposition 4 against brute force; and the counts at (10, 1000), (30, 300), (40, 41);
- Proposition 5 on 300 seeded matrices (n ≤ 6): strictly increasing rows, the shift M·n(n + 1)/2 of every permutation's
  cost, equal optimal sets (brute force), and Theorem 2 on the shifted matrix.

## Sources

- H. W. Kuhn (1955). *The Hungarian method for the assignment problem*. Naval Research Logistics Quarterly 2, 83–97.
  [doi:10.1002/nav.3800020109](https://doi.org/10.1002/nav.3800020109). Credit, as in the entry. Not accessible.
- J. Munkres (1957). *Algorithms for the assignment and transportation problems*. Journal of the Society for Industrial
  and Applied Mathematics 5(1), 32–38. [doi:10.1137/0105003](https://doi.org/10.1137/0105003). Credit, as in the
  entry. Not accessible.
- J. Edmonds, R. M. Karp (1972). *Theoretical improvements in algorithmic efficiency for network flow problems*. Journal
  of the ACM 19(2), 248–264. [doi:10.1145/321694.321699](https://doi.org/10.1145/321694.321699). Base (the O(n³) bound
  for the n × n assignment problem, abstract). Abstract and Section 2.1 read.
- N. Tomizawa (1971). *On some techniques useful for solution of transportation network problems*. Networks 1(2),
  173–194. [doi:10.1002/net.3230010206](https://doi.org/10.1002/net.3230010206). Credit, as in the entry. Not
  accessible.
- cp-algorithms contributors. *Hungarian algorithm for solving the assignment problem* (translated from e-maxx.ru).
  [cp-algorithms.com/graph/hungarian-algorithm.html](https://cp-algorithms.com/graph/hungarian-algorithm.html). Base:
  the only source read that states the per-row bound for this implementation. The passages quoted above were read.
