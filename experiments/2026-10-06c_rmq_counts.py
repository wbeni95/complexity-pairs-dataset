"""Exact comparison counts for pairs/range-minimum-queries-naive-vs-sparse-table (count-based V2, round 2026-10-06c).

What it tries:
  1. Whether CPython's two-argument min(x, y) calls __lt__ exactly once (it must, for the sparse table's
     preprocessing comparisons to be visible to an instrumented value type).
  2. Whether the UNCHANGED implementations return the same minima on CountingKey values as on plain ints
     (scaling instances, and 300 random generate() instances wrapped value by value).
  3. Whether the harness counts equal closed forms computed from the instance alone:
       scan:         sum over queries of (r - l)              (one `x < m` per scanned element after the first)
       sparse table: sum_{j=1..K} (n - 2^j + 1) + q,  K = floor(log2 n), q = n
                     (one comparison inside each min() of the table build, one `a <= b` per query);
                     for n = 2^K this is n log2 n - n + log2 n + 2.
  4. The fits (validator's eval_cost / fit_slope) for candidate n ranges, claims and rivals.

Run from the repository root:  PYTHONIOENCODING=utf-8 ./.venv/Scripts/python experiments/2026-10-06c_rmq_counts.py
Deterministic (seeded generators; exact counts).

Outcome (run 2026-10-06, Python 3.14.2; the same counts under 3.12.10 via 2026-10-06c_count_v2_summary.py):
  1. min(x, y) on two counting values makes exactly 1 __lt__ call (and min(x, y, z) makes 2).
  2. Identical minima in every case checked.
  3. Closed forms hold exactly at every n checked (scan: n = 50..3200; sparse table: 9 non-powers of two and
     2^11..2^17).
  4. Scan, n = 200..3200 (unchanged n_values), against n**2: alpha 1.0014; counts / n^2 = 0.7385..0.7563;
     rivals n*log(n) 1.7406, n**2*log(n) 0.9312, n**3 0.6676, all rejected at tolerance 0.03; local slopes
     0.981..1.017.
     Sparse table, n = 2000..128000 (unchanged n_values), against the leading term n*log(n): alpha 1.0073;
     rivals n 1.1126, n*log(n)**2 0.9202, n**2 0.5563, all rejected. On n = 2^11..2^17 the leading term gives
     1.0074 and the exact form n*log2(n) - n + log2(n) + 2 gives 1.0000, with the same rival verdicts.
     CHOSEN: unchanged n_values, leading terms n**2 and n*log(n) (deviations 0.0014 and 0.0073 are under
     a third of the tolerance, so the exact form was not needed; it is stated in the entry text instead).
  (A first draft of this docstring, written before the run, guessed alpha 1.022 for the leading term on the
  old n; the run gave 1.0073. The guess was replaced by the measured value.)

Check lines (every min() line of 1: one __lt__ call per argument after the first; 2; both lines of 3) start with
[PASS] or [FAIL]; the run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The
ratios and the fits (4) are reported, not checked.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

E = "range-minimum-queries-naive-vs-sparse-table"
entry_dir, entry, harness = H.entry_and_harness(E)
naive = H.V.load_callable(entry_dir, "implementations/naive_scan.py:rmq_naive")
sparse = H.V.load_callable(entry_dir, "implementations/sparse_table.py:rmq_sparse_table")
CK = harness.CountingKey

FAILED = []


def check_line(ok, *parts):
    """Print one check line with a [PASS] or [FAIL] prefix and remember the failures."""
    print("[PASS]" if ok else "[FAIL]", *parts, flush=True)
    if not ok:
        FAILED.append(" ".join(str(p) for p in parts).strip())
    return ok


def finish_checks():
    """End of the run: ALL CHECKS PASSED (exit code 0), or the failed checks and exit code 1."""
    if FAILED:
        print(f"FAILED: {len(FAILED)} check(s):")
        for label in FAILED:
            print(f"  {label}")
        sys.exit(1)
    print("ALL CHECKS PASSED")

# 1. min() and __lt__
for args in [(CK(3), CK(5)), (CK(5), CK(3)), (CK(4), CK(4)), (CK(1), CK(2), CK(0))]:
    harness._comparisons = 0
    m = min(*args)
    check_line(harness._comparisons == len(args) - 1,
               f"min of {[a.v for a in args]} -> {m.v}; comparisons counted = {harness._comparisons}")


def unwrap(t):
    return tuple(x.v if isinstance(x, CK) else x for x in t)


# 2. answers unchanged
differs = []
for n in [1, 2, 3, 7, 50, 300, 1000]:
    vals, qs = harness._scaling_draws(n, random.Random(f"rmq-eq|{n}"))
    cvals = tuple(CK(x) for x in vals)
    for fn in (naive, sparse):
        if unwrap(fn((cvals, qs))) != fn((vals, qs)):
            differs.append((n, fn.__name__))
rng = random.Random("rmq-eq-random")
for t in range(300):
    n = rng.randrange(1, 60)
    vals, qs = harness.generate(n, rng)
    cvals = tuple(CK(x) for x in vals)
    for fn in (naive, sparse):
        if unwrap(fn((cvals, qs))) != fn((vals, qs)):
            differs.append((t, n, fn.__name__))
check_line(not differs, "answers on CountingKey values == answers on plain ints: "
           + ("OK" if not differs else f"DIFFER at {differs[:5]}") + " (7 scaling + 300 random instances)")


# 3. closed forms from the instance alone
def scan_closed(qs):
    return sum(r - l for l, r in qs)


def sparse_closed(n):
    K = n.bit_length() - 1
    return sum(n - (1 << j) + 1 for j in range(1, K + 1)) + n


def measured(fn, n):
    rng = random.Random(f"{E}|v2|{n}")
    inst = harness.generate_scaling(n, rng)
    random.seed(f"{E}|v2|{n}|0|x")
    return harness.reported_cost(fn(inst)), inst


bad = []
for n in [50, 200, 400, 600, 800, 1200, 1600, 2400, 3200]:
    c, inst = measured(naive, n)
    if c != scan_closed(inst[1]):
        bad.append(n)
check_line(not bad, "scan count == sum(r - l): " + ("OK" if not bad else f"MISMATCH at n = {bad}") + " at n = 50..3200")
bad = []
for n in [10, 100, 1000, 2000, 4000, 8000, 16000, 64000, 128000] + [1 << k for k in range(11, 18)]:
    c, inst = measured(sparse, n)
    if c != sparse_closed(n):
        bad.append((n, c, sparse_closed(n)))
    if n & (n - 1) == 0:
        K = n.bit_length() - 1
        if c != n * K - n + K + 2:
            bad.append((n, c, n * K - n + K + 2))
check_line(not bad, "sparse count == sum_j (n - 2^j + 1) + n: " + ("OK" if not bad else f"MISMATCH {bad[:5]}")
           + " (9 non-powers of two, 2^11..2^17; = n log2 n - n + log2 n + 2 on powers of two)")

# 4. fits
TOL = 0.03
ns = [200, 400, 600, 800, 1200, 1600, 2400, 3200]
vals = H.counts(E, "scan each range", ns)
print("\nscan, counts / n^2:", [round(v / n ** 2, 4) for n, v in zip(ns, vals)])
H.report("scan vs n**2", ns, vals, "n**2", ["n*log(n)", "n**2*log(n)", "n**3"], TOL)

ns_old = [2000, 4000, 8000, 16000, 32000, 64000, 128000]
vals_old = H.counts(E, "sparse table", ns_old)
H.report("sparse table, old n, leading term", ns_old, vals_old, "n*log(n)", ["n", "n*log(n)**2", "n**2"], TOL)

ns_p2 = [1 << k for k in range(11, 18)]
vals_p2 = H.counts(E, "sparse table", ns_p2)
H.report("sparse table, powers of two, leading term", ns_p2, vals_p2, "n*log(n)", ["n", "n*log(n)**2", "n**2"], TOL)
H.report("sparse table, powers of two, exact form", ns_p2, vals_p2, "n*log2(n) - n + log2(n) + 2",
         ["n", "n*log(n)**2", "n**2"], TOL)

finish_checks()
