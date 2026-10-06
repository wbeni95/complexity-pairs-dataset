<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Element distinctness: Theta(N) classical queries vs Theta(N^(2/3)) quantum queries (Ambainis quantum walk)

**Type:** T9 (proven quantum advantage (query model)) · **Verification:** V0

**Problem.** Given oracle access to x_1, ..., x_N (values from a set of size M >= N), decide whether all N values are distinct, and if not, find i != j with x_i = x_j.

**Input.** N = number of items. Size: Query model: cost is the number of oracle calls (each returns one x_i).

| Algorithm | Model | Time | Space |
|---|---|---|---|
| classical: read everything, sort, scan | classical-deterministic | N queries; O(N log N) comparisons | O(N) values |
| Ambainis quantum walk algorithm | quantum | O(N^(2/3)) queries, bounded error (running time is also analysed in the paper; not recorded here) | O(N^(2/3)) values held in quantum registers |

**Relationship.** Proven POLYNOMIAL separation in the query model, tight on both sides: Theta(N) classical queries (even randomized) vs Theta(N^(2/3)) quantum queries. Element distinctness is harder than the collision problem quantumly (N^(2/3) vs N^(1/3)) because it has no 2-to-1 promise: there may be a single colliding pair. The quantum-walk technique that achieves it became a general tool (the abstract notes the generalisation to finding k equal items with O(N^(k/(k+1))) queries).

**Caveats.** A separation relative to an oracle, and only polynomial; it does not imply BQP != BPP. The classical lower bound counts queries; in the comparison model, classical TIME is Theta(N log N). The quantum algorithm has bounded error. The quantum lower bound of Aaronson & Shi was first proven for large ranges; the small-range case (M close to N) is due to Ambainis 2005.

**Notes.** Pairs naturally with pairs/collision-problem-classical-vs-quantum: the same lower-bound technique (polynomial method) gives N^(1/3) for collision and N^(2/3) for element distinctness. The classical TIME side of the same problem (all pairs, Theta(N^2), vs sorting, O(N log N)) is recorded separately in pairs/element-distinctness-pairs-vs-sorting (added in parallel on 2026-10-06); this entry concerns query complexity.

**Verification.** Cited from the literature. DOIs, titles, years, volumes, issues and pages checked against Crossref (and theoryofcomputing.org for the 2005 paper); the query bounds checked against the arXiv abstracts of Ambainis (quant-ph/0311001) and Shi (quant-ph/0112086), and the Theory of Computing abstract of Ambainis 2005. Not implemented: a quantum-walk simulation on lib/qsim.py would need a register of N^(2/3) values and is left open (see research/2026-10-07_quantum_entries.md).

**Sources.**

- Ambainis, A. (2007). *Quantum Walk Algorithm for Element Distinctness*. SIAM Journal on Computing 37(1), 210-239. [doi:10.1137/S0097539705447311](https://doi.org/10.1137/S0097539705447311)
- Aaronson, S.; Shi, Y. (2004). *Quantum lower bounds for the collision and the element distinctness problems*. Journal of the ACM 51(4), 595-605. [doi:10.1145/1008731.1008735](https://doi.org/10.1145/1008731.1008735)
- Ambainis, A. (2005). *Polynomial Degree and Lower Bounds in Quantum Complexity: Collision and Element Distinctness with Small Range*. Theory of Computing 1, 37-46. [doi:10.4086/toc.2005.v001a003](https://doi.org/10.4086/toc.2005.v001a003)
