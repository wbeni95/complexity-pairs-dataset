"""Exact operation counts for pairs/optimal-bst-recursion-vs-dp-vs-knuth (deterministic).

Run from the repository root:  python experiments/2026-10-07b_optimal_bst_counts.py

What is counted: COMPARISONS of two cost values (<, <=, >, >=) made by the unchanged implementations, through the
harness's CountingInt (the V2 measure), plus additions (reported only) and, for the plain recursion, the number
of calls of its inner function cost(i, j) (counted with sys.setprofile, without touching the code).

Part 1  closed forms, checked for every n and family listed:
        plain recursion  calls = 3^n, comparisons = (3^(n-1) - 1)/2 (n >= 1)            [proven, see below]
        cubic DP         comparisons = (n+1) n (n-1)/6 on every input                     [proven]
        Knuth            comparisons = sum_{L=2..n} (r[n-L+1][n] - r[0][L-1]) (r = largest optimal roots,
                         computed here by a separate cubic DP)                            [proven, telescoping]
                         and = (n-1)^2 on the heavy-ends family (V2 family)               [proven, see harness]
        Proofs: recursion: C(m) = (m-1) + 2 sum_{k<m} C(k), C(0) = 0, so C(m) = 3 C(m-1) + 1 for m >= 2, C(1) = 0;
        calls K(m) = 1 + 2 sum_{k<m} K(k), K(0) = 1, so K(m) = 3 K(m-1) = 3^m. Cubic: an interval of length L makes
        L - 1 comparisons, sum_L (n-L+1)(L-1) = C(n+1, 3). Knuth: an interval (i, j), L = j-i >= 2, makes
        r[i+1][j] - r[i][j-1] comparisons; summing over i telescopes.
Part 2  Knuth's count on other families (random, skewed, all-zero, ...) for n = 32..512 and the fitted alpha
        against n^2 and the rivals.
Part 3  validator-style alphas (least-squares slope of log count vs log cost) of the exact closed forms over the
        entry's n_values, for the claims and the rivals; used to choose the tolerance.
Part 4  monotonicity r[i][j-1] <= r[i][j] <= r[i+1][j] of the largest optimal roots on the Part-1 instances.

Outcome (2026-10-07, this script's output; deterministic):
Part 1: every closed form holds exactly, 0 mismatches. Recursion n = 0..11 on families small/zero/wide: calls
        1, 3, 9, ..., 177147 = 3^n; comparisons 0, 0, 1, 4, 13, 40, 121, 364, 1093, 3280, 9841, 29524; additions
        0, 4, 16, 51, 156, 471, 1416, 4251, 12756, 38271, 114816, 344451 = (35 * 3^(n-2) - 3)/2 for n >= 2 (read off
        the data, not used for V2). Cubic DP and Knuth, n = 0..40 on all 10 V1 families: cubic comparisons
        C(n+1, 3) (165 at n = 10, 10660 at n = 40), cubic additions n(n+1)(n+2)/6 + 3n(n+1)/2 - n (375, 13900;
        read off, consistent with the code); Knuth comparisons = the telescoped root sum on every instance (e.g.
        n = 40: bits 746, small 819, zero 780, wide 802, one_heavy 591, geometric 809, heavy_ends 1521 = 39^2),
        Knuth additions = comparisons + 2n^2. Heavy-ends n = 48, 64, 96, 128: 2209, 3969, 9025, 16129 = (n-1)^2.
Part 2: Knuth comparisons for n = 32, 64, 128, 256, 512 (count/n^2 at n = 512; alpha vs n^2, n^3, n, n log n,
        n^2 log n):
        small      [520, 2128, 8058, 32472, 130090]   0.4963  0.993 0.662 1.987 1.640 0.898
        wide       [486, 1942, 8073, 31973, 134033]   0.5113  1.013 0.675 2.026 1.672 0.916
        one_heavy  [616, 1768, 6372, 29528, 159670]   0.6091  1.005 0.670 2.010 1.657 0.908
        geometric  [518, 2071, 8245, 32878, 131316]   0.5009  0.998 0.665 1.996 1.648 0.903
        zero       [496, 2016, 8128, 32640, 130816]   0.4990  1.005 0.670 2.010 1.660 0.909  (= n(n-1)/2)
        gaps_only  [536, 1993, 8406, 32690, 131049]   0.4999  0.995 0.663 1.990 1.643 0.900
        keys_only  [518, 2188, 8226, 34315, 132832]   0.5067  0.999 0.666 1.998 1.649 0.903
        heavy_ends [961, 3969, 16129, 65025, 261121]  0.9961  1.010 0.674 2.021 1.668 0.914  (= (n-1)^2)
        count/n^2 ranges over 0.3889 (one_heavy, n = 128) .. 0.9961 across all rows.
Part 3: recursion n = 5..11: 3^n 1.0015, 2^n 1.5874, 4^n 0.7937, 4^n/n^1.5 0.9232, n 3^n 0.8955;
        cubic DP n = 16..128: n^3 1.0006, n^2 1.5009, n^4 0.7504, n^3 log n 0.9184;
        Knuth n = 32..512: n^2 1.0103, n^3 0.6735, n 2.0206, n log n 1.6681, n^2 log n 0.9138.
        Tolerance 0.04 chosen: the claims are within 0.0103 of 1 (and every Part-2 family within 0.013), the
        nearest declared rival is 0.077 away (4^n/n^1.5 for the recursion).
Part 4: 0 monotonicity violations.
"""
import importlib.util
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENTRY = ROOT / "pairs" / "optimal-bst-recursion-vs-dp-vs-knuth"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


H = load(ENTRY / "harness.py", "obst_harness")
REC = load(ENTRY / "implementations" / "recursion.py", "obst_rec").obst_recursive
CUB = load(ENTRY / "implementations" / "cubic_dp.py", "obst_cub").obst_cubic
KNU = load(ENTRY / "implementations" / "knuth.py", "obst_knu").obst_knuth


def counting(inst):
    p, q = inst
    return tuple(H.CountingInt(x) for x in p), tuple(H.CountingInt(x) for x in q)


def run_counted(fn, inst):
    """Return (value, comparisons, additions) for one run on a CountingInt copy of inst."""
    ci = counting(inst)
    H.reset_counters()
    out = fn(ci)
    comps, adds = H.counters()
    value = out.v if isinstance(out, H.CountingInt) else out
    return value, comps, adds


def recursion_calls(inst):
    calls = 0

    def prof(frame, event, arg):
        nonlocal calls
        if event == "call" and frame.f_code.co_name == "cost" and frame.f_code.co_filename.endswith("recursion.py"):
            calls += 1

    sys.setprofile(prof)
    try:
        REC(inst)
    finally:
        sys.setprofile(None)
    return calls


def largest_roots(inst):
    """Separate cubic DP returning the table of LARGEST optimal roots (plain ints)."""
    p, q = inst
    n = len(p)
    c = [[0] * (n + 1) for _ in range(n + 1)]
    w = [[0] * (n + 1) for _ in range(n + 1)]
    r = [[None] * (n + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        w[i][i] = q[i]
    for L in range(1, n + 1):
        for i in range(n - L + 1):
            j = i + L
            w[i][j] = w[i][j - 1] + p[j - 1] + q[j]
            vals = [c[i][k - 1] + c[k][j] for k in range(i + 1, j + 1)]
            m = min(vals)
            r[i][j] = i + 1 + max(t for t, v in enumerate(vals) if v == m)
            c[i][j] = w[i][j] + m
    return r


def fit_slope(xs, ys):
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx


def alpha(ns, values, cost):
    return fit_slope([math.log(cost(n)) for n in ns], [math.log(v) for v in values])


def part1():
    print("Part 1: closed forms")
    bad = 0
    # plain recursion
    for fam in ("small", "zero", "wide"):
        for n in range(0, 12):
            inst = H._instance(n, random.Random(f"rec|{fam}|{n}"), fam)
            val, comps, adds = run_counted(REC, inst)
            calls = recursion_calls(inst)
            want_c = (3 ** (n - 1) - 1) // 2 if n >= 1 else 0
            ok = calls == 3 ** n and comps == want_c and val == CUB(inst)
            bad += not ok
            if fam == "small":
                print(f"  recursion n={n:2d}: calls={calls} (3^n={3 ** n}), comparisons={comps} "
                      f"((3^(n-1)-1)/2={want_c}), additions={adds}  {'ok' if ok else 'MISMATCH'}")
    # cubic DP and Knuth on all V1 families
    mono_viol = 0
    for fam in H.FAMILIES:
        for n in list(range(0, 41)):
            inst = H._instance(n, random.Random(f"dp|{fam}|{n}"), fam)
            v1, c1, a1 = run_counted(CUB, inst)
            v2, c2, a2 = run_counted(KNU, inst)
            r = largest_roots(inst)
            want_knuth = sum(r[n - L + 1][n] - r[0][L - 1] for L in range(2, n + 1))
            ok = v1 == v2 and c1 == (n + 1) * n * (n - 1) // 6 and c2 == want_knuth
            if fam == "heavy_ends":
                ok = ok and c2 == (n - 1) ** 2 if n >= 1 else ok
            bad += not ok
            for i in range(n + 1):
                for j in range(i + 2, n + 1):
                    if not (r[i][j - 1] <= r[i][j] <= r[i + 1][j]):
                        mono_viol += 1
            if n in (10, 40):
                print(f"  {fam:10s} n={n:2d}: cubic comps={c1} (C(n+1,3)={(n + 1) * n * (n - 1) // 6}), adds={a1}; "
                      f"knuth comps={c2} (telescoped={want_knuth}), adds={a2}  {'ok' if ok else 'MISMATCH'}")
    for n in (48, 64, 96, 128):
        inst = H._heavy_ends(n, random.Random(f"he|{n}"), int)
        v2, c2, a2 = run_counted(KNU, inst)
        ok = c2 == (n - 1) ** 2
        bad += not ok
        print(f"  heavy_ends n={n}: knuth comps={c2} ((n-1)^2={(n - 1) ** 2})  {'ok' if ok else 'MISMATCH'}")
    print(f"  mismatches: {bad}")
    print(f"Part 4: monotonicity violations of the largest-optimal-root table: {mono_viol}")


def part2():
    print("Part 2: Knuth comparisons on other families, n = 32..512")
    ns = [32, 64, 128, 256, 512]
    rivals = {"n**2": lambda n: n ** 2, "n**3": lambda n: n ** 3, "n": lambda n: n,
              "n*log(n)": lambda n: n * math.log(n), "n**2*log(n)": lambda n: n * n * math.log(n)}
    for fam in ("small", "wide", "one_heavy", "geometric", "zero", "gaps_only", "keys_only", "heavy_ends"):
        vals = []
        for n in ns:
            inst = H._instance(n, random.Random(f"fam|{fam}|{n}"), fam)
            vals.append(run_counted(KNU, inst)[1])
        ratios = ", ".join(f"{v / n ** 2:.4f}" for n, v in zip(ns, vals))
        al = ", ".join(f"{k}: {alpha(ns, vals, f):.3f}" for k, f in rivals.items())
        print(f"  {fam:10s} counts={vals}  count/n^2=[{ratios}]  alpha {al}")


def part3():
    print("Part 3: alphas of the exact closed forms over the entry's n_values")
    rec_ns = [5, 6, 7, 8, 9, 10, 11]
    cub_ns = [16, 32, 64, 128]
    knu_ns = [32, 64, 128, 256, 512]
    rec = [(3 ** (n - 1) - 1) / 2 for n in rec_ns]
    cub = [(n + 1) * n * (n - 1) / 6 for n in cub_ns]
    knu = [(n - 1) ** 2 for n in knu_ns]
    for name, ns, vals, costs in (
        ("recursion", rec_ns, rec, {"3**n": lambda n: 3 ** n, "2**n": lambda n: 2 ** n, "4**n": lambda n: 4 ** n,
                                    "4**n/n**1.5": lambda n: 4 ** n / n ** 1.5, "n*3**n": lambda n: n * 3 ** n}),
        ("cubic DP", cub_ns, cub, {"n**3": lambda n: n ** 3, "n**2": lambda n: n ** 2, "n**4": lambda n: n ** 4,
                                   "n**3*log(n)": lambda n: n ** 3 * math.log(n)}),
        ("Knuth", knu_ns, knu, {"n**2": lambda n: n ** 2, "n**3": lambda n: n ** 3, "n": lambda n: n,
                                "n*log(n)": lambda n: n * math.log(n), "n**2*log(n)": lambda n: n * n * math.log(n)}),
    ):
        print(f"  {name:9s} n={ns}: " + ", ".join(f"{k}: {alpha(ns, vals, f):.4f}" for k, f in costs.items()))


if __name__ == "__main__":
    part1()
    part2()
    part3()
