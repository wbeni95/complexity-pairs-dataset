# Simon's problem: Θ(2^(n/2)) classical vs O(n) quantum queries

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** f is 2-to-1 with f(x) = f(x ⊕ s) for a hidden nonzero s. Find s.

| Algorithm | Model | Queries | Implementation |
|---|---|---|---|
| Collision search | classical | Θ(2^(n/2)) (birthday bound; optimal by the cited lower bound of Simon 1997) | [classical.py](implementations/classical.py) |
| Simon's algorithm | quantum | n − 1 + O(1), O(n) | [quantum.py](implementations/quantum.py) |

**The exponential gap.** Simon (1997) showed that any classical algorithm needs Ω(2^(n/2)) queries (cited, not
proved here).
Each quantum round yields a random y with y·s = 0, and about n rounds plus Gaussian elimination over GF(2)
recover s. Shor's factoring algorithm grew directly out of this idea.

**How it is verified.** Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py)). The output
register is measured right after the query, which is valid because it is never used again. V1 checks every
answer against the promise structure. V2 fits the averaged query counts: 2^(n/2) for classical, n for quantum.

**Caveat.** This is a separation relative to an oracle. Turning it into an unconditional statement about
explicit problems (BQP ≠ BPP) would require proving P ≠ PSPACE.

**Sources.** Simon, *On the power of quantum computation*, SIAM J. Comput. 1997. Shor, SIAM J. Comput. 1997.
