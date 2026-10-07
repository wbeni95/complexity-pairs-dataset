# Proofs: travelling salesman, permutation enumeration vs Held–Karp

This file proves every claim that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): correctness of both, the exact counts and Θ bounds for time and space,
and the factorial-to-exponential improvement (T8). The statement in the entry's `background` field (NP-completeness
of the Hamiltonian circuit problem, and that P vs NP is open) is cited and is not proved; §4 proves the one-line reduction
that turns it into the NP-hardness of this problem, on which the T6 tag rests. Each section ends with the
deterministic checks of its computable facts; a check covers only the inputs it states.

**Notation and cost model.** W is an n × n matrix of non-negative integers (W[i][i] is never used). A *tour* is a
cyclic order of the n cities; its length is the sum of W[u][v] over its n consecutive pairs (u, v), including the
return to the start. For n ≤ 1 the answer is 0 (both implementations return 0). Machine model (elementary
operations): additions, comparisons and list or tuple indexing cost O(1); allocating a list or tuple of length t
costs Θ(t + 1). Machine-model assumption on a library routine (stated in the entry's `background` with its source,
not proved here): `itertools.permutations` on r items behaves as its documented equivalent code (the `indices` and
`cycles` loop), at O(1) per elementary step of that code, and yields each permutation exactly once.

**Lemma 0 (cost of the documented code).** On r items the documented code makes, over the whole enumeration, exactly
Σ_{t=0}^{r−1} r!/t! < e·r! decrements of `cycles[i]`, and its rotations of `indices[i:]` move Σ_{t=0}^{r−1} r!/t!
entries in total; besides, it builds r! tuples of length r. So it does O(r) work per tuple *amortised*, Θ(r·r!) in
total. A single step can take Θ(r²) (the last one decrements and rotates at every position, r + r(r + 1)/2 steps).

*Proof.* Let V_i be the number of times the `for` loop reaches position i. Position r − 1 is reached once per pass
of the `while` loop, r! times (r! − 1 passes that yield and the final one). `cycles[i]` restarts at r − i after it
reaches 0, so position i rolls over (rotates r − i entries and moves on to i − 1) once every r − i visits; hence
V_{i−1} = V_i/(r − i), and V_i = r!/(r − i − 1)!. The decrements number Σ_i V_i, and the rotations move
Σ_i (V_i/(r − i))·(r − i) = Σ_i V_i entries; with t = r − i − 1 both equal Σ_{t=0}^{r−1} r!/t!. ∎

This assumption and Lemma 0 are used only for the upper bound of Theorem 1; building each r-tuple takes Ω(r) anyway.

## 1. Permutation enumeration (`implementations/brute_force.py`)

**Theorem 1.** For n ≥ 2, `tsp_brute` returns the minimum tour length. It evaluates exactly (n − 1)! tours with
n edge weights each ((n − 1)!·(n − 1) additions), so its time is Θ(n·(n − 1)!) = Θ(n!); beyond the input it keeps
the current permutation (n − 1 entries), the generator's state (O(n)) and O(1) numbers: Θ(n) space.

*Proof.* Every tour can be rotated to start at city 0 without changing its length, and then it is 0 followed by a
permutation of 1..n − 1; conversely every such permutation is a tour. The loop visits every permutation once and
computes `W[0][perm[0]] + W[perm[-1]][0]` plus the n − 2 inner edges, i.e. the tour's length with n − 1 additions,
and keeps the minimum. Each iteration costs Θ(n) amortised (the next tuple by Lemma 0, the slice `perm[1:]`, the
n − 2 additions). ∎

**Check.** `tests/test_proofs_tsp.py`, `test_documented_permutations`: the documented code reproduces
`itertools.permutations(range(r))`, its decrements and rotated entries both equal Σ_{t=0}^{r−1} r!/t! < e·r!, and
its longest step is r + r(r + 1)/2, for r = 1..8. `test_enumeration`: the inner addition line runs (n − 1)!·(n − 2) times and
the loop body (n − 1)! times (trace hook), and the result equals the Held–Karp value, for n = 2..8 (seed 1); the
largest permutation tuple has n − 1 entries.

## 2. Held–Karp (`implementations/held_karp.py`)

Let m = n − 1 and represent a set S ⊆ {1, …, n − 1} by the bitmask with bit c − 1 for city c. For j ∈ S, let
opt(S, j) be the least length of a path that starts at city 0, visits exactly the cities of S (each once) and ends at
j.

**Theorem 2.** For n ≥ 2, after the loop `best[S][j − 1]` = opt(S, j) for every non-empty S and j ∈ S, and
`tsp_held_karp` returns min_j (opt(full, j) + W[j][0]), the minimum tour length.

*Proof.* opt({j}, j) = W[0][j], and for |S| ≥ 2, opt(S, j) = min_{k ∈ S∖{j}} (opt(S∖{j}, k) + W[k][j]) (the city before
j on an optimal path is some k, and the rest of the path is a path through S∖{j} ending at k; conversely every such
combination is a valid path). The code initialises `best[{j}][j]` = W[0][j] and processes the non-empty sets S in increasing
numerical order; processing S pushes `best[S][j]` + W[j][k] into `best[S ∪ {k}][k]` for every j ∈ S and k ∉ S.
So `best[T][k]` receives pushes only while T ∖ {k} is processed, and T ∖ {k} < T numerically; a singleton never
receives a push. We show by strong induction along the processing order that `best[S][j]` = opt(S, j) for all
j ∈ S when S is processed. For a singleton this is the initial value. For |S| ≥ 2, every push into `best[S][j]`
came from S ∖ {j}, processed earlier, when its entries were already opt(S ∖ {j}, k) by induction; there was one push
for each k ∈ S ∖ {j}, so `best[S][j]` is the minimum of the recurrence, opt(S, j). No entry changes after its set is
processed. Every entry with j ∈ S is finite, since the matrix is complete and
its entries are integers, so the test `row[j] == math.inf` never skips a member of S. A tour that starts at 0 is a
path through all of {1, …, n − 1} followed by the edge back to 0, which gives the returned value. ∎

**Theorem 3.** For n ≥ 2, on every input, the inner loop over k runs exactly m²·2^(m−1) times, the loop over j runs
m(2^m − 1) times, and the table has 2^m rows of m entries. So the time is Θ(m² 2^m) = Θ(n² 2ⁿ) and the space
Θ(m 2^m) = Θ(n 2ⁿ).

*Proof.* For each of the 2^m − 1 non-empty sets S the loop over j runs m times; exactly the |S| members of S pass
the test (all their entries are finite, Theorem 2), and each runs the loop over k, m iterations. Σ_S |S| = m·2^(m−1)
(each city lies in half of the subsets). The table is allocated as 2^m lists of m entries. With m = n − 1,
m² 2^(m−1) = (n − 1)² 2ⁿ/4. ∎

**Check.** `tests/test_proofs_tsp.py`, `test_held_karp`: the k-loop body runs m²·2^(m−1) times and the j-loop body
m(2^m − 1) times (trace hook), the table at return has 2^m rows of length m, and the result equals the enumeration,
for n = 2..9 (seed 2); on 200 random matrices with n = 2..7 (seed 3) both equal the minimum over all cyclic orders
computed by an independent recursion over Hamiltonian paths. The V2 measurements time the two algorithms against n!
and n² 2ⁿ; measurements, not part of the proofs.

## 3. The improvement (T8)

Both algorithms return the minimum tour length (Theorems 1, 2); the enumeration takes Θ(n!) and Held–Karp
Θ(n² 2ⁿ). Since n! ≥ (n/e)ⁿ (because eⁿ = Σ_k n^k/k! ≥ nⁿ/n!), n!/(n² 2ⁿ) ≥ (n/(2e))ⁿ/n² → ∞: a super-polynomial improvement that is still
exponential (n² 2ⁿ is not polynomial in the input size n²). This is the T8 claim and the README's "factorial →
single exponential".

## 4. NP-hardness (the T6 tag)

**Lemma 4.** Let n ≥ 2. A directed graph G on the vertices 0..n − 1 has a Hamiltonian circuit if and only if the instance
W[u][v] = 1 for the arcs (u, v) of G and W[u][v] = 2 for the other pairs u ≠ v has minimum tour length n.

*Proof.* For n ≥ 2 every tour has n edges of length ≥ 1, so its length is ≥ n, with equality exactly when all its
edges are arcs of G, i.e. when it is a Hamiltonian circuit of G. (For n = 1 both implementations return 0, so the
lemma needs n ≥ 2; NP-hardness is unaffected, since the instances with n = 1 are trivial.) ∎

With the background statement that deciding whether a directed graph has a Hamiltonian circuit is NP-complete
(Karp 1972), Lemma 4 is a polynomial-time reduction (graphs with fewer than two vertices are decided directly), so
computing the minimum tour length is NP-hard, and a polynomial algorithm for it would imply P = NP. This consequence
is ours (Lemma 4); only the NP-completeness and the openness of P vs NP are background.

**Check.** `tests/test_proofs_tsp.py`, `test_reduction`: on all directed graphs with n = 2, 3 and 4 (4, 64 and
4096 graphs), the optimum of the 1/2 instance is n exactly when a Hamiltonian circuit exists (found by brute force over
cyclic orders).

## Claim map

| Claim (location) | Proof |
|---|---|
| enumeration correct, Θ(n!) ((n − 1)! tours, Θ(n) each), Θ(n) space | Theorem 1 |
| Held–Karp correct (`algorithms[1].correctness`) | Theorem 2 |
| Held–Karp Θ(n² 2ⁿ) time, Θ(n 2ⁿ) space | Theorem 3 |
| factorial → single exponential (T8, `relationship`, README, `notes`) | §3 |
| NP-hardness via Hamiltonian circuit (T6, `relationship`, README) | §4 with the background item |
