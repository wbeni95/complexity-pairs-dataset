# Residual s–t distance at most 6, and Dinic in Θ(n²) reads, on the max-flow entry's random dense networks

> **Provenance: own extension.** Base: Motwani (1994), J. ACM 41(6), doi:10.1145/195613.195663, read in an author's
> copy. On random graphs it proves that "any non-maximum 0–1 flow admits a short augmenting path", and the same for
> k-factors, a network flow problem "where all edge capacities are non-negative integers which do not exceed k": every
> non-maximal k-sub-factor has an augmenting path of length at most 2L + 1 with L = c·ln n/ln Δ for some constant c > 0
> (its Theorem 9). It has no random capacities, no explicit distance bound such as 6 and no explicit failure
> probabilities. This note proves a statement of that kind for the entry's family, which has random integer capacities
> in {1, …, 100} on a dense random digraph: for every n ≥ 21 793, with probability at least 1 − 2/n, **every** feasible
> flow has residual s–t distance at most 6 or no residual s–t path at all. It gives explicit failure probabilities and
> the consequences for the entry's two implementations. What goes beyond the base is listed in
> [Literature](#literature).

## Setting

The pair [max-flow-edmonds-karp-vs-dinic](../../pairs/max-flow-edmonds-karp-vs-dinic/) implements Edmonds–Karp
(`implementations/edmonds_karp.py`) and Dinic (`implementations/dinic.py`) and defines the random instance family
`generate_scaling(n, rng)` in its `harness.py`; its tests and probe run both implementations on it. The model 𝔊ₙ, the notation M, m = n − 2, c(u, v), c(A, B), X, μ = E X = 101/4, a_v, b_v, c_out(s),
c_in(t), F, φ(θ) = E e^{−θX}, and the event 𝒞 are those of the note
[max-flow-random-dense-trivial-min-cut](../max-flow-random-dense-trivial-min-cut/). In short: every ordered pair is an
edge independently with probability ½, with a capacity uniform on {1, …, 100}; s = 0, t = n − 1. Probabilities are in
𝔊ₙ (ideal random bits). The tail inequalities A1–A3 are proved in the appendix of that note. E is the number of edges.

**The code.** Both implementations store edge i = (u, v, c) as arc 2i (u → v, capacity c) and arc 2i + 1 (v → u,
capacity 0), and `adj[u]` lists the arc ids at u in edge order. The current flow f is stored in the residual
capacities: arc 2i has residual c − f_i and arc 2i + 1 has residual f_i. The residual capacity from x to y is
r_f(x, y) = (c(x, y) − f(x, y)) + f(y, x). The residual graph G_f has an arc x → y iff r_f(x, y) > 0, and d_f(x, y) is
the distance in G_f (∞ if there is no path). A *feasible flow* satisfies 0 ≤ f ≤ c on every edge and conservation at
every vertex other than s and t; v(f) is its value.

- **Edmonds–Karp** repeats: a breadth-first search (BFS) from s over arcs with positive residual, which stops before
  the next dequeue as soon as t has a parent; then it pushes the bottleneck along the tree path to t.
- **Dinic** repeats phases: a full BFS from s computes `level[·]` (the distances in G_f); if t is reached, a
  depth-first search (DFS) with current-arc pointers `it[u]` pushes flow along *admissible* arcs (positive residual,
  level increasing by 1) and augments each time it reaches t. P is the number of BFS passes, including the final one
  that does not reach t.

**Cost measure.** Dinic *reads* = executions of `v = to[e]` in the BFS plus executions of
the first `e = arcs[it[u]]` (current-arc scans). Edmonds–Karp reads = executions of `v = to[e]` in its BFS.

## Statements

**Events.** For an integer k, 𝒫₁(k) is the event that κ⁺(v) ≥ k and κ⁻(v) ≥ k for every v ∈ M, with κ± from
Lemma 3(a) below (they depend only on the capacities at v). For integers x, y, 𝒫₂(x, y) is the event:

- *(forward)* for every partition (X, L, Y) of V with s ∈ X, t ∈ Y, |X| ≥ x and |Y| ≥ y:
  c(X, Y ∖ {t}) − c(L, X) > 100·(n − |X|);
- *(backward)* for every partition (Z, S, B) of V with s ∈ Z, t ∈ B, |B| ≥ x and |Z| ≥ y:
  c(Z ∖ {s}, B) − c(B, S) > 100·(n − |B|).

(L and S may be empty.) Both events are properties of the capacities only, not of any flow.

**Theorem 4 (deterministic).** Consider any network on the vertices 0, …, n − 1 (s = 0, t = n − 1) without parallel
edges and with integer capacities in {1, …, 100}. If it satisfies 𝒫₁(k) and 𝒫₂(k + 1, ⌈n/2⌉), then **every** feasible
flow f has d_f(s, t) ≤ 6 or d_f(s, t) = ∞.

**Theorem 5 (probability, analytic).** For n ≥ 4 and p ∈ (0, 1) let λ = √(((n − 1)/2)·ln(2m/p)),
k_s = ⌈(42/142)·(0.295·(n − 1) − λ)⌉, x = k_s + 1 and h = μ·x(x − 1) − 100n. If h > 0, then

    P(not 𝒫₁(k_s) or not 𝒫₂(x, ⌈n/2⌉)) ≤ p + 2n·2^{2n−3}·exp(−2h²/(10⁴·x·n)).

With p = 10⁻³ the right-hand side is **≤ 0.01 for every n ≥ 21 437** (and > 0.01 at n = 21 436). With p = 1/n it is
**≤ 2/n for every n ≥ 21 793**.

**Proposition 6 (computed bounds).** With the sharper lower bound for κ± and exact Chernoff bounds described in the
proof, the hypotheses of Theorem 4 fail with probability at most 0.002 + 2f₂, where f₂ is computed by `verify.py`
(ε rounded to four digits for display; log₁₀ f₂ rounded up):

| n | degrees in | ε | k | log₁₀ f₂ ≤ |
|---|---|---|---|---|
| 3000 | [1344, 1655] | 0.0882 | 320 | −53.88 |
| 4000 | [1818, 2181] | 0.0763 | 444 | −1133.47 |
| 5000 | [2295, 2704] | 0.0683 | 571 | −2873.36 |
| 10 000 | [4704, 5295] | 0.0485 | 1226 | −22233.38 |
| 20 000 | [9573, 10426] | 0.0345 | 2581 | −119197.53 |

So at these five n the failure probability is ≤ 0.002 + 2.6·10⁻⁵⁴ (at n = 3000, 2f₂ = 2.5988·10⁻⁵⁴). These are union
bounds evaluated by `verify.py` with certified rounding (see the proof), for exactly these n.

**Corollary 7 (the two implementations).** On the event of Theorem 4:

1. every augmenting path of Edmonds–Karp has at most 6 arcs;
2. Dinic makes P ≤ 7 BFS passes;
3. Dinic reads ≤ 4E(P − 1) + 2E + 6F ≤ 26E + 600(n − 1) ≤ 26·n(n − 1) + 600(n − 1).

Its first BFS reads 2E ≥ n(n − 1)/2 entries except with probability ≤ (n − 1)/2·(3/4)^{n−2} + e^{−n(n−1)/8}, which is
≤ 1/n for every n ≥ 40. Hence, **for every n ≥ 21 793, with probability at least 1 − 3/n,
n(n − 1)/2 ≤ Dinic reads ≤ 26·n(n − 1) + 600(n − 1)**: Dinic makes Θ(n²) reads with high probability.

**Theorem 8 (distance ≤ 8, for moderate n).** If 𝒫₁(k), 𝒫₂(k + 1, y₃) and 𝒫₂(n − y₃ + 1, ⌈n/2⌉) hold for some y₃,
then every feasible flow has d_f(s, t) ≤ 8 or ∞. On this event Edmonds–Karp's paths have at most 8 arcs, P ≤ 9, and
Dinic reads ≤ 34E + 800(n − 1). With the computation of Proposition 6 (failure ≤ 0.002 + 2f₂, f₂ now the sum of the two
forward 𝒫₂ terms), `verify.py` gives:

| n | 350 | 400 | 500 | 560 | 600 | 700 | 800 | 900 | 1000 | 1200 | 1500 | 2000 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k | 21 | 26 | 35 | 41 | 45 | 55 | 65 | 76 | 87 | 108 | 142 | 200 |
| y₃ | 263 | 300 | 375 | 420 | 435 | 508 | 580 | 653 | 700 | 870 | 1050 | 1400 |
| log₁₀ f₂ ≤ | −49.29 | −151.38 | −352.58 | −488.76 | −613.34 | −1048.20 | −1565.01 | −2261.04 | −2328.70 | −4758.79 | −6885.82 | −14154.69 |

So at each of these twelve n, with probability ≥ 0.998 − 1.1·10⁻⁴⁹, every residual s–t distance is ≤ 8 and Dinic makes
P ≤ 9 passes.

**Proposition 9 (phase structure).** (i) Dinic has a phase with level[t] = 1, and Edmonds–Karp an augmenting path of
length 1, iff (s, t) is an edge (probability ½). (ii) Both have length-2 paths except with probability (3/4)^m.
(iii) Both have length-3 paths except with probability ≤ 2·P(Bin(m, 299/800) < 0.3m) + 2^{−(0.3m)²}
≤ 2e^{−0.010878125·m} + 2^{−0.09m²}. Hence, for every n ≥ 21 793, with probability at least 1 − 3/n,

    P = 3 + 1[(s, t) ∈ E] + #(phases with level[t] ∈ {4, 5, 6}).

**Proposition 10 (the edge (s, t)).** On every network of the family, Dinic's list of phase lengths with the edge
(s, t) is [1] followed by its list without that edge, and Edmonds–Karp's sequence of augmenting paths with the edge is
s → t followed by its sequence without it. So P(G) = 1[(s, t) ∈ E] + P(G − (s, t)), and in 𝔊ₙ no value of P has
probability more than ½, for every n.

## Proof

### Lemma 1 (invariants of the implementations; every network with non-negative integer capacities)

(a) Every augmentation pushes an integer ≥ 1 along a simple s–t path of arcs with positive residual. No augmenting
path uses an arc whose head is s or whose tail is t. Hence f(y, s) = 0 and f(t, y) = 0 on every edge into s and every
edge out of t, at all times.

(b) Edmonds–Karp: d_f(s, x) never decreases for any x, so the lengths of its augmenting paths do not decrease, and
each augmenting path is a shortest s–t path of the current G_f.

(c) Dinic: in a phase with ℓ = level[t] ≥ 1 (where level[t] = d_f(s, t) at the start of the phase): every augmenting
path has exactly ℓ arcs; the phase ends; it augments at least once; at its end no s–t path of admissible arcs is left;
and the next phase has level[t] > ℓ or level[t] = −1. Within the phase, pointer increments (`it[u] += 1`) number at most
2E, scans = advances + skips, and advances = retreats + A_p·ℓ, where A_p is the number of augmentations of the phase.

*Proof.* (a) Edmonds–Karp reads its path from the parent pointers of one BFS; each vertex gets a parent at most once,
and s never gets one, so the path is simple, starts at s and ends at t. Dinic's DFS starts at s (level 0), follows
arcs that raise the level by 1 and augments as soon as it reaches t. In both cases no arc of the path ends at s, and
none leaves t. The flow on an edge (y, s) can grow only along its forward arc y → s, which is never used; the same
holds for edges (t, y). The pushed amount is a minimum of positive integer residuals.

(b) Let d be the distance function of G_f before an augmentation along a shortest path. Every arc x → y of G_f
satisfies d(y) ≤ d(x) + 1. After the augmentation the arcs of the new residual graph are arcs of G_f or reverses of
path arcs; a path arc x → y has d(y) = d(x) + 1, so its reverse y → x also satisfies d(x) ≤ d(y) + 1. So every arc of
the new residual graph satisfies the same inequality, and every distance from s is at least the old one. The BFS tree
path is a shortest path, so the path lengths do not decrease.

(c) Levels are fixed during the phase. An augmentation lowers the residuals of admissible arcs and raises those of
their reverses, which lower the level by 1, so an arc that is not admissible stays so for the rest of the phase. Call a
vertex *dead* if it has no admissible path to t; a dead vertex stays dead. *Invariant:* for every u, every arc of
`adj[u]` before position `it[u]` is inadmissible or leads to a dead vertex. The scan loop increments `it[u]` only past an
inadmissible arc. A retreat from w happens only when `it[w]` has reached the end of `adj[w]`, so w is dead by the
invariant (and w ≠ t, since the DFS augments at t); the retreat then increments `it[u]` past the arc u → w. That arc is
the one used for the advance, because between the advance and the retreat only vertices of higher level were visited
(a vertex cannot reappear deeper on a level-increasing path) and no augmentation occurred (an augmentation clears the
path). So the invariant holds. Each pointer stays ≤ |adj[u]|, so there are at most Σ_u |adj[u]| = 2E pointer
increments. Each scan ends with `break`, which is followed by an advance, or with a pointer increment (a skip). Each
advance puts one arc on the path, and each arc leaves it by a retreat or by an augmentation; an augmentation clears a
path from level 0 to level ℓ, that is, exactly ℓ arcs, and the path is empty when the phase ends. So advances =
retreats + A_p·ℓ, skips + retreats ≤ 2E, and A_p ≤ v(f) ≤ cap({s}) is finite: the phase ends. It ends when the path is
empty and `it[s]` is at the end of `adj[s]`, so s is dead: no admissible s–t path is left. At the start of the phase t
had a level, so an admissible s–t path existed; with no augmentation it would still exist, so the phase augments at
least once. Finally, let d be the levels of the phase (d = ∞ for vertices the BFS did not reach). At the start every
residual arc x → y satisfies d(y) ≤ d(x) + 1. The phase creates only reverses of path arcs, which go from level i + 1
to level i between reached vertices, so the inequality still holds at the end. Hence the new distance of t is ≥ ℓ. If it
were ℓ, a shortest path would use only arcs with d(y) = d(x) + 1 and positive residual, i.e. admissible arcs, which
contradicts the end of the phase. ∎

### Lemma 2 (ball inequalities; every network, every feasible flow)

(a) For i ≥ 1 let X = {v : d_f(s, v) ≤ i − 1}, L = {v : d_f(s, v) = i} and Y = V ∖ (X ∪ L). If t ∈ Y, then
c(X, Y) ≤ v(f) + f(L, X) ≤ F + c(L, X).
(b) For j ≥ 1 let B = {v : d_f(v, t) ≤ j − 1}, S = {v : d_f(v, t) = j} and Z = V ∖ (B ∪ S). If s ∈ Z, then
c(Z, B) ≤ v(f) + f(B, S) ≤ F + c(B, S).

*Proof.* (a) A residual arc x → y with x ∈ X would give d_f(s, y) ≤ i, so for x ∈ X and y ∈ Y, r_f(x, y) = 0, i.e.
f(x, y) = c(x, y) and f(y, x) = 0. Summing conservation over X (s ∈ X, t ∉ X) gives f(X, V ∖ X) − f(V ∖ X, X) = v(f).
Here f(V ∖ X, X) = f(L, X) + f(Y, X) = f(L, X) and f(X, V ∖ X) ≥ f(X, Y) = c(X, Y). Finally v(f) ≤ F (Lemma 0 of the
trivial-min-cut note) and f ≤ c. (b) is the mirror image: no residual arc goes from Z to B, so f = c on edges from Z to B
and f = 0 on edges from B to Z; the net flow into B is v(f); f(V ∖ B, B) ≥ c(Z, B) and f(B, V ∖ B) = f(B, S). ∎

### Lemma 3 (residual degree; every network without parallel edges, every feasible flow, every v ∉ {s, t})

Let N⁺_f(v) be the set of heads of residual arcs out of v and N⁻_f(v) the set of tails of residual arcs into v. Let
d⁺(v), d⁻(v) be the out- and in-degree of v.

(a) |N⁺_f(v)| ≥ κ⁺(v) := min_j max(d⁺(v) − j, i*(j)), where j runs over 0, …, d⁺(v) with σ(j) ≤ τ(d⁻(v)); σ(j) is the sum
of the j smallest out-capacities of v, τ(i) the sum of the i largest in-capacities, and i*(j) = min{i : τ(i) ≥ σ(j)}.
κ⁻(v) is defined with in- and out-capacities exchanged, and |N⁻_f(v)| ≥ κ⁻(v).
(b) For every integer c₀ ∈ [1, 100], κ⁺(v) ≥ (c₀/(100 + c₀))·h⁺_{c₀}(v) with h⁺_{c₀}(v) = #{w : c(v, w) ≥ c₀}; likewise for
κ⁻ with in-arcs.

*Proof.* (a) N⁺_f(v) contains the head of every out-edge that is not saturated and the tail of every in-edge with
positive flow. The heads of the out-edges are distinct, and so are the tails of the in-edges, because there are no
parallel edges; a head and a tail may coincide (antiparallel edges), hence the maximum below, not a sum. Let j be the number of saturated out-edges and
I⁺ the set of in-edges with positive flow. Out-flow ≥ σ(j) and in-flow ≤ τ(|I⁺|), and conservation makes them equal, so
j is feasible and |I⁺| ≥ i*(j). Thus |N⁺_f(v)| ≥ max(d⁺ − j, |I⁺|) ≥ κ⁺(v). (b) At least j − (d⁺ − h⁺) of the j smallest
out-capacities are ≥ c₀, so σ(j) ≥ c₀(j − d⁺ + h⁺), and τ(i) ≤ 100i. So every feasible j has i*(j) ≥ c₀(j − d⁺ + h⁺)/100,
and with z = d⁺ − j, max(z, c₀(h⁺ − z)/100) ≥ c₀h⁺/(100 + c₀). In-arcs: exchange the roles. ∎

### Theorem 4

Suppose 7 ≤ d := d_f(s, t) < ∞.

*Forward.* Let u be the second vertex of a shortest s–t path; u ∈ M. The set X₂ = {v : d_f(s, v) ≤ 2} contains u and
N⁺_f(u), and u ∉ N⁺_f(u), so |X₂| ≥ 1 + κ⁺(u) ≥ k + 1. Let L₃ = {v : d_f(s, v) = 3} and Y₃ = V ∖ (X₂ ∪ L₃); t ∈ Y₃
because d > 3. If |Y₃| ≥ ⌈n/2⌉, the forward half of 𝒫₂(k + 1, ⌈n/2⌉) gives c(X₂, Y₃ ∖ {t}) > c(L₃, X₂) + 100(n − |X₂|).
Since there are no parallel edges and capacities are ≤ 100, c_in(t) ≤ c(X₂, t) + 100·(|L₃| + |Y₃| − 1) =
c(X₂, t) + 100(n − |X₂| − 1). Adding, c(X₂, Y₃) > c(L₃, X₂) + c_in(t) + 100 > c(L₃, X₂) + F, which contradicts
Lemma 2(a) with i = 3. So |Y₃| ≤ ⌈n/2⌉ − 1, and X₃ = X₂ ∪ L₃ has |X₃| ≥ ⌊n/2⌋ + 1.

*Backward.* Let w be the second-to-last vertex of a shortest path; w ∈ M. B₂ = {v : d_f(v, t) ≤ 2} contains w and
N⁻_f(w), so |B₂| ≥ k + 1. Define S₃ = {v : d_f(v, t) = 3} and Z₃ = V ∖ (B₂ ∪ S₃); s ∈ Z₃. If |Z₃| ≥ ⌈n/2⌉, the backward
half of 𝒫₂ and c_out(s) ≤ c(s, B₂) + 100(n − |B₂| − 1) give c(Z₃, B₂) > c(B₂, S₃) + c_out(s) ≥ c(B₂, S₃) + F, which
contradicts Lemma 2(b) with j = 3. So B₃ = B₂ ∪ S₃ has |B₃| ≥ ⌊n/2⌋ + 1.

Now |X₃| + |B₃| ≥ 2⌊n/2⌋ + 2 > n, so some z has d_f(s, z) ≤ 3 and d_f(z, t) ≤ 3, and d ≤ 6: a contradiction. (The
argument uses only d ≥ 4, so it shows that a finite d ≥ 4 is ≤ 6.) Lemmas 2 and 3 hold for every feasible flow and the
events concern the capacities only, so the conclusion holds simultaneously for all feasible flows, in particular for
every intermediate flow of both implementations, whatever their tie-breaking. ∎

### Theorem 5

*𝒫₁.* By Lemma 3(b) with c₀ = 42, κ±(v) ≥ (42/142)·h±₄₂(v). An ordered pair is an edge of capacity ≥ 42 with
probability ½·59/100 = 59/200 = 0.295, independently, so h⁺₄₂(v) and h⁻₄₂(v) are Bin(n − 1, 0.295). By A3,
P(h < 0.295(n − 1) − λ) ≤ e^{−2λ²/(n−1)} = p/(2m) for each of the 2m variables. On the complement, every κ± is
≥ (42/142)(0.295(n − 1) − λ) and, being an integer, ≥ k_s. (The choice c₀ = 42 maximises (c₀/(100 + c₀))·(101 − c₀)/200
over c₀ = 1, …, 100; value 1239/14200 = 0.087254.)

*𝒫₂, forward half.* A partition with |X| = a and |Y| = b is fixed by choosing X ∖ {s} among the m middle vertices and
Y ∖ {t} among the remaining n − a − 1 of them, so there are at most Σ_a C(n − 2, a − 1)·2^{n−a−1} ≤ n·2^{2n−3}
partitions. For a fixed partition with ℓ = |L| = n − a − b, S = c(X, Y ∖ {t}) − c(L, X) is a sum over the a(b − 1) + aℓ =
a(n − a − 1) ≤ an distinct ordered pairs of X × (Y ∖ {t}) and L × X, with signs + and −; the terms are independent
with range 100. E S = μa(b − 1 − ℓ) = μa(2b − n + a − 1) ≥ μa(a − 1) because 2b ≥ n. Let f(a) = μa(a − 1) − 100n. If
f(a) > 0, A3 gives P(S ≤ 100(n − a)) ≤ P(S ≤ E S − f(a)) ≤ exp(−2f(a)²/(10⁴·a·n)). The function g(a) = f(a)²/a has
derivative f(a)·(μa(3a − 1) + 100n)/a², which is positive where f > 0, and f increases in a; so for every a ≥ x,
f(a) ≥ f(x) = h > 0 and g(a) ≥ g(x) = h²/x. So every partition with |X| ≥ x fails with probability
≤ exp(−2h²/(10⁴xn)). The backward half has the same distribution (reverse every ordered pair and exchange s and t).
Adding up gives the bound.

*Evaluation, 4 ≤ n ≤ 10⁶.* The claims are that the second summand 2n·2^{2n−3}·exp(−2h²/(10⁴xn)) is ≤ 0.009 for
p = 10⁻³ (total ≤ 0.01) and ≤ 1/n for p = 1/n (total ≤ 2/n). Since g increases where f > 0, the summand decreases when
x grows, so it suffices to evaluate it with any integer k ≤ k_s in place of k_s. `verify.py` does this for every integer
n from 4 to 10⁶ with exact integer arithmetic: each logarithm is replaced by an integer bound in units of 10⁻³⁰ (from a
correctly rounded 50-digit decimal value plus one unit; for k > 70 000, ln k is bounded above by its tangent at the
start k₀ of a block of 1000, ln k ≤ ln k₀ + (k − k₀)/k₀, since ln is concave). It takes the largest k with
A = 1239(n − 1) − 14200(k − 1) > 0 and 2A²·10³⁰ > 4200²·(n − 1)·L, where L·10⁻³⁰ ≥ ln(2m/p); this certifies
k − 1 < (42/142)(0.295(n − 1) − λ), so k ≤ k_s. With x = k + 1 and H = 4h = 101x(x − 1) − 400n > 0 it checks
H²·10³⁰ ≥ 8·10⁴·x·n·R, where R·10⁻³⁰ ≥ ln(2n) + (2n − 3) ln 2 + ln(1/0.009) (p = 10⁻³), respectively
≥ ln(2n) + (2n − 3) ln 2 + ln n (p = 1/n). This succeeds for every n ∈ [21 437, 10⁶] (p = 10⁻³; at n = 21 437, x = 1744)
and for every n ∈ [21 793, 10⁶] (p = 1/n; at n = 21 793, x = 1763). At n = 21 436 and p = 10⁻³ a 50-digit evaluation
gives k_s = 1742 (the real number inside the ceiling is 1741.9166…), x = 1743 and the value 0.0429… > 0.01.

*n > 10⁶.* With p = 10⁻³, 2m/p ≤ 2000n, so λ ≤ √((n/2)·ln(2000n)); with p = 1/n, 2m/p ≤ 2n², so λ ≤ √((n/2)·ln(2n²)).
In both cases λ/n decreases in n, and at n = 10⁶ it is ≤ 0.003273 (p = 10⁻³) and ≤ 0.003764 (p = 1/n). So
k_s ≥ (42/142)(0.295 − λ/n − 0.295/n)·n ≥ 0.0861n and x ≥ 0.08n. As g increases where f > 0 (here n > 632),
2h²/(10⁴xn) = 2g(x)/(10⁴n) ≥ 2g(0.08n)/(10⁴n) = (0.1616n − 102.02)²/400 ≥ 6.5·10⁻⁵n², while
ln(2n·2^{2n−3}) + ln n ≤ ln(2n) + 1.3863n + ln n. At n = 10⁶ the difference exceeds 6·10⁷, and it increases with n
(its derivative is ≥ 1.3·10⁻⁴n − 2/n − 1.3863 > 0). So the second summand is ≤ e^{−6·10⁷} ≤ min(0.009, 1/n) for every
n > 10⁶ as well. ∎

### Proposition 6 (computed bounds)

The same two events, with a sharper κ and exact Chernoff bounds:

- *Degrees.* With λ_d = √(((n − 1)/2)·ln(4m/p_deg)), every out- and in-degree of a middle vertex lies in
  [N_lo, N_hi] = [⌈(n − 1)/2 − λ_d⌉, ⌊(n − 1)/2 + λ_d⌋] except with probability ≤ 2m·2e^{−2λ_d²/(n−1)} = p_deg (A3).
- *Capacity samples.* Given the edge set, the capacities are i.i.d. uniform on {1, …, 100}. For each of the 2m samples
  (out-capacities and in-capacities of a middle vertex, of size N ≥ N_lo) and each c ∈ {1, …, 100}, the empirical
  distribution function F̂(c) is within ε of c/100 except with probability ≤ 2e^{−2N_lo·ε²} (A3), where
  ε = √(ln(400m/p_cdf)/(2N_lo)). The union over 2m samples and 100 values is ≤ p_cdf.
- *Order statistics.* On these events, the r-th smallest of N values is ≥ ⌈100(r/N − ε)⌉ ∨ 1 (if it equals c, then
  r/N ≤ F̂(c) ≤ c/100 + ε), and the r-th largest of N′ values, i.e. the q-th smallest with q = N′ − r + 1, is
  ≤ ⌈100(q/N′ + ε)⌉ ∧ 100 (at c = ⌈100(q/N′ + ε)⌉, F̂(c) ≥ c/100 − ε ≥ q/N′). Put these bounds into the min–max of
  Lemma 3(a): every j feasible for the true values is feasible for the bounds, and the bound for i*(j) can only drop.
  This gives a number k(N, N′) ≤ κ for a vertex with N out- and N′ in-arcs (and vice versa for κ⁻). k(N, N′) does not
  increase with N′ (for fixed i the i-th largest upper bound grows with N′, and there are more of them), so
  k = min_{N_lo≤N≤N_hi} k(N, N_hi) satisfies 𝒫₁(k) on these events. Thus 𝒫₁(k) fails with probability
  ≤ f₁ = p_deg + p_cdf = 0.002 (p_deg = p_cdf = 10⁻³). Any ε′ ≥ ε may be used in place of ε (the CDF event only gets
  larger).
- *𝒫₂(x, y).* For a partition with |X| = a, |Y| = b, S is a sum of a(b − 1) copies of X minus a(n − a − b) copies, all
  independent, so by A1, P(S ≤ 100(n − a)) ≤ e^{100(n−a)θ}·φ(θ)^{a(b−1)}·ψ(θ)^{a(n−a−b)} with ψ(θ) = E e^{θX}, for every
  θ ≥ 0. For fixed θ this decreases in b (each step multiplies by (φ(θ)/ψ(θ))^a ≤ 1), so the value at b = y bounds every
  b ≥ y. With Σ_b C(n − a − 1, b − 1) ≤ 2^{n−a−1}, the forward half fails with probability at most

      f₂ = min(1, Σ_{a=x}^{n−y} C(n − 2, a − 1)·2^{n−a−1}·e^{100(n−a)θ_a}·φ(θ_a)^{a(y−1)}·ψ(θ_a)^{a(n−a−y)}),

  for any choice of θ_a ≥ 0; the backward half has the same bound. `verify.py` takes θ_a by bisection on the derivative
  of the convex exponent and evaluates the sum in logarithms, with x = k + 1 and y = ⌈n/2⌉. Total: f₁ + 2f₂. ∎

*Evaluation.* `verify.py` computes λ_d and ε in 50-digit decimal arithmetic; N_lo and N_hi are exact because
(n − 1)/2 ∓ λ_d is more than 10⁻³⁰ away from an integer at every listed n. It rounds ε up to a double (ε′ ≥ ε) and
evaluates the order-statistic bounds with IEEE double +, −, ×, ÷ (each correctly rounded, so the absolute error of
100(r/N − ε′) is below 10⁻¹²), shifting by 10⁻⁹ downwards before each ceiling of a lower bound and upwards before each
ceiling of an upper bound; so the computed bounds are valid and k is a valid lower bound for κ. It sums f₂ in 50-digit
decimal arithmetic, with φ(θ) and ψ(θ) in closed form (geometric sums), with θ_a from a double-precision bisection
(any θ_a ≥ 0 is valid) converted exactly; the accumulated relative error is far below 10⁻²⁰, and the comparisons with
2.6·10⁻⁵⁴ (Proposition 6) and 1.1·10⁻⁴⁹ (Theorem 8) allow a relative margin of 10⁻²⁰. The table lists log₁₀ f₂ rounded
up to two decimals. Two further numerical facts are checked there (they are proved above, so these are checks only):
k(N, N′) is non-increasing in N′ (n = 400), and k(N, N′) never exceeds the exact κ of Lemma 3(a) on 1500 random capacity
samples.

### Corollary 7

(1) Each Edmonds–Karp path is a shortest s–t path of G_f for the current feasible flow (Lemma 1(b)), so it has at most
6 arcs by Theorem 4. (2) level[t] at the start of each non-final Dinic phase is d_f(s, t) ∈ {1, …, 6} and strictly
increases (Lemma 1(c)), so there are at most 6 non-final phases and P ≤ 7. (3) A non-final phase reads at most 2E in
its BFS (each reached vertex is scanned once) and at most 2E + A_p·ℓ_p in scans (scans = skips + retreats + A_p·ℓ_p by
Lemma 1(c)); the final BFS reads at most 2E. So reads ≤ 4E(P − 1) + 2E + Σ_p A_p·ℓ_p ≤ 24E + 2E + 6·Σ_p A_p, and
Σ_p A_p ≤ F ≤ c_out(s) ≤ 100(n − 1) (each augmentation adds ≥ 1). With E ≤ n(n − 1) this is the stated bound.

*Lower bound.* For a fixed v ≠ s, "no edge s → v" and, for each of the other n − 2 vertices w, "not both s → w and
w → v" are independent events with probabilities ½ and ¾, so v is at distance > 2 from s with probability
½·(3/4)^{n−2}; a union over the n − 1 targets bounds the probability that some vertex is unreachable. If every vertex is
reachable, the first BFS scans every adjacency list: 2E reads. E is Bin(n(n − 1), ½), and A3 gives
P(E < n(n − 1)/4) ≤ e^{−n(n−1)/8}. Both n·(n − 1)/2·(3/4)^{n−2} (the ratio of consecutive values is
(n + 1)/(n − 1)·¾ < 1 for n ≥ 8) and n·e^{−n(n−1)/8} decrease in n, and at n = 40 their sum is 0.01395 < 1; so the
failure probability of the lower bound is ≤ 1/n for every n ≥ 40. *With high probability.* For n ≥ 21 793, Theorem 5
with p = 1/n bounds the failure of the event of Theorem 4 by 2/n, so both bounds of (3) hold with probability
≥ 1 − 3/n. ∎

*Remark (classical bound).* Without the random-graph event, on every network of the family (no parallel edges,
capacities ≤ 100, E ≥ 1): P − 1 ≤ F (Lemma 1(c)) and ℓ_p ≤ n − 1, so reads ≤ 4EF + 2E + F(n − 1), and with F ≤ 100·min(n − 1, E)
this gives reads/(V²E) ≤ 4F/V² + 2/V² + F/(VE) ≤ 700/V. So, in reads, Dinic's worst-case O(V²E) bound is not attained
on any sequence of such networks with V → ∞.

### Theorem 8

As for Theorem 4, assuming 9 ≤ d < ∞. |X₂| ≥ k + 1. Lemma 2(a) with i = 3 and 𝒫₂(k + 1, y₃) give |Y₃| ≤ y₃ − 1, so
|X₃| ≥ n − y₃ + 1. With i = 4 (t ∈ Y₄ because d > 4) and 𝒫₂(n − y₃ + 1, ⌈n/2⌉), the same computation (now with X₃,
L₄, Y₄ and c_in(t) ≤ c(X₃, t) + 100(n − |X₃| − 1)) gives |Y₄| ≤ ⌈n/2⌉ − 1, so |X₄| ≥ ⌊n/2⌋ + 1. Backward in the same
way, |B₄| ≥ ⌊n/2⌋ + 1, so X₄ ∩ B₄ ≠ ∅ and d ≤ 8. The read bound follows as in Corollary 7: 4E·8 + 2E + 8F. Both halves
of both 𝒫₂ events are needed; the backward halves have the same bounds as the forward ones, so the failure probability
is ≤ f₁ + 2f₂ with f₂ the sum of the two forward terms. ∎

### Proposition 9

(i) The first BFS gives level[t] = 1 iff the arc s → t has positive residual, i.e. iff (s, t) is an edge; later phases
have level[t] ≥ 2 (Lemma 1(c)). Edmonds–Karp's first BFS finds t while scanning s iff (s, t) is an edge, and after that
augmentation the arc s → t has residual 0 for good (Lemma 1(a)). (ii) A length-2 path s → v → t exists iff some v ∈ M
has a_v, b_v > 0, which fails with probability (3/4)^m; the length-1 step changes only the arcs of (s, t).
(iii) *The length-2 stage.* The arcs on paths s → v → t are the forward arcs of (s, v) and (v, t); their reverses have
residual 0 (Lemma 1(a)), and only augmentations through v change them. Dinic's DFS in the phase with level[t] = 2 pushes
flow only when it reaches t, so its augmentations are exactly along such paths; Edmonds–Karp's length-2 augmentations
are such paths too. Each v with a_v, b_v > 0 carries one augmentation of min(a_v, b_v), after which one of its two arcs
is saturated for good, and the middle arcs are untouched. Afterwards r(s, u) > 0 iff a_u > b_u, and r(w, t) > 0 iff
b_w > a_w. With U = {u ∈ M : a_u > b_u} and W = {w ∈ M : b_w > a_w}, a length-3 path exists iff some edge goes from U
to W, and then the next Dinic phase (and the next Edmonds–Karp path) has length exactly 3. Each u is in U with
probability P(a_u > b_u) = 299/800, independently, so |U| and |W| are Bin(m, 299/800) (dependent on each other); U and W
are determined by the pairs at s and t, and the middle pairs are independent of them. So
P(no length-3 path) ≤ 2·P(Bin(m, 299/800) < 0.3m) + 2^{−(0.3m)²}, and A3 with u = (299/800 − 3/10)m gives
P(Bin(m, 299/800) < 0.3m) ≤ e^{−2(59/800)²m} = e^{−0.010878125m}. On the event of Theorem 4 together with the events of
(ii) and (iii), the phases are: [1 if (s, t) ∈ E], 2, 3, then phases of length 4–6, then the final BFS. For n ≥ 21 793
the event of Theorem 4 fails with probability ≤ 2/n (Theorem 5, p = 1/n), and (3/4)^m + 2e^{−0.010878125m} + 2^{−0.09m²}
≤ 1/n (`verify.py` evaluates n times this sum at n = 21 793: ≤ 4.92·10⁻⁹⁹; it decreases in n). So the formula for P holds
with probability ≥ 1 − 3/n. ∎

`verify.py` also evaluates the sharper bound in (iii), with the exact binomial tail: ≤ 0.367, ≤ 0.134 and
≤ 2.12·10⁻³ at n = 40, 100 and 400 (values rounded up).

### Proposition 10

Let G contain the edge (s, t) with capacity c₀ ≥ 1 and let G′ be G without it. *Dinic.* In phase 1 on G, level[t] = 1.
Along DFS paths the level rises by one, so t is reached only directly from s; every excursion through another level-1
vertex ends in retreats, and the only augmentation is along s → t, of size c₀. After phase 1 all arcs of G′ have their
initial residuals, s → t has residual 0 and t → s has residual c₀. By induction over phases: if all arcs of G′ have the
same residuals in both runs at the start of a phase, then the BFS levels coincide (the arc s → t has residual 0, and the
arc t → s points to s, which has level 0); the DFS makes the same advances, retreats and augmentations, because the extra
arc in `adj[s]` is never admissible (it only costs one scan) and `adj[t]` is never scanned by the DFS, while every other
adjacency list keeps the relative order of its arcs; so the residuals of G′'s arcs stay equal. The final BFS also
coincides. *Edmonds–Karp.* The first BFS on G scans all of `adj[s]`, gives t its parent through s → t, stops and pushes
c₀; in later BFSs the arc s → t has residual 0 and `adj[t]` is never scanned (each BFS stops before dequeuing t, or t is
unreachable), so the parent pointers coincide with those on G′. *Consequence.* In 𝔊ₙ the indicator 1[(s, t) ∈ E] is a
fair coin independent of G − (s, t), so P(P = c) = ½·P(P′ = c) + ½·P(P′ = c − 1) ≤ ½ for every c, where P′ = P(G − (s, t)). ∎

## Literature

- **Motwani (1994)**, J. ACM 41(6), 1329–1356. Read in an author's copy linked from the author's publication page (the
  publisher's PDF was not accessible): the abstract, the introduction and main results (§§1–1.2), the section on
  k-factors and the statements of Theorems 5–7 and 9–11. Abstract: "Our results show that in almost every graph, any
  non-maximum 0–1 flow admits a short augmenting path." Content: matchings (bipartite and general), k-factors and the
  permanent in random graphs; "The k-factor problem can be seen to be a special case of the network flow problem where all edge capacities
  are non-negative integers which do not exceed k"; Theorem 9: for every non-maximal k-sub-factor there is an
  augmenting path "of length at most 2L + 1, where L = c ln n/ ln Δ and c > 0 is some constant"; Dinic's algorithm for
  k-factors then terminates in O(m log n/log Δ) time (Corollaries 7–8). There are no random capacities, no constant
  distance bound and no explicit failure probabilities. A footnote says the paper is based on the author's PhD
  dissertation (1988), which could not be accessed. **Motwani (1989)**, STOC '89, the conference version (read in an
  archived copy of the publisher's PDF): it announces for "random 0-1 flow problem instances" that Dinic's algorithm
  terminates in almost linear time with high probability, and defers "the precise details of this result to the final
  version of the paper"; the journal version does not contain that section.
- **Karp, Motwani and Nisan (1993; report 1988)**: the abstract, an author's copy of the journal text and the pages of
  the report that were read (see the trivial-min-cut note) give linear-time algorithms and the trivial-cut phenomenon;
  they do not analyse the number of phases or the BFS work of Edmonds–Karp or Dinic (Dinic's algorithm appears only as
  an alternative inside one step of their algorithm).
- **What goes beyond the base**, as far as could be established from the parts read: (1) a dense random digraph with
  random integer capacities in {1, …, 100}, where the base treats 0-1 flows and k-factor networks (fixed capacities at
  most k) on random graphs; (2) an explicit distance bound, 6 (and 8 under weaker events), for every feasible
  flow, where the base gives 2L + 1 with L = c·ln n/ln Δ and an unspecified constant c; (3) explicit failure
  probabilities: analytic for every n ≥ 21 437 (≤ 0.01) and every n ≥ 21 793 (≤ 2/n), and computed at the listed n;
  (4) the consequences for the entry's implementations: P ≤ 7, reads ≤ 26E + 600(n − 1), n(n − 1)/2 ≤ reads with
  explicit failure probability; (5) the phase structure (Propositions 9 and 10).
- Credit: the algorithms are due to Edmonds and Karp (1972) and Dinic (1970). Lemmas 1(b) and 1(c) are proved above
  for the entry's code. Of Edmonds and Karp (1972) only the abstract and Section 2.1 were read; Dinic (1970) was not
  accessible.

## Scope

- The family `generate_scaling` (model 𝔊ₙ, ideal random bits; the Mersenne Twister is not analysed). Theorem 4, the
  deterministic implication of Theorem 8, Lemmas 1–3 and Proposition 10 (its first sentence) are deterministic;
  Theorem 5, Proposition 6, the probability statements of Corollary 7, Theorem 8 and Proposition 9, and the last
  sentence of Proposition 10 are about 𝔊ₙ.
- Explicit guarantees: failure ≤ 0.01 for every n ≥ 21 437 (Theorem 5, p = 10⁻³) and ≤ 2/n for every n ≥ 21 793
  (p = 1/n); Dinic's read bounds and the formula for P with probability ≥ 1 − 3/n for every n ≥ 21 793; ≤ 0.002 +
  2.6·10⁻⁵⁴ at the five n of Proposition 6; distance ≤ 8 with failure ≤ 0.002 + 1.1·10⁻⁴⁹ at the twelve n of Theorem 8.
  No bound on the probability of the events of Theorems 4 and 8 is claimed for n < 350, or for n below 21 437 other
  than the listed values; Corollary 7 (the lower-bound tail, n ≥ 40), Proposition 9 (ii)–(iii) and Proposition 10 hold
  at the n they state.
- The bound 6 is not claimed to be sharp.
- All cost statements are in the reads measure defined above; running time is not analysed.

## Verification

```bash
python theorems/max-flow-random-dense-dinic-short-residual-paths/verify.py            # about a minute
python theorems/max-flow-random-dense-dinic-short-residual-paths/verify.py --full     # about 2.5 min (larger instances)
```

Deterministic (fixed seeds), standard library only, no network; exit code 0 only if every check passes. The script
loads the entry's `harness.py` and both implementations unchanged. It checks:

- the exact constants (c₀ = 42, 59/200, 299/800, 2(59/800)² = 0.010878125) with fractions; the reachability probability
  ½·(3/4)^{n−2} and Proposition 9(ii)'s (3/4)^m by exhaustive enumeration of all digraphs on 3 and 4 vertices and of all
  edge sets at s and t for m ≤ 6; the values of the bound of Proposition 9(iii) at n = 40, 100, 400; and the two explicit
  rates used for "1 − 3/n" (at n = 40 and n = 21 793);
- Theorem 5, certified in exact integer arithmetic (logarithms bounded in units of 10⁻³⁰), at every n from 4 to 10⁶ for
  p = 10⁻³ (threshold 21 437) and p = 1/n (threshold 21 793); the value at n = 21 436; the numbers of the argument for
  n > 10⁶;
- every value in the tables of Proposition 6 and Theorem 8 (certified: exact N_lo, N_hi and k, decimal sums for f₂), the
  bounds 2.6·10⁻⁵⁴ and 1.1·10⁻⁴⁹, that the platform's floats are IEEE binary64, the monotonicity of k(N, N′) in N′
  (n = 400), and k(N, N′) ≤ κ on 1500 random samples;
- that its instrumented copies of both implementations reproduce the line-execution counts of the unchanged code
  (`sys.settrace`) on 12 seeded instances (n = 10–40), and that their flow values equal those of the unchanged code on
  every simulated instance;
- on 605 seeded instances (n = 20, 40, 80, 160; with `--full` also 70 instances with n = 240, 320, 400): Lemma 1
  (no flow into s or out of t, levels, path lengths, at least one augmentation per phase, the per-phase counts),
  Lemma 0(ii) of the trivial-min-cut note at the end of Dinic, Lemmas 2
  and 3 and the |X₂| step of Theorem 4 at every Dinic phase start, the read bound of Corollary 7 and the bounds of the
  remark after it, Proposition 9's characterisation of the phases of lengths 1, 2 and 3 and the decomposition of P, and
  the identity of Proposition 10 (each instance with the edge (s, t) toggled);
- the partition-level step of Theorem 4 at every Dinic phase start with 4 ≤ d_f(s, t) < ∞ (349 phase starts in the
  default run): for the actual partition (X₂, L₃, Y₃) of the flow, c(X₂, Y₃ ∖ {t}) − c(L₃, X₂) ≤ 100(n − |X₂|), and the backward mirror
  c(Z₃ ∖ {s}, B₂) − c(B₂, S₃) ≤ 100(n − |B₂|); these follow from Lemma 2 and the bound on c_in(t) (resp. c_out(s)) used
  in the proof, so the 𝒫₂ inequality fails for every such partition;
- Lemmas 2 and 3 on 108 random feasible flows that neither algorithm produces (random Ford–Fulkerson prefixes, and
  Edmonds–Karp prefixes or maximum flows followed by random residual cycles).

Each instance-level statement is printed with its number of cases, zeros included; a statement listed above fails if
it never occurs (in part R the two steps of Theorem 4 are only reported, as no random flow need reach d ≥ 3 or 4).
The event 𝒫₂(x, y) quantifies over exponentially many partitions of V, so the events cannot be checked on instances,
and Theorems 4 and 8 themselves are not checked on instances. The script checks every lemma and step they use, and computes
their probability bounds (Theorem 5, Proposition 6, Theorem 8).

## Sources

- R. Motwani (1994). *Average-case analysis of algorithms for matchings and related problems*. Journal of the ACM 41(6),
  1329–1356. [doi:10.1145/195613.195663](https://doi.org/10.1145/195613.195663). Base. Read in an author's copy (the
  parts listed in [Literature](#literature)).
- R. Motwani (1989). *Expanding graphs and the average-case analysis of algorithms for matchings and related problems*.
  Proceedings of the 21st Annual ACM Symposium on Theory of Computing (STOC '89), 550–561.
  [doi:10.1145/73007.73060](https://doi.org/10.1145/73007.73060). Read (archived copy of the publisher's PDF).
- R. M. Karp, R. Motwani, N. Nisan (1993). *Probabilistic analysis of network flow algorithms*. Mathematics of
  Operations Research 18(1), 71–97. [doi:10.1287/moor.18.1.71](https://doi.org/10.1287/moor.18.1.71). Abstract and an
  author's copy of the journal text read; the 1988 report version partly read (pages listed in the trivial-min-cut
  note).
- J. Edmonds, R. M. Karp (1972). *Theoretical improvements in algorithmic efficiency for network flow problems*. Journal
  of the ACM 19(2), 248–264. [doi:10.1145/321694.321699](https://doi.org/10.1145/321694.321699). Credit for the
  algorithm; only the abstract and Section 2.1 were read.
- E. A. Dinic (1970). *Algorithm for solution of a problem of maximum flow in a network with power estimation*. Soviet
  Mathematics Doklady 11, 1277–1280. Credit for the algorithm; not accessible.
- The tail inequalities (Chernoff 1952, Hoeffding 1963) are proved in the appendix of the
  [trivial-min-cut note](../max-flow-random-dense-trivial-min-cut/#appendix-tail-inequalities-and-sperners-theorem).
