"""Discovery and recognition methods for the Complexity Pairs Dataset (standard library only).

Added 2026-10-06 by a delegated research agent (round 2026-10-06d); see research/2026-10-06d_methodology.md and
notes/discovery-methods.md. Every routine works in exact rational arithmetic (`fractions.Fraction`) unless its
docstring says otherwise, so the results are exact and reproducible.

Modules:
  exactalg     linear algebra over Q, univariate polynomials over Q, Sturm root isolation, Kronecker factoring,
               LLL lattice reduction and integer-relation search, arithmetic in a number field Q[x]/(m)
  recurrences  Berlekamp-Massey over Q, guessing of linear recurrences with polynomial coefficients
               (holonomic / P-recursive guessing), growth constant and polynomial exponent of the solution
  fitting      log-log slope fits as in tools/validate.py, the log-factor identifiability analysis, BIC selection
  lp           an exact rational simplex method (Bland's rule)
  boolean      Boolean-function measures: D(f), deg(f), approximate degree (exact LP), s, bs, C, NPN classes
  csp          Schaefer's dichotomy as a tractability predictor (polymorphisms) with the matching solvers
"""
