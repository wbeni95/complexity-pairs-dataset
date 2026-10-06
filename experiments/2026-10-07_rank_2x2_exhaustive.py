"""Experiment (research/2026-10-07_search_flipgraph.md, section "Is rank 7 optimal?"): exhaustive check that
the 2x2x2 matrix multiplication tensor has no rank-6 decomposition over GF(2).

Method (search/lowrank.py): rank(T) <= r iff some r rank-one matrices span a space containing the slice space S;
all candidate subspaces of the quotient by S are enumerated, so the answer is exact.

Steps:
  1. Method validation A: for ALL 4096 tensors of shape 2x2x3 over GF(2), the exact rank computed by an
     independent breadth-first sumset expansion must equal the smallest r with rank_at_most(...) = True.
  2. Method validation B: the same comparison on a seeded random sample of 3000 tensors of shape 2x3x3
     (BFS ranks for all 2^18 tensors).
  3. Positive control: <2,2,2> rank <= 7 must be True, and the witness must give a scheme that passes both exact
     verifiers.
  4. Main question: <2,2,2> rank <= 6, using each of the three slicings (cyclic rotations of the tensor).
Deterministic (seed 20261007 for the sample).

Run from the repository root:  python experiments/2026-10-07_rank_2x2_exhaustive.py
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search import lowrank  # noqa: E402
from search.gf2mm import dims, mm_tensor, verify, verify_explicit  # noqa: E402
from search.machine import CpuMeter, set_below_normal_priority  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tests"))
from test_search_driver import bfs_ranks  # noqa: E402  (independent rank computation)

print("below-normal priority:", set_below_normal_priority())
meter = CpuMeter().start()


def slices_of(t, shape):
    na, nb, nc = shape
    return [(t >> (x * nb * nc)) & ((1 << (nb * nc)) - 1) for x in range(na)]


def exact_rank(slices, nb, nc):
    r = 0
    while not lowrank.rank_at_most(slices, nb, nc, r)[0]:
        r += 1
    return r


for shape, sample in (((2, 2, 3), None), ((2, 3, 3), 3000)):
    t0 = time.perf_counter()
    ranks = bfs_ranks(shape)
    items = sorted(ranks.items())
    if sample:
        items = random.Random(20261007).sample(items, sample)
    mism = sum(exact_rank(slices_of(t, shape), shape[1], shape[2]) != r for t, r in items)
    hist = {}
    for _, r in sorted(ranks.items()):
        hist[r] = hist.get(r, 0) + 1
    print(f"validation {shape}: {len(ranks)} tensors ranked by BFS (rank histogram {hist}); "
          f"compared {len(items)}: {mism} mismatches ({time.perf_counter() - t0:.1f} s)")

T = mm_tensor((2, 2, 2))
ans, witness, stats = lowrank.mm_rank_at_most((2, 2, 2), 7)
terms = lowrank.decomposition_from_witness(T, witness, dims((2, 2, 2))[2])
print(f"positive control <2,2,2> rank <= 7: {ans}; witness gives {len(terms)} terms, verify={verify((2, 2, 2), terms)}, "
      f"verify_explicit={verify_explicit((2, 2, 2), terms)}; stats {stats}")


def rotate(T, shape):
    """Cyclic rotation U(x)V(x)W -> V(x)W(x)U of a tensor given as U-slices (bit y*nc + z)."""
    na, nb, nc = shape
    out = [0] * nb
    for x in range(na):
        for y in range(nb):
            for z in range(nc):
                if (T[x] >> (y * nc + z)) & 1:
                    out[y] |= 1 << (z * na + x)
    return out, (nb, nc, na)


shape = dims((2, 2, 2))
cur = T
for k in range(3):
    t0 = time.perf_counter()
    ans6, _, st6 = lowrank.rank_at_most(cur, shape[1], shape[2], 6)
    print(f"<2,2,2> slicing {k}: rank <= 6 over GF(2)? {ans6}; {st6}; {time.perf_counter() - t0:.2f} s")
    cur, shape = rotate(cur, shape)
print("machine:", meter.stop())
