# XOR-SAT and #XOR-SAT: brute force vs Gaussian elimination over GF(2)

**Type:** T2 (naive-exp → poly) · **Verification:** V2 (exact operation counts, with rivals)

**Problem.** Given m XOR clauses a_i1 x₁ ⊕ … ⊕ a_in xₙ = bᵢ as a dense 0/1 matrix [A | b], output the number of satisfying
assignments and, if there is one, a satisfying assignment. The decision problem (XOR-SAT) and the counting problem
(#XOR-SAT) are answered together. The count is always 0 or 2^(n − rank A).

| Algorithm | Time | Implementation |
|---|---|---|
| Brute force over all 2ⁿ assignments (no early stop: it counts) | O(2ⁿ·(m + 1)(n + 1)); Θ(2ⁿ·n) on systems with m ≥ 1 independent rows | [brute_force.py](implementations/brute_force.py) |
| Gaussian elimination over GF(2) | O(m·n·min(m, n) + m + n); Θ(n³) worst case for n × n | [gaussian_elimination.py](implementations/gaussian_elimination.py) |

**Why it is here.** XOR clauses are linear equations over the two-element field, so the solutions form an affine
subspace. One elimination yields consistency, the rank r, the count 2^(n−r) and a solution. As cited background,
this is the affine class of Schaefer's (1978) dichotomy for Boolean constraints.

**Boundary** (cited background; not claims of this entry). By the Creignou–Hermann (1996) dichotomy, counting the
solutions of Boolean constraints is polynomial for affine constraints and #P-complete for every other constraint
language, which includes 2-CNF and Horn formulas; counting the satisfying assignments of CNF formulas is #P-complete
(Valiant 1979).
So #XOR-SAT is easy while #SAT, #2-SAT and #Horn-SAT are #P-hard: unless every #P function is computable in polynomial
time, XOR is the only one of these counting problems with a polynomial algorithm. The decision versions of 2-SAT and
Horn-SAT are easy:
see [two-sat-brute-force-vs-scc](../two-sat-brute-force-vs-scc/) and
[horn-sat-brute-force-vs-unit-propagation](../horn-sat-brute-force-vs-unit-propagation/).

**Verification.**
- *V1:* both implementations agree on the count on 60 systems (n = 0..14 for brute force, up to 120 for elimination):
  random dense and sparse 3-XOR systems, planted consistent ones, inconsistent ones (a row equal to a sum of rows with b
  flipped), rank-deficient ones and the V2 family permuted. The independent `check` is certificate-based. It builds an
  XOR basis of the packed rows keyed by the *highest* coefficient and tracks which input rows each basis vector combines.
  "No solution" is accepted only with a re-verified combination equal to 0 = 1. A count is accepted only if it equals
  2^(n−r), where r independent combinations of input rows bound the rank from below and n − r null-space vectors are
  verified against every row, and only with a witness that satisfies every row. For n ≤ 10 it also counts exhaustively.
- *Oracle control* ([experiment](../../experiments/2026-10-06f_entries_xor_sat.py)): all 1020 correct outputs accepted.
  All 4348 wrong ones were rejected: count ± a factor 2, count + 1, "no solution" for consistent systems, a claimed
  solution for inconsistent ones, a violating or missing witness. That holds both where the exhaustive count is active
  (n ≤ 10: 2868) and where only the certificates decide (n = 11..40: 1480).
- *V2:* a counting bit type counts every AND, XOR and truth test on input-derived bits; the implementations are
  unchanged. The family Xₙ (n ≥ 1; rows: all ones, then x₁ + x_{k+1} + … + xₙ for k = 2..n) has full rank. That
  makes brute force cost exactly (2n + 1)(2ⁿ⁺¹ − 2), since row i is reached by 2ⁿ⁻ⁱ assignments. It also gives forward elimination
  its maximal number of row operations, exactly n(n² + 6n − 4)/3 operations. Both forms are derived in entry.json and
  checked for n = 1..16 and n = 1..200.

| Fit (tolerance 0.02) | α | Rivals (must not fit) |
|---|---|---|
| brute force vs (2n + 1)(2ⁿ⁺¹ − 2), n = 8..16 | 1.000 | 2ⁿ: 1.120, n²·2ⁿ: 0.897 |
| elimination vs n(n² + 6n − 4), n = 16..128 | 1.000 | n²: 1.439, n⁴: 0.720 |

**Caveats.** Brute force abandons an assignment at its first violated row. With m ≥ 1 independent rows that happens
after fewer than 2 rows on average, so its cost is Θ(2ⁿ·n). The Θ(2ⁿ·m·n) worst case is attained with dependent rows (m
copies of one equation). The fitted costs are exact closed forms; the bare n³ gives α = 0.959. Packed rows (machine
words of w bits) turn the XOR of k entries into ⌈k/w⌉ word operations, a constant factor that is not counted.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact operation counts for all sizes of
their domains, the correctness of both algorithms, the count 0 or 2^(n − rank A), the brute-force cost on systems with
independent rows and its worst case, the elimination bounds and the caveats. It names the checks: the count-check
scripts and [tests/test_proofs_xor_sat.py](../../tests/test_proofs_xor_sat.py).

**Sources.** Schaefer, STOC 1978. Creignou & Hermann, Information and Computation 1996. Valiant, SIAM J. Comput. 1979.
