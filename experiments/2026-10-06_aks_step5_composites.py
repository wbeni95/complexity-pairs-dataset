"""Experiment (RESEARCH_LOG RL-003): does our AKS implementation really decide primality, including
composites that only step 5 (the polynomial congruence) can reject?

1. AKS, trial division and Miller-Rabin agree on every N in [0, 3000).
2. Semiprimes N = p q whose prime factors both exceed AKS's r get past steps 1-4 (no perfect power,
   no factor <= r, N > r), so only step 5 can reject them. Each must be reported composite.

Run from the repository root:  python experiments/2026-10-06_aks_step5_composites.py
"""
import importlib.util
import math
import random
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


aks = load("pairs/primality-trial-vs-aks/implementations/aks.py", "aks")
trial = load("pairs/primality-trial-vs-aks/implementations/trial_division.py", "trial")
mr = load("pairs/primality-miller-rabin-vs-aks/implementations/miller_rabin.py", "mr")

random.seed(20261006)  # Miller-Rabin's bases
disagree = [x for x in range(3000)
            if not (aks.is_prime_aks(x) == trial.is_prime_trial(x) == mr.is_prime_miller_rabin(x))]
print(f"part 1: N in [0, 3000): {len(disagree)} disagreements {disagree[:10]}")


def r_of(N):
    """The r chosen in AKS step 2 (smallest r coprime to N with ord_r(N) > log2(N)^2)."""
    max_k = math.floor(math.log2(N) ** 2)
    r = 2
    while not (math.gcd(r, N) == 1 and aks._order_exceeds(N, r, max_k)):
        r += 1
    return r


primes = [p for p in range(300, 1500) if all(p % d for d in range(2, math.isqrt(p) + 1))]
tested = []
for i, p in enumerate(primes):
    for q in primes[i:i + 3]:
        N = p * q
        r = r_of(N)
        if min(p, q) > r:
            t0 = time.perf_counter()
            verdict = aks.is_prime_aks(N)
            tested.append((N, p, q, r, verdict, time.perf_counter() - t0))
    if len(tested) >= 12:
        break
wrong = [t for t in tested if t[4] is not False]
print(f"part 2: {len(tested)} step-5-only composites tested, {len(wrong)} wrongly reported prime")
for N, p, q, r, verdict, dt in tested:
    print(f"   N = {N} = {p} * {q}, r = {r}: {'prime' if verdict else 'composite'} ({dt * 1e3:.1f} ms)")
