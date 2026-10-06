"""Experiment (research/2026-10-07_search_flipgraph.md, section "Saved schemes"): separate re-verification of every
scheme saved under search/schemes/, independently of the run that produced it.

For each JSON file:
  * recompute the rank from the term list and compare with the "rank" field;
  * check the factors are in range for the format;
  * verify (bit-sliced tensor comparison) and verify_explicit (one Brent equation at a time, separate code);
  * functional check: run the scheme on 100 random 0/1 matrix pairs (seed 20261007) and compare with the
    schoolbook product over GF(2);
  * check the "status" label against the "best_known_rank" field;
  * report whether the 0/1 coefficients happen to be valid over Z as they stand (no sign lifting attempted);
  * for square formats k x k x k, the exponent log_k(rank) of the recursive algorithm (characteristic 2 only).
For square formats, an equivalence invariant is also printed: the multiset over terms of the sorted triple of
GF(2) matrix ranks of (alpha, beta, gamma). It is unchanged by the symmetries (A, B, C) -> (XAY^-1, YBZ^-1, ZCX^-1),
cyclic rotation and transposition, so schemes with different invariants are certainly inequivalent (equal
invariants prove nothing). The number of distinct invariants per (format, rank) is a lower bound on the number of
inequivalent schemes among the saved ones.
Sorting networks saved there (object "sorting network") are re-checked by the 0-1 principle and all n! permutations.
Exit code 1 if any check fails. Deterministic.

Run from the repository root:  python experiments/2026-10-07_reverify_schemes.py
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from search import gf2mm, sortnet  # noqa: E402
from search.experiment import status_label  # noqa: E402
from search.machine import CpuMeter, set_below_normal_priority  # noqa: E402

def gf2_matrix_rank(x, rows, cols):
    basis = {}
    for r in range(rows):
        v = (x >> (r * cols)) & ((1 << cols) - 1)
        while v:
            hb = v.bit_length() - 1
            if hb in basis:
                v ^= basis[hb]
            else:
                basis[hb] = v
                break
    return len(basis)


def invariant(fmt, terms):
    n, m, p = fmt
    trip = [tuple(sorted((gf2_matrix_rank(a, n, m), gf2_matrix_rank(b, m, p), gf2_matrix_rank(c, p, n))))
            for a, b, c in terms]
    return tuple(sorted(trip))


print("below-normal priority:", set_below_normal_priority())
invariants = {}
meter = CpuMeter().start()
files = sorted((ROOT / "search" / "schemes").glob("*.json"))
bad = 0
by_group = {}
for path in files:
    doc = json.loads(path.read_text(encoding="utf-8"))
    if doc.get("object") == "sorting network":
        n, net = doc["n"], [tuple(c) for c in doc["comparators"]]
        ok = sortnet.sorts(n, net) and sortnet.sorts_permutations(n, net) and doc["size"] == len(net)
        bad += not ok
        by_group.setdefault((("sortnet", n), len(net), doc.get("status")), []).append(path.name)
        print(f"{'OK ' if ok else 'FAIL'} {path.name}: sorting network n={n} size {len(net)} | 0-1 principle and "
              f"all {math.factorial(n)} permutations: {ok} | '{doc.get('status')}'")
        continue
    fmt = tuple(doc["format"])
    terms = [tuple(t) for t in doc["terms"]]
    gf2mm.check_factor_ranges(fmt, terms)
    ok_rank = doc["rank"] == len(terms)
    ok1 = gf2mm.verify(fmt, terms)
    ok2 = gf2mm.verify_explicit(fmt, terms)
    ok3 = gf2mm.random_check(fmt, terms, trials=100, seed=20261007)
    ok_label = doc.get("status") == status_label(len(terms), doc.get("best_known_rank"))
    over_z = gf2mm.verify_over_integers(fmt, terms)
    expo = ""
    if fmt[0] == fmt[1] == fmt[2] and fmt[0] > 1:
        expo = f" log_{fmt[0]}(r) = {math.log(len(terms), fmt[0]):.4f}"
        invariants.setdefault((fmt, len(terms)), set()).add(invariant(fmt, terms))
    allok = ok_rank and ok1 and ok2 and ok3 and ok_label
    bad += not allok
    by_group.setdefault((fmt, len(terms), doc.get("status")), []).append(path.name)
    print(f"{'OK ' if allok else 'FAIL'} {path.name}: format {fmt} rank {len(terms)} | verify {ok1} | "
          f"verify_explicit {ok2} | random 100 {ok3} | rank field {ok_rank} | label '{doc.get('status')}' {ok_label} | "
          f"valid over Z as-is {over_z}{expo}")
print(f"\n{len(files)} files, {bad} failing")
for (fmt, r, status), names in sorted(by_group.items(), key=str):
    print(f"  {fmt} rank {r} [{status}]: {len(names)} file(s)")
for (fmt, r), inv in sorted(invariants.items(), key=str):
    print(f"  {fmt} rank {r}: {len(inv)} distinct factor-rank invariant(s) among the saved schemes")
print("machine:", meter.stop())
sys.exit(1 if bad else 0)
