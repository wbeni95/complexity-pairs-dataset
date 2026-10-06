"""Follow-up (2026-10-07): is there a real bias in the classical birthday count at n = 8 (N = 256)?

History: experiments/2026-10-07_collision_expected_queries.py gave, for the classical algorithm at n = 8,
z = +3.19 (4000 instances, run 1; identical in run 2) and, in its pre-declared replication with fresh seeds,
z = +2.05 (40000 instances). The other six sizes gave |z| <= 2.12 with mixed signs. Three checks, declared
before running:
  1. E[Q] for N = 256 recomputed in exact rational arithmetic (fractions), against the float value 20.0726,
     and the exact distribution P(Q = q) for a chi-square test below.
  2. An independent sampler that bypasses the harness, the Oracle class and the implementation: a uniformly
     random perfect matching is irrelevant under a uniformly random query order, so it suffices to draw a
     random permutation of the pair labels (each label twice) and record the first repeat. 10^6 samples.
  3. The full pipeline (harness.generate + implementations/classical.py) with 200000 fresh instances.
If 2 and 3 agree with 1, the earlier deviations were chance; if 3 deviates and 2 does not, the pipeline is
suspect; if both deviate, the formula is suspect.

Deterministic (fixed seeds). Run from the repository root (about 1-2 minutes):
    PYTHONIOENCODING=utf-8 python experiments/2026-10-07_collision_classical_n8_followup.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Collision problem").
"""
import importlib.util
import math
import random
import statistics
import sys
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
ENTRY = ROOT / "pairs" / "collision-problem-classical-vs-quantum"


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ENTRY / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


N = 256
# 1. exact distribution: P(Q > q) = prod_{i=1}^{q-1} (N - 2i)/(N - i)
tail = [Fraction(1), Fraction(1)]
q = 1
while tail[-1] > 0:
    tail.append(tail[-1] * Fraction(N - 2 * q, N - q))
    q += 1
E = sum(tail)
pmf = {q: tail[q - 1] - tail[q] for q in range(1, len(tail))}
var = sum(Fraction(q * q) * p for q, p in pmf.items()) - E * E
print(f"1. exact E[Q] = {float(E):.6f} (rational with {len(str(E.denominator))}-digit denominator); "
      f"exact sd = {math.sqrt(var):.4f}; sum of pmf = {float(sum(pmf.values())):.12f}")


def chi_square(counts, total):
    """Chi-square of observed first-repeat times against the exact pmf, bins merged to expected >= 50."""
    bins, exp_acc, obs_acc, stat, dof = [], 0.0, 0, 0.0, -1
    for q in sorted(pmf):
        exp_acc += float(pmf[q]) * total
        obs_acc += counts.get(q, 0)
        if exp_acc >= 50:
            stat += (obs_acc - exp_acc) ** 2 / exp_acc
            dof += 1
            exp_acc, obs_acc = 0.0, 0
    if exp_acc > 0:
        stat += (obs_acc - exp_acc) ** 2 / exp_acc
        dof += 1
    return stat, dof


def report(label, qs):
    mean, se = statistics.fmean(qs), statistics.stdev(qs) / math.sqrt(len(qs))
    counts = {}
    for v in qs:
        counts[v] = counts.get(v, 0) + 1
    stat, dof = chi_square(counts, len(qs))
    print(f"{label}: mean {mean:.4f} +- {se:.4f} ({len(qs)} samples), z = {(mean - float(E)) / se:+.2f}; "
          f"chi-square {stat:.1f} on {dof} d.o.f. (expectation {dof}, s.d. {math.sqrt(2 * dof):.1f})")


# 2. independent sampler
rng = random.Random("collision-n8-independent")
labels = [i // 2 for i in range(N)]
qs = []
for _ in range(1_000_000):
    rng.shuffle(labels)
    seen = set()
    for idx, lab in enumerate(labels, 1):
        if lab in seen:
            qs.append(idx)
            break
        seen.add(lab)
report("2. independent sampler", qs)

# 3. full pipeline
harness = load("harness.py", "col_harness")
classical = load("implementations/classical.py", "col_classical").collision_classical
qs = []
for k in range(200_000):
    inst = harness.generate(8, random.Random(f"n8-followup|inst|{k}"))
    random.seed(f"n8-followup|alg|{k}")
    out = classical(inst)
    assert harness.check(inst, out)
    qs.append(out[1])
report("3. full pipeline", qs)
