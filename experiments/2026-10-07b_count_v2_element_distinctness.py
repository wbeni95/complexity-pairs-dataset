"""Count-based V2 for pairs/element-distinctness-pairs-vs-sorting: exact comparison counts and fits.

Question: with comparisons between input values counted by the harness (CountingKey wraps the distinct
values of generate_scaling; the implementations are unchanged), do the counts fit n^2 (all pairs) and
n log n (sort + neighbour scan) tightly enough to reject rivals at log-factor distance?

Cross-checks that do not depend on the counting type's internals:
  * all pairs on distinct input must make exactly n(n-1)/2 equality tests (no early exit);
  * the sorting algorithm's count minus the n - 1 neighbour tests is the bottom-up merge sort's comparison
    count, which must satisfy  sum over merges of min(len_left, len_right) <= C_merge <= sum of
    (len_left + len_right - 1), both computed from the run lengths of the bottom-up passes alone.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_element_distinctness.py
Deterministic (validator seeds).

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  * all pairs: exactly n(n-1)/2 at n = 500..4000; alpha 1.0004 vs n^2; rivals n log n 1.7572, n^2 log n
    0.9356 (rejected at 0.03 and 0.02); diagnostic resolved.
  * sorting: 9710, 21426, 46876, 101729, 219403, 471108, 1006063, 2140632 at n = 1000..128000
    (n log2 n - c n, c = 0.2421-0.2558); merge part within the run-length bounds at every n; alpha 1.0021
    vs n log n; rivals n 1.1113, n log^2 n 0.9123, n^2 0.5557 (rejected); powers of two give alpha 1.0018.
  Written to entry.json: the existing n_values, tolerance 0.03, samples 1.

Check lines (all pairs exactly n(n-1)/2; merge part within the run-length bounds) start with [PASS] or [FAIL]; the
run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The ratios, fits, rivals and
slopes are reported, not checked.
"""
import importlib.util
import math
import sys
from pathlib import Path

_p = Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py"
_s = importlib.util.spec_from_file_location("cv2h", _p)
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

EID = "element-distinctness-pairs-vs-sorting"
ALL, SORT = "all pairs", "sort, then compare neighbours"

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


def merge_bounds(n):
    lo = hi = 0
    width = 1
    while width < n:
        for start in range(0, n, 2 * width):
            a = min(width, n - start)
            b = max(0, min(width, n - start - width))
            if b:
                lo += min(a, b)
                hi += a + b - 1
        width *= 2
    return lo, hi


print("== all pairs (claim n**2) ==")
ap_ns = [500, 1000, 1500, 2000, 3000, 4000]
ap = H.counts(EID, ALL, ap_ns, 1)
ok = all(int(v) == n * (n - 1) // 2 for n, v in zip(ap_ns, ap))
check_line(ok, "  exactly n(n-1)/2:", ok)
for tol in (0.03, 0.02):
    H.report(f"tol={tol}", ap_ns, ap, "n**2", ["n*log(n)", "n**2*log(n)"], tol)

print("\n== sort, then compare neighbours (claim n*log(n)) ==")
for s_ns in ([1000, 2000, 4000, 8000, 16000, 32000, 64000, 128000],
             [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072]):
    sv = H.counts(EID, SORT, s_ns, 1)
    for n, v in zip(s_ns, sv):
        lo, hi = merge_bounds(n)
        cm = v - (n - 1)
        check_line(lo <= cm <= hi,
                   f"  n={n}: {int(v)} (merge part {int(cm)}, bounds [{lo}, {hi}] ok={lo <= cm <= hi}); "
                   f"/(n log2 n) = {v / (n * math.log2(n)):.5f}; (n log2 n - v)/n = {(n * math.log2(n) - v) / n:.4f}")
    for tol in (0.03, 0.05):
        H.report(f"tol={tol}", s_ns, sv, "n*log(n)", ["n", "n*log(n)**2", "n**2"], tol)

finish_checks()

