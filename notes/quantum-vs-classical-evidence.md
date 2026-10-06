# Research note: the evidence on quantum vs classical computational power

The project's motivating hypothesis is that **quantum computers can efficiently solve problems that
classical computers cannot**, i.e. BQP ≠ BPP. This note sorts the evidence by how strong it is and points
to the dataset entries that record each kind. It is a map, not a proof.

## Why a proof is out of reach

BPP ⊆ BQP ⊆ PSPACE. If BQP ≠ BPP, then BPP ≠ PSPACE, and since P ⊆ BPP, also **P ≠ PSPACE**. That separation
is itself a famous open problem. Any unconditional proof of quantum advantage for explicit problems would
therefore also settle a major question of classical complexity. No dataset can do that. What a dataset can do is
make the evidence explicit, checkable and queryable.

## Tier 1: proven, relative to an oracle (black-box models)

In the query model, separations are **theorems**:

| Separation | Classical | Quantum | Entry |
|---|---|---|---|
| Bernstein–Vazirani | n queries | 1 query | `pairs/bernstein-vazirani-classical-vs-quantum` (T9, V2) |
| Unstructured search (Grover) | Θ(N) | Θ(√N), and no better (BBBV 1997) | `pairs/grover-search-classical-vs-quantum` (T9, V2) |
| Simon's problem | Ω(2^(n/2)) | O(n) | `pairs/simon-classical-vs-quantum` (T9, V2) |
| Discrete log, generic groups | Ω(√p) (Shoup 1997) | poly(log p) (Shor) | `staging/discrete-logarithm` (T6 + T9) |
| Forrelation | Ω̃(√N) | 1 query (Aaronson–Ambainis 2015) | not yet ingested |
| BQP ⊄ PH relative to an oracle | — | — | Raz & Tal 2019/2022 |

These results show that *black-box* quantum speedups are real, sometimes exponential. Grover's lower bound also
shows their limit: for unstructured search the speedup is only quadratic, so quantum computers are not
expected to solve NP-complete problems by brute force.

## Tier 2: conjectured, for explicit problems

| Problem | Best classical | Quantum | Entry |
|---|---|---|---|
| Integer factoring | sub-exponential L[1/3] (heuristic GNFS) | polynomial (Shor) | `staging/integer-factoring` |
| Discrete log in GF(p)* and on elliptic curves | L[1/3] / O(√p) | polynomial (Shor) | `staging/discrete-logarithm` |

No classical polynomial algorithm is known, and none is ruled out. Factoring is in NP ∩ coNP and not believed
to be NP-complete. A classical polynomial algorithm would contradict no theorem; it would "only" break widely
deployed cryptography.

## Tier 3: hardness of classical *simulation* (sampling)

If classical computers could efficiently sample from certain quantum distributions, the polynomial hierarchy
would collapse. This holds for IQP circuits (Bremner–Jozsa–Shepherd 2011) and for BosonSampling (Aaronson–Arkhipov
2013), the latter built on the #P-hardness of the permanent (see `pairs/permanent-naive-vs-ryser`). Experiments such as
Google's Sycamore (2019) and USTC's Jiuzhang (2020) target this regime.

These experiments are **fixed-size instances**, not problem families, so they are outside the dataset's pair
definition (START_HERE section 1). Classical simulation has also caught up with some of them: for example, a
tensor-network method reproduced the Sycamore sampling task (Pan & Zhang 2022). The quantitative claims remain contested.

## Counter-evidence: dequantization

Several claimed exponential quantum speedups for machine-learning and linear-algebra tasks disappear once the
classical algorithm gets comparable input access (length-squared sampling). Recommendation systems are the
canonical case (Tang 2019; framework in Chia et al. 2022): `staging/recommendation-systems-dequantization` (T5).
Each such case shows the speedup came from the input model, not from quantum mechanics.

## How the dataset tracks this

- Every algorithm has `model` ∈ {classical-deterministic, classical-randomized, quantum}.
- `lower_bounds[]` records proven or conditional lower bounds together with their setting (query model, generic group,
  SETH, …), so "proven" and "believed" stay distinguishable.
- T9 is proven in a query model, T5 is dequantized, and T6 with a quantum algorithm is a conjectured
  advantage. `index.json` counts each.

A fair one-line summary of the current evidence is that quantum advantage is proven in black-box models,
strongly believed for factoring and discrete log, contested for sampling experiments, and has evaporated for
several machine-learning tasks.

## Sources

- Simon, D. R. (1997). On the power of quantum computation. SIAM J. Comput. 26(5). doi:10.1137/S0097539796298637
- Bernstein, E.; Vazirani, U. (1997). Quantum complexity theory. SIAM J. Comput. 26(5). doi:10.1137/S0097539796300921
- Bennett, C. H.; Bernstein, E.; Brassard, G.; Vazirani, U. (1997). Strengths and weaknesses of quantum computing. SIAM J. Comput. 26(5). doi:10.1137/S0097539796300933
- Shor, P. W. (1997). Polynomial-time algorithms for prime factorization and discrete logarithms on a quantum computer. SIAM J. Comput. 26(5). doi:10.1137/S0097539795293172
- Shoup, V. (1997). Lower bounds for discrete logarithms and related problems. EUROCRYPT '97. doi:10.1007/3-540-69053-0_18
- Aaronson, S.; Ambainis, A. (2015). Forrelation: a problem that optimally separates quantum from classical computing. STOC 2015. doi:10.1145/2746539.2746547
- Raz, R.; Tal, A. (2019). Oracle separation of BQP and PH. STOC 2019. doi:10.1145/3313276.3316315 (journal version J. ACM 2022, doi:10.1145/3530258)
- Bremner, M. J.; Jozsa, R.; Shepherd, D. J. (2011). Classical simulation of commuting quantum computations implies collapse of the polynomial hierarchy. Proc. R. Soc. A. doi:10.1098/rspa.2010.0301
- Aaronson, S.; Arkhipov, A. (2013). The computational complexity of linear optics. Theory of Computing 9. doi:10.4086/toc.2013.v009a004
- Arute, F. et al. (2019). Quantum supremacy using a programmable superconducting processor. Nature 574. doi:10.1038/s41586-019-1666-5
- Zhong, H.-S. et al. (2020). Quantum computational advantage using photons. Science 370. doi:10.1126/science.abe8770
- Pan, F.; Zhang, P. (2022). Solving the sampling problem of the Sycamore quantum circuits. Phys. Rev. Lett. 129. doi:10.1103/PhysRevLett.129.090502
- Tang, E. (2019). A quantum-inspired classical algorithm for recommendation systems. STOC 2019. doi:10.1145/3313276.3316310
