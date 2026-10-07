"""Cross-check of the exact closed-form operation counts of the count-based entries.

Every count is measured on the UNCHANGED implementation with the entry's own harness counter, seeded exactly as
tools/validate.py seeds a V2 run (instance rng "<id>|v2|<n>", algorithm seed "<id>|v2|<n>|0|<algorithm name>").
Each formula is the one proved in pairs/<slug>/PROOFS.md; the script only
compares, it derives nothing. Sizes: the entry's V2 sizes plus extra sizes (0, 1, 2, non-powers of two, sizes above
the V2 range where affordable). Component checks (failure table vs scan, build vs scan, per operation kind, ...)
read the harness's own per-kind tallies or attribute counted operations to the calling function / source line at
run time (wrappers installed in memory around the harness counter methods; no file is modified).

Usage:  python experiments/2026-10-07_closed_form_checks.py [group ...]
        groups: strings sorting algebra expdp query extra   (default: all)
Output: one line per (formula, size range) with the mismatches; a summary per group; exit code 0.
"""
from __future__ import annotations

import inspect
import itertools
import json
import math
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from search.machine import set_below_normal_priority  # noqa: E402
from tools.validate import load_callable, load_module, resolve_in_repo  # noqa: E402

PAIRS = REPO / "pairs"
RESULTS = []          # (group, label, status, detail)


# ----------------------------------------------------------------------------------------------------------------
# Loading and measuring
# ----------------------------------------------------------------------------------------------------------------

def entry_of(eid):
    return json.loads((PAIRS / eid / "entry.json").read_text(encoding="utf-8"))


def harness_of(eid):
    e = entry_of(eid)
    return load_module(resolve_in_repo(PAIRS / eid, e["test_harness"]["module"]))


def alg_name(eid, impl):
    for a in entry_of(eid)["algorithms"]:
        if a.get("implementation") == impl:
            return a["name"]
    raise KeyError(impl)


def measure(eid, impl, n, gen=None, cost=None, seed_n=None):
    """Exact count at size n, seeded as tools/validate.py seeds V2 (sample 0)."""
    h = harness_of(eid)
    fn = load_callable(PAIRS / eid, impl)
    sn = n if seed_n is None else seed_n
    rng = random.Random(f"{eid}|v2|{sn}")
    inst = (gen or getattr(h, "generate_scaling", h.generate))(n, rng)
    random.seed(f"{eid}|v2|{sn}|0|{alg_name(eid, impl)}")
    out = fn(inst)
    return h.reported_cost(out) if cost is None else cost(out)


def record(group, label, ns, mism, domain_note, extra=""):
    status = "OK" if not mism else "MISMATCH"
    shown = ", ".join(f"n={n}: count {a} vs formula {f}" for n, a, f in mism[:8])
    if len(mism) > 8:
        shown += f", ... ({len(mism)} in all)"
    detail = f"sizes {compact(ns)}" + (f" | {shown}" if mism else "") + (f" | {domain_note}" if domain_note else "") \
        + (f" | {extra}" if extra else "")
    RESULTS.append((group, label, status, detail))
    print(f"[{group}] {status:8s} {label}: {detail}", flush=True)


def compact(ns):
    ns = list(ns)
    if len(ns) <= 12:
        return ",".join(map(str, ns))
    return ",".join(map(str, ns[:6])) + ",...," + ",".join(map(str, ns[-4:])) + f" ({len(ns)} sizes)"


def check(group, eid, impl, label, formula, ns, domain=lambda n: True, gen=None, cost=None):
    """Compare the measured count with formula(n) for every n; mismatches inside the claimed domain are failures,
    mismatches outside it are reported as such (they mark where the closed form stops holding)."""
    mism_in, mism_out, errors = [], [], []
    for n in ns:
        try:
            a = measure(eid, impl, n, gen=gen, cost=cost)
        except Exception as ex:  # noqa: BLE001 -- e.g. a generator that is undefined at this n
            errors.append(f"n={n}: {type(ex).__name__}")
            continue
        try:
            f = formula(n)
        except (ZeroDivisionError, ValueError, OverflowError) as ex:
            f = f"undefined ({type(ex).__name__})"
        if a != f:
            (mism_in if domain(n) else mism_out).append((n, a, f))
    note = []
    if mism_out:
        note.append("outside the domain: " + "; ".join(f"n={n}: {a} vs {f}" for n, a, f in mism_out[:6]))
    if errors:
        note.append("not measurable: " + ", ".join(errors[:6]))
    record(group, label, ns, mism_in, " / ".join(note))
    return mism_in, mism_out


# ----------------------------------------------------------------------------------------------------------------
# Small helpers
# ----------------------------------------------------------------------------------------------------------------

def C(a, b):
    return math.comb(a, b) if 0 <= b <= a else 0


def P2(e):
    """2**e as an exact Fraction for any integer e."""
    return F(2) ** e


def fib(k):
    a, b = 0, 1
    for _ in range(k):
        a, b = b, a + b
    return a


def lucas(k):
    a, b = 2, 1
    for _ in range(k):
        a, b = b, a + b
    return a


def ilog2(n):
    return n.bit_length() - 1


def is_pow2(n):
    return n >= 1 and n & (n - 1) == 0


class CallCounter:
    """Counts Python-level calls of functions with a given code name (sys.setprofile)."""

    def __init__(self, name):
        self.name, self.calls = name, 0

    def __enter__(self):
        def prof(frame, event, arg):
            if event == "call" and frame.f_code.co_name == self.name:
                self.calls += 1
        sys.setprofile(prof)
        return self

    def __exit__(self, *exc):
        sys.setprofile(None)


# ----------------------------------------------------------------------------------------------------------------
# Group: strings
# ----------------------------------------------------------------------------------------------------------------

def group_strings():
    g = "strings"
    E = "string-matching-naive-vs-kmp"
    small = list(range(0, 41))
    v2n = [200, 400, 800, 1600, 3200]
    v2k = [3000, 10000, 30000, 100000, 300000]

    def M(n):  # actual pattern length produced by generate_scaling: a^(m-1) b with m = n // 2 ('b' when m = 0)
        return max(n // 2, 1)
    check(g, E, "implementations/naive.py:count_naive", "KMP-entry naive (n-m+1)m, m=n//2",
          lambda n: (n - n // 2 + 1) * (n // 2), small + v2n, domain=lambda n: n >= 2)
    check(g, E, "implementations/naive.py:count_naive", "KMP-entry naive (n-M+1)M, M=len(P)=max(n//2,1)",
          lambda n: (n - M(n) + 1) * M(n), small + v2n)
    check(g, E, "implementations/kmp.py:count_kmp", "KMP 3n+2m-6, m=n//2",
          lambda n: 3 * n + 2 * (n // 2) - 6, small + v2k, domain=lambda n: n >= 6)
    check(g, E, "implementations/kmp.py:count_kmp", "KMP 4n-6-[n odd] (corrected form, n>=6)",
          lambda n: 4 * n - 6 - (n % 2), small + v2k, domain=lambda n: n >= 6)
    check(g, E, "implementations/kmp.py:count_kmp", "KMP small-n forms: n (n<=3), 2n (n=4,5)",
          lambda n: n if n <= 3 else (2 * n if n <= 5 else 3 * n + 2 * (n // 2) - 6), small)
    # component: failure table 3M - 6 (M >= 3), 1 (M = 2), 0 (M = 1); scan 3n - M
    h = harness_of(E)
    kmp = load_module(resolve_in_repo(PAIRS / E, "implementations/kmp.py"))
    mism = []
    for n in small + v2k:
        text, pattern = h.generate_scaling(n, random.Random(0))
        kmp._failure(pattern)
        fail_cnt = h._comparisons
        Mv = len(pattern)
        f_fail = 3 * Mv - 6 if Mv >= 3 else (1 if Mv == 2 else 0)
        if fail_cnt != f_fail:
            mism.append((n, fail_cnt, f_fail))
    record(g, "KMP failure table 3M-6 (M>=3; 1 at M=2; 0 at M=1)", small + v2k, mism, "")
    mism = []
    for n in list(range(6, 41)) + v2k:
        total = measure(E, "implementations/kmp.py:count_kmp", n)
        text, pattern = h.generate_scaling(n, random.Random(0))
        kmp._failure(pattern)
        scan = total - h._comparisons
        if scan != 3 * n - len(pattern):
            mism.append((n, scan, 3 * n - len(pattern)))
    record(g, "KMP scan 3n-M (n>=6)", list(range(6, 41)) + v2k, mism, "")

    E = "multi-pattern-matching-naive-vs-aho-corasick"
    ns = list(range(0, 31)) + [32, 40, 48, 64]
    check(g, E, "implementations/naive.py:count_occurrences_naive", "multi naive n(n+1)(3n^2-2n+2)/6",
          lambda n: F(n * (n + 1) * (3 * n * n - 2 * n + 2), 6), ns)
    check(g, E, "implementations/kmp_each.py:count_occurrences_kmp_each", "multi KMP 3n^3-2n^2-5n+6",
          lambda n: 3 * n ** 3 - 2 * n ** 2 - 5 * n + 6, ns, domain=lambda n: n >= 2)
    check(g, E, "implementations/aho_corasick.py:count_occurrences_aho_corasick", "AC 4n^2-3",
          lambda n: 4 * n * n - 3, ns + [128, 256, 300], domain=lambda n: n >= 1)
    # AC components by phase: attribute each counted comparison to the line of count_occurrences_aho_corasick
    # that called _child (build loop, failure-link loop, scan loop)
    ac = load_module(resolve_in_repo(PAIRS / E, "implementations/aho_corasick.py"))
    src, start = inspect.getsourcelines(ac.count_occurrences_aho_corasick)
    line_fail = start + next(i for i, s in enumerate(src) if "fail = [0] * len(children)" in s)
    line_scan = start + next(i for i, s in enumerate(src) if "visits = [0] * len(children)" in s)
    h = harness_of(E)
    orig_eq = h.CountingChar.__eq__
    tally = {"build": 0, "fail": 0, "scan": 0}

    def eq(self, other):
        ln = sys._getframe(2).f_lineno           # frame 1 = _child, frame 2 = the caller line
        tally["build" if ln < line_fail else ("fail" if ln < line_scan else "scan")] += 1
        return orig_eq(self, other)
    h.CountingChar.__eq__ = eq
    mb, mf, ms = [], [], []
    try:
        for n in range(0, 31):
            for key in tally:
                tally[key] = 0
            inst = h.generate_scaling(n, random.Random(0))
            ac.count_occurrences_aho_corasick(inst)
            if tally["build"] != (n - 1) ** 2 and n >= 1:
                mb.append((n, tally["build"], (n - 1) ** 2))
            if n >= 2 and tally["fail"] != 3 * n - 5:
                mf.append((n, tally["fail"], 3 * n - 5))
            if n >= 2 and tally["scan"] != 3 * n * n - n + 1:
                ms.append((n, tally["scan"], 3 * n * n - n + 1))
            if n == 1:
                n1 = dict(tally)
            if n == 0:
                n0 = dict(tally)
    finally:
        h.CountingChar.__eq__ = orig_eq
    record(g, "AC trie build (n-1)^2 (n>=1)", range(1, 31), mb, f"n=0: {n0}")
    record(g, "AC failure links 3n-5 (n>=2)", range(2, 31), mf, f"n=1: {n1}")
    record(g, "AC scan 3n^2-n+1 (n>=2)", range(2, 31), ms, f"n=1 scan {n1['scan']} (formula 3)")

    E = "regex-matching-backtracking-vs-thompson"
    check(g, E, "implementations/backtracking.py:match_backtracking", "regex backtracking (n+2)2^(n-1)-1",
          lambda n: (n + 2) * P2(n - 1) - 1, list(range(0, 19)))
    for impl, nm in (("implementations/memoized.py:match_memoized", "memoised"),
                     ("implementations/thompson.py:match_thompson", "Thompson")):
        check(g, E, impl, f"regex {nm} n(n+1)", lambda n: n * (n + 1), list(range(0, 41)) + [48, 64, 100, 128])


# ----------------------------------------------------------------------------------------------------------------
# Group: sorting, selection, geometry, RMQ
# ----------------------------------------------------------------------------------------------------------------

def merge_bounds_topdown(n):
    """sum of min(l, r) and of (l + r - 1) over the merges of a top-down merge sort of n items (split n//2)."""
    if n <= 1:
        return 0, 0
    l, r = n // 2, n - n // 2
    a1, b1 = merge_bounds_topdown(l)
    a2, b2 = merge_bounds_topdown(r)
    return a1 + a2 + min(l, r), b1 + b2 + l + r - 1


def merge_bounds_bottomup(n):
    lo_sum = hi_sum = 0
    width = 1
    while width < n:
        for lo in range(0, n, 2 * width):
            mid, hi = min(lo + width, n), min(lo + 2 * width, n)
            l, r = mid - lo, hi - mid
            if l and r:
                lo_sum += min(l, r)
                hi_sum += l + r - 1
        width *= 2
    return lo_sum, hi_sum


def group_sorting():
    g = "sorting"
    E = "longest-increasing-subsequence"
    check(g, E, "implementations/subset_enumeration.py:lis_subsets", "LIS subsets n2^(n-1)-2^n+1",
          lambda n: n * P2(n - 1) - P2(n) + 1, list(range(0, 19)))
    check(g, E, "implementations/quadratic_dp.py:lis_quadratic", "LIS DP n(n-1)/2",
          lambda n: n * (n - 1) // 2, list(range(0, 41)) + [100, 200, 400, 800, 1600])
    check(g, E, "implementations/patience.py:lis_patience", "LIS patience sum_{j=2..n} floor(log2 j)",
          lambda n: sum(ilog2(j) for j in range(2, n + 1)), list(range(0, 70)) + [10000, 30000, 100000, 300000])

    E = "sorting-insertion-vs-merge"
    h = harness_of(E)
    mism = []
    ns = list(range(0, 30)) + [50, 100, 250, 500, 1000]
    for n in ns:
        a = measure(E, "implementations/insertion_sort.py:insertion_sort", n)
        xs = h.generate(n, random.Random(f"{E}|v2|{n}"))
        f = 0
        for i in range(1, n):
            gi = sum(1 for j in range(i) if xs[j] > xs[i])
            f += gi + (1 if gi < i else 0)
        if a != f:
            mism.append((n, a, f))
    record(g, "insertion sort sum_i g_i + [g_i < i] (instance formula)", ns, mism, "")
    mism = []
    ns = list(range(0, 40)) + [1000, 2000, 4000, 8000]
    for n in ns:
        a = measure(E, "implementations/merge_sort.py:merge_sort", n)
        lo, hi = merge_bounds_topdown(n)
        if not lo <= a <= hi:
            mism.append((n, a, f"[{lo}, {hi}]"))
    record(g, "merge sort: sum min(l,r) <= C <= sum (l+r-1)", ns, mism, "")

    E = "inversion-counting-quadratic-vs-merge"
    check(g, E, "implementations/pairs_scan.py:inversions_quadratic", "inversions all pairs n(n-1)/2",
          lambda n: n * (n - 1) // 2, list(range(0, 30)) + [250, 500, 750, 1000, 1500, 2000])
    mism = []
    for n in ns:
        a = measure(E, "implementations/merge_count.py:inversions_merge", n)
        lo, hi = merge_bounds_topdown(n)
        if not lo <= a <= hi:
            mism.append((n, a, f"[{lo}, {hi}]"))
    record(g, "inversion merge: merge bounds", ns, mism, "")

    E = "element-distinctness-pairs-vs-sorting"
    check(g, E, "implementations/all_pairs.py:distinct_all_pairs", "distinctness all pairs n(n-1)/2 (distinct input)",
          lambda n: n * (n - 1) // 2, list(range(0, 30)) + [500, 1000, 1500, 2000, 3000, 4000])
    mism = []
    for n in ns:
        a = measure(E, "implementations/sort_adjacent.py:distinct_by_sorting", n)
        lo, hi = merge_bounds_bottomup(n)
        nb = max(n - 1, 0)
        if not lo + nb <= a <= hi + nb:
            mism.append((n, a, f"[{lo + nb}, {hi + nb}]"))
    record(g, "distinctness sort: merge bounds + (n-1) neighbour tests", ns, mism, "")

    E = "closest-pair-brute-vs-divide-conquer"
    check(g, E, "implementations/brute_force.py:closest_pair_brute", "closest pair brute n(n-1) mults",
          lambda n: n * (n - 1), list(range(0, 30)) + [125, 250, 500, 1000, 2000], domain=lambda n: n >= 2)
    # D&C decomposition: squarings (strip filter) = S(n); products inside _dist2 = base cases 2 per pair
    h = harness_of(E)
    dc = load_module(resolve_in_repo(PAIRS / E, "implementations/divide_conquer.py"))

    def S(n):
        return 0 if n <= 3 else n + S(n // 2) + S(n - n // 2)

    def B(n):
        return 2 * C(n, 2) if n <= 3 else B(n // 2) + B(n - n // 2)
    orig_mul, orig_pow = h.CountingInt.__mul__, h.CountingInt.__pow__
    tally = {"pow": 0, "dist2": 0, "other": 0}

    def mul(self, other):
        tally["dist2" if sys._getframe(1).f_code.co_name == "_dist2" else "other"] += 1
        return orig_mul(self, other)

    def pw(self, e):
        tally["pow"] += 1
        return orig_pow(self, e)
    h.CountingInt.__mul__, h.CountingInt.__rmul__, h.CountingInt.__pow__ = mul, mul, pw
    m1, m2, ex = [], [], []
    ns = list(range(2, 40)) + [1000, 2000, 4000, 8000, 16000, 32000, 64000]
    try:
        for n in ns:
            for key in tally:
                tally[key] = 0
            inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
            dc.closest_pair_dc(inst)
            if tally["pow"] != S(n):
                m1.append((n, tally["pow"], S(n)))
            if tally["dist2"] != B(n):
                m2.append((n, tally["dist2"], B(n)))
            if n in (1000, 64000):
                ex.append(f"n={n}: S={tally['pow']} base={tally['dist2']} strip-scan={tally['other']} "
                          f"total={tally['pow'] + tally['dist2'] + tally['other']}")
    finally:
        h.CountingInt.__mul__, h.CountingInt.__rmul__, h.CountingInt.__pow__ = orig_mul, orig_mul, orig_pow
    record(g, "closest pair D&C strip filter S(n)=n+S(fl)+S(cl), S(2)=S(3)=0", ns, m1, "", "; ".join(ex))
    record(g, "closest pair D&C base cases: 2 products per pair in leaves", ns, m2, "")

    E = "range-minimum-queries-naive-vs-sparse-table"
    h = harness_of(E)
    ns = list(range(1, 40)) + [200, 400, 600, 800, 1200, 1600]
    mism = []
    for n in ns:
        a = measure(E, "implementations/naive_scan.py:rmq_naive", n)
        _, queries = h._scaling_draws(n, random.Random(f"{E}|v2|{n}"))
        f = sum(r - l for l, r in queries)
        if a != f:
            mism.append((n, a, f))
    record(g, "RMQ scan sum(r-l) (instance formula)", ns, mism, "")
    ns2 = list(range(1, 70)) + [2000, 4000, 8000, 16000, 32000, 64000, 128000]
    check(g, E, "implementations/sparse_table.py:rmq_sparse_table", "RMQ sparse table sum_{j=1..K}(n-2^j+1)+n",
          lambda n: sum(n - 2 ** j + 1 for j in range(1, ilog2(n) + 1)) + n, ns2)
    check(g, E, "implementations/sparse_table.py:rmq_sparse_table", "RMQ sparse n log2 n - n + log2 n + 2 (n=2^K)",
          lambda n: n * ilog2(n) - n + ilog2(n) + 2, [1, 2, 4, 8, 16, 32, 64, 128, 1024, 3, 5, 6, 7, 2000],
          domain=is_pow2)


# ----------------------------------------------------------------------------------------------------------------
# Group: algebra (matrix, integer and polynomial multiplication, transforms)
# ----------------------------------------------------------------------------------------------------------------

def group_algebra():
    g = "algebra"
    for E, nimpl, simpl in (("matrix-multiplication-naive-vs-strassen", "implementations/naive.py:matmul_naive",
                             "implementations/strassen.py:matmul_strassen"),
                            ("boolean-matrix-multiplication-naive-vs-strassen", "implementations/naive.py:bmm_naive",
                             "implementations/strassen_over_integers.py:bmm_strassen")):
        short = "matmul" if E.startswith("matrix") else "boolean"
        check(g, E, nimpl, f"{short} schoolbook n^3", lambda n: n ** 3,
              list(range(0, 21)) + [32, 64, 128] + ([256] if short == "matmul" else []))
        check(g, E, simpl, f"{short} Strassen 7^log2(n/16)*16^3",
              lambda n: 7 ** int(math.log2(n // 16)) * 4096 if is_pow2(n) and n >= 16 else F(-1),
              [1, 2, 4, 8, 15, 16, 17, 20, 24, 31, 32, 33, 48, 64, 128] + ([256] if short == "matmul" else []),
              domain=lambda n: is_pow2(n) and n >= 16)
    def small_padded(n):   # n <= 16: schoolbook on the s x s padded matrices, s = 2^ceil(log2 n)
        s = 1 << (n - 1).bit_length() if n else 0
        return n * (s * s - (s - n) ** 2)
    check(g, "matrix-multiplication-naive-vs-strassen", "implementations/strassen.py:matmul_strassen",
          "matmul Strassen n<=16: n(s^2-(s-n)^2), s=2^ceil(log2 n) (padded schoolbook)",
          small_padded, list(range(0, 17)))

    E = "integer-multiplication-schoolbook-vs-karatsuba"
    check(g, E, "implementations/schoolbook.py:multiply_schoolbook", "integer schoolbook n^2",
          lambda n: n * n, list(range(0, 33)) + [64, 128, 256, 512, 1024])
    check(g, E, "implementations/karatsuba.py:multiply_karatsuba", "Karatsuba 3^log2(n/32)*32^2",
          lambda n: 3 ** int(math.log2(n // 32)) * 1024 if is_pow2(n) and n >= 32 else F(-1),
          [1, 16, 31, 32, 33, 48, 63, 64, 65, 96, 100, 128, 256, 512, 1024, 2048],
          domain=lambda n: is_pow2(n) and n >= 32)
    check(g, E, "implementations/karatsuba.py:multiply_karatsuba", "Karatsuba n<=32: n^2",
          lambda n: n * n, list(range(0, 33)))
    # edge case: equal halves at some recursion node (x1 == x0 and y1 == y0) -> z1's products are on plain zeros
    h = harness_of(E)
    kar = load_callable(PAIRS / E, "implementations/karatsuba.py:multiply_karatsuba")
    rows = []
    for n, digits in ((64, [7] * 64), (128, [5] * 128), (64, [1, 2] * 32), (128, list(range(1, 65)) * 2)):
        a = tuple(h.CountingDigit(d) for d in digits)
        b = tuple(h.CountingDigit(d) for d in digits)
        h._mults = 0
        kar((a, b))
        rows.append(f"n={n} digits={'const' if len(set(digits)) == 1 else 'periodic'}: {h._mults} "
                    f"(formula {3 ** int(math.log2(n // 32)) * 1024})")
    RESULTS.append((g, "Karatsuba equal-halves inputs (outside the generator's generic draws)", "INFO", "; ".join(rows)))
    print(f"[{g}] INFO     Karatsuba equal-halves inputs: " + "; ".join(rows), flush=True)

    E = "polynomial-multiplication-naive-vs-ntt"
    check(g, E, "implementations/naive.py:polymul_naive", "poly schoolbook n^2 (no zero coefficient drawn)",
          lambda n: n * n, list(range(0, 30)) + [100, 200, 300, 400, 600, 800])
    check(g, E, "implementations/ntt.py:polymul_ntt", "NTT 3n log2 n + 5n (n=2^k)",
          lambda n: 3 * n * ilog2(n) + 5 * n if is_pow2(n) else F(-1),
          [1, 2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 16384, 3, 5, 6, 7, 100],
          domain=lambda n: is_pow2(n) and n >= 2)

    E = "or-convolution-naive-vs-zeta-mobius"
    check(g, E, "implementations/naive.py:or_convolution_naive", "OR naive 2*4^n", lambda n: 2 * 4 ** n,
          list(range(0, 10)))
    check(g, E, "implementations/zeta_mobius.py:or_convolution_zeta_mobius", "zeta-Moebius (3n+2)2^(n-1)",
          lambda n: (3 * n + 2) * P2(n - 1), list(range(0, 17)))
    E = "xor-convolution-naive-vs-walsh-hadamard"
    check(g, E, "implementations/naive.py:xor_convolution_naive", "XOR naive 2*4^n", lambda n: 2 * 4 ** n,
          list(range(0, 10)))
    check(g, E, "implementations/fwht.py:xor_convolution_fwht", "FWHT (3n+2)2^n",
          lambda n: (3 * n + 2) * 2 ** n, list(range(0, 15)))
    E = "subset-sum-zeta-transform-naive-vs-yates"
    check(g, E, "implementations/naive.py:zeta_naive", "zeta naive 3^n", lambda n: 3 ** n, list(range(0, 12)))
    check(g, E, "implementations/yates.py:zeta_yates", "Yates n2^(n-1)", lambda n: n * P2(n - 1),
          list(range(0, 17)))


# ----------------------------------------------------------------------------------------------------------------
# Group: exponential and polynomial DPs, graphs, SAT
# ----------------------------------------------------------------------------------------------------------------

def kinds_check(g, eid, impl, label, formulas, ns, domain=lambda n: True):
    """formulas: dict kind -> f(n); compares the harness's per-kind tally (dict _ops) after each run."""
    h = harness_of(eid)
    mism = []
    for n in ns:
        measure(eid, impl, n)
        for kind, f in formulas.items():
            if domain(n) and h._ops[kind] != f(n):
                mism.append((n, f"{kind}={h._ops[kind]}", f(n)))
    record(g, label, ns, mism, "")


def group_expdp():
    g = "expdp"
    E = "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"
    check(g, E, "implementations/enumeration.py:count_hamiltonian_cycles_enumeration", "Ham enumeration n!",
          lambda n: math.factorial(n), list(range(0, 11)), domain=lambda n: n >= 2)
    check(g, E, "implementations/inclusion_exclusion.py:count_hamiltonian_cycles_inclusion_exclusion",
          "Ham IE n(n-1)(n+2)2^(n-2)+2^(n-1)-1", lambda n: n * (n - 1) * (n + 2) * P2(n - 2) + P2(n - 1) - 1,
          list(range(0, 14)), domain=lambda n: n >= 1)
    kinds_check(g, E, "implementations/inclusion_exclusion.py:count_hamiltonian_cycles_inclusion_exclusion",
                "Ham IE per kind: mul n(n-1)(n+2)2^(n-3), add mul+2^(n-1)-1",
                {"mul": lambda n: n * (n - 1) * (n + 2) * P2(n - 3),
                 "add": lambda n: n * (n - 1) * (n + 2) * P2(n - 3) + P2(n - 1) - 1,
                 "truth": lambda n: 0, "compare": lambda n: 0}, list(range(2, 13)))
    check(g, E, "implementations/held_karp_counting.py:count_hamiltonian_cycles_held_karp",
          "Ham Held-Karp (n-1)(n-2)2^(n-2)+2(n-1)", lambda n: (n - 1) * (n - 2) * P2(n - 2) + 2 * (n - 1),
          list(range(0, 17)), domain=lambda n: n >= 1)
    kinds_check(g, E, "implementations/held_karp_counting.py:count_hamiltonian_cycles_held_karp",
                "Ham HK per kind: mul = add = (n-1)(n-2)2^(n-3)+(n-1)",
                {"mul": lambda n: (n - 1) * (n - 2) * P2(n - 3) + n - 1,
                 "add": lambda n: (n - 1) * (n - 2) * P2(n - 3) + n - 1}, list(range(2, 15)))

    E = "linear-ordering-enumeration-vs-subset-dp"
    check(g, E, "implementations/enumeration.py:linear_ordering_enumeration", "LO enumeration n!(n(n-1)/2+1)-1",
          lambda n: math.factorial(n) * (n * (n - 1) // 2 + 1) - 1, list(range(0, 9)))
    check(g, E, "implementations/subset_dp.py:linear_ordering_subset_dp", "LO DP 2^(n-2)(n+4)(n-1)+1",
          lambda n: P2(n - 2) * (n + 4) * (n - 1) + 1, list(range(0, 16)), domain=lambda n: n >= 2)
    kinds_check(g, E, "implementations/subset_dp.py:linear_ordering_subset_dp",
                "LO DP per kind: add n(n-1)2^(n-2)+n2^(n-1), compare n2^(n-1)-2^n+1",
                {"add": lambda n: n * (n - 1) * P2(n - 2) + n * P2(n - 1),
                 "compare": lambda n: n * P2(n - 1) - P2(n) + 1}, list(range(2, 14)))

    E = "first-match-rule-ordering-enumeration-vs-subset-dp"
    check(g, E, "implementations/enumeration.py:first_match_order_enumeration", "FM enumeration k!(k+1)(k+3)/3-1",
          lambda k: F(math.factorial(k) * (k + 1) * (k + 3), 3) - 1, list(range(0, 9)),
          domain=lambda k: k >= 2)
    kinds_check(g, E, "implementations/enumeration.py:first_match_order_enumeration",
                "FM enumeration per kind: truth k!k(k+1)/3, add k!k, compare k!-1",
                {"truth": lambda k: F(math.factorial(k) * k * (k + 1), 3), "add": lambda k: math.factorial(k) * k,
                 "compare": lambda k: math.factorial(k) - 1}, list(range(2, 9)))
    check(g, E, "implementations/subset_dp.py:first_match_order_subset_dp", "FM DP 3k^2+(7k-2)2^(k-1)+2",
          lambda k: 3 * k * k + (7 * k - 2) * P2(k - 1) + 2, list(range(0, 19)), domain=lambda k: k >= 1)
    kinds_check(g, E, "implementations/subset_dp.py:first_match_order_subset_dp",
                "FM DP per kind: truth k^2+k2^k, bit k^2+k2^k, add k^2+k2^k+1, compare k2^(k-1)-2^k+1",
                {"truth": lambda k: k * k + k * 2 ** k, "bit": lambda k: k * k + k * 2 ** k,
                 "add": lambda k: k * k + k * 2 ** k + 1,
                 "compare": lambda k: k * P2(k - 1) - P2(k) + 1}, list(range(1, 15)))

    E = "global-min-cut-brute-vs-stoer-wagner"
    check(g, E, "implementations/brute_force.py:min_cut_brute_force", "min cut brute n(n-1)2^(n-3)+2^(n-1)-2",
          lambda n: n * (n - 1) * P2(n - 3) + P2(n - 1) - 2, list(range(0, 15)), domain=lambda n: n >= 2)
    check(g, E, "implementations/stoer_wagner.py:min_cut_stoer_wagner", "Stoer-Wagner (n-2)(2n^2+n+3)/6",
          lambda n: F((n - 2) * (2 * n * n + n + 3), 6), list(range(0, 41)) + [48, 64, 128, 256],
          domain=lambda n: n >= 2)
    h = harness_of(E)
    for impl, lab, fa, fc in (
            ("implementations/brute_force.py:min_cut_brute_force", "min cut brute: adds n(n-1)2^(n-3), cmps 2^(n-1)-2",
             lambda n: n * (n - 1) * P2(n - 3), lambda n: P2(n - 1) - 2),
            ("implementations/stoer_wagner.py:min_cut_stoer_wagner",
             "Stoer-Wagner: adds (n-1)(n-2)(n+3)/6, cmps n(n-1)(n-2)/6+n-2",
             lambda n: F((n - 1) * (n - 2) * (n + 3), 6), lambda n: F(n * (n - 1) * (n - 2), 6) + n - 2)):
        mism = []
        ns = range(2, 15) if "brute" in impl else range(2, 41)
        for n in ns:
            measure(E, impl, n)
            if h._adds != fa(n) or h._cmps != fc(n):
                mism.append((n, (h._adds, h._cmps), (fa(n), fc(n))))
        record(g, lab, ns, mism, "")

    E = "horn-sat-brute-force-vs-unit-propagation"
    check(g, E, "implementations/brute_force.py:horn_sat_brute_force", "Horn brute 6((2n+13)2^(n-2)-2n-4)",
          lambda n: 6 * ((2 * n + 13) * P2(n - 2) - 2 * n - 4), list(range(0, 17)), domain=lambda n: n >= 3)
    check(g, E, "implementations/unit_propagation.py:horn_sat_unit_propagation", "Horn unit propagation 12n-7",
          lambda n: 12 * n - 7, list(range(0, 301)) + [1000, 2000, 4000, 8000, 16000, 32000],
          domain=lambda n: n >= 3)

    E = "two-sat-brute-force-vs-scc"
    check(g, E, "implementations/brute_force.py:two_sat_brute_force", "2-SAT brute 3(n+7)2^n+12",
          lambda n: 3 * (n + 7) * 2 ** n + 12, list(range(0, 17)), domain=lambda n: n >= 3)
    check(g, E, "implementations/aspvall_plass_tarjan.py:two_sat_scc", "APT 49(n+2)",
          lambda n: 49 * (n + 2), list(range(0, 301)) + [1000, 2000, 4000, 8000, 16000, 32000],
          domain=lambda n: n >= 3)
    # build part 28n + 28: attribute counted operations to the function _node / the build loop by line number
    h = harness_of(E)
    apt = load_module(resolve_in_repo(PAIRS / E, "implementations/aspvall_plass_tarjan.py"))
    src, start = inspect.getsourcelines(apt.two_sat_scc)
    line_dfs = start + next(i for i, s in enumerate(src) if "index = [-1] * num_nodes" in s)
    orig = {}
    tally = {"build": 0, "dfs": 0}

    def wrap(name):
        f = getattr(h.CountingLit, name)
        orig[name] = f

        def w(self, *a):
            fr = sys._getframe(1)
            while fr is not None and fr.f_code.co_name not in ("two_sat_scc",):
                fr = fr.f_back
            tally["build" if fr is not None and fr.f_lineno < line_dfs else "dfs"] += 1
            return f(self, *a)
        setattr(h.CountingLit, name, w)
    names = [nm for nm in ("__abs__", "__neg__", "__add__", "__radd__", "__sub__", "__rsub__", "__mul__", "__rmul__",
                           "__and__", "__rand__", "__rshift__", "__rrshift__", "__xor__", "__rxor__", "__lt__",
                           "__le__", "__gt__", "__ge__", "__eq__", "__ne__", "__index__", "__hash__", "__bool__")
             if nm in h.CountingLit.__dict__]
    for nm in names:
        wrap(nm)
    h.CountingLit.__int__ = h.CountingLit.__index__
    mism = []
    try:
        for n in range(3, 60):
            tally["build"] = tally["dfs"] = 0
            inst = h.generate_scaling(n, random.Random(0))
            apt.two_sat_scc(inst)
            if tally["build"] != 28 * n + 28 or tally["dfs"] != 21 * n + 70:
                mism.append((n, (tally["build"], tally["dfs"]), (28 * n + 28, 21 * n + 70)))
    finally:
        for nm, f in orig.items():
            setattr(h.CountingLit, nm, f)
        h.CountingLit.__int__ = orig["__index__"]
    record(g, "APT split: build 28n+28, Tarjan DFS 21n+70", range(3, 60), mism, "")

    E = "xor-sat-brute-force-vs-gaussian-elimination"
    check(g, E, "implementations/brute_force.py:xor_sat_brute_force", "XOR-SAT brute (2n+1)(2^(n+1)-2)",
          lambda n: (2 * n + 1) * (2 ** (n + 1) - 2), list(range(0, 17)), domain=lambda n: n >= 1)
    check(g, E, "implementations/gaussian_elimination.py:xor_sat_gauss", "XOR-SAT Gauss n(n^2+6n-4)/3",
          lambda n: F(n * (n * n + 6 * n - 4), 3), list(range(0, 129)) + [200, 256], domain=lambda n: n >= 1)

    E = "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"
    check(g, E, "implementations/brute_force.py:mwis_brute_force", "MIS brute N2^(N-1), N=3n",
          lambda n: 3 * n * P2(3 * n - 1), list(range(0, 7)))
    check(g, E, "implementations/column_dp.py:mwis_column_dp", "MIS DP 10n-5", lambda n: 10 * n - 5,
          list(range(0, 60)) + [100, 200, 400, 800, 1600, 3200], domain=lambda n: n >= 1)
    h = harness_of(E)
    mism = []
    for n in range(1, 60):
        measure(E, "implementations/column_dp.py:mwis_column_dp", n)
        if h._ops["compare"] != 6 * n - 2:
            mism.append((n, h._ops["compare"], 6 * n - 2))
    record(g, "MIS DP comparisons 6n-2 (k=3, tallied separately)", range(1, 60), mism, "")
    # general k: n P_k + (n-1) F_{k+2} on king's graphs (positive weights)
    dp = load_callable(PAIRS / E, "implementations/column_dp.py:mwis_column_dp")
    mism, vals = [], []
    for k in range(1, 9):
        states = [s for s in range(1 << k) if s & (s >> 1) == 0]
        Pk = sum(bin(s).count("1") for s in states)
        for n in (1, 2, 3, 7, 20):
            inst = h.king_instance(k, n, random.Random(f"k{k}n{n}"))
            h.reset_counters()
            dp(inst)
            f = n * Pk + (n - 1) * fib(k + 2)
            if len(states) != fib(k + 2):
                mism.append((n, f"states {len(states)}", fib(k + 2)))
            if h._ops["add"] != f:
                mism.append((n, h._ops["add"], f))
            if n == 20:
                vals.append(h._ops["add"])
    record(g, "MIS DP general k: nP_k+(n-1)F_{k+2} (k=1..8, king's graph)", [1, 2, 3, 7, 20], mism, "",
           f"n=20, k=1..8: {vals}")

    E = "planar-perfect-matchings-enumeration-vs-kasteleyn"
    check(g, E, "implementations/enumeration.py:count_perfect_matchings_enumeration", "ladder enumeration L(n/2+2)-3",
          lambda n: lucas(n // 2 + 2) - 3, list(range(2, 61, 2)))
    check(g, E, "implementations/kasteleyn_bareiss.py:count_perfect_matchings_kasteleyn",
          "Kasteleyn (n-2)n(n-1)/8", lambda n: F((n - 2) * n * (n - 1), 8), list(range(2, 121, 2)) + [128, 256])
    h = harness_of(E)
    en = load_callable(PAIRS / E, "implementations/enumeration.py:count_perfect_matchings_enumeration")
    mism = []
    for m in range(1, 25):
        a, b, W = 2, m, h._matrix(2, m, lambda: 1)
        inst = (a, b, tuple(tuple(h.CountingInt(x) for x in row) for row in W))
        h._ops = 0
        en(inst)
        f = fib(m + 3) - 2 + F((m - 1) * fib(m) + 2 * m * fib(m - 1), 5)
        if h._ops != f:
            mism.append((m, h._ops, f))
    record(g, "2 x m ladder enumeration F(m+3)-2+((m-1)F(m)+2mF(m-1))/5", range(1, 25), mism, "")

    E = "spanning-tree-count-enumeration-vs-kirchhoff"
    check(g, E, "implementations/kirchhoff_bareiss.py:count_spanning_trees_kirchhoff", "Kirchhoff (n-2)(n-1)(2n-3)/2",
          lambda n: F((n - 2) * (n - 1) * (2 * n - 3), 2), list(range(0, 71)) + [128], domain=lambda n: n >= 1)

    E = "minimum-spanning-tree-brute-vs-kruskal"
    check(g, E, "implementations/prim.py:mst_prim", "Prim (n-1)^2", lambda n: (n - 1) ** 2,
          list(range(0, 60)) + [100, 200, 400, 800], domain=lambda n: n >= 1)

    def enum_f(n):
        m = n * (n - 1) // 2
        return (n - 1) * C(m, n - 1) + n ** (n - 2) - 1
    check(g, E, "implementations/brute_force.py:mst_brute", "MST enumeration (n-1)C(m,n-1)+n^(n-2)-1",
          enum_f, list(range(0, 8)), domain=lambda n: n >= 1)
    # Kruskal decomposition: 3m packing + comparisons inside sorted() on the same keys + one divmod per scanned key
    h = harness_of(E)
    mism = []
    for n in (2, 3, 5, 10, 50, 100):
        total = measure(E, "implementations/kruskal.py:mst_kruskal", n)
        W = h._scaling_draws(n, random.Random(f"{E}|v2|{n}"))
        nn, m = n * n, n * (n - 1) // 2
        keys = [h.CountingWeight(W[u][v] * nn + u * n + v) for u in range(n) for v in range(u + 1, n)]
        h._ops = 0
        skeys = sorted(keys)
        sort_cmp = h._ops
        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        taken = scanned = 0
        for key in skeys:
            if taken == n - 1:
                break
            scanned += 1
            u, v = divmod(key.v % nn, n)
            ru, rv = find(u), find(v)
            if ru != rv:
                parent[rv] = ru
                taken += 1
        if total != 3 * m + sort_cmp + scanned:
            mism.append((n, total, 3 * m + sort_cmp + scanned))
    record(g, "Kruskal = 3m + sort comparisons + scanned keys (decomposition)", [2, 3, 5, 10, 50, 100], mism, "")

    E = "all-pairs-shortest-paths-bellman-ford-vs-floyd-warshall"
    check(g, E, "implementations/bellman_ford.py:apsp_bellman_ford", "Bellman-Ford n^2(n-1)^2",
          lambda n: n * n * (n - 1) ** 2, list(range(0, 21)) + [25, 32, 40])
    check(g, E, "implementations/floyd_warshall.py:apsp_floyd_warshall", "Floyd-Warshall n^3-n",
          lambda n: n ** 3 - n, list(range(0, 41)) + [48, 64, 96, 128, 160, 200])

    E = "three-xor-all-triples-vs-patricia-trie"
    p2 = [1, 2, 4, 8, 16, 32, 64, 128, 256, 512]
    check(g, E, "implementations/all_triples.py:three_xor_all_triples", "3XOR all triples (n^3-n)/6",
          lambda n: (n ** 3 - n) // 6, p2)
    check(g, E, "implementations/patricia_trie.py:three_xor_patricia_trie", "3XOR Patricia 7n^2+2n log2 n-3n",
          lambda n: 7 * n * n + 2 * n * ilog2(n) - 3 * n, p2 + [1024, 2048])
    h = harness_of(E)
    mism = []
    for n in p2 + [1024]:
        measure(E, "implementations/patricia_trie.py:three_xor_patricia_trie", n)
        want = {"xor": n * n, "and_or": n * ilog2(n) + n * (n - 1), "truth": n * ilog2(n) + n * (n - 1),
                "compare": 4 * n * n - n, "shift": 0}
        if dict(h._ops) != want:
            mism.append((n, dict(h._ops), want))
    record(g, "3XOR Patricia per kind", p2 + [1024], mism, "")

    E = "max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp"
    check(g, E, "implementations/recursion.py:maxbst_recursive", "maxBST recursion (3^(n-1)-1)/2",
          lambda n: F(3 ** n, 3) / 2 - F(1, 2), list(range(0, 12)), domain=lambda n: n >= 1)
    check(g, E, "implementations/cubic_dp.py:maxbst_cubic", "maxBST cubic (n+1)n(n-1)/6",
          lambda n: (n + 1) * n * (n - 1) // 6, list(range(0, 41)) + [64, 128])
    check(g, E, "implementations/endpoint_dp.py:maxbst_endpoint", "maxBST endpoint n(n-1)/2",
          lambda n: n * (n - 1) // 2, list(range(0, 61)) + [64, 128, 256, 512])
    h = harness_of(E)
    rec = load_callable(PAIRS / E, "implementations/recursion.py:maxbst_recursive")
    cub = load_callable(PAIRS / E, "implementations/cubic_dp.py:maxbst_cubic")
    endp = load_callable(PAIRS / E, "implementations/endpoint_dp.py:maxbst_endpoint")
    table_fams = [f for f in h.SCALING_FAMILIES if f in h.GENERAL_FAMILIES or f in h.MIN_FAMILIES]
    bst_fams = [f for f in h.SCALING_FAMILIES if f in h.FAMILIES]
    mism, calls_m = [], []
    for fam in (table_fams[:3] + bst_fams[:3]):
        bst = fam in h.FAMILIES
        extra = (lambda n: n * (n + 1)) if bst else (lambda n: 0)
        for n in range(0, 11):
            for fn, f in ((rec, lambda n: F(11 * 3 ** n, 9) / 2 - F(1, 2)),
                          (cub, lambda n: F(n * (n + 1) * (n + 2), 6) - n + F(n * (n + 1), 2)),
                          (endp, lambda n: F(3 * n * (n - 1), 2))):
                inst = h.wrap_counting(h.instance_of(fam, n, random.Random(f"{fam}{n}")))
                h.reset_counters()
                if fn is rec:
                    with CallCounter("cost") as cc:
                        fn(inst)
                    if cc.calls != 3 ** n:
                        calls_m.append((n, cc.calls, 3 ** n))
                    if n < 2:                    # the additions form holds from n = 2 on (S01)
                        continue
                else:
                    fn(inst)
                want = f(n) + extra(n)
                if h._additions != want:
                    mism.append((n, f"{fam}/{fn.__name__}: {h._additions}", want))
    record(g, "maxBST additions: (11*3^(n-2)-1)/2 rec (n>=2), cubic n(n+1)(n+2)/6-n+n(n+1)/2, endpoint 3n(n-1)/2; "
              "BST form + n(n+1)", range(0, 11), mism, "", f"families {table_fams[:3] + bst_fams[:3]}")
    record(g, "maxBST recursion: 3^n calls of cost()", range(0, 11), calls_m, "")

    E = "optimal-bst-recursion-vs-dp-vs-knuth"
    check(g, E, "implementations/recursion.py:obst_recursive", "OBST recursion (3^(n-1)-1)/2",
          lambda n: F(3 ** n, 3) / 2 - F(1, 2), list(range(0, 12)), domain=lambda n: n >= 1)
    check(g, E, "implementations/cubic_dp.py:obst_cubic", "OBST cubic (n+1)n(n-1)/6",
          lambda n: (n + 1) * n * (n - 1) // 6, list(range(0, 41)) + [64, 128])
    check(g, E, "implementations/knuth.py:obst_knuth", "OBST Knuth (n-1)^2 (heavy ends)",
          lambda n: (n - 1) ** 2, list(range(0, 61)) + [64, 128, 256, 512], domain=lambda n: n >= 1)
    h = harness_of(E)
    rec = load_callable(PAIRS / E, "implementations/recursion.py:obst_recursive")
    cub = load_callable(PAIRS / E, "implementations/cubic_dp.py:obst_cubic")
    kn = load_callable(PAIRS / E, "implementations/knuth.py:obst_knuth")
    mism, calls_m = [], []
    for n in range(0, 12):
        inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
        h.reset_counters()
        with CallCounter("cost") as cc:
            rec(inst)
        if cc.calls != 3 ** n:
            calls_m.append((n, cc.calls, 3 ** n))
        if n >= 2 and h._additions != F(35 * 3 ** n, 9) / 2 - F(3, 2):
            mism.append((n, f"rec {h._additions}", F(35 * 3 ** n, 9) / 2 - F(3, 2)))
        inst = h.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
        h.reset_counters()
        cub(inst)
        if h._additions != F(n * (n + 1) * (n + 2), 6) + F(3 * n * (n + 1), 2) - n:
            mism.append((n, f"cubic {h._additions}", F(n * (n + 1) * (n + 2), 6) + F(3 * n * (n + 1), 2) - n))
    for n in list(range(0, 41)) + [128]:
        for fam in h.FAMILIES:
            p, q = h._instance(n, random.Random(f"{fam}{n}"), fam)
            inst = (tuple(h.CountingInt(x) for x in p), tuple(h.CountingInt(x) for x in q))
            h.reset_counters()
            kn(inst)
            if h._additions != h._comparisons + 2 * n * n:
                mism.append((n, f"knuth add {h._additions} cmp {h._comparisons}", "cmp + 2n^2"))
    record(g, "OBST additions: rec (35*3^(n-2)-3)/2 (n>=2), cubic n(n+1)(n+2)/6+3n(n+1)/2-n, Knuth cmp+2n^2",
           range(0, 41), mism, "")
    record(g, "OBST recursion: 3^n calls of cost()", range(0, 12), calls_m, "")


# ----------------------------------------------------------------------------------------------------------------
# Group: query complexity (deterministic exact counts only)
# ----------------------------------------------------------------------------------------------------------------

def group_query():
    g = "query"
    E = "deutsch-jozsa-classical-vs-quantum"
    check(g, E, "implementations/classical.py:dj_classical", "DJ deterministic 2^(n-1)+1 (scaling inputs)",
          lambda n: 2 ** (n - 1) + 1, list(range(1, 17)))
    h = harness_of(E)
    mism = []
    for n in range(1, 17):
        for seed in range(6):        # both branches of generate_scaling (constant / c XOR top bit), both c
            inst = h.generate_scaling(n, random.Random(seed))
            out = load_callable(PAIRS / E, "implementations/classical.py:dj_classical")(inst)
            if out[1] != 2 ** (n - 1) + 1:
                mism.append((n, out[1], 2 ** (n - 1) + 1))
    record(g, "DJ deterministic on every scaling input (6 seeds per n)", range(1, 17), mism, "")
    check(g, E, "implementations/randomized.py:dj_randomized", "DJ randomized exactly 20", lambda n: 20,
          list(range(1, 17)))
    check(g, E, "implementations/quantum.py:dj_quantum", "DJ quantum exactly 1", lambda n: 1, list(range(1, 11)))
    E = "bernstein-vazirani-classical-vs-quantum"
    check(g, E, "implementations/classical.py:bv_classical", "BV classical n", lambda n: n, list(range(0, 17)))
    check(g, E, "implementations/quantum.py:bv_quantum", "BV quantum 1", lambda n: 1, list(range(1, 11)))
    E = "minimum-finding-classical-vs-quantum"
    check(g, E, "implementations/classical.py:minimum_scan", "min finding classical N=2^n", lambda n: 2 ** n,
          list(range(0, 17)))
    E = "nand-tree-evaluation-deterministic-vs-randomized"
    check(g, E, "implementations/left_first.py:nand_tree_left_first", "NAND left-first 2^h", lambda n: 2 ** n,
          list(range(0, 17)))
    # Hopcroft-Karp phases on G_k: k + 1 (counted as BFS passes = iterations of the outer while loop)
    E = "bipartite-matching-kuhn-vs-hopcroft-karp"
    h = harness_of(E)
    hk = load_module(resolve_in_repo(PAIRS / E, "implementations/hopcroft_karp.py"))
    src, start = inspect.getsourcelines(hk.matching_hopcroft_karp)
    line_bfs = start + next(i for i, s in enumerate(src) if "dist = [INF] * n_left" in s)
    mism = []
    for k in range(1, 13):
        n = 4 * k * k + k
        inst = h.generate_scaling(n, random.Random(0))
        phases = [0]

        def tracer(frame, event, arg):
            if frame.f_code is hk.matching_hopcroft_karp.__code__:
                if event == "line" and frame.f_lineno == line_bfs:
                    phases[0] += 1
                return tracer
            return None
        sys.settrace(tracer)
        try:
            hk.matching_hopcroft_karp(inst)
        finally:
            sys.settrace(None)
        if phases[0] != k + 1:
            mism.append((k, phases[0], k + 1))
    record(g, "Hopcroft-Karp on G_k: k+1 BFS passes (k augmenting phases + the final pass that finds no path)",
           range(1, 13), mism, "")


# ----------------------------------------------------------------------------------------------------------------
# Group: extra (secondary claims: uncounted loop work by line tracing; input independence; bounds)
# ----------------------------------------------------------------------------------------------------------------

def line_count(fn, args, marker):
    """Number of executions of the (unique) source line of fn containing `marker` during fn(*args)."""
    src, start = inspect.getsourcelines(fn)
    hits = [start + i for i, s in enumerate(src) if marker in s]
    assert len(hits) == 1, (marker, hits)
    target, code, cnt = hits[0], fn.__code__, [0]

    def tracer(frame, event, arg):
        if frame.f_code is code:
            if event == "line" and frame.f_lineno == target:
                cnt[0] += 1
            return tracer
        return None
    sys.settrace(tracer)
    try:
        fn(*args)
    finally:
        sys.settrace(None)
    return cnt[0]


def group_extra():
    g = "extra"
    E = "hamiltonian-cycle-count-enumeration-vs-inclusion-exclusion"
    h = harness_of(E)
    hk = load_callable(PAIRS / E, "implementations/held_karp_counting.py:count_hamiltonian_cycles_held_karp")
    ie = load_callable(PAIRS / E, "implementations/inclusion_exclusion.py:count_hamiltonian_cycles_inclusion_exclusion")
    mism = []
    for n in range(2, 11):
        c = line_count(hk, (h.counted_complete_digraph(n),), "if (prev >> a) & 1:")
        if c != (n - 1) ** 2 * (2 ** (n - 2) - 1):
            mism.append((n, c, (n - 1) ** 2 * (2 ** (n - 2) - 1)))
    record(g, "Ham HK membership tests (n-1)^2(2^(n-2)-1) (uncounted plain-int work)", range(2, 11), mism, "")
    mism = []
    for n in range(2, 10):
        c = line_count(ie, (h.counted_complete_digraph(n),), "if i != j:")
        f = n * sum(C(n - 1, s) * (s + 1) ** 2 for s in range(n))
        if c != f:
            mism.append((n, c, f))
    record(g, "Ham IE index comparisons n t^2 per set of size t (summed)", range(2, 10), mism, "")
    # counts identical on random 0/1 digraphs (the entry: 'identical on random graphs')
    mism = []
    for n in range(2, 10):
        for seed in range(3):
            rng = random.Random(f"r{n}{seed}")
            adj = tuple(tuple(h.CountingInt(rng.randint(0, 1) if u != v else rng.randint(0, 1)) for v in range(n))
                        for u in range(n))
            for fn, f in ((ie, lambda n: n * (n - 1) * (n + 2) * P2(n - 2) + P2(n - 1) - 1),
                          (hk, lambda n: (n - 1) * (n - 2) * P2(n - 2) + 2 * (n - 1))):
                h.reset_counter()
                fn(adj)
                if sum(h._ops.values()) != f(n):
                    mism.append((n, f"{fn.__name__} {sum(h._ops.values())}", f(n)))
    record(g, "Ham IE and HK counts on random 0/1 matrices (random diagonal too)", range(2, 10), mism, "")

    E = "max-weight-independent-set-grid-enumeration-vs-path-decomposition-dp"
    h = harness_of(E)
    dp = load_callable(PAIRS / E, "implementations/column_dp.py:mwis_column_dp")
    mism = []
    for k in range(1, 6):
        for n in (1, 2, 5, 10):
            c = line_count(dp, (h.king_instance(k, n, random.Random(1)),), "if t & s:")
            if c != (n - 1) * fib(k + 2) ** 2:
                mism.append((n, f"k={k}: {c}", (n - 1) * fib(k + 2) ** 2))
    record(g, "MIS DP compatibility tests (n-1)F_{k+2}^2 (uncounted)", [1, 2, 5, 10], mism, "")

    for E, impl in (("max-cost-bst-recursion-vs-cubic-dp-vs-endpoint-dp", "implementations/cubic_dp.py:maxbst_cubic"),
                    ("optimal-bst-recursion-vs-dp-vs-knuth", "implementations/cubic_dp.py:obst_cubic")):
        h = harness_of(E)
        fn = load_callable(PAIRS / E, impl)
        mism = []
        for n in range(0, 25):
            c = line_count(fn, (h.generate_scaling(n, random.Random(n)),), "cand = c[i][k - 1] + c[k][j]")
            if c != n * (n + 1) * (n + 2) // 6:
                mism.append((n, c, n * (n + 1) * (n + 2) // 6))
        record(g, f"{E.split('-')[0]} cubic DP candidate roots n(n+1)(n+2)/6 (uncounted)", range(0, 25), mism, "")

    E = "optimal-bst-recursion-vs-dp-vs-knuth"
    h = harness_of(E)
    kn = load_callable(PAIRS / E, "implementations/knuth.py:obst_knuth")
    mism, worst = [], {}
    for n in range(1, 41):
        for fam in h.FAMILIES:
            for seed in range(2):
                p, q = h._instance(n, random.Random(f"{fam}{n}{seed}"), fam)
                inst = (tuple(h.CountingInt(x) for x in p), tuple(h.CountingInt(x) for x in q))
                h.reset_counters()
                kn(inst)
                if h._comparisons > (n - 1) ** 2:
                    mism.append((n, f"{fam}: {h._comparisons}", f"<= {(n - 1) ** 2}"))
                if fam != "heavy_ends":
                    worst[n] = max(worst.get(n, 0), h._comparisons)
    record(g, "OBST Knuth comparisons <= (n-1)^2 on all ten families", range(1, 41), mism, "",
           f"max over the nine other families at n=40: {worst[40]} (bound {39 ** 2})")

    E = "xor-sat-brute-force-vs-gaussian-elimination"
    h = harness_of(E)
    bf = load_callable(PAIRS / E, "implementations/brute_force.py:xor_sat_brute_force")
    mism, tested = [], 0
    for n in range(1, 11):
        rng = random.Random(f"fr{n}")
        done = 0
        while done < 3:
            rows = [[rng.randint(0, 1) for _ in range(n)] for _ in range(n)]
            # rank over GF(2) by packing
            basis, rank = [], 0
            for r in rows:
                x = int("".join(map(str, r)), 2)
                for bvec in basis:
                    x = min(x, x ^ bvec)
                if x:
                    basis.append(x)
                    rank += 1
            if rank < n:
                continue
            system = (n, tuple(tuple(h.CountingBit(b) for b in r + [rng.randint(0, 1)]) for r in rows))
            h._ops = 0
            bf(system)
            if h._ops != (2 * n + 1) * (2 ** (n + 1) - 2):
                mism.append((n, h._ops, (2 * n + 1) * (2 ** (n + 1) - 2)))
            done += 1
            tested += 1
    record(g, "XOR-SAT brute (2n+1)(2^(n+1)-2) on random full-rank n x n systems", range(1, 11), mism, "",
           f"{tested} systems")

    E = "spanning-tree-count-enumeration-vs-kirchhoff"
    h = harness_of(E)
    kf = load_callable(PAIRS / E, "implementations/kirchhoff_bareiss.py:count_spanning_trees_kirchhoff")
    mism, tested = [], 0
    for n in range(2, 30):
        rng = random.Random(f"kc{n}")
        while True:     # random connected graph: a random tree plus random extra edges
            A = [[0] * n for _ in range(n)]
            for v in range(1, n):
                u = rng.randrange(v)
                A[u][v] = A[v][u] = 1
            for u in range(n):
                for v in range(u + 1, n):
                    if rng.random() < 0.3:
                        A[u][v] = A[v][u] = 1
            break
        h._ops = 0
        kf(tuple(tuple(h.CountingInt(x) for x in row) for row in A))
        tested += 1
        if h._ops != F((n - 2) * (n - 1) * (2 * n - 3), 2):
            mism.append((n, h._ops, F((n - 2) * (n - 1) * (2 * n - 3), 2)))
    record(g, "Kirchhoff (n-2)(n-1)(2n-3)/2 on random connected graphs", range(2, 30), mism, "", f"{tested} graphs")

    E = "global-min-cut-brute-vs-stoer-wagner"
    mism = []
    for n in range(2, 13):
        for s in range(3):
            for impl, f in (("implementations/brute_force.py:min_cut_brute_force",
                             lambda n: n * (n - 1) * P2(n - 3) + P2(n - 1) - 2),
                            ("implementations/stoer_wagner.py:min_cut_stoer_wagner",
                             lambda n: F((n - 2) * (2 * n * n + n + 3), 6))):
                h = harness_of(E)
                inst = h.generate_scaling(n, random.Random(f"other{n}{s}"))
                load_callable(PAIRS / E, impl)(inst)
                a = h.reported_cost(None)
                if a != f(n):
                    mism.append((n, a, f(n)))
    record(g, "min cut brute and Stoer-Wagner on other weight draws (3 per n)", range(2, 13), mism, "")

    # Horn: the oracle's naive forward chaining needs exactly n full passes on H_n (entry's verification text)
    E = "horn-sat-brute-force-vs-unit-propagation"
    h = harness_of(E)
    mism = []
    for n in range(3, 201):
        c = line_count(h._naive_chaining, (n, h._family(n)), "changed = False")
        if c != n:
            mism.append((n, c, n))
    record(g, "Horn oracle: naive forward chaining makes exactly n passes on H_n", range(3, 201), mism, "")

    # information: counts at sizes that are not powers of two (padding), against the closed form of the padded size
    rows = []
    for n in (17, 20, 24, 31, 33, 48, 100):
        s = 1 << (n - 1).bit_length()
        a = measure("matrix-multiplication-naive-vs-strassen", "implementations/strassen.py:matmul_strassen", n)
        b = measure("boolean-matrix-multiplication-naive-vs-strassen",
                    "implementations/strassen_over_integers.py:bmm_strassen", n)
        rows.append(f"n={n}: {a}/{b} (padded size {s}: {7 ** int(math.log2(s // 16)) * 4096})")
    RESULTS.append((g, "Strassen counts at non-powers of two (matmul/boolean)", "INFO", "; ".join(rows)))
    print(f"[{g}] INFO     Strassen non-powers of two (matmul/boolean): " + "; ".join(rows), flush=True)
    rows = []
    for n in (33, 40, 48, 63, 65, 96, 100, 127, 129):
        s = 1 << (n - 1).bit_length()
        a = measure("integer-multiplication-schoolbook-vs-karatsuba", "implementations/karatsuba.py:multiply_karatsuba",
                    n)
        rows.append(f"n={n}: {a} (form at the next power of two {s}: {3 ** int(math.log2(s // 32)) * 1024})")
    RESULTS.append((g, "Karatsuba counts at non-powers of two (no padding: L splits into L//2, L-L//2)", "INFO",
                    "; ".join(rows)))
    print(f"[{g}] INFO     Karatsuba non-powers of two (no padding; L splits into L//2, L-L//2): " + "; ".join(rows),
          flush=True)
    rows = []
    for n in (3, 5, 6, 7, 9, 100, 1000):
        a = measure("polynomial-multiplication-naive-vs-ntt", "implementations/ntt.py:polymul_ntt", n)
        rows.append(f"n={n}: {a}")
    RESULTS.append((g, "NTT counts at non-powers of two", "INFO", "; ".join(rows)))
    print(f"[{g}] INFO     NTT non-powers of two: " + "; ".join(rows), flush=True)


# ----------------------------------------------------------------------------------------------------------------

GROUPS = {"strings": group_strings, "sorting": group_sorting, "algebra": group_algebra, "expdp": group_expdp,
          "query": group_query, "extra": group_extra}


def main(argv):
    pr = set_below_normal_priority()
    print(f"Python {sys.version.split()[0]}; below-normal priority: {pr}", flush=True)
    chosen = argv or list(GROUPS)
    t0 = time.perf_counter()
    for name in chosen:
        t = time.perf_counter()
        GROUPS[name]()
        print(f"--- group {name}: {time.perf_counter() - t:.1f} s", flush=True)
    bad = [r for r in RESULTS if r[2] == "MISMATCH"]
    print(f"\nSUMMARY: {len(RESULTS)} checks, {sum(r[2] == 'OK' for r in RESULTS)} OK, {len(bad)} with mismatches "
          f"inside the stated domain, {sum(r[2] == 'INFO' for r in RESULTS)} info; {time.perf_counter() - t0:.1f} s")
    for r in bad:
        print("  MISMATCH:", r[1], "|", r[3])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
