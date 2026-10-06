"""Count-based V2 for pairs/closest-pair-brute-vs-divide-conquer: exact multiplication counts, fits, rivals.

The harness wraps every coordinate in CountingInt and reports multiplications (a squaring `** 2` counts as
one). Expected: brute force exactly n(n-1) (dx*dx and dy*dy per pair). Divide and conquer splits its count
into three parts, two of which depend on n alone:
  strip filter  S(n) = 0 for n <= 3, else n + S(n // 2) + S(n - n // 2)   (one squaring per point per
                internal node of the recursion);
  base cases    B(n) = 2 for n = 2, 6 for n = 3, else B(n // 2) + B(n - n // 2)   (2 per pair);
  strip scan    the rest (dy^2 per examined pair, plus dx^2 for pairs not stopped at): data-dependent.
The instrumentation must not change the answers: outputs on the counting instance (unwrapped) are compared
with outputs on the same points as plain ints.

Informational only: the comparison counts (tallied separately by the harness), which include the comparisons
made inside CPython's sorted() and min(); these are not used for V2 because they can change between Python
versions.

Run from the repository root:  ./.venv/Scripts/python experiments/2026-10-07b_count_v2_closest_pair.py
Deterministic (validator seeds).

Outcome (run 2026-10-06 local date, Python 3.14.2; deterministic, identical on rerun):
  * answers with CountingInt equal answers with plain ints at n = 2, 3, 4, 7, 50, 300 (both algorithms).
  * brute force: exactly n(n-1) at n = 125..2000; alpha 1.0013; rivals n log n 1.7214, n^2 log n 0.9257.
  * divide and conquer, n = 1000..64000: 14523 ... 1436363 multiplications (1.4057-1.4573 n log2 n); the
    strip filter S(n) is 61.5%-66.5% of the count, the strip scan 28.7%-31.1%; alpha 0.9933; rivals n 1.1054,
    n log^2 n 0.9017, n^2 0.5527; per-sample alpha 0.9933 / 0.9949 / 0.9949 over three seeded samples.
    INFO: comparison counts (incl. CPython's sorted()/min()) give alpha 1.0072; S(n) alone 1.0091.
  Written to entry.json: the existing n_values, tolerance 0.03, samples 1, multiplications only.
"""
import importlib.util
import math
import random
from pathlib import Path

_s = importlib.util.spec_from_file_location("cv2h", Path(__file__).resolve().parent / "2026-10-07b_count_v2_helpers.py")
H = importlib.util.module_from_spec(_s)
_s.loader.exec_module(H)

EID = "closest-pair-brute-vs-divide-conquer"
BR, DC = "all pairs", "Shamos-Hoey divide and conquer"
edir, entry, h = H.entry_and_harness(EID)


def S(n):
    return 0 if n <= 3 else n + S(n // 2) + S(n - n // 2)


def B(n):
    if n == 2:
        return 2
    if n == 3:
        return 6
    return B(n // 2) + B(n - n // 2)


print("== answers unchanged by the instrumentation ==")
for name in (BR, DC):
    fn = H.V.load_callable(edir, H.algorithm(entry, name)["implementation"])
    ok = True
    for n in (2, 3, 4, 7, 50, 300):
        inst = h.generate_scaling(n, random.Random(f"check|{n}"))
        plain = tuple((p[0].v, p[1].v) for p in inst)
        out = fn(inst)
        ok &= out.v == fn(plain)
    print(f"  {name}: equal on n = 2, 3, 4, 7, 50, 300: {ok}")

print("\n== brute force (claim n**2) ==")
ns = [125, 250, 500, 1000, 2000]
v = H.counts(EID, BR, ns, 1)
print("  exactly n(n-1):", all(int(c) == n * (n - 1) for n, c in zip(ns, v)))
H.report("tol=0.03", ns, v, "n**2", ["n*log(n)", "n**2*log(n)"], 0.03)

print("\n== divide and conquer (claim n * log(n)) ==")
fn = H.V.load_callable(edir, H.algorithm(entry, DC)["implementation"])
for ns in ([1000, 2000, 4000, 8000, 16000, 32000, 64000],):
    vals, comps = [], []
    for n in ns:
        rng = random.Random(f"{EID}|v2|{n}")
        inst = h.generate_scaling(n, rng)
        random.seed(f"{EID}|v2|{n}|0|{DC}")
        fn(inst)
        c = h.reported_cost(None)
        vals.append(c)
        comps.append(h._comparisons)
        print(f"  n={n}: mults {c} = strip filter {S(n)} + base {B(n)} + strip scan {c - S(n) - B(n)}; "
              f"/(n log2 n) = {c / (n * math.log2(n)):.4f}; comparisons (info) {h._comparisons}")
    assert vals == H.counts(EID, DC, ns, 1), "helper and inline counts differ"
    H.report("mults, tol=0.03", ns, vals, "n * log(n)", ["n", "n*log(n)**2", "n**2"], 0.03)
    H.report("INFO comparisons, tol=0.03", ns, comps, "n * log(n)", ["n", "n*log(n)**2", "n**2"], 0.03)
    sv = [S(n) for n in ns]
    H.report("INFO strip-filter part S(n) alone", ns, sv, "n * log(n)", ["n", "n*log(n)**2"], 0.03)

print("\n== divide and conquer: sample-to-sample stability (decides samples=1) ==")
ns = [1000, 2000, 4000, 8000, 16000, 32000, 64000]
per = H.counts(EID, DC, ns, 3, per_sample=True)
for k in range(3):
    vk = [p[k] for p in per]
    print(f"  sample {k}: alpha vs n log n = {H.alpha(ns, vk, 'n * log(n)'):.4f}, vs n = {H.alpha(ns, vk, 'n'):.4f}, "
          f"vs n log^2 n = {H.alpha(ns, vk, 'n*log(n)**2'):.4f}")
for n, p in zip(ns, per):
    print(f"  n={n}: {p}, spread/mean = {(max(p) - min(p)) / (sum(p) / 3):.4f}")

