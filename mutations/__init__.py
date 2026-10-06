"""Mutation engine for complexity pairs (standard library only).

Mutations act on PROBLEMS and IMPLEMENTATIONS, never on cost formulas: a mutated problem is defined by the brute side
(which evaluates any objective or algebra), the fast algorithm is run as a mutated copy, the two are compared by
differential testing, and the cost of every survivor is MEASURED by exact operation counts.

Modules:
  algebra      structures (semirings, monoids, ⊗-magmas), element wrappers for injection, property checker
  rewrite      in-memory copies of repository implementations, targeted AST rewrites
  engine       Mutant, differential testing, shrinking, classification, cost fitting (reuses tools/validate.py)
  oracles      generic brute-force oracles over any structure
  targets      the MIRROR and OPSWAP mutants of the 2026-10-06d pilot
  literature   reference list and DOI / arXiv verification (Crossref, DataCite, arXiv APIs)

CLI: python -m mutations --help
"""
