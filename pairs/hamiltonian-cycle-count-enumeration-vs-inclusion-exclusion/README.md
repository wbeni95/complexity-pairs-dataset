# Counting Hamiltonian cycles: enumeration vs inclusion–exclusion (and the Held–Karp counting DP)

**Type:** T6 (open: the decision problem is NP-complete; cited background), secondary T8 (super-poly → faster super-poly) ·
**Verification:** V2 (exact operation counts, with rivals)

**Problem.** Input: a digraph on n vertices as an n × n 0/1 adjacency matrix (A[u][v] = 1 iff u → v is an arc;
the diagonal is ignored). Output: the number of directed Hamiltonian cycles, each cycle counted once, not once per
start vertex. Conventions: n ≤ 1 gives 0, and n = 2 gives A[0][1]·A[1][0]. For an undirected graph (a symmetric
matrix) with n ≥ 3 the answer is twice the number of undirected Hamiltonian cycles.

| Algorithm | Time (n vertices) | Space | Implementation |
|---|---|---|---|
| Permutation enumeration (fix vertex 0, try all (n−1)! orders) | Θ(n!) arc tests; exactly n! on the complete digraph | Θ(n), given the documented cost of `itertools.permutations` | [enumeration.py](implementations/enumeration.py) |
| Inclusion–exclusion over vertex subsets, closed walks counted by a walk-length DP | Θ(n³·2ⁿ); exactly n(n−1)(n+2)·2ⁿ⁻² + 2ⁿ⁻¹ − 1 operations on every input | Θ(n) numbers | [inclusion_exclusion.py](implementations/inclusion_exclusion.py) |
| Held–Karp / Bellman DP over (subset, end vertex), with (+, ·) in place of (min, +) | Θ(n²·2ⁿ); exactly (n−1)(n−2)·2ⁿ⁻² + 2(n−1) operations on every input | Θ(n·2ⁿ) numbers | [held_karp_counting.py](implementations/held_karp_counting.py) |

**Why it is here.** Every directed Hamiltonian cycle is a closed walk of length n from vertex 0 whose first n
vertices are all different. Count all closed walks that stay inside a vertex set T, for every T that contains 0,
and combine them with signs (−1)^(n−|T|). Walks that miss a vertex cancel out, and only the Hamiltonian cycles
are left. Each walk count is a short dynamic programme, so the n! orders become 2ⁿ⁻¹ subsets times a polynomial,
in polynomial memory. The Held–Karp counting DP is faster by a factor Θ(n), but it stores a table of Θ(n·2ⁿ)
numbers: a time/memory trade-off between the two exponential algorithms. All three stay exponential. Deciding
whether a Hamiltonian cycle exists is NP-complete (Karp 1972; cited background), and a graph is Hamiltonian iff the
count is positive, so a polynomial-time counting algorithm would imply P = NP.

**Verification.**
- *V1:* the validator runs n = 0..12 and 14, 8 instances per size (112 instances, 296 implementation runs, 104
  instances on which at least two implementations are compared). The instances are random digraphs and undirected
  graphs (densities 0.3–0.9), complete digraphs with and without one arc, directed and undirected cycles,
  complete bipartite graphs (balanced and unbalanced), digraphs with a vertex that has no out-arcs or no in-arcs,
  planted Hamiltonian cycles with sparse extra arcs, and the Petersen graph. All are randomly relabelled, and
  about 30% carry random diagonal bits. Enumeration runs up to n = 9 and inclusion–exclusion up to n = 12; the
  Held–Karp count runs on every size.
- *Oracle:* `check` is independent of the implementations. It uses closed forms that hold for every n:
  - complete digraph (n−1)!, and (n−1)! − (n−2)! with one arc removed;
  - not strongly connected: 0;
  - a single directed n-cycle: 1; an undirected n-cycle: 2;
  - bipartite with unequal sides: 0; K_{m,m}: m!(m−1)!.

  Otherwise it runs a depth-first backtracking count, which always finishes for n ≤ 10 and is capped at 200 000
  search nodes above. It judged 109 of the 112 validator instances exactly. The other 3 (n = 14) were judged only
  by necessary conditions: the count is at most the product of the out-degrees (and of the in-degrees), and it is
  even for undirected graphs.
- *Experiment* ([script](../../experiments/2026-10-06f_entries_hamiltonian.py)):
  - 400 more instances (n = 3..12, 388 judged exactly): 0 failures;
  - every closed form against the exhaustive depth-first count on 39 graphs: 0 mismatches. The Petersen graph
    gives 0 in the three methods that run at n = 10 (inclusion–exclusion, Held–Karp and the oracle's
    depth-first count; the enumeration runs only up to n = 9);
  - **oracle control:** 3535 deliberately wrong outputs on 410 instances (off by one, doubled, halved = the
    undirected count, times n = counted once per start vertex, (n−1)!, negative, float, bool, None). 3471 were
    rejected, 64 left undecided (all at n = 11..14, where no exact rule applied), and **0 accepted**. Of the
    correct outputs, 398 were accepted, 12 left undecided and 0 rejected.
- *V2:* the scaling instance is the complete digraph Kₙ (where the enumeration can never stop early), with
  entries of a counting integer type. It counts every truth test, comparison and +, −, · on entry-derived values.
  The implementations are unchanged. The counts equal the hand-derived closed forms for every n checked:
  enumeration n = 2..10, inclusion–exclusion n = 2..13, Held–Karp n = 2..16. On random graphs both dynamic
  programmes give exactly the same counts as on Kₙ, because they never branch on an entry.

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| enumeration vs n!, n = 5..10 | 1.000 | (n−1)!: 1.071, n·n!: 0.938, n²·2ⁿ: 2.130 |
| inclusion–exclusion vs n(n−1)(n+2)·2ⁿ⁻² + 2ⁿ⁻¹ − 1, n = 6..13 | 1.000 | n²·2ⁿ: 1.112, n⁴·2ⁿ: 0.897, 3ⁿ: 0.923 |
| Held–Karp vs (n−1)(n−2)·2ⁿ⁻² + 2(n−1), n = 8..16 | 1.000 | n·2ⁿ: 1.144, n³·2ⁿ: 0.938, 3ⁿ: 0.811 |

The log-factor diagnostic is resolved in all three fits. Leading terms alone give α = 0.993 for n³·2ⁿ
(inclusion–exclusion) and 1.031 for n²·2ⁿ (Held–Karp, outside the band), so the exact forms are used as cost
expressions (RL-062).

**Caveats.**
- Arithmetic is counted at unit cost. Answers are at most (n−1)!, and walk counts at most (n−1)ⁿ, so all numbers
  have O(n log n) bits.
- Θ(n!) is the enumeration's worst case. It stops at the first missing arc, so it makes fewer arc tests on sparse
  graphs, but it always generates all (n−1)! orders.
- Loop control and subset bookkeeping on plain integers are not counted. In both dynamic programmes they are of
  the same order as the counted operations.
- Above n = 10, `check` is exact only for the recognised families, or when the depth-first count finishes. There
  the agreement of inclusion–exclusion with Held–Karp (n = 10..12) carries the evidence.
- The entry makes no claim about the fastest known algorithms for this problem.

**Proofs.** [PROOFS.md](PROOFS.md) proves the exact operation counts of this entry for all sizes of their domains,
from the code, and names the scripts and sizes that check each count. It also proves the correctness of the three
algorithms (and what the DPs compute with integer weights), the undirected convention, the space and integer-size
bounds, and the closed forms and bounds the oracle uses;
[tests/test_proofs_hamiltonian.py](../../tests/test_proofs_hamiltonian.py) checks them on stated ranges.

**Sources.** Kohn, Gottlieb & Kohn, ACM '77. Karp, Oper. Res. Lett. 1982. Bax, IPL 1993. Held & Karp, J. SIAM
1962. Bellman, J. ACM 1962. Karp 1972 (NP-completeness of Hamiltonian cycle).
