"""Timing probe for pairs/all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall: which n ranges give
runtimes between ~0.1 ms and ~300 ms on complete digraphs, and do the fits look right before the V2
claim is written into entry.json?

Bellman-Ford from every source makes n(n-1) passes over m = n(n-1) edges: cost n^2 (n-1)^2 relaxations.
Floyd-Warshall makes exactly n^3 relaxation steps.

Outcome (2026-10-07, console; timings vary between runs):
  round 1: Bellman-Ford alpha = 0.975 vs n^2 (n-1)^2 and 1.021 vs n^4 over n = 6..24, but only 9.5 ms at
           n = 24; Floyd-Warshall alpha = 0.909 vs n^3 over n = 16..128.
  round 2: Bellman-Ford alpha = 0.972 over n = 8..40 (0.11 ms .. 71 ms), local slopes 0.93..1.02;
           Floyd-Warshall alpha = 0.918 over n = 32..200 (1.04 ms .. 165 ms), local slopes rising from
           0.90 to 0.97 with n (lower-order Theta(n^2) loop overhead at small n).
  Round-2 ranges were written into entry.json.

Run from the repository root:  python experiments/2026-10-07_apsp_timing_probe.py
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall"
print("Bellman-Ford x n, complete digraphs")
ph.probe(E, "implementations/bellman_ford.py:apsp_bellman_ford", "generate_scaling",
         "n**2 * (n-1)**2", [6, 8, 10, 13, 16, 20, 24])
ph.probe(E, "implementations/bellman_ford.py:apsp_bellman_ford", "generate_scaling",
         "n**4", [6, 8, 10, 13, 16, 20, 24], label="same timings vs n**4")
print("Floyd-Warshall, complete digraphs")
ph.probe(E, "implementations/floyd_warshall.py:apsp_floyd_warshall", "generate_scaling",
         "n**3", [16, 24, 32, 48, 64, 96, 128])

# Second round (after the first showed Bellman-Ford at only 9.5 ms for n = 24 and Floyd-Warshall at
# alpha = 0.909 over n = 16..128, i.e. lower-order overhead at small n): larger n for both.
print("Second round")
ns = [8, 10, 13, 16, 20, 25, 32, 40]
a, t = ph.probe(E, "implementations/bellman_ford.py:apsp_bellman_ford", "generate_scaling", "n**2 * (n-1)**2", ns)
print("  local slopes:", [round(s, 3) for s in ph.local_slopes(ns, t, "n**2 * (n-1)**2")])
ns = [32, 48, 64, 96, 128, 160, 200]
a, t = ph.probe(E, "implementations/floyd_warshall.py:apsp_floyd_warshall", "generate_scaling", "n**3", ns)
print("  local slopes:", [round(s, 3) for s in ph.local_slopes(ns, t, "n**3")])
