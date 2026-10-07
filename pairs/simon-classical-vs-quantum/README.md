# Simon's problem: Θ(2^(n/2)) classical vs O(n) quantum queries

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** f is 2-to-1 with f(x) = f(x ⊕ s) for a hidden nonzero s. Find s.

| Algorithm | Model | Queries | Implementation |
|---|---|---|---|
| Collision search | classical | Θ(2^(n/2)) expected (birthday law; optimal up to a constant factor) | [classical.py](implementations/classical.py) |
| Simon's algorithm | quantum | expected fewer than n + 0.61 rounds (n − 1 + O(1)), O(n) | [quantum.py](implementations/quantum.py) |

**The exponential gap (proved here).** Any classical algorithm needs Ω(2^(n/2)) queries: after collision-free
queries the hidden s is uniform on the nonzero values not yet excluded, so q queries succeed with probability at most
(C + 1)/(2ⁿ − 1 − C), C = q(q − 1)/2 (credit: Simon 1997).
Each quantum round yields a uniformly random y with y·s = 0, and fewer than n + 0.61 rounds in expectation plus
Gaussian elimination over GF(2) recover s.

**Background (cited, not proved here).** Simon's algorithm inspired Shor's factoring algorithm (Shor 1997, introduction).

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py)). The output
register is measured right after the query, which is valid because it is never used again. V1 checks every
answer against the promise structure. V2 fits the averaged query counts: 2^(n/2) for classical, n for quantum.

**Caveat.** This is a separation relative to an oracle. It does not by itself imply BQP ≠ BPP for explicit
problems.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the count per round, the correctness and
expected queries of both algorithms, the distribution of one quantum round, the post-processing, and the classical
lower bound. It names the deterministic checks of each ([tests/test_proofs_query.py](../../tests/test_proofs_query.py),
the experiment and the count-check scripts).

**Sources.** Simon, *On the power of quantum computation*, SIAM J. Comput. 1997. Shor, SIAM J. Comput. 1997.
