# Methodology: how new "formulas" are found, predicted, recognised, and tested against quantum questions (2026-10-06d)

Author: delegated research agent (Claude), for the maintainer. Round prefix `2026-10-06d_`. Status: research report.
It adds no entry and changes nothing in `pairs/`, `staging/`, `synthetic/`, `tools/`, `schema/`, `lib/`, `search/`,
`RESEARCH_LOG.md`, `README.md` or `index.json`. New code lives in `methods/` and `tests/test_methods.py`; experiments in
`experiments/2026-10-06d_meth_*.py`.

## How to read the labels

| Label | Meaning |
|---|---|
| **[exp: name]** | Output of `experiments/2026-10-06d_meth_<name>.py` (deterministic; rerun reproduces the number). |
| **[DOI OK]** | DOI resolved via Crossref/DataCite and the registered title and year match ([exp: sources]). **Only title and year were checked, not the paper's content.** Where a specific statement from the paper is used, it is additionally marked *content recalled* unless the title itself states it. |
| **[arXiv OK]** | arXiv id exists with the cited title and year ([exp: sources]); same caveat. |
| **[book]** | Book, cited by title; not machine-checked unless a DOI is given. |
| **[recalled]** | From memory, not verified against a registry or the source. Treat as a hypothesis. |

Status words: **theorem** (proven, cited), **conjecture**, **observation** (my computation, finite range), **proposal** (my recommendation).

---

## Summary

1. **Science finds new "formulas" (algorithms with a cost) by pairing a proposer with an exact verifier.** Every
   successful automated method in the survey (superoptimisation, flip graphs and SAT search for matrix multiplication,
   AlphaTensor, AlphaDev, FunSearch, AlphaEvolve, PSLQ/LLL, holonomic guessing, the Ramanujan Machine) yields
   *finite* objects or *conjectures*. An asymptotic cost statement comes only from (i) an amplification mechanism
   (a small bilinear scheme applied recursively gives an exponent), (ii) a guessed recurrence plus a proof, or
   (iii) a human or machine proof. This matches START_HERE section 6.
2. **The cost's shape can be recovered exactly from the dataset's own exact counts.** For **12 of 12** count sequences of
   slow algorithms (Fibonacci, edit distance, matrix chain, optimal BST, 4 synthetic recurrences, LIS enumeration, regex
   backtracking, global min cut, zeta transform), an exact recurrence guess, an exact growth constant with its minimal
   polynomial, and the exact polynomial exponent all **match the entry's claimed cost** [exp: formula_recognition].
   The headline case: plain-recursion edit distance follows a guessed order-3 holonomic recurrence, λ = 3 + 2√2
   (minimal polynomial x² − 6x + 1) and θ = **−1/2 exactly**, which is the entry's Θ((3+2√2)ⁿ/√n). An independent
   "experimental mathematics" route (ratio method plus LLL from the counts alone) recovers the same minimal polynomial
   in 12 of 12 cases.
3. **Log factors: the V2 timing tolerance, not the noise, is what blocks them.** Re-analysing the recorded run
   `ledger/runs/20261006T105123Z.json`: **0 of 44** timing fits with a diagnostic could resolve a log factor *even
   with perfect, noise-free data* on the same n-grids at tolerance 0.25. The largest possible separation on any
   timing grid is **0.1015** [exp: log_identifiability]. This sharpens RL-048. Exact counts at n = 2ᵏ fix the problem
   completely: Berlekamp–Massey on the doubling sequence gives the exponent *and* the log power exactly (NTT: (x−2)²,
   so n log n; Karatsuba: x − 3, so n^log₂3; Strassen: x − 7; Yates: (x−2)², so N log N).
4. **Quantum: what is provable is query-model separation; the polynomial method makes it checkable by machine.** Exact
   approximate degrees with primal and dual certificates: adeg₁/₃(ORₙ) for 70 values of n ≤ 256 grows like
   **0.7246·√n** (log-log slope **0.4748** for n ≥ 16), the Ω(√N) behind Grover's optimality via Q₂ ≥ adeg/2;
   parity has adeg = n (n ≤ 16). On all 222 NPN classes of 4-bit functions, proven inequalities (Huang's
   deg ≤ s², s ≤ bs ≤ C ≤ D, bs ≤ 2deg²) hold, and the class counts 14 and 222 match the published values
   [exp: boolean_measures].
5. **Location of fast algorithms: a mechanical predictor exists for constraint problems.** Schaefer's theorem via
   polymorphisms classifies all 276 Boolean relations of arity ≤ 3 identically to the independent syntactic
   definitions (0 mismatches). The predicted polynomial algorithm agrees with brute force on **900 of 900** random
   instances (150 per class), and affine counting 2^(n−rank) matches on 150 of 150 [exp: csp_predictor].
6. **Recommendations, ranked** (section 6): (1) an exact "shape" diagnostic for exact-count V2 (doubling-sequence
   Berlekamp–Massey, recurrence guessing for exponential counts); (2) stop expecting log factors from timing at
   tolerance 0.25; (3) machine-checkable polynomial-method certificates for T9 entries; (4) CSP-predictor-driven
   candidates (Horn-SAT, XOR-SAT, #XOR-SAT); (5) exact Q_E by SDP in a separate venv; (6) LLM proposers only behind
   exact verifiers.

---

## 1. Area 1: discovering algorithms and formulas

The common pattern is: **a large, cheaply generated space of candidates; an exact (or exhaustive) verifier; a
guiding signal.** The verifier decides; the proposer (enumeration, stochastic search, RL, an LLM) only ranks.

| Method | What it can produce | What it cannot produce | Verification it needs | Use here |
|---|---|---|---|---|
| **Superoptimisation**: exhaustive search, Massalin 1987, doi:10.1145/36206.36194 [DOI OK]; stochastic search (STOKE), Schkufza, Sharma, Aiken 2013, doi:10.1145/2451116.2451150 [DOI OK] | The shortest or fastest loop-free instruction sequence for a fixed function on fixed-width inputs | Anything asymptotic: inputs are bounded, so the cost is O(1) | Exhaustive testing or an SMT equivalence check over all inputs of the fixed width | Constant-factor results only; out of scope as pairs (notes/constant-factor-alphadev.md) |
| **AlphaDev** (RL over assembly), Mankowitz et al. 2023, doi:10.1038/s41586-023-06004-9 [DOI OK] | Shorter sort3–sort5 routines, merged into libc++ (*content recalled*; already in the project's note) | Asymptotic gains | The 0-1 principle plus exhaustive input checks | Same as above |
| **Bilinear-scheme search for matrix multiplication**: AlphaTensor (RL), Fawzi et al. 2022, doi:10.1038/s41586-022-05172-4 [DOI OK]; flip graphs, Kauers & Moosbauer 2023, doi:10.1145/3597066.3597120 [DOI OK]; SAT and local search, Heule, Kauers, Seidl 2021, "New ways to multiply 3×3-matrices", doi:10.1016/j.jsc.2020.10.003 [DOI OK] | A rank-r scheme for a k×k format. Recursion turns it into an *asymptotic* exponent log_k r (Strassen's mechanism). **The only search family here whose finite outputs amplify into new asymptotic pairs.** | A better ω unless r < k^(current exponent); for 3×3 that means r ≤ 21 (research/2026-10-07_patterns.md §4) | Exact check of the Brent equations over the ring (the project's two verifiers) | Already running (`search/`); RL-054/070/071 |
| **LLM-guided program search**: FunSearch, Romera-Paredes et al. 2024, doi:10.1038/s41586-023-06924-6 [DOI OK]; AlphaEvolve, Novikov et al. 2025, arXiv:2506.13131 [arXiv OK] | Programs that *construct* objects (cap sets, packings, schemes) or heuristics, scored by an evaluator (*content recalled*) | Proofs of asymptotic cost; a heuristic that scores well on test instances is not an algorithm with a proven bound | An exact evaluator on every candidate, plus a separate proof for any asymptotic claim | A proposer for `search/`-style spaces; never a source of verified pairs by itself |
| **Program synthesis**: Gulwani, Polozov, Singh 2017, doi:10.1561/2500000010 [DOI OK]; syntax-guided synthesis, Alur et al. 2013, doi:10.1109/FMCAD.2013.6679385 [DOI OK] | Programs meeting a specification, from examples or a logical spec, in a fixed grammar | Programs much larger than the grammar's reach; cost guarantees unless the cost is in the spec | Specification check (SMT or exhaustive) | Small DSL searches with an exact verifier (START_HERE §5) |
| **Symbolic regression**: Schmidt & Lipson 2009, doi:10.1126/science.1165893; AI Feynman, Udrescu & Tegmark 2020, doi:10.1126/sciadv.aay2631; SINDy, Brunton, Proctor, Kutz 2016, doi:10.1073/pnas.1517384113 [all DOI OK] | A closed-form expression fitting data | Certainty: in general it is NP-hard (Virgolin & Pissis 2022, arXiv:2207.01018 [arXiv OK]), and on finite ranges different forms fit equally well (section 3 here) | Held-out data at most; no proof | Weak for costs; exact counts plus recurrence guessing (below) are strictly better |
| **Integer relations / minimal polynomials**: LLL 1982, doi:10.1007/BF01457454; PSLQ, Ferguson, Bailey, Arno 1999, doi:10.1090/S0025-5718-99-00995-3; Kannan, Lenstra, Lovász 1988, doi:10.1090/S0025-5718-1988-0917831-4; the BBP formula found this way, Bailey, Borwein, Plouffe 1997, doi:10.1090/S0025-5718-97-00856-9 [all DOI OK] | Small integer relations among high-precision numbers: minimal polynomials of constants, formulas for constants | A relation when the precision is too low for the coefficient size (an information bound); proofs | Higher precision, then an exact algebraic proof (e.g. divisibility of a known annihilating polynomial) | **Run here** on growth constants ([exp: formula_recognition], section 5.1) |
| **Sequence and recurrence guessing**: Berlekamp–Massey, Massey 1969, doi:10.1109/TIT.1969.1054260; holonomic sequences, Stanley 1980, doi:10.1016/S0195-6698(80)80051-5; GFUN, Salvy & Zimmermann 1994, doi:10.1145/178365.178368; Kauers & Paule 2011, *The Concrete Tetrahedron*, doi:10.1007/978-3-7091-0445-3 [all DOI OK] | A linear recurrence (constant or polynomial coefficients) fitting the terms, hence asymptotics λⁿ nᶿ and fast evaluation | Sequences outside the class (e.g. no small recurrence found for the MST enumeration count, section 5.1); a proof that the guess holds for all n | Overdetermined systems plus held-out terms. A proof comes from structure: diagonals of rational functions are D-finite (Lipshitz 1989, doi:10.1016/0021-8693(89)90222-6 [DOI OK; content recalled]), or from the program's call structure | **Run here** on 14 count sequences |
| **Ramanujan Machine**: Raayoni et al. 2021, doi:10.1038/s41586-021-03229-4 [DOI OK] | Conjectured continued-fraction formulas for constants | Proofs | Numerical agreement to many digits, then a proof | Not directly applicable |
| **Automated conjecturing**: Graffiti, Fajtlowicz 1988, doi:10.1016/0012-365X(88)90199-9; ML-guided intuition, Davies et al. 2021, doi:10.1038/s41586-021-04086-x; RL counterexample search, Wagner 2021, arXiv:2104.14516 [all OK] | Conjectured inequalities and relations between invariants; counterexamples | Proofs (a counterexample *is* a proof of falsity) | A human or machine proof; for counterexamples, an exact check | The 4-bit measure tables (section 5.3) are the raw material for such conjectures on query measures |

**Take-away (observation, consistent with all rows):** no method in this table produces a verified asymptotic
algorithm on its own. New pairs come either from bilinear amplification (Strassen-type) or from a proof. For the
project, the methods' value is (a) proposing candidates, (b) recognising and checking the *shape* of costs, and
(c) generating counterexamples to wrong claims.

---

## 2. Area 2: predicting where fast algorithms exist (and where they do not)

### 2.1 Structural theories that imply polynomial algorithms (theorems)

| Theory | Statement (status) | Mechanisable as a predictor? |
|---|---|---|
| Matroids and greedy | Greedy is optimal for every weight function iff the independence system is a matroid (Rado; Edmonds 1971, doi:10.1007/BF01584082 [DOI OK; content recalled]) | **Yes, for small ground sets**: test the exchange axiom exhaustively. Explains the MST entry (graphic matroid). Not run (time). |
| Submodular minimisation | Polynomial time: ellipsoid (Grötschel, Lovász, Schrijver 1981, doi:10.1007/BF02579273), combinatorial (Schrijver 2000, doi:10.1006/jctb.2000.1989; Iwata, Fleischer, Fujishige 2001, doi:10.1145/502090.502096) [all DOI OK; content recalled] | Partly: submodularity of a given set function on a small ground set can be tested exhaustively |
| Total unimodularity | A TU constraint matrix with integral right-hand side makes the LP integral (Hoffman–Kruskal [recalled]); TU is recognisable in polynomial time via Seymour's decomposition (Seymour 1980, doi:10.1016/0095-8956(80)90075-1 [DOI OK; content recalled]) | **Yes, small cases**: brute-force all square subdeterminants (`exactalg.det_bareiss`). Explains bipartite matching/assignment vs general matching. Not run. |
| Bounded treewidth | MSO-definable properties are decidable in linear time on graphs of bounded treewidth (Courcelle 1990, doi:10.1016/0890-5401(90)90043-H); tree decompositions of width k in linear time for fixed k (Bodlaender 1996, doi:10.1137/S0097539793251219); Arnborg & Proskurowski 1989, doi:10.1016/0166-218X(89)90031-0 [all DOI OK; content recalled] | In principle, but the constants are astronomical; useful as a *reason* why NP-hard entries become polynomial on restricted families |
| Boolean CSP dichotomy | Schaefer 1978, doi:10.1145/800133.804350: six tractable classes, all else NP-complete (theorem). Algebraic form via polymorphisms: Jeavons, Cohen, Gyssens 1997, doi:10.1145/263867.263489; Jeavons 1998, doi:10.1016/S0304-3975(97)00230-2 [all DOI OK] | **Yes, implemented and run** (section 5.4) |
| General finite-domain CSP dichotomy | Conjectured by Feder & Vardi 1998, doi:10.1137/S0097539794266766; proven independently by Bulatov 2017, doi:10.1109/FOCS.2017.37, and Zhuk 2017/2020, doi:10.1109/FOCS.2017.38, doi:10.1145/3402029 (theorem). Tractable iff there is a weak near-unanimity polymorphism, equivalently a Siggers polymorphism (Siggers 2010, doi:10.1007/s00012-010-0082-3) [all DOI OK; content recalled]. Special case: H-colouring is in P iff H is bipartite (else NP-complete), Hell & Nešetřil 1990, doi:10.1016/0095-8956(90)90132-J [DOI OK] | **Decidable for a fixed finite template** (search for a 4-ary Siggers polymorphism); exponential in the domain size, feasible for domains of size ≤ 3 with a constraint solver. Not run (next step) |
| Counting dichotomies | Boolean #CSP is in FP iff affine, else #P-complete (Creignou & Hermann 1996, doi:10.1006/inco.1996.0016); general #CSP dichotomy (Bulatov 2013, doi:10.1145/2528400) is decidable (Dyer & Richerby 2013, doi:10.1137/100811258) [all DOI OK; content recalled] | **Boolean case implemented** (affine test plus counting, section 5.4) |
| Planar matchings vs the permanent | The permanent is #P-complete (Valiant 1979, doi:10.1016/0304-3975(79)90044-6); planar perfect matchings are countable in polynomial time via Pfaffians (Kasteleyn 1961, doi:10.1016/0031-8914(61)90063-5; Temperley & Fisher 1961, doi:10.1080/14786436108243366); holographic algorithms generalise this (Valiant 2008, doi:10.1137/070682575; Cai & Lu 2011, doi:10.1016/j.jcss.2010.06.005) [all DOI OK; content recalled] | Only by the explicit "matchgate signature" test of holographic algorithms; a research project, not a quick predictor |

### 2.2 Theories that predict hardness

| Theory | Status | What it predicts for candidate pairs |
|---|---|---|
| NP-completeness (Cook 1971, doi:10.1145/800157.805047 [DOI OK]; Karp 1972 [book chapter]) | Theorem (relative to P ≠ NP, a conjecture) | No polynomial algorithm unless P = NP, so T6 + T8 at best |
| Ladner 1975, doi:10.1145/321864.321877 [DOI OK] | Theorem: if P ≠ NP, NP-intermediate problems exist | Dichotomies are special, not automatic |
| ETH / SETH (Impagliazzo & Paturi 2001, doi:10.1006/jcss.2000.1727; Impagliazzo, Paturi, Zane 2001, doi:10.1006/jcss.2001.1774) [DOI OK] | Conjectures | No 2^o(n) algorithm for 3-SAT (ETH); no (2−ε)ⁿ for CNF-SAT (SETH). Bounds how far T8 improvements can go |
| Fine-grained: 3SUM (Gajentaan & Overmars 1995, doi:10.1016/0925-7721(95)00022-2); APSP and triangle equivalences (Vassilevska Williams & Williams 2018, doi:10.1145/3186893); edit distance under SETH (Backurs & Indyk 2018, doi:10.1137/15M1053128); OV via 2-CSP (Williams 2005, doi:10.1016/j.tcs.2005.09.023) [all DOI OK] | Conditional lower bounds (conjectures plus proven reductions) | The project's 3SUM, APSP and edit-distance entries sit **exactly at** the conjectured barriers: a strongly subquadratic edit-distance or 3SUM algorithm, or a truly subcubic APSP algorithm, would refute a named conjecture. Their "fast" sides are believed optimal up to n^o(1) |

**Which of these can become a mechanical predictor for candidate pairs (proposal):**
(1) Schaefer and Boolean #CSP: done, exact, instant. (2) H-colouring bipartiteness: trivial. (3) Finite-domain CSP via
Siggers-polymorphism search: decidable, feasible for tiny templates. (4) Matroid exchange axiom and TU on small
instances: exhaustive tests. (5) Reductions to 3SUM/APSP/OV/SAT: not mechanisable in general; they need a human
reduction, but a *tag* ("at a SETH/3SUM/APSP barrier") can be added per entry from the literature.

---

## 3. Area 3: recognising the shape of a cost from data

| Approach | What it yields | Limit | Here |
|---|---|---|---|
| Empirical complexity fitting (trend-prof: Goldsmith, Aiken, Wilkerson 2007, doi:10.1145/1287624.1287681; input-sensitive profiling: Coppa, Demetrescu, Finocchi 2012, doi:10.1145/2254064.2254076; McGeoch 2012, doi:10.1017/CBO9780511843747 [all DOI OK]) | Power-law exponents of counts or times against input size | Finite range: n^a vs n^a log n and vs n^(a+δ) are nearly collinear in log space | The project's V2; quantified in section 5.2 |
| Model selection (AIC: Akaike 1974, doi:10.1109/TAC.1974.1100705; BIC: Schwarz 1978, doi:10.1214/aos/1176344136 [DOI OK]) | A ranking of candidate shapes by fit and complexity | Shapes with equal parameter counts reduce to residual comparison; identifiability is set by collinearity (corr(log n, log log n) ≥ 0.98 on every grid tried) | Section 5.2, part 3 |
| Growth constants from exact counts: the ratio method and differential approximants (Guttmann (ed.) 2009, doi:10.1007/978-1-4020-9927-4 [DOI OK]); analytic combinatorics (Flajolet & Sedgewick 2009, doi:10.1017/CBO9780511801655 [DOI OK]) | λ and θ in a(n) ~ C λⁿ nᶿ, numerically | Numeric, with error estimates only | Richardson-extrapolated ratios, then LLL (section 5.1) |
| Recurrence guessing (Berlekamp–Massey; holonomic guessing via Padé-type approximants, Beckermann & Labahn 1994, doi:10.1137/S0895479892230031 [DOI OK; content recalled]) and the asymptotics of recurrences (Wimp & Zeilberger 1985, doi:10.1016/0022-247X(85)90209-4 [DOI OK]) | An *exact* recurrence, hence an exact λ (algebraic, with minimal polynomial) and an exact θ | Needs exact terms and enough of them: (r+1)(d+1) unknowns plus a margin. Proof is separate | Section 5.1; for divide-and-conquer counts on n = 2ᵏ the sequence in k is C-finite (cf. Bentley, Haken, Saxe 1980, doi:10.1145/1008861.1008865 [DOI OK; content recalled]), section 5.2 part 4 |
| Recognising constants (integer relations, minimal polynomials; KLL 1988) | Exact algebraic identification of a numeric growth constant | Precision must exceed (degree + 1) × log10(coefficient size) | Section 5.1 |

---

## 4. Area 4: quantum questions

### 4.1 Provable vs conjectural (status table)

| Claim | Status | Source |
|---|---|---|
| BQP ≠ BPP | **Open**. It would imply P ≠ PSPACE (BPP ⊆ BQP ⊆ PSPACE) | notes/quantum-vs-classical-evidence.md |
| Exponential query separations for *promise* problems (Simon; Bernstein–Vazirani recursive; Forrelation: 1 vs Ω̃(√N)) | **Theorems** in the query model | Simon 1997, doi:10.1137/S0097539796298637; Bernstein & Vazirani 1997; Aaronson & Ambainis 2015, doi:10.1145/2746539.2746547 [DOI OK] |
| For *total* functions, quantum query speedups are at most polynomial: D(f) = O(Q₂(f)⁶) | **Theorem** | Beals et al. 2001, doi:10.1145/502090.502097 [DOI OK; the exponent 6 is recalled]. Improved to D = O(Q⁴) by Aaronson, Ben-David, Kothari, Rao, Tal 2021, doi:10.1145/3406325.3451047 [DOI OK; exponent recalled] |
| Grover is optimal: Ω(√N) | **Theorem** | Bennett, Bernstein, Brassard, Vazirani 1997, doi:10.1137/S0097539796300933; Zalka 1999, doi:10.1103/PhysRevA.60.2746 [DOI OK] |
| BQP ⊄ PH relative to an oracle | **Theorem** (oracle) | Raz & Tal 2022, doi:10.1145/3530258 [DOI OK] |
| Hardness of classical sampling (IQP, BosonSampling) | **Conditional** (non-collapse of PH, plus further conjectures for approximate sampling) | Bremner, Jozsa, Shepherd 2011, doi:10.1098/rspa.2010.0301 [DOI OK]; Aaronson & Arkhipov, arXiv:1011.3245 [arXiv OK] (the ToC DOI 10.4086/toc.2013.v009a004 resolves but Crossref stores no title) |
| Factoring and discrete log in quantum polynomial time | **Theorem** (Shor 1997, doi:10.1137/S0097539795293172 [DOI OK]); classical hardness is a **conjecture** | — |
| Dequantisation of low-rank QML tasks | **Theorems** (classical algorithms with comparable input access) | Tang 2019, doi:10.1145/3313276.3316310; Chia et al. 2022, doi:10.1145/3549524 [DOI OK]; caveats: Aaronson 2015, "Read the fine print", doi:10.1038/nphys3272 [DOI OK] |

### 4.2 Lower-bound methods (all theorems; the content statements are recalled unless stated)

- **Polynomial method**: Q_E(f) ≥ deg(f)/2 and Q_ε(f) ≥ adeg_ε(f)/2 (Beals et al. 2001 [DOI OK]); adeg(ORₙ) = Θ(√n)
  and the degree of total functions (Nisan & Szegedy 1994, doi:10.1007/BF01263419 [DOI OK]); symmetric functions:
  adeg = Θ(√(n(n − Γ(f)))) (Paturi 1992, doi:10.1145/129712.129758 [DOI OK]). **Computed exactly here** (section 5.3).
  Dual certificates ("dual polynomials") are exact lower-bound witnesses; the exchange algorithm below produces them.
- **Adversary methods**: Ambainis 2002, doi:10.1006/jcss.2002.1826; negative weights, Høyer, Lee, Špalek 2007,
  doi:10.1145/1250790.1250867; equivalence of the positive versions, Špalek & Szegedy 2006, arXiv:quant-ph/0409116
  [arXiv OK]. The general adversary bound is tight for bounded-error query complexity up to a constant factor
  (Reichardt 2011, doi:10.1137/1.9781611973082.44; Lee, Mittal, Reichardt, Špalek, Szegedy 2011,
  doi:10.1109/FOCS.2011.75) [DOI OK].
- **SDP characterisation**: Barnum, Saks, Szegedy 2003, doi:10.1109/CCC.2003.1214419 [DOI title OK; Crossref stores no
  year]: quantum query complexity is the value of a semidefinite program, which is exactly computable in principle
  for small functions.
- **Computer searches on small functions**: exact quantum query complexity of all Boolean functions on up to 4 bits
  via SDP (Montanaro, Jozsa, Mitchison 2015, doi:10.1007/s00453-013-9826-8 [DOI OK; content recalled]); superlinear
  exact separations found from small seeds (Ambainis 2013, doi:10.1145/2488608.2488721 [DOI OK]); exact Q_E of EXACT
  and THRESHOLD (Ambainis, Iraids, Smotrovs, arXiv:1302.1235 [arXiv OK]); Midrijanis, arXiv:quant-ph/0403168 [arXiv OK].
- **Classical lower bounds needed by T9 entries**: block sensitivity gives R₂(f) = Ω(bs(f)) (Nisan 1991,
  doi:10.1137/0220062 [DOI OK; the constant is recalled]); Yao's minimax principle (Yao 1977,
  doi:10.1109/SFCS.1977.24 [DOI OK]) turns a hard distribution into a randomised lower bound. For the project's
  *promise* problems (Simon, collision) the classical bounds are probabilistic or birthday arguments, which are
  already cited in the entries; bs-based bounds apply to total functions such as OR (Grover, minimum finding).

### 4.3 Boundaries of classical simulability (theorems; content recalled)

Stabiliser circuits (Gottesman–Knill: Gottesman 1998, arXiv:quant-ph/9807006 [arXiv OK]; Aaronson & Gottesman 2004,
doi:10.1103/PhysRevA.70.052328 [DOI OK]); matchgates / non-interacting fermions (Valiant 2002,
doi:10.1137/S0097539700377025; Terhal & DiVincenzo 2002, doi:10.1103/PhysRevA.65.032325; Jozsa & Miyake 2008,
doi:10.1098/rspa.2008.0189) [DOI OK]; low entanglement (Vidal 2003, doi:10.1103/PhysRevLett.91.147902; Jozsa & Linden
2003, doi:10.1098/rspa.2002.1097) [DOI OK]; tensor networks of low treewidth (Markov & Shi 2008,
doi:10.1137/050644756 [DOI OK]). **Use for the project:** a claimed quantum speedup whose circuit falls in one of these
classes is not a speedup. These are the quantum analogue of the "structure implies a fast algorithm" theories of
section 2 and could become a checklist field for quantum entries.

### 4.4 How this serves the project (proposal)

- The owner's thesis ("quantum ≠ classical capability") is **proven in the query model** and is exactly what T9
  records. The polynomial method makes the quantum *lower* bounds (optimality of Grover, of minimum finding) checkable
  by machine for small N, with exact rational certificates (section 5.3). The *classical* lower bounds of T9 entries
  are combinatorial and, for total functions, can be cross-checked by exact D, bs and C computations.
- Exponential T9 separations require promises (theorem: total functions allow only polynomial gaps). This explains
  why every exponential T9 entry (Simon, Deutsch–Jozsa exact, Bernstein–Vazirani) is a promise problem.

---

## 5. Computational results (all exact unless marked; provenance in brackets)

### 5.1 (a) Formula recognition on the project's exact counts [exp: formula_recognition]

Counts come from the entries' own implementations. Call counts are measured with `sys.setprofile` for small n; a call
recurrence read off the code is checked to be **equal** to the measured counts, then used to extend the sequence. The
sizes are listed per row. Harness counts are measured for every n.

| Sequence (entry) | Measured / extended | Guessed recurrence (terms used / checked) | Characteristic polynomial (factors) | λ, minimal polynomial | θ | Claim | Verdict |
|---|---|---|---|---|---|---|---|
| Fibonacci naive, calls | n ≤ 22 / to 40 | C-finite order 3 (37 / 41) | (x−1)(x²−x−1) | 1.618033988749895, x²−x−1 | 0 | Θ(φⁿ) | match |
| Edit distance plain recursion, calls | n ≤ 7 / to 26 | **P-recursive order 3, degree 2**: (−2n²+3n)a(n) + (14n²−27n+10)a(n−1) + (−14n²+29n−12)a(n−2) + (2n²−5n+2)a(n−3) = 0; 21 equations, 12 unknowns, nullspace dim 1, 3 held out | −2(x−1)(x²−6x+1) | 5.82842712474619, x²−6x+1 | **−1/2** (exact; numeric slope −0.4950) | Θ((3+2√2)ⁿ/√n) | match |
| Matrix chain plain recursion, calls | n ≤ 10 / to 30 | order 1 (26 / 30) | x−3 | 3 | 0 | Θ(3ⁿ) | match |
| Optimal BST plain recursion, calls | n ≤ 9 / to 30 | order 1 | x−3 | 3 | 0 | Θ(3ⁿ) | match |
| synthetic c1-0-1, calls | n ≤ 18 / to 40 | order 4 | (x−1)(x³−x²−1) | 1.46557123187677 | 0 | λ = 1.4655712319 | match |
| synthetic c1-1-1, calls | n ≤ 18 / to 40 | order 4 | (x−1)(x³−x²−x−1) | 1.83928675521416 | 0 | Θ(λⁿ) | match |
| synthetic c1-1-1-1, calls | n ≤ 18 / to 40 | order 5 | (x−1)(x⁴−x³−x²−x−1) | 1.92756197548293 | 0 | Θ(λⁿ) | match |
| synthetic c2-3, calls | n ≤ 18 / to 40 | order 3 | (x−1)(x²−x−1) | 1.618…, x²−x−1 | 0 | λ = 1.6180339887 (support polynomial) | match |
| LIS subset enumeration (harness) | n = 1..16 | order 3 (12 / 16) | (x−1)(x−2)² | 2 (mult. 2) | 1 | Θ(2ⁿ n) | match |
| Regex backtracking on Pₙ (harness) | n = 1..14 | order 3 (10 / 14) | (x−1)(x−2)² | 2 (mult. 2) | 1 | n·2ⁿ | match |
| Global min cut brute force (harness) | n = 2..16 | order 4 (11 / 15) | (x−1)(x−2)³ | 2 (mult. 3) | 2 | Θ(n² 2ⁿ) | match |
| Zeta transform naive (harness) | n = 1..14 | order 1 | x−3 | 3 | 0 | Θ(3ⁿ) | match |
| Determinant cofactor expansion, calls | n ≤ 8 / to 30 | P-recursive order 2, degree 1: a(n) − (n+1)a(n−1) + (n−1)a(n−2) = 0 | — (deg p₀ < deg p₁) | factorial type | — | Θ(n!) | super-exponential correctly detected; λⁿnᶿ does not apply |
| MST enumeration (harness n = 2..7 equals the entry's formula; formula to n = 40) | 39 terms | **none** with order ≤ 4, degree ≤ 4 | — | — | — | 2^Θ(n log n) | NULL (whether it is holonomic is not decided here) |

Dominance of λ over all other roots is **certified** exactly in every λⁿ row (per-factor Schur bound, `exactalg.dominance_certificate`).

**Independent experimental-mathematics route** (counts only, no recurrence): Richardson-extrapolated ratios give λ with an
*estimated* error, and LLL with an information-bound acceptance test gives a minimal-polynomial guess. Examples:
edit distance λ ≈ 5.82842753658999 (estimated error 8.1·10⁻⁸, actual 4.1·10⁻⁷), giving x²−6x+1; Fibonacci
1.61803019415872 (estimated 1.8·10⁻⁶), giving x²−x−1; c1-0-1 1.4655129467457 (estimated 2.9·10⁻⁵), giving x³−x²−1;
global min cut 2.00048763442422 (estimated 6.8·10⁻⁴), giving x−2. **The guess agrees with the exact minimal
polynomial in 12 of 12 cases.**

What this shows (observation): for every exponential slow algorithm whose count the project records exactly, the
claimed cost is recoverable **exactly**, including the polynomial correction θ, which a log-log V2 fit cannot see
(the edit-distance n^(−1/2)). The guesses are conjectures checked on held-out terms. For the call counts, the
recurrence family is also implied by the program's structure: the counting recurrences above are linear with constant
or polynomial coefficients by construction.

### 5.2 (b) Identifiability of log factors [exp: log_identifiability]

**Part 1, the recorded run re-analysed with perfect data.** For each V2 measurement in `ledger/runs/20261006T105123Z.json`
(read-only), the validator's diagnostic was recomputed with the measured values replaced by the claimed cost itself
(noise-free):

| measure | fits with a diagnostic | resolved in the ledger | resolvable with **perfect** data, same grid and tolerance | largest tolerance that still resolves (min / median / max) |
|---|---|---|---|---|
| time (tol 0.25) | 44 | 0 | **0** | 0.0212 / 0.0494 / **0.1015** |
| reported counts (tol 0.01–0.25) | 56 | 47 | 48 | 0.0319 / 0.0821 / 0.3993 |

The best timing grid (modular exponentiation, square-and-multiply, n-span ×64) separates a log factor by only 0.1015.
**So RL-048's "0 timing fits resolve a log factor" is a property of the tolerance and the n-ranges, not of timing
noise. Even perfect timings could not resolve it at ±0.25.** The single count fit where perfect data would resolve
but the ledger does not is LIS subset enumeration: the perfect-data margin is 0.0319 against tolerance 0.03, and the
measured count (n−2)·2^(n−1) + 1 has lower-order terms that shift it.

**Part 2, analytic separation on geometric grids** (8 points). The noise-free separation is approximately
1/(a·ln n̄): for n ∈ [10³, 10⁵] it is 0.0994 (a = 1), 0.0523 (a = 2), 0.0355 (a = 3). SE(α) at σ = 0.05 is 0.0117 / 0.0059 / 0.0039.
In the free model log y = c + a log n + b log log n, SE(b) at σ = 0.05 is 1.456 on [10³, 10⁵] and 0.204 on [2⁵, 2²⁰]:
a log *exponent* cannot be estimated when the power is free, because corr(log n, log log n) ≥ 0.98 on every grid.

**Part 3, Monte Carlo model selection** (truth n log n, 8 points on [10³, 10⁵], 400 seeds, six candidate shapes):
correct 100% (σ = 0), 99.8% (0.01), 81.0% (0.03), 57.8% (0.1), 31.5% (0.3). The main confusion is with n^1.1, and
symmetrically n^1.1 data is called n log n in 62 of 400 cases at σ = 0.03. Noise-free n log n data fitted against a
claim of n^1.1 gives α = 1.0094 and passes tolerance 0.25.

**Part 4, exact remedy: recurrences in k for counts at n = 2ᵏ.**

| Counts | Berlekamp–Massey | Shape read off |
|---|---|---|
| NTT, k = 1..14 (harness) | (x−2)², order 2, 11 terms used, 14 checked | n¹ (log n)¹; the claim n(3 log₂ n + 5) is consistent |
| Karatsuba, k = 5..12 | x−3 | n^(log₂3), no log factor |
| Strassen, k = 4..7 harness plus the ledger's k = 8 | x−7 (4 used, 5 checked; few terms) | n^(log₂7), no log factor |
| Yates zeta transform, n = 1..14 (N = 2ⁿ) | (x−2)² | N log N |

The dominant root gives the exponent exactly (log₂ λ), and its multiplicity m gives the log power (log n)^(m−1). For
exact counts this **settles log factors with no tolerance at all**. The cost is that n must be restricted to powers of
2 (or another fixed ratio) and enough terms are needed: (2L + 2 + held-out) for order L.

### 5.3 (c) Boolean-function measures [exp: boolean_measures]

- **adeg₁/₃(ORₙ)**, exact via the Stiefel exchange algorithm on the symmetrised problem, with a primal polynomial and
  an alternating dual certificate (weak duality) proving optimality at every degree. Values: n:adeg = 1:1, 2:1, 3:1,
  4–10:2, 11–21:3, 22–37:4, 38–58:5, 59–80:6, 96:7, 128:8, 160:9, 192:10, 256:11. Convention: least d with E_d ≤ 1/3;
  ties E_d = 1/3 occur at n = 3 and n = 10. Fit: adeg ≈ **0.7246·√n**; log-log slope for n ≥ 16 is **0.4748**
  (theory: 1/2). The Nisan–Szegedy bound √(n/6) [statement recalled] holds at every computed n. Via Q₂ ≥ adeg/2:
  Q₂(OR₂₅₆) ≥ 5.5.
- **Observation:** E₁(ORₙ) = (n−1)/(2n) exactly for every n = 2..64.
- **Parity:** deg = n (Möbius, n ≤ 12) and adeg = n (n ≤ 16). **Majority:** adeg = 1, 1, 1, 3, 3, 3, 5, … (odd n ≤ 41), with
  log-log slope 0.8738 for n ≥ 9 (Paturi: linear). This is INCONCLUSIVE as an asymptotic statement: a finite range
  shows the theorem's linear growth only approximately. **Thresholds** on n = 64:
  adeg / √(n(n−Γ)) ranges over 0.268–0.750 for t = 1..32. That is consistent with Θ(·), but the constants vary by a factor of 2.8.
- **All functions on 3 and 4 variables:** 14 and 222 NPN classes (published 14 and 222, OEIS A000370 [recalled]).
  For all 222 classes: Huang's deg ≤ s² [theorem; DOI OK], s ≤ bs ≤ C ≤ D, deg ≤ D, adeg ≤ deg, bs ≤ 2deg², and
  D ≤ C·bs [recalled] **all hold**. Distributions: D = 4 for 184 classes (evasive), deg < D for 22 classes; adeg
  is 0:1, 1:7, 2:102, 3:106, 4:6. Largest D − ⌈adeg/2⌉ gaps (D = 4, adeg = 2): truth tables 0x0001 (AND-type),
  0x0006, 0x0007, 0x0017, 0x0018. Symmetrisation check: the multilinear LP and the univariate exchange give the same
  adeg for all 32 symmetric 4-bit functions.
- **Solver cross-check:** the exchange optimum is certified and equals the exact simplex LP optimum in **960 of 960**
  (profile, degree) cases (all 0/1 profiles, n ≤ 6, d ≤ 3).
- **Not done:** exact Q_E/Q₂ by SDP. No SDP solver is available in the standard library, and a pure-Python SDP with
  certified rational rounding was not feasible in this round's budget (next step 5 in section 6).

### 5.4 (d) Tractability predictor [exp: csp_predictor]

- **Galois-connection check:** for all 4 + 16 + 256 relations of arity 1, 2, 3, the polymorphism classification equals
  the syntactic one (Horn / dual-Horn / 2-CNF clause sets, GF(2) cosets): **0 mismatches**. Nonempty ternary relations
  per class: 0-valid 128, 1-valid 128, Horn 121, dual-Horn 121, bijunctive 165, affine 51. **15 nonempty ternary
  relations are in no class** (their single-relation CSP is NP-complete by Schaefer). No published count was checked.
- **Algorithms vs brute force:** for each class, 150 random languages (3 relations each) and instances (n = 6..11):
  decisions agree **150/150** for every class, and every witness is valid (Horn 93/93, dual-Horn 82/82, bijunctive
  48/48, affine 14/14, constant classes 150/150). Affine counts 2^(n−rank) equal the brute-force counts 150/150.
- **Negative control:** Horn propagation applied to NAE-3-SAT, which the predictor does not license, gives a
  **wrong witness on 200 of 200** instances. Its *decisions* happened to agree on all 200 random instances, which is
  why the first version of this control, which compared decisions only, wrongly showed "0 failures" (section 7).
- **Named languages:** 2-SAT → P (bijunctive); 3-SAT → NP-complete; positive 3-clauses only → P (1-valid, dual-Horn);
  Horn-3-SAT → P (0-valid, Horn); XOR-SAT → P (affine); 1-in-3-SAT → NP-complete; NAE-3-SAT → NP-complete;
  2-colouring → P (bijunctive, affine).

### 5.5 Citation checks [exp: sources]

117 identifiers: **114 OK**, 1 OK without a year (Barnum–Saks–Szegedy CCC 2003), and 2 Theory of Computing DOIs whose
Crossref title is empty (their arXiv versions match). Four DOIs I first guessed were wrong (they belong to other
papers) and were corrected through Crossref search: Graffiti, Siggers, Reichardt SODA 2011, Kannan–Lenstra–Lovász.

---

## 6. Recommendations (proposals, ranked)

| # | Recommendation | Why (evidence) | Effort |
|---|---|---|---|
| 1 | **Exact shape diagnostic for exact-count V2**: for exact counts at n = 2ᵏ, run Berlekamp–Massey in k and report (λ, multiplicity), i.e. exponent and log power. For exponential counts on consecutive n, run C-finite or holonomic guessing and report (λ, minimal polynomial, θ). Informational first, like the log-factor diagnostic. | 12/12 slow-count sequences and 4/4 doubling sequences identified exactly (5.1, 5.2); resolves log factors with no tolerance | 0.5–1 day (code exists in `methods/`; needs a harness option for n = 2ᵏ grids and a DECISION entry) |
| 2 | **Document that timing V2 at ±0.25 cannot resolve log factors on any current grid** (max separation 0.1015), and move remaining log-sensitive claims to counts | 5.2 part 1 | 1 hour (text) plus per-entry conversions |
| 3 | **Polynomial-method certificates for T9 entries**: store, for small N, the exact adeg with primal polynomial and dual weights as machine-checkable artefacts (OR for Grover and minimum finding; parity as the contrast) | 5.3; the certificates are exact rationals and checkable in milliseconds | 1 day |
| 4 | **CSP predictor as a candidate source**: new T2 pairs Horn-SAT (brute force vs unit propagation, Dowling & Gallier 1984, doi:10.1016/0743-1066(84)90014-1 [DOI OK]) and XOR-SAT (brute force vs GF(2) elimination), plus a counting pair #XOR-SAT; boundary notes for 1-in-3-SAT and NAE-3-SAT next to the existing 2-SAT/3-SAT note | 5.4: solvers exist and agree 150/150 with brute force | 1 day per pair (hand to the candidates agent) |
| 5 | **Exact Q_E and Q₂ of tiny functions by SDP** (Barnum–Saks–Szegedy), in a separate venv with a numerical SDP solver, then *rational rounding plus an exact feasibility check* of primal and dual, to cross-check published tables (Montanaro–Jozsa–Mitchison 2015) | Section 4.2; the only route to quantum *upper* bounds on small functions | 2–3 days |
| 6 | **Finite-domain CSP predictor** (Siggers-polymorphism search, domain ≤ 3), plus matroid and TU tests on small instances | Section 2.1; decidable, mechanisable | 1–2 days |
| 7 | **LLM or RL proposers only behind exact verifiers** (FunSearch/AlphaEvolve style) in spaces whose finite outputs amplify (bilinear schemes) | Section 1 take-away | high; only after 1–4 |

---

## 7. Decision log, failures and near-misses (this round)

**Decisions**

| Decision | Alternatives considered | Evidence that settled it |
|---|---|---|
| Exact rational arithmetic everywhere; floats only for the numeric θ slope, the Monte Carlo and the Durand–Kerner fallback | mpmath or numpy (not installed; the brief forbids installing into `.venv`) | All headline numbers are exact; the run times were 1–25 s per experiment |
| Extend call counts beyond the measured n with a recurrence read off the code, after checking equality with the measured counts | Measured counts only | Edit distance is measurable only to n = 7 (8 terms), but the holonomic ansatz needs ≥ 12 + margin terms; the model equals all measured counts in every case |
| Symmetric approximate degree by the exchange algorithm with a dual certificate, cross-checked by the simplex LP | Simplex only | Exchange: 70 values of n in 1.5 s with optimality certificates; LP agreement 960/960 |
| LLL acceptance uses an *estimated* error (Richardson difference) and an information bound | Using the true error (first version) | The first version leaked the exact answer into the "independent" route; fixed |
| No SDP computation | Pure-Python SDP; a separate venv with a solver | No exact or well-documented numerics achievable in the budget; documented as next step 5 |
| Matroid / TU demonstrations not run | Implement them in `methods/structure.py` | Time budget; recorded as next step 6 |
| adeg convention: least d with E_d ≤ 1/3 (ties count) | Strict < 1/3 | Standard; ties at n = 3 and 10 are listed so either convention can be read off |

**Failures and near-misses of my own computations** (all fixed before the final runs)

1. **Wrong claim input (my bug):** for `synthetic/linear-recurrence-c2-3` I compared against the root of the
   *coefficient* polynomial x² − 2x − 3 (λ = 3). The naive recursion's call count depends only on the *support* of the
   coefficients, so λ = φ, which is what the entry says. The first run printed "DIFFERS"; the entry was right.
2. **LLL acceptance too lenient:** with a 4-digit estimate of φ, LLL's degree-1 relation 34x − 55 was accepted.
   Fixed by requiring the residual to be explained by the estimated error and (d+1)·log₁₀(max|c|) + 1 ≤ digits.
   After the fix, 12/12 agree.
3. **Too few terms:** global min cut with n ≤ 14 (13 terms) gave "no recurrence", because order 4 needs
   2·4 + 2 training terms plus holdout. With n ≤ 16 the order-4 recurrence (x−1)(x−2)³ is found.
4. **Negative control that could not fail:** the NAE-3-SAT control first compared decisions only (0/200
   disagreements). Unit propagation uses only NAE's implied Horn clause (¬x∨¬y∨¬z) and answers "satisfiable" with the
   all-zero assignment. Checking witnesses shows 200/200 invalid.
5. **Dominance test:** the first version (one global Schur bound) was inconclusive for (x−1)(x²−x−1). It was replaced by
   a per-irreducible-factor Schur bound, which certifies every case here, with a labelled Durand–Kerner fallback.
6. **Tooling:** two patch attempts silently failed because the shell here-document collapsed `\\n` escapes; they were
   redone with the Edit tool. No result was affected.
7. **Citations:** four guessed DOIs were wrong (section 5.5).

**Open ideas** (IDEA): the holonomic θ formula could also check *staging* claims that state a polynomial factor; a
Siggers-polymorphism search would extend the predictor beyond Boolean domains; dual-polynomial certificates for the
collision problem need two-variable symmetrisation (Aaronson–Shi 2004, doi:10.1145/1008731.1008735 [DOI OK]); the
222-class table is raw material for automated conjecturing on query measures; whether the MST enumeration count is
holonomic is undecided (Flajolet, Gerhold, Salvy 2005, arXiv:math/0501379 [arXiv OK], give tools for
non-holonomicity proofs; content recalled).

---

## 8. Draft RESEARCH_LOG entries (DRAFT, for the maintainer to edit and number)

- **DRAFT · VERIFIED · Cost shapes of 12 slow-algorithm count sequences recovered exactly.** Recurrence guessing over Q
  (Berlekamp–Massey, holonomic) plus exact minimal polynomials: all 12 match the entries' claims, including edit
  distance λ = 3+2√2, θ = −1/2 exactly; the LLL route from counts alone agrees 12/12. Provenance: experiment
  `2026-10-06d_meth_formula_recognition.py` (agent report).
- **DRAFT · VERIFIED (re-analysis) · Timing V2 cannot resolve log factors even with perfect data.** On the grids of
  ledger run 20261006T105123Z, 0 of 44 timing fits would resolve a log factor with noise-free data at ±0.25; the
  maximum separation is 0.1015. Sharpens RL-048: the binding constraint is the tolerance and the range, not noise.
  Provenance: `2026-10-06d_meth_log_identifiability.py`.
- **DRAFT · VERIFIED · Doubling-sequence recurrences give exponent and log power exactly.** NTT (x−2)²,
  Karatsuba x−3, Strassen x−7, Yates (x−2)², all consistent with the claims.
- **DRAFT · VERIFIED · Exact approximate degree of ORₙ grows like √n.** n ≤ 256, certified primal and dual, fit
  0.7246·√n, slope 0.4748; parity adeg = n; proven inequalities hold on all 222 NPN classes of 4-bit functions;
  exchange and LP agree 960/960. Provenance: `2026-10-06d_meth_boolean_measures.py`.
- **DRAFT · VERIFIED · Schaefer predictor.** 0 mismatches between polymorphic and syntactic classes over 276 relations;
  900/900 decisions and all witnesses agree with brute force; affine counts 150/150. Provenance:
  `2026-10-06d_meth_csp_predictor.py`.
- **DRAFT · INCONCLUSIVE · Finite-range asymptotics of adeg(MAJₙ)**: log-log slope 0.8738 on odd n ≤ 41, where the
  theorem says linear. A finite range does not show the asymptotic exponent; this is the same identifiability lesson as RL-048.
- **DRAFT · NULL · MST enumeration count**: no recurrence of order ≤ 4 and degree ≤ 4 from 39 exact terms. Not
  evidence of non-holonomicity.
- **DRAFT · NEAR-MISS · Agent's own errors** (section 7, items 1–5), all fixed before the final runs.
- **DRAFT · DECISION (proposed) · Exact shape diagnostic for exact-count V2** (recommendation 1), informational first.
- **DRAFT · IDEA · SDP-based exact quantum query complexity; Horn-SAT / XOR-SAT / #XOR-SAT candidate pairs;
  Siggers-polymorphism predictor** (recommendations 4–6).
- **DRAFT · VERIFIED · Citations of the methodology report:** 117 identifiers, 114 OK, 1 OK without a year, 2 with empty
  Crossref titles (arXiv versions OK), 4 guessed DOIs corrected. Provenance: `2026-10-06d_meth_sources.py` (external).

---

## 9. Bibliography (verification labels from [exp: sources]; title and year checked only)

All DOIs and arXiv ids cited above are listed with title and year in `experiments/2026-10-06d_meth_sources.py`
(`SOURCES`). Final run: 114 OK. The exceptions:
10.1109/CCC.2003.1214419 (title OK, no year in Crossref); 10.4086/toc.2006.v002a001 and 10.4086/toc.2013.v009a004
(Crossref title empty; arXiv quant-ph/0409116 and 1011.3245 OK). Not registry-checked: Karp 1972 [book chapter],
Hoffman–Kruskal 1956 [recalled], Minsky & Papert 1969 *Perceptrons* [book], Stiefel's exchange algorithm [recalled],
OEIS A000370 (NPN class counts 14, 222) [recalled], Bland 1977 is DOI OK (10.1287/moor.2.2.103).

## 10. Reproduction

From the repository root (Windows, `.venv` = CPython 3.14.2, standard library only for everything below):

```
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe experiments\2026-10-06d_meth_formula_recognition.py     # (a) ~ few s
.venv\Scripts\python.exe experiments\2026-10-06d_meth_log_identifiability.py     # (b) ~ 5 s
.venv\Scripts\python.exe experiments\2026-10-06d_meth_boolean_measures.py        # (c) ~ 30 s
.venv\Scripts\python.exe experiments\2026-10-06d_meth_csp_predictor.py           # (d) ~ 2 s
.venv\Scripts\python.exe experiments\2026-10-06d_meth_sources.py                 # citations (network, rate-limited, cached)
.venv\Scripts\python.exe -m unittest tests.test_methods                          # 20 tests
.venv\Scripts\python.exe -m unittest discover -s tests                           # 130 tests OK at the end of this round
.venv\Scripts\python.exe tools\validate.py                                       # 62/62 OK at the end of this round
```

No extra package was needed; `experiments/2026-10-06d_meth_requirements.txt` was therefore not created.

## 11. Files created

- `methods/__init__.py`, `methods/exactalg.py`, `methods/recurrences.py`, `methods/fitting.py`, `methods/lp.py`,
  `methods/boolean.py`, `methods/csp.py`
- `tests/test_methods.py`
- `experiments/2026-10-06d_meth_formula_recognition.py`, `experiments/2026-10-06d_meth_log_identifiability.py`,
  `experiments/2026-10-06d_meth_boolean_measures.py`, `experiments/2026-10-06d_meth_csp_predictor.py`,
  `experiments/2026-10-06d_meth_sources.py`
- `research/2026-10-06d_methodology.md` (this report), `notes/discovery-methods.md`
