#!/usr/bin/env python3
"""Static consistency checks across index.json, entry.json files and the latest ledger (deviation analysis, 2026-10-07b).

Checks (scope: every entry.json under pairs/, staging/, synthetic/; index.json; the newest ledger run):
  1. index.json counts (entries, validated_pairs, T6/T9/T7 counts, with_quantum_algorithm, by_level, by_type)
     recomputed from the entry files on disk, using the counting rule of START_HERE (validated = V1+ in pairs/
     with any of T1-T5, T8, T9, primary or secondary; "open_problems_T6" counted as primary-or-secondary,
     "quantum_separations_T9_in_pairs" (renamed 2026-10-07 from "proven_quantum_advantage_T9") as primary-or-
     secondary in pairs/ only, by_type as primary only).
  2. Every index.json entry row against its entry.json: level, pair_type, secondary_tags, path, algorithm names,
     time_complexity text, implemented flag.
  3. Latest ledger run against entry.json: claimed level equals entry level; each V2 measurement's cost,
     n_values, measure and tolerance equal the CURRENT harness.scaling (detects entries edited after the
     last recorded run); every V2-claiming entry has a V2 record for every implemented algorithm.
  4. Tag conventions not enforced by the validator: entries with a poly -> faster-poly step among their
     algorithms (claimed costs both polynomial and different) that do not carry T3 (primary or secondary),
     detected by a simple classification of scaling.cost strings (exponential if it contains '**n',
     '**(n', 'factorial' or 'C('; otherwise polynomial).
Deterministic; no timing.

Result (2026-10-06, ~10:03 local, while another agent was adding entries): disk 56 entries vs index 54 (two new
entries, global-min-cut and xor-convolution, not yet indexed); 0 row mismatches for the 54 indexed entries;
3 entries (matching, element distinctness, sorting) had scaling configs differing from ledger 20261006T070542Z
and 2 new entries had no ledger record; T3 convention gap: Fibonacci and MST have a poly -> faster-poly step
without T3, while LIS carries secondary T3. Output depends on the working tree at run time.
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
VALID_TAGS = {"T1", "T2", "T3", "T4", "T5", "T8", "T9"}


def entries():
    out = []
    for loc in ("pairs", "staging", "synthetic"):
        for d in sorted((REPO / loc).iterdir()):
            if (d / "entry.json").is_file():
                out.append((loc, d, json.loads((d / "entry.json").read_text(encoding="utf-8"))))
    return out


def is_exp(cost):
    return any(s in cost for s in ("**n", "**(n", "factorial", "C("))


def main():
    es = entries()
    idx = json.loads((REPO / "index.json").read_text(encoding="utf-8"))
    tags = lambda e: {e["pair_type"], *e.get("secondary_tags", [])}  # noqa: E731
    calc = {
        "entries": len(es),
        "validated_pairs": sum(loc == "pairs" and e["verification"]["level"] >= "V1" and bool(tags(e) & VALID_TAGS)
                               for loc, _, e in es),
        "open_problems_T6": sum("T6" in tags(e) for _, _, e in es),
        "quantum_separations_T9_in_pairs": sum("T9" in tags(e) and loc == "pairs" for loc, _, e in es),
        "synthetic_T7": sum(e["pair_type"] == "T7" for _, _, e in es),
        "with_quantum_algorithm": sum(any(a["model"] == "quantum" for a in e["algorithms"]) for _, _, e in es),
        "by_level": dict(Counter(e["verification"]["level"] for _, _, e in es)),
        "by_type": dict(Counter(e["pair_type"] for _, _, e in es)),
    }
    print("1. index.json counts vs recomputed from disk")
    for k, v in calc.items():
        iv = idx["counts"].get(k)
        if isinstance(v, dict):
            iv2 = {kk: vv for kk, vv in (iv or {}).items() if vv}
            ok = iv2 == v
            print(f"   {k}: index {iv2}  disk {v}  {'OK' if ok else 'MISMATCH'}")
        else:
            print(f"   {k}: index {iv}  disk {v}  {'OK' if iv == v else 'MISMATCH'}")

    print("\n2. index rows vs entry.json")
    rows = {r["id"]: r for r in idx["entries"]}
    disk_ids = {e["id"] for _, _, e in es}
    print(f"   ids only in index: {sorted(set(rows) - disk_ids)}; ids only on disk: {sorted(disk_ids - set(rows))}")
    nmis = 0
    for loc, d, e in es:
        r = rows.get(e["id"])
        if r is None:
            continue
        probs = []
        if r["level"] != e["verification"]["level"]:
            probs.append(f"level {r['level']} vs {e['verification']['level']}")
        if r["pair_type"] != e["pair_type"]:
            probs.append("pair_type")
        if sorted(r.get("secondary_tags", [])) != sorted(e.get("secondary_tags", [])):
            probs.append("secondary_tags")
        if r["path"] != f"{loc}/{d.name}":
            probs.append("path")
        ia = [(a["name"], a["time_complexity"], a["implemented"]) for a in r["algorithms"]]
        ea = [(a["name"], a["time_complexity"], bool(a.get("implementation"))) for a in e["algorithms"]]
        if ia != ea:
            probs.append("algorithms (name / time_complexity / implemented)")
        if probs:
            nmis += 1
            print(f"   {e['id']}: {', '.join(probs)}")
    print(f"   rows with a mismatch: {nmis} of {len(es)}")

    print("\n3. latest ledger vs current entry.json")
    latest = sorted((REPO / "ledger" / "runs").glob("*.json"))[-1]
    led = {r["id"]: r for r in json.loads(latest.read_text(encoding="utf-8"))["entries"]}
    print(f"   ledger file: {latest.name}")
    nprob = 0
    for loc, d, e in es:
        r = led.get(e["id"])
        if r is None:
            print(f"   {e['id']}: not in the latest ledger run")
            nprob += 1
            continue
        if r["claimed"] != e["verification"]["level"]:
            print(f"   {e['id']}: ledger claimed {r['claimed']} vs entry {e['verification']['level']}")
            nprob += 1
        if e["verification"]["level"] >= "V2":
            recs = {m["algorithm"]: m for m in r.get("v2", []) or []}
            for a in e["algorithms"]:
                if not a.get("implementation"):
                    continue
                sc = a.get("harness", {}).get("scaling", {})
                m = recs.get(a["name"])
                if m is None:
                    print(f"   {e['id']} / {a['name']}: no V2 record")
                    nprob += 1
                    continue
                diffs = []
                if m["cost"] != sc.get("cost"):
                    diffs.append(f"cost {m['cost']!r} vs {sc.get('cost')!r}")
                if m["n_values"] != sc.get("n_values"):
                    diffs.append("n_values")
                if m["measure"] != sc.get("measure", "time"):
                    diffs.append("measure")
                if m["tolerance"] != sc.get("tolerance", 0.25):
                    diffs.append("tolerance")
                if [x["cost"] for x in m.get("rivals", [])] != sc.get("rivals", []):
                    diffs.append("rivals")
                if diffs:
                    print(f"   {e['id']} / {a['name']}: {', '.join(diffs)}")
                    nprob += 1
    print(f"   problems: {nprob}")

    print("\n4. tag convention: poly -> faster-poly step present but no T3 tag")
    for loc, d, e in es:
        costs = [a.get("harness", {}).get("scaling", {}).get("cost") for a in e["algorithms"]
                 if a.get("harness", {}).get("scaling")]
        poly = sorted({c for c in costs if c and not is_exp(c) and c != "1"})
        if len(poly) >= 2 and "T3" not in tags(e):
            print(f"   {e['id']} ({e['pair_type']}, secondary {e.get('secondary_tags', [])}): polynomial costs {poly}")
    print("   entries with T3 as a SECONDARY tag:",
          [e["id"] for _, _, e in es if "T3" in e.get("secondary_tags", [])])


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    main()
