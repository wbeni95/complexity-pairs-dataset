# Proofs: maximum bipartite matching, Kuhn vs Hopcroft–Karp

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
from the code in this folder: the exact operation counts for every size of their domains (sections 1–4), augmenting
paths and Berge's criterion (section 5), the correctness of Kuhn's algorithm (section 6) and of Hopcroft–Karp with
its O(√V) phase bound (section 7), the time bounds (section 8), the separation over all graphs with V vertices
(section 9), space (section 10), the oracle's error bound (section 11) and the flow remark (section 12). Each proof is
followed by the deterministic scripts or tests that check it and the sizes they check it on. A check covers only
those sizes; the proofs cover the whole domain. `entry.json` sketches the count proofs in the `time_complexity`
fields; sections 1–4 give the steps that the sketches leave out. Section 13 lists the measured statements.

## Counting convention

`harness.py`, class `CountingNeighbours` (a `tuple` subclass): `__getitem__` adds 1 to the module counter `_scans`
and returns the entry; `__iter__` adds 1 for every entry it yields; `len()` is the tuple's own and does not count.
`generate_scaling(n, rng)` requires n = 4k² + k with k ≥ 1 (`adversarial_k`; otherwise it raises `ValueError`),
builds G_k with `adversarial(k)`, wraps every adjacency list in `CountingNeighbours` (the outer tuple `adj` stays a
plain tuple) and sets `_scans = 0`; `reported_cost(output)` returns `_scans`. In `matching_kuhn` an entry is read
only by `v = nbrs[ptr[u]]` (1 count each); `adj[u]` indexes the plain outer tuple, and `len(nbrs)` does not count.
In `matching_hopcroft_karp` the BFS reads entries by `for v in adj[u]`, a loop without `break`, so each run of it
counts deg(u), and the DFS reads them by `v = nbrs[ptr[u]]` (1 count each). Nothing else reads the lists. Below,
"u reads r entries" means r counts.

**The family G_k** (`adversarial(k)`), with a = k²: left vertices 0..2a − 1, each with the list (0, 1, …, a − 1) of
the a gadget right vertices; then, for j = 1, …, k, path j with new right vertices R_1, …, R_j and left vertices
appended in the order L_2, …, L_j, L_1, with the list (R_(i−1), R_i) for L_i (i ≥ 2) and (R_1) for L_1. So
V = 4k² + k and E = 2a² + Σ_j (2j − 1) = 2k⁴ + k². The gadget and the k paths are pairwise disjoint components. Both
algorithms move from a left vertex u only to right vertices in u's list and from a right vertex only to its
partner, so every search stays in the component of its root.

## 1. Kuhn: at most n_left·E ≤ V·E entries on every input

**Statement.** On every input, each search of `matching_kuhn` (one value of `root`) reads at most E entries, so a
run reads at most n_left·E ≤ V·E (`time_complexity` of Kuhn; "at most V E" in `caveats`; "each search scans every
adjacency list at most once" in the docstring of `kuhn.py`).

**Proof.** Given in `entry.json`, field `time_complexity` of Kuhn (the parenthetical remark). The missing steps:
(a) the root is free when its search starts: a flip gives new partners only to the vertices on the stack, which are
the root and vertices pushed as `w = match_r[v]` with w ≠ −1, that is, vertices already matched; so a search adds at
most its own root to the matched left vertices, and before the search from root u only vertices < u are matched.
(b) "reads each entry of its list at most once": every read `v = nbrs[ptr[u]]` is guarded by `ptr[u] < len(nbrs)`
and followed by `ptr[u] += 1`, and `ptr` is reset only when the next root starts; so in one search the list of u is
read at most deg(u) times, and the search reads at most Σ_u deg(u) = E entries.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Kuhn: <= E per search, <= n_left E
in total": graphs from `harness.generate`, n = 0..60, 4 seeds per n (244 graphs).

## 2. Kuhn on G_k: (7k⁶ + 9k⁴ + 11k² − 3k)/6 entries

**Statement.** For every k ≥ 1, `matching_kuhn` on G_k reads exactly (7k⁶ + 9k⁴ + 11k² − 3k)/6 entries: (u + 1)(u + 2)/2
in the search from gadget root u < a, a(a + 1) in the search from each gadget root u ≥ a, 1 in the search from each
L_i (2 ≤ i ≤ j) of path j, and 2j − 1 in the search from L_1 of path j. The values listed in `entry.json` for
k = 3..11 (987, 5190, …, 2088999) are this formula; for example k = 3 gives (5103 + 729 + 99 − 9)/6 = 987 and k = 11
gives (12400927 + 131769 + 1331 − 33)/6 = 2088999.

**Proof.** Given in `entry.json`, field `time_complexity` of Kuhn (proof sketch). The missing steps:
(a) Each search starts with `seen` all false and `ptr` all 0, stays in its root's component, and changes nothing if
it fails. The roots run in index order: the gadget vertices 0..2a − 1, then path 1, …, path k, each path in the order
L_2, …, L_j, L_1.
(b) Gadget root u < a, when gadget vertex i is matched to right vertex u − 1 − i (i < u) and the rights u..a − 1 are
free (true for u = 0). Let c_0 = u and c_m = u − m (1 ≤ m ≤ u). Each c_m reads rights 0..m − 1, which are seen
(`continue`), and then right m, which is unseen; for m < u right m is matched to c_(m+1), which is pushed, and for
m = u right u (≤ a − 1) is free and the search succeeds. So c_m reads m + 1 entries, in all
Σ_{m=0..u} (m + 1) = (u + 1)(u + 2)/2. The flip walks the stack from the top, c_u = 0, …, c_0 = u, and gives vertex i
the right vertex u − i: the invariant for u + 1. After root a − 1, vertex i is matched to right a − 1 − i, and every
gadget right vertex is matched.
(c) Gadget root u ≥ a: let c_0 = u and c_m = a − m (1 ≤ m ≤ a). For m < a, c_m reads rights 0..m − 1 (seen) and
right m, which is matched to c_(m+1) (pushed); c_a = 0 reads rights 0..a − 1, all seen, and is popped; then each c_m
(m < a) resumes at `ptr` = m + 1, reads the rest of its list, all seen, and is popped. No right vertex of the gadget
is free, so the search fails: each of the a + 1 vertices reads its whole list, a(a + 1) entries, and the matching is
unchanged.
(d) Path j: before its roots, all its vertices are free. L_i (i = 2, …, j, in this order) reads R_(i−1), which is
free (L_(i−1) took R_(i−2)), and takes it: 1 entry each. Then L_1 reads R_1 (matched to L_2, pushed); L_i
(2 ≤ i ≤ j − 1) reads R_(i−1) (seen) and R_i (matched to L_(i+1), pushed); L_j reads R_(j−1) (seen) and R_j, which is
free: 1 + 2(j − 1) = 2j − 1 entries. For j = 1, L_1 reads R_1, which is free: 1 = 2j − 1. Path j costs 3j − 2.
(e) Sum: Σ_{u<a} (u + 1)(u + 2)/2 = C(a + 2, 3) (hockey stick), plus a·a(a + 1), plus Σ_{j=1..k} (3j − 2) = k(3k − 1)/2;
with a = k² this is (k⁶ + 3k⁴ + 2k²)/6 + k⁶ + k⁴ + (9k² − 3k)/6 = (7k⁶ + 9k⁴ + 11k² − 3k)/6.

**Check.** At the V2 sizes k = 3..11 (n = 39, 68, …, 495): `experiments/2026-10-07b_count_v2_matching.py`.
`experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Kuhn on G_k: (7k^6+9k^4+11k^2-3k)/6":
k = 1..12; line "Kuhn on G_k: scans per search": k = 1..7, the count of every search.

## 3. Hopcroft–Karp on G_k: k + 1 phases and (24k⁵ + 9k⁴ + 4k³ + 24k² − 25k + 12)/6 entries

**Statement.** For every k ≥ 1, `matching_hopcroft_karp` on G_k runs the body of its `while True` loop exactly
k + 1 times (k phases that augment, and a final breadth-first search that finds no free right vertex, after which it
returns), and reads exactly (24k⁵ + 9k⁴ + 4k³ + 24k² − 25k + 12)/6 entries: in phase 1, E in the BFS and
a(a + 1)/2 + a² + k(k + 1)/2 in the DFS; in phase t (2 ≤ t ≤ k), 2a² + (k − t + 1)(2t − 1) in the BFS and
2a² + (2t − 1) + (k − t)(2t + 1) in the DFS; in phase k + 1, 2a² in the BFS. The values listed in `entry.json` for
k = 4..15 (4572, 13602, …, 3116527) are this formula; for example k = 4 gives (24576 + 2304 + 256 + 384 − 100 + 12)/6
= 4572.

**Proof.** Given in `entry.json`, field `time_complexity` of Hopcroft–Karp (proof sketch). The missing steps:
(a) BFS. The queue starts with the free left vertices in index order, with dist 0; a vertex is appended only when
its dist is INF, and then gets dist du + 1. So each vertex is processed at most once, in FIFO order, with
nondecreasing dist. A processed vertex u reads its whole list unless `du + 1 > target`, and then reads nothing;
`target` is set once, to du + 1 at the first free right vertex met.
(b) DFS. The roots are the free left vertices with dist 0, in index order. At u the DFS reads from `ptr[u]` on; it
pushes w = `match_r[v]` if dist[w] = du + 1, augments at a free v if du + 1 = target, and goes on to the next entry
otherwise; when the list of u is exhausted without a push, it sets dist[u] = INF and pops u. An augmentation sets
dist = INF on the stack and flips the path. `ptr` is reset once per phase.
(c) Phase 1. All left vertices are free with dist 0. The BFS meets a free right vertex at its first read
(target = 1) and appends nothing, so every vertex reads its whole list: E. In the DFS no vertex has dist 1, so
nothing is pushed: each root takes its first free right vertex (du + 1 = 1 = target) or dies. Gadget root u < a reads
rights 0..u − 1, taken by the roots 0..u − 1, and takes right u: u + 1 entries. Gadget roots a..2a − 1 read a entries
each and die. In path j ≥ 2, L_i (i = 2..j) takes the free R_(i−1) after 1 entry, and L_1 reads R_1, taken by L_2,
and dies: j entries; in path 1, L_1 takes R_1: 1 entry. Total a(a + 1)/2 + a² + k(k + 1)/2. Afterwards gadget vertex
i is matched to right i (i < a), path 1 is matched, and each path j ≥ 2 has L_i matched to R_(i−1) (2 ≤ i ≤ j) with
L_1 and R_j free.
(d) Phase t, 2 ≤ t ≤ k, when paths 1..t − 1 are matched L_i ↔ R_i and the gadget and the paths j ≥ t are as after
phase 1. BFS: the queue starts with the gadget vertices a..2a − 1 and the L_1 of each path j ≥ t. Vertex a reads its
a entries and gives dist 1 to the a matched gadget vertices; the other free gadget vertices read a entries each and
add nothing; the matched gadget vertices (dist 1; du + 1 = 2 ≤ target, since target is INF or t) read a entries each
and add nothing: 2a². In path j ≥ t, L_1 reads R_1 and gives dist 1 to L_2, and a read L_i (2 ≤ i ≤ j) reads
R_(i−1) (its own partner) and R_i, which gives dist i to L_(i+1) if i < j and is free if i = j. Vertices of dist
d ≤ t − 1 pass the test (d + 1 ≤ t ≤ target) and are read; so L_i has dist i − 1 for i ≤ t + 1 (i ≤ j). Among the
right neighbours of the vertices of dist ≤ t − 1 (the gadget rights and R_1..R_t of the paths j ≥ t) only R_t of path
t is free, and it is met from L_t of dist t − 1: target = t. Every vertex of dist ≥ t is processed after all
vertices of dist ≤ t − 1, hence after target = t is set, and is skipped. So path j ≥ t reads L_1 (1 entry) and
L_2..L_t (2 each): 2t − 1, and paths < t are not reached.
DFS: root a reads right r = 0, 1, …, a − 1 in turn; the partner of right r has dist 1 and is pushed, reads its a
entries (their partners have dist 1 or INF, never 2, and no gadget right vertex is free) and dies; then root a dies:
a + a² entries. The other a − 1 free gadget roots read a entries each, whose partners now have dist INF: 2a² in
all. Path t: L_1 reads R_1 and pushes L_2; L_i (2 ≤ i < t) reads R_(i−1) (its own partner, dist i − 1 ≠ i) and R_i,
and pushes L_(i+1); L_t reads R_(t−1) and R_t, which is free at du + 1 = t = target, and augments: 2t − 1 entries,
after which L_i ↔ R_i for every i. Path j > t: the same steps reach L_t, which pushes L_(t+1) (dist t); L_(t+1)
reads R_t (its own partner) and R_(t+1), whose partner L_(t+2) has dist INF (the BFS skipped L_(t+1)), or which is
free but at du + 1 = t + 1 ≠ target (if j = t + 1); so L_(t+1) dies, and L_t, …, L_1, whose lists are exhausted, die
in turn: 2t + 1 entries, and path j is unchanged. No augmentation happens in the gadget, so this is the assumption
for phase t + 1.
(e) Phase k + 1: the free left vertices are the gadget vertices a..2a − 1, the BFS reads 2a² as in (d), meets no free
right vertex (the gadget rights are matched and every path is perfectly matched), and the function returns. So the
loop body runs k + 1 times.
(f) Sum: phase t (2 ≤ t ≤ k) contributes 4a² + (k − t + 1)(2t − 1) + (2t − 1) + (k − t)(2t + 1) = 4a² + 4t(k − t + 1) − 2,
and Σ_{t=2..k} t(k − t + 1) = k(k + 1)(k + 2)/6 − k. The total
(2a² + k²) + a(a + 1)/2 + a² + k(k + 1)/2 + Σ_{t=2..k} (4a² + 4t(k − t + 1) − 2) + 2a² is, with a = k²,
4k⁵ + (3/2)k⁴ + (2/3)k³ + 4k² − (25/6)k + 2 = (24k⁵ + 9k⁴ + 4k³ + 24k² − 25k + 12)/6 (for k = 1 the sum over t is
empty and both sides are 8).

**Check.** At the V2 sizes k = 4..15 (n = 68, 105, …, 915): `experiments/2026-10-07b_count_v2_matching.py`.
`experiments/2026-10-07_closed_form_checks.py`, group `query`, line "Hopcroft-Karp on G_k: k+1 BFS passes (k
augmenting phases + the final pass that finds no path)": k = 1..12. `experiments/2026-10-07_count_proof_checks.py`,
group `query`, line "Hopcroft-Karp on G_k: (24k^5+9k^4+4k^3+24k^2-25k+12)/6": k = 1..16; line "Hopcroft-Karp on
G_k: BFS and DFS scans per phase": k = 1..9, the counts of every BFS and DFS pass and the number of passes.

## 4. Hopcroft–Karp: at most E entries per BFS and per DFS pass

**Statement.** On every input, in each phase of `matching_hopcroft_karp` the BFS reads each adjacency list at most
once and the DFS reads each entry at most once, so each reads at most E entries ("each adjacency list is scanned at
most once per DFS pass" in the docstring of `hopcroft_karp.py`).

**Proof.** BFS: a vertex enters the queue either at the start (dist 0) or when its dist is INF, after which its dist
is finite for the rest of the phase; so it is processed at most once, and a processed vertex iterates its list at
most once. DFS: `ptr` is reset once per phase, and every read `v = nbrs[ptr[u]]` is guarded by `ptr[u] < len(nbrs)`
and followed by `ptr[u] += 1`.

**Check.** `experiments/2026-10-07_count_proof_checks.py`, group `query`, line "Hopcroft-Karp: <= E per BFS and
per DFS pass": the same 244 graphs as in section 1.

## 5. Augmenting paths and Berge's criterion

A matching M is a set of edges no two of which share a vertex; a vertex is *M-free* if no edge of M touches it. An
*M-augmenting path* is a path (no repeated vertex) whose two ends are M-free and whose edges alternate between edges
not in M and edges in M, starting and ending with an edge not in M. In a bipartite graph it has odd length
2t − 1 and runs from a free left vertex to a free right vertex. For two edge sets, A ⊕ B is their symmetric
difference.

**Lemma A1 (flip).** If P is M-augmenting, then M ⊕ P is a matching with |M| + 1 edges, every vertex of P is
matched in M ⊕ P by an edge of P, and the vertices off P keep their M-edges. *Proof.* Each interior vertex of P has
one edge of P in M and one not in M; in M ⊕ P it keeps exactly the other one. The two ends are M-free and get their
end edge. P has one more edge outside M than inside.

**Lemma A2 (Berge's criterion, the direction used here).** If M and N are matchings with |N| − |M| = s > 0, then
N ⊕ M contains at least s vertex-disjoint M-augmenting paths. In particular, a matching that is not maximum has an
augmenting path. *Proof.* Every vertex has at most one edge of each matching, so the components of N ⊕ M are paths
and cycles whose edges alternate between N and M. A cycle, or a path with an even number of edges, has as many
N-edges as M-edges; a path with an odd number of edges has one more of one kind. So at least s components are paths
with one more N-edge than M-edges, which start and end with N-edges. Their ends are M-free: an M-edge at an end x
would not be in N (x already has its N-edge in the path), hence would lie in N ⊕ M and give x degree 2 in the
component. So these s components are vertex-disjoint M-augmenting paths. Conversely, by Lemma A1 a matching that
has an augmenting path is not maximum. So a matching is maximum if and only if it has no augmenting path. (Credit:
Berge 1957.)

## 6. Correctness of Kuhn's algorithm

**Lemma K1 (the stack is an alternating path).** During the search from `root`, the stack is r = s_0, s_1, …, s_t
where each s_{a+1} = `match_r[v_{a+1}]` for a right vertex v_{a+1} ∈ adj[s_a] that was marked `seen` when s_{a+1} was
pushed. The v_a are distinct, the s_a are distinct, and s_0 v_1 s_1 … v_t s_t is an M-alternating path (M the
matching when the search starts) whose edges s_a v_{a+1} are not in M and v_a s_a are in M. *Proof.* The matching
does not change during a search. A right vertex is marked `seen` once per search, so the v_a are distinct; s_a for
a ≥ 1 is the partner of v_a and the root is free (section 1, step (a)), so the s_a are distinct. The edge s_a v_{a+1}
is not in M: for a = 0 the root is free; for a ≥ 1 the partner of s_a is v_a ≠ v_{a+1}. Popping removes the top, so
the stack always has this form.

**Lemma K2 (success).** If the search finds a free right vertex f in adj[s_t], then P = s_0 v_1 s_1 … v_t s_t f is an
M-augmenting path, and the flip loop replaces M by M ⊕ P. *Proof.* P is a path by Lemma K1 (f is free, so it is none
of the matched v_a), with free ends. The loop `for u in reversed(stack)` gives s_t the vertex f, then s_{t−1} the old
partner v_t of s_t, …, s_0 the old partner v_1 of s_1, and stops with `v = old = −1` (the root was free); `match_r` is
updated alongside. That is exactly M ⊕ P.

**Lemma K3 (failure is complete).** If the search from r fails, no M-augmenting path starts at r. *Proof.* A vertex
is popped only when `ptr[u] = len(nbrs)`, after it has read its whole list; on failure every pushed vertex is
popped, so every visited left vertex has read every entry, and every right neighbour of a visited vertex is `seen`.
A seen right vertex is either free, which ends the search with success at once, or matched, and then its partner is
pushed (visited). Suppose r = x_0, v_1, x_1, …, v_k is M-augmenting. By induction, v_1 is a neighbour of the
visited root, hence seen; if v_a is seen, it is matched (a < k), x_a is its partner and is visited, so v_{a+1} is
seen. So the free vertex v_k is seen, and the search would have succeeded.

**Lemma K4 (failed roots stay failed).** Let u be an M-free left vertex from which no M-augmenting path starts, and
let P be an M-augmenting path that does not start at u. Then no (M ⊕ P)-augmenting path starts at u. *Proof.* As in
`entry.json`, field `correctness` of Kuhn: u is free and P's interior vertices are matched, so u is not on P. Let Q
be an (M ⊕ P)-augmenting path from u. If Q avoids P, its edges and its free end have the same status in M, so Q was
M-augmenting. Otherwise let z be the first vertex of Q on P. The edge of Q entering z is not on P, and z is matched
in M ⊕ P by an edge of P (Lemma A1), so that edge is not in M ⊕ P; edges not in the matching go from left to right
along Q, so z is a right vertex. Then Q from u to z, followed by P from z to its free right end y (starting with z's
M-edge unless z = y), is an M-augmenting path from u: its vertices before z are off P, and on P the statuses
alternate as in M. Contradiction.

**Theorem K.** `matching_kuhn` returns the size of a maximum matching. *Proof.* The roots are tried in index order.
By Lemmas K2 and A1 a successful search adds one edge and keeps every matched vertex matched; a failed search
changes nothing. By Lemma K3 a root whose search fails has no augmenting path at that time; by Lemma K4 this stays
true after every later augmentation (each later path starts at a later root and does not start at u). At the end
every free left vertex is a failed root, and every augmenting path starts at a free left vertex, so none exists. By
Lemma A2 the matching is maximum, and `size` counts its edges.

**Check.** `tests/test_proofs_matching.py`, `test_kuhn_searches`: 240 seeded graphs (`harness.generate` with
n = 0..40, unions of up to 5 paths in the G_k orientation or reversed, and G_k for k = 1..3); the matching is read
at the start of every search from the running code: the root is free, the search succeeds exactly when an
independent alternating BFS finds an augmenting path from the root, every earlier failed root still has none, and the
final matching has no augmenting path. The V1 battery (n = 0..300) compares both implementations with the
Edmonds-matrix oracle.

## 7. Correctness of Hopcroft–Karp and its phase bound

A *phase* is one run of the body of `while True`; M is the matching when it starts. Let G_M be the digraph on the
left vertices with an arc x → `match_r[v]` for every matched v ∈ adj[x], λ(x) the BFS distance in G_M from the set of
M-free left vertices (∞ if unreachable), and T* = 1 + min λ(x) over the left vertices x that have an M-free
neighbour (∞ if there is none). `INF` in the code is n_left + n_right + 1, larger than any level.

**Lemma HK1 (BFS).** (i) Every M-augmenting path has at least 2T* − 1 edges, and one with exactly 2T* − 1 edges
exists if T* < ∞. (ii) After the BFS, `target` = T*, and `dist[x]` = λ(x) if λ(x) ≤ T*, `INF` otherwise; if T* = ∞,
`target` = `INF` and the function returns.
*Proof.* (i) An augmenting path x_0 v_1 x_1 … x_{t−1} v_t has x_{a+1} = `match_r[v_{a+1}]`, an arc of G_M, so
λ(x_a) ≤ a, and x_{t−1} has the free neighbour v_t, so t − 1 ≥ T* − 1. Conversely, a shortest G_M-path from a free
left vertex to a vertex at level T* − 1 with a free neighbour f has distinct vertices, its right vertices are the
partners of distinct left vertices, and f is free, so it gives an augmenting path with T* right vertices and
2T* − 1 edges. (ii) The queue starts with the free left vertices (dist 0) and appends a vertex only when its dist is
`INF`, giving it du + 1; so, as in any breadth-first search, vertices are dequeued in non-decreasing dist and
dist = λ for every vertex appended from an expanded vertex. A dequeued u is skipped exactly when du + 1 > `target`.
`target` is set once, by the first expanded vertex with a free neighbour, to its dist + 1. Vertices at levels
< T* − 1 have no free neighbour, and none is skipped while `target` = `INF`; the first expanded vertex with a free
neighbour is at level T* − 1, so `target` = T*. All vertices at level T* − 1 are expanded (du + 1 = T* ≤ `target`),
so every vertex at level T* gets dist T*; vertices at level ≥ T* are skipped, so nothing at level > T* gets a
finite dist. If T* = ∞ nothing is skipped and `target` stays `INF`.

**Lemma HK2 (the DFS finds vertex-disjoint shortest augmenting paths).** Each augmentation of the phase is along an
M-augmenting path x_0 v_1 x_1 … x_{T*−1} v_{T*} with `dist[x_a]` = λ(x_a) = a; the paths of one phase are
vertex-disjoint; and the matching at the end of the phase is M ⊕ (P_1 ∪ … ∪ P_r).
*Proof.* A push needs `dist[w]` = du + 1 and a success needs a free v with du + 1 = `target` = T*; dist values only
change to `INF`; so the stack holds vertices with dist 0, 1, 2, … (no repetition), and a successful stack has T* left
vertices. After a success, the path's left vertices get dist `INF` and its right vertices are matched to them, so
neither can be used again: they are never pushed, never accepted as free, never passed through, and a root already
matched in this phase is skipped (`match_l[root] != −1`). Vertices off the earlier paths keep their M-status, so
each path is M-augmenting and avoids the earlier ones; as in Lemma K2 the flip replaces the current matching M_j by
M_j ⊕ P_{j+1}, and disjointness gives M ⊕ (P_1 ∪ … ∪ P_r).

**Lemma HK3 (maximality).** At the end of a phase with T* < ∞, no shortest M-augmenting path avoids the vertices of
all paths found in it.
*Proof.* Let T = T* and λ as above; for a stack vertex, `dist` = λ, and later `dist` is λ or `INF` (dead, or on a
found path). Let F(τ) be the set of vertices on the paths found up to time τ. A *layered path from x* (λ(x) = j < T)
is x = y_j, v_{j+1}, y_{j+1}, …, y_{T−1}, v_T with v_{a+1} ∈ adj[y_a], λ(y_a) = a, y_{a+1} the M-partner of v_{a+1},
and v_T M-free. Call x *live* at τ if x ∉ F(τ) and some layered path from x avoids F(τ), and an entry (x, v) of
adj[x] *open* at τ if such a path starts with the edge x v. F only grows, so liveness and openness can only be lost.
*Invariant (J): between steps of the DFS loop, for every left vertex x, no entry of adj[x] before position `ptr[x]`
is open, except possibly the entry at position `ptr[x]` − 1 when x is on the stack below the top (the entry through
which x pushed its successor).* It holds when `ptr` is reset. When the top u reads the entry (u, v) at position
`ptr[u]` (du = λ(u)): (1) if v ∈ F, no path through v avoids F; (2) if v is currently free (hence M-free and not in
F) and du + 1 ≠ T, a layered path through u v would need λ(u) = T − 1; (3) if v is free and du + 1 = T, the
search succeeds and the whole stack joins F, whose vertices have no open entries; (4) if v is matched to w with
`dist[w]` ≠ du + 1, then either λ(w) ≠ λ(u) + 1 (not layered), or w ∈ F, or w died earlier: w died as the top with
an exhausted pointer, so by (J) none of its entries was open and w was not live, and it stays not live; in each case
u v is not open; (5) if `dist[w]` = du + 1, w is pushed and (u, v) becomes u's exception; (6) when the top u is
popped dead, all its entries are passed and, by (J) without exception, none is open, so u is not live; hence the
exception entry of its parent, which can only continue through u, is not open, and (J) holds with the parent as the
top.
*Conclusion.* Every M-free left vertex has λ = 0 and, unless it was matched earlier in the phase (then it is in F),
is a root of the DFS loop (free vertices are never pushed, since pushes are partners of matched vertices). Its
search ends with a success (it joins F) or with the root popped dead (not live). So at the end every M-free left
vertex is in F or not live. Let P = x_0 v_1 x_1 … x_{T−1} v_T be a shortest M-augmenting path avoiding F. By Lemma
HK1, λ(x_a) ≤ a and λ(x_{T−1}) ≥ T − 1; λ grows by at most 1 along P, so λ(x_a) = a and P is a layered path from the
M-free vertex x_0 avoiding F, i.e. x_0 is live: a contradiction.

**Lemma HK4 (length increase).** Let ℓ be the length of a shortest M-augmenting path, P_1, …, P_r vertex-disjoint
M-augmenting paths of length ℓ such that no M-augmenting path of length ℓ avoids all of them, and
M′ = M ⊕ (P_1 ∪ … ∪ P_r). Then every M′-augmenting path has more than ℓ edges, hence at least ℓ + 2.
*Proof.* Let A = P_1 ∪ … ∪ P_r (rℓ edges) and let P be M′-augmenting. N = M′ ⊕ P is a matching with |M| + r + 1
edges, and M ⊕ N = A ⊕ P. By Lemma A2 it contains r + 1 vertex-disjoint M-augmenting paths, each with ≥ ℓ edges,
so |A ⊕ P| = rℓ + |P| − 2|A ∩ P| ≥ (r + 1)ℓ, i.e. |P| ≥ ℓ + 2|A ∩ P|. If P shares a vertex x with some P_i, then x
is matched in M′ by an edge of P_i (Lemma A1), so x is not an end of P (the ends are M′-free), and P, alternating,
contains x's M′-edge, which lies in A: |P| ≥ ℓ + 2. If P avoids every P_i, its edges and ends have the same status in
M, so it is M-augmenting, |P| ≥ ℓ, and |P| = ℓ is excluded by the hypothesis. Lengths of augmenting paths are odd.
(Credit: Hopcroft & Karp 1973.)

**Theorem HK.** `matching_hopcroft_karp` returns the size of a maximum matching; it runs at most
min_{i ≥ 0} (i + ⌊V/(2i + 2)⌋) + 1 phases, which is less than √(2V) + 1 for V ≥ 1; each phase takes O(V + E) time
and reads at most E entries in its BFS and at most E in its DFS (section 4); so the total time is O((V + E)√V).
*Proof.* The last phase finds T* = ∞, so no augmenting path exists (Lemma HK1) and the matching is maximum
(Lemma A2); `size` counts the augmentations. A phase with T* < ∞ augments at least once (otherwise F is empty and a
shortest path avoids it, against Lemma HK3), and by Lemmas HK2–HK4 the shortest augmenting length grows by at least
2. So after i such phases every augmenting path has at least 2i + 1 edges, hence at least 2i + 2 vertices. Let ν be
the maximum size and d_i = ν − |M| after i such phases; by Lemma A2 (N maximum) there are d_i vertex-disjoint
augmenting paths, so d_i(2i + 2) ≤ V; each further phase with T* < ∞ adds at least one edge, so their total number
q satisfies q ≤ i + ⌊V/(2i + 2)⌋ for every i ≥ 0. With i = ⌊√(V/2)⌋ and s = √(V/2): i ≤ s and
⌊V/(2i + 2)⌋ < V/(2s) = s, so q < 2s = √(2V), and the number of phases is q + 1. Per phase: building `dist`,
`queue` and `ptr` is O(V); in the BFS every left vertex enters the queue at most once and reads its list at most once;
in the DFS `ptr` only grows, every left vertex is pushed at most once (after it leaves the stack its dist is `INF`),
pops are at most pushes plus roots, and the flips of the disjoint paths cost O(V) together.

**Check.** `tests/test_proofs_matching.py`, `test_hopcroft_karp_phases`: the same kinds of graphs as in section 6
(240 seeded graphs, more than 300 phases with T* < ∞). The matching at every phase start and `target` and `dist`
after every BFS are read from the running code. Checked: `target` = (ℓ + 1)/2 and the levels against an independent
alternating BFS (HK1); the matching changes along r ≥ 1 vertex-disjoint M-augmenting paths of length ℓ (the symmetric
difference has rℓ edges on r(ℓ + 1) vertices, 2r of them M-free) (HK2); no shortest M-augmenting path avoids their
vertices, while un-banning one of them exposes one again (HK3, with a sensitivity control); the shortest length grows
by at least 2 (HK4); the phase count is at most min_i(i + ⌊V/(2i + 2)⌋) + 1 and below √(2V) + 1; the last phase has no
augmenting path; and the result equals Kuhn's.

## 8. Time bounds

The cost model is the entry's: index operations are unit cost.

**Kuhn.** Each search costs O(V + E): allocating `seen` and `ptr` is O(V), at most E entries are read (section 1),
every loop step reads an entry or pops, pops are at most pushes ≤ n_left, and the flip is O(n_left). With n_left
searches the total is O(n_left·(V + E)) ⊆ O(V(V + E)), which is O(VE) when E = Ω(V).

**Hopcroft–Karp.** O((V + E)√V) by Theorem HK.

**Dense graphs.** E ≤ n_left·n_right ≤ V²/4, so the bounds are O(V³) and O(V^2.5).

## 9. The separation over all graphs with V vertices

**Statement.** For every V ≥ 5 there is a graph with V vertices on which Kuhn reads more than 7V³/34992 adjacency
entries, while on every graph with V vertices Kuhn reads at most n_left·E ≤ V³/4 entries and Hopcroft–Karp takes
O(V^2.5) time. So over graphs with V vertices the worst cases are Θ(V³) for Kuhn and O(V^2.5) for Hopcroft–Karp. On
G_k itself the ratios are Kuhn/(VE) → 7/48 and HK/(E√V) → 1.

**Proof.** Let k ≥ 1 be the largest integer with 4k² + k ≤ V. Then V < 4(k + 1)² + (k + 1) = 4k² + 9k + 5 ≤ 18k², so
k² > V/18. Add V − (4k² + k) isolated right vertices to G_k. They are in no adjacency list, so no search reads more or
less than on G_k (the extra entries of `seen` are never consulted), and Kuhn reads exactly
(7k⁶ + 9k⁴ + 11k² − 3k)/6 ≥ 7k⁶/6 > 7V³/(6·18³) = 7V³/34992 entries (section 2). The upper bounds are sections 1 and 8.
The ratios: Kuhn(k) = (7/6)k⁶ + O(k⁴) and VE = (4k² + k)(2k⁴ + k²) = 8k⁶ + O(k⁵), so Kuhn(k)/(VE) → 7/48;
HK(k) = 4k⁵ + O(k⁴) and E√V = (2k⁴ + k²)√(4k² + k) = 4k⁵ + O(k⁴), so HK(k)/(E√V) → 1 (section 3).

**Check.** `tests/test_proofs_matching.py`, `test_kuhn_count_on_padded_family` (k = 1..5, with 0, 1, 3 or 7 isolated
right vertices and 0 or 2 isolated left vertices: the harness's `CountingNeighbours` count equals the closed form).
The closed forms themselves are checked as listed in sections 2 and 3.

## 10. Space

**Statement.** The unit is the list entry (one word each); CPython's over-allocation of lists and its integer
objects are not counted. Besides the input, both algorithms hold O(V) list entries, at least n_left + n_right (the
two partner arrays). Kuhn holds at most 4·n_left + 3·n_right list entries at any time, and at most
3·n_left + 2·n_right in the lists bound to its local variables between statements (what the check measures).
Hopcroft–Karp holds at most 5·n_left + n_right list entries at any time, also while one of its lists is being
replaced.

**Proof.** Kuhn's containers are `match_l` (n_left), `match_r` (n_right), and per search `seen` (n_right), `ptr`
(n_left) and `stack` (at most n_left: a left vertex is pushed at most once per search, section 1). Between statements
that is at most 3·n_left + 2·n_right. The lists of a search are replaced one at a time at the start of the next
search: while the new `seen` is created, the previous `seen`, `ptr` and `stack` still exist (the previous stack holds
at most n_left vertices, the path of a successful search), at most n_left + n_right + 2·n_right + n_left + n_left
= 3·n_left + 3·n_right; while the new `ptr` is created, the new `seen`, the previous `ptr` and `stack` and the new
`ptr` exist, at most n_left + n_right + n_right + 2·n_left + n_left = 4·n_left + 2·n_right; `stack = [root]` replaces
a list of at most n_left entries by one entry. So at most max(3·n_left + 3·n_right, 4·n_left + 2·n_right)
≤ 4·n_left + 3·n_right at any time.
Hopcroft–Karp's containers are `match_l`, `match_r`, and per phase `dist` (n_left), `queue` (at most n_left: a vertex
is appended only while its dist is `INF`), `ptr` (n_left) and `stack` (at most n_left, distinct vertices). At the
start of a phase `dist`, `queue` and `ptr` are replaced one at a time, and whenever one of them is replaced the
previous `stack` is empty (the DFS of every root ends with an empty stack, after a dead end or after `stack = []` at
an augmentation), so at most four lists of at most n_left entries coexist with `match_l` and `match_r`:
5·n_left + n_right at any time. `nbrs` is a list of the input.

**Check.** `tests/test_proofs_matching.py`, `test_space`: on 60 seeded graphs of the kinds of section 6, the
instrumented peak of `tests/proof_space.py` (container slots bound to local variables between statements, the input
excluded) lies between n_left + n_right and 3·n_left + 2·n_right for Kuhn and 5·n_left + n_right for Hopcroft–Karp.
The transient values at list creation are not visible to this check; they are covered by the proof.

## 11. The oracle's error bound (caveat)

`harness.check` returns `None` if a side has more than 160 vertices. Otherwise it compares the output with the rank,
over the field GF(P) with P = 2⁶¹ − 1, of the n_left × n_right matrix B with an independent uniform entry from
{1, …, P − 1} at every edge and 0 elsewhere.

**Statement.** The rank of B is at most the maximum matching size ν, and it is smaller with probability at most
ν/(P − 1) < 10⁻¹⁵ per instance; with the seed derived from the instance, the check is deterministic.

**Proof.** P is prime (a Mersenne prime; the test below runs the Lucas–Lehmer test). Let A be the same matrix with a
distinct indeterminate z_{uv} at every edge. For a set R of k rows and a set S of k columns, det A[R, S] is the sum
over bijections σ: R → S of ±Π_{u∈R} A[u][σ(u)]; a term is non-zero exactly when σ is a perfect matching between R
and S, and distinct σ give distinct monomials, so no terms cancel: the minor is a non-zero polynomial (with
coefficients ±1, hence non-zero over GF(P) as well) if and only if R and S have a perfect matching. So every minor
of size > ν is the zero polynomial, and the substituted matrix B has rank ≤ ν (the one-sided error). A ν × ν minor
of A for a maximum matching is a non-zero polynomial of total degree ν; by the Schwartz–Zippel lemma (induction on
the number of variables, using that a non-zero polynomial of degree d in one variable has at most d roots), its value
at independent uniform points of {1, …, P − 1} is 0 with probability at most ν/(P − 1) ≤ 160/(2⁶¹ − 2) < 7·10⁻¹⁷.
Gaussian elimination over GF(P) (row swaps and adding multiples of a pivot row, inverses by Fermat's little theorem
since P is prime) preserves the rank and counts the pivots, which is the rank. The generator is
`random.Random(repr(graph))`, a fixed function of the instance.

**Check.** `tests/test_proofs_matching.py`, `test_edmonds_oracle`: the Lucas–Lehmer test confirms that 2⁶¹ − 1 is
prime, 160/(P − 1) < 10⁻¹⁵, and `harness.check` accepts Kuhn's output on all 2^(ab) bipartite graphs with a, b ≤ 3
(689 graphs). The V1 battery uses the oracle on n = 0..300.

## 12. Matchings and unit-capacity flows (notes)

**Statement.** Let the network have a source s, a sink t, arcs s → u (every left u), u → v (every edge) and v → t
(every right v), all of capacity 1. The matchings of size k correspond one-to-one to the integral flows of value k,
so the maximum matching size is the maximum value of an integral flow in this network.

**Proof.** A matching M gives the flow with value 1 on s → u, u → v and v → t for every (u, v) ∈ M and 0 elsewhere:
capacities hold and flow is conserved, and the value is |M|. Conversely, an integral flow has values 0 or 1; a left
vertex receives at most 1 from s, so at most one of its arcs u → v carries flow, and a right vertex sends at most 1
to t, so at most one arc into it carries flow; the arcs u → v with flow 1 form a matching whose size is the value.
The two maps are inverse to each other.

**Check.** `tests/test_proofs_matching.py`, `test_unit_capacity_flow`: on 150 seeded `harness.generate` graphs
(n = 0..40), the Edmonds–Karp implementation of `pairs/max-flow-edmonds-karp-vs-dinic` on this network returns
Kuhn's matching size.

## 13. Measured statements (data, not theorems)

The V2 fits and the earlier timing fits, and the random-graph figures in the caveats: on the 8 random bipartite
graphs measured (one each for V = 100, 200, 400, 800 and p = 0.05, 0.5) Hopcroft–Karp needed 2 to 5 phases, and
Kuhn read about 0.08·VE entries for p = 0.5 and 0.025–0.047·VE for p = 0.05
(`experiments/2026-10-07_bipartite_matching_counts.py`). These are measurements of those instances only.
