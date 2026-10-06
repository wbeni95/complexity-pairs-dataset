"""Timing probe for pairs/range-minimum-queries-naive-vs-sparse-table on the long-query family
(generate_scaling: q = n queries, each of length > n/2): choose n ranges and look at the fits before
writing entry.json. Also fits the sparse-table timings against plain n to see whether the log factor
can be resolved.

Run from the repository root:  python experiments/2026-10-07_rmq_probe.py

Outcome (2026-10-07, console): scan alpha = 1.029 vs n^2 over n = 200..2400, but with local slopes 1.398
(800 -> 1200) and 0.495 (1200 -> 1600): n = 1200 took 21.4 ms. Two immediate re-runs gave 17.0 and 16.2 ms
at n = 1200 (alpha 1.013 and 1.009, local slopes 0.96..1.06), so the first value was a contention spike
(other agents share the machine). The total scanned length of the generated queries is 0.7475 / 0.7531 /
0.7496 n^2 at n = 800 / 1200 / 1600 (deterministic). Sparse table over n = 2000..128000: alpha = 0.989 vs
n log n and 1.100 vs n, so the log factor is not resolvable.
"""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "range-minimum-queries-naive-vs-sparse-table"
ns = [200, 400, 600, 800, 1200, 1600, 2400]
a, t = ph.probe(E, "implementations/naive_scan.py:rmq_naive", "generate_scaling", "n**2", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**2")])
ns = [2000, 4000, 8000, 16000, 32000, 64000, 128000]
a, t = ph.probe(E, "implementations/sparse_table.py:rmq_sparse_table", "generate_scaling", "n*log(n)", ns)
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n*log(n)")])
ph.probe(E, "implementations/sparse_table.py:rmq_sparse_table", "generate_scaling", "n", ns, label="sparse table vs plain n")

# Recheck after the first run showed a local-slope jump at n = 1200 (run inline at first, kept here):
# deterministic total scanned length of the generated queries, then two more timing runs.
import random  # noqa: E402

H = ph.harness_of(E)
for n in [800, 1200, 1600]:
    v, q = H.generate_scaling(n, random.Random(f"probe|{n}"))
    tot = sum(r - l + 1 for l, r in q)
    print(n, "total scanned", tot, "ratio to n^2", round(tot / n ** 2, 4))
ns = [200, 400, 600, 800, 1200, 1600, 2400]
for rep in range(2):
    a, t = ph.probe(E, "implementations/naive_scan.py:rmq_naive", "generate_scaling", "n**2", ns)
    print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n**2")])
