"""Experiment (2026-10-07, Deutsch-Jozsa entry): four checks of pairs/deutsch-jozsa-classical-vs-quantum.

1. Worst case of the deterministic algorithm, by EXHAUSTION over all promise inputs for n = 1..4
   (2 constant + C(N, N/2) balanced functions): is the maximum number of queries exactly 2^(n-1) + 1, and
   is it attained exactly on the four functions produced by harness.generate_scaling (both constants and
   f(x) = c XOR top bit)? Also: is every answer correct?
2. Exactness of the simulated quantum algorithm, by exhaustion for n = 1..4 plus 300 random balanced
   functions for n = 5..10: the probability of measuring |0...0> must be 1 for constant f and 0 for balanced
   f. Reports the largest floating-point deviation.
3. One-sided error of the randomized classical algorithm, with k random queries instead of K = 20 so that
   errors are frequent enough to measure: the empirical error rate on random balanced functions is compared
   with the exact value 2^(1-k) (z-score). Constant functions must never be misclassified.
4. Expected queries of the deterministic algorithm on uniformly random BALANCED functions: exactly
   1 + N / (N/2 + 1) (the position of the first value different from f(0) in a random arrangement of the
   remaining N - 1 values, N/2 of which differ). Compared with the empirical mean (z-score).

Deterministic (fixed seeds). Run from the repository root:
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_deutsch_jozsa_checks.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Deutsch-Jozsa").
"""
import importlib.util
import itertools
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from lib.qsim import Oracle, State  # noqa: E402

ENTRY = ROOT / "pairs" / "deutsch-jozsa-classical-vs-quantum"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


harness = load("harness.py", "dj_harness")
dj_classical = load("implementations/classical.py", "dj_classical").dj_classical


def promise_inputs(n):
    N = 1 << n
    yield (0,) * N
    yield (1,) * N
    for ones in itertools.combinations(range(N), N // 2):
        s = set(ones)
        yield tuple(1 if x in s else 0 for x in range(N))


def p_zero(table, n):
    st = State(n)
    st.h_all()
    Oracle(table).apply_phase(st)
    st.h_all()
    return abs(st.amp[0]) ** 2


print("1. Deterministic worst case, exhaustive")
for n in range(1, 5):
    worst, argmax, count, wrong = 0, [], 0, 0
    for table in promise_inputs(n):
        count += 1
        answer, q = dj_classical((n, table))
        wrong += harness.check((n, table), (answer, q)) is not True
        if q > worst:
            worst, argmax = q, [table]
        elif q == worst:
            argmax.append(table)
    adversarial = {harness.generate_scaling(n, random.Random(s))[1] for s in range(200)}
    print(f"   n={n}: {count} promise inputs, {wrong} wrong answers; max queries {worst} "
          f"(2^(n-1)+1 = {2 ** (n - 1) + 1}); attained on {len(argmax)} inputs; "
          f"equal to the generate_scaling set: {set(argmax) == adversarial}")

print("2. Quantum exactness: P(outcome 0)")
dev_const = dev_bal = 0.0
for n in range(1, 5):
    for table in promise_inputs(n):
        p = p_zero(table, n)
        if len(set(table)) == 1:
            dev_const = max(dev_const, abs(1 - p))
        else:
            dev_bal = max(dev_bal, p)
rng = random.Random(5)
for n in range(5, 11):
    for _ in range(50):
        values = [0] * (1 << (n - 1)) + [1] * (1 << (n - 1))
        rng.shuffle(values)
        dev_bal = max(dev_bal, p_zero(tuple(values), n))
    for c in (0, 1):
        dev_const = max(dev_const, abs(1 - p_zero((c,) * (1 << n), n)))
print(f"   max |1 - P(0)| over constant functions: {dev_const:.3e}; max P(0) over balanced functions: {dev_bal:.3e}")

print("3. Randomized algorithm with k queries: error rate on random balanced functions vs 2^(1-k)")
for k in (1, 2, 3, 4, 6, 8):
    rng = random.Random(1000 + k)
    trials, errors, const_errors = 20000, 0, 0
    for i in range(trials):
        n = 6
        inst = harness.generate(n, rng)
        while len(set(inst[1])) == 1:
            inst = harness.generate(n, rng)
        o = Oracle(inst[1])
        answers = {o(rng.randrange(1 << n)) for _ in range(k)}
        errors += len(answers) == 1
        c = (rng.randrange(2),) * (1 << n)
        o = Oracle(c)
        const_errors += len({o(rng.randrange(1 << n)) for _ in range(k)}) > 1
    p = 2 ** (1 - k)
    se = math.sqrt(p * (1 - p) / trials) if 0 < p < 1 else 0
    z = (errors / trials - p) / se if se else float("nan")
    print(f"   k={k}: error rate {errors / trials:.5f} vs exact {p:.5f} ({trials} balanced instances), "
          f"z = {z:+.2f}; constant functions misclassified: {const_errors}")

print("4. Deterministic algorithm on random balanced functions: mean queries vs 1 + N/(N/2+1)")
for n in (2, 4, 6, 8, 10, 12):
    rng = random.Random(77 + n)
    N = 1 << n
    qs = []
    for _ in range(20000 if n <= 8 else 4000):
        values = [0] * (N // 2) + [1] * (N // 2)
        rng.shuffle(values)
        qs.append(dj_classical((n, tuple(values)))[1])
    mean, se = statistics.fmean(qs), statistics.stdev(qs) / math.sqrt(len(qs))
    exact = 1 + N / (N / 2 + 1)
    print(f"   n={n}: mean {mean:.4f} +- {se:.4f} ({len(qs)} instances), exact {exact:.4f}, z = {(mean - exact) / se:+.2f}; "
          f"worst case would be {N // 2 + 1}")
