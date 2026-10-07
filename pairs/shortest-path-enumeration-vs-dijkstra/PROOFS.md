# Proofs: single-pair shortest path, simple-path enumeration vs Dijkstra

This file proves the claims of this entry about its two implementations: correctness, the exact search-tree sizes
and the Θ(n·(n − 2)!) bound of the enumeration (on every n × n input), Dijkstra's Θ(n²) bound and the exact set
of weights it reads, the lower bound showing that Θ(n²) is optimal for weight-matrix input, and the space bounds.
Each section names its deterministic check. A check covers only its stated range; the proofs cover every input of
the problem. The V2 timing fits in `entry.json` are measurements, not proofs; the Fibonacci-heap and later bounds
are background.

The input is an n × n matrix W with entries in [0, ∞] (W[u][v] is the weight of the arc u → v; an absent arc has
weight `math.inf`; the diagonal is not used), s = 0, t = n − 1. Every input is thus a complete digraph with some arcs
of weight ∞. A path is simple; δ(v) is the minimum weight of an s–v path (∞ if every s–v path uses an absent arc).
All arguments below hold with ∞ entries: ∞ + x = ∞, and a comparison with ∞ is false unless the other side is
finite and smaller.

## 1. Enumeration: correctness

With non-negative weights, deleting a closed sub-walk from an s–t walk does not increase its weight, so the minimum
over all s–t walks is attained by a simple path, and the problem asks for the minimum over simple s–t paths.
`dfs(u, cost)` is called exactly once for every simple path from s that meets t at most at its end, with `cost` its
weight: it extends the current path by every unvisited vertex v (marking v, recursing, unmarking), and it stops at
t. So every simple s–t path is reached once, at a call with u = t, where `best = min(best, cost)`; paths through
absent arcs have cost ∞, so the result is δ(t), and ∞ if t is unreachable. For n = 1, s = t and the answer is 0. ∎

## 2. Enumeration: exact sizes, Θ(n·(n − 2)!) time on every input

Let n ≥ 2 and P = Σ_{k=0..n−2} (n − 2)!/(n − 2 − k)! = Σ_{j=0..n−2} (n − 2)!/j!, the number of sequences of distinct
vertices chosen from the n − 2 vertices other than s and t.

**Statement.** On every n × n input (the control flow of `dfs` never looks at the weights), `shortest_path_enumerate`
makes exactly 2P calls of `dfs`: P calls at a vertex other than t, each of which scans all n vertices, and P calls at
t, which scan none; it adds exactly 2P − 1 weights. There are exactly P simple s–t paths in the complete digraph, and
P = ⌊e·(n − 2)!⌋ for n ≥ 3 (P = 1 for n = 2). So the time is Θ(n·P) = Θ(n·(n − 2)!). Since
(m/e)^m ≤ m! ≤ m^m, this is 2^Θ(n log n): super-exponential in n, and 2^Θ(√N·log N) in the number N = n² of matrix
entries.

*Proof.* A call at a vertex other than t corresponds to a simple path s, x_1, …, x_k (0 ≤ k ≤ n − 2) avoiding t: P
of them. Each scans v = 0..n − 1 and has exactly one child at t (t is never visited before), so there are P calls at
t, which are exactly the simple s–t paths. Every call except the root adds one weight (`cost + W[u][v]`):
2P − 1 additions. For m = n − 2 ≥ 1, e·m! − P = Σ_{j>m} m!/j! lies strictly between 0 and
Σ_{i≥1} (m + 1)^(−i) = 1/m ≤ 1, so P = ⌊e·m!⌋. Since (n − 2)! ≤ P ≤ e·(n − 2)!, and each call costs O(n) (a
scan) or O(1) (at t), the time is Θ(n·(n − 2)!). ∎

**Check.** `tests/test_proofs_sp.py`, class `EnumerationSizes`: on complete digraphs with n = 2..9, the number of
`dfs` calls (counted with `sys.setprofile`) is 2P and the number of weight reads (counted with a matrix wrapper) is
2P − 1; for n = 2..8 the scan line `if not visited[v]:` (counted per call with `sys.settrace`) runs exactly n times
in each call not at t and 0 times in each call at t; P = ⌊e·(n − 2)!⌋ for n = 3..20.

## 3. Dijkstra: correctness

The implementation keeps `dist` and `done`; in each of n rounds it settles an unsettled vertex u with minimum
`dist[u]` (the first such vertex in index order) and relaxes the arcs from u to unsettled vertices.

**Invariant.** Every `dist[v]` is the weight of some s–v path or ∞, so `dist[v]` ≥ δ(v); and when u is settled,
`dist[u]` = δ(u).

*Proof.* The first part holds because `dist[v]` is only set to `dist[u] + W[u][v]`. Suppose u is the first vertex
settled with `dist[u]` > δ(u); then δ(u) < ∞ and u ≠ s (s is settled first, with 0 = δ(s)). Take a shortest s–u
path and let y be its first vertex not settled when u is chosen, x its predecessor (settled, so
`dist[x]` = δ(x)). When x was settled, the relaxation of x → y gave `dist[y]` ≤ δ(x) + W[x][y] = δ(y) (a prefix of
a shortest path is shortest), and δ(y) ≤ δ(u) because the weights after y are non-negative. So
`dist[y]` ≤ δ(u) < `dist[u]`, contradicting the choice of u. ∎ The function returns `dist[n − 1]` = δ(t).

## 4. Dijkstra: Θ(n²) time and the weights it reads

Each of the n rounds scans all n vertices for the minimum (the generator inside `min`) and all n vertices for the
relaxation: Θ(n) per round, Θ(n²) in total, on every input (there is no early exit).

**Reads.** In the round that settles u, the relaxation reads `row[v]` = W[u][v] exactly for the vertices v not yet
settled (u itself is marked before the loop). So for each unordered pair {u, v} it reads exactly one of W[u][v],
W[v][u], the one leaving the vertex settled first (possibly twice, in the test and in the assignment), and it never
reads the diagonal: exactly n(n − 1)/2 distinct weights.

**Check.** `tests/test_proofs_sp.py`, class `DijkstraReads`: with a matrix wrapper that records every read, on 40
seeded random complete digraphs with n drawn from 1..40, the set of read pairs has n(n − 1)/2 elements and contains, for every
pair, exactly the arc leaving the vertex that the test's own replay of the settling order settles first.

## 5. Θ(n²) is optimal for weight-matrix input

**Model.** An algorithm reads the matrix one entry at a time, and its steps (and output) depend only on n and on
the values it has read; each read is at least one step.

**Claim.** For n ≥ 4, split the vertices other than s, t into U (⌊(n − 2)/2⌋ of them) and X (the rest). Let I_n have
w(s, u) = 1 (u ∈ U), w(u, x) = 2 (u ∈ U, x ∈ X), w(x, t) = 1 (x ∈ X) and every other weight 100. Then every correct
deterministic algorithm reads all |U|·|X| = ⌊(n − 2)²/4⌋ weights w(u, x) on I_n. So does every run of a
zero-error randomized algorithm: fix its random bits; the run is then a deterministic computation that must be
correct on I_n and on the instance I′ below, and the same argument applies. In this model Θ(n²) is therefore
optimal up to a constant factor.

*Proof.* δ(t) = 4 on I_n: any path using a weight-100 arc weighs more than 4, and the only s–t paths using only the
other arcs are s → u → x → t, of weight 4. If an algorithm does not read some w(u, x), the instance I′ with
w(u, x) = 1 gives it the same values, hence the same output; but δ(t) = 3 on I′ (the path s → u → x → t). One of the
two outputs is wrong. |U|·|X| = ⌊(n − 2)/2⌋·⌈(n − 2)/2⌉ = ⌊(n − 2)²/4⌋. ∎ All weights lie in the harness range
[1, 100].

**Check.** `tests/test_proofs_sp.py`, class `LowerBoundInstance`: for n = 4..12, Dijkstra and a Floyd–Warshall
written in the test give 4 on I_n and 3 after lowering any single weight w(u, x) to 1 (the enumeration as well for
n ≤ 8).

## 6. Space

Enumeration: `visited` (n entries) and the recursion, whose depth is the number of vertices on the current path, at
most n: Θ(n). Dijkstra: `dist` and `done` (n entries each); the generator inside `min` holds one pair at a time:
Θ(n). **Check:** `tests/test_proofs_sp.py`, class `Space`: the largest recursion depth of `dfs` (counted with
`sys.setprofile`) is exactly n on complete digraphs with n = 2..9, and the tracemalloc peak of Dijkstra grows by
less than a factor 3 per doubling of n = 50, 100, 200 (Θ(n); the n × n matrix is input).

## 7. Correctness check

**Check.** `tests/test_proofs_sp.py`, class `Correctness`: both implementations equal a Floyd–Warshall written in
the test on 72 seeded complete digraphs (n = 1..8; 37 with weights 0..100, of which 6 contain an off-diagonal 0, and
35 with weights 1..3, many ties), on 48 seeded digraphs with absent arcs (weight `math.inf`, probability 0.3 or 0.6)
and weights 0..5 (n = 1..8, including unreachable t), and, for Dijkstra, on complete digraphs with n = 9..30.
