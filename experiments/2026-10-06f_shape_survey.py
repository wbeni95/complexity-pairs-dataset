#!/usr/bin/env python3
"""Shape diagnostic survey over every exact-count V2 series (round 2026-10-06f).

For every V2 measurement with measure "reported" in ledger/runs/20261006T143136Z.json (read-only), run the
validator's own informational shape diagnostic (tools/validate.run_shape -> methods/shape.py) and print one row:
category, reason, found vs claimed, grid, and seconds.

Grid per series:
  * if the entry's harness.scaling has a `shape` block, that block is used ("entry");
  * otherwise an automatic candidate ("auto", not stored anywhere): the cost is parsed; a log factor or an irrational
    power of n gives a doubling grid n = 2, 4, ..., else a consecutive grid n = 1, 2, ...; counts are taken in
    increasing n until 22 terms (doubling: n = 2^16) or until one count takes longer than --max-count-seconds;
    if the smallest n fails (some harnesses need a minimum n) the start moves up. Series with samples > 1 are
    reported without counting (randomised_counts).
Counting uses the V2 seeding scheme, so the counts at V2's n values equal the ledger values.

Usage (repository root; one process, below-normal priority, about 2-4 minutes):
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe experiments/2026-10-06f_shape_survey.py [--json out.json]
      [--only <entry-id substring>] [--max-count-seconds 3]
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "tools"))
sys.setrecursionlimit(10000)

import validate as V  # noqa: E402
from methods import shape as sd  # noqa: E402

LEDGER = REPO / "ledger" / "runs" / "20261006T143136Z.json"


def auto_kind(cost: str) -> str:
    try:
        s = sd.parse_cost(cost)
    except sd.NotParseable:
        return "consecutive"
    if sd.const_equal(s.base, sd.ONE) and (s.q != 0 or sd.p_rational(s.p2) is None):
        return "doubling"
    return "consecutive"


def count_fn(entry, harness, gen, alg, fn):
    def count(n):
        inst = gen(n, random.Random(f"{entry['id']}|v2|{n}"))
        random.seed(f"{entry['id']}|v2|{n}|0|{alg['name']}")
        return harness.reported_cost(fn(inst))
    return count


def adaptive_counts(count, kind: str, max_s: float, target: int = 22):
    """Counts on increasing n; returns (ns, values, stop_reason)."""
    starts = [1, 2, 3, 4, 5, 6, 8] if kind == "consecutive" else [2, 4, 8, 16]
    for lo in starts:
        ns, vals = [], []
        n = lo
        try:
            while True:
                t0 = time.perf_counter()
                v = count(n)
                dt = time.perf_counter() - t0
                ns.append(n)
                vals.append(v)
                if len(ns) >= target or (kind == "doubling" and n >= 2 ** 16):
                    return ns, vals, f"target reached ({len(ns)} terms)"
                if dt > max_s:
                    return ns, vals, f"stopped: one count took {dt:.1f}s"
                n = n + 1 if kind == "consecutive" else 2 * n
        except Exception as e:  # noqa: BLE001 -- harness may need a larger n
            if len(ns) >= 6:
                return ns, vals, f"stopped at n={n}: {type(e).__name__}"
            continue
    return [], [], "no start value worked"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="write all results to this file")
    ap.add_argument("--only", help="entry id substring")
    ap.add_argument("--max-count-seconds", type=float, default=3.0)
    args = ap.parse_args()
    try:
        from search.machine import set_below_normal_priority
        set_below_normal_priority()
    except Exception:  # noqa: BLE001
        pass
    led = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = []
    for e in led["entries"]:
        if args.only and args.only not in e["id"]:
            continue
        for m in e.get("v2", []):
            if m["measure"] != "reported":
                continue
            d = REPO / e["path"]
            entry = V.load_entry(d)
            harness = V.load_module(V.resolve_in_repo(d, entry["test_harness"]["module"]))
            gen = getattr(harness, "generate_scaling", harness.generate)
            alg = next(a for a in V.implemented(entry) if a["name"] == m["algorithm"])
            fn = V.load_callable(d, alg["implementation"])
            sc = dict(alg["harness"]["scaling"])
            t0 = time.perf_counter()
            origin = "entry" if "shape" in sc else "auto"
            fake_m = {"n_values": m["n_values"], "values": m["values"]}
            note = ""
            if origin == "auto":
                kind = auto_kind(sc["cost"])
                if sc.get("samples", 1) > 1:
                    sc["shape"] = {"sequence": kind, "n_range": [1, 2] if kind == "consecutive" else [2, 4]}
                else:
                    ns, vals, note = adaptive_counts(count_fn(entry, harness, gen, alg, fn), kind,
                                                     args.max_count_seconds)
                    if len(ns) < 2:
                        rows.append({"entry": e["id"], "algorithm": m["algorithm"], "cost": sc["cost"],
                                     "origin": origin, "category": "UNDETERMINED", "reason": "count_failed",
                                     "detail": note})
                        print(f"{e['id'][:40]:40s} {m['algorithm'][:30]:30s} count_failed {note}", flush=True)
                        continue
                    sc["shape"] = {"sequence": kind, "n_range": [ns[0], ns[-1]]}
                    fake_m = {"n_values": ns, "values": [float(v) if isinstance(v, (int, float)) else v for v in vals]}
                    fake_m["values"] = vals  # exact ints are reused directly by run_shape
            res = V.run_shape(entry, harness, gen, alg, fn, sc, fake_m)
            dt = time.perf_counter() - t0
            row = {"entry": e["id"], "algorithm": m["algorithm"], "cost": sc["cost"], "origin": origin,
                   "block": sc.get("shape"), "samples": sc.get("samples", 1), "count_note": note,
                   "seconds_total": round(dt, 2), **res}
            rows.append(row)
            print(f"{e['id'][:40]:40s} {m['algorithm'][:30]:30s} [{origin}] {V.shape_line(res)[:260]}", flush=True)
    cats = {}
    for r in rows:
        cats[(r["category"], r["reason"])] = cats.get((r["category"], r["reason"]), 0) + 1
    print(f"\n{len(rows)} series")
    for (c, rsn), k in sorted(cats.items()):
        print(f"  {c:12s} {rsn:36s} {k}")
    if args.json:
        Path(args.json).write_text(json.dumps(rows, indent=1, default=str), encoding="utf-8")
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
