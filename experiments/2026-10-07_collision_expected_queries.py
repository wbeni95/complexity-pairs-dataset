"""Experiment (2026-10-07, collision entry): do the simulated collision algorithms use the number of queries
that theory predicts EXACTLY, not just Theta(sqrt N) / Theta(N^(1/3))? And what fitted slope should V2 see?

Exact expectations on uniformly random 2-to-1 functions (harness.generate), N = 2^n:
  classical birthday:  E = sum_{q>=0} P(Q > q),  P(Q > q) = prod_{i=1}^{q-1} (N - 2i)/(N - i)
  BHT, known t:        E = k + P_nc(k) * (2m + 1) / sin^2((2m+1) theta),  sin^2 theta = k/N,  m = floor(pi/(4 theta))
  BHT, exponential:    E = k + P_nc(k) * expected_cost_exponential(N, k, q_iter=2, q_check=1)
where k = round(N^(1/3)) and P_nc(k) = prod_{i=1}^{k-1} (N - 2i)/(N - i) is the probability that the k
classically queried points contain no collision (then exactly t = k points are marked). Each Grover iteration
costs 2 queries (compute + uncompute), each measured candidate 1 query.

Part A compares empirical means (many random instances, fixed seeds) with these values: z = (mean - E)/s.e.
Part B computes, for the V2 configurations in entry.json, the slope alpha that the EXACT expectations give
(the value the validator's fit should approach) and the standard error of the fitted alpha implied by the
per-n spread and the chosen number of samples (delta method: Var(alpha) = sum_i w_i^2 (sd_i/(mean_i sqrt S))^2,
w_i = (x_i - xbar)/Sxx). This is the justification of the `samples` values.

Part A2 is a replication declared after the first run (see history): classical n = 8 with fresh seeds and
40000 instances. Part C needs no simulation: it evaluates the exact expectations up to n = 30 to show where
E(n) / N^(1/3) settles, because the V2 range (n <= 15) is pre-asymptotic for the exponential-search variant.

History (all runs kept in the report):
  Run 1 (first implementation of bht.py, which stopped querying K at the first collision found inside K):
    bht_known z = +0.57, -1.97, -2.73, -1.61, -1.56 for n = 3, 6, 9, 12, 15, all but one negative.
    Cause: the formula assumes all k points of K are queried (BHT's steps 1-3), the code exited early, so the
    simulated counts were systematically LOWER than the formula. bht.py was changed to query all of K first
    (BHT's order); the formula was not changed. Same run, classical n = 8: z = +3.19 with an unchanged
    implementation (17 z-scores in the run, so P(max |z| >= 3.19) is about 2.4% by chance), hence Part A2.
  Run 2 (this script as it stands): see the report.

Deterministic. Run from the repository root (about 4 minutes):
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_collision_expected_queries.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Collision problem").
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

ENTRY = ROOT / "pairs" / "collision-problem-classical-vs-quantum"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


harness = load("harness.py", "col_harness")
classical = load("implementations/classical.py", "col_classical").collision_classical
bht_mod = load("implementations/bht.py", "col_bht")


def p_no_collision(N, q):
    """P(no collision among q distinct points) for a uniformly random 2-to-1 function."""
    p = 1.0
    for i in range(1, q):
        p *= (N - 2 * i) / (N - i)
    return p


def exact_classical(N):
    """E[Q] = sum_{q>=0} P(Q > q); P(Q > 0) = P(Q > 1) = 1 and P(Q > q+1) = P(Q > q) (N - 2q)/(N - q)."""
    total, p, q = 1.0, 1.0, 1  # the 1.0 is P(Q > 0)
    while p > 0:
        total += p  # P(Q > q)
        p *= (N - 2 * q) / (N - q)
        q += 1
    return total


def exact_bht(N, k, kind):
    tail = (qsearch.expected_cost_known(N, k, 2, 1) if kind == "known"
            else qsearch.expected_cost_exponential(N, k, 2, 1))
    return k + p_no_collision(N, k) * tail


ALGS = {
    "classical": (classical, lambda n: exact_classical(1 << n)),
    "bht_known": (bht_mod.collision_bht, lambda n: exact_bht(1 << n, bht_mod.subset_size(n), "known")),
    "bht_exponential": (bht_mod.collision_bht_exponential,
                        lambda n: exact_bht(1 << n, bht_mod.subset_size(n), "exponential")),
}


def run(name, n, samples, seed):
    fn, _ = ALGS[name]
    counts = []
    for k in range(samples):
        inst = harness.generate(n, random.Random(f"{seed}|inst|{n}|{k}"))
        random.seed(f"{seed}|alg|{name}|{n}|{k}")
        out = fn(inst)
        assert harness.check(inst, out), (name, n, k)
        counts.append(out[1])
    return counts


print("Part A: empirical mean vs exact expectation")
plan = {
    "classical": [(4, 4000), (6, 4000), (8, 4000), (10, 4000), (12, 2000), (14, 1000), (16, 500)],
    "bht_known": [(3, 4000), (6, 4000), (9, 4000), (12, 2000), (15, 300)],
    "bht_exponential": [(3, 4000), (6, 4000), (9, 4000), (12, 2000), (15, 300)],
}
spread = {}
for name, cfg in plan.items():
    for n, samples in cfg:
        counts = run(name, n, samples, "A")
        mean = statistics.fmean(counts)
        sd = statistics.stdev(counts)
        se = sd / math.sqrt(samples)
        exact = ALGS[name][1](n)
        spread[(name, n)] = (mean, sd)
        print(f"  {name:16s} n={n:2d}: mean {mean:9.4f} +- {se:7.4f} ({samples} instances), exact {exact:9.4f}, "
              f"z = {(mean - exact) / se:+.2f}; sd/mean = {sd / mean:.3f}")

print("\nPart A2: replication of classical n = 8 with fresh seeds")
counts = run("classical", 8, 40000, "A2")
mean, se = statistics.fmean(counts), statistics.stdev(counts) / math.sqrt(len(counts))
print(f"  classical        n= 8: mean {mean:9.4f} +- {se:7.4f} (40000 instances), exact {exact_classical(256):9.4f}, "
      f"z = {(mean - exact_classical(256)) / se:+.2f}")

print("\nPart B: slope implied by the exact expectations, and predicted s.e. of the V2 fit")
V2 = {  # must match entry.json
    "classical": ("2**(n/2)", [4, 6, 8, 10, 12, 14, 16], 100),
    "bht_known": ("2**(n/3)", [3, 6, 9, 12, 15], 40),
    "bht_exponential": ("2**(n/3)", [3, 6, 9, 12, 15], 100),
}
for name, (cost, ns, samples) in V2.items():
    xs = [math.log(2 ** (n / 2) if cost == "2**(n/2)" else 2 ** (n / 3)) for n in ns]
    ex = [ALGS[name][1](n) for n in ns]
    xbar = statistics.fmean(xs)
    sxx = sum((x - xbar) ** 2 for x in xs)
    w = [(x - xbar) / sxx for x in xs]
    alpha = sum(wi * math.log(e) for wi, e in zip(w, ex))
    var = sum(wi ** 2 * (spread[(name, n)][1] / spread[(name, n)][0]) ** 2 / samples for wi, n in zip(w, ns))
    print(f"  {name:16s} cost {cost}: exact E(n) = {', '.join(f'{e:.2f}' for e in ex)}; "
          f"alpha(exact) = {alpha:.3f}; predicted s.e. of alpha with {samples} samples/n = {math.sqrt(var):.3f}")

print("\nPart C: exact E(n) / N^(1/3) for large n (no simulation)")
for n in range(3, 31, 3):
    N, k = 1 << n, bht_mod.subset_size(n)
    ek, ee = exact_bht(N, k, "known"), exact_bht(N, k, "exponential")
    print(f"  n={n:2d}: k={k:5d}  known: E/N^(1/3) = {ek / 2 ** (n / 3):.4f}   exponential: E/N^(1/3) = {ee / 2 ** (n / 3):.4f}"
          f"   classical: E/sqrt(N) = {exact_classical(N) / 2 ** (n / 2):.4f}" if n <= 21 else
          f"  n={n:2d}: k={k:5d}  known: E/N^(1/3) = {ek / 2 ** (n / 3):.4f}   exponential: E/N^(1/3) = {ee / 2 ** (n / 3):.4f}")
for lo, hi in ((3, 15), (15, 30)):
    ns = list(range(lo, hi + 1, 3))
    for kind in ("known", "exponential"):
        xs = [math.log(2 ** (n / 3)) for n in ns]
        ys = [math.log(exact_bht(1 << n, bht_mod.subset_size(n), kind)) for n in ns]
        xbar, ybar = statistics.fmean(xs), statistics.fmean(ys)
        slope = sum((x - xbar) * (y - ybar) for x, y in zip(xs, ys)) / sum((x - xbar) ** 2 for x in xs)
        print(f"  exact slope against N^(1/3) over n = {lo}..{hi} (step 3), {kind}: {slope:.3f}")
