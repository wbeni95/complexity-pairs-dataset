# Optimal LZ77-style parsing with k repeat-offset slots: enumeration vs dynamic programming over (position, slots)

**Type:** T2 (naive super-exponential → polynomial, for every fixed k) ·
**Verification:** V2 (exact operation counts, with rivals) ·
**Provenance:** literature (folklore; Bloom 2015, a blog post, not peer-reviewed; see [Background](#background)).
Every claim of this entry is proved in [PROOFS.md](PROOFS.md). The worst-case bounds that the entry links to are in
two theorem notes labelled undetermined: they may be our own results, but sources that might contain them could not
be read (two journal papers, because the publisher's site refused automated access, and a 2010 thesis, which is not
consultable until 2050; see [Related notes](#related-notes)).

**Problem.** A string s of length n over an integer alphabet is coded from left to right by tokens. The coder keeps
k *repeat-offset slots* R = (R[0], …, R[k−1]), initially (1, …, 1). At position i the tokens are:

| Token | Allowed if | Cost | Slots afterwards |
|---|---|---|---|
| literal | always | 9 | unchanged |
| repeat of slot j, length L | R[j] ≤ i, L ≥ REPMIN, the next L symbols equal those at distance R[j] | 3 + j + γ(L) | slot j moves to the front |
| new match, distance d, length L | 1 ≤ d ≤ i, L ≥ 2, the next L symbols equal those at distance d | 2 + γ(L−1) + γ(d) | d is pushed to the front, the last slot is dropped |

Here γ(x) = 2⌊log₂ x⌋ + 1 is the length of the Elias gamma code of x. Copies may overlap the text being coded
(d < L is allowed), and equal values may sit in several slots. The costs are *static*: they depend only on the
token. The task is to find the minimum total cost of a parse of the whole string. k ≥ 1 and REPMIN ≥ 1 are fixed
parameters; every complexity statement is for fixed k.

| Algorithm | Time (n = \|s\|, k fixed) | Space | Implementation |
|---|---|---|---|
| Enumeration of all parses | 2^Θ(n log n) token evaluations (and time) in the worst case; exactly Σ_{j=1}^{m} (j−1)!(j+2) on the V2 family (n = 3m) | O(n²(n + k)): at most n(1 + kn + n²/4) + 1 stack entries | [enumeration.py](implementations/enumeration.py) |
| DP over (position, slot contents) | O(n^(k+2)) relaxations (and time) on every input, tight on aⁿ; exactly (4m³ − 15m² + 29m − 9)/3 on the V2 family (k = 2) | O(n^(k+1)) states | [slot_dp.py](implementations/slot_dp.py) |

**Why the DP is exact (proof).** Call a pair (position i, slot tuple R) a *state*. Whether a token is allowed at
(i, R), its length, its cost and the next slot tuple depend only on (i, R) and the token, because the costs are
static and the match test reads only s, i and the distance. So the parses are exactly the paths from
(0, (1, …, 1)) to a state at position n in the graph whose arcs are the allowed tokens, and the cost of a parse is
the total cost of its arcs. Every arc moves to a larger position, so the graph is acyclic and the positions are a
topological order. The DP processes positions from left to right. When it reaches position i, every arc into a state
at i starts at an earlier position, which has already offered its value. By induction on i, the stored value of
(i, R) is the cheapest path to (i, R), and the minimum over the states at position n is the optimum.

New matches from (i, R) lead to (i + L, (d, R[0], …, R[k−2])) at a cost that does not depend on R[k−1]. Among the
states at position i with the same first k − 1 slots, the cheapest one therefore offers the smallest value to each
such successor. The DP generates new matches only from that state (*prefix grouping*), which changes no minimum.
The full proof is in [PROOFS.md](PROOFS.md), section 5.

**Why it is polynomial for fixed k.** A slot holds 1 or the distance d ≤ i − 2 of an earlier new match, so
position i has at most n^k states and n^(k−1) prefix groups. Every token at position i has length at most n − i, so
a state makes at most 1 + k(n − i) relaxations (literal and repeats) and a group at most i(n − i) (new matches). Over
the n positions this is O(n^(k+2)), and the work that is not counted adds O(k·T + n²) for T relaxations
([PROOFS.md](PROOFS.md), sections 6.2 and 6.3). The order is attained on aⁿ, and the number of states is at most
3 + Σ_{j=1}^{n−2} j^k on every input, for every REPMIN ≥ 1
([theorems/lz77-repeat-slots-state-bounds](../../theorems/lz77-repeat-slots-state-bounds/), Theorem C).

**Why enumeration is super-exponential.** In F1(m) = x₁ab x₂ab … x_m ab, where every x_j occurs only once, block
j ≥ 2 can be coded by two literals or by a new match of length 2 at any distance 3, 6, …, 3(j−1). So there are at
least m! parses, for every k and REPMIN. With fresh padding this gives at least ⌊n/3⌋! = 2^((1/3 − o(1)) n log₂ n)
token evaluations (for n ≥ 1). In the other direction, for n ≥ 1, a parse is a composition of n into token
lengths, with at most n + k + 1 tokens of each length at each position. A partial parse is determined by the parse
that completes it with literals and by its number of tokens. Together these give at most
(n + 1)·2^(n−1)·(n + k + 1)^n search-tree nodes, which is 2^O(n log n); the work that is not counted adds
O((n + k)(E + 1) + n²) for E evaluations ([PROOFS.md](PROOFS.md), sections 6.4 to 6.6).

**The V2 family and its exact counts.** generate_scaling gives F1(m) with k = 2 and REPMIN = 3. Every match token in
F1 has length exactly 2: no match can start at or cover a fresh symbol, a match starting at a b would have length 1,
and a match starting at the a of block j has distance 3t and stops at x_{j+1} ≠ x_{j−t+1} (for j = m, at the end of
the string). So no repeat is ever allowed, and the counts can be derived exactly ([PROOFS.md](PROOFS.md),
sections 1 to 3):
- *Enumeration.* A prefix ending at the start of block j can be extended by j + 2 tokens inside the block (x_j; the
  literal a or one of j − 1 new matches; the literal b after the literal a). There are (j−1)! such prefixes, so the
  count is Σ_{j=1}^{m} (j−1)!(j+2) = Σ_{j=1}^{m} j! + 2Σ_{j=0}^{m−1} j!, with exactly m! complete parses, for
  every k. Since Σ_{j=0}^{N} j! ≤ 2·N! for N ≥ 1, the count lies between m! + 3(m−1)! and m! + 3(m−1)! + 6(m−2)!
  (m ≥ 3), i.e. it is m!(1 + 3/m + O(1/m²)).
- *DP.* The slot tuples inside block j are (3u₀, …, 3u_{c−1}, 1, …, 1) with 0 ≤ c ≤ max(0, min(k, j−2)) and
  1 ≤ u_a ≤ j−2−a. There are S(j) = Σ_c (j−2)!/(j−2−c)! of them (so S(1) = S(2) = 1), and G(j) prefix groups (the
  same sum with c ≤ max(0, min(k−1, j−2))). The count is
  Σ_j 3S(j) + Σ_{j≥2} (j−1)G(j), which equals (4m³ − 15m² + 29m − 9)/3 for k = 2.

**Verification.**
- *V1:* the validator runs n = 0..8, 10, 12 and 14, with 6 instances per size, k ∈ {1, 2, 3} and REPMIN ∈ {1, 2, 3}.
  The instances are aⁿ, random strings over 2–4 letters, periodic strings with substitutions, copy strings with
  overlapping copies, words separated by fresh symbols, and the V2 family. The enumeration runs up to n = 8, the DP
  on every size. The `check` oracle is independent of both implementations: a backward memoised recursion over
  (position, slots) with its own match test, exact for n ≤ 24.
- *Tests* ([test_entry_lz77_repeat_slots.py](../../tests/test_entry_lz77_repeat_slots.py)):
  - every binary string of length ≤ 7 for k = 1, 2, 3 and REPMIN = 1, 2, 3: enumeration = DP = oracle;
  - seeded instances up to n = 24; the match-length table against its definition (length ≤ 8);
  - the closed forms of both V2 counts (the enumeration also for k = 1, 3), the slot tuples of every block of F1,
    and the parse counts of F1 (at least m!, exactly m! for REPMIN = 3, with padding);
  - the per-position state bound max(1, (i−2)^k) and the total 3 + Σ_{j=1}^{n−2} j^k (REPMIN = 1, 2, 3), and the
    lower bound on aⁿ;
  - on every binary string of length 1..7: at most n[n^k(1 + kn) + n^(k+1)] relaxations, and at most
    (n + 1)·2^(n−1)·(n + k + 1)^n search-tree nodes;
  - the maximum stack of the enumeration, at most n(1 + kn + n²/4) + 1 entries (every binary string of length 1..8,
    aⁿ for n ≤ 11, or n ≤ 9 when k ≥ 2 and REPMIN = 1, F1(m) for m ≤ 7);
  - the work that is not counted, in both algorithms (copies of their loops with every step counted);
  - rejection of wrong outputs.
- *V2 (exact counts):* the implementations count their own operations, and the harness reports them.
  - Enumeration: fitted on n = 12..24 against (n/3 + 3)·(n/3 − 1)!, which equals the exact count up to a factor
    in [1, 1 + 6/((m + 3)(m − 1))]. Rivals 2ⁿ, (n/3 + 1)! and n·(n/3)! are rejected. The slope fit over five sizes
    is a consistency check; the factorial growth rests on the exact count, which is proved.
  - DP: fitted on n = 30..120 against the exact polynomial. Rivals n², n⁴ and 2^(n/3) are rejected. The shape
    diagnostic identifies n³ exactly from the counts for n = 3..60.

**Caveats.**
- What is counted: one cost addition per candidate, i.e. token evaluations of the enumeration and relaxations of the
  DP. Not counted: the match-length table that both build, the scan for distances with a match, the k slot tests
  per state, and dictionary or stack operations. This work is bounded in [PROOFS.md](PROOFS.md), sections 6.3 and
  6.6.
- The model is an abstraction with static costs. With adaptive (history-dependent) prices, a DP that keeps one value
  per (position, slots) is not exact
  ([counterexample](../../theorems/lz77-repeat-slots-exact-pruning/#hypotheses-that-cannot-be-dropped)). The entry
  makes no claim about any real compression format.
- The exponent of the DP grows with k. The entry makes no claim for k growing with n.
- The super-exponential lower bound for the enumeration uses an alphabet of n/3 + O(1) symbols.

## Related notes

Both are labelled undetermined: they may be our own results beyond the folklore DP, but sources that might contain
them could not be read, so this could not be checked: the journal version of the paper on dictionary-symbolwise
flexible parsing and the full text of Langiu's paper on the "Zip case" (the publisher's site refused automated
access), and a 2010 PhD thesis titled "Parsing algorithms for data compression" (not consultable until 2050).
- [lz77-repeat-slots-state-bounds](../../theorems/lz77-repeat-slots-state-bounds/): exact state and relaxation bounds
  (at most 3 + Σ_{j=1}^{n−2} j^k states; n^(k+2)/(k+2) + O(n^(k+1)) relaxations in the worst case, attained on aⁿ;
  every REPMIN ≥ 1). For REPMIN ≥ 2, an exact pruning rule keeps only 2n − 2 states on aⁿ (n ≥ 3), but Θ(n^(k+1)) in
  the worst case over unbounded alphabets.
- [lz77-repeat-slots-exact-pruning](../../theorems/lz77-repeat-slots-exact-pruning/): an optimum-preserving
  pruning rule (G3) for every k and REPMIN ≥ 2, its generalisation G3* to other static costs, and counterexamples
  for the hypotheses (among them REPMIN = 1, where one-symbol repeats break the rule).

## Background

Cited; not claims of this entry.
- C. Bloom's 2015 post states that when the dynamic "state" of a parse is small, a truly optimal parse can be
  computed by dynamic programming with a table of size N·S for a state of size S, and that as soon as even one
  "repeat match" is introduced, S is too big. His A* parser labels its nodes by {state, pos}, where the state
  includes only the repeat-match offsets and a few further bits, and discards paths that cannot be better than the
  current best path by more than a threshold; the higher the threshold, the more approximate he calls the parse. The
  post gives no correctness proof. This entry credits the DP over (position, slot contents) to this post (folklore;
  not peer-reviewed), and the {Pos, State} parser with a general adaptive state to the 2011 post below.
- C. Bloom's 2011 post (Part 3 of "LZ Optimal Parse with A Star") describes a forward optimal parse whose nodes are
  {Pos, State} pairs, with a general adaptive state, keeps one cheapest arrival per node, and stops exploring an arrival whose cost exceeds the best
  cost at the same position by more than a threshold, assuming that starting from a different state cannot help more
  than some amount.

Every claim of this entry is proved in [PROOFS.md](PROOFS.md) or in the linked notes, and checked by the scripts.

**Sources.** C. Bloom, "01-23-15 - LZA New Optimal Parse", cbloom rants (blog, 2015) · C. Bloom, "12-17-11 - LZ
Optimal Parse with A Star Part 3" (blog, 2011). Links are in entry.json.
