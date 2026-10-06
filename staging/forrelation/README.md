<!-- generated from entry.json by tools/build_index.py; edit entry.json, not this file -->
# Forrelation: 1 quantum query vs Omega(sqrt(N)/log N) classical queries (optimal partial-function separation)

**Type:** T9 (proven quantum advantage (query model)) · **Verification:** V0

**Problem.** Given oracle access to two Boolean functions f, g: {0,1}^n -> {-1, 1}, N = 2^n, decide whether g is highly correlated with the Fourier (Hadamard) transform of f or nearly uncorrelated with it, under the promise that one of the two holds. The forrelation is Phi(f, g) = N^(-3/2) sum_{x,y} f(x) (-1)^(x.y) g(y); the paper fixes explicit constant thresholds for 'large' and 'small' (not reproduced here).

**Input.** n = number of input bits; N = 2^n. Size: Query model: cost is the number of queries to f or g (2N values in total).

| Algorithm | Model | Time | Space |
|---|---|---|---|
| classical: read both functions | classical-deterministic | 2N queries; O(N log N) arithmetic operations | O(N) |
| classical: generic simulation of a 1-query quantum algorithm | classical-randomized | O(sqrt N) queries (t = 1 in O(N^(1-1/(2t)))), bounded error | not recorded |
| quantum: one-query forrelation estimator | quantum | 1 query, bounded error; O(n) gates besides the oracle | O(n) qubits |

**Relationship.** Proven separation in the query model: 1 quantum query vs Omega~(sqrt N) randomized classical queries, with an O(sqrt N) classical upper bound. Aaronson & Ambainis also prove this is OPTIMAL for 1-query quantum algorithms: no partial Boolean function has constant quantum query complexity and linear randomized query complexity. In terms of n = log N the gap is exponential (1 vs about 2^(n/2)/n). Related: Raz & Tal (STOC 2019; J. ACM 2022) give a distribution on 2N bits that ONE quantum query distinguishes from uniform with advantage Omega(1/log N), while no quasi-polynomial-size constant-depth circuit achieves advantage better than polylog(N)/sqrt(N) (ECCC TR18-107 abstract); this yields an oracle relative to which BQP is not contained in PH.

**Caveats.** A separation relative to an oracle (and for a promise problem); it does not imply BQP != BPP. The quantum algorithm has bounded error, and the classical lower bound is for bounded-error randomized algorithms. The Raz-Tal result is also relative to an oracle. Aaronson (Nature Physics 2015) stresses that such speedups need the functions to be given as oracles (or loaded efficiently) and that the hardness proof concerns inputs that are random individually.

**Notes.** Strongest single data point in the dataset for 'black-box quantum advantage': the gap 1 vs ~sqrt N is proven and proven optimal. Aaronson & Ambainis conjecture that a natural generalisation (k-fold Forrelation) gives the optimal t vs ~N^(1-1/2t) separation for every t, and show that this generalisation is BQP-complete (abstract). Whether the Raz-Tal distribution should be described as a variant of Forrelation is not asserted here: their abstract does not say so, and the paper was not read for this entry.

**Verification.** Cited from the literature. DOIs, titles, years, volumes, issues and pages checked against Crossref; the query bounds and the optimality statement checked against the arXiv abstract of Aaronson & Ambainis (1411.5729); the Raz-Tal statement checked against their ECCC abstract (TR18-107). Not implemented: a lib/qsim.py implementation is feasible (one query, O(n) qubits) but needs a sampler for forrelated pairs (f, g), which is left open.

**Sources.**

- Aaronson, S.; Ambainis, A. (2015). *Forrelation: A Problem that Optimally Separates Quantum from Classical Computing*. STOC 2015, 307-316. [doi:10.1145/2746539.2746547](https://doi.org/10.1145/2746539.2746547) [arXiv:1411.5729](https://arxiv.org/abs/1411.5729)
- Raz, R.; Tal, A. (2019). *Oracle separation of BQP and PH*. STOC 2019, 13-23. [doi:10.1145/3313276.3316315](https://doi.org/10.1145/3313276.3316315)
- Raz, R.; Tal, A. (2022). *Oracle Separation of BQP and PH*. Journal of the ACM 69(4), 1-21. [doi:10.1145/3530258](https://doi.org/10.1145/3530258)
- Aaronson, S. (2015). *Read the fine print*. Nature Physics 11(4), 291-293. [doi:10.1038/nphys3272](https://doi.org/10.1038/nphys3272)
