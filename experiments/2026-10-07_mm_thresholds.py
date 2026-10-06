#!/usr/bin/env python3
"""Rank thresholds a small matrix-multiplication scheme must beat to matter asymptotically (2026-10-07).

Question: a bilinear scheme for n x n matrix multiplication with r multiplications, applied recursively, gives
omega <= log_n r (START_HERE / CONTRIBUTING: "a fixed-size scheme that yields an asymptotic bound when applied
recursively is in scope through that bound"). For each small n, what is the largest r that would beat
  (a) Strassen's exponent log2 7 (the dataset's T3 entry),
  (b) the GF(2) exponent log4 47 from AlphaTensor's rank-47 4x4 scheme (cited in the Strassen entry),
  (c) the current upper bound omega < 2.371339 (Alman et al., arXiv 2404.16349, cited in the Strassen entry),
and how do these compare with the trivial lower bound r >= n^2 (the n^2 x n^2 flattening of the matrix
multiplication tensor has full rank) and with the best ranks that are verifiable from cited titles
(Strassen 7 for n = 2; Laderman 23 for n = 3, title "... 3x3 matrices using 23 multiplications"; 49 = 7^2 for
n = 4 from Strassen applied to 2 x 2 blocks; 47 for n = 4 over GF(2), AlphaTensor)?

Method: exact arithmetic on logarithms (math.log); r_max(target) = the largest integer r with log(r)/log(n) <
target. Deterministic, no randomness.

Result (run 2026-10-07): printed table. log_3 22 = 2.8136 > log2 7 = 2.8074, so a 3x3 scheme of rank 22 (the
target of the parallel flip-graph search) would be a new record rank but would not improve on Strassen's
exponent; rank 21 (log_3 21 = 2.7712) would. Key lines: n = 3 needs r <= 21 to beat log2 7 (best known 23, so
log_3 23 = 2.854 does not beat Strassen) and r <= 13 to beat 2.371339; n = 4 needs r <= 48 to beat log2 7 and
r <= 26 to beat 2.371339 (best known 47 over GF(2), 49 in general from Strassen squared); n = 2 would need
r <= 6 (rank 7 for 2 x 2 is optimal by Winograd 1971 / Hopcroft-Kerr 1971: titles verified, statement recalled).
The column "(5/2)n^2 - 3n" is Blaser's lower bound AS RECALLED (the 1999 FOCS title, verified, states a 5/2 n^2
lower bound; the exact lower-order term is not verified here). IF it is right, it exceeds the 2.371339 threshold
for n = 3..7 (13.5 > 13, 28 > 26, 47.5 > 45, 72 > 70, 101.5 > 100), so no square format below 8 x 8 could improve
omega; at n = 8 it gives 136 <= 138. This comparison is conditional and only indicative.
"""
from __future__ import annotations

import math
import sys

TARGETS = [("log2 7 (Strassen)", math.log(7, 2)),
           ("log4 47 (AlphaTensor, GF(2))", math.log(47, 4)),
           ("2.371339 (Alman et al. bound)", 2.371339)]
KNOWN = {2: "7 (Strassen)", 3: "23 (Laderman)", 4: "49 = 7^2 (Strassen on blocks); 47 over GF(2) (AlphaTensor)"}


def r_max(n: int, target: float) -> int:
    r = math.floor(n ** target)
    while r > 0 and math.log(r) / math.log(n) >= target:
        r -= 1
    return r


def main() -> int:
    print(f"{'n':>2} {'n^2':>5} {'(5/2)n^2-3n':>12}  " + "  ".join(f"r_max < {name:<28}" for name, _ in TARGETS)
          + "  best verifiable rank")
    for n in range(2, 9):
        bl = 2.5 * n * n - 3 * n
        cells = "  ".join(f"{r_max(n, t):>8} (n^t={n ** t:7.2f})        " for _, t in TARGETS)
        print(f"{n:>2} {n * n:>5} {bl:>12.1f}  {cells}  {KNOWN.get(n, '-')}")
    print(f"\nlog_3 23 = {math.log(23, 3):.4f}; log2 7 = {math.log(7, 2):.4f}; log4 47 = {math.log(47, 4):.4f}; "
          f"log4 49 = {math.log(49, 4):.4f}")
    print(f"log_3 22 = {math.log(22, 3):.4f} (a rank-22 3x3 scheme would be a record rank but would NOT beat log2 7); "
          f"log_3 21 = {math.log(21, 3):.4f}; log4 46 = {math.log(46, 4):.4f}; log4 48 = {math.log(48, 4):.4f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
