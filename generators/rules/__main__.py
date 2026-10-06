"""CLI for the rule-mining package.

  python -m generators.rules list                       # rules and their catalogue entries
  python -m generators.rules screen memo --seed 1 --count 50 [--out results/x.jsonl]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import RULES, load
from .common import write_jsonl
from .runner import compact, run_rule, summarise


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m generators.rules", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list")
    sp = sub.add_parser("screen")
    sp.add_argument("rule", choices=RULES)
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--count", type=int, default=50)
    sp.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    if args.cmd == "list":
        for r in RULES:
            cat = load(r).CATALOGUE
            print(f"{r}: {cat['name']}\n  precondition: {cat['precondition']}\n  cost: {cat['cost_change']}\n"
                  f"  failure: {cat['failure_mode']}")
        return 0
    recs = run_rule(args.rule, args.seed, args.count)
    if args.out:
        write_jsonl(args.out, [compact(r) for r in recs])
    print(json.dumps(summarise(recs), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
