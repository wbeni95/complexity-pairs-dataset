"""Count-based V2 for pairs/inversion-counting-quadratic-vs-merge and pairs/longest-increasing-subsequence.

Question: with element comparisons counted by the harness (CountingKey; implementations unchanged), do the
exact counts fit the claimed costs tightly enough to reject rivals at log-factor (or factor-n) distance?

Closed forms checked against the counts (they use only n, not the counting type):
  inversions, all pairs: n(n-1)/2 (one `>` per pair i < j).
  LIS on the strictly increasing scaling input:
    subset enumeration: sum over masks of max(popcount - 1, 0) = n 2^(n-1) - 2^n + 1;
    quadratic DP: n(n-1)/2;
    patience sorting: the binary search over s tails with every tail < x runs floor(log2(s + 1)) times,
    so the total is sum_{s=1..n-1} floor(log2(s + 1)) = sum_{j=2..n} floor(log2 j).
Merge-sort counting has no closed form on random input; its counts are checked against the merge bounds
sum of min(left, right) <= C <= sum of (left + right - 1) over the merges of the top-down recursion.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_inversions_lis.py
Deterministic (validator seeds).

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  every closed form above matched the counts exactly.
  * inversions, all pairs: n = 250..2000, alpha 1.0008; rivals n log n 1.7353, n^2 log n 0.9295.
  * inversions, merge-sort counting: n = 2000..64000, 19421 ... 941126 (c = 1.2553-1.2668), all within the
    merge bounds, 3-sample spread <= 0.11%; alpha 1.0101; rivals n 1.1194, n log^2 n 0.9203, n^2 0.5597.
  * LIS subset enumeration: n = 10..16 alpha 1.0191 (rivals 2^n 1.1337, 2^n n^2 0.9254; diagnostic NOT
    resolved, 0.9800); n = 12..18 alpha 1.0140 (1.1125, 0.9314; diagnostic 0.9816, NOT resolved); n = 14..20
    alpha 1.0107.
  * LIS quadratic DP: n = 100..1600, alpha 1.0016; rivals n log n 1.7127, n^2 log n 0.9233.
  * LIS patience: n = 1000..100000 alpha 1.0185 (c = 1.91-1.98, sawtooth from floor(log2)); n = 10000..300000
    alpha 1.0120; rivals n 1.1055, n log^2 n 0.9331, n^2 0.5527.
  Written to entry.json: inversions as measured; LIS subset n = 12..18, DP n = 100..1600, patience
  n = 10000..300000; all tolerance 0.03.

Check lines (exact counts and closed forms; merge-sort counts within the merge bounds) start with [PASS] or [FAIL];
the run ends with ALL CHECKS PASSED (exit code 0) or lists the failed checks (exit code 1). The ratios, spreads,
fits, rivals and slopes are reported, not checked.
"""
import importlib.util
import math
import sys
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

INV = "inversion-counting-quadratic-vs-merge"
LIS = "longest-increasing-subsequence"

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


def topdown_merge_bounds(n):
    if n <= 1:
        return 0, 0
    mid = n // 2
    l1, h1 = topdown_merge_bounds(mid)
    l2, h2 = topdown_merge_bounds(n - mid)
    return l1 + l2 + min(mid, n - mid), h1 + h2 + n - 1


print("== inversions: all pairs (claim n**2) ==")
ns = [250, 500, 750, 1000, 1500, 2000]
v = H.counts(INV, "all pairs", ns, 1)
ok = all(int(c) == n * (n - 1) // 2 for n, c in zip(ns, v))
check_line(ok, "  exactly n(n-1)/2:", ok)
H.report("tol=0.03", ns, v, "n**2", ["n*log(n)", "n**2*log(n)"], 0.03)

print("\n== inversions: merge-sort counting (claim n*log(n)) ==")
ns = [2000, 4000, 8000, 16000, 32000, 64000]
per = H.counts(INV, "merge-sort counting", ns, 3, per_sample=True)
for n, c in zip(ns, per):
    lo, hi = topdown_merge_bounds(n)
    within = all(lo <= x <= hi for x in c)
    check_line(within, f"  n={n}: samples {c}, within bounds [{lo}, {hi}]: {within}, "
                       f"(n log2 n - c0)/n = {(n * math.log2(n) - c[0]) / n:.4f}, "
                       f"spread/mean = {(max(c) - min(c)) / (sum(c) / 3):.1e}")
v = [c[0] for c in per]
H.report("samples=1 tol=0.03", ns, v, "n * log(n)", ["n", "n*log(n)**2", "n**2"], 0.03)

print("\n== LIS: subset enumeration (claim 2**n * n) ==")
for ns in ([10, 11, 12, 13, 14, 15, 16],):
    v = H.counts(LIS, "subset enumeration", ns, 1)
    ok = all(int(c) == n * 2 ** (n - 1) - 2 ** n + 1 for n, c in zip(ns, v))
    check_line(ok, "  closed form n 2^(n-1) - 2^n + 1:", ok)
    H.report("tol=0.03", ns, v, "2**n * n", ["2**n", "2**n * n**2"], 0.03)
# The closed form is exact, so other ranges can be evaluated without running the enumeration:
for ns in ([12, 13, 14, 15, 16, 17, 18], [14, 15, 16, 17, 18, 19, 20]):
    v = [n * 2 ** (n - 1) - 2 ** n + 1 for n in ns]
    H.report("closed form, tol=0.03", ns, v, "2**n * n", ["2**n", "2**n * n**2"], 0.03)

print("\n== LIS: quadratic DP (claim n**2) ==")
ns = [100, 200, 400, 800, 1600]
v = H.counts(LIS, "quadratic dynamic programming", ns, 1)
ok = all(int(c) == n * (n - 1) // 2 for n, c in zip(ns, v))
check_line(ok, "  exactly n(n-1)/2:", ok)
H.report("tol=0.03", ns, v, "n**2", ["n*log(n)", "n**2*log(n)"], 0.03)

print("\n== LIS: patience sorting (claim n*log(n)) ==")
for ns in ([1000, 3000, 10000, 30000, 100000], [10000, 30000, 100000, 300000]):
    v = H.counts(LIS, "patience sorting with binary search", ns, 1)
    cf = [sum(int(math.log2(j)) for j in range(2, n + 1)) for n in ns]
    ok = [int(c) for c in v] == cf
    check_line(ok, "  closed form sum floor(log2 j):", ok)
    for n, c in zip(ns, v):
        print(f"    n={n}: {int(c)}, (n log2 n - c)/n = {(n * math.log2(n) - c) / n:.4f}")
    H.report("tol=0.03", ns, v, "n*log(n)", ["n", "n*log(n)**2", "n**2"], 0.03)

finish_checks()

