"""Follow-up (2026-10-07) to experiments/2026-10-07_deutsch_jozsa_checks.py, check 4 at n = 8.

That run gave z = -2.37 (mean 2.9617 +- 0.0097 over 20000 random balanced functions vs the exact
1 + N/(N/2+1) = 2.9845). With 11 z-scores in that script, one |z| >= 2.37 has probability about 18% by
chance alone, so it is not evidence of a bug by itself. This replication was declared BEFORE running it:
a fresh seed and 200000 instances at n = 8. If the deviation is real, |z| should grow to about 7.5; if it
was chance, |z| should be of order 1. The original result is kept and reported either way.

Run from the repository root:  PYTHONIOENCODING=utf-8 python experiments/2026-10-07_deutsch_jozsa_followup_n8.py
Outcome: recorded in research/2026-10-07_quantum_entries.md (section "Deutsch-Jozsa").
"""
import importlib.util
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "dj_classical", ROOT / "pairs" / "deutsch-jozsa-classical-vs-quantum" / "implementations" / "classical.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

n, N, samples = 8, 256, 200000
rng = random.Random("dj-followup-n8")
qs = []
for _ in range(samples):
    values = [0] * (N // 2) + [1] * (N // 2)
    rng.shuffle(values)
    qs.append(mod.dj_classical((n, tuple(values)))[1])
mean, se = statistics.fmean(qs), statistics.stdev(qs) / math.sqrt(samples)
exact = 1 + N / (N / 2 + 1)
print(f"n={n}: mean {mean:.4f} +- {se:.4f} ({samples} instances), exact {exact:.4f}, z = {(mean - exact) / se:+.2f}")
