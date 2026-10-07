# Ordering a first-match rule list: enumeration vs dynamic programming over subsets

**Type:** T6 (open: the problem is NP-hard), secondary T8 (super-poly → faster super-poly) ·
**Verification:** V2 (exact operation counts, with rivals)

**Problem.** There are k rules and m items. Rule r either matches item i or not. If r is the *first* rule of the
order that matches i, item i pays cost[i][r]. An item that no rule matches pays its own fixed default. Find the
order of the k rules with the smallest total price, and return that price and an optimal order. This is how a
first-match rule list, a decision list or a packet filter assigns items to rules.

**In the literature.** Two special cases are well studied:
- *MaxDL* (Chakravarthy, Joshi, Ramakrishnan, Godbole & Balakrishnan, IJCNLP 2008) orders labelled rules into a
  decision list so that as many items as possible get their correct label. Here that means cost[i][r] = 0 if rule r
  gives item i its correct label and 1 otherwise, with every default equal to 1.
- *Weighted lexicographic fitting* (Yee, Dahan, Hauser & Orlin, Marketing Science 2007) orders aspects so that a
  lexicographic rule agrees with as much weight of observed preferences as possible. An item is a pair of profiles
  with an observed preference and a weight w. A rule is an aspect, and it matches the pair iff it tells the two
  profiles apart. The cost is w if the aspect ranks the pair against the observed preference, and 0 otherwise.
  Schmitt & Martignon (JMLR 2006) study the unit-weight version for the cue orders of lexicographic strategies.

This entry allows any non-negative cost per (item, rule), a direct generalization. The correctness argument and
the hardness reduction below carry over unchanged.

| Algorithm | Time (k rules, m items) | Space | Implementation |
|---|---|---|---|
| Enumeration of all k! orders | O(k!·k·m); exactly k!(k+1)(k+3)/3 − 1 counted operations on the V2 family | Θ(k + m) | [enumeration.py](implementations/enumeration.py) |
| Dynamic programming over subsets of rules (Yee et al. 2007) | Θ(2^k·(k + m)) on every input; exactly 3k² + (7k−2)·2^(k−1) + 2 on the V2 family | Θ(2^k) | [subset_dp.py](implementations/subset_dp.py) |

**Why it works.** The DP is Algorithm 2 of Yee et al. (2007). They note that it is similar to the Held–Karp
recurrence (1962), and they present it as turning a search over n! orders into a search over 2^n subsets. Its
correctness rests on their Propositions 2 and 3. Suppose the set S of rules already placed is known. Then placing
rule r next captures exactly the items that r matches and no rule of S matches, and the order inside S does not
matter. Their proof uses only this fact, so it holds for arbitrary costs; entry.json gives the proof in this
entry's notation. Hence best[S ∪ {r}] = min over the last rule r of best[S] + gain(S, r). One pass over the items
per subset collects gain(S, r) for every r. An item matched by t rules stays uncaptured for 2^(k−t) subsets and
then adds t costs, and t·2^(k−t) ≤ 2^(k−1), so the whole DP is Θ(2^k·(k + m)). CORELS (Angelino et al.) uses the
same fact when it learns rule lists. Its equivalent-support bound and symmetry-aware map keep only the best
ordering of each set of antecedents.

**Why it stays exponential.** The problem is NP-hard. The reduction is the one Schmitt & Martignon (2006,
Theorem 5) give for lexicographic cue orders, from feedback arc set (NP-complete, Karp 1972). Every arc u → v
becomes an item that only u and v match, with cost 0 for u and 1 for v. An order then pays exactly for its backward
arcs, and the minimum equals the minimum feedback arc set. When every item matches at most two rules, the problem
is exactly the linear ordering problem (NP-hard; Grötschel, Jünger & Reinelt 1984). The proof is in entry.json.

**Verification.**
- *V1:* the validator runs k = 0..7, 9 and 11, 6 instances per size. The instances are:
  - random items;
  - feedback-arc-set reductions;
  - the cyclic V2 family;
  - all-pairs (linear ordering) instances;
  - ties (zero costs, items matched by no rule or by every rule, duplicated items);
  - large costs.

  Costs at non-matching positions are random and must be ignored. The `check` oracle is independent of both
  implementations:
  - it recomputes the order's cost from rule positions;
  - it compares the cost with a lower bound (each item's cheapest matching rule);
  - otherwise it runs a branch and bound over order prefixes. This is exact for k ≤ 7; above that it has a node
    budget, after which an improving single-rule move proves non-optimality.
- *Experiment* ([script](../../experiments/2026-10-07_first_match_checks.py)):
  - exact counts against the closed forms;
  - 476 extra implementation runs, all accepted by the oracle except 2 undecided at k ≥ 8;
  - the feedback-arc-set reduction on 300 random weighted digraphs: the optimum always equals the brute-force minimum
    feedback arc set weight, and the reduced cost equals the backward-arc weight on 39 314 orders;
  - the linear-ordering identity on 25 741 (instance, order) pairs;
  - an oracle control: 2515 deliberately wrong outputs rejected, 0 accepted, 0 undecided, and 216 correct outputs
    accepted.
- *V2 (exact counts):* on the cyclic family, item i is matched by rules i and i+1 (mod k), with m = k items.
  CountingInt entries count every truth test, comparison, +, −, <<, & and | on input-derived values.
  - Enumeration: exactly k!(k+1)(k+3)/3 − 1 (k ≥ 2). Fitted on k = 4..8, against the rivals k!·k, k!·k³ and k·2^k.
  - DP: exactly 3k² + (7k−2)·2^(k−1) + 2 (k ≥ 2). Fitted on k = 6..14, against the rivals k²·2^k, 2^k, k! and 3^k.

  The shape diagnostic runs on the DP counts for k = 3..18. The enumeration count is factorial and outside the
  diagnostic's growth family.

**Caveats.** O(k!·k·m) is the enumeration's worst case. An item that every rule matches costs one test per order.
In the DP, additions and comparisons between two plain integers are not counted, nor is subset bookkeeping on plain
integers (entry.json gives the details). Above k = 7 the V1 oracle is exact only when the lower bound is attained or
the branch and bound finishes within its budget. The entry makes no claim about the fastest known algorithm for
this problem.

**Sources.** Yee, Dahan, Hauser & Orlin, Marketing Science 2007 (the subset DP: Algorithm 2, Propositions 2–3) ·
Schmitt & Martignon, JMLR 2006 (Theorem 5: the feedback-arc-set reduction) · Chakravarthy, Joshi, Ramakrishnan,
Godbole & Balakrishnan, IJCNLP 2008 (MaxDL) · Karp 1972 · Grötschel, Jünger & Reinelt 1984 · Held & Karp 1962 ·
Bodlaender, Fomin, Koster, Kratsch & Thilikos 2012 · Angelino, Larus-Stone, Alabi, Seltzer & Rudin, JMLR 2018
(arXiv 1704.01701).
