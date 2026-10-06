"""CLI for the mutation engine.

  python -m mutations list                         # mutant ids per builder
  python -m mutations run [--only a,b] [--workers 4] [--out DIR]
  python -m mutations props [--out FILE]           # mechanical property table of every structure
  python -m mutations summary [--records DIR]      # boundary map (markdown) from the records
  python -m mutations literature [--out FILE]      # verify DOIs / arXiv ids (network; rate-limited)
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

DEFAULT_RECORDS = REPO / "mutations" / "records" / "2026-10-06d"


def _builders():
    from mutations import targets
    return {**targets.OPSWAP_BUILDERS, **targets.MIRROR_BUILDERS}


def _run_builder(name: str, seed: str, trials_scale: int = 1) -> tuple[str, list, float]:
    try:
        from search.machine import set_below_normal_priority
        set_below_normal_priority()
    except Exception:  # noqa: BLE001
        pass
    from mutations import engine
    t0 = time.perf_counter()
    mutants = _builders()[name]()
    recs = []
    for m in mutants:
        m.trials *= trials_scale
        r = engine.run_mutant(m, seed)
        r["trials_scale"] = trials_scale
        r["builder"] = name
        recs.append(json.loads(json.dumps(r, ensure_ascii=False, default=repr)))
    return name, recs, time.perf_counter() - t0


def cmd_run(args):
    names = list(_builders()) if not args.only else args.only.split(",")
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    from mutations import engine
    workers = max(1, min(4, args.workers))
    t0 = time.perf_counter()
    with cf.ProcessPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(_run_builder, n, args.seed, args.trials_scale) for n in names]
        for f in cf.as_completed(futs):
            name, recs, dt = f.result()
            engine.write_records(recs, out_dir / f"{name}.jsonl")
            counts = {}
            for r in recs:
                counts[r["status"]] = counts.get(r["status"], 0) + 1
            print(f"[{time.perf_counter() - t0:7.1f}s] {name}: {len(recs)} mutants in {dt:.1f}s {counts}", flush=True)
    return 0


def cmd_list(args):
    for name, b in _builders().items():
        ms = b()
        print(f"{name}: {len(ms)} mutants")
        if args.verbose:
            for m in ms:
                print("   ", m.id)
    return 0


def cmd_props(args):
    from mutations import algebra, targets
    rows = []
    for key, S in targets.structures_for_properties().items():
        props = algebra.check_properties(S)
        rows.append({"structure": key, "label": S.label, "kind": S.kind, "properties": props})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False, default=repr) + "\n")
    for r in rows:
        held = [k for k, v in r["properties"].items() if v["holds"] is True]
        print(f"{r['structure']:>18}: " + " ".join(held))
    return 0


def cmd_summary(args):
    recs = []
    for p in sorted(Path(args.records).glob("*.jsonl")):
        if p.name in ("properties.jsonl", "literature.jsonl"):
            continue
        recs += [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]
    counts = {}
    for r in recs:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    print(f"{len(recs)} mutants: {counts}; near-miss flags: {sum(1 for r in recs if r.get('near_miss'))}")
    print("| pair | family | operator | mode | subject | status | tests | detail |")
    print("|---|---|---|---|---|---|---|---|")
    for r in recs:
        t = r["tests"]
        detail = r.get("reason") or r.get("trivial_reason") or ""
        if r["status"] == "KILLED":
            ce = r["counterexample"]
            detail = f"n={ce['size']}: oracle {ce['oracle_output']} vs subject {ce['subject_output']}; agree " \
                     f"{r['agreement_rate']}" + (f"; NEAR-MISS: {r['near_miss']}" if r.get("near_miss") else "")
        if r.get("cost_fit") and "alphas" in r["cost_fit"]:
            cf_ = r["cost_fit"]
            detail += f" fit[{cf_['measure']}] {cf_['claimed']}: alpha={cf_['alphas'].get(cf_['claimed'])}, " \
                      f"fits={cf_['fitting_within_tol']}"
        detail = detail.replace("|", "/")[:400]
        print(f"| {r['pair']} | {r['family']} | {r['operator']} | {r['mode']} | {r['subject']} | {r['status']} | "
              f"{t['tests']} | {detail} |")
    return 0


def cmd_literature(args):
    from mutations import literature
    rows = literature.verify_all()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for r in rows:
        print(f"{r['key']:>32}: {r['status']}  {r.get('found_title', '')[:90]}")
    return 0


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(prog="python -m mutations", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--only", default="")
    r.add_argument("--workers", type=int, default=4)
    r.add_argument("--out", default=str(DEFAULT_RECORDS))
    r.add_argument("--seed", default="2026-10-06d")
    r.add_argument("--trials-scale", type=int, default=1, help="multiply every mutant's trials per size")
    r.set_defaults(fn=cmd_run)
    li = sub.add_parser("list")
    li.add_argument("-v", "--verbose", action="store_true")
    li.set_defaults(fn=cmd_list)
    p = sub.add_parser("props")
    p.add_argument("--out", default=str(DEFAULT_RECORDS / "properties.jsonl"))
    p.set_defaults(fn=cmd_props)
    s = sub.add_parser("summary")
    s.add_argument("--records", default=str(DEFAULT_RECORDS))
    s.set_defaults(fn=cmd_summary)
    lt = sub.add_parser("literature")
    lt.add_argument("--out", default=str(DEFAULT_RECORDS / "literature.jsonl"))
    lt.set_defaults(fn=cmd_literature)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
