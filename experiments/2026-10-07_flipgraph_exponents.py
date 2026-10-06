"""Experiment (research/2026-10-07_search_flipgraph.md, section "What the ranks mean"): exponents of the recursive
algorithms obtained from k x k x k schemes of rank r, omega_r = log_k(r), compared with Strassen's log2(7).

A rank-r scheme for (k, k, k), valid over a ring R, gives an O(N^(log_k r)) algorithm for N x N matrices over R by
recursive block application (Strassen 1969's argument). A scheme verified only over GF(2) gives this bound in
characteristic 2 only. Pure arithmetic; deterministic.

Run from the repository root:  python experiments/2026-10-07_flipgraph_exponents.py
"""
import math

STRASSEN = math.log2(7)
print(f"Strassen log2(7) = {STRASSEN:.5f}")
for k, ranks in ((2, (8, 7, 6)), (3, (27, 24, 23, 22, 21)), (4, (64, 54, 53, 52, 51, 50, 49, 48, 47, 46))):
    for r in ranks:
        e = math.log(r, k)
        rel = "beats" if e < STRASSEN - 1e-12 else ("equals" if abs(e - STRASSEN) < 1e-12 else "does not beat")
        print(f"k={k} rank {r:2d}: log_{k}({r}) = {e:.5f}  ({rel} log2 7)")
print(f"largest 3x3 rank beating Strassen: {max(r for r in range(1, 28) if math.log(r, 3) < STRASSEN)}")
print(f"largest 4x4 rank beating Strassen: {max(r for r in range(1, 65) if math.log(r, 4) < STRASSEN - 1e-12)}")
