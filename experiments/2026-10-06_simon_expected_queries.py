"""Experiment (RESEARCH_LOG RL-015): does the simulated Simon algorithm use the number of queries that
theory predicts, not merely O(n)?

Each round yields a uniform y in the (n-1)-dimensional space {y : y.s = 0}. Collecting n - 1 linearly
independent y's takes E(n) = sum_{j=1}^{n-1} 1 / (1 - 2^(-j)) rounds (one query each) in expectation.
We compare the empirical mean over many random instances with E(n), reporting z = (mean - E) / s.e.

Run from the repository root:  python experiments/2026-10-06_simon_expected_queries.py
"""
import importlib.util
import math
import random
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # for lib.qsim


def load(rel, name):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


generate = load("pairs/simon-classical-vs-quantum/harness.py", "harness").generate
simon_quantum = load("pairs/simon-classical-vs-quantum/implementations/quantum.py", "quantum").simon_quantum


def expected_queries(n):
    return sum(1 / (1 - 2 ** -j) for j in range(1, n))


for n, samples in ((2, 4000), (3, 4000), (4, 4000), (6, 3000), (8, 1500)):
    random.seed(12345 + n)  # measurement outcomes inside the simulator
    counts = [simon_quantum(generate(n, random.Random(f"chk{n}|{k}")))[1] for k in range(samples)]
    mean = statistics.fmean(counts)
    se = statistics.stdev(counts) / math.sqrt(samples)
    e = expected_queries(n)
    print(f"n={n}: empirical mean {mean:.4f} +- {se:.4f} (1 s.e., {samples} instances); "
          f"exact E(n) = {e:.4f}; z = {(mean - e) / se:+.2f}")
