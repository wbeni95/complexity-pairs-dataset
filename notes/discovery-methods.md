# Methodology note: discovery and recognition methods evaluated in RL-082

**Not an entry.** A short summary of the methods evaluated in RL-082, written 2026-10-06 by a delegated research
agent (Claude) and reduced to a summary of completed work in RL-086.
The evidence, numbers and citations are in [research/2026-10-06d_methodology.md](../research/2026-10-06d_methodology.md);
the code is in [methods/](../methods/).

## The one principle

Every method in the survey of [research/2026-10-06d_methodology.md](../research/2026-10-06d_methodology.md) §1 that
has produced new algorithms or formulas pairs a **proposer** (enumeration, stochastic search, RL, an LLM) with an
**exact verifier**. Finite outputs (a program for bounded inputs, a matrix-multiplication scheme, a
constant's minimal polynomial, a guessed recurrence) are only as good as their verification. An *asymptotic* cost
needs one of three things: an amplification mechanism (a small bilinear scheme applied recursively), a proof, or a
guessed recurrence that is then proven. This is START_HERE section 6 restated as a method.

## What was evaluated, and what it showed

1. **Exact formula recognition** (`methods/recurrences.py`).
   - For 12 of 12 slow-algorithm count sequences in the dataset, a guessed exact recurrence gave the growth constant
     λ with its minimal polynomial and the polynomial exponent θ, and all matched the entries' claims. Example:
     plain-recursion edit distance gave λ = 3+2√2 (x²−6x+1) and θ = −1/2.
   - An independent route (ratio method plus LLL) agreed in 12 of 12 cases.
   - Cofactor determinant was flagged as factorial-type. The MST enumeration count gave no recurrence of order ≤ 4
     and degree ≤ 4 from 39 terms (NULL; not evidence of non-holonomicity).
   - Guesses were accepted only if overdetermined, with a one-dimensional solution space, and reproducing held-out
     terms. They remain conjectures until proven.
2. **Log-factor identifiability.**
   - On the grids of ledger run 20261006T105123Z, with perfect noise-free data, 0 of 44 timing fits could resolve a
     log factor at tolerance ±0.25. The largest tolerance that would resolve one is 0.1015.
   - On counts at n = 2^k, Berlekamp–Massey found recurrences with characteristic polynomials NTT (x−2)² (n log n),
     Karatsuba x−3, Strassen x−7 (from 4 terms) and Yates (x−2)² (N log N), consistent with the claims. These are
     guesses on finitely many k; they fix the exponent and the log power for all n only together with a proof of the
     recurrence.
   - Monte Carlo (truth n log n, 8 points on [10³, 10⁵]): the correct model was chosen 81.0% of the time at σ = 0.03
     and 57.8% at σ = 0.1. The usual confusion was with n^1.1.
3. **Polynomial-method certificates** (`methods/boolean.py`).
   - Exact adeg₁/₃(ORₙ) for 70 values of n ≤ 256, each with a primal and a dual certificate. Fit 0.7246·√n, log-log
     slope 0.4748 for 16 ≤ n ≤ 256: consistent with, not a proof of, the cited Θ(√n) bound behind Grover's
     optimality.
   - Parity has adeg = n for n ≤ 16. Majority has slope 0.8738 on odd n ≤ 41 against the theorem's linear growth:
     INCONCLUSIVE as an asymptotic statement on this range.
   - On all 222 NPN classes of 4-bit functions, deg ≤ s² (Huang 2019), s ≤ bs ≤ C ≤ D and deg ≤ D hold.
4. **Schaefer tractability predictor** (`methods/csp.py`).
   - Polymorphism and syntactic classifications agreed on all 276 relations of arity ≤ 3.
   - The predicted polynomial algorithm agreed with brute force on 900/900 instances, with valid witnesses; affine
     counting 2^(n−rank) agreed on 150/150.
   - Negative control: Horn propagation on NAE-3-SAT gave an invalid witness on 200/200.
5. **Not done:** exact quantum query complexity by SDP (no solver in the standard library), and the matroid and TU
   demos.

## Lessons learned

- A good fit is not an identification. On finite ranges n log n and n^1.1 were confused in 15–20% of cases at
  only 3% noise, and a free log exponent was not estimable, because corr(log n, log log n) ≥ 0.98 on every grid tried.
- An LLL or PSLQ relation whose coefficients use about as many digits as the precision supplies is not evidence: the
  first acceptance test accepted 34x − 55 for φ.
- A negative control that cannot fail proves nothing. The first NAE-3-SAT control compared decisions only; checking
  witnesses showed 200/200 invalid.
- A paper's content was quoted only where it was read; where only the title was checked, the citation is labelled.
