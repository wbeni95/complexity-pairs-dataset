# Unstructured search: Θ(N) classical vs Θ(√N) quantum queries (Grover)

**Type:** T9 (proven quantum advantage, query model) · **Verification:** V2 (query counts)

**Problem.** Among N = 2ⁿ positions exactly one is marked, and only an oracle can tell which. Find it.

| Algorithm | Model | Queries | Implementation |
|---|---|---|---|
| Random-order scan | classical | (N+1)/2 expected, Θ(N) | [classical.py](implementations/classical.py) |
| Grover's algorithm | quantum | (π/4)√N + O(1), Θ(√N) | [grover.py](implementations/grover.py) |

**Proven in both directions.** Classically, Ω(N) queries are necessary. Quantumly, Ω(√N) are necessary
(Bennett–Bernstein–Brassard–Vazirani 1997), so Grover is optimal. Generic quantum search therefore buys a
**square root, not an exponential**. This is a proven *limit* on quantum advantage for black-box search.

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py)) with a shared
counting oracle. V2 fits the averaged query counts: 2ⁿ for classical, 2^(n/2) for Grover.

**Caveat.** This is a separation relative to an oracle. It does not prove BQP ≠ BPP.

**Sources.** Grover, STOC 1996. Bennett, Bernstein, Brassard & Vazirani, SIAM J. Comput. 1997.
