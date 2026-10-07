# Bernstein–Vazirani: n classical queries vs 1 quantum query

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** f(x) = s·x mod 2 for a hidden n-bit string s. Find s.

| Algorithm | Model | Queries | Implementation |
|---|---|---|---|
| Query the unit vectors | classical | n (optimal, also randomized with success > 1/2) | [classical.py](implementations/classical.py) |
| Bernstein–Vazirani | quantum | **1** | [quantum.py](implementations/quantum.py) |

**Proven gap.** For a uniformly random s, the answers to q classical queries leave s uniform on an affine
subspace of dimension at least n − q. So a classical algorithm, randomized or not, finds s with probability at
most 2^(q−n), and success above 1/2 needs all n queries. One quantum query (Hadamard, phase oracle, Hadamard)
yields s exactly (in exact arithmetic; the floating-point simulation agrees up to rounding, about 10⁻¹⁵).

**How it is verified.** The quantum algorithm runs on an exact state-vector simulator ([lib/qsim.py](../../lib/qsim.py)).
Both algorithms query the same counting oracle. V2 fits the *query counts*: n for classical, constant 1 for quantum.
Simulation time grows exponentially, as simulating any quantum computer does. That cost is not the claim.

**Caveat.** This is a separation relative to an oracle, and only a linear one. It does not prove BQP ≠ BPP.
See [simon-classical-vs-quantum](../simon-classical-vs-quantum) for an exponential separation.

**Source.** Bernstein & Vazirani, *Quantum complexity theory*, SIAM J. Comput. 1997.

**Proofs.** [PROOFS.md](PROOFS.md) proves every claim of this entry: the exact counts, the correctness of both
algorithms and the classical lower bound. It names the deterministic checks of each
([tests/test_proofs_query.py](../../tests/test_proofs_query.py) and the count-check scripts).

**Background (cited, not proved here).** A recursive version of the problem gives a superpolynomial quantum–classical
query separation (Bernstein & Vazirani 1997).
