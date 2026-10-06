"""Timing probe for pairs/element-distinctness-pairs-vs-sorting on distinct inputs (generate_scaling):
choose n ranges with runtimes between ~0.1 ms and ~300 ms and look at the fits before writing entry.json.
Also fits the merge-sort timings against plain n, to quantify how little the fit can say about the
log factor.

Run from the repository root:  python experiments/2026-10-07_element_distinctness_probe.py

Outcome (2026-10-07, console): all pairs alpha = 1.044 vs n^2 over n = 250..3000 (local slopes 1.13 at the
smallest step, then 0.99..1.04; 80 ms at n = 3000, so entry.json uses 500..4000). Merge sort over
n = 1000..64000: alpha = 1.001 vs n log n, 1.125 vs n (also inside the 0.25 tolerance), 0.558 vs n^2
(rejected). So V2 confirms near-linear growth for the sorting algorithm but cannot isolate the log factor.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "element-distinctness-pairs-vs-sorting"
ns = [250, 500, 1000, 1500, 2000, 3000]
a, t = ph.probe(E, "implementations/all_pairs.py:distinct_all_pairs", "generate_scaling", "n**2", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**2")])
ns = [1000, 2000, 4000, 8000, 16000, 32000, 64000]
a, t = ph.probe(E, "implementations/sort_adjacent.py:distinct_by_sorting", "generate_scaling", "n*log(n)", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n*log(n)")])
ph.probe(E, "implementations/sort_adjacent.py:distinct_by_sorting", "generate_scaling", "n", ns, label="merge sort vs plain n")
ph.probe(E, "implementations/sort_adjacent.py:distinct_by_sorting", "generate_scaling", "n**2", ns, label="merge sort vs n**2 (should fail)")
