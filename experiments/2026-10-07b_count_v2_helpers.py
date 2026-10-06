"""Shared helpers for the 2026-10-07b count-based V2 experiments (not an experiment itself).

counts(entry_id, alg_name, ns, samples) reproduces exactly what tools/validate.py does for a
measure="reported" V2 claim: the same per-(entry, n, sample) seeds, harness.generate_scaling, the same
re-seeding of the global random module, the UNCHANGED implementation, then harness.reported_cost(output);
values are averaged over samples. fit(...) uses the validator's own eval_cost and fit_slope, so the alpha
values printed by the experiments are the ones the validator computes for the same n_values.

Loaded by the experiment scripts with importlib (the file name starts with a digit). Deterministic.
"""
from __future__ import annotations

import importlib.util
import json
import math
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

_spec = importlib.util.spec_from_file_location("cpairs_validate", REPO / "tools" / "validate.py")
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)


def entry_and_harness(entry_id: str):
    entry_dir = REPO / "pairs" / entry_id
    entry = json.loads((entry_dir / "entry.json").read_text(encoding="utf-8"))
    harness = V.load_module(V.resolve_in_repo(entry_dir, entry["test_harness"]["module"]))
    return entry_dir, entry, harness


def algorithm(entry: dict, name: str) -> dict:
    for a in entry["algorithms"]:
        if a["name"] == name:
            return a
    raise KeyError(name)


def counts(entry_id: str, alg_name: str, ns, samples: int = 1, per_sample: bool = False):
    """Exact reported counts as the validator would measure them (mean over samples, or all samples)."""
    entry_dir, entry, harness = entry_and_harness(entry_id)
    alg = algorithm(entry, alg_name)
    fn = V.load_callable(entry_dir, alg["implementation"])
    out = []
    for n in ns:
        vals = []
        for k in range(samples):
            rng = random.Random(f"{entry['id']}|v2|{n}" + (f"|{k}" if k else ""))
            inst = harness.generate_scaling(n, rng)
            random.seed(f"{entry['id']}|v2|{n}|{k}|{alg['name']}")
            vals.append(harness.reported_cost(fn(inst)))
        out.append(vals if per_sample else sum(vals) / len(vals))
    return out


def alpha(ns, values, cost: str) -> float:
    xs = [math.log(V.eval_cost(cost, n)) for n in ns]
    ys = [math.log(v) for v in values]
    if max(xs) - min(xs) < 1e-12:
        return math.inf
    return V.fit_slope(xs, ys)


def diag(ns, values, cost: str):
    """(alpha vs cost*log n, alpha vs cost/log n), as in the validator's diagnostic."""
    xs = [math.log(V.eval_cost(cost, n)) for n in ns]
    ys = [math.log(v) for v in values]
    lx = [math.log(math.log(n)) for n in ns]
    up = [x + l for x, l in zip(xs, lx)]
    down = [x - l for x, l in zip(xs, lx)]
    return V.fit_slope(up, ys), V.fit_slope(down, ys)


def local_slopes(ns, values, cost: str):
    xs = [math.log(V.eval_cost(cost, n)) for n in ns]
    ys = [math.log(v) for v in values]
    return [(ys[i + 1] - ys[i]) / (xs[i + 1] - xs[i]) for i in range(len(ns) - 1)]


def report(label: str, ns, values, cost: str, rivals, tol: float):
    a = alpha(ns, values, cost)
    up, down = diag(ns, values, cost)
    print(f"  {label}: n={list(ns)}")
    print(f"    counts={[int(v) if float(v).is_integer() else round(v, 2) for v in values]}")
    print(f"    alpha vs {cost} = {a:.4f}  (|alpha-1| = {abs(a - 1):.4f}, tol {tol}) -> {'ok' if abs(a - 1) <= tol else 'FAIL'}")
    for r in rivals:
        ra = alpha(ns, values, r)
        print(f"    rival {r}: alpha = {ra:.4f} -> {'rejected' if abs(ra - 1) > tol else 'NOT rejected'}")
    print(f"    diagnostic: vs cost*log n = {up:.4f}, vs cost/log n = {down:.4f} -> "
          f"{'resolved' if abs(up - 1) > tol and abs(down - 1) > tol else 'NOT resolved'}")
    ls = local_slopes(ns, values, cost)
    print(f"    local slopes vs {cost}: {[round(s, 4) for s in ls]}")
    return a
