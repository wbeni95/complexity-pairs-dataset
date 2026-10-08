#!/usr/bin/env python3
"""Verifier for theorems/tripartition-tensor-p2-rank-at-most-29 (see README.md in this folder).

What it checks, in order (exact integer and rational arithmetic, Python standard library only):
  1. the SHA-256 of data/P2_rank29.json, before anything else is read from it;
  2. the file format: the keys, "tensor" = "T_2,2,2", "scale" = "1/4", "rank" = 29, three 15 x 29 matrices,
     every entry in {-1, 0, 1};
  3. the coordinate convention: the 15 two-element subsets of {1, ..., 6} in increasing order of the bitmask
     sum_{e in S} 2^(e-1) are exactly the list INDEX below, and README.md prints the same list;
  4. the identity of the Theorem, entry by entry over the integers:
         sum_{r=1}^{29} A[i][r] B[j][r] C[k][r] = 4 * [S_i, S_j, S_k are pairwise disjoint]
     for all 15^3 = 3375 index triples (i, j, k); P_2 has 90 nonzero entries;
  5. Lemma 2 (conciseness) for k = 1, 2, 3: the x-slices of P_k are nonzero with pairwise disjoint supports;
  6. Lemma 3: 8^k C(2k,k) < 27^k exactly for 1 <= k <= 10 and > for k = 11, and the ratio step
     16(2k+1) > 27(k+1) for k >= 3 (checked for 3 <= k <= 1000; the README proves it for all k >= 3).
Every check prints a [PASS]/[FAIL] line with what it covered and an exact step count; the wall-clock seconds are
printed on a separate line. Exit code 0 only if every check passes.

Usage (from the repository root):  python theorems/tripartition-tensor-p2-rank-at-most-29/verify.py
Deterministic and offline; well under a second.
"""
import hashlib
import json
import sys
import time
from fractions import Fraction
from itertools import combinations
from math import comb
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "P2_rank29.json"
SHA256 = "3a46395da0783d3b315509261ea69fb4bb511ce2418a05b432e4bd0bfea32351"
RANK = 29
SCALE = 4
# coordinate i (counting from 0) <-> the i-th 2-subset of {1,...,6} (colexicographic order)
INDEX = ["12", "13", "23", "14", "24", "34", "15", "25", "35", "45", "16", "26", "36", "46", "56"]

FAILURES = []


def check(label, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        FAILURES.append(label)
    return ok


def timed(t0):
    print(f"    ({time.perf_counter() - t0:.3f} s)")


def ksubsets(n, k):
    """k-subsets of {1..n} as bitmasks (bit e-1 <-> element e), in increasing numeric order (colex order)."""
    return sorted(sum(1 << (e - 1) for e in c) for c in combinations(range(1, n + 1), k))


def label(mask):
    return "".join(str(e + 1) for e in range(10) if mask >> e & 1)


def main():
    t_start = time.perf_counter()

    # 1. pinned data file
    t0 = time.perf_counter()
    raw = DATA.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    if not check("SHA-256 of data/P2_rank29.json", digest == SHA256, f"{len(raw)} bytes, {digest}"):
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    timed(t0)

    # 2. format
    t0 = time.perf_counter()
    D = json.loads(raw.decode("utf-8"))
    A, B, C = D.get("A"), D.get("B"), D.get("C")
    shape_ok = (set(D) == {"tensor", "scale", "rank", "A", "B", "C"} and D["tensor"] == "T_2,2,2"
                and D["scale"] == f"1/{SCALE}" and D["rank"] == RANK
                and all(isinstance(M, list) and len(M) == 15 and all(isinstance(row, list) and len(row) == RANK
                                                                     for row in M) for M in (A, B, C)))
    entries = [x for M in (A, B, C) for row in M for x in row] if shape_ok else []
    vals_ok = shape_ok and all(type(x) is int and x in (-1, 0, 1) for x in entries)
    check("format: keys, tensor T_2,2,2, scale 1/4, rank 29, three 15 x 29 matrices, entries in {-1,0,1}",
          shape_ok and vals_ok, f"{len(entries)} entries ({sum(1 for x in entries if x)} nonzero), "
                                f"steps = {len(entries)} entry tests")
    timed(t0)
    if not (shape_ok and vals_ok):
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1

    # 3. coordinate convention
    t0 = time.perf_counter()
    subs = ksubsets(6, 2)
    readme = (HERE / "README.md").read_text(encoding="utf-8")
    table = "| " + " | ".join(str(i) for i in range(15)) + " |"
    sets = "| " + " | ".join("{" + ",".join(s) + "}" for s in INDEX) + " |"
    check("coordinates: the 15 two-subsets of {1..6} in increasing bitmask order equal INDEX, and README.md "
          "prints the same table", [label(m) for m in subs] == INDEX and table in readme and sets in readme,
          f"15 subsets compared, steps = {len(subs)}")
    timed(t0)

    # 4. the identity 4 * P_2 = sum_r a_r (x) b_r (x) c_r over the integers
    t0 = time.perf_counter()
    full = (1 << 6) - 1
    bad, nonzero, steps = 0, 0, 0
    for i, x in enumerate(subs):
        Ai = A[i]
        for j, y in enumerate(subs):
            AB = [Ai[r] * B[j][r] for r in range(RANK)]
            steps += RANK
            for k, z in enumerate(subs):
                Ck = C[k]
                v = sum(AB[r] * Ck[r] for r in range(RANK))
                steps += RANK
                part = not (x & y) and not (x & z) and not (y & z) and (x | y | z) == full
                nonzero += part
                if v != SCALE * part:
                    bad += 1
    check("identity 4*P_2 = sum_{r=1}^{29} a_r (x) b_r (x) c_r over Z, every entry",
          bad == 0 and nonzero == 90, f"15^3 = 3375 entries, {nonzero} nonzero entries of P_2 (6!/(2!)^3 = 90), "
                                      f"{bad} mismatches, steps = {steps} integer products")
    timed(t0)

    # 5. Lemma 2: x-slices of P_k nonzero with pairwise disjoint supports (k = 1, 2, 3)
    t0 = time.perf_counter()
    ok, steps, sizes = True, 0, []
    for k in (1, 2, 3):
        n = 3 * k
        sk = ksubsets(n, k)
        fullk = (1 << n) - 1
        row_of = {}
        for x in sk:
            supp = 0
            for y in sk:
                steps += 1
                if x & y:
                    continue
                z = fullk ^ x ^ y
                if (y, z) in row_of:
                    ok = False
                row_of[(y, z)] = x
                supp += 1
            ok &= supp > 0
        ok &= len(row_of) == comb(n, k) * comb(2 * k, k)
        sizes.append(f"k={k}: {len(sk)} slices, {len(row_of)} support pairs")
    check("Lemma 2: the x-slices of P_k are nonzero and have pairwise disjoint supports (k = 1, 2, 3)", ok,
          "; ".join(sizes) + f"; steps = {steps} pair tests")
    timed(t0)

    # 6. Lemma 3: theta_k < N_k exactly for 1 <= k <= 10, > for k = 11; ratio step for k >= 3
    t0 = time.perf_counter()
    below = [k for k in range(1, 12) if 8 ** k * comb(2 * k, k) < 27 ** k]
    ratios = [Fraction(8 ** k * comb(3 * k, k) * comb(2 * k, k), 27 ** k * comb(3 * k, k)) for k in range(1, 12)]
    step_ok = all(16 * (2 * k + 1) > 27 * (k + 1) for k in range(3, 1001))
    check("Lemma 3: theta_k = 8^k C(3k,k) C(2k,k) / 27^k < N_k = C(3k,k) exactly for k = 1..10, > for k = 11; "
          "16(2k+1) > 27(k+1) for 3 <= k <= 1000",
          below == list(range(1, 11)) and 8 ** 11 * comb(22, 11) > 27 ** 11 and step_ok,
          "theta_k/N_k = " + ", ".join(f"{float(q):.3f}" for q in ratios) + " (k = 1..11); steps = 11 + 1 + 998 "
                                                                           "integer comparisons")
    timed(t0)

    print(f"total {time.perf_counter() - t_start:.3f} s")
    if FAILURES:
        print(f"FAILED: {len(FAILURES)} check(s): {FAILURES}")
        return 1
    print("ALL CHECKS PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
