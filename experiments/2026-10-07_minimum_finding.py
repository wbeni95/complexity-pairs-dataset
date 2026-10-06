"""Experiment (2026-10-07, minimum-finding entry): Durr-Hoyer quantum minimum finding on lib/qsim.

A. The paper's "infinite algorithm" (no time-out, stopped when the threshold holds the minimum). By Durr-Hoyer
   Lemma 1 the element of rank r is ever chosen as threshold with probability 1/r, and then triggers one BBHT
   search with t = r - 1 marked items. Hence the EXACT expectations
       E_time    = sum_{r=2}^{N} (1/r) (lg N + I(r-1)),       I(t) = expected BBHT iterations
       E_queries = 1 + sum_{r=2}^{N} (1/r) B(r-1),           B(t) = expected BBHT queries (2 per iteration + 1 check)
   (lib.qsearch.expected_cost_exponential). Compared with the empirical means (z-scores) and with the paper's
   bound m0 = 45/4 sqrt(N) + 7/10 lg^2 N (Lemma 2, in time units).
B. The algorithm as published (time-out 22.5 sqrt N + 1.4 lg^2 N): empirical failure rate (Theorem 1 only
   guarantees success >= 1/2), with a one-sided 95% upper bound; mean and spread of the reported query count.
C. Where the quantum count drops below the classical N: means at n = 11, 12, 13 (few runs; each run costs
   seconds of simulation).
D. The slope alpha the V2 fit (cost 2**(n/2), n = 2, 4, 6, 8, 10) should see, from the part-B means, and the
   predicted standard error of the fitted alpha for the `samples` value in entry.json.

Deterministic (fixed seeds). Run from the repository root (several minutes):
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_minimum_finding.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Minimum finding").
"""
import importlib.util
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import qsearch  # noqa: E402

ENTRY = ROOT / "pairs" / "minimum-finding-classical-vs-quantum"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


harness = load("harness.py", "min_harness")
dh = load("implementations/durr_hoyer.py", "min_dh")


def exact_infinite(n):
    N = 1 << n
    e_time = sum((n + qsearch.expected_cost_exponential(N, r - 1, 1, 0)) / r for r in range(2, N + 1))
    e_q = 1 + sum(qsearch.expected_cost_exponential(N, r - 1, 2, 1) / r for r in range(2, N + 1))
    return e_time, e_q


def stats(xs):
    return statistics.fmean(xs), (statistics.stdev(xs) if len(xs) > 1 else 0.0)


print("A. Infinite algorithm: time and queries until the threshold holds the minimum")
for n, runs in ((2, 4000), (4, 4000), (6, 3000), (8, 2000), (10, 1000)):
    times, queries = [], []
    for k in range(runs):
        inst = harness.generate(n, random.Random(f"A|inst|{n}|{k}"))
        out = dh.durr_hoyer_run(inst, random.Random(f"A|alg|{n}|{k}"), budget=None, stop_value=0)
        assert out["index"] == inst[1].index(0)
        times.append(out["time"])
        queries.append(out["queries"])
    e_time, e_q = exact_infinite(n)
    m0 = 45 / 4 * math.sqrt(1 << n) + 7 / 10 * n * n
    (mt, st), (mq, sq) = stats(times), stats(queries)
    print(f"  n={n:2d} ({runs} runs): time {mt:8.2f} +- {st / math.sqrt(runs):5.2f} vs exact {e_time:8.2f} "
          f"(z = {(mt - e_time) / (st / math.sqrt(runs)):+.2f}); Lemma-2 bound m0 = {m0:7.2f} (exact/m0 = {e_time / m0:.3f}); "
          f"queries {mq:8.2f} +- {sq / math.sqrt(runs):5.2f} vs exact {e_q:8.2f} (z = {(mq - e_q) / (sq / math.sqrt(runs)):+.2f})")

print("\nB. Published algorithm (time-out 22.5 sqrt N + 1.4 lg^2 N): failures and query counts")
means = {}
for n, runs in ((2, 4000), (4, 4000), (6, 3000), (8, 2000), (10, 1000)):
    fails, queries, thr, meas = 0, [], [], []
    for k in range(runs):
        inst = harness.generate(n, random.Random(f"B|inst|{n}|{k}"))
        out = dh.durr_hoyer_run(inst, random.Random(f"B|alg|{n}|{k}"))
        fails += inst[1][out["index"]] != 0
        queries.append(out["queries"])
        thr.append(out["thresholds"])
        meas.append(out["measurements"])
    mq, sq = stats(queries)
    means[n] = (mq, sq)
    upper = 1 - 0.05 ** (1 / runs) if fails == 0 else float("nan")
    print(f"  n={n:2d} ({runs} runs): failures {fails} (rate {fails / runs:.5f}"
          + (f"; 95% upper bound {upper:.5f}" if fails == 0 else "") + f"); budget {dh.durr_hoyer_budget(n):.1f} time units; "
          f"queries mean {mq:.2f}, sd {sq:.2f} (classical: {1 << n}); thresholds {statistics.fmean(thr):.2f}, "
          f"measurements {statistics.fmean(meas):.2f}")

print("\nC. Crossover with the classical N queries")
for n, runs in ((11, 20), (12, 12), (13, 6)):
    qs, fails = [], 0
    for k in range(runs):
        inst = harness.generate(n, random.Random(f"C|inst|{n}|{k}"))
        out = dh.durr_hoyer_run(inst, random.Random(f"C|alg|{n}|{k}"))
        fails += inst[1][out["index"]] != 0
        qs.append(out["queries"])
    mq, sq = stats(qs)
    print(f"  n={n:2d} ({runs} runs): quantum queries mean {mq:.1f} (sd {sq:.1f}), classical {1 << n}, "
          f"ratio {mq / (1 << n):.3f}; failures {fails}")

print("\nD. Expected V2 slope against 2**(n/2) over n = 2, 4, 6, 8, 10")
ns = [2, 4, 6, 8, 10]
xs = [math.log(2 ** (n / 2)) for n in ns]
xbar = statistics.fmean(xs)
sxx = sum((x - xbar) ** 2 for x in xs)
w = [(x - xbar) / sxx for x in xs]
alpha = sum(wi * math.log(means[n][0]) for wi, n in zip(w, ns))
for samples in (5, 10, 20):
    se = math.sqrt(sum(wi ** 2 * (means[n][1] / means[n][0]) ** 2 / samples for wi, n in zip(w, ns)))
    print(f"  alpha from part-B means = {alpha:.3f}; predicted s.e. of the fitted alpha with {samples} samples/n = {se:.4f}")
