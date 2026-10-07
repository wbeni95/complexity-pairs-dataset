"""Probe for pairs/chromatic-number-subset-dp-vs-inclusion-exclusion.

Part 1 (deterministic): for the V2 instances (generate_scaling = G(n, 0.8), seeded exactly as
tools/validate.py seeds them: random.Random(f"{entry_id}|v2|{n}")), print chi(G), hence the number of
inclusion-exclusion rounds, and count the subset DP's inner-loop iterations with an instrumented copy,
to confirm the exact count 3^n - 2^n.
Part 2 (timing, console): validator-style fits for the n ranges considered for entry.json, plus a fit of
the inclusion-exclusion timings against 2^n alone (to see whether the factor n is resolvable at all).

Run from the repository root:  python experiments/2026-10-07_chromatic_probe.py

Outcome (2026-10-07). Part 1 (deterministic): chi of the V2 instances for n = 6..18 is
4, 5, 4, 6, 6, 7, 7, 8, 8, 8, 8, 9, 10 (chi/n between 0.50 and 5/7 = 0.714); the DP's inner-iteration count equals
3^n - 2^n for every n = 6..12 (665 ... 527345). Part 2 (console): subset DP alpha = 0.963 vs 3^n over
n = 6..12 (local slopes 0.84, 0.90 at the two smallest steps, then 0.94..1.03), so entry.json uses 7..13;
inclusion-exclusion over n = 9..16: alpha = 0.954 vs n 2^n, 1.069 vs 2^n (both inside the tolerance:
the factor n is not resolvable), 0.674 vs 3^n (rejected). Local slopes vary (0.87..1.03) because chi, and
with it the number of rounds, grows in steps (chi = 8 for n = 13..16).
"""
import importlib.util
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "chromatic-number-subset-dp-vs-inclusion-exclusion"
H = ph.harness_of(E)
ie = ph.validate.load_callable(ROOT / "pairs" / E, "implementations/inclusion_exclusion.py:chromatic_inclusion_exclusion")


def dp_iterations(n):
    count = 0
    for S in range(1, 1 << n):
        T = S
        while T:
            count += 1
            T = (T - 1) & S
    return count


print("Part 1: chi of the V2 instances (G(n, 0.8)) and DP iteration counts")
for n in range(6, 19):
    g = H.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    chi = ie(g)
    line = f"  n={n}: edges={len(g[1])}, chi={chi} (rounds of inclusion-exclusion), chi/n={chi / n:.2f}"
    if n <= 12:
        it = dp_iterations(n)
        line += f"; DP inner iterations {it} = 3^n - 2^n: {it == 3 ** n - 2 ** n}"
    print(line, flush=True)

print("Part 2: timing")
ns = [6, 7, 8, 9, 10, 11, 12]
a, t = ph.probe(E, "implementations/subset_dp.py:chromatic_subset_dp", "generate_scaling", "3**n", ns, tag=f"{E}|v2")
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "3**n")])
ns = [9, 10, 11, 12, 13, 14, 15, 16]
a, t = ph.probe(E, "implementations/inclusion_exclusion.py:chromatic_inclusion_exclusion", "generate_scaling", "n * 2**n", ns, tag=f"{E}|v2")
print("  local slopes:", [round(x, 3) for x in ph.local_slopes(ns, t, "n * 2**n")])
ph.probe(E, "implementations/inclusion_exclusion.py:chromatic_inclusion_exclusion", "generate_scaling", "2**n", ns, tag=f"{E}|v2", label="inclusion-exclusion vs 2**n alone")
ph.probe(E, "implementations/inclusion_exclusion.py:chromatic_inclusion_exclusion", "generate_scaling", "3**n", ns, tag=f"{E}|v2", label="inclusion-exclusion vs 3**n (should fail)")
