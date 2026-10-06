#!/usr/bin/env python3
"""(c) Exact Boolean-function measures for small n, and the polynomial-method lower bound behind Grover.

Questions:
  1. Does the exact approximate degree adeg_{1/3}(OR_n) grow like sqrt(n), the Omega(sqrt N) that makes Grover
     optimal via Q_2(f) >= adeg(f)/2 (Beals et al. 2001; Nisan-Szegedy 1994)? Exact values for n = 1..64 and
     selected n up to 256, each with a primal polynomial and a dual certificate that prove optimality.
  2. Parity: exact degree n and approximate degree n; majority: approximate degree linear in n; threshold
     functions against Paturi's Theta(sqrt(n (n - Gamma))).
  3. All Boolean functions of 3 and 4 variables up to NPN equivalence: class counts (published: 14 and 222,
     OEIS A000370 [recalled]); D, deg, s, bs, C, adeg (exact LP) for every class; mechanical checks of proven
     inequalities (Huang 2019: deg <= s^2; s <= bs <= C <= D; deg <= D; bs <= 2 deg^2 (Nisan-Szegedy)); the
     symmetrisation theorem (multilinear LP == univariate exchange for symmetric functions); and the largest gaps
     between D and the polynomial-method quantum lower bound ceil(adeg/2) among 4-bit functions.
  4. Cross-check of the two exact solvers (exchange algorithm vs simplex LP) on small profiles.

Exact rational arithmetic throughout (methods/boolean.py, methods/lp.py). Deterministic (no randomness).
Runtime: about 30 s (most of it the 222-class LP), one process, below-normal priority.

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06d_meth_boolean_measures.py
"""
from __future__ import annotations

import math
import sys
import time
from fractions import Fraction
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from methods import boolean as bf  # noqa: E402
from methods import fitting as ft  # noqa: E402
from methods.lp import solve_lp  # noqa: E402

try:
    from search.machine import set_below_normal_priority
    set_below_normal_priority()
except Exception:  # pragma: no cover
    pass

EPS = Fraction(1, 3)


def part1() -> None:
    print("=== Part 1: adeg_{1/3}(OR_n), exact (exchange algorithm; primal + dual certificate at every d)")
    ns = list(range(1, 65)) + [80, 96, 128, 160, 192, 256]
    vals = {}
    t0 = time.perf_counter()
    for n in ns:
        d, errs = bf.adeg_symmetric([0] + [1] * n, EPS)
        vals[n] = (d, errs[-1], errs[-2] if len(errs) > 1 else None)
    print(f"  computed for {len(ns)} values of n in {time.perf_counter() - t0:.1f} s; convention: adeg = least d "
          f"with E_d <= 1/3 (ties count)")
    line = ", ".join(f"{n}:{vals[n][0]}" for n in ns)
    print(f"  n:adeg  {line}")
    ties = [n for n in ns if vals[n][1] == EPS]
    print(f"  n with E_d exactly 1/3 at the threshold degree (tie): {ties}")
    E1 = [n for n in range(2, 65) if bf.best_uniform_error([0] + [1] * n, 1)["error"] != Fraction(n - 1, 2 * n)]
    print(f"  closed form observed for d = 1: E_1(OR_n) = (n-1)/(2n) for all n = 2..64? "
          f"{'yes' if not E1 else 'NO, fails at ' + str(E1)}")
    # fits
    xs = [math.sqrt(n) for n in ns]
    ys = [vals[n][0] for n in ns]
    c = sum(x * y for x, y in zip(xs, ys)) / sum(x * x for x in xs)
    big = [n for n in ns if n >= 16]
    a = ft.slope([math.log(n) for n in big], [math.log(vals[n][0]) for n in big])
    print(f"  least-squares adeg ~ c sqrt(n): c = {c:.4f}; log-log slope over n >= 16: {a:.4f} (theory: 1/2)")
    lb_ok = all(vals[n][0] >= math.sqrt(n / 6) for n in ns)
    print(f"  Nisan-Szegedy lower bound adeg(OR_n) >= sqrt(n/6) [statement recalled]: holds for all computed n: "
          f"{lb_ok}")
    print(f"  => Grover optimality via polynomials: Q_2(OR_n) >= adeg/2, e.g. n = 256: >= {vals[256][0] / 2}")


def part2() -> None:
    print("\n=== Part 2: parity, majority, thresholds")
    par = []
    for n in range(1, 17):
        tt = bf.PARITY(n) if n <= 12 else None
        dg = bf.deg(tt, n) if tt else None
        ad, _ = bf.adeg_symmetric([k % 2 for k in range(n + 1)], EPS)
        par.append((n, dg, ad))
    print("  parity (n, deg via Moebius for n <= 12, adeg_{1/3}): " + ", ".join(f"({n},{d},{a})" for n, d, a in par))
    maj = [(n, bf.adeg_symmetric([int(2 * k > n) for k in range(n + 1)], EPS)[0]) for n in range(1, 42, 2)]
    print("  majority n:adeg  " + ", ".join(f"{n}:{a}" for n, a in maj))
    a = ft.slope([math.log(n) for n, _ in maj if n >= 9], [math.log(v) for n, v in maj if n >= 9])
    print(f"  majority log-log slope (n >= 9): {a:.4f} (Paturi: linear, slope 1)")
    n = 64
    rows = []
    for t in (1, 2, 4, 8, 16, 24, 32):
        F = [int(k >= t) for k in range(n + 1)]
        ad, _ = bf.adeg_symmetric(F, EPS)
        gamma = abs(2 * t - n - 1)
        rows.append((t, ad, ad / math.sqrt(n * (n - gamma))))
    print(f"  thresholds on n = {n} (f = 1 iff |x| >= t): t, adeg, adeg / sqrt(n (n - Gamma)) with "
          f"Gamma = |2t - n - 1|:")
    print("    " + "; ".join(f"t={t}: {ad}, {r:.3f}" for t, ad, r in rows))


def part3() -> None:
    print("\n=== Part 3: all functions on 3 and 4 variables, up to NPN equivalence")
    for n in (3, 4):
        t0 = time.perf_counter()
        reps = bf.npn_classes(n)
        print(f"  n = {n}: {len(reps)} NPN classes (published value: {14 if n == 3 else 222}, OEIS A000370 "
              f"[recalled]) [{time.perf_counter() - t0:.1f} s]")
    reps = bf.npn_classes(4)
    n = 4
    t0 = time.perf_counter()
    rows = []
    for tt in reps:
        r = {"tt": tt, "D": bf.D(tt, n), "deg": bf.deg(tt, n), "s": bf.sensitivity(tt, n),
             "bs": bf.block_sensitivity(tt, n), "C": bf.certificate_complexity(tt, n)}
        r["adeg"] = bf.adeg_general(tt, n, EPS)
        rows.append(r)
    print(f"  measures for the 222 classes computed in {time.perf_counter() - t0:.1f} s (adeg by exact LP)")
    checks = {
        "Huang 2019: deg <= s^2": all(r["deg"] <= r["s"] ** 2 for r in rows),
        "s <= bs <= C <= D": all(r["s"] <= r["bs"] <= r["C"] <= r["D"] for r in rows),
        "deg <= D": all(r["deg"] <= r["D"] for r in rows),
        "adeg <= deg": all(r["adeg"] <= r["deg"] for r in rows),
        "bs <= 2 deg^2 (Nisan-Szegedy)": all(r["bs"] <= 2 * r["deg"] ** 2 for r in rows),
        "D <= C * bs [recalled: Beals et al. 2001]": all(r["D"] <= r["C"] * r["bs"] for r in rows),
    }
    for k, v in checks.items():
        print(f"    {k}: {'holds' if v else 'VIOLATED'} for all 222 classes")
    from collections import Counter
    for key in ("D", "deg", "adeg", "s", "bs", "C"):
        cnt = Counter(r[key] for r in rows)
        print(f"    distribution of {key:4s}: " + ", ".join(f"{v}: {cnt[v]}" for v in sorted(cnt)))
    evasive = sum(r["D"] == 4 for r in rows)
    print(f"    classes with D = 4 (evasive): {evasive} of 222; classes with deg < D: "
          f"{sum(r['deg'] < r['D'] for r in rows)}")
    gaps = sorted(rows, key=lambda r: (r["D"] - math.ceil(r["adeg"] / 2), r["D"]), reverse=True)[:5]
    print("    largest gaps D - ceil(adeg/2) (D vs the polynomial-method quantum lower bound):")
    for r in gaps:
        code = sum(b << i for i, b in enumerate(r["tt"]))
        print(f"      truth table 0x{code:04x}: D={r['D']} deg={r['deg']} adeg={r['adeg']} s={r['s']} bs={r['bs']} "
              f"C={r['C']}")
    # symmetrisation theorem check on all symmetric 4-bit functions
    mism = 0
    for prof in range(1 << (n + 1)):
        F = [prof >> k & 1 for k in range(n + 1)]
        tt = bf.symmetric(n, lambda k: F[k])
        a1 = bf.adeg_general(tt, n, EPS)
        a2, _ = bf.adeg_symmetric(F, EPS)
        mism += a1 != a2
    print(f"    symmetrisation: multilinear LP adeg == univariate exchange adeg for all 32 symmetric 4-bit "
          f"functions: {mism == 0} ({mism} mismatches)")
    # T9 link: block sensitivity of OR_n
    print("    block sensitivity bs(OR_n), n = 1..5 (classical Omega(bs) randomized bound): "
          + ", ".join(str(bf.block_sensitivity(bf.OR(k), k)) for k in range(1, 6)))


def part4() -> None:
    print("\n=== Part 4: exchange algorithm vs simplex LP on univariate profiles (all 0/1 profiles, n <= 6, d <= 3)")
    agree = total = 0
    for n in range(2, 7):
        for prof in range(1 << (n + 1)):
            F = [prof >> k & 1 for k in range(n + 1)]
            for d in range(0, min(3, n - 1) + 1):
                ex = bf.best_uniform_error(F, d)
                A, b = [], []
                for k in range(n + 1):
                    row = [Fraction(k) ** j for j in range(d + 1)]
                    A.append(row + [-1]); b.append(F[k])
                    A.append([-v for v in row] + [-1]); b.append(-F[k])
                lp = solve_lp([0] * (d + 1) + [-1], A, b, free=range(d + 1))
                total += 1
                agree += (ex["error"] == -lp["value"]) and ex["certified"]
    print(f"  {agree} of {total} (profile, degree) cases: exchange optimum certified AND equal to the LP optimum")


def main() -> int:
    part1()
    part2()
    part3()
    part4()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
