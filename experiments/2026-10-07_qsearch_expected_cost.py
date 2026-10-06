"""Experiment (2026-10-07): high-precision check of lib/qsearch.py against its exact expected costs.

Motivation: in experiments/2026-10-07_collision_expected_queries.py (run 2) the BHT variant built on the
BBHT exponential search showed z = +0.99, +1.71, +0.81, +0.76 at n = 3, 6, 9, 12 (all positive; combined
about +2.1). Is lib.qsearch.expected_cost_exponential (or the simulated search) slightly off, or is this chance?
This script isolates the search: a fixed set of t marked elements among N = 2^n, the phase oracle
Oracle.apply_phase_where (2 queries per Grover iteration) and one classical query per measured candidate,
exactly as in the BHT and Durr-Hoyer implementations. For each (n, t) it compares the mean number of queries
over many runs with the exact expectation, for both search_known_count and exponential_search, and reports
z-scores. It also prints the success probability per attempt of the known-count search against
sin^2((2m+1) theta) via the mean number of attempts.

Deterministic (fixed seeds). Run from the repository root (about 1-2 minutes):
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_qsearch_expected_cost.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Reusable machinery").
"""
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib import qsearch  # noqa: E402
from lib.qsim import Oracle  # noqa: E402


def run(kind, n, marked, rng):
    o = Oracle(tuple(range(1 << n)))
    phase = lambda st: o.apply_phase_where(st, lambda x, fx: x in marked)  # noqa: E731
    check = lambda x: (o(x), x in marked)[1]  # noqa: E731
    if kind == "known":
        x, attempts = qsearch.search_known_count(n, phase, check, len(marked), rng)
    else:
        x, _, interrupted = qsearch.exponential_search(n, phase, check, rng)
        attempts = None
        assert not interrupted
    assert x in marked
    return o.queries, attempts


zs = {"known": [], "exponential": []}
for n, ts, runs in ((4, (1, 2, 3, 4, 8), 20000), (6, (1, 2, 4, 5, 16), 20000), (8, (1, 3, 6, 40), 8000)):
    N = 1 << n
    for t in ts:
        for kind in ("known", "exponential"):
            rng = random.Random(f"qsearch|{kind}|{n}|{t}")
            marked = set(rng.sample(range(N), t))
            out = [run(kind, n, marked, rng) for _ in range(runs)]
            q = [a for a, _ in out]
            mean, se = statistics.fmean(q), statistics.stdev(q) / math.sqrt(runs)
            exact = (qsearch.expected_cost_known(N, t, 2, 1) if kind == "known"
                     else qsearch.expected_cost_exponential(N, t, 2, 1))
            if se == 0:  # e.g. t = N/4 with known t: one iteration succeeds with certainty (BBHT section 3.1)
                print(f"  n={n} t={t:3d} {kind:11s}: every one of {runs} runs used exactly {q[0]} queries; exact {exact:.6f}")
                continue
            z = (mean - exact) / se
            zs[kind].append(z)
            extra = ""
            if kind == "known":
                m = qsearch.known_count_iterations(N, t)
                p = qsearch.success_probability(N, t, m)
                extra = f"; m = {m}, 1/mean(attempts) = {1 / statistics.fmean(a for _, a in out):.4f} vs p = {p:.4f}"
            print(f"  n={n} t={t:3d} {kind:11s}: mean {mean:8.4f} +- {se:6.4f} ({runs} runs), exact {exact:8.4f}, z = {z:+.2f}{extra}")

for kind, z in zs.items():
    print(f"{kind}: {len(z)} z-scores, mean {statistics.fmean(z):+.3f}, combined (sum/sqrt(k)) {sum(z) / math.sqrt(len(z)):+.2f}, "
          f"max |z| {max(abs(v) for v in z):.2f}")
