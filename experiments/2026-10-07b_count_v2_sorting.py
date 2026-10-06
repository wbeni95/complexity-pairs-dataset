"""Count-based V2 for pairs/sorting-insertion-vs-merge: exact comparison counts, fits, rivals, log factor.

Question: with comparisons counted by the harness (CountingKey wraps the values of generate(); the
implementations are unchanged), which n_values / samples / tolerance give a fit that (a) passes for the
claimed cost, (b) rejects the named rivals and (c) resolves the log factor (validator diagnostic)?

Also an instrumentation cross-check that does not use the counting type: insertion sort's comparisons
are predicted in closed form from the input alone. For element i let g_i = #{j < i : a_j > a_i}; the
while loop makes g_i comparisons that succeed plus one that fails unless it ran off the left end
(g_i = i). So C = sum_i (g_i + [g_i < i]). Merge sort: counts are checked against the textbook bounds
(n/2) log2 n <= C <= n ceil(log2 n) - 2^ceil(log2 n) + 1 (worst case of top-down merge sort).

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_sorting.py
Deterministic (validator seeds). Outcome: see the docstring block "RESULT" at the bottom, filled in after
the run, and research/2026-10-07b_count_based_v2.md.

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  * instrumentation cross-check: counted = closed form at n = 50, 100, 250, 500 (731, 2990, 15452, 62822).
  * insertion sort, n = 250..4000, mean of 3 samples: 15574.67, 63461.67, 250154.67, 999716.33, 3990076
    (0.997-1.015 x n^2/4); alpha 0.9990 vs n^2; rivals n log n 1.7427, n^2 log n 0.9308 (both rejected at
    0.03 and 0.05); diagnostic resolved. One sample: alpha 0.9989.
    On the OLD timing range n = 100..3200: 3 samples alpha 0.9943; 1 sample alpha 0.9828 with a local slope
    of 0.883 between n = 100 and 200 (sampling noise) -> samples = 3 and n >= 250 were chosen.
  * merge sort, n = 1000..64000: 8701 ... 941409 = n log2 n - c n, c = 1.2523-1.2659; all within the
    textbook bounds; alpha 1.0114 vs n log n; rivals n 1.1255, n log^2 n 0.9182, n^2 0.5628 (rejected);
    powers of two 1024..65536 give 1.0115, n = 4096..262144 gives 1.0082. 3-sample spread <= 0.098% of the
    count; 3-sample mean gives alpha 1.0113 -> samples = 1.
  Written to entry.json: insertion n = 250..4000, samples 3; merge n = 1000..64000; both tolerance 0.03.
"""
import importlib.util
import math
import random
from pathlib import Path

_p = Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py"
_s = importlib.util.spec_from_file_location("cv2h", _p)
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

EID = "sorting-insertion-vs-merge"
_, entry, harness = H.entry_and_harness(EID)


def insertion_closed_form(values):
    c = 0
    for i in range(1, len(values)):
        g = sum(1 for j in range(i) if values[j] > values[i])
        c += g + (1 if g < i else 0)
    return c


def merge_worst_bound(n):
    L = math.ceil(math.log2(n))
    return n * L - 2 ** L + 1


print("== cross-check: insertion sort counts vs closed form (validator seeds, sample 0) ==")
for n in (50, 100, 250, 500):
    rng = random.Random(f"{EID}|v2|{n}")
    vals = harness.generate(n, rng)
    measured = H.counts(EID, "insertion sort", [n], 1)[0]
    print(f"  n={n}: counted {int(measured)}, closed form {insertion_closed_form(vals)}")

print("\n== insertion sort (claim n**2) ==")
ins_ns = [250, 500, 1000, 2000, 4000]
per = H.counts(EID, "insertion sort", ins_ns, 3, per_sample=True)
for n, v in zip(ins_ns, per):
    print(f"  n={n}: samples {v}, mean/(n^2/4) = {sum(v) / 3 / (n * n / 4):.5f}")
means = [sum(v) / 3 for v in per]
for tol in (0.05, 0.03):
    H.report(f"samples=3 tol={tol}", ins_ns, means, "n**2", ["n*log(n)", "n**2*log(n)", "n**3"], tol)
first = [v[0] for v in per]
H.report("samples=1 tol=0.05", ins_ns, first, "n**2", ["n*log(n)"], 0.05)

print("\n== merge sort (claim n*log(n)) ==")
for ms_ns in ([1000, 2000, 4000, 8000, 16000, 32000, 64000],
              [1024, 2048, 4096, 8192, 16384, 32768, 65536],
              [4096, 8192, 16384, 32768, 65536, 131072, 262144]):
    vals = H.counts(EID, "merge sort", ms_ns, 1)
    for n, v in zip(ms_ns, vals):
        lo, hi = n / 2 * math.log2(n), merge_worst_bound(n)
        print(f"  n={n}: {int(v)}  /(n log2 n) = {v / (n * math.log2(n)):.5f}  "
              f"(n log2 n - v)/n = {(n * math.log2(n) - v) / n:.4f}  within bounds: {lo <= v <= hi}")
    for tol in (0.05, 0.03):
        H.report(f"tol={tol}", ms_ns, vals, "n*log(n)", ["n", "n**2", "n*log(n)**2"], tol)

print("\n== merge sort: sample-to-sample variation of the count (decides samples=1 vs 3) ==")
ms_ns = [1000, 2000, 4000, 8000, 16000, 32000, 64000]
per = H.counts(EID, "merge sort", ms_ns, 3, per_sample=True)
for n, v in zip(ms_ns, per):
    print(f"  n={n}: samples {v}, (max-min)/mean = {(max(v) - min(v)) / (sum(v) / 3):.2e}")
H.report("merge sort samples=3 tol=0.03", ms_ns, [sum(v) / 3 for v in per], "n*log(n)",
         ["n", "n*log(n)**2", "n**2"], 0.03)

print("\n== insertion sort on the OLD timing range n = 100..3200 (for comparison only) ==")
old = [100, 200, 400, 800, 1600, 3200]
H.report("samples=3 tol=0.03", old, H.counts(EID, "insertion sort", old, 3), "n**2", ["n*log(n)", "n**2*log(n)"], 0.03)
H.report("samples=1 tol=0.03", old, H.counts(EID, "insertion sort", old, 1), "n**2", ["n*log(n)", "n**2*log(n)"], 0.03)

print("\n== FINAL CONFIGURATION (as written to entry.json) ==")
H.report("insertion sort, samples=3, tol=0.03", ins_ns, H.counts(EID, "insertion sort", ins_ns, 3), "n**2",
         ["n*log(n)", "n**2*log(n)"], 0.03)
H.report("merge sort, samples=1, tol=0.03", ms_ns, H.counts(EID, "merge sort", ms_ns, 1), "n*log(n)",
         ["n", "n*log(n)**2", "n**2"], 0.03)

