# Methodology note: discovery and recognition methods the project should adopt

**Not an entry.** A short, durable guide for future work, written 2026-10-06 by a delegated research agent (Claude).
The evidence, numbers and citations are in [research/2026-10-06d_methodology.md](../research/2026-10-06d_methodology.md);
the code is in [methods/](../methods/).

## The one principle

Every method that has produced new algorithms or formulas pairs a **proposer** (enumeration, stochastic search, RL,
an LLM) with an **exact verifier**. Finite outputs (a program for bounded inputs, a matrix-multiplication scheme, a
constant's minimal polynomial, a guessed recurrence) are only as good as their verification. An *asymptotic* cost
needs one of three things: an amplification mechanism (a small bilinear scheme applied recursively), a proof, or a
guessed recurrence that is then proven. This is START_HERE section 6 restated as a method.

## Adopt, in priority order

1. **Exact shape identification for exact counts** (`methods/recurrences.py`).
   - Exponential costs counted on consecutive n: guess a recurrence (Berlekamp–Massey or holonomic), read off the
     exact growth constant λ with its minimal polynomial and the polynomial exponent θ.
   - Divide-and-conquer costs counted at n = 2^k: Berlekamp–Massey in k. The dominant root gives the exponent
     log₂ λ; its multiplicity m gives (log n)^(m−1).
   - *Why:* this recovered the claimed cost exactly for 12 of 12 slow-algorithm count sequences, including the
     n^(−1/2) of plain-recursion edit distance, and settled log factors for the NTT, Karatsuba, Strassen and Yates
     with no tolerance.
   - *Rule:* a guess counts only if it is overdetermined, has a one-dimensional solution space and reproduces
     held-out terms. It is still a conjecture until proven.
2. **Do not expect log factors from timing.** At tolerance ±0.25, no current timing grid can separate n^a from
   n^a log n, even with perfect data: the largest separation is 0.10. Log-sensitive claims need exact counts.
3. **Polynomial-method certificates for quantum lower bounds** (`methods/boolean.py`).
   - Exact approximate degree with a primal polynomial and a dual certificate proves Q₂ ≥ adeg/2 for small N.
   - adeg(ORₙ) grows like √n, which is Grover's optimality.
   - D, bs and C give the classical side for total functions.
   - Exponential quantum query gaps need promise problems: for total functions the gap is provably polynomial.
4. **Mechanical tractability prediction where a dichotomy theorem exists** (`methods/csp.py`).
   - Boolean CSPs: Schaefer's six polymorphisms (and affine-only for counting).
   - Next: H-colouring (bipartite or not); finite-domain CSPs via a Siggers polymorphism; matroid and TU tests on
     small instances.
   - Use it to propose candidate pairs (Horn-SAT, XOR-SAT, #XOR-SAT) and boundary notes (1-in-3-SAT, NAE-3-SAT).
5. **Exact quantum query complexity of tiny functions by SDP**: in a separate venv, with rational rounding and an
   exact feasibility check of both primal and dual before any number is quoted.
6. **LLM or RL proposers** (FunSearch, AlphaEvolve style): only behind an exact verifier, and preferably in search
   spaces whose finite outputs amplify into asymptotic statements.

## Do not

- Do not treat a good fit as identification. On finite ranges, n log n and n^1.1 are confused in 15–20% of cases
  at only 3% noise. A free log exponent is not estimable, because corr(log n, log log n) ≥ 0.98.
- Do not accept an LLL or PSLQ relation whose coefficients use about as many digits as the precision supplies.
- Do not run a negative control that cannot fail. Check witnesses, not just decisions.
- Do not quote a paper's content when only its title was checked. Label it.
