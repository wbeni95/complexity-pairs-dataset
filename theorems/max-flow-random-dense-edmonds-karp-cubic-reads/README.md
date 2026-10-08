# Edmonds–Karp makes Θ(n³) reads with high probability on the max-flow entry's random dense networks

> **Provenance: own result.** A documented literature search found no analysis of the breadth-first-search work of
> the Edmonds–Karp algorithm on dense random networks with random capacities. The sources checked are listed in
> [Literature search](#literature-search). This is a statement about that search, not a claim of priority.

## Setting

The pair [max-flow-edmonds-karp-vs-dinic](../../pairs/max-flow-edmonds-karp-vs-dinic/) implements Edmonds–Karp
(`implementations/edmonds_karp.py`) and defines the random instance family `generate_scaling(n, rng)` in its
`harness.py`. The model 𝔊ₙ (every ordered
pair is an edge independently with probability ½, with a capacity uniform on {1, …, 100}; s = 0, t = n − 1; ideal
random bits), the notation M, m = n − 2, c(u, v), X, μ = E X = 101/4, a_v = c(s, v), b_v = c(v, t), c_out(s), c_in(t),
F, and the event 𝒞 with its probability bound B(n) are those of the note
[max-flow-random-dense-trivial-min-cut](../max-flow-random-dense-trivial-min-cut/); the tail inequalities A1–A3 are
proved in its appendix. The residual graph G_f, the code conventions and Lemma 1 (invariants of the implementations)
are those of the note [max-flow-random-dense-dinic-short-residual-paths](../max-flow-random-dense-dinic-short-residual-paths/).

The Edmonds–Karp code repeats a breadth-first search (BFS) from s over arcs with positive residual: `queue = deque([s])`;
`while queue and parent_edge[t] == -1:` dequeue u and run `for e in adj[u]: v = to[e]; …`, giving v the parent arc e and
enqueuing it if the arc has positive residual and v has no parent yet. The loop over `adj[u]` has no `break`, and the
early exit is tested only before a dequeue. If t got a parent, the code pushes the bottleneck along the tree path.

**Cost measure.** *Reads* = executions of `v = to[e]` in the BFS. A = number of augmentations (there are A + 1 BFS
passes). |adj[v]| = outdeg(v) + indeg(v) (the code stores one arc per edge endpoint), δ_M = min_{v∈M} |adj[v]|,
Φ₂ = Σ_{v∈M} min(a_v, b_v), D = F − c(s, t) − Φ₂, and μ′ = E(a_v − b_v)⁺ = 13433/800 = 16.79125 (exact; a_v, b_v
independent copies of X).

## Statements

**Theorem 1 (deterministic).** On every network on the vertices 0, …, n − 1 (s = 0, t = n − 1) without parallel edges
and with integer capacities in {1, …, 100}, D ≥ 0 and Edmonds–Karp makes at least δ_M·D²/20000 reads.

**Theorem 2 (tail bound).** Let n ≥ 4 and p₁, p₂ ∈ (0, 1), and put y = √((n − 1)·ln(m/p₁)) and
x = √(10⁴·m·ln(2/p₂)/2). With probability at least 1 − p₁ − p₂ − B(n),

    reads ≥ (n − 1 − y)·(μ′m − x)²/20000      (when μ′m > x and n − 1 > y).

**With p₁ = p₂ = 1/n:** for every n ≥ 40, with probability at least 1 − 3/n, reads ≥ ℓ(n)·n³, where

    ℓ(n) = (1 − 1/n − √(2 ln n/n))·(μ′(1 − 2/n) − √(5000 ln(2n)/n))²/20000

whenever both brackets are positive (every n ≥ 98). ℓ is non-decreasing on that range and tends to
μ′²/20000 = 180445489/12800000000 = 0.0140973…; ℓ(1000) ≥ 0.0049 and ℓ(21 793) ≥ 0.0112. In particular, **for every n ≥ 1000, with probability at least
1 − 3/n, Edmonds–Karp makes at least 0.0049·n³ reads.**

Values for p₁ = p₂ = 0.01 (so with probability ≥ 0.98 − B(n)), computed by `verify.py` and rounded down:

| n | δ_M > | D > | reads ≥ | as a multiple of n³ |
|---|---|---|---|---|
| 400 | 333.9 | 3435.8 | 1.971·10⁵ | 0.00308 |
| 800 | 704.0 | 8801.5 | 2.726·10⁶ | 0.00532 |
| 1200 | 1080.5 | 14482.3 | 1.133·10⁷ | 0.00655 |
| 2000 | 1842.8 | 26273.6 | 6.360·10⁷ | 0.00795 |
| 10⁴ | 9627.3 | 151604.3 | 1.106·10¹⁰ | 0.01106 |
| 10⁵ | 98729.4 | 1627621.9 | 1.307·10¹³ | 0.01307 |

**Corollary 3 (many long BFS passes).** In the setting of Theorem 1 with D ≥ 200, at least ⌊D/200⌋ + 1 BFS passes each
dequeue at least 1 + D/200 vertices. In 𝔊ₙ, let x be as in Theorem 2 with p₂ = 1/n and z = √(5000(n − 1) ln n). For
every n ≥ 40 with μ′m − x ≥ 200, with probability at least 1 − 3/n, more than a fraction
(μ′m − x)/(200(μ(n − 1) + z + 1)) of all BFS passes dequeue more than 1 + (μ′m − x)/200 vertices. Divided by 1 and by n
respectively, these two bounds tend to μ′/(200μ) = 13433/4040000 = 0.003325 and μ′/200 = 13433/160000 = 0.08395625.

**Theorem 4 (upper bound; every network with non-negative integer capacities).** A ≤ F and reads ≤ 2E·(A + 1) ≤
2E·(F + 1), where E is the number of edges. On every network of the family (no parallel edges, capacities ≤ 100),
F ≤ 100(n − 1), so reads ≤ 2E·(100(n − 1) + 1) ≤ 2n(n − 1)(100n − 99).

Together, Theorems 2 and 4 give: **for every n ≥ 1000, with probability at least 1 − 3/n,
0.0049·n³ ≤ Edmonds–Karp reads ≤ 200·n³** on this family. By the
[Dinic note](../max-flow-random-dense-dinic-short-residual-paths/) (Corollary 7), for every n ≥ 21 793, with
probability at least 1 − 3/n, n(n − 1)/2 ≤ Dinic reads ≤ 26·n(n − 1) + 600(n − 1) on the same family.

## Proof

### Theorem 1

*(i) Stages.* By Lemma 1(b) of the Dinic note the augmenting paths come in order of length. *Length 1:* only the arc
s → t can form such a path, because the reverse arc of an edge (t, s) has residual f(t, s) = 0 (Lemma 1(a)). If the edge
(s, t) exists, the first BFS finds t while scanning s (it scans all of `adj[s]`) and pushes c(s, t), which saturates the
arc for good. *Length 2:* a path s → v → t with v ∈ M uses the forward arcs of (s, v) and (v, t); their reverses have
residual f(v, s) = f(t, v) = 0. Only augmentations through v change these two arcs. The first one pushes
min(a_v, b_v) and saturates one of them, which cannot recover (that would need flow on an arc whose head is s or whose
tail is t). So the augmentations of length ≤ 2 push exactly c(s, t) + Φ₂, and the remaining augmentations, τ = 1, …, N
in order, all have length ≥ 3 and push D = F − c(s, t) − Φ₂ ≥ 0 in total (the final flow value is F, Lemma 0 of the
trivial-min-cut note).

*(ii) One BFS before an augmentation of length ≥ 3.* Let U_τ = {y : r_f(s, y) > 0} before augmentation τ. The BFS
dequeues s and scans `adj[s]`. The arcs out of s are the forward arcs of edges (s, y) and the reverse arcs of edges
(y, s), whose residual is 0; so the scan enqueues exactly U_τ, each vertex once. t ∉ U_τ, and no vertex of U_τ has a
residual arc to t, since the residual distance of t is ≥ 3. The queue is first in, first out, so the vertices of U_τ
are dequeued next; while they are scanned t gets no parent and the queue is not empty, so every vertex of U_τ is
dequeued and its whole list is read. Hence this BFS makes at least |adj[s]| + Σ_{u∈U_τ} |adj[u]| ≥ δ_M·|U_τ| reads
(U_τ ⊆ M because r(s, t) = 0 after stage 1).

*(iii) The size of U_τ.* R_τ := Σ_y r_f(s, y) = c_out(s) − v(f) before augmentation τ, by Lemma 1(a). Without parallel
edges each r_f(s, y) ≤ c(s, y) ≤ 100, so |U_τ| ≥ R_τ/100. R_1 = R_end + D with R_end = c_out(s) − F ≥ 0, and
R_τ − R_{τ+1} = b_τ ∈ [1, 100], the bottleneck of augmentation τ (it is at most the residual of the first arc).

*(iv) Summation.* Σ_τ R_τ = N·R_end + Σ_σ σ·b_σ, and Σ_σ σ·b_σ = Σ_{k=0}^{N−1} (D − B(k)) with B(k) = Σ_{σ≤k} b_σ ≤ 100k.
Every term D − B(k) is ≥ 0. Let q = ⌈D/100⌉ ≤ N (as D ≤ 100N). Then

    Σ_σ σ·b_σ ≥ Σ_{k=0}^{q−1} (D − 100k) = qD − 50q(q − 1) = D²/200 + 50q − (100q − D)²/200 ≥ D²/200,

because 0 ≤ 100q − D < 100 (for D = 0 the claim is trivial). So Σ_τ |U_τ| ≥ Σ_τ R_τ/100 ≥ D²/20000, and the reads are
at least δ_M·D²/20000. ∎

### Theorem 2

|adj[v]| is a sum over the 2(n − 1) distinct ordered pairs (v, w), (w, v), so it is Bin(2(n − 1), ½). By A3,
P(|adj[v]| ≤ n − 1 − y) ≤ e^{−y²/(n−1)} = p₁/m; a union over M gives δ_M > n − 1 − y with probability ≥ 1 − p₁. On 𝒞,
F = min(c_out(s), c_in(t)) (Theorem 1 of the trivial-min-cut note); the term c(s, t) cancels, and with
a − min(a, b) = (a − b)⁺,

    D = min(Σ_M a_v, Σ_M b_v) − Σ_M min(a_v, b_v) = min(Σ_M (a_v − b_v)⁺, Σ_M (b_v − a_v)⁺).

The pairs (a_v, b_v), v ∈ M, are independent, so each of the two sums has m independent terms in [0, 100] with mean
μ′. By A3, each sum is ≤ μ′m − x with probability ≤ e^{−2x²/(10⁴m)} = p₂/2. Put both bounds into Theorem 1. For the limit
take p₁ = p₂ = 1/n. Then y² = (n − 1)·ln(mn) ≤ 2n ln n and x² = 5000·m·ln(2n) ≤ 5000·n·ln(2n), so
n − 1 − y ≥ n(1 − 1/n − √(2 ln n/n)) and μ′m − x ≥ n(μ′(1 − 2/n) − √(5000 ln(2n)/n)); when both are positive the
bound is ≥ ℓ(n)·n³. The failure probability is ≤ 2/n + B(n) ≤ 3/n for n ≥ 40, because B(n) ≤ 1/n for every n ≥ 40
(trivial-min-cut note, Theorem 1(b)). The functions ln n/n (n ≥ 3) and ln(2n)/n (n ≥ 2) decrease, so both brackets of
ℓ increase with n; once positive they stay positive, and ℓ, a product of positive non-decreasing factors, is
non-decreasing, with limit μ′²/20000. `verify.py` evaluates ℓ(1000) = 0.004945… and ℓ(21 793) = 0.011237… in 50-digit
decimal arithmetic (square roots rounded up). The upper bound 200n³ is Theorem 4: 2n(n − 1)(100n − 99) ≤ 200n³. The
value μ′ = 13433/800 is a finite sum over the two independent copies of X. ∎

### Corollary 3

For τ ≤ ⌊D/200⌋ + 1, R_τ ≥ R_1 − 100(τ − 1) ≥ R_end + D − 100⌊D/200⌋ ≥ R_end + D/2, so |U_τ| ≥ D/200, and that pass
dequeues s and U_τ. These passes exist because N ≥ D/100 ≥ ⌊D/200⌋ + 1 when D ≥ 200. *In 𝔊ₙ.* By the proof of
Theorem 2 (p₂ = 1/n), D > μ′m − x except with probability 1/n + B(n). c_out(s) is a sum of n − 1 independent terms in
[0, 100] with mean μ, so by A3, c_out(s) < μ(n − 1) + z except with probability e^{−2z²/(10⁴(n−1))} = 1/n. On these
events, with μ′m − x ≥ 200, at least ⌊D/200⌋ + 1 > D/200 > (μ′m − x)/200 passes dequeue more than
1 + (μ′m − x)/200 vertices, and there are A + 1 ≤ F + 1 ≤ c_out(s) + 1 < μ(n − 1) + z + 1 passes (Theorem 4). The
failure probability is ≤ 2/n + B(n) ≤ 3/n for n ≥ 40. Since x and z are O(√(n log n)), the two bounds divided by 1 and
by n tend to μ′/(200μ) = 13433/4040000 = 0.003325 and μ′/200 = 13433/160000 = 0.08395625. ∎

### Theorem 4

Each augmentation adds at least 1 to the flow (Lemma 1(a) of the Dinic note), so A ≤ F. In one BFS every vertex is
enqueued at most once (its parent is set before it is enqueued), so its list is read at most once: at most
Σ_v |adj[v]| = 2E reads per BFS, and there are A + 1 of them. On the family, F ≤ c_out(s) ≤ 100·outdeg(s) ≤ 100(n − 1),
and E ≤ n(n − 1). ∎

*Remark (classical bound).* On every network with integer capacities ≤ 100 and E ≥ 1, F ≤ c_out(s) ≤ 100E, so
reads/(V·E²) ≤ 2(F + 1)/(V·E) ≤ 202/V. In reads, Edmonds–Karp's worst-case O(V·E²) bound is therefore not attained on
any sequence of such networks with V → ∞.

## Literature search

The algorithm is due to Edmonds and Karp (1972). The search looked for analyses of its running time, number of
augmentations or BFS work on random networks, and for results on maximum flows in random networks with random
capacities. Bibliographic databases: Crossref, OpenAlex and arXiv, with topic keywords (probabilistic analysis of
network flow algorithms; maximum flow on random graphs and augmenting paths; average-case running time of Edmonds–Karp
on random networks; flow in networks with random capacities; maximal flow through a directed graph with random
capacities; Edmonds–Karp or Dinic with random inputs). What was found and read:

- Karp, Motwani and Nisan (1993), abstract and an author's copy of the journal text, and their 1988 report, pp. 3–5,
  10, 24–27 and 29: linear-time algorithms for maximum flow and transportation problems with random capacities, and the
  trivial minimum cut. No analysis of Edmonds–Karp.
- Motwani (1994), author's copy (abstract, §§1–1.2, the k-factor section, the main theorems), and Motwani (1989), full
  conference text: short augmenting paths for 0-1 flows, matchings and k-factors in random graphs; Dinic's algorithm
  for these problems. No analysis of Edmonds–Karp's BFS work on networks with random capacities.
- Grimmett and Welsh (1982), §§1 and 3; Grimmett and Suen (1982), in full: limit theorems for the maximum flow value.
- Khandwawala and Sundaresan (2010), abstract: multicommodity flow on the complete graph with i.i.d. capacities.
- Waissi (1991), in full: a class of acyclic networks on which Dinic's algorithm attains its worst-case bound.
  Naparstek and Leshem (2014), preprint version: the expected time of the auction algorithm for bipartite matching on
  random graphs.
- Title only: Zadeh (1972), on the efficiency of the Edmonds–Karp algorithm.

None of the material read states a lower bound on the BFS work, the number of augmentations or the number of dequeued
vertices of Edmonds–Karp on dense random networks with random capacities. The full text of Zadeh (1972) could not be
accessed.

## Scope

- Theorem 1 and Theorem 4 are deterministic. Theorem 2 and Corollary 3 are about the model 𝔊ₙ with ideal random bits
  (the Mersenne Twister is not analysed). Theorem 2 in its general form holds for every n ≥ 4 (it gives nothing where
  B(n) ≥ 1, in particular n ≤ 21), and the explicit 1 − 3/n statements start at n = 40 (the ℓ(n) bound is non-trivial
  from n = 98 on), with 0.0049·n³ from n = 1000 and the comparison with Dinic from n = 21 793.
- The constant 0.0140973 is a proved lower-bound constant, not claimed to be the true asymptotic constant of the reads.
- All cost statements are in the reads measure defined above; running time is not analysed.
- Nothing is claimed for other edge densities or capacity laws.

## Verification

```bash
python theorems/max-flow-random-dense-edmonds-karp-cubic-reads/verify.py            # about 10 s
python theorems/max-flow-random-dense-edmonds-karp-cubic-reads/verify.py --full     # adds n = 240, 320, 400 (about 80 s)
```

Deterministic (fixed seeds), standard library only, no network; exit code 0 only if every check passes. The script
loads the entry's `harness.py` and both implementations unchanged. It checks:

- the exact constants μ = 101/4, μ′ = 13433/800 (enumeration of all pairs of capacities), μ′²/20000, μ′/(200μ) and μ′/200
  with fractions;
- every value of the table of Theorem 2 as a lower bound (50-digit decimal, square roots rounded up), the two Hoeffding
  identities behind y and x, ℓ(1000) ≥ 0.0049 and ℓ(21 793) ≥ 0.0112 (and, as a check, monotonicity of ℓ on a grid);
- that its instrumented copy of Edmonds–Karp reproduces the line-execution counts of the unchanged code
  (`sys.settrace`: BFS passes, dequeues, reads, augmentations) on 12 seeded instances (n = 10–40), and that its flow
  value equals that of the unchanged Edmonds–Karp and Dinic on every simulated instance;
- on 630 seeded instances (n = 20, 40, 80, 160; with `--full` also 72 instances with n = 240, 320, 400): the stages of
  lengths 1 and 2 (counts and pushed amounts), D ≥ 0, every step of Theorem 1 in every pass of length ≥ 3 (R = c_out(s) −
  v(f) read from the arcs, |U| ≥ R/100, dequeues ≥ |U| + 1, reads ≥ |adj[s]| + Σ_U |adj|, bottleneck in [1, 100]) and the
  whole chain per instance, the formula for D on the instances with F = min(c_out(s), c_in(t)), Corollary 3 on the
  instances with D ≥ 200, and the bounds of Theorem 4 and of the remark after it. Each statement is printed with its
  number of cases, zeros included, and fails if it never occurs.

## Sources

- J. Edmonds, R. M. Karp (1972). *Theoretical improvements in algorithmic efficiency for network flow problems*.
  Journal of the ACM 19(2), 248–264. [doi:10.1145/321694.321699](https://doi.org/10.1145/321694.321699). Credit for the
  algorithm. Only the abstract and Section 2.1 were read.
- R. M. Karp, R. Motwani, N. Nisan (1993). *Probabilistic analysis of network flow algorithms*. Mathematics of
  Operations Research 18(1), 71–97. [doi:10.1287/moor.18.1.71](https://doi.org/10.1287/moor.18.1.71). Abstract and an
  author's copy of the journal text; report version partly read.
- R. Motwani (1994). *Average-case analysis of algorithms for matchings and related problems*. Journal of the ACM 41(6),
  1329–1356. [doi:10.1145/195613.195663](https://doi.org/10.1145/195613.195663). Author's copy read (parts).
- R. Motwani (1989). *Expanding graphs and the average-case analysis of algorithms for matchings and related problems*.
  STOC '89, 550–561. [doi:10.1145/73007.73060](https://doi.org/10.1145/73007.73060). Read.
- G. R. Grimmett, D. J. A. Welsh (1982). *Flow in networks with random capacities*. Stochastics 7(3), 205–229.
  [doi:10.1080/17442508208833219](https://doi.org/10.1080/17442508208833219). §§1 and 3 read.
- G. R. Grimmett, W.-C. S. Suen (1982). *The maximal flow through a directed graph with random capacities*. Stochastics
  8(2), 153–159. [doi:10.1080/17442508208833234](https://doi.org/10.1080/17442508208833234). Read in full.
- M. Khandwawala, R. Sundaresan (2010). *Optimal multicommodity flow through the complete graph with random edge
  capacities*. Journal of Applied Probability 47(1), 201–215. [doi:10.1239/jap/1269610826](https://doi.org/10.1239/jap/1269610826).
  Abstract only.
- N. Zadeh (1972). *Theoretical efficiency of the Edmonds-Karp algorithm for computing maximal flows*. Journal of the
  ACM 19(1), 184–192. [doi:10.1145/321679.321693](https://doi.org/10.1145/321679.321693). Title only (not
  accessible).
- G. R. Waissi (1991). *Worst case behavior of the Dinic algorithm*. Applied Mathematics Letters 4(5), 57–60.
  [doi:10.1016/0893-9659(91)90145-l](https://doi.org/10.1016/0893-9659(91)90145-l). Read in full.
- O. Naparstek, A. Leshem (2014). *Expected time complexity of the auction algorithm and the push relabel algorithm for
  maximum bipartite matching on random graphs*. Random Structures & Algorithms 48(2), 384–395.
  [doi:10.1002/rsa.20578](https://doi.org/10.1002/rsa.20578). Preprint version read (abstract, introduction).
