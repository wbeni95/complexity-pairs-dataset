# Proofs: counting Hamiltonian cycles, enumeration vs inclusion–exclusion vs Held–Karp

This file proves the claims that this entry makes about its problem and its three algorithms (in `entry.json`,
`README.md`, the docstrings of the code and the harness). Sections 1 to 3 prove the exact operation counts, for
every size of their domain, from the code in this folder. Sections 4 to 10 prove the other claims: correctness of
the three algorithms (also with integer arc weights), the undirected convention, space and integer sizes, the
time/memory trade-off, and the facts used by the V1 oracle. Each proof is followed by the deterministic scripts
that check it and the sizes they check it on. A check covers only those sizes; the proofs cover the whole domain.

The statements listed under `background` in `entry.json` (NP-completeness of the Hamiltonian cycle problems, the
history of inclusion–exclusion counting and of the Held–Karp recurrence) are cited, not proved here.

## Counting convention

`harness.py`, class `CountingInt`, with the module tally `_ops = {"truth", "compare", "mul", "add"}`:
`__add__`, `__radd__`, `__sub__`, `__rsub__` and `__neg__` add 1 to `_ops["add"]`; `__mul__` and `__rmul__` add 1
to `_ops["mul"]` (all through `_arith`, which returns a new `CountingInt`); the six comparison methods add 1 to
`_ops["compare"]`; `__bool__` adds 1 to `_ops["truth"]`. `generate_scaling(n, rng)` returns the complete digraph
K_n as an n × n matrix of `CountingInt` entries (1 off the diagonal, 0 on it) and resets the tally
(`reset_counter`); `reported_cost(output)` returns the sum of the four tallies.

An arithmetic operation with at least one `CountingInt` operand counts exactly 1 (if only the right operand is one,
the int method returns `NotImplemented` and Python calls the reflected method) and returns a `CountingInt`; an
operation on two plain ints counts nothing. Index arithmetic, `mask` bookkeeping, `i != j` on indices and
`count += 1` are on plain ints. "Every input" below means every n × n matrix of `CountingInt` entries; no
implementation branches on an entry except the enumeration's arc tests.

## 1. Enumeration: n! arc tests on K_n; (n − 1)! orders on every input

**Statement.** For every n ≥ 2, `count_hamiltonian_cycles_enumeration` generates all (n − 1)! orders on every input,
and on K_n it makes exactly n! counted operations, all of them truth tests (arc tests). For n ≤ 1 it makes none.

**Proof.** n ≤ 1 returns 0 before any test. For n ≥ 2 the loop runs over all (n − 1)! permutations of 1..n − 1
produced by `permutations`, on every input; only the inner `break` depends on the input. In an order, the test
`not adj[prev][v]` calls `CountingInt.__bool__` once (1 truth test). On K_n, prev ≠ v always (prev is 0 or the
previous, different element of the permutation), so the entry is 1, no test fails, and the n − 1 tests all run.
Then `complete and adj[prev][0]` evaluates to the entry `adj[prev][0]` (complete is the plain `True`), whose truth
the `if` tests: 1 more truth test. No other operation touches an entry. Total n · (n − 1)! = n!.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Ham enumeration n!": n = 0..10
(includes the V2 sizes n = 5..10; n = 0, 1 reported as outside the domain with count 0).
`experiments/2026-10-07_count_proof_checks.py`, group `subsets`, line "Hamiltonian enumeration: (n-1)! orders on
random digraphs, truth tests only": n = 2..8, 3 seeded random digraphs per n.

## 2. Inclusion–exclusion: n(n − 1)(n + 2)2^(n−3) multiplications, that plus 2^(n−1) − 1 additions

**Statement.** For every n ≥ 1 and every input, `count_hamiltonian_cycles_inclusion_exclusion` makes exactly
n(n − 1)(n + 2)2^(n−3) counted multiplications and n(n − 1)(n + 2)2^(n−3) + 2^(n−1) − 1 counted additions and
subtractions, in total n(n − 1)(n + 2)2^(n−2) + 2^(n−1) − 1 operations, and no truth test or comparison. For a set
T of size t the walk DP makes n steps of t(t − 1) products and t(t − 1) additions; the signed accumulation of
T = {0} adds a plain 0 and is not counted. It also makes n·t² plain index comparisons `i != j` per set (caveat).

**Proof.** n = 1 returns 0 at once, and the formula gives 0 + 1 − 1 = 0. Let n ≥ 2. The outer loop visits the
2^(n−1) sets T = {0} ∪ S, S ⊆ {1..n − 1}, starting with `mask = 0`, that is T = {0}. Let t = |T|. `walks` starts
as the plain list [1, 0, …, 0]. In each of the n steps, for each j the inner loop tests `i != j` (plain) for all t
values of i, t² per step, and for the t − 1 values i ≠ j evaluates `acc = acc + walks[i] * adj[...]`: the product
has the `CountingInt` factor `adj[...]`, so it counts 1 multiplication (also when `walks[i]` is a plain int) and
returns a `CountingInt`, and the addition then counts 1 (also when `acc` is the plain 0). So each step makes
t(t − 1) of each, whatever the values.

After the n steps, `walks[0]` is a `CountingInt` if t ≥ 2 (it is a sum of t − 1 ≥ 1 counted products), and the
plain int 0 if t = 1 (no term). The signed accumulation `total ± walks[0]` therefore counts 1 for every T with
t ≥ 2, that is 2^(n−1) − 1 times, and for T = {0} it computes plain 0 ± plain 0, since T = {0} is processed first,
when `total` is still the plain 0. Nothing else counts.

Summing over S with |S| = s, t = s + 1, m = n − 1:
Σ_s C(m, s)(s + 1)s = Σ_s C(m, s)[s(s − 1) + 2s] = m(m − 1)2^(m−2) + 2m·2^(m−1) = m(m + 3)2^(m−2)
= (n − 1)(n + 2)2^(n−3). Times n steps: n(n − 1)(n + 2)2^(n−3) multiplications and as many DP additions; adding
the 2^(n−1) − 1 accumulations gives the statement. The index comparisons are n·t² per set.

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Ham IE n(n-1)(n+2)2^(n-2)+2^(n-1)-1":
n = 0..13 (includes the V2 sizes n = 6..13; n = 0 reported as outside the domain); line "Ham IE per kind: mul
n(n-1)(n+2)2^(n-3), add mul+2^(n-1)-1": n = 2..12 (truth tests and comparisons 0); group `extra`, line "Ham IE and
HK counts on random 0/1 matrices (random diagonal too)": n = 2..9, 3 matrices per n; line "Ham IE index
comparisons n t^2 per set of size t (summed)": n = 2..9.

## 3. Held–Karp counting: (n − 1)(n − 2)2^(n−3) + (n − 1) multiplications and as many additions

**Statement.** For every n ≥ 1 and every input, `count_hamiltonian_cycles_held_karp` makes exactly
(n − 1)(n − 2)2^(n−3) + (n − 1) counted multiplications and as many counted additions, in total
(n − 1)(n − 2)2^(n−2) + 2(n − 1) operations, and no truth test or comparison: a set of size s ≥ 2 costs s(s − 1)
products, and the closing loop n − 1. Its inner loop makes (n − 1)²(2^(n−2) − 1) membership tests
`(prev >> a) & 1` on plain ints (caveat).

**Proof.** n = 1 returns 0 at once, and the formula gives 0. Let n ≥ 2 and m = n − 1. The base loop only stores
entries. The main loop skips the empty set (it starts at 1) and the singletons, so it handles every mask with
s ≥ 2 bits. For each of its s bits b it sets `prev = mask ^ (1 << b)` (s − 1 bits) and, for the m values of a, tests
`(prev >> a) & 1` (plain); for the s − 1 values a in `prev` it evaluates `acc = acc + paths[prev][a] * adj[a + 1][b + 1]`,
one counted product (the factor `adj[...]` is a `CountingInt`) and one counted addition (also when `acc` is the
plain 0). So a mask costs s(s − 1) of each kind, and the closing loop `total = total + paths[full][b] * adj[b + 1][0]`
m of each. Total per kind Σ_{s≥2} C(m, s)s(s − 1) + m = m(m − 1)2^(m−2) + m = (n − 1)(n − 2)2^(n−3) + (n − 1).
The membership tests number m per pair (mask, b), and there are Σ_{s≥2} C(m, s)s = m·2^(m−1) − m such pairs:
m²(2^(m−1) − 1) = (n − 1)²(2^(n−2) − 1).

**Check.** `experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Ham Held-Karp
(n-1)(n-2)2^(n-2)+2(n-1)": n = 0..16 (includes the V2 sizes n = 8..16; n = 0 reported as outside the domain); line
"Ham HK per kind: mul = add = (n-1)(n-2)2^(n-3)+(n-1)": n = 2..14; group `extra`, line "Ham IE and HK counts on
random 0/1 matrices (random diagonal too)": n = 2..9, 3 matrices per n; line "Ham HK membership tests
(n-1)^2(2^(n-2)-1) (uncounted plain-int work)": n = 2..10.

## 4. Correctness of the enumeration

A directed Hamiltonian cycle on n ≥ 2 vertices passes through vertex 0, so it has exactly one rotation
0 → v_1 → … → v_{n−1} → 0, and (v_1, …, v_{n−1}) is an order of {1, …, n − 1}. Conversely an order is such a cycle
iff its n arcs exist. The function enumerates the (n − 1)! orders (`itertools.permutations` yields each once: its
documented behaviour, listed in `background`) and counts those whose n arcs all have non-zero
entries; every tested arc joins two different vertices (consecutive elements of the order, or the last element and
0), so the diagonal is never read. For n = 2 the single order (1) is counted iff both arcs exist, the convention;
n ≤ 1 returns 0.

## 5. Correctness of inclusion–exclusion

**5.1 Walks.** Let U be the set of closed walks w_0 = 0, w_1, …, w_n = 0 of length n in which every step joins two
different vertices along an arc. Such a walk is a Hamiltonian cycle written from 0 iff w_0, …, w_{n−1} are pairwise
distinct, i.e. iff they cover all n vertices; each directed Hamiltonian cycle arises from exactly one walk (its
rotation from 0). For v ≠ 0 let B_v be the walks of U that avoid v.

**5.2 Inclusion–exclusion.** The Hamiltonian walks are those in no B_v, so their number is
Σ_{X ⊆ V − {0}} (−1)^|X| |∩_{v ∈ X} B_v| (the standard sieve: a walk avoiding exactly the set Y of vertices is
counted Σ_{X ⊆ Y} (−1)^|X| = [Y = ∅] times). The intersection is the set of walks inside T = V − X, so the count is
Σ_{T ∋ 0} (−1)^(n−|T|) W(T). For each T the code keeps `walks[i]` = the number of walks of the current length from 0
to `allowed[i]` inside T, starting with the walk of length 0 at vertex 0, and one step sets
walks'[j] = Σ_{i ≠ j} walks[i]·adj[allowed[i]][allowed[j]] (the condition i ≠ j excludes the diagonal). After n steps
`walks[0]` = W(T). The signed sum is accumulated with sign + iff n − t is even. For n = 2 the formula gives
W({0, 1}) − W({0}) = A[0][1]A[1][0] − 0.

**5.3 Integer weights.** If the entries are arbitrary integers, the same computation counts every walk with weight
Π (entries of its arcs), and the sieve of 5.2 cancels each non-Hamiltonian walk with its weight, so the result is
Σ over Hamiltonian cycles of the product of their arc entries. The Held–Karp DP (section 6) computes the same
weighted sum. The enumeration tests entries for non-zero only, so it counts the cycles whose arcs are all
non-zero. This is why the inputs are restricted to 0/1 entries.

## 6. Correctness of the Held–Karp counting DP

paths[S][v] (S a non-empty subset of {1, …, n − 1}, v ∈ S) is the number of directed paths from 0 that visit
exactly {0} ∪ S and end at v. For |S| = 1 this is A[0][v]. For |S| ≥ 2 a path ends with a unique last arc u → v
(u ∈ S − {v}), preceded by a path over S − {v} ending at u, so paths[S][v] = Σ_{u ∈ S − {v}} paths[S − {v}][u]·A[u][v]
(induction on |S|; the code processes masks in increasing order, so S − {v} < S is final). Closing every path over
all of {1, …, n − 1} with the arc back to 0 gives each directed Hamiltonian cycle once (its rotation from 0). No
diagonal entry is read (u ≠ v, and the base and closing arcs join 0 and v ≠ 0). n ≤ 1 returns 0; for n = 2,
paths[{1}][1]·A[1][0] = A[0][1]A[1][0].

**Checks for sections 4–6.** `tests/test_proofs_hamiltonian.py`, class `Correctness`: the three implementations equal
an independent count over the successor permutations that form one n-cycle, on every digraph with n ≤ 4 (random
diagonal bits) and on 30 seeded digraphs with n = 5..7; with integer entries 0..3 (n = 2..6, 30 matrices) the two
DPs equal the arc-weighted sum and the enumeration the number of cycles with non-zero arcs.
`tests/test_entries_2026_10_06f_hamiltonian.py` (conventions, diagonal, agreement with the oracle) and the V1
battery.

## 7. Undirected graphs

For a symmetric matrix with n ≥ 3, every undirected Hamiltonian cycle gives exactly two directed ones (its two
orientations, which differ because n ≥ 3), and every directed Hamiltonian cycle of a symmetric digraph comes from
one undirected cycle. So the count is twice the number of undirected Hamiltonian cycles, in particular even.

**Check.** `tests/test_proofs_hamiltonian.py`, class `Undirected` (30 seeded graphs with n = 3..7: both DPs return
twice the number of undirected cycles counted by enumeration).

## 8. Space and integer sizes

- *Enumeration:* the permutation generator (O(n) words under the machine-model assumption, Lemma 0.1 of
  `pairs/permanent-naive-vs-ryser/PROOFS.md`), the current order and a few counters: Θ(n).
- *Inclusion–exclusion:* `allowed`, `walks` and `nxt` hold at most n entries each (at most 2n walk counts at a time)
  besides the input: Θ(n) numbers.
- *Held–Karp:* `paths` has 2^(n−1) rows of n − 1 entries, (n − 1)·2^(n−1) numbers (4608 at n = 10, 9 961 472 at
  n = 20): Θ(n 2^n).
- *Integer sizes (0/1 entries):* the answer is at most (n − 1)! (orders of n − 1 vertices). A closed walk of length n
  inside T has at most t − 1 choices per step, so W(T) and every partial sum `acc` of a walk count are at most
  (n − 1)^n, and |`total`| ≤ 2^(n−1)(n − 1)^n. paths[S][v] ≤ (|S| − 1)! ≤ (n − 2)!. All of these have O(n log n)
  bits, so unit-cost arithmetic hides a polynomial factor only.

**Checks.** `tests/test_proofs_hamiltonian.py`: class `IntegerSizes` (the largest `acc` and `total` read from the
running code on the complete digraph, which is entrywise the largest 0/1 input, n = 2..8, within the bounds above;
the two table sizes quoted in the notes); class `WorkingMemory` (Held–Karp's tracemalloc peak between 8 and 200
bytes per table entry for n = 8..14; inclusion–exclusion's peak at most 4096 + 256n bytes for n = 4..10, no growth
with 2^n).

## 9. The trade-off between the two DPs

By sections 2 and 3, inclusion–exclusion makes n(n − 1)(n + 2)·2^(n−2) + 2^(n−1) − 1 operations and Held–Karp
(n − 1)(n − 2)·2^(n−2) + 2(n − 1). The ratio tends to n(n + 2)/(n − 2) = Θ(n): inclusion–exclusion is slower by a
factor Θ(n) and stores Θ(n) numbers instead of Θ(n 2^n) (section 8). Both are exponential (each count is at least
2^(n−2) for n ≥ 3), and the enumeration's n! on the complete digraph is super-exponential: n!/(n^3 2^n) → ∞. This is
the factorial-to-2^n·poly(n) improvement of the T8 tag. A graph is Hamiltonian iff its count is positive, so every
counting algorithm also decides Hamiltonicity.

## 10. Facts used by the V1 oracle (`harness.py`)

**10.1 Closed forms.** `closed_form` applies these rules (each is correct on its own, so the order does not matter):
- *Complete digraph:* every order of {1, …, n − 1} is a cycle: (n − 1)!.
- *Complete digraph minus one arc u → v:* the cycles through the arc u → v are (n − 2)! (glue u and v into one
  block and order the n − 1 blocks cyclically), so (n − 1)! − (n − 2)! remain.
- *Not strongly connected:* a Hamiltonian cycle would make every vertex reachable from every other: 0.
- *Strongly connected with every out-degree 1:* the out-arcs define a successor function s, and the vertices reachable
  from 0 are its orbit; strong connectivity makes the orbit all of V, so s is one n-cycle, and it is the only
  Hamiltonian cycle (a Hamiltonian cycle uses one out-arc of every vertex): 1. The same with in-degrees and the
  predecessor function.
- *Undirected n-cycle* (symmetric, connected, every degree 2): exactly one undirected Hamiltonian cycle, so 2 by
  section 7.
- *Connected bipartite graph with sides of different sizes:* a Hamiltonian cycle alternates between the sides, so the
  sides must have equal size: 0.
- *K_{m,m}* (symmetric, bipartite with equal sides m and m^2 edges, i.e. all pairs between the sides): fix vertex 0
  on its side; a cycle from 0 alternates sides, so it is an order of the m vertices of the other side (m! choices)
  interleaved with an order of the other m − 1 vertices of 0's side ((m − 1)! choices): m!(m − 1)!.

**10.2 Depth-first count.** `dfs_count` pushes one stack entry per simple path from 0 along arcs (loops are excluded
from the successor lists) and counts the paths through all n vertices whose last vertex has an arc back to 0: each
Hamiltonian cycle once. The number of nodes is the number of simple paths from 0, at most that of the complete
digraph, Σ_{j=0..n−1} (n − 1)!/(n − 1 − j)! = Σ_{i=0..n−1} (n − 1)!/i!, which is 986 410 for n = 10; for n ≤ 10 the
oracle runs without a budget, so it always finishes.

**10.3 Necessary conditions.** A directed Hamiltonian cycle is determined by its successor function, which picks one
out-neighbour of every vertex, so the count is at most the product of the out-degrees (and, with predecessors, of
the in-degrees). For a symmetric matrix with n ≥ 3 the count is even (section 7).

**Checks.** `tests/test_proofs_hamiltonian.py`, class `OracleFacts`: the closed forms against the Held–Karp count and
`closed_form` (n = 3..9, m = 2..4); the node bound (the complete digraph needs exactly the bound for n = 2..8, the
budget trick shows the count finishes within it on 28 seeded digraphs, and the bound is 986 410 at n = 10); the
necessary conditions on 36 seeded digraphs and 36 undirected graphs with n = 3..8.
`experiments/2026-10-06f_entries_hamiltonian.py` §3 compares every closed form with the exhaustive depth-first
count on 39 graphs.
