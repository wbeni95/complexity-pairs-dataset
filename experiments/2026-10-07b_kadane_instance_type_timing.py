#!/usr/bin/env python3
"""Small re-measurement: does Kadane's per-element time depend on the instance type? (deviation analysis, 2026-10-07b)

Hypothesis (from experiments/2026-10-07b_instance_audit.py): the reproducible local-slope anomaly of the
maximum-subarray Kadane fit in every ledger run (local slopes 0.994 1.004 0.778 1.235 0.895 in 20261006T070542Z)
comes from harness.generate switching instance type between n values: n = 100000 is an all-negative array,
n = 1000000 an all-non-negative one, the rest mixed signs.

Method: for n = 100000, build one instance of each type exactly as harness.generate does (values in [-100, -1],
[0, 100], [-100, 100]; seeded Random), time pairs/maximum-subarray/implementations/kadane.py on each with the
validator's own time_call (best of 3 loops of >= 20 ms), interleaved over 3 rounds, and report ns per element.
Runtime about 1-2 s. Timing is noisy (another agent may be running CPU-heavy jobs), so only ratios between
types measured in the same round are interpreted, and only if they agree across rounds.

History (2026-10-06 local, ~10:05-10:10; console-level timing while another agent's CPU-heavy jobs ran,
4 flipwalk.exe processes visible in tasklist):
  run 1 (3 rounds, mean ratios): all-negative x0.774 / 0.734 / 0.763 of mixed, all-non-negative x0.869 / 0.891 /
        0.893 -- consistent across rounds.
  run 2 (3 rounds, added the slope prediction): rounds DISAGREED (all-negative 0.864 / 1.068 / 0.645,
        all-non-negative 0.859 / 1.227 / 1.312), so by the rule above it is not interpreted (CPU contention).
  run 3 (this version: 9 rounds, medians): all-negative median 0.694 (range 0.631-0.942), all-non-negative
        median 0.881 (range 0.754-0.955); predicted local slopes 0.697 / 1.332 / 0.894 against the ledger's
        0.778 / 1.235 / 0.895.
Verdict: the direction (both uniform-sign instance types are cheaper per element than mixed signs) holds in
runs 1 and 3: all 24 of their round-ratios (6 + 18) are below 1; the magnitude is noisy under contention.
Consistent with, not proof of, the instance-mix explanation. See research/2026-10-07b_deviations.md section 2.
"""
from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "tools"))
from validate import time_call  # noqa: E402

spec = importlib.util.spec_from_file_location("kad", REPO / "pairs" / "maximum-subarray" / "implementations" / "kadane.py")
kad = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kad)

N = 100_000
rng = random.Random("2026-10-07b|kadane")
inst = {
    "all-negative": [rng.randint(-100, -1) for _ in range(N)],
    "all-non-negative": [rng.randint(0, 100) for _ in range(N)],
    "mixed": [rng.randint(-100, 100) for _ in range(N)],
}
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import math  # noqa: E402

ratios = {"all-negative": [], "all-non-negative": []}
ROUNDS = 9
for rnd in range(ROUNDS):
    t = {k: time_call(kad.max_subarray_kadane, v) for k, v in inst.items()}
    base = t["mixed"]
    for k in ratios:
        ratios[k].append(t[k] / base)
    print(f"round {rnd}: " + "  ".join(f"{k}: {v / N * 1e9:6.2f} ns/elem (x{v / base:.3f} of mixed)" for k, v in t.items()))
# Predicted local slopes of the ledger's Kadane series if time = n * (per-element cost of the instance type):
# n = 30000 (mixed) -> 100000 (all-negative) -> 300000 (mixed) -> 1000000 (all-non-negative)
rn = sorted(ratios["all-negative"])[ROUNDS // 2]  # median
rp = sorted(ratios["all-non-negative"])[ROUNDS // 2]  # median
print(f"median ratios over {ROUNDS} rounds: all-negative {rn:.3f}, all-non-negative {rp:.3f}")
print("predicted local slopes 30000->100000, 100000->300000, 300000->1000000: "
      f"{1 + math.log(rn) / math.log(100000 / 30000):.3f} {1 - math.log(rn) / math.log(3):.3f} "
      f"{1 + math.log(rp) / math.log(1000000 / 300000):.3f}  (ledger 20261006T070542Z: 0.778 1.235 0.895)")
