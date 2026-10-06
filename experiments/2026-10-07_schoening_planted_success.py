"""Experiment: on planted 3-CNF formulas with a UNIQUE satisfying assignment, how does the per-try success
probability of Schöning's walk (pairs/3sat-brute-force-vs-schoening, one try = random start + 3n flips,
first falsified clause, random literal) compare with the lower bound p(n) used to set the restart budget?

Instances: hidden a*; m = 5n clauses drawn uniformly among the 3-clauses (3 distinct variables) that a*
satisfies; kept only if a* is the unique solution (checked by enumerating all 2^n assignments). Five
instances per n, 4000 tries each (seeded), n = 6..16. Reports the empirical success fraction p_hat with
its binomial standard error, p(n), and the ratio. The theory (Schöning 1999; the bound in schoening.py)
requires p_hat >= p(n) up to sampling error for every satisfiable formula.

Also fits log(mean p_hat) against n to estimate the empirical base b in p_hat ~ b^n, to see how far
planted unique-solution instances are from the (3/4)^n worst-case order.

Run from the repository root:  python experiments/2026-10-07_schoening_planted_success.py

Outcome (2026-10-07, deterministic seeds; about 11 s): mean p_hat = 0.4915, 0.2885, 0.2451, 0.1338, 0.0905, 0.0720
for n = 6, 8, ..., 16 (standard errors 0.0018-0.0035), against p(n) = 0.0706, 0.0332, 0.0163, 0.0082, 0.0042, 0.0022.
The smallest per-instance ratio p_hat / p(n) was 5.92, 5.66, 13.16, 13.87, 15.02, 14.40, so the bound held on all 30
instances. Empirical base about 0.822 per variable (least squares) against 0.708 for p(n) over the same n range
(p(n) includes the 1/sqrt(n) factor). Planted unique-solution formulas are therefore much easier than the worst case,
and timing on them would not test the (4/3)^n bound.
"""
import importlib.util
import math
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("sch", ROOT / "pairs" / "3sat-brute-force-vs-schoening" / "implementations" / "schoening.py")
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)


def planted_unique(n, rng, m_factor=5):
    while True:
        star = [None] + [rng.random() < 0.5 for _ in range(n)]
        clauses = []
        while len(clauses) < round(m_factor * n):
            vs = rng.sample(range(1, n + 1), 3)
            cl = tuple(v if rng.random() < 0.5 else -v for v in vs)
            if any(star[abs(l)] == (l > 0) for l in cl):
                clauses.append(cl)
        sols = 0
        for mask in range(1 << n):
            if all(any(((mask >> (abs(l) - 1)) & 1) == (l > 0) for l in cl) for cl in clauses):
                sols += 1
                if sols > 1:
                    break
        if sols == 1:
            return clauses


def one_try(n, clauses, rnd):
    value = [False] + [rnd.random() < 0.5 for _ in range(n)]
    for step in range(3 * n + 1):
        falsified = None
        for clause in clauses:
            for lit in clause:
                if value[abs(lit)] == (lit > 0):
                    break
            else:
                falsified = clause
                break
        if falsified is None:
            return True
        if step < 3 * n:
            v = abs(rnd.choice(falsified))
            value[v] = not value[v]
    return False


TRIES = 4000
ns, means = [], []
for n in range(6, 17, 2):
    rng = random.Random(f"planted-unique|{n}")
    rnd = random.Random(f"walk|{n}")
    p_low = S.success_lower_bound(n)
    hats = []
    for inst in range(5):
        clauses = planted_unique(n, rng)
        wins = sum(one_try(n, clauses, rnd) for _ in range(TRIES))
        hats.append(wins / TRIES)
    mean = sum(hats) / len(hats)
    se = math.sqrt(max(mean * (1 - mean), 1e-12) / (TRIES * len(hats)))
    ns.append(n)
    means.append(mean)
    print(f"n={n}: p_hat per instance {[round(h, 4) for h in hats]}, mean {mean:.4f} +- {se:.4f}; "
          f"p(n) = {p_low:.5f}; min p_hat / p(n) = {min(hats) / p_low:.2f}", flush=True)

xs = ns
ys = [math.log(m) for m in means]
mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
print(f"empirical base b (p_hat ~ b^n, least squares over n = {ns[0]}..{ns[-1]}): {math.exp(slope):.4f}; "
      f"for comparison 3/4 = 0.75 and the bound's own fit gives "
      f"{math.exp(sum((x - mx) * (math.log(S.success_lower_bound(x)) - sum(math.log(S.success_lower_bound(z)) for z in xs) / len(xs)) for x in xs) / sum((x - mx) ** 2 for x in xs)):.4f}")
