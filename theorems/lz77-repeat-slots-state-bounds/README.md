# How many states the exact DP for LZ77-style parsing with k repeat-offset slots holds, with and without exact pruning

> **Provenance: 🟡⏳ Undetermined (may be our own result).**
>
> *Base:* the folklore dynamic program over (position, slot contents). C. Bloom's blog posts (not peer-reviewed)
> contain the dynamic program over {state, pos} with the repeat-match offsets in the state, the remark that a state
> space of size S needs a table of size N·S and becomes too big once repeat matches are present, and pruning by a
> threshold that he calls approximate (2015), and a forward optimal parser over {Pos, State} nodes with a general
> adaptive state (2011). Neither post counts the states of the dynamic program with repeat offsets, and neither gives
> a proof. The pair entry
> [lz77-repeat-slots-enumeration-vs-slot-dp](../../pairs/lz77-repeat-slots-enumeration-vs-slot-dp/) writes out the
> correctness proof of the dynamic program.
>
> *Beyond the sources read:* this note proves exact upper and lower bounds on the number of states and relaxations for
> every k (Theorem C), the exact behaviour of the optimum-preserving pruning rule G3 of
> [lz77-repeat-slots-exact-pruning](../lz77-repeat-slots-exact-pruning/) on aⁿ (Theorem A), and that this pruning
> keeps Θ(n^(k+1)) states in the worst case, the same order as without pruning (Theorems F1, F2, Corollary W).
> Nothing read states these state bounds.
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

The model is that of [lz77-repeat-slots-exact-pruning](../lz77-repeat-slots-exact-pruning/#setting), repeated here.
A string s = s[0] … s[n−1] over an integer alphabet is parsed from position 0 to n. The k slots
R = (R[0], …, R[k−1]) start as 1^k = (1, …, 1). At position i:

| Token | Allowed if | Cost | Next position, next slots |
|---|---|---|---|
| literal | i < n | 9 | i + 1, R |
| repeat of slot j, length L | R[j] ≤ i, L ≥ REPMIN, i + L ≤ n, s[i+t] = s[i+t−R[j]] for 0 ≤ t < L | 3 + j + γ(L) | i + L, (R[j], R[0..j−1], R[j+1..k−1]) |
| new match, distance d, length L | 1 ≤ d ≤ i, L ≥ 2, i + L ≤ n, s[i+t] = s[i+t−d] for 0 ≤ t < L | 2 + γ(L−1) + γ(d) | i + L, (d, R[0..k−2]) |

γ(x) = 2⌊log₂ x⌋ + 1. **REPMIN ≥ 2** throughout, except in Theorem C, which holds for every REPMIN ≥ 1. Let ml(i, d) be the largest L with i + L ≤ n and
s[i+t] = s[i+t−d] for all t < L. f(x) denotes the optimum of the prefix s[0..x).

**Counting conventions.**
- *Unpruned DP.* st[i] is the set of states (slot tuples) present at position i; these are exactly the slot tuples
  reachable at position i from (0, 1^k). S_i = |st[i]|, S = Σ_{i=0}^{n} S_i, and G_i is the number of distinct
  prefixes R[0..k−2] among st[i] (for k = 1 the prefix is empty and G_i = 1). The DP with *prefix grouping* relaxes
  at each position i < n, for every state, its literal and its repeats, and, once per prefix group, the new matches.
  Its number of relaxations is

      T = Σ_{i=0}^{n−1} [ Σ_{R ∈ st[i]} (1 + Σ_{j : R[j] ≤ i} max(0, ml(i, R[j]) − REPMIN + 1)) + G_i Σ_{d=1}^{i} max(0, ml(i, d) − 1) ].

- *Pruned DP* (rule G3 or G3\* of the pruning note: at each position i < n one cheapest state R\* is chosen by any rule
  and every R ≠ R\* with c(R) ≥ c(R\*) + margin(R, R\*) is deleted). K_i is the set of states kept at position i < n,
  and S^kept = Σ_{i<n} |K_i| + |st′[n]|, where st′[n] is the set of states present at position n (never pruned).

## Statements

**Theorem C (unpruned DP).** Let k ≥ 1 and REPMIN ≥ 1, and let δ = 1 if REPMIN = 1 and δ = 0 if REPMIN ≥ 2.
1. *Every input of length n.* S_i ≤ 1 for i ≤ 2 and S_i ≤ (i−2)^k for i ≥ 3; G_i ≤ max(1, (i−2)^(k−1)). Hence

       S ≤ 3 + Σ_{j=1}^{n−2} j^k,     T ≤ S₀ + Σ_{i=1}^{n−1} [ S_i (1 + k(n−i−1+δ)) + G_i · i · (n−i−1) ].

2. *The string aⁿ.* For 2k + 1 ≤ i ≤ n, S_i ≥ Π_{t=1}^{k} (i − 2t) and G_i ≥ Π_{t=1}^{k−1} (i − 2t). For n ≥ 1 and
   REPMIN ∈ {1, 2} the bound on T in item 1 holds with equality (for n = 0, T = 0 < 1 = S₀). For k = 1,
   S = 3 + Σ_{j=1}^{n−2} j exactly (n ≥ 2).
3. *Worst case, k and REPMIN fixed.* max_{|s|=n} S = n^(k+1)/(k+1) + O(n^k) and
   max_{|s|=n} T = n^(k+2)/(k+2) + O(n^(k+1)); aⁿ attains both up to the error terms.

**Theorem A (G3 pruning on aⁿ).** Let k ≥ 1, REPMIN ≥ 2, n ≥ 3, the pruned DP with G3 or G3\*, and any comparator
rule. Let f(0) = 0, f(1) = 9, f(2) = 18 and f(i) = 12 + γ(i − 2) for i ≥ 3.
1. For every i ∈ [0, n−1], K_i = {1^k}, and the value of 1^k at i is f(i).
2. st′[n] = {1^k} ∪ {(d, 1^(k−1)) : 2 ≤ d ≤ n − 2}, which is n − 2 states.
3. S^kept = n + (n − 2) = 2n − 2.
4. For REPMIN = 2 the pruned DP makes exactly n + k(n−1)(n−2)/2 + n(n−1)(n−2)/6 relaxations.

The total 2n − 2 counts one state at each of the n pruned positions plus the n − 2 unpruned states at position n.
If position n were pruned as well, the same argument (step 4 below at i = n) leaves one state there, and the total is
n + 1.

**Corollary S (separation on aⁿ only).** On aⁿ the unpruned DP has at least n^(k+1)/(k+1) − O(n^k) states and
n^(k+2)/(k+2) + O(n^(k+1)) relaxations (REPMIN = 2), the pruned DP 2n − 2 states and n³/6 + O(kn²) relaxations
(n ≥ 3). So on this family pruning separates the state counts for every k, and the relaxation counts for k ≥ 2 (for
k = 1 both are Θ(n³)). It does not separate them in the worst case (Corollary W).

**Fact P (exact prefix minimum).** Under G3 and under G3\*, the smallest value present at every position x ≤ n of
the pruned run is f(x).

**Theorem F1 (k ≤ 4).** Let F1(m) = x₁ab x₂ab … x_m ab, where every x_j occurs once (n = 3m; block j occupies
positions 3j−3, 3j−2, 3j−1). Let k ∈ {1, 2, 3, 4}, REPMIN ≥ 2, any comparator rule. For every j with
k + 2 ≤ j ≤ m − 1 and every x ∈ {3j, 3j+1, 3j+2}, every state (3t₀, …, 3t_{k−1}) with 2 ≤ t_a ≤ j − a − 1 is kept at
x under G3, and under G3\* at the positions x with n − x ≥ REPMIN + 1. Hence, under G3,

    Σ_{x<n} |K_x| ≥ 3 Σ_{j=k+2}^{m−1} Π_{a=0}^{k−1} (j − a − 2) = 3·k!·C(m−2, k+1) = n^(k+1)/(3^k (k+1)) − O(n^k).

**Proposition F1′ (F1 does not suffice for k ≥ 5).** For every k ≥ 1, REPMIN ≥ 2, any comparator rule, G3 or G3\*,
and every position x < n of F1(m), every kept state has at most 4 entries outside {1, 3}. So on F1 the pruned DP
keeps O(n⁴) states at each position x < n. The states at position n (which is not pruned) have at most 5 entries
outside {1, 3}, so there are O(n⁵) of them, and the total S^kept is O(n⁵), for every fixed k.

**Theorem F2 (every k).** Let k ≥ 1 and L ≥ 2 with

    (K)   (k − 1)/2 < 9L − 3 − γ(L − 1)

(L = 2 allows k ≤ 28; L = k + 1 allows every k). Let M = k + L, let G_min be the least power of two with
γ(G_min) ≥ 9L − 1 (G_min = 256 for L = 2), G the least multiple of M with G ≥ max(G_min, k),
span = G(2^(k−1) − 1) + (k − 1), and B′ the least multiple of M with B′ ≥ max(G_min, span + 1). The string
F2(k, L, m, T) consists of:
- a *dictionary* of m blocks, block t (0 ≤ t < m) being k fresh symbols followed by the word w = c₁ … c_L (pairwise
  distinct letters that occur only in occurrences of w); the words start at P_D = {Mt + k : 0 ≤ t < m}, and the
  dictionary has length Mm;
- B′ fresh symbols, ending at Q₀ = Mm + B′ (a multiple of M);
- the word w at the positions q_i = Q₀ + G(2^(i−1) − 1) + (i − 1), i = 1, …, k, with fresh symbols in between;
- T fresh symbols after q_k + L. So n = Q₀ + span + L + T.

Every fresh symbol occurs once. For every comparator rule and every (p₀, …, p_{k−1}) ∈ P_D^k, the state

    R(p) = (q_k − p₀, q_{k−1} − p₁, …, q₁ − p_{k−1})

is kept (a) under G3 at every position x ∈ X = [q_k + L, n − 1]; (b) under G3\* at every x ∈ X with
n − x ≥ REPMIN + 1, if T ≥ REPMIN + 1. These m^k states are distinct, so under G3, Σ_{x<n} |K_x| ≥ T·m^k.

**Corollary W (worst case of the pruned DP).** Fix k ≥ 1 and REPMIN ≥ 2, let L = 2 if k ≤ 28 and L = k + 1
otherwise, M = k + L and C = B′ + span + L (constants of Theorem F2). Over strings with an unbounded integer alphabet,
for n ≥ C + 2M,

    (n − C − 2M + 1)^(k+1) / (2^(k+1) M^k)  ≤  max_{|s|=n} S^kept(s)  ≤  3 + Σ_{j=1}^{n−2} j^k      (under G3),

and the same under G3\* for n ≥ C + REPMIN + 2M with C replaced by C + REPMIN. So **exact pruning keeps Θ(n^(k+1))
states in the worst case**, the order of the unpruned DP. The relaxations of the pruned DP are at least its kept
states at positions < n (each relaxes its literal) and at most the T of Theorem C, so in the worst case they are
Ω(n^(k+1)) and O(n^(k+2)); the note does not determine their order.

The strings F1 and F2 use many distinct symbols: F1(m) uses m + 2, and F2 with T = Mm uses n − (m + k − 1)L symbols,
a fraction (2k + L)/(2(k + L)) + o(1) of n. **The note claims nothing about strings over a fixed alphabet.**

## Proofs

### Theorem C

*Item 1.* A slot value other than the initial 1 was pushed by a new match at some position p with distance d ≤ p and
length ≥ 2, which ended at a position p + L ≤ i; so 1 ≤ d ≤ i − 2. Repeats only reorder the slots. Hence for i ≥ 3 all
entries lie in [1, i−2], giving S_i ≤ (i−2)^k and G_i ≤ (i−2)^(k−1); for i ≤ 2 no new match can have ended (it needs
p ≥ 1 and p + 2 ≤ i), so st[i] ⊆ {1^k}. Summing, S ≤ 3 + Σ_{i=3}^{n} (i−2)^k. None of this uses REPMIN. For T: if
n = 0, then T = 0 ≤ S₀. If n ≥ 1, at position 0 no slot value and no distance is ≤ 0, so only the literal of 1^k is
relaxed, which is the term S₀. For i ≥ 1, ml(i, d) ≤ n − i, so each slot gives at most
n − i − REPMIN + 1 ≤ n − i − 1 + δ repeat lengths and each distance d ≤ i at most n − i − 1 new-match lengths.

*Item 2.* Let 2k + 1 ≤ i ≤ n and choose 1 ≤ d_t ≤ i − 2t for t = 1, …, k. Code a^(i−2k) by literals, then make new
matches of length 2 at the positions i − 2k, i − 2k + 2, …, i − 2, the one at position i − 2t with distance d_t. Each
is allowed: d_t ≤ i − 2t, every distance matches in aⁿ, and the match ends at i − 2t + 2 ≤ n. The last match pushes
d₁, so slot t − 1 ends up holding d_t. Distinct choices give distinct tuples at position i, and distinct
(d₁, …, d_{k−1}) give distinct prefixes. The construction uses only literals and new matches, so it works for every
REPMIN. For the identity: in aⁿ, ml(i, d) = n − i for every 1 ≤ d ≤ i; for i ≥ 1 every slot value v satisfies v ≤ i
(v = 1 or v ≤ i − 2); so with REPMIN ∈ {1, 2} every state at i ≥ 1 has exactly k(n − i − REPMIN + 1) =
k(n − i − 1 + δ) repeat relaxations and every group i(n − i − 1) new-match relaxations. At i = 0 (a position < n when
n ≥ 1) only the literal of 1^k is allowed. For k = 1 the lower bound i − 2 equals the upper bound for i ≥ 3.

*Item 3.* We use, for fixed k and N → ∞, Σ_{j=1}^{N} j^k = N^(k+1)/(k+1) + O(N^k) (compare with ∫₀^N x^k dx and
∫₁^(N+1) x^k dx), and hence

    (Σ*)   Σ_{j=1}^{N} j^k (N − j) = N Σ j^k − Σ j^(k+1) = N^(k+2)/((k+1)(k+2)) + O(N^(k+1)).

States: item 1 gives at most n^(k+1)/(k+1) + O(n^k); on aⁿ, Π_t (i − 2t) ≥ (i − 2k)^k, and
Σ_{i=2k+1}^{n} (i − 2k)^k = Σ_{j=1}^{n−2k} j^k = n^(k+1)/(k+1) − O(n^k). Relaxations, upper bound: S₀ = 1, and for
1 ≤ i ≤ n − 1 we have S_i ≤ i^k, G_i·i ≤ i^k and n − i − 1 + δ ≤ n − i, so item 1 gives
T ≤ 1 + Σ_{i=1}^{n−1} [i^k + (k + 1) i^k (n − i)] ≤ Σ_{i=1}^{n} [i^k + (k + 1) i^k (n − i)] = n^(k+2)/(k+2) + O(n^(k+1))
by (Σ*). Here the i = n term of the last sum, n^k, absorbs the i = 0 term: S₀ = 1 ≤ n^k, and even the cruder value
1 + k(n − 1) of the i = 0 term of a bound summed from i = 0 would be at most n^k, by Bernoulli's inequality.
Lower bound on aⁿ with REPMIN = r: a state at i ≥ 1 has k·max(0, n − i − r + 1) repeat relaxations and a group
i(n − i − 1) new-match relaxations; with j = i − 2k, S_i ≥ j^k and G_i·i ≥ j^(k−1)·j, so
T ≥ k Σ_{j=1}^{N₁} j^k (N₁ − j) + Σ_{j=1}^{N₂} j^k (N₂ − j) with N₁ = n − 2k − r + 1 and N₂ = n − 2k − 1, which is
k n^(k+2)/((k+1)(k+2)) + n^(k+2)/((k+1)(k+2)) − O(n^(k+1)) = n^(k+2)/(k+2) − O(n^(k+1)) by (Σ*). ∎

### Theorem A

**Lemma Γ.** (a) γ(x + y + 1) ≤ γ(x) + γ(y) + 1 for integers x, y ≥ 1. (b) γ(z + 1) ≤ γ(z) + 2 for z ≥ 1.

*Proof.* (a) Let μ = max(x, y) and e = ⌊log₂ μ⌋. Then x + y + 1 ≤ 2μ + 1 ≤ 2(2^(e+1) − 1) + 1 < 2^(e+2), so
γ(x + y + 1) ≤ 2e + 3 = γ(μ) + 2 ≤ γ(x) + γ(y) + 1, because the smaller of γ(x), γ(y) is at least 1.
(b) z + 1 ≤ 2z. ∎

*Proof of 1, by strong induction on i.* Assume K_p = {1^k} with value f(p) for all p < i.
1. *Which states exist at i.* Every state at i comes from 1^k at some p < i: a literal or a repeat (the slot value is
   1, which needs p ≥ 1) gives 1^k, since moving a 1 to the front of 1^k changes nothing; a new match with distance
   d ≤ p and length i − p ≥ 2 gives (d, 1^(k−1)). For i ≤ 2 no new match ends at i.
2. *The value of 1^k at i* is the minimum of the literal f(i−1) + 9, the new matches with d = 1 from 1 ≤ p ≤ i − 2,
   costing f(p) + 3 + γ(i − p − 1), and the repeats, which are never cheaper than the new match with d = 1 from the
   same p (3 + j + γ(i − p) ≥ 3 + γ(i − p − 1)). For i ≤ 2 the value is 0, 9, 18. For i ≥ 3: p = 1 gives
   12 + γ(i − 2); p = 2 (if i ≥ 4) gives 21 + γ(i − 3) ≥ 19 + γ(i − 2) by Γ(b); p ≥ 3 gives
   15 + γ(p − 2) + γ(i − p − 1) ≥ 14 + γ(i − 2) by Γ(a) with x = p − 2, y = i − p − 1; the literal gives 27 for i = 3
   and 21 + γ(i − 3) ≥ 19 + γ(i − 2) for i ≥ 4. So the value is f(i). (The d = 1 match from p = 1 needs only L ≥ 2,
   so it is allowed for every REPMIN.)
3. *The other states.* For 2 ≤ d ≤ i − 2 the state (d, 1^(k−1)) is reached only by new matches with distance d from
   some p with d ≤ p ≤ i − 2, so its value c satisfies: from p = 2 (only for d = 2), c ≥ 20 + γ(i − 3) + γ(d) ≥
   f(i) + γ(d) + 6; from p ≥ 3, c ≥ 14 + γ(p − 2) + γ(i − p − 1) + γ(d) ≥ 13 + γ(i − 2) + γ(d) = f(i) + γ(d) + 1.
4. *Pruning.* So 1^k is the unique cheapest state at i, and R\* = 1^k whatever the comparator rule. For
   R = (d, 1^(k−1)), a₀ = 0 and the G3 margin is γ(d) − 1 + Σ_{a≥1} max(0, γ(1) − 1 − a) = γ(d) − 1 < γ(d) + 1 ≤
   c − f(i), so R is deleted. The G3\* margin is not larger (pruning note, Theorem 3). Hence K_i = {1^k}. ∎

*Proof of 2.* The states at n come from 1^k at p ≤ n − 1: 1^k, and (d, 1^(k−1)) for 1 ≤ d ≤ p ≤ n − 2. Every
d ∈ [2, n − 2] occurs (take p = n − 2, L = 2), and d = 1 gives 1^k. That is 1 + (n − 3) = n − 2 states. ∎

*Proof of 4.* At position i the single kept state 1^k makes one literal relaxation; for 1 ≤ i ≤ n − 2, k repeats
with n − i − 1 lengths each (the slot value 1 ≤ i, ml = n − i, REPMIN = 2); and i distances with n − i − 1 new-match
lengths each, in its single prefix group. At i = 0 and i = n − 1 only the literal is allowed. The total is
n + Σ_{i=1}^{n−2} (k + i)(n − 1 − i) = n + k(n−1)(n−2)/2 + n(n−1)(n−2)/6. ∎

*Corollary S* follows from Theorem C (items 2 and 3) and Theorem A.

### Fact P

Every value of the pruned run is the cost of a token sequence from (0, 1^k), so the smallest value at x is at least
f(x). For the converse, run the witness argument of the pruning note (proof of Theorem 2) with target x instead of n:
a witness is (i, R, τ) with R present at i, τ a token sequence from (i, R) ending at position x, and
c(i, R) + cost(τ) = f(x). Tokens that end at a position ≤ x read only s[0..x), so Theorem 1 (resp. 3) of the pruning
note applies to the string s[0..x). For G3 the margin does not depend on x. For G3\* the margin with remaining length
x − i is at most the margin with remaining length n − i that the run uses, because the maximum in E_a is taken over a
smaller range of L. So a deleted witness passes to R\*, and the rest of the argument is unchanged. ∎

### Two facts about strings with fresh symbols

A *fresh* symbol occurs once in s. Let a word w = c₁ … c_L have pairwise distinct letters that occur only inside
occurrences of w, with consecutive occurrences separated by at least one fresh symbol, and assume that every symbol
of s is fresh or lies in an occurrence of w. For an occurrence o let
U(o) = {o − o′ : o′ < o an occurrence}.

**Fact M.** (M1) A token that covers a fresh symbol is a literal, so every parse has token boundaries on both sides
of every fresh symbol. (M2) Every match token (repeat or new) with start y, length ℓ ≥ 2 and distance v lies inside
one occurrence o (y = o + u with u + ℓ ≤ L), and v ∈ U(o).

*Proof.* (M1) A match token copies earlier symbols, and a fresh symbol has no earlier copy. (M2) The covered symbols
are not fresh, so they lie in occurrences; two consecutive covered symbols lie in the same occurrence, since
occurrences are separated by fresh symbols. s[y − v] = s[y] = c_{u+1}, and c_{u+1} occurs only at offset u of
occurrences, so y − v = o′ + u for an earlier occurrence o′. ∎

### Theorem F1

1. *Costs.* By Fact M (word ab, occurrences at 3j − 2), the match tokens are the "ab" of block j ≥ 2, with distance
   3t (1 ≤ t ≤ j − 1) and length exactly 2, and every pushed slot value is a multiple of 3. Block j's "ab" costs 18
   by literals; 3 + γ(3t) ≥ 6 by a new match, with equality iff t = 1; and 6 + b ≥ 6 by a repeat of slot b holding a
   multiple of 3 (possible only for REPMIN = 2), with equality iff b = 0. Block 1's "ab" costs 18 and each x_j costs 9.
2. *Prefix optimum and cheapest states.* f(3j) = 27 + 15(j − 1), f(3j + 1) = f(3j) + 9, f(3j + 2) = f(3j) + 18;
   positions 3j + 1 and 3j + 2 are reached only by literals. A prefix parse attains f(3j) iff block 1 is coded by
   literals and every later block costs exactly 6, i.e. uses new(3) or a repeat of slot 0. Block 2 must use new(3),
   since no slot holds a multiple of 3 before it; after that slot 0 holds 3 (new(3) puts 3 there, a repeat of slot 0
   keeps it there). So every optimal prefix parse ending at x ≥ 6 leaves slot 0 = 3 and all entries in {1, 3}. By
   Fact P every cheapest state at x ≥ 6 has value f(x), hence is reached by such a parse: R\*(x)[0] = 3 and all its
   entries are in {1, 3}.
3. *The chain.* Fix j and t₀, …, t_{k−1} as in the statement and put r_a = 3t_a ≥ 6. Let S be the state chosen as
   comparator at position 3(j−k) + 1 (the a of block j − k + 1; note j − k ≥ 2). By Fact P and step 2, its value is
   f(3(j−k)) + 9 and S[0] = 3. From S, code the "ab" of block j − k + 1 by new(r_{k−1}); then for i = 2, …, k code
   block j − k + i by the literal x_{j−k+i} and new(r_{k−i}). These matches are allowed, since
   t_{k−i} ≤ j − (k − i) − 1. After i blocks (i ≥ 1), at the three positions x of the next block (the first reached
   by the match, the other two by literals), the chain state is R_i = (r_{k−i}, …, r_{k−1}, S[0..k−i−1]), and its cost exceeds f(x) by
   e_i = Σ_{a=k−i}^{k−1} (γ(r_a) − 3). Since R_i[0] ≥ 6 differs from the first entry 3 of every cheapest state,
   a₀ = 0 against every possible comparator, and the G3 margin is at least Σ_{b<i} (γ(R_i[b]) − 1 − b). Hence
   e_i − margin ≤ Σ_{b<i} (b − 2) = i(i − 5)/2 < 0 for 1 ≤ i ≤ 4.
4. *Induction along the chain.* If a chain state is present at a chain position with value at most its chain cost, it
   is kept there (its excess over the cheapest value is below the margin). It is then relaxed, by its literal and by
   the next new match (with prefix grouping, from a group minimum that is not larger), so the next chain state is
   present with value at most its chain cost. The start S is kept because it is the comparator. At i = k the chain
   state is (3t₀, …, 3t_{k−1}).
5. *Count.* Distinct (t₀, …, t_{k−1}) give distinct states. Σ_{j=k+2}^{m−1} Π_{a<k} (j − 2 − a) =
   k! Σ_{j=k+2}^{m−1} C(j − 2, k) = k!·C(m − 2, k + 1) by the hockey-stick identity.
6. *G3\*.* If n − x ≥ REPMIN + 1, the range REPMIN ≤ L ≤ n − x contains two consecutive integers ≥ 2, one of which is
   not a power of two, so λ_x = 0 and the G3\* margin equals the G3 margin (pruning note, Theorem 3). The chain
   positions before x satisfy this too. ∎

### Proposition F1′

For x < 6 every state is 1^k. Let x ≥ 6 and let R ≠ R\*(x) be kept, with excess e = c(R) − f(x). Call an entry outside
{1, 3} *free*. Since all entries of R\*(x) lie in {1, 3}, free entries sit at slots ≥ a₀.
1. Each free entry v (a multiple of 3, v ≥ 6, so γ(v) ≥ 5) was pushed by new(v) in its own block, at cost 3 + γ(v)
   against that block's minimum 6: distinct slots hold entries from distinct pushes, and a block contains at most one
   match token. Every other block costs at least its minimum, so e ≥ Σ_free (γ(v) − 3).
2. In the G3 margin Σ_{b≥a₀} max(0, γ(R[b]) − 1 − b), a free entry v at slot b contributes max(0, γ(v) − 1 − b), an
   entry 1 contributes 0, and an entry 3 contributes max(0, 2 − b). A 3 at slot 0 does not count: if R[0] = 3 = R\*[0],
   then a₀ ≥ 1. So the entries 3 contribute at most 1 (a 3 at slot 1).
3. Keeping R requires e < margin, hence Σ_free [γ(v) − 3 − max(0, γ(v) − 1 − b_v)] < [a 3 at slot 1]. Each bracket
   equals min(γ(v) − 3, b_v − 2) ≥ min(2, b_v − 2).
4. With u ≥ 5 free entries at distinct slots, the left side is at least its value on the u lowest available slots,
   where slots ≥ 4 contribute 2: at least −2 − 1 + 0 + 1 + 2 = 0 (slots 0..4), and at least −2 + 0 + 1 + 2 + 2 = 3 if
   slot 1 holds a 3. Either way the inequality fails. The G3\* margin is not larger than the G3 margin.
5. *Counts.* For fixed k, the tuples with at most u entries outside {1, 3}, each such entry at most n, number
   O(n^u). A state at position n is offered by a kept state at some x < n through one token; a literal or a repeat
   does not change the set of entries, and a new match adds one entry. So states at n have at most 5 free entries,
   and S^kept ≤ n·O(n⁴) + O(n⁵) = O(n⁵). ∎

### Theorem F2

1. *Residues and distinct differences.* Q₀ ≡ G ≡ 0 (mod M), so q_i ≡ i − 1 (mod M), and every word start in P_D is
   ≡ M − L = k. For i < i′, q_{i′} − q_i = G(2^(i′−1) − 2^(i−1)) + (i′ − i) ≡ i′ − i (mod G), with 1 ≤ i′ − i ≤ k − 1
   < G; so two pairs with the same difference have the same δ = i′ − i, and then G·2^(i−1)(2^δ − 1) = G·2^(l−1)(2^δ − 1)
   gives i = l. Moreover q_{i+1} − q_i = G·2^(i−1) + 1 > G > L + 1 (so consecutive words are separated by fresh
   symbols, as Fact M requires), q₁ − max P_D = B′ + L ≥ G_min, and q₁ − span > Mm because B′ > span.
2. *Distance sets.* For p ∈ P_D, U(p) ⊆ MZ. For a query word, U(q_i) = {q_i − p : p ∈ P_D} ∪ {q_i − q_l : l < i},
   and all its elements are ≥ G_min.
3. *Lemma Q1: a repeat inside the query word at q_{i′} uses a value pushed by a new match inside that same word.*
   Slot values are 1 or distances of earlier new matches, which lie in U(o) for their occurrence o (M2), and the
   repeat's value v must lie in U(q_{i′}), i.e. q_{i′} − v is an earlier occurrence.
   - v = 1: q_{i′} − 1 is fresh, so it is not an occurrence.
   - v from a dictionary word (v ≡ 0 mod M): q_{i′} − v ≡ i′ − 1, which is not ≡ k, so it is not in P_D; and
     q_{i′} − v = q_l would give v ≡ i′ − l ≢ 0.
   - v = q_i − p from an earlier query word (i < i′, p ∈ P_D): q_{i′} − v = p + (q_{i′} − q_i) ≡ k + (i′ − i) ≢ k, so
     it is not in P_D; and q_{i′} − v = q_l would give p = q_l − (q_{i′} − q_i) ≥ q₁ − span > Mm, impossible.
   - v = q_i − q_l with l < i < i′: q_{i′} − v > q_l > Mm is not in P_D; and q_{i′} − v = q_{l′} would make (l, l′) a
     second pair with the difference q_{i′} − q_i (l′ > l), contradicting step 1.
4. *Lemma Q2: on a query word every parse pays at least 9 per symbol, with equality only for literals* (also for the
   part of a parse that ends inside the word). Tokens stay inside the word (M1, M2). If a match token occurs, the
   first one is a new match (Q1), costing 2 + γ(ℓ − 1) + γ(v) ≥ 3 + γ(G_min) ≥ 9L + 2 > 9L, since v ≥ G_min.
5. *Lemma Q3.* f(x) = f(Mm) + 9(x − Mm) for Mm ≤ x ≤ n, and every parse of s[0..x) of cost f(x) codes s[Mm..x) by
   literals: there is a token boundary at Mm (M1), fresh symbols cost 9 each, query-word symbols at least 9 each with
   equality only for literals (Q2), and appending literals to an optimal parse of s[0..Mm) attains the bound.
6. *Cheapest states.* By Fact P, every cheapest state at x ∈ [Mm, n − 1] has value f(x), so it is reached by a parse
   that codes s[Mm..x) by literals; its slot values were pushed inside the dictionary or are initial. So
   R\*(x)[0] ∈ {1} ∪ MZ.
7. *The chain.* Let r_a = q_{k−a} − p_a ∈ U(q_{k−a}). Then r_a ≡ (k − a − 1) − k ≡ −(a + 1) ≢ 0 (mod M) and
   r_a ≥ G_min > 1, so r_a ∉ {1} ∪ MZ. Start from S = R\*(q₁), whose value is f(q₁); at q_i (i = 1, …, k) use the new
   match of length L with distance r_{k−i} (the word at q_i equals the word at p_{k−i}); code all fresh symbols by
   literals. For x ∈ [q_i + L, q_{i+1}] (with q_{k+1} := n) the chain state is R_i = (r_{k−i}, …, r_{k−1},
   S[0..k−i−1]), with excess e_i = Σ_{a=k−i}^{k−1} (2 + γ(L − 1) + γ(r_a) − 9L) over f(x) (Lemma Q3). Since R_i[0]
   ∉ {1} ∪ MZ, a₀ = 0 against every possible comparator, and the G3 margin is at least
   Σ_{b<i} (γ(R_i[b]) − 1 − b). So e_i − margin ≤ i(3 + γ(L − 1) − 9L) + i(i − 1)/2 < 0 by (K), as i ≤ k. The
   induction along the chain is as in Theorem F1; here the start S is the comparator at q₁ and is relaxed there
   directly. Under G3\*, λ_x = 0 whenever n − x ≥ REPMIN + 1, and the chain positions before q_k + L satisfy
   n − x ≥ T + 1.
8. *Count.* r_a determines p_a, so the m^k states are distinct; X has T positions. ∎

### Corollary W

*Under G3.* For n ≥ C + 2M put m = ⌊(n − C)/(2M)⌋ ≥ 1 and T = n − C − Mm ∈ [Mm, Mm + 2M − 1]. The constants
B′, span and C do not depend on m, so F2(k, L, m, T) has length C + Mm + T = n, and Theorem F2(a) gives
Σ_{x<n} |K_x| ≥ T m^k ≥ M m^(k+1) ≥ M ((n − C − 2M + 1)/(2M))^(k+1). *Under G3\*.* For n ≥ C + REPMIN + 2M put
m = ⌊(n − C − REPMIN)/(2M)⌋ and T = n − C − Mm ∈ [Mm + REPMIN, Mm + REPMIN + 2M − 1]; then T ≥ REPMIN + 1, and
Theorem F2(b) covers the T − REPMIN ≥ Mm tail positions with n − x ≥ REPMIN + 1, which gives the same bound with C
replaced by C + REPMIN. *Upper bound.* Every state of the pruned run was offered by an allowed token from a present
state, so it is reachable, and Theorem C applies. The symbol count: the words occupy (m + k)L positions and use L
letters, all other symbols are fresh. ∎

## Scope

- The model and the pruning rules are those of the pruning note; REPMIN ≥ 2 throughout, except in Theorem C
  (REPMIN ≥ 1). Static costs.
- The worst-case statements (Theorems F1, F2, Corollary W) use strings with Θ(n) distinct symbols. The note claims
  nothing about fixed alphabets, nothing about the worst-case order of the pruned DP's relaxations beyond the bounds
  Ω(n^(k+1)) and O(n^(k+2)), and nothing about a pruner that compares each state with every kept state.
- Theorem C counts reachable states; the relaxation identity of item 2 is for REPMIN ∈ {1, 2} and n ≥ 1.

## Literature

- **Credit for the base.** The DP over {state, pos} with the repeat-match offsets in the state, and the remark that a
  state space of size S needs a table of size N·S and is too big once repeat matches are present, are described by
  C. Bloom (blog post, 2015, not peer-reviewed).
- **Status:** every statement above is proved here and checked by `verify.py`. The closest sources could not be
  read (see below), so the note is labelled undetermined (it may be our own result) and claims no novelty beyond "not
  found in the sources read". Not found in the sources checked for the pruning note (Langiu's thesis, 2012; Ferragina–Nitto–Venturini,
  arXiv:0802.0835v1; Farruggia–Ferragina–Frangioni–Venturini, arXiv:1307.3872v1; Kosolobov, STACS 2018: full texts
  searched by keyword, relevant passages read; the preprint of the dictionary-symbolwise flexible parsing paper, HAL
  hal-00742078: read in full, one cost per edge of a graph on text positions, no state beyond the position), in which
  no treatment of repeat-offset slots and no count of parser states was found. The sources that were
  not read, and how arXiv was searched, are listed in the pruning note's
  [Literature](../lz77-repeat-slots-exact-pruning/#literature) section. This is a statement about these sources, not
  a claim of priority.

## Verification

```bash
python theorems/lz77-repeat-slots-state-bounds/verify.py
```

The script is deterministic (fixed seeds), uses the Python standard library only, needs no network, and runs in well
under a minute on a laptop. It exits with code 0 only if every check passes. It checks:

- Theorem C: the per-position bounds on S_i and G_i, the bound on S and the bound on T, on every binary string of
  length ≤ 12 and every ternary string of length ≤ 8 (up to renaming the letters, which changes no cost),
  k = 1, 2, 3, REPMIN = 1, 2, 3; on aⁿ the lower bounds, the identity for T (REPMIN = 1 and 2, n ≥ 1; and T = 0,
  S₀ = 1 for n = 0) and the exact count for k = 1, for several (k, n) including n = 1, 2; the identity (Σ*), the
  integral bounds, the Bernoulli step 1 + k(n − 1) ≤ n^k, and the error term of item 3 numerically for small k;
- Theorem A for k = 1..5 and every n = 3..40, G3 and G3\*, five comparator rules (including position-dependent and seeded
  random ones), REPMIN = 2, 3, 5: the kept sets and values, st′[n], the total 2n − 2, the relaxation count
  (REPMIN = 2), the total n + 1 with position n pruned, and that the pruned optimum is the unpruned one;
- Fact P on every F1 and F2 instance below;
- Theorem F1 for k = 1..4 on several m, under G3 with five comparator rules and under G3\*: every claimed state is
  kept at every claimed position, the cheapest states have first entry 3 and entries in {1, 3}, and the kept count is
  at least 3·k!·C(m − 2, k + 1); Proposition F1′ for k = 1..6 (at most 4 free entries in a kept state at every
  position x < n, at most 5 in a state at position n);
- Theorem F2 for k = 1..5 (L = 2) on several (m, T), for k ≤ 3 under G3 (three comparator rules) and G3\* (two),
  REPMIN = 2, 3, and for k = 4, 5 under G3 and G3\*, REPMIN = 2: every claimed state is kept at every claimed position, Lemma Q3, R\*(x)[0] ∈ {1} ∪ MZ, the distinct differences and residues of
  step 1, the symbol count, and condition (K) for L = 2 (exactly k ≤ 28) and L = k + 1 (k ≤ 1000);
- Corollary W: the length and the inequality T m^k ≥ (n − C − 2M + 1)^(k+1)/(2^(k+1) M^k) for every n in a range,
  for k = 1..4 under G3 and G3\*.

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
