# Collision problem: Θ(N^½) classical vs Θ(N^⅓) quantum queries (Brassard–Høyer–Tapp)

**Type:** T9 (quantum separation, query model) · **Verification:** V2 (query counts)

**Problem.** f is 2-to-1 on N = 2ⁿ points: every value has exactly two preimages. Find two inputs with the same value.

| Algorithm | Model | Expected queries | Implementation |
|---|---|---|---|
| Birthday search (random order) | classical, randomized | Θ(√N), ≈ 1.2533·√N | [classical.py](implementations/classical.py) |
| BHT, known number of marked points | quantum (Las Vegas) | Θ(N^⅓); 2.56–2.57·N^⅓ for n = 15..30 (exact evaluation) | [bht.py](implementations/bht.py) `collision_bht` |
| BHT with BBHT exponential search | quantum (Las Vegas) | Θ(N^⅓); 3.84–3.90·N^⅓ for n = 18..30 (exact evaluation) | [bht.py](implementations/bht.py) `collision_bht_exponential` |

**Bounds on both sides.**
- *Classical, Ω(√N).* On a random 2-to-1 function, every next query completes a pair with probability exactly i/(N−i)
  after i collision-free queries, whatever the algorithm does. This is the birthday bound.
- *Quantum, Ω(N^⅓).* Cited, not proved here: Aaronson & Shi (2004). Their proof needs a codomain of size ≥ 3N/2;
  the harness's codomain has size 2N. Kutin (2005) and Ambainis (2005) removed that condition.
- *Upper bound.* BHT attains O(N^⅓) (Brassard, Høyer & Tapp, Theorem 1; cited, not proved here). The separation
  is polynomial, not exponential, and its tightness rests on the cited quantum lower bound.

**How BHT works.** It queries k = round(N^⅓) points classically. If none of them collide, exactly k other points are
their partners, and Grover search over the whole domain finds one in about (π/4)·√(N/k) iterations.

**Relation to Simon's problem (same promise, different structure).** Simon's functions are the 2-to-1 functions whose
pairs are {x, x ⊕ s}. On them, finding a collision and finding s are the same task. With that XOR structure, O(n) =
O(log N) quantum queries suffice, an **exponential** speedup ([simon-classical-vs-quantum](../simon-classical-vs-quantum)).
Without structure, the best possible is Θ(N^⅓) by the cited bounds, only a **polynomial** speedup. Classically, both
take Θ(√N).

**How it is verified.**
- *Simulation.* Exact state-vector simulation ([lib/qsim.py](../../lib/qsim.py), [lib/qsearch.py](../../lib/qsearch.py)).
  Each Grover iteration costs **2** queries, because f(x) has to be computed and then uncomputed.
- *V1.* Every output is checked against the instance.
- *V2.* Fits the mean query counts. The exact expectations predict α = 0.997, 1.027 and 1.154 for the three
  algorithms. The last value is pre-asymptotic: the exact slope over n = 15..30 is 1.009.
- *Theory vs simulation.* The [experiment](../../experiments/2026-10-07_collision_expected_queries.py) compares
  simulated means with exact expectations. It caught an implementation detail in a first version, which stopped
  querying K at the first internal collision; that version's counts fell systematically below the formula. It was
  fixed to follow BHT's step order.

**Caveats.** This is a separation relative to an oracle. It does not imply BQP ≠ BPP. BHT's algorithm also needs
N^⅓ classical values to be readable in superposition.

**Sources.** Brassard, Høyer & Tapp, LATIN '98 (arXiv:quant-ph/9705002). Boyer, Brassard, Høyer & Tapp, Fortschr. Phys. 1998.
Aaronson & Shi, J. ACM 2004. Kutin, Theory of Computing 2005. Ambainis, Theory of Computing 2005. Simon, SIAM J. Comput. 1997.
