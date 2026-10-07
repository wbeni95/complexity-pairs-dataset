# Proofs: chromatic number, subset DP over independent sets vs inclusion–exclusion

This file proves the claims that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md`, the docstrings of the code and the harness): correctness of both algorithms, the exact counts
3^n − 2^n and (2χ(G) + 2)·2^n − 2, the time, space and bit-size bounds, and the facts used by the V1 oracle. Each
section names the deterministic checks that re-run its computable facts and the ranges they cover. A check covers
only its range; the written proof covers the general statement.

The statements listed under `background` in `entry.json` (NP-completeness, Lawler's refinement and the Moon–Moser
bound, later refinements, the polynomial-space variant and the chromatic polynomial) are cited, not proved here. The
V2 runtime fits are measured data.

Credit: the subset DP goes back at least to Lawler (1976); the inclusion–exclusion algorithm is Björklund, Husfeldt
& Koivisto's (2009).

## 0. Conventions

G = (V, E) is a simple undirected graph on V = {0, …, n − 1}; vertex sets are n-bit masks, and operations on masks
are unit cost. χ(G[S]) denotes the chromatic number of the subgraph induced by S, with χ(G[∅]) = 0. A set is
*independent* if it contains no edge. For the subset DP the counted unit is an *inner iteration* (one pass of the
submask loop); for inclusion–exclusion the counted units are the *arithmetic operations* on the values a, p and
`total` (additions, subtractions, multiplications). The checks count executions of the corresponding source lines of
the unchanged code with `sys.settrace` (`tests/test_proofs_chromatic.py`, class `LineCounts`).

## 1. Subset DP over all independent sets (`subset_dp.py`)

**1.1 Independence table.** For S ≠ ∅ with lowest vertex v, S is independent iff S − {v} is independent and v has
no neighbour in S − {v}. The code applies this rule in increasing order of S (S − {v} < S), starting from
`independent[0] = True`.

**1.2 Lemma.** For S ≠ ∅, χ(G[S]) = 1 + min over non-empty independent T ⊆ S of χ(G[S − T]).

*Proof.* (≤) A proper colouring of G[S − T] with c colours plus one new colour on the independent set T is a proper
colouring of G[S] with c + 1 colours. (≥) An optimal colouring of G[S] uses χ(G[S]) ≥ 1 colours, each on a
non-empty independent class; removing one class T leaves a proper colouring of G[S − T] with χ(G[S]) − 1 colours. ∎

**1.3 Correctness.** The code computes `chi[S]` in increasing order of S; for a non-empty submask T of S,
S ^ T = S − T < S, so `chi[S ^ T]` is final. `best` starts at n ≥ |S| ≥ χ(G[S]) and is lowered to the minimum of
`chi[S ^ T] + 1` over the independent non-empty submasks T (every single vertex is one), which is χ(G[S]) by 1.2.
It returns `chi[2^n − 1]` = χ(G); for n = 0 the loop is empty and it returns `chi[0]` = 0.

**1.4 Exact count.** The loop `T = S; while T: …; T = (T − 1) & S` visits every non-empty submask of S exactly once,
in decreasing order: listing the bits of S from low to high identifies the submasks of S with the integers
0..2^|S| − 1 in an order-preserving way, and (T − 1) & S is the image of the predecessor (T − 1 clears the lowest set
bit of T and sets all bits below it; & S keeps those of S). Hence the number of inner iterations is

  Σ_S (2^|S| − 1) = Σ_k C(n, k) 2^k − 2^n = 3^n − 2^n

on every input (binomial theorem), each O(1) on masks, and the independence table takes 2^n − 1 steps. Total
Θ(3^n) time on every input.

**1.5 Space.** Two lists of 2^n entries (`independent`, `chi`) and n adjacency masks: Θ(2^n).

**Checks.** `tests/test_proofs_chromatic.py`: class `Correctness` (both algorithms equal an independent
backtracking oracle on every graph with n ≤ 5, on 40 seeded graphs with n = 6..10 including empty and complete
graphs, and on the harness families of section 4, n ≤ 10); class `LineCounts`, `test_dp_inner_iterations`
(executions of the inner-loop test = 3^n − 2^n and of the table line = 2^n − 1, n = 0..9); class `WorkingMemory`
(tracemalloc peak between 8·2^n and 32·2^n bytes, n = 6..14). `experiments/2026-10-07_chromatic_probe.py` and
`experiments/2026-10-06c_value_reach_probe.py` count the same loop for n = 6..12 and n = 7..10.

## 2. Inclusion–exclusion (`inclusion_exclusion.py`)

Let a(S) be the number of non-empty independent sets contained in S.

**2.1 Recurrence.** For v ∈ S, a(S) = a(S − {v}) + a(S − N[v]) + 1, where N[v] is v with its neighbours: the
non-empty independent subsets of S either avoid v (counted by a(S − {v})) or contain v, and those are {v} ∪ J with
J an independent subset of S − N[v], empty (1 set) or not (a(S − N[v]) sets). The code uses the lowest vertex v of S;
S ^ low = S − {v} and S & ~closed[v] = S − N[v] are smaller than S, so their values are final; a(∅) = 0. It also
stores whether n − |S| is even (adding one vertex flips the parity).

**2.2 Lemma (inclusion–exclusion).** For k ≥ 1 let c_k = Σ_S (−1)^(n−|S|) a(S)^k. Then c_k is the number of
k-tuples (I_1, …, I_k) of non-empty independent sets with I_1 ∪ … ∪ I_k = V.

*Proof.* a(S)^k counts the k-tuples of non-empty independent sets contained in S, i.e. with union U ⊆ S. A tuple
with union U is therefore counted with total weight Σ_{U ⊆ S ⊆ V} (−1)^(n−|S|) = Σ_{R ⊆ V−U} (−1)^(|V−U|−|R|) =
(1 − 1)^|V−U|, which is 1 if U = V and 0 otherwise. ∎

**2.3 Lemma.** For n ≥ 1 and k ≥ 1, c_k > 0 iff χ(G) ≤ k.

*Proof.* (⇐) An optimal colouring has χ(G) non-empty independent colour classes covering V; together with k − χ(G)
repetitions of the first class they form a k-tuple counted by c_k. (⇒) Given a counted tuple, give each vertex the
index of the first set that contains it. Two vertices with the same colour i lie in the independent set I_i, so
they are not adjacent: a proper colouring with at most k colours. ∎

**2.4 Correctness.** Round k (k = 1, 2, …) multiplies every `p[S]` (initially 1) by a(S), so `p[S]` = a(S)^k, and
sums them with the signs (−1)^(n−|S|): `total` = c_k. The function returns the first k with c_k > 0, which is χ(G)
by 2.3; since χ(G) ≤ n the loop always returns, and the final `raise` is unreachable. For n = 0 it returns 0.

**2.5 Exact count.** The table pass makes two additions for each of the 2^n − 1 non-empty sets. Each round makes
one multiplication and one addition or subtraction per set, 2·2^n operations, and there are χ(G) rounds. In total

  2(2^n − 1) + 2χ(G)·2^n = (2χ(G) + 2)·2^n − 2

arithmetic operations (also for n = 0, where both sides are 0). Since χ(G) ≤ n this is O(n 2^n), and Θ(n 2^n)
whenever χ(G) = Θ(n). The mask operations of the table pass (S & −S, bit_length, S ^ low, S & ~closed[v], the
parity flag) are Θ(2^n).

**2.6 Sizes of the integers and bit complexity.** a(S) ≤ 2^|S| − 1 < 2^n, so in round k ≤ χ(G) every table entry
a(S)^k is below 2^(nk) and has at most n·χ(G) bits. The running sum satisfies |total| ≤ Σ_S a(S)^k < 2^n·2^(nk), so
it has at most n(χ(G) + 1) bits. With schoolbook arithmetic, the multiplication in round k (an entry of at most
n(k − 1) bits times one of at most n bits) costs O(n^2 k) bit operations and the addition O(nk); over the 2^n sets
and the χ(G) ≤ n rounds this is O(2^n n^2 χ(G)^2) = O(n^4 2^n) bit operations, plus O(n 2^n) for the table pass.

**2.7 Space.** Three lists of 2^n entries (`a`, `even`, `p`) and n closed neighbourhoods: Θ(2^n) numbers.

**Checks.** `tests/test_proofs_chromatic.py`: class `Correctness` (as in section 1); class `CoverIdentity` (c_k
equals the number of covering k-tuples, counted by enumeration, and c_k > 0 iff χ ≤ k, for every graph with
n ≤ 4 and k = 1, 2, 3; the recurrence 2.1 for every S and v on 48 seeded graphs with n ≤ 8); class `LineCounts`,
`test_ie_arithmetic_operations` (the table line runs 2^n − 1 times, the multiplication line χ·2^n times, the two
accumulation lines χ·2^n times together, and the weighted sum is (2χ + 2)·2^n − 2, on 55 seeded graphs with
n = 0..10); `test_bit_lengths` (largest table entry at most nχ bits, largest |total| at most n(χ + 1) bits, read from
the running code on 36 seeded graphs n = 1..9 and the V2 instances n = 10, 11, 12); class `WorkingMemory`
(tracemalloc peak between 8·2^n and 128·2^n bytes, n = 6..14).

## 3. The pair

3^n − 2^n against (2χ(G) + 2)·2^n − 2 ≤ (2n + 2)·2^n: the ratio grows without bound, (3/2)^n/(2n + 2) → ∞, and both
counts are at least 2^n for n ≥ 2 (3^n ≥ 2^(n+1) from n = 2 on), so the improvement is exponential to smaller
exponential (tag T8).

## 4. Facts used by the harness

**4.1 The oracle.** `_colourable(n, edges, k)` tries colours in a fixed vertex order and lets a vertex take only the
colours 0..min(k, used + 1) − 1, where `used` is the number of colours opened so far. Every proper k-colouring
becomes one of this form after renaming the colours in the order of their first use along the vertex order, so the
search finds a k-colouring iff one exists. `check` accepts an output c iff c colours suffice and c − 1 do not, i.e.
iff c = χ(G).

**4.2 The instance families.** The empty graph on n ≥ 1 vertices has χ = 1 and the complete graph χ = n (all vertices
pairwise adjacent). The cycle C_n (n ≥ 3) has χ = 2 for even n (alternate colours) and χ = 3 for odd n (an odd cycle
has no proper 2-colouring, since colours must alternate around it; three colours suffice). A bipartite graph has
χ ≤ 2. A disjoint union of t ≥ 1 triangles plus isolated vertices has χ = 3.

**Check.** `tests/test_proofs_chromatic.py`, class `Correctness`, `test_harness_families` (n = 1..10).

## 5. Computed facts about the V2 timing instances

The seeded V2 instances (G(n, 0.8), seeds `"<id>|v2|<n>"`) have χ = 4, 5, 4, 6, 6, 7, 7, 8, 8, 8, 8, 9, 10 for
n = 6..18, so χ/n lies between 1/2 (n = 8, 16) and 5/7 ≈ 0.714 (n = 7) there. This is a computed property of these
instances, not an asymptotic statement about G(n, 0.8). Since a(S) ≤ a(V) and the rounds stop at k = χ, the largest
table entry is a(V)^χ; on these instances it has far fewer than nχ bits (for example 57 bits at n = 18, against the
bound 180).

**Check.** `tests/test_proofs_chromatic.py`, class `TimingInstances` (χ by the unchanged inclusion–exclusion
implementation and 1/2 ≤ χ/n ≤ 5/7 in exact fractions, n = 6..18; the bit length of a(V)^χ, with a(V) counted by
enumerating all vertex subsets, for n = 13..18, 57 at n = 18). `experiments/2026-10-07_chromatic_probe.py` prints the
same χ values.
