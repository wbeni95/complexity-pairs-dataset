#!/usr/bin/env python3
"""(d) A tractability predictor: Schaefer's six classes via polymorphisms, checked against brute force.

Questions:
  1. For every Boolean relation of arity 1, 2 and 3 (4 + 16 + 256 relations), does the polymorphism test agree with
     the independent syntactic definition (Horn / dual-Horn / 2-CNF clause sets, GF(2) cosets)? How many relations
     fall into each class, and how many single-relation languages are NP-complete by Schaefer's theorem?
  2. For random languages drawn inside each tractable class, does the class's polynomial algorithm (trivial
     assignment, unit propagation, 2-SAT via SCC, GF(2) elimination) decide satisfiability exactly like brute force,
     and is every returned witness a solution? For affine languages, does 2^(n - rank) equal the brute-force count
     (the only tractable counting class, Creignou & Hermann 1996)?
  3. The predictor on named languages related to the dataset: 2-SAT, 3-SAT, Horn-SAT, XOR-SAT, 1-in-3-SAT,
     NAE-3-SAT, graph 2-colouring.

Seeds fixed (random.Random(20261006 + 1000 * class + i)); exact. Runtime a few seconds, one process, below-normal priority.

Usage (repository root):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06d_meth_csp_predictor.py
"""
from __future__ import annotations

import random
import sys
import time
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from methods import csp  # noqa: E402

try:
    from search.machine import set_below_normal_priority
    set_below_normal_priority()
except Exception:  # pragma: no cover
    pass


def rel(*tuples) -> frozenset:
    return frozenset(tuple(t) for t in tuples)


def clause(signs) -> frozenset:
    """The relation of a clause: all tuples except the single falsifying one (sign 1 = positive literal)."""
    k = len(signs)
    return frozenset(t for t in product((0, 1), repeat=k) if any(t[i] == signs[i] for i in range(k)))


def part1() -> dict:
    print("=== Part 1: polymorphism classes vs syntactic definitions, all relations of arity 1..3")
    by_class = {}
    for k in (1, 2, 3):
        rels = csp.all_relations(k)
        mism = 0
        counts = {c: 0 for c in csp.CLASSES}
        nonempty_np = 0
        for R in rels:
            p = csp.polymorphism_classes(R)
            s = csp.syntactic_classes(R, k)
            mism += p != s
            if R:
                for c in p:
                    counts[c] += 1
                    by_class.setdefault((k, c), []).append(R)
                nonempty_np += not p
        print(f"  arity {k}: {len(rels)} relations; polymorphic == syntactic for all: {mism == 0} ({mism} mismatches)")
        print(f"    nonempty relations per class: " + ", ".join(f"{c} {counts[c]}" for c in csp.CLASSES))
        print(f"    nonempty relations in NO class (CSP of that single relation is NP-complete): {nonempty_np}")
    return by_class


def part2(by_class: dict) -> None:
    print("\n=== Part 2: predicted polynomial algorithm vs brute force on random instances")
    t0 = time.perf_counter()
    for ci, c in enumerate(csp.CLASSES):
        pool = [R for k in (2, 3) for R in by_class[(k, c)]
                if 0 < len(R) < 2 ** len(next(iter(R)))]  # skip trivial (full) relations
        n_inst = agree = wit_ok = sat_count = 0
        cnt_ok = cnt_total = 0
        for i in range(150):
            rng = random.Random(20261006 + 1000 * ci + i)
            gamma = rng.sample(pool, 3)
            n = rng.randint(6, 11)
            m = rng.randint(n // 2, 3 * n)
            inst = csp.random_instance(gamma, n, m, rng)
            bs, _, bcount = csp.brute_force(inst)
            ps, pw = csp.solve_by_class(inst, c)
            n_inst += 1
            if c in ("0-valid", "1-valid"):
                agree += ps is True and bs is True  # these languages are always satisfiable by the constant
            else:
                agree += ps == bs
            if ps:
                wit_ok += csp.satisfies(inst, pw)
                sat_count += 1
            if c == "affine":
                _, _, acount = csp.solve_affine(inst)
                cnt_total += 1
                cnt_ok += acount == bcount
        extra = f"; affine counts 2^(n-rank) == brute-force counts: {cnt_ok}/{cnt_total}" if c == "affine" else ""
        print(f"  {c:10s}: {agree}/{n_inst} decisions agree with brute force; witnesses valid {wit_ok}/{sat_count} "
              f"(satisfiable instances){extra}")
    print(f"  [{time.perf_counter() - t0:.1f} s]")
    # negative control: the Horn solver on a non-Horn language must be able to fail
    rng = random.Random(7)
    nae = rel(*[t for t in product((0, 1), repeat=3) if len(set(t)) == 2])
    wrong_decision = wrong_witness = 0
    for i in range(200):
        inst = csp.random_instance([nae], 8, 14, rng)
        bs, _, _ = csp.brute_force(inst)
        hs, hw = csp.solve_horn(inst)
        wrong_decision += hs != bs
        wrong_witness += bool(hs) and not csp.satisfies(inst, hw)
    print(f"  negative control: Horn propagation applied to NAE-3-SAT (not Horn; the predictor does not license it): "
          f"wrong decision on {wrong_decision}/200 random instances, invalid witness on {wrong_witness}/200")
    # (first version of this control compared decisions only and reported 0/200: Horn propagation uses only the
    #  Horn clauses implied by NAE, i.e. (not x or not y or not z), so it answers 'satisfiable' with the all-zero
    #  assignment, which agrees with brute force on satisfiable instances while the witness is wrong.)


def part3() -> None:
    print("\n=== Part 3: named languages")
    named = {
        "2-SAT (all binary clauses)": [clause(s) for s in product((0, 1), repeat=2)],
        "3-SAT (all ternary clauses)": [clause(s) for s in product((0, 1), repeat=3)],
        "positive 3-clauses only (x or y or z)": [clause((1, 1, 1))],
        "Horn-3-SAT (<= 1 positive literal)": [clause(s) for s in product((0, 1), repeat=3) if sum(s) <= 1],
        "XOR-SAT (x+y+z = 0 or 1)": [rel(*[t for t in product((0, 1), repeat=3) if sum(t) % 2 == b]) for b in (0, 1)],
        "1-in-3-SAT": [rel((1, 0, 0), (0, 1, 0), (0, 0, 1))],
        "NAE-3-SAT": [rel(*[t for t in product((0, 1), repeat=3) if len(set(t)) == 2])],
        "graph 2-colouring (x != y)": [rel((0, 1), (1, 0))],
    }
    for name, gamma in named.items():
        print(f"  {name:42s} -> {csp.predict(gamma)}")


def main() -> int:
    by_class = part1()
    part2(by_class)
    part3()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
