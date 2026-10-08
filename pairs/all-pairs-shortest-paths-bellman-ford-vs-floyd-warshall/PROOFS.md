# Proofs: all-pairs shortest paths, Bellman–Ford from every source vs Floyd–Warshall

This file proves every claim that this entry makes (in `entry.json`, `README.md` and the docstrings of the code),
from the code in this folder: the exact operation counts for every size of their domains (sections 1–2), the
correctness of both algorithms (sections 3–4), the time bounds and the density comparison (section 5), the space
bounds (section 6), and the two caveats about the early-exit variant and negative weights (sections 7–8). Each proof
is followed by the deterministic scripts or tests that check it and the sizes they check it on. A check covers only
those sizes; the proofs cover the whole domain. The statements listed under "Background" in `entry.json` are cited,
not proved here.

**Notation.** The vertices are 0..n − 1. E is the set of pairs (u, v) with u ≠ v and `W[u][v] is not None`, m = |E|,
and w(u, v) = `W[u][v]`. A *walk* from s to t is a sequence s = x_0, x_1, …, x_k = t with (x_{i−1}, x_i) ∈ E; it has
k edges, its *intermediate* vertices are x_1, …, x_{k−1}, and its weight is the sum of its edge weights (0 for the
empty walk, k = 0). A *path* is a walk without repeated vertices, so it has at most n − 1 edges; a *cycle* is a
closed walk x_0 = x_k (k ≥ 1) with no other repetition. d(s, t) is the minimum weight of an s–t walk, which exists
whenever no negative cycle is reachable from s (Lemma 3.3). The problem statement's D is D[s][t] = d(s, t) (and
D[s][s] = 0), or None if t is not reachable from s.

## Counting convention

`harness.py`, class `CountingWeight`: `__add__` and `__radd__` add 1 to the module counter `_additions` and return
a new `CountingWeight`; comparisons do not count. `generate_scaling(n, rng)` returns the complete digraph on n
vertices: off-diagonal entries `CountingWeight` with values in [1, 1000], diagonal entries the plain int 0; it sets
`_additions = 0`. `reported_cost(output)` returns `_additions`.

An addition counts 1 if at least one operand is a `CountingWeight`: with a plain int or float (`INF`) on the left,
the left operand's `__add__` returns `NotImplemented` and Python calls `CountingWeight.__radd__`. An addition of two
plain numbers does not count. A "relaxation step" is one execution of the line `d = dist[u] + w` (Bellman–Ford) or
`d = dik + Dk[j]` (Floyd–Warshall).

## 1. Bellman–Ford from every source: n(n − 1)m relaxation steps, n²(n − 1)² counted on the complete digraph

**Statement.** On every input with n vertices and m edges, `apsp_bellman_ford` makes exactly n(n − 1)m relaxation
steps (n sources, n − 1 passes, m relaxations, no early exit). On the complete digraph (m = n(n − 1)) of the scaling
family every step is counted: exactly n²(n − 1)² counted additions (3136 at n = 8, …, 2433600 at n = 40, the values
listed in `entry.json`).

**Proof.** `edges` lists every pair u ≠ v with `W[u][v] is not None`, m entries. For each of the n sources the loop
`for _ in range(n - 1)` runs n − 1 passes, and each pass runs the inner loop over all m edges, executing
`d = dist[u] + w` once per edge; nothing breaks out early. That is n(n − 1)m steps. On the scaling family every
listed `w` is an off-diagonal entry, a `CountingWeight`, so each step counts 1 whatever `dist[u]` is (`INF`, the
plain 0 of the source, or a `CountingWeight`). With m = n(n − 1) the count is n²(n − 1)².

**Check.** `experiments/2026-10-07b_count_v2_apsp_strings.py` (the V2 sizes n = 8, 10, 13, 16, 20, 25, 32, 40).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Bellman-Ford n^2(n-1)^2": n = 0..20, 25, 32, 40.
`experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "APSP relaxation steps: Bellman-Ford n(n-1)m,
Floyd-Warshall n^3 on random digraphs": n = 0..14, 3 seeded digraphs per n with densities 0.1, 0.5 and 1.0.

## 2. Floyd–Warshall: n³ relaxation steps, n³ − n counted on the complete digraph

**Statement.** On every input with n vertices, `apsp_floyd_warshall` makes exactly n³ relaxation steps. On the
scaling family exactly n³ − n of them are counted (32736 at n = 32, …, 7999800 at n = 200, the values listed in
`entry.json`): the n steps with i = j = k add the implementation's own diagonal zeros.

**Proof.** The three loops over k, i, j run `d = dik + Dk[j]` n³ times with no skip. On the scaling family, `D`
starts with the plain 0 on the diagonal and the `CountingWeight` input weights elsewhere.

*The diagonal stays plain and the off-diagonal entries stay counting.* An entry D[i][j] changes only to a value `d`
smaller than its current value. All weights are ≥ 1 (in particular non-negative), so every value in `D` is
≥ 0, and d ≥ 0 = D[i][i] never replaces a diagonal entry. An off-diagonal entry is only replaced by a sum
`dik + Dk[j]` with i ≠ j; such a sum has an off-diagonal operand (i = k = j is impossible), which by induction is a
`CountingWeight`, so the new value is one too.

*Counting.* Hence the step (k, i, j) adds two plain zeros exactly when D[i][k] and D[k][j] are both diagonal, that
is i = k and k = j, and counts 1 otherwise: n³ − n.

**Check.** `experiments/2026-10-07b_count_v2_apsp_strings.py` (the V2 sizes n = 32, 48, 64, 96, 128, 160, 200).
`experiments/2026-10-07_closed_form_checks.py`, group `expdp`, line "Floyd-Warshall n^3-n": n = 0..40, 48, 64, 96,
128, 160, 200. `experiments/2026-10-07_count_proof_checks.py`, group `graphs`, line "APSP relaxation steps:
Bellman-Ford n(n-1)m, Floyd-Warshall n^3 on random digraphs": n = 0..14, 3 seeded digraphs per n.

## 3. Correctness of Bellman–Ford from every source

**Statement.** Fix a source s and a weight matrix whose weights are numbers of any sign, such that no negative cycle
is reachable from s. After the n − 1 passes of `apsp_bellman_ford`, `dist[v]` = d(s, v) for every v reachable from s
and `dist[v]` = `INF` for every other v; so row s of the output is row s of D. In particular the output is D on every
input of the problem statement (non-negative weights give no negative cycle).

**Lemma 3.1 (walks).** At every moment, `dist[v]` is `INF` or the weight of some s–v walk. *Proof.* Initially
`dist[s]` = 0 is the empty walk and the rest is `INF`. A relaxation sets `dist[v]` = `dist[u]` + w(u, v) < `dist[v]`;
this value is finite only if `dist[u]` is (`INF` plus a number is `INF`, never smaller than `dist[v]`), and then it is
the weight of a walk to u followed by the edge (u, v).

**Lemma 3.2 (passes).** After p passes (0 ≤ p ≤ n − 1), `dist[v]` ≤ ω_p(v), the minimum weight of an s–v walk with at
most p edges (`INF` if there is none). *Proof.* Induction on p; p = 0 holds (`dist[s]` = 0). Let a walk with at most
p ≥ 1 edges end with the edge (u, v), and let its prefix to u have weight a (at most p − 1 edges). After p − 1 passes
`dist[u]` ≤ a; values never increase, so when pass p relaxes (u, v), `dist[v]` becomes at most a + w(u, v). A walk
with 0 edges is the empty walk at s.

**Lemma 3.3 (paths suffice).** If no negative cycle is reachable from s, then for every v reachable from s some s–v
path has the minimum weight among all s–v walks; hence d(s, v) exists and equals ω_{n−1}(v), and d(s, s) = 0.
*Proof.* A walk with a repeated vertex x_i = x_j (i < j) contains the closed walk x_i, …, x_j. A closed walk splits
at a repeated vertex into two shorter closed walks, so by induction it is a union of cycles, all reachable from s,
each of weight ≥ 0. Deleting x_{i+1}, …, x_j therefore gives a walk with fewer edges and no larger weight. Repeating
this ends at a path. There are finitely many paths, each with at most n − 1 edges, so the minimum over walks is
attained by a path. For v = s the empty walk is a path of weight 0, and every closed walk at s weighs ≥ 0.

**Proof of the statement.** For v reachable from s, Lemmas 3.2 and 3.3 give `dist[v]` ≤ ω_{n−1}(v) = d(s, v), and
Lemma 3.1 gives `dist[v]` ≥ d(s, v). If v is not reachable, there is no walk and `dist[v]` stays `INF` (Lemma 3.1).
The row is built with `None` for `INF` (an integer or a finite sum never equals `INF`).

**Check.** `harness.check` against heap-based Dijkstra from every source (the V1 battery of `tools/validate.py`,
n = 0..30). `tests/test_proofs_apsp.py`, `test_correct_on_problem_inputs` (`harness.generate` digraphs, n = 0..20,
4 seeds each) and `test_correct_with_negative_weights` (n = 0..12, 6 seeds each, weights of both signs without
negative cycles, against an independent oracle described in section 8).

## 4. Correctness of Floyd–Warshall

**Statement.** For every weight matrix without a negative cycle (weights of any sign), `apsp_floyd_warshall` returns
D. In particular it does so on every input of the problem statement.

**Proof.** For 0 ≤ k ≤ n let d_k(i, j) be the minimum weight of an i–j walk whose intermediate vertices all lie in
{0, …, k − 1} (`INF` if there is none). As in Lemma 3.3 (deleting a closed sub-walk keeps the intermediate vertices
inside the set), the minimum is attained by a path; so d_0(i, j) = w(i, j) or `INF` for i ≠ j, d_0(i, i) = 0 (the
empty walk; there are no self-loops), and d_n = D with `INF` for unreachable pairs.

*Recurrence.* d_{k+1}(i, j) = min(d_k(i, j), d_k(i, k) + d_k(k, j)). "≤": both terms are weights of walks with
intermediate vertices in {0, …, k} (join the two walks at k). "≥": take a path attaining d_{k+1}(i, j); if k is not
one of its intermediate vertices, its weight is ≥ d_k(i, j); otherwise k occurs exactly once, and the path splits at
k into an i–k path and a k–j path whose intermediate vertices lie in {0, …, k − 1}, of weights ≥ d_k(i, k) and
≥ d_k(k, j).

*The loop computes it in place.* The initial matrix is d_0. Assume D = d_k when the iteration with this k starts.
Then D[k][k] = d_k(k, k) = 0 (the empty walk; closed walks weigh ≥ 0). The step (k, i, k) computes
min(D[i][k], D[i][k] + 0) and the step (k, k, j) computes min(D[k][j], 0 + D[k][j]), so row k and column k do not
change during this iteration; in particular `dik` (read once per i) and `Dk[j]` keep the values d_k(i, k) and
d_k(k, j). Every entry is therefore set to min(d_k(i, j), d_k(i, k) + d_k(k, j)) = d_{k+1}(i, j). After the last
iteration D = d_n, and `INF` entries are returned as `None`.

**Check.** As in section 3: the V1 battery (n = 0..60) and `tests/test_proofs_apsp.py`,
`test_correct_on_problem_inputs` and `test_correct_with_negative_weights`.

## 5. Running time and the density comparison

The cost model is the entry's: weights are bounded (by 1000 in the harness), so each addition, comparison, index
operation and list operation costs Θ(1).

**Statement.** `apsp_bellman_ford` takes Θ(n²(m + 1)) time on every input, that is Θ(n²m) for m ≥ 1 and Θ(n⁴) when
m = Θ(n²); `apsp_floyd_warshall` takes Θ(n³) time on every input with n ≥ 1. Consequently: for m = Θ(n) both are
Θ(n³); for m = ω(n) Floyd–Warshall is faster by the factor Θ(m/n) (the factor Θ(n) on dense digraphs); for m = o(n)
Bellman–Ford from every source is faster by the factor Θ(n/(m + 1)).

**Proof.** Bellman–Ford: listing the edges runs the comprehension over n² pairs, Θ(n²). For each of the n sources,
initialising `dist` and building the output row take Θ(n), and the n − 1 passes take Θ(1 + m) each (section 1: m
relaxation steps per pass, each Θ(1), no early exit). Total Θ(n² + n·n + n(n − 1)(1 + m)) = Θ(n²(m + 1)).
Floyd–Warshall: building D and the output takes Θ(n²), and the triple loop makes exactly n³ steps of Θ(1) each
(section 2) plus Θ(n²) overhead in the two outer loops: Θ(n³). The comparison is the ratio n²(m + 1)/n³ = (m + 1)/n
of the two bounds: it is Θ(1) for m = Θ(n), grows like m/n for m = ω(n), and tends to 0 for m = o(n). With m ≥ c·n²
(c > 0 a constant) the bounds are Θ(n⁴) and Θ(n³).

**Check.** The step counts are checked as listed in sections 1 and 2; the comparison is arithmetic on the two
bounds.

## 6. Space

**Statement.** Besides the input, `apsp_bellman_ford` holds Θ(m + n²) words: the edge list (Θ(m)), `dist` (n) and
the output (Θ(n²)); `apsp_floyd_warshall` holds Θ(n²) words. Counting one word per container slot, the containers
bound to local variables (with the returned object) never hold more than 4m + n² + 3n slots in Bellman–Ford and
2n² + 2n slots in Floyd–Warshall, and at the return they hold at least n² + n slots (the output) in both.

**Proof.** Bellman–Ford creates: `edges`, a list of m triples (m + 3m slots); one `dist` list of n slots per source,
the previous one being released when the name is rebound; `rows`, a list of at most n tuples of n slots (at most n + n² slots);
the returned tuple of the n rows (n slots; the row tuples are shared); the generator that builds a row holds no
container. Total at most 4m + n + (n + n²) + n = 4m + n² + 3n. Floyd–Warshall creates `D`, a list of n lists of n
(n + n² slots; `Dk` and `Di` are aliases), and the returned tuple of n new tuples of n (n + n² slots): at most
2n² + 2n. At the return each output holds n² + n slots. Since m ≤ n(n − 1), both are Θ(n²) words besides the input,
and Bellman–Ford's edge list is Θ(m). The bounds count the containers bound to local variables (and the returned object) between statements, which is what the check measures. While a new list is being created it can briefly coexist with the list it replaces, which adds at most the size of that one list; the Θ bounds are unaffected.

**Check.** `tests/test_proofs_apsp.py`, `test_space`: the instrumented peak of `tests/proof_space.py` (container
slots bound to local variables at every line and return event, the input excluded) lies between n² + n and the
bounds above, n = 0..10, 3 seeded digraphs each.

## 7. The early-exit variant (caveat)

The variant is the one of `experiments/2026-10-07_apsp_bellman_ford_early_exit.py`: the same edge list in the same
order (u ascending, then v ascending), at most n − 1 passes per source, and the passes for a source stop after the
first pass in which no `dist` value decreases. It is not an implementation of this entry.

**Statement.** On every input with non-negative weights: (a) from every source it makes at most min(m + 1, n − 1)
passes, so at most n·m·min(m + 1, n − 1) relaxation steps in all; for m ≤ n − 2 that is at most n·m·(m + 1), which is
o(n²m) when m = o(n). (b) For every n ≥ 2 and every m with n − 1 ≤ m ≤ n(n − 1) there are inputs with m edges on which
it makes at least m·(n(n − 1)/2 + n − 1) ≥ n²m/2 relaxation steps: the edges (i, i − 1), i = 1..n − 1, of weight 1
and any m − (n − 1) further edges of weight ≥ n. So its worst case is Θ(n²m) whenever m ≥ n − 1, but not when
m = o(n).

**Proof.** (a) Lemmas 3.1–3.3 hold for the variant up to the pass where it stops. With non-negative weights, some
shortest walk to each reachable vertex is a path, which uses at most min(m, n − 1) edges. After q = min(m, n − 1)
passes every `dist` value is therefore final (Lemmas 3.1–3.3); if q < n − 1 the next pass changes nothing and the
variant stops after at most q + 1 passes, and otherwise it stops at the cap of n − 1 passes.

(b) Fix the source s. Every walk from s to s − q (0 ≤ q ≤ s) that uses a heavy edge weighs ≥ n > q, and the only walk
with light edges alone is s, s − 1, …, s − q (a light edge lowers the vertex number by one); so d(s, s − q) = q, and by
Lemma 3.1 `dist[s − q]` ≥ q at all times. Claim: at the end of pass p (0 ≤ p ≤ s), `dist[s − q]` = q for q ≤ p and
`dist[s − q]` ≥ n for p < q ≤ s. For p = 0 this is the initial state. In pass p + 1 ≤ s, a relaxation into s − q
either uses a heavy edge, which gives a value ≥ 0 + n, or the light edge (s − q + 1, s − q). That edge is relaxed
before the only light edge into s − q + 1, namely (s − q + 2, s − q + 1), because its tail is smaller; so when it is
relaxed, `dist[s − q + 1]` is its value at the end of pass p, possibly lowered by heavy edges to a value ≥ n. For
q ≥ p + 2 that value is ≥ n (induction), so `dist[s − q]` stays ≥ n. For q = p + 1 it is p, so `dist[s − p − 1]` drops
from a value ≥ n to p + 1. Values with q ≤ p are already final. Hence each of the passes 1, …, s lowers a value, the
variant cannot stop before pass s + 1, and it makes at least min(s + 1, n − 1) passes from s. Summing,
Σ_{s=0}^{n−1} min(s + 1, n − 1) = n(n − 1)/2 + (n − 1) passes, each with m relaxation steps. The experiment's family
(b) (heavy weight 10⁶, the complete digraph) is the case m = n(n − 1).

**Check.** `tests/test_proofs_apsp.py`, `test_early_exit_lower_bound_family` (n = 2..16; for each n the values
m = n − 1, n(n − 1) and four seeded values in between, with random heavy edges of weight in [n, 3n]: at least
min(s + 1, n − 1) passes from every source s, and at least m(n(n − 1)/2 + n − 1) relaxation steps in total) and
`test_early_exit_upper_bound` (n = 1..16, densities 0, 0.05, 0.2, 0.6 and 1, 4 seeds each: at most min(m + 1, n − 1)
passes per source).

## 8. Negative weights (caveat)

**Statement.** (a) Both implementations return D for every weight matrix with weights of any sign and no negative
cycle; Bellman–Ford's row s needs only that no negative cycle is reachable from s. (b) The standard negative-cycle
test (one more pass after the n − 1 passes, reporting a cycle if it lowers some `dist` value) reports a cycle if and
only if a negative cycle is reachable from s. This test is not part of the entry's implementation.

**Proof.** (a) Sections 3 and 4 use only these hypotheses. (b) If no negative cycle is reachable, then after n − 1
passes `dist` = d(s, ·) (section 3), and d(s, v) ≤ d(s, u) + w(u, v) for every edge (u, v) with u reachable (a walk to
u extended by (u, v)), so the extra pass lowers nothing. If a negative cycle x_0, …, x_k = x_0 is reachable from s,
every x_i has a finite `dist` after n − 1 passes (Lemma 3.2: it is reachable by a path of at most n − 1 edges). If the
extra pass lowered nothing, then `dist[x_i]` ≤ `dist[x_{i−1}]` + w(x_{i−1}, x_i) for all i; summing over the cycle
gives 0 ≤ Σ w(x_{i−1}, x_i) < 0, a contradiction.

**Check.** `tests/test_proofs_apsp.py`, `test_correct_with_negative_weights` (weights w(u, v) = w₀(u, v) + p(u) − p(v)
with w₀ in [0, 20] and p in [−30, 30], so negative weights occur and every cycle keeps its non-negative w₀-weight;
the oracle is heap-based Dijkstra on w₀, shifted back by p(s) − p(t); n = 0..12, 6 seeds) and
`test_negative_cycle_test` (the extra pass against an exhaustive search for negative cycles reachable from s,
n = 1..6, 60 random digraphs per n with weights in [−6, 9]).
