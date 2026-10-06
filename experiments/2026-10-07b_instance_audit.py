#!/usr/bin/env python3
"""Which V2 timing instances does the validator actually use? (deviation analysis, 2026-10-07b)

The validator times ONE instance per n (samples = 1 for every timing fit), drawn from
random.Random(f"{entry_id}|v2|{n}") through harness.generate_scaling (or harness.generate if the harness has
no generate_scaling). Because the seed is fixed, every ledger run times the SAME instance at each n, so the
run-to-run spread of alpha (experiments/2026-10-07b_ledger_stability.py) measures timing noise only, never
instance-to-instance variation. This script regenerates those exact instances (no timing) to explain two
reproducible local-slope anomalies:

A. maximum-subarray (harness has no generate_scaling): harness.generate draws r = rng.random() first and makes
   an all-negative array if r < 0.1, an all-non-negative one if r < 0.2, otherwise mixed signs. For every V2 n of
   the three algorithms, report the instance type, plus how often Kadane's branch "ending_here < 0" fires
   and how often "best" is updated (both are counted by re-running Kadane's loop logic here, not timed).
B. chromatic-number inclusion-exclusion: the claimed cost is n * 2^n, while entry.json's time_complexity says
   (2 chi(G) + 2) 2^n arithmetic operations. For every V2 n, compute chi(G) of the exact timing instance with the
   harness's own oracle (harness._colourable, smallest k that succeeds), then fit the exact operation-count
   model (2 chi + 2) 2^n against n 2^n with the validator's fit_slope.
C. Which V2 entries draw their timing instances from harness.generate (no worst-case generator).

Deterministic; light (chromatic oracle on G(n, 0.8), n <= 18). No timing.

Result (2026-10-06 local time): A. Kadane's V2 instances: n = 100000 all-negative, n = 1000000 all-non-negative,
others mixed; brute force: n = 150 all-negative, n = 200 all-non-negative; running sums: n = 200
all-non-negative. B. chi(G) = 6, 7, 7, 8, 8, 8, 8, 9, 10 for n = 10..18 (chi/n 0.50-0.64); alpha of
(2 chi + 2) 2^n against n 2^n = 0.9638; plain 2^n against n 2^n = 0.9047. C. 10 V2 entries time instances from
harness.generate. See research/2026-10-07b_deviations.md sections 2 and 4.
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
sys.path.insert(0, str(REPO / "tools"))
from validate import fit_slope  # noqa: E402


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def entry(eid):
    return json.loads((REPO / "pairs" / eid / "entry.json").read_text(encoding="utf-8"))


def part_a():
    eid = "maximum-subarray"
    h = load(REPO / "pairs" / eid / "harness.py", "ms_h")
    e = entry(eid)
    print("A. maximum-subarray V2 instances (harness.generate; no generate_scaling)")
    for alg in e["algorithms"]:
        ns = alg["harness"]["scaling"]["n_values"]
        print(f"  {alg['name']}")
        for n in ns:
            rng = random.Random(f"{eid}|v2|{n}")
            r = random.Random(f"{eid}|v2|{n}").random()
            a = h.generate(n, rng)
            kind = "all-negative" if r < 0.1 else ("all-non-negative" if r < 0.2 else "mixed")
            resets = upd = 0
            best = eh = a[0]
            for x in a[1:]:
                if eh < 0:
                    eh = x
                    resets += 1
                else:
                    eh += x
                if eh > best:
                    best = eh
                    upd += 1
            print(f"    n={n:8d}  type={kind:17s}  resets/n={resets / n:.3f}  best-updates/n={upd / n:.4f}")


def part_b():
    eid = "chromatic-number-subset-dp-vs-inclusion-exclusion"
    h = load(REPO / "pairs" / eid / "harness.py", "ch_h")
    e = entry(eid)
    alg = [a for a in e["algorithms"] if "inclusion" in a["name"]][0]
    ns = alg["harness"]["scaling"]["n_values"]
    print("\nB. chromatic inclusion-exclusion: chi(G) of the exact V2 timing instances (G(n, 0.8))")
    chis = []
    for n in ns:
        g = h.generate_scaling(n, random.Random(f"{eid}|v2|{n}"))
        nn, edges = g
        k = 1
        while not h._colourable(nn, edges, k):
            k += 1
        chis.append(k)
        print(f"    n={n:3d}  edges={len(edges):4d}  chi={k:2d}  chi/n={k / n:.3f}")
    xs = [math.log(n * 2 ** n) for n in ns]
    ys = [math.log((2 * c + 2) * 2 ** n) for n, c in zip(ns, chis)]
    print(f"    alpha of the exact op-count model (2 chi + 2) 2^n against n 2^n: {fit_slope(xs, ys):.4f}")
    ys2 = [math.log(2 ** n) for n in ns]
    print(f"    alpha of plain 2^n against n 2^n (for scale): {fit_slope(xs, ys2):.4f}")


def part_c():
    print("\nC. V2 entries whose timing instances come from harness.generate (no generate_scaling)")
    for d in sorted((REPO / "pairs").iterdir()):
        ej = d / "entry.json"
        if not ej.is_file():
            continue
        e = json.loads(ej.read_text(encoding="utf-8"))
        if e["verification"]["level"] < "V2":
            continue
        timing = [a for a in e["algorithms"] if a.get("harness", {}).get("scaling", {}).get("measure", "time") == "time"
                  and a.get("harness", {}).get("scaling")]
        if not timing:
            continue
        src = (d / "harness.py").read_text(encoding="utf-8")
        if "def generate_scaling" not in src:
            print(f"    {e['id']}: {len(timing)} timing fit(s), instances from harness.generate")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    part_a()
    part_b()
    part_c()
