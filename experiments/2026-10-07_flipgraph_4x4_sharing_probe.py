"""Experiment (research/2026-10-07_search_flipgraph.md, sections 5.2 and IDEAS): why do 4x4x4 walks stall?

Measures, along one uncapped walk from the standard algorithm (seed 1, linear reductions, no escapes):
  * the rank and the number of shared (position, value) keys (= groups of >= 2 terms sharing a factor, the only
    places where flips exist) every 250,000 flips up to 3,000,000 flips;
  * at the end: the cost of one lookahead scan and how many of 2,000 consecutive states have a reducing flip;
  * the mean Hamming weight of the factors at start and end.
The same measurement is repeated with weight cap 4 (max_weight=4). Deterministic apart from the timings.

Run from the repository root:  python experiments/2026-10-07_flipgraph_4x4_sharing_probe.py
"""
import random
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from search.flipgraph import FlipGraphState  # noqa: E402
from search.gf2mm import standard_scheme, verify  # noqa: E402
from search.machine import CpuMeter, set_below_normal_priority  # noqa: E402

print("below-normal priority:", set_below_normal_priority())


def mean_weight(st):
    ws = [bin(x).count("1") for t in st.t.values() for x in t]
    return sum(ws) / len(ws)


for cap in (0, 4):
    meter = CpuMeter().start()
    st = FlipGraphState(standard_scheme((4, 4, 4)), random.Random(1), "linear", max_weight=cap)
    line = [f"0:{st.rank}/{len(st.shared)}"]
    w0 = mean_weight(st)
    for k in range(1, 3_000_001):
        st.flip()
        if k % 250_000 == 0:
            line.append(f"{k // 1000}k:{st.rank}/{len(st.shared)}")
    assert verify((4, 4, 4), st.scheme())
    print(f"cap {cap}: (flips:rank/shared keys) " + " ".join(line))
    t = time.perf_counter()
    hits = 0
    for _ in range(2000):
        st.flip()
        if st.reducing_flips(limit=1):
            hits += 1
    dt = time.perf_counter() - t
    print(f"cap {cap}: {hits}/2000 consecutive states have a reducing flip; flip + scan {dt / 2000 * 1e6:.1f} us "
          f"per step; mean factor weight {w0:.2f} at start, {mean_weight(st):.2f} at end; rank {st.rank}; "
          f"rejected proposals {st.n_rejected}; machine {meter.stop()}")
