# Linear ordering problem: enumeration vs dynamic programming over subsets

**Type:** T6 (open: the problem is NP-hard; cited background), secondary T8 (super-poly → faster super-poly) ·
**Verification:** V2 (exact operation counts, with rivals)

**Problem.** Given an n × n integer matrix W, find the order of the n elements that maximises the sum of W[a][b]
over all pairs with a before b. The diagonal is ignored. Minimising the weight of the backward pairs is the same
problem. For the 0/1 matrix of a digraph it is the feedback arc set problem.

| Algorithm | Time | Space | Implementation |
|---|---|---|---|
| Enumeration of all n! orders | Θ(n!·n²), given the documented cost of `itertools.permutations`; exactly n!(n(n−1)/2 + 1) − 1 counted operations | Θ(n) | [enumeration.py](implementations/enumeration.py) |
| Dynamic programming over subsets | Θ(n²·2ⁿ); exactly 2^(n−2)(n+4)(n−1) + 1 counted operations | Θ(2ⁿ) | [subset_dp.py](implementations/subset_dp.py) |

**Why it works.** Suppose the set S of elements placed first is known. Then placing v next contributes W[v][u] for
every element u placed later, whatever the order inside S. So best[S ∪ {v}] = max over v of
best[S] + Σ_{u ∉ S∪{v}} W[v][u], the Held–Karp recurrence over (set placed so far, next element). Both algorithms
stay exponential. The linear ordering problem is NP-hard (Grötschel, Jünger & Reinelt 1984), and its 0/1 case,
feedback arc set, is NP-complete (Karp 1972); both are cited background.

**Verification.**
- *V1:* the validator runs n = 0..8, 10 and 12, 5 instances per size. The instances are random matrices (signed and
  non-negative), tournaments, hidden acyclic instances, zero matrices and large entries; the diagonal holds junk.
  The `check` oracle is independent of both implementations:
  - it recomputes the value from positions;
  - it compares the value with an upper bound (the larger direction of every pair);
  - otherwise it runs a branch and bound over prefixes. This is exact for n ≤ 8; above that it has a node budget,
    after which an improving single-element move proves non-optimality.
- *Experiment* ([2026-10-06i_linear_ordering.py](../../experiments/2026-10-06i_linear_ordering.py)):
  - 436 extra implementation runs, 0 failures;
  - an oracle control: 2460 deliberately wrong outputs rejected, 0 accepted, and 212 correct outputs accepted.
- *V2 (exact counts):* CountingInt entries count every comparison and +, −; the counts do not depend on the entries.

  | Algorithm | Fitted on | Rivals |
  |---|---|---|
  | Enumeration | n = 4..8 | n!·n, n!·n³, n²·2ⁿ |
  | DP | n = 6..14 | n·2ⁿ, n³·2ⁿ, 3ⁿ, n! |

  The shape diagnostic runs on the DP counts for n = 2..15.

**Caveats.** This DP recomputes each gain from scratch. Running row sums would give Θ(n·2ⁿ) time with Θ(n·2ⁿ)
memory (PROOFS.md section 7), which is not implemented here. Loop control and subset bookkeeping on plain integers
are not counted; they are of the same order as the counted operations (PROOFS.md section 8).

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves the equivalences in the problem
statement, the correctness of both algorithms, the space bounds, the running-row-sum variant and the oracle facts;
[tests/test_proofs_linear_ordering.py](../../tests/test_proofs_linear_ordering.py) checks them on stated ranges.

**Sources.** Grötschel, Jünger & Reinelt, Oper. Res. 1984 · Karp 1972 · Held & Karp 1962 · Bodlaender, Fomin,
Koster, Kratsch & Thilikos, Theory Comput. Syst. 2012.
