# Minimum finding: N classical queries vs O(√N) quantum queries (Dürr–Høyer)

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** A table T[0..N−1] (N = 2ⁿ) of distinct values is accessible only through probes. Find the index of the minimum.

| Algorithm | Model | Queries | Error | Implementation |
|---|---|---|---|---|
| Scan | classical, deterministic | exactly N | none | [classical.py](implementations/classical.py) |
| Dürr–Høyer | quantum | O(√N) expected; measured ≈ 2·(22.5√N + 1.4 lg²N) | < 1/2, proved (0 failures in 14 000 simulated runs) | [durr_hoyer.py](implementations/durr_hoyer.py) |

**Gap (quadratic), proved here.** Minimum finding contains unstructured search. Set T[x] = 0 for the marked x
and T[x] = x + 1 otherwise; the values are distinct and one probe of T costs one search query. Classical algorithms therefore need
Ω(N) probes even with bounded error, and quantum algorithms need Ω(√N) (the hybrid argument; credit:
Bennett–Bernstein–Brassard–Vazirani 1997). Dürr–Høyer attains O(√N) expected queries with success probability above
1/2, proved with the implementation's own constants, so the separation is Θ(N) vs Θ(√N): a square root, not an
exponential. All four bounds are proved in [PROOFS.md](PROOFS.md).

**How Dürr–Høyer works.** It keeps a threshold y and repeatedly uses Grover search for an *unknown* number of marked
items, the BBHT exponential search, to find some j with T[j] < T[y], which then becomes the new threshold. It stops
at the time-out 22.5√N + 1.4 lg²N, measured in the paper's time units.

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py), search subroutines in
[lib/qsearch.py](../../lib/qsearch.py)). Each Grover iteration is charged **two** queries, because T[j] has to be computed
and then uncomputed. V2 fits the query counts: the scan gives N exactly, and Dürr–Høyer is fitted against 2^(n/2)
over n = 4..12. The [experiment](../../experiments/2026-10-07_minimum_finding.py) checks the simulation against theory.
The time and queries until the threshold reaches the minimum match their exact expectations (|z| ≤ 1.01). The
paper's bound m0 is 3.7–9.3× larger than the exact expectation for n = 2..10.

**Caveats, with numbers.**
- *Bounded error.* V1 agreement is probabilistic.
- *Constants.* With the published time-out the simulated mean quantum count is **above** N at every measured
  N ≤ 2048 (N = 4, 16, 64, 256, 1024, 2048). It is above N at N = 2048 (ratio 1.12) and below N at N = 4096
  (ratio 0.78).
- *Fit depends on range.* Over n = 2..10 the fitted α is 0.800, close to the tolerance edge, because lower-order
  terms dominate at tiny N.
- *Oracle model.* This is a separation relative to an oracle, and it does not imply BQP ≠ BPP.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact counts, the classical and quantum
lower bounds, the analysis of the exponential search (fewer than 9·m₀(t) expected iterations), and Dürr–Høyer's
Lemma 1, Lemma 2 and Theorem 1 with the implementation's constants (for n ≥ 1). It names the deterministic checks of
each ([tests/test_proofs_query.py](../../tests/test_proofs_query.py), the experiment and the count-check scripts).

**Background (cited, not proved here).** Dürr & Høyer remark that the algorithm also works for non-distinct values.

**Sources.** Dürr & Høyer, *A quantum algorithm for finding the minimum*, arXiv:quant-ph/9607014 (1996).
Boyer, Brassard, Høyer & Tapp, *Tight bounds on quantum searching*, Fortschr. Phys. 46 (1998).
Bennett, Bernstein, Brassard & Vazirani, SIAM J. Comput. 26 (1997).
