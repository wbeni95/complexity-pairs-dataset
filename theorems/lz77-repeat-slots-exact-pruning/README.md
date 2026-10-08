# An exact pruning rule for optimal LZ77-style parsing with k repeat-offset slots

> **Provenance: 🟡⏳ Undetermined (may be our own result).**
>
> *Base:* the folklore dynamic program over (position, slot contents). C. Bloom's blog posts (not peer-reviewed)
> contain a forward optimal parser over {Pos, State} nodes with a general adaptive state and a threshold early out
> (2011), and the dynamic program over {state, pos} with the repeat-match offsets in the state, pruned by a threshold
> that he calls approximate (2015). Neither post gives a proof. The pair entry
> [lz77-repeat-slots-enumeration-vs-slot-dp](../../pairs/lz77-repeat-slots-enumeration-vs-slot-dp/) writes out the
> correctness proof of the dynamic program.
>
> *Beyond the sources read:* this note proves a pruning rule that provably preserves the optimum, for every number k of
> slots (rule G3, Theorems 1 and 2), and its generalisation to other static cost models (G3\*, Theorem 3); it shows
> that the margin is attained (Proposition 4) and gives counterexamples showing that the hypotheses and the shape of
> the margin are needed (Remark 5, Proposition 6, Remark 7). Nothing read states an exact pruning rule of this kind.
>
> *Sources that could not be read:* the journal version of the paper on dictionary-symbolwise flexible parsing
> (Crochemore, Giambruno, Langiu, Mignosi and Restivo, Journal of Discrete Algorithms 14 (2012) 74–90,
> [doi:10.1016/j.jda.2011.12.021](https://doi.org/10.1016/j.jda.2011.12.021)), because the publisher's site refused
> automated access (its preprint was read in full and has no repeat-offset state); A. Langiu, "On parsing optimality
> for dictionary-based text compression—the Zip case" (Journal of Discrete Algorithms 20 (2013) 65–70,
> [doi:10.1016/j.jda.2013.04.001](https://doi.org/10.1016/j.jda.2013.04.001)), for the same reason (only its abstract
> was read); and a 2010 PhD thesis titled "Parsing algorithms for data compression" (University of Pisa,
> <https://etd.adm.unipi.it/t/etd-05252010-115131>), which its thesis record marks as not consultable until 2050.
> Whether they contain these results could not be checked, so these results may be our own. If you can tell us whether
> one of these sources contains the result, please open an issue. What was checked in the literature is in
> [Literature](#literature).

## Setting

A string s = s[0] … s[n−1] over an integer alphabet is coded from position 0 to position n by *tokens*. Fix k ≥ 1
(the number of repeat-offset slots) and REPMIN ≥ 1. A *slot tuple* is R = (R[0], …, R[k−1]) with positive integer
entries; the coder starts with (1, …, 1), written 1^k. At position i, with slot tuple R, the tokens are:

| Token | Allowed if | Cost | Next position, next slots |
|---|---|---|---|
| literal | i < n | 9 | i + 1, R |
| repeat of slot j, length L | R[j] ≤ i, L ≥ REPMIN, i + L ≤ n, s[i+t] = s[i+t−R[j]] for 0 ≤ t < L | 3 + j + γ(L) | i + L, (R[j], R[0..j−1], R[j+1..k−1]) |
| new match, distance d, length L | 1 ≤ d ≤ i, L ≥ 2, i + L ≤ n, s[i+t] = s[i+t−d] for 0 ≤ t < L | 2 + γ(L−1) + γ(d) | i + L, (d, R[0..k−2]) |

Here γ(x) = 2⌊log₂ x⌋ + 1 (the length of the Elias gamma code of x); γ is nondecreasing. A repeat moves its slot to
the front; a new match pushes its distance to the front and drops the last slot (equal values may sit in several
slots). Copies may overlap (d < L). The costs are *static*: they depend only on the token.

- A *state* is a pair (i, R). A *continuation* from (i, R) is a sequence of tokens, each allowed at the state that
  the previous ones lead to, that ends at position n. Its cost is the sum of the token costs.
- V(i, R) is the minimum cost of a continuation from (i, R). It is finite, since literals are always allowed.
  OPT(s) = V(0, 1^k) is the optimum.
- **The DP.** For i = 0, 1, …, n − 1 in turn, every state present at position i offers, for every allowed token,
  its value plus the token cost to the successor state; a state's value is the smallest offer it receives. New
  matches may be offered once per *prefix group* (states at position i with the same R[0..k−2]) from the cheapest
  state of the group, since their successor and cost do not depend on R[k−1]. The answer is the smallest value at
  position n. It equals OPT(s): this is the case "nothing is deleted" of the proof of Theorem 2 (the pair entry gives
  a direct proof in its PROOFS.md, section 5).
- **The pruned DP with margin μ.** The same, except that at each position i < n, before offering, it chooses *one*
  state R\* of minimum value c\* at position i (by any rule, possibly depending on i) and deletes every state
  R ≠ R\* with c(R) ≥ c\* + μ(R, R\*). Position n is not pruned.

For two slot tuples R ≠ R′ let a₀ be the first index with R[a₀] ≠ R′[a₀], and define

    D(R, R′) = Σ_{a=a₀}^{k−1} max(0, γ(R[a]) − 1 − a),        D(R, R) = 0.

D is not symmetric. For k = 1 it reads D((r), (r′)) = γ(r) − 1 for r ≠ r′.

## Statements

**Theorem 1 (rule G3: continuation bound).** Assume REPMIN ≥ 2. For every position i, all slot tuples R and R′
(arbitrary positive entries) and every continuation τ from (i, R), there is a continuation τ′ from (i, R′) with
cost(τ′) ≤ cost(τ) + D(R, R′). In particular V(i, R′) ≤ V(i, R) + D(R, R′).

**Theorem 2 (G3 pruning is exact).** Assume REPMIN ≥ 2. The pruned DP with margin μ = D returns OPT(s), for every
string s, every k ≥ 1, every rule for choosing the comparators R\* (ties included), with or without prefix
grouping.

**Theorem 3 (rule G3\*: other static costs).** Keep the tokens, the conditions under which they are allowed and the
slot updates, with REPMIN ≥ 2, but let the costs be arbitrary real numbers lit, new(L, d) and rep(L, j) that depend
only on the token (so literal and new-match costs never read the slots). For a position i, 0 ≤ a < k and x ≥ 1 let

    E_a(x) = max { new(L, x) − rep(L, j) : a ≤ j ≤ k−1, REPMIN ≤ L ≤ n − i },
    D*_i(R, R′) = Σ_{a=a₀}^{k−1} max(0, E_a(R[a])),        D*_i(R, R) = 0,

where a term counts 0 if REPMIN > n − i (then no repeat can start at or after i, and D*_i = 0). Then every
continuation τ from
(i, R) has a continuation τ′ from (i, R′) with cost(τ′) ≤ cost(τ) + D*_i(R, R′), and the pruned DP that uses the
margin D*_i at position i returns OPT(s), under every comparator rule, with or without prefix grouping.

*For the costs of the Setting,* new(L, x) − rep(L, j) = γ(x) − 1 − j + (γ(L−1) − γ(L)), so

    D*_i(R, R′) = Σ_{a=a₀}^{k−1} max(0, γ(R[a]) − 1 − a + λ_i),    λ_i = max_{REPMIN ≤ L ≤ n−i} (γ(L−1) − γ(L)) ∈ {0, −2}

for REPMIN ≤ n − i (and D*_i = 0 otherwise).

γ(L−1) − γ(L) is −2 if L is a power of two and 0 otherwise. Hence D*_i ≤ D always, and D*_i = D whenever the range
REPMIN ≤ L ≤ n − i contains a number that is not a power of two: for example when n − i ≥ REPMIN + 1 (two consecutive
integers ≥ 2 are never both powers of two), or when n − i ≥ 3 and REPMIN ≤ 3.

**Proposition 4 (the margin is attained).** Let s = aabbbbabbaabaaaab (n = 17), k = 2, REPMIN = 2. At position 11
the DP holds the states (9, 5) with value 53 (the cheapest) and (3, 5) with value 56, and

    V(11, (3, 5)) = 13,   V(11, (9, 5)) = 18,   D((3, 5), (9, 5)) = (γ(3) − 1) + (γ(5) − 1 − 1) = 2 + 3 = 5.

So the bound of Theorem 1 holds with equality for R = (3, 5), R′ = (9, 5): no bound V(i, R′) ≤ V(i, R) + m(R, R′)
with m depending only on the two tuples can have m((3, 5), (9, 5)) < 5. From (3, 5) the continuation "repeat slot 0 (distance 3, length 3, cost 6),
repeat slot 1 (distance 5, length 3, cost 7)" costs 13. From (9, 5), "new match (3, 3), cost 8; new match (5, 3),
cost 10" costs 18, and no continuation is cheaper (V computed exactly by `verify.py`). The optimum is 69 = 56 + 13. The rules
NB and NB0 of Remark 7 give this pair the margin 2, delete (3, 5) at position 11 and return 71.

**Remark 5 (the maximum over the slots j ≥ a is needed in G3\*).** Restricting E_a to j = a makes the continuation
bound of Theorem 3 false.
Take k = 2, REPMIN = 2 and the static costs lit = 9, new(L, d) = 3 + γ(L−1) + 2γ(d), rep(L, j) = 2 + w_j + γ(L) with
(w₀, w₁) = (4, 2), so a repeat from slot 1 is cheaper than one from slot 0. Let s = aaaababa (n = 8), i = 2,
R = (2, 1) and R′ = (1, 1).
- From R: new match (distance 1, length 2) for 6, so the slots become (1, 2); literal b for 9; repeat of slot 1
  (distance 2, length 3) for 2 + 2 + 3 = 7. So V(2, R) ≤ 22, and in fact V(2, R) = 22.
- From R′ every continuation costs at least 27: V(2, R′) = 27 (computed exactly by `verify.py`; e.g. new match (1, 2) for 6,
  literal b for 9, new match (2, 3) for 3 + 3 + 6 = 12).
- With j = a only: E₀(2) = max_L [9 + γ(L−1) − 6 − γ(L)] = 3 and E₁(1) = max_L [5 + γ(L−1) − 4 − γ(L)] = 1, total
  4 < 5 = V(2, R′) − V(2, R). With j ≥ a: E₀(2) = 5 (from j = 1), so D*₂(R, R′) = 6 ≥ 5.

The entry 2 of R, at index 0, is used from slot 1, because the new match pushed 1 in front of it: this is the case
j > a in the proof. If rep(L, j) is nondecreasing in j (as for the costs of the Setting), the maximum over j ≥ a is
attained at j = a. The tuple (2, 1) is not reachable at position 2 from 1^k; the theorem, and this counterexample,
concern arbitrary tuples. We do not claim that the pruned DP with the j = a margin returns a wrong value on some
input.

## Hypotheses that cannot be dropped

**Proposition 6.**
- **(a) One-symbol repeats (REPMIN = 1).** For s = aaaaba and k = 1, 2, 3, OPT(s) = 32, but the DP pruned with
  margin D returns 33, for every choice of the comparators. An optimal parse is: literal a; repeat of slot 0
  (distance 1, length 1, cost 4); new match (distance 2, length 2, cost 6); literal b; repeat of slot 0 (distance 2,
  length 1, cost 4). For k = 1, at position 4 the state (2) has value 19 and the cheapest state (1) has value 15;
  since 19 ≥ 15 + D((2), (1)) = 17, (2) is deleted, and from (1) the last a costs a literal (9 instead of 4). The
  continuation bound of Theorem 1 fails there as well: V(4, (1)) = 18 > 15 = V(4, (2)) + D((2), (1)). A one-symbol
  repeat cannot be replaced by a new match (those need L ≥ 2), which is the step of the proof that fails. The
  string bbbbab is the same example with the letters swapped.
- **(b) Adaptive costs.** If the costs depend on the history, keeping one value per (position, slots) is not exact,
  even without pruning. Take k = 1, REPMIN = 2 and the following prices in bits. Each token pays −log₂ of the
  probability of its type, P(type) = (number of earlier tokens of this type + 1)/(number of earlier tokens + 3), with
  the three types literal, repeat and new match. A literal also pays −log₂ P(symbol), with
  P(symbol) = (earlier literals of this symbol + 1)/(earlier literals + 4). A repeat also pays 1 + γ(L) bits, a new
  match γ(L−1) + γ(d) bits. For s = bbba there are three parses:
  - four literals: probability 1/2100, cost log₂ 2100 = 11.0362 bits (the optimum);
  - literal, new match (distance 1, length 2), literal: probability 1/600 plus 2 bits, 11.2288 bits;
  - literal, repeat (length 2), literal: probability 1/600 plus 4 bits, 13.2288 bits.

  All three pass through the state (3, (1)). There the prefix "literal, new match" costs 2 + log₂ 48 = 7.5850 bits
  and the prefix of three literals log₂ 200 = 7.6439 bits, so a DP with one value per state keeps the former. The
  final literal a then costs log₂(25/2) = 3.6439 bits instead of log₂(21/2) = 3.3923 bits, and the DP returns
  11.2288 bits. No ties occur. The proof of Theorem 1 does not apply either, since it copies tokens at the same
  cost.

**Remark 7 (naive margins fail; REPMIN = 2).** For k = 1 all of the following margins equal D. Each of them makes the
pruned DP (REPMIN = 2) return a wrong value on the string and for the k shown in the table, for *every* choice of
the comparators (checked by running the pruned DP along every sequence of choices among equally cheap states). The
note claims nothing about other values of k for these strings.

| Margin μ(R, R\*) | k | String | OPT | Pruned DP |
|---|---|---|---|---|
| K1: γ(R[0]) − 1 (the k = 1 rule on slot 0) | 2 and 3 | abaababbbbab | 52 | 53 |
| NS: Σ_{x ∈ set(R) ∖ set(R\*)} (γ(x) − 1) | 2 | abbbbabbbaaabba | 54 | 56 |
| NS | 3 | abbaabbbbbaaabaa | 71 | 72 |
| NB: Σ_{a : R[a] ≠ R\*[a]} (γ(R[a]) − 1) | 2 | aabbbbabbaabaaaab | 69 | 71 |
| NB0: Σ_{a : R[a] ≠ R\*[a]} max(0, γ(R[a]) − 1 − a) | 2 | aabbbbabbaabaaaab | 69 | 71 |

D differs from NB0 in that it charges *every* index from the first difference on, not only the indices where the
two tuples differ. In the simulation of Theorem 1 an index whose value is the same in R and R′ can become misaligned
once entries in front of it have been used, and then it costs a new match. Some strings fail only for some
comparator choices: on aaabbaaaaba with k = 3 the K1-pruned DP returns 50 or 51 depending on the choices
(OPT = 50); the table lists strings that fail for every choice.

## Proofs

### Theorem 1

Fix i, R, R′ and a continuation τ from (i, R). We build τ′ token by token. Both runs are always at the same position,
because every token of τ′ has the length of the token of τ it replaces. During the construction let S be the slot
tuple of the run of τ and T that of τ′. We maintain

    S = P ++ (R[u] : u ∈ U),        T = P ++ (R′[v] : v ∈ V),

where P is a common tuple, U is an increasing list of indices of R, V is an increasing list of indices of R′, and
|U| = |V|. Initially P is empty and U = V = (0, 1, …, k−1). Write U[β] for the β-th element of U (from 0). Let the
next token of τ be t, at position p.

- **Literal:** copy it. Nothing changes.
- **New match (d, L):** copy it. Whether it is allowed depends only on p, d, L and s. If U is not empty, the last
  entry of S belongs to U and the last entry of T to V, so the update gives P := (d) ++ P with the last element of U
  and of V removed. If U is empty, S = T = P and both runs push d and drop the last entry.
- **Repeat of slot j < |P|:** copy it. S[j] = T[j], so it is allowed in both runs, at the same cost 3 + j + γ(L).
  P is reordered; U and V do not change.
- **Repeat of slot j = |P| + β, aligned, i.e. R[U[β]] = R′[V[β]]:** copy it (same slot, same value, same cost). Then
  P := (R[U[β]]) ++ P, and position β is removed from U and from V.
- **Repeat of slot j = |P| + β, misaligned, i.e. x = R[U[β]] ≠ R′[V[β]]:** use the new match (x, L) instead. It is
  allowed, because L ≥ REPMIN ≥ 2, x ≤ p (the repeat was allowed) and the text matches at distance x. Then
  S becomes (x) ++ P ++ (U without position β) and T becomes (x) ++ P ++ (V without its last element), so
  P := (x) ++ P, position β is removed from U, and the last element is removed from V. The extra cost is
  new − rep = 2 + γ(L−1) + γ(x) − 3 − j − γ(L) ≤ γ(x) − 1 − j, since γ is nondecreasing.

The only extra costs come from misaligned repeats. Once U is empty, S = T and every later token is copied exactly. An
index that leaves U never returns, so every index of R causes at most one misaligned repeat. It remains to show that
a misaligned repeat that uses the index a = U[β] has a ≥ a₀ and slot j ≥ a; then its extra cost is at most
γ(R[a]) − 1 − a, and the total is at most Σ_{a ≥ a₀} max(0, γ(R[a]) − 1 − a) = D(R, R′).

**Lemma A (alignment).** Let α be the number of elements of U that are smaller than a₀ (they are U[0], …, U[α−1]).
Then U[β] = V[β] for all β < α, at every step.

*Proof.* True initially. Truncation by a new match: if |U| > α, it removes an element ≥ a₀ from U and the element at
position |V| − 1 ≥ α from V; if |U| = α, then U = V entirely (by the claim) and both lose their last element. An
aligned repeat at β < α removes the same position from both; at β ≥ α it does not touch the first α positions. A
misaligned repeat has β ≥ α: for β < α, U[β] = V[β] < a₀ and R, R′ agree below a₀, so the repeat would be aligned.
It removes position β ≥ α from U and position |V| − 1 ≥ β from V. ∎

So a misaligned repeat uses an index a = U[β] with β ≥ α, hence a ≥ a₀.

**Lemma B (slot index).** A repeat that uses the index a = U[β] has slot j = |P| + β ≥ a.

*Proof.* Take any index b < a. If b is still in U, it stands before a, because U is increasing; there are exactly β
such b. Otherwise b left U. It did not leave by a truncation, since a truncation removes the largest element of U
and a > b was in U at that time. So b left by a repeat, and each such repeat put one element into P. While U is not
empty, P never loses elements (a new match adds one; a repeat inside P only reorders P). Hence |P| is at least the
number of b < a not in U, and j = |P| + β ≥ a. ∎

This proves Theorem 1. Lemma B uses only the slot updates, not the costs.

### Theorem 2

Every value stored by the pruned DP is the cost of an actual token sequence from (0, 1^k) to that state: an offer is
a stored value plus a token cost, and with prefix grouping the group minimum is the value of a state of the group,
from which the same new match leads to the same successor. Call (i, R, τ) a *witness* if R is present at position i
when position i is processed, τ is a continuation from (i, R) and c(i, R) + cost(τ) = OPT(s). Initially
(0, 1^k, an optimal parse) is a witness. Let (i, R, τ) be a witness with i < n.

1. If R is deleted, then R ≠ R\* and c(R) ≥ c\* + D(R, R\*). Theorem 1 gives a continuation τ′ from (i, R\*) with
   c\* + cost(τ′) ≤ c\* + cost(τ) + D(R, R\*) ≤ c(R) + cost(τ) = OPT(s). The left side is the cost of a parse, so
   equality holds, and (i, R\*, τ′) is a witness whose state is kept.
2. So assume R is kept, and let t be the first token of τ, leading to (i′, R′), with τ = t τ_rest. The DP offers
   c(R) + cost(t) to (i′, R′), or, for a new match with grouping, the group minimum plus cost(t), which is not larger.
   So the final value satisfies c(i′, R′) + cost(τ_rest) ≤ OPT(s); it is also the cost of a parse, so equality holds,
   and (i′, R′, τ_rest) is a witness at the larger position i′.

By induction some witness reaches position n, where the smallest value is therefore at most OPT(s); it is at least
OPT(s) because it is the cost of a parse. The argument never compares two deletions and works for every comparator
choice. ∎

### Theorem 3

The simulation of Theorem 1 uses only the allowedness conditions and the slot updates, which are unchanged. Copied
tokens cost the same in both runs: literals and new matches do not read the slots, and a copied repeat uses the same
slot index j and length L. A misaligned repeat at position p ≥ i with slot j and length L is replaced by the new
match (x, L), with extra cost new(L, x) − rep(L, j). Here REPMIN ≤ L ≤ n − p ≤ n − i, and j ≥ a by Lemma B, so the
extra cost is at most E_a(x) ≤ max(0, E_a(x)), where x = R[a] and a ≥ a₀ by Lemma A. Each index contributes at most
once, so the total is at most D*_i(R, R′). The witness argument of Theorem 2 then applies verbatim with D*_i at
position i. For the costs of the Setting, the maximum over j ≥ a of −j is −a, and the maximum over L of
γ(L−1) − γ(L) is λ_i, which gives the displayed formula. ∎

### Propositions 4 and 6, Remarks 5 and 7

These are statements about explicit finite instances. The arithmetic shown with each statement verifies the
witnessing parses and continuations by hand (upper bounds on V and OPT). The remaining facts (that no continuation or
parse is cheaper, the values held by the DP, and the outputs of the pruned DP along every sequence of comparator
choices) are finite exhaustive computations in `verify.py`, each optimum by two independent exact methods (all
parses, and a backward recursion over states). For Proposition 6(a) a complete hand proof follows.

*Proof of Proposition 6(a).* Let s = aaaaba (positions 0–5), REPMIN = 1 and k ≥ 1. Every token costs at least 4 (a
literal 9, a repeat 3 + j + γ(L) ≥ 4, a new match 2 + γ(L−1) + γ(d) ≥ 4). Position 0 and the b at position 4 have no
earlier copy, so they are coded by literals (18). Hence the tokens covering positions 1–3 end at position 4, and the
last a (position 5) is coded by a token of length 1: a literal (9), or a repeat of length 1 of a slot holding a value
v with s[5 − v] = a, i.e. v ∈ {2, …, 5} (cost 4 + j ≥ 4); new matches need length ≥ 2. A slot holds a value v ≥ 2 only
if a new match with distance v ≥ 2 was made, which must lie inside positions 1–3 (no match token covers position 0
or 4): it starts at some p ≥ v ≥ 2 and has length ≥ 2, so it is the new match at p = 2 with distance 2 and length 2
(cost 2 + γ(1) + γ(2) = 6), and position 1 then needs a token of its own (≥ 4). So either positions 1–3 cost at least
10 and the last a at least 4, or they cost at least 6 (one token of length 3 costs at least 2 + γ(2) + γ(1) = 6, two or
three tokens at least 8) and the last a costs 9. Hence OPT(s) ≥ 18 + min(10 + 4, 6 + 9) = 32, and the parse shown
costs 32. In the pruned DP, positions 1, 2, 3 hold only 1^k (no new match with distance ≥ 2 ends before position 4).
Position 4 holds 1^k with value 9 + 6 = 15 (literal, new match (1, 3); every parse of aaaa costs at least 9 + 6) and
(2, 1^(k−1)) with value 13 + 6 = 19 (the value 13 of 1^k at position 2 is 9 + 4, and (2, 1^(k−1)) is reached only by
the new match (2, 2) from position 2), and no other state. So 1^k is the unique cheapest state at position 4 and the
comparator for every rule; D((2, 1^(k−1)), 1^k) = γ(2) − 1 = 2 and 19 ≥ 15 + 2, so (2, 1^(k−1)) is deleted. Every state
at positions 5 and 6 comes from 1^k at position 4 (a token ending at 5 covers the b, so it is the literal b): at
position 5 the slots all hold 1 and s[4] = b ≠ a, so the last a costs 9, and the pruned DP returns 15 + 9 + 9 = 33.
The same holds with a and b swapped. For k = 1, V(4, (2)) = 9 + 4 = 13 and V(4, (1)) = 9 + 9 = 18. ∎

## Scope

- The model is the one in the table: the slot update "move to front on a repeat, push to the front and drop the last
  on a new match", repeat costs that do not read the slot *value*, literal and new-match costs that do not read the
  slots, and static costs. Theorems 1–3 need REPMIN ≥ 2, the minimum new-match length: by Proposition 6(a), with
  REPMIN = 1 both the continuation bound and the pruned DP fail on an explicit string. By Proposition 6(b), with
  adaptive costs even the unpruned DP with one value per state fails. Other update rules (for example a swap with the
  front slot) are not analysed.
- The rule compares each state with one cheapest state per position. A pruner that compares each state with every
  kept state is not analysed here.
- Theorem 2 says nothing about *how many* states survive. On aⁿ only one state survives at every position < n, but
  in the worst case Θ(n^(k+1)) states survive, the same order as without pruning (over unbounded alphabets):
  [lz77-repeat-slots-state-bounds](../lz77-repeat-slots-state-bounds/).
- Proposition 4 shows that D cannot be lowered for one pair of tuples; it does not claim that D is attained for
  every pair.
- Proposition 6(b) shows that the unpruned one-value-per-state DP fails under adaptive prices; the note makes no
  claim about G3 pruning under adaptive prices.

## Literature

- **Credit for the base.** C. Bloom described, in blog posts (not peer-reviewed), a forward parser over
  {Pos, State} nodes with a general adaptive state and a threshold early out (2011), and the DP over {state, pos} with
  the repeat-match offsets in the state, pruned by a threshold (2015). He calls the threshold pruning
  approximate ("The higher you set that threshold, the more approximate and faster the parse.", 2015) and justifies
  his early-out rule "arrival.cost_from_head - best_cost_from_head[P] > threshold" by the assumption "that starting
  from a different state can't help more than some amount" (2011, Part 3). Theorem 2 gives an explicit,
  state-dependent threshold, D(R, R\*), for which such a rule provably keeps the optimum under the hypotheses of the
  Setting.
- **Status:** Theorems 1–3, Proposition 4, Remark 5, Proposition 6 and Remark 7 are proved or checked here. They
  were not found in the sources read (below). The closest sources could not be read, so the note is labelled
  undetermined (it may be our own result) and claims no novelty beyond "not found in the sources read".
- **What was checked.** Full texts searched by keyword, with the table of contents and the relevant passages read:
  A. Langiu, *Optimal Parsing for Dictionary Text Compression* (PhD thesis, 2012); Ferragina, Nitto and Venturini,
  *Bit-optimal Lempel-Ziv compression* (arXiv:0802.0835v1); Farruggia, Ferragina, Frangioni and Venturini,
  *Bicriteria data compression* (arXiv:1307.3872v1); D. Kosolobov, *Relations Between Greedy and Bit-Optimal LZ77
  Encodings* (STACS 2018). These searches found no treatment of repeat-offset slots in them. Read in full: the
  preprint of Crochemore, Giambruno, Langiu, Mignosi and Restivo, *Dictionary-symbolwise flexible parsing* (HAL
  hal-00742078). Its parsing graph has the text positions as vertices and one cost per edge, with no state beyond the
  position, so it has no repeat-offset slots, no pruning between states at one position and no state counts; a search
  of the whole text for "offset", "repeat", "cache", "prun" and "dominat" found nothing. The [MS-PATCH] LZX DELTA
  specification was read at its section on repeated offsets (three offset registers R0, R1, R2, initially (1, 1, 1):
  a new offset is pushed in front of them, and only a repeat of R1 or R2 swaps it with R0); its table of contents lists
  no section on parsing optimisation. Further LZ77 parsing papers were checked at the
  level of titles and abstracts only, among them Langiu's journal paper on the "Zip case". One round of arXiv API
  searches failed (the service refused the requests); a later search of arXiv titles and abstracts found no paper
  that models a cache of repeat offsets.
- **Not read.** Not read here (the publisher's site refused automated access): the journal version of the
  dictionary-symbolwise flexible parsing paper (Journal of Discrete Algorithms 14, 2012; the subject of chapter 4 of
  Langiu's thesis), of which only the preprint above was read, and the full text of Langiu's journal paper on the "Zip
  case". Not accessible: the peer-reviewed versions of the two arXiv preprints; the full text of the journal paper on
  brotli; and a 2010 PhD thesis titled "Parsing algorithms for data compression"
  (University of Pisa), which its thesis record marks as not consultable until 24 June 2050. Of the thesis only the
  abstract was read: it treats bit-optimal LZ77 parsing as a shortest-path computation in a directed acyclic graph,
  and does not mention repeat offsets.
- This is a statement about the sources listed, not a claim of priority.

## Verification

```bash
python theorems/lz77-repeat-slots-exact-pruning/verify.py
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and runs in
about 20 seconds on a laptop. It exits with code 0 only if every check passes. Optima are computed by two exact
methods (enumeration of all parses, and a backward recursion over states). It checks:

- the DP itself: forward DP with and without prefix grouping = backward recursion, on every binary string of length
  ≤ 9, and = enumeration of all parses for length ≤ 6 (k = 1, 2, 3; REPMIN = 1, 2, 3);
- Theorem 1 directly, V(i, R′) ≤ V(i, R) + D(R, R′), for every pair of tuples with entries in [1, i] at every
  position i: k = 2 on every binary string of length 2..7, k = 3 on every binary string of length 2..6 (REPMIN = 2, 3;
  strings starting with a, which covers all binary strings up to swapping the letters);
- Theorem 2: the G3-pruned DP returns the optimum on every binary string of length 1..13 starting with a (swapping
  the letters gives the rest; k = 1, 2, 3, REPMIN = 2)
  under four comparator rules (lexicographically smallest, largest, position-dependent, seeded random), without
  prefix grouping, and with the G3\* margin; and on every ternary string of length 1..8, up to renaming the letters
  (REPMIN = 2, 3);
- Theorem 3 in three cost models (the costs of the Setting, the model of Remark 5, and repeat costs (3, 9, 3)[j] +
  γ(L) with the new-match costs of the Setting): the continuation bound for every pair of tuples (k = 2, every binary
  string of length 2..8 starting with a), pruned = unpruned with the lexicographically smallest comparator
  (k = 1, 2, 3, every binary string of length 1..11 starting with a), and, on 4000 seeded random cases, the formula with λ_i, D\*_i ≤ D, and D\*_i = D
  when n − i ≥ REPMIN + 1;
- Proposition 4, Remark 5 (including that the j = a margin is violated by exactly 10 pairs in the k = 2 range
  above),
  Proposition 6 (for (a) also the values of the hand proof and the failure of the continuation bound; exact rational
  probabilities for (b)) and the table of Remark 7, each pruned value along every sequence of comparator choices.

## Sources

Credit only (see [Literature](#literature)):

- C. Bloom (2015). *01-23-15 - LZA New Optimal Parse*. cbloom rants (blog), 23 January 2015. Not peer-reviewed.
  <https://cbloomrants.blogspot.com/2015/01/01-23-15-lza-new-optimal-parse.html>
- C. Bloom (2011). *12-17-11 - LZ Optimal Parse with A Star Part 3*. cbloom rants (blog), 17 December 2011. Not
  peer-reviewed. <https://cbloomrants.blogspot.com/2011/12/12-17-11-lz-optimal-parse-with-star_17.html>

Checked, not credited (see [Literature](#literature)):

- M. Crochemore, L. Giambruno, A. Langiu, F. Mignosi, A. Restivo (2012). *Dictionary-symbolwise flexible parsing*.
  Journal of Discrete Algorithms 14, 74–90. [doi:10.1016/j.jda.2011.12.021](https://doi.org/10.1016/j.jda.2011.12.021).
  The journal version was not read here: the publisher's site refused automated access. The preprint
  <https://hal.science/hal-00742078> was read in full.
- *Parsing Algorithms for Data Compression*. PhD thesis, University of Pisa, 2010; thesis record
  <https://etd.adm.unipi.it/t/etd-05252010-115131>, which marks it as not consultable until 24 June 2050. Only the
  abstract was read.
