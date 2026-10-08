# Trivial minimum cut on the max-flow entry's random dense networks

> **Provenance: 🟡⏳ Undetermined (may be our own result).** Karp, Motwani and Nisan credit Karp (1979), Grimmett and
> Welsh (1982) and Grimmett and Suen (1982) with the result that, on complete graphs with i.i.d. edge capacities, the
> minimum s–t cut is almost surely one of the two trivial cuts. Grimmett–Welsh (the sections on complete graphs),
> Grimmett–Suen (in full) and Karp–Motwani–Nisan (the journal text and parts of their 1988 report) were read.
> Grimmett–Welsh and Grimmett–Suen prove results on the maximum-flow value only (first-order limits on undirected
> complete graphs or with one orientation per pair, and bounds on its mean); Karp–Motwani–Nisan prove trivial-cut
> theorems only for other models (undirected graphs with unit capacities, or given source and sink capacities). None of
> them states the result for this note's model. Beyond them, this note proves the deterministic statement (a) with an
> explicit event 𝒞 and the value returned by both implementations of the entry, an explicit bound on P(not 𝒞) for every
> finite n, and the fair-coin statement (c) with an explicit tie bound, for a directed complete graph in which every
> ordered pair has a capacity that is 0 with probability ½ and otherwise uniform on {1, …, 100}, so that the source and
> sink capacities are random as well. Karp (1979), a contribution to the Tenth International Symposium on Mathematical
> Programming, could not be read: it is known only from Karp–Motwani–Nisan's citation, and no copy, publisher record or
> DOI was found. Whether it contains the result could not be checked, so the result may be our own. If you can tell us
> whether this source contains the result, please open an issue. The proof below is complete and does not rely on any
> of these sources.
>
> Bases: Karp (1979), as reported by Karp–Motwani–Nisan (not accessible); Grimmett–Welsh (1982), Stochastics 7(3),
> doi:10.1080/17442508208833219, and Grimmett–Suen (1982), Stochastics 8(2), doi:10.1080/17442508208833234 (flow-value
> limits). What was read, and what this note adds, is in [Literature](#literature).

## Setting

The pair [max-flow-edmonds-karp-vs-dinic](../../pairs/max-flow-edmonds-karp-vs-dinic/) defines the random instance
family `generate_scaling(n, rng)` in its `harness.py`; its tests and probe run its two implementations on it. For u = 0, …, n − 1 and v = 0, …, n − 1 with u ≠ v,
in this order, the generator evaluates `rng.random() < 0.5` and, only if that holds, draws a capacity
`rng.randint(1, 100)` for the edge (u, v). The source is s = 0 and the sink is t = n − 1.

**Model 𝔊ₙ.** Every ordered pair (u, v), u ≠ v, is an edge independently with probability ½, and its capacity is
independent and uniform on {1, …, 100}. With ideal random bits this is exactly the distribution of
`generate_scaling`: `random()` returns multiples of 2⁻⁵³ in [0, 1), so `random() < 0.5` has probability exactly ½,
and `randint` is exactly uniform. (This is Lemma G of the pair's
[PROOFS.md](../../pairs/max-flow-edmonds-karp-vs-dinic/PROOFS.md), section 9; the call structure is checked by
`tests/test_proofs_maxflow.py`, class `RandomModel`.) All probabilities below are taken in 𝔊ₙ. The simulations in `verify.py` use
Python's Mersenne Twister as it is. There are no parallel edges; antiparallel pairs occur.

**Notation.** M = {1, …, n − 2} is the set of middle vertices and m = n − 2. c(u, v) is the capacity of the edge
(u, v), and 0 if there is no such edge; c(A, B) = Σ_{a∈A, b∈B} c(a, b). The capacity X of one ordered pair has
P(X = 0) = ½ and P(X = c) = 1/200 for c = 1, …, 100, so E X = 101/4 and Var X = 16867/16. For v ∈ M, a_v = c(s, v)
and b_v = c(v, t). c_out(s) = c(s, V) and c_in(t) = c(V, t). F is the value of a maximum s–t flow. An s–t cut is a
vertex set S with s ∈ S and t ∉ S; its capacity is cap(S) = c(S, V ∖ S). The two **trivial cuts** are S = {s},
with capacity c_out(s), and S = V ∖ {t}, with capacity c_in(t). Finally

    φ(θ) = E e^{−θX} = ½ + (1/200)·Σ_{c=1}^{100} e^{−θc}      (θ ≥ 0).

## Statement

**Theorem 1.** Let n ≥ 4. Let 𝒞 be the event that

    c(S′, M ∖ S′) > 100·min(|S′|, |M ∖ S′|)      for every nonempty proper subset S′ of M.

**(a) Deterministic part.** Consider any network on the vertices 0, …, n − 1 with non-negative integer capacities and with
0 ≤ a_v ≤ 100 and 0 ≤ b_v ≤ 100 for every v ∈ M. If it satisfies 𝒞, then every s–t cut other than the two trivial
cuts has capacity > min(c_out(s), c_in(t)). Hence F = min(c_out(s), c_in(t)), the minimum cuts are exactly the
trivial cuts whose capacity equals this minimum, and both implementations of the entry return this value.

**(b) Probability of 𝒞.** In 𝔊ₙ,

    P(not 𝒞) ≤ B(n) := Σ_{j=1}^{m−1} C(m, j) · inf_{θ>0} e^{100·min(j, m−j)·θ} · φ(θ)^{j(m−j)},

and B(n) → 0 as n → ∞. More precisely, B(n) < 1 for every n ≥ 22, B(n) < 5.48·10⁻⁵ and B(n) ≤ 1/n for every
n ≥ 40, and B(n) < 7.6·10⁻⁶ for every n ≥ 202. Upper bounds on B(n), computed by `verify.py` and rounded up:

| n | 20 | 30 | 40 | 60 | 80 | 160 | 400 | 800 | 1200 |
|---|---|---|---|---|---|---|---|---|---|
| B(n) ≤ | 7.238 (vacuous) | 7.215·10⁻³ | 5.474·10⁻⁵ | 1.385·10⁻⁹ | 1.881·10⁻¹⁴ | 3.962·10⁻³⁵ | 4.876·10⁻¹⁰¹ | 9.785·10⁻²¹⁵ | 3.120·10⁻³³⁰ |

For every n from 4 to 21 the computed bound is ≥ 1, so part (b) gives nothing there.

**(c) Which trivial cut.** Let Δ = c_out(s) − c_in(t). In 𝔊ₙ,

    P(Δ = 0) ≤ √(2/m) + e^{−0.1225·m},      P(Δ < 0) = P(Δ > 0) = (1 − P(Δ = 0))/2.

So each of the two events "({s}, V ∖ {s}) is the only minimum cut" and "(V ∖ {t}, {t}) is the only minimum cut" has
probability at least ½ − (√(2/m) + e^{−0.1225m})/2 − P(not 𝒞) and at most ½. Both probabilities tend to ½: which
trivial cut is minimum is asymptotically a fair coin.

The two notes [max-flow-random-dense-dinic-short-residual-paths](../max-flow-random-dense-dinic-short-residual-paths/)
and [max-flow-random-dense-edmonds-karp-cubic-reads](../max-flow-random-dense-edmonds-karp-cubic-reads/) use this
theorem. They also use the tail inequalities proved in the [Appendix](#appendix-tail-inequalities-and-sperners-theorem).

## Proof

### Flows, cuts and the two implementations

A *feasible flow* assigns f(e) ∈ [0, c(e)] to every edge and satisfies conservation (inflow = outflow) at every
vertex other than s and t; its value v(f) is the net flow out of s. For vertex sets A, B write f(A, B) for the total
flow on edges from A to B.

**Lemma 0.** (i) For every feasible flow f and every s–t cut S, v(f) ≤ cap(S). (ii) Each of the entry's two
implementations stops, on every network with non-negative integer capacities (the entry's input domain), with a
feasible flow f and an s–t cut S with v(f) = cap(S), and returns v(f). Hence both return F, and F equals the minimum
capacity of an s–t cut.

*Proof.* (i) Summing conservation over the vertices of S (s ∈ S, t ∉ S) gives
v(f) = f(S, V ∖ S) − f(V ∖ S, S) ≤ c(S, V ∖ S).
(ii) Both implementations store a flow in the residual capacities: edge i = (u, v, c) gives arc 2i (u → v, residual
c − f_i) and arc 2i + 1 (v → u, residual f_i). Pushing an amount b ≤ the smallest residual along a simple s–t path of
arcs with positive residual keeps every f_i in [0, c_i], preserves conservation at the inner vertices of the path,
and raises v(f) by b. The returned value is the sum of these amounts, which is v(f). Each amount is a positive integer
and v(f) ≤ cap({s}) by (i), so there are finitely many augmentations. Edmonds–Karp augments after every breadth-first
search that reaches t, so it stops; for Dinic, every phase whose search reaches t ends and augments at least once
(Lemma 1(c) of the [Dinic note](../max-flow-random-dense-dinic-short-residual-paths/)), so it stops too. Both stop
exactly when a breadth-first search from s does not reach t over arcs with positive residual. Let S be the set it
reaches. No arc with positive residual leaves S, so every edge from S to
V ∖ S is saturated and every edge from V ∖ S to S carries no flow, and the identity in (i) gives v(f) = cap(S).
With (i), v(f) is the largest flow value and cap(S) the smallest cut capacity. ∎

### (a) Cut algebra

Every s–t cut is S = {s} ∪ S′ with S′ ⊆ M. The edges leaving S go from s to t, from s to M ∖ S′, from S′ to t and
from S′ to M ∖ S′, so

    cap(S) = c(s, t) + Σ_{v∈M∖S′} a_v + Σ_{u∈S′} b_u + c(S′, M ∖ S′).

With c_out(s) = c(s, t) + Σ_{v∈M} a_v and c_in(t) = c(s, t) + Σ_{v∈M} b_v,

    cap(S) − c_out(s) = c(S′, M ∖ S′) − Σ_{u∈S′} (a_u − b_u) ≥ c(S′, M ∖ S′) − 100·|S′|,
    cap(S) − c_in(t)  = c(S′, M ∖ S′) − Σ_{v∈M∖S′} (b_v − a_v) ≥ c(S′, M ∖ S′) − 100·|M ∖ S′|,

because every difference a_v − b_v lies in [−100, 100]. S′ = ∅ and S′ = M give the two trivial cuts. For every other
S′, the event 𝒞 makes the first right-hand side positive if |S′| ≤ |M ∖ S′| and the second one otherwise. So
cap(S) > min(c_out(s), c_in(t)). By Lemma 0, F is the minimum cut capacity, which is therefore min(c_out(s), c_in(t)),
attained exactly by the trivial cuts with that capacity, and both implementations return it. ∎

### (b) Probability of 𝒞

Fix S′ ⊆ M with |S′| = j, 1 ≤ j ≤ m − 1. The value c(S′, M ∖ S′) is the sum of the capacities of the j(m − j)
ordered pairs in S′ × (M ∖ S′), which are independent copies of X. By the Chernoff bound (A1 in the Appendix),
P(c(S′, M ∖ S′) ≤ T) ≤ e^{θT}·φ(θ)^{j(m−j)} for every θ > 0. Take T = 100·min(j, m − j), use a union bound over the
C(m, j) sets of size j, and sum over j. This gives P(not 𝒞) ≤ B(n).

*All large n.* Take θ = ½ in every term. φ(½) = 0.5077074… < 1. For j ≤ m/2 we have min(j, m − j) = j,
m − j ≥ m/2 and C(m, j) ≤ m^j, so the j-th term is at most (m·e^{50}·φ(½)^{m/2})^j = r^j. The term for j > m/2 equals
the term for m − j. So B(n) ≤ 2·Σ_{j≥1} r^j = 2r/(1 − r) whenever r < 1. The derivative of
ln r = ln m + 50 + (m/2)·ln φ(½) in m is 1/m + ½ ln φ(½) < 0 for m ≥ 3 (½ ln φ(½) = −0.3389…), so r decreases in m.
At m = 200, ln r = −12.4866…, so B(n) ≤ 2r/(1 − r) < 7.6·10⁻⁶ for every n ≥ 202. Since r → 0, B(n) → 0. Moreover
ln(n·r) has derivative 1/n + 1/m + ½ ln φ(½) < 0 in n for n ≥ 202, and 1/(1 − r) decreases with r, so n·2r/(1 − r)
decreases; at n = 202 it is 1.53·10⁻³ < 1. Hence B(n) ≤ 1/n for every n ≥ 202.

*Computed values (22 ≤ n ≤ 201, and the table).* `verify.py` evaluates the sum term by term. For j ≤ m/2 the exponent
equals j·k·(100θ/k + ln φ(θ)) with k = m − j. The script finds θ_k by bisection, in double precision, on the derivative
of 100θ/k + ln φ(θ). Any θ ≥ 0 gives a valid bound, so only the final evaluation has to be accurate. That evaluation is
done in 50-digit decimal arithmetic (Python's `decimal` module, in which +, −, ×, ÷, exp and ln are correctly rounded):
θ_k is converted exactly, φ(θ) is taken in the closed form ½ + q(1 − q¹⁰⁰)/(200(1 − q)) with q = e^{−θ}, ln C(m, j)
comes from sums of ln i, and the terms C(m, j)·e^{100jθ_k}·φ(θ_k)^{jk} are summed as e^{(their logarithms)}. Each
logarithm takes fewer than 2500 correctly rounded operations (the longest chain is that of the table entry n = 1200)
on numbers of absolute value below 10⁷, and the only
cancellation, in 1 − q, loses at most six digits because the script uses only θ = 0 or θ ≥ 10⁻⁶ (checked). So the
accumulated relative error is far below 10⁻²⁵, and every comparison allows a relative margin of 10⁻²⁰. For every n
from 22 to 201 the result is < 1, and for every n from 40 to 201 it is < 5.48·10⁻⁵ (the largest value is
5.473049·10⁻⁵, at n = 40) and ≤ 1/n. Together with the bound for n ≥ 202, this gives the sentences of (b) after the
union bound. The table lists the decimal sums rounded up to four significant digits. ∎

### (c) Ties: a Littlewood–Offord argument

The term c(s, t) cancels in Δ, so Δ = Σ_{v∈M} (a_v − b_v). The pairs (a_v, b_v) are independent across v, and a_v and
b_v are independent with the same law, so (a_v, b_v) and (b_v, a_v) have the same law. Let d_v = |a_v − b_v| and,
when d_v > 0, ε_v = sign(a_v − b_v). Conditional on (d_v)_{v∈M}, the signs ε_v are independent and uniform on {+1, −1}.
The number K of v with d_v > 0 is binomial Bin(m, q) with q = 1 − P(a_v = b_v) = 1 − (¼ + 1/400) = 299/400.

Condition on the d_v, with K = k ≥ 1. Then Δ = Σ_{d_v>0} ε_v·d_v. The sign vectors with Σ ε_v d_v = 0 form an
antichain in {+1, −1}^k under the coordinatewise order: if ε ≤ ε′ and ε ≠ ε′, the two sums differ by at least
2·min d_v > 0. By Sperner's theorem (A4) there are at most C(k, ⌊k/2⌋) of them, so
P(Δ = 0 | d) ≤ C(k, ⌊k/2⌋)/2^k. This quotient is at most 1/√k: for k = 2r, p_r = C(2r, r)/4^r satisfies

    p_r² = Π_{i=1}^{r} ((2i − 1)/(2i))² ≤ Π_{i=1}^{r} (2i − 1)/(2i + 1) = 1/(2r + 1),

using (2i − 1)/(2i) ≤ 2i/(2i + 1), so p_r ≤ 1/√(2r + 1) < 1/√k; and for k = 2r + 1,
C(k, r)/2^k = p_r·(2r + 1)/(2r + 2) ≤ √(2r + 1)/(2r + 2) < 1/√k. (If K = 0, then Δ = 0; this case lies in {K < m/2}
below.) Hence

    P(Δ = 0) ≤ E[K^{−1/2}; K ≥ m/2] + P(K < m/2) ≤ √(2/m) + e^{−2(q − ½)²·m},

where the last term is Hoeffding's inequality (A3) for K, and 2(q − ½)² = 2·(99/400)² = 0.1225125 ≥ 0.1225.
Exchanging a and b maps Δ to −Δ without changing the law, so P(Δ < 0) = P(Δ > 0). On 𝒞, part (a) says that the
minimum cut is unique and is {s} if Δ < 0, and V ∖ {t} if Δ > 0. So P({s} is the only minimum cut) ≥ P(Δ < 0) −
P(not 𝒞); and it is ≤ P(Δ < 0) ≤ ½, because {s} can be the only minimum cut only if c_out(s) < c_in(t). The same
holds for V ∖ {t}. ∎

The bound in (c) is far from sharp. With A = Σ_{v∈M} a_v and B = Σ_{v∈M} b_v, which are independent with the same law,
P(Δ = 0) = P(A = B) = Σ_x P(A = x)². `verify.py` evaluates this sum exactly (integer convolution): 0.00204 at n = 20 and
0.00141 at n = 40, against the bounds ≈ 0.444 and ≈ 0.239. The bound is only used for the limit ½.

## Literature

- **Karp, Motwani and Nisan (1993)**, Math. Oper. Res. 18(1). Read: the abstract (database record). Under "certain
  assumptions about the probability distribution of edge capacities" it states for "the maximum flow problem with
  multiple sources and sinks" that "with high probability the minimum cut isolates either the sources or the sinks".
  An author's copy of the journal paper (dated August 9, 1995, linked from the second author's publication page) was
  also read: it repeats the attribution quoted below from the report, and its results keep the hypotheses described
  there: the multiple-source result (Theorem 3.2) is for undirected graphs with capacity 1 on every present edge, and
  in the single-source theorem (Theorem 4.5) the source and sink capacities are given and satisfy a realizability
  condition. So it does not apply to 𝔊ₙ.
- **Karp, Motwani and Nisan (1988)**, the technical report with the same title (University of California, Berkeley).
  Read: the abstract page and pp. 3–5, 10, 24–27 and 29 of the scanned report (report page numbers). On p. 5:
  "Consider now the Max-Flow problem where |S| = |T| = 1 and the edge capacities are i.i.d. random variables. […]
  Karp [18], Grimmett & Welsh [15] and Grimmett & Suen [16] obtained strong asymptotic results for complete graphs
  with i.i.d. edge capacities. In particular, they showed that the minimum cut is almost surely the set of edges
  incident on the source or those incident on the sink. These results are all existential and do not yield any fast
  algorithms to construct the maximum flow." Their own single-source result (§4.5, conditions (M.1)–(M.4) and
  Corollary 1, pp. 26–27) has i.i.d. middle capacities on {0, …, K} with mean at least 1 + ε, but given source and sink
  capacities that satisfy a realizability condition (M.4). In 𝔊ₙ the source and sink capacities are random, so
  Corollary 1 does not apply as stated. Reference [18] is R. M. Karp, "The Probabilistic Analysis of Combinatorial
  Optimization Algorithms", Tenth International Symposium on Mathematical Programming, 1979 (as listed on p. 29; not
  accessible).
- **Grimmett and Welsh (1982).** Read (author's copy): §1 and §3, the part on complete graphs (§2, on trees, and §4
  were not needed). Capacities are i.i.d. non-negative random variables
  with any distribution (atom at 0 allowed). §3 treats two cases: "the complete graph is undirected, whilst in the second
  each edge is directed in a specified manner" (from i to j for i < j). Theorem 3.3: (1/n)Xₙ → μ_B on the undirected graph
  and (1/n)Yₙ → γ with μ_M ≤ γ ≤ μ_B on the directed one, almost surely and in L¹ (μ_B the mean capacity, μ_M the mean of
  the minimum of two capacities); "We have not been able to find the exact growth rate γ". Their proof of the first
  limit for Bernoulli capacities bounds the probability of small cutsets by a union bound over vertex sets, the same
  kind of argument as part (b). They do not state that the minimum cut is trivial, and they give no finite-n bound on
  the probability that a non-trivial cut is minimal (their Lemma 3.2 bounds only the mean flow values).
- **Grimmett and Suen (1982).** Read in full (author's copy). Theorem 1: (1/n)Yₙ → μ_B almost surely and in L¹ on the
  complete graph with edges directed from the smaller to the larger vertex; Theorem 2: (1/n)Yₙ → ½μ_B when each pair
  gets one random orientation. They add that these conclusions "do not surprise us, since the cutsets … which involve
  fewest edges are the two families of edges which are incident to 0 and to ∞", which explains the limits; they do not
  state that the minimum cut is trivial.
- **What this note adds**, as far as could be established from the texts read: the deterministic statement (a) with
  an explicit event 𝒞; an explicit bound on P(not 𝒞) for each finite n, with values; the fair-coin statement (c) with
  an explicit tie bound; the model with both orientations of every pair together with random source and sink
  capacities (Karp–Motwani–Nisan's directed theorem has both orientations but given source and sink capacities); and
  verification code tied to the entry's generator and implementations. Grimmett–Welsh and Grimmett–Suen give results
  on the flow value only (limits, and bounds on its mean).
- **Why undetermined.** Karp (1979), the third work that Karp, Motwani and Nisan credit with the trivial minimum cut,
  could not be read: no copy, publisher record or DOI was found, and it is known only from their citation. Whether it
  states the result for this model (capacity 0 with probability ½, both orientations of every pair, random source and
  sink capacities), and so whether parts (a)–(b) in their asymptotic form are in it, could not be checked; the result
  may therefore be our own.

## Scope

- Part (a) is deterministic and holds for every network with the stated capacity bounds. Parts (b) and (c) are about
  the model 𝔊ₙ with ideal random bits; the Mersenne Twister is not analysed.
- Part (b) gives nothing for n ≤ 21: the computed bound is ≥ 1 there.
- Nothing is claimed on the complement of 𝒞, for other edge densities or for other capacity laws.
- The tie bound in (c) is valid but weak (see the exact values above).
- The "computed" values of (b) are decimal evaluations of the stated formula with certified rounding, for exactly the n
  stated (22 ≤ n ≤ 201 and the table); every n ≥ 202 is covered by the written tail bound.

## Verification

```bash
python theorems/max-flow-random-dense-trivial-min-cut/verify.py            # about 10 s
python theorems/max-flow-random-dense-trivial-min-cut/verify.py --full     # adds instances with n = 320, 640 (about 70 s)
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and exits with
code 0 only if every check passes. It loads the entry's `harness.py` and both implementations unchanged. It checks:

- the exact constants (E X, Var X, q = 299/400, 2(q − ½)² ≥ 0.1225) with fractions;
- in 50-digit decimal arithmetic: the table of (b) (each listed value is the computed sum rounded up), the computed
  bound ≥ 1 for every n in [4, 21], B(n) < 1 for every n in [22, 201], B(n) < 5.48·10⁻⁵ and B(n) ≤ 1/n for every n in
  [40, 201], and the numbers of the tail bound for n ≥ 202 (φ(½), ln r at m = 200, the two derivative signs);
- the Littlewood–Offord count by brute force (300 seeded vectors, k ≤ 12), C(k, ⌊k/2⌋)²·k ≤ 4^k for k ≤ 2000 with exact
  integers, the exact tie probabilities at n = 20 and 40 against the bound, and P(Δ < 0) = P(Δ > 0) there;
- Lemma 0 and part (a) on seeded instances of the entry's generator: the cut identities for every cut (n = 6, 8, 10, 12;
  120 instances); on 80 instances with n = 14, 16, 18, by enumerating every cut, that both implementations return the
  minimum cut capacity (Lemma 0), and, on the 26 instances where 𝒞 holds, that the minimum cuts are exactly the trivial
  cuts attaining min(c_out(s), c_in(t)); on 910 larger instances (n = 20–160; more with `--full`), that both
  implementations agree and return at most min(c_out(s), c_in(t)) (Lemma 0(i));
- the appendix facts on finite cases: A1 against the exact distributions of sums of 1–6 copies of X (7 values of θ); A2
  on 300 seeded discrete distributions with mean 0; A3 against exact binomial tails for N ≤ 80 and six values of p; A4 on
  all antichains of subsets of a 4-set and of a 5-set (168 and 7581 of them).

## Appendix: tail inequalities and Sperner's theorem

The notes on this family use only these four facts. They are classical; the short proofs are given so that the notes
are self-contained.

**A1 (Chernoff bound).** Let Y_1, …, Y_N be independent and T real. For every θ ≥ 0,
P(Σ Y_i ≤ T) ≤ e^{θT}·Π E e^{−θY_i} and P(Σ Y_i ≥ T) ≤ e^{−θT}·Π E e^{θY_i}.
*Proof.* Markov's inequality for the non-negative variable e^{−θΣY_i} gives P(e^{−θΣY_i} ≥ e^{−θT}) ≤ e^{θT}·E e^{−θΣY_i},
and the expectation factorises by independence. The second bound is the same with θ replaced by −θ. ∎

**A2 (Hoeffding's lemma).** If a ≤ Y ≤ b and E Y = 0, then E e^{λY} ≤ e^{λ²(b−a)²/8} for every real λ.
*Proof.* If a = b, then Y = 0. Otherwise a ≤ 0 ≤ b. By convexity, e^{λy} ≤ ((b − y)e^{λa} + (y − a)e^{λb})/(b − a) on
[a, b], so with E Y = 0, E e^{λY} ≤ (b·e^{λa} − a·e^{λb})/(b − a) = e^{L(h)}, where h = λ(b − a), p = −a/(b − a) ∈ [0, 1]
and L(h) = −hp + ln(1 − p + p·e^h). Here L(0) = L′(0) = 0 and L″(h) = ρ(1 − ρ) ≤ ¼ with ρ = p·e^h/(1 − p + p·e^h).
Taylor's theorem gives L(h) ≤ h²/8. ∎

**A3 (Hoeffding's inequality).** If Y_1, …, Y_N are independent with a_i ≤ Y_i ≤ b_i and S = Σ Y_i, then for u ≥ 0
P(S ≤ E S − u) ≤ exp(−2u²/Σ(b_i − a_i)²), and the same bound holds for P(S ≥ E S + u).
*Proof.* Apply A1 to Y_i − E Y_i and A2 to each factor: the bound is exp(−λu + λ²·Σ(b_i − a_i)²/8) for every λ ≥ 0;
take λ = 4u/Σ(b_i − a_i)². ∎

**A4 (Sperner's theorem).** An antichain 𝒜 of subsets of a k-element set has at most C(k, ⌊k/2⌋) members.
*Proof.* Each of the k! maximal chains ∅ ⊂ {x_1} ⊂ … ⊂ {x_1, …, x_k} contains at most one member of 𝒜, and a set of
size r lies on r!(k − r)! of them. So Σ_{A∈𝒜} |A|!(k − |A|)! ≤ k!, that is Σ_{A∈𝒜} 1/C(k, |A|) ≤ 1, and every term is
≥ 1/C(k, ⌊k/2⌋). ∎ (Sign vectors in {+1, −1}^k correspond to subsets, the positions of +1, and the coordinatewise order
to inclusion.)

## Sources

- R. M. Karp, R. Motwani, N. Nisan (1993). *Probabilistic analysis of network flow algorithms*. Mathematics of
  Operations Research 18(1), 71–97. [doi:10.1287/moor.18.1.71](https://doi.org/10.1287/moor.18.1.71). Abstract and an
  author's copy of the journal text read.
- R. M. Karp, R. Motwani, N. Nisan (1988). *Probabilistic analysis of network flow algorithms*. Technical report,
  Computer Science Division, University of California, Berkeley. The pages listed in [Literature](#literature) were
  read.
- R. M. Karp (1979). *The probabilistic analysis of combinatorial optimization algorithms*. Tenth International
  Symposium on Mathematical Programming. Base. Not accessible; known from the citation in the report above.
- G. R. Grimmett, D. J. A. Welsh (1982). *Flow in networks with random capacities*. Stochastics 7(3), 205–229.
  [doi:10.1080/17442508208833219](https://doi.org/10.1080/17442508208833219). Base (flow-value limits, Theorem 3.3).
  §§1 and 3 read (author's copy).
- G. R. Grimmett, W.-C. S. Suen (1982). *The maximal flow through a directed graph with random capacities*.
  Stochastics 8(2), 153–159. [doi:10.1080/17442508208833234](https://doi.org/10.1080/17442508208833234). Base
  (flow-value limits, Theorems 1–2). Read in full (author's copy).
- L. R. Ford, D. R. Fulkerson (1956). *Maximal flow through a network*. Canadian Journal of Mathematics 8, 399–404.
  [doi:10.4153/CJM-1956-045-5](https://doi.org/10.4153/CJM-1956-045-5). The max-flow min-cut theorem; the part used here
  is proved in Lemma 0. Not read for this note.
- P. Erdős (1945). *On a lemma of Littlewood and Offord*. Bulletin of the American Mathematical Society 51(12),
  898–902. [doi:10.1090/S0002-9904-1945-08454-7](https://doi.org/10.1090/S0002-9904-1945-08454-7). Cited for the origin
  of the antichain argument in (c), which is proved here in full. Not read for this note.
- E. Sperner (1928). *Ein Satz über Untermengen einer endlichen Menge*. Mathematische Zeitschrift 27, 544–548.
  [doi:10.1007/BF01171114](https://doi.org/10.1007/BF01171114). A4; proved above. Not read for this note.
- W. Hoeffding (1963). *Probability inequalities for sums of bounded random variables*. Journal of the American
  Statistical Association 58(301), 13–30. [doi:10.1080/01621459.1963.10500830](https://doi.org/10.1080/01621459.1963.10500830).
  A2–A3; proved above. Not read for this note.
- H. Chernoff (1952). *A measure of asymptotic efficiency for tests of a hypothesis based on the sum of observations*.
  The Annals of Mathematical Statistics 23(4), 493–507. [doi:10.1214/aoms/1177729330](https://doi.org/10.1214/aoms/1177729330).
  A1; proved above. Not read for this note.
