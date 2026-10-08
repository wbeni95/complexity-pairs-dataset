# Proofs: optimal LZ77-style parsing with k repeat-offset slots, enumeration vs slot DP

This file proves every claim that this entry makes about its problem and its two algorithms (in `entry.json`,
`README.md` and the docstrings of the code): the correctness of both algorithms, every stated time and space bound,
the exact operation counts on the V2 family, the facts used by the V1 oracle, and the factual caveats. Sections 2 and
3 prove the exact counts; the other sections prove the rest. Statements about the literature are not claims of this
entry: they are listed under `background` in `entry.json`, with their sources, and are not proved here. Two results
are used from the theorem notes of this repository, which prove them: the state bounds of
[theorems/lz77-repeat-slots-state-bounds](../../theorems/lz77-repeat-slots-state-bounds/) (Theorem C) and the
adaptive-price counterexample of
[theorems/lz77-repeat-slots-exact-pruning](../../theorems/lz77-repeat-slots-exact-pruning/) (Proposition 6(b)).
Each proof is followed by the deterministic tests or scripts that check its computable facts and the ranges they
check. A check covers only those ranges; the proofs cover the general statements.

## 0. Definitions, cost model and counting convention

**Problem.** An instance is (s, k, REPMIN): a string s = s[0] … s[n−1] of integers, an integer k ≥ 1 and an integer
REPMIN ≥ 1. γ(x) = 2⌊log₂ x⌋ + 1 for integers x ≥ 1; γ is nondecreasing. A *slot tuple* is R = (R[0], …, R[k−1])
with positive integer entries, and 1^k = (1, …, 1). A *state* is a pair (i, R) with 0 ≤ i ≤ n. At a state (i, R) with
i < n the allowed *tokens* are:

| Token | Allowed if | Cost | Next state |
|---|---|---|---|
| literal | always | 9 | (i + 1, R) |
| repeat of slot j, length L | R[j] ≤ i, L ≥ REPMIN, i + L ≤ n, s[i+t] = s[i+t−R[j]] for 0 ≤ t < L | 3 + j + γ(L) | (i + L, (R[j], R[0..j−1], R[j+1..k−1])) |
| new match, distance d, length L | 1 ≤ d ≤ i, L ≥ 2, i + L ≤ n, s[i+t] = s[i+t−d] for 0 ≤ t < L | 2 + γ(L−1) + γ(d) | (i + L, (d, R[0..k−2])) |

A *parse* is a sequence of tokens, each allowed at the state that the previous ones lead to, from (0, 1^k) to a state
at position n. Its cost is the sum of its token costs, and OPT(s) is the minimum cost of a parse. The all-literal
parse always exists, so OPT(s) ≤ 9n; every token costs at least 4, so OPT(s) ≥ 0. A *match token* is a repeat or a
new match. For 1 ≤ d ≤ i ≤ n, ml(i, d) is the largest L with i + L ≤ n and s[i+t] = s[i+t−d] for all t < L. A repeat
of slot j with length L is allowed at (i, R) iff R[j] ≤ i and REPMIN ≤ L ≤ ml(i, R[j]); a new match (d, L) iff
1 ≤ d ≤ i and 2 ≤ L ≤ ml(i, d).

**Cost model** (CONTRIBUTING, "Machine model"). Elementary operations cost O(1): list allocation, append and
indexing; dictionary operations (one operation each, plus hashing the key); arithmetic and comparisons on the
integers that occur (positions and distances at most n; every token costs at most 9 + k + 2γ(n) and a parse has at
most n tokens, so every cost value is at most n(9 + k + 2γ(n))). `int.bit_length` on such integers is elementary.
Building, slicing, comparing or hashing a tuple of length at most k costs O(k) elementary operations, which is O(1)
for fixed k. No library routine with a non-trivial cost is used, so no machine-model assumption is needed.

**Counting convention.** `implementations/enumeration.py` adds 1 to `evaluations` immediately before each
`stack.append` that pushes a child (one literal, one per (slot, length) of a repeat, one per (distance, length) of a
new match); the root is not counted. `implementations/slot_dp.py` adds 1 to `relaxations` immediately before each
call of `_offer` (one per state for the literal, one per (slot, length) for the repeats, one per (prefix group,
distance, length) for the new matches). Both counters are only incremented and returned; they do not influence
what the functions compute. `harness.reported_cost(output)` returns `output[1]`, the count.

## 1. The family F1 and its match tokens

**Definition.** For m ≥ 0 and pad ≥ 0, F1(m) = x₁ a b x₂ a b … x_m a b, followed by `pad` further symbols, where
a = 0, b = 1, x_j = j + 1 and the padding symbols are m + 2, …, m + 1 + pad (`harness.f1_string(m, pad)`). Block j
(1 ≤ j ≤ m) occupies the positions 3j − 3 (x_j), 3j − 2 (a) and 3j − 1 (b). Every x_j and every padding symbol
occurs once (*fresh*). For m ≥ 1, F1(m) with padding uses m + 2 + pad distinct symbols, and without padding n = 3m
and the alphabet has n/3 + 2 symbols (F1(0) with padding uses pad symbols).

**Lemma 1.** In F1(m) (with any padding), for every position i and distance 1 ≤ d ≤ i:
1. if s[i] is fresh, ml(i, d) = 0;
2. if i = 3j − 2 (the a of block j), ml(i, d) = 2 if d = 3t with 1 ≤ t ≤ j − 1, and 0 otherwise;
3. if i = 3j − 1 (the b of block j), ml(i, d) = 1 if d = 3t with 1 ≤ t ≤ j − 1, and 0 otherwise.

Consequently every new match, and for REPMIN ≥ 2 every match token, has length exactly 2, starts at the a of a
block j ≥ 2 and has a distance 3t with 1 ≤ t ≤ j − 1 (with REPMIN = 1, repeats of length 1 can also occur, from m = 3 on); with
REPMIN ≥ 3 no repeat is ever allowed; and every new match (3t, 2) at the a of block j ≥ 2 is allowed, whatever the
slots.

*Proof.* A fresh symbol has no earlier copy, so s[i] ≠ s[i − d]. At i = 3j − 2, s[i − d] = a iff i − d is the a of
an earlier block t′, i.e. d = 3(j − t′) with 1 ≤ j − t′ ≤ j − 1; then s[i+1] = b = s[i+1−d], and the match stops
at length 2: either i + 2 = n, or s[i+2] is the fresh symbol x_{j+1} (j < m) or a padding symbol (j = m), and a fresh
symbol never equals an earlier one. The case i = 3j − 1 is the same, one step later: s[i − d] = b iff d = 3t with
1 ≤ t ≤ j − 1, and s[i + 1] is fresh or i + 1 = n. ∎

**Check.** `tests/test_entry_lz77_repeat_slots.py`, `test_f1_has_m_factorial_parses` (the symbol count m + 2 + pad,
m = 1..6, pad ≤ 2); the closed forms of sections 2 and 3, which rest on Lemma 1, in `test_v2_closed_forms`.

## 2. Enumeration on F1: Σ_{j=1}^{m} (j−1)!(j+2) token evaluations (V2)

**Statement.** On F1(m) without padding, with REPMIN = 3 and any k ≥ 1, `lz77_slots_enumeration` makes exactly
Σ_{j=1}^{m} (j−1)!(j+2) = Σ_{j=1}^{m} j! + 2Σ_{j=0}^{m−1} j! token evaluations, and F1(m) has exactly m! complete
parses. For m ≥ 3,

    m! + 3(m−1)!  ≤  Σ_{j=1}^{m} (j−1)!(j+2)  ≤  m! + 3(m−1)! + 6(m−2)!,

so the count is m!(1 + 3/m + O(1/m²)) = Θ(m!), and it equals (m + 3)(m − 1)! = m! + 3(m−1)! (the V2 `cost` with
n = 3m) up to a factor in [1, 1 + 6/((m + 3)(m − 1))].

**Proof.** Every popped stack entry is a node of the search tree (a partial parse), every node is pushed once (the
root initially, every other node by one counted push), and nodes at position n push nothing. So the count is the
number of non-root nodes. By Lemma 1, at the start 3j − 3 of block j a node pushes only the literal x_j (no
distance has ml ≥ 2 and no slot has ml ≥ REPMIN); at the a (3j − 2) it pushes the literal a and the j − 1 new matches
(3t, 2), t = 1, …, j − 1 (each distance has exactly one length, and no repeat has ml ≥ 3); at the b (3j − 1),
reached only by the literal a, it pushes only the literal b (ml ≤ 1 < 2). So every node at the start of block j
causes exactly 1 + j + 1 = j + 2 pushes inside the block and has exactly j descendants at the start of block j + 1
(through the literals a, b, or through one of the j − 1 matches); for j = 1 there is no match, so 1 descendant. By
induction the number of nodes at the start of block j is (j − 1)!, so block j contributes (j − 1)!(j + 2) pushes, and
the number of nodes at position n = 3m, i.e. of complete parses, is m!. Since (j − 1)!(j + 2) = j! + 2(j − 1)!, the
sum is Σ_{j=1}^{m} j! + 2Σ_{j=0}^{m−1} j!. The count does not depend on k: neither literals nor new matches read
the slots.

*Sandwich.* Σ_{j=0}^{N} j! ≤ 2·N! for N ≥ 1: true for N = 1 (2 ≤ 2), and Σ_{j=0}^{N+1} j! ≤ 2·N! + (N + 1)! ≤
2(N + 1)! because 2·N! ≤ (N + 1)!. Write the count as m! + 3(m−1)! + R with
R = Σ_{j=1}^{m−2} j! + 2Σ_{j=0}^{m−2} j! ≥ 0. For m ≥ 3 (N = m − 2 ≥ 1), R ≤ 2(m−2)! + 4(m−2)! = 6(m−2)!. Dividing by
(m + 3)(m − 1)! = m! + 3(m − 1)! gives the ratio bound 6(m − 2)!/((m + 3)(m − 1)!) = 6/((m + 3)(m − 1)). ∎

**Check.** `tests/test_entry_lz77_repeat_slots.py`, `test_v2_closed_forms`: the implementation's count equals the sum
for m = 1..8 (k = 2, `generate_scaling`) and m = 1..7 (k = 1, 3); the identity with Σ j! and the sandwich for
m = 3..29, with Σ_{j≤m−2} j! ≤ 2(m − 2)!. `test_f1_has_m_factorial_parses`: exactly m! parses (REPMIN = 3, k = 1, 2,
3, m ≤ 6, padding 0..2). The validator's V2 run measures n = 12..24 (m = 4..8): 53, 221, 1181, 7661, 58061.

## 3. Slot DP on F1: (4m³ − 15m² + 29m − 9)/3 relaxations for k = 2 (V2)

**3.1 The states.** Run the DP on F1(m) without padding, REPMIN = 3. Let A_j be the set of slot tuples present at
position 3j − 3. For a block index j and 0 ≤ c, write P_j(c) = Π_{a=0}^{c−1} (j − 2 − a) (an empty product is 1).

**Lemma 2.** A_j is also the set of tuples present at 3j − 2 and at 3j − 1, and A_j is the set of tuples
(3u₀, …, 3u_{c−1}, 1, …, 1) with 0 ≤ c ≤ max(0, min(k, j − 2)) and 1 ≤ u_a ≤ j − 2 − a. Their number is
S(j) = Σ_{c=0}^{max(0, min(k, j−2))} P_j(c) (so S(1) = S(2) = 1), and the number of distinct prefixes R[0..k−2] among
them is G(j) = Σ_{c=0}^{max(0, min(k−1, j−2))} P_j(c).

*Proof.* Without pruning, the keys of `best[i]` are exactly the slot tuples reachable at position i: every key was
offered by a token from a key at a smaller position, and every token from a key is offered (with prefix grouping,
the new match (d, L) from the group with prefix P is offered to (d, P), and the set of these successors is the same
as without grouping). By Lemma 1, position 3j − 2 is reached only by the literal x_j from 3j − 3 (a token ending there
would have to copy the fresh x_j), and 3j − 1 only by the literal a from 3j − 2 (a match token ending there would
have length 1); literals keep the tuple, so the three positions of block j hold the same set. Position 3j is reached
by the literal b from 3j − 1 and by the new matches (3t, 2), 1 ≤ t ≤ j − 1, from 3j − 2. Hence A_1 = {1^k} and
A_{j+1} = A_j ∪ {(3t, R[0..k−2]) : R ∈ A_j, 1 ≤ t ≤ j − 1}. The description of A_j follows by induction on j: it holds
for j = 1, 2 (only c = 0). If it holds for j, pushing 3t (t ≤ j − 1 = (j + 1) − 2) in front of
(3u₀, …, 3u_{c−1}, 1, …) and dropping the last entry gives a tuple of the stated form for j + 1, with
min(c + 1, k) ≤ min(k, j − 1) leading entries and the bounds u′₀ = t ≤ (j + 1) − 2 and
u′_{a+1} = u_a ≤ (j + 1) − 2 − (a + 1).
Conversely a tuple of the form for j + 1 with c ≥ 1 arises by pushing 3u₀ in front of
(3u₁, …, 3u_{c−1}, 1, …, 1) ∈ A_j (whose last entry is a 1, since c − 1 ≤ k − 1), and the tuple with c = 0 is 1^k ∈ A_j.
Distinct (c, u) give distinct tuples, because 3u ≠ 1 fixes c as the number of leading entries different from 1. The
count of tuples with c leading entries is P_j(c). The (k − 1)-prefixes are the tuples of the same form of length k − 1,
with c ≤ min(k − 1, j − 2); each arises (from the tuple with a 1 in the last slot, or with c = k), so their number is
G(j). For k = 1 the prefix is empty and G(j) = 1. ∎

**3.2 The count.** At every position i < n the DP makes one literal relaxation per state and no repeat relaxation
(Lemma 1: no slot has ml ≥ 3). New-match relaxations occur only at the a of block j: `distances` is
{3t : 1 ≤ t ≤ j − 1}, each with ml = 2, so each prefix group makes j − 1 relaxations (one length each). Hence the
total is

    T(m, k) = Σ_{j=1}^{m} 3 S(j) + Σ_{j=1}^{m} (j − 1) G(j),

which is `harness.dp_count_f1(m, k)`. For k = 2: S(1) = 1 and S(j) = 1 + (j − 2) + (j − 2)(j − 3) for j ≥ 2, G(j) = j − 1
for j ≥ 2. With Σ_{j=2}^{m} (j − 1) = m(m − 1)/2, Σ_{j=2}^{m} (j − 2)(j − 3) = (m − 1)(m − 2)(m − 3)/3 and
Σ_{j=2}^{m} (j − 1)² = (m − 1)m(2m − 1)/6,

    T(m, 2) = 3 + 3m(m − 1)/2 + (m − 1)(m − 2)(m − 3) + (m − 1)m(2m − 1)/6 = (4m³ − 15m² + 29m − 9)/3,

for every m ≥ 1 (m = 1 gives 3). With n = 3m this is 4n³/81 − 5n²/9 + 29n/9 − 3, the V2 `cost`. The optimum on F1(m)
is 27 + 15(m − 1) (block 1 by literals, 27; each later block 9 for x_j and 6 for new(3, 2)): by Lemma 1 every
block j ≥ 2 costs at least 9 + min(18, 3 + γ(3t)) = 15. ∎

**Check.** `tests/test_entry_lz77_repeat_slots.py`, `test_v2_closed_forms`: the implementation's count equals the
polynomial for m = 1..40 (k = 2) and `dp_count_f1` for m = 1..15 (k = 1, 3), with optimum 27 + 15(m − 1); the state
counts at all three positions of every block equal S(j) for m ≤ 9, k = 1, 2, 3. The validator's V2 run measures
n = 30..120 (m = 10..40), and its shape diagnostic identifies n³ from the counts for n = 3..60.

## 4. Correctness of the enumeration

The stack starts with the root (0, 1^k, 0). A popped entry (i, R, c) with i < n pushes one entry for every allowed
token at (i, R): the literal; for every slot j with R[j] ≤ i and every length REPMIN ≤ L ≤ ml(i, R[j]), the repeat; for
every 1 ≤ d ≤ i and every 2 ≤ L ≤ ml(i, d), the new match; each with the next state and c plus the token cost (the
match tests are exactly those of section 0, since `match_lengths` computes ml, section 6.1). Every pushed entry has a
larger position, so the search terminates. By induction on the number of tokens, the entries ever pushed are exactly
the partial parses with their costs, each once. The popped entries at position n are therefore exactly the complete
parses with their costs, and the function returns the smallest one (`best` starts as None and is replaced by every
strictly smaller cost). For n = 0 the root is the only parse, with cost 0. ∎

**Check.** `test_all_short_binary_strings` (enumeration = DP = oracle on every binary string of length ≤ 7,
k = 1, 2, 3, REPMIN = 1, 2, 3), `test_agree_and_check` (seeded instances, n ≤ 8), `test_known_values`; the
validator's V1 runs (n ≤ 8 for the enumeration).

## 5. Correctness of the slot DP

**Theorem.** `lz77_slots_dp` returns OPT(s).

*Proof.* (1) Whether a token is allowed at (i, R), its length, its cost and the next slot tuple depend only on (i, R)
and the token: the costs are static and the match test reads only s, i and the distance (section 0). So the parses
of s are exactly the paths from (0, 1^k) to a state at position n in the directed graph whose vertices are the
states and whose arcs are the allowed tokens, and the cost of a parse is the total arc cost of its path. Every arc
increases the position by L ≥ 1, so the graph is acyclic and the positions are a topological order.

(2) Without grouping, the DP sets best[0] = {1^k: 0} and processes i = 0, …, n − 1 in turn; processing i offers, for
every key R of best[i] and every allowed token, best[i][R] + cost to the successor, and `_offer` keeps the minimum.
Claim: when position i is processed, best[i][R] is the minimum cost of a path from (0, 1^k) to (i, R), for every
reachable (i, R), and the keys of best[i] are the reachable tuples. Induction on i: every arc into a state at
position i starts at a smaller position, which has already been processed with its final values, and has offered
along every arc. So the minimum over the in-arcs of (predecessor value + arc cost) has been offered, and nothing
smaller (every offer is such a sum). Tuples that are not reachable are never offered.

(3) *Prefix grouping.* A new match (d, L) from (i, R) leads to (i + L, (d, R[0..k−2])) at cost 2 + γ(L−1) + γ(d);
neither the successor nor the cost reads R[k−1], and whether it is allowed reads only i, d, L and s. So all states at
position i with the same prefix P = R[0..k−2] offer the same set of new-match successors, with the same token
costs, and the smallest offer to each such successor comes from the cheapest member of the group. The DP offers the
new matches once per group, from `groups[P]`, the minimum value in the group (the dictionary update keeps the
minimum). Every other offer is unchanged, so every minimum in (2), and the set of keys, is unchanged.

(4) Hence the minimum over the keys of best[n] is the minimum cost of a parse. best[n] is non-empty because the
all-literal path reaches it. ∎

The same argument is the case "nothing is deleted" of the witness argument in the proof of Theorem 2 of
[theorems/lz77-repeat-slots-exact-pruning](../../theorems/lz77-repeat-slots-exact-pruning/).

**Check.** As in section 4; in addition `theorems/lz77-repeat-slots-exact-pruning/verify.py`, part M (forward DP
with and without prefix grouping = backward recursion on every binary string of length ≤ 9, = enumeration for
length ≤ 6, k = 1, 2, 3, REPMIN = 1, 2, 3).

## 6. Time bounds on every input

**6.1 The match-length table.** `match_lengths` allocates rows of lengths 1, 2, …, n + 1 ((n + 1)(n + 2)/2 entries) and
fills them backwards: for i = n − 1, …, 0 and d = 1, …, i it sets ml[i][d] = 1 + ml[i+1][d] if s[i] = s[i − d] and
leaves 0 otherwise. Since ml(i, d) = 1 + ml(i + 1, d) when s[i] = s[i−d] (with ml(n, d) = 0) and 0 otherwise, by
downward induction on i the table equals ml. It makes Σ_{i<n} i = n(n − 1)/2 symbol comparisons: Θ(n²) work for
n ≥ 2. Both implementations build it.

**Check.** `test_match_table` (both copies equal the definition, and have (n + 1)(n + 2)/2 entries, on every binary
string of length ≤ 8).

**6.2 Slot DP: states and relaxations.** Let S_i be the number of keys of best[i] (the reachable tuples, section 5),
G_i the number of their distinct prefixes, and T the number of relaxations.
- *States.* A slot value other than the initial 1 was pushed by a new match at some position p ≤ i − 2 with distance
  d ≤ p and length ≥ 2 ending at a position ≤ i; repeats only reorder the slots. So for i ≥ 3 every entry lies in
  [1, i − 2], S_i ≤ (i − 2)^k and G_i ≤ (i − 2)^(k−1); for i ≤ 2 no new match has ended, so S_i ≤ 1 and G_i ≤ 1. In
  total S = Σ_{i=0}^{n} S_i ≤ 3 + Σ_{j=1}^{n−2} j^k ≤ 3 + n^(k+1). None of this depends on REPMIN. (This is Theorem C(1)
  of [theorems/lz77-repeat-slots-state-bounds](../../theorems/lz77-repeat-slots-state-bounds/).)
- *Relaxations.* At position i < n a state makes 1 literal relaxation and, for each of its k slots, at most
  max(0, ml − REPMIN + 1) ≤ n − i repeat relaxations; a prefix group makes Σ_{d=1}^{i} max(0, ml(i, d) − 1) ≤ i(n − i)
  new-match relaxations. With S_i ≤ n^k and G_i ≤ n^(k−1) for n ≥ 1,

      T ≤ Σ_{i=0}^{n−1} [n^k (1 + k n) + n^(k−1) · n · n] = n [n^k (1 + k n) + n^(k+1)] = O(n^(k+2))

  for fixed k (and T = 0 for n = 0).
- *Tightness.* On aⁿ, for every fixed k and REPMIN, the DP has at least Σ_{i=2k+1}^{n} Π_{t=1}^{k} (i − 2t) =
  n^(k+1)/(k+1) − O(n^k) states and makes n^(k+2)/(k+2) + O(n^(k+1)) relaxations, and over all strings of length n the
  maxima are n^(k+1)/(k+1) + O(n^k) states and n^(k+2)/(k+2) + O(n^(k+1)) relaxations: Theorem C(2), (3) of the
  state-bounds note, which counts exactly the relaxations of this implementation (literal and repeats per state, new
  matches per prefix group). So O(n^(k+2)) is attained on aⁿ.

**Check.** `test_all_short_binary_strings` (T ≤ n[n^k(1 + kn) + n^(k+1)] on every binary string of length 1..7, k = 1,
2, 3, REPMIN = 1, 2, 3); `test_state_bound` (S_i ≤ max(1, (i−2)^k) on 60 seeded binary strings of length ≤ 14;
S ≤ 3 + Σ_{j≤n−2} j^k on those and on every binary string of length ≤ 8, REPMIN = 1, 2, 3; S_i ≥ Π_t (i − 2t) on a¹²,
REPMIN = 1, 2, 3); `theorems/lz77-repeat-slots-state-bounds/verify.py`, part C (Theorem C, including the per-position
bounds on every binary string of length ≤ 12 and every ternary string of length ≤ 8).

**6.3 Slot DP: the work that is not counted.** Besides the T counted `_offer` calls (each one dictionary lookup, at
most one store, one or two γ evaluations and O(1) additions, plus O(k) to hash the k-tuple key), `lz77_slots_dp`
does the following, and nothing else.
- Per position i < n: the list `distances`, i distance tests, n(n − 1)/2 in total.
- Per state at a position i < n (L = Σ_{i<n} S_i of them; L ≤ T, since each makes one literal relaxation): k slot
  tests, one prefix slice and one group update (O(k) each).
- Per slot that passes its test: one tuple `moved` (O(k)), followed by at least one repeat relaxation; so at most as
  many as there are repeat relaxations.
- Per prefix group (G_i ≤ S_i of them at position i): one loop iteration.
- Per (prefix group, distance in `distances`): one tuple `pushed` (O(k)), followed by at least one new-match
  relaxation (the distance has ml ≥ 2); so at most as many as there are new-match relaxations.
- The table `best` (n + 1 dictionaries), the match-length table (section 6.1) and the final minimum over best[n],
  which has S_n ≤ T + 1 keys (for n ≥ 1 every key of best[n] was created by a relaxation).

In total, for n ≥ 1, O(k·T + k·L + n²) = O(k·T + n²) elementary operations, i.e. O(n^(k+2)) time for fixed k (for
n = 0 the function does O(k) work).

**Check.** `test_dp_uncounted_work`: a copy of the loops of `slot_dp.py` with every step counted, whose optimum and
relaxation count equal the implementation's, has L literal relaxations and k·L slot tests, n(n − 1)/2 distance tests,
at most as many `moved` tuples as repeat relaxations, at most as many `pushed` tuples as new-match relaxations, and
S_n ≤ T + 1; on every binary string of length ≤ 7 (k = 1, 2, 3, REPMIN = 1, 2, 3), on aⁿ for n = 10, 16 and on F1(5),
F1(9).

**6.4 Enumeration: lower bound.** Let n ≥ 1 and s = F1(m) with m = ⌊n/3⌋, padded to length n (pad = n − 3m ≤ 2).
For every k and REPMIN, s has at least m! complete parses: code every fresh symbol by a literal, block 1 by literals,
and block j ≥ 2 either by the literals a, b or by one of the new matches (3t, 2), 1 ≤ t ≤ j − 1, which are allowed
whatever the slots (Lemma 1). These choices give Π_{j=2}^{m} j = m! distinct parses. (With REPMIN = 3 there are no
others, section 2; with REPMIN ≤ 2 repeats may add more.) For n ≥ 1 every complete parse has at least one token, and
its last token's push is counted once, so the enumeration makes at least as many evaluations as there are complete
parses: at least ⌊n/3⌋! evaluations. Since log₂ m! ≥ m log₂ m − m log₂ e, this is 2^((1/3 − o(1)) n log₂ n). The string
uses at most ⌊n/3⌋ + 2 + pad = n/3 + O(1) distinct symbols.

**Check.** `test_f1_has_m_factorial_parses` (at least m! parses for REPMIN = 1, 2 and exactly m! for REPMIN = 3,
k = 1, 2, 3, m ≤ 6, padding 0..2; evaluations ≥ parses for m ≤ 4).

**6.5 Enumeration: upper bound.** Let n ≥ 1. At a position i ≤ n − 1 and for a given length L there are at most
1 + k + i ≤ n + k < n + k + 1 tokens of length L (the literal if L = 1, at most one repeat per slot, at most one new
match per distance d ≤ i). A complete parse is determined by its sequence of token lengths, a composition of n (2^(n−1)
possibilities), and by the choice of a token of the given length at each of its at most n token positions; so there
are at most 2^(n−1)(n + k + 1)^n complete parses. A partial parse is a prefix of the complete parse obtained by
appending literals (always allowed), and is determined by that parse and its number of tokens (0..n). So the search
tree has at most (n + 1)·2^(n−1)·(n + k + 1)^n nodes, and the enumeration makes one evaluation per non-root node:
fewer than (n + 1)·2^(n−1)·(n + k + 1)^n = 2^(n log₂ n + O(n)) for fixed k. With 6.4, the worst case over strings of
length n is 2^Θ(n log n) evaluations, for every fixed k ≥ 1 and REPMIN ≥ 1. (At n = 0 the bound would be 1/2, while
the tree has the single root node: hence n ≥ 1.)

**Check.** `test_all_short_binary_strings` (evaluations + 1 ≤ (n + 1)·2^(n−1)·(n + k + 1)^n on every binary string of
length 1..7, k = 1, 2, 3, REPMIN = 1, 2, 3).

**6.6 Enumeration: the work that is not counted.** Each node is popped once (E + 1 pops for E evaluations, section 2).
A popped node at position n costs O(1). A popped node at position i < n makes k slot tests and i ≤ n − 1 distance
tests, builds at most one tuple per allowed slot and per distance with ml ≥ 2 (O(k) each, each followed by at least
one counted push), and makes its counted pushes (O(1) each: a stack entry is a triple holding the position, a
reference to a shared slot tuple and the cost). So the total is O((n + k)(E + 1)) elementary operations plus the
Θ(n²) table; by 6.4 and 6.5 this is 2^Θ(n log n) time in the worst case for fixed k.

**Check.** `test_enumeration_stack_bound`: a copy of the loop of `enumeration.py` with the same push order, whose
evaluation count equals the implementation's (every binary string of length 1..8), pops exactly E + 1 nodes, makes
k slot tests per expanded node and at most n − 1 distance tests per expanded node; on every binary string of length
1..8, on aⁿ for n ≤ 11 (n ≤ 9 when k ≥ 2 and REPMIN = 1) and on F1(m) for m ≤ 7, k = 1, 2, 3, REPMIN = 1, 2, 3.

## 7. Space

**Enumeration.** Besides the Θ(n²) table, the search keeps its stack. Invariant: after the first pop, the stack,
from bottom to top, is C₁ C₂ … C_r, where C_t is a non-empty set of not yet popped children of a node v_t, every v_t
has been expanded (so its position is < n), and v_{t+1} is a descendant of v_t. The pop removes the top entry u of C_r
(dropping C_r if it becomes empty); if u is at a position < n, its children are pushed as C_{r+1}, and u is a
descendant of v_r (or of v_{r−1} if C_r was dropped), so the invariant is kept. Positions strictly increase along
descendants, so r ≤ n. A node at position i has at most 1 + k(n − i) + i(n − i) ≤ 1 + kn + n²/4 children (repeats:
at most n − i lengths per slot; new matches: at most n − i − 1 lengths per distance d ≤ i). So the stack never holds
more than max(1, n(1 + kn + n²/4)) ≤ n(1 + kn + n²/4) + 1 = O(n²(n + k)) entries, each O(k) words.

**Slot DP.** It keeps all its states: S ≤ 3 + Σ_{j=1}^{n−2} j^k = O(n^(k+1)) keys of k entries each (section 6.2, for
every REPMIN ≥ 1), the dictionary `groups` of the current position (at most S_i entries), the list `distances` (at
most n entries) and the Θ(n²) table: O(n^(k+1)) for fixed k (and n ≥ 2), plus Θ(n²).

**Check.** `test_enumeration_stack_bound` (maximum stack ≤ n(1 + kn + n²/4) + 1, ranges as in 6.6); `test_state_bound`
(ranges as in 6.2).

## 8. The V1 oracle and the check (`harness.py`)

- `oracle_optimum` computes V(i, R) = 0 for i = n and otherwise the minimum, over the allowed tokens at (i, R), of the
  token cost plus V at the next state, with memoisation over (i, R). Its match test `extent(i, d)` compares symbols
  directly and returns ml(i, d). By the graph argument of section 5(1) (positions strictly increase, so the recursion
  terminates), V(i, R) is the minimum cost of a token sequence from (i, R) to position n, and V(0, 1^k) = OPT(s). It
  uses neither the match-length table, nor a forward pass, nor prefix grouping, nor any code of the implementations.
  It is exact for every n; `check` calls it for n ≤ 24 (`ORACLE_MAX_N`) and returns None above.
- `check` returns False for an output that is not a pair of integers (a `bool` is rejected because its type is not
  `int`), for a negative count, and for a cost outside [0, 9n] (the all-literal parse costs 9n and every cost is
  non-negative, section 0); otherwise, for n ≤ 24, True iff the cost equals V(0, 1^k).
- `equal` compares the costs only, because the counts of the two implementations differ by design.

**Check.** `test_all_short_binary_strings` (oracle = enumeration = DP, OPT ≤ 9n, every binary string of length ≤ 7),
`test_wrong_outputs_rejected`, `test_agree_and_check` (cost ± 1 rejected, seeded instances up to n = 24).

## 9. Factual caveats

- *What is counted* (`caveats`): exactly the counters of section 0; the uncounted work is bounded in sections 6.3 and
  6.6.
- *Adaptive prices.* If the token prices depend on the history, the DP that keeps one value per (position, slots) is
  not exact: Proposition 6(b) of
  [theorems/lz77-repeat-slots-exact-pruning](../../theorems/lz77-repeat-slots-exact-pruning/#hypotheses-that-cannot-be-dropped)
  gives an explicit string (bbba, k = 1, REPMIN = 2) and price rule on which it returns a non-optimal value. This
  entry's problem has static costs, to which section 5 applies.
- *Alphabet.* The lower bound of 6.4 uses n/3 + O(1) distinct symbols; the V2 family uses n/3 + 2 (section 1).
- *Fixed k.* All exponents are for fixed k; the entry makes no claim for k growing with n.

**Check.** `theorems/lz77-repeat-slots-exact-pruning/verify.py`, part H (Proposition 6(b) with exact rational
probabilities).
