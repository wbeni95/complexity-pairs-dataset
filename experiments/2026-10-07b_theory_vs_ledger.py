#!/usr/bin/env python3
"""Recorded query / operation counts against exact closed forms (deviation analysis, 2026-10-07b).

For every V2 series with measure "reported" in the ledger, compare each recorded value with the exact value
(deterministic algorithms) or the exact expectation (randomized ones) predicted by theory, and compute the
log-log slope alpha that the EXACT predictions would give over the same n values (what the validator's fit
"should" see). Closed forms used:

  Bernstein-Vazirani      classical n, quantum 1
  Deutsch-Jozsa           classical deterministic 2^(n-1) + 1 (worst case), randomized K = 20, quantum 1
  minimum finding         classical scan N = 2^n
  Grover, quantum         floor((pi/4) 2^(n/2)) iterations + 1 confirming classical query (RL-013)
  Grover, classical       uniform random order with one marked item: E = (N + 1)/2, Var = (N^2 - 1)/12
  Simon, quantum          E(n) = sum_{j=1}^{n-1} 1/(1 - 2^-j) (RL-015); Var = sum_j 2^-j/(1 - 2^-j)^2
                          (sum of independent geometric waiting times with success 1 - 2^-j)
  Simon classical and     birthday search on a uniformly random 2-to-1 function, N = 2^n:
  collision classical     P(Q > 0) = P(Q > 1) = 1, P(Q > q+1) = P(Q > q) (N - 2q)/(N - q);
                          E = sum_q P(Q > q), E[Q^2] = sum_q (2q + 1) P(Q > q)  (same recursion as
                          experiments/2026-10-07_collision_expected_queries.py, re-implemented here)
  collision BHT           k + P_nc(k) * lib.qsearch.expected_cost_{known,exponential}(N, k, 2, 1),
                          k = max(1, round(2^(n/3))) (formula of experiments/2026-10-07_collision_expected_queries.py);
                          no variance available, so only the relative deviation is given
  Strassen (cutoff 16)    7^log2(n/16) * 16^3 scalar multiplications; schoolbook n^3 (RL-047)
  Durr-Hoyer              no exact expectation for the timed-out variant used in V2; compared with the
                          classical N at the same n only (crossover)

z = (recorded mean - exact expectation) / (sd / sqrt(samples)); |z| > 2 is flagged. Ledger values are the
means over `samples` seeded instances. All runs are checked; reported counts were identical in every run that
recorded them (checked here as well).

Deterministic, no simulation, no timing. Uses ledger/runs/*.json, lib/qsearch.py and tools/validate.py.

Result (2026-10-06 local time, five ledger files): see research/2026-10-07b_deviations.md section 3.
Summary: every deterministic count equals its closed form exactly (BV, DJ, minimum-finding classical,
Grover quantum, Strassen, schoolbook). Randomized means: all |z| < 2; largest exact-variance |z| is Simon
quantum n = 2 (z = -1.57, 1.65 vs E = 2); the exact-E(n) slope over the Simon n values is 1.0186 against the
recorded 1.121, a +1.80 s.e. deviation (delta-method s.e. 0.0569, 83% of Var(alpha) from n = 2). BBHT
collision: exact-expectation alpha 1.1544 (recorded 1.1640); exact expectations against 2^(n/2) give 0.7696,
inside the tolerance, so even noise-free data over n = 3..15 would not exclude the classical cost; known-t exact
0.6844 (rejected). Grover quantum: closed-form slope 0.9245 over n = 2..12 (= recorded), 0.9996 over 14..40.
Durr-Hoyer queries / classical N = 17.15, 7.43, 3.38, 1.64, 0.77 at n = 4..12.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
from validate import eval_cost, fit_slope  # noqa: E402
from lib import qsearch  # noqa: E402

RUNS = sorted((REPO / "ledger" / "runs").glob("*.json"))


def birthday_moments(N):
    e, e2, p, q = 0.0, 0.0, 1.0, 0
    while p > 0:
        e += p
        e2 += (2 * q + 1) * p
        if q >= 1:
            p *= (N - 2 * q) / (N - q)
        q += 1
    return e, e2 - e * e


def p_no_collision(N, q):
    p = 1.0
    for i in range(1, q):
        p *= (N - 2 * i) / (N - i)
    return p


def bht_expect(n, kind):
    N = 1 << n
    k = max(1, round(2 ** (n / 3)))
    tail = (qsearch.expected_cost_known(N, k, 2, 1) if kind == "known"
            else qsearch.expected_cost_exponential(N, k, 2, 1))
    return k + p_no_collision(N, k) * tail


def simon_moments(n):
    e = sum(1 / (1 - 2.0 ** -j) for j in range(1, n))
    v = sum(2.0 ** -j / (1 - 2.0 ** -j) ** 2 for j in range(1, n))
    return e, v


def model(eid, alg, n):
    """Return (expected value, variance or None, exact_flag)."""
    N = 2 ** n
    a = alg.lower()
    if eid.startswith("bernstein"):
        return (1.0, 0.0, True) if "quantum" in a else (float(n), 0.0, True)
    if eid.startswith("deutsch"):
        if "quantum" in a:
            return 1.0, 0.0, True
        if "randomized" in a:
            return 20.0, 0.0, True
        return float(2 ** (n - 1) + 1), 0.0, True
    if eid.startswith("minimum-finding"):
        if "classical" in a:
            return float(N), 0.0, True
        return None
    if eid.startswith("grover"):
        if "classical" in a:
            return (N + 1) / 2, (N * N - 1) / 12, False
        return float(math.floor(math.pi / 4 * 2 ** (n / 2)) + 1), 0.0, True
    if eid.startswith("simon"):
        if "quantum" in a:
            e, v = simon_moments(n)
            return e, v, False
        e, v = birthday_moments(N)
        return e, v, False
    if eid.startswith("collision"):
        if "classical" in a:
            e, v = birthday_moments(N)
            return e, v, False
        # NOTE: test "exponential" first: the exponential variant's name contains "unknown", which contains
        # "known" (a first version of this script tested "known" first and silently reported the known-t
        # expectations for the exponential variant; caught by comparing with research/2026-10-07_quantum_entries.md).
        if "exponential" in a:
            return bht_expect(n, "exponential"), None, False
        return bht_expect(n, "known"), None, False
    if eid.startswith("matrix-multiplication"):
        if a == "strassen":
            return float(7 ** round(math.log2(n / 16)) * 16 ** 3), 0.0, True
        return float(n ** 3), 0.0, True
    return None


def main():
    series = {}
    for p in RUNS:
        d = json.loads(p.read_text(encoding="utf-8"))
        for e in d["entries"]:
            for m in e.get("v2", []) or []:
                if m["measure"] == "reported":
                    series.setdefault((e["id"], m["algorithm"]), []).append((p.stem, m))
    print(f"reported-count series: {len(series)}")
    for (eid, alg), lst in sorted(series.items()):
        vals_sets = {tuple(m["values"]) for _, m in lst}
        stem, m = lst[-1]
        print(f"\n== {eid} / {alg}  [runs: {len(lst)}, distinct value vectors across runs: {len(vals_sets)}]")
        print(f"   claimed cost {m['cost']}, samples {m['samples']}, recorded alpha "
              f"{'const' if m['alpha'] is None else format(m['alpha'], '.4f')}")
        exp_vals = []
        for n, v in zip(m["n_values"], m["values"]):
            mod = model(eid, alg, n)
            if mod is None:
                print(f"   n={n:3d} recorded {v:12.4f}   (no exact model)")
                exp_vals.append(None)
                continue
            e, var, exact = mod
            exp_vals.append(e)
            if exact:
                flag = "EXACT MATCH" if abs(v - e) < 1e-9 else f"MISMATCH (diff {v - e:+.6g})"
                print(f"   n={n:3d} recorded {v:12.4f}   predicted {e:12.4f}   {flag}")
            elif var is not None and var > 0:
                se = math.sqrt(var / m["samples"])
                z = (v - e) / se
                print(f"   n={n:3d} recorded {v:12.4f}   E = {e:12.4f}   rel {v / e - 1:+.4f}   s.e. {se:9.4f}   "
                      f"z = {z:+.2f}{'   <-- |z| > 2' if abs(z) > 2 else ''}")
            else:
                print(f"   n={n:3d} recorded {v:12.4f}   E = {e:12.4f}   rel {v / e - 1:+.4f}   (no variance)")
        if m["alpha"] is not None and all(x is not None for x in exp_vals):
            xs = [math.log(eval_cost(m["cost"], n)) for n in m["n_values"]]
            a_exact = fit_slope(xs, [math.log(x) for x in exp_vals])
            print(f"   alpha of the EXACT predictions over these n: {a_exact:.4f}  (recorded {m['alpha']:.4f}, "
                  f"difference {m['alpha'] - a_exact:+.4f})")
            # delta-method s.e. of the fitted alpha from the exact per-n variance (randomized series only)
            mods = [model(eid, alg, n) for n in m["n_values"]]
            if all(md is not None and md[1] is not None and md[1] > 0 for md in mods):
                xb = sum(xs) / len(xs)
                sxx = sum((x - xb) ** 2 for x in xs)
                var_a = sum(((x - xb) / sxx) ** 2 * (md[1] / md[0] ** 2) / m["samples"] for x, md in zip(xs, mods))
                se_a = math.sqrt(var_a)
                contrib = [((x - xb) / sxx) ** 2 * (md[1] / md[0] ** 2) / m["samples"] / var_a for x, md in zip(xs, mods)]
                print(f"   predicted s.e. of alpha (delta method, {m['samples']} samples): {se_a:.4f}; "
                      f"(recorded - exact)/s.e. = {(m['alpha'] - a_exact) / se_a:+.2f}; share of Var(alpha) from "
                      f"each n: " + " ".join(f"{c:.2f}" for c in contrib))
            if len(m["n_values"]) > 2:
                a_drop = fit_slope(xs[1:], [math.log(v) for v in m["values"][1:]])
                a_drop_exact = fit_slope(xs[1:], [math.log(x) for x in exp_vals[1:]])
                print(f"   without the smallest n: recorded-data alpha {a_drop:.4f}, exact alpha {a_drop_exact:.4f}")
    # BHT: no closed-form variance. Approximate z with the per-n sd implied by the agent's run-2 table in
    # research/2026-10-07_quantum_entries.md (s.e. x sqrt(samples); agent report, not re-run here).
    rep = {"known": {3: (0.0164, 4000), 6: (0.0395, 4000), 9: (0.0485, 4000), 12: (0.0962, 2000), 15: (0.4752, 300)},
           "exponential": {3: (0.0397, 4000), 6: (0.0870, 4000), 9: (0.2164, 4000), 12: (0.5917, 2000), 15: (3.1143, 300)}}
    for (eid, alg), lst in sorted(series.items()):
        if not eid.startswith("collision") or "classical" in alg.lower():
            continue
        kind = "exponential" if "exponential" in alg.lower() else "known"
        m = lst[-1][1]
        print(f"\n== {eid} / {kind}: approximate z with sd from the agent's run-2 table")
        for n, v in zip(m["n_values"], m["values"]):
            se_rep, s_rep = rep[kind][n]
            sd = se_rep * math.sqrt(s_rep)
            e = bht_expect(n, kind)
            z = (v - e) / (sd / math.sqrt(m["samples"]))
            print(f"   n={n:3d} recorded {v:9.4f}   E = {e:9.4f}   sd ~ {sd:7.3f}   z ~ {z:+.2f}")
    # Durr-Hoyer vs classical N at the same n
    for (eid, alg), lst in series.items():
        if eid.startswith("minimum-finding") and "durr" in alg.lower():
            m = lst[-1][1]
            print("\n== Durr-Hoyer recorded queries vs classical N at the same n")
            for n, v in zip(m["n_values"], m["values"]):
                print(f"   n={n:3d} quantum {v:10.1f}   classical N = {2 ** n:6d}   ratio {v / 2 ** n:.3f}")
    # Simon classical vs collision classical: the same model, compare recorded means at common n
    print("\n== exact-E slopes over alternative ranges (pre-asymptotic check)")
    for n_lo, n_hi in [(2, 10), (3, 10), (4, 10), (2, 30), (10, 30)]:
        ns = list(range(n_lo, n_hi + 1))
        a = fit_slope([math.log(n) for n in ns], [math.log(simon_moments(n)[0]) for n in ns])
        print(f"   Simon E(n) vs n over n = {n_lo}..{n_hi}: alpha = {a:.4f}")
    ns3 = [3, 6, 9, 12, 15]
    ex = [math.log(bht_expect(n, "exponential")) for n in ns3]
    print(f"   BBHT exact expectations vs 2^(n/2) over n = 3..15: alpha = {fit_slope([n / 2 * math.log(2) for n in ns3], ex):.4f}; "
          f"BHT known-t exact vs 2^(n/2): {fit_slope([n / 2 * math.log(2) for n in ns3], [math.log(bht_expect(n, 'known')) for n in ns3]):.4f}")
    ns = [2, 4, 6, 8, 10, 12]
    a = fit_slope([n / 2 * math.log(2) for n in ns], [math.log(math.floor(math.pi / 4 * 2 ** (n / 2)) + 1) for n in ns])
    print(f"   Grover floor(pi/4 2^(n/2)) + 1 vs 2^(n/2) over n = 2..12 (even): alpha = {a:.4f}")
    ns2 = list(range(14, 41, 2))
    a = fit_slope([n / 2 * math.log(2) for n in ns2], [math.log(math.floor(math.pi / 4 * 2 ** (n / 2)) + 1) for n in ns2])
    print(f"   same over n = 14..40 (even): alpha = {a:.4f}")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
