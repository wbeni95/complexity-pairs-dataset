"""Diagnostic (research/2026-10-06c_kernel_deadends.md): after the new kernel escapes a dead end, does it come back to
the same dead end, or does it reach new ones?

Uses the line-by-line Python mirror (search/kernel_reference.py, identical trajectories to search/kernel/flipwalk.rs
by the differential tests) with its test-only on_dead_end hook. Start: Strassen (x) Strassen for 4x4x4 (rank 49, no
two terms share a factor). Seeds 1-4, 200 000 steps each, plateau 50 000, slack 3, no weight cap, escape on.
At every detection it records the scheme as a sorted tuple of terms (exact identity, not equivalence) and its rank.
Prints: detections, distinct dead ends, how many detections were at the start scheme itself, the rank distribution
of the dead ends, and the best rank. Single process, a few seconds; run after the 8-process main run had finished.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-06c_deadend_revisits.py
RESULT (2026-10-06, after the main run, 3.1 s): every detection was at rank 49 and the best rank stayed 49.
seed 1: 214 detections, 11 distinct dead ends (32 at S(x)S itself, the most visited one 54 times);
seed 2: 242, 10 (4, 40); seed 3: 141, 11 (3, 34); seed 4: 72, 2 (16, 56).
The escape keeps returning to a handful of rank-49 dead ends.
"""
import collections
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, kernel_reference as kr  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    s = gf2mm.strassen_scheme()
    _, ss = gf2mm.kron_scheme((2, 2, 2), s, (2, 2, 2), s)
    ss_key = tuple(sorted(tuple(t) for t in ss))
    for seed in (1, 2, 3, 4):
        seen = collections.Counter()
        ranks = collections.Counter()

        def hook(terms, best_rank):
            seen[tuple(sorted(tuple(t) for t in terms))] += 1
            ranks[len(terms)] += 1

        res = kr.walk(ss, seed, 200_000, plateau=50_000, slack=3, dead_end=True, on_dead_end=hook)
        assert gf2mm.verify((4, 4, 4), res["best"])
        total = sum(seen.values())
        print(f"seed {seed}: {total} detections, {len(seen)} distinct dead ends, {seen[ss_key]} at the start S(x)S, "
              f"most visited {max(seen.values()) if seen else 0}x, ranks {dict(sorted(ranks.items()))}, "
              f"flips {res['flips']}, plus {res['plus']}, restarts {res['restarts']}, best rank {len(res['best'])}",
              flush=True)
    print(f"{time.time() - t0:.1f} s")
