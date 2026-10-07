"""Measurement: how much of its worst-case bound the Hungarian implementation uses on uniformly random matrices.

pairs/assignment-brute-vs-hungarian/PROOFS.md (Lemma H0) proves that the implementation makes at most n(n + 1)/2
search iterations and at most n(n + 1)(2n + 1)/6 reduced-cost evaluations on every n x n input. This script counts
both on uniformly random matrices with entries in [0, 99] (the harness's first instance kind), n = 30, 50, 75, 100,
150, 200, three seeded matrices per n, and prints them as fractions of those bounds. The counts come from the
UNCHANGED implementation, through matrix rows that count every entry read (the search reads one entry per
reduced-cost evaluation, and the final sum reads n more) and an outer tuple that records every row read (one per
iteration, plus n in the final sum). The output is deterministic.

The fractions are measured data about random matrices, not a theorem. Each line starts with [DATA]; the bound check
lines start with [PASS] or [FAIL]. Exit code 0 iff no [FAIL].

Usage (repository root):  python experiments/2026-10-07_assignment_random_matrix_counts.py
"""
import importlib.util
import random
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
E = REPO / "pairs" / "assignment-brute-vs-hungarian"


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


HUNG = _load(E / "implementations" / "hungarian.py", "exp_asg_hung").assignment_hungarian


class Row(tuple):
    reads = 0

    def __getitem__(self, j):
        Row.reads += 1
        return tuple.__getitem__(self, j)


class Rows(tuple):
    reads = 0

    def __getitem__(self, i):
        Rows.reads += 1
        return tuple.__getitem__(self, i)


def main():
    failures = 0
    for n in (30, 50, 75, 100, 150, 200):
        it_bound = n * (n + 1) // 2
        ev_bound = n * (n + 1) * (2 * n + 1) // 6
        fr_it, fr_ev = [], []
        for t in range(3):
            rng = random.Random(f"assignment-random-counts|{n}|{t}")
            C = Rows(Row(rng.randint(0, 99) for _ in range(n)) for _ in range(n))
            Row.reads = Rows.reads = 0
            HUNG(C)
            iterations = Rows.reads - n
            evaluations = Row.reads - n
            ok = iterations <= it_bound and evaluations <= ev_bound
            failures += not ok
            print(f"[{'PASS' if ok else 'FAIL'}] n={n} seed={t}: iterations {iterations} <= {it_bound}, "
                  f"reduced-cost evaluations {evaluations} <= {ev_bound}")
            fr_it.append(iterations / it_bound)
            fr_ev.append(evaluations / ev_bound)
        print(f"[DATA] n={n}: iterations / bound {min(fr_it):.3f}..{max(fr_it):.3f}; "
              f"evaluations / bound {min(fr_ev):.3f}..{max(fr_ev):.3f}")
    print(f"summary: {failures} failures")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
