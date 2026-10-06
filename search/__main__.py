"""Command line for the search environment. Run from the repository root:

  python -m search flip --format 3 3 3 --seed 1 --max-flips 2000000 --plateau 50000 [--escape plus]
                        [--reduction linear] [--lookahead 0] [--max-weight 0] [--max-seconds 600] [--target-rank 23] [--start scheme.json]
                        [--save-dir DIR] [--best-known 23] [--log run.jsonl]
  python -m search verify FILE.json [FILE.json ...]
  python -m search sortnet --n 6 --seed 1 --tries 2000

`flip` starts from the standard algorithm (rank n*m*p) unless --start is given, prints the rank trajectory and,
with --save-dir, saves the best scheme (and, with --best-known, labels it "matches best known",
"above best known" or "BELOW best known -- candidate, needs independent checks"). Every saved scheme passes
the exact verifier first. `verify` re-checks saved schemes with both exact verifiers.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import gf2mm
from .driver import WalkConfig, run_walk
from .experiment import status_label
from .machine import CpuMeter, environment, set_below_normal_priority


def cmd_flip(args) -> int:
    set_below_normal_priority()
    fmt = tuple(args.format)
    start = None
    if args.start:
        sfmt, start, _ = gf2mm.load_scheme(args.start)
        if tuple(sfmt) != fmt:
            print(f"start scheme has format {sfmt}, not {fmt}", file=sys.stderr)
            return 2
    cfg = WalkConfig(fmt=fmt, seed=args.seed, max_flips=args.max_flips, plateau=args.plateau, escape=args.escape,
                     slack=args.slack, reduction=args.reduction, max_seconds=args.max_seconds,
                     target_rank=args.target_rank, lookahead_every=args.lookahead, max_weight=args.max_weight)
    meter = CpuMeter().start()
    res = run_walk(cfg, start=start, logfile=args.log, echo=print)
    load = meter.stop()
    print(json.dumps({k: v for k, v in res.items() if k not in ("best_scheme", "first_at_rank", "config")}))
    print(json.dumps(load))
    if args.save_dir:
        os.makedirs(args.save_dir, exist_ok=True)
        r = res["best_rank"]
        path = os.path.join(args.save_dir, f"{fmt[0]}x{fmt[1]}x{fmt[2]}_rank{r}_seed{args.seed}.json")
        gf2mm.save_scheme(path, fmt, res["best_scheme"], status=status_label(r, args.best_known),
                          best_known_rank=args.best_known,
                          provenance={"command": " ".join(sys.argv), "seed": args.seed,
                                      "reached_at_flip": res["best_reached_at_flip"],
                                      "reached_at_seconds": res["best_reached_at_seconds"],
                                      "total_flips": res["flips"], "machine": load, "environment": environment()})
        print("saved", path)
    return 0


def cmd_verify(args) -> int:
    bad = 0
    for path in args.files:
        fmt, terms, doc = gf2mm.load_scheme(path)
        ok1 = gf2mm.verify(fmt, terms)
        ok2 = gf2mm.verify_explicit(fmt, terms)
        ok3 = gf2mm.random_check(fmt, terms, trials=50, seed=0)
        rank_ok = doc.get("rank") == len(terms)
        print(f"{path}: format {fmt} rank {len(terms)} verify={ok1} verify_explicit={ok2} random_check={ok3} "
              f"rank_field_ok={rank_ok}")
        bad += not (ok1 and ok2 and ok3 and rank_ok)
    return 1 if bad else 0


def cmd_sortnet(args) -> int:
    from . import sortnet
    set_below_normal_priority()
    net, stats = sortnet.search(args.n, seed=args.seed, tries=args.tries)
    print(f"n={args.n}: best size {len(net)} after {args.tries} tries; verified={sortnet.sorts(args.n, net)}")
    print(net)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m search", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("flip", help="flip-graph random walk for GF(2) matrix multiplication schemes")
    f.add_argument("--format", type=int, nargs=3, required=True, metavar=("N", "M", "P"))
    f.add_argument("--seed", type=int, required=True)
    f.add_argument("--max-flips", type=int, required=True)
    f.add_argument("--plateau", type=int, default=100_000)
    f.add_argument("--escape", choices=("plus", "restart", "none"), default="plus")
    f.add_argument("--slack", type=int, default=1)
    f.add_argument("--reduction", choices=("linear", "pair"), default="linear")
    f.add_argument("--lookahead", type=int, default=0, help="scan for a reducing flip every K flips (0 = off)")
    f.add_argument("--max-weight", type=int, default=0, help="reject flips creating heavier factors (0 = off)")
    f.add_argument("--max-seconds", type=float)
    f.add_argument("--target-rank", type=int)
    f.add_argument("--start")
    f.add_argument("--save-dir")
    f.add_argument("--best-known", type=int)
    f.add_argument("--log")
    f.set_defaults(func=cmd_flip)
    v = sub.add_parser("verify", help="re-verify saved scheme JSON files")
    v.add_argument("files", nargs="+")
    v.set_defaults(func=cmd_verify)
    s = sub.add_parser("sortnet", help="small randomized sorting-network search")
    s.add_argument("--n", type=int, required=True)
    s.add_argument("--seed", type=int, required=True)
    s.add_argument("--tries", type=int, default=1000)
    s.set_defaults(func=cmd_sortnet)
    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
