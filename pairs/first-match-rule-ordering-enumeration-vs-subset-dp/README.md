# Ordering a first-match rule list: enumeration vs dynamic programming over subsets (and the same DP with zeta-transformed gains)

**Type:** T6 (open: the problem is NP-hard, given a cited hardness result), secondary T8 (super-poly → faster
super-poly) ·
**Verification:** V2 (exact operation counts, with rivals)

**Problem.** There are k rules and m items. Rule r either matches item i or not. If r is the *first* rule of the
order that matches i, item i pays cost[i][r]. An item that no rule matches pays its own fixed default. Find the
order of the k rules with the smallest total price, and return that price and an optimal order. This is how a
first-match rule list, a decision list or a packet filter assigns items to rules.

**In the literature** (cited background). Two special cases are well studied:
- *MaxDL* (Chakravarthy, Joshi, Ramakrishnan, Godbole & Balakrishnan, IJCNLP 2008) orders labelled rules into a
  decision list so that as many items as possible get their correct label. Here that means cost[i][r] = 0 if rule r
  gives item i its correct label and 1 otherwise, with every default equal to 1.
- *Weighted lexicographic fitting* (Yee, Dahan, Hauser & Orlin, Marketing Science 2007) orders aspects so that a
  lexicographic rule agrees with as much weight of observed preferences as possible. An item is a pair of profiles
  with an observed preference and a weight w. A rule is an aspect, and it matches the pair iff it tells the two
  profiles apart. The cost is w if the aspect ranks the pair against the observed preference, and 0 otherwise.
  Schmitt & Martignon (JMLR 2006) study the unit-weight version for the cue orders of lexicographic strategies.

This entry allows any non-negative cost per (item, rule), a direct generalization. The correctness argument and
the hardness reduction below are proved for it in [PROOFS.md](PROOFS.md).

| Algorithm | Time (k rules, m items) | Space | Implementation |
|---|---|---|---|
| Enumeration of all k! orders | O(k!·k·m) for k, m ≥ 1, given the documented cost of `itertools.permutations`; exactly k!(k+1)(k+3)/3 − 1 counted operations on the V2 family (k ≥ 2) | Θ(k) | [enumeration.py](implementations/enumeration.py) |
| Dynamic programming over subsets of rules (Yee et al. 2007) | Θ(2^k·(k + m)) on every input; exactly 3k² + (7k−2)·2^(k−1) + 2 on the V2 family (k ≥ 2) | Θ(2^k) | [subset_dp.py](implementations/subset_dp.py) |
| The same DP with gains from zeta transforms (technique of Koivisto & Sood 2004) | Θ(k²·2^k + k·m) on every input (k ≥ 1), including reading the input; exactly k² + 2k + 2 + (k² + 2k − 2)·2^(k−1) counted operations on the V2 family (k ≥ 2), more than the subset DP's for every k ≥ 6 | Θ(k·2^k) | [zeta_dp.py](implementations/zeta_dp.py) |

**Why it works.** The DP is Algorithm 2 of Yee et al. (2007). They note that it is similar to the Held–Karp
recurrence (1962), and they present it as turning a search over n! orders into a search over 2^n subsets; they prove
it correct for their costs (Propositions 2 and 3). Suppose the set S of rules already placed is known. Then placing
rule r next captures exactly the items that r matches and no rule of S matches, and the order inside S does not
matter. This fact alone gives the proof for arbitrary costs ([PROOFS.md](PROOFS.md), section 4). Hence
best[S ∪ {r}] = min over the last rule r of best[S] + gain(S, r). One pass over the items
per subset collects gain(S, r) for every r. An item matched by t rules stays uncaptured for 2^(k−t) subsets and
then adds t costs, and t·2^(k−t) ≤ 2^(k−1), so the whole DP is Θ(2^k·(k + m)). CORELS (Angelino et al.) uses the
same fact when it learns rule lists. Its equivalent-support bound and symmetry-aware map keep only the best
ordering of each set of antecedents.

**Third algorithm: gains from zeta transforms.** The DP above spends m capture tests on every subset. Group the
items by their match set instead: let a_r[U] be the sum of cost[i][r] over the items whose match set is U (for r in
U). An item is captured by r right after the set S exactly when its match set contains r and lies in the
complement of S, so gain(S, r) is the sum of a_r over the subsets of the complement: a zeta transform (sum over
subsets). Yates' method computes it for all sets with k·2^(k−1) additions per rule. The recurrence is then the same,
step by step, so this version returns exactly the subset DP's optimum and order ([PROOFS.md](PROOFS.md), section 11).
- *Time.* Θ(k²·2^k + k·m) on every input for k ≥ 1; the k·m term is reading the match flags. As k → ∞ (m any
  function of k) it beats the subset DP's Θ(2^k·(k + m)) exactly when m/k² → ∞, and loses exactly when m/k² → 0.
  For a fixed k both take Θ(m) time; as m grows, the speed-up in the entry's counting convention approaches the
  interval from 2^k/k + 3/2 to 5·2^(k−1)/k + 3, so it is of order 2^k/k (PROOFS.md, section 11.8).
- *What the counts show.* Its tables start from the 0 of the costs' number type, so on every instance with at least
  one item every transform addition is counted (PROOFS.md, section 11.5). On the V2 family (m = k items) it is the slower of the two DPs: its count,
  k² + 2k + 2 + (k² + 2k − 2)·2^(k−1), exceeds the subset DP's for every k ≥ 6, and the ratio grows like k/7.
- *Credit.* The technique, a transform over the subset lattice whose values feed a dynamic program over the sets
  placed so far, is that of Koivisto & Sood (JMLR 2004, section 4: Propositions 6 and 7 and Theorem 8, where the
  transform is called the Möbius transform; section 5: Theorem 11). They compute it with a fast transform for which
  they cite Kennes & Smets (1991); the fast transform is Yates' method (1937), as in the pair
  [subset-sum-zeta-transform-naive-vs-yates](../subset-sum-zeta-transform-naive-vs-yates). The min-plus recurrence and
  the reading at the complement are routine adaptations, proved here and not claimed as new.

**NP-hardness.** Feedback arc set reduces to this problem, by the reduction Schmitt & Martignon (2006,
Theorem 5) give for lexicographic cue orders. Every arc u → v becomes an item that only u and v match, with cost 0
for u and 1 for v (loops are deleted first; they lie in every feedback arc set). An order then pays exactly for its
backward arcs, and the minimum equals the minimum feedback arc set. The reduction and membership in NP are proved in
[PROOFS.md](PROOFS.md), section 7. Feedback arc set is NP-complete (Karp 1972; cited background), so the problem is
NP-hard. When every item matches at most two rules, the problem is exactly the linear ordering problem (both
directions are proved in PROOFS.md, section 8; its NP-hardness is also stated by Grötschel, Jünger & Reinelt 1984).

**Verification.**
- *V1:* the validator runs k = 0..7, 9 and 11, 6 instances per size. The instances are:
  - random items;
  - feedback-arc-set reductions;
  - the cyclic V2 family;
  - all-pairs (linear ordering) instances;
  - ties (zero costs, items matched by no rule or by every rule, duplicated items);
  - large costs.

  Costs at non-matching positions are random and must be ignored. The enumeration runs up to k = 7, both DPs on
  every size. The `check` oracle is independent of all three implementations:
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
- *Experiment for the third algorithm* ([script](../../experiments/2026-10-13_first_match_zeta_checks.py)):
  - its exact V2 counts, split by kind, for k = 2..17;
  - its exact counts on every instance (PROOFS.md, Theorem 11.5) on 270 seeded instances;
  - on 250 extra instances (k = 0..12) it returns exactly the subset DP's optimum and order; for k ≤ 7 that is the
    brute-force optimum, and the oracle accepts every output it can decide (2 undecided at k ≥ 8);
  - line-execution counts of the unchanged code, which give its executed operations;
  - negative controls: copies of the code with a deliberate error (the gain read at the wrong set, a pass left out,
    the defaults left out, ties broken differently, one extra counted addition, tables started from the plain 0 so
    that additions of two plain zeros go uncounted) are all caught.
- *V2 (exact counts):* on the cyclic family, item i is matched by rules i and i+1 (mod k), with m = k items.
  CountingInt entries count every truth test, comparison, +, −, <<, & and | on input-derived values.
  - Enumeration: exactly k!(k+1)(k+3)/3 − 1 (k ≥ 2). Fitted on k = 4..8, against the rivals k!·k, k!·k³ and k·2^k.
  - DP: exactly 3k² + (7k−2)·2^(k−1) + 2 (k ≥ 2). Fitted on k = 6..14, against the rivals k²·2^k, 2^k, k! and 3^k.
  - DP with zeta-transformed gains: exactly k² + 2k + 2 + (k² + 2k − 2)·2^(k−1) (k ≥ 2). Fitted on k = 6..14,
    against the rivals k·2^k, k³·2^k, k! and 3^k.

  The shape diagnostic runs on the subset DP's counts for k = 3..18 and on the zeta variant's for k = 2..19. The
  enumeration count is factorial and outside the diagnostic's growth family.

**Caveats.** O(k!·k·m) is the enumeration's worst case. An item that every rule matches costs one test per order. In
the DP, additions and comparisons between two plain integers are not counted, nor is subset bookkeeping on plain
integers (entry.json and PROOFS.md section 10 give the details). The DP with zeta-transformed gains builds its tables
from the 0 of the costs' number type, so that, on every instance with at least one item, every addition of its
transform is counted (PROOFS.md section 11.5).
Above k = 7 the V1 oracle is exact only when the lower bound is attained or the branch and bound finishes within its
budget. The entry makes no claim about the fastest known algorithm for this problem.

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves the correctness of both
algorithms, the bounds on every input, the reduction, the linear-ordering equivalence and the oracle facts;
[tests/test_proofs_first_match.py](../../tests/test_proofs_first_match.py) checks them on stated ranges. Section 11
proves every claim about the third algorithm, checked by
[tests/test_proofs_first_match_zeta.py](../../tests/test_proofs_first_match_zeta.py) and the experiment above.

**Sources.** Yee, Dahan, Hauser & Orlin, Marketing Science 2007 (the subset DP: Algorithm 2, Propositions 2–3) ·
Schmitt & Martignon, JMLR 2006 (Theorem 5: the feedback-arc-set reduction) · Chakravarthy, Joshi, Ramakrishnan,
Godbole & Balakrishnan, IJCNLP 2008 (MaxDL) · Karp 1972 · Grötschel, Jünger & Reinelt 1984 · Held & Karp 1962 ·
Bodlaender, Fomin, Koster, Kratsch & Thilikos 2012 · Angelino, Larus-Stone, Alabi, Seltzer & Rudin, JMLR 2018
(arXiv 1704.01701) · Koivisto & Sood, JMLR 2004 (the zeta-transform technique: sections 4 and 5) · Yates 1937 ·
Kennes & Smets 1991.
