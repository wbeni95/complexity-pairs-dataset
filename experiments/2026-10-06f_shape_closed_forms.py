#!/usr/bin/env python3
"""Closed forms behind two characteristic polynomials found by the shape diagnostic (round 2026-10-06f).

The diagnostic found (x + 1)(x - 1)^2 for the KMP count and (x + 1)(x - 1)^3 for the naive matcher's count on
consecutive n (string-matching-naive-vs-kmp, worst-case harness with m = n // 2). The factor x + 1 is a parity term.
This script computes the counts with the entry's own harness and implementations (V2 seeding scheme) and checks:

  KMP:    a(n) = 4n - 6 for even n >= 6 and 4n - 7 for odd n >= 7 (RL-057 quoted 4n - 6 from even-n V2 grids);
          it prints the irregular small values n = 1..5;
  naive:  a(n) = (n - m + 1) * m with m = n // 2 for n >= 2 (the harness docstring's formula).

Deterministic, < 1 s.  Usage:  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06f_shape_closed_forms.py
"""
from __future__ import annotations

import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
import validate as V  # noqa: E402


def counts(prefix: str, ns):
    d = REPO / "pairs" / "string-matching-naive-vs-kmp"
    entry = V.load_entry(d)
    harness = V.load_module(V.resolve_in_repo(d, entry["test_harness"]["module"]))
    alg = next(a for a in V.implemented(entry) if a["name"].startswith(prefix))
    fn = V.load_callable(d, alg["implementation"])
    out = {}
    for n in ns:
        inst = harness.generate_scaling(n, random.Random(f"{entry['id']}|v2|{n}"))
        random.seed(f"{entry['id']}|v2|{n}|0|{alg['name']}")
        out[n] = harness.reported_cost(fn(inst))
    return out


def main() -> int:
    kmp = counts("Knuth-Morris-Pratt", range(1, 61))
    small = {n: kmp[n] for n in range(1, 6)}
    ok = all(kmp[n] == 4 * n - 6 - (n % 2) for n in range(6, 61))
    print(f"KMP n = 1..5: {small}; formula 4n-6 (even) / 4n-7 (odd) at those n: "
          f"{ {n: 4 * n - 6 - (n % 2) for n in range(1, 6)} }")
    print(f"KMP a(n) = 4n - 6 (even n), 4n - 7 (odd n) for all n = 6..60: {ok}")
    naive = counts("naive", range(2, 61))
    ok2 = all(naive[n] == (n - n // 2 + 1) * (n // 2) for n in range(2, 61))
    print(f"naive a(n) = (n - m + 1) m, m = n // 2, for all n = 2..60: {ok2}")
    return 0 if ok and ok2 else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
