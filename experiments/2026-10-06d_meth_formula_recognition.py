#!/usr/bin/env python3
"""(a) Formula recognition on the dataset's own exact counts: recurrence -> growth constant -> minimal polynomial.

Question: given only the exact cost counts of a slow algorithm in the dataset (calls of a plain recursion, or the
operation count that the entry's harness reports), can the cost's FORM be recovered mechanically, exactly, and
compared with the entry's claimed cost?

Pipeline per sequence (methods/recurrences.py, methods/exactalg.py; all exact over Q unless marked):
  1. counts a(n) for consecutive n, obtained from the entry's own implementation:
       - plain recursions: calls counted with sys.setprofile on the implementation (small n); a call-count
         recurrence read off the code is checked against those measured counts and then used to extend the
         sequence (stated per sequence: "measured n <= N, model beyond");
       - harness counts: harness.reported_cost(implementation(harness.generate_scaling(n, rng))), measured for
         every n used (no model).
  2. guess a recurrence: Berlekamp-Massey over Q (C-finite) or holonomic guessing (P-recursive), with held-out
     terms that the guess must reproduce;
  3. characteristic polynomial -> dominant real root lambda (Sturm isolation, exact rational interval of width
     1e-30) -> exact minimal polynomial (Kronecker factorisation) -> polynomial exponent theta (multiplicity - 1
     for C-finite, the exact Birkhoff-Trjitzinsky balance in Q(lambda) for P-recursive);
  4. independent "experimental mathematics" route: estimate lambda from the counts alone (ratio method with
     Richardson extrapolation, exact rationals), then guess its minimal polynomial with LLL from that estimate,
     and check whether it equals the exact one from step 3;
  5. compare (lambda, theta) with the entry's claimed cost.

Deterministic (counts do not depend on the instance for the families used; rng seeds fixed anyway).
Runtime: a few seconds on the maintainer's machine. Uses one process; below-normal priority.

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06d_meth_formula_recognition.py
"""
from __future__ import annotations

import math
import random
import sys
from fractions import Fraction
from functools import lru_cache
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.setrecursionlimit(10000)

from methods import exactalg as ea  # noqa: E402
from methods import recurrences as rc  # noqa: E402
from validate import load_callable, load_entry, load_module, resolve_in_repo  # noqa: E402

try:
    from search.machine import set_below_normal_priority
    set_below_normal_priority()
except Exception:  # pragma: no cover
    pass


# --------------------------------------------------------------------------------------------------------------
# Count sources
# --------------------------------------------------------------------------------------------------------------


def count_calls(fn, arg, code_name: str) -> int:
    """Number of Python-level calls of functions whose code object is named code_name while running fn(arg)."""
    n = 0

    def prof(frame, event, a):
        nonlocal n
        if event == "call" and frame.f_code.co_name == code_name:
            n += 1

    sys.setprofile(prof)
    try:
        fn(arg)
    finally:
        sys.setprofile(None)
    return n


def entry_impl(entry_rel: str, alg_name_prefix: str):
    d = REPO / entry_rel
    e = load_entry(d)
    alg = next(a for a in e["algorithms"] if a["name"].startswith(alg_name_prefix))
    return e, alg, load_callable(d, alg["implementation"]), d


def harness_counts(entry_rel: str, alg_prefix: str, ns: list[int]) -> list[int]:
    e, alg, fn, d = entry_impl(entry_rel, alg_prefix)
    harness = load_module(resolve_in_repo(d, e["test_harness"]["module"]))
    gen = getattr(harness, "generate_scaling", harness.generate)
    out = []
    for n in ns:
        rng = random.Random(f"{e['id']}|meth|{n}")
        inst = gen(n, rng)
        random.seed(f"{e['id']}|meth|{n}|{alg['name']}")
        out.append(int(harness.reported_cost(fn(inst))))
    return out


def fib_counts(N_measure: int, N: int):
    _, _, fn, _ = entry_impl("pairs/fibonacci-naive-vs-dp", "naive")
    measured = [count_calls(fn, n, "fib_naive") for n in range(N_measure + 1)]

    @lru_cache(None)
    def C(n):  # read off the code: one call, plus the two recursive calls for n >= 2
        return 1 if n < 2 else 1 + C(n - 1) + C(n - 2)

    model = [C(n) for n in range(N + 1)]
    return measured, model, 0


def edit_counts(N_measure: int, N: int):
    _, _, fn, _ = entry_impl("pairs/edit-distance-brute-vs-dp", "plain")
    rng = random.Random(20261006)
    measured = []
    for n in range(N_measure + 1):
        a = "".join(rng.choice("ACGT") for _ in range(n))
        b = "".join(rng.choice("ACGT") for _ in range(n))
        measured.append(count_calls(fn, (a, b), "d"))

    def model_n(n):
        @lru_cache(None)
        def C(i, j):  # d(i, j) returns at once on a boundary, else makes three recursive calls
            return 1 if i == n or j == n else 1 + C(i + 1, j) + C(i, j + 1) + C(i + 1, j + 1)
        return C(0, 0)

    return measured, [model_n(n) for n in range(N + 1)], 0


def matrix_chain_counts(N_measure: int, N: int):
    _, _, fn, _ = entry_impl("pairs/matrix-chain-recursion-vs-dp", "plain")
    rng = random.Random(7)
    measured = [count_calls(fn, [rng.randint(1, 9) for _ in range(n + 1)], "cost") for n in range(1, N_measure + 1)]

    @lru_cache(None)
    def C(m):  # chain of m matrices: one call, plus calls on both sides of every split
        return 1 if m == 1 else 1 + sum(C(k) + C(m - k) for k in range(1, m))

    return measured, [C(m) for m in range(1, N + 1)], 1


def obst_counts(N_measure: int, N: int):
    _, _, fn, _ = entry_impl("pairs/optimal-bst-recursion-vs-dp-vs-knuth", "plain")
    rng = random.Random(11)
    measured = []
    for n in range(0, N_measure + 1):
        p = [rng.randint(1, 9) for _ in range(n)]
        q = [rng.randint(1, 9) for _ in range(n + 1)]
        measured.append(count_calls(fn, (p, q), "cost"))

    @lru_cache(None)
    def C(m):  # cost(i, j) with j - i = m: one call, plus cost(i, k-1) and cost(k, j) for every root k
        return 1 if m == 0 else 1 + sum(C(k - 1) + C(m - k) for k in range(1, m + 1))

    return measured, [C(m) for m in range(0, N + 1)], 0


def synthetic_counts(folder: str, N_measure: int, N: int):
    d = REPO / folder
    mod = load_module(d / "implementations" / "naive.py")
    measured = [count_calls(mod.solve, n, "solve") for n in range(N_measure + 1)]
    coeffs, k = mod.COEFFS, len(mod.INIT)

    @lru_cache(None)
    def C(n):
        return 1 if n < k else 1 + sum(C(n - i) for i, c in enumerate(coeffs, 1) if c)

    return measured, [C(n) for n in range(N + 1)], 0


# --------------------------------------------------------------------------------------------------------------
# Analysis
# --------------------------------------------------------------------------------------------------------------


def lam_iv_lo(gr):
    return gr["lambda_interval"][0]


def dec(x: Fraction, digits: int = 15) -> str:
    return f"{float(x):.{digits}g}"


def analyse(label: str, seq: list[int], start: int, claim: str, claim_lambda_minpoly: list[int] | None,
            claim_theta: Fraction | None, source: str) -> dict:
    print(f"\n=== {label}")
    print(f"    source: {source}")
    print(f"    claimed cost (entry): {claim}")
    print(f"    terms: a({start}..{start + len(seq) - 1}) = {seq[:8]}{' ...' if len(seq) > 8 else ''}")
    res = {"label": label}
    g = rc.guess_c_finite(seq, holdout=4)
    if g:
        chi = g["charpoly"]
        print(f"    C-finite guess (Berlekamp-Massey over Q): order {g['order']}, a(n) = "
              + " + ".join(f"({c})a(n-{i + 1})" for i, c in enumerate(g["coeffs"]) if c)
              + f"; found from {g['terms_used']} terms, reproduces all {g['terms_checked']}")
    else:
        g = rc.search_p_recursive(seq, max_order=4, max_degree=4, start=start, extra=4, holdout=3)
        if not g:
            print("    NO recurrence found (C-finite up to order len/2 - 3; P-recursive order <= 4, degree <= 4)")
            res["recurrence"] = None
            return res
        print(f"    P-recursive guess: order {g['order']}, degree {g['degree']}: "
              + " + ".join(f"({ea.pstr(p, 'n')}) a(n-{i})" for i, p in enumerate(g["polys"])) + " = 0")
        print(f"      {g['equations']} equations for {g['unknowns']} unknowns, nullspace dim 1; "
              f"reproduces all {g['terms_checked']} terms (last 3 held out)")
        chi, D, alpha, beta = rc.p_recursive_characteristic(g)
        if alpha[0] == 0:
            print(f"    leading coefficients: deg p_0 < D = {D}: FACTORIAL-type growth (super-exponential); "
                  "the lambda^n n^theta formula does not apply")
            res.update(recurrence=g, factorial=True)
            return res
    gr = rc.growth_from_charpoly(chi)
    mp = gr["minpoly"]
    print(f"    characteristic polynomial: {ea.pstr(chi)}; factors over Z: "
          + " * ".join(f"({ea.pstr(f)})" for f in ea.factor_kronecker(chi)))
    print(f"    dominant real root lambda = {gr['lambda']:.15g} (exact interval of width 1e-30); minimal polynomial "
          f"{ea.pstr(mp)}; multiplicity {gr['multiplicity']}; dominance over the other roots: {gr['dominance']}")
    if g["kind"] == "C-finite":
        theta = Fraction(gr["multiplicity"] - 1)
        theta_s = f"{theta} (multiplicity - 1)"
    else:
        th = rc.theta_p_recursive(g, mp)
        theta = th[0] if len(th) <= 1 and th else (Fraction(0) if not th else None)
        theta_s = (str(theta) if theta is not None else "in Q(lambda): " + ea.pstr(th, "lambda")) + \
            " (exact balance at order 1/n)"
    tnum = rc.theta_numeric(seq, gr["lambda"], start=start, tail=6)
    print(f"    polynomial exponent theta = {theta_s}; numeric slope of log(a(n)/lambda^n) vs log n over the last 6 "
          f"terms: {tnum:.4f}")
    # independent route: ratio method + Richardson, then LLL
    lam_r, err_est = rc.richardson_with_error(seq, start, order=3)
    err = abs(lam_r - lam_iv_lo(gr))
    print(f"    ratio method (Richardson, order 3, from the counts only): lambda ~ {dec(lam_r, 15)}; "
          f"estimated error {float(err_est):.2e} (actual {float(err):.2e})")
    guess = ea.minpoly_by_lll(lam_r, max_degree=4, err=err_est)
    print(f"    LLL integer relation on that estimate (precision 10^-{max(1, math.floor(-math.log10(float(err_est))))}): "
          f"{ea.pstr(guess) if guess else 'none accepted'}")
    agree = guess is not None and ea.pint(guess) == ea.pint(mp)
    print(f"      -> {'AGREES with' if agree else ('no guess; consistent with' if guess is None else 'DIFFERS from')} "
          f"the exact minimal polynomial")
    lam_ok = claim_lambda_minpoly is not None and ea.pint(claim_lambda_minpoly) == ea.pint(mp)
    th_ok = claim_theta is not None and theta is not None and theta == claim_theta
    verdict = "MATCHES" if lam_ok and th_ok else ("lambda matches, theta differs" if lam_ok else "DIFFERS")
    print(f"    comparison with the claim: lambda {('OK' if lam_ok else 'NO')}, theta "
          f"{('OK' if th_ok else 'NO/not stated')} -> {verdict}")
    res.update(recurrence=g, minpoly=mp, theta=theta, lll_agrees=agree, verdict=verdict)
    return res


def main() -> int:
    results = []

    def model_check(name, measured, model, offset_label):
        k = len(measured)
        ok = measured == model[:k]
        print(f"[count model] {name}: measured calls for the first {k} sizes {measured[:6]}...; "
              f"model {'EQUALS' if ok else 'DIFFERS FROM'} the measured counts")
        if not ok:
            raise SystemExit("count model mismatch for " + name)

    m, model, s = fib_counts(22, 40)
    model_check("fibonacci naive", m, model, "n")
    results.append(analyse("Fibonacci, naive recursion: calls of fib_naive(n)", model, s,
                           "Theta(phi^n)", [-1, -1, 1], Fraction(0),
                           "pairs/fibonacci-naive-vs-dp naive.py; measured n <= 22, call-count model to n = 40"))

    m, model, s = edit_counts(7, 26)
    model_check("edit distance plain recursion", m, model, "n")
    results.append(analyse("Edit distance, plain recursion: calls of d(i, j) for two length-n strings", model, s,
                           "Theta(D(n, n)) = Theta((3 + 2 sqrt 2)^n / sqrt(n))", [1, -6, 1], Fraction(-1, 2),
                           "pairs/edit-distance-brute-vs-dp brute_force.py; measured n <= 7, model to n = 26"))

    m, model, s = matrix_chain_counts(10, 30)
    model_check("matrix chain plain recursion", m, model, "n")
    results.append(analyse("Matrix-chain ordering, plain recursion: calls of cost(i, j), n matrices", model, s,
                           "Theta(3^n)", [-3, 1], Fraction(0),
                           "pairs/matrix-chain-recursion-vs-dp recursion.py; measured n <= 10, model to n = 30"))

    m, model, s = obst_counts(9, 30)
    model_check("optimal BST plain recursion", m, model, "n")
    results.append(analyse("Optimal BST, plain recursion: calls of cost(i, j), n keys", model, s,
                           "Theta(3^n) on every input", [-3, 1], Fraction(0),
                           "pairs/optimal-bst-recursion-vs-dp-vs-knuth recursion.py; measured n <= 9, model to n = 30"))

    for folder, mp in [("synthetic/linear-recurrence-c1-0-1", [-1, 0, -1, 1]),
                       ("synthetic/linear-recurrence-c1-1-1", [-1, -1, -1, 1]),
                       ("synthetic/linear-recurrence-c1-1-1-1", [-1, -1, -1, -1, 1]),
                       ("synthetic/linear-recurrence-c2-3", [-1, -1, 1])]:
        m, model, s = synthetic_counts(folder, 18, 40)
        model_check(folder, m, model, "n")
        results.append(analyse(f"{folder}: calls of solve(n)", model, s,
                               "Theta(lambda^n), lambda the dominant root of the recurrence's characteristic "
                               "polynomial", mp, Fraction(0),
                               f"{folder} naive.py; measured n <= 18, model to n = 40"))

    ns = list(range(1, 17))
    seq = harness_counts("pairs/longest-increasing-subsequence", "subset", ns)
    results.append(analyse("LIS subset enumeration: element comparisons (harness count)", seq, 1,
                           "Theta(2^n n) on every input", [-2, 1], Fraction(1),
                           "harness.reported_cost, measured for every n = 1..16"))

    ns = list(range(1, 15))
    seq = harness_counts("pairs/regex-matching-backtracking-vs-thompson", "backtracking", ns)
    results.append(analyse("Regex backtracking on P_n = ((a?)^n a^n, a^n): symbol comparisons (harness count)", seq,
                           1, "n * 2**n (V2 cost expression)", [-2, 1], Fraction(1),
                           "harness.reported_cost, measured for every n = 1..14"))

    ns = list(range(2, 17))
    seq = harness_counts("pairs/global-min-cut-brute-vs-stoer-wagner", "brute", ns)
    results.append(analyse("Global min cut, brute force: weight additions + comparisons (harness count)", seq, 2,
                           "Theta(n^2 2^n)", [-2, 1], Fraction(2),
                           "harness.reported_cost, measured for every n = 2..16"))

    ns = list(range(1, 15))
    seq = harness_counts("pairs/subset-sum-zeta-transform-naive-vs-yates", "submask", ns)
    results.append(analyse("Zeta transform, submask enumeration: additions (harness count)", seq, 1,
                           "Theta(3^n)", [-3, 1], Fraction(0), "harness.reported_cost, measured for every n = 1..14"))

    # ---- limits of the method: factorial growth, and a sequence outside the holonomic class
    _, _, fn, _ = entry_impl("pairs/determinant-cofactor-vs-gaussian", "Laplace")
    rng = random.Random(5)
    measured = [count_calls(fn, [[rng.randint(0, 9) for _ in range(n)] for _ in range(n)], "_expand")
                for n in range(0, 9)]

    @lru_cache(None)
    def Ccof(k):  # _expand with k columns left: one call, plus k recursive calls with k - 1 columns
        return 1 if k == 0 else 1 + k * Ccof(k - 1)

    model = [Ccof(n) for n in range(0, 31)]
    model_check("determinant cofactor expansion", measured, model, "n")
    results.append(analyse("Determinant, cofactor expansion: calls of _expand, n x n matrix", model, 0,
                           "Theta(n!) field operations", None, None,
                           "pairs/determinant-cofactor-vs-gaussian cofactor.py; measured n <= 8, model to n = 30"))

    from math import comb
    ns = list(range(2, 8))
    measured = harness_counts("pairs/minimum-spanning-tree-brute-vs-kruskal", "enumeration", ns)
    formula = [(n - 1) * comb(n * (n - 1) // 2, n - 1) + n ** (n - 2) - 1 for n in range(2, 41)]
    ok = measured == formula[:len(measured)]
    print(f"[count model] MST enumeration: harness counts n = 2..7 {measured}; entry formula "
          f"(n-1) C(m, n-1) + n^(n-2) - 1 {'EQUALS' if ok else 'DIFFERS FROM'} them")
    if not ok:
        raise SystemExit("MST formula mismatch")
    results.append(analyse("MST, enumeration of (n-1)-edge subsets: weight operations (harness count)", formula, 2,
                           "n * C(n(n-1)/2, n-1) = 2^Theta(n log n)", None, None,
                           "harness.reported_cost measured n = 2..7; the entry's exact formula to n = 40"))

    print("\n=== summary")
    for r in results:
        print(f"  {r['label'][:78]:78s} -> {r.get('verdict', 'no recurrence' if r.get('recurrence') is None else 'factorial')}"
              + ("" if r.get("lll_agrees") is None else f"; LLL route {'agrees' if r['lll_agrees'] else 'no agreement'}"))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
