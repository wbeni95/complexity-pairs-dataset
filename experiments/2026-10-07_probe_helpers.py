"""Shared helper for the 2026-10-07 timing probes (not an experiment by itself).

probe(entry_id, impl_spec, generator_name, cost, ns) times one implementation of a pairs/ entry on the
chosen n values with the validator's own routine (tools/validate.py time_call: best of 3 samples, each
looped until it lasts >= 20 ms, garbage collector off) and fits the log-log slope alpha of time against
cost(n), exactly as `validate.py --scaling` does. Nothing in the entry is modified, so n ranges and cost
expressions can be explored before they are written into entry.json.

Instances are drawn from random.Random(f"{tag}|{n}"), so they are deterministic; the timings are not.

Load it from another experiment with importlib (the file name starts with a digit):
    spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
"""
import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT))
import validate  # noqa: E402

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def harness_of(entry_id):
    return validate.load_module(ROOT / "pairs" / entry_id / "harness.py")


def probe(entry_id, impl_spec, generator_name, cost, ns, tag="probe", label=None):
    entry_dir = ROOT / "pairs" / entry_id
    harness = harness_of(entry_id)
    fn = validate.load_callable(entry_dir, impl_spec)
    gen = getattr(harness, generator_name)
    times = []
    for n in ns:
        inst = gen(n, random.Random(f"{tag}|{n}"))
        random.seed(f"{tag}|{n}|impl")
        times.append(validate.time_call(fn, inst))
    xs = [math.log(validate.eval_cost(cost, n)) for n in ns]
    alpha = validate.fit_slope(xs, [math.log(t) for t in times])
    detail = ", ".join(f"n={n}: {t * 1e3:.3g}ms" for n, t in zip(ns, times))
    print(f"  {label or impl_spec} [{generator_name}] vs {cost}: alpha={alpha:.3f}  {detail}", flush=True)
    return alpha, times


def local_slopes(ns, times, cost):
    """Per-step slopes between consecutive n values (shows curvature that a single fit hides)."""
    out = []
    for (n0, t0), (n1, t1) in zip(zip(ns, times), zip(ns[1:], times[1:])):
        c0, c1 = validate.eval_cost(cost, n0), validate.eval_cost(cost, n1)
        out.append(math.log(t1 / t0) / math.log(c1 / c0))
    return out
