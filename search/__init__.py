"""Search environment for the complexity-pairs dataset.

Modules:
  gf2mm      matrix multiplication tensors and schemes over GF(2); exact verifiers; known schemes; JSON I/O
  flipgraph  flip-graph moves (flips, reductions, plus transitions); the flip graph is due to Kauers & Moosbauer (ISSAC 2023)
  driver     seeded, budgeted random walks with plateau escapes, logging and periodic exact verification
  machine    below-normal process priority and machine-load measurement
  lowrank    exhaustive GF(2) rank test for very small tensors (used to check that <2,2,2> has no rank-6 scheme)
  sortnet    sorting networks: exact 0-1-principle verifier and a small randomized search (second target)

Command line (run from the repository root):
  python -m search flip --format 3 3 3 --seed 1 --max-flips 2000000 --plateau 50000 --save-dir <dir>
  python -m search verify search/schemes/<file>.json
  python -m search sortnet --n 6 --seed 1 --tries 2000
New formats need nothing but --format n m p: the standard algorithm of rank n*m*p is the start scheme
(or pass --start <scheme.json> to continue from a saved scheme).
"""
