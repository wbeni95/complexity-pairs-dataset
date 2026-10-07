"""Timing probe for pairs/3sat-brute-force-vs-schoening on the unsatisfiable family of generate_scaling
(random 3-CNF, m = 5n, plus the 8 clauses on (x1, x2, x3), shuffled).

Part 1 (deterministic): brute force's mean number of clause checks per assignment on the V2-seeded
instances, to see whether its cost is 2^n * Theta(m) or 2^n * Theta(1) on this family.
Part 2 (deterministic): Schöning's total number of clause checks on the same instances (instrumented copy,
seeded like the validator), divided by T(n) (3n + 1), i.e. the mean scan length per step.
Part 3 (timing, console): validator-style fits against several cost expressions.

Run from the repository root:  python experiments/2026-10-07_3sat_timing_probe.py

Outcome (2026-10-07). Parts 1-2 (deterministic): brute force makes 6.81, 8.12, 6.56, 8.23, 7.20, 7.87 clause checks
per assignment for n = 4..14 (step 2), 0.24 m at n = 4 and 0.10 m at n = 14 (measured on this range only; no
asymptotic claim). Schöning (T = 88, 196, 416, 848, 1682 tries for n = 4..12) scans 8.1 to 17.3 clauses per step
(0.20 m to 0.30 m; measured).
Part 3 (console): brute force alpha = 1.016 vs 2^n and 0.899 vs 2^n n (n = 8..16). Schöning (n = 4..12):
alpha = 0.960 vs (4/3)^n n^2.5, 1.225 vs (4/3)^n n^1.5, 2.082 vs (4/3)^n alone, and 0.865 vs 2^n.
Conclusion: over the timeable range the polynomial factors dominate and the fit cannot separate Schöning's claimed
bound from brute force's 2^n, so no V2 claim (the entry stays at V1).
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("probe_helpers", ROOT / "experiments" / "2026-10-07_probe_helpers.py")
ph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ph)

E = "3sat-brute-force-vs-schoening"
H = ph.harness_of(E)
S = ph.validate.load_module(ROOT / "pairs" / E / "implementations" / "schoening.py")


def brute_checks(formula):
    n, clauses = formula
    checks = 0
    for mask in range(1 << n):
        for clause in clauses:
            checks += 1
            for lit in clause:
                if ((mask >> (abs(lit) - 1)) & 1) == (lit > 0):
                    break
            else:
                break
        else:
            return True, checks
    return False, checks


def schoening_checks(formula, seed):
    random.seed(seed)
    n, clauses = formula
    checks = 0
    T = S.tries_needed(n)
    for _ in range(T):
        value = [False] + [random.random() < 0.5 for _ in range(n)]
        for step in range(3 * n + 1):
            falsified = None
            for clause in clauses:
                checks += 1
                for lit in clause:
                    if value[abs(lit)] == (lit > 0):
                        break
                else:
                    falsified = clause
                    break
            if falsified is None:
                return True, checks, T
            if step < 3 * n:
                v = abs(random.choice(falsified))
                value[v] = not value[v]
    return False, checks, T


print("Part 1 and 2: clause checks on the V2-seeded unsatisfiable instances")
for n in range(4, 15, 2):
    f = H.generate_scaling(n, random.Random(f"{E}|v2|{n}"))
    m = len(f[1])
    sat_b, cb = brute_checks(f)
    line = f"  n={n}, m={m}: brute force {cb} checks = {cb / 2 ** n:.2f} per assignment ({cb / 2 ** n / m:.3f} m)"
    if n <= 12:
        sat_s, cs, T = schoening_checks(f, f"probe|{n}")
        assert not sat_b and not sat_s
        line += f"; Schöning T={T}, {cs} checks = {cs / (T * (3 * n + 1)):.2f} per step ({cs / (T * (3 * n + 1)) / m:.3f} m)"
    print(line, flush=True)

print("Part 3: timing")
ns = [8, 9, 10, 11, 12, 13, 14, 15, 16]
for cost in ("2**n", "2**n * n"):
    ph.probe(E, "implementations/brute_force.py:sat_brute_force", "generate_scaling", cost, ns, label=f"brute force vs {cost}")
ns = [4, 5, 6, 7, 8, 9, 10, 11, 12]
for cost in ("(4/3)**n * n**2.5", "(4/3)**n * n**1.5", "(4/3)**n", "2**n"):
    ph.probe(E, "implementations/schoening.py:sat_schoening", "generate_scaling", cost, ns, label=f"Schöning vs {cost}")
