# Unstructured search: Θ(N) classical vs Θ(√N) quantum queries (Grover)

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** Among N = 2ⁿ positions exactly one is marked, and only an oracle can tell which. Find it.

| Algorithm | Model | Queries | Implementation |
|---|---|---|---|
| Random-order scan | classical | (N+1)/2 expected, Θ(N) (optimal up to a constant factor) | [classical.py](implementations/classical.py) |
| Grover's algorithm | quantum | (π/4)√N + O(1) expected, Θ(√N) (optimal up to a constant factor) | [grover.py](implementations/grover.py) |

**Bounds in both directions (proved here).** Classically, Ω(N) queries are necessary: an algorithm with q queries
finds a uniformly random marked position with probability at most (q + 1)/N. Quantumly, Ω(√N) are necessary: the
hybrid argument gives at least (pN − 1)/(4√N) queries for success probability p (credit: Bennett–Bernstein–Brassard–
Vazirani 1997), so Grover is optimal up to a constant factor. Generic quantum search therefore buys a
**square root, not an exponential**. This is a *limit* on quantum advantage for black-box search. Grover's success
probability sin²((2k+1)θ), sin θ = 1/√N (credit: Grover 1996), and his expected count (π/4)√N + O(1) are proved too.

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py)) with a shared
counting oracle. V2 fits the averaged query counts: 2ⁿ for classical, 2^(n/2) for Grover.

**Caveat.** This is a separation relative to an oracle. It does not prove BQP ≠ BPP.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact count per attempt, both
algorithms' correctness and expected counts, Grover's success probability, and the classical and quantum lower
bounds. It names the deterministic checks of each ([tests/test_proofs_query.py](../../tests/test_proofs_query.py)
and the count-check script).

**Sources.** Grover, STOC 1996. Bennett, Bernstein, Brassard & Vazirani, SIAM J. Comput. 1997.
