# Proofs: maximum flow, Edmonds–Karp vs Dinic

This file proves the claims of this entry about its two implementations: that both return the value of a maximum
flow, the worst-case upper bounds O(V·E²) and O(V²·E), the space bound, the bounds in terms of the flow value that
the caveats state, the matching reduction mentioned in the notes, and a separation of the two implementations on the
entry's own random family (sections 9 and 10). Each section names the deterministic checks. A check covers only its
stated range; the proofs cover every network of the problem (sections 1 to 8) or every n in the stated range
(section 10).

**What is shown about Dinic being faster.** The worst-case bounds O(V·E²) and O(V²·E) are proved as **upper bounds**
only. On the random networks of `generate_scaling` (the model 𝔊ₙ of section 9, under the ideal-random-bits
Assumption R), section 10 proves a separation: for every n ≥ 21 793, with probability at least 1 − 5/n, Edmonds–Karp
makes at least 0.011·n³ reads while Dinic runs in O(n²) time. **No
worst-case separation is proved:** the worst-case lower bound proved for Edmonds–Karp, Ω(n³) on networks with
capacities ≤ 100 (Corollary S), does not exceed Dinic's proved worst-case bound O(V²·E). The T3 tag rests on the
worst-case upper bounds proved in sections 3–4 (the published bounds of the two algorithms, listed in the `background`
field of `entry.json`) and on that family separation.

## 0. Notation and the residual arrays

A network is (n, s, t, edges) with vertices 0..n − 1, s ≠ t, and edges e_i = (u_i, v_i, c_i), i = 0..E − 1, with
u_i ≠ v_i and integer capacities c_i ≥ 0 (parallel and antiparallel edges allowed). V = n. A *flow* is a vector f
with 0 ≤ f_i ≤ c_i and conservation (inflow = outflow) at every vertex other than s, t; its value |f| is the net
flow out of s. A *cut* is a vertex set S with s ∈ S, t ∉ S; its capacity is c(S) = Σ c_i over the edges with
u_i ∈ S, v_i ∉ S.

Both implementations build the same arrays: edge i gets the arc 2i (u_i → v_i, `cap` initially c_i) and the arc
2i + 1 (v_i → u_i, `cap` initially 0); arc e and arc e ^ 1 are reverses of each other; `adj[u]` lists the arcs
leaving u (Σ_u |adj[u]| = 2E). The *residual graph* consists of the arcs with `cap` > 0.

**Invariant R.** At every moment, `cap[2i] + cap[2i+1] = c_i` and `cap[e] ≥ 0` for every arc, so f_i := `cap[2i+1]`
satisfies 0 ≤ f_i ≤ c_i; f is a flow, and |f| equals the variable `flow`.

*Proof.* Initially f = 0 and `flow` = 0. Both implementations change `cap` only by an augmentation: along a path
P = (x_0 = s, x_1, …, x_k = t) of arcs with positive `cap` they compute δ = the minimum `cap` on P (δ ≥ 1, since
capacities are integers), lower `cap` of each arc of P by δ and raise `cap` of its reverse by δ, and add δ to `flow`.
This keeps the sum per edge and non-negativity (δ is the minimum). On edge i, an arc 2i on P raises f_i by δ and an
arc 2i + 1 on P lowers f_i by δ, so each inner vertex x_j receives δ more net inflow through the arc (x_{j−1}, x_j)
and sends δ more net outflow through (x_j, x_{j+1}): conservation holds, and the net outflow of s rises by δ.
The paths used are simple (§2, §4), so no arc occurs twice on P. ∎

**Cost model.** Running times count elementary operations, each O(1): indexing and assigning list entries, appending to
a list, `deque.append` and `deque.popleft` (O(1) per the documentation of `collections.deque`), comparisons, and
arithmetic on capacities and flow values; creating a list of length k costs O(k), and the built-in `min` over a path of
k arcs costs O(k). Arithmetic on capacities and flow values is counted as unit cost. In the harness every capacity is
at most 100 and every flow value at most 100·E, so these are machine-size integers; for arbitrary integer capacities
the bounds count arithmetic operations. *Reads* (section 10) are particular elementary operations, so a lower bound
on reads is a lower bound on time.

## 1. Lemma M (max-flow min-cut, from the residual graph)

(a) For every flow f and every cut S, |f| ≤ c(S).
(b) If the residual graph has no s–t path, the vertices S reachable from s form a cut with c(S) = |f|, so f is a
maximum flow and S is a minimum cut.

*Proof.* (a) Summing conservation over the vertices of S gives |f| = Σ_{u_i ∈ S, v_i ∉ S} f_i −
Σ_{u_i ∉ S, v_i ∈ S} f_i ≤ Σ_{u_i ∈ S, v_i ∉ S} c_i = c(S). (b) t ∉ S. For an edge with u_i ∈ S, v_i ∉ S, the arc
2i leaves S, so its `cap` is 0 and f_i = c_i; for an edge with u_i ∉ S, v_i ∈ S, the arc 2i + 1 (v_i → u_i) leaves
S, so f_i = `cap[2i+1]` = 0. The identity in (a) then reads |f| = c(S); by (a) no flow exceeds c(S). ∎

So the maximum flow value equals the minimum cut capacity whenever some flow satisfies (b); both implementations
end in that state (below), which proves the equality for every network of the problem. The harness oracle compares
with the minimum over all cuts, which is valid by this lemma.

## 2. Breadth-first search

Let d(v) be the residual distance from s (fewest arcs on a residual s–v path; ∞ if there is none). A breadth-first
search from s that labels a vertex when it is first enqueued visits the vertices in non-decreasing d and labels
every reached v with d(v); the parent of v is a vertex at distance d(v) − 1 (standard: by induction, the queue
always holds labels ℓ, …, ℓ, ℓ + 1, …, ℓ + 1). Every residual arc (x, y) satisfies d(y) ≤ d(x) + 1.

A simple path has at most V − 1 arcs, and it uses at most one arc of each edge i (arcs 2i and 2i + 1 both join u_i
and v_i), so it has at most E arcs. Hence d(t) ≤ L := min(V − 1, E) when t is reachable.

## 3. Edmonds–Karp

**Correctness.** Each iteration runs the BFS of §2 (it stops as soon as t is labelled). If t is labelled, the arcs
`parent_edge` from t back to s form a shortest residual s–t path, and the code augments along it (Invariant R). If
t is not labelled, the queue emptied, so every vertex reachable from s was labelled and t is not reachable: the code
returns `flow`, which is the maximum by Lemma M(b). Termination follows from the bound below (and also from
integrality: each augmentation adds δ ≥ 1, and |f| ≤ c({s}) by Lemma M(a)).

**Lemma D (distances never decrease).** Let d be the distances before an augmentation along a path all of whose
arcs (x, y) satisfy d(y) = d(x) + 1, and d' the distances after it. Then d'(v) ≥ d(v) for every v.

*Proof.* After the augmentation every residual arc (x, y) was residual before (then d(y) ≤ d(x) + 1 by §2) or is
the reverse of a path arc (then d(y) = d(x) − 1). Along a shortest residual s–v path x_0 = s, …, x_k = v after the
augmentation, induction gives d(x_j) ≤ j, so d(v) ≤ k = d'(v). ∎

**Lemma A (number of augmentations).** Edmonds–Karp makes at most A ≤ E·(L + 1) ≤ E·V augmentations, where
L = min(V − 1, E), whatever the capacities.

*Proof.* Call an arc *critical* in an augmentation if its `cap` becomes 0 there; the arc attaining δ is critical,
so every augmentation has a critical arc. Let the arc e = (x → y) be critical in augmentation j and again in a later
augmentation j″, and let d_j denote the distances before augmentation j. In j, e lies on a shortest path:
d_j(y) = d_j(x) + 1. After j, `cap[e]` = 0; it becomes positive again only through an augmentation j′ with
j < j′ < j″ along the reverse arc (y → x), so d_{j′}(x) = d_{j′}(y) + 1 ≥ d_j(y) + 1 = d_j(x) + 2 (Lemma D), and
d_{j″}(x) ≥ d_{j′}(x). So each time e is critical, d(x) is at least 2 larger than the previous time. When e is
critical, x is on a shortest s–t path and x ≠ t, so 0 ≤ d(x) ≤ L − 1. Hence e is critical at most ⌊(L − 1)/2⌋ + 1
≤ (L + 1)/2 times, and with 2E arcs, A ≤ 2E·(L + 1)/2 = E(L + 1). ∎

**Theorem EK (time).** Edmonds–Karp runs in O((A + 1)(V + E)) time, hence O(V·E²) for E ≥ 1 (and O(V) for E = 0),
independently of the capacity values; on graphs without parallel edges, E ≤ V(V − 1), so O(V⁵).

*Proof.* Building the arrays costs O(V + E). One iteration costs O(V) for `parent_edge` and the two walks along the
path (at most V − 1 arcs), plus O(V + E) for the BFS (each vertex is enqueued at most once, so each list `adj[u]`
is read at most once). There are A + 1 iterations. With A ≤ E(L + 1): if E ≥ V, then L + 1 ≤ V and
(A + 1)(V + E) ≤ (EV + 1)·2E ≤ 4VE²; if E < V, then L + 1 ≤ E + 1 ≤ 2E and (A + 1)(V + E) ≤ (2E² + 1)·2V ≤ 6VE²
(E ≥ 1). ∎

## 4. Dinic

Each phase runs a full BFS from s (no early stop), so `level[v]` = d(v) for the residual graph at the start of the
phase (§2). If t is unreachable it returns `flow`, a maximum by Lemma M(b). Otherwise it runs the depth-first search
with the pointers `it`.

Call an arc e leaving u *admissible* (at a moment) if `cap[e]` > 0 and `level[to[e]] = level[u] + 1`; call a
vertex *dead* if no path of admissible arcs leads from it to t.

**Lemma B1.** Within a phase, a non-admissible arc never becomes admissible; hence a dead vertex stays dead.

*Proof.* Levels are fixed during the phase. `cap` changes only by augmentations along the current `path`, whose
arcs were admissible when they were pushed and have not changed since (no augmentation happens between a push and
the next augmentation, which clears the path). An augmentation lowers `cap` of level-increasing arcs and raises
`cap` only of their reverses, which go from level ℓ + 1 to level ℓ and are never admissible. ∎

**Lemma B2 (the search finds a blocking flow).** During a phase: (i) `path` is a sequence of admissible arcs from s
to the current vertex u; (ii) every arc of `adj[u]` before position `it[u]` is non-admissible or leads to a dead
vertex. When the phase ends (`path` empty and `it[s]` at the end of `adj[s]`), s is dead: no s–t path of
admissible arcs remains. Every phase that starts with t reachable makes at least one augmentation.

*Proof.* (i) holds by the argument in the proof of B1. (ii) The pointer `it[u]` moves in two places. In the scan
loop it passes an arc that is not admissible at that moment, which stays non-admissible (B1). At a retreat from a
vertex x (the DFS stood at x with `it[x]` at the end of `adj[x]` and x ≠ t, since t is handled first), every arc of
x is non-admissible or leads to a dead vertex by (ii) for x, so x is dead; the pointer of x's predecessor then
passes the arc into x, which leads to a dead vertex, and stays so (B1). That arc is the one at `it[u]` of the
predecessor u: between the advance from u along it and this retreat, the DFS visited only vertices of higher level
than u (levels rise by 1 along `path`, so u does not reappear on it) and made no augmentation (an augmentation clears
`path`), so `it[u]` did not move. When the phase ends, (ii) for s says that s
is dead. At the start of the phase a shortest residual s–t path is a path of admissible arcs, so s is not dead;
admissibility changes only through augmentations, so at least one augmentation happened. ∎

**Lemma B3 (the distance to t grows).** Let d be the distances at the start of a phase and d' those at the start of
the next one. Then d' ≥ d pointwise and d'(t) ≥ d(t) + 1.

*Proof.* Every augmentation of the phase uses arcs with d(y) = d(x) + 1, so, as in the proof of Lemma D, every
residual arc (x, y) at the end of the phase satisfies d(y) ≤ d(x) + 1 (the arcs that became residual are reverses of
such arcs), which gives d' ≥ d. If d'(t) = d(t) = ℓ, take a residual s–t path x_0, …, x_ℓ at the end of the phase:
d(x_j) ≤ j, d(x_ℓ) = ℓ and each step raises d by at most 1, so d(x_j) = j for all j. Every arc of the path is then
level-increasing with positive `cap`, i.e. admissible, and s is not dead, contradicting Lemma B2. ∎

**Theorem DI.** Dinic returns the maximum flow value. It makes at most L = min(V − 1, E) phases with t reachable
(in particular at most V − 1), plus the final BFS. A phase costs O(V + E + ℓ·A_p) ⊆ O(V·E) for E ≥ 1, where
A_p ≤ E is its number of augmentations and ℓ = `level[t]` ≤ V − 1. The total time is O(V²·E) for E ≥ 1 (O(V) for
E = 0); on graphs without parallel edges, O(V⁴).

*Proof.* By B3, d(t) strictly increases from phase to phase and lies in 1..L while t is reachable (§2), which bounds
the number of phases; the last BFS finds t unreachable and the answer is maximal by Lemma M(b). Within a phase, the
pointers only move forward, so the scan loop and the retreats increment them at most Σ_u |adj[u]| = 2E times in
total. Each augmentation makes some admissible arc saturated, which stays non-admissible (B1); of the two arcs of an
edge at most one is level-increasing, so there are at most E admissible arcs and A_p ≤ E. Every
advance pushes an arc that is later popped by a retreat (at most 2E of them) or cleared by an augmentation, whose
path has exactly ℓ arcs (levels rise by 1 per arc from 0 to ℓ); so there are at most 2E + ℓ·A_p advances, and each
augmentation costs O(ℓ) for its minimum and its updates. With the BFS (O(V + E)) the phase costs
O(V + E + ℓ·A_p) ⊆ O(V + E + V·E) = O(V·E) for E ≥ 1. Summing over at most V phases gives O(V²·E). ∎

## 5. Space

Both implementations store `to` and `cap` (2E entries each), `adj` (V lists, 2E entries in total), and O(V)-size
arrays (`parent_edge`, the queue; `level`, `it`, and `path`, which has at most V − 1 arcs). The input edge tuple is
read once. Space O(V + E) besides the input. **Check:** `tests/test_proofs_maxflow.py`, class `Space`: the
tracemalloc peak of one call, divided by V + E, stays below 200 bytes and grows by less than 30% per doubling of n on
`generate_scaling`, n = 40, 80, 160 (measured: about 100 to 115 bytes).

## 6. Bounds in terms of the flow value F (the caveats)

**Theorem F.** Let F be the maximum flow value, C the largest capacity and outdeg(s) the number of edges leaving s.
(a) Edmonds–Karp makes A ≤ F augmentations and runs in O((F + 1)(V + E)) time.
(b) Dinic makes at most F + 1 phases (BFS passes, the final one included) and runs in O((F + 1)(V + E)) time.
(c) F ≤ C·outdeg(s); without parallel edges out of s, outdeg(s) ≤ min(V − 1, E).
(d) Hence, with C ≤ 100 and no parallel edges out of s, both run in T = O((min(V, E) + 1)(V + E)) = O(V·E) time
for E ≥ 1, so T/(V²E) = O(1/V) → 0 as V → ∞ and T/(V·E²) = O(1/E) → 0 as E → ∞. So in this capacity range Dinic's
bound O(V²E) is not attained along any sequence of networks with V → ∞, and Edmonds–Karp's O(V·E²) along none with
E → ∞. On `generate_scaling` (G(n, 1/2), capacities 1..100, s = 0, t = n − 1, no parallel edges) both run in O(n³)
time.

*Proof.* (a) Each augmentation adds δ ≥ 1 to `flow`, which never exceeds F; the cost per iteration is as in
Theorem EK. (b) Every phase but the last augments at least once (B2) and adds at least 1 to the flow. Per phase the
cost is O(V + E + ℓ·A_p) with ℓ ≤ V − 1 (proof of DI), so the total is O((F + 1)(V + E) + V·F) ⊆ O((F + 1)(V + E)).
(c) F ≤ c({s}) by Lemma M(a), and c({s}) ≤ C·outdeg(s); without parallel edges the edges out of s go to distinct
vertices other than s, and each is one of the E edges. (d) By (a)-(c), T ≤ K·(min(V, E) + 1)(V + E) for a constant
K. If E ≤ V: (E + 1)(V + E) ≤ 2E·2V. If E > V: (V + 1)(V + E) ≤ 2V·2E. So T ≤ 4K·V·E, and T/(V²E) ≤ 4K/V,
T/(VE²) ≤ 4K/E. On `generate_scaling`, E ≤ n(n − 1), so T = O(n·n²). ∎

**Check.** `tests/test_proofs_maxflow.py`, class `FlowValueBounds`: the number of BFS passes of each implementation
is counted by replacing the name `deque` in the implementation's module with a counting subclass (the
implementation files are unchanged; each BFS creates one deque, so Edmonds–Karp makes A + 1 of them and Dinic one
per phase). It checks A ≤ F and A ≤ E(L + 1) for Edmonds–Karp, phases ≤ F + 1 and phases ≤ L + 1 for Dinic, and
F ≤ C·outdeg(s), on the validator's sizes (n = 2..10, 12, 14, 6 seeded instances each from the harness generator)
and on `generate_scaling` for n = 20, 40, 80 (where also F ≤ 100(n − 1)).

## 7. Notes: maximum bipartite matching as a unit-capacity flow

**Claim.** For a bipartite graph with sides X, Y, let N be the network with s → x (capacity 1) for x ∈ X, x → y
(capacity 1) for every edge xy, and y → t (capacity 1) for y ∈ Y. The maximum flow value of N equals the maximum
matching size, and the flow that either implementation computes (f_i = `cap[2i+1]` at return; the functions
return only its value) yields a maximum matching (the edges x → y with f = 1).

*Proof.* A matching M gives the flow sending 1 along s → x → y → t for each xy ∈ M, of value |M| (each x and y is
used once, so capacities hold). Conversely, the flow f computed by either implementation is integral (Invariant R
with integer δ), so f ∈ {0, 1} on every arc of N. A vertex x ∈ X receives at most 1 (from s), so at most one edge
x → y carries flow; a vertex y ∈ Y sends at most 1 (to t), so at most one edge into y carries flow. The edges
x → y with flow 1 therefore form a matching, of size |f| (the flow out of s crosses the cut {s} ∪ X exactly
through these edges). ∎

**Check.** `tests/test_proofs_maxflow.py`, class `BipartiteMatching`: both implementations on N equal a brute-force
maximum matching on 60 seeded random bipartite graphs with |X|, |Y| ≤ 5.

## 8. Correctness check

**Check.** `tests/test_proofs_maxflow.py`, class `Correctness`: both implementations equal the minimum over all s–t
cuts (enumerated in the test, independently of the harness) on 152 seeded networks with n = 2..9 from the harness
generator, including zero capacities, parallel and antiparallel edges and unreachable t. The validator's V1 run
(`python tools/validate.py pairs/max-flow-edmonds-karp-vs-dinic`, n = 2..10, 12, 14 with the cut-enumeration
oracle) checks the same on its battery.

## 9. The random family of `generate_scaling`

`generate_scaling(n, rng)` in `harness.py` runs over u = 0, …, n − 1 and, inside, v = 0, …, n − 1. For u ≠ v it
evaluates `rng.random() < 0.5` and, only if that holds, calls `rng.randint(1, 100)` and appends the edge (u, v) with
that capacity. It returns (n, 0, n − 1, edges), with the edges in the order of the loops.

**Model 𝔊ₙ.** Vertices 0, …, n − 1, s = 0, t = n − 1; every ordered pair (u, v) with u ≠ v is an edge independently
with probability ½, and its capacity is independent of everything else and uniform on {1, …, 100}.

**Assumption R (ideal random bits).** The successive values of `rng.random()` are independent and uniform on
{k·2⁻⁵³ : 0 ≤ k < 2⁵³}, the successive values of `rng.randint(1, 100)` are independent and uniform on {1, …, 100}, and
the two sequences are independent. This idealizes the Mersenne Twister generator behind `random.Random`, which is not
analysed here; the assumption is listed in the `background` field.

**Lemma G.** Under Assumption R, `generate_scaling(n, rng)` has the law 𝔊ₙ. Every instance, whatever the random
values, has no loops, no parallel edges (each ordered pair is visited once) and capacities in {1, …, 100}.

*Proof.* Each ordered pair (u, v), u ≠ v, uses its own call of `random()`, and it is an edge iff that value is < ½,
which has probability P(k < 2⁵²) = ½. A capacity is drawn only for an edge, by its own call of `randint`. Distinct
pairs use distinct calls, so the indicators are independent, and the capacities are independent of the indicators
and of each other. The structural facts hold because the loops visit each ordered pair u ≠ v exactly once. ∎

**Check.** `tests/test_proofs_maxflow.py`, class `RandomModel`: with a `random.Random` subclass that records every call,
`generate_scaling` makes exactly one `random()` call per ordered pair u ≠ v in loop order, a `randint(1, 100)` call
right after it exactly when the value is < ½, and returns exactly these edges with these capacities, s = 0 and t = n − 1
(n = 2, 3, 5, 10, 25, 60; 4 seeds each). It also checks, as a check of the premise on these seeds only, that every value
of `random()` is a multiple of 2⁻⁵³.

## 10. Separation on the random family

The separation uses three theorem notes of this repository, which prove their statements for exactly the model 𝔊ₙ
and for these two implementation files:
[max-flow-random-dense-trivial-min-cut](../../theorems/max-flow-random-dense-trivial-min-cut/) (Theorem 1 and the tail
inequalities A1–A4 of its appendix),
[max-flow-random-dense-dinic-short-residual-paths](../../theorems/max-flow-random-dense-dinic-short-residual-paths/)
(Lemmas 1–3, Theorems 4 and 5, Corollary 7), and
[max-flow-random-dense-edmonds-karp-cubic-reads](../../theorems/max-flow-random-dense-edmonds-karp-cubic-reads/)
(Theorems 1, 2 and 4).

**Reads.** For Edmonds–Karp, the executions of `v = to[e]` in its breadth-first search; for Dinic, the executions of
`v = to[e]` in its breadth-first search plus the executions of the first `e = arcs[it[u]]` (current-arc scans). Each
read is an elementary operation (section 0).

**Theorem S.** Let the network be drawn from 𝔊ₙ. For every n ≥ 21 793, with probability at least 1 − 5/n, both
(a) and (b) hold:

(a) Edmonds–Karp makes at least 0.011·n³ reads, so it runs at least 0.011·n³ elementary operations;
(b) Dinic makes at most 7 breadth-first searches and at most 26·n(n − 1) + 600(n − 1) ≤ 27·n² reads, and it runs in
O(n²) time (an absolute constant times n²).

On that event Edmonds–Karp makes at least (0.011/27)·n ≥ 4·10⁻⁴·n times as many reads as Dinic. On every instance of
the family (whatever the random values) both implementations run in O(n³) time (Theorem F).

*Proof.* By Lemma G, every instance has n vertices, no parallel edges and capacities in {1, …, 100}, which is the
setting of the deterministic theorems of the notes.

(a) Theorem 2 of the Edmonds–Karp note with p₁ = p₂ = 1/n: for every n ≥ 40 at which both factors of ℓ are
positive (every n ≥ 98), except with probability 2/n + B(n) ≤ 3/n (B(n) ≤ 1/n for n ≥ 40 by Theorem 1(b) of the
trivial-min-cut note), Edmonds–Karp makes at least ℓ(n)·n³ reads; ℓ is non-decreasing on that range and
ℓ(21 793) ≥ 0.0112. So for n ≥ 21 793 it makes at least 0.0112·n³ ≥ 0.011·n³ reads.

(b) Theorem 5 of the Dinic note with p = 1/n: for every n ≥ 21 793 the events 𝒫₁(k_s) and 𝒫₂(k_s + 1, ⌈n/2⌉) hold
except with probability 2/n. On them, Theorem 4 of that note bounds every residual s–t distance by 6, so (Corollary 7)
Dinic has at most 6 phases with t reachable, each with level[t] ≤ 6, and P ≤ 7 breadth-first searches, and its reads
are at most 26E + 600(n − 1) ≤ 26n(n − 1) + 600(n − 1); for n ≥ 600 this is ≤ 26n² + 600n ≤ 27n². For the time: by the
proof of Theorem DI, building the arrays costs O(V + E) and a phase with A_p augmentations and ℓ_p = level[t] costs
O(V + E + ℓ_p·A_p); the final search costs O(V + E). With at most 6 phases, ℓ_p ≤ 6 and Σ_p A_p ≤ F ≤ 100(n − 1)
(Theorem F), the total is O(7(V + E) + 6F) = O(n²), since V + E ≤ n².

The union of the two exceptional events has probability ≤ 3/n + 2/n = 5/n. On the complement,
0.011·n³ = (0.011/27)·n·27n² ≥ 4·10⁻⁴·n·(Dinic reads). The last sentence of the theorem is Theorem F(d). ∎

**Corollary S (Edmonds–Karp's worst case for capacities ≤ 100).** For every n ≥ 1000 there is a network with n
vertices, capacities in {1, …, 100} and no parallel edges on which Edmonds–Karp makes at least 0.0049·n³ reads. With
Theorem F, its worst-case running time over such networks with n vertices is Θ(n³).

*Proof.* By Theorem 2 of the Edmonds–Karp note (p₁ = p₂ = 1/n), the event "at least ℓ(n)·n³ reads" has probability at
least 1 − 3/n > 0 in 𝔊ₙ, and ℓ(n) ≥ ℓ(1000) ≥ 0.0049 for n ≥ 1000; every outcome of 𝔊ₙ is such a network. The upper
bound O(n³) is Theorem F(d) with E ≤ n(n − 1). ∎

**What is not proved.** No worst-case separation: over networks with capacities ≤ 100 and no parallel edges,
Dinic's proved worst-case bound is O(V·E) = O(n³) as well (Theorem F(d), E ≤ n(n − 1)), and over all networks the proved bounds are the
upper bounds O(V·E²) and O(V²·E); no lower bound for Dinic beyond the trivial one is proved. Theorem S says nothing
about n < 21 793, in particular nothing about the sizes at which the entry's tests and probe run (n ≤ 160), and it is
about the model 𝔊ₙ under Assumption R, not about the Mersenne Twister.

**Checks.** The probability bounds and constants of the notes are evaluated, with certified rounding, by their
`verify.py` scripts (`theorems/max-flow-random-dense-*/verify.py`), which also check every deterministic step on seeded
instances of `generate_scaling` against the unchanged implementations; the correspondence between the generator and
𝔊ₙ is checked by the class `RandomModel` (section 9). The class `MeasuredCounts` reproduces the measured counts quoted
in `entry.json` (verification) on the probe's instances; those counts are data, not part of the proof.
